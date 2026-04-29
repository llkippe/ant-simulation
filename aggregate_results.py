import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse
import subprocess

# Argument parsing
parser = argparse.ArgumentParser(description='Aggregate simulation results across runs.')
parser.add_argument('--force', action='store_true', help='Force recalculation even if output files already exist.')
parser.add_argument('--config', type=str, help='Path to a specific config folder to process (relative to data directory). If not specified, processes all config folders.')
args = parser.parse_args()

data_dir = "data"

print("="*60)
print(" STARTE META-AGGREGATION DER SIMULATIONEN")
print("="*60)

# Determine which config folders to process
if args.config:
    config_folders = [args.config]
    if not os.path.exists(os.path.join(data_dir, args.config)):
        print(f"Fehler: Konfigurationsordner '{args.config}' existiert nicht in {data_dir}")
        exit(1)
else:
    config_folders = os.listdir(data_dir)

# Gehe durch die ausgewählten Ordner im data-Verzeichnis
for config_folder in config_folders:
    config_path = os.path.join(data_dir, config_folder)

    # Überspringe Dateien, wir suchen nur Konfigurations-Ordner
    if not os.path.isdir(config_path):
        continue

    # Suche alle Run-Ordner in diesem Konfigurations-Ordner
    run_folders = [f for f in os.listdir(config_path) if f.startswith("run_")]
    if not run_folders:
        continue

    # Check if output files already exist and skip if not forcing
    expected_files = [
        "meta_throughput.csv",
        "04_meta_throughput.png",
        "meta_global_metrics.csv",
        "05_meta_global_metrics.png",
        "meta_performance_summary.csv",
        "06_meta_performance_boxplots.png"
    ]
    all_exist = all(os.path.exists(os.path.join(config_path, f)) for f in expected_files)
    skip_reason = None
    if len(run_folders) == 1:
        skip_reason = "nur ein Lauf vorhanden"
    elif all_exist and not args.force:
        skip_reason = "Ausgabedateien existieren bereits"
    
    if skip_reason:
        print(f"Überspringe Konfiguration: {config_folder} ({skip_reason})")
        continue

    print(f"\nVerarbeite Konfiguration: {config_folder} ({len(run_folders)} Läufe)")

    all_run_throughputs = []
    all_global_metrics = []
    all_settings = []
    all_source_metrics = []  # Für Rohdaten-Berechnungen
    summary_dfs = []

    # 1. Daten aus allen Runs einlesen
    for run_folder in run_folders:
        run_path = os.path.join(config_path, run_folder)

        # -- Durchsatz pro Zeitschritt berechnen (source_metrics.csv) --
        source_metrics_path = os.path.join(run_path, "source_metrics.csv")
        if os.path.exists(source_metrics_path):
            try:
                df_sm = pd.read_csv(source_metrics_path)
                if not df_sm.empty:
                    troughput_per_step = df_sm.groupby('step')['throughput'].sum()
                    troughput_per_step.name = run_folder
                    all_run_throughputs.append(troughput_per_step)
                    all_source_metrics.append(df_sm)  # Rohdaten speichern
            except pd.errors.EmptyDataError:
                pass  # Skip empty files

        # -- Global-Metriken pro Schritt sammeln (global_metrics.csv) --
        global_metrics_path = os.path.join(run_path, "global_metrics.csv")
        if os.path.exists(global_metrics_path):
            try:
                df_gm = pd.read_csv(global_metrics_path)
                if not df_gm.empty:
                    expected_cols = ['step', 'avg_step_efficeny_to_food', 'avg_step_efficeny_to_nest', 'dissapointmentRate', 'exploitingAntsCount']
                    missing = [c for c in expected_cols if c not in df_gm.columns]
                    if not missing:
                        all_global_metrics.append(df_gm[expected_cols])
            except pd.errors.EmptyDataError:
                pass  # Skip empty files

        # -- Settings für Exploitation Rate --
        settings_path = os.path.join(run_path, "settings.csv")
        if os.path.exists(settings_path):
            df_set = pd.read_csv(settings_path)
            if 'totalAnts' in df_set.columns:
                all_settings.append(df_set['totalAnts'].iloc[0])

        # -- Performance Metriken pro Run sammeln --
        performance_summary_path = os.path.join(run_path, "performance_summary.csv")
        
        # Falls Datei fehlt, build_graphs.py für diesen Run ausführen
        if not os.path.exists(performance_summary_path):
            print(f" -> performance_summary.csv fehlt in {run_folder}. Führe build_graphs.py aus...")
            try:
                # Ruft python3 build_graphs.py <run_path> auf
                subprocess.run(["python3", "build_graphs.py", run_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f" -> Fehler beim Ausführen von build_graphs.py für {run_folder}: {e}")
            except FileNotFoundError:
                print(" -> Fehler: Die Datei 'build_graphs.py' wurde im aktuellen Verzeichnis nicht gefunden.")

        # Überprüfen, ob sie JETZT existiert (falls das Skript erfolgreich war)
        if os.path.exists(performance_summary_path):
            df_ps = pd.read_csv(performance_summary_path)
            if 'Run_ID' not in df_ps.columns:
                df_ps['Run_ID'] = run_folder
            summary_dfs.append(df_ps)
        else:
            print(f" -> WARNUNG: {performance_summary_path} konnte nicht gefunden/erstellt werden.")
            

    # Sammle alle Deletions-Steps aus allen Runs
    all_deletion_steps = []
    if all_source_metrics:
        for df_sm in all_source_metrics:
            deletion_steps = df_sm[df_sm['deletion_step'] != -1]['deletion_step'].unique()
            all_deletion_steps.extend(deletion_steps)

    # Meta-Throughput: Durchschnitt + Standardabweichung (ohne null-gefüllte Steps)
    if all_run_throughputs:
        tp_df = pd.concat(all_run_throughputs, axis=1)
        #print(tp_df)
        mean_tp = tp_df.mean(axis=1, skipna=True)
        std_tp = tp_df.std(axis=1, skipna=True)
        count_tp = tp_df.count(axis=1)

        # Sicherstellen, dass Schrittfolge sortiert ist (keine Verbindung von Ende zu Anfang)
        mean_tp = mean_tp.sort_index()
        std_tp = std_tp.reindex(mean_tp.index)
        count_tp = count_tp.reindex(mean_tp.index)

        meta_throughput = pd.DataFrame({
            'step': mean_tp.index,
            'mean_throughput': mean_tp.values,
            'std_throughput': std_tp.values,
            'n_runs': count_tp.values,
        }).reset_index(drop=True)

        out_meta_tp_csv = os.path.join(config_path, "meta_throughput.csv")
        meta_throughput.to_csv(out_meta_tp_csv, index=False)

        # Exploitation Rate aggregieren
        all_ee_ratios = []
        for i, df_gm in enumerate(all_global_metrics):
            if i < len(all_settings):
                total_ants = all_settings[i]
                ee_ratio = df_gm.set_index('step')['exploitingAntsCount'] / total_ants
                ee_ratio.name = f'run_{i}'
                all_ee_ratios.append(ee_ratio)

        if all_ee_ratios:
            ee_df = pd.concat(all_ee_ratios, axis=1)
            mean_ee = ee_df.mean(axis=1, skipna=True)

        plt.figure(figsize=(14, 6))
        ax1 = plt.gca()
        # Plot Throughput
        valid_tp = mean_tp.dropna()
        ax1.plot(valid_tp.index, valid_tp.values, color='royalblue', lw=2, label='Ø Globaler Durchsatz')
        ax1.fill_between(valid_tp.index, 
                         (valid_tp - std_tp.loc[valid_tp.index]).clip(lower=0),
                         (valid_tp + std_tp.loc[valid_tp.index]),
                         color='royalblue', alpha=0.3, label='± 1 Standardabweichung')

        ax1.set_xlabel('Simulations-Schritte', fontsize=12)
        ax1.set_ylabel('Durchsatz Summe', fontsize=12)

        max_step = int(valid_tp.index.max())
        tick_spacing = max(1000, (max_step // 10))
        tick_spacing = (tick_spacing // 1000) * 1000
        tick_spacing = max(1000, tick_spacing)
        xticks = np.arange(0, max_step + tick_spacing, tick_spacing)
        ax1.set_xticks(xticks)
        ax1.set_xticklabels([str(int(x)) for x in xticks], rotation=0)

        ax1.legend(loc='upper left')
        ax1.grid(True, linestyle='--', alpha=0.5)

        # Visualisiere Wiederauftauchen von Futterquellen
        first_respawn = True
        for del_step in sorted(set(all_deletion_steps)):
            ax1.axvline(
                x=del_step,
                color='orange',
                linestyle=':',
                alpha=1,
                linewidth=2,
                label='Futterquellenereignis' if first_respawn else '_nolegend_'
            )
            first_respawn = False

        # Exploitation Rate auf twin axis
        if all_ee_ratios:
            ax2 = ax1.twinx()
            valid_ee = mean_ee.dropna()
            ax2.plot(valid_ee.index, valid_ee.values, color='black', linewidth=2, linestyle=':', label='Ausbeutungsrate (Normalisiert)')
            ax2.set_ylabel('Ausbeutungsrate', color='black', fontsize=12)
            ax2.tick_params(axis='y', labelcolor='black')
            ax2.set_ylim(0, 1.0)

            # Combine legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        plt.title(f'Gesamtdurchsatz über {count_tp.max():.0f} Läufe\n({config_folder})', fontsize=14)
        out_tp_plot = os.path.join(config_path, "04_meta_throughput.png")
        plt.savefig(out_tp_plot, bbox_inches='tight', dpi=150)
        plt.close()
        print(f" -> Meta-Throughput CSV gespeichert: {out_meta_tp_csv}")
        print(f" -> Meta-Throughput Graph gespeichert: {out_tp_plot}")

    # Meta-Global-Metrics Plot (Energie/Enttäuschung)
    if all_global_metrics:
        gm_combined = pd.concat(all_global_metrics, keys=range(len(all_global_metrics)), names=['run', 'idx']).reset_index(level='run')
        step_agg = gm_combined.groupby('step').mean().sort_index()
        step_std = gm_combined.groupby('step').std().sort_index()

        # CSV speichern
        meta_global = pd.DataFrame({
            'step': step_agg.index,
            'mean_efficiency_to_food': step_agg['avg_step_efficeny_to_food'],
            'std_efficiency_to_food': step_std['avg_step_efficeny_to_food'],
            'mean_efficiency_to_nest': step_agg['avg_step_efficeny_to_nest'],
            'std_efficiency_to_nest': step_std['avg_step_efficeny_to_nest'],
            'mean_dissapointmentRate': step_agg['dissapointmentRate'],
            'std_dissapointmentRate': step_std['dissapointmentRate'],
            'n_runs': len(all_global_metrics),
        }).reset_index(drop=True)

        out_meta_global_csv = os.path.join(config_path, "meta_global_metrics.csv")
        meta_global.to_csv(out_meta_global_csv, index=False)
        print(f" -> Meta-Global-Metrics CSV gespeichert: {out_meta_global_csv}")

        plt.figure(figsize=(16, 6))
        ax2 = plt.gca()
        ax2.plot(step_agg.index, step_agg['avg_step_efficeny_to_food'], color='green', lw=2, label='Ø Effizienz zu Futterquellen')
        ax2.fill_between(step_agg.index,
                         (step_agg['avg_step_efficeny_to_food'] - step_std['avg_step_efficeny_to_food']).clip(lower=0),
                         (step_agg['avg_step_efficeny_to_food'] + step_std['avg_step_efficeny_to_food']).clip(upper=1),
                         color='green', alpha=0.1, label='± 1 SD Futter')

        ax2.plot(step_agg.index, step_agg['avg_step_efficeny_to_nest'], color='blue', lw=2, label='Ø Effizienz zurück zum Nest')
        ax2.fill_between(step_agg.index,
                         (step_agg['avg_step_efficeny_to_nest'] - step_std['avg_step_efficeny_to_nest']).clip(lower=0),
                         (step_agg['avg_step_efficeny_to_nest'] + step_std['avg_step_efficeny_to_nest']).clip(upper=1),
                         color='blue', alpha=0.1, label='± 1 SD Nest')

        ax2.set_ylim(0, 1.1) 
        ax2.set_ylabel('Pfadeffizienz', fontsize=12)
        ax2.set_xlabel('Simulations-Schritte', fontsize=12)

        max_step = int(step_agg.index.max())
        tick_spacing = max(1000, (max_step // 10))
        tick_spacing = (tick_spacing // 1000) * 1000
        tick_spacing = max(1000, tick_spacing)
        xticks = np.arange(0, max_step + tick_spacing, tick_spacing)
        ax2.set_xticks(xticks)
        ax2.set_xticklabels([str(int(x)) for x in xticks], rotation=0)

        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)

        ax3 = ax2.twinx()
        ax3.fill_between(step_agg.index, (step_agg['dissapointmentRate'] - step_std['dissapointmentRate']).clip(lower=0), 
                         step_agg['dissapointmentRate'] + step_std['dissapointmentRate'], color='red', alpha=0.1)
        ax3.plot(step_agg.index, step_agg['dissapointmentRate'], color='red', linestyle='--', alpha=0.4, label='Ø Enttäuschungsrate')
        ax3.set_ylabel('Enttäuschungsrate', color='red', fontsize=12)
        ax3.tick_params(axis='y', labelcolor='red')

        # Visualisiere Wiederauftauchen von Futterquellen
        first_respawn = True
        for del_step in sorted(set(all_deletion_steps)):
            ax2.axvline(
                x=del_step,
                color='orange',
                linestyle=':',
                alpha=1,
                linewidth=2,
                label='Futterquellenereignis' if first_respawn else '_nolegend_'
            )
            first_respawn = False

        # Combine legends from all axes
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines3, labels3 = ax3.get_legend_handles_labels()
        ax2.legend(lines2 + lines3, labels2 + labels3, loc='upper left')

        plt.title(f'Pfadeffizienz und Enttäuschungsrate über {len(all_global_metrics)} Läufe\n({config_folder})', fontsize=14)
        out_global_plot = os.path.join(config_path, "05_meta_global_metrics.png")
        plt.savefig(out_global_plot, bbox_inches='tight', dpi=150)
        plt.close()
        print(f" -> Meta-Global-Metrics Graph gespeichert: {out_global_plot}")

    # 3. CSV: Laufbasierte Meta-Performance (jedes Run ist ein sample)
    if summary_dfs:
        merged_summary = pd.concat(summary_dfs, ignore_index=True)

        # Run-Level-Metriken aggregieren (je Run als unabhängige Stichprobe)
        # Für Convergence_Steps und Recovery_Steps: nutze Median der Runs (wie im Boxplot)
        # Für andere Metriken: nutze Mean
        perf_rows = []
        
        for metric in merged_summary['Metric'].unique():
            metric_data = merged_summary[merged_summary['Metric'] == metric]
            
            # Raten-Metriken: Mean und Std verwenden
            if metric in ['Convergence_Success_Rate_Pct', 'Recovery_Success_Rate_Pct']:
                values = metric_data['Mean'].dropna().astype(float)
                if len(values) > 0:
                    perf_rows.append({
                        'Metric': metric,
                        'Mean': values.mean(),
                        'Std': values.std(),
                        'Median': np.nan,
                        'Min': np.nan,
                        'Max': np.nan,
                        'IQR': np.nan,
                        'n_runs': len(values)
                    })
            # Convergence_Steps und Recovery_Steps: nutze Median (wie in boxplot)
            elif metric in ['Convergence_Steps', 'Recovery_Steps']:
                values = metric_data['Median'].dropna().astype(float)
                iqr_values = metric_data['IQR'].dropna().astype(float)
                if len(values) > 0:
                    perf_rows.append({
                        'Metric': metric,
                        'Mean': values.mean(),
                        'Std': values.std(),
                        'Median': values.median(),
                        'Min': values.min(),
                        'Max': values.max(),
                        'IQR': iqr_values.median() if len(iqr_values) > 0 else np.nan,
                        'n_runs': len(values)
                    })
            # Alle anderen Metriken: nutze Mean
            else:
                values = metric_data['Mean'].dropna().astype(float)
                iqr_values = metric_data['IQR'].dropna().astype(float)
                if len(values) > 0:
                    perf_rows.append({
                        'Metric': metric,
                        'Mean': values.mean(),
                        'Std': values.std(),
                        'Median': values.median(),
                        'Min': values.min(),
                        'Max': values.max(),
                        'IQR': iqr_values.median() if len(iqr_values) > 0 else np.nan,
                        'n_runs': len(values)
                    })
        
        perf_agg = pd.DataFrame(perf_rows)

        out_perf_summary = os.path.join(config_path, 'meta_performance_summary.csv')
        perf_agg.to_csv(out_perf_summary, index=False)
        print(f" -> Meta-Performance Summary CSV gespeichert: {out_perf_summary}")

        # Notched Boxplot mit Jitter Overlay
        metrics_to_plot = [
            'Convergence_Steps',
            'Recovery_Steps',
            'Global_Throughput',
            'Efficiency_Food',
            'Efficiency_Nest',
            "Jains_Fairness_Index",
        ]
        labels = [
            'Convergence Steps',
            'Recovery Steps',
            'Global Throughput',
            'Efficiency Food',
            'Efficiency Nest',
            "Jain\'s Fairness",
        ]

        data_series = []
        for metric in metrics_to_plot:
            d = merged_summary.loc[merged_summary['Metric'] == metric, 'Mean'].dropna().astype(float)
            if d.empty:
                d = pd.Series([np.nan])
            data_series.append(d)

        fig3, axes = plt.subplots(1, 5, figsize=(22, 6))
        ax_c, ax_r, ax_tp, ax_eff, ax_j = axes.flatten()

        # Convergence Steps (robuster mit Median)
        conv_values = merged_summary.loc[merged_summary['Metric'] == 'Convergence_Steps', 'Median'].dropna().astype(float)
        ax_c.boxplot(conv_values, notch=True, patch_artist=True, boxprops=dict(facecolor='orange', alpha=0.5))
        ax_c.scatter(np.random.normal(1, 0.08, size=len(conv_values)), conv_values, color='orange', alpha=0.9, s=30)
        c_mean = np.nanmean(conv_values) if len(conv_values)>0 else np.nan
        c_med = np.nanmedian(conv_values) if len(conv_values)>0 else np.nan
        ax_c.set_title('Konvergenzzeit (Median)', fontsize=12)
        ax_c.set_ylabel('Schritte nach Erstellung', fontsize=10)

        #if 'Convergence_Rate_Pct' in merged_summary['Metric'].values:
        #    conv_rate_val = merged_summary.loc[merged_summary['Metric'] == 'Convergence_Rate_Pct', 'Mean'].dropna().astype(float)
        #    if len(conv_rate_val) > 0:
        #        x_ax_lbl = ax_c.set_xticklabels([f'Erfolgsrate: {np.nanmean(conv_rate_val):.1f}%'])
        #        plt.setp(x_ax_lbl, color='red', fontweight='bold', fontsize=11)
        ax_c.set_xticklabels([])  # Keine x-Achsen-Beschriftung
        ax_c.grid(axis='y', linestyle='--', alpha=0.3)

        # Recovery Steps
        rec_values = merged_summary.loc[merged_summary['Metric'] == 'Recovery_Steps', 'Median'].dropna().astype(float)
        ax_r.boxplot(rec_values, notch=True, patch_artist=True, boxprops=dict(facecolor='darkviolet', alpha=0.5))
        ax_r.scatter(np.random.normal(1, 0.08, size=len(rec_values)), rec_values, color='darkviolet', alpha=0.9, s=30)
        r_mean = np.nanmean(rec_values) if len(rec_values)>0 else np.nan
        r_med = np.nanmedian(rec_values) if len(rec_values)>0 else np.nan
        ax_r.set_title('Erholungszeit (Median)', fontsize=12)
        ax_r.set_ylabel('Schritte', fontsize=10)
       
        #if 'Recovery_Rate_Pct' in merged_summary['Metric'].values:
        #    recovery_rate_val = merged_summary.loc[merged_summary['Metric'] == 'Recovery_Rate_Pct', 'Mean'].dropna().astype(float)
        #    if len(recovery_rate_val) > 0:
        #        x_ax_lbl = ax_r.set_xticklabels([f'Erholungsrate: {np.nanmean(recovery_rate_val):.1f}%'])
        #        plt.setp(x_ax_lbl, color='red', fontweight='bold', fontsize=11)
        ax_r.set_xticklabels([])  # Keine x-Achsen-Beschriftung
        ax_r.grid(axis='y', linestyle='--', alpha=0.3)

        # Global Throughput
        tp_values = merged_summary.loc[merged_summary['Metric'] == 'Global_Throughput', 'Mean'].dropna().astype(float)
        ax_tp.boxplot(tp_values, notch=True, patch_artist=True, boxprops=dict(facecolor='gray', alpha = 0.5))
        ax_tp.scatter(np.random.normal(1, 0.08, size=len(tp_values)), tp_values, color='gray', alpha=0.9, s=30)
        ax_tp.set_title('Ø Gesamt-Durchsatz', fontsize=12)
        ax_tp.set_xticklabels([])

        
        ax_tp.grid(axis='y', linestyle='--', alpha=0.3)

        # Pfadeffizienz als notched boxplot
        eff_food = merged_summary.loc[merged_summary['Metric'] == 'Efficiency_Food', 'Mean'].dropna().astype(float)
        eff_nest = merged_summary.loc[merged_summary['Metric'] == 'Efficiency_Nest', 'Mean'].dropna().astype(float)
        if len(eff_food) > 0 or len(eff_nest) > 0:
            eff_data = [eff_food if len(eff_food) > 0 else np.array([np.nan]), eff_nest if len(eff_nest) > 0 else np.array([np.nan])]
            ax_eff_box = ax_eff.boxplot(eff_data, notch=True, patch_artist=True, tick_labels=['Futter', 'Nest'], boxprops=dict(alpha=0.5))
            for patch, color in zip(ax_eff_box['boxes'], ['green', 'blue']):
                patch.set(facecolor=color, alpha=0.5)
            ax_eff.scatter(np.random.normal(1, 0.08, size=len(eff_food)), eff_food, color='green', alpha=0.7, s=30)
            ax_eff.scatter(np.random.normal(2, 0.08, size=len(eff_nest)), eff_nest, color='blue', alpha=0.7, s=30)
            ax_eff.set_title('Ø Pfadeffizienz', fontsize=12)

            ax_eff.grid(axis='y', linestyle='--', alpha=0.3)
        else:
            ax_eff.text(0.5, 0.5, 'Keine Pfadeffizienz-Daten', ha='center', va='center')
            ax_eff.axis('off')

        # Jain's Fairness
        jain_values = merged_summary.loc[merged_summary['Metric'] == 'Jains_Fairness_Index', 'Mean'].dropna().astype(float)
        if len(jain_values) > 0:
            ax_j.boxplot(jain_values, notch=True, patch_artist=True, boxprops=dict(facecolor='gold', alpha=0.5))
            ax_j.scatter(np.random.normal(1, 0.08, size=len(jain_values)), jain_values, color='darkgoldenrod', alpha=0.7, s=30)
            ax_j.set_title("Jain's Fairness Index", fontsize=12)
            ax_j.set_xticklabels([])
            ax_j.set_ylim(-0.05, 1.05)
            ax_j.grid(axis='y', linestyle='--', alpha=0.3)
        else:
            ax_j.text(0.5, 0.5, 'Keine Jain-Daten', ha='center', va='center')
            ax_j.axis('off')

        
        fig3.tight_layout()
        out_perf_box = os.path.join(config_path, '06_meta_performance_boxplots.png')
        fig3.savefig(out_perf_box, bbox_inches='tight', dpi=150)
        plt.close(fig3)
        print(f" -> Meta-Performance Boxplot gespeichert: {out_perf_box}")

print("\n" + "="*60)
print(" ALLE BATCHES ERFOLGREICH AGGREGIERT")
print("="*60)

