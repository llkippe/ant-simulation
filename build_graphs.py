import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.markers as mmarkers
import sys
import os

# 1. Handle Input Argument
if len(sys.argv) < 2:
    print("Usage: python3 build_graphs.py <run_number>")
    sys.exit(1)

run_id = sys.argv[1]
base_dir = f"data/{run_id}"
csv_source = os.path.join(base_dir, "source_metrics.csv")
csv_global = os.path.join(base_dir, "global_metrics.csv")
output_path = os.path.join(base_dir, "simulation_analysis.png")

if not os.path.exists(csv_source) or not os.path.exists(csv_global):
    print(f"Error: Missing CSV files in {base_dir}")
    sys.exit(1)

# 2. Load Data
df_source = pd.read_csv(csv_source)
df_global = pd.read_csv(csv_global)

pivot_df = df_source.pivot(index='step', columns='source_id', values='throughput').fillna(0)
source_ids = sorted(pivot_df.columns)

# 3. Setup Colors
cmap = plt.get_cmap('tab10')
colors = {sid: cmap(i % 10) for i, sid in enumerate(source_ids)}

# 4. Initialize Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 14), sharex=True)

# Show X-axis labels on the top plot too
ax1.tick_params(labelbottom=True)

# === UPPER PLOT: SOURCE THROUGHPUT ===
ax1.stackplot(pivot_df.index, pivot_df.values.T, 
             labels=[f'Source {int(sid)}' for sid in source_ids], 
             colors=[colors[sid] for sid in source_ids], alpha=0.7)

# Increased spacing and vertical breathing room for markers
marker_y_start = -40 
marker_spacing = 25  

for i, sid in enumerate(source_ids):
    source_data = df_source[df_source['source_id'] == sid]
    color = colors[sid]
    y_pos = marker_y_start - (i * marker_spacing)
    
    # Add a subtle "lane" line for each source
    ax1.axhline(y_pos, color='gray', linestyle=':', alpha=0.2, zorder=0)
    
    # --- Marker: Creation Step (Half-circle left) ---
    creation_step = source_data['creation_step'].max()
    if creation_step != -1:
        ax1.scatter(creation_step, y_pos, color=color, s=150, 
                    marker=mmarkers.MarkerStyle('o', fillstyle='left'), 
                    edgecolors='black', zorder=10)

    # --- Marker: Deletion Step (Half-circle right) ---
    deletion_step = source_data['deletion_step'].max()
    if deletion_step != -1:
        ax1.scatter(deletion_step, y_pos, color=color, s=150, 
                    marker=mmarkers.MarkerStyle('o', fillstyle='right'), 
                    edgecolors='black', zorder=10)

    # --- RESTORED: Marker: Throughput > 50 (Triangle) ---
    over_50 = source_data[source_data['throughput'] > 50]
    if not over_50.empty:
        first_step_over_50 = over_50['step'].min()
        ax1.scatter(first_step_over_50, y_pos, color=color, s=180, marker='^', 
                    edgecolors='black', zorder=10)

# Adjust y-axis to fit markers without being cramped
lowest_y = marker_y_start - (len(source_ids) * marker_spacing) - 20
ax1.set_ylim(bottom=lowest_y)
ax1.set_ylabel('Throughput / Event Tracks', fontsize=12)
ax1.set_title('Ant Simulation Performance Metrics', fontsize=16, pad=20)
ax1.grid(axis='y', linestyle='--', alpha=0.3)

# === LOWER PLOT: GLOBAL EFFICIENCY & DISAPPOINTMENT ===
# Plot Efficiency (Assuming Java update for 0.0 - 1.0 range)
ax2.plot(df_global['step'], df_global['avg_step_efficeny_to_food'], color='green', label='Efficiency to Food', lw=2.5)
ax2.plot(df_global['step'], df_global['avg_step_efficeny_to_nest'], color='blue', label='Efficiency to Nest', lw=2.5)

ax2.set_ylim(0, 1.1) # Set fixed scale for efficiency
ax2.set_ylabel('Efficiency Ratio (1.0 = Linear)', fontsize=12)
ax2.set_xlabel('Simulation Step', fontsize=12)
ax2.legend(loc='upper left')
ax2.grid(True, alpha=0.3)

# Secondary Y-axis for Disappointment
ax3 = ax2.twinx()
ax3.fill_between(df_global['step'], df_global['dissapointmentRate'], color='red', alpha=0.1)
ax3.plot(df_global['step'], df_global['dissapointmentRate'], color='red', linestyle='--', alpha=0.4, label='Disappointment')
ax3.set_ylabel('Disappointment Rate', color='red', fontsize=12)
ax3.tick_params(axis='y', labelcolor='red')

# === LEGEND CONSTRUCTION ===
marker_legend_elements = [
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='left'), color='w', 
           label='Source Created', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='right'), color='w', 
           label='Source Deleted', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker='^', color='w', label='Throughput > 50',
           markerfacecolor='gray', markersize=12, markeredgecolor='black'),
]
source_legend_elements = [Line2D([0], [0], color=colors[sid], lw=6, label=f'Source {int(sid)}') for sid in source_ids]

ax1.legend(handles=marker_legend_elements + source_legend_elements, 
          loc='upper left', bbox_to_anchor=(1.02, 1), title="Legend & Sources")

plt.tight_layout()
plt.savefig(output_path, bbox_inches='tight')
print(f"Graph successfully saved to: {output_path}")