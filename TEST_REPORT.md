# Phase 1 verification report

Recovery and final verification: **2026-10-13**, Asia/Amman.

## Completed deliverable

**The complete Blender video rendered successfully.** All 240 source frames
finished. FFmpeg encoded and fully decoded the final MP4 without an error.
The completed video was verified again during recovery on 2026-10-13.

| Property | Observed result |
| --- | --- |
| File | `pip-and-the-giant-strawberry.mp4` |
| Duration | 20.000 seconds |
| Delivery resolution | 1080 × 1920 |
| Video | H.264, yuv420p, 24 fps, 480 encoded frames |
| Animation | 240 distinct Blender poses at 12 poses/second |
| Audio | AAC stereo, 48 kHz, 20 seconds |
| File size | 2,128,577 bytes |
| Full pipeline wall time | 1,172.891 seconds, approximately 19.5 minutes |
| Renderer | Blender 4.2.23 LTS, Cycles CPU, 8 local render threads |
| Source image resolution | 540 × 960, four samples with denoising |
| Enlargement | Lanczos to 1080 × 1920; titles drawn at native output size |
| SHA-256 | `fa11f7fa625d26cbde8e1cab528a9ee4ce55598980c42b86aa6114272de29d50` |

This is a genuine 3D Blender animation, with an explicitly disclosed
resolution tradeoff. It is not a native-1080p 3D render and does not have 24
independently animated poses per second.

The complete sample uses the original accurate/high CPU denoising settings
from the initial implementation (`90f23e7`). The current code then changed
only denoiser settings to fast/balanced, explicitly disabled GPU denoising,
and added denoiser metrics. That revised configuration passed its own actual
two-second Blender integration render on four CPU threads. A second complete
20-second render with the revised denoiser has not been run.

## Tests and visual review

- **17 unit tests passed**, covering episode continuity, pose behavior,
  reproducible unclipped audio, fades, WAV headers, fallback frames, cloud
  workflow safeguards, distinct batch job IDs, duplicate-story rejection,
  and disabled production/upload settings.
- **Actionlint 1.7.12 passed** for both GitHub workflows. Local ShellCheck and
  Pyflakes subprocess checks were disabled because those tools were not
  installed; Actionlint's workflow/expression validation was run.
- Python syntax compilation passed.
- The optimized Blender smoke clip passed all MP4 checks. Its full pipeline
  took 128.234 seconds locally with four CPU render threads.
- The complete fallback clip passed all MP4 checks in 76.031 seconds. This
  fallback is a shaded Python/Pillow illustration, not full 3D geometry.
- A simulated Blender subprocess failure produced a correctly labeled and
  verified fallback MP4. This was an intentional failure-path test, not an
  assertion that Blender failed on the actual full sample.
- The exported `.blend` reopened in Blender 4.2.23 with 224 objects, 240 frames,
  12 fps, the correct character ID, CPU rendering, and 240 keys per root channel.
- Frames extracted from the actual completed MP4 at 1, 6, 10.5, 14, and 18.5
  seconds were visually reviewed. They show the entrance, discovery, nose
  contact, happy hop, and final heart. Pip starts partly off-screen while
  walking into the shot, intentionally.
- Original audio was generated from oscillators and seeded noise. Its decoded
  integrated loudness measured -25.6 LUFS and true peak approximately -9.7 dBFS.
  Audio structure and decoding were checked; no human listening review is
  claimed.

Machine-readable measurements are preserved in `docs/evidence/`.

## Native-resolution benchmark and free-runner limitations

One native 1080 × 1920 frame at 12 samples and four CPU threads completed in
116.485 seconds, while another local render was running. Multiplying that
single frame by 240 gives about 7.8 hours. This is a rough local estimate with
CPU contention, **not a measured GitHub runtime or proof that every free runner
would exceed its limit**. The full native-resolution episode was not run.

The cloud default benchmarks the lower-cost Blender mode, applies a safety
margin, and uses the illustrated fallback if its configured CPU budget would
be exceeded or Blender fails. Standard public-repository runners are used;
private-repository jobs are skipped before runner allocation. No paid service,
GPU rental, billing upgrade, Actions artifact storage, or YouTube integration
was activated.

## GitHub status — not completed

The requested repository, `sharrqawi/kids-shorts-factory`, returned HTTP 404 to
the connected GitHub account during recovery. A direct Git remote lookup also
could not access it without authentication. No local Git credentials were
available.

The browser showed a different public repository,
`sharrqawii/kids-shorts-factory` (two trailing i's). The connected GitHub account
reported no push permission there. The latest user instruction explicitly
targeted `sharrqawi`, prohibited creating another repository, and permitted a
ZIP if a push was unavailable. Therefore the verified project and sample were
packaged locally; no files were pushed to a different account.

**Not tested:** GitHub-hosted Linux execution, workflow dispatch, release-upload
permissions, cloud download links, GitHub-account quota state, a five-episode
cloud batch, recurring production, and YouTube publishing. No successful cloud
run or online artifact link is claimed. The finished local MP4 and ZIP are the
available downloads.

## Preserved project and next phase

The existing project was recovered, not restarted. The local Git history
preserves the implementation and all tracked source files. Final reports were
added without replacing the renderer. Public-facing commit metadata uses a
GitHub no-reply address; the ZIP excludes `.git`, credentials, caches, and
temporary render files. A separate Git bundle preserves the reachable commits.

The five-per-day architecture is implemented as a disabled configuration and
tested daily planner. It contains five original story concepts; only the
strawberry renderer is implemented. The planner clearly blocks the other four
until their renderers exist and prevents completed stories being reused to
fill a daily quota. See `docs/FIVE_PER_DAY.md`.
