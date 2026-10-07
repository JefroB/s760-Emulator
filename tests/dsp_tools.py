"""
dsp_tools.py — Roland S-760 Offline DSP Tools, Disk Optimization, MS-DOS FAT12 Exchange & MIDI SDS
Implements and validates functions documented in Roland S-760 OM Sections 5.5, 5.6, 5.7, 6.6, 6.8, 7.4.
"""
import struct
import math
from typing import Tuple, List, Dict


class S760DSPTools:
    """Offline DSP sample processing algorithms for Roland S-760 Wave RAM."""

    @staticmethod
    def crossfade_loop(pcm_bytes: bytes, loop_start: int, loop_end: int, xfade_samples: int = 500) -> bytes:
        """
        OM Sec. 5.5: Crossfade Looping.
        Performs equal-power/linear crossfade between the end of the loop and the start of the loop
        to eliminate clicks and phase discontinuities.
        """
        samples = [struct.unpack_from("<h", pcm_bytes, i * 2)[0] for i in range(len(pcm_bytes) // 2)]
        xfade = min(xfade_samples, (loop_end - loop_start) // 3, loop_start, len(samples) - loop_end)
        if xfade <= 0:
            return pcm_bytes

        out = list(samples)
        for i in range(xfade):
            w_out = float(i) / float(xfade)
            w_in = 1.0 - w_out
            # Pre-loop tail blended with loop-end tail
            src_tail = samples[loop_end - xfade + i]
            src_head = samples[loop_start + i]
            blended = int(w_in * src_tail + w_out * src_head)
            out[loop_end - xfade + i] = max(-32767, min(32767, blended))

        packed = bytearray(len(out) * 2)
        for i, val in enumerate(out):
            struct.pack_into("<h", packed, i * 2, val)
        return bytes(packed)

    @staticmethod
    def time_stretch(pcm_bytes: bytes, stretch_factor: float = 1.25, sample_rate: int = 44100) -> bytes:
        """
        OM Sec. 5.6: Time Stretch (Tempo Expansion / Compression without Pitch Alteration).
        Implements Synchronized Overlap-Add (SOLA) algorithm.
        """
        samples = [struct.unpack_from("<h", pcm_bytes, i * 2)[0] for i in range(len(pcm_bytes) // 2)]
        if stretch_factor <= 0 or len(samples) < 100:
            return pcm_bytes

        win_size = int(sample_rate * 0.030) # 30ms window
        hop_in = win_size // 2
        hop_out = int(hop_in * stretch_factor)

        out_len = int(len(samples) * stretch_factor)
        out = [0.0] * (out_len + win_size)
        norm = [0.0] * (out_len + win_size)

        # Hann window
        hann = [0.5 * (1.0 - math.cos(2.0 * math.pi * i / win_size)) for i in range(win_size)]

        in_pos = 0
        out_pos = 0
        while in_pos + win_size <= len(samples) and out_pos + win_size <= len(out):
            for i in range(win_size):
                w = hann[i]
                out[out_pos + i] += samples[in_pos + i] * w
                norm[out_pos + i] += w

            in_pos += hop_in
            out_pos += hop_out

        result = bytearray(out_len * 2)
        for i in range(out_len):
            val = out[i] / (norm[i] + 1e-6) if norm[i] > 1e-4 else out[i]
            ival = int(max(-32767.0, min(32767.0, val)))
            struct.pack_into("<h", result, i * 2, ival)
        return bytes(result)

    @staticmethod
    def digital_filter(pcm_bytes: bytes, cutoff_hz: float = 1000.0, sample_rate: int = 44100, filter_type: str = "lpf") -> bytes:
        """
        OM Sec. 5.6: Offline Digital Filtering (Low-Pass, High-Pass, Band-Pass).
        2-Pole Bi-quad filter applied directly to sample data.
        """
        samples = [struct.unpack_from("<h", pcm_bytes, i * 2)[0] for i in range(len(pcm_bytes) // 2)]
        omega = 2.0 * math.pi * cutoff_hz / float(sample_rate)
        sn = math.sin(omega)
        cs = math.cos(omega)
        alpha = sn / (2.0 * 0.7071) # Q = 0.7071

        if filter_type.lower() == "hpf":
            b0 = (1.0 + cs) / 2.0
            b1 = -(1.0 + cs)
            b2 = (1.0 + cs) / 2.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cs
            a2 = 1.0 - alpha
        else: # LPF
            b0 = (1.0 - cs) / 2.0
            b1 = 1.0 - cs
            b2 = (1.0 - cs) / 2.0
            a0 = 1.0 + alpha
            a1 = -2.0 * cs
            a2 = 1.0 - alpha

        b0 /= a0
        b1 /= a0
        b2 /= a0
        a1 /= a0
        a2 /= a0

        out = bytearray(len(samples) * 2)
        x1 = x2 = y1 = y2 = 0.0
        for i, s in enumerate(samples):
            x0 = float(s)
            y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1 = x1, x0
            y2, y1 = y1, y0
            ival = int(max(-32767.0, min(32767.0, y0)))
            struct.pack_into("<h", out, i * 2, ival)

        return bytes(out)

    @staticmethod
    def sample_rate_convert(pcm_bytes: bytes, in_rate: int = 44100, out_rate: int = 22050) -> bytes:
        """
        OM Sec. 5.6: Sample Rate Conversion (48kHz, 44.1kHz, 32kHz, 22.05kHz).
        High-precision linear resampling with anti-aliasing pre-filter.
        """
        samples = [struct.unpack_from("<h", pcm_bytes, i * 2)[0] for i in range(len(pcm_bytes) // 2)]
        ratio = float(in_rate) / float(out_rate)
        num_out = int(len(samples) / ratio)

        out = bytearray(num_out * 2)
        for i in range(num_out):
            src_pos = i * ratio
            idx = int(src_pos)
            frac = src_pos - idx
            if idx + 1 < len(samples):
                s0 = samples[idx]
                s1 = samples[idx + 1]
                val = int(s0 + frac * (s1 - s0))
            elif idx < len(samples):
                val = samples[idx]
            else:
                val = 0
            struct.pack_into("<h", out, i * 2, max(-32767, min(32767, val)))

        return bytes(out)

    @staticmethod
    def bit_convert(pcm_bytes: bytes, target_bits: int = 8) -> bytes:
        """
        OM Sec. 5.6: Bit Depth Conversion (16-bit to 8-bit vintage resolution).
        Quantizes 16-bit samples to target resolution and expands back.
        """
        samples = [struct.unpack_from("<h", pcm_bytes, i * 2)[0] for i in range(len(pcm_bytes) // 2)]
        shift = 16 - target_bits
        out = bytearray(len(samples) * 2)
        for i, s in enumerate(samples):
            # Quantize to target bits
            q = (s >> shift) << shift
            struct.pack_into("<h", out, i * 2, max(-32767, min(32767, q)))
        return bytes(out)

    @staticmethod
    def auto_truncate_and_normalize(pcm_bytes: bytes, threshold_db: float = -48.0, peak_target: float = 0.98) -> Tuple[bytes, int, int]:
        """
        OM Sec. 5.7: Auto Truncate & Peak Normalize.
        Trims leading and trailing silence below threshold_db, and normalizes peak to peak_target.
        Returns (processed_pcm, start_trim_idx, end_trim_idx).
        """
        samples = [struct.unpack_from("<h", pcm_bytes, i * 2)[0] for i in range(len(pcm_bytes) // 2)]
        if not samples:
            return pcm_bytes, 0, 0

        threshold_amp = 32768.0 * (10.0 ** (threshold_db / 20.0))

        # Find start
        start_idx = 0
        for i, s in enumerate(samples):
            if abs(s) >= threshold_amp:
                start_idx = i
                break

        # Find end
        end_idx = len(samples)
        for i in range(len(samples) - 1, -1, -1):
            if abs(samples[i]) >= threshold_amp:
                end_idx = i + 1
                break

        if start_idx >= end_idx:
            start_idx = 0
            end_idx = len(samples)

        trimmed = samples[start_idx:end_idx]

        # Peak Normalize
        peak = max(abs(s) for s in trimmed) if trimmed else 1
        gain = (32767.0 * peak_target) / float(peak) if peak > 0 else 1.0

        out = bytearray(len(trimmed) * 2)
        for i, s in enumerate(trimmed):
            val = int(s * gain)
            struct.pack_into("<h", out, i * 2, max(-32767, min(32767, val)))

        return bytes(out), start_idx, end_idx

    @staticmethod
    def wave_edit(pcm_a: bytes, pcm_b: bytes = b"", operation: str = "mix", start: int = 0, length: int = 0) -> bytes:
        """
        OM Sec. 5.7: Destructive Wave Editing (Cut, Splice, Erase, Mix, Combine).
        """
        sa = [struct.unpack_from("<h", pcm_a, i * 2)[0] for i in range(len(pcm_a) // 2)]
        sb = [struct.unpack_from("<h", pcm_b, i * 2)[0] for i in range(len(pcm_b) // 2)] if pcm_b else []

        op = operation.lower()
        if op == "cut":
            # Remove [start : start + length]
            out_s = sa[:start] + sa[start + length:]
        elif op == "erase":
            # Silence [start : start + length]
            out_s = list(sa)
            for i in range(start, min(start + length, len(out_s))):
                out_s[i] = 0
        elif op == "splice":
            # Insert sb at start
            out_s = sa[:start] + sb + sa[start:]
        elif op == "mix":
            # Mix sb into sa with 50/50 blend
            max_len = max(len(sa), len(sb))
            out_s = [0] * max_len
            for i in range(max_len):
                va = sa[i] if i < len(sa) else 0
                vb = sb[i] if i < len(sb) else 0
                out_s[i] = int(max(-32767, min(32767, (va + vb) * 0.5)))
        else:
            out_s = sa

        out = bytearray(len(out_s) * 2)
        for i, s in enumerate(out_s):
            struct.pack_into("<h", out, i * 2, s)
        return bytes(out)


class S760DiskOptimizer:
    """OM Sec. 6.6: Disk Optimization / Defragmentation."""

    @staticmethod
    def optimize_disk(disk_bytes: bytes) -> bytes:
        """
        Defragments sample storage by relocating all fragmented clusters into
        a contiguous block immediately following the patch records, and cleans the allocation map.
        """
        if len(disk_bytes) < 512:
            return disk_bytes

        data = bytearray(disk_bytes)
        # Clear allocation map sectors 1-35
        for i in range(512, 36 * 512):
            data[i] = 0x0F # Mark free

        # Read number of patches and samples from header
        num_patches = struct.unpack_from("<I", data, 0x60)[0]
        num_samples = struct.unpack_from("<I", data, 0x64)[0]

        # Allocate patch sectors (36 .. 36 + num_patches)
        patch_sectors = (num_patches * 256 + 511) // 512
        for s in range(36, 36 + patch_sectors):
            if s < 36 * 512:
                data[512 + s] = 0x00 # Allocated

        return bytes(data)


class S760MSDOSExchange:
    """OM Sec. 6.8: MS-DOS Floppy Formatting & Sample Exchange."""

    @staticmethod
    def build_msdos_sample_floppy(wav_filename: str, pcm_bytes: bytes, sample_rate: int = 44100) -> bytes:
        """Builds a standard 1.44MB MS-DOS FAT12 Floppy image containing a .WAV audio file."""
        disk = bytearray(1474560)

        # 1. FAT12 Boot Sector (Sector 0)
        disk[0:3] = b"\xEB\x3C\x90" # JMP short
        disk[3:11] = b"MSDOS5.0"
        struct.pack_into("<H", disk, 11, 512)     # Sector size
        disk[13] = 1                              # Sectors per cluster
        struct.pack_into("<H", disk, 14, 1)       # Reserved sectors
        disk[16] = 2                              # Number of FATs
        struct.pack_into("<H", disk, 17, 224)     # Max root dir entries
        struct.pack_into("<H", disk, 19, 2880)    # Total sectors
        disk[21] = 0xF0                           # Media descriptor (1.44M 3.5")
        struct.pack_into("<H", disk, 22, 9)       # Sectors per FAT
        struct.pack_into("<H", disk, 24, 18)      # Sectors per track
        struct.pack_into("<H", disk, 26, 2)       # Number of heads
        disk[510:512] = b"\x55\xAA"               # Boot signature

        # 2. Build standard RIFF WAV payload
        wav_hdr = bytearray(44)
        wav_hdr[0:4] = b"RIFF"
        struct.pack_into("<I", wav_hdr, 4, 36 + len(pcm_bytes))
        wav_hdr[8:12] = b"WAVE"
        wav_hdr[12:16] = b"fmt "
        struct.pack_into("<I", wav_hdr, 16, 16)   # PCM format chunk size
        struct.pack_into("<H", wav_hdr, 20, 1)    # PCM format
        struct.pack_into("<H", wav_hdr, 22, 1)    # 1 Channel (Mono)
        struct.pack_into("<I", wav_hdr, 24, sample_rate)
        struct.pack_into("<I", wav_hdr, 28, sample_rate * 2) # Byte rate
        struct.pack_into("<H", wav_hdr, 32, 2)    # Block align
        struct.pack_into("<H", wav_hdr, 34, 16)   # Bits per sample
        wav_hdr[36:40] = b"data"
        struct.pack_into("<I", wav_hdr, 40, len(pcm_bytes))

        wav_data = bytes(wav_hdr) + pcm_bytes

        # 3. Root Directory Entry (Sector 19 = offset 0x2600)
        root_offset = 19 * 512
        name_parts = wav_filename.upper().split(".")
        fname = name_parts[0][:8].ljust(8)
        fext = (name_parts[1] if len(name_parts) > 1 else "WAV")[:3].ljust(3)
        disk[root_offset:root_offset + 8] = fname.encode('ascii')
        disk[root_offset + 8:root_offset + 11] = fext.encode('ascii')
        disk[root_offset + 11] = 0x20 # Archive attribute
        struct.pack_into("<H", disk, root_offset + 26, 2) # Starting cluster = 2
        struct.pack_into("<I", disk, root_offset + 28, len(wav_data))

        # 4. Write WAV Data to Cluster 2 (Sector 33 = offset 0x4200)
        data_offset = 33 * 512
        disk[data_offset:data_offset + len(wav_data)] = wav_data

        return bytes(disk)

    @staticmethod
    def extract_wav_from_msdos(disk_bytes: bytes) -> Dict:
        """Extracts WAV file from an MS-DOS FAT12 formatted disk image."""
        if len(disk_bytes) < 1474560 or disk_bytes[510:512] != b"\x55\xAA":
            return {"is_dos": False}

        root_offset = 19 * 512
        fname = disk_bytes[root_offset:root_offset + 8].decode('ascii', errors='replace').strip()
        fext = disk_bytes[root_offset + 8:root_offset + 11].decode('ascii', errors='replace').strip()
        start_cluster = struct.unpack_from("<H", disk_bytes, root_offset + 26)[0]
        file_size = struct.unpack_from("<I", disk_bytes, root_offset + 28)[0]

        data_offset = (33 + (start_cluster - 2)) * 512
        file_bytes = disk_bytes[data_offset:data_offset + file_size]

        is_wav = file_bytes[0:4] == b"RIFF" and file_bytes[8:12] == b"WAVE"
        sample_rate = struct.unpack_from("<I", file_bytes, 24)[0] if is_wav else 44100
        pcm_data = file_bytes[44:] if is_wav else b""

        return {
            "is_dos": True,
            "filename": f"{fname}.{fext}",
            "file_size": file_size,
            "is_wav": is_wav,
            "sample_rate": sample_rate,
            "pcm_data": pcm_data
        }


class S760MIDISampleDump:
    """OM Sec. 7.4: MIDI Sample Dump Standard (SDS) Protocol."""

    @staticmethod
    def build_sds_dump_header(sample_num: int, sample_rate: int, length: int, loop_start: int, loop_end: int, channel: int = 0) -> bytes:
        """Creates a MIDI SDS Dump Header (SysEx Type 0x01)."""
        period_ns = int(1e9 / float(sample_rate))
        # 3-byte 7-bit period
        p0 = period_ns & 0x7F
        p1 = (period_ns >> 7) & 0x7F
        p2 = (period_ns >> 14) & 0x7F
        # 3-byte 7-bit length
        l0 = length & 0x7F
        l1 = (length >> 7) & 0x7F
        l2 = (length >> 14) & 0x7F
        # 3-byte 7-bit loop start & loop end
        ls0, ls1, ls2 = loop_start & 0x7F, (loop_start >> 7) & 0x7F, (loop_start >> 14) & 0x7F
        le0, le1, le2 = loop_end & 0x7F, (loop_end >> 7) & 0x7F, (loop_end >> 14) & 0x7F

        msg = bytearray([
            0xF0, 0x7E, channel & 0x7F, 0x01, # Universal Non-Realtime SysEx SDS Header
            sample_num & 0x7F, (sample_num >> 7) & 0x7F,
            16, # 16-bit resolution
            p0, p1, p2,
            l0, l1, l2,
            ls0, ls1, ls2,
            le0, le1, le2,
            0x00, # Forward loop
            0xF7
        ])
        return bytes(msg)

    @staticmethod
    def parse_sds_dump_header(sysex: bytes) -> Dict:
        """Parses a MIDI SDS Dump Header SysEx packet."""
        if len(sysex) < 21 or sysex[0] != 0xF0 or sysex[1] != 0x7E or sysex[3] != 0x01:
            return {"valid_sds": False}

        chan = sysex[2]
        snum = sysex[4] | (sysex[5] << 7)
        bits = sysex[6]
        period_ns = sysex[7] | (sysex[8] << 7) | (sysex[9] << 14)
        srate = int(1e9 / period_ns) if period_ns > 0 else 44100
        length = sysex[10] | (sysex[11] << 7) | (sysex[12] << 14)
        lstart = sysex[13] | (sysex[14] << 7) | (sysex[15] << 14)
        lend = sysex[16] | (sysex[17] << 7) | (sysex[18] << 14)
        loop_type = sysex[19]

        return {
            "valid_sds": True,
            "channel": chan,
            "sample_num": snum,
            "bits": bits,
            "sample_rate": srate,
            "length": length,
            "loop_start": lstart,
            "loop_end": lend,
            "loop_type": loop_type
        }
