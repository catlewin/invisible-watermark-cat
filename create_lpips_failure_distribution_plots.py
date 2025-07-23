import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Configurable constants
methods = ['dwtDct', 'dwtDctSvd', 'rivaGan']
attacks = ['crop', 'decrease_brightness', 'increase_brightness', 'denoising', 'jpeg',
           'mask', 'noise', 'overlay', 'resize', 'rotate', 'upscale']
image_names = [
    "cat", "city_day", "city_night", "desert", "dog", "fish", "food",
    "forest", "man1", "man2", "man3", "mountain", "pages", "woman1", "woman2"
]
base_dir = "decode_lpips_results"
bin_width = 0.1

# Create output directory
os.makedirs("lpips_failure_distribution_plots", exist_ok=True)

for method in methods:
    # Store all first-failure lpips scores and attack types for this method
    method_lpips_scores = []
    method_attack_labels = []

    print(f"\n--- Processing method: {method} ---")

    for attack in attacks:
        for image in image_names:
            csv_path = os.path.join(base_dir, f"{attack}_test_results/512x512/{method}/{image}_merged_results.csv")
            if not os.path.exists(csv_path):
                continue
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                print(f"Error reading {csv_path}: {e}")
                continue

            first_failure_row = df[df['success'] == False].head(1)
            if not first_failure_row.empty:
                lpips = first_failure_row.iloc[0].get('lpips_score', None)
                try:
                    lpips = float(lpips)
                except (ValueError, TypeError):
                    lpips = None

                if lpips is not None and not pd.isna(lpips):
                    method_lpips_scores.append(lpips)
                    method_attack_labels.append(attack)

    # Skip if no failures
    if not method_lpips_scores:
        print(f"No failures found for method {method}. Skipping.")
        continue

    # Determine dynamic LPIPS bins for this method
    max_lpips_score = max(method_lpips_scores)
    max_bin_edge = bin_width * int(np.ceil(max_lpips_score / bin_width)) + bin_width
    lpips_bins = np.arange(0.0, max_bin_edge, bin_width)
    bin_labels = [f"{lpips_bins[i]:.1f}-{lpips_bins[i + 1]:.1f}" for i in range(len(lpips_bins) - 1)]
    bin_attack_counts = {label: defaultdict(int) for label in bin_labels}

    # Bin first failure LPIPS scores
    for lpips, attack in zip(method_lpips_scores, method_attack_labels):
        for i in range(len(lpips_bins) - 1):
            if lpips_bins[i] <= lpips < lpips_bins[i + 1]:
                bin_label = f"{lpips_bins[i]:.1f}-{lpips_bins[i + 1]:.1f}"
                bin_attack_counts[bin_label][attack] += 1
                break

    # Color map for attacks
    attack_colors = plt.get_cmap('tab10')
    attack_colors_dict = {attack: attack_colors(i % 10) for i, attack in enumerate(attacks)}

    # Prepare grouped bar plot
    x = np.arange(len(bin_labels))
    bar_width = 0.08
    plt.figure(figsize=(12, 6))

    for i, attack in enumerate(attacks):
        values = [bin_attack_counts[bin_label][attack] for bin_label in bin_labels]
        plt.bar(x + i * bar_width, values, width=bar_width, label=attack, color=attack_colors_dict[attack])

    # Finalize plot
    plt.title(f"First Decode Failures by LPIPS Bin – {method}")
    plt.xlabel("LPIPS Score Bins")
    plt.ylabel("Number of First Decode Failures")
    plt.xticks(x + (len(attacks) / 2 - 0.5) * bar_width, bin_labels, rotation=45)
    plt.legend(title="Attack Type", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(f"lpips_failure_distribution_plots/{method}_lpips_failure_distribution.png")
    plt.close()
