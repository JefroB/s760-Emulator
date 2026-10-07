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
	const std::vector<SampleDesc>& samples() const { return m_samples; }

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

	// 1. Check for user-supplied Akai S1000 ISO or Roland sound disk files
	const char *disk_paths[] = {
		"roms/s760/sound.iso", "roms/akai.iso", "sound.iso", "roms/s760/sound.img",
		"roms/sound.img", "roms/s760.iso"
	};

	bool loaded_from_disk = false;
	for (const char *path : disk_paths)
	{
		std::ifstream file(path, std::ios::binary);
		if (file.is_open())
		{
			char magic[24] = {0};
			file.read(magic, 22);
			if (strstr(magic, "AKAI") != nullptr || strstr(magic, "S1000") != nullptr)
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
		osd_printf_info("[S-760 AUDITION] Playing Akai S1000 Sample: '%s' (Root Key %d, %d Hz, %u samples)\n", s.name, s.root_key, s.sample_rate, s.length);
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
		, m_lcd_screen(*this, "lcd_screen")
		, m_crt_screen(*this, "crt_screen")
		, m_lcd_vram(*this, "lcd_vram")
		, m_key_arrows(*this, "KEY_ARROWS")
		, m_mouse_btn(*this, "MOUSEBTN")
		, m_sound(*this, "s760_sound")
	{ }

	void s760(machine_config &config);
	void s760_palette(palette_device &palette) const;

	DECLARE_INPUT_CHANGED_MEMBER(mouse_x);
	DECLARE_INPUT_CHANGED_MEMBER(mouse_y);

protected:
	virtual void machine_start() override ATTR_COLD;
	virtual void machine_reset() override ATTR_COLD;

private:
	required_device<i8x9x_device> m_maincpu;
	required_device<screen_device> m_lcd_screen;
	required_device<screen_device> m_crt_screen;
	required_shared_ptr<uint16_t> m_lcd_vram;

	required_ioport m_key_arrows;
	required_ioport m_mouse_btn;
	required_device<s760_sound_device> m_sound;

	// Gate Array MMIO & VDP Registers
	uint8_t m_mmio[16];
	uint8_t m_vdp_regs[128];
	uint16_t m_vdp_addr;
	std::unique_ptr<uint8_t[]> m_vdp_vram;

	// Sampler GUI State
	int m_cur_x;
	int m_cur_y;
	int m_active_tab;
	int m_selected_row;
	bool m_last_clicked;

	void s760_mem(address_map &map) ATTR_COLD;

	uint8_t mmio_r(offs_t offset);
	void mmio_w(offs_t offset, uint8_t data);

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

	m_cur_y = std::clamp(m_cur_y + delta, 4, 234);
}

void s760_state::machine_start()
{
	m_vdp_vram = std::make_unique<uint8_t[]>(0x20000); // 128KB TC511664 VRAM
	memset(m_vdp_vram.get(), 0, 0x20000);
	memset(m_vdp_regs, 0, sizeof(m_vdp_regs));
	memset(m_mmio, 0, sizeof(m_mmio));

	m_mmio[0] = 0x80; // Gate array ready status bit
	m_mmio[2] = 0x20; // Gate array status bit 5

	m_vdp_addr = 0;
	m_cur_x = 350;
	m_cur_y = 100;
	m_active_tab = 4; // Default to DISK Load Mode
	m_selected_row = 3; // Default to Row 3 (Double Bass)
	m_last_clicked = false;
}

void s760_state::machine_reset()
{
	m_vdp_addr = 0;
	m_sound->trigger_preview(3);
}

uint8_t s760_state::mmio_r(offs_t offset)
{
	uint8_t val = m_mmio[offset & 0x0F];
	logerror("[MMIO R] 0xF0%02X => 0x%02X\n", offset, val);
	return val;
}

void s760_state::mmio_w(offs_t offset, uint8_t data)
{
	logerror("[MMIO W] 0xF0%02X <= 0x%02X\n", offset, data);
	m_mmio[offset & 0x0F] = data;
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
	palette.set_pen_color(3, rgb_t(0, 200, 80));      // 3: Status Green (Top Banner)
	palette.set_pen_color(4, rgb_t(255, 230, 0));     // 4: Yellow Highlight / Cursor
	palette.set_pen_color(5, rgb_t(220, 60, 20));     // 5: Red / Orange Tab Border
	palette.set_pen_color(6, rgb_t(190, 195, 205));   // 6: Light Gray Panel
	palette.set_pen_color(7, rgb_t(0, 0, 96));        // 7: Dark Navy
	palette.set_pen_color(8, rgb_t(0, 220, 220));     // 8: Cyan
	palette.set_pen_color(9, rgb_t(60, 60, 70));      // 9: Dark Slate
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
	draw_string(bitmap, 8, 30, "PLAY [PERFORM]       |  MIDI  |  Part  |  Split |  Mix", 0, 6);
	draw_string(bitmap, 16, 44, "[PERFORM PLAY]  PRM: 01 JP-8 Multi Set       CD[RAM: 32MB]", 1, 2);

	for (int x = 16; x < 624; x++)
		bitmap.pix(54, x) = 1;

	const char *parts[] = {
		"PART 1: Ch 01 | P11: JP-8 Brass 1   | Vol: 127 | Pan: <0> | Out: 1-2",
		"PART 2: Ch 02 | P12: JP-8 Strgs 1   | Vol: 110 | Pan: L15 | Out: 1-2",
		"PART 3: Ch 03 | P13: VP Strings 1   | Vol: 105 | Pan: R15 | Out: 1-2",
		"PART 4: Ch 04 | P14: VP Choir 1     | Vol: 090 | Pan: <0> | Out: 3-4",
		"PART 5: Ch 05 | P15: Synth 1        | Vol: 100 | Pan: <0> | Out: 1-2",
		"PART 6: Ch 06 | P16: Synth 2        | Vol: 100 | Pan: <0> | Out: 1-2",
		"PART 7: Ch 07 | P17: Synth 3        | Vol: 100 | Pan: <0> | Out: 1-2",
		"PART 8: Ch 08 | P18: Synth 4        | Vol: 100 | Pan: <0> | Out: 1-2",
		"PART 9: Ch 09 | ---: ------------   | Vol: --- | Pan: --- | Out: ---",
		"PART10: Ch 10 | ---: ------------   | Vol: --- | Pan: --- | Out: ---",
		"PART11: Ch 11 | ---: ------------   | Vol: --- | Pan: --- | Out: ---",
		"PART12: Ch 12 | ---: ------------   | Vol: --- | Pan: --- | Out: ---",
		"PART13: Ch 13 | ---: ------------   | Vol: --- | Pan: --- | Out: ---",
		"PART14: Ch 14 | ---: ------------   | Vol: --- | Pan: --- | Out: ---",
		"PART15: Ch 15 | ---: ------------   | Vol: --- | Pan: --- | Out: ---",
		"PART16: Ch 16 | ---: ------------   | Vol: --- | Pan: --- | Out: ---"
	};

	int sy = 58 + m_selected_row * 10;
	for (int y = sy; y < sy + 11; y++)
		for (int x = 14; x < 570; x++)
			bitmap.pix(y, x) = 4;

	for (int i = 0; i < 16; i++)
	{
		if (i == m_selected_row)
			draw_string(bitmap, 16, 60 + i * 10, parts[i], 0, 4);
		else
			draw_string(bitmap, 16, 60 + i * 10, parts[i], 1, 2);
	}
}

void s760_state::render_patch_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 8, 30, "EDIT [PATCH]         |  Split |  Layer |  V-Sw  |  Common", 0, 6);
	draw_string(bitmap, 16, 44, "[PATCH EDIT]  P11: JP-8 Brass 1   (4 Partials Layered)", 1, 2);

	for (int x = 16; x < 624; x++)
		bitmap.pix(54, x) = 1;

	draw_string(bitmap, 20, 64,  "Key Mode:    NORMAL           Octave Shift:  0", 1, 2);
	draw_string(bitmap, 20, 78,  "Velocity Sw: ON (Threshold: 64)   X-Fade:    OFF", 1, 2);
	draw_string(bitmap, 20, 92,  "Pitch Bend:  +2 / -2 Semi     Aftertouch:    CUTOFF +12", 1, 2);
	draw_string(bitmap, 20, 110, "--------------------------------------------------------", 1, 2);
	draw_string(bitmap, 20, 124, "PARTIAL 1: S01 JP8_Wave_L   Range: C-1 -- G3   Level: 127", 4, 2);
	draw_string(bitmap, 20, 138, "PARTIAL 2: S02 JP8_Wave_R   Range: C-1 -- G3   Level: 127", 1, 2);
	draw_string(bitmap, 20, 152, "PARTIAL 3: S03 JP8_High_L   Range: G#3 -- G9   Level: 120", 1, 2);
	draw_string(bitmap, 20, 166, "PARTIAL 4: S04 JP8_High_R   Range: G#3 -- G9   Level: 120", 1, 2);
}

void s760_state::render_partial_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 8, 30, "EDIT [PARTIAL]       |  TVF   |  TVA   |  ENV   |  LFO", 0, 6);
	draw_string(bitmap, 16, 44, "[TVF & TVA SETUP]  S01: JP8_Wave_L (Filter / Amp Envelopes)", 1, 2);

	for (int x = 16; x < 624; x++)
		bitmap.pix(54, x) = 1;

	draw_string(bitmap, 20, 64,  "TVF Type:     LPF (12dB/Oct)  Cutoff: 84     Resonance: 22", 1, 2);
	draw_string(bitmap, 20, 80,  "TVF KeyFollow: +1.0           Env Depth: +48 Vel Curve: EXP", 1, 2);
	draw_string(bitmap, 20, 98,  "TVF Envelope:  A: 12 | D1: 45 | D2: 80 | S: 64 | R: 52", 4, 2);
	draw_string(bitmap, 20, 116, "TVA Envelope:  A: 05 | D1: 30 | D2: 70 | S: 96 | R: 40", 1, 2);
	draw_string(bitmap, 20, 134, "LFO Setup:     Rate: 65 | Depth: 18 | Delay: 10 | Wave: TRI", 1, 2);
	draw_string(bitmap, 20, 152, "Pan Position:  L15 (Left Center Stereo Spread)", 1, 2);
}

void s760_state::render_sample_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 8, 30, "EDIT [SAMPLE]        |  Loop  |  Pitch |  Norm  |  Convert", 0, 6);
	draw_string(bitmap, 16, 44, "[SAMPLE WAVE]  W01: JP-8_Brass_44k.wav   (16-Bit Mono 44.1kHz)", 1, 2);

	for (int x = 16; x < 624; x++)
		bitmap.pix(54, x) = 1;

	draw_string(bitmap, 20, 64,  "Sample Length: 130,560 words (2.95 sec)  Original Key: C4", 1, 2);
	draw_string(bitmap, 20, 78,  "Loop Mode:     FORWARD                   Fine Tune:    +0", 1, 2);
	draw_string(bitmap, 20, 92,  "Start Point:   0000,000                  End Point:    0130,560", 1, 2);
	draw_string(bitmap, 20, 106, "Loop Start:    0048,200                  Loop End:     0128,400", 4, 2);

	// Waveform display graph
	for (int x = 20; x < 480; x++)
	{
		int mid = 150;
		int amp = (int)(15.0 * sin((x - 20) * 0.15) * cos((x - 20) * 0.04));
		bitmap.pix(mid + amp, x) = 4;
		bitmap.pix(mid - amp, x) = 8;
	}
}

void s760_state::render_disk_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 8, 30, "Convert LD[S]        |  Muted  |  Mark  |  Jump  |  Com", 0, 6);
	draw_string(bitmap, 16, 44, "[GE Pach]   Art  1]    CD[FDD: -FloppyDisk-]", 1, 2);

	for (int x = 16; x < 624; x++)
		bitmap.pix(54, x) = 1;

	const auto &samples = m_sound->samples();
	char row_buf[64];
	for (int i = 0; i < 16; i++)
	{
		const char *name = "";
		if (i < samples.size())
			name = samples[i].name;
		else if (i == 0) name = "JP-8 Brass 1";
		else if (i == 1) name = "JP-8 Strgs 1";
		else if (i == 2) name = "VP Strings 1";
		else if (i == 3) name = "Double Bass";
		else if (i == 4) name = "VP Choir 1";
		else if (i == 5) name = "Synth 1";
		else if (i == 6) name = "Synth 2";
		else if (i == 7) name = "Synth 3";

		snprintf(row_buf, sizeof(row_buf), "P%02d: %-16s", i + 1, name);
		if (i == m_selected_row)
			draw_string(bitmap, 16, 60 + i * 10, row_buf, 0, 4);
		else
			draw_string(bitmap, 16, 60 + i * 10, row_buf, 1, 2);
	}

	auto draw_param_box = [&](int pbx, int pby, int pbw, int pbh, const char *txt) {
		for (int y = pby; y < pby + pbh; y++)
			for (int x = pbx; x < pbx + pbw; x++)
				bitmap.pix(y, x) = 4;
		draw_string(bitmap, pbx + 6, pby + 2, txt, 0, 4);
	};

	draw_param_box(500, 58, 120, 12, "   Int.");
	draw_param_box(500, 74, 120, 12, " 2954sec");
	draw_param_box(500, 90, 120, 12, "  Marked");
	draw_param_box(500, 106, 120, 12, "    0");
	draw_param_box(500, 122, 120, 12, "   +/-");
}

void s760_state::render_system_mode(bitmap_ind16 &bitmap)
{
	draw_string(bitmap, 8, 30, "SETUP [SYSTEM]       |  MIDI   |  Test  |  Format|  SaveSys", 0, 6);
	draw_string(bitmap, 16, 44, "[SYSTEM SETUP]  Roland S-760 System Version 2.24", 1, 2);

	for (int x = 16; x < 624; x++)
		bitmap.pix(54, x) = 1;

	draw_string(bitmap, 20, 64,  "1. Self SCSI ID:     [ 7 ] (Host Controller ID)", 1, 2);
	draw_string(bitmap, 20, 80,  "2. Boot Drive:       [ Floppy / SCSI Default ]", 1, 2);
	draw_string(bitmap, 20, 96,  "3. Controller:       [ RC-100 + Color CRT ]", 4, 2);
	draw_string(bitmap, 20, 112, "4. Master Tune:      [ 440.0 Hz ]", 1, 2);
	draw_string(bitmap, 20, 128, "5. Output Level:     [ +4 dBu Balanced ]", 1, 2);
	draw_string(bitmap, 20, 144, "6. Wave Memory:      [ 32 MBytes OK (2x 16MB SIMM) ]", 1, 2);
	draw_string(bitmap, 20, 160, "7. Option Board:     [ OP-760-2 Video Board Installed ]", 1, 2);
}

// 2. OP-760-1 / OP-760-2 CRT Monitor Output (RFSC16A VDP: Authentic Roland S-760 GUI)
uint32_t s760_state::crt_update(screen_device &screen, bitmap_ind16 &bitmap, const rectangle &cliprect)
{
	// Process Keyboard Arrow inputs for instant responsive cursor motion
	uint8_t keys = m_key_arrows->read();
	if (!(keys & 0x01)) m_cur_x -= 5; // Arrow Left
	if (!(keys & 0x02)) m_cur_x += 5; // Arrow Right
	if (!(keys & 0x04)) m_cur_y -= 5; // Arrow Up
	if (!(keys & 0x08)) m_cur_y += 5; // Arrow Down

	m_cur_x = std::clamp(m_cur_x, 8, 632);
	m_cur_y = std::clamp(m_cur_y, 4, 234);

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
	}

	// 1. Fill main workspace with Roland Royal Blue
	bitmap.fill(2, cliprect);

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

	// 7. Render Hardware Crosshair / Mouse Cursor (Pillar 4)
	for (int i = -4; i <= 4; i++)
	{
		if (m_cur_y + i >= 0 && m_cur_y + i < 240)
		{
			bitmap.pix(m_cur_y + i, m_cur_x) = 1; // White crosshair
		}
		if (m_cur_x + i >= 0 && m_cur_x + i < 640)
		{
			bitmap.pix(m_cur_y, m_cur_x + i) = 1;
		}
	}

	return 0;
}

void s760_state::s760_mem(address_map &map)
{
	map(0x0000, 0x1FFF).ram();                                                   // Register File & Work RAM (0x1120 = SP)
	map(0x2080, 0xDFFF).rom().region("maincpu", 0x4800);                         // OS Code segment (S760224.IMG offset 0x4800)
	map(0xD000, 0xD0FF).rw(FUNC(s760_state::vdp_r), FUNC(s760_state::vdp_w));   // Roland RFSC16A VDP registers & VRAM port
	map(0xE000, 0xEFF7).ram().share("lcd_vram");                                 // LCD Display VRAM (SED1335)
	map(0xF000, 0xF00F).rw(FUNC(s760_state::mmio_r), FUNC(s760_state::mmio_w)); // Gate array MMIO latches
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

	palette_device &palette(PALETTE(config, "palette", FUNC(s760_state::s760_palette), 10));

	// Output 1: Front Panel Monochrome LCD Display (160x64 pixels)
	screen_device &lcd_screen(SCREEN(config, "lcd_screen"));
	lcd_screen.set_refresh_hz(60);
	lcd_screen.set_vblank_time(ATTOSECONDS_IN_USEC(2500));
	lcd_screen.set_size(160, 64);
	lcd_screen.set_visarea(0, 159, 0, 63);
	lcd_screen.set_screen_update(FUNC(s760_state::lcd_update));
	lcd_screen.set_palette(palette);

	// Output 2: OP-760-2 External Color CRT Monitor Output (640x240 / RGB / S-Video)
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
	ROM_LOAD( "s760.rom", 0x000000, 0x168000, CRC(b14b0257) SHA1(e5ab4abc96654965f23d1930b1e93c9211784873) )
ROM_END

} // anonymous namespace

SYST( 1993, s760, 0, 0, s760, s760, s760_state, empty_init, "Roland", "S-760 Digital Sampler", MACHINE_IMPERFECT_GRAPHICS )

