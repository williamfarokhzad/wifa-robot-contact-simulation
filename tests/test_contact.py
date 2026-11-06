import json
import math
from pathlib import Path
import subprocess
import sys
import unittest
from decimal import Decimal, localcontext

from contact import compare


class ContactTests(unittest.TestCase):
    def test_exact_time_from_conservation_of_energy(self):
        event, _ = compare(.18, 0, 10, .5, .5, .05)
        self.assertAlmostEqual(event.time_s, math.sqrt(.036))
        self.assertAlmostEqual(.5 * .5 * event.pre_velocity_m_s ** 2, .5 * 10 * .18)
        self.assertAlmostEqual(event.rebound_height_m, .045)

    def test_first_sample_is_one_tick_after_last_clear_tick(self):
        event, sampled = compare(.18, 0, 10, .5, .5, .05)
        self.assertGreater(.18 - 5 * .15 ** 2, 0)
        self.assertAlmostEqual(sampled.time_s, .20)
        self.assertAlmostEqual(sampled.clearance_before_clamp_m, -.02)
        self.assertAlmostEqual(sampled.impulse_n_s, 1.5)
        self.assertGreater(sampled.rebound_height_m, event.rebound_height_m)

    def test_nonzero_launch_crosses_after_apex_and_loses_no_energy(self):
        event, sampled = compare(.15, 1, 10, .5, 1, .1)
        self.assertAlmostEqual(event.time_s, .30)
        self.assertAlmostEqual(event.rebound_height_m, .2)
        self.assertAlmostEqual(sampled.time_s, event.time_s)
        self.assertAlmostEqual(sampled.clearance_before_clamp_m, 0)

    def test_inelastic_exact_tick(self):
        event, sampled = compare(.2, 0, 10, .5, 0, .05)
        self.assertEqual(event, sampled)
        self.assertEqual(event.rebound_speed_m_s, 0)
        self.assertEqual(event.rebound_height_m, 0)
        self.assertAlmostEqual(event.impulse_n_s, 1)

    def test_fast_descending_root_matches_high_precision_position_zero(self):
        with localcontext() as ctx:
            ctx.prec = 48
            h, v, g = map(Decimal, ('0.000001', '-100', '0.1'))
            t_ref = (v + (v * v + 2 * g * h).sqrt()) / g
        event, sampled = compare(float(h), float(v), float(g), 1, .4, 1e-5)
        self.assertTrue(math.isclose(event.time_s, float(t_ref), rel_tol=1e-14))
        self.assertGreater(sampled.time_s, event.time_s)

    def test_finer_aligned_grid_cannot_cross_later(self):
        for v in (-2, 0, 3):
            _, coarse = compare(.18, v, 10, .5, .5, .05)
            event, fine = compare(.18, v, 10, .5, .5, .002)
            self.assertLessEqual(fine.time_s, coarse.time_s)
            self.assertLess(fine.time_s - event.time_s, .002)
            self.assertLessEqual(abs(fine.clearance_before_clamp_m), abs(coarse.clearance_before_clamp_m))

    def test_reject_bad_numbers_and_units(self):
        valid = [.18, 0, 10, .5, .5, .05]
        for i, value in ((0, 0), (1, float('nan')), (2, -10), (3, True), (4, 1.1), (5, 0)):
            with self.subTest(i=i, value=value), self.assertRaises(ValueError):
                invalid = valid.copy()
                invalid[i] = value
                compare(*invalid)

    def test_cli_outputs_json_and_handles_missing_file(self):
        root = Path(__file__).resolve().parents[1]
        def run(path):
            return subprocess.run([sys.executable, 'contact.py', path], cwd=root, capture_output=True, text=True)
        example = run('examples/coarse.json')
        self.assertEqual(example.returncode, 0, example.stderr)
        self.assertAlmostEqual(json.loads(example.stdout)['delay_s'], .2 - math.sqrt(.036))
        missing = run('examples/not-present.json')
        self.assertEqual(missing.returncode, 2)
        self.assertIn('error:', missing.stderr)
        self.assertNotIn('Traceback', missing.stderr)


if __name__ == '__main__':
    unittest.main()
