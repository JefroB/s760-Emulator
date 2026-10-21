# Precommit CI check — 2026-10-21

The README rewrite, hardware-documentation consolidation, fixture relocation and compiler/decompiler exclusions were checked against a checkout-like source copy. It included the Git index after tracking removals plus pending nonignored files; private firmware, exports, compiler/decompiler tools and agent files were absent. The built Python extension was supplied as CI would supply a build output. No hosted GitHub Actions run was triggered.

## Corrections

The first public-source run collected 791 tests but failed 87 tests in four SDS patch modules because they read uncommitted OS images without guards. The tests now resolve private firmware on demand and explicitly skip when it is absent. Four synthetic validation/branch checks were separated from image-rebuild cases so they continue running without firmware. No firmware was added to Git or downloaded.

The local-only toolchain distribution-policy tests also contained seven assertions requiring tools to stay tracked. These now enforce the user's local-only policy while preserving the separate checks rejecting proprietary/derived distribution inputs. This test file remains ignored and does not enter public CI.

The workflow now exposes the installed MSVC compiler through vswhere for Python C++ probes, prints pytest skip reasons and uploads JUnit results from ignored `temp/ci/`. Compiler discovery and workflow YAML were checked locally.

## Results

| Check | Result |
| --- | --- |
| Checkout-like backend, no firmware or compiler tools | 599 passed, 196 explicit skips; no failures |
| Complete local backend with firmware/native runtime and local tools | 1,239 passed, 2 existing boot-observer/property skips |
| Four corrected SDS modules with local firmware | 104 passed, no skips |
| Local-only distribution-policy checks | 41 passed |
| C++ executables invoked by CI | All six passed |
| Frontend Vitest | 24 files, 128 tests passed |
| Playwright using CI configuration | 9 passed, 25 external/native/packaged cases skipped |

The firmware-free run includes seven passing synthetic checks and 97 explicit firmware skips across the four corrected modules. The existing two authored-program boot skips are not acceptance for a new OS.

## Limits and reproduction

This was local validation, not a fresh hosted build or dependency installation. Existing C++ executables and the Python extension were used; the checkout-like copy included only the MAME driver/CPU sources inspected by Python tests. Frontend checks used Node22.17.1. The workflow's Node20 selection satisfies the checked Vite/React plugin minimum of 20.19; this report does not claim a separate Node20 execution.

Reproduce public CI using the workflow's build steps followed by `python -m pytest tests -ra --junitxml=temp/ci/pytest-results.xml` in a clean checkout. Local full-suite runs should isolate the harness scratch/snapshot directories as described in the build-and-test skill. Frontend checks use Vitest and Playwright without updating visual baselines. Raw logs, JUnit and source identities remain private under `temp/work/ci-check-20261021/`; this document retains the compact result and scope.
