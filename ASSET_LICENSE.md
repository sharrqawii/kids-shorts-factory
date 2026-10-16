# Original creative assets

The original character design, procedural mesh designs, scene arrangement,
episode story, animation, melody, sound effects, and generated audio/video
created for this repository are dedicated under **CC0 1.0 Universal** to the
extent any copyright or related rights exist. They may be reused, modified,
and included in monetized videos without attribution or royalties.

License: https://creativecommons.org/publicdomain/zero/1.0/
Legal text: https://creativecommons.org/publicdomain/zero/1.0/legalcode.en

No stock music, recorded voices, sampled songs, downloaded character models,
trademarks, or external texture images are included. Audio is generated from
sine oscillators and seeded noise in `factory/audio.py`. The melody and sound
event timing are written specifically for this project. No generative media
API is called.

The source code is MIT-licensed under LICENSE. Third-party software keeps its
own license; this dedication does not relicense Blender, FFmpeg, NumPy, Pillow,
their bundled fonts, or any other dependency. This is not a claim that an
automated platform can never issue an erroneous copyright match.

## Dependencies and typography

- Blender / bpy: GPL-3.0; https://www.blender.org/about/license/ . Blender is
  a rendering tool; the original rendered scene assets are covered above.
- FFmpeg: LGPL/GPL depending on the installed build; the build used here has
  libx264 enabled. No FFmpeg executable is redistributed in this repository.
  https://ffmpeg.org/legal.html
- NumPy: BSD-3-Clause; https://numpy.org/doc/stable/license.html
- Pillow: HPND; https://pillow.readthedocs.io/en/stable/about.html#license
- Pillow's bundled Aileron Regular font is used through `ImageFont.load_default`.
  Its font license is SIL Open Font License 1.1. No separate font download is
  required. https://github.com/python-pillow/Pillow/tree/main/Tests/fonts
- PyYAML (development only): MIT; https://github.com/yaml/pyyaml/blob/main/LICENSE

For future episodes, preserve this provenance record. Adding outside media
requires recording that media's source and license separately.
