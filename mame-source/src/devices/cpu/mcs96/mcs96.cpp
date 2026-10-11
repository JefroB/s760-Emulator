// license:BSD-3-Clause
// copyright-holders:Olivier Galibert
/***************************************************************************

    mcs96.h

    MCS96, 8098/8398/8798 branch

***************************************************************************/

#include "emu.h"
#include "mcs96.h"

#include "endianness.h"

mcs96_device::mcs96_device(const machine_config &mconfig, device_type type, const char *tag, device_t *owner, uint32_t clock, int data_width, address_map_constructor regs_map) :
	cpu_device(mconfig, type, tag, owner, clock),
	program_config("program", ENDIANNESS_LITTLE, data_width, 16),
	regs_config("register", ENDIANNESS_LITTLE, 16, 8, 0, regs_map),
	program(nullptr), regs(nullptr), register_file(*this, "register_file"),
	icount(0), bcount(0), inst_state(0), cycles_scaling(0), pending_irq(0),
	PC(0), PPC(0), PSW(0), OP1(0), OP2(0), OP3(0), OPI(0), TMP(0), irq_requested(false)
{
}

void mcs96_device::device_start()
{
	program = &space(AS_PROGRAM);
	if(program->data_width() == 8) {
		program->cache(m_cache8);
		m_pr8 = [this](offs_t address) -> u8 { return m_cache8.read_byte(address); };
	} else {
		program->cache(m_cache16);
		m_pr8 = [this](offs_t address) -> u8 { return m_cache16.read_byte(address); };
	}
	regs = &space(AS_DATA);

	set_icountptr(icount);

	auto register_file_bytes = util::little_endian_cast<u8>(register_file.target());
	state_add(STATE_GENPC,     "GENPC",     PC).noshow();
	state_add(STATE_GENPCBASE, "CURPC",     PPC).noshow();
	state_add(STATE_GENFLAGS,  "GENFLAGS",  PSW).formatstr("%16s").noshow();
	state_add(MCS96_PC,        "PC",        PC);
	state_add(MCS96_PSW,       "PSW",       PSW);
	state_add(MCS96_INT_PENDING, "INT_PENDING", pending_irq);
	state_add(MCS96_SP,        "SP",        register_file[0]);
	state_add(MCS96_AX,        "AX",        register_file[2]);
	state_add(MCS96_DX,        "DX",        register_file[3]);
	state_add(MCS96_BX,        "BX",        register_file[4]);
	state_add(MCS96_CX,        "CX",        register_file[5]);
	state_add(MCS96_AL,        "AL",        register_file_bytes[4]).noshow();
	state_add(MCS96_AH,        "AH",        register_file_bytes[5]).noshow();
	state_add(MCS96_DL,        "DL",        register_file_bytes[6]).noshow();
	state_add(MCS96_DH,        "DH",        register_file_bytes[7]).noshow();
	state_add(MCS96_BL,        "BL",        register_file_bytes[8]).noshow();
	state_add(MCS96_BH,        "BH",        register_file_bytes[9]).noshow();
	state_add(MCS96_CL,        "CL",        register_file_bytes[10]).noshow();
	state_add(MCS96_CH,        "CH",        register_file_bytes[11]).noshow();

	save_item(NAME(inst_state));
	save_item(NAME(pending_irq));
	save_item(NAME(PC));
	save_item(NAME(PPC));
	save_item(NAME(PSW));
	save_item(NAME(OP1));
	save_item(NAME(OP2));
	save_item(NAME(OP3));
	save_item(NAME(OPI));
	save_item(NAME(TMP));
	save_item(NAME(irq_requested));
	save_item(NAME(m_pending1));
	save_item(NAME(m_mask1));
	save_item(NAME(m_wsr));
}

void mcs96_device::device_reset()
{
	m_pending1 = m_mask1 = m_wsr = 0;
	PC = m_reset_pc;
	PPC = PC;
	PSW = 0;
	irq_requested = false;
	inst_state = STATE_FETCH;
}

uint32_t mcs96_device::execute_min_cycles() const noexcept
{
	return 4;
}

uint32_t mcs96_device::execute_max_cycles() const noexcept
{
	return 33;
}

void mcs96_device::recompute_bcount(uint64_t event_time)
{
	if(!event_time || event_time >= total_cycles() + icount) {
		bcount = 0;
		return;
	}
	bcount = total_cycles() + icount - event_time;
}

void mcs96_device::check_irq()
{
	irq_requested = ((PSW & pending_irq) || (m_kb_mode && (m_pending1 & m_mask1 & 0x7f))) && (PSW & F_I);
}

void mcs96_device::take_interrupt()
{
 int level = 7;
 if (m_kb_mode && (m_pending1 & m_mask1 & 0x7f)) {
  for (level = 14; level >= 8 && !(m_pending1 & m_mask1 & (1 << (level-8))); --level) {}
  m_pending1 &= ~(1 << (level-8));
 } else {
  for (; level >= 0 && !(PSW & pending_irq & (1 << level)); --level) {}
  if (level != 7 || m_kb_mode) pending_irq &= ~(1 << level);
 }
 OP1 = level;
 standard_irq_callback(OP1, PC);
 TMP = reg_r16(0x18)-2;
 reg_w16(0x18, TMP);
 any_w16(TMP, PC);
 const u16 vector = level < 8 ? 0x2000+2*level : 0x2030+2*(level-8);
 const u16 target = any_r16(vector);
 if (m_kb_mode) logerror("[KBIRQ] level=%d vector=%04x target=%04x return=%04x SP=%04x\n",level,vector,target,PC,u16(TMP));
 PC = target;
 check_irq();
}

void mcs96_device::kb_push_flags(bool all)
{
 u16 sp = reg_r16(0x18)-2;
 any_w16(sp, PSW);
 PSW = 0;
 if (all) {
  sp -= 2;
  any_w16(sp, u16(m_mask1) | (u16(m_wsr) << 8));
  m_mask1 = 0;
  m_wsr = 0;
 }
 reg_w16(0x18, sp);
 check_irq();
}

void mcs96_device::kb_pop_flags(bool all)
{
 u16 sp = reg_r16(0x18);
 if (all) {
  const u16 saved = any_r16(sp);
  m_mask1 = u8(saved);
  m_wsr = u8(saved >> 8);
  sp += 2;
 }
 PSW = any_r16(sp);
 reg_w16(0x18, sp+2);
 check_irq();
}

void mcs96_device::int_mask_w(u8 data)
{
	PSW = (PSW & 0xff00) | data;
	check_irq();
}

u8 mcs96_device::int_mask_r()
{
	return PSW;
}

void mcs96_device::int_pending_w(u8 data)
{
	pending_irq = data;
	check_irq();
}

u8 mcs96_device::int_pending_r()
{
	return pending_irq;
}

void mcs96_device::execute_run()
{
	internal_update(total_cycles());

	//  if(inst_substate)
	//      do_exec_partial();

	while(icount > 0) {
		while(icount > bcount) {
			int picount = inst_state >= 0x200 ? -1 : icount;
			do_exec_full();
			if(icount == picount) {
				fatalerror("Unhandled %x (%04x)\n", inst_state, PPC);
			}
		}
		while(bcount && icount <= bcount)
			internal_update(total_cycles() + icount - bcount);
		//      if(inst_substate)
		//          do_exec_partial();
	}
}

device_memory_interface::space_config_vector mcs96_device::memory_space_config() const
{
	return space_config_vector {
		std::make_pair(AS_PROGRAM, &program_config),
		std::make_pair(AS_DATA, &regs_config)
	};
}

void mcs96_device::state_import(const device_state_entry &entry)
{
}

void mcs96_device::state_export(const device_state_entry &entry)
{
}

void mcs96_device::state_string_export(const device_state_entry &entry, std::string &str) const
{
	switch(entry.index()) {
	case STATE_GENFLAGS:
	case MCS96_PSW:
		str = string_format("%c%c%c%c%c%c%c %c%c%c%c%c%c%c%c",
						PSW & F_Z  ? 'Z' : '.',
						PSW & F_N  ? 'N' : '.',
						PSW & F_V  ? 'V' : '.',
						PSW & F_VT ? 'v' : '.',
						PSW & F_C  ? 'C' : '.',
						PSW & F_I  ? 'I' : '.',
						PSW & F_ST ? 'S' : '.',
						PSW & 0x80 ? '7' : '.',
						PSW & 0x40 ? '6' : '.',
						PSW & 0x20 ? '5' : '.',
						PSW & 0x10 ? '4' : '.',
						PSW & 0x08 ? '3' : '.',
						PSW & 0x04 ? '2' : '.',
						PSW & 0x02 ? '1' : '.',
						PSW & 0x01 ? '0' : '.');
		break;
	}
}

void mcs96_device::reg_w8(u8 adr, u8 data)
{
	regs->write_byte(adr, data);
}

void mcs96_device::reg_w16(u8 adr, u16 data)
{
	regs->write_word(adr & 0xfe, data);
}

uint8_t mcs96_device::reg_r8(uint8_t adr)
{
	return regs->read_byte(adr);
}

uint16_t mcs96_device::reg_r16(uint8_t adr)
{
	return regs->read_word(adr & 0xfe);
}

void mcs96_device::any_w8(u16 adr, u8 data)
{
	s760_write_log("W8", adr, data);
	if (adr < 0x100)
		regs->write_byte(adr, data);
	else
		program->write_byte(adr, data);
}

void mcs96_device::any_w16(u16 adr, u16 data)
{
	adr &= 0xfffe;
	s760_write_log("W16", adr, data);
	if (adr < 0x100)
		regs->write_word(adr, data);
	else
		program->write_word(adr, data);
}

// S-760 finding 50 (ChatGPT review 49): write-aware trace. ChatGPT 49 correctly
// noted finding 48 sampled selectors only at READS and never watched WRITES, so
// it could not distinguish "redundant selection" (OS writes 0x010C the same
// value) from "no selection", nor confirm the 0x00B1 service dispatch at the
// 0x2AAE edge-detector. This logs WRITES to the selector words 0x0100-0x010F and
// to the specific addresses in that routine (0x23A0 source, 0x8F98 shadow,
// 0x0104 service selector, 0x2964 flag). Pure logging; env S760_INTENT_TRACE.
void mcs96_device::s760_write_log(const char *kind, u16 adr, u16 data)
{
	static const bool boot_probe = getenv("S760_BOOT_PROBE") != nullptr;
	static unsigned boot_probe_count = 0;
	if (boot_probe && boot_probe_count < 80 &&
		(adr == 0x0104 || (adr >= 0x2a88 && adr <= 0x2a99)))
	{
		logerror("[BOOTPROBE] %s PPC=%04x PC=%04x adr=%04x value=%04x RW1C=%04x code2A90=%02x %02x %02x %02x %02x %02x %02x %02x %02x\n",
			kind, PPC, PC, adr, data, reg_r16(0x1c),
			program->read_byte(0x2a90), program->read_byte(0x2a91),
			program->read_byte(0x2a92), program->read_byte(0x2a93),
			program->read_byte(0x2a94), program->read_byte(0x2a95),
			program->read_byte(0x2a96), program->read_byte(0x2a97),
			program->read_byte(0x2a98));
		boot_probe_count++;
	}
	static int s_on = -1;
	if (s_on < 0)
		s_on = (getenv("S760_INTENT_TRACE") != nullptr) ? 1 : 0;
	if (!s_on)
		return;
	const bool selword = (adr >= 0x0100 && adr <= 0x010F);
	const bool watched  = (adr == 0x23A0 || adr == 0x8F98 || adr == 0x2964);
	if (!selword && !watched)
		return;
	static u32 s_wcount = 0;
	if (s_wcount >= 4000)
		return;
	logerror("[WRITE %s] n=%u PC=%04x adr=%04x data=%04x\n", kind, s_wcount, PPC, adr, data);
	s_wcount++;
}

// S-760 finding 48 (ChatGPT review 47): OBSERVATIONAL, intent-labelled capture of
// program-space accesses in the 0x8000-0xBFFF window at the CPU's REAL seams --
// data/operand reads flow through any_r8/any_r16 (below); instruction fetches
// flow through read_pc()->m_pr8 (see header). This logs the TRUE access intent
// (not a PC heuristic) plus the four data-selector words 0x0108/0x010A/0x010C/
// 0x010E, so we can see whether data reads here actually track a selector.
// NO BEHAVIOR CHANGE: pure logging, gated by env S760_INTENT_TRACE. Writes are
// intentionally NOT substituted; this is baseline observation only.
void mcs96_device::s760_intent_log(const char *kind, u16 adr, u16 val)
{
	static const bool boot_fetch = getenv("S760_BOOT_PROBE") != nullptr;
	static u16 boot_history[16] = {};
	static unsigned boot_history_pos = 0, boot_history_dumps = 0;
	static unsigned boot_instruction_count = 0;
	if (boot_fetch && kind[0] == 'F' && adr == PPC)
	{
		if (++boot_instruction_count % 1000000 == 0 && boot_instruction_count <= 20000000)
			logerror("[BOOTPROGRESS] instructions=%u PPC=%04x SP=%04x queue=%04x/%04x\n",
				boot_instruction_count, PPC, reg_r16(0x18), program->read_word(0x21ac), program->read_word(0x21ae));
		if (adr == 0x2a94 && boot_history_dumps++ < 4)
			for (unsigned i = 0; i < 16; ++i)
				logerror("[BOOTPATH] slot=%u previous=%04x\n", i, boot_history[(boot_history_pos + i) & 15]);
		boot_history[boot_history_pos++ & 15] = adr;
	}
	static unsigned boot_fetch_count = 0;
	if (boot_fetch && kind[0] == 'F' && adr >= 0x2a80 && adr <= 0x2aa0 && boot_fetch_count++ < 120)
		logerror("[BOOTFETCH] PPC=%04x adr=%04x val=%02x RW1C=%04x\n", PPC, adr, val, reg_r16(0x1c));
	static int s_on = -1;
	if (s_on < 0)
		s_on = (getenv("S760_INTENT_TRACE") != nullptr) ? 1 : 0;
	if (!s_on)
		return;
	// 0x8000-0xBFFF window (finding 48) PLUS the specific edge-detector operands
	// 0x23A0 (source) that finding 49 asked to observe. 0x8F98 is already in the
	// window range.
	const bool inwin = (adr >= 0x8000 && adr <= 0xBFFF);
	if (!inwin && adr != 0x23A0)
		return;
	static u32 s_count = 0;
	if (s_count >= 4000)
		return;
	// Selector words live at >=0x100, so read them straight from program space.
	const u16 s0108 = program->read_word(0x0108);
	const u16 s010a = program->read_word(0x010A);
	const u16 s010c = program->read_word(0x010C);
	const u16 s010e = program->read_word(0x010E);
	logerror("[INTENT %s] n=%u PC=%04x adr=%04x val=%04x sel[0108/0A/0C/0E]=%04x %04x %04x %04x\n",
		kind, s_count, PPC, adr, val, s0108, s010a, s010c, s010e);
	s_count++;
}

u8 mcs96_device::any_r8(u16 adr)
{
	if (adr < 0x100)
		return regs->read_byte(adr);
	else {
		u8 v = program->read_byte(adr);
		s760_intent_log("DATA8", adr, v);
		return v;
	}
}

u16 mcs96_device::any_r16(u16 adr)
{
	adr &= 0xfffe;
	if (adr < 0x100)
		return regs->read_word(adr);
	else {
		u16 v = program->read_word(adr);
		s760_intent_log("DATA16", adr, v);
		return v;
	}
}

bool mcs96_device::memory_translate(int spacenum, int intention, offs_t &address, address_space *&target_space)
{
	if (spacenum == AS_PROGRAM && intention != TR_FETCH && address < 0x100)
		target_space = regs;
	else
		target_space = &space(spacenum);
	return true;
}

uint8_t mcs96_device::do_addb(uint8_t v1, uint8_t v2)
{
	uint16_t sum = v1+v2;
	PSW &= ~(F_Z|F_N|F_C|F_V);
	if(!uint8_t(sum))
		PSW |= F_Z;
	else if(int8_t(sum) < 0)
		PSW |= F_N;
	if(~(v1^v2) & (v1^sum) & 0x80)
		PSW |= F_V|F_VT;
	if(sum & 0xff00)
		PSW |= F_C;
	return sum;
}

uint16_t mcs96_device::do_add(uint16_t v1, uint16_t v2)
{
	uint32_t sum = v1+v2;
	PSW &= ~(F_Z|F_N|F_C|F_V);
	if(!uint16_t(sum))
		PSW |= F_Z;
	else if(int16_t(sum) < 0)
		PSW |= F_N;
	if(~(v1^v2) & (v1^sum) & 0x8000)
		PSW |= F_V|F_VT;
	if(sum & 0xffff0000)
		PSW |= F_C;
	return sum;
}

uint8_t mcs96_device::do_subb(uint8_t v1, uint8_t v2)
{
	uint16_t diff = v1 - v2;
	PSW &= ~(F_N|F_V|F_Z|F_C);
	if(!uint8_t(diff))
		PSW |= F_Z;
	else if(int8_t(diff) < 0)
		PSW |= F_N;
	if((v1^v2) & (v1^diff) & 0x80)
		PSW |= F_V;
	if(!(diff & 0xff00))
		PSW |= F_C;
	return diff;
}

uint16_t mcs96_device::do_sub(uint16_t v1, uint16_t v2)
{
	uint32_t diff = v1 - v2;
	PSW &= ~(F_N|F_V|F_Z|F_C);
	if(!uint16_t(diff))
		PSW |= F_Z;
	else if(int16_t(diff) < 0)
		PSW |= F_N;
	if((v1^v2) & (v1^diff) & 0x8000)
		PSW |= F_V;
	if(!(diff & 0xffff0000))
		PSW |= F_C;
	return diff;
}

uint8_t mcs96_device::do_addcb(uint8_t v1, uint8_t v2)
{
	uint16_t sum = v1+v2+(PSW & F_C ? 1 : 0);
	PSW &= ~(F_Z|F_N|F_C|F_V);
	if(!uint8_t(sum))
		PSW |= F_Z;
	else if(int8_t(sum) < 0)
		PSW |= F_N;
	if(~(v1^v2) & (v1^sum) & 0x80)
		PSW |= F_V|F_VT;
	if(sum & 0xff00)
		PSW |= F_C;
	return sum;
}

uint16_t mcs96_device::do_addc(uint16_t v1, uint16_t v2)
{
	uint32_t sum = v1+v2+(PSW & F_C ? 1 : 0);
	PSW &= ~(F_Z|F_N|F_C|F_V);
	if(!uint16_t(sum))
		PSW |= F_Z;
	else if(int16_t(sum) < 0)
		PSW |= F_N;
	if(~(v1^v2) & (v1^sum) & 0x8000)
		PSW |= F_V|F_VT;
	if(sum & 0xffff0000)
		PSW |= F_C;
	return sum;
}

uint8_t mcs96_device::do_subcb(uint8_t v1, uint8_t v2)
{
	uint16_t diff = v1 - v2 - (PSW & F_C ? 0 : 1);
	PSW &= ~(F_N|F_V|F_Z|F_C);
	if(!uint8_t(diff))
		PSW |= F_Z;
	else if(int8_t(diff) < 0)
		PSW |= F_N;
	if((v1^v2) & (v1^diff) & 0x80)
		PSW |= F_V;
	if(!(diff & 0xff00))
		PSW |= F_C;
	return diff;
}

uint16_t mcs96_device::do_subc(uint16_t v1, uint16_t v2)
{
	uint32_t diff = v1 - v2 - (PSW & F_C ? 0 : 1);
	PSW &= ~(F_N|F_V|F_Z|F_C);
	if(!uint16_t(diff))
		PSW |= F_Z;
	else if(int16_t(diff) < 0)
		PSW |= F_N;
	if((v1^v2) & (v1^diff) & 0x8000)
		PSW |= F_V;
	if(!(diff & 0xffff0000))
		PSW |= F_C;
	return diff;
}

void mcs96_device::set_nz8(uint8_t v)
{
	PSW &= ~(F_N|F_V|F_Z|F_C);
	if(!v)
		PSW |= F_Z;
	else if(int8_t(v) < 0)
		PSW |= F_N;
}

void mcs96_device::set_nz16(uint16_t v)
{
	PSW &= ~(F_N|F_V|F_Z|F_C);
	if(!v)
		PSW |= F_Z;
	else if(int16_t(v) < 0)
		PSW |= F_N;
}

#include "cpu/mcs96/mcs96.hxx"
