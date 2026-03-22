import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.markers as mmarkers
import sys
import os
import numpy as np


# ==========================================
# 1. Handle Input Argument & Paths
# ==========================================
if len(sys.argv) < 2:
    print("Usage: python3 build_graphs.py <run_number>")
    sys.exit(1)

run_id = sys.argv[1]
base_dir = f"{run_id}"
csv_source = os.path.join(base_dir, "source_metrics.csv")
csv_global = os.path.join(base_dir, "global_metrics.csv")
csv_settings = os.path.join(base_dir, "settings.csv")



# Neue Output-Pfade
out_source_png = os.path.join(base_dir, "01_source_throughput.png")
out_global_png = os.path.join(base_dir, "02_global_efficiency.png")
out_boxplots_png = os.path.join(base_dir, "03_performance_boxplots.png")

if not os.path.exists(csv_source) or not os.path.exists(csv_global):
    print(f"Error: Missing CSV files in {base_dir}")
    sys.exit(1)

# ==========================================
# 2. Load Data & Setup
# ==========================================
df_source = pd.read_csv(csv_source)
df_global = pd.read_csv(csv_global)
df_settings = pd.read_csv(csv_settings)

pivot_df = df_source.pivot(index='step', columns='source_id', values='throughput').fillna(0)
source_ids = sorted(pivot_df.columns)

cmap = plt.get_cmap('tab10')
colors = {sid: cmap(i % 10) for i, sid in enumerate(source_ids)}

#max_step = df_source['step'].max()
#xticks = np.arange(0, max_step+100, 1000)

# convergence daten 
troughput_convergence = 1
#steps_to_reach_convergence_list = []
convergence_data_pairs = []

# Wir nutzen das bereits berechnete global_throughput
global_throughput = pivot_df.sum(axis=1)
deletion_steps = df_source[df_source['deletion_step'] != -1]['deletion_step'].unique()


recovery_events = [] # Liste für Marker: (step, throughput_value)
recovery_times = []  # Liste für Statistik: (time_delta)
# Puffer und Bestätigungsfenster definieren
puffer = 0.9  # 90% des alten Niveaus reichen als "recovered"
min_stable_steps = 100
steps_for_avg = 50

# ==========================================
# GRAPH 1: SOURCE THROUGHPUT
# ==========================================
fig1, ax1 = plt.subplots(figsize=(16, 8))


ax1.stackplot(pivot_df.index, pivot_df.values.T, 
             labels=[f'Source {int(sid)}' for sid in source_ids], 
             colors=[colors[sid] for sid in source_ids], alpha=0.7)

# Neue Werte für Marker-Positionen
marker_y_start = -1 # Reduziert den Startpunkt
marker_spacing = 1   # Reduziert den Abstand zwischen den Markern


for d_step in deletion_steps:
    # 1. Zielwert definieren (Durchschnitt vor der Löschung)
    pre_data = global_throughput[(global_throughput.index >= d_step - steps_for_avg) & (global_throughput.index < d_step)]
    
    if pre_data.empty: continue
    target_value = pre_data.mean() * puffer
    
    # 2. Den "Tiefpunkt" abwarten
    # Wir suchen erst ab dem Punkt, an dem der Durchsatz UNTER den Zielwert gefallen ist
    post_deletion = global_throughput[global_throughput.index > d_step]
    
    # Wir finden den ersten Schritt, an dem der Durchsatz wirklich eingebrochen ist
    dropped_data = post_deletion[post_deletion < target_value]
    if dropped_data.empty: continue
    first_drop_step = dropped_data.index.min()
    
    # 3. Recovery-Suche erst NACH dem Einbruch starten
    actual_recovery_search = post_deletion[post_deletion.index > first_drop_step]
    
    for step, value in actual_recovery_search.items():
        if value >= target_value:
            # Stabilitäts-Check (100 Schritte)
            future = global_throughput[(global_throughput.index >= step) & (global_throughput.index <= step + min_stable_steps)]
            if not future.empty and future.min() >= target_value:
                recovery_step = step
                recovery_times.append(recovery_step - d_step)
                recovery_events.append((recovery_step, value))
                break



for i, sid in enumerate(source_ids):
    source_data = df_source[df_source['source_id'] == sid]
    color = colors[sid]
    y_pos = marker_y_start - (i * marker_spacing)

    # Marker: Creation
    creation_step = source_data['creation_step'].max()
    if creation_step != -1:
        ax1.scatter(creation_step, y_pos, color=color, s=120,
                    marker=mmarkers.MarkerStyle('o', fillstyle='left'),
                    edgecolors='black', zorder=10)

    # Marker: Deletion
    deletion_step = source_data['deletion_step'].max()
    if deletion_step != -1:
        ax1.scatter(deletion_step, y_pos, color=color, s=130,
                    marker=mmarkers.MarkerStyle('o', fillstyle='right'),
                    edgecolors='black', zorder=10)

    # Throughput > 50 Score Calculation
    over_convergence = source_data[source_data['throughput'] > troughput_convergence]
    if creation_step != -1 and not over_convergence.empty:
        first_step_over_convergence = over_convergence['step'].min()
        steps_to_reach_convergence = first_step_over_convergence - creation_step
        
        convergence_data_pairs.append((sid, steps_to_reach_convergence))

        ax1.scatter(first_step_over_convergence, y_pos, color=color, s=110, marker='^',
                    edgecolors='black', zorder=10)
        
if recovery_events:
    r_steps, r_values = zip(*recovery_events)
    ax1.scatter(r_steps, r_values, color='darkviolet', s=90, marker='D', 
                edgecolors='black', label='Resilienz erreicht', zorder=20)


# Anpassung der unteren y-Achsenbegrenzungen
lowest_y = marker_y_start - (len(source_ids) * marker_spacing)
ax1.set_ylim(bottom=lowest_y) 

# 1. Berechne den maximalen Gesamtdurchsatz (Summe aller Quellen pro Zeitschritt)
max_total_throughput = pivot_df.sum(axis=1).max()

# 2. Definiere das obere Limit für die Ticks (aufgerundet auf die nächste Ganzzahl für sauberere Ticks)
upper_tick_limit = int(np.ceil(max_total_throughput))

# 3. Y-Achse anpassen (wir ersetzen die 6 durch upper_tick_limit + 1, damit das Max enthalten ist)
yticks = np.arange(len(source_ids) * -1, upper_tick_limit + 1, 1)
ax1.set_yticks(yticks)

max_step = df_source['step'].max()
tick_spacing = max(1000, (max_step // 10)) 
# Rundet auf das nächste Tausender für saubere Zahlen
tick_spacing = (tick_spacing // 1000) * 1000 

xticks = np.arange(0, max_step + tick_spacing, tick_spacing)
ax1.set_xticks(xticks)


ax1.set_xlabel('Simulations Schritt', fontsize=12)
ax1.set_ylabel('Durchsatz & Simulations Events', fontsize=12)
ax1.set_title('Futterqullendurchsatz pro Zeitschritt', fontsize=16, pad=10)
ax1.grid(axis='y', linestyle='--', alpha=0.3)


# exploration / explotation index

total_ants = df_settings['totalAnts'].iloc[0]
ee_ratio = df_global['exploitingAntsCount'] / total_ants

ax1_twin = ax1.twinx()

# Plotting the line
line_twin = ax1_twin.plot(df_global['step'], ee_ratio, color='black', 
                          linewidth=2, linestyle=':', label='Exploitation Rate (0-1)')

# ax1 current range: [lowest_y, 5] (based on your earlier code)
throughput_min, throughput_max = ax1.get_ylim()

# We want the twin axis to start at 0 at the same visual level as ax1's zero.
# To do this, we set the twin bottom so that 0 is at the same % height.
# Formula: twin_bottom = (throughput_min / throughput_max) * twin_max
twin_max = 1.0  # Since it's a ratio 0.0 to 1.0
twin_min = (throughput_min / throughput_max) * twin_max

ax1_twin.set_ylim(twin_min, twin_max)

# 5. Styling
ax1_twin.set_ylabel('Exploitation Ratio (Normalized)', color='black', fontsize=12)
ax1_twin.tick_params(axis='y', labelcolor='black')

# Update Legend to include the new line


# Legend Setup für Graph 1
marker_legend_elements = [
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='left'), color='w', 
           label='Futterquelle erstellt', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='right'), color='w', 
           label='Futterquelle gelöscht', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker='^', color='w', label=f'Durchsatz > {troughput_convergence}',
           markerfacecolor='gray', markersize=12, markeredgecolor='black'),
    Line2D([0], [0], marker='D', color='w', label='Resilienz erreicht',
           markerfacecolor='darkviolet', markersize=8, markeredgecolor='black'),
]


source_legend_elements = [Line2D([0], [0], color=colors[sid], lw=6, label=f'Futterquelle {int(sid)}') for sid in source_ids]

all_handles = marker_legend_elements + source_legend_elements + line_twin
ax1.legend(handles=all_handles, loc='upper left', bbox_to_anchor=(1.1, 1))
#ax1.legend(handles=marker_legend_elements + source_legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))

fig1.tight_layout()
fig1.savefig(out_source_png, bbox_inches='tight')
plt.close(fig1)

# ==========================================
# GRAPH 2: GLOBAL EFFICIENCY & DISAPPOINTMENT
# ==========================================
fig2, ax2 = plt.subplots(figsize=(16, 6))

ax2.plot(df_global['step'], df_global['avg_step_efficeny_to_food'], color='green', label='Pfadeffizienz zu Futterquellen', lw=2)
ax2.plot(df_global['step'], df_global['avg_step_efficeny_to_nest'], color='blue', label='Pfadeffizienz zurück zum Nest', lw=2)

ax2.set_ylim(0, 1.1) 
ax2.set_ylabel('Pfadeffizienz', fontsize=12)
ax2.set_xlabel('Simulations Schritt', fontsize=12)
ax2.set_title('Pfadeffizienz & Enttäuschungsrate', fontsize=16, pad=20)
ax2.legend(loc='upper left')
#ax2.set_xticks(xticks)
ax2.grid(True, alpha=0.3)

ax3 = ax2.twinx()
ax3.fill_between(df_global['step'], df_global['dissapointmentRate'], color='red', alpha=0.1)
ax3.plot(df_global['step'], df_global['dissapointmentRate'], color='red', linestyle='--', alpha=0.4, label='Disappointment')
ax3.set_ylabel('Enttäuschungsrate', color='red', fontsize=12)
ax3.tick_params(axis='y', labelcolor='red')

fig2.tight_layout()
fig2.savefig(out_global_png, bbox_inches='tight')
plt.close(fig2)


# ==========================================
# Berechnung Jain's Fairness Index
# 1. Berechne, wie viele Futterquellen zu jedem Zeitschritt AKTIV sind
active_counts = pd.Series(0, index=pivot_df.index)
for sid in source_ids:
    s_data = df_source[df_source['source_id'] == sid]
    c_step = s_data['creation_step'].max()
    d_step = s_data['deletion_step'].max()
    
    if c_step != -1:  # Quelle wurde erstellt
        mask = (pivot_df.index >= c_step)
        if d_step != -1:
            mask = mask & (pivot_df.index <= d_step)
        active_counts += mask.astype(int)

# 2. Jains Fairness Formel anwenden: (Summe(x))^2 / (n * Summe(x^2))
sum_tp = pivot_df.sum(axis=1)
sum_sq_tp = (pivot_df ** 2).sum(axis=1)

# Verhindern von Division durch Null (wo keine Quellen oder kein Durchsatz ist)
denominator = (active_counts * sum_sq_tp).replace(0, np.nan)
jains_index = (sum_tp ** 2) / denominator

# NaNs zu 0 umwandeln (falls zeitweise gar kein Durchsatz da ist)
jains_index = jains_index.fillna(0)


# ==========================================
# GRAPH 3: BOXPLOTS (Time to Throughput & Efficiency)
# ==========================================
fig3, (ax_box1, ax_box_rec, ax_box2, ax_box3, ax_box_jain) = plt.subplots(1, 5, figsize=(22, 6))

# --- 1. Schritte bis Durchsatz-Ziel (Convergence) ---
total_sources = len(source_ids)
converged_count = len(convergence_data_pairs)
failed_conv = total_sources - converged_count
conv_rate = (converged_count / total_sources * 100) if total_sources > 0 else 0

if convergence_data_pairs:
    # 1. Daten entpacken: sids ist eine Liste der IDs, steps eine Liste der Werte
    point_sids, point_steps = zip(*convergence_data_pairs)
    point_colors = [colors[sid] for sid in point_sids]
    x_coords = np.random.normal(1, 0.04, size=converged_count)
    ax_box1.scatter(x_coords, point_steps, alpha=0.7, edgecolors='black', 
                      color=point_colors, s=70, marker='^')
    ax_box1.hlines(np.median(point_steps), 0.8, 1.2, colors='black', linestyles='--', lw=2)

ax_box1.set_title(f'Zeit bis Durchsatz > {troughput_convergence} erreicht', fontsize=10)
ax_box1.set_ylabel('Schritte', fontsize=10)
ax_box1.set_xticks([1])
# Rotes Label für Convergence-Fehler
lbl_conv = ax_box1.set_xticklabels([f"Durchsatz nicht erreicht:\n{failed_conv}mal ({100-conv_rate:.1f}%)"])
plt.setp(lbl_conv, color='red', fontweight='bold', fontsize=9)
ax_box1.grid(axis='y', linestyle='--', alpha=0.3)

# --- 2. Time-to-Recovery ---
total_deletions = len(deletion_steps)
recovered_count = len(recovery_times)
failed_rec = total_deletions - recovered_count
rec_rate = (recovered_count / total_deletions * 100) if total_deletions > 0 else 0

if total_deletions > 0:
    if recovery_times:
        x_jitter = np.random.normal(1, 0.05, size=len(recovery_times))
        ax_box_rec.scatter(x_jitter, recovery_times, color='darkviolet', s=60, marker='D', edgecolors='black', alpha=0.7)
        ax_box_rec.hlines(np.median(recovery_times), 0.8, 1.2, colors='black', linestyles='--', lw=2)
    
    ax_box_rec.set_title('Erholungszeit', fontsize=10)
    ax_box_rec.set_ylabel('Schritte nach Einbruch', fontsize=10)
    ax_box_rec.set_xticks([1])
    # Rotes Label für Recovery-Fehler
    lbl_rec = ax_box_rec.set_xticklabels([f"Nicht regeneriert:\n{failed_rec} ({100-rec_rate:.1f}%)"])
    plt.setp(lbl_rec, color='red', fontweight='bold', fontsize=9)

# --- 3. Pfadeffizienz (unverändert) ---
eff_food = df_global['avg_step_efficeny_to_food'].dropna()
eff_nest = df_global['avg_step_efficeny_to_nest'].dropna()
if not eff_food.empty:
    bp2 = ax_box2.boxplot([eff_food, eff_nest], patch_artist=True, tick_labels=['Futter', 'Nest'], widths=0.4)
    for patch, color in zip(bp2['boxes'], ['green', 'blue']):
        patch.set(facecolor=color, alpha=0.5)
    ax_box2.set_title('Ø Pfadeffizienz', fontsize=10)
    ax_box2.set_ylim(-0.05, 1.05)
    ax_box2.grid(axis='y', linestyle='--', alpha=0.3)

# --- 4. Gesamt-Durchsatz (unverändert) ---
bp4 = ax_box3.boxplot(global_throughput, patch_artist=True, widths=0.4)
for box in bp4['boxes']:
    box.set(facecolor='gray', alpha=0.5)
ax_box3.set_title('Ø Gesamt-Durchsatz', fontsize=10)
ax_box3.set_xticklabels([''])
ax_box3.grid(axis='y', linestyle='--', alpha=0.3)

# --- 5. Jain's Fairness Index (unverändert) ---
bp5 = ax_box_jain.boxplot(jains_index, patch_artist=True, widths=0.4)
for box in bp5['boxes']:
    box.set(facecolor='gold', alpha=0.5)
ax_box_jain.set_title("Jain's Fairness Index", fontsize=10)
ax_box_jain.set_ylim(-0.05, 1.05)
ax_box_jain.set_xticklabels([''])
ax_box_jain.grid(axis='y', linestyle='--', alpha=0.3)

fig3.tight_layout()
plt.subplots_adjust(wspace=0.4, bottom=0.2) # Mehr Platz unten für die roten Texte
fig3.savefig(out_boxplots_png, bbox_inches='tight')
plt.close(fig3)


# ==========================================
# 4. Finish
# ==========================================
print("Graphs successfully split and saved to:")
print(f"1: {out_source_png}")
print(f"2: {out_global_png}")
print(f"3: {out_boxplots_png}")

# ==========================================
# 5. Save Extended Numerical Metrics to File
# ==========================================
out_metrics_csv = os.path.join(base_dir, "performance_summary.csv")

def get_stats(data_list):
    data = np.array(data_list)
    if data.size == 0:
        return [np.nan] * 5 # Jetzt 5 Werte
    data = data[~pd.isna(data)]
    if data.size == 0:
        return [np.nan] * 5
        
    return [np.mean(data), np.std(data), np.min(data), np.max(data), np.median(data)]
# Stats berechnen
# Stats berechnen (liefert jetzt 5 Werte)
_, steps_to_reach_convergence_list = zip(*convergence_data_pairs)

stats_conv  = get_stats(steps_to_reach_convergence_list)
stats_rec   = get_stats(recovery_times)
stats_tp    = get_stats(global_throughput)
stats_eff_f = get_stats(eff_food)
stats_eff_n = get_stats(eff_nest)
stats_jain  = get_stats(jains_index)

metrics_summary = {
    "Metric": ["Convergence_Steps", "Recovery_Steps", "Global_Throughput", 
               "Efficiency_Food", "Efficiency_Nest", "Jains_Fairness_Index"],
    "Mean":   [stats_conv[0], stats_rec[0], stats_tp[0], stats_eff_f[0], stats_eff_n[0], stats_jain[0]],
    "Median": [stats_conv[4], stats_rec[4], stats_tp[4], stats_eff_f[4], stats_eff_n[4], stats_jain[4]], # NEU
    "Std_Dev":[stats_conv[1], stats_rec[1], stats_tp[1], stats_eff_f[1], stats_eff_n[1], stats_jain[1]],
    "Min":    [stats_conv[2], stats_rec[2], stats_tp[2], stats_eff_f[2], stats_eff_n[2], stats_jain[2]],
    "Max":    [stats_conv[3], stats_rec[3], stats_tp[3], stats_eff_f[3], stats_eff_n[3], stats_jain[3]]
}

df_summary = pd.DataFrame(metrics_summary)

# Raten anhängen (mit NaN für den Median-Platzhalter)
df_summary.loc[len(df_summary)] = ["Convergence_Rate_Pct", conv_rate, np.nan, np.nan, np.nan, np.nan]
df_summary.loc[len(df_summary)] = ["Recovery_Rate_Pct", rec_rate, np.nan, np.nan, np.nan, np.nan]


# Run_ID einfügen und speichern
df_summary.insert(0, "Run_ID", run_id)
df_summary.to_csv(out_metrics_csv, index=False)


print("\n" + "="*80)
print(f" PERFORMANCE SUMMARY - RUN: {run_id}")
print("="*80)
print(df_summary.drop(columns=["Run_ID"]).to_string(index=False, justify='center', float_format=lambda x: f"{x:8.2f}"))
print("="*80)
print(f"Datei gespeichert: {out_metrics_csv}\n")