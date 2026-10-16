"""Deterministic poses shared by Blender and the lightweight fallback."""
import math


def ease(t, start, end):
    x = min(1.0, max(0.0, (t - start) / (end - start)))
    return x * x * (3 - 2 * x)


def pose(t):
    walk = 1 - ease(t, 3.2, 4.0)
    approach = ease(t, 8.0, 10.5)
    hop = sum(0.28 * max(0, math.sin((t - start) * math.pi / .65))
              if start <= t <= start + .65 else 0 for start in (13.6, 14.7))
    blink = min(abs(t - b) / .12 for b in (2.2, 5.1, 7.3, 11.6, 16.2, 18.5))
    return {
        "x": -2.1 + 1.03 * ease(t, 0, 3.7) + .44 * approach,
        "y": -.45 + .67 * approach,
        "z": abs(math.sin(t * 7)) * .055 * walk + hop,
        "walk": math.sin(t * 7) * .20 * walk,
        "turn": .08 + .30 * ease(t, 4, 5) + .67 * approach - .79 * ease(t, 12, 13.4),
        "head_tilt": .16 * math.sin((t - 4) * 1.7) if 4 < t < 8 else -.08 * approach,
        "lean": -.12 * ease(t, 9, 10.5) + .12 * ease(t, 11, 12),
        "eye": max(.08, min(1, blink)),
        "berry_wobble": .11 * math.sin((t - 10.5) * 10) * math.exp(-(t - 10.5) * 1.5) if t >= 10.5 else 0,
        "heart": ease(t, 17, 17.6) * (1 - ease(t, 19.5, 20)),
        "heart_z": 2.4 + .38 * ease(t, 17, 20),
    }


def validate_episode(config):
    if (config["width"], config["height"], config["duration"]) != (1080, 1920, 20):
        raise ValueError("Phase 1 requires 1080x1920 and exactly 20 seconds")
    if config["animation_fps"] != 12 or config["delivery_fps"] != 24:
        raise ValueError("Phase 1 uses 12 animated poses/sec delivered at 24 fps")
    beats = config["beats"]
    if beats[0]["start"] != 0 or beats[-1]["end"] != config["duration"]:
        raise ValueError("Story beats must cover the entire episode")
    for i, beat in enumerate(beats):
        if beat["end"] <= beat["start"] or (i and beats[i-1]["end"] != beat["start"]):
            raise ValueError("Story beats must be ordered, without gaps or overlaps")
