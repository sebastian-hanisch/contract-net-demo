"""
Contract Net Protocol an der Kran-Auftragsvergabe – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Erstes Stück der "Konzepte"-Reihe, Multi-Agenten-Koordinations-Linie - der Root
dieser neuen Linie: das Contract Net Protocol (Smith, 1980) zeigt dezentrale
Aufgabenvergabe (ankündigen -> bieten -> zuschlagen) an einer bewusst vereinfachten
Kran-zu-Container-Auftrag-Zuweisung (KEINE gemeinsame Schiene, keine Non-Crossing-
Regel wie im Schwester-Fall-Demo quaycrane-demo - dort geht es um die physische
Kran-Choreographie, hier um den Koordinations-MECHANISMUS).

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import cn_constants as C
from cn_evaluation import comparison, stats_up_to_step
from cn_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from cn_protocol import run_protocol
from cn_scenario import generate_instance
from cn_visualization import build_bid_chart, build_schedule_figure

st.set_page_config(page_title="Contract Net Protocol – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _compute_protocol(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed):
    instance = generate_instance(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed)
    result = run_protocol(instance)
    return instance, result


@st.cache_data(show_spinner=False)
def _compute_comparison(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed):
    instance = generate_instance(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed)
    result = run_protocol(instance)
    return comparison(instance, result, time_limit_seconds=C.ORTOOLS_TIME_LIMIT_SECONDS)


st.title("📡 Contract Net Protocol an der Kran-Auftragsvergabe")
st.markdown(
    """
Der Auftakt einer neuen Konzepte-Linie: **Multi-Agenten-Koordination** - dezentrale
Entscheidungsfindung statt eines zentralen Solvers. Beim **Contract Net Protocol**
(Smith, 1980) kündigt ein Manager Aufträge einzeln an; jeder Agent (hier: ein Kran)
bietet seine eigene, rein lokale Fertigstellungszeit; der Zuschlag geht an das
niedrigste Gebot. Schnell und robust - aber wie der aufgeklappte Abschnitt direkt
darunter zeigt, hat das einen strukturellen Preis.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren "
    "vergleichen, zeigt diese Demo - wie die übrigen Stücke der Konzepte-Reihe - EIN Verfahren "
    "an einem wachsenden Beispiel. Das Vehikel ist eine bewusst vereinfachte Kran-zu-Container-"
    "Auftrag-Zuweisung, inspiriert vom Schwester-Fall-Demo quaycrane-demo, aber OHNE dessen "
    "gemeinsame Schiene/Non-Crossing-Regel - hier geht es um den Koordinations-Mechanismus, "
    "nicht um die physische Kran-Choreographie."
)

with st.expander("So funktioniert das Contract Net Protocol", expanded=True):
    st.markdown(
        r"""
Jeder Auftrag wird **einzeln und in Ankunftsreihenfolge** angekündigt - der Manager
kennt zukünftige Aufträge nicht im Voraus:

- **Ankündigen**: der nächste Auftrag (Position + Bearbeitungsdauer) wird bekanntgegeben.
- **Bieten**: jeder Agent berechnet rein lokal, wann er fertig wäre, wenn er diesen
  Auftrag ans Ende seiner eigenen Warteschlange hängt - `Gebot = eigene_freie_Zeit +
  Anfahrtszeit + Auftragsdauer`.
- **Zuschlagen**: das niedrigste Gebot gewinnt. Der Agent aktualisiert seine Position
  und freie Zeit entsprechend.

**Die strukturelle Schwäche, die dieses Stück lehrt**: einmal vergeben, wird ein
Auftrag **nie wieder infrage gestellt** - auch wenn ein späterer Auftrag zeigt, dass
eine andere Zuteilung insgesamt besser gewesen wäre. Das Protokoll sieht immer nur
den gerade angekündigten Auftrag, nie das große Ganze. Genau das beheben die
nächsten (noch nicht gebauten) Stücke dieser Linie - Kombinatorische Auktionen
(Bündel-Gebote), Distributed Constraint Optimization (formaler
Nachrichtenaustausch) und Multi-Agent Reinforcement Learning (gelernte
Langzeit-Politik) - jeweils über einen anderen Mechanismus.

Zum Vergleich löst diese Demo dieselbe Instanz zusätzlich **zentral** mit dem echten
**Google-OR-Tools-CP-SAT-Solver**, der ALLE Aufträge von Anfang an kennt - der
Unterschied zwischen beiden macht die Kosten der Dezentralität sichtbar.

**Ein wichtiger Einwand vorab**: Contract Net ist ein **Online-Algorithmus** (jede
Zuteilung fällt ohne Kenntnis künftiger Aufträge, unwiderruflich), CP-SAT löst die
**Offline-Version** desselben Problems (vollständige Information vorab) - die beiden
sind nicht einfach zwei Lösungen desselben Problems. Genau dieser Vergleich ist aber
kein Kategorienfehler, sondern das Standardwerkzeug der Online-Algorithmen-Theorie:
die **kompetitive Analyse** (Sleator & Tarjan, 1985) misst einen Online-Algorithmus
exakt daran, wie weit er hinter dem Offline-Optimum zurückbleibt - der sogenannte
**kompetitive Faktor**. Der unten gezeigte Prozentwert ist genau das, empirisch für
Ihre aktuelle Instanz gemessen - kein bewiesener Worst-Case über alle möglichen
Ankunftsreihenfolgen, sondern eine Stichprobe.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Ausgeglichene Basis": "6 Aufträge, gleichmäßige Dauer - die Kurzsichtigkeit des Protokolls kostet hier kaum etwas.",
    "Ein großer Auftrag früh": "Ein früher, ungewöhnlich langer Auftrag bindet einen Agenten - ein danach angekündigter, eigentlich naheliegender Auftrag muss an einen weit entfernten Agenten gehen.",
    "Mehr Agenten, mehr Kontention": "Mehr Aufträge und Agenten - mehr Gelegenheiten für eine früh getroffene, nicht mehr korrigierbare Fehlentscheidung.",
    "Worst Case: Sequenzielle Falle": "Wenige Agenten, große Streuung, teure Anfahrten - die Lücke zum zentralen Optimum wird am deutlichsten.",
}
preset_cols = st.columns(len(C.PRESETS))
for i, name in enumerate(C.PRESETS.keys()):
    with preset_cols[i]:
        st.button(name, use_container_width=True, on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_jobs = st.slider("Anzahl Aufträge", *bounds("n_jobs_slider"), key="n_jobs_slider")
    n_agents = st.slider("Anzahl Agenten (Kräne)", *bounds("n_agents_slider"), key="n_agents_slider")
    duration_variability = st.slider(
        "Streuung der Auftragsdauer", *bounds("duration_variability_slider"), key="duration_variability_slider",
        help="0 = alle Aufträge ähnlich lang. Höhere Werte lassen gelegentlich einen ungewöhnlich langen "
        "Auftrag entstehen - genau die Situation, in der die fehlende Rücksicht des Protokolls teuer wird.",
    )
    travel_time_per_unit = st.slider(
        "Anfahrtszeit pro Positionseinheit", *bounds("travel_time_per_unit_slider"),
        key="travel_time_per_unit_slider",
        help="Wie teuer es einen Agenten kostet, zu einem entfernten Auftrag zu fahren.",
    )
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)

    st.button(
        "🎲 Neue Instanz generieren",
        use_container_width=True,
        on_click=randomize_seed,
        help="Würfelt einen neuen Zufalls-Seed für Auftragspositionen und -dauern.",
    )

sync_query_params(n_jobs, n_agents, duration_variability, travel_time_per_unit, seed)

scenario_key = (int(n_jobs), int(n_agents), duration_variability, travel_time_per_unit, int(seed))

with st.spinner("Führe Contract Net Protocol aus..."):
    instance, result = _compute_protocol(*scenario_key)

st.markdown("## 🎯 Die Auftragsvergabe Schritt für Schritt")

if "cn_step" not in st.session_state or st.session_state.get("cn_step_owner") != scenario_key:
    st.session_state["cn_step"] = instance.n_jobs - 1
    st.session_state["cn_step_owner"] = scenario_key

max_step = instance.n_jobs - 1
step_col, play_col = st.columns([5, 1])
with step_col:
    if max_step == 0:
        step = 0
        st.caption("Nur ein Auftrag - kein Regler nötig.")
    else:
        step = st.slider(
            "Schritt (Auftragsvergabe)", 0, max_step, key="cn_step",
            help="Ein Schritt = eine angekündigte und vergebene Auftrags-Runde, in Ankunftsreihenfolge.",
        )
with play_col:
    auto_play = st.button("▶️ Abspielen", use_container_width=True)

cmp = _compute_comparison(*scenario_key)
ortools_makespan = cmp["ortools_makespan"] if cmp["ortools_feasible"] else None

chart_col, bid_col = st.columns([3, 2])
schedule_slot = chart_col.empty()
bid_slot = bid_col.empty()


def _render(current_step):
    schedule_slot.plotly_chart(
        build_schedule_figure(instance, result, current_step, ortools_makespan),
        use_container_width=True, key=f"schedule_{current_step}",
    )
    bid_slot.plotly_chart(
        build_bid_chart(result.steps[current_step]),
        use_container_width=True, key=f"bids_{current_step}",
    )


if auto_play:
    for s in range(0, max_step + 1):
        _render(s)
        time.sleep(0.4)
    step = max_step
else:
    _render(step)

live = stats_up_to_step(result, step)
lm1, lm2 = st.columns(2)
lm1.metric("Aufträge bisher vergeben", f"{live['jobs_awarded']} / {instance.n_jobs}")
lm2.metric(
    "Aktuell schlechteste freie Zeit", f"{live['worst_agent_free_time']:.1f} min",
    help="Die späteste Fertigstellungszeit über alle Agenten, nach den bisher gezeigten Schritten.",
)

st.markdown("---")

st.subheader("📐 Wie teuer wird die fehlende Weitsicht?")
st.markdown(
    """
Live für Ihre aktuelle Instanz: die vollständige, dezentrale Contract-Net-Vergabe
(Online, ohne Kenntnis künftiger Aufträge) gegen die zentrale **OR-Tools-CP-SAT-Lösung**
(Offline, kennt alle Aufträge von Anfang an) - der empirische **kompetitive Faktor**
für genau diese Instanz, keine bewiesene Worst-Case-Schranke.
"""
)

cc1, cc2 = st.columns(2)
cc1.metric("Diese Demo (Contract Net, dezentral)", f"{cmp['cnp_makespan']:.1f} min")
if cmp["ortools_feasible"]:
    delta = cmp["cnp_makespan"] - cmp["ortools_makespan"]
    cc2.metric(
        "Zentrale Optimierung (CP-SAT)", f"{cmp['ortools_makespan']:.1f} min",
        delta=f"{delta:+.1f} min ggü. Contract Net", delta_color="inverse",
        help=f"Echter industrieller Solver, {cmp['ortools_wall_time']:.2f}s - "
        + ("beweist Optimalität." if cmp["ortools_optimal"] else "Zeitlimit erreicht, beste gefundene Lösung."),
    )
else:
    cc2.metric("Zentrale Optimierung (CP-SAT)", "kein Ergebnis im Zeitlimit")

if cmp["gap_pct"] is not None:
    if cmp["gap_pct"] >= C.GAP_HIGHLIGHT_THRESHOLD_PCT:
        st.warning(
            f"⚠️ **+{cmp['gap_pct']:.1f}% länger** als das zentrale Optimum - die fehlende Rücksicht auf "
            f"spätere Aufträge kostet hier spürbar. Das Protokoll kann eine einmal vergebene Aufgabe nie "
            f"zurücknehmen, selbst wenn ein späterer Auftrag zeigt, dass es besser gegangen wäre."
        )
    else:
        st.info(
            "Bei dieser Instanz ist der Unterschied noch klein - mehr Aufträge, mehr Streuung in der "
            "Auftragsdauer oder teurere Anfahrten machen ihn deutlicher (siehe Presets oben)."
        )

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gebot** von Agent $a$ mit aktueller Position $p_a$ und freier Zeit $f_a$ für
Auftrag $j$ (Position $q_j$, Dauer $d_j$):

$$
\text{Gebot}(a, j) = f_a + \underbrace{|p_a - q_j| \cdot \tau}_{\text{Anfahrtszeit}} + d_j
$$

wobei $\tau$ die Anfahrtszeit pro Positionseinheit ist. **Zuschlag** an
$\arg\min_a \text{Gebot}(a, j)$; danach $p_a \gets q_j$, $f_a \gets \text{Gebot}(a,j)$
für den Gewinner.

**Warum das strukturell irreversibel ist**: das Protokoll verarbeitet Aufträge
$j = 1, \dots, n$ streng nacheinander. Zum Zeitpunkt der Vergabe von Auftrag $j$
ist über Auftrag $j+1, \dots, n$ noch nichts bekannt - es gibt keinen
Mechanismus, eine bereits getroffene Zuteilung im Licht eines späteren Auftrags
zu revidieren. Das Protokoll minimiert damit **nicht** den Makespan
$\max_a f_a$ über alle Aufträge gemeinsam, sondern trifft $n$ unabhängige,
myopische Einzelentscheidungen.

**Zentrale Referenz**: OR-Tools CP-SAT löst dasselbe Problem mit vollständiger
Information - Zuweisung $x_{j,a} \in \{0,1\}$, Start-/Endzeiten je Auftrag,
Sequencing (inkl. Anfahrtszeit) zwischen Aufträgen desselben Agenten, und
lexikografischem Tie-Breaking (`Minimize(makespan · W + \sum \text{Ende})`) gegen
willkürlichen Leerlauf unter gleich-optimalen Lösungen - dieselbe Formel, die
bereits in quaycrane-demo denselben Artefakt behoben hat.

**Online vs. Offline, formal**: Contract Net ist ein Online-Algorithmus $\text{ALG}$ -
Entscheidung für Auftrag $j$ fällt ohne Kenntnis von $j+1, \dots, n$. CP-SAT liefert
$\text{OPT}$, das Offline-Optimum mit vollständiger Information. Die **kompetitive
Analyse** (Sleator & Tarjan, 1985) definiert den kompetitiven Faktor gerade als
$\text{ALG}/\text{OPT}$ - der oben gezeigte Gap-Prozentsatz ist $(\text{ALG} -
\text{OPT})/\text{OPT}$, also dieselbe Größe, hier empirisch für eine konkrete
Instanz statt als bewiesene Schranke über alle Eingaben.

Implementiert in `cn_bidding.py` (die Gebotsformel), `cn_protocol.py`
(Ankündigen-Bieten-Zuschlagen-Schleife) und `cn_ortools_reference.py` (echter
Google-OR-Tools-CP-SAT-Solver).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
