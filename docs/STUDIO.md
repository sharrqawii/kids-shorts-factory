# Pip Studio: Kids Factory + Creator Studio

The original Blender project and verified Pip episode are preserved. The new `studio/` package is an optional browser interface and durable queue. It does not import PyTorch or Blender. WanGP is explicitly credited in the UI and integrated through its documented Python API in a separate process.

## Start the browser app

Python 3.11 and FFmpeg/ffprobe are required. From the project folder:

```powershell
py -3.11 -m venv .studio-venv
.studio-venv\Scripts\python -m pip install -r requirements-studio.txt
.studio-venv\Scripts\python -m studio.server
```

Open http://127.0.0.1:8765. On Linux use `python3 -m venv .studio-venv` and `.studio-venv/bin/python` instead. No Node build, accounts, external fonts or paid APIs are needed. `Start-Studio.cmd` provides the Windows launcher, creating only the lightweight environment.

The complete delivery ZIP includes the original MP4 under `sample/`. The launcher detects it. Otherwise set `PIP_SAMPLE` to the absolute location of the verified MP4. Set `BLENDER_PYTHON` to the Python executable in the existing CPU environment containing `requirements.txt`. Its environment must stay separate from WanGP.

## Two workspaces

- **Kids Factory:** the existing Pip identity, scene and strawberry episode. Explicitly select Blender economy (540×960 enlarged to 1080×1920) or native 1080×1920. Duration, character and soundtrack are fixed by this proven template. Free-form prompts do not rewrite Blender geometry or stories. WanGP is also available for experimental children's scenes; a reference image guides appearance but does not guarantee Pip consistency.
- **Creator Studio:** WanGP text-to-video and image-to-video for cinematic scenes, product stories and social content. Choose model, supported resolution, duration, seed, inference steps, prompt and reference image. Advertising is a creative use case of these controls, not a separate trained model. LTX/Wan settings and duration alignment differ, and the verified output reports the actual duration and dimensions.

There is no automatic switch from WanGP to Blender. The original standalone factory CLI retains its legacy `auto` mode and its existing CI tests; Studio always calls Blender with an explicit mode. No publishing or recurring-production routes are implemented. The existing disabled five-story planner remains available.

## Connect an isolated WanGP installation

Inspected upstream revision: `af2ed29a83dbccc7f1c0571a73005648436b392e` (13 October 2026). Use this revision for the integration contract; future upstream changes may require retesting.

Follow [WanGP's installation guide](https://github.com/deepbeepmeep/WanGP/blob/af2ed29a83dbccc7f1c0571a73005648436b392e/docs/INSTALLATION.md) in a directory **outside this project**, with a dedicated GPU virtual environment. Do not install its requirements into the Blender or Studio environments. Installation and model downloads can consume many GB; nothing is downloaded by the browser app at startup.

Set these environment variables before launching Studio (replace paths with your installation):

```powershell
$env:WANGP_ROOT='D:\AI\WanGP'
$env:WANGP_PYTHON='D:\AI\wangp-venv\Scripts\python.exe'
$env:BLENDER_PYTHON='D:\AI\blender-venv\Scripts\python.exe'
$env:PIP_SAMPLE='D:\videos\pip-and-the-giant-strawberry.mp4'
.studio-venv\Scripts\python -m studio.server
```

Download the selected model through WanGP's official interface first, or deliberately set `WANGP_ALLOW_MODEL_DOWNLOADS=yes` for the worker. By default the worker sets Hugging Face/Transformers offline mode; missing weights fail rather than claiming a successful generation. Upstream may use non-Hugging-Face download paths, so this is not a network sandbox. Do not configure paid prompt enhancers or third-party API credentials in WanGP. The presets here explicitly disable prompt enhancement.

The integration uses `shared.api.init(root=..., output_dir=..., cli_args=['--attention','sdpa','--profile','4'])`, obtains model defaults, calls `submit_task`, receives `on_progress` callbacks, calls `cancel()` for cooperative cancellation and checks `result.success` plus MP4 paths. A seconds string for `video_length` lets WanGP normalize its own frame constraints. Source: [documented Python API](https://github.com/deepbeepmeep/WanGP/blob/af2ed29a83dbccc7f1c0571a73005648436b392e/docs/API.md).

One separate process is used per job. This improves isolation and recovery at the cost of reloading models between jobs. Initial presets: Wan 2.1 1.3B text, Wan 2.1 14B image, and LTX-2 distilled 22B text/image. Listing a model does not mean it fits this GPU or has been tested. No silent upscaling to 1080p is applied to WanGP outputs.

## Existing free cloud GPU adapter

`studio/providers.py` implements an HTTP adapter to **this project's GPU bridge**, not an invented WanGP REST API. The bridge invokes WanGP's documented in-process API. It only connects to an existing resource; it cannot create a VM, reserve a GPU, buy credits, enable billing or provision infrastructure.

On a legitimately provided, zero-cost GPU host that permits a persistent service, install this project's lightweight Studio requirements separately and point `WANGP_ROOT`/`WANGP_PYTHON` to that host's GPU installation. Set a strong random `STUDIO_BRIDGE_TOKEN` (at least 32 characters) in its environment and run:

```bash
python -m studio.server --gpu-bridge --host 127.0.0.1 --port 8766
```

Use an existing HTTPS reverse proxy for a remote connection. Do not expose the unauthenticated local browser server. Non-loopback binding is allowed only for the authenticated GPU bridge. TLS termination, access control, storage and service supervision are the host operator's responsibility. This is a single-user tool, not a multi-tenant public hosting product.

On the browser controller set `FREE_GPU_URL`, `FREE_GPU_TOKEN`, and `FREE_GPU_CONFIRMED_ZERO_COST=yes`. The last setting is an operator attestation, **not proof of the host's billing terms**. Do not set it for a metered account or paid endpoint. The adapter checks the bridge contract, transfers a normalized reference image, submits a job, polls real status, propagates cancellation and downloads the output. Both sides decode-check the MP4. Redirects are rejected so tokens cannot be forwarded to another host.

No cloud GPU or free entitlement is included or currently verified. See [free GPU research](FREE_GPU.md). Do not use this bridge to bypass a notebook provider's restrictions. Cloud CPU GitHub Actions continue to generate Blender episodes without the PC; the interactive browser app currently runs where you start its server.

## Queue, privacy and recovery

SQLite history, normalized images, outputs and private logs live under ignored `studio-data/` (or `STUDIO_DATA` / `--data`). One worker processes FIFO jobs. Queue limit: 10 pending/running; UI displays the most recent 100. On restart, running jobs become `interrupted` and require manual resubmission; queued jobs remain queued. Do not run multiple controllers against the same data directory.

Jobs time out after one hour. Cancellation first requests WanGP cancellation, then terminates the owned process tree after five seconds. Blender progress is indeterminate; WanGP reports actual phase progress. Output is offered only after ffprobe and a complete FFmpeg decode pass. A valid MP4 does not mean its content meets creative or child-safety requirements: review before sharing.

Uploads accept PNG/JPEG up to 8 MB / 16 megapixels, normalize to at most 2048 pixels and discard metadata. Prompts render as text. Paths are generated server-side; references are random IDs. Local requests enforce loopback Host and same-origin checks. Tokens and raw GPU error logs never appear in browser API responses. Do not place credentials in prompts. Private logs may contain upstream paths or diagnostics; they are excluded from Git. Downloads may contain original prompts in upstream metadata; inspect before sharing.

## Licensing

Our integration code is MIT. Existing procedural Pip models, audio and scenery retain [their original asset terms](../ASSET_LICENSE.md). The optional WanGP runtime is not bundled or relicensed. Its [Community License 2.0](https://github.com/deepbeepmeep/WanGP/blob/af2ed29a83dbccc7f1c0571a73005648436b392e/LICENSE.txt) permits internal creation and requires visible integration credit. Direct sales of outputs have attribution requirements; selling hosted access to WanGP has additional restrictions. Review the full terms and each model's separate license before commercial use. The project does not grant a blanket commercial license to model weights or reference images.

## Verification

Run `python -m unittest discover -s tests -v` in the original development environment. This exercises the existing factory plus the Studio contracts using mocked WanGP response objects, real HTTP requests, a simulated remote GPU transport, persistence, failure/cancellation and an actual FFmpeg-generated decode fixture. Mock output is explicitly not a GPU generation. Consult [STUDIO_TEST_REPORT.md](STUDIO_TEST_REPORT.md) for the real machine and browser results.
