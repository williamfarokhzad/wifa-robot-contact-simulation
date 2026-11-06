"""Compare the first impact of a vertical drop against a sampled floor."""
import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Impact:
    time_s: float
    pre_velocity_m_s: float
    clearance_before_clamp_m: float
    rebound_speed_m_s: float
    impulse_n_s: float
    rebound_height_m: float


def compare(clearance_m, velocity_m_s, gravity_m_s2, mass_kg, restitution, step_s):
    """Return two first impact estimates; upward velocity is positive."""
    values = (clearance_m, velocity_m_s, gravity_m_s2, mass_kg, restitution, step_s)
    # Explicit teaching bounds avoid degenerate steps and arithmetic overflow.
    bounds = ((1e-6, 100), (-100, 100), (.1, 100), (1e-6, 1000), (0, 1), (1e-5, 10))
    for name, value, (low, high) in zip(
        ("clearance_m", "velocity_m_s", "gravity_m_s2", "mass_kg", "restitution", "step_s"),
        values, bounds,
    ):
        if type(value) not in (float, int) or not low <= value <= high:
            raise ValueError(f"{name} must be a number between {low} and {high}")

    h, v, g, m, e, dt = values
    impact_speed = math.sqrt(v * v + 2 * g * h)
    # Algebraically equivalent root that avoids cancellation on fast downward releases.
    t_hit = 2 * h / (impact_speed - v) if v < 0 else (v + impact_speed) / g
    ticks = t_hit / dt
    nearest = round(ticks)
    # Treat a root numerically indistinguishable from a positive integer tick as on that tick.
    on_tick = nearest > 0 and abs(ticks - nearest) <= 2 * math.ulp(ticks)
    sample_time = t_hit if on_tick else max(t_hit, math.ceil(ticks) * dt)
    delay = sample_time - t_hit
    # Evaluate relative to the exact crossing to avoid subtracting large similar numbers.
    depth = -delay * (impact_speed + .5 * g * delay)
    if delay == 0:
        depth = 0.0

    def impact(t, before, gap):
        after = e * (-before)
        return Impact(t, before, gap, after, m * (after - before), after ** 2 / (2 * g))

    return impact(t_hit, -impact_speed, 0.0), impact(sample_time, -impact_speed - g * delay, depth)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path, help="JSON scenario from examples/")
    args = parser.parse_args()
    try:
        config = json.loads(args.scenario.read_text(encoding="utf-8"))
        event, sampled = compare(**config)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    report = {"event": asdict(event), "sampled": asdict(sampled), "delay_s": sampled.time_s - event.time_s}
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
