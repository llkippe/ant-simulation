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
    if not os.path.isdir(config_path):
        continue

    # Suche alle Run-Ordner in diesem Konfigurations-Ordner
    run_folders = [f for f in os.listdir(config_path) if f.startswith("run_")]
    if not run_folders:
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
            df_sm = pd.read_csv(source_metrics_path)
            troughput_per_step = df_sm.groupby('step')['throughput'].sum()
            troughput_per_step.name = run_folder
            all_run_throughputs.append(troughput_per_step)
            all_source_metrics.append(df_sm)  # Rohdaten speichern

        # -- Global-Metriken pro Schritt sammeln (global_metrics.csv) --
        global_metrics_path = os.path.join(run_path, "global_metrics.csv")
        if os.path.exists(global_metrics_path):
            df_gm = pd.read_csv(global_metrics_path)
            if not df_gm.empty:
                expected_cols = ['step', 'avg_step_efficeny_to_food', 'avg_step_efficeny_to_nest', 'dissapointmentRate', 'exploitingAntsCount']
                missing = [c for c in expected_cols if c not in df_gm.columns]
                if not missing:
                    all_global_metrics.append(df_gm[expected_cols])

        # -- Settings für Exploitation Rate --
        settings_path = os.path.join(run_path, "settings.csv")
        if os.path.exists(settings_path):
            df_set = pd.read_csv(settings_path)
            if 'totalAnts' in df_set.columns:
                all_settings.append(df_set['totalAnts'].iloc[0])

        # -- Performance Metriken pro Run sammeln --
        performance_summary_path = os.path.join(run_path, "performance_summary.csv")
        if os.path.exists(performance_summary_path):
            df_ps = pd.read_csv(performance_summary_path)
            if 'Run_ID' not in df_ps.columns:
                df_ps['Run_ID'] = run_folder
            summary_dfs.append(df_ps)

    # Meta-Throughput: Durchschnitt + Standardabweichung (ohne null-gefüllte Steps)
    if all_run_throughputs:
        tp_df = pd.concat(all_run_throughputs, axis=1)
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
        ax1.legend(loc='upper left')
        ax1.grid(True, linestyle='--', alpha=0.5)

        # Exploitation Rate auf twin axis
        if all_ee_ratios:
            ax2 = ax1.twinx()
            valid_ee = mean_ee.dropna()
            ax2.plot(valid_ee.index, valid_ee.values, color='black', linewidth=2, linestyle=':', label='Exploitation Rate (0-1)')
            ax2.set_ylabel('Exploitation Ratio (Normalized)', color='black', fontsize=12)
            ax2.tick_params(axis='y', labelcolor='black')
            ax2.set_ylim(0, 1.0)

            # Combine legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        plt.title(f'Meta-Analyse: Gesamtdurchsatz über {count_tp.max():.0f}/{len(run_folders)} Läufe\n({config_folder})', fontsize=14)
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
        ax2.plot(step_agg.index, step_agg['avg_step_efficeny_to_nest'], color='blue', lw=2, label='Ø Effizienz zurück zum Nest')

        ax2.set_ylim(0, 1.1) 
        ax2.set_ylabel('Pfadeffizienz', fontsize=12)
        ax2.set_xlabel('Simulations-Schritte', fontsize=12)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)

        ax3 = ax2.twinx()
        ax3.fill_between(step_agg.index, (step_agg['dissapointmentRate'] - step_std['dissapointmentRate']).clip(lower=0), 
                         step_agg['dissapointmentRate'] + step_std['dissapointmentRate'], color='red', alpha=0.1)
        ax3.plot(step_agg.index, step_agg['dissapointmentRate'], color='red', linestyle='--', alpha=0.4, label='Ø Enttäuschungsrate')
        ax3.set_ylabel('Enttäuschungsrate', color='red', fontsize=12)
        ax3.tick_params(axis='y', labelcolor='red')

        plt.title(f'Meta-Global-Metrics über {len(all_global_metrics)} Läufe\n({config_folder})', fontsize=14)
        out_global_plot = os.path.join(config_path, "05_meta_global_metrics.png")
        plt.savefig(out_global_plot, bbox_inches='tight', dpi=150)
        plt.close()
        print(f" -> Meta-Global-Metrics Graph gespeichert: {out_global_plot}")

    # 3. CSV: Durchschnittliche Performance-Metriken
    if summary_dfs:
        merged_summary = pd.concat(summary_dfs, ignore_index=True)

        # Run_ID ist string, daher vor der numerischen Aggregation rausnehmen
        merged_summary_numeric = merged_summary.drop(columns=['Run_ID'], errors='ignore')
        agg_summary = merged_summary_numeric.groupby('Metric', as_index=False).mean()

        out_csv = os.path.join(config_path, "aggregated_performance_summary.csv")
        agg_summary.to_csv(out_csv, index=False)
        print(f" -> Aggregiertes Performance-CSV gespeichert: {out_csv}")

    # 4. Meta Performance Boxplots (aus Rohdaten)
    if all_source_metrics and all_global_metrics:
        # Rohdaten sammeln für alle Metriken
        all_convergence_steps = []
        all_recovery_steps = []
        all_efficiency_food = []
        all_efficiency_nest = []
        all_global_throughputs = []
        all_jains = []

        troughput_convergence = 1  # Wie im Original

        for i, df_sm in enumerate(all_source_metrics):
            if df_sm.empty:
                continue

            pivot_df = df_sm.pivot(index='step', columns='source_id', values='throughput').fillna(0)
            source_ids = sorted(pivot_df.columns)
            global_throughput = pivot_df.sum(axis=1)

            # Convergence (quasi 1. Schritt > threshold nach creation)
            for sid in source_ids:
                source_data = df_sm[df_sm['source_id'] == sid]
                creation_step = source_data['creation_step'].max()
                if creation_step == -1:
                    continue
                over_convergence = source_data[source_data['throughput'] > troughput_convergence]
                if not over_convergence.empty:
                    first_step_over_convergence = over_convergence['step'].min()
                    steps_to_reach_convergence = first_step_over_convergence - creation_step
                    if steps_to_reach_convergence >= 0:
                        all_convergence_steps.append(steps_to_reach_convergence)

            # Recovery (nach dem Build-Graphs-Algorithmus)
            puffer = 0.9
            min_stable_steps = 100
            steps_for_avg = 50
            deletion_steps = df_sm[df_sm['deletion_step'] != -1]['deletion_step'].unique()
            for d_step in deletion_steps:
                pre_data = global_throughput[(global_throughput.index >= d_step - steps_for_avg) & (global_throughput.index < d_step)]
                if pre_data.empty:
                    continue
                target_value = pre_data.mean() * puffer

                post_deletion = global_throughput[global_throughput.index > d_step]
                dropped_data = post_deletion[post_deletion < target_value]
                if dropped_data.empty:
                    continue
                first_drop_step = dropped_data.index.min()

                actual_recovery_search = post_deletion[post_deletion.index > first_drop_step]
                for step, value in actual_recovery_search.items():
                    if value >= target_value:
                        future = global_throughput[(global_throughput.index >= step) & (global_throughput.index <= step + min_stable_steps)]
                        if not future.empty and future.min() >= target_value:
                            recovery_step = step - d_step
                            all_recovery_steps.append(recovery_step)
                            break

            # Global Throughput
            global_tp = pivot_df.sum(axis=1)
            all_global_throughputs.extend(global_tp.values)

            # Jain's Fairness
            sum_tp = pivot_df.sum(axis=1)
            sum_sq_tp = (pivot_df ** 2).sum(axis=1)
            active_counts = (pivot_df > 0).sum(axis=1).replace(0, np.nan)
            denominator = (active_counts * sum_sq_tp).replace(0, np.nan)
            jains_index = (sum_tp ** 2) / denominator
            jains_index = jains_index.clip(upper=1).fillna(0)
            if not jains_index.empty:
                all_jains.extend(jains_index.dropna().values)

        # Efficiency aus global_metrics
        for df_gm in all_global_metrics:
            all_efficiency_food.extend(df_gm['avg_step_efficeny_to_food'].dropna().values)
            all_efficiency_nest.extend(df_gm['avg_step_efficeny_to_nest'].dropna().values)

        # Raten aus aggregierten Daten
        merged_summary = pd.concat(summary_dfs, ignore_index=True)
        conv_rate = merged_summary[merged_summary['Metric'] == 'Convergence_Rate_Pct']['Mean'].mean() if 'Convergence_Rate_Pct' in merged_summary['Metric'].values else 0
        rec_rate = merged_summary[merged_summary['Metric'] == 'Recovery_Rate_Pct']['Mean'].mean() if 'Recovery_Rate_Pct' in merged_summary['Metric'].values else 0

        fig3, (ax_box1, ax_box_rec, ax_box2, ax_box3, ax_box_jain) = plt.subplots(1, 5, figsize=(22, 6))

        # --- 1. Convergence Steps ---
        if all_convergence_steps:
            x_coords = np.random.normal(1, 0.04, size=len(all_convergence_steps))
            ax_box1.scatter(x_coords, all_convergence_steps, alpha=0.7, edgecolors='black', color='lightblue', s=70, marker='^')
            ax_box1.hlines(np.median(all_convergence_steps), 0.8, 1.2, colors='black', linestyles='--', lw=2)
            ax_box1.set_title('Zeit bis Convergence', fontsize=10)
            ax_box1.set_ylabel('Schritte', fontsize=10)
            ax_box1.set_xticks([1])
            ax_box1.set_xticklabels([f"Ø Rate: {conv_rate:.1f}%"])
            ax_box1.grid(axis='y', linestyle='--', alpha=0.3)

        # --- 2. Recovery Steps ---
        if all_recovery_steps:
            x_coords = np.random.normal(1, 0.04, size=len(all_recovery_steps))
            ax_box_rec.scatter(x_coords, all_recovery_steps, alpha=0.7, edgecolors='black', color='lightcoral', s=70, marker='v')
            ax_box_rec.hlines(np.median(all_recovery_steps), 0.8, 1.2, colors='black', linestyles='--', lw=2)
            ax_box_rec.set_title('Erholungszeit', fontsize=10)
            ax_box_rec.set_ylabel('Schritte nach Einbruch', fontsize=10)
            ax_box_rec.set_xticks([1])
            ax_box_rec.set_xticklabels([f"Ø Rate: {rec_rate:.1f}%"])

        # --- 3. Efficiency ---
        if all_efficiency_food and all_efficiency_nest:
            bp2 = ax_box2.boxplot([all_efficiency_food, all_efficiency_nest], patch_artist=True, tick_labels=['Futter', 'Nest'], widths=0.4)
            for patch, color in zip(bp2['boxes'], ['green', 'blue']):
                patch.set(facecolor=color, alpha=0.5)
            ax_box2.set_title('Ø Pfadeffizienz', fontsize=10)
            ax_box2.set_ylim(-0.05, 1.05)
            ax_box2.grid(axis='y', linestyle='--', alpha=0.3)

        # --- 4. Global Throughput ---
        if all_global_throughputs:
            bp4 = ax_box3.boxplot(all_global_throughputs, patch_artist=True, widths=0.4)
            for box in bp4['boxes']:
                box.set(facecolor='gray', alpha=0.5)
            ax_box3.set_title('Ø Gesamt-Durchsatz', fontsize=10)
            ax_box3.set_xticklabels([''])

        # --- 5. Jain's Fairness ---
        if all_jains:
            bp5 = ax_box_jain.boxplot(all_jains, patch_artist=True, widths=0.4)
            for box in bp5['boxes']:
                box.set(facecolor='gold', alpha=0.5)
            ax_box_jain.set_title("Jain's Fairness Index", fontsize=10)
            ax_box_jain.set_ylim(-0.05, 1.05)
            ax_box_jain.set_xticklabels([''])

        fig3.tight_layout()
        plt.subplots_adjust(wspace=0.4, bottom=0.2)
        out_perf_box = os.path.join(config_path, "06_meta_performance_boxplots.png")
        fig3.savefig(out_perf_box, bbox_inches='tight', dpi=150)
        plt.close(fig3)
        print(f" -> Meta-Performance-Boxplot gespeichert: {out_perf_box}")

print("\n" + "="*60)
print(" ALLE BATCHES ERFOLGREICH AGGREGIERT")
print("="*60)