import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
import wave
import numpy as np
from factory.audio import synthesize,write_audio
from factory.graphics import fallback_frame
from factory.story import pose,validate_episode

ROOT=Path(__file__).resolve().parents[1]


class StoryTests(unittest.TestCase):
    def test_episode_covers_twenty_seconds(self):
        config=json.loads((ROOT/'episodes/strawberry.json').read_text())
        validate_episode(config)
        self.assertEqual(config['duration']*config['animation_fps'],240)

    def test_rejects_story_gap_and_wrong_output(self):
        config=json.loads((ROOT/'episodes/strawberry.json').read_text())
        broken=copy.deepcopy(config);broken['beats'][1]['start']=4.5
        with self.assertRaises(ValueError):validate_episode(broken)
        broken=copy.deepcopy(config);broken['height']=1080
        with self.assertRaises(ValueError):validate_episode(broken)

    def test_story_has_motion_and_contact_reaction(self):
        self.assertLess(pose(0)['x'],pose(4)['x'])
        self.assertLess(pose(8)['x'],pose(11)['x'])
        self.assertEqual(pose(10)['berry_wobble'],0)
        self.assertGreater(abs(pose(10.7)['berry_wobble']),.01)
        self.assertGreater(pose(13.9)['z'],.2)
        self.assertGreater(pose(18)['heart'],.99)

    def test_all_poses_are_finite_and_safe(self):
        for frame in range(240):
            state=pose(frame/12)
            self.assertTrue(all(math.isfinite(x) for x in state.values()))
            self.assertTrue(.08<=state['eye']<=1)
            self.assertGreaterEqual(state['z'],0)

    def test_identity_is_versioned(self):
        spec=json.loads((ROOT/'assets/pip.json').read_text())
        self.assertEqual(spec['id'],'pip-capybara-v1')
        self.assertEqual(spec['palette']['scarf'],'48BFA7')


class AudioTests(unittest.TestCase):
    def test_original_audio_length_peak_and_fades(self):
        audio=synthesize()
        self.assertEqual(audio.shape,(960000,2))
        self.assertTrue(np.isfinite(audio).all())
        self.assertGreater(float(np.sqrt(np.mean(audio**2))),.015)
        self.assertLessEqual(float(np.abs(audio).max()),.751)
        self.assertEqual(float(np.abs(audio[[0,-1]]).max()),0)
        self.assertFalse(np.array_equal(audio[:,0],audio[:,1]))

    def test_audio_is_deterministic(self):
        np.testing.assert_array_equal(synthesize(2),synthesize(2))

    def test_wave_header(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'audio.wav';write_audio(path,2)
            with wave.open(str(path)) as wav:
                self.assertEqual((wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes()),(2,2,48000,96000))


class FallbackTests(unittest.TestCase):
    def test_render_all_story_beats(self):
        frames=[fallback_frame(t,270,480) for t in [0,4,8,11,14,18,19.9]]
        self.assertTrue(all(image.size==(270,480) for image in frames))
        self.assertTrue(all(image.mode=='RGB' for image in frames))
        self.assertEqual(len(set(image.tobytes() for image in frames)),len(frames))


if __name__=='__main__':unittest.main()
