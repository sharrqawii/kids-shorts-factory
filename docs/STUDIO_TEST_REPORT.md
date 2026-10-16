# Studio verification — 13 October 2026

This report distinguishes the proven Blender video from mocked WanGP integration tests. See `TEST_REPORT.md` at the repository root for the original Phase 1 evidence.

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

The GitHub connector is authenticated to a different account and has no push permission on `sharrqawii/kids-shorts-factory`. A noninteractive Git push dry-run also failed due to missing authentication. The existing browser session does have repository-owner access. Source transfer through that session and a real Actions run are being verified separately; local tests above do not establish a cloud pass.

The manual `restore-source.yml` workflow is a one-time recovery mechanism: it checks a reviewed archive's SHA256, validates every extracted source checksum and refuses to replace an existing factory/Studio source tree. It cannot restore workflow files using its token; those are transferred separately. It has no schedule and uses the standard public Linux CPU runner. Complete local source and the original render remain available in the delivery ZIP regardless of the remote transfer result.
