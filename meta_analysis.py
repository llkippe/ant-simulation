import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

def load_config_data(config_path):
    """Sammelt die aggregierten Metriken aller runs einer Konfiguration."""
    all_runs_metrics = # FIX: Initialisierung korrigiert
    
    run_folders = [f for f in os.listdir(config_path) if f.startswith("run_")]
    if not run_folders:
        return pd.DataFrame()

    for run in run_folders:
        summary_path = os.path.join(config_path, run, "performance_summary.csv")
        if os.path.exists(summary_path):
            df = pd.read_csv(summary_path)
            run_data = {}
            for _, row in df.iterrows():
                metric = row['Metric']
                # Zeitdaten -> Median, Durchsatz/Effizienz -> Mean [1, 2]
                if "Steps" in metric:
                    run_data[metric] = row['Median']
                elif "Rate_Pct" in metric:
                    run_data[metric] = row['Mean'] 
                else:
                    run_data[metric] = row['Mean']
            all_runs_metrics.append(run_data)
            
    return pd.DataFrame(all_runs_metrics)

def plot_meta_analysis(df_aggregate, config_name, output_path):
    """Erstellt die wissenschaftliche Meta-Aggregation."""
    fig, axes = plt.subplots(1, 5, figsize=(24, 7))
    ax_conv, ax_rec, ax_eff, ax_tp, ax_jain = axes

    # --- 1. Konvergenzzeit ---
    # Wir filtern NaNs nur für diese Spalte [5]
    data = df_aggregate.dropna()
    # Erfolgsrate berechnen aus der entsprechenden Spalte
    rate = df_aggregate.mean() if 'Convergence_Rate_Pct' in df_aggregate else 0
    
    if not data.empty:
        ax_conv.boxplot(data, notch=True, patch_artist=True, boxprops=dict(facecolor='lightblue', alpha=0.5))
        # FIX: len(data) entspricht nun exakt der Series-Größe
        ax_conv.scatter(np.random.normal(1, 0.04, size=len(data)), data, color='teal', marker='^', alpha=0.6)
    
    ax_conv.set_title('Meta: Zeit bis Konvergenz')
    ax_conv.set_ylabel('Schritte (Median pro Run)')
    ax_conv.set_xticklabels([f"Ø Erfolgsrate:\n{rate:.1f}%"])
    ax_conv.grid(axis='y', linestyle='--', alpha=0.3)

    # --- 2. Erholungszeit ---
    data = df_aggregate.dropna()
    rate = df_aggregate.mean() if 'Recovery_Rate_Pct' in df_aggregate else 0
    
    if not data.empty:
        ax_rec.boxplot(data, notch=True, patch_artist=True, boxprops=dict(facecolor='mediumpurple', alpha=0.5))
        ax_rec.scatter(np.random.normal(1, 0.04, size=len(data)), data, color='darkviolet', marker='D', alpha=0.6)
    
    ax_rec.set_title('Meta: Erholungszeit')
    ax_rec.set_xticklabels()
    ax_rec.grid(axis='y', linestyle='--', alpha=0.3)

    # --- 3. Pfadeffizienz ---
    eff_f = df_aggregate['Efficiency_Food'].dropna()
    eff_n = df_aggregate['Efficiency_Nest'].dropna()
    if not eff_f.empty and not eff_n.empty:
        bp = ax_eff.boxplot([eff_f, eff_n], notch=True, patch_artist=True, tick_labels=['Futter', 'Nest'])
        for patch, color in zip(bp['boxes'], ['green', 'blue']):
            patch.set(facecolor=color, alpha=0.3)
        ax_eff.scatter(np.random.normal(1, 0.04, size=len(eff_f)), eff_f, color='green', alpha=0.4, s=20)
        ax_eff.scatter(np.random.normal(2, 0.04, size=len(eff_n)), eff_n, color='blue', alpha=0.4, s=20)
    ax_eff.set_title('Meta: Ø Pfadeffizienz')
    ax_eff.set_ylim(-0.05, 1.05)
    ax_eff.grid(axis='y', linestyle='--', alpha=0.3)

    # --- 4. Gesamt-Durchsatz ---
    data = df_aggregate.dropna()
    if not data.empty:
        ax_tp.boxplot(data, notch=True, patch_artist=True, boxprops=dict(facecolor='gray', alpha=0.3))
        ax_tp.scatter(np.random.normal(1, 0.04, size=len(data)), data, color='black', alpha=0.4)
    ax_tp.set_title('Meta: Ø Gesamt-Durchsatz')
    ax_tp.set_xticklabels([''])
    ax_tp.grid(axis='y', linestyle='--', alpha=0.3)

    # --- 5. Jain's Fairness Index ---
    data = df_aggregate['Jains_Fairness_Index'].dropna()
    if not data.empty:
        ax_jain.boxplot(data, notch=True, patch_artist=True, boxprops=dict(facecolor='gold', alpha=0.3))
        ax_jain.scatter(np.random.normal(1, 0.04, size=len(data)), data, color='orange', alpha=0.6)
    ax_jain.set_title("Meta: Jain's Fairness Index")
    ax_jain.set_ylim(-0.05, 1.05)
    ax_jain.grid(axis='y', linestyle='--', alpha=0.3)

    plt.suptitle(f"Meta-Aggregation: {config_name}\n(N = {len(df_aggregate)} unabhängige Simulationsläufe)", fontsize=14)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()

if __name__ == "__main__":
    data_dir = "data"
    for config_folder in os.listdir(data_dir):
        config_path = os.path.join(data_dir, config_folder)
        if os.path.isdir(config_path):
            print(f"Verarbeite Konfiguration: {config_folder}")
            df_aggregate = load_config_data(config_path)
            if not df_aggregate.empty:
                out_path = os.path.join(config_path, "meta_analysis_report.png")
                plot_meta_analysis(df_aggregate, config_folder, out_path)
                print(f"  -> Meta-Graph erstellt: {out_path}")