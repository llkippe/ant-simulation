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
csv_path = os.path.join(base_dir, "source_metrics.csv")
output_path = os.path.join(base_dir, "throughput_chart.png")

# Check if the file exists before proceeding
if not os.path.exists(csv_path):
    print(f"Error: File not found at {csv_path}")
    sys.exit(1)

# 2. Load Data
df = pd.read_csv(csv_path)

# 2. Prepare Data for Stackplot
pivot_df = df.pivot(index='step', columns='source_id', values='throughput').fillna(0)
source_ids = sorted(pivot_df.columns)

# 3. Setup Colors
cmap = plt.get_cmap('tab10')
colors = {sid: cmap(i % 10) for i, sid in enumerate(source_ids)}

# 4. Initialize Plot
plt.figure(figsize=(15, 8))
ax = plt.gca()

# 5. Create the Stackplot
ax.stackplot(pivot_df.index, pivot_df.values.T, 
             labels=[f'Source {int(sid)}' for sid in source_ids], 
             colors=[colors[sid] for sid in source_ids], alpha=0.7)

# 6. Add Event Markers with Vertical Tracks to avoid overlap
marker_y_start = -20
marker_spacing = 13

for i, sid in enumerate(source_ids):
    source_data = df[df['source_id'] == sid]
    color = colors[sid]
    # Each source gets its own Y-row below the zero line
    y_pos = marker_y_start - (i * marker_spacing)
    
    # --- Marker: Creation Step (Half-circle open to right) ---
    creation_step = source_data['creation_step'].max()
    if creation_step != -1:
        m = mmarkers.MarkerStyle('o', fillstyle='left')
        ax.scatter(creation_step, y_pos, color=color, s=120, marker=m, 
                    edgecolors='black', label='_nolegend_', zorder=10)

    # --- Marker: Deletion Step (Half-circle open to left) ---
    deletion_step = source_data['deletion_step'].max()
    if deletion_step != -1:
        m = mmarkers.MarkerStyle('o', fillstyle='right')
        ax.scatter(deletion_step, y_pos, color=color, s=120, marker=m, 
                    edgecolors='black', label='_nolegend_', zorder=10)

    # --- Marker: Throughput > 50 (Triangle) ---
    over_50 = source_data[source_data['throughput'] > 50]
    if not over_50.empty:
        first_step_over_50 = over_50['step'].min()
        ax.scatter(first_step_over_50, y_pos, color=color, s=140, marker='^', 
                    edgecolors='black', label='_nolegend_', zorder=10)

# 7. Custom Legend Explanation
marker_legend_elements = [
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='left'), color='w', 
           label='Source Created', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='right'), color='w', 
           label='Source Deleted', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker='^', color='w', label='Throughput > 50',
           markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], color='none', label=''), # Spacer
]

source_legend_elements = [
    Line2D([0], [0], color=colors[sid], lw=6, label=f'Source {int(sid)}') for sid in source_ids
]

ax.legend(handles=marker_legend_elements + source_legend_elements, 
          loc='upper left', bbox_to_anchor=(1.02, 1), 
          title="Legend & Source IDs")

# 8. Formatting
plt.title('Source Throughput with Event Markers', fontsize=16, pad=20)
plt.xlabel('Simulation Step', fontsize=12)
plt.ylabel('Throughput', fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.3)

# Adjust y-axis range to fit the staggered markers
lowest_y = marker_y_start - (len(source_ids) * marker_spacing) - 10
plt.ylim(bottom=lowest_y)

plt.tight_layout()
plt.savefig(output_path)
print(f"Graph successfully saved to: {output_path}")