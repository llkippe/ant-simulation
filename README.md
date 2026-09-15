# Ant Simulation — Bachelorarbeit

Dieses Repository enthält Code und Auswertungsskripte für Simulationen einer Ameisenkolonie (Teil einer Bachelorarbeit). Ziel ist die Untersuchung von Konvergenz, Resilienz und Pfadeffizienz in verschiedenen Konfigurationen.

**Projektübersicht**
- **Code:** Simulations-Engine in Java (Maven-Projekt) unter `src/main/java`.
- **Analyse / Plots:** Python-Skripte im Projekt-Root erzeugen Graphen und aggregierte Ergebnisse.
- **Daten:** Rohläufe und Meta-Ergebnisse liegen im `data/`-Verzeichnis.

**Wichtige Dateien**
- `aggregate_results.py`: Aggregiert Ergebnisse über mehrere Runs und erzeugt Meta-CSV sowie Meta-Plots. [aggregate_results.py](aggregate_results.py#L1)
- `build_graphs.py`: Erzeugt Diagramme und Run-spezifische Metriken aus einzelnen Run-Ordnern. [build_graphs.py](build_graphs.py#L1)
- Java-Simulation: Hauptklasse `Simulation`. [src/main/java/de/lucakippe/simulation/Simulation.java](src/main/java/de/lucakippe/simulation/Simulation.java#L1)

**Datenstruktur (kurz)**
- `data/<config_folder>/run_X/` — einzelne Läufe mit CSV-Dateien wie `source_metrics.csv`, `global_metrics.csv`, `performance_summary.csv`, `settings.csv`.
- `data/<config_folder>/meta_*.csv` — von `aggregate_results.py` erzeugte Meta-Dateien pro Konfiguration.

**Installation (Python)**
- Empfohlen: virtuelles Environment verwenden (im Repo ist `graph_venv/`).

Beispiel (falls noch nicht aktiviert):
```
python3 -m venv graph_venv
source graph_venv/bin/activate
pip install -r requirements.txt
```

**Build (Java)**
- Maven wird verwendet; von Projekt-Root aus:
```
mvn -q -DskipTests package
```

Hinweis: Die Simulation kann auch per IDE gestartet werden. Die Klasse `Simulation` ist der Einstiegspunkt.

**Typische Workflows**
- Einen einzelnen Run auswerten (innerhalb desRun-Ordners):
```
python3 build_graphs.py data/<config_folder>/run_1
```
- Alle Runs einer Konfiguration aggregieren und Meta-Plots erzeugen:
```
python3 aggregate_results.py --config <config_folder>
```
- Alle Konfigurationen verarbeiten:
```
python3 aggregate_results.py
```

**Reproduzierbarkeit / Hinweise**
- Jeder Run speichert Settings und Metriken im jeweiligen `run_X`-Ordner.
- `aggregate_results.py` ruft bei Bedarf `build_graphs.py` auf, falls `performance_summary.csv` fehlt.
