# Studio verification — local tests 13 October; GitHub checks 16 October 2026

This report distinguishes genuine Blender and local WanGP videos from mocked integration tests. See `TEST_REPORT.md` at the repository root for the original Phase 1 evidence.

## Verified locally

- All 39 unit/integration tests passed: the original 17 factory tests plus 22 Studio tests.
- WanGP API tests used documented response-shaped mocks for success, progress, errors, missing outputs and cooperative cancellation. No mock is described as a generated AI video.
- Real HTTP tests passed for job creation/history/cancellation, authenticated GPU bridge transport, reference-image processing, cross-origin/Host rejection and range/download responses. The bridge transport test deliberately uses dummy bytes, not GPU inference.
- A real FFmpeg-created test MP4 passed metadata and full decoding checks; invalid bytes were rejected.
- A fresh two-second Blender Cycles CPU economy smoke render completed all 24 animation frames and verified its 1080×1920 MP4. The factory source and original dependency files were preserved.
- All workflow YAML files passed actionlint; the new Studio tests use existing CPU dependencies. GPU dependencies are not installed by CI.
- Browser review covered Kids Factory, Creator Studio, explicit engine selection, a failed unconfigured WanGP job, the video dialog and an actual download. Mobile content width equalled viewport width (375 pixels), with no horizontal overflow.
- The original Pip sample loaded with browser `readyState=4`, no media error, duration 20 seconds and dimensions 1080×1920. Its browser-downloaded copy matched SHA256 `fa11f7fa625d26cbde8e1cab528a9ee4ce55598980c42b86aa6114272de29d50`.

## GPU status

**Genuine local WanGP generation succeeded.** The PC has an NVIDIA RTX 4060 Ti with 8 GB VRAM. An isolated WanGP environment was installed outside the repository. PyTorch `2.10.0+cu130` detected CUDA and that GPU; dependency checks passed. The Studio controller invoked the separate worker against inspected upstream revision `af2ed29a83dbccc7f1c0571a73005648436b392e`, used the real Python API, observed eight inference steps, received an MP4 and verified the entire file with FFmpeg.

- Model: `t2v_1.3B` (Wan 2.1 1.3B), text-to-video; seed 42; eight inference steps; SDPA; memory profile 4.
- Prompt: “An original small glass sculpture on warm sandstone, sunlight, gentle slow camera movement.”
- Requested: two seconds at 480×480, 16 fps. Delivered: 33 frames / 2.0625 seconds, 480×480 H.264. This is WanGP's frame alignment, not an exact two-second cut.
- Full controller job: approximately 354.88 seconds including startup and model downloads. Inference loop: approximately 23.8 seconds. This is one measurement, not a throughput promise.
- Output: `sample/wangp-local-gpu-smoke.mp4`; SHA256 `a6c93c00d41e163ffa9ceb6ef66ed7d702ffd7aae648a542803d61847c6d1573`.
- The viewed middle frame shows a small golden glass sculpture on illuminated sand. This low-step technical smoke test has no generated soundtrack and is not presented as a finished advertisement.
- Model weights and GPU packages were stored outside the repository. No cloud GPU was provisioned or tested.

Other models, image-to-video inference, production-length WanGP videos, free cloud GPU inference and continuous cloud UI hosting are unverified. GPU availability is not proof of successful generation. No paid service, billing, recurring generation or YouTube uploads were activated.

## GitHub status

**Source recovery and real GitHub CPU checks succeeded on 16 October 2026.** The existing browser-owner session transferred the reviewed archives and workflows, and the public CPU recovery job committed the source. All 62 tracked source files matched the local project after recovery. The existing GitHub initialization and recovered Blender history were also merged locally and preserved in the bundled Git history.

- [Recovery run 38865498691](https://github.com/sharrqawii/kids-shorts-factory/actions/runs/38865498691): success, 15 seconds overall.
- [CPU check run 38865655080](https://github.com/sharrqawii/kids-shorts-factory/actions/runs/38865655080): success, job 1 minute 26 seconds, commit `a731a30bd25457f7408309fe4f160de0f4e6907f`.
- Cloud logs confirm 39 tests passed in 4.324 seconds, all 24 Blender smoke frames completed, and full video decoding passed. Portable fallback and simulated native-renderer-failure recovery also passed. These legacy fallback tests do not enable engine switching in Studio.
- Public downloads of both local videos and the source transfer archive were read back without authentication and their SHA256 hashes matched exactly.
- GitHub reported a Node 20 deprecation warning for pinned actions; it ran them on Node 24 successfully. No check failed.

## Complete cloud episode: verified

The manually dispatched [full render run 38865913633](https://github.com/sharrqawii/kids-shorts-factory/actions/runs/38865913633) succeeded on the standard public `ubuntu-24.04` CPU runner. Total workflow duration was 9 minutes 21 seconds; the render job was 9 minutes 16 seconds; generation and verification took 502.242 seconds. This proves the sample can be generated without the PC running.

- Blender 4.2.23 LTS / Cycles CPU, four threads, economy mode explicitly selected; no fallback or GPU used.
- All 240 animation frames rendered at 540×960, 12 distinct poses per second; Lanczos upscaling to 1080×1920 and 24 delivery frames per second. Native-resolution titles; original synthesized music and sound effects.
- MP4: 20 seconds, 1080×1920, H.264/yuv420p, 480 delivery frames, AAC stereo at 48 kHz; 2,271,858 bytes.
- All ten verification checks passed in the cloud. The public MP4 was downloaded without authentication, its SHA256 matched, and an independent local full FFmpeg decode plus all ten factory checks passed again.
- SHA256: `2f05808b80478061f26548acb7c7a228a23a2cb7187427fcc9a6f86bffb2835e`.
- [Download the cloud MP4](https://github.com/sharrqawii/kids-shorts-factory/releases/download/episode-38865913633-1/pip-and-the-giant-strawberry.mp4) · [release and reports](https://github.com/sharrqawii/kids-shorts-factory/releases/tag/episode-38865913633-1) · [sanitized evidence](evidence/github-full-render.json).

Native 1080×1920 Blender rendering has not been benchmarked end to end. The successful economy sample is upscaled. This single run does not demonstrate five new stories per day or continuous service availability. The cloud render did not test WanGP; that verified GPU test remains local only.

## Repository transfer details

The connector remains read-only for this repository and noninteractive Git authentication was unavailable. The browser-based transfer completed the authorized repository work without creating credentials or exposing private configuration.

The manual `restore-source.yml` workflow is a one-time recovery mechanism: it checks a reviewed archive's SHA256, validates every extracted source checksum and refuses to replace an existing factory/Studio source tree. It cannot restore workflow files using its token; those are transferred separately. It has no schedule and uses the standard public Linux CPU runner. Complete local source and the original render remain available in the delivery ZIP regardless of the remote transfer result.
