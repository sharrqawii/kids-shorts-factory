# kids-shorts-factory — Pip Studio

**New: Pip Studio adds Kids Factory + Creator Studio.** Open the lightweight
browser app with `Start-Studio.cmd` on Windows, or follow
[the Studio guide](docs/STUDIO.md). It adds an optional isolated WanGP engine,
a persistent queue, reference images, history and verified downloads.
Blender and the original Pip assets are preserved. WanGP GPU verification and
cloud status are reported separately in [the Studio test report](docs/STUDIO_TEST_REPORT.md).
No paid service, recurring production or YouTube upload is enabled.

A small, reproducible video generator: **Pip, a baby capybara, discovers a giant
strawberry in a pastel garden**. Everything is built from source: geometry,
animation, music, and sound effects. No paid API, account secret, GPU service,
or YouTube integration is needed by the renderer.

**The complete episode has been rendered and verified both locally and on a
free GitHub CPU runner.** [Download the cloud-rendered MP4](https://github.com/sharrqawii/kids-shorts-factory/releases/download/episode-38865913633-1/pip-and-the-giant-strawberry.mp4).
[The full cloud run](https://github.com/sharrqawii/kids-shorts-factory/actions/runs/38865913633)
succeeded in 9 minutes 21 seconds overall; video generation took 502.2 seconds.
All 240 Blender frames completed and full MP4 decoding passed. In the completed
project ZIP, open `sample/pip-and-the-giant-strawberry.mp4`. The same folder
contains the editable Blender scene, original audio, and measured render report.
The original Phase 1 evidence is preserved in [TEST_REPORT.md](TEST_REPORT.md).
The expanded project is now committed to the existing repository, and
[the free GitHub CPU checks passed](https://github.com/sharrqawii/kids-shorts-factory/actions/runs/38865655080),
including all 39 tests and a real Blender smoke render. Download the complete
project and both verified local videos from [the Studio release](https://github.com/sharrqawii/kids-shorts-factory/releases/tag/studio-phase-2).

The final file is **20 seconds, 1080 × 1920, H.264 MP4, 24 fps, AAC stereo at
48 kHz**. Pip walks in, notices the berry, leans in for a gentle boop, watches
it wobble, hops with delight, and settles beside it under a floating heart.

## Start here — no coding needed

In this **public** GitHub repository:

1. Open **Actions → Render Pip episode → Run workflow**.
2. Select **economy** for the proven Blender CPU mode and press **Run workflow**.
3. Wait for the run to finish. Your PC can be switched off after starting it.
4. Open the repository's **Releases** page. Open the new **Pip episode build**.
5. Download `pip-and-the-giant-strawberry.mp4`. The accompanying JSON report
   tells you exactly which renderer ran and which checks passed.

The first time you copy a workflow into your account, GitHub may require you
to enable Actions. No billing upgrade is required. The workflow skips private
repositories before allocating a runner. Nothing uploads to YouTube.

**Phase 1 is a render proof and software test, not an unattended channel.**
There is no recurring schedule, publishing integration, or paid service.
See [the current verification report](docs/STUDIO_TEST_REPORT.md) for the local
WanGP test and completed cloud render; [TEST_REPORT.md](TEST_REPORT.md) preserves
the original Phase 1 record.

The next-phase [five-per-day architecture](docs/FIVE_PER_DAY.md) includes a
disabled production configuration, five original story concepts, and a tested
daily queue planner. Only the strawberry story currently has a renderer;
the planner reports the other four as blocked instead of calling them finished.

## Quality and time tradeoffs

| Mode | Image production | Use |
| --- | --- | --- |
| `auto` | Benchmarks three Blender frames; selects economy if the measured estimate fits, otherwise the illustrated fallback | Default cloud proof |
| `economy` | True Blender 3D, Cycles CPU, 540 × 960, four samples with denoising; Lanczos enlarged to 1080 × 1920 | Lower CPU cost |
| `blender` | True Blender 3D at native 1080 × 1920, 12 samples with denoising | Higher cost in time; may hit the configured budget |
| `fallback` | Python/Pillow shaded 2.5D illustration at native 1080 × 1920 | Works without Blender; lower visual fidelity |

All modes animate **12 poses per second**, each held for two frames in the
24 fps video. This gives a toy/stop-motion feel and halves 3D frame work. It
does not claim 24 independently rendered poses. Text is drawn at native output
resolution, including in economy mode. The fallback is clearly identified in
the report and release notes; it is never reported as a successful Blender run.

The current Blender configuration explicitly keeps denoising on the CPU,
uses the fast auxiliary-pass prefilter and balanced OpenImageDenoise quality,
limits light bounces, and retains scene data between frames. No particles,
hair, cloth simulation, external textures, or large downloaded models are used.

## Keeping this at $0

- Both workflows require a public repository and `ubuntu-24.04`, a standard
  GitHub-hosted CPU runner. Neither requests a GPU or a larger paid runner.
- The full render has a 75-minute Blender budget and a 100-minute job timeout,
  below GitHub's six-hour job limit. Auto mode falls back on a benchmark
  overrun, timeout, or Blender failure. Explicit Blender modes fail visibly
  instead of quietly changing quality.
- Runs are serialized. There is no cron schedule, dependency cache, Actions
  artifact upload, Git LFS, Codespaces environment, paid API, or hosted server.
- Completed sample builds use GitHub Release attachments, avoiding the shared
  Actions/Packages artifact-storage quota. Each run has a unique tag. Release
  attachments are intended here as sample software build outputs.
- The repository cannot override your account's billing settings. It never
  changes them or enables a paid product. GitHub may change availability,
  apply fair-use limits, or require account verification. This is not a promise
  of unlimited commercial rendering forever.

GitHub documents free standard runners for public repositories and a six-hour
job limit. Its terms restrict Actions to work related to the repository's
software, including development/testing. This Phase 1 workflow validates this
renderer and produces its sample output; an eventual continuous commercial
content factory needs a fresh hosting/terms review.

Sources checked 2026-10-12:

- [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Runner specifications](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [Actions limits](https://docs.github.com/en/actions/reference/limits)
- [Release attachments](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [Actions terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions)

## Reusable character

`assets/pip.json` fixes Pip's proportions, palette, name, and version.
`factory/scene.py:make_pip` creates a named Blender hierarchy with a broad
muzzle, tiny ears, four short feet, a mint scarf, and a yellow flower pin.
There is no prompt-based regeneration, so identity does not drift by episode.

The render exports `pip-strawberry.blend`, including the complete 240-frame
animation. It can be opened in Blender 4.2 for editing. The committed Python
builder is the source of truth; the generated binary is not needed in Git.
Animation timing is deterministic in `factory/story.py`. Audio and scene
variation use a fixed seed. See [docs/CHARACTER.md](docs/CHARACTER.md).

## Run on a computer (optional)

Python **3.11** and FFmpeg/ffprobe must be installed. Blender is supplied as the
official pinned `bpy` Python wheel; a separate Blender GUI installation is not
required. The wheel is large and installs into the virtual environment.

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m factory.render --mode auto
```

Ubuntu 24.04 with Python 3.11:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg libxi6 libxrender1 libxfixes3 libxkbcommon0 libgl1 libegl1 libsm6
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m factory.render --mode auto
```

If Blender cannot install, the fallback needs only `numpy==1.26.4` and
`Pillow==11.3.0` plus FFmpeg. Install those two packages and run
`python -m factory.render --mode fallback`.

The default output directory is `build/episode`. A `--smoke` run intentionally
produces only two seconds and names it `smoke-test.mp4`. Intermediate PNGs and
logs remain in a unique `run-*` directory for diagnosis. They are ignored by
Git and never uploaded by the workflow. Delete old `build` folders when no
longer needed. No cleanup script deletes user files automatically.

## Validation and licenses

The pipeline checks resolution, duration, frame count, codec, pixel format,
audio channels and rate, then fully decodes the MP4 with FFmpeg. Tests also
cover beat continuity, meaningful story actions, audio reproducibility,
clipping, fades, WAV structure, and the fallback across every story beat.

Code: [MIT](LICENSE). Original creative assets, melody, and sound effects:
[CC0](ASSET_LICENSE.md). No stock audio or external character assets are used.

## Project layout

```text
assets/pip.json               Stable character specification
episodes/strawberry.json      Episode delivery settings and story beats
factory/scene.py              Blender character, berry, garden, camera, light
factory/story.py              Animation poses
factory/audio.py              Original music and effects
factory/graphics.py           Native-resolution titles and portable fallback
factory/blender_worker.py     Isolated CPU render process and .blend export
factory/render.py             Benchmark, render, encode, fallback, report
factory/verify.py             ffprobe and full-decode checks
tests/                       Automated source tests
.github/workflows/           Cloud smoke tests and full render proof
```
