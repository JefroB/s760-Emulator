"""
scripts/extract_s760_sample.py — Extracts raw 16-bit PCM WAV files from Roland S-760 floppy disk images (.img).
Used to ingest audio recorded directly onto physical Gotek disks from S-760 analog inputs.
"""

import os
import struct
import wave
import argparse


def extract_samples_from_img(img_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    with open(img_path, "rb") as f:
        data = f.read()

    if len(data) < 512:
        raise ValueError("Invalid disk image size")

    # Read number of sample records from Sector 0
    num_samples = struct.unpack_from("<I", data, 0x64)[0]
    print(f"Disk '{img_path}': Found {num_samples} sample records.")

    extracted_files = []
    offset = 0x10000

    for s_idx in range(min(num_samples, 64)):
        if offset + 256 > len(data):
            break

        sample_id = struct.unpack_from("<H", data, offset)[0]
        raw_name = data[offset + 2:offset + 18].decode('ascii', errors='ignore').strip()
        sample_name = "".join(c if (c.isalnum() or c in "._- ") else "_" for c in raw_name) or f"sample_{sample_id}"
        sample_rate = struct.unpack_from("<I", data, offset + 0x12)[0] or 44100
        root_key = data[offset + 0x1E]
        byte_len = struct.unpack_from("<I", data, offset + 0x20)[0]

        offset += 256
        if offset + byte_len > len(data):
            break

        pcm_bytes = data[offset:offset + byte_len]
        offset += (byte_len + 511) & ~511  # Align to sector

        # Write WAV file
        wav_path = os.path.join(output_dir, f"{sample_id:02d}_{sample_name}.wav")
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)

        print(f"  Extracted [{sample_id:02d}] '{sample_name}': {len(pcm_bytes)//2} samples @ {sample_rate} Hz (Root Key {root_key}) -> {wav_path}")
        extracted_files.append(wav_path)

    return extracted_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract WAV samples from Roland S-760 .IMG disk")
    parser.add_argument("img_path", help="Path to Roland S-760 .IMG disk file")
    parser.add_argument("--out", default="extracted_wavs", help="Output directory for extracted WAVs")
    args = parser.parse_args()

    extract_samples_from_img(args.img_path, args.out)
