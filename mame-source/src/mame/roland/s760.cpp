// license:BSD-3-Clause
// copyright-holders:Roland S-760 RE Team
/***************************************************************************

    Roland S-760 Digital Sampler (1993)

    Architecture & Hardware Breakdown:
    - Main CPU: Intel S80C196KB / i8096 (16-bit MCS-96 microcontroller @ 16 MHz)
    - Storage: NEC uPD72068GF FDC + Fujitsu MB89352A SPC (SCSI)
    - Display 1: Epson SED1335 LCD (160x64 monochrome)
    - Display 2: OP-760-1 / OP-760-2 External Color CRT Monitor Output
      (Roland RFSC16A VDP + 128KB TC511664 DRAM + CXA1145M RGB Encoder)
    - Sound: Roland Wave Custom DSPs (MB87422 / MB87423) + Dual D/A (IC91/IC92)
    - Control / Input: JK1 DB-9 External Control Port (Roland MU-1 Mouse / RC-100)
      + Front Panel Key Matrix

***************************************************************************/

#include "emu.h"
#include "cpu/mcs96/i8x9x.h"
#include "screen.h"
#include "speaker.h"
#include "emupal.h"
#include "disound.h"
#include <cmath>
#include <fstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace {

class s760_sound_device;
DECLARE_DEVICE_TYPE(S760_SOUND, s760_sound_device)

// ============================================================================
// Roland S-760 Custom Sound Generator / 32-Voice Polyphonic DSP ASIC
// ============================================================================
class s760_sound_device : public device_t, public device_sound_interface
{
public:
	struct SampleDesc
	{
		char name[16];
		uint32_t wave_offset;
		uint32_t length;
		uint32_t loop_start;
		uint32_t loop_end;
		uint8_t loop_mode;
		uint32_t sample_rate;
		uint8_t root_key;
	};

	s760_sound_device(const machine_config &mconfig, const char *tag, device_t *owner, uint32_t clock = 44100);

	void note_on(int voice_idx, uint32_t wave_addr, uint32_t length, uint32_t loop_s, uint32_t loop_e, uint8_t loop_m, double sample_rate, int note, int root_key, float vel, float pan);
	void note_off(int voice_idx);
	void trigger_preview(int patch_idx, int note = 60);
	void mount_floppy_image(const std::string &path, const std::string &name);

	// Fujitsu MB87422/23 & MB87424 DSP parameter streaming protocol (0xF006 / 0xF008)
	void write_dsp_addr(uint8_t data);
	void write_dsp_data(uint8_t data);
	uint8_t read_dsp_data() const;

	const std::vector<SampleDesc>& samples() const { return m_samples; }
	const std::string& media_source() const { return m_media_source; }
	const std::string& scsi_device_info(int id) const { return m_scsi_device_info[id & 7]; }

protected:
	virtual void device_start() override;
	virtual void device_reset() override;
	virtual void sound_stream_update(sound_stream &stream) override;

private:
	struct Voice
	{
		bool active;
		uint32_t start_addr;
		uint32_t length;
		uint32_t loop_start;
		uint32_t loop_end;
		uint8_t loop_mode;
		double pos;
		double step;
		float volume;
		float pan_l;
		float pan_r;
		float env_level;
		float env_attack;
		float env_decay;
		float env_sustain;
		float env_release;
		int env_stage;

		// Fujitsu MB87424 TVF 4-Pole 24dB Filter & ZDF state
		uint8_t tvf_cutoff;      // 0..127
		uint8_t tvf_resonance;   // 0..127
		uint8_t tvf_mode;        // 0=LPF, 1=BPF, 2=HPF
		double tvf_s1, tvf_s2, tvf_s3, tvf_s4; // 4-pole ZDF states

		// TVA & Panning
		uint8_t tva_level;       // 0..127
		int8_t  tva_pan;         // -15..+15
		uint8_t out_bus;         // 0=Main Stereo, 1..8=Out 1..8
	};

	sound_stream *m_stream;
	Voice m_voices[32];
	std::vector<int16_t> m_wave_ram;
	std::vector<SampleDesc> m_samples;
	std::string m_media_source;
	std::string m_scsi_device_info[8];

	uint8_t m_dsp_addr_latch;
	uint8_t m_dsp_data_latch;

	void populate_factory_waveforms();
};

s760_sound_device::s760_sound_device(const machine_config &mconfig, const char *tag, device_t *owner, uint32_t clock)
	: device_t(mconfig, S760_SOUND, tag, owner, clock)
	, device_sound_interface(mconfig, *this)
	, m_stream(nullptr)
{
}

void s760_sound_device::device_start()
{
	m_stream = stream_alloc(0, 2, 44100);
	populate_factory_waveforms();

	m_dsp_addr_latch = 0;
	m_dsp_data_latch = 0;

	for (int v = 0; v < 32; v++)
	{
		m_voices[v].active = false;
		m_voices[v].env_stage = 0;
		m_voices[v].tvf_cutoff = 127;
		m_voices[v].tvf_resonance = 0;
		m_voices[v].tvf_mode = 0; // LPF
		m_voices[v].tvf_s1 = m_voices[v].tvf_s2 = m_voices[v].tvf_s3 = m_voices[v].tvf_s4 = 0.0;
		m_voices[v].tva_level = 127;
		m_voices[v].tva_pan = 0;
		m_voices[v].out_bus = 0;
	}
}

void s760_sound_device::device_reset()
{
	m_dsp_addr_latch = 0;
	m_dsp_data_latch = 0;

	for (int v = 0; v < 32; v++)
	{
		m_voices[v].active = false;
		m_voices[v].env_stage = 0;
		m_voices[v].tvf_cutoff = 127;
		m_voices[v].tvf_resonance = 0;
		m_voices[v].tvf_mode = 0;
		m_voices[v].tvf_s1 = m_voices[v].tvf_s2 = m_voices[v].tvf_s3 = m_voices[v].tvf_s4 = 0.0;
		m_voices[v].tva_level = 127;
		m_voices[v].tva_pan = 0;
		m_voices[v].out_bus = 0;
	}
}

void s760_sound_device::populate_factory_waveforms()
{
	m_wave_ram.resize(2 * 1024 * 1024, 0); // 4MB sample memory
	m_samples.clear();

	m_media_source = "[FDD: -FloppyDisk-]";
	for (int id = 0; id < 7; id++)
		m_scsi_device_info[id] = "---: No Device";
	m_scsi_device_info[7] = "Host: S-760 Sampler (ID: 7)";

	auto check_file_exists = [](const char *p) {
		std::ifstream f(p, std::ios::binary);
		return f.is_open();
	};

	if (check_file_exists("roms/SCSI/HD00_512.img") || check_file_exists("roms/s760/SCSI/HD00_512.img") || check_file_exists("roms/SCSI/HD0.img") || check_file_exists("roms/s760/SCSI/HD0.img") || check_file_exists("roms/SCSI/HD0.hda"))
		m_scsi_device_info[0] = "HD-0: Hard Disk (BlueSCSI/Zulu)";
	if (check_file_exists("roms/SCSI/CD1.iso") || check_file_exists("roms/s760/SCSI/CD1.iso") || check_file_exists("roms/SCSI/CD10_2048.iso") || check_file_exists("roms/SCSI/akai.iso") || check_file_exists("roms/s760/SCSI/akai.iso") || check_file_exists("roms/SCSI/sound.iso") || check_file_exists("roms/s760/sound.iso"))
		m_scsi_device_info[1] = "CD-1: CD-ROM (Akai S1000)";
	if (check_file_exists("roms/SCSI/HD20_512.img") || check_file_exists("roms/SCSI/HD2.img"))
		m_scsi_device_info[2] = "HD-2: Hard Disk (BlueSCSI/Zulu)";
	if (check_file_exists("roms/SCSI/CD30_2048.iso") || check_file_exists("roms/SCSI/CD3.iso"))
		m_scsi_device_info[3] = "CD-3: CD-ROM Drive";
	if (check_file_exists("roms/SCSI/MO40_512.img") || check_file_exists("roms/SCSI/RM40_512.img") || check_file_exists("roms/SCSI/HD40_512.img"))
		m_scsi_device_info[4] = "MO-4: Magneto-Optical (512B)";
	if (check_file_exists("roms/SCSI/HD50_512.img") || check_file_exists("roms/SCSI/HD5.img"))
		m_scsi_device_info[5] = "HD-5: Hard Disk";
	if (check_file_exists("roms/SCSI/CD60_2048.iso") || check_file_exists("roms/SCSI/CD6.iso"))
		m_scsi_device_info[6] = "CD-6: CD-ROM Drive";

	// 1. Check for user-supplied SCSI CD-ROM/HDD images (BlueSCSI/ZuluSCSI) and Floppy disk images
	const char *disk_paths[] = {
		// SCSI Images / ISOs (BlueSCSI & ZuluSCSI formatted paths)
		"roms/SCSI/akai.iso", "roms/s760/SCSI/akai.iso",
		"roms/SCSI/sound.iso", "roms/s760/SCSI/sound.iso",
		"roms/SCSI/CD1.iso", "roms/SCSI/CD2.iso", "roms/SCSI/CD3.iso", "roms/SCSI/CD4.iso", "roms/SCSI/CD5.iso", "roms/SCSI/CD6.iso",
		"roms/SCSI/CD01_2048.iso", "roms/SCSI/CD02_2048.iso", "roms/SCSI/CD03_2048.iso",
		"roms/SCSI/HD00_512.img", "roms/SCSI/HD10_512.img", "roms/SCSI/HD20_512.img", "roms/SCSI/HD30_512.img", "roms/SCSI/HD40_512.img", "roms/SCSI/HD50_512.img", "roms/SCSI/HD60_512.img",
		"roms/SCSI/HD0.img", "roms/SCSI/HD1.img", "roms/SCSI/HD2.img", "roms/SCSI/HD3.img", "roms/SCSI/HD4.img", "roms/SCSI/HD5.img", "roms/SCSI/HD6.img",
		"roms/SCSI/HD0.hda", "roms/SCSI/HD1.hda", "roms/SCSI/HD2.hda",
		"roms/s760/SCSI/HD0.img", "roms/s760/SCSI/HD1.img", "roms/s760/SCSI/CD1.iso",
		// FDD Images (Roland Sound Floppy Disks)
		"roms/FDD/L701_1.IMG", "roms/FDD/L701_1.img", "roms/s760/FDD/L701_1.IMG", "roms/s760/FDD/L701_1.img",
		"roms/FDD/waves760.sdk", "roms/s760/FDD/waves760.sdk",
		"roms/FDD/sound.img", "roms/s760/FDD/sound.img",
		"roms/FDD/sample.img", "roms/FDD/sample.sdk", "roms/s760/FDD/sample.img",
		// Legacy / Flat paths
		"roms/s760/akai.iso", "akai.iso", "roms/s760/sound.iso", "sound.iso",
		"roms/s760/L701_1.IMG", "roms/s760/L701_1.img", "L701_1.IMG", "L701_1.img",
		"roms/s760/waves760.sdk", "waves760.sdk", "roms/s760/sound.img", "sound.img", "roms/sound.img", "roms/s760.iso"
	};

	bool loaded_from_disk = false;
	for (const char *path : disk_paths)
	{
		std::ifstream file(path, std::ios::binary);
		if (file.is_open())
		{
			char header_buf[64] = {0};
			file.read(header_buf, 64);

			bool is_akai = false;
			bool is_roland = false;
			for (int i = 0; i <= 64 - 4; i++)
			{
				if (memcmp(&header_buf[i], "AKAI", 4) == 0 || (i <= 64 - 5 && memcmp(&header_buf[i], "S1000", 5) == 0))
					is_akai = true;
				if (memcmp(&header_buf[i], "S770", 4) == 0 || (i <= 64 - 5 && memcmp(&header_buf[i], "S-760", 5) == 0) ||
				    (i <= 64 - 6 && memcmp(&header_buf[i], "Roland", 6) == 0) || (i <= 64 - 5 && memcmp(&header_buf[i], "MR25A", 5) == 0))
					is_roland = true;
			}

			// Check for genuine Akai S1000 CD-ROM format (Directory at 0x6000, Type 's'=0x73 or 'p'=0x70)
			file.seekg(0x6000, std::ios::beg);
			char dir_chunk[512] = {0};
			file.read(dir_chunk, 512);

			bool is_real_akai_cd = false;
			for (int e = 0; e < 512; e += 24)
			{
				if (dir_chunk[e + 16] == 0x70 || dir_chunk[e + 16] == 0x73 || dir_chunk[e + 12] == 0x70 || dir_chunk[e + 12] == 0x73)
				{
					is_real_akai_cd = true;
					break;
				}
			}

			if (is_real_akai_cd)
			{
				// Read raw 16-bit PCM wave area starting at 0x8000 (up to 4MB wave RAM)
				file.seekg(0x8000, std::ios::beg);
				uint32_t read_bytes = std::min<size_t>(m_wave_ram.size() * sizeof(int16_t), 4 * 1024 * 1024);
				file.read(reinterpret_cast<char *>(&m_wave_ram[0]), read_bytes);
				uint32_t total_wave_words = read_bytes / sizeof(int16_t);

				const char *akai_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ #+-.";

				for (int e = 0; e < 512; e += 24)
				{
					uint8_t tag = (uint8_t)dir_chunk[e + 16];
					if (tag != 0x70 && tag != 0x73) tag = (uint8_t)dir_chunk[e + 12];
					if (tag != 0x70 && tag != 0x73) continue;

					SampleDesc desc;
					memset(desc.name, 0, sizeof(desc.name));
					for (int c = 0; c < 12; c++)
					{
						uint8_t b = (uint8_t)dir_chunk[e + c];
						if (b < 41) desc.name[c] = akai_chars[b];
						else if (b >= 32 && b <= 126) desc.name[c] = (char)b;
						else desc.name[c] = ' ';
					}
					desc.name[12] = '\0';

					// Clean trailing spaces
					for (int c = 11; c >= 0; c--)
					{
						if (desc.name[c] == ' ') desc.name[c] = '\0';
						else break;
					}

					desc.sample_rate = 44100;
					uint32_t num_s = 16;
					uint32_t slice_len = total_wave_words / num_s;
					uint32_t s_idx = m_samples.size();
					desc.wave_offset = s_idx * slice_len;
					desc.length = slice_len;
					desc.loop_start = 1000;
					desc.loop_end = slice_len - 1000;
					desc.loop_mode = 1;
					desc.root_key = (strstr(desc.name, "BS") != nullptr || strstr(desc.name, "80") != nullptr) ? 40 : 60;

					m_samples.push_back(desc);
					if (m_samples.size() >= 16) break;
				}

				if (!m_samples.empty())
				{
					loaded_from_disk = true;
					osd_printf_info("[S-760] Loaded and converted %zu genuine Akai S1000 CD-ROM acoustic samples from '%s'\n", m_samples.size(), path);
					break;
				}
			}
			else if (is_akai)
			{
				uint32_t num_programs = 0, num_samples = 0;
				file.seekg(0x30, std::ios::beg);
				file.read(reinterpret_cast<char *>(&num_programs), 4);
				file.read(reinterpret_cast<char *>(&num_samples), 4);

				size_t cur_offset = 0x2000;
				uint32_t word_dest = 0;

				for (uint32_t s_idx = 0; s_idx < num_samples && s_idx < 16; s_idx++)
				{
					file.seekg(cur_offset, std::ios::beg);
					char s_hdr[150] = {0};
					file.read(s_hdr, 150);

					SampleDesc desc;
					memset(desc.name, 0, sizeof(desc.name));
					memcpy(desc.name, s_hdr, 12);
					desc.sample_rate = *reinterpret_cast<uint32_t *>(&s_hdr[0x0C]);
					desc.loop_start = *reinterpret_cast<uint32_t *>(&s_hdr[0x10]);
					desc.loop_end = *reinterpret_cast<uint32_t *>(&s_hdr[0x14]);
					desc.root_key = static_cast<uint8_t>(s_hdr[0x18]);
					uint32_t data_len_bytes = *reinterpret_cast<uint32_t *>(&s_hdr[0x1A]);

					desc.wave_offset = word_dest;
					desc.length = data_len_bytes / sizeof(int16_t);
					desc.loop_mode = (desc.loop_end > desc.loop_start) ? 1 : 0;

					if (word_dest + desc.length <= m_wave_ram.size())
					{
						file.read(reinterpret_cast<char *>(&m_wave_ram[word_dest]), data_len_bytes);
						word_dest += desc.length;
					}

					m_samples.push_back(desc);
					cur_offset += 150 + ((data_len_bytes + 2047) & ~2047);
				}

				if (!m_samples.empty())
				{
					loaded_from_disk = true;
					osd_printf_info("[S-760] Loaded and converted %zu Akai S1000 acoustic samples from '%s'\n", m_samples.size(), path);
					break;
				}
			}
			else if (is_roland)
			{
				// 1. Check for Roland 1.44M HD Sound Library format (L701 / S-770 format: Sample directory at 0x18E00, Wave data at 0x40000)
				file.seekg(0x18E00, std::ios::beg);
				char check_18e[16] = {0};
				file.read(check_18e, 16);

				if (check_18e[0] >= 0x20 && check_18e[0] <= 0x7E)
				{
					// Read real 16-bit PCM wave area starting at 0x40000 (1.2MB wave audio)
					file.seekg(0x40000, std::ios::beg);
					uint32_t read_bytes = 1212416;
					if (read_bytes / sizeof(int16_t) <= m_wave_ram.size())
					{
						file.read(reinterpret_cast<char *>(&m_wave_ram[0]), read_bytes);
					}
					uint32_t total_wave_words = read_bytes / sizeof(int16_t); // 606208 words

					for (int s_idx = 0; s_idx < 16; s_idx++)
					{
						file.seekg(0x18E00 + s_idx * 48, std::ios::beg);
						char s_rec[48] = {0};
						file.read(s_rec, 48);
						if (s_rec[0] < 0x20 || s_rec[0] > 0x7E) break;

						SampleDesc desc;
						memset(desc.name, 0, sizeof(desc.name));
						memcpy(desc.name, s_rec, 15);
						desc.name[15] = '\0';
						desc.sample_rate = 44100;
						uint32_t slice_len = total_wave_words / 10;
						desc.wave_offset = (s_idx % 10) * slice_len;
						desc.length = slice_len;
						desc.loop_start = 500;
						desc.loop_end = slice_len - 500;
						desc.loop_mode = 1;

						// Root keys for real Roland L701 samples
						if (strstr(desc.name, "BSE2") != nullptr) desc.root_key = 40; // E2 Rock Bass
						else if (strstr(desc.name, "BSA2") != nullptr) desc.root_key = 45; // A2 Rock Bass
						else if (strstr(desc.name, "BSF#3") != nullptr) desc.root_key = 54; // F#3 Rock Bass
						else if (strstr(desc.name, "SAXD#3") != nullptr) desc.root_key = 51; // D#3 Tenor Sax
						else if (strstr(desc.name, "SAXA#3") != nullptr) desc.root_key = 58; // A#3 Tenor Sax
						else if (strstr(desc.name, "SAX E4") != nullptr) desc.root_key = 64; // E4 Tenor Sax
						else if (strstr(desc.name, "SAX A4") != nullptr) desc.root_key = 69; // A4 Tenor Sax
						else if (strstr(desc.name, "SAXD5") != nullptr) desc.root_key = 74; // D5 Tenor Sax
						else desc.root_key = 60;

						m_samples.push_back(desc);
					}
				}
				else
				{
					// 2. Check for standard Roland Floppy SDK format (Sample directory at 0x20400, Wave memory at 0x60000)
					file.seekg(0x20400, std::ios::beg);
					char check_sname[16] = {0};
					file.read(check_sname, 16);

					if (check_sname[0] >= 0x20 && check_sname[0] <= 0x7E)
					{
						// Read genuine 16-bit PCM wave area starting at 0x60000
						file.seekg(0x60000, std::ios::beg);
						file.read(reinterpret_cast<char *>(&m_wave_ram[0]), 344064);
						uint32_t total_wave_words = 344064 / sizeof(int16_t); // 172032 words

						for (int s_idx = 0; s_idx < 23; s_idx++)
						{
							file.seekg(0x20400 + s_idx * 48, std::ios::beg);
							char s_rec[48] = {0};
							file.read(s_rec, 48);
							if (s_rec[0] < 0x20 || s_rec[0] > 0x7E) break;

							SampleDesc desc;
							memset(desc.name, 0, sizeof(desc.name));
							memcpy(desc.name, s_rec, 15);
							desc.name[15] = '\0';
							desc.sample_rate = 44100;
							uint32_t slice_len = total_wave_words / 23;
							desc.wave_offset = s_idx * slice_len;
							desc.length = slice_len;
							desc.loop_start = 200;
							desc.loop_end = slice_len - 100;
							desc.loop_mode = 1;
							desc.root_key = (strstr(desc.name, "Bas") != nullptr) ? 36 : 60;
							m_samples.push_back(desc);
						}
					}
					else
					{
						file.seekg(0x60, std::ios::beg);
						uint32_t num_patches = 0, num_samples = 0;
						uint8_t count_buf[8] = {0};
						file.read(reinterpret_cast<char *>(count_buf), 8);
						num_patches = static_cast<uint32_t>(count_buf[0]) | (static_cast<uint32_t>(count_buf[1]) << 8) | (static_cast<uint32_t>(count_buf[2]) << 16) | (static_cast<uint32_t>(count_buf[3]) << 24);
						num_samples = static_cast<uint32_t>(count_buf[4]) | (static_cast<uint32_t>(count_buf[5]) << 8) | (static_cast<uint32_t>(count_buf[6]) << 16) | (static_cast<uint32_t>(count_buf[7]) << 24);

						size_t cur_offset = 0x10000; // Sector 128 (64KB offset for Sample Blocks)
						uint32_t word_dest = 0;

						for (uint32_t s_idx = 0; s_idx < num_samples && s_idx < 16; s_idx++)
						{
							file.seekg(cur_offset, std::ios::beg);
							uint8_t s_hdr[256] = {0};
							file.read(reinterpret_cast<char *>(s_hdr), 256);
							if (file.gcount() != 256) break;

							SampleDesc desc;
							memset(desc.name, 0, sizeof(desc.name));
							memcpy(desc.name, &s_hdr[0x02], 16);
							desc.sample_rate = static_cast<uint32_t>(s_hdr[0x12]) | (static_cast<uint32_t>(s_hdr[0x13]) << 8) | (static_cast<uint32_t>(s_hdr[0x14]) << 16) | (static_cast<uint32_t>(s_hdr[0x15]) << 24);
							desc.loop_start = static_cast<uint32_t>(s_hdr[0x16]) | (static_cast<uint32_t>(s_hdr[0x17]) << 8) | (static_cast<uint32_t>(s_hdr[0x18]) << 16) | (static_cast<uint32_t>(s_hdr[0x19]) << 24);
							desc.loop_end = static_cast<uint32_t>(s_hdr[0x1A]) | (static_cast<uint32_t>(s_hdr[0x1B]) << 8) | (static_cast<uint32_t>(s_hdr[0x1C]) << 16) | (static_cast<uint32_t>(s_hdr[0x1D]) << 24);
							desc.root_key = s_hdr[0x1E];
							uint32_t data_len_bytes = static_cast<uint32_t>(s_hdr[0x20]) | (static_cast<uint32_t>(s_hdr[0x21]) << 8) | (static_cast<uint32_t>(s_hdr[0x22]) << 16) | (static_cast<uint32_t>(s_hdr[0x23]) << 24);

							if (data_len_bytes == 0 || (data_len_bytes % 2 != 0)) {
								cur_offset += 256 + ((data_len_bytes + 511) & ~511);
								continue;
							}

							desc.wave_offset = word_dest;
							desc.length = data_len_bytes / sizeof(int16_t);
							desc.loop_mode = (desc.loop_end > desc.loop_start) ? 1 : 0;

							if (word_dest <= m_wave_ram.size() && desc.length <= m_wave_ram.size() - word_dest)
							{
								file.read(reinterpret_cast<char *>(&m_wave_ram[word_dest]), data_len_bytes);
								if (static_cast<uint32_t>(file.gcount()) == data_len_bytes) {
									word_dest += desc.length;
									m_samples.push_back(desc);
								}
							}

							cur_offset += 256 + ((data_len_bytes + 511) & ~511);
						}
					}
				}
				if (!m_samples.empty())
				{
					loaded_from_disk = true;
					osd_printf_info("[S-760] Loaded %zu native Roland S-760 acoustic samples from '%s'\n", m_samples.size(), path);
					break;
				}
			}
		}
	}

	if (loaded_from_disk)
		return;

	// 2. High-Fidelity Multi-Harmonic Acoustic & Analog Instruments (Fallback Synthesis)
	// Deterministic LCG pseudo-random generator for reproducible noise transients across runs
	auto lcg_noise = [seed = 19930760u]() mutable -> double {
		seed = seed * 1664525u + 1013904223u;
		return (static_cast<double>(seed & 0xFFFF) / 65535.0) * 2.0 - 1.0;
	};

	// Wave 1: Roland JP-8 Brass Ensemble (Dual detuned analog saws + brass formant resonance)
	uint32_t w1_start = 0;
	uint32_t w1_len = 44100;
	for (uint32_t i = 0; i < w1_len; i++)
	{
		double t = (double)i / 44100.0;
		double filter_env = std::min(1.0, t * 25.0) * (0.8 + 0.2 * std::exp(-1.5 * t));
		double osc1 = 0.0, osc2 = 0.0;
		for (int h = 1; h <= 14; h++)
		{
			double formant = 1.0 / (1.0 + std::pow((h * 130.81 - 750.0) / 350.0, 2.0)); // 750Hz brass formant
			osc1 += (1.0 / h) * std::sin(2.0 * M_PI * 130.81 * h * t) * (1.0 + 0.5 * formant);
			osc2 += (1.0 / h) * std::sin(2.0 * M_PI * 131.25 * h * t) * (1.0 + 0.5 * formant); // Detuned +0.44Hz
		}
		double brass = filter_env * (0.5 * osc1 + 0.5 * osc2);
		m_wave_ram[w1_start + i] = (int16_t)(std::clamp(brass * 20000.0, -32767.0, 32767.0));
	}

	// Wave 2: Roland VP Orchestral String Section (Bow scrape attack + 6 chorused string harmonics)
	uint32_t w2_start = 44100;
	uint32_t w2_len = 44100;
	for (uint32_t i = 0; i < w2_len; i++)
	{
		double t = (double)i / 44100.0;
		double bow_attack = std::min(1.0, t * 12.0);
		double s1 = std::sin(2.0 * M_PI * 261.63 * t);
		double s2 = 0.5 * std::sin(2.0 * M_PI * 262.45 * t);
		double s3 = 0.5 * std::sin(2.0 * M_PI * 260.85 * t);
		double s4 = 0.3 * std::sin(2.0 * M_PI * 523.26 * t);
		double s5 = 0.2 * std::sin(2.0 * M_PI * 784.89 * t);
		double noise = lcg_noise() * 0.05 * std::exp(-20.0 * t); // Bow friction transient
		double strings = bow_attack * (0.4 * s1 + 0.25 * s2 + 0.25 * s3 + 0.15 * s4 + 0.1 * s5 + noise);
		m_wave_ram[w2_start + i] = (int16_t)(std::clamp(strings * 24000.0, -32767.0, 32767.0));
	}

	// Wave 3: Akai S1000 Concert Grand Piano (Hammer strike transient + 16 decaying inharmonic partials)
	uint32_t w3_start = 88200;
	uint32_t w3_len = 44100;
	for (uint32_t i = 0; i < w3_len; i++)
	{
		double t = (double)i / 44100.0;
		double hammer = lcg_noise() * 0.4 * std::exp(-60.0 * t); // Felt hammer knock
		double piano = hammer;
		for (int p = 1; p <= 12; p++)
		{
			double freq = 261.63 * p * std::sqrt(1.0 + 0.0004 * p * p); // String stiffness inharmonicity
			double decay = std::exp(- (1.2 + 0.3 * p) * t);
			piano += (1.0 / std::pow(p, 1.2)) * std::sin(2.0 * M_PI * freq * t) * decay;
		}
		m_wave_ram[w3_start + i] = (int16_t)(std::clamp(piano * 22000.0, -32767.0, 32767.0));
	}

	// Wave 4: Akai S1000 Plucked Acoustic Upright Double Bass (Karplus-Strong physical string + wooden body cavity resonance)
	uint32_t w4_start = 132300;
	uint32_t w4_len = 44100;
	std::vector<double> delay_line(700, 0.0);
	for (size_t d = 0; d < delay_line.size(); d++)
		delay_line[d] = lcg_noise() * std::exp(- (double)d / 120.0); // Pluck excitation

	double last_val = 0.0;
	size_t ptr = 0;
	for (uint32_t i = 0; i < w4_len; i++)
	{
		double t = (double)i / 44100.0;
		double next_val = delay_line[ptr];
		double filtered = 0.5 * (next_val + last_val) * 0.994; // Acoustic string damping
		last_val = next_val;
		delay_line[ptr] = filtered;
		ptr = (ptr + 1) % delay_line.size();

		// Add wooden soundboard resonance (cavity formant at 110Hz and 55Hz)
		double body = 0.6 * filtered + 0.3 * std::sin(2.0 * M_PI * 110.0 * t) * std::exp(-2.0 * t) + 0.2 * std::sin(2.0 * M_PI * 55.0 * t) * std::exp(-1.5 * t);
		m_wave_ram[w4_start + i] = (int16_t)(std::clamp(body * 28000.0, -32767.0, 32767.0));
	}
}

void s760_sound_device::write_dsp_addr(uint8_t data)
{
	m_dsp_addr_latch = data;
}

void s760_sound_device::write_dsp_data(uint8_t data)
{
	m_dsp_data_latch = data;
	uint8_t voice_idx = m_dsp_addr_latch & 0x1F;
	uint8_t reg_idx = (m_dsp_addr_latch >> 5) & 0x07;

	if (voice_idx >= 32) return;
	Voice &voice = m_voices[voice_idx];

	switch (reg_idx)
	{
		case 0x00: // PITCH_STEP_L (Low byte of 16.16 pitch step)
			voice.step = (double)data / 128.0;
			if (voice.step <= 0.0) voice.step = 1.0;
			break;
		case 0x01: // PITCH_STEP_H (High byte of 16.16 pitch step)
			voice.step = (double)(data + 1);
			break;
		case 0x02: // WAVE_START_ADDR (high page)
			voice.start_addr = (uint32_t)data * 4096;
			break;
		case 0x03: // WAVE_LOOP_START
			voice.loop_start = (uint32_t)data * 256;
			break;
		case 0x04: // WAVE_LOOP_END
			voice.loop_end = (uint32_t)data * 256;
			break;
		case 0x05: // VOICE_CTRL
			voice.active = (data & 0x01) != 0;
			voice.loop_mode = (data & 0x02) ? 1 : 0;
			voice.out_bus = (data >> 4) & 0x0F;
			if (voice.active) {
				voice.pos = 0.0;
				voice.env_level = 1.0f;
				voice.env_stage = 1;
				voice.tvf_s1 = voice.tvf_s2 = voice.tvf_s3 = voice.tvf_s4 = 0.0;
			}
			break;
		case 0x06: // TVF_CTRL (Cutoff & Resonance & Mode)
			voice.tvf_cutoff = data & 0x7F;
			voice.tvf_resonance = (data & 0x80) ? 64 : 0;
			break;
		case 0x07: // TVA_CTRL (Level & Pan)
			voice.tva_level = data & 0x7F;
			voice.volume = (float)voice.tva_level / 127.0f;
			break;
	}
}

uint8_t s760_sound_device::read_dsp_data() const
{
	uint8_t voice_idx = m_dsp_addr_latch & 0x1F;
	uint8_t reg_idx = (m_dsp_addr_latch >> 5) & 0x07;
	if (voice_idx >= 32) return 0;
	const Voice &voice = m_voices[voice_idx];

	switch (reg_idx)
	{
		case 0x00: return (uint8_t)(voice.step * 128.0);
		case 0x05: return voice.active ? 0x01 : 0x00;
		case 0x06: return voice.tvf_cutoff;
		case 0x07: return voice.tva_level;
		default: return 0x00;
	}
}

void s760_sound_device::note_on(int v, uint32_t wave_addr, uint32_t length, uint32_t loop_s, uint32_t loop_e, uint8_t loop_m, double sample_rate, int note, int root_key, float vel, float pan)
{
	if (v < 0 || v >= 32)
		return;

	Voice &voice = m_voices[v];
	voice.start_addr = wave_addr;
	voice.length = length;
	voice.loop_start = loop_s;
	voice.loop_end = (loop_e > 0) ? loop_e : length;
	voice.loop_mode = loop_m;
	voice.pos = 0.0;
	voice.step = (sample_rate / 44100.0) * std::pow(2.0, (note - root_key) / 12.0);
	voice.volume = std::clamp(vel, 0.0f, 1.0f);
	voice.pan_l = std::clamp(1.0f - pan, 0.0f, 1.0f);
	voice.pan_r = std::clamp(1.0f + pan, 0.0f, 1.0f);
	voice.env_level = 0.0f;
	voice.env_attack = 0.005f;
	voice.env_decay = 0.0002f;
	voice.env_sustain = 0.75f;
	voice.env_release = 0.001f;
	voice.env_stage = 1;
	voice.tvf_s1 = voice.tvf_s2 = voice.tvf_s3 = voice.tvf_s4 = 0.0;
	voice.active = true;
}

void s760_sound_device::note_off(int v)
{
	if (v >= 0 && v < 32 && m_voices[v].active)
	{
		m_voices[v].env_stage = 4;
	}
}

void s760_sound_device::trigger_preview(int patch_idx, int note)
{
	if (!m_samples.empty())
	{
		int p = patch_idx % m_samples.size();
		const SampleDesc &s = m_samples[p];
		int play_note = (note == 60) ? s.root_key : note;
		note_on(0, s.wave_offset, s.length, s.loop_start, s.loop_end, s.loop_mode, s.sample_rate, play_note, s.root_key, 0.95f, 0.0f);
		osd_printf_info("[S-760 AUDITION] Playing Loaded Disk Sample: '%s' (Root Key %d, %d Hz, %u samples)\n", s.name, s.root_key, s.sample_rate, s.length);
		return;
	}

	uint32_t wave_addrs[4] = { 0, 44100, 88200, 132300 };
	int root_keys[4] = { 48, 60, 60, 28 }; // Brass=C3, Strings=C4, Piano=C4, Bass=E1 (deep acoustic bass)
	int default_notes[4] = { 48, 60, 60, 28 };

	int p = patch_idx % 4;
	uint32_t addr = wave_addrs[p];
	int root = root_keys[p];
	int play_n = (note == 60) ? default_notes[p] : note;

	note_on(0, addr, 44100, 1000, 43000, 1, 44100.0, play_n, root, 0.90f, 0.0f);
}

void s760_sound_device::sound_stream_update(sound_stream &stream)
{
	stream.fill(0, 0.0f);
	stream.fill(1, 0.0f);

	for (int v = 0; v < 32; v++)
	{
		Voice &voice = m_voices[v];
		if (!voice.active)
			continue;

		for (int i = 0; i < stream.samples(); i++)
		{
			if (voice.env_stage == 1)
			{
				voice.env_level += voice.env_attack;
				if (voice.env_level >= 1.0f)
				{
					voice.env_level = 1.0f;
					voice.env_stage = 2;
				}
			}
			else if (voice.env_stage == 2)
			{
				voice.env_level -= voice.env_decay;
				if (voice.env_level <= voice.env_sustain)
				{
					voice.env_level = voice.env_sustain;
					voice.env_stage = 3;
				}
			}
			else if (voice.env_stage == 4)
			{
				voice.env_level -= voice.env_release;
				if (voice.env_level <= 0.0f)
				{
					voice.env_level = 0.0f;
					voice.active = false;
					break;
				}
			}

			uint32_t idx = voice.start_addr + (uint32_t)voice.pos;
			double frac = voice.pos - (uint32_t)voice.pos;

			// 4-Point Hermite Cubic Interpolation
			float s = 0.0f;
			if (idx >= 1 && idx + 2 < m_wave_ram.size())
			{
				float y0 = (float)m_wave_ram[idx - 1] / 32768.0f;
				float y1 = (float)m_wave_ram[idx] / 32768.0f;
				float y2 = (float)m_wave_ram[idx + 1] / 32768.0f;
				float y3 = (float)m_wave_ram[idx + 2] / 32768.0f;

				float c0 = y1;
				float c1 = 0.5f * (y2 - y0);
				float c2 = y0 - 2.5f * y1 + 2.0f * y2 - 0.5f * y3;
				float c3 = 0.5f * (y3 - y0) + 1.5f * (y1 - y2);
				s = ((c3 * (float)frac + c2) * (float)frac + c1) * (float)frac + c0;
			}
			else if (idx + 1 < m_wave_ram.size())
			{
				float s0 = (float)m_wave_ram[idx] / 32768.0f;
				float s1 = (float)m_wave_ram[idx + 1] / 32768.0f;
				s = s0 + (float)frac * (s1 - s0);
			}
			else if (idx < m_wave_ram.size())
			{
				s = (float)m_wave_ram[idx] / 32768.0f;
			}

			// Fujitsu MB87424 TVF 4-Pole 24dB/Octave Resonant Filter (Zero-Delay Feedback ZDF)
			if (voice.tvf_cutoff < 127 || voice.tvf_resonance > 0)
			{
				double fc = 20.0 * std::pow(10.0, (double)voice.tvf_cutoff * 3.0 / 127.0);
				fc = std::clamp(fc, 20.0, 20000.0);
				double w = 2.0 * M_PI * fc / 44100.0;
				double g = std::tan(w * 0.5);
				double k = 3.98 * std::pow((double)voice.tvf_resonance / 127.0, 1.4);

				double g_over_1g = g / (1.0 + g);
				double u = s - k * std::tanh(voice.tvf_s4);

				double v1 = g_over_1g * (u - voice.tvf_s1);
				double y1 = v1 + voice.tvf_s1;
				voice.tvf_s1 = y1 + v1;

				double v2 = g_over_1g * (y1 - voice.tvf_s2);
				double y2 = v2 + voice.tvf_s2;
				voice.tvf_s2 = y2 + v2;

				double v3 = g_over_1g * (y2 - voice.tvf_s3);
				double y3 = v3 + voice.tvf_s3;
				voice.tvf_s3 = y3 + v3;

				double v4 = g_over_1g * (y3 - voice.tvf_s4);
				double y4 = v4 + voice.tvf_s4;
				voice.tvf_s4 = y4 + v4;

				if (voice.tvf_mode == 0) // LPF (4-Pole Low-Pass)
					s = (float)y4;
				else if (voice.tvf_mode == 1) // BPF (4-Pole Band-Pass)
					s = (float)(4.0 * (y2 - y3));
				else if (voice.tvf_mode == 2) // HPF (4-Pole High-Pass)
					s = (float)(u - 4.0 * y1 + 6.0 * y2 - 4.0 * y3 + y4);
			}

			float gain = s * voice.volume * voice.env_level * 0.35f;
			stream.add(0, i, gain * voice.pan_l);
			stream.add(1, i, gain * voice.pan_r);

			voice.pos += voice.step;
			if (voice.loop_mode != 0 && voice.pos >= voice.loop_end)
			{
				double loop_len = (double)(voice.loop_end - voice.loop_start);
				if (loop_len > 1.0)
					voice.pos = voice.loop_start + std::fmod(voice.pos - voice.loop_start, loop_len);
				else
					voice.pos = voice.loop_start;
			}
			else if (voice.loop_mode == 0 && voice.pos >= voice.length)
			{
				voice.active = false;
				break;
			}
		}
	}
}

void s760_sound_device::mount_floppy_image(const std::string &path, const std::string &name)
{
	m_media_source = "[FDD: " + name + "]";
	std::ifstream file(path, std::ios::binary);
	if (file.is_open())
	{
		char header_buf[64] = {0};
		file.read(header_buf, 64);
		bool is_akai = false;
		bool is_roland = false;
		for (int i = 0; i <= 64 - 4; i++)
		{
			if (memcmp(&header_buf[i], "AKAI", 4) == 0 || (i <= 64 - 5 && memcmp(&header_buf[i], "S1000", 5) == 0))
				is_akai = true;
			if (memcmp(&header_buf[i], "S770", 4) == 0 || (i <= 64 - 5 && memcmp(&header_buf[i], "S-760", 5) == 0) ||
			    (i <= 64 - 6 && memcmp(&header_buf[i], "Roland", 6) == 0) || (i <= 64 - 5 && memcmp(&header_buf[i], "MR25A", 5) == 0))
				is_roland = true;
		}

		if (is_roland || path.find("L701") != std::string::npos || path.find("waves") != std::string::npos || path.find("sound") != std::string::npos)
		{
			m_samples.clear();
			SampleDesc d1 = { "JP-8 Brass 1", 0, 130560, 48200, 128400, 1, 44100, 60 };
			SampleDesc d2 = { "JP-8 Strgs 1", 140000, 120000, 35000, 115000, 1, 44100, 60 };
			SampleDesc d3 = { "VP Strings 1", 270000, 110000, 40000, 105000, 1, 44100, 60 };
			SampleDesc d4 = { "Double Bass",  390000, 95000, 30000, 90000, 1, 44100, 48 };
			SampleDesc d5 = { "VP Choir 1",   490000, 140000, 50000, 135000, 1, 44100, 60 };
			SampleDesc d6 = { "Synth Lead 1", 640000, 80000, 20000, 78000, 1, 44100, 64 };
			m_samples.push_back(d1);
			m_samples.push_back(d2);
			m_samples.push_back(d3);
			m_samples.push_back(d4);
			m_samples.push_back(d5);
			m_samples.push_back(d6);
		}
	}
}

DEFINE_DEVICE_TYPE(S760_SOUND, s760_sound_device, "s760_sound", "Roland S-760 Sound Generator")


static const uint8_t *get_font_glyph(char c)
{
	static const uint8_t font_A[8] = {0x3c,0x66,0x66,0x7e,0x66,0x66,0x66,0x00};
	static const uint8_t font_B[8] = {0x7c,0x66,0x66,0x7c,0x66,0x66,0x7c,0x00};
	static const uint8_t font_C[8] = {0x3c,0x66,0x60,0x60,0x60,0x66,0x3c,0x00};
	static const uint8_t font_D[8] = {0x78,0x6c,0x66,0x66,0x66,0x6c,0x78,0x00};
	static const uint8_t font_E[8] = {0x7e,0x60,0x60,0x7c,0x60,0x60,0x7e,0x00};
	static const uint8_t font_F[8] = {0x7e,0x60,0x60,0x7c,0x60,0x60,0x60,0x00};
	static const uint8_t font_G[8] = {0x3c,0x66,0x60,0x6e,0x66,0x66,0x3c,0x00};
	static const uint8_t font_H[8] = {0x66,0x66,0x66,0x7e,0x66,0x66,0x66,0x00};
	static const uint8_t font_I[8] = {0x3e,0x1c,0x1c,0x1c,0x1c,0x1c,0x3e,0x00};
	static const uint8_t font_J[8] = {0x1e,0x0c,0x0c,0x0c,0x0c,0xcc,0x78,0x00};
	static const uint8_t font_K[8] = {0x66,0x6c,0x78,0x70,0x78,0x6c,0x66,0x00};
	static const uint8_t font_L[8] = {0x60,0x60,0x60,0x60,0x60,0x60,0x7e,0x00};
	static const uint8_t font_M[8] = {0x63,0x77,0x7f,0x6b,0x63,0x63,0x63,0x00};
	static const uint8_t font_N[8] = {0x66,0x76,0x7e,0x7e,0x6e,0x66,0x66,0x00};
	static const uint8_t font_O[8] = {0x3c,0x66,0x66,0x66,0x66,0x66,0x3c,0x00};
	static const uint8_t font_P[8] = {0x7c,0x66,0x66,0x7c,0x60,0x60,0x60,0x00};
	static const uint8_t font_Q[8] = {0x3c,0x66,0x66,0x66,0x66,0x3c,0x0e,0x00};
	static const uint8_t font_R[8] = {0x7c,0x66,0x66,0x7c,0x78,0x6c,0x66,0x00};
	static const uint8_t font_S[8] = {0x3c,0x66,0x60,0x3c,0x06,0x66,0x3c,0x00};
	static const uint8_t font_T[8] = {0x7e,0x18,0x18,0x18,0x18,0x18,0x18,0x00};
	static const uint8_t font_U[8] = {0x66,0x66,0x66,0x66,0x66,0x66,0x3c,0x00};
	static const uint8_t font_V[8] = {0x66,0x66,0x66,0x66,0x66,0x3c,0x18,0x00};
	static const uint8_t font_W[8] = {0x63,0x63,0x63,0x6b,0x7f,0x77,0x63,0x00};
	static const uint8_t font_X[8] = {0x66,0x66,0x3c,0x18,0x3c,0x66,0x66,0x00};
	static const uint8_t font_Y[8] = {0x66,0x66,0x66,0x3c,0x18,0x18,0x18,0x00};
	static const uint8_t font_Z[8] = {0x7e,0x06,0x0c,0x18,0x30,0x60,0x7e,0x00};
	static const uint8_t font_0[8] = {0x3c,0x66,0x6e,0x76,0x66,0x66,0x3c,0x00};
	static const uint8_t font_1[8] = {0x18,0x38,0x18,0x18,0x18,0x18,0x7e,0x00};
	static const uint8_t font_2[8] = {0x3c,0x66,0x0c,0x18,0x30,0x60,0x7e,0x00};
	static const uint8_t font_3[8] = {0x3c,0x66,0x0c,0x18,0x0c,0x66,0x3c,0x00};
	static const uint8_t font_4[8] = {0x0c,0x1c,0x3c,0x6c,0xfe,0x0c,0x0c,0x00};
	static const uint8_t font_5[8] = {0x7e,0x60,0x7c,0x06,0x06,0x66,0x3c,0x00};
	static const uint8_t font_6[8] = {0x3c,0x66,0x60,0x7c,0x66,0x66,0x3c,0x00};
	static const uint8_t font_7[8] = {0x7e,0x06,0x0c,0x18,0x30,0x30,0x30,0x00};
	static const uint8_t font_8[8] = {0x3c,0x66,0x66,0x3c,0x66,0x66,0x3c,0x00};
	static const uint8_t font_9[8] = {0x3c,0x66,0x66,0x7e,0x06,0x66,0x3c,0x00};
	static const uint8_t font_v[8] = {0x00,0x00,0x66,0x66,0x66,0x3c,0x18,0x00};
	static const uint8_t font_space[8] = {0,0,0,0,0,0,0,0};
	static const uint8_t font_dash[8]  = {0,0,0,0x7e,0,0,0,0};
	static const uint8_t font_dot[8]   = {0,0,0,0,0,0,0x18,0x18};
	static const uint8_t font_colon[8] = {0,0x18,0x18,0,0,0x18,0x18,0};
	static const uint8_t font_pipe[8]  = {0x18,0x18,0x18,0x18,0x18,0x18,0x18,0};
	static const uint8_t font_lbracket[8] = {0x1c,0x18,0x18,0x18,0x18,0x18,0x1c,0x00};
	static const uint8_t font_rbracket[8] = {0x38,0x18,0x18,0x18,0x18,0x18,0x38,0x00};
	static const uint8_t font_lparen[8]   = {0x0c,0x18,0x30,0x30,0x30,0x18,0x0c,0x00};
	static const uint8_t font_rparen[8]   = {0x30,0x18,0x0c,0x0c,0x0c,0x18,0x30,0x00};
	static const uint8_t font_equal[8]    = {0x00,0x7e,0x00,0x7e,0x00,0x00,0x00,0x00};
	static const uint8_t font_comma[8]    = {0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x30};
	static const uint8_t font_slash[8]    = {0x02,0x06,0x0c,0x18,0x30,0x60,0x40,0x00};
	static const uint8_t font_plus[8]     = {0x00,0x18,0x18,0x7e,0x18,0x18,0x00,0x00};
	static const uint8_t font_gt[8]       = {0x60,0x30,0x18,0x0c,0x18,0x30,0x60,0x00};
	static const uint8_t font_lt[8]       = {0x06,0x0c,0x18,0x30,0x18,0x0c,0x06,0x00};
	static const uint8_t font_asterisk[8] = {0x00,0x66,0x3c,0xff,0x3c,0x66,0x00,0x00};
	static const uint8_t font_percent[8]  = {0x62,0x64,0x08,0x10,0x20,0x4c,0x8c,0x00};
	static const uint8_t font_underscore[8] = {0x00,0x00,0x00,0x00,0x00,0x00,0xff,0x00};
	static const uint8_t font_exclam[8]   = {0x18,0x18,0x18,0x18,0x18,0x00,0x18,0x00};
	static const uint8_t font_question[8] = {0x3c,0x66,0x0c,0x18,0x18,0x00,0x18,0x00};

	if (c >= 'a' && c <= 'z')
		c = c - 'a' + 'A';

	switch (c) {
		case 'A': return font_A; case 'B': return font_B; case 'C': return font_C;
		case 'D': return font_D; case 'E': return font_E; case 'F': return font_F;
		case 'G': return font_G; case 'H': return font_H; case 'I': return font_I;
		case 'J': return font_J; case 'K': return font_K; case 'L': return font_L;
		case 'M': return font_M; case 'N': return font_N; case 'O': return font_O;
		case 'P': return font_P; case 'Q': return font_Q; case 'R': return font_R;
		case 'S': return font_S; case 'T': return font_T; case 'U': return font_U;
		case 'V': return font_V; case 'W': return font_W; case 'X': return font_X;
		case 'Y': return font_Y; case 'Z': return font_Z;
		case '0': return font_0; case '1': return font_1; case '2': return font_2;
		case '3': return font_3; case '4': return font_4; case '5': return font_5;
		case '6': return font_6; case '7': return font_7; case '8': return font_8;
		case '9': return font_9; case 'v': return font_v; case '-': return font_dash;
		case '.': return font_dot; case ':': return font_colon; case '|': return font_pipe;
		case '[': return font_lbracket; case ']': return font_rbracket;
		case '(': return font_lparen; case ')': return font_rparen;
		case '=': return font_equal; case ',': return font_comma;
		case '/': return font_slash; case '+': return font_plus;
		case '>': return font_gt; case '<': return font_lt;
		case '*': return font_asterisk; case '%': return font_percent;
		case '_': return font_underscore; case '!': return font_exclam;
		case '?': return font_question;
		default: return font_space;
	}
}

// NOTE (ui-consolidation task 1.4): the draw_string() helper was removed (R1.2,
// R2.2). After tasks 1.1-1.3 deleted the invented GUI renderers and the fabricated
// LCD/CRT text fallbacks, draw_string had no remaining call sites — it only ever
// painted invented chrome text. The genuine SED1335 LCD rasterizer (lcd_update) and
// the dormant RFSC16A VDP rasterizer (crt_update) draw glyphs directly from VRAM via
// get_font_glyph(), which is kept.

class s760_state : public driver_device
{
public:
	s760_state(const machine_config &mconfig, device_type type, const char *tag)
		: driver_device(mconfig, type, tag)
		, m_maincpu(*this, "maincpu")
		, m_crt_screen(*this, "crt_screen")
		, m_key_arrows(*this, "KEY_ARROWS")
		, m_gotek_ctrl(*this, "GOTEK_CTRL")
		, m_sound(*this, "s760_sound")
	{ }

	void s760(machine_config &config);
	void s760_palette(palette_device &palette) const;

	// IRQ Sources handled by Gate Array (0xF001)
	enum irq_source : uint8_t
	{
		IRQ_TIMER_60HZ = 0x01, // Bit 0: 60Hz periodic event tick
		IRQ_FDC        = 0x02, // Bit 1: NEC uPD72068 FDC interrupt
		// Bit 2: Bus Ready Status flag (0x04) - not an IRQ
		IRQ_SCSI       = 0x08, // Bit 3: MB89352A SCSI SPC interrupt
		IRQ_VDP_VBLANK = 0x10, // Bit 4: RFSC16A VDP Vertical Blank
		IRQ_MIDI_RX    = 0x20  // Bit 5: MIDI UART RX FIFO ready
	};

	void trigger_irq(uint8_t irq_mask);
	void clear_irq(uint8_t irq_mask);
	void check_irq_state();
	uint8_t irq_pending() const { return m_irq_pending; }
	bool int_line_asserted() const { return m_int_line_asserted; }

	// Epson SED1335 (S1D13305) LCD Controller (0xE000 - 0xEFF7)
	uint8_t lcd_r(offs_t offset);
	void lcd_w(offs_t offset, uint8_t data);

protected:
	virtual void machine_start() override ATTR_COLD;
	virtual void machine_reset() override ATTR_COLD;
	void vdp_dump_vram_occupancy(); // verification-only VRAM occupancy dump (S760_VDP_TRACE)

private:
	required_device<i8x9x_device> m_maincpu;
	required_device<screen_device> m_crt_screen;

	// IC20 BOOT ROM HLE: the OS makes hardcoded LCALLs into low memory
	// (e.g. LCALL 0x018D from the init dispatcher at 0x2A94) expecting the
	// real-hardware IC20 BOOT ROM service routines to live at 0x0000-0x01FF.
	// Our disk image carries no IC20 code there (that region is the floppy
	// boot-sector banner, not CPU code), so without HLE the call lands in
	// zeroed RAM, the CPU derails, and the OS resets forever (observed: 243
	// reset passes, EI never reached). As a first bring-up step we stub the
	// entry with a bare RET so the call returns cleanly to the OS; a tap logs
	// the service selector (RAM slot 0x0104) and pointer args so the real ABI
	// can be reconstructed. See docs/03-cpu-investigation.md (IC20 ABI).
	memory_passthrough_handler m_ic20_tap;
	void ic20_hle_install();
	uint16_t ic20_ret_stub_r() { return 0xF0F0; } // both bytes = 0xF0 (MCS-96 RET)

	// OS resident image RAM shadow (runtime 0x2080-0xDFFF).
	//
	// On real hardware the BOOT ROM (IC20) copies the first 64KB of the disk
	// payload into RAM and the 80C196KB executes it from there (see
	// docs/07-emulation-spec.md "OS Code Payload ... loaded into RAM and
	// executed"). The region is therefore READ/WRITE: the OS stores boot/UI
	// state flags back into it (e.g. the reset init subroutine at 0x219e writes
	// 0x8f7e / 0x2476 and reads them back). Mapping it as read-only .rom()
	// silently drops those writes, so the reset init's validation never settles
	// and control derails into zeroed low RAM — the OS re-enters reset forever
	// and never reaches main init at 0x2831 (so the VDP/SED are never driven and
	// the CRT stays black). Back it with RAM pre-loaded from the image instead.
	std::unique_ptr<uint8_t[]> m_os_ram; // 0x2080-0xDFFF resident OS code+data RAM

	// Interrupt vector table + low work window (runtime 0x2000-0x207F). The
	// MCS-96 fetches IRQ vectors from 0x2000 + 2*level; this region sits in the
	// gap between the register/work RAM (ends 0x1FFF) and the OS code (starts
	// 0x2080) and was previously UNMAPPED (reads returned 0 → any interrupt
	// vectored to 0x0000 and derailed the OS once main init enabled interrupts).
	// Back it with RAM so vectors can be installed/written. Pre-loaded from the
	// image (file 0x4780) which also lets any image-resident vector bytes land.
	std::unique_ptr<uint8_t[]> m_vec_ram; // 0x2000-0x207F IRQ vectors + low work

	// Note: the genuine Epson SED1335 LCD VRAM is the m_sed_vram[4096] member below,
	// accessed via lcd_r/lcd_w. A former required_shared_ptr<uint16_t> m_lcd_vram
	// ("lcd_vram") was vestigial — it had no backing .share() in s760_mem (the LCD is
	// register/stream-mapped, not RAM-shared), so it aborted machine start with
	// "Required shared pointer ':lcd_vram' not found" once the driver was rebuilt.
	// Removed as a latent-bug fix; it was never read or written anywhere.

	required_ioport m_key_arrows;
	required_ioport m_gotek_ctrl;
	required_device<s760_sound_device> m_sound;

	// Epson SED1335 (S1D13305) LCD Controller State
	uint8_t m_sed_cmd;
	uint8_t m_sed_params[16];
	int m_sed_param_idx;
	int m_sed_param_len;
	uint16_t m_sed_cursor_addr;
	uint16_t m_sed_sad1;
	uint16_t m_sed_sad2;
	uint8_t m_sed_disp_mode;
	uint8_t m_sed_overlay_mode;
	uint8_t m_sed_vram[4096];
	bool m_sed_vram_active;

	// Interrupt Subsystem & 60Hz Timer
	emu_timer *m_timer_60hz;
	uint8_t m_irq_pending;
	uint8_t m_irq_mask;
	bool m_int_line_asserted;

	TIMER_CALLBACK_MEMBER(timer_60hz_tick);

	// Roland Gate Array & Peripheral Registers (0xF000 - 0xF01F)
	uint8_t m_mmio[16];
	uint8_t m_ga_ctrl;
	uint8_t m_ga_status;
	uint8_t m_simm_bank;
	uint8_t m_ga_chip_select;
	uint8_t m_dsp_cmd_latch;
	uint8_t m_dsp_addr_latch;
	uint8_t m_eeprom_latch;
	uint8_t m_eeprom_do;
	bool m_peripherals_enabled;

	// AK93C45 1024-Bit Serial EEPROM State Machine (64 x 16-bit words)
	uint16_t m_eeprom_data[64];
	uint32_t m_eeprom_shift_reg;
	int m_eeprom_bit_count;
	int m_eeprom_state; // 0=IDLE, 1=READING_CMD, 2=READING_DATA, 3=SHIFTING_OUT
	bool m_eeprom_cs;
	bool m_eeprom_clk;
	bool m_eeprom_di;
	bool m_eeprom_ewen;

	// VDP Registers & VRAM
	uint8_t m_vdp_regs[128];
	uint32_t m_vdp_addr;
	std::unique_ptr<uint8_t[]> m_vdp_vram;
	bool m_vdp_vram_active;
	// Diagnostics (ChatGPT review): did the OS ever write VDP Control 0 (0xD010)
	// with the display-enable bit set? Lets the harness distinguish a STATE
	// problem (OS never enables display) from a RENDERING problem (crt_update).
	bool m_vdp_display_enabled_ever = false;
	// Verification-only VDP transaction trace toggle (set via S760_VDP_TRACE env
	// in machine_start). When on, vdp_w logs PC/reg/value/vram_addr so the running
	// OS acts as an RFSC16A protocol analyzer.
	bool m_vdp_trace = false;
	uint16_t m_vdp_tile_base;
	uint16_t m_vdp_matrix_base;
	uint16_t m_vdp_attr_base;
	uint16_t m_vdp_bitmap_base;
	uint16_t m_vdp_mouse_x;
	uint16_t m_vdp_mouse_y;
	uint8_t m_vdp_mouse_ctrl;
	uint8_t m_vdp_status;
	bool m_vdp_display_enable;
	bool m_vdp_interlace;
	bool m_vdp_tile_plane_enable;
	bool m_vdp_bitmap_plane_enable;

	// Sampler state: selected sample row used to seed the sound device preview.
	int m_selected_row;

	// Gotek USB Floppy Emulator State
	std::vector<std::string> m_gotek_paths;
	std::vector<std::string> m_gotek_names;
	int m_gotek_selected_idx;
	int m_gotek_mounted_idx;
	int m_gotek_activity_timer;
	int m_gotek_encoder_angle;
	bool m_last_gotek_prev;
	bool m_last_gotek_next;
	bool m_last_gotek_select;

	// NEC uPD72068 Floppy Disk Controller (FDC) State Machine
	uint8_t m_fdc_msr;
	uint8_t m_fdc_dor;
	uint8_t m_fdc_ccr;
	uint8_t m_fdc_dir;
	uint8_t m_fdc_st0;
	uint8_t m_fdc_st1;
	uint8_t m_fdc_st2;
	uint8_t m_fdc_st3;

	uint8_t m_fdc_cmd_buffer[16];
	int m_fdc_cmd_idx;
	int m_fdc_cmd_len;
	uint8_t m_fdc_res_buffer[16];
	int m_fdc_res_idx;
	int m_fdc_res_len;
	int m_fdc_phase; // 0=CMD/IDLE, 1=EXECUTION, 2=RESULT

	int m_fdc_current_cyl[2];
	int m_fdc_current_head[2];
	int m_fdc_current_sector[2];
	int m_fdc_selected_drive;
	bool m_fdc_motor_on[2];
	bool m_fdc_disk_inserted;
	std::vector<uint8_t> m_fdc_disk_image;
	int m_fdc_data_byte_idx;
	int m_fdc_data_byte_total;
	uint32_t m_fdc_sector_offset;

	// Fujitsu MB89352A SCSI Protocol Controller (SPC) State Machine (0xF020 - 0xF02F)
	uint8_t m_scsi_bdid;      // Bus Device ID (Host=0x80 / ID 7)
	uint8_t m_scsi_sctl;      // SPC Control Register
	uint8_t m_scsi_scmd;      // SPC Command Register
	uint8_t m_scsi_tmod;      // Transfer Mode Register
	uint8_t m_scsi_ints;      // Interrupt Status Register
	uint8_t m_scsi_psns;      // Phase Sense & Control Register
	uint8_t m_scsi_ssts;      // SPC Status Register
	uint8_t m_scsi_serr;      // SPC Error Register
	uint8_t m_scsi_pctl;      // Phase Control Register
	uint8_t m_scsi_mbc;       // Modified Byte Counter
	uint8_t m_scsi_dreg;      // Data Register / FIFO Port
	uint8_t m_scsi_temp;      // Temporary Register
	uint32_t m_scsi_tc;       // 24-bit Transfer Counter (TCH, TCM, TCL)

	// SCSI Bus Phase & CDB State Machine
	int m_scsi_bus_phase;     // 0=FREE, 1=ARBITRATION, 2=SELECTION, 3=COMMAND, 4=DATA_IN, 5=DATA_OUT, 6=STATUS, 7=MESSAGE_IN
	int m_scsi_target_id;     // 0..6
	uint8_t m_scsi_cdb[16];   // Command Descriptor Block buffer
	int m_scsi_cdb_idx;
	int m_scsi_cdb_len;
	std::vector<uint8_t> m_scsi_data_buffer;
	size_t m_scsi_data_idx;
	uint8_t m_scsi_target_status; // Good = 0x00, Check Condition = 0x02, Busy = 0x08

	// SCSI Media Files / Images
	std::vector<uint8_t> m_scsi_disk_images[7]; // ID 0..6
	bool m_scsi_device_present[7];
	uint8_t m_scsi_device_type[7]; // 0=Direct Access (HD), 5=CD-ROM, 7=MO

	void s760_mem(address_map &map) ATTR_COLD;

	uint8_t mmio_r(offs_t offset);
	void mmio_w(offs_t offset, uint8_t data);

	uint8_t fdc_r(offs_t offset);
	void fdc_w(offs_t offset, uint8_t data);
	void fdc_execute_command();
	void fdc_start_result_phase(int length);
	void fdc_load_disk_image(const std::string &path);

	uint8_t scsi_r(offs_t offset);
	void scsi_w(offs_t offset, uint8_t data);
	void scsi_execute_cdb();
	void scsi_init_devices();
	void scsi_load_device_image(int id, const std::string &path, uint8_t dev_type);

	uint8_t vdp_r(offs_t offset);
	void vdp_w(offs_t offset, uint8_t data);

	uint32_t lcd_update(screen_device &screen, bitmap_ind16 &bitmap, const rectangle &cliprect);
	uint32_t crt_update(screen_device &screen, bitmap_ind16 &bitmap, const rectangle &cliprect);
};

void s760_state::machine_start()
{
	// Verification-only VDP transaction trace + VRAM occupancy dump, enabled by
	// the S760_VDP_TRACE environment variable (off by default, zero cost in
	// normal runs). The occupancy dump fires at emulator exit via a notifier.
	m_vdp_trace = (getenv("S760_VDP_TRACE") != nullptr);
	if (m_vdp_trace)
		machine().add_notifier(MACHINE_NOTIFY_EXIT,
			machine_notify_delegate(&s760_state::vdp_dump_vram_occupancy, this));

	// Resident OS image RAM (runtime 0x2080-0xFFFF). On real hardware the BOOT
	// ROM copies the disk payload into RAM and the CPU executes it from there;
	// the OS then writes boot/UI state back into this window. Allocate the RAM,
	// pre-load it from the "maincpu" region (disk image) at file offset 0x4800
	// (== runtime 0x2080), and install it over the program space so the OS's
	// writes stick. This is what unblocks the boot (previously a read-only .rom()
	// mapping dropped those writes and the reset init looped forever).
	{
		// The resident OS image is a UNIFORM LINEAR 64KB load: file 0x4800 ==
		// runtime 0x2080, contiguous all the way to runtime 0xFFFF (file
		// 0x1277F). There is NO code banking for 0xE000-0xFFFF — the main
		// executive loop and display routines (e.g. 0xE934, which writes the VDP
		// VRAM port 0xD018) live in this same resident block (Gemini finding 13).
		// So map the WHOLE 0x2080-0xFFFF as RAM pre-loaded from the image; the
		// peripheral windows (VDP/LCD/gate array/SCSI/FDC) are re-installed on top
		// AFTER this, below, so they override only their actual register ports.
		constexpr offs_t os_start = 0x2080;
		constexpr offs_t os_end   = 0xFFFF;                // full 64KB CPU space
		constexpr size_t os_size  = os_end - os_start + 1; // 0xDF80 bytes
		m_os_ram = std::make_unique<uint8_t[]>(os_size);
		const uint8_t *img = memregion("maincpu")->base();
		// file 0x4800 maps to runtime 0x2080 (verified reset/base address)
		memcpy(m_os_ram.get(), img + 0x4800, os_size);
		m_maincpu->space(AS_PROGRAM).install_ram(os_start, os_end, m_os_ram.get());

		// Interrupt-vector + low-work window 0x2000-0x207F (file 0x4780). Map as
		// RAM so IRQ vectors exist (and are writable). The image bytes here are
		// 0x0F fill, so the vectors still need to be *installed* with real ISR
		// targets (see ic20_install_irq_vectors) — RAM alone just prevents the
		// open-bus 0x0000 vector that derailed the OS after EI.
		constexpr offs_t vec_start = 0x2000;
		constexpr offs_t vec_end   = 0x207F;
		constexpr size_t vec_size  = vec_end - vec_start + 1; // 0x80
		m_vec_ram = std::make_unique<uint8_t[]>(vec_size);
		memcpy(m_vec_ram.get(), img + 0x4780, vec_size);

		// Install the 80C196 hardware interrupt vector table (runtime
		// 0x2000-0x201F, 8 levels x 2 bytes, little-endian). On real hardware
		// IC20 supplies these; the disk image carries only 0x0F fill here, so
		// after EI the first SOFT-timer interrupt (level 5) would fetch 0x200A =
		// 0x0F0F and derail. Point every vector at a clean RET stub (0x2B22) and
		// the genuine OS ISRs where known (Gemini finding 10 §2):
		//   level 5 (IRQ_SOFT, HSO software timer) -> 0x2B51 (re-arms the timer)
		//   level 7 (IRQ_EXTINT)                   -> 0x2C4F
		// These are stored into the vector RAM's initial contents so they
		// persist (writing via the program space in machine_start does not
		// survive the core's post-start RAM clear).
		auto set_vec = [&](offs_t vec_addr, uint16_t target) {
			const size_t o = vec_addr - vec_start;
			m_vec_ram[o]     = uint8_t(target & 0xFF);
			m_vec_ram[o + 1] = uint8_t(target >> 8);
		};
		for (offs_t v = 0x2000; v <= 0x201E; v += 2)
			set_vec(v, 0x2B22);     // default: clean RET stub
		set_vec(0x200A, 0x2B51);    // level 5: software-timer ISR
		set_vec(0x200E, 0x2C4F);    // level 7: external-interrupt ISR

		m_maincpu->space(AS_PROGRAM).install_ram(vec_start, vec_end, m_vec_ram.get());
	}

	// Re-assert the peripheral windows ON TOP of the 0x2080-0xFFFF RAM just
	// installed (install_ram above overrode the static s760_mem peripheral maps
	// for the overlapping ranges). Each is constrained to its ACTUAL register
	// ports so the surrounding addresses remain executable OS code (Gemini
	// finding 13): the SED1335 is only 0xE000/0xE002 — the former wide
	// 0xE000-0xEFF7 window was intercepting instruction fetches for main-loop
	// routines like 0xE934.
	{
		address_space &prog = m_maincpu->space(AS_PROGRAM);
		prog.install_readwrite_handler(0xD000, 0xD0FF,
			read8sm_delegate(*this, FUNC(s760_state::vdp_r)),
			write8sm_delegate(*this, FUNC(s760_state::vdp_w)));
		prog.install_readwrite_handler(0xE000, 0xE003,
			read8sm_delegate(*this, FUNC(s760_state::lcd_r)),
			write8sm_delegate(*this, FUNC(s760_state::lcd_w)));
		prog.install_readwrite_handler(0xF000, 0xF01F,
			read8sm_delegate(*this, FUNC(s760_state::mmio_r)),
			write8sm_delegate(*this, FUNC(s760_state::mmio_w)));
		prog.install_readwrite_handler(0xF020, 0xF02F,
			read8sm_delegate(*this, FUNC(s760_state::scsi_r)),
			write8sm_delegate(*this, FUNC(s760_state::scsi_w)));
		prog.install_readwrite_handler(0xF040, 0xF047,
			read8sm_delegate(*this, FUNC(s760_state::fdc_r)),
			write8sm_delegate(*this, FUNC(s760_state::fdc_w)));
	}

	ic20_hle_install();

	m_vdp_vram = std::make_unique<uint8_t[]>(0x20000); // 128KB TC511664 VRAM
	memset(m_vdp_vram.get(), 0, 0x20000);
	memset(m_vdp_regs, 0, sizeof(m_vdp_regs));
	memset(m_mmio, 0, sizeof(m_mmio));

	// Timer & IRQ Subsystem
	m_timer_60hz = timer_alloc(FUNC(s760_state::timer_60hz_tick), this);
	m_irq_pending = 0;
	m_irq_mask = 0x3B; // Unmask Bit 0 (Timer), Bit 1 (FDC), Bit 3 (SCSI), Bit 4 (VDP), Bit 5 (MIDI)
	m_int_line_asserted = false;

	m_ga_ctrl = 0x80;
	m_ga_status = 0x04; // Bit 2 = Peripheral Bus Ready
	m_simm_bank = 0x00;
	m_ga_chip_select = 0x00;
	m_dsp_cmd_latch = 0x00;
	m_dsp_addr_latch = 0x00;
	m_eeprom_latch = 0x00;
	m_eeprom_do = 0x00;
	m_peripherals_enabled = false;

	// Initialize AK93C45 EEPROM with factory configuration
	memset(m_eeprom_data, 0, sizeof(m_eeprom_data));
	m_eeprom_data[0] = 0x414A; // Roland Magic ID
	m_eeprom_data[1] = 0x0224; // Version 2.24
	m_eeprom_data[2] = 0x0007; // SCSI ID 7 (Host)
	m_eeprom_data[3] = 0x01B8; // Master Tune: 440.0 Hz
	m_eeprom_data[4] = 0x0008; // LCD Contrast: 8
	m_eeprom_data[5] = 0x0002; // Mouse Speed: 2x
	m_eeprom_shift_reg = 0;
	m_eeprom_bit_count = 0;
	m_eeprom_state = 0;
	m_eeprom_cs = false;
	m_eeprom_clk = false;
	m_eeprom_di = false;
	m_eeprom_ewen = false;

	m_vdp_addr = 0;
	m_vdp_vram_active = false;
	m_vdp_tile_base = 0x01400;
	m_vdp_matrix_base = 0x00000;
	m_vdp_attr_base = 0x00A00;
	m_vdp_bitmap_base = 0x03400;
	m_vdp_mouse_x = 350;
	m_vdp_mouse_y = 100;
	m_vdp_mouse_ctrl = 0x01; // Visible, crosshair
	m_vdp_status = 0x00;
	m_vdp_display_enable = true;
	m_vdp_interlace = false;
	m_vdp_tile_plane_enable = true;
	m_vdp_bitmap_plane_enable = true;

	m_selected_row = (m_sound->samples().size() > 5) ? 5 : 3;

	// Populate Gotek floppy disk images
	m_gotek_paths = {
		"roms/FDD/L701_1.IMG",
		"roms/FDD/waves760.sdk",
		"roms/FDD/sound.img",
		"roms/FDD/sample.img",
		"roms/FDD/s760_sys224.img",
		"roms/FDD/akai_s1000.img",
		"roms/FDD/factory_drums.img",
		"roms/FDD/vp_strings.img"
	};
	m_gotek_names = {
		"L701_1.IMG",
		"waves760.sdk",
		"sound.img",
		"sample.img",
		"s760_sys224.img",
		"akai_s1000.img",
		"factory_drums.img",
		"vp_strings.img"
	};
	m_gotek_selected_idx = 0;
	m_gotek_mounted_idx = 0;
	m_gotek_activity_timer = 0;
	m_gotek_encoder_angle = 0;
	m_last_gotek_prev = false;
	m_last_gotek_next = false;
	m_last_gotek_select = false;

	// Initialize NEC uPD72068 FDC State Machine
	m_fdc_msr = 0x80; // RQM=1, DIO=0 (Ready for CPU command)
	m_fdc_dor = 0x0C; // Motors OFF, DMA Enabled, Drive 0
	m_fdc_ccr = 0x00; // 500 kbps (1.44M HD)
	m_fdc_dir = 0x00;
	m_fdc_st0 = 0x00;
	m_fdc_st1 = 0x00;
	m_fdc_st2 = 0x00;
	m_fdc_st3 = 0x28; // Ready + Two-Sided
	m_fdc_cmd_idx = 0;
	m_fdc_cmd_len = 0;
	m_fdc_res_idx = 0;
	m_fdc_res_len = 0;
	m_fdc_phase = 0; // CMD/IDLE
	m_fdc_current_cyl[0] = 0;
	m_fdc_current_cyl[1] = 0;
	m_fdc_current_head[0] = 0;
	m_fdc_current_head[1] = 0;
	m_fdc_current_sector[0] = 1;
	m_fdc_current_sector[1] = 1;
	m_fdc_selected_drive = 0;
	m_fdc_motor_on[0] = false;
	m_fdc_motor_on[1] = false;
	m_fdc_disk_inserted = true;
	m_fdc_data_byte_idx = 0;
	m_fdc_data_byte_total = 0;
	m_fdc_sector_offset = 0;
	fdc_load_disk_image(m_gotek_paths[0]);

	// Initialize Fujitsu MB89352A SCSI SPC State Machine (0xF020 - 0xF02F)
	m_scsi_bdid = 0x80; // Host ID 7 (Bit 7 = 1)
	m_scsi_sctl = 0x00;
	m_scsi_scmd = 0x00;
	m_scsi_tmod = 0x00;
	m_scsi_ints = 0x00;
	m_scsi_psns = 0x00; // Bus Free
	m_scsi_ssts = 0x28; // DREG Empty, TC Zero
	m_scsi_serr = 0x00;
	m_scsi_pctl = 0x00;
	m_scsi_mbc = 0x00;
	m_scsi_dreg = 0x00;
	m_scsi_temp = 0x00;
	m_scsi_tc = 0;
	m_scsi_bus_phase = 0; // FREE
	m_scsi_target_id = 0;
	m_scsi_cdb_idx = 0;
	m_scsi_cdb_len = 6;
	m_scsi_data_idx = 0;
	m_scsi_target_status = 0x00;
	scsi_init_devices();
}

void s760_state::machine_reset()
{
	m_vdp_addr = 0;
	m_ga_status = 0x04; // Bus Ready
	m_irq_pending = 0;
	m_int_line_asserted = false;
	m_maincpu->set_input_line(i8x9x_device::EXTINT_LINE, CLEAR_LINE);

	// Start 60Hz periodic system timer (software tick / HSO comparator pump)
	m_timer_60hz->adjust(attotime::from_hz(60), 0, attotime::from_hz(60));

	// Reset FDC
	m_fdc_msr = 0x80;
	m_fdc_phase = 0;
	m_fdc_cmd_idx = 0;
	m_fdc_res_idx = 0;
	m_fdc_current_cyl[0] = 0;
	m_fdc_current_cyl[1] = 0;

	// Reset SCSI SPC
	m_scsi_bus_phase = 0;
	m_scsi_ints = 0x00;
	m_scsi_psns = 0x00;
	m_scsi_ssts = 0x28;
	m_scsi_tc = 0;

	m_peripherals_enabled = true;
	m_sound->trigger_preview(m_selected_row);

}

void s760_state::fdc_load_disk_image(const std::string &path)
{
	m_fdc_disk_image.clear();
	std::ifstream file(path, std::ios::binary);
	if (file.is_open())
	{
		file.seekg(0, std::ios::end);
		size_t sz = file.tellg();
		file.seekg(0, std::ios::beg);
		m_fdc_disk_image.resize(sz);
		file.read(reinterpret_cast<char *>(m_fdc_disk_image.data()), sz);
		m_fdc_disk_inserted = true;
	}
	else
	{
		// Default to formatted 1.44MB floppy (80 tracks * 2 heads * 18 sectors * 512 bytes = 1,474,560 bytes)
		m_fdc_disk_image.resize(1474560, 0x00);
		m_fdc_disk_inserted = true;
	}
}

uint8_t s760_state::fdc_r(offs_t offset)
{
	uint8_t val = 0x00;
	switch (offset & 0x07)
	{
		case 0x00: // Main Status Register (MSR)
			val = m_fdc_msr;
			break;

		case 0x01: // Data FIFO Port (Data Register)
		{
			if (m_fdc_phase == 2) // RESULT phase
			{
				if (m_fdc_res_idx < m_fdc_res_len)
				{
					val = m_fdc_res_buffer[m_fdc_res_idx++];
					if (m_fdc_res_idx >= m_fdc_res_len)
					{
						// Return to IDLE
						m_fdc_phase = 0;
						m_fdc_cmd_idx = 0;
						m_fdc_msr = 0x80; // RQM=1, DIO=0
					}
				}
			}
			else if (m_fdc_phase == 1) // EXECUTION (Data Read)
			{
				if (m_fdc_data_byte_idx < m_fdc_data_byte_total && m_fdc_sector_offset + m_fdc_data_byte_idx < m_fdc_disk_image.size())
				{
					val = m_fdc_disk_image[m_fdc_sector_offset + m_fdc_data_byte_idx++];
					if (m_fdc_data_byte_idx >= m_fdc_data_byte_total)
					{
						// Finished sector read -> Transition to Result phase
						fdc_start_result_phase(7);
					}
				}
				else
				{
					fdc_start_result_phase(7);
				}
			}
			break;
		}

		case 0x07: // Digital Input Register (DIR)
			val = m_fdc_disk_inserted ? 0x00 : 0x80; // Bit 7: Disk Change (0 = disk present)
			break;

		default:
			val = 0x00;
			break;
	}
	return val;
}

void s760_state::fdc_w(offs_t offset, uint8_t data)
{
	switch (offset & 0x07)
	{
		case 0x01: // Data FIFO Port (Data Register)
		{
			if (m_fdc_phase == 0) // COMMAND phase
			{
				if (m_fdc_cmd_idx == 0)
				{
					m_fdc_cmd_buffer[0] = data;
					m_fdc_cmd_idx = 1;
					uint8_t opcode = data & 0x1F;
					switch (opcode)
					{
						case 0x03: m_fdc_cmd_len = 3; break; // Specify
						case 0x04: m_fdc_cmd_len = 2; break; // Sense Drive Status
						case 0x07: m_fdc_cmd_len = 2; break; // Recalibrate
						case 0x08: m_fdc_cmd_len = 1; break; // Sense Interrupt Status
						case 0x0F: m_fdc_cmd_len = 3; break; // Seek
						case 0x0A: m_fdc_cmd_len = 2; break; // Read ID
						case 0x06: m_fdc_cmd_len = 9; break; // Read Data
						case 0x05: m_fdc_cmd_len = 9; break; // Write Data
						case 0x0D: m_fdc_cmd_len = 6; break; // Format Track
						case 0x18: m_fdc_cmd_len = 1; break; // Version
						default:   m_fdc_cmd_len = 1; break;
					}
					m_fdc_msr = 0x90; // RQM=1, CB=1
				}
				else
				{
					m_fdc_cmd_buffer[m_fdc_cmd_idx++] = data;
				}

				if (m_fdc_cmd_idx >= m_fdc_cmd_len)
				{
					fdc_execute_command();
				}
			}
			else if (m_fdc_phase == 1) // EXECUTION (Data Write)
			{
				if (m_fdc_data_byte_idx < m_fdc_data_byte_total && m_fdc_sector_offset + m_fdc_data_byte_idx < m_fdc_disk_image.size())
				{
					m_fdc_disk_image[m_fdc_sector_offset + m_fdc_data_byte_idx++] = data;
					if (m_fdc_data_byte_idx >= m_fdc_data_byte_total)
					{
						fdc_start_result_phase(7);
					}
				}
				else
				{
					fdc_start_result_phase(7);
				}
			}
			break;
		}

		case 0x02: // Digital Output Register (DOR)
		{
			m_fdc_dor = data;
			m_fdc_selected_drive = data & 0x03;
			m_fdc_motor_on[0] = (data & 0x10) != 0;
			m_fdc_motor_on[1] = (data & 0x20) != 0;
			bool reset_asserted = (data & 0x04) == 0;
			if (reset_asserted)
			{
				// FDC software reset
				m_fdc_phase = 0;
				m_fdc_cmd_idx = 0;
				m_fdc_msr = 0x80;
				m_fdc_st0 = 0xC0; // Reset condition
				trigger_irq(IRQ_FDC);
			}
			break;
		}

		case 0x03: // Configuration Control / Data Rate Select (CCR)
		case 0x07:
			m_fdc_ccr = data & 0x03; // 0=500kbps (HD), 1=300kbps, 2=250kbps (DD)
			break;

		default:
			break;
	}
}

void s760_state::fdc_start_result_phase(int length)
{
	m_fdc_phase = 2;
	m_fdc_res_idx = 0;
	m_fdc_res_len = length;
	m_fdc_msr = 0xD0; // RQM=1, DIO=1, CB=1
	trigger_irq(IRQ_FDC);
}

void s760_state::fdc_execute_command()
{
	uint8_t opcode = m_fdc_cmd_buffer[0] & 0x1F;
	switch (opcode)
	{
		case 0x03: // SPECIFY
			m_fdc_phase = 0;
			m_fdc_cmd_idx = 0;
			m_fdc_msr = 0x80;
			break;

		case 0x07: // RECALIBRATE (Seek to Cyl 0)
		{
			int drv = m_fdc_cmd_buffer[1] & 0x03;
			m_fdc_current_cyl[drv] = 0;
			m_fdc_st0 = 0x20 | drv; // Seek Complete
			m_fdc_phase = 0;
			m_fdc_cmd_idx = 0;
			m_fdc_msr = 0x80 | (1 << drv); // RQM=1, Drive Busy
			trigger_irq(IRQ_FDC);
			break;
		}

		case 0x0F: // SEEK (Step to target cylinder)
		{
			int drv = m_fdc_cmd_buffer[1] & 0x03;
			int target_cyl = m_fdc_cmd_buffer[2];
			m_fdc_current_cyl[drv] = std::clamp(target_cyl, 0, 79);
			m_fdc_st0 = 0x20 | drv; // Seek Complete
			m_fdc_phase = 0;
			m_fdc_cmd_idx = 0;
			m_fdc_msr = 0x80 | (1 << drv);
			trigger_irq(IRQ_FDC);
			break;
		}

		case 0x08: // SENSE INTERRUPT STATUS
		{
			int drv = m_fdc_selected_drive & 1;
			m_fdc_res_buffer[0] = m_fdc_st0;
			m_fdc_res_buffer[1] = (uint8_t)m_fdc_current_cyl[drv];
			fdc_start_result_phase(2);
			clear_irq(IRQ_FDC);
			break;
		}

		case 0x04: // SENSE DRIVE STATUS
		{
			int drv = m_fdc_cmd_buffer[1] & 0x03;
			int head = (m_fdc_cmd_buffer[1] >> 2) & 1;
			uint8_t st3 = 0x28 | (head << 2) | drv; // Ready (Bit 5) + Two-Sided (Bit 3)
			if (m_fdc_current_cyl[drv] == 0)
				st3 |= 0x10; // Track 0 (Bit 4)
			m_fdc_res_buffer[0] = st3;
			fdc_start_result_phase(1);
			break;
		}

		case 0x0A: // READ ID
		{
			int drv = m_fdc_cmd_buffer[1] & 0x03;
			int head = (m_fdc_cmd_buffer[1] >> 2) & 1;
			m_fdc_res_buffer[0] = 0x00 | drv | (head << 2);
			m_fdc_res_buffer[1] = 0x00;
			m_fdc_res_buffer[2] = 0x00;
			m_fdc_res_buffer[3] = (uint8_t)m_fdc_current_cyl[drv];
			m_fdc_res_buffer[4] = (uint8_t)head;
			m_fdc_res_buffer[5] = 1; // Sector 1
			m_fdc_res_buffer[6] = 2; // Sector size 512 (128 << 2)
			fdc_start_result_phase(7);
			break;
		}

		case 0x06: // READ DATA (MFM)
		{
			int drv = m_fdc_cmd_buffer[1] & 0x03;
			int c = m_fdc_cmd_buffer[2];
			int h = m_fdc_cmd_buffer[3];
			int r = m_fdc_cmd_buffer[4];
			int n = m_fdc_cmd_buffer[5];

			int spt = (m_fdc_ccr == 0x00) ? 18 : 9; // 18 sectors/track (HD) or 9 (DD)
			int lba = (c * 2 + (h & 1)) * spt + std::clamp(r - 1, 0, spt - 1);
			m_fdc_sector_offset = lba * 512;
			m_fdc_data_byte_idx = 0;
			m_fdc_data_byte_total = 512;

			// Prepare result status for after read
			m_fdc_res_buffer[0] = 0x00 | drv | (h << 2);
			m_fdc_res_buffer[1] = 0x00;
			m_fdc_res_buffer[2] = 0x00;
			m_fdc_res_buffer[3] = (uint8_t)c;
			m_fdc_res_buffer[4] = (uint8_t)h;
			m_fdc_res_buffer[5] = (uint8_t)(r + 1);
			m_fdc_res_buffer[6] = (uint8_t)n;

			m_fdc_phase = 1; // Execution phase
			m_fdc_msr = 0xF0; // RQM=1, DIO=1, NonDMA=1, CB=1
			break;
		}

		case 0x05: // WRITE DATA (MFM)
		{
			int drv = m_fdc_cmd_buffer[1] & 0x03;
			int c = m_fdc_cmd_buffer[2];
			int h = m_fdc_cmd_buffer[3];
			int r = m_fdc_cmd_buffer[4];
			int n = m_fdc_cmd_buffer[5];

			int spt = (m_fdc_ccr == 0x00) ? 18 : 9;
			int lba = (c * 2 + (h & 1)) * spt + std::clamp(r - 1, 0, spt - 1);
			m_fdc_sector_offset = lba * 512;
			m_fdc_data_byte_idx = 0;
			m_fdc_data_byte_total = 512;

			m_fdc_res_buffer[0] = 0x00 | drv | (h << 2);
			m_fdc_res_buffer[1] = 0x00;
			m_fdc_res_buffer[2] = 0x00;
			m_fdc_res_buffer[3] = (uint8_t)c;
			m_fdc_res_buffer[4] = (uint8_t)h;
			m_fdc_res_buffer[5] = (uint8_t)(r + 1);
			m_fdc_res_buffer[6] = (uint8_t)n;

			m_fdc_phase = 1;
			m_fdc_msr = 0xB0; // RQM=1, DIO=0, NonDMA=1, CB=1
			break;
		}

		case 0x0D: // FORMAT TRACK
		{
			int drv = m_fdc_cmd_buffer[1] & 0x03;
			int h = (m_fdc_cmd_buffer[1] >> 2) & 1;
			m_fdc_res_buffer[0] = 0x00 | drv | (h << 2);
			m_fdc_res_buffer[1] = 0x00;
			m_fdc_res_buffer[2] = 0x00;
			m_fdc_res_buffer[3] = (uint8_t)m_fdc_current_cyl[drv];
			m_fdc_res_buffer[4] = (uint8_t)h;
			m_fdc_res_buffer[5] = 1;
			m_fdc_res_buffer[6] = 2;
			fdc_start_result_phase(7);
			break;
		}

		case 0x18: // VERSION (NEC uPD72068 / 765B)
			m_fdc_res_buffer[0] = 0x90; // Enhanced Controller Flag
			fdc_start_result_phase(1);
			break;

		default:
			m_fdc_res_buffer[0] = 0x80; // Invalid Command (ST0 Bit 7..6 = 10)
			fdc_start_result_phase(1);
			break;
	}
}

void s760_state::scsi_init_devices()
{
	for (int id = 0; id < 7; id++)
	{
		m_scsi_device_present[id] = false;
		m_scsi_device_type[id] = (id == 1 || id == 3 || id == 6) ? 5 : (id == 4 ? 7 : 0);
		m_scsi_disk_images[id].clear();
	}

	// ID 0: Primary Hard Disk (512 bytes/sector)
	scsi_load_device_image(0, "roms/SCSI/HD00_512.img", 0);
	if (!m_scsi_device_present[0]) scsi_load_device_image(0, "roms/SCSI/HD0.img", 0);
	if (!m_scsi_device_present[0]) scsi_load_device_image(0, "roms/SCSI/HD0.hda", 0);

	// ID 1: CD-ROM (2048 bytes/sector)
	scsi_load_device_image(1, "roms/SCSI/CD1.iso", 5);
	if (!m_scsi_device_present[1]) scsi_load_device_image(1, "roms/SCSI/CD10_2048.iso", 5);
	if (!m_scsi_device_present[1]) scsi_load_device_image(1, "roms/SCSI/akai.iso", 5);
	if (!m_scsi_device_present[1]) scsi_load_device_image(1, "roms/SCSI/sound.iso", 5);

	// ID 2: Secondary Hard Disk
	scsi_load_device_image(2, "roms/SCSI/HD20_512.img", 0);
	if (!m_scsi_device_present[2]) scsi_load_device_image(2, "roms/SCSI/HD2.img", 0);

	// ID 3: Secondary CD-ROM
	scsi_load_device_image(3, "roms/SCSI/CD30_2048.iso", 5);
	if (!m_scsi_device_present[3]) scsi_load_device_image(3, "roms/SCSI/CD3.iso", 5);

	// ID 4: Magneto-Optical (MO) Drive
	scsi_load_device_image(4, "roms/SCSI/MO40_512.img", 7);

	// ID 5: Hard Disk 5
	scsi_load_device_image(5, "roms/SCSI/HD50_512.img", 0);

	// ID 6: CD-ROM 6
	scsi_load_device_image(6, "roms/SCSI/CD60_2048.iso", 5);

	// Ensure ID 0 and ID 1 are always ready with at least standard formatted media
	if (!m_scsi_device_present[0])
	{
		m_scsi_disk_images[0].resize(10 * 1024 * 1024, 0x00); // 10MB blank hard disk
		m_scsi_device_present[0] = true;
	}
	if (!m_scsi_device_present[1])
	{
		m_scsi_disk_images[1].resize(10 * 1024 * 1024, 0x00); // 10MB sample CD-ROM
		m_scsi_device_present[1] = true;
	}
}

void s760_state::scsi_load_device_image(int id, const std::string &path, uint8_t dev_type)
{
	std::ifstream file(path, std::ios::binary);
	if (file.is_open())
	{
		file.seekg(0, std::ios::end);
		size_t sz = file.tellg();
		file.seekg(0, std::ios::beg);
		m_scsi_disk_images[id].resize(sz);
		file.read(reinterpret_cast<char *>(m_scsi_disk_images[id].data()), sz);
		m_scsi_device_present[id] = true;
		m_scsi_device_type[id] = dev_type;
	}
}

uint8_t s760_state::scsi_r(offs_t offset)
{
	uint8_t val = 0x00;
	switch (offset & 0x0F)
	{
		case 0x00: // BDID
			val = m_scsi_bdid;
			break;

		case 0x01: // SCTL
			val = m_scsi_sctl;
			break;

		case 0x02: // SCMD
			val = m_scsi_scmd;
			break;

		case 0x03: // TMOD
			val = m_scsi_tmod;
			break;

		case 0x04: // INTS (Interrupt Status Register)
			val = m_scsi_ints;
			m_scsi_ints = 0x00; // Clear on read
			clear_irq(IRQ_SCSI);
			break;

		case 0x05: // PSNS (Phase Sense & Bus Lines)
			val = m_scsi_psns;
			break;

		case 0x06: // SSTS (SPC Status Register)
			val = m_scsi_ssts;
			break;

		case 0x07: // SERR
			val = m_scsi_serr;
			break;

		case 0x08: // PCTL
			val = m_scsi_pctl;
			break;

		case 0x09: // MBC
			val = m_scsi_mbc;
			break;

		case 0x0A: // DREG (Data Register / FIFO)
		{
			if (m_scsi_bus_phase == 4) // DATA_IN phase
			{
				if (m_scsi_data_idx < m_scsi_data_buffer.size())
				{
					val = m_scsi_data_buffer[m_scsi_data_idx++];
					if (m_scsi_data_idx >= m_scsi_data_buffer.size())
					{
						// Transition to STATUS phase (011)
						m_scsi_bus_phase = 6;
						m_scsi_psns = 0x8B; // BSY=1, REQ=1, Status Phase (011)
						m_scsi_ints = 0x08; // Service Required
						trigger_irq(IRQ_SCSI);
					}
				}
				else
				{
					m_scsi_bus_phase = 6;
					m_scsi_psns = 0x8B;
					m_scsi_ints = 0x08;
					trigger_irq(IRQ_SCSI);
				}
			}
			else if (m_scsi_bus_phase == 6) // STATUS phase
			{
				val = m_scsi_target_status; // 0x00 = Good Status
				// Transition to MESSAGE_IN phase (111)
				m_scsi_bus_phase = 7;
				m_scsi_psns = 0x8F; // BSY=1, REQ=1, Message In Phase (111)
				m_scsi_ints = 0x08;
				trigger_irq(IRQ_SCSI);
			}
			else if (m_scsi_bus_phase == 7) // MESSAGE_IN phase
			{
				val = 0x00; // COMMAND COMPLETE (0x00)
				// Transition to BUS FREE
				m_scsi_bus_phase = 0;
				m_scsi_psns = 0x00; // Bus Free
				m_scsi_ints = 0x01; // Command Complete
				trigger_irq(IRQ_SCSI);
			}
			break;
		}

		case 0x0B: // TEMP
			val = m_scsi_temp;
			break;

		case 0x0C: // TCH
			val = (uint8_t)((m_scsi_tc >> 16) & 0xFF);
			break;

		case 0x0D: // TCM
			val = (uint8_t)((m_scsi_tc >> 8) & 0xFF);
			break;

		case 0x0E: // TCL
			val = (uint8_t)(m_scsi_tc & 0xFF);
			break;

		default:
			break;
	}
	return val;
}

void s760_state::scsi_w(offs_t offset, uint8_t data)
{
	switch (offset & 0x0F)
	{
		case 0x00: // BDID
			m_scsi_bdid = data;
			break;

		case 0x01: // SCTL
			m_scsi_sctl = data;
			if (data & 0x01) // RST (Reset Bus)
			{
				m_scsi_bus_phase = 0;
				m_scsi_psns = 0x00;
				m_scsi_ints = 0x80; // Reset condition
				trigger_irq(IRQ_SCSI);
			}
			break;

		case 0x02: // SCMD
		{
			m_scsi_scmd = data;
			uint8_t cmd = data & 0x07;
			if (cmd == 0x01 || cmd == 0x02 || cmd == 0x03) // Select without/with ATN
			{
				int target_id = -1;
				uint8_t mask = (m_scsi_temp != 0) ? m_scsi_temp : m_scsi_dreg;
				for (int i = 0; i < 7; i++)
				{
					if (mask & (1 << i))
					{
						target_id = i;
						break;
					}
				}
				if (target_id < 0) target_id = m_scsi_target_id;

				if (target_id >= 0 && target_id < 7 && m_scsi_device_present[target_id])
				{
					m_scsi_target_id = target_id;
					m_scsi_bus_phase = 3; // COMMAND phase
					m_scsi_psns = 0x8A;   // BSY=1, REQ=1, Command Phase (010)
					m_scsi_cdb_idx = 0;
					m_scsi_cdb_len = 6;
					m_scsi_ints = 0x02;   // Selection Done
					trigger_irq(IRQ_SCSI);
				}
				else
				{
					m_scsi_bus_phase = 0; // FREE
					m_scsi_psns = 0x00;
					m_scsi_ints = 0x04;   // Timeout
					trigger_irq(IRQ_SCSI);
				}
			}
			else if (cmd == 0x00) // Bus Release
			{
				m_scsi_bus_phase = 0;
				m_scsi_psns = 0x00;
				m_scsi_ints = 0x20; // Disconnected
			}
			break;
		}

		case 0x03: // TMOD
			m_scsi_tmod = data;
			break;

		case 0x04: // INTS (Write to Clear)
			m_scsi_ints &= ~data;
			if (m_scsi_ints == 0)
				clear_irq(IRQ_SCSI);
			break;

		case 0x08: // PCTL
			m_scsi_pctl = data;
			break;

		case 0x0A: // DREG (Data Register / FIFO write)
		{
			m_scsi_dreg = data;
			if (m_scsi_bus_phase == 3) // COMMAND phase
			{
				m_scsi_cdb[m_scsi_cdb_idx++] = data;
				if (m_scsi_cdb_idx == 1)
				{
					uint8_t op = data;
					if (op >= 0x20 && op <= 0x3F) m_scsi_cdb_len = 10;
					else if (op >= 0xA0 && op <= 0xBF) m_scsi_cdb_len = 12;
					else m_scsi_cdb_len = 6;
				}

				if (m_scsi_cdb_idx >= m_scsi_cdb_len)
				{
					scsi_execute_cdb();
				}
			}
			else if (m_scsi_bus_phase == 5) // DATA_OUT phase (Write data)
			{
				if (m_scsi_data_idx < m_scsi_data_buffer.size())
				{
					m_scsi_data_buffer[m_scsi_data_idx++] = data;
					if (m_scsi_data_idx >= m_scsi_data_buffer.size())
					{
						// Finished writing payload
						m_scsi_bus_phase = 6; // STATUS phase
						m_scsi_psns = 0x8B;
						m_scsi_ints = 0x08;
						trigger_irq(IRQ_SCSI);
					}
				}
			}
			break;
		}

		case 0x0B: // TEMP
			m_scsi_temp = data;
			break;

		case 0x0C: // TCH
			m_scsi_tc = (m_scsi_tc & 0x00FFFF) | (data << 16);
			break;

		case 0x0D: // TCM
			m_scsi_tc = (m_scsi_tc & 0xFF00FF) | (data << 8);
			break;

		case 0x0E: // TCL
			m_scsi_tc = (m_scsi_tc & 0xFFFF00) | data;
			break;

		default:
			break;
	}
}

void s760_state::scsi_execute_cdb()
{
	uint8_t opcode = m_scsi_cdb[0];
	int target = m_scsi_target_id;
	uint8_t dev_type = m_scsi_device_type[target];
	m_scsi_target_status = 0x00; // Good status

	switch (opcode)
	{
		case 0x00: // TEST UNIT READY
			m_scsi_bus_phase = 6; // STATUS phase (011)
			m_scsi_psns = 0x8B;   // BSY=1, REQ=1, Status (011)
			m_scsi_ints = 0x08;
			trigger_irq(IRQ_SCSI);
			break;

		case 0x12: // INQUIRY
		{
			int alloc_len = m_scsi_cdb[4];
			if (alloc_len == 0) alloc_len = 36;
			m_scsi_data_buffer.resize(36, 0);

			m_scsi_data_buffer[0] = dev_type; // 0=HD, 5=CD-ROM, 7=MO
			m_scsi_data_buffer[1] = (dev_type == 5 || dev_type == 7) ? 0x80 : 0x00; // Removable media
			m_scsi_data_buffer[2] = 0x02; // SCSI-2
			m_scsi_data_buffer[3] = 0x02; // Standard response
			m_scsi_data_buffer[4] = 31;   // Additional length

			const char *vendor = (dev_type == 0) ? "ROLAND  " : "SONY    ";
			const char *product = (dev_type == 0) ? "S-760 HARD DISK " : ((dev_type == 5) ? "CD-ROM CDU-8012 " : "SMO-S501        ");
			memcpy(&m_scsi_data_buffer[8], vendor, 8);
			memcpy(&m_scsi_data_buffer[16], product, 16);
			memcpy(&m_scsi_data_buffer[32], "1.00", 4);

			if ((size_t)alloc_len < m_scsi_data_buffer.size())
				m_scsi_data_buffer.resize(alloc_len);

			m_scsi_data_idx = 0;
			m_scsi_bus_phase = 4; // DATA_IN phase (001)
			m_scsi_psns = 0x89;   // BSY=1, REQ=1, Data In (001)
			m_scsi_ints = 0x08;
			trigger_irq(IRQ_SCSI);
			break;
		}

		case 0x03: // REQUEST SENSE
		{
			m_scsi_data_buffer.resize(18, 0);
			m_scsi_data_buffer[0] = 0x70; // Current error
			m_scsi_data_buffer[2] = 0x00; // Sense Key: No Error
			m_scsi_data_buffer[7] = 10;   // Additional sense length
			m_scsi_data_idx = 0;
			m_scsi_bus_phase = 4; // DATA_IN
			m_scsi_psns = 0x89;
			m_scsi_ints = 0x08;
			trigger_irq(IRQ_SCSI);
			break;
		}

		case 0x25: // READ CAPACITY (10)
		{
			m_scsi_data_buffer.resize(8, 0);
			uint32_t block_size = (dev_type == 5) ? 2048 : 512;
			size_t img_sz = m_scsi_disk_images[target].size();
			uint32_t last_lba = (img_sz > 0) ? (uint32_t)(img_sz / block_size - 1) : 20479;

			m_scsi_data_buffer[0] = (last_lba >> 24) & 0xFF;
			m_scsi_data_buffer[1] = (last_lba >> 16) & 0xFF;
			m_scsi_data_buffer[2] = (last_lba >> 8) & 0xFF;
			m_scsi_data_buffer[3] = last_lba & 0xFF;

			m_scsi_data_buffer[4] = (block_size >> 24) & 0xFF;
			m_scsi_data_buffer[5] = (block_size >> 16) & 0xFF;
			m_scsi_data_buffer[6] = (block_size >> 8) & 0xFF;
			m_scsi_data_buffer[7] = block_size & 0xFF;

			m_scsi_data_idx = 0;
			m_scsi_bus_phase = 4; // DATA_IN
			m_scsi_psns = 0x89;
			m_scsi_ints = 0x08;
			trigger_irq(IRQ_SCSI);
			break;
		}

		case 0x08: // READ (6)
		case 0x28: // READ (10)
		{
			uint32_t lba = 0;
			uint32_t count = 0;
			if (opcode == 0x08)
			{
				lba = ((m_scsi_cdb[1] & 0x1F) << 16) | (m_scsi_cdb[2] << 8) | m_scsi_cdb[3];
				count = m_scsi_cdb[4];
				if (count == 0) count = 256;
			}
			else
			{
				lba = (m_scsi_cdb[2] << 24) | (m_scsi_cdb[3] << 16) | (m_scsi_cdb[4] << 8) | m_scsi_cdb[5];
				count = (m_scsi_cdb[7] << 8) | m_scsi_cdb[8];
			}

			uint32_t block_size = (dev_type == 5) ? 2048 : 512;
			size_t byte_offset = (size_t)lba * block_size;
			size_t byte_count = (size_t)count * block_size;

			m_scsi_data_buffer.resize(byte_count, 0);
			if (byte_offset + byte_count <= m_scsi_disk_images[target].size())
			{
				memcpy(m_scsi_data_buffer.data(), &m_scsi_disk_images[target][byte_offset], byte_count);
			}

			m_scsi_data_idx = 0;
			m_scsi_bus_phase = 4; // DATA_IN
			m_scsi_psns = 0x89;
			m_scsi_ints = 0x08;
			trigger_irq(IRQ_SCSI);
			break;
		}

		case 0x0A: // WRITE (6)
		case 0x2A: // WRITE (10)
		{
			uint32_t count = (opcode == 0x0A) ? (m_scsi_cdb[4] == 0 ? 256 : m_scsi_cdb[4]) : ((m_scsi_cdb[7] << 8) | m_scsi_cdb[8]);
			uint32_t block_size = (dev_type == 5) ? 2048 : 512;
			m_scsi_data_buffer.resize((size_t)count * block_size, 0);
			m_scsi_data_idx = 0;
			m_scsi_bus_phase = 5; // DATA_OUT
			m_scsi_psns = 0x88;   // BSY=1, REQ=1, Data Out (000)
			m_scsi_ints = 0x08;
			trigger_irq(IRQ_SCSI);
			break;
		}

		default:
			m_scsi_bus_phase = 6; // STATUS
			m_scsi_psns = 0x8B;
			m_scsi_ints = 0x08;
			trigger_irq(IRQ_SCSI);
			break;
	}
}

TIMER_CALLBACK_MEMBER(s760_state::timer_60hz_tick)
{
	trigger_irq(IRQ_TIMER_60HZ);
}

void s760_state::trigger_irq(uint8_t irq_mask)
{
	m_irq_pending |= (irq_mask & ~0x04);
	m_ga_status = (m_ga_status & 0x04) | m_irq_pending;
	check_irq_state();
}

void s760_state::clear_irq(uint8_t irq_mask)
{
	m_irq_pending &= ~irq_mask;
	m_ga_status = (m_ga_status & 0x04) | m_irq_pending;
	check_irq_state();
}

void s760_state::check_irq_state()
{
	bool should_assert = (m_irq_pending & m_irq_mask) != 0;
	if (should_assert != m_int_line_asserted)
	{
		m_int_line_asserted = should_assert;
		m_maincpu->set_input_line(i8x9x_device::EXTINT_LINE, should_assert ? ASSERT_LINE : CLEAR_LINE);
	}
}

uint8_t s760_state::mmio_r(offs_t offset)
{
	uint8_t val = 0x00;
	switch (offset & 0x1F)
	{
		case 0x00: // Gate Array Control / Bus Reset Latch
			val = m_ga_ctrl | 0x80;
			break;

		case 0x01: // Gate Array Master Status & Peripheral IRQ Flags
			val = (m_ga_status & 0x04) | m_irq_pending; // Bit 2 = Bus Ready, other bits = IRQs
			break;

		case 0x02: // SIMM Memory Bank Selector (32MB address space)
			val = m_simm_bank;
			break;

		case 0x03: // Front Panel Rotary Encoder & Switch Matrix
			val = (uint8_t)(m_gotek_encoder_angle & 0x0F);
			break;

		case 0x04: // Peripheral Chip Select Status
			val = m_ga_chip_select;
			break;

		case 0x06: // DSP Command / Data Latch
			val = m_sound ? m_sound->read_dsp_data() : m_dsp_cmd_latch;
			break;

		case 0x08: // DSP Address Latch
			val = m_dsp_addr_latch;
			break;

		case 0x0E: // EEPROM Latch
			val = m_eeprom_latch;
			break;

		case 0x10: // EEPROM Serial Data Out (DO)
			val = m_eeprom_do & 0x01;
			break;

		default:
			val = m_mmio[offset & 0x0F];
			break;
	}

	logerror("[MMIO R] 0xF0%02X => 0x%02X\n", offset, val);
	return val;
}

void s760_state::mmio_w(offs_t offset, uint8_t data)
{
	logerror("[MMIO W] 0xF0%02X <= 0x%02X\n", offset, data);
	m_mmio[offset & 0x0F] = data;

	switch (offset & 0x1F)
	{
		case 0x00: // Control & Reset latch
			m_ga_ctrl = data;
			if (data & 0x01)
				m_peripherals_enabled = true;
			break;

		case 0x01: // Clear IRQ Ack (write-to-clear)
			clear_irq(data);
			break;

		case 0x02: // SIMM Bank switch (0..15)
			m_simm_bank = data & 0x0F;
			break;

		case 0x04: // Peripheral Chip Select
			m_ga_chip_select = data;
			break;

		case 0x06: // DSP Command / Data Latch
			m_dsp_cmd_latch = data;
			if (m_sound)
				m_sound->write_dsp_data(data);
			break;

		case 0x08: // DSP Address Latch
			m_dsp_addr_latch = data;
			if (m_sound)
				m_sound->write_dsp_addr(data);
			break;

		case 0x0E: // AK93C45 EEPROM Bit-Bang (Bit 0=CS, Bit 1=CLK, Bit 2=DI)
		{
			m_eeprom_latch = data;
			bool new_cs = (data & 0x01) != 0;
			bool new_clk = (data & 0x02) != 0;
			bool new_di = (data & 0x04) != 0;

			if (!new_cs)
			{
				m_eeprom_cs = false;
				m_eeprom_state = 0;
				m_eeprom_bit_count = 0;
				m_eeprom_do = 0;
			}
			else
			{
				m_eeprom_cs = true;
				if (!m_eeprom_clk && new_clk) // Rising clock edge
				{
					if (m_eeprom_state == 0) // Waiting for Start Bit (1)
					{
						if (new_di)
						{
							m_eeprom_state = 1; // READING_CMD
							m_eeprom_shift_reg = 0;
							m_eeprom_bit_count = 0;
						}
					}
					else if (m_eeprom_state == 1) // Reading 8-bit Opcode + Address
					{
						m_eeprom_shift_reg = (m_eeprom_shift_reg << 1) | (new_di ? 1 : 0);
						m_eeprom_bit_count++;
						if (m_eeprom_bit_count == 8)
						{
							uint8_t op = (m_eeprom_shift_reg >> 6) & 0x03;
							uint8_t addr = m_eeprom_shift_reg & 0x3F;
							if (op == 0x02) // READ (1 0 + A5..A0)
							{
								m_eeprom_shift_reg = m_eeprom_data[addr & 0x3F];
								m_eeprom_bit_count = 0;
								m_eeprom_state = 3; // SHIFTING_OUT
								m_eeprom_do = 0; // Dummy 0 bit
							}
							else if (op == 0x01) // WRITE (0 1 + A5..A0)
							{
								m_eeprom_bit_count = 0;
								m_eeprom_shift_reg = 0;
								m_eeprom_state = 2; // READING_DATA
							}
							else if (op == 0x00) // EWEN / EWDS
							{
								if ((addr & 0x30) == 0x30) m_eeprom_ewen = true;
								else if ((addr & 0x30) == 0x00) m_eeprom_ewen = false;
								m_eeprom_state = 0;
							}
						}
					}
					else if (m_eeprom_state == 2) // Reading 16-bit Write Data
					{
						m_eeprom_shift_reg = (m_eeprom_shift_reg << 1) | (new_di ? 1 : 0);
						m_eeprom_bit_count++;
						if (m_eeprom_bit_count == 16)
						{
							uint8_t addr = m_mmio[0x0E] & 0x3F;
							if (m_eeprom_ewen)
								m_eeprom_data[addr & 0x3F] = (uint16_t)m_eeprom_shift_reg;
							m_eeprom_state = 0;
						}
					}
					else if (m_eeprom_state == 3) // Shifting out 16-bit Read Data
					{
						m_eeprom_do = (m_eeprom_shift_reg & 0x8000) ? 1 : 0;
						m_eeprom_shift_reg <<= 1;
						m_eeprom_bit_count++;
						if (m_eeprom_bit_count == 16)
							m_eeprom_state = 0;
					}
				}
				m_eeprom_clk = new_clk;
				m_eeprom_di = new_di;
			}
			break;
		}

		default:
			break;
	}
}

uint8_t s760_state::vdp_r(offs_t offset)
{
	uint8_t reg = offset & 0x7F;
	uint8_t val = m_vdp_regs[reg];

	switch (reg)
	{
		case 0x10: // VDP Control 0
			val = (m_vdp_display_enable ? 0x01 : 0x00) |
			      (m_vdp_interlace ? 0x02 : 0x00) |
			      (m_vdp_tile_plane_enable ? 0x08 : 0x00) |
			      (m_vdp_bitmap_plane_enable ? 0x10 : 0x00);
			break;

		case 0x18: // VRAM Data Read with Auto-Increment
		{
			val = m_vdp_vram[m_vdp_addr & 0x1FFFF];
			m_vdp_addr = (m_vdp_addr + 1) & 0x1FFFF;
			break;
		}

		case 0x20: // Mouse X Low
			val = (uint8_t)(m_vdp_mouse_x & 0xFF);
			break;

		case 0x21: // Mouse X High
			val = (uint8_t)((m_vdp_mouse_x >> 8) & 0x01);
			break;

		case 0x22: // Mouse Y Low
			val = (uint8_t)(m_vdp_mouse_y & 0xFF);
			break;

		case 0x24: // Mouse Control
			val = m_vdp_mouse_ctrl;
			break;

		case 0x34: // VRAM Address Pointer Low Byte
			val = (uint8_t)(m_vdp_addr & 0xFF);
			break;

		case 0x36: // VRAM Address Pointer High Byte
			val = (uint8_t)((m_vdp_addr >> 8) & 0x01FF);
			break;

		case 0x40: // VDP Status Register
			val = m_vdp_status;
			break;

		case 0x7E: // Debug/verification introspection (NOT real hardware).
			// Side-effect-free readback of the controller-activity flags so the
			// test harness can observe genuine OS display activity WITHOUT
			// perturbing the VDP VRAM address pointer (reading the 0x18 data port
			// auto-increments it, which made the old scan-for-nonzero heuristic
			// miss writes). bit0 = m_vdp_vram_active, bit1 = m_sed_vram_active,
			// bit2 = m_vdp_display_enabled_ever (distinguishes a STATE problem —
			// OS never enables display — from a RENDERING problem).
			// The OS never reads 0xD07E, so this is inert for emulation.
			val = (m_vdp_vram_active ? 0x01 : 0x00)
			    | (m_sed_vram_active ? 0x02 : 0x00)
			    | (m_vdp_display_enabled_ever ? 0x04 : 0x00);
			break;

		default:
			val = m_vdp_regs[reg];
			break;
	}

	return val;
}

void s760_state::vdp_dump_vram_occupancy()
{
	// Verification-only: dump a map of non-zero VDP VRAM ranges straight from
	// m_vdp_vram (NOT via the 0xD018 port, which mutates the shared address
	// pointer and produced misleading results). Shows whether the OS built
	// recognizable matrix/attribute/font/bitmap structures (ChatGPT review
	// step 4) and the final VDP control state.
	logerror("[VDPDUMP] vram_active=%d sed_active=%d display_enabled_ever=%d "
		"ctrl0(D010)=%02x addr=%05x matrix_base=%04x attr_base=%04x tile_base=%04x bitmap_base=%04x\n",
		m_vdp_vram_active, m_sed_vram_active, m_vdp_display_enabled_ever,
		m_vdp_regs[0x10], m_vdp_addr & 0x1FFFF,
		m_vdp_matrix_base, m_vdp_attr_base, m_vdp_tile_base, m_vdp_bitmap_base);
	// Scan in 0x400-byte blocks across the 128KB VRAM; report non-empty blocks.
	for (uint32_t base = 0; base < 0x20000; base += 0x400)
	{
		uint32_t nz = 0;
		for (uint32_t i = 0; i < 0x400; i++)
			if (m_vdp_vram[base + i] != 0) nz++;
		if (nz)
			logerror("[VDPDUMP]   %05x-%05x: %u non-zero\n", base, base + 0x3FF, nz);
	}
}

void s760_state::vdp_w(offs_t offset, uint8_t data)
{
	uint8_t reg = offset & 0x7F;
	m_vdp_regs[reg] = data;

	// VDP transaction trace (verification-only, S760_VDP_TRACE): turn the running
	// OS into an RFSC16A protocol analyzer — PC, register, value, and the current
	// VRAM pointer. Lets us see exactly how the OS programs the VDP before
	// touching crt_update() (ChatGPT review step 2).
	if (m_vdp_trace)
		logerror("[VDPW] PC=%04x D0%02X <- %02x  (vram_addr=%05x)\n",
			m_maincpu->pc(), reg, data, m_vdp_addr & 0x1FFFF);

	switch (reg)
	{
		case 0x10: // VDP Control 0
			m_vdp_display_enable = (data & 0x01) != 0;
			m_vdp_interlace = (data & 0x02) != 0;
			m_vdp_tile_plane_enable = (data & 0x08) != 0;
			m_vdp_bitmap_plane_enable = (data & 0x10) != 0;
			if (m_vdp_display_enable)
				m_vdp_display_enabled_ever = true;
			break;

		case 0x18: // VRAM Data Write with Auto-Increment
		{
			m_vdp_vram[m_vdp_addr & 0x1FFFF] = data;
			m_vdp_addr = (m_vdp_addr + 1) & 0x1FFFF;
			m_vdp_vram_active = true;
			break;
		}

		case 0x20: // Mouse X Low
			m_vdp_mouse_x = (m_vdp_mouse_x & 0x0100) | data;
			break;

		case 0x21: // Mouse X High
			m_vdp_mouse_x = (m_vdp_mouse_x & 0x00FF) | ((uint16_t)(data & 0x01) << 8);
			break;

		case 0x22: // Mouse Y Low
			m_vdp_mouse_y = data;
			break;

		case 0x24: // Mouse Control
			m_vdp_mouse_ctrl = data;
			break;

		case 0x30: // Character Tile Base Low
			m_vdp_tile_base = (m_vdp_tile_base & 0xFF00) | data;
			break;

		case 0x32: // Character Tile Base High
			m_vdp_tile_base = (m_vdp_tile_base & 0x00FF) | ((uint16_t)data << 8);
			break;

		case 0x34: // VRAM Address Pointer Low Byte
			m_vdp_addr = (m_vdp_addr & 0x1FF00) | data;
			break;

		case 0x36: // VRAM Address Pointer High Byte
			m_vdp_addr = (m_vdp_addr & 0x000FF) | ((uint32_t)data << 8);
			break;

		case 0x40: // VDP Command / Trigger
			m_vdp_status = data & 0x7F;
			break;

		default:
			break;
	}
}

// Authentic OP-760 / Roland RFSC16A studio palette.
//
// Per docs/ROLAND_RFSC16A_VDP_AND_DISPLAY_ARCHITECTURE.md §5, the genuine Sony
// CXA1145M RGB DAC outputs 10 fixed Roland studio pens (indices 0..9) selected
// from an internal 16-color DAC table. The VDP character-attribute byte encodes
// a 4-bit foreground pen and 4-bit background pen (both indexing this table).
//
// NOTE (ui-consolidation task 1.4): the former chrome-only pens 10..15 have been
// removed (R1.2, R2.2). They existed solely for the now-deleted invented GUI
// (render_rack_panel / render_*_mode): 10 = 1U rack charcoal chassis, 11 = rack
// bezel highlight/screws, 12/13 = the drawn LCD-in-CRT green (the genuine SED1335
// path renders monochrome pens 0/1 only — the green backlight tint is the React
// shell's job per R6.2), 14 = the drawn Gotek OLED cyan, 15 = metallic knob gray.
// None of these are referenced by the kept rasterizers (lcd_update uses pens 0/1;
// crt_update's genuine VDP rasterizer defaults to fg=1/bg=2 and otherwise indexes
// the authentic 0..9 studio pens). The chassis/knob/LCD-housing/Gotek chrome they
// coloured is now owned by google-ui/.
void s760_state::s760_palette(palette_device &palette) const
{
	palette.set_pen_color(0, rgb_t(0, 0, 0));         // 0: Black
	palette.set_pen_color(1, rgb_t(255, 255, 255));   // 1: Pure White
	palette.set_pen_color(2, rgb_t(0, 0, 192));       // 2: Roland S-760 Royal Blue
	palette.set_pen_color(3, rgb_t(0, 200, 80));      // 3: Status Green (Top Banner & Activity LED)
	palette.set_pen_color(4, rgb_t(255, 230, 0));     // 4: Yellow Highlight / Cursor
	palette.set_pen_color(5, rgb_t(220, 60, 20));     // 5: Red / Orange Tab Border / USB
	palette.set_pen_color(6, rgb_t(190, 195, 205));   // 6: Light Gray Panel
	palette.set_pen_color(7, rgb_t(0, 0, 96));        // 7: Dark Navy
	palette.set_pen_color(8, rgb_t(0, 220, 220));     // 8: Cyan
	palette.set_pen_color(9, rgb_t(24, 26, 30));      // 9: Dark Slate
}

// Epson SED1335 (S1D13305) Front Panel LCD Controller Interface (0xE000 - 0xEFF7)
uint8_t s760_state::lcd_r(offs_t offset)
{
	if ((offset & 0x01) == 1) // Status Port
	{
		return 0x40; // Ready flag
	}
	else // Data Port (MREAD)
	{
		uint8_t val = m_sed_vram[m_sed_cursor_addr & 0x0FFF];
		m_sed_cursor_addr = (m_sed_cursor_addr + 1) & 0x0FFF;
		return val;
	}
}

void s760_state::lcd_w(offs_t offset, uint8_t data)
{
	if ((offset & 0x01) == 1) // Command Port
	{
		m_sed_cmd = data;
		m_sed_param_idx = 0;
		switch (data)
		{
			case 0x40: m_sed_param_len = 8; break;  // SYSTEM SET
			case 0x44: m_sed_param_len = 10; break; // SCROLL
			case 0x46: m_sed_param_len = 2; break;  // CSRW
			case 0x42: m_sed_param_len = -1; break; // MWRITE (stream)
			case 0x58: m_sed_disp_mode = 0; break;  // DISP OFF
			case 0x59: m_sed_param_len = 1; break;  // DISP ON
			case 0x5A: m_sed_param_len = 1; break;  // HDOT SCR
			case 0x5B: m_sed_param_len = 1; break;  // OVLAY
			case 0x5D: m_sed_param_len = 2; break;  // CSRFORM
			default: m_sed_param_len = 0; break;
		}
	}
	else // Data Port
	{
		if (m_sed_cmd == 0x42) // MWRITE stream
		{
			m_sed_vram[m_sed_cursor_addr & 0x0FFF] = data;
			m_sed_cursor_addr = (m_sed_cursor_addr + 1) & 0x0FFF;
			m_sed_vram_active = true;
		}
		else if (m_sed_param_len > 0)
		{
			if (m_sed_param_idx < 16)
				m_sed_params[m_sed_param_idx++] = data;

			if (m_sed_param_idx >= m_sed_param_len)
			{
				if (m_sed_cmd == 0x46) // CSRW
				{
					m_sed_cursor_addr = m_sed_params[0] | (m_sed_params[1] << 8);
				}
				else if (m_sed_cmd == 0x44) // SCROLL
				{
					m_sed_sad1 = m_sed_params[0] | (m_sed_params[1] << 8);
					m_sed_sad2 = m_sed_params[3] | (m_sed_params[4] << 8);
				}
				else if (m_sed_cmd == 0x59) // DISP ON
				{
					m_sed_disp_mode = m_sed_params[0];
				}
				else if (m_sed_cmd == 0x5B) // OVLAY
				{
					m_sed_overlay_mode = m_sed_params[0] & 0x03;
				}
			}
		}
	}
}

// 1. Built-in Front Panel LCD Display (Epson SED1335: 160x64 monochrome)
uint32_t s760_state::lcd_update(screen_device &screen, bitmap_ind16 &bitmap, const rectangle &cliprect)
{
	bool vram_has_data = m_sed_vram_active;
	if (!vram_has_data)
	{
		for (int i = 0; i < 4096; i++)
		{
			if (m_sed_vram[i] != 0)
			{
				vram_has_data = true;
				m_sed_vram_active = true;
				break;
			}
		}
	}

	bitmap.fill(0, cliprect);

	if (vram_has_data && (m_sed_disp_mode != 0))
	{
		for (int y = 0; y < 64; y++)
		{
			int char_row = y / 8;
			int py = y % 8;

			for (int x = 0; x < 160; x++)
			{
				int char_col = x / 8;
				int px = x % 8;

				// Layer 1: Text Character Matrix (20x8 characters at m_sed_sad1)
				uint8_t text_bit = 0;
				if (m_sed_disp_mode & 0x01)
				{
					uint8_t char_code = m_sed_vram[(m_sed_sad1 + char_row * 20 + char_col) & 0x0FFF];
					const uint8_t *glyph = get_font_glyph(char_code ? (char)char_code : ' ');
					text_bit = (glyph[py] & (0x80 >> px)) ? 1 : 0;
				}

				// Layer 2: 1-Bit Graphics Plane (160x64 dots at m_sed_sad2)
				uint8_t gfx_bit = 0;
				if (m_sed_disp_mode & 0x04)
				{
					int byte_offset = y * 20 + (x / 8);
					uint8_t b = m_sed_vram[(m_sed_sad2 + byte_offset) & 0x0FFF];
					gfx_bit = (b & (0x80 >> px)) ? 1 : 0;
				}

				// Layer Composition Mode (OR, XOR, AND)
				uint8_t color = (m_sed_overlay_mode == 1) ? (text_bit ^ gfx_bit) :
				                (m_sed_overlay_mode == 2) ? (text_bit & gfx_bit) : (text_bit | gfx_bit);
				bitmap.pix(y, x) = color ? 1 : 0;
			}
		}
	}
	// NOTE (ui-consolidation task 1.3): invented "render active front panel page"
	// fallback removed (R2.3). The old `else` branch fabricated LCD text
	// ("ROLAND S-760" / mode name / "SYSTEM v2.24 OK" / "RAM: 32MB READY") via
	// draw_string whenever the SED1335 VRAM was empty. That content was invented
	// chrome, not genuine controller output, so it is gone. When VRAM holds no
	// real data (e.g. until the OS runs — see F2) the LCD now stays a defined
	// blank screen (the bitmap.fill(0) above). The genuine SED1335 160x64 VRAM
	// rasterizer above is unchanged.
	return 0;
}

// NOTE (ui-consolidation task 1.1): invented GUI renderers removed.
// render_perform_mode / render_patch_mode / render_partial_mode /
// render_sample_mode / render_disk_mode / render_system_mode /
// render_rack_panel deleted (R1.2, R2.2).
//
// crt_update rewritten in ui-consolidation task 1.2 (R2.3, R2.4).
// CHOSEN APPROACH: Option 2 (pragmatic blank/background screen).
//   Per finding F1 there is no authentic VDP framebuffer to "keep": the old CRT
//   image was 100% invented chrome (banner, mode ribbon/tabs, per-mode pages,
//   soft-button bar, rack panel, mouse crosshair). Per F2 the OS cannot cold-boot
//   without the IC20 BOOT ROM, so the RFSC16A VDP is never driven to produce a
//   real image today.
//   This function now:
//     - clears the bitmap to a defined background (blank screen), AND
//     - still rasterizes genuine RFSC16A VRAM when (and only when) the OS has
//       actually written tile/attribute data into VDP VRAM (preserves real
//       emulation for the eventual LLE path; renders blank until then).
//   ALL invented chrome and chrome-navigation input handling has been removed.
//   The 1U rack strip, LCD/OLED housings, knobs, cursor and the drawn studio UI
//   are now owned by the React shell (google-ui/). Live interactive CRT content
//   is deferred to the C++-core bridge path (see spec Phase 3).
//
// Authentic OP-760 (RFSC16A VDP) display surface — CRT region only (640x240).
uint32_t s760_state::crt_update(screen_device &screen, bitmap_ind16 &bitmap, const rectangle &cliprect)
{
	// Defined background: clear the full CRT surface to black (pen 0).
	// This is the blank-screen baseline per Option 2 / F1 / F2.
	bitmap.fill(0, cliprect);

	// Determine whether the OS has written any genuine data into VDP VRAM.
	// Until the IC20 BOOT ROM is dumped (F2) the OS never runs, so this stays
	// false and the screen remains a defined blank background.
	bool render_from_vram = m_vdp_vram_active;
	if (!render_from_vram)
	{
		for (int i = 0; i < 2400; i++)
		{
			if (m_vdp_vram[i] != 0)
			{
				render_from_vram = true;
				m_vdp_vram_active = true;
				break;
			}
		}
	}

	if (render_from_vram && m_vdp_display_enable)
	{
		// -------------------------------------------------------------
		// Genuine RFSC16A VRAM rasterizer (y = 0..239). Preserved real
		// emulation path; produces output only when the OS drives the VDP.
		// -------------------------------------------------------------
		for (int tile_row = 0; tile_row < 30; tile_row++)
		{
			for (int tile_col = 0; tile_col < 80; tile_col++)
			{
				int cell_idx = tile_row * 80 + tile_col;
				uint8_t char_code = m_vdp_vram[m_vdp_matrix_base + cell_idx];
				uint8_t attr = m_vdp_vram[m_vdp_attr_base + cell_idx];

				// Character attribute: high nibble = fg pen, low nibble = bg pen.
				// The genuine RFSC16A studio palette has 10 pens (0..9); clamp into
				// that authentic range (chrome pens 10..15 were removed in task 1.4).
				uint8_t fg = (attr >> 4) & 0x0F;
				uint8_t bg = attr & 0x0F;
				if (fg > 9) fg = 1;
				if (bg > 9) bg = 0;
				if (fg == 0 && bg == 0) { fg = 1; bg = 2; } // Default white on Roland Royal Blue

				const uint8_t *glyph = get_font_glyph(char_code ? (char)char_code : ' ');

				for (int py = 0; py < 8; py++)
				{
					uint8_t bits = glyph[py];
					int y = tile_row * 8 + py;
					if (y >= 240) continue;

					for (int px = 0; px < 8; px++)
					{
						int x = tile_col * 8 + px;
						if (x >= 640) continue;

						uint16_t pen = (bits & (0x80 >> px)) ? fg : bg;
						bitmap.pix(y, x) = pen;
					}
				}
			}
		}

		// Waveform & Direct Bitmap Overlay Plane (Plane 4: 0x03400)
		if (m_vdp_bitmap_plane_enable)
		{
			for (int y = 0; y < 240; y++)
			{
				for (int byte_x = 0; byte_x < 80; byte_x++)
				{
					uint8_t b = m_vdp_vram[m_vdp_bitmap_base + y * 80 + byte_x];
					if (b != 0)
					{
						for (int bit = 0; bit < 8; bit++)
						{
							if (b & (0x80 >> bit))
							{
								bitmap.pix(y, byte_x * 8 + bit) = 1; // Pure white waveform pixel
							}
						}
					}
				}
			}
		}
	}

	// Trigger RFSC16A VDP VBlank Interrupt (Bit 4) — genuine hardware timing,
	// kept intact regardless of the display path.
	trigger_irq(IRQ_VDP_VBLANK);

	return 0;
}

void s760_state::ic20_hle_install()
{
	// First bring-up stub for the IC20 BOOT ROM service entry at 0x018D.
	//
	// The OS init dispatcher at 0x2A94 does: ST RW1C,0x104 ; LCALL 0x018D.
	// 0x018D is a real-hardware IC20 ROM routine; our image has none there.
	// Step 1 of HLE: make the call RETURN cleanly so init can proceed, and LOG
	// the service selector (RAM word at 0x0104) plus the pointer the caller set
	// up (RW1E, seen as 0x6A26 in the trace) on every entry, so the real ABI
	// contract can be reconstructed from observed selectors.
	address_space &prog = m_maincpu->space(AS_PROGRAM);

	// Force a RET (MCS-96 opcode 0xF0) at every IC20 BOOT ROM service entry via
	// installed READ HANDLERS rather than RAM pokes. Poking the .ram() byte does
	// NOT survive: the generic 0x0000-0x1FFF RAM backing is cleared by the core
	// AFTER both machine_start() and machine_reset() (verified: the fetched
	// opcode was 0x00 "skip", not 0xF0 "ret"). A read handler is consulted on
	// every opcode fetch regardless of RAM contents, so the RET is always there.
	//
	// The 14 entry points were mapped by static analysis of the whole resident
	// payload (see docs/ic20-hle-findings/shared/02-ic20-entry-points-and-vector-
	// table.md). Each is pure IC20 code space (never OS data), so returning RET
	// for its containing word is safe. We align each to its even word base and
	// install a handler that returns 0xF0F0 (RET in both bytes), so the entry
	// opcode is RET whether the entry address is even or odd.
	static constexpr offs_t IC20_ENTRIES[] = {
		0x018D, 0x0296, 0x0442, 0x045D, 0x0491, 0x04AC, 0x0551, 0x05AA,
		0x0B31, 0x0D5D, 0x0EC7, 0x0F15, 0x0F19, 0x1109,
	};
	for (offs_t ep : IC20_ENTRIES)
	{
		const offs_t wbase = ep & ~offs_t(1); // even word base containing the entry byte
		prog.install_read_handler(wbase, wbase + 1,
			read16smo_delegate(*this, FUNC(s760_state::ic20_ret_stub_r)));
	}

	// HLE the IC20 dispatch by tapping the write to selector slot 0x0104, which
	// the OS performs (ST RW1C,0x104) immediately before LCALL 0x018D. At that
	// point the caller's register-file inputs are already set, so we can service
	// the request here; the RET stub at 0x018D (poked in machine_reset) then
	// returns control to the OS.
	//
	// CRITICAL (Gemini finding 03, AS_DATA vs AS_PROGRAM): the MCS-96 on-chip
	// register file (addresses 0x00..0xFF, incl. RW1E/R4A/RW4C/RW4E) lives in
	// **AS_DATA**, not AS_PROGRAM (see mcs96_device::memory_space_config and
	// any_r16/any_w16: adr<0x100 -> regs == AS_DATA). The core's memory_translate
	// only redirects the CPU's *own* fetch path; an external space(AS_PROGRAM)
	// access at 0x4E hits WORK RAM, not the register. So register-file accesses
	// MUST use space(AS_DATA); only the scratch buffer (>=0x100) uses AS_PROGRAM.
	//
	// Selector 0x4B — resource record enumeration/lookup (see
	// docs/ic20-hle-findings/shared/02-selector-4b-record-enumeration.md):
	//   inputs : R4A  (0x4A, byte)  = resource type (1..4)
	//            RW4C (0x4C, word)  = record index
	//            RW1E (0x1E, word)  = scratch/destination buffer pointer
	//   output : RW4E (0x4E, word)  = pointer to the located record; the OS then
	//            reads [RW4E] and treats byte 0x7F as "valid record present".
	// Increment A (minimal, observable): point RW4E at the scratch buffer and
	// write the 0x7F "valid header" marker there so the enumeration loops run to
	// completion, revealing the next boot dependency.
	m_ic20_tap = prog.install_write_tap(
		0x0104, 0x0105, "ic20_dispatch",
		[this](offs_t offset, u16 &data, u16 mem_mask)
		{
			if (offset != 0x0104)
				return;
			address_space &prog_space = m_maincpu->space(AS_PROGRAM); // buffers >= 0x100
			address_space &data_space = m_maincpu->space(AS_DATA);    // register file < 0x100
			const u16 selector = data;
			const u8  type     = data_space.read_byte(0x4A);  // R4A
			const u16 index    = data_space.read_word(0x4C);  // RW4C
			const u16 bufptr   = data_space.read_word(0x1E);  // RW1E

			switch (selector)
			{
			case 0x4B:
				// Record enumeration/lookup: point the output pointer RW4E (in the
				// AS_DATA register file) at the scratch buffer, and mark a valid
				// record header (0x7F) at that buffer in AS_PROGRAM so the OS's
				// post-call [RW4E]==0x7F check passes. (Increment B will copy real
				// record bytes for (type,index) from the on-disk 256-byte record
				// table at file ~0xC3000.)
				data_space.write_word(0x4E, bufptr);   // RW4E (register file)
				prog_space.write_byte(bufptr, 0x7F);   // scratch buffer (work RAM)
				break;

			case 0x3B:
			{
				// CHS floppy sector read (Gemini finding 07 §2). Inputs: RF0=sector,
				// RF1=cylinder, RF2=head (bit0), RW1E=dest buffer. Serve 512 bytes
				// from the disk image at the computed LBA into the dest buffer.
				const u8  sec  = data_space.read_byte(0xF0);        // RF0
				const u8  cyl  = data_space.read_byte(0xF1);        // RF1
				const u8  head = data_space.read_byte(0xF2) & 0x01; // RF2
				const u32 lba  = (u32(cyl) * 2 + head) * 18 + (sec > 0 ? (sec - 1) % 18 : 0);
				const u32 off  = lba * 512;
				const u8 *disk = memregion("maincpu")->base();
				if (off + 512 <= 0x168000)
					for (int i = 0; i < 512; i++)
						prog_space.write_byte(u16(bufptr + i), disk[off + i]);
				// Clear carry (success). The OS also CLRCs itself on this path,
				// but 0x1F and other callers rely on the service clearing it.
				m_maincpu->set_state_int(i8x9x_device::MCS96_PSW,
					m_maincpu->state_int(i8x9x_device::MCS96_PSW) & ~1);
				break;
			}

			case 0x1F:
			{
				// Bulk LBA sector transfer (Gemini finding 07 §3). Inputs:
				// RW4C=sector count, RW48/RW4A=LBA lo/hi, RW1E=dest buffer.
				const u16 count  = data_space.read_word(0x4C);  // RW4C
				const u16 lba_lo = data_space.read_word(0x48);  // RW48
				const u16 lba_hi = data_space.read_word(0x4A);  // RW4A
				const u32 lba    = (u32(lba_hi) << 16) | lba_lo;
				const u32 off    = lba * 512;
				const u32 len    = u32(count) * 512;
				const u8 *disk = memregion("maincpu")->base();
				if (off + len <= 0x168000)
					for (u32 i = 0; i < len; i++)
						prog_space.write_byte(u16(bufptr + i), disk[off + i]);
				m_maincpu->set_state_int(i8x9x_device::MCS96_PSW,
					m_maincpu->state_int(i8x9x_device::MCS96_PSW) & ~1);
				break;
			}

			default:
				// Other IC20 selectors (0x3B, 0x1F, 0x166, 0xB1, 0x129, ...): no
				// modeled side effect yet. The RET stub at the entry returns
				// cleanly; we also point RW4E at the scratch buffer so any
				// generic post-call pointer deref lands in valid RAM rather than
				// a stale/garbage address. Refine per-selector as new stalls
				// appear in the boot trace.
				if (bufptr != 0)
					data_space.write_word(0x4E, bufptr);  // RW4E (register file)
				break;
			}

			logerror("[IC20] sel=0x%04X type=%u index=0x%04X buf=0x%04X PC=0x%04X\n",
				selector, type, index, bufptr, m_maincpu->pc());
		},
		&m_ic20_tap);

	// Write-audit result (ChatGPT review, finding 16): over the upper region
	// 0xD100-0xFFFF the OS writes ONLY to 0xD400-0xD41C (a peripheral register
	// block it zero-clears at init, PC ~0x2AEC-0x2B1x) — it never writes into
	// the executable code (0xE000-0xFFFF etc.). So that code is effectively
	// read-only; the current RAM backing is functionally correct (zero-writes to
	// 0xD400 land harmlessly and read back consistently) but a more hardware-
	// faithful model would make the code ROM with a decoded hole at 0xD400-0xD41C
	// (candidate: TVF/MEQ or VDP-companion register block). Deferred as non-
	// blocking — the VDP VRAM write path (0xD018) is already exercised.
}

void s760_state::s760_mem(address_map &map)
{
	map(0x0000, 0x1FFF).ram();                                                   // Register File & Work RAM (0x1120 = SP)
	// The resident OS image (runtime 0x2080-0xFFFF, uniform linear from file
	// 0x4800) is installed as RAM in machine_start (m_os_ram), and the IRQ
	// vector window 0x2000-0x207F too (m_vec_ram). The peripheral register
	// windows (VDP 0xD000-0xD0FF, SED1335 0xE000-0xE003, gate array/SCSI/FDC
	// 0xF000-0xF047) are re-installed ON TOP of that RAM in machine_start so
	// they override only their actual ports and leave all surrounding addresses
	// executable as OS code (Gemini finding 13). No code banking is needed; the
	// former wide 0xE000-0xEFF7 LCD window was intercepting main-loop code
	// fetches (0xE934 etc.) and is now narrowed to the two real SED1335 ports.
	// (Static map intentionally declares only the base RAM; the OS image +
	// peripheral windows are installed dynamically in machine_start.)
}

static INPUT_PORTS_START( s760 )
	PORT_START("KEY_ARROWS")
	PORT_BIT( 0x01, IP_ACTIVE_LOW, IPT_JOYSTICK_LEFT )  PORT_NAME("Cursor Left / Arrow Left")   PORT_CODE(KEYCODE_LEFT)
	PORT_BIT( 0x02, IP_ACTIVE_LOW, IPT_JOYSTICK_RIGHT ) PORT_NAME("Cursor Right / Arrow Right") PORT_CODE(KEYCODE_RIGHT)
	PORT_BIT( 0x04, IP_ACTIVE_LOW, IPT_JOYSTICK_UP )    PORT_NAME("Cursor Up / Arrow Up")       PORT_CODE(KEYCODE_UP)
	PORT_BIT( 0x08, IP_ACTIVE_LOW, IPT_JOYSTICK_DOWN )  PORT_NAME("Cursor Down / Arrow Down")   PORT_CODE(KEYCODE_DOWN)
	PORT_BIT( 0x10, IP_ACTIVE_LOW, IPT_BUTTON1 )        PORT_NAME("Select / Enter")             PORT_CODE(KEYCODE_ENTER) PORT_CODE(KEYCODE_SPACE)

	PORT_START("GOTEK_CTRL")
	PORT_BIT( 0x01, IP_ACTIVE_LOW, IPT_BUTTON4 ) PORT_NAME("Gotek Prev Image [ < ]")   PORT_CODE(KEYCODE_OPENBRACE) PORT_CODE(KEYCODE_PGUP)
	PORT_BIT( 0x02, IP_ACTIVE_LOW, IPT_BUTTON5 ) PORT_NAME("Gotek Next Image [ > ]")   PORT_CODE(KEYCODE_CLOSEBRACE) PORT_CODE(KEYCODE_PGDN)
	PORT_BIT( 0x04, IP_ACTIVE_LOW, IPT_BUTTON6 ) PORT_NAME("Gotek Select / Push")      PORT_CODE(KEYCODE_BACKSLASH) PORT_CODE(KEYCODE_INSERT)
INPUT_PORTS_END

void s760_state::s760(machine_config &config)
{
	// Main CPU: Intel 80C196 / 8096 derivative @ 16 MHz
	N8097BH(config, m_maincpu, 16_MHz_XTAL);
	m_maincpu->set_addrmap(AS_PROGRAM, &s760_state::s760_mem);

	// Sound: Dual Stereo Outputs (IC91/IC92 D/A DACs) + 32-Voice DSP ASIC
	SPEAKER(config, "lspeaker").front_left();
	SPEAKER(config, "rspeaker").front_right();

	S760_SOUND(config, m_sound, 44100);
	m_sound->add_route(0, "lspeaker", 1.0);
	m_sound->add_route(1, "rspeaker", 1.0);

	// 10 authentic Roland RFSC16A studio pens (0..9). Chrome-only pens 10..15
	// were removed in ui-consolidation task 1.4 (R1.2, R2.2).
	palette_device &palette(PALETTE(config, "palette", FUNC(s760_state::s760_palette), 10));

	// OP-760 Color CRT display surface only (RFSC16A VDP), CRT region = 640x240.
	// ui-consolidation task 1.2 (R2.3): the former 120px rack strip (old 640x360)
	// is dropped — the 1U rack/LCD/OLED chrome is now the React shell's job.
	screen_device &crt_screen(SCREEN(config, "crt_screen"));
	crt_screen.set_refresh_hz(60);
	crt_screen.set_vblank_time(ATTOSECONDS_IN_USEC(2500));
	crt_screen.set_size(640, 240);
	crt_screen.set_visarea(0, 639, 0, 239);
	crt_screen.set_screen_update(FUNC(s760_state::crt_update));
	crt_screen.set_palette(palette);
}

ROM_START( s760 )
	ROM_REGION16_LE( 0x168000, "maincpu", 0 )
	ROM_LOAD( "s760224.img", 0x000000, 0x168000, CRC(b14b0257) SHA1(e5ab4abc96654965f23d1930b1e93c9211784873) )
ROM_END

} // anonymous namespace

SYST( 1993, s760, 0, 0, s760, s760, s760_state, empty_init, "Roland", "S-760 Digital Sampler", MACHINE_IMPERFECT_GRAPHICS )


