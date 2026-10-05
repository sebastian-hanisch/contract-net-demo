"""Orakel-Test: unabhängige Greedy-Nachrechnung des Contract Net und exakte Teilmengen-DP (Routen per Permutation) gegen
Protokoll und CP-SAT-Referenz. Teilt keinen Code mit cn_protocol/cn_bruteforce."""

import itertools
import math
import random

from cn_ortools_reference import solve_with_ortools
from cn_protocol import run_protocol
from cn_scenario import Instance, Job, generate_instance


def _exact_makespan(inst):
    n, k, tau = inst.n_jobs, inst.n_agents, inst.travel_time_per_unit
    cost = [[0.0] * (1 << n) for _ in range(k)]
    for a in range(k):
        for subset in range(1, 1 << n):
            jobs = [j for j in range(n) if subset >> j & 1]
            best = math.inf
            for perm in itertools.permutations(jobs):
                pos, t = inst.agent_start_positions[a], 0.0
                for j in perm:
                    t += abs(pos - inst.jobs[j].position) * tau + inst.jobs[j].duration
                    pos = inst.jobs[j].position
                best = min(best, t)
            cost[a][subset] = best
    full = (1 << n) - 1
    f = [0.0] + [math.inf] * full
    for a in range(k):
        g = [math.inf] * (full + 1)
        for t in range(full + 1):
            s = t
            while True:
                g[t] = min(g[t], max(f[t ^ s], cost[a][s]))
                if s == 0:
                    break
                s = (s - 1) & t
        f = g
    return f[full]


def _my_cnp(inst):
    pos, free = list(inst.agent_start_positions), [0.0] * inst.n_agents
    sched = {a: [] for a in range(inst.n_agents)}
    for job in inst.jobs:
        fin = [free[a] + abs(pos[a] - job.position) * inst.travel_time_per_unit + job.duration for a in range(inst.n_agents)]
        w = fin.index(min(fin))          # Gleichstand: kleinste Agenten-ID
        free[w], pos[w] = fin[w], job.position
        sched[w].append(job.index)
    return sched, free


def test_protocol_matches_independent_greedy_including_ties():
    rng = random.Random(1)
    for it in range(120):
        n, k = rng.randint(1, 12), rng.randint(1, 4)
        if it % 3 == 0:     # viele exakte Gleichstände
            jobs = tuple(Job(i, float(rng.choice([0, 5, 10, 10, 15])), float(rng.choice([5, 10]))) for i in range(n))
            starts = tuple(float(rng.choice([5, 10, 10, 15])) for _ in range(k))
            inst = Instance(n, k, jobs, starts, rng.choice([0.5, 1.0]))
        else:
            inst = generate_instance(n, k, rng.choice([0.0, 0.5, 1.0]), rng.uniform(0.2, 2.0), rng.randint(0, 999))
        res = run_protocol(inst)
        sched, free = _my_cnp(inst)
        assert {a: list(v) for a, v in res.schedules.items()} == sched
        assert all(abs(x - y) < 1e-9 for x, y in zip(res.agent_finish_times, free))


def test_cpsat_reference_matches_exact_dp_and_never_below():
    """CP-SAT rechnet intern auf aufgerundetem Raster; gemeldet wird der exakt nachgerechnete Zeitplan: nie unter dem
    echten Optimum, höchstens wenige Promille darüber (Rasterwahl)."""
    rng = random.Random(2)
    for _ in range(25):
        n, k = rng.randint(4, 5), rng.randint(2, 3)
        inst = generate_instance(n, k, rng.choice([0.0, 0.5]), rng.choice([0.5, 1.0, 2.0]), rng.randint(0, 999))
        exact = _exact_makespan(inst)
        res = solve_with_ortools(inst, time_limit_seconds=5.0)
        assert res.feasible and res.optimal
        assert res.makespan >= exact - 1e-9
        assert res.makespan <= exact * 1.01
        assert run_protocol(inst).makespan >= exact - 1e-9


def test_decentral_never_shown_better_than_central_optimum():
    """Regression: mit dem aufgerundeten Rasterwert zeigte der Vergleich ein Contract Net, das das zentrale Optimum schlägt
    (Lücke -0,8 %, Seed 9/10 bei n=6, k=2, Variabilität 0). Die Lücke darf höchstens um Rasterrauschen negativ sein."""
    for seed in (9, 10):
        inst = generate_instance(6, 2, 0.0, 1.0, seed)
        res = solve_with_ortools(inst, time_limit_seconds=5.0)
        assert run_protocol(inst).makespan >= res.makespan - 1e-9, seed
        assert res.model_makespan >= res.makespan - 1e-9      # Rasterwert nie unter dem realen Makespan
