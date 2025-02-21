import os
import json
import matplotlib.pyplot as plt
import numpy as np
from tkinter import Tk, filedialog

# 📘 **Open file dialog to select the JSON file**
Tk().withdraw()  # Hide the main Tkinter window
file_path = filedialog.askopenfilename(title="Select JSON file",
                                       filetypes=[("JSON files", "*.json"), ("All files", "*.*")])

# 🛠️ **Check if the file exists**
if not file_path or not os.path.isfile(file_path):
    raise FileNotFoundError(f"Could not find the file at {file_path}. Please check if the file path is correct.")

# 📘 **Load the JSON file**
with open(file_path, 'r') as file:
    data = json.load(file)

# 📘 **Extract BrainSenseLfp Data**
brain_sense_lfp_data = data.get('BrainSenseLfp', [])

if not brain_sense_lfp_data:
    raise ValueError("No BrainSenseLfp data found in the JSON file.")

# 📘 **Outlier Removal Functions**
def remove_outliers(data, threshold=3):
    """Remove outliers using the robust Z-score method."""
    median = np.nanmedian(data)
    mad = np.nanmedian(np.abs(data - median))
    if mad == 0:
        mad = 1e-6
    z_scores = (data - median) / (1.4826 * mad)
    return [value if abs(z) < threshold else np.nan for value, z in zip(data, z_scores)]

# 🔥 **Process LFP and Amplitude Data for Each Session**
for i, entry in enumerate(brain_sense_lfp_data):
    lfp_data = entry.get('LfpData', [])

    if len(lfp_data) < 2:
        print(f"Skipping session {i + 1} due to insufficient data.")
        continue

    left_lfp_values = []
    right_lfp_values = []
    left_amp_values = []
    right_amp_values = []
    timestamps = []

    for item in lfp_data:
        timestamps.append(item.get('TicksInMs', 0))

        if 'Left' in item:
            left_lfp_values.append(item['Left'].get('LFP', np.nan))
            left_amp_values.append(item['Left'].get('mA', np.nan))
        else:
            left_lfp_values.append(np.nan)
            left_amp_values.append(np.nan)

        if 'Right' in item:
            right_lfp_values.append(item['Right'].get('LFP', np.nan))
            right_amp_values.append(item['Right'].get('mA', np.nan))
        else:
            right_lfp_values.append(np.nan)
            right_amp_values.append(np.nan)

    # Apply outlier removal
    left_lfp_cleaned = remove_outliers(left_lfp_values)
    right_lfp_cleaned = remove_outliers(right_lfp_values)

    # Normalize timestamps to seconds
    min_time = min(timestamps)
    timestamps_in_seconds = [(t - min_time) / 1000 for t in timestamps]

    # 📈 **Plot for Each Session**
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True, constrained_layout=True)
    fig.suptitle(f'Session {i + 1}: LFP and Stimulation Analysis', fontsize=16)

    # Plot Left LFP
    axes[0].plot(timestamps_in_seconds, left_lfp_cleaned, color='red', label='Left LFP')
    axes[0].set_title('LFP Left Hemisphere')
    axes[0].set_ylabel('LFP (uV)')
    axes[0].grid(True, linestyle='--', alpha=0.6)
    axes[0].legend(loc='upper right')

    # Plot Right LFP
    axes[1].plot(timestamps_in_seconds, right_lfp_cleaned, color='green', label='Right LFP')
    axes[1].set_title('LFP Right Hemisphere')
    axes[1].set_ylabel('LFP (uV)')
    axes[1].grid(True, linestyle='--', alpha=0.6)
    axes[1].legend(loc='upper right')

    # Plot Stimulation Amplitude
    axes[2].plot(timestamps_in_seconds, left_amp_values, color='red', label='Stimulation Left')
    axes[2].plot(timestamps_in_seconds, right_amp_values, color='green', label='Stimulation Right')
    axes[2].set_title('Stimulation Amplitude (Left = Red, Right = Green)')
    axes[2].set_xlabel('Time (seconds)')
    axes[2].set_ylabel('Amplitude (mA)')
    axes[2].grid(True, linestyle='--', alpha=0.6)
    axes[2].legend(loc='upper right')

    for ax in axes:
        ax.tick_params(axis='x', rotation=45)

    # Save figures as PNG and SVG
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.dirname(file_path)
    png_path = os.path.join(output_dir, f"{base_filename}_session_{i + 1}.png")
    svg_path = os.path.join(output_dir, f"{base_filename}_session_{i + 1}.svg")

    plt.savefig(png_path, format='png')
    plt.savefig(svg_path, format='svg')
    plt.show()

    print(f"Session {i + 1} plots saved as {png_path} and {svg_path}")
