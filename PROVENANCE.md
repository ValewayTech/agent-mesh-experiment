# Provenance

This repository is a fresh public export of the author's working repository. The working history was not carried over, so commit hashes cited in earlier drafts no longer exist. The run summaries now cite the pre-registration SHA-256 instead.

## Pre-registration re-hash

Before publication, the `approved_by` fields in `preregistration.yaml` were anonymised to "Sebastian Vale", internal reference IDs were removed, and one `why` line was reworded to "The author approved the next stage". **No hypothesis, design, setting or analysis plan was changed.** Because the file's bytes changed, its SHA-256 changed. The hashes recorded in `results/*/config.json` (`prereg_sha256`) and the pre-registration text embedded there were updated with the same edit. Each historical version was re-hashed after applying the identical edit:

| Version | Used by | Original SHA-256 | Re-hashed SHA-256 |
|---|---|---|---|
| v1 | `results/pilot`, `results/pilot-v1` | 016c03773f65010c0eade74ffe0c5d8aa9f04a985c8582810d8de0329201d3fd | unchanged (no approver field) |
| v2 | `results/pilot-v3`, `results/pilot-v3b`, `results/live-v1` | 9f0264c4c00aeb7fdf58d2c83138ae9b73f2a25ca7fd824242e90367d6071e2a | 7f9b66f47b9346e6f186ef56eba9723e42a420fab2d4d59afc8df3cb5d088a5c |
| v2 + E1 | `results/live-B-unlimited`, `results/live-B-deny` | 2d4c4929ae1f54b73dde6961934d0a2d82f95f9aa1381d0a14958e3193be7815 | 983ecfa7ec836e1d367269cc051f7598d47f6589aca381ce0173ff25f28849ec |
| v2 + E1 + E2 (current) | `results/e2-main` | dc233ca6c4b237d740f9183750eba349721e62d22defe4e41af05afcbce9b82e | 564f390ec47aef881023034ccece40822493239f5e7ebf00b3a4d9f72aec12bd |

The current `preregistration.yaml` in this repository hashes to `564f390ec47aef881023034ccece40822493239f5e7ebf00b3a4d9f72aec12bd`.
