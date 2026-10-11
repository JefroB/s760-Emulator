-- Native-machine control surface. Never writes guest RAM, PC or firmware flags.
local json = require('json')
local channel = emu.file('rw')
local error = channel:open('socket.127.0.0.1:' .. assert(os.getenv('S760_RUNTIME_PORT')))
assert(not error, tostring(error))
local machine = manager.machine
local incoming = ''
local mouse_x, mouse_y, target_x, target_y = 0, 0, 0, 0
local settle = 0
local step_pending = nil
local render_pending = nil
local audio_enabled, audio_chunks, audio_frames = false, {}, 0
local audio_total, audio_dropped = 0, 0
local audio_limit = 44100
local midi_pending, midi_delivered, midi_error = 0, {}, ''
local midi_queue = {}
local button_states, external_midi = {}, ''
local checkpoint_pause = {grace=0}
checkpoint_pause.notifier = emu.add_machine_pause_notifier(function()
    -- The frame hook can pause inside a timer before the same frame's
    -- periodic hook runs. Skip that first periodic hook; the next one runs
    -- from the paused main loop after the old timer has returned.
    checkpoint_pause.grace = 1
end)
emu.register_sound_update(function(sound)
    if not audio_enabled then return end
    local left, right = sound[':lspeaker'], sound[':rspeaker']
    if not left or not right then return end
    left, right = left[1], right[1]
    assert(#left == #right, 'Native speaker channel length mismatch')
    local n = #left
    if n == 0 then return end
    -- Drop oldest complete blocks on overflow and report every lost frame.
    while audio_frames + n > audio_limit and #audio_chunks > 0 do
        local old = table.remove(audio_chunks, 1)
        audio_frames = audio_frames - old.frames
        audio_dropped = audio_dropped + old.frames
    end
    if n > audio_limit then
        audio_dropped = audio_dropped + n
    else
        local packed = {}
        for i=1,n do packed[i] = string.pack('<ff', left[i], right[i]) end
        audio_chunks[#audio_chunks+1] = {frames=n, data=table.concat(packed)}
        audio_frames = audio_frames + n
    end
    audio_total = audio_total + n
end)
local function write_all(data)
    local offset = 1
    while offset <= #data do
        local written = channel:write(data:sub(offset))
        assert(written > 0, 'Runtime socket closed')
        offset = offset + written
    end
end
local function reply(value)
    local encoded = json.stringify(value)
    write_all(string.pack('<I4', #encoded) .. encoded)
end
reply({protocol=1, token=os.getenv('S760_RUNTIME_TOKEN')})
local function field(port, name)
    local p = assert(machine.ioport.ports[port], 'Unknown input port')
    return assert(p.fields[name], 'Unknown input field')
end
local function send_audio(count)
    reply({ok=true, audio={frames=count, channels=2, rate=44100,
           first_sample=audio_total-audio_frames, dropped_frames=audio_dropped},
           seconds=machine.time:as_double(), buffered_frames=audio_frames-count})
    local remaining = count
    while remaining > 0 do
        local chunk = audio_chunks[1]
        local take = math.min(remaining, chunk.frames)
        write_all(chunk.data:sub(1, take*8))
        if take == chunk.frames then table.remove(audio_chunks, 1)
        else
            chunk.data = chunk.data:sub(take*8+1)
            chunk.frames = chunk.frames-take
        end
        remaining = remaining-take
    end
    audio_frames = audio_frames-count
end
local function run_midi_queue()
    coroutine.wrap(function()
            while #midi_queue > 0 do
                local event = midi_queue[1]
                local delay = event.sample/44100-machine.time:as_double()
                if delay > 0 and not emu.wait(delay) then
                    midi_error, midi_pending, midi_queue = 'MIDI schedule interrupted', 0, {}
                    return
                end
                if not emu.midi_send(':midiin', event.bytes) then
                    midi_error, midi_pending, midi_queue = 'MIDI transmitter rejected event', 0, {}
                    return
                end
                midi_delivered[#midi_delivered+1] = {sample=event.sample, seconds=machine.time:as_double()}
                if #midi_delivered > 256 then table.remove(midi_delivered, 1) end
                table.remove(midi_queue, 1)
                midi_pending = midi_pending-1
            end
    end)()
end
local function execute(command)
    if command.op == 'checkpoint_save' then
        assert(machine.paused and external_midi == '',
               'Checkpoint requires paused machine and disconnected external MIDI')
        local state = machine:buffer_save()
        local events = {}
        for _, event in ipairs(midi_queue) do
            local bytes = {}
            for i=1,#event.bytes do bytes[i] = event.bytes:byte(i) end
            events[#events+1] = {sample=event.sample,bytes=bytes}
        end
        local meta = json.stringify({version=2, seconds=machine.time:as_double(),
            midi=events, delivered=midi_delivered, midi_error=midi_error, mouse={mouse_x,mouse_y,target_x,target_y,settle},
            buttons=button_states, enabled=audio_enabled, frames=audio_frames,
            total=audio_total, dropped=audio_dropped})
        local chunks = {}
        for _, chunk in ipairs(audio_chunks) do chunks[#chunks+1] = chunk.data end
        local pcm = table.concat(chunks)
        local file = assert(io.open('runtime-checkpoint.bin', 'wb'))
        assert(file:write(string.pack('<I4I4I4', #meta, #state, #pcm), meta, state, pcm))
        assert(file:close())
        reply({ok=true, bytes=12+#meta+#state+#pcm})
    elseif command.op == 'checkpoint_load' then
        assert(machine.paused and external_midi == '',
               'Restore requires paused machine and disconnected external MIDI')
        local file = assert(io.open('runtime-checkpoint.bin', 'rb'))
        local blob = file:read('a'); file:close()
        local m, s, a = string.unpack('<I4I4I4', blob)
        assert(m <= 65536 and s <= 256*1024*1024 and a <= audio_limit*8 and #blob == 12+m+s+a,
               'Invalid checkpoint section lengths')
        local meta = assert(json.parse(blob:sub(13,12+m)))
        assert(meta.version == 2 and type(meta.enabled) == 'boolean' and meta.frames*8 == a
               and meta.frames >= 0 and meta.total >= meta.frames and meta.dropped >= 0,
               'Invalid checkpoint metadata')
        assert(type(meta.mouse) == 'table' and #meta.mouse == 5 and type(meta.buttons) == 'table',
               'Invalid checkpoint input metadata')
        assert(type(meta.seconds) == 'number' and meta.seconds >= 0
               and type(meta.midi) == 'table' and #meta.midi <= 256
               and type(meta.delivered) == 'table' and #meta.delivered <= 256
               and type(meta.midi_error) == 'string', 'Invalid checkpoint MIDI metadata')
        local restored_events, previous = {}, -1
        for _, event in ipairs(meta.midi) do
            assert(type(event.sample) == 'number' and event.sample % 1 == 0
                   and event.sample >= math.ceil(meta.seconds*44100)
                   and event.sample <= math.floor((meta.seconds+30)*44100)
                   and event.sample >= previous and type(event.bytes) == 'table'
                   and #event.bytes >= 1 and #event.bytes <= 3, 'Invalid checkpoint MIDI event')
            local bytes = {}
            for _, byte in ipairs(event.bytes) do
                assert(type(byte) == 'number' and byte % 1 == 0 and byte >= 0 and byte <= 255,
                       'Invalid checkpoint MIDI byte')
                bytes[#bytes+1] = string.char(byte)
            end
            restored_events[#restored_events+1] = {sample=event.sample,bytes=table.concat(bytes)}
            previous = event.sample
        end
        for _, input in ipairs(meta.buttons) do field(input.port,input.name) end
        assert(machine:buffer_load(blob:sub(13+m,12+m+s)))
        for _, input in ipairs(button_states) do field(input.port,input.name):set_value(0) end
        button_states = meta.buttons
        for _, input in ipairs(button_states) do field(input.port,input.name):set_value(input.down and 1 or 0) end
        mouse_x,mouse_y,target_x,target_y,settle = table.unpack(meta.mouse)
        for _, f in pairs(machine.ioport.ports[':NATIVE_MOUSE_X'].fields) do f:set_value(mouse_x) end
        for _, f in pairs(machine.ioport.ports[':NATIVE_MOUSE_Y'].fields) do f:set_value(mouse_y) end
        audio_enabled,audio_frames,audio_total,audio_dropped = meta.enabled,meta.frames,meta.total,meta.dropped
        audio_chunks = a > 0 and {{frames=meta.frames,data=blob:sub(13+m+s)}} or {}
        machine.sounds[':lspeaker'].hook = audio_enabled
        machine.sounds[':rspeaker'].hook = audio_enabled
        -- MAME postload synchronously resumes old waiters with false. Only
        -- after that cancellation do we install and rearm the saved timeline.
        midi_queue,midi_pending = restored_events,#restored_events
        midi_delivered,midi_error = meta.delivered,meta.midi_error
        if midi_pending > 0 then run_midi_queue() end
        reply({ok=true, seconds=machine.time:as_double()})
    elseif command.op == 'status' then
        reply({ok=true, state=machine.paused and 'paused' or 'running',
               seconds=machine.time:as_double(), firmware_ready='unknown',
               audio_enabled=audio_enabled, audio_dropped=audio_dropped,
               midi_pending=midi_pending, midi_delivered=midi_delivered, midi_error=midi_error})
    elseif command.op == 'schedule_midi' then
        assert(machine.paused, 'Pause before submitting a MIDI schedule')
        assert(midi_pending == 0 or command.append == true, 'Previous MIDI schedule is still pending')
        assert(type(command.events) == 'table' and #command.events >= 1 and #command.events <= 256,
               'Expected 1 to 256 MIDI events')
        assert(midi_pending + #command.events <= 256, 'MIDI schedule capacity exceeded')
        local now, previous, events = machine.time:as_double(),
            (#midi_queue > 0 and midi_queue[#midi_queue].sample or -1), {}
        for _, event in ipairs(command.events) do
            assert(type(event.sample) == 'number' and event.sample % 1 == 0
                   and event.sample >= math.ceil(now*44100) and event.sample <= math.floor((now+30)*44100)
                   and event.sample >= previous, 'Invalid, late or unordered MIDI timestamp')
            assert(type(event.bytes) == 'table' and #event.bytes >= 1 and #event.bytes <= 3,
                   'Expected 1 to 3 MIDI bytes')
            local bytes = {}
            for _, byte in ipairs(event.bytes) do
                assert(type(byte) == 'number' and byte % 1 == 0 and byte >= 0 and byte <= 255,
                       'Invalid MIDI byte')
                bytes[#bytes+1] = string.char(byte)
            end
            events[#events+1] = {sample=event.sample, bytes=table.concat(bytes)}
            previous = event.sample
        end
        local start = midi_pending == 0
        if start then midi_delivered, midi_error = {}, '' end
        for _, event in ipairs(events) do midi_queue[#midi_queue+1] = event end
        midi_pending = midi_pending + #events
        if start then run_midi_queue() end
        reply({ok=true, accepted=#events})
    elseif command.op == 'pause' then
        emu.pause()
        reply({ok=true, state='paused', seconds=machine.time:as_double()})
    elseif command.op == 'resume' then
        emu.unpause()
        reply({ok=true, state='running'})
    elseif command.op == 'step' then
        assert(machine.paused, 'Pause the machine before stepping')
        step_pending = machine.time:as_double()
        emu.step()
    elseif command.op == 'audio_capture' then
        assert(type(command.enabled) == 'boolean', 'Expected audio capture enabled boolean')
        audio_enabled = command.enabled
        machine.sounds[':lspeaker'].hook = audio_enabled
        machine.sounds[':rspeaker'].hook = audio_enabled
        audio_chunks, audio_frames, audio_total, audio_dropped = {}, 0, 0, 0
        reply({ok=true})
    elseif command.op == 'audio' then
        assert(audio_enabled, 'Enable audio capture first')
        send_audio(audio_frames)
    elseif command.op == 'render' then
        assert(machine.paused and audio_enabled, 'Render requires paused machine and enabled capture')
        assert(type(command.frames) == 'number' and command.frames % 1 == 0
               and command.frames >= 1 and command.frames <= 8192, 'Invalid render frame count')
        assert(audio_dropped == 0, 'Restart capture after an audio discontinuity')
        render_pending = {frames=command.frames, steps=0}
    elseif command.op == 'frames' then
        local crt, w, h = machine.screens[':crt_screen']:pixels()
        local lcd, lw, lh = machine.screens[':lcd_screen']:pixels()
        local registers = machine.devices[':maincpu'].spaces['register']
        reply({ok=true, surfaces={{0,w,h},{1,lw,lh}}, seconds=machine.time:as_double(), paused=machine.paused,
               cursor={registers:read_u16(0xd0), registers:read_u8(0xd2)}})
        write_all(crt)
        write_all(lcd)
    elseif command.op == 'button' then
        field(command.port, command.name):set_value(command.down and 1 or 0)
        local found = false
        for _, input in ipairs(button_states) do
            if input.port == command.port and input.name == command.name then input.down=command.down; found=true end
        end
        if not found then button_states[#button_states+1] = {port=command.port,name=command.name,down=command.down} end
        reply({ok=true})
    elseif command.op == 'pointer' then
        assert(type(command.x) == 'number' and command.x >= 0 and command.x <= 320, 'Invalid pointer X')
        assert(type(command.y) == 'number' and command.y >= 0 and command.y <= 120, 'Invalid pointer Y')
        target_x, target_y = command.x, command.y
        reply({ok=true})
    elseif command.op == 'quit' then
        reply({ok=true})
        machine:exit()
    elseif command.op == 'midi_device' then
        for _, image in pairs(machine.images) do
            if image.image_type_name == 'midiin' then
                if command.name == '' then image:unload()
                else
                    local failure = image:load(command.name)
                    assert(not failure, tostring(failure))
                end
                external_midi = command.name
                reply({ok=true})
                return
            end
        end
        reply({ok=false, error='MIDI input device is unavailable'})
    else
        reply({ok=false, error='Unsupported runtime operation'})
    end
end
local function pump(outside_timeslice)
    if render_pending then
        if audio_dropped > 0 then
            emu.pause()
            render_pending = nil
            reply({ok=false, error='Audio overflow during render'})
        elseif audio_frames >= render_pending.frames then
            emu.pause()
            local count = render_pending.frames
            render_pending = nil
            send_audio(count)
        elseif render_pending.steps >= 60 then
            emu.pause()
            render_pending = nil
            reply({ok=false, error='No sufficient PCM after 60 video steps'})
        else
            render_pending.steps = render_pending.steps+1
            -- Run freely between frame callbacks until the requested PCM is
            -- available. Pausing after every step imposed wall-clock sleeps
            -- even in nothrottle mode and starved the host audio worker.
            if machine.paused then emu.unpause() end
        end
        return
    end
    if step_pending then
        if machine.paused and machine.time:as_double() > step_pending then
            reply({ok=true, state='paused', seconds=machine.time:as_double()})
            step_pending = nil
        end
        return
    end
    -- MU-1 packets contain signed eight-bit deltas. Split long host jumps so
    -- crossing the screen cannot wrap the guest delta and move backwards.
    if mouse_x ~= target_x or mouse_y ~= target_y then
        mouse_x = mouse_x + math.max(-63, math.min(63, target_x - mouse_x))
        mouse_y = mouse_y + math.max(-63, math.min(63, target_y - mouse_y))
        for _, f in pairs(machine.ioport.ports[':NATIVE_MOUSE_X'].fields) do f:set_value(mouse_x) end
        for _, f in pairs(machine.ioport.ports[':NATIVE_MOUSE_Y'].fields) do f:set_value(mouse_y) end
        settle = 2
    elseif settle > 0 then settle = settle - 1 end
    incoming = incoming .. channel:read(4096)
    if #incoming > 65536 then machine:exit(); return end
    local newline = incoming:find('\n', 1, true)
    -- At most one command per frame: bounded work, no unbounded input drain.
    if newline and (settle == 0 or machine.paused) then
        local text = incoming:sub(1, newline - 1)
        local command = json.parse(text)
        -- frame_done may run inside an emulated timer callback. Loading there
        -- lets the old callback's return path overwrite restored timer state;
        -- saving there can capture a timer before it has been rescheduled.
        -- Service buffer checkpoints only from the paused wall-time callback.
        if command and (command.op == 'checkpoint_save' or command.op == 'checkpoint_load')
           and machine.paused and not outside_timeslice then return end
        incoming = incoming:sub(newline + 1)
        local ok, failure = pcall(function() execute(assert(command)) end)
        if not ok then reply({ok=false, error=tostring(failure)}) end
    end
end
emu.register_frame_done(function() pump(false) end)
-- Frames may stop while paused; the control channel must still service resume,
-- status and shutdown. Periodic callbacks use wall time, not guest execution.
emu.register_periodic(function()
    if machine.paused then
        local safe = checkpoint_pause.grace == 0
        checkpoint_pause.grace = 0
        pump(safe)
    end
end)
