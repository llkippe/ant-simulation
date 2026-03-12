import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.markers as mmarkers
import sys
import os
import numpy as np


troughput_convergence = 0.8
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

pivot_df = df_source.pivot(index='step', columns='source_id', values='throughput').fillna(0)
source_ids = sorted(pivot_df.columns)

cmap = plt.get_cmap('tab10')
colors = {sid: cmap(i % 10) for i, sid in enumerate(source_ids)}

max_step = df_source['step'].max()
xticks = np.arange(0, max_step+100, 1000)

# Liste zum Sammeln der Daten für den Boxplot später
steps_to_reach_convergence_list = []

# ==========================================
# GRAPH 1: SOURCE THROUGHPUT
# ==========================================
fig1, ax1 = plt.subplots(figsize=(16, 8))



ax1.stackplot(pivot_df.index, pivot_df.values.T, 
             labels=[f'Source {int(sid)}' for sid in source_ids], 
             colors=[colors[sid] for sid in source_ids], alpha=0.7)

# Neue Werte für Marker-Positionen
marker_y_start = -1  # Reduziert den Startpunkt
marker_spacing = 1   # Reduziert den Abstand zwischen den Markern

# Liste zum Sammeln der Daten für den Boxplot später
steps_to_reach_convergence_list = []

for i, sid in enumerate(source_ids):
    source_data = df_source[df_source['source_id'] == sid]
    color = colors[sid]
    y_pos = marker_y_start - (i * marker_spacing)

    # Marker: Creation
    creation_step = source_data['creation_step'].max()
    if creation_step != -1:
        ax1.scatter(creation_step, y_pos, color=color, s=150,
                    marker=mmarkers.MarkerStyle('o', fillstyle='left'),
                    edgecolors='black', zorder=10)

    # Marker: Deletion
    deletion_step = source_data['deletion_step'].max()
    if deletion_step != -1:
        ax1.scatter(deletion_step, y_pos, color=color, s=150,
                    marker=mmarkers.MarkerStyle('o', fillstyle='right'),
                    edgecolors='black', zorder=10)

    # Throughput > 50 Score Calculation
    over_convergence = source_data[source_data['throughput'] > troughput_convergence]
    if creation_step != -1 and not over_convergence.empty:
        first_step_over_convergence = over_convergence['step'].min()
        steps_to_reach_convergence = first_step_over_convergence - creation_step
        steps_to_reach_convergence_list.append(steps_to_reach_convergence)

        ax1.scatter(first_step_over_convergence, y_pos, color=color, s=180, marker='^',
                    edgecolors='black', zorder=10)

# Anpassung der unteren y-Achsenbegrenzungen
lowest_y = marker_y_start - (len(source_ids) * marker_spacing)
ax1.set_ylim(bottom=lowest_y) 

yticks = np.arange(len(source_ids) * -1, 6, 1)
ax1.set_yticks(yticks)



ax1.set_xticks(xticks)


ax1.set_xlabel('Simulations Schritt', fontsize=12)
ax1.set_ylabel('Durchsatz & Simulations Events', fontsize=12)
ax1.set_title('Futterqullendurchsatz pro Zeitschritt', fontsize=16, pad=10)
ax1.grid(axis='y', linestyle='--', alpha=0.3)

# Legend Setup für Graph 1
marker_legend_elements = [
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='left'), color='w', 
           label='Futterquelle erstellt', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='right'), color='w', 
           label='Futterquelle gelöscht', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker='^', color='w', label=f'Durchsatz > {troughput_convergence}',
           markerfacecolor='gray', markersize=12, markeredgecolor='black'),
]
source_legend_elements = [Line2D([0], [0], color=colors[sid], lw=6, label=f'Futterquelle {int(sid)}') for sid in source_ids]
ax1.legend(handles=marker_legend_elements + source_legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))

fig1.tight_layout()
fig1.savefig(out_source_png, bbox_inches='tight')
plt.close(fig1)

# ==========================================
# GRAPH 2: GLOBAL EFFICIENCY & DISAPPOINTMENT
# ==========================================
fig2, ax2 = plt.subplots(figsize=(16, 6))

ax2.plot(df_global['step'], df_global['avg_step_efficeny_to_food'], color='green', label='Pfadeffizienz zu Futterquellen', lw=2.5)
ax2.plot(df_global['step'], df_global['avg_step_efficeny_to_nest'], color='blue', label='Pfadeffizienz zurück zum Nest', lw=2.5)

ax2.set_ylim(0, 1.1) 
ax2.set_ylabel('Pfadeffizienz', fontsize=12)
ax2.set_xlabel('Simulations Schritt', fontsize=12)
ax2.set_title('Pfadeffizienz & Enttäuschungsrate', fontsize=16, pad=20)
ax2.legend(loc='upper left')
ax2.set_xticks(xticks)
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
# GRAPH 3: BOXPLOTS (Time to Throughput & Efficiency)
# ==========================================
# Wir nutzen 1 Reihe, 2 Spalten, damit die Skalierungen nicht kaputt gehen
fig3, (ax_box1, ax_box2) = plt.subplots(1, 2, figsize=(7, 4))


# --- Linker Boxplot: Steps to reach 50 Throughput ---
if steps_to_reach_convergence_list: # Check if there is data
    bp1 = ax_box1.boxplot(steps_to_reach_convergence_list, patch_artist=True, widths=0.4)
    # Style the box
    for box in bp1['boxes']:
        box.set(facecolor='orange', alpha=0.7)
    
    ax_box1.set_title(f'Durchschnittliche Schritte bis Durchsatz > {troughput_convergence}', fontsize=10)
    ax_box1.set_ylabel('Schritte', fontsize=12)
    ax_box1.set_xticks([1])
    ax_box1.set_xticklabels(['Alle Futterquellen'])
    ax_box1.grid(axis='y', linestyle='--', alpha=0.5)

# --- Rechter Boxplot: Average Efficiency ---
# Wir werfen NaN werte raus, falls es Lücken in der Simulation gibt
eff_food = df_global['avg_step_efficeny_to_food'].dropna()
eff_nest = df_global['avg_step_efficeny_to_nest'].dropna()

bp2 = ax_box2.boxplot([eff_food, eff_nest], patch_artist=True, labels=['Zu Futterquellen', 'Zum Nest'], widths=0.4)

# Style the boxes (Green for Food, Blue for Nest)
colors_box = ['green', 'blue']
for patch, color in zip(bp2['boxes'], colors_box):
    patch.set(facecolor=color, alpha=0.5)

ax_box2.set_title('Durchschnittliche Pfadeffizienz', fontsize=10)
ax_box2.set_ylabel('Effizienz der Pfadlänge [∅] (0.0 - 1.0)', fontsize=10)
ax_box2.set_ylim(-0.05, 1.05)
ax_box2.grid(axis='y', linestyle='--', alpha=0.5)

fig3.tight_layout()
plt.subplots_adjust(wspace=0.4) 
fig3.savefig(out_boxplots_png, bbox_inches='tight')
plt.close(fig3)

# ==========================================
# 4. Finish
# ==========================================
print("Graphs successfully split and saved to:")
print(f"1: {out_source_png}")
print(f"2: {out_global_png}")
print(f"3: {out_boxplots_png}")