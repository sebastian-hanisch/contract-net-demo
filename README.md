# Contract Net Protocol an der Kran-Auftragsvergabe – Streamlit-Demo

Erstes Stück der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations
Research und Machine Learning", **Multi-Agenten-Koordinations-Linie** - der Root
dieser neuen Linie: das **Contract Net Protocol** (Smith, 1980) zeigt dezentrale
Aufgabenvergabe (ankündigen → bieten → zuschlagen) statt eines zentralen Solvers.

## Warum ein eigenes, vereinfachtes Vehikel statt quaycrane-demo

Das Vokabular (Kräne, Aufträge, Positionen) ist an das Schwester-Fall-Demo
[quaycrane-demo](../quaycrane-demo) angelehnt, aber die Struktur bewusst
vereinfacht: **keine gemeinsame Schiene, keine Non-Crossing-Regel** zwischen
Agenten. quaycrane-demo behandelt bereits eigenständig die physische
Kran-Choreographie (Kim & Park 2004); diese Demo zeigt einen
Koordinations-*Mechanismus* und würde durch dieselbe Komplexität nur verwässert.
quaycrane-demos zentraler CP-SAT-Solver dient hier als Namensgeber für das
Vergleichsprinzip, nicht als strukturelle Vorlage - `cn_ortools_reference.py` ist
ein eigenes, viel einfacheres Modell (nur Sequencing innerhalb eines Agenten,
keine Interaktion zwischen Agenten).

## Die gelehrte Schwäche

Jeder Agent bietet rein lokal: "wenn ich diesen Auftrag ans Ende meiner eigenen
Warteschlange hänge, wann bin ich fertig?" Der Zuschlag geht ans niedrigste Gebot -
und bleibt **für immer bestehen**, egal was später angekündigt wird. Ein
überraschender, empirisch gefundener Fund beim Kalibrieren (siehe unten): selbst
bei völlig gleichmäßiger Auftragsdauer (keine "Ausreißer") schwankt die Lücke zum
zentralen Optimum stark - schon die reine Positions-/Reihenfolge-Struktur macht
eine frühe, unumkehrbare Zuteilung teuer, nicht nur ungewöhnlich lange Aufträge.
Sogar mit nur **einem** Agenten kann das Protokoll gegen die zentrale Lösung
verlieren, weil es Aufträge strikt in Ankunftsreihenfolge abarbeitet und sie nie
zur besseren Reihenfolge umsortiert (`tests/test_protocol.py::
test_single_agent_cnp_can_lose_to_cp_sat_on_ordering_alone`).

## Eine Überraschung beim Kalibrieren, nicht vorab angenommen

Die ursprüngliche Annahme war: `duration_variability=0` (keine Ausreißer) sollte
eine durchgehend kleine Lücke zeigen, erst höhere Werte sollten sie sichtbar
machen. Ein Kalibrierungs-Sweep über 20 Seeds bei `duration_variability=0` zeigte
stattdessen eine Lücke zwischen **-0,8 % und 74,7 %** - die Positions-/
Reihenfolge-Struktur allein treibt die Lücke schon erheblich, unabhängig von
Auftragsdauer-Ausreißern. Presets wurden deshalb nicht nach der ersten
plausiblen Parameterkombination benannt, sondern nach tatsächlich gemessenen,
seed-spezifischen Ergebnissen kalibriert (siehe `cn_constants.PRESETS`s
Kommentar) - dieselbe "sweep vor Behauptung" Disziplin wie im übrigen Portfolio.

## Referenzlöser

- **`cn_ortools_reference.py`**: echter Google-OR-Tools-CP-SAT-Solver mit
  vollständiger Information über alle Aufträge - was ein zentraler Planer
  erreicht hätte. Lexikografisches Tie-Breaking (`Minimize(makespan · W +
  Σ Ende)`) verhindert, dass gleich-optimale Lösungen mit willkürlichem
  Leerlauf zurückgegeben werden (dieselbe Formel/derselbe Fund wie in
  quaycrane-demo).
- **`cn_bruteforce.py`**: vollständige Enumeration aller Zuordnungen UND
  Reihenfolgen - nur für sehr kleine Instanzen (Tests, nicht live in der App).

## Verifikation

- **Unumkehrbarkeit**: einmal vergebene Aufträge ändern nie den Agenten
  (`test_once_awarded_a_job_never_changes_agent_across_later_steps`).
- **Vollständigkeit**: jeder Auftrag wird genau einmal zugeteilt.
- **Optimalitätsschranke**: Contract Net schlägt nie das CP-SAT-Optimum (bis auf
  die bewusste, dokumentierte Rundungstoleranz des skalierten CP-SAT-Modells).
- **Bruteforce- und Ein-Agenten-Cross-Check**: CP-SAT stimmt mit vollständiger
  Enumeration überein; im Ein-Agenten-Fall serviert Contract Net nachweislich in
  reiner Ankunftsreihenfolge.
- **Tie-Break-Regression**: mehrfaches Lösen derselben Instanz liefert
  identischen Makespan UND identische Sekundärkennzahl (kein Leerlauf-Artefakt).
- **Preset-Kalibrierung**: `test_presets_produce_gap_in_expected_band` hält die
  gemessenen Lücken-Bänder der vier Presets als Regression fest.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Hauptablauf: Presets, Einstellungen, Vergabe-Animation, Vergleich, Formulierungs-Expander |
| `cn_constants.py` | Defaults, Regler-Grenzen, `PRESETS` |
| `cn_presets.py` | `SettingSpec`/`SETTING_SPECS`, Permalink-Logik, Presets, Zufalls-Seed-Button |
| `cn_scenario.py` | Zufällige Kran-zu-Auftrag-Instanzen (`Job`, `Instance`) |
| `cn_bidding.py` | Die Gebotsformel - der eine gelehrte Mechanismus |
| `cn_protocol.py` | Ankündigen-Bieten-Zuschlagen-Schleife über eine ganze Instanz |
| `cn_ortools_reference.py` | Echter Google-OR-Tools-CP-SAT-Solver (zentrale Referenz) |
| `cn_bruteforce.py` | Unabhängige Referenzlösung (vollständige Enumeration) |
| `cn_evaluation.py` | Kennzahlen, Vergleich gegen CP-SAT |
| `cn_visualization.py` | Wachsender Gantt-Chart + Gebots-Balkendiagramm je Schritt (Plotly) |
| `tests/` | Gebots-/Protokoll-Invarianten, CP-SAT-/Bruteforce-Cross-Check, Preset-Kalibrierungs-Regression |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
