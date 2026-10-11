# Licensing, project purpose and hardware use

## Project-owned code

Original code owned by this project's contributors and authorized for release
is offered under the standard [BSD-3-Clause license](../LICENSE). This follows
the owner's preference for broad reuse, including modification, redistribution,
commercial use and closed-source derivatives. Required notices must be retained;
the license does not grant permission to imply contributor endorsement.

This is not a relicensing of third-party material or a representation that the
project owns every file in the repository. Existing file-level licenses and
copyright notices remain in force. MAME, its bundled libraries and other
dependencies retain their own terms. The complete MAME binary is not made BSD
by this choice. Files or contributions of uncertain provenance must be resolved
before including them in a release. See the [distribution assessment](NATIVE_BOUNDARY_QUALIFICATION.md).

## Purpose and limitations

The project provides an emulator for understanding and testing sampler behavior,
including development of independently authored firmware replacements and new
functions for physical hardware. Emulator success does not establish that a
firmware image is safe or correct on a real sampler. Device behavior still has
documented gaps; firmware experiments may cause data loss, make a device
unusable, or require external recovery equipment.

The standard license supplies the software **as is**, disclaims warranties and
limits liability. No guarantee of hardware safety, fitness, uninterrupted
operation or recovery is provided. These are standard license provisions, not
a guarantee that all claims or liability are excluded in every jurisdiction.
They also do not resolve third-party intellectual-property rights.

Hardware experimenters should keep verified original firmware and data backups,
establish a recovery method before writing a device, and independently validate
each change. This guidance adds no extra restriction to the BSD license.
No project-branded hardware-safe replacement firmware is currently qualified.

## Firmware and contributions

Roland binaries and third-party sample libraries are not distributed. Users
supply authorized copies as described in [firmware setup](FIRMWARE_SETUP.md).
An independently authored replacement may ship after functionality, provenance
and licensing are established; merely editing or repackaging Roland firmware
does not satisfy that policy.

Contributors should submit only material they have authority to license, identify
copied or adapted third-party code and retain its notices. Original contributions
use BSD-3-Clause unless an applicable existing file license requires otherwise.
Nothing here retroactively grants rights to someone else's contribution.

The standard license text is retained without custom legal clauses. Reference:
[Open Source Initiative BSD-3-Clause](https://opensource.org/license/bsd-3-clause).
