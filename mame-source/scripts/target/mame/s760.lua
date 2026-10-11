-- license:BSD-3-Clause
-- copyright-holders:MAMEdev Team

CPUS["MCS96"] = true
SOUNDS["SAMPLES"] = true
MACHINES["WATCHDOG"] = true
MACHINES["EEPROMDEV"] = true

function createProjects_mame_s760(_target, _subtarget)
	project ("mame_s760")
	targetsubdir(_target .."_" .. _subtarget)
	kind (LIBTYPE)
	uuid (os.uuid("drv-mame-s760"))
	addprojectflags()
	precompiledheaders_novs()

	includedirs {
		MAME_DIR .. "src/osd",
		MAME_DIR .. "src/emu",
		MAME_DIR .. "src/devices",
		MAME_DIR .. "src/mame/shared",
		MAME_DIR .. "src/lib",
		MAME_DIR .. "src/lib/util",
		MAME_DIR .. "3rdparty",
		GEN_DIR  .. "mame/layout",
	}

	files {
		MAME_DIR .. "src/mame/roland/s760.cpp",
	}
end

function linkProjects_mame_s760(_target, _subtarget)
	links {
		"mame_s760",
	}
end
