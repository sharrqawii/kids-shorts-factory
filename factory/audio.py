"""Original synthesized melody and Foley; no samples, downloads or voices."""
import json
import wave
from pathlib import Path
import numpy as np

RATE = 48000


def synthesize(duration=20, rate=RATE):
    out = np.zeros((int(duration * rate), 2), dtype=np.float64)
    rng = np.random.default_rng(17)

    def add(signal, at, gain=.1, pan=0):
        start = int(at * rate)
        size = min(len(signal), len(out) - start)
        if size <= 0 or start < 0:
            return
        out[start:start + size, 0] += signal[:size] * gain * (1 - pan * .4)
        out[start:start + size, 1] += signal[:size] * gain * (1 + pan * .4)

    def bell(freq, length=.7):
        t = np.arange(int(length * rate)) / rate
        env = np.minimum(t / .008, 1) * np.exp(-t * 6)
        return env * (np.sin(2*np.pi*freq*t) + .20*np.sin(2*np.pi*freq*2*t)*np.exp(-t*7))

    # A short original C-major pentatonic phrase, varied over four bars.
    phrase = [72, 76, 79, 76, 74, 72, 67, None, 69, 72, 76, 79, 81, 79, 76, 72]
    for i in range(40):
        note = phrase[i % len(phrase)]
        if note is not None:
            add(bell(440 * 2 ** ((note-69)/12)), .12 + i*.48, .105, np.sin(i)*.45)
    for at, notes in [(0,(48,55,60)),(3.84,(53,60,65)),(7.68,(48,55,60)),(11.52,(55,62,67)),(15.36,(48,55,60))]:
        t = np.arange(int(3.8*rate))/rate
        env = np.minimum(t/.15,1) * np.minimum((3.8-t)/.6,1)
        pad = sum(np.sin(2*np.pi*440*2**((n-69)/12)*t) for n in notes) / 3
        add(pad*env, at, .035)
    # Soft, filtered-looking wooden taps for the walk.
    for at in np.arange(.35, 3.65, .45):
        t = np.arange(int(.09*rate))/rate
        add((np.sin(2*np.pi*180*t)+.15*rng.normal(size=len(t)))*np.exp(-t*65),at,.075,-.5)
    for i,n in enumerate([79,84,88,91]):
        add(bell(440*2**((n-69)/12),1),4.1+i*.12,.14,.4)
    # A gentle elastic boop, then matching hop notes.
    t = np.arange(int(.5*rate))/rate
    add(np.sin(2*np.pi*(320*t-190*t*t))*np.exp(-t*9),10.5,.16,.4)
    for at,n in [(13.6,76),(14.7,79),(17.15,84),(17.4,88),(17.65,91)]:
        add(bell(440*2**((n-69)/12),1.4),at,.12)
    fade = np.minimum(np.arange(len(out))/rate/.1,1) * np.minimum((len(out)-1-np.arange(len(out)))/rate/.6,1)
    out *= fade[:,None]
    peak = float(np.max(np.abs(out)))
    if peak > .75:
        out *= .75/peak
    return out.astype(np.float32)


def write_audio(path, duration=20):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = synthesize(duration)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes((data*32767).astype('<i2').tobytes())
    report = {"sample_rate": RATE, "channels": 2, "duration": duration,
              "peak_dbfs": float(20*np.log10(max(float(np.abs(data).max()), 1e-12))),
              "rms_dbfs": float(20*np.log10(max(float(np.sqrt(np.mean(data**2))), 1e-12))),
              "source": "Original deterministic synthesis; assets licensed CC0-1.0"}
    path.with_suffix('.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
