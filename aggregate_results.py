import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

data_dir = "data"

print("="*60)
print(" STARTE META-AGGREGATION DER SIMULATIONEN")
print("="*60)

# Gehe durch alle Ordner im data-Verzeichnis
for config_folder in os.listdir(data_dir):
    config_path = os.path.join(data_dir, config_folder)
    
    # Überspringe Dateien, wir suchen nur Konfigurations-Ordner
    if not os.path.isdir(config_path): continue
    
    # Suche alle Run-Ordner in diesem Konfigurations-Ordner
    run_folders = [f for f in os.listdir(config_path) if f.startswith("run_")]
    if not run_folders: continue

    print(f"\nVerarbeite Konfiguration: {config_folder} ({len(run_folders)} Läufe)")

    all_throughputs = []
    summary_dfs = []

    # 1. Daten aus allen Runs einlesen
    for run_folder in run_folders:
        run_path = os.path.join(config_path, run_folder)

        # -- Durchsatz pro Zeitschritt berechnen --
        source_metrics_path = os.path.join(run_path, "source_metrics.csv")
        if os.path.exists(source_metrics_path):
            df_sm = pd.read_csv(source_metrics_path)
            # Gesamtdurchsatz pro Zeitschritt (Summe aller Quellen)
            troughput_per_step = df_sm.groupby('step')['throughput'].sum()
            all_throughputs.append(troughput_per_step)

        # -- Performance Metriken sammeln --
        performance_summary_path = os.path.join(run_path, "performance_summary.csv")
        if os.path.exists(performance_summary_path):
            df_ps = pd.read_csv(performance_summary_path)
            summary_dfs.append(df_ps)

    # 2. Meta-Graph: Durchschnittlicher Durchsatz über die Zeit inkl. Varianz
    if all_throughputs:
        # Führt alle Serien zusammen, auffüllen mit 0 bei fehlenden Werten
        tp_df = pd.concat(all_throughputs, axis=1).fillna(0) 
        
        mean_tp = tp_df.mean(axis=1)
        std_tp = tp_df.std(axis=1)

        plt.figure(figsize=(14, 6))
        plt.plot(mean_tp.index, mean_tp, color='royalblue', lw=2, label='Ø Globaler Durchsatz')
        
        # Varianzbereich (Standardabweichung) einzeichnen
        plt.fill_between(mean_tp.index, 
                         (mean_tp - std_tp).clip(lower=0), # Durchsatz kann nicht < 0 sein
                         mean_tp + std_tp, 
                         color='royalblue', alpha=0.3, label='± 1 Standardabweichung')

        plt.title(f'Meta-Analyse: Gesamtdurchsatz über {len(run_folders)} Läufe\n({config_folder})', fontsize=14)
        plt.xlabel('Simulations-Schritte', fontsize=12)
        plt.ylabel('Durchsatz Summe', fontsize=12)
        plt.legend(loc='upper right')
        plt.grid(True, linestyle='--', alpha=0.5)
        
        out_plot = os.path.join(config_path, "04_meta_throughput.png")
        plt.savefig(out_plot, bbox_inches='tight', dpi=150)
        plt.close()
        print(f" -> Graph gespeichert: {out_plot}")

    # 3. CSV: Durchschnittliche Performance-Metriken
    if summary_dfs:
        merged_summary = pd.concat(summary_dfs)
        
        # Wir gruppieren nach der "Metric" Spalte und berechnen den Durchschnitt der Means, Medians, etc.
        agg_summary = merged_summary.groupby('Metric').mean().reset_index()
        
        # 'Run_ID' ergibt im Aggregat keinen Sinn mehr
        if 'Run_ID' in agg_summary.columns:
            agg_summary = agg_summary.drop(columns=['Run_ID'])
            
        out_csv = os.path.join(config_path, "aggregated_performance_summary.csv")
        agg_summary.to_csv(out_csv, index=False)
        print(f" -> Tabelle gespeichert: {out_csv}")

print("\n" + "="*60)
print(" ALLE BATCHES ERFOLGREICH AGGREGIERT")
print("="*60)