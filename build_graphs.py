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

# ==========================================
# CONVERGENCE TRACKING PARAMETERS
# ==========================================
convergence_throughput_threshold = 0.4
convergence_evaluation_steps = 200
convergence_window_size = int(convergence_evaluation_steps / df_settings['reportingInterval'].iloc[0])
convergence_data_pairs = []

# ==========================================
# RECOVERY TRACKING PARAMETERS & DATA
# ==========================================
global_throughput = pivot_df.sum(axis=1)
all_deletion_steps = df_source[df_source['deletion_step'] != -1]['deletion_step'].unique()

# Thresholds and timing for recovery tracking
inactive_food_source_threshold = 0.05  # Throughput below this = source considered "inactive"
recovery_target_ratio = 0.9  # Must reach this ratio of pre-deletion throughput
recovery_stability_steps = 400  # Minimum steps to confirm stable recovery
pre_deletion_averaging_steps = 400  # Steps before deletion to calculate baseline throughput
max_recovery_time_steps = int(df_settings['FOOD_SPAWN_INTERVALL'].iloc[0] * 2)  # Max steps after deletion to find recovery

# Data structures for recovery analysis
recovery_events = []  # For charting: (recovery_step, throughput_value, deletion_step)
recovery_times = []  # For statistics: time deltas from deletion to recovery
active_deletion_events = []  # Deletions from sources that were actually active





# ==========================================
# GRAPH 1: SOURCE THROUGHPUT + SOURCE EVENTS (SEPARAT)
# ==========================================
fig1, (ax_tp, ax_markers) = plt.subplots(2, 1, figsize=(16, 9), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

ax_tp.stackplot(pivot_df.index, pivot_df.values.T,
                labels=[f'Quelle {int(sid)}' for sid in source_ids],
                colors=[colors[sid] for sid in source_ids], alpha=0.7)

ax_tp.set_ylabel('Durchsatz')
ax_tp.set_title('Futterquellendurchsatz (gestapelt)')
ax_tp.legend(loc='upper left', fontsize='small')
ax_tp.grid(axis='y', linestyle='--', alpha=0.3)

# Neue Werte für Marker-Positionen
marker_y_start = (len(source_ids) - 1) * 1.5
marker_spacing = 1.5   # Erhöht den Abstand, um Überlappung zu vermeiden


min_stability_points_required = recovery_stability_steps / df_settings['reportingInterval'].iloc[0]

# ==========================================
# RECOVERY ANALYSIS: Find active deletions and track recovery
# ==========================================

for source_deletion_step in all_deletion_steps:
    # Get source data to check if it was actually active before deletion
    source_data_at_deletion = df_source[df_source['deletion_step'] == source_deletion_step]
    
    if source_data_at_deletion.empty:
        continue
    
    # Get the throughput of this source just before deletion
    source_id = source_data_at_deletion['source_id'].iloc[0]
    source_throughput_data = df_source[df_source['source_id'] == source_id].sort_values('step')
    
    # Find throughput just before deletion (last available point)
    pre_deletion_source_throughput = source_throughput_data[source_throughput_data['step'] < source_deletion_step]
    if pre_deletion_source_throughput.empty:
        continue
    
    source_throughput_at_deletion = pre_deletion_source_throughput['throughput'].iloc[-1]
    
    # *** ONLY TRACK RECOVERY IF SOURCE WAS ACTUALLY ACTIVE ***
    if source_throughput_at_deletion < inactive_food_source_threshold:
        continue  # Skip inactive sources completely
    
    # Source was active - add to tracking list
    active_deletion_events.append({
        'deletion_step': source_deletion_step,
        'source_id': source_id,
        'source_throughput_at_deletion': source_throughput_at_deletion
    })
    
    # Calculate target throughput: 90% of pre-deletion global average
    pre_deletion_global_data = global_throughput[
        (global_throughput.index >= source_deletion_step - pre_deletion_averaging_steps) & 
        (global_throughput.index < source_deletion_step)
    ]
    
    if pre_deletion_global_data.empty:
        continue
    
    target_throughput = pre_deletion_global_data.mean() * recovery_target_ratio
    
    # Find when the deleted source becomes inactive (throughput falls below threshold)
    source_post_deletion = source_throughput_data[source_throughput_data['step'] > source_deletion_step]
    
    source_becomes_inactive_step = None
    for _, row in source_post_deletion.iterrows():
        if row['throughput'] < inactive_food_source_threshold:
            source_becomes_inactive_step = row['step']
            break
    
    # If source never became inactive in recorded data, we can't determine recovery
    if source_becomes_inactive_step is None:
        continue
    
    # Now search for recovery starting from when the source became inactive
    recovery_search_start = source_becomes_inactive_step
    recovery_search_end = source_deletion_step + max_recovery_time_steps
    
    recovery_data = global_throughput[
        (global_throughput.index >= recovery_search_start) & 
        (global_throughput.index <= recovery_search_end)
    ]
    
    if recovery_data.empty:
        continue
    
    # Look for first point where global throughput reaches target
    recovery_step_found = None
    for step, throughput_value in recovery_data.items():
        if throughput_value >= target_throughput:
            # Verify stability: check if it stays above target for required window
            stability_window = global_throughput[
                (global_throughput.index >= step) & 
                (global_throughput.index <= step + recovery_stability_steps)
            ]
            
            if len(stability_window) >= min_stability_points_required:
                if stability_window.mean() >= target_throughput:
                    recovery_step_found = step
                    recovery_time = step - source_deletion_step
                    recovery_events.append((recovery_step_found, throughput_value, source_deletion_step))
                    recovery_times.append(recovery_time)
                    break



for i, source_id in enumerate(source_ids):
    # Ensure data is sorted by step for rolling() to work correctly
    source_data = df_source[df_source['source_id'] == source_id].sort_values('step')
    
    color = colors[source_id]
    y_pos = marker_y_start - (i * marker_spacing)

    # Marker: Source Creation
    source_creation_step = source_data['creation_step'].max()
    if source_creation_step != -1:
        ax_markers.scatter(source_creation_step, y_pos, color=color, s=120,
                    marker=mmarkers.MarkerStyle('o', fillstyle='left'),
                    edgecolors='black', zorder=10)

    # Marker: Source Deletion
    source_deletion_step = source_data['deletion_step'].max()
    if source_deletion_step != -1:
        ax_markers.scatter(source_deletion_step, y_pos, color=color, s=130,
                    marker=mmarkers.MarkerStyle('o', fillstyle='right'),
                    edgecolors='black', zorder=10)
    

    # --- CONVERGENCE TRACKING (Rolling Average) ---
    # Calculate rolling average over convergence_evaluation_steps
    # min_periods ensures output only starts after enough data points
    rolling_avg = source_data['throughput'].rolling(
        window=convergence_window_size, 
        min_periods=convergence_window_size
    ).mean()

    # Find where rolling average exceeds convergence threshold
    above_convergence_threshold = source_data[rolling_avg > convergence_throughput_threshold]
    
    if source_creation_step != -1 and not above_convergence_threshold.empty:
        # First step where rolling average exceeds threshold (marks end of evaluation window)
        first_step_above_threshold = above_convergence_threshold['step'].min()
        steps_to_reach_convergence = first_step_above_threshold - source_creation_step
        
        convergence_data_pairs.append((source_id, steps_to_reach_convergence))

        ax_markers.scatter(first_step_above_threshold, y_pos, color=color, s=110, marker='^',
                    edgecolors='black', zorder=10)
        
if recovery_events:
    r_steps, r_values, r_del_steps = zip(*recovery_events)
    ax_tp.scatter(r_steps, r_values, color='darkviolet', s=90, marker='D', 
                edgecolors='black', label='Resilienz erreicht', zorder=20)
    for step, del_step, value in zip(r_steps, r_del_steps, r_values):
        ax_tp.text(
            step, value + 0.05,
            f"{del_step}",
            fontsize=9,
            ha='center',
            va='bottom',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, boxstyle='round,pad=0.1')
        )
    
    ax_tp.legend(loc='upper left', fontsize='small')


# Marker-Panel konfigurieren
ax_markers.set_ylim(-1, marker_y_start + 2)
ax_markers.set_yticks([i * 1.5 for i in range(len(source_ids))])
ax_markers.set_yticklabels([f'Quelle {int(sid)}' for sid in source_ids][::-1])
ax_markers.set_xlabel('Simulations-Schritt', fontsize=12)
ax_markers.set_ylabel('Lifecycle-Ereignisse', fontsize=12)
ax_markers.set_title('Lifecycle-Ereignisse', fontsize=12)
ax_markers.grid(axis='y', linestyle='--', alpha=0.3)

# Durchsatz-Panel xticks y axis
max_step = df_source['step'].max()
tick_spacing = max(1000, (max_step // 10))
# Rundet auf das nächste Tausender
tick_spacing = (tick_spacing // 1000) * 1000

xticks = np.arange(0, max_step + tick_spacing, tick_spacing)
ax_tp.set_xticks(xticks)
ax_markers.set_xticks(xticks)
ax_tp.set_xticklabels([str(int(x)) for x in xticks], rotation=0)
ax_markers.set_xticklabels([str(int(x)) for x in xticks], rotation=0)

# Beide Achsen unten beschriften
ax_tp.tick_params(axis='x', labelbottom=True)
ax_markers.tick_params(axis='x', labelbottom=True)

ax_tp.set_xlabel('Simulations-Schritt', fontsize=12)
ax_markers.set_xlabel('Simulations-Schritt', fontsize=12)
ax_tp.set_ylabel('Durchsatz', fontsize=12)
ax_tp.set_title('Futterquellendurchsatz pro Zeitschritt', fontsize=16, pad=10)
ax_tp.grid(axis='y', linestyle='--', alpha=0.3)
ax_markers.grid(axis='y', linestyle='--', alpha=0.3)

# exploration / explotation index

total_ants = df_settings['totalAnts'].iloc[0]
ee_ratio = df_global['exploitingAntsCount'] / total_ants

ax_tp_twin = ax_tp.twinx()

# Plotting the line
two_line = ax_tp_twin.plot(df_global['step'], ee_ratio, color='black', 
                          linewidth=2, linestyle=':', label='Ausbeutungsrate')

# ax_tp current range
throughput_min, throughput_max = ax_tp.get_ylim()

# Normalize twin axis so 0 is aligned
if throughput_max > 0:
    twin_max = 1.0
    twin_min = (throughput_min / throughput_max) * twin_max
else:
    twin_min, twin_max = 0.0, 1.0

ax_tp_twin.set_ylim(twin_min, twin_max)

ax_tp_twin.set_ylabel('Ausbeutungsrate (Normalisiert)', color='black', fontsize=12)
ax_tp_twin.tick_params(axis='y', labelcolor='black')

# Legend Setup für Graph 1
marker_legend_elements = [
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='left'), color='w', 
           label='Futterquelle erstellt', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker=mmarkers.MarkerStyle('o', fillstyle='right'), color='w', 
           label='Futterquelle gelöscht', markerfacecolor='gray', markersize=10, markeredgecolor='black'),
    Line2D([0], [0], marker='^', color='w', label=f'Durchsatz > {convergence_throughput_threshold}',
           markerfacecolor='gray', markersize=12, markeredgecolor='black'),
    Line2D([0], [0], marker='D', color='w', label='Erholung erreicht',
           markerfacecolor='darkviolet', markersize=8, markeredgecolor='black'),
]


source_legend_elements = [Line2D([0], [0], color=colors[sid], lw=6, label=f'Futterquelle {int(sid)}') for sid in source_ids]

all_handles = marker_legend_elements + source_legend_elements + two_line
ax_tp.legend(handles=all_handles, loc='upper left', bbox_to_anchor=(1.1, 1))
#ax_tp.legend(handles=marker_legend_elements + source_legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))

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
# CALCULATION OF JAIN'S FAIRNESS INDEX
# ==========================================
# Count how many food sources are active at each simulation step
active_source_counts = pd.Series(0, index=pivot_df.index)
for source_id in source_ids:
    source_data = df_source[df_source['source_id'] == source_id]
    source_creation_step = source_data['creation_step'].max()
    source_deletion_step = source_data['deletion_step'].max()
    
    if source_creation_step != -1:  # Source was created
        active_mask = (pivot_df.index >= source_creation_step)
        if source_deletion_step != -1:
            active_mask = active_mask & (pivot_df.index <= source_deletion_step)
        active_source_counts += active_mask.astype(int)

# Apply Jain's Fairness Formula: (Sum(x))^2 / (n * Sum(x^2))
sum_throughput = pivot_df.sum(axis=1)
sum_throughput_squared = (pivot_df ** 2).sum(axis=1)

# Prevent division by zero (where no sources or no throughput)
denominator = (active_source_counts * sum_throughput_squared).replace(0, np.nan)
jains_index = (sum_throughput ** 2) / denominator

# Convert NaNs to 0 (where there's temporarily no throughput)
jains_index = jains_index.fillna(0)


# ==========================================
# GRAPH 3: BOXPLOTS (Time to Throughput & Efficiency)
# ==========================================
fig3, (ax_box1, ax_box_rec, ax_box3, ax_box2 , ax_box_jain) = plt.subplots(1, 5, figsize=(22, 6))

# --- 1. Schritte bis Durchsatz-Ziel (Convergence) ---
total_sources = len(source_ids)
converged_count = len(convergence_data_pairs)
failed_conv = total_sources - converged_count
conv_rate = (converged_count / total_sources * 100) if total_sources > 0 else 0

if convergence_data_pairs:
    # Unpack data: source_ids and steps to convergence
    source_ids_converged, steps_to_convergence = zip(*convergence_data_pairs)
    point_colors = [colors[sid] for sid in source_ids_converged]
    x_coords = np.random.normal(1, 0.04, size=converged_count)
    ax_box1.scatter(x_coords, steps_to_convergence, alpha=0.7, edgecolors='black', 
                      color=point_colors, s=70, marker='^')
    ax_box1.hlines(np.median(steps_to_convergence), 0.8, 1.2, colors='black', linestyles='--', lw=2)

ax_box1.set_title(f'Schritte bis Durchsatz > {convergence_throughput_threshold} erreicht', fontsize=10)
ax_box1.set_ylabel('Schritte nach Erstellung', fontsize=10)
ax_box1.set_xticks([1])
# Rotes Label für Convergence-Fehler
lbl_conv = ax_box1.set_xticklabels([f"Durchsatz nicht erreicht:\n{failed_conv} mal ({100-conv_rate:.1f}%)"])
plt.setp(lbl_conv, color='red', fontweight='bold', fontsize=9)
ax_box1.grid(axis='y', linestyle='--', alpha=0.3)

# --- 2. Time-to-Recovery ---
total_active_deletions = len(active_deletion_events)
recovered_count = len(recovery_times)
failed_rec = total_active_deletions - recovered_count
rec_rate = (recovered_count / total_active_deletions * 100) if total_active_deletions > 0 else 0

if total_active_deletions > 0:
    if recovery_times:
        x_jitter = np.random.normal(1, 0.05, size=len(recovery_times))
        ax_box_rec.scatter(x_jitter, recovery_times, color='darkviolet', s=60, marker='D', edgecolors='black', alpha=0.7)
        ax_box_rec.hlines(np.median(recovery_times), 0.8, 1.2, colors='black', linestyles='--', lw=2)
    
    ax_box_rec.set_title('Erholungszeit', fontsize=10)
    ax_box_rec.set_ylabel('Schritte nach Einbruch', fontsize=10)
    ax_box_rec.set_xticks([1])
    # Rotes Label für Recovery-Fehler
    lbl_rec = ax_box_rec.set_xticklabels([f"Nicht regeneriert:\n{failed_rec} mal ({100-rec_rate:.1f}%)"])
    plt.setp(lbl_rec, color='red', fontweight='bold', fontsize=9)

# --- 3. Path Efficiency ---
efficiency_to_food = df_global['avg_step_efficeny_to_food'].dropna()
efficiency_to_nest = df_global['avg_step_efficeny_to_nest'].dropna()
if not efficiency_to_food.empty:
    bp2 = ax_box2.boxplot([efficiency_to_food, efficiency_to_nest], patch_artist=True, tick_labels=['Futter', 'Nest'], widths=0.4)
    for patch, color in zip(bp2['boxes'], ['green', 'blue']):
        patch.set(facecolor=color, alpha=0.5)
    ax_box2.set_title('Ø Pfadeffizienz', fontsize=10)
    ax_box2.set_ylim(-0.05, 1.05)
    ax_box2.grid(axis='y', linestyle='--', alpha=0.3)

# --- 4. Global Throughput ---
bp4 = ax_box3.boxplot(global_throughput, patch_artist=True, widths=0.4)
for box in bp4['boxes']:
    box.set(facecolor='gray', alpha=0.5)
ax_box3.set_title('Ø Gesamt-Durchsatz', fontsize=10)
ax_box3.set_xticklabels([''])
ax_box3.grid(axis='y', linestyle='--', alpha=0.3)

# --- 5. Jain's Fairness Index ---
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
# METRICS CALCULATION & EXPORT
# ==========================================
output_metrics_csv = os.path.join(base_dir, "performance_summary.csv")

def calculate_statistics(data_list):
    """Calculate mean, std, min, max, median, and IQR for a data list"""
    data = np.array(data_list)
    if data.size == 0:
        return [np.nan] * 6
    data = data[~pd.isna(data)]
    if data.size == 0:
        return [np.nan] * 6
        
    iqr = np.percentile(data, 75) - np.percentile(data, 25)
    return [np.mean(data), np.std(data), np.min(data), np.max(data), np.median(data), iqr]

# Extract convergence steps from data pairs
if convergence_data_pairs:
    _, convergence_steps_list = zip(*convergence_data_pairs)
else:
    convergence_steps_list = []

# Calculate statistics for all metrics
stats_convergence_steps = calculate_statistics(convergence_steps_list)
stats_recovery_steps = calculate_statistics(recovery_times)
stats_global_throughput = calculate_statistics(global_throughput)
stats_efficiency_to_food = calculate_statistics(efficiency_to_food)
stats_efficiency_to_nest = calculate_statistics(efficiency_to_nest)
stats_fairness_index = calculate_statistics(jains_index)

# Build metrics summary dictionary
metrics_summary = {
    "Metric": [
        "Convergence_Steps",
        "Recovery_Steps", 
        "Global_Throughput",
        "Efficiency_Food",
        "Efficiency_Nest",
        "Jains_Fairness_Index"
    ],
    "Mean": [
        stats_convergence_steps[0],
        stats_recovery_steps[0],
        stats_global_throughput[0],
        stats_efficiency_to_food[0],
        stats_efficiency_to_nest[0],
        stats_fairness_index[0]
    ],
    "Median": [
        stats_convergence_steps[4],
        stats_recovery_steps[4],
        stats_global_throughput[4],
        stats_efficiency_to_food[4],
        stats_efficiency_to_nest[4],
        stats_fairness_index[4]
    ],
    "Std_Dev": [
        stats_convergence_steps[1],
        stats_recovery_steps[1],
        stats_global_throughput[1],
        stats_efficiency_to_food[1],
        stats_efficiency_to_nest[1],
        stats_fairness_index[1]
    ],
    "Min": [
        stats_convergence_steps[2],
        stats_recovery_steps[2],
        stats_global_throughput[2],
        stats_efficiency_to_food[2],
        stats_efficiency_to_nest[2],
        stats_fairness_index[2]
    ],
    "Max": [
        stats_convergence_steps[3],
        stats_recovery_steps[3],
        stats_global_throughput[3],
        stats_efficiency_to_food[3],
        stats_efficiency_to_nest[3],
        stats_fairness_index[3]
    ],
    "IQR": [
        stats_convergence_steps[5],
        stats_recovery_steps[5],
        stats_global_throughput[5],
        stats_efficiency_to_food[5],
        stats_efficiency_to_nest[5],
        stats_fairness_index[5]
    ]
}

df_summary = pd.DataFrame(metrics_summary)

# Append success rates
df_summary.loc[len(df_summary)] = [
    "Convergence_Success_Rate_Pct",
    conv_rate,
    np.nan, np.nan, np.nan, np.nan, np.nan
]
df_summary.loc[len(df_summary)] = [
    "Recovery_Success_Rate_Pct",
    rec_rate,
    np.nan, np.nan, np.nan, np.nan, np.nan
]
df_summary.loc[len(df_summary)] = [
    "Active_Deletion_Events_Count",
    len(active_deletion_events),
    np.nan, np.nan, np.nan, np.nan, np.nan
]

# Add run ID and save
df_summary.insert(0, "Run_ID", run_id)
df_summary.to_csv(output_metrics_csv, index=False)

