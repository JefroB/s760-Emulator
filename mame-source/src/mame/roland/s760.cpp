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
	};

	sound_stream *m_stream;
	Voice m_voices[32];
	std::vector<int16_t> m_wave_ram;
	std::vector<SampleDesc> m_samples;
	std::string m_media_source;
	std::string m_scsi_device_info[8];

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

	for (int v = 0; v < 32; v++)
	{
		m_voices[v].active = false;
		m_voices[v].env_stage = 0;
	}
}

void s760_sound_device::device_reset()
{
	for (int v = 0; v < 32; v++)
	{
		m_voices[v].active = false;
		m_voices[v].env_stage = 0;
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
						uint32_t num_patches = 0, num_samples = 0;
						file.seekg(0x60, std::ios::beg);
						file.read(reinterpret_cast<char *>(&num_patches), 4);
						file.read(reinterpret_cast<char *>(&num_samples), 4);

						size_t cur_offset = 0x10000; // Sector 128 (64KB offset for Sample Blocks)
						uint32_t word_dest = 0;

						for (uint32_t s_idx = 0; s_idx < num_samples && s_idx < 16; s_idx++)
						{
							file.seekg(cur_offset, std::ios::beg);
							char s_hdr[256] = {0};
							file.read(s_hdr, 256);

							SampleDesc desc;
							memset(desc.name, 0, sizeof(desc.name));
							memcpy(desc.name, &s_hdr[0x02], 16);
							desc.sample_rate = *reinterpret_cast<uint32_t *>(&s_hdr[0x12]);
							desc.loop_start = *reinterpret_cast<uint32_t *>(&s_hdr[0x16]);
							desc.loop_end = *reinterpret_cast<uint32_t *>(&s_hdr[0x1A]);
							desc.root_key = static_cast<uint8_t>(s_hdr[0x1E]);
							uint32_t data_len_bytes = *reinterpret_cast<uint32_t *>(&s_hdr[0x20]);

							desc.wave_offset = word_dest;
							desc.length = data_len_bytes / sizeof(int16_t);
							desc.loop_mode = (desc.loop_end > desc.loop_start) ? 1 : 0;

							if (word_dest + desc.length <= m_wave_ram.size())
							{
								file.read(reinterpret_cast<char *>(&m_wave_ram[word_dest]), data_len_bytes);
								word_dest += desc.length;
							}

							m_samples.push_back(desc);
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
		double noise = ((double)(rand() % 100) / 100.0 - 0.5) * 0.05 * std::exp(-20.0 * t); // Bow friction transient
		double strings = bow_attack * (0.4 * s1 + 0.25 * s2 + 0.25 * s3 + 0.15 * s4 + 0.1 * s5 + noise);
		m_wave_ram[w2_start + i] = (int16_t)(std::clamp(strings * 24000.0, -32767.0, 32767.0));
	}

	// Wave 3: Akai S1000 Concert Grand Piano (Hammer strike transient + 16 decaying inharmonic partials)
	uint32_t w3_start = 88200;
	uint32_t w3_len = 44100;
	for (uint32_t i = 0; i < w3_len; i++)
	{
		double t = (double)i / 44100.0;
		double hammer = ((double)(rand() % 100) / 100.0 - 0.5) * 0.4 * std::exp(-60.0 * t); // Felt hammer knock
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
		delay_line[d] = ((double)(rand() % 1000) / 500.0 - 1.0) * std::exp(- (double)d / 120.0); // Pluck excitation

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

			float s = 0.0f;
			if (idx + 1 < m_wave_ram.size())
			{
				float s0 = (float)m_wave_ram[idx];
				float s1 = (float)m_wave_ram[idx + 1];
				s = (s0 + frac * (s1 - s0)) / 32768.0f;
			}
			else if (idx < m_wave_ram.size())
			{
				s = (float)m_wave_ram[idx] / 32768.0f;
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

static void draw_string(bitmap_ind16 &bitmap, int x, int y, const char *str, uint16_t fg, uint16_t bg = 0xffff)
{
	while (*str)
	{
		char c = *str++;
		const uint8_t *glyph = get_font_glyph(c);
		for (int row = 0; row < 8; row++)
		{
			uint8_t bits = glyph[row];
			for (int col = 0; col < 8; col++)
			{
				if (bits & (0x80 >> col))
					bitmap.pix(y + row, x + col) = fg;
				else if (bg != 0xffff)
					bitmap.pix(y + row, x + col) = bg;
			}
		}
		x += 8;
	}
}

class s760_state : public driver_device
{
public:
	s760_state(const machine_config &mconfig, device_type type, const char *tag)
		: driver_device(mconfig, type, tag)
		, m_maincpu(*this, "maincpu")
		, m_crt_screen(*this, "crt_screen")
		, m_lcd_vram(*this, "lcd_vram")
		, m_key_arrows(*this, "KEY_ARROWS")
		, m_mouse_btn(*this, "MOUSEBTN")
		, m_gotek_ctrl(*this, "GOTEK_CTRL")
		, m_sound(*this, "s760_sound")
	{ }

	void s760(machine_config &config);
	void s760_palette(palette_device &palette) const;

	DECLARE_INPUT_CHANGED_MEMBER(mouse_x);
	DECLARE_INPUT_CHANGED_MEMBER(mouse_y);

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

protected:
	virtual void machine_start() override ATTR_COLD;
	virtual void machine_reset() override ATTR_COLD;

private:
	required_device<i8x9x_device> m_maincpu;
	required_device<screen_device> m_crt_screen;
	required_shared_ptr<uint16_t> m_lcd_vram;

	required_ioport m_key_arrows;
	required_ioport m_mouse_btn;
	required_ioport m_gotek_ctrl;
	required_device<s760_sound_device> m_sound;

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
	uint16_t m_vdp_addr;
	std::unique_ptr<uint8_t[]> m_vdp_vram;

	// Sampler GUI State
	int m_cur_x;
	int m_cur_y;
	int m_active_tab;
	int m_selected_row;
	bool m_last_clicked;

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

	void render_perform_mode(bitmap_ind16 &bitmap);
	void render_patch_mode(bitmap_ind16 &bitmap);
	void render_partial_mode(bitmap_ind16 &bitmap);
	void render_sample_mode(bitmap_ind16 &bitmap);
	void render_disk_mode(bitmap_ind16 &bitmap);
	void render_system_mode(bitmap_ind16 &bitmap);
	void render_rack_panel(bitmap_ind16 &bitmap);
};

INPUT_CHANGED_MEMBER(s760_state::mouse_x)
{
	int delta = newval - oldval;
	if (delta > 0x80)
		delta -= 0x100;
	else if (delta < -0x80)
		delta += 0x100;

	m_cur_x = std::clamp(m_cur_x + delta, 8, 632);
}

INPUT_CHANGED_MEMBER(s760_state::mouse_y)
{
	int delta = newval - oldval;
	if (delta > 0x80)
		delta -= 0x100;
	else if (delta < -0x80)
		delta += 0x100;

	m_cur_y = std::clamp(m_cur_y + delta, 4, 354);
}

void s760_state::machine_start()
{
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
	m_cur_x = 350;
	m_cur_y = 100;
	m_active_tab = 4; // Default to DISK Load Mode
	m_selected_row = (m_sound->samples().size() > 5) ? 5 : 3;
	m_last_clicked = false;

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
	m_maincpu->set_input_line(MCS96_INT_VECTOR, CLEAR_LINE);

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
		m_maincpu->set_input_line(MCS96_INT_VECTOR, should_assert ? ASSERT_LINE : CLEAR_LINE);
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

		case 0x06: // DSP Command Latch
			val = m_dsp_cmd_latch;
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

		case 0x06: // DSP Command Latch
			m_dsp_cmd_latch = data;
			break;

		case 0x08: // DSP Address Latch
			m_dsp_addr_latch = data;
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
	if (reg == 0x18 || reg == 0x40)
	{
		val = 0x00; // Ready status
	}
	return val;
}

void s760_state::vdp_w(offs_t offset, uint8_t data)
{
	uint8_t reg = offset & 0x7F;
	m_vdp_regs[reg] = data;

	if (reg == 0x34)
	{
		m_vdp_addr = (m_vdp_addr & 0xFF00) | data;
	}
	else if (reg == 0x36)
	{
		m_vdp_addr = (m_vdp_addr & 0x00FF) | (data << 8);
	}
	else if (reg == 0x18)
	{
		m_vdp_vram[m_vdp_addr & 0x1FFFF] = data;
		m_vdp_addr = (m_vdp_addr + 1) & 0x1FFFF;
	}
}

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
	palette.set_pen_color(9, rgb_t(24, 26, 30));      // 9: Dark Slate / Gotek Bezel
	palette.set_pen_color(10, rgb_t(38, 40, 46));     // 10: 1U Rack Dark Charcoal Chassis
	palette.set_pen_color(11, rgb_t(75, 80, 92));     // 11: Rack Bezel Highlight / Screws
	palette.set_pen_color(12, rgb_t(30, 95, 35));     // 12: LCD Green Backlight Background
	palette.set_pen_color(13, rgb_t(165, 245, 110));  // 13: LCD Bright Green Pixel / Text
	palette.set_pen_color(14, rgb_t(80, 230, 255));   // 14: Gotek OLED Cyan/Blue
	palette.set_pen_color(15, rgb_t(120, 125, 135));  // 15: Metallic Knob Gray
}

// 1. Built-in Front Panel LCD Display (Epson SED1335: 160x64 monochrome)
uint32_t s760_state::lcd_update(screen_device &screen, bitmap_ind16 &bitmap, const rectangle &cliprect)
{
	bool vram_has_data = false;
	for (int i = 0; i < 0x3FF; i++)
	{
		if (m_lcd_vram[i] != 0)
		{
			vram_has_data = true;
			break;
		}
	}

	bitmap.fill(0, cliprect);

	if (vram_has_data)
	{
		for (int y = 0; y < 64; y++)
		{
			for (int x = 0; x < 160; x++)
			{
				int bit_global = y * 160 + x;
				int word_idx = bit_global / 16;
				int bit_idx = 15 - (bit_global % 16);
				uint16_t word_val = m_lcd_vram[word_idx & 0x3FF];
				uint16_t color = (word_val & (1 << bit_idx)) ? 1 : 0;
				bitmap.pix(y, x) = color;
			}
		}
	}
	else
	{
		// Render active front panel page according to active tab
		const char *mode_names[] = { "PERFORM MODE", "PATCH EDIT", "PARTIAL EDIT", "SAMPLE EDIT", "DISK LOAD", "SYSTEM CONFIG" };
		draw_string(bitmap, 24, 6,  "ROLAND  S-760", 1);
		draw_string(bitmap, 12, 22, mode_names[m_active_tab], 1);
		draw_string(bitmap, 12, 38, "SYSTEM v2.24  OK", 1);
		draw_string(bitmap, 20, 50, "RAM: 32MB READY", 1);
	}
	return 0;
}

void s760_state::render_perform_mode(bitmap_ind16 &bitmap)
{
	// Sub-ribbon
	draw_string(bitmap, 16, 30, "Perform Play 1", 0, 6);
	for (int y = 29; y < 39; y++)
		for (int x = 200; x < 244; x++)
			bitmap.pix(y, x) = 5;
	draw_string(bitmap, 204, 30, "Pform", 1, 5);

	for (int y = 28; y < 40; y++) {
		bitmap.pix(y, 360) = 0;
		bitmap.pix(y, 425) = 0;
		bitmap.pix(y, 490) = 0;
	}
	draw_string(bitmap, 372, 30, "Mark", 0, 6);
	draw_string(bitmap, 437, 30, "Jump", 0, 6);
	draw_string(bitmap, 502, 30, "Com", 8, 6);

	// Main Screen Content
	draw_string(bitmap, 16, 44, "PRM: 01 JP-8 MULTI SET", 1, 2);
	draw_string(bitmap, 340, 44, "Master: 127", 8, 2);

	// Yellow Table Header
	for (int y = 55; y < 65; y++)
		for (int x = 12; x < 492; x++)
			bitmap.pix(y, x) = 4;
	draw_string(bitmap, 16, 56, "Part  Patch Name          MIDI-Ch  Output  Pan  Level", 0, 4);

	const char *perf_parts[] = {
		" 1   P11: JP-8 BRASS 1    01       1-2     <0>  127",
		" 2   P12: JP-8 STRGS 1    02       1-2     L15  110",
		" 3   P13: VP STRINGS 1    03       1-2     R15  105",
		" 4   P14: VP CHOIR 1      04       1-2     <0>  090",
		" 5   P15: SYNTH 1         05       1-2     <0>  100",
		" 6   P16: SYNTH 2         06       1-2     <0>  100",
		" 7   P17: SYNTH 3         07       1-2     <0>  100",
		" 8   P18: SYNTH 4         08       1-2     <0>  100",
	};

	for (int i = 0; i < 8; i++)
	{
		uint16_t color = (i == m_selected_row % 8) ? 4 : 1;
		draw_string(bitmap, 16, 67 + i * 10, perf_parts[i], color, 2);
	}

	// Peak Level meter box
	for (int y = 55; y < 65; y++)
		for (int x = 504; x < 624; x++)
			bitmap.pix(y, x) = 4;
	draw_string(bitmap, 524, 56, "Peak Level", 0, 4);

	for (int y = 68; y < 146; y++)
		for (int x = 504; x < 624; x++)
			bitmap.pix(y, x) = 0;

	for (int s = 0; s < 12; s++)
	{
		int my = 136 - s * 6;
		uint16_t seg_color = (s < 8) ? 3 : (s < 10) ? 4 : 5;
		for (int y = my; y < my + 4; y++)
		{
			for (int x = 520; x < 560; x++) bitmap.pix(y, x) = seg_color;
			for (int x = 568; x < 608; x++) bitmap.pix(y, x) = seg_color;
		}
	}
	draw_string(bitmap, 510, 72, "L", 1, 0);
	draw_string(bitmap, 612, 72, "R", 1, 0);

	// Keyboard Map
	for (int y = 150; y < 160; y++)
		for (int x = 12; x < 624; x++)
			bitmap.pix(y, x) = 4;
	draw_string(bitmap, 16, 151, "Keyboard Part Map (C-1 to G9)", 0, 4);

	// Soft buttons
	const char *soft_btns[] = { "[ ] KbdOn", "Q-Samp", "Sol/Mut", "PartMap", "VolInfo" };
	for (int b = 0; b < 5; b++)
	{
		int bx = b * 128 + 12;
		for (int y = 222; y < 236; y++)
			for (int x = bx; x < bx + 120; x++)
				bitmap.pix(y, x) = 1;
		draw_string(bitmap, bx + 10, 225, soft_btns[b], 0, 1);
	}
}

void s760_state::render_patch_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 16, 30, "Patch Common", 0, 6);
	for (int y = 29; y < 39; y++)
		for (int x = 200; x < 244; x++)
			bitmap.pix(y, x) = 5;
	draw_string(bitmap, 204, 30, "Patch", 1, 5);

	for (int y = 28; y < 40; y++) {
		bitmap.pix(y, 360) = 0;
		bitmap.pix(y, 425) = 0;
		bitmap.pix(y, 490) = 0;
	}
	draw_string(bitmap, 372, 30, "Mark", 0, 6);
	draw_string(bitmap, 437, 30, "Jump", 0, 6);
	draw_string(bitmap, 502, 30, "Com", 8, 6);

	// Parameters
	for (int y = 44; y < 54; y++)
	{
		for (int x = 12; x < 312; x++) bitmap.pix(y, x) = 4;
		for (int x = 324; x < 624; x++) bitmap.pix(y, x) = 4;
	}
	draw_string(bitmap, 16, 45, "Parameter", 0, 4);
	draw_string(bitmap, 328, 45, "Information", 0, 4);

	draw_string(bitmap, 16, 60, "Patch Name:   [ 01 JP-8 BRASS 1 ]", 1, 2);
	draw_string(bitmap, 16, 75, "1Shot Mode:   [ Off ]  (Off, On)", 1, 2);
	draw_string(bitmap, 16, 90, "Bend Range:   Up: [ +2 ]  Down: [ -2 ]", 1, 2);
	draw_string(bitmap, 16, 105,"Tone Assign:  [ Poly ]", 1, 2);

	draw_string(bitmap, 328, 60, "Cutoff Offset: [------^------] +0", 1, 2);
	draw_string(bitmap, 328, 76, "Reso Offset:   [------^------] +0", 1, 2);
	draw_string(bitmap, 328, 92, "Attack Offset: [------^------] +0", 1, 2);
	draw_string(bitmap, 328, 108,"Release Off:   [------^------] +0", 1, 2);
	draw_string(bitmap, 328, 124,"V-Sens Offset: [------^------] +0", 1, 2);

	for (int y = 144; y < 154; y++)
		for (int x = 12; x < 624; x++)
			bitmap.pix(y, x) = 4;
	draw_string(bitmap, 16, 145, "Partial Key Assignment Overview", 0, 4);

	const char *patch_btns[] = { "MIDISel", "[ ] O.W", "---", "---", "---" };
	for (int b = 0; b < 5; b++)
	{
		int bx = b * 128 + 12;
		uint16_t bg = (b == 0) ? 8 : 1;
		for (int y = 222; y < 236; y++)
			for (int x = bx; x < bx + 120; x++)
				bitmap.pix(y, x) = bg;
		draw_string(bitmap, bx + 10, 225, patch_btns[b], 0, bg);
	}
}

void s760_state::render_partial_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 16, 30, "Partial TVF", 0, 6);
	for (int y = 29; y < 39; y++)
		for (int x = 200; x < 244; x++)
			bitmap.pix(y, x) = 5;
	draw_string(bitmap, 204, 30, "Part1", 1, 5);

	for (int y = 28; y < 40; y++) {
		bitmap.pix(y, 360) = 0;
		bitmap.pix(y, 425) = 0;
		bitmap.pix(y, 490) = 0;
	}
	draw_string(bitmap, 372, 30, "Mark", 0, 6);
	draw_string(bitmap, 437, 30, "Jump", 0, 6);
	draw_string(bitmap, 502, 30, "Com", 8, 6);

	for (int y = 44; y < 54; y++)
		for (int x = 12; x < 624; x++)
			bitmap.pix(y, x) = 4;
	draw_string(bitmap, 16, 45, "TVF Filter Parameters & Graphic Envelope", 0, 4);

	draw_string(bitmap, 16, 58, "Cutoff Freq: [  84 ]     Resonance: [  32 ]     Cutoff KF: [ +1.0 ]", 1, 2);
	draw_string(bitmap, 16, 72, "Vel-Curve:   [ 1:/ ]     V-Sens:    [ +45 ]     Time KF:   [    0 ]", 1, 2);
	draw_string(bitmap, 16, 86, "Envelope Points: [1] 0 127   [2] 74 45   [3] 102 0   [4] 127 0", 8, 2);

	// Black background envelope graph box
	for (int y = 100; y < 216; y++)
		for (int x = 12; x < 624; x++)
			bitmap.pix(y, x) = 0;

	// Sustain marker (Green)
	for (int y = 102; y < 214; y++)
		bitmap.pix(y, 380) = 3;
	draw_string(bitmap, 370, 106, "SUS", 3, 0);

	// Soft buttons
	const char *part_btns[] = { "[ ] Single", "---", "---", "Loop", "---" };
	for (int b = 0; b < 5; b++)
	{
		int bx = b * 128 + 12;
		for (int y = 222; y < 236; y++)
			for (int x = bx; x < bx + 120; x++)
				bitmap.pix(y, x) = 1;
		draw_string(bitmap, bx + 10, 225, part_btns[b], 0, 1);
	}
}

void s760_state::render_sample_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 16, 30, "Sampling", 0, 6);
	for (int y = 29; y < 39; y++)
		for (int x = 200; x < 244; x++)
			bitmap.pix(y, x) = 5;
	draw_string(bitmap, 204, 30, "Samp1", 1, 5);

	for (int y = 28; y < 40; y++) {
		bitmap.pix(y, 360) = 0;
		bitmap.pix(y, 425) = 0;
		bitmap.pix(y, 490) = 0;
	}
	draw_string(bitmap, 372, 30, "Mark", 0, 6);
	draw_string(bitmap, 437, 30, "Jump", 0, 6);
	draw_string(bitmap, 502, 30, "Com", 8, 6);

	draw_string(bitmap, 16, 44, "[ 1]PNO:MP-1.", 1, 2);
	draw_string(bitmap, 320, 44, "Remaining 341.0sec/ 342.2sec", 1, 2);

	const char *samp_params[] = {
		"Mode            Stereo",
		"Orig Key            C_4",
		"Freq           44.1KHz",
		"Time                .6",
		"Pre-Trig           ---",
		"Normalize          Off",
		"Input           Analog",
		"Type            OneWay",
		"Trigger          Level",
		"Threshold            0",
		"Digital ATT          0"
	};
	for (int i = 0; i < 11; i++)
		draw_string(bitmap, 16, 58 + i * 13, samp_params[i], 1, 2);

	for (int y = 58; y < 70; y++)
		for (int x = 320; x < 384; x++)
			bitmap.pix(y, x) = 1;
	draw_string(bitmap, 324, 60, "[EQ ON ]", 0, 1);

	for (int y = 74; y < 84; y++)
		for (int x = 320; x < 620; x++)
			bitmap.pix(y, x) = 4;
	draw_string(bitmap, 420, 75, "[H.F] [H.G] [L.F] [L.G]", 0, 4);

	draw_string(bitmap, 320, 88,  "Input-Left   --    --    --    --", 1, 2);
	draw_string(bitmap, 320, 102, "Input-Right  --    --    --    --", 1, 2);

	// VU Meters Box
	for (int y = 126; y < 204; y++)
		for (int x = 320; x < 620; x++)
			bitmap.pix(y, x) = 0;
	for (int x = 320; x < 620; x++) {
		bitmap.pix(126, x) = 8;
		bitmap.pix(203, x) = 8;
	}
	for (int y = 126; y < 204; y++) {
		bitmap.pix(y, 320) = 8;
		bitmap.pix(y, 619) = 8;
	}

	draw_string(bitmap, 330, 142, "LEFT", 1, 0);
	for (int seg = 0; seg < 10; seg++) {
		uint16_t col = (seg < 6) ? 3 : (seg < 8) ? 4 : 5;
		for (int dy = 0; dy < 6; dy++)
			for (int dx = 0; dx < 12; dx++)
				bitmap.pix(142 + dy, 395 + seg * 20 + dx) = col;
	}

	draw_string(bitmap, 330, 172, "RIGHT", 1, 0);
	for (int seg = 0; seg < 10; seg++) {
		uint16_t col = (seg < 5) ? 3 : (seg < 7) ? 4 : 5;
		for (int dy = 0; dy < 6; dy++)
			for (int dx = 0; dx < 12; dx++)
				bitmap.pix(172 + dy, 395 + seg * 20 + dx) = col;
	}
}

void s760_state::render_disk_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 16, 30, "Disk Load", 0, 6);
	for (int y = 29; y < 39; y++)
		for (int x = 200; x < 244; x++)
			bitmap.pix(y, x) = 5;
	draw_string(bitmap, 204, 30, "Disk", 1, 5);

	for (int y = 28; y < 40; y++) {
		bitmap.pix(y, 360) = 0;
		bitmap.pix(y, 425) = 0;
		bitmap.pix(y, 490) = 0;
	}
	draw_string(bitmap, 372, 30, "Mark", 0, 6);
	draw_string(bitmap, 437, 30, "Jump", 0, 6);
	draw_string(bitmap, 502, 30, "Com", 8, 6);

	draw_string(bitmap, 24, 44, "TG[Pfom]   ID[All]   CD[FDD:-FloppyDisk-]", 1, 2);

	// Yellow table header bar
	for (int y = 56; y < 66; y++)
		for (int x = 12; x < 460; x++)
			bitmap.pix(y, x) = 4;
	draw_string(bitmap, 24, 57, "1files", 0, 4);
	draw_string(bitmap, 340, 57, "Time P#", 0, 4);

	const char *disk_rows[] = {
		" 1: PNO:Acoustic Pno        22.2",
		" 2:                          0.0",
		" 3:                          0.0",
		" 4:                          0.0",
		" 5:                          0.0",
		" 6:                          0.0",
		" 7:                          0.0",
		" 8:                          0.0",
		" 9:                          0.0",
		"10:                          0.0",
		"11:                          0.0",
		"12:                          0.0",
		"13:                          0.0",
		"14:                          0.0",
		"15:                          0.0",
		"16:                          0.0",
	};

	for (int i = 0; i < 16; i++)
	{
		int ry = 68 + (int)(i * 9.5);
		draw_string(bitmap, 24, ry, disk_rows[i], 1, 2);
	}

	auto draw_param_box = [&](int pbx, int pby, int pbw, int pbh, const char *txt, const char *val) {
		for (int y = pby; y < pby + 10; y++)
			for (int x = pbx; x < pbx + pbw; x++)
				bitmap.pix(y, x) = 4;
		draw_string(bitmap, pbx + 30, pby + 1, txt, 0, 4);
		draw_string(bitmap, pbx + 26, pby + 12, val, 8, 2);
	};

	draw_param_box(470, 56, 140, 22, "Int.", "363.8sec");
	draw_param_box(470, 80, 140, 22, "Disk", "****.sec");
	draw_param_box(470, 104, 140, 22, "Marked", "0");

	// Soft buttons
	for (int y = 222; y < 236; y++)
		for (int x = 12; x < 104; x++)
			bitmap.pix(y, x) = 1;
	draw_string(bitmap, 28, 225, "AllOn", 0, 1);

	for (int y = 222; y < 236; y++)
		for (int x = 120; x < 220; x++)
			bitmap.pix(y, x) = 8;
	draw_string(bitmap, 156, 225, "---", 0, 8);

	for (int y = 222; y < 236; y++)
		for (int x = 236; x < 336; x++)
			bitmap.pix(y, x) = 1;
	draw_string(bitmap, 266, 225, "Load", 0, 1);

	for (int y = 222; y < 236; y++)
		for (int x = 352; x < 452; x++)
			bitmap.pix(y, x) = 1;
	draw_string(bitmap, 368, 225, "OW Off", 0, 1);

	for (int y = 222; y < 236; y++)
		for (int x = 468; x < 590; x++)
			bitmap.pix(y, x) = 1;
	draw_string(bitmap, 492, 225, "VolInfo", 0, 1);
}

void s760_state::render_system_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 16, 30, "System SCSI", 0, 6);
	for (int y = 29; y < 39; y++)
		for (int x = 200; x < 244; x++)
			bitmap.pix(y, x) = 5;
	draw_string(bitmap, 204, 30, "Systm", 1, 5);

	for (int y = 28; y < 40; y++) {
		bitmap.pix(y, 360) = 0;
		bitmap.pix(y, 425) = 0;
		bitmap.pix(y, 490) = 0;
	}
	draw_string(bitmap, 372, 30, "Mark", 0, 6);
	draw_string(bitmap, 437, 30, "Jump", 0, 6);
	draw_string(bitmap, 502, 30, "Com", 8, 6);

	const char *scsi_prms[] = {
		"S-760 Self SCSI ID    7",
		"Initial Drive    SCSI:6",
		"Initial Volume       65",
		"Boot Drive      Default",
		"Fast Delete Mode    Off",
		"Overwrite Switch    Off",
		"CDP Driver Type     Off"
	};
	for (int i = 0; i < 7; i++)
		draw_string(bitmap, 16, 60 + i * 18, scsi_prms[i], 1, 2);

	// SCSI Targets Box
	for (int y = 48; y < 208; y++)
		for (int x = 310; x < 620; x++)
			bitmap.pix(y, x) = 0;
	for (int x = 310; x < 620; x++) {
		bitmap.pix(48, x) = 8;
		bitmap.pix(207, x) = 8;
	}
	for (int y = 48; y < 208; y++) {
		bitmap.pix(y, 310) = 8;
		bitmap.pix(y, 619) = 8;
	}

	const char *targets[] = {
		"--0: - No Drive",
		"--1: - No Drive",
		"--2: - No Drive",
		"--3: - No Drive",
		"--4: - No Drive",
		"--5: - No Drive",
		"--6: - No Drive",
		"ME7: S-760 Self",
		"*FDD:-FloppyDisk-"
	};
	for (int t = 0; t < 9; t++)
		draw_string(bitmap, 320, 54 + t * 16, targets[t], (t >= 7) ? 8 : 6, 0);
}

// 2. 1U Rack Front Panel with Embedded 160x64 LCD & Gotek Floppy Emulator
void s760_state::render_rack_panel(bitmap_ind16 &bitmap)
{
	// 1. Fill 1U Rack Chassis Area (y = 240..359) with Dark Charcoal (Pen 10)
	for (int y = 240; y < 360; y++)
	{
		for (int x = 0; x < 640; x++)
		{
			bitmap.pix(y, x) = 10;
		}
	}

	// 2. Bezel Highlight & Shadow lines
	for (int x = 0; x < 640; x++)
	{
		bitmap.pix(240, x) = 11; // Top Highlight Line
		bitmap.pix(241, x) = 0;  // Bezel groove
		bitmap.pix(358, x) = 11; // Bottom groove
		bitmap.pix(359, x) = 0;  // Bottom shadow
	}

	// 3. Rack Mount Ears (Left x=0..14, Right x=626..639)
	for (int y = 240; y < 360; y++)
	{
		bitmap.pix(y, 14) = 0;
		bitmap.pix(y, 15) = 11;
		bitmap.pix(y, 625) = 0;
		bitmap.pix(y, 626) = 11;
	}

	auto draw_rack_screw = [&](int cx, int cy) {
		for (int dy = -3; dy <= 3; dy++)
			for (int dx = -3; dx <= 3; dx++)
				if (dx * dx + dy * dy <= 10)
					bitmap.pix(cy + dy, cx + dx) = 11;
		for (int dx = -2; dx <= 2; dx++)
			bitmap.pix(cy, cx + dx) = 0; // Screw slot
	};

	draw_rack_screw(7, 256);
	draw_rack_screw(7, 344);
	draw_rack_screw(633, 256);
	draw_rack_screw(633, 344);

	// 4. Left Silkscreen Panel Text & Power Switch (Unbranded Chassis)
	draw_string(bitmap, 18, 256, "S-760", 8);
	draw_string(bitmap, 18, 270, "DIGITAL", 6);
	draw_string(bitmap, 18, 280, "SAMPLER", 6);

	// Power Switch at (18..36, 298..336)
	draw_string(bitmap, 18, 296, "POWER", 6);
	for (int y = 308; y < 336; y++)
		for (int x = 18; x < 38; x++)
			bitmap.pix(y, x) = 0;
	for (int y = 310; y < 334; y++)
		for (int x = 20; x < 36; x++)
			bitmap.pix(y, x) = 9;
	for (int y = 312; y < 322; y++)
		for (int x = 22; x < 34; x++)
			bitmap.pix(y, x) = 3; // Power ON indicator

	// 5. Embedded 160x64 Monochrome LCD Screen (x=48..215, y=246..317)
	for (int y = 246; y < 318; y++)
		for (int x = 48; x < 216; x++)
			bitmap.pix(y, x) = 9;

	for (int x = 48; x < 216; x++)
	{
		bitmap.pix(246, x) = 0;
		bitmap.pix(317, x) = 11;
	}
	for (int y = 246; y < 318; y++)
	{
		bitmap.pix(y, 48) = 0;
		bitmap.pix(y, 215) = 11;
	}

	// Render LCD screen pixels (160x64) from (52, 250) to (211, 313)
	bool vram_has_data = false;
	for (int i = 0; i < 0x3FF; i++)
	{
		if (m_lcd_vram[i] != 0)
		{
			vram_has_data = true;
			break;
		}
	}

	// Fill LCD backlight background (Pen 12)
	for (int y = 0; y < 64; y++)
		for (int x = 0; x < 160; x++)
			bitmap.pix(250 + y, 52 + x) = 12;

	if (vram_has_data)
	{
		for (int y = 0; y < 64; y++)
		{
			for (int x = 0; x < 160; x++)
			{
				int bit_global = y * 160 + x;
				int word_idx = bit_global / 16;
				int bit_idx = 15 - (bit_global % 16);
				uint16_t word_val = m_lcd_vram[word_idx & 0x3FF];
				if (word_val & (1 << bit_idx))
					bitmap.pix(250 + y, 52 + x) = 13; // Bright LCD Pixel (Pen 13)
			}
		}
	}
	else
	{
		const char *mode_names[] = { "PERFORM MODE", "PATCH EDIT", "PARTIAL EDIT", "SAMPLE EDIT", "DISK LOAD", "SYSTEM CONFIG" };
		draw_string(bitmap, 60, 254, "S-760 SAMPLER", 13, 12);
		draw_string(bitmap, 56, 268, mode_names[m_active_tab], 13, 12);
		draw_string(bitmap, 56, 282, "SYSTEM v2.24  OK", 13, 12);
		draw_string(bitmap, 64, 296, "RAM: 32MB READY", 13, 12);
	}

	// LCD Function buttons row below LCD [F1]..[F6] (y = 324..338)
	const char *fkeys[6] = { "F1", "F2", "F3", "F4", "F5", "F6" };
	for (int b = 0; b < 6; b++)
	{
		int bx = 52 + b * 27;
		for (int y = 324; y < 338; y++)
			for (int x = bx; x < bx + 22; x++)
				bitmap.pix(y, x) = 9;
		draw_string(bitmap, bx + 3, 327, fkeys[b], 1, 9);
	}

	// 6. Center Controls Section (x=222..434)
	draw_string(bitmap, 224, 248, "MASTER", 6);
	draw_string(bitmap, 224, 258, "VOLUME", 6);

	// Master Volume knob (cx=246, cy=284, radius 13)
	for (int dy = -13; dy <= 13; dy++)
	{
		for (int dx = -13; dx <= 13; dx++)
		{
			if (dx * dx + dy * dy <= 169)
				bitmap.pix(284 + dy, 246 + dx) = 15;
		}
	}
	bitmap.pix(284 - 10, 246) = 0; // Pointer notch

	// PHONES jack at (246, 334)
	draw_string(bitmap, 224, 314, "PHONES", 6);
	for (int dy = -6; dy <= 6; dy++)
		for (int dx = -6; dx <= 6; dx++)
			if (dx * dx + dy * dy <= 36)
				bitmap.pix(334 + dy, 246 + dx) = 0;
	for (int dy = -3; dy <= 3; dy++)
		for (int dx = -3; dx <= 3; dx++)
			if (dx * dx + dy * dy <= 9)
				bitmap.pix(334 + dy, 246 + dx) = 11;

	// INPUT Level mini knobs at (286, 334) and (306, 334)
	draw_string(bitmap, 276, 314, "INPUT L-R", 6);
	auto draw_mini_knob = [&](int cx, int cy) {
		for (int dy = -5; dy <= 5; dy++)
			for (int dx = -5; dx <= 5; dx++)
				if (dx * dx + dy * dy <= 25)
					bitmap.pix(cy + dy, cx + dx) = 15;
		bitmap.pix(cy - 4, cx) = 0;
	};
	draw_mini_knob(286, 334);
	draw_mini_knob(306, 334);

	// Center Keypad Matrix at x=334..430
	auto draw_rack_btn = [&](int bx, int by, const char *txt, int bw = 28) {
		for (int y = by; y < by + 16; y++)
			for (int x = bx; x < bx + bw; x++)
				bitmap.pix(y, x) = 9;
		draw_string(bitmap, bx + 2, by + 4, txt, 1, 9);
	};

	draw_rack_btn(334, 252, "F1");
	draw_rack_btn(366, 252, "F2");
	draw_rack_btn(398, 252, "EDIT", 32);

	draw_rack_btn(334, 274, "F3");
	draw_rack_btn(366, 274, "F4");
	draw_rack_btn(398, 274, "UTIL", 32);

	draw_rack_btn(334, 296, "EXIT");
	draw_rack_btn(366, 296, "MENU");
	draw_rack_btn(398, 296, "ENTR", 32);

	draw_rack_btn(334, 318, "DEC ");
	draw_rack_btn(366, 318, "INC ");
	draw_rack_btn(398, 318, "SHFT", 32);

	// 7. Right Drive Bay: GOTEK USB Floppy Emulator (x=438..622, y=246..352)
	for (int y = 246; y < 352; y++)
		for (int x = 438; x < 622; x++)
			bitmap.pix(y, x) = 9;

	for (int x = 438; x < 622; x++)
	{
		bitmap.pix(246, x) = 0;
		bitmap.pix(351, x) = 11;
	}
	for (int y = 246; y < 352; y++)
	{
		bitmap.pix(y, 438) = 0;
		bitmap.pix(y, 621) = 11;
	}

	draw_string(bitmap, 444, 248, "GOTEK FlashFloppy USB", 6, 9);

	// Gotek OLED Display Glass (x=444..564, y=258..298)
	for (int y = 258; y < 298; y++)
		for (int x = 444; x < 564; x++)
			bitmap.pix(y, x) = 0; // OLED Deep Black

	for (int x = 444; x < 564; x++)
	{
		bitmap.pix(258, x) = 11;
		bitmap.pix(297, x) = 11;
	}
	for (int y = 258; y < 298; y++)
	{
		bitmap.pix(y, 444) = 11;
		bitmap.pix(y, 563) = 11;
	}

	// Line 1: [01/08] L701_1.IMG
	char oled_line1[32];
	int total_img = (int)m_gotek_names.size();
	const char *cur_name = (total_img > 0) ? m_gotek_names[m_gotek_selected_idx].c_str() : "NO IMAGES";
	snprintf(oled_line1, sizeof(oled_line1), "[%02d/%02d] %-9s", m_gotek_selected_idx + 1, total_img, cur_name);
	draw_string(bitmap, 448, 262, oled_line1, 14, 0);

	// Line 2: Track & Mount Status
	char oled_line2[32];
	if (m_gotek_selected_idx == m_gotek_mounted_idx)
		snprintf(oled_line2, sizeof(oled_line2), "T:00.0 *MOUNTED*");
	else
		snprintf(oled_line2, sizeof(oled_line2), "T:00.0 [PUSH-SEL]");
	draw_string(bitmap, 448, 274, oled_line2, 14, 0);

	// Line 3: Drive Specs
	draw_string(bitmap, 448, 286, "Roland S-760 1.44M", 14, 0);

	// Rotary Encoder Knob (cx=592, cy=276, radius 14)
	for (int dy = -14; dy <= 14; dy++)
	{
		for (int dx = -14; dx <= 14; dx++)
		{
			int dist2 = dx * dx + dy * dy;
			if (dist2 <= 196)
			{
				if (dist2 > 140)
					bitmap.pix(276 + dy, 592 + dx) = ((dx + dy) & 2) ? 6 : 11; // Knurled outer ring
				else if (dist2 <= 49)
					bitmap.pix(276 + dy, 592 + dx) = 9; // Center push button cap
				else
					bitmap.pix(276 + dy, 592 + dx) = 15; // Inner dial body
			}
		}
	}
	draw_string(bitmap, 578, 250, "ENCODER", 6, 9);
	draw_string(bitmap, 582, 294, "PUSH", 6, 9);

	// Indicator dot on encoder dial based on angle
	double rad = m_gotek_encoder_angle * (2.0 * M_PI / 12.0);
	int dot_x = 592 + (int)(9.0 * cos(rad));
	int dot_y = 276 + (int)(9.0 * sin(rad));
	bitmap.pix(dot_y, dot_x) = 1;
	bitmap.pix(dot_y + 1, dot_x) = 1;

	// Gotek Interactive Buttons: [ < ] [ > ] [ SEL ]
	auto draw_gotek_btn = [&](int bx, int by, int bw, const char *txt, bool is_sel = false) {
		for (int y = by; y < by + 18; y++)
			for (int x = bx; x < bx + bw; x++)
				bitmap.pix(y, x) = 6;
		for (int x = bx; x < bx + bw; x++)
		{
			bitmap.pix(by, x) = 1;
			bitmap.pix(by + 17, x) = 0;
		}
		for (int y = by; y < by + 18; y++)
		{
			bitmap.pix(y, bx) = 1;
			bitmap.pix(y, bx + bw - 1) = 0;
		}
		draw_string(bitmap, bx + (bw - (int)strlen(txt) * 8) / 2, by + 5, txt, is_sel ? 5 : 0, 6);
	};

	draw_gotek_btn(448, 306, 32, "<");
	draw_gotek_btn(486, 306, 32, ">");
	draw_gotek_btn(524, 306, 42, "SEL", true);

	// USB Stick Slot & Flash Drive Body (x=572..614, y=308..324)
	for (int y = 308; y < 324; y++)
		for (int x = 572; x < 614; x++)
			bitmap.pix(y, x) = 0; // USB Socket

	for (int y = 310; y < 322; y++)
		for (int x = 576; x < 610; x++)
			bitmap.pix(y, x) = 5; // Red USB Flash Drive Body
	for (int y = 312; y < 320; y++)
		for (int x = 584; x < 602; x++)
			bitmap.pix(y, x) = 0; // Black grip inset
	draw_string(bitmap, 574, 328, "USB", 6, 9);

	// Disk Activity LED at (452, 336)
	uint16_t led_color = (m_gotek_activity_timer > 0) ? 3 : 7;
	for (int dy = -3; dy <= 3; dy++)
		for (int dx = -3; dx <= 3; dx++)
			if (dx * dx + dy * dy <= 9)
				bitmap.pix(336 + dy, 452 + dx) = led_color;
	draw_string(bitmap, 460, 332, "ACT", 6, 9);
}

// OP-760 Color CRT Monitor Output + 1U Rack Panel Composite Renderer (640x360)
uint32_t s760_state::crt_update(screen_device &screen, bitmap_ind16 &bitmap, const rectangle &cliprect)
{
	// Process Keyboard Arrow inputs for instant responsive cursor motion
	uint8_t keys = m_key_arrows->read();
	if (!(keys & 0x01)) m_cur_x -= 5; // Arrow Left
	if (!(keys & 0x02)) m_cur_x += 5; // Arrow Right
	if (!(keys & 0x04)) m_cur_y -= 5; // Arrow Up
	if (!(keys & 0x08)) m_cur_y += 5; // Arrow Down

	m_cur_x = std::clamp(m_cur_x, 8, 632);
	m_cur_y = std::clamp(m_cur_y, 4, 354);

	// Process Gotek physical buttons & rotary encoder hotkeys
	uint8_t gotek_in = m_gotek_ctrl->read();
	bool gotek_prev_btn = !(gotek_in & 0x01);
	bool gotek_next_btn = !(gotek_in & 0x02);
	bool gotek_select_btn = !(gotek_in & 0x04);

	if (gotek_prev_btn && !m_last_gotek_prev)
	{
		int n = (int)m_gotek_names.size();
		m_gotek_selected_idx = (m_gotek_selected_idx - 1 + n) % n;
		m_gotek_encoder_angle = (m_gotek_encoder_angle - 1 + 12) % 12;
	}
	if (gotek_next_btn && !m_last_gotek_next)
	{
		int n = (int)m_gotek_names.size();
		m_gotek_selected_idx = (m_gotek_selected_idx + 1) % n;
		m_gotek_encoder_angle = (m_gotek_encoder_angle + 1) % 12;
	}
	if (gotek_select_btn && !m_last_gotek_select)
	{
		m_gotek_mounted_idx = m_gotek_selected_idx;
		m_gotek_activity_timer = 40;
		m_sound->mount_floppy_image(m_gotek_paths[m_gotek_mounted_idx], m_gotek_names[m_gotek_mounted_idx]);
	}
	m_last_gotek_prev = gotek_prev_btn;
	m_last_gotek_next = gotek_next_btn;
	m_last_gotek_select = gotek_select_btn;

	if (m_gotek_activity_timer > 0)
		m_gotek_activity_timer--;

	// Handle Click / Selection (Mouse Button 1, Space, or Enter)
	uint8_t btn = m_mouse_btn->read();
	bool clicked = !(keys & 0x10) || !(btn & 0x01);
	bool click_edge = clicked && !m_last_clicked;
	m_last_clicked = clicked;

	if (click_edge)
	{
		if (m_cur_y >= 14 && m_cur_y <= 28)
		{
			if (m_cur_x >= 12 && m_cur_x <= 84) m_active_tab = 0;       // PERFORM
			else if (m_cur_x >= 95 && m_cur_x <= 160) m_active_tab = 1;  // PATCH
			else if (m_cur_x >= 170 && m_cur_x <= 252) m_active_tab = 2; // PARTIAL
			else if (m_cur_x >= 265 && m_cur_x <= 336) m_active_tab = 3; // SAMPLE
			else if (m_cur_x >= 345 && m_cur_x <= 408) m_active_tab = 4; // DISK
			else if (m_cur_x >= 420 && m_cur_x <= 490) m_active_tab = 5; // SYSTEM
		}
		else if (m_cur_y >= 58 && m_cur_y <= 218 && m_cur_x >= 14 && m_cur_x <= 480)
		{
			m_selected_row = std::clamp((m_cur_y - 58) / 10, 0, 15);
			m_sound->trigger_preview(m_selected_row);
		}
		// Gotek Interactive Buttons:
		else if (m_cur_y >= 304 && m_cur_y <= 326)
		{
			int n = (int)m_gotek_names.size();
			if (m_cur_x >= 448 && m_cur_x <= 480) // [ < ] Prev Button
			{
				m_gotek_selected_idx = (m_gotek_selected_idx - 1 + n) % n;
				m_gotek_encoder_angle = (m_gotek_encoder_angle - 1 + 12) % 12;
			}
			else if (m_cur_x >= 486 && m_cur_x <= 518) // [ > ] Next Button
			{
				m_gotek_selected_idx = (m_gotek_selected_idx + 1) % n;
				m_gotek_encoder_angle = (m_gotek_encoder_angle + 1) % 12;
			}
			else if (m_cur_x >= 524 && m_cur_x <= 566) // [ SEL ] Select Button
			{
				m_gotek_mounted_idx = m_gotek_selected_idx;
				m_gotek_activity_timer = 40;
				m_sound->mount_floppy_image(m_gotek_paths[m_gotek_mounted_idx], m_gotek_names[m_gotek_mounted_idx]);
				fdc_load_disk_image(m_gotek_paths[m_gotek_mounted_idx]);
			}
		}
		// Gotek Rotary Encoder Dial (center at 592, 276, radius 16):
		else if (std::hypot(m_cur_x - 592, m_cur_y - 276) <= 16)
		{
			int n = (int)m_gotek_names.size();
			if (std::hypot(m_cur_x - 592, m_cur_y - 276) <= 8) // Center push action
			{
				m_gotek_mounted_idx = m_gotek_selected_idx;
				m_gotek_activity_timer = 40;
				m_sound->mount_floppy_image(m_gotek_paths[m_gotek_mounted_idx], m_gotek_names[m_gotek_mounted_idx]);
				fdc_load_disk_image(m_gotek_paths[m_gotek_mounted_idx]);
			}
			else if (m_cur_y < 276) // Turn left
			{
				m_gotek_selected_idx = (m_gotek_selected_idx - 1 + n) % n;
				m_gotek_encoder_angle = (m_gotek_encoder_angle - 1 + 12) % 12;
			}
			else // Turn right
			{
				m_gotek_selected_idx = (m_gotek_selected_idx + 1) % n;
				m_gotek_encoder_angle = (m_gotek_encoder_angle + 1) % 12;
			}
		}
	}

	// 1. Fill CRT workspace (y = 0..239) with Roland Royal Blue
	for (int y = 0; y < 240; y++)
		for (int x = 0; x < 640; x++)
			bitmap.pix(y, x) = 2;

	// 2. Top Status Bar (Green Bar)
	for (int y = 0; y < 14; y++)
		for (int x = 0; x < 640; x++)
			bitmap.pix(y, x) = 3;

	draw_string(bitmap, 6, 3, "Volume[ - :      ]                 ID:04              ---/---", 0, 3);

	// 3. Mode Ribbon (White Background)
	for (int y = 14; y < 28; y++)
		for (int x = 0; x < 640; x++)
			bitmap.pix(y, x) = 1;

	draw_string(bitmap, 16, 17, "PERFORM", (m_active_tab == 0) ? 5 : 0, 1);
	draw_string(bitmap, 88, 17, "|", 0, 1);
	draw_string(bitmap, 108, 17, "PATCH", (m_active_tab == 1) ? 5 : 0, 1);
	draw_string(bitmap, 164, 17, "|", 0, 1);
	draw_string(bitmap, 184, 17, "PARTIAL", (m_active_tab == 2) ? 5 : 0, 1);
	draw_string(bitmap, 256, 17, "|", 0, 1);
	draw_string(bitmap, 276, 17, "SAMPLE", (m_active_tab == 3) ? 5 : 0, 1);
	draw_string(bitmap, 340, 17, "|", 0, 1);
	draw_string(bitmap, 360, 17, "DISK", (m_active_tab == 4) ? 5 : 0, 1);
	draw_string(bitmap, 412, 17, "|", 0, 1);
	draw_string(bitmap, 432, 17, "SYSTEM", (m_active_tab == 5) ? 5 : 0, 1);

	// Draw active tab box
	int tab_boxes[6][2] = {
		{ 12, 84 },   // 0: PERFORM
		{ 102, 156 }, // 1: PATCH
		{ 178, 248 }, // 2: PARTIAL
		{ 270, 332 }, // 3: SAMPLE
		{ 352, 402 }, // 4: DISK
		{ 426, 486 }  // 5: SYSTEM
	};

	int bx0 = tab_boxes[m_active_tab][0];
	int bx1 = tab_boxes[m_active_tab][1];
	for (int x = bx0; x < bx1; x++)
	{
		bitmap.pix(14, x) = 5;
		bitmap.pix(27, x) = 5;
	}
	for (int y = 14; y < 28; y++)
	{
		bitmap.pix(y, bx0) = 5;
		bitmap.pix(y, bx1) = 5;
	}

	// 4. Context Sub-Ribbon (Light Gray)
	for (int y = 28; y < 40; y++)
		for (int x = 0; x < 640; x++)
			bitmap.pix(y, x) = 6;

	// 5. Render active mode view
	switch (m_active_tab)
	{
		case 0: render_perform_mode(bitmap); break;
		case 1: render_patch_mode(bitmap); break;
		case 2: render_partial_mode(bitmap); break;
		case 3: render_sample_mode(bitmap); break;
		case 4: render_disk_mode(bitmap); break;
		case 5: render_system_mode(bitmap); break;
		default: render_disk_mode(bitmap); break;
	}

	// 6. Bottom Button Bar (Light Gray)
	for (int y = 224; y < 240; y++)
		for (int x = 0; x < 640; x++)
			bitmap.pix(y, x) = 6;

	auto draw_soft_button = [&](int pbx, const char *txt) {
		for (int y = 226; y < 238; y++)
			for (int x = pbx; x < pbx + 100; x++)
				bitmap.pix(y, x) = 1;
		draw_string(bitmap, pbx + 12, 228, txt, 0, 1);
	};

	const char *btn_labels[6][5] = {
		{ " Play  ", " Edit  ", " Part+ ", " Part- ", " Save  " }, // PERFORM
		{ " Wave  ", " TVF   ", " TVA   ", " LFO   ", " Pitch " }, // PATCH
		{ " TVF   ", " TVA   ", " ENV   ", " LFO   ", " Copy  " }, // PARTIAL
		{ " Loop  ", " Norm  ", " Cut   ", " Pitch ", " Revrs " }, // SAMPLE
		{ " AllOn ", "       ", " ConvLD", " ON Off", " VolInfo" }, // DISK
		{ " Setup ", " MIDI  ", " Test  ", " Format", " SaveSys" }  // SYSTEM
	};

	for (int b = 0; b < 5; b++)
	{
		draw_soft_button(12 + b * 128, btn_labels[m_active_tab][b]);
	}

	// 7. Render 1U Rack Panel with Embedded LCD & Gotek Floppy Emulator (y = 240..359)
	render_rack_panel(bitmap);

	// 8. Render Hardware Crosshair / Mouse Cursor (Pillar 4)
	for (int i = -4; i <= 4; i++)
	{
		if (m_cur_y + i >= 0 && m_cur_y + i < 360)
		{
			bitmap.pix(m_cur_y + i, m_cur_x) = 1; // White crosshair
		}
		if (m_cur_x + i >= 0 && m_cur_x + i < 640)
		{
			bitmap.pix(m_cur_y, m_cur_x + i) = 1;
		}
	}

	// 9. Trigger RFSC16A VDP VBlank Interrupt (Bit 4)
	trigger_irq(IRQ_VDP_VBLANK);

	return 0;
}

void s760_state::s760_mem(address_map &map)
{
	map(0x0000, 0x1FFF).ram();                                                   // Register File & Work RAM (0x1120 = SP)
	map(0x2080, 0xDFFF).rom().region("maincpu", 0x4800);                         // OS Code segment (S760224.IMG offset 0x4800)
	map(0xD000, 0xD0FF).rw(FUNC(s760_state::vdp_r), FUNC(s760_state::vdp_w));   // Roland RFSC16A VDP registers & VRAM port
	map(0xE000, 0xEFF7).ram().share("lcd_vram");                                 // LCD Display VRAM (SED1335)
	map(0xF000, 0xF01F).rw(FUNC(s760_state::mmio_r), FUNC(s760_state::mmio_w)); // Gate array MMIO latches
	map(0xF020, 0xF02F).rw(FUNC(s760_state::scsi_r), FUNC(s760_state::scsi_w)); // Fujitsu MB89352A SCSI SPC registers
	map(0xF040, 0xF047).rw(FUNC(s760_state::fdc_r), FUNC(s760_state::fdc_w));   // NEC uPD72068 FDC registers
}

static INPUT_PORTS_START( s760 )
	PORT_START("KEY_ARROWS")
	PORT_BIT( 0x01, IP_ACTIVE_LOW, IPT_JOYSTICK_LEFT )  PORT_NAME("Cursor Left / Arrow Left")   PORT_CODE(KEYCODE_LEFT)
	PORT_BIT( 0x02, IP_ACTIVE_LOW, IPT_JOYSTICK_RIGHT ) PORT_NAME("Cursor Right / Arrow Right") PORT_CODE(KEYCODE_RIGHT)
	PORT_BIT( 0x04, IP_ACTIVE_LOW, IPT_JOYSTICK_UP )    PORT_NAME("Cursor Up / Arrow Up")       PORT_CODE(KEYCODE_UP)
	PORT_BIT( 0x08, IP_ACTIVE_LOW, IPT_JOYSTICK_DOWN )  PORT_NAME("Cursor Down / Arrow Down")   PORT_CODE(KEYCODE_DOWN)
	PORT_BIT( 0x10, IP_ACTIVE_LOW, IPT_BUTTON1 )        PORT_NAME("Select / Enter")             PORT_CODE(KEYCODE_ENTER) PORT_CODE(KEYCODE_SPACE)

	PORT_START("MOUSEX")
	PORT_BIT( 0xff, 0x00, IPT_MOUSE_X ) PORT_SENSITIVITY(100) PORT_KEYDELTA(0) PORT_PLAYER(1) PORT_CHANGED_MEMBER(DEVICE_SELF, FUNC(s760_state::mouse_x), 0)

	PORT_START("MOUSEY")
	PORT_BIT( 0xff, 0x00, IPT_MOUSE_Y ) PORT_SENSITIVITY(100) PORT_KEYDELTA(0) PORT_PLAYER(1) PORT_CHANGED_MEMBER(DEVICE_SELF, FUNC(s760_state::mouse_y), 0)

	PORT_START("MOUSEBTN")
	PORT_BIT( 0x01, IP_ACTIVE_LOW, IPT_BUTTON2 ) PORT_NAME("Mouse Left Click")  PORT_CODE(MOUSECODE_BUTTON1)
	PORT_BIT( 0x02, IP_ACTIVE_LOW, IPT_BUTTON3 ) PORT_NAME("Mouse Right Click") PORT_CODE(MOUSECODE_BUTTON2)

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

	palette_device &palette(PALETTE(config, "palette", FUNC(s760_state::s760_palette), 16));

	// Unified Output: OP-760 Color CRT Display + 1U Rack Panel with LCD & Gotek (640x360)
	screen_device &crt_screen(SCREEN(config, "crt_screen"));
	crt_screen.set_refresh_hz(60);
	crt_screen.set_vblank_time(ATTOSECONDS_IN_USEC(2500));
	crt_screen.set_size(640, 360);
	crt_screen.set_visarea(0, 639, 0, 359);
	crt_screen.set_screen_update(FUNC(s760_state::crt_update));
	crt_screen.set_palette(palette);
}

ROM_START( s760 )
	ROM_REGION16_LE( 0x168000, "maincpu", 0 )
	ROM_LOAD( "s760224.img", 0x000000, 0x168000, CRC(b14b0257) SHA1(e5ab4abc96654965f23d1930b1e93c9211784873) )
ROM_END

} // anonymous namespace

SYST( 1993, s760, 0, 0, s760, s760, s760_state, empty_init, "Roland", "S-760 Digital Sampler", MACHINE_IMPERFECT_GRAPHICS )


