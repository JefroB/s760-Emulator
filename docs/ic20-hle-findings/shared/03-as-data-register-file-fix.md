# Finding 03 — Critical MCS-96 Register File Space Fix: AS_DATA vs. AS_PROGRAM

**Author:** Gemini  
**Status:** SHARED / FINAL  
**Date:** 2026-10-09  
**Driver Target:** `mame-source/src/mame/roland/s760.cpp` (`ic20_hle_install`)  
**Core Target:** `mame-source/src/devices/cpu/mcs96/mcs96.cpp`

---

## 1. Executive Summary & Root Cause

In `ic20_hle_install()` inside [`s760.cpp`](file:///d:/S-760/mame-source/src/mame/roland/s760.cpp), Kiro's HLE hook attempted to return the output pointer `RW4E` to the OS by writing:

```cpp
address_space &p = m_maincpu->space(AS_PROGRAM);
p.write_word(0x4E, bufptr);
p.write_byte(bufptr, 0x7F);
```

**The Bug:**
In MAME's `mcs96_device`, the on-chip register file (`0x00..0xFF`, containing registers `RW4E`, `RW4C`, `R4A`, `RW1E`) lives in **`AS_DATA`**, NOT `AS_PROGRAM`!
Source confirmation in `mame-source/src/devices/cpu/mcs96/mcs96.cpp`:
```cpp
device_memory_interface::space_config_vector mcs96_device::memory_space_config() const
{
    return space_config_vector {
        std::make_pair(AS_PROGRAM, &program_config),
        std::make_pair(AS_DATA, &regs_config)
    };
}
```
And inside `any_r16` / `any_w16`:
```cpp
void mcs96_device::any_w16(u16 adr, u16 data)
{
    adr &= 0xfffe;
    if (adr < 0x100)
        regs->write_word(adr, data); // regs == AS_DATA!
    else
        program->write_word(adr, data);
}
```

### Consequences:
1. `p.write_word(0x4E, bufptr)` wrote to the `.ram()` work RAM buffer in `AS_PROGRAM`, leaving the CPU's register `RW4E` untouched in `AS_DATA`.
2. When the OS executed `BA0C: LDB RDA, [RW4E]`, the CPU read the address from register `RW4E` in `AS_DATA` (which was uninitialized/zero).
3. The CPU read byte `[0x0000]` instead of `[bufptr]`, saw `0x00`, and `CMPB RDA, #0x7F` failed (`JNE 0xBA1D` or `0xBA50`).
4. The OS treated all 960 resource entries (Performances, Patches, Partials, Samples) as absent and failed to build the directory correctly!

---

## 2. The Remediation in `s760.cpp`

To properly service the IC20 HLE:
- **Register file accesses (`< 0x100`):** Must use `m_maincpu->space(AS_DATA)`.
- **Buffer memory accesses (`>= 0x100`):** Must use `m_maincpu->space(AS_PROGRAM)`.

### Corrected Code for `s760_state::ic20_hle_install()`:

```cpp
m_ic20_tap = prog.install_write_tap(
    0x0104, 0x0105, "ic20_dispatch",
    [this](offs_t offset, u16 &data, u16 mem_mask)
    {
        if (offset != 0x0104)
            return;
        address_space &prog_space = m_maincpu->space(AS_PROGRAM);
        address_space &data_space = m_maincpu->space(AS_DATA);

        const u16 selector = data;
        const u8  type     = data_space.read_byte(0x4A); // R4A
        const u16 index    = data_space.read_word(0x4C); // RW4C
        const u16 bufptr   = data_space.read_word(0x1E); // RW1E

        if (selector == 0x4B)
        {
            // Point the register RW4E in AS_DATA to the scratch buffer in AS_PROGRAM:
            data_space.write_word(0x4E, bufptr);

            // Write valid header marker 0x7F to the scratch buffer in AS_PROGRAM:
            prog_space.write_byte(bufptr, 0x7F);
        }

        logerror("[IC20] sel=0x%04X type=%u index=0x%04X buf=0x%04X PC=0x%04X\n",
            selector, type, index, bufptr, m_maincpu->pc());
    },
    &m_ic20_tap);
```
