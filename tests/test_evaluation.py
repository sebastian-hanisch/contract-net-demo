import cn_constants as C
from cn_evaluation import comparison, stats_up_to_step
from cn_protocol import run_protocol
from cn_scenario import generate_instance


def test_gap_pct_matches_manual_computation():
    instance = generate_instance(n_jobs=6, n_agents=2, duration_variability=0.5, travel_time_per_unit=1.0, seed=1)
    result = run_protocol(instance)
    cmp = comparison(instance, result, time_limit_seconds=5.0)

    assert cmp["ortools_feasible"]
    expected_gap = (cmp["cnp_makespan"] - cmp["ortools_makespan"]) / cmp["ortools_makespan"] * 100.0
    assert abs(cmp["gap_pct"] - expected_gap) < 1e-9


def test_gap_pct_is_never_negative_beyond_floating_point_noise():
    # CNP kann laut test_protocol.py::test_protocol_makespan_never_beats_cp_sat_optimum
    # nie besser als das Optimum sein - die Lücke darf also nicht spürbar negativ werden.
    for seed in range(10):
        instance = generate_instance(
            n_jobs=6, n_agents=2, duration_variability=0.4, travel_time_per_unit=1.0, seed=seed
        )
        result = run_protocol(instance)
        cmp = comparison(instance, result, time_limit_seconds=5.0)
        assert cmp["gap_pct"] >= -1e-6, f"seed={seed}"


def test_stats_up_to_step_tracks_progress():
    instance = generate_instance(n_jobs=6, n_agents=2, duration_variability=0.3, travel_time_per_unit=1.0, seed=1)
    result = run_protocol(instance)

    first = stats_up_to_step(result, 0)
    assert first["jobs_awarded"] == 1

    last = stats_up_to_step(result, len(result.steps) - 1)
    assert last["jobs_awarded"] == instance.n_jobs
    assert last["worst_agent_free_time"] == result.makespan


def test_presets_produce_gap_in_expected_band():
    # Regressions-Wächter für die kalibrierten Preset-Seeds (siehe calibrate_presets.py) -
    # haelt die Presets ehrlich, falls cn_scenario/cn_bidding sich mal aendern.
    expected_bands = {
        "Ausgeglichene Basis": (0.0, 15.0),
        "Ein großer Auftrag früh": (15.0, 35.0),
        "Mehr Agenten, mehr Kontention": (20.0, 45.0),
        "Worst Case: Sequenzielle Falle": (40.0, 75.0),
    }
    for name, params in C.PRESETS.items():
        instance = generate_instance(
            n_jobs=params["n_jobs"], n_agents=params["n_agents"],
            duration_variability=params["duration_variability"],
            travel_time_per_unit=params["travel_time_per_unit"], seed=params["seed"],
        )
        result = run_protocol(instance)
        cmp = comparison(instance, result, time_limit_seconds=8.0)
        assert cmp["ortools_feasible"], name
        lo, hi = expected_bands[name]
        assert lo <= cmp["gap_pct"] <= hi, f"{name}: gap={cmp['gap_pct']:.1f}%"
