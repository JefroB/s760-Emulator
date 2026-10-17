-- Native-machine control surface. Never writes guest RAM, PC or firmware flags.
local json = require('json')
local channel = emu.file('rw')
local error = channel:open('socket.127.0.0.1:' .. assert(os.getenv('S760_RUNTIME_PORT')))
assert(not error, tostring(error))
local machine = manager.machine
local incoming = ''
local mouse_x, mouse_y, target_x, target_y = 0, 0, 0, 0
local pointer_pending = 0
local value_position, output_level, input_level = 0, 100, 100
local settle = 0
local step_pending = nil
local render_pending = nil
local audio_enabled, audio_chunks, audio_frames = false, {}, 0
local audio_total, audio_dropped = 0, 0
local audio_stream_origin, audio_stream_contiguous = nil, true
local audio_limit = 44100
local midi_pending, midi_delivered, midi_error = 0, {}, ''
local midi_queue = {}
local button_states, external_midi = {}, ''
local checkpoint_pause = {grace=0}
-- Opt-in diagnostic observer. Callbacks return nil and never change bus data.
-- Only the authenticated native client exposes this; it is not a browser action.
local bus_trace = nil
local function start_bus_trace(first, last_address, include_fdc)
    local cpu = machine.devices[':maincpu']
    local space, banks = cpu.spaces['program'], {}
    for i=0,31 do banks[i] = space:read_u8(0x100+i) end
    local trace = {rows={}, dropped=0, accesses=0, polls={}}
    local function observe(kind, address, data, mask)
        if address >= 0x100 and address < 0x120 then
            if kind == 'w' then
                if (mask & 0xff) ~= 0 then banks[address-0x100] = data & 0xff end
                if mask > 0xff and address < 0x11f then banks[address-0xff] = (data >> 8) & 0xff end
            end
            if address < 0x118 then return end
        else
            local slot = 8 + 2*(address >> 14)
            address = ((banks[slot] | (banks[slot+1] << 8)) << 10) + (address & 0x3fff)
            if (address < first or address > last_address)
                and not (include_fdc and (address == 0x102000 or address == 0x102002)) then return end
        end
        trace.accesses = trace.accesses + 1
        -- Aggregate read polls by address/value/PC. Writes retain their order.
        local pc = cpu.state['PC'].value
        local key = kind == 'r' and string.format('%x:%x:%x:%x',address,data,pc,mask) or nil
        local last = key and trace.polls[key] or nil
        if last then
            last.count = last.count + 1
            last.last_seconds = machine.time:as_double()
        elseif #trace.rows < 256 then
            local row = {kind=kind, address=address, data=data, mask=mask,
                pc=pc, seconds=machine.time:as_double(), count=1}
            trace.rows[#trace.rows+1] = row
            if key then trace.polls[key] = row end
        else
            trace.dropped = trace.dropped + 1
        end
    end
    trace.read = space:install_read_tap(0,0xffff,'s760-diagnostic-read',function(a,d,m) observe('r',a,d,m) end)
    trace.write = space:install_write_tap(0,0xffff,'s760-diagnostic-write',function(a,d,m) observe('w',a,d,m) end)
    return trace
end
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
    local first = left.first_sample
    local qualified = type(first) == 'number' and first % 1 == 0 and first >= 0
        and right.first_sample == first and left.sample_rate == 44100 and right.sample_rate == 44100
    left, right = left[1], right[1]
    assert(#left == #right, 'Native speaker channel length mismatch')
    local n = #left
    if n == 0 then return end
    if not qualified then
        audio_stream_origin, audio_stream_contiguous = nil, false
    elseif audio_total == 0 and audio_stream_contiguous then
        audio_stream_origin = first
    elseif audio_stream_origin and first ~= audio_stream_origin + audio_total then
        audio_stream_origin, audio_stream_contiguous = nil, false
    end
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
output_level = field(':NATIVE_OUTPUT','Output Level').user_value
input_level = field(':NATIVE_INPUT','Input Level').user_value
local function send_audio(count, display, input_status)
    local crt, w, h, lcd, lw, lh
    if display then
        crt, w, h = machine.screens[':crt_screen']:pixels()
        lcd, lw, lh = machine.screens[':lcd_screen']:pixels()
    end
    local response = {ok=true, surfaces=display and {{0,w,h},{1,lw,lh}} or nil, output_level=output_level, input_level=input_level,
           audio={frames=count, channels=2, rate=44100,
           first_sample=audio_total-audio_frames, dropped_frames=audio_dropped,
           stream_first_sample=audio_stream_origin and audio_stream_origin+audio_total-audio_frames or nil,
           stream_contiguous=audio_stream_contiguous and audio_stream_origin ~= nil},
           seconds=machine.time:as_double(), buffered_frames=audio_frames-count}
    if input_status then for key,value in pairs(input_status) do response[key]=value end end
    reply(response)
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
    if display then write_all(crt); write_all(lcd) end
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
local function validate_device_clock(rate)
    if rate == nil then return end
    assert(os.getenv('S760_ASIO_CLOCK'), 'Device clock pacing requires ASIO')
    assert(type(rate)=='number' and rate>=0.97 and rate<=1.03, 'Invalid device clock pacing')
end
local function apply_device_clock(rate)
    if rate ~= nil then machine.video.throttle_rate=rate end
end
local function execute(command)
    validate_device_clock(command.clock_rate)
    if command.op == 'checkpoint_save' then
        assert(not bus_trace, 'Stop diagnostic tracing before checkpointing')
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
            pointer_pending=pointer_pending, value_position=value_position, output_level=output_level, input_level=input_level,
            buttons=button_states, enabled=audio_enabled, frames=audio_frames,
            total=audio_total, dropped=audio_dropped,
            stream_origin=audio_stream_origin, stream_contiguous=audio_stream_contiguous})
        local chunks = {}
        for _, chunk in ipairs(audio_chunks) do chunks[#chunks+1] = chunk.data end
        local pcm = table.concat(chunks)
        local file = assert(io.open('runtime-checkpoint.bin', 'wb'))
        assert(file:write(string.pack('<I4I4I4', #meta, #state, #pcm), meta, state, pcm))
        assert(file:close())
        reply({ok=true, bytes=12+#meta+#state+#pcm})
    elseif command.op == 'checkpoint_load' then
        assert(not bus_trace, 'Stop diagnostic tracing before checkpointing')
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
        assert(type(meta.stream_contiguous) == 'boolean'
               and (meta.stream_origin == nil or (type(meta.stream_origin) == 'number'
               and meta.stream_origin % 1 == 0 and meta.stream_origin >= 0)),
               'Invalid checkpoint PCM origin')
        assert(type(meta.mouse) == 'table' and #meta.mouse == 5 and type(meta.buttons) == 'table',
               'Invalid checkpoint input metadata')
        local restored_value, restored_level = meta.value_position or 0, meta.output_level or 100
        assert(type(restored_value) == 'number' and restored_value % 1 == 0 and restored_value >= 0 and restored_value <= 65535
               and type(restored_level) == 'number' and restored_level % 1 == 0 and restored_level >= 0 and restored_level <= 100,
               'Invalid checkpoint dial metadata')
        local restored_input = meta.input_level or 100
        assert(type(restored_input) == 'number' and restored_input % 1 == 0
               and restored_input >= 0 and restored_input <= 100, 'Invalid checkpoint input gain')
        assert(meta.pointer_pending == nil or (type(meta.pointer_pending) == 'number'
               and meta.pointer_pending % 1 == 0 and meta.pointer_pending >= 0 and meta.pointer_pending <= 16),
               'Invalid checkpoint pointer metadata')
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
        pointer_pending = meta.pointer_pending or 0
        value_position, output_level = restored_value, restored_level
        field(':NATIVE_VALUE','Value Encoder'):set_value(value_position)
        field(':NATIVE_OUTPUT','Output Level').user_value = output_level
        input_level = restored_input
        field(':NATIVE_INPUT','Input Level').user_value = input_level
        for _, f in pairs(machine.ioport.ports[':NATIVE_MOUSE_X'].fields) do f:set_value(mouse_x) end
        for _, f in pairs(machine.ioport.ports[':NATIVE_MOUSE_Y'].fields) do f:set_value(mouse_y) end
        audio_enabled,audio_frames,audio_total,audio_dropped = meta.enabled,meta.frames,meta.total,meta.dropped
        audio_stream_origin,audio_stream_contiguous = meta.stream_origin,meta.stream_contiguous
        audio_chunks = a > 0 and {{frames=meta.frames,data=blob:sub(13+m+s)}} or {}
        machine.sounds[':lspeaker'].hook = audio_enabled
        machine.sounds[':rspeaker'].hook = audio_enabled
        -- MAME postload synchronously resumes old waiters with false. Only
        -- after that cancellation do we install and rearm the saved timeline.
        midi_queue,midi_pending = restored_events,#restored_events
        midi_delivered,midi_error = meta.delivered,meta.midi_error
        if midi_pending > 0 then run_midi_queue() end
        reply({ok=true, seconds=machine.time:as_double()})
    elseif command.op == 'bus_trace' then
        assert(machine.paused, 'Pause before changing diagnostic tracing')
        assert(type(command.enabled) == 'boolean', 'Expected diagnostic enabled boolean')
        assert(command.include_fdc == nil or type(command.include_fdc) == 'boolean', 'Expected include_fdc boolean')
        if command.enabled then
            assert(not bus_trace, 'Diagnostic trace is already active')
            local first = command.first == nil and 0x100000 or command.first
            local last = command.last == nil and 0x101fff or command.last
            assert(type(first) == 'number' and first % 1 == 0 and first >= 0x100000
                and type(last) == 'number' and last % 1 == 0 and last <= 0x103fff
                and first <= last, 'Expected inclusive external I/O trace range')
            bus_trace = start_bus_trace(first, last, command.include_fdc == true)
            reply({ok=true, capacity=256})
        else
            assert(bus_trace, 'Diagnostic trace is not active')
            bus_trace.read:remove()
            bus_trace.write:remove()
            -- Each native tap owns its Lua callback, which captures this trace.
            -- Break the trace -> tap references after detaching so the registry
            -- callbacks cannot keep retired taps and their trace rows alive.
            bus_trace.read, bus_trace.write = nil, nil
            reply({ok=true, rows=bus_trace.rows, dropped=bus_trace.dropped, accesses=bus_trace.accesses})
            bus_trace = nil
        end
    elseif command.op == 'input_audio' or command.op == 'input_audio_binary' then
        local binary=command.op=='input_audio_binary'
        assert(os.getenv('S760_NATIVE_ADC'), 'Native ADC input is not enabled')
        assert(command.live == nil or type(command.live) == 'boolean', 'Invalid live input mode')
        assert(command.output == nil or (type(command.output)=='boolean' and command.live==true), 'Invalid duplex input mode')
        assert(machine.paused or command.live == true, 'Pause before queuing offline input PCM')
        assert(command.rate == 44100 and command.channels == 2, 'Input requires 44100Hz stereo PCM16')
        local count
        if binary then
            assert(os.getenv('S760_ASIO_CLOCK'), 'Binary PCM requires ASIO')
            assert(type(command.frames)=='number' and command.frames%1==0 and command.frames>=1 and command.frames<=2048
                and type(command.pcm)=='string' and #command.pcm==command.frames*4, 'Invalid binary PCM packet')
            count=command.frames
        else
            assert(type(command.samples)=='table' and #command.samples > 0
                and #command.samples <= 4096 and #command.samples % 2 == 0, 'Expected 1 to 2048 input frames')
            for _,sample in ipairs(command.samples) do
                assert(type(sample)=='number' and sample % 1 == 0 and sample >= -32768 and sample <= 32767, 'Invalid PCM16 sample')
            end
            count=#command.samples/2
        end
        local depth = machine.ioport.ports[':NATIVE_PCM_DEPTH']:read()
        if command.live and machine.paused then
            reply({ok=true, queued=depth, discarded=count, paused=true})
            return
        end
        if depth + count > 16384 and command.live and command.output then
            -- A full ADC queue must not block draining native output or clock
            -- feedback. Reject the complete input packet, preserving the FIFO.
            apply_device_clock(command.clock_rate)
            send_audio(audio_frames,false,{ok=true,queued=depth,discarded=count,
                underruns=machine.ioport.ports[':NATIVE_PCM_LOSSES']:read()})
            return
        end
        assert(depth + count <= 16384, 'Input PCM queue is full')
        -- Explicit host-only peripheral endpoint, never CPU RAM/wave RAM.
        local ingress = assert(machine.memory.shares[':native_pcm_ingress'])
        for i=1,count*2 do
            local sample=binary and string.unpack('<I2',command.pcm,(i-1)*2+1) or command.samples[i]
            ingress:write_u16(i*2,sample & 0xffff)
        end
        ingress:write_u16(0,count) -- publish only after complete validation/write
        local queued = machine.ioport.ports[':NATIVE_PCM_DEPTH']:read()
        assert(queued == depth + count, 'Native ADC input is not enabled')
        local status={ok=true, queued=queued, underruns=machine.ioport.ports[':NATIVE_PCM_LOSSES']:read()}
        apply_device_clock(command.clock_rate)
        if command.output then send_audio(audio_frames,false,status) else reply(status) end
    elseif command.op == 'input_status' then
        reply({ok=true, queued=machine.ioport.ports[':NATIVE_PCM_DEPTH']:read(),
            underruns=machine.ioport.ports[':NATIVE_PCM_LOSSES']:read()})
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
        audio_stream_origin, audio_stream_contiguous = nil, true
        reply({ok=true})
    elseif command.op == 'audio' then
        assert(audio_enabled, 'Enable audio capture first')
        apply_device_clock(command.clock_rate)
        send_audio(audio_frames)
    elseif command.op == 'device_clock' then
        assert(command.clock_rate ~= nil, 'Missing device clock pacing')
        apply_device_clock(command.clock_rate)
        reply({ok=true, clock_rate=machine.video.throttle_rate})
    elseif command.op == 'render' then
        assert(machine.paused and audio_enabled, 'Render requires paused machine and enabled capture')
        assert(type(command.frames) == 'number' and command.frames % 1 == 0
               and command.frames >= 1 and command.frames <= 8192, 'Invalid render frame count')
        assert(audio_dropped == 0, 'Restart capture after an audio discontinuity')
        assert(command.display == nil or type(command.display) == 'boolean', 'Invalid display request')
        if command.input_samples ~= nil then
            assert(os.getenv('S760_NATIVE_ADC'), 'Native ADC input is not enabled')
            local samples=command.input_samples
            assert(type(samples)=='table' and #samples==command.frames*2, 'Invalid render input size')
            for _,sample in ipairs(samples) do
                assert(type(sample)=='number' and sample%1==0 and sample>=-32768 and sample<=32767, 'Invalid PCM16 sample')
            end
            local depth=machine.ioport.ports[':NATIVE_PCM_DEPTH']:read()
            assert(depth+command.frames<=16384, 'Input PCM queue is full')
            local ingress=assert(machine.memory.shares[':native_pcm_ingress'])
            for first=0,command.frames-1,2048 do
                local count=math.min(2048,command.frames-first)
                for i=1,count*2 do ingress:write_u16(i*2,samples[first*2+i] & 0xffff) end
                ingress:write_u16(0,count)
                depth=depth+count
                assert(machine.ioport.ports[':NATIVE_PCM_DEPTH']:read()==depth, 'Native ADC input is not enabled')
            end
        end
        render_pending = {frames=command.frames, steps=0, display=command.display}
    elseif command.op == 'frames' then
        local crt, w, h = machine.screens[':crt_screen']:pixels()
        local lcd, lw, lh = machine.screens[':lcd_screen']:pixels()
        local registers = machine.devices[':maincpu'].spaces['register']
        reply({ok=true, surfaces={{0,w,h},{1,lw,lh}}, seconds=machine.time:as_double(), paused=machine.paused, output_level=output_level, input_level=input_level,
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
    elseif command.op == 'dial' then
        assert((command.id == 'ALPHA' or command.id == 'VOLUME' or command.id == 'INPUT') and type(command.delta) == 'number'
               and command.delta % 1 == 0 and math.abs(command.delta) <= 32, 'Invalid native dial input')
        if command.id == 'ALPHA' then
            value_position = (value_position + command.delta) % 65536
            field(':NATIVE_VALUE','Value Encoder'):set_value(value_position)
        elseif command.id == 'INPUT' then
            input_level = math.max(0, math.min(100, input_level + command.delta))
            field(':NATIVE_INPUT','Input Level').user_value = input_level
        else
            output_level = math.max(0, math.min(100, output_level + command.delta))
            field(':NATIVE_OUTPUT','Output Level').user_value = output_level
        end
        reply({ok=true, value_position=value_position, output_level=output_level, input_level=input_level})
    elseif command.op == 'pointer' then
        assert(type(command.x) == 'number' and command.x >= 0 and command.x <= 320, 'Invalid pointer X')
        assert(type(command.y) == 'number' and command.y >= 0 and command.y <= 120, 'Invalid pointer Y')
        target_x, target_y = command.x, command.y
        pointer_pending = 16
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
local function update_pointer()
    -- OS 2.24 bank004F:88AB..892F moves/clamps the cursor and selects 1x
    -- or 2x sensitivity. Panel operations can also relocate it. Translate
    -- absolute host coordinates using read-only guest position/sensitivity;
    -- all movement still goes through ordinary MU-1 relative input packets.
    -- Never keep chasing an old target after the request has settled.
    if settle > 0 and not machine.paused then
        settle = settle - 1
    elseif pointer_pending > 0 and not machine.paused then
        local registers = machine.devices[':maincpu'].spaces['register']
        local program = machine.devices[':maincpu'].spaces['program']
        local scale = (program:read_u8(0x2140) == 0 and program:read_u8(0x272e) == 0) and 2 or 1
        local function delta(target, current, low, high)
            local distance = math.max(low, math.min(high, target * 2)) - current
            -- At 2x sensitivity the guest may be on the opposite pixel parity.
            -- Truncate toward zero: nearest reachable pixel without oscillation.
            local amount = distance / scale
            amount = amount < 0 and math.ceil(amount) or math.floor(amount)
            return math.max(-63, math.min(63, amount))
        end
        local dx = delta(target_x, registers:read_u16(0xd0), program:read_u16(0x213a), program:read_u16(0x2138))
        local dy = delta(target_y, registers:read_u8(0xd2), program:read_u16(0x213e), program:read_u16(0x213c))
        pointer_pending = (dx == 0 and dy == 0) and 0 or pointer_pending - 1
        mouse_x = (mouse_x + dx) & 0xffff
        mouse_y = (mouse_y + dy) & 0xffff
        for _, f in pairs(machine.ioport.ports[':NATIVE_MOUSE_X'].fields) do f:set_value(mouse_x) end
        for _, f in pairs(machine.ioport.ports[':NATIVE_MOUSE_Y'].fields) do f:set_value(mouse_y) end
        settle = (dx == 0 and dy == 0) and 0 or 2
    end
end
local function pump(outside_timeslice)
    update_pointer()
    if render_pending then
        if audio_dropped > 0 then
            emu.pause()
            render_pending = nil
            reply({ok=false, error='Audio overflow during render'})
        elseif audio_frames >= render_pending.frames then
            emu.pause()
            local count, display = render_pending.frames, render_pending.display
            render_pending = nil
            send_audio(count, display)
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
    -- A 2048-frame stereo PCM16 JSON packet can exceed 24KB. Reading only
    -- 4KB/frame caps transport below 44.1kHz even when the host keeps up.
    -- One bounded packet per frame remains the execution limit.
    incoming = incoming .. channel:read(65536)
    if #incoming > 65536 then machine:exit(); return end
    local newline = incoming:find('\n', 1, true)
    -- At most one command per frame: bounded work, no unbounded input drain.
    if newline then
        local text = incoming:sub(1, newline - 1)
        local command = json.parse(text)
        local consumed=newline
        if command and command.op=='input_audio_binary' then
            local frames=command.frames
            if type(frames)~='number' or frames%1~=0 or frames<1 or frames>2048 then
                reply({ok=false,error='Invalid binary PCM framing'});machine:exit();return
            end
            if #incoming<newline+frames*4 then return end
            command.pcm=incoming:sub(newline+1,newline+frames*4)
            consumed=newline+frames*4
        end
        -- Peripheral PCM delivery must continue while ordinary mouse packets
        -- settle. Keep the existing serialization for all other commands.
        if not ((settle == 0 and pointer_pending == 0) or machine.paused
            or (command and (command.op=='audio' or ((command.op == 'input_audio' or command.op=='input_audio_binary') and command.live == true)))) then return end
        -- frame_done may run inside an emulated timer callback. Loading there
        -- lets the old callback's return path overwrite restored timer state;
        -- saving there can capture a timer before it has been rescheduled.
        -- Service buffer checkpoints only from the paused wall-time callback.
        if command and (command.op == 'checkpoint_save' or command.op == 'checkpoint_load')
           and machine.paused and not outside_timeslice then return end
        incoming = incoming:sub(consumed + 1)
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
