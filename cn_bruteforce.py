"""Erschöpfender Referenzlöser - probiert jede Zuordnung von Aufträgen zu Agenten
UND jede Reihenfolge innerhalb eines Agenten durch. Nur für sehr kleine n_jobs
praktikabel (Testzwecke: Cross-Check gegen cn_ortools_reference, nicht live in
der App gezeigt)."""

from itertools import permutations, product


def _schedule_makespan(instance, assignment_by_agent):
    """assignment_by_agent: dict agent_id -> Tupel von job_index in Bearbeitungsreihenfolge."""
    finish_times = []
    for agent_id, job_order in assignment_by_agent.items():
        position = instance.agent_start_positions[agent_id]
        free_time = 0.0
        for job_index in job_order:
            job = instance.jobs[job_index]
            free_time += instance.travel_time(position, job.position) + job.duration
            position = job.position
        finish_times.append(free_time)
    return max(finish_times) if finish_times else 0.0


def solve_bruteforce(instance):
    n, k = instance.n_jobs, instance.n_agents
    best_makespan = float("inf")
    best_assignment = None

    for agent_choice in product(range(k), repeat=n):
        by_agent = {a: [] for a in range(k)}
        for job_index, agent_id in enumerate(agent_choice):
            by_agent[agent_id].append(job_index)

        # Für jeden Agenten jede Reihenfolge seiner eigenen Aufträge durchprobieren.
        agent_orderings = [
            list(permutations(jobs)) if jobs else [()] for jobs in by_agent.values()
        ]
        for combo in product(*agent_orderings):
            assignment_by_agent = {a: combo[a] for a in range(k)}
            makespan = _schedule_makespan(instance, assignment_by_agent)
            if makespan < best_makespan:
                best_makespan = makespan
                best_assignment = assignment_by_agent

    return best_makespan, best_assignment
