"""Defaults, Slider-Grenzen und Presets für die Contract-Net-Demo."""

DEFAULT_N_JOBS = 8
DEFAULT_N_AGENTS = 2
DEFAULT_DURATION_VARIABILITY = 0.3
DEFAULT_TRAVEL_TIME_PER_UNIT = 1.0
DEFAULT_SEED = 7

N_JOBS_MIN, N_JOBS_MAX = 4, 16
N_AGENTS_MIN, N_AGENTS_MAX = 2, 4
DURATION_VARIABILITY_MIN, DURATION_VARIABILITY_MAX = 0.0, 1.0
TRAVEL_TIME_PER_UNIT_MIN, TRAVEL_TIME_PER_UNIT_MAX = 0.2, 2.0

POSITION_RANGE_MAX = 20.0
DURATION_BASE_RANGE = (5, 15)
# Ein "Spitzen-Auftrag" macht die Auswirkung fehlender Rücksichtnahme sichtbar: mit
# Wahrscheinlichkeit duration_variability * SPIKE_PROBABILITY_SCALE wird ein Auftrag um
# SPIKE_MULTIPLIER verlängert. Beide Werte empirisch kalibriert (siehe calibrate_presets.py),
# nicht auf den ersten Versuch übernommen.
SPIKE_PROBABILITY_SCALE = 0.4
SPIKE_MULTIPLIER = 4.0

# OR-Tools-Referenzlauf: harte Zeitgrenze, damit ein Preset niemals hängt.
ORTOOLS_TIME_LIMIT_SECONDS = 10.0

# Ab welcher Lückengröße die Kernaussage-Sektion als "deutlich" statt "noch klein" gilt.
GAP_HIGHLIGHT_THRESHOLD_PCT = 10.0

# Seeds empirisch kalibriert via calibrate_presets.py (2026-09-07) - nicht der erste
# Versuch übernommen. Realer Fund dabei: selbst bei duration_variability=0 schwankt die
# Lücke zu CP-SAT stark (-0,8% bis 74,7% über 20 Seeds) - die Positions-/Reihenfolge-
# Struktur allein treibt die Lücke schon, nicht nur Auftragsdauer-Spitzen.
PRESETS = {
    "Ausgeglichene Basis": {
        "n_jobs": 6, "n_agents": 2, "duration_variability": 0.0,
        "travel_time_per_unit": 1.0, "seed": 2,
    },
    "Ein großer Auftrag früh": {
        "n_jobs": 6, "n_agents": 2, "duration_variability": 0.5,
        "travel_time_per_unit": 1.0, "seed": 10,
    },
    "Mehr Agenten, mehr Kontention": {
        "n_jobs": 10, "n_agents": 3, "duration_variability": 0.5,
        "travel_time_per_unit": 1.5, "seed": 0,
    },
    "Worst Case: Sequenzielle Falle": {
        "n_jobs": 12, "n_agents": 2, "duration_variability": 0.8,
        "travel_time_per_unit": 2.0, "seed": 2,
    },
}
