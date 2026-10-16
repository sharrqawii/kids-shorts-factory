# Free GPU investigation — 13 October 2026

**No cloud GPU endpoint or account entitlement was obtained or verified. Nothing paid was activated.** A local NVIDIA RTX 4060 Ti with 8 GB VRAM is present; this is a local resource, not a cloud solution.

| Option | Legitimate free use | Suitability for this studio |
| --- | --- | --- |
| Hugging Face ZeroGPU | The current official documentation permits free use of existing Spaces. Eligible personal accounts with verified email and age over 30 days can host up to two ZeroGPU Spaces; free users have five GPU minutes per day. | Gradio-only allocation model with constrained execution. WanGP would need a tested ZeroGPU-specific integration; this ordinary persistent-process bridge is **not** a validated ZeroGPU deployment. Account eligibility, quota and compatibility are unknown. |
| Google Colab free | Interactive notebook experimentation with GPU access subject to availability and changing limits. | Free managed runtimes prohibit primarily interacting via an external web UI, remote-control shells and distributed workers. Therefore no Colab web bridge or unattended factory is implemented. A manually operated notebook experiment is distinct and remains untested. |
| GitHub Actions standard public Linux runners | Existing public-repository CPU workflows. | No CUDA GPU on the standard CPU runner. Keep using Blender; do not install WanGP weights there or select paid/larger runners. |
| Existing donated / institution-provided GPU | Potentially free if the user actually has access and hosting is permitted. | Supported by the authenticated existing-endpoint adapter. None connected. The operator must independently confirm zero cost. |

Sources: [Hugging Face ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu), [Colab FAQ](https://research.google.com/colaboratory/faq.html), [GitHub hosted runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners).

Five original GPU-generated Shorts per day on free cloud resources is **not proven**. Availability, generation time, model download storage and quotas are unresolved. No account cycling, credit purchases, paid trials or restriction bypasses are used. The existing disabled production planner is retained; generation scheduling and YouTube uploads remain off.
