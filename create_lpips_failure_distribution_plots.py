import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Configurable constants
methods = ['dwtDct', 'dwtDctSvd', 'rivaGan']
attacks = [ 'mask', 'overlay', 'resize']
image_names = [
    "cat", "city_day", "city_night", "desert", "dog", "fish", "food",
    "forest", "man1", "man2", "man3", "mountain", "pages", "woman1", "woman2"
]
base_dir = "decode_lpips_results"
bin_width = 0.05

# Create output directory
os.makedirs("lpips_failure_distribution_plots/high_lpips", exist_ok=True)

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
    max_bin_edge = bin_width * (int(np.ceil(max_lpips_score / bin_width)) + 1)
    lpips_bins = np.arange(0.0, max_bin_edge, bin_width)
    bin_labels = [f"{lpips_bins[i]:.2f}-{lpips_bins[i + 1]:.2f}" for i in range(len(lpips_bins) - 1)]
    bin_attack_counts = {label: defaultdict(int) for label in bin_labels}

    # Bin first failure LPIPS scores
    for lpips, attack in zip(method_lpips_scores, method_attack_labels):
        for i in range(len(lpips_bins) - 1):
            if lpips_bins[i] <= lpips < lpips_bins[i + 1]:
                bin_label = f"{lpips_bins[i]:.2f}-{lpips_bins[i + 1]:.2f}"
                if bin_label not in bin_attack_counts:
                    print(f"❌ Unexpected bin label: {bin_label}")
                    print(f"  lpips={lpips}, bin_edges={lpips_bins}")
                    raise KeyError(bin_label)

                bin_attack_counts[bin_label][attack] += 1
                break

    # Color map for attacks
    attack_colors = plt.get_cmap('tab10')
    attack_colors_dict = {attack: attack_colors(i % 10) for i, attack in enumerate(attacks)}

    # Prepare grouped bar plot
    spacing_scale = 0.4  # try between 0.5–0.8 for tighter spacing
    x = np.arange(len(bin_labels)) * spacing_scale

    bar_width = 0.08
    plt.figure(figsize=(10, 6))

    for i, attack in enumerate(attacks):
        # Total failures for this attack (across all bins)
        total_failures = sum(bin_attack_counts[bin_label][attack] for bin_label in bin_labels)
        if total_failures == 0:
            values = [0] * len(bin_labels)
        else:
            values = [
                100 * bin_attack_counts[bin_label][attack] / total_failures
                for bin_label in bin_labels
            ]

        plt.bar(x + i * bar_width, values, width=bar_width, label=attack, color=attack_colors_dict[attack])

    # Finalize plot
    plt.title(f"First Decode Failures by LPIPS Bin – {method}")
    plt.xlabel("LPIPS Score Bins")
    plt.ylabel("Percent of First Decode Failures")
    # Find the max percent value across all bars
    max_percent = max(
        100 * bin_attack_counts[bin_label][attack] / sum(
            bin_attack_counts[bin_label][attack] for bin_label in bin_labels)
        if sum(bin_attack_counts[bin_label][attack] for bin_label in bin_labels) > 0 else 0
        for attack in attacks
        for bin_label in bin_labels
    )
    if max_percent == 100:
        max_percent = 100 + 5

    # Add a small margin (e.g., 5%)
    plt.ylim(0, min(100, max_percent + 5))

    group_center = x + (len(attacks) * bar_width) / 2 - bar_width / 2
    plt.xticks(group_center, bin_labels, rotation=45)
    plt.legend(title="Attack Type", loc='upper right', frameon=True)
    plt.tight_layout()
    plt.savefig(f"lpips_failure_distribution_plots/high_lpips/{method}_lpips_failure_distribution.png")
    plt.close()
