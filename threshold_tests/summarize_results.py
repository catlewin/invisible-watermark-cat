import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter

def load_thresholds_by_method(results_root: str, methods: List[str], metric: str) -> Dict[str, List[float]]:
    thresholds_by_method = {}
    for method in methods:
        method_dir = os.path.join(results_root, method)
        thresholds = []

        for file in os.listdir(method_dir):
            if file.endswith("_results.csv"):
                file_path = os.path.join(method_dir, file)
                df = pd.read_csv(file_path)
                successful = df[df["success"] == True]
                if not successful.empty:
                    thresholds.append(successful[metric].max())
                else:
                    thresholds.append(0)

        thresholds_by_method[method] = thresholds
    return thresholds_by_method


def prepare_distribution_scale(thresholds_by_method: Dict[str, List[float]]) -> Tuple[List[int], int]:
    # Define fixed x values (e.g. 0 to max threshold in 5s)
    max_thresh = max(t for ts in thresholds_by_method.values() for t in ts)
    x_vals = list(range(0, int(max_thresh) + 5, 5))

    # Find global max frequency
    max_freq = 0
    for thresholds in thresholds_by_method.values():
        counts = [thresholds.count(x) for x in x_vals]
        max_freq = max(max_freq, max(counts))

    return x_vals, max_freq


def generate_individual_distributions(thresholds_by_method: Dict[str, List[float]], output_dir: str, metric_label: str):
    x_vals, max_freq = prepare_distribution_scale(thresholds_by_method)

    for method, thresholds in thresholds_by_method.items():
        if not thresholds:
            continue

        counts = [thresholds.count(x) for x in x_vals]

        plt.figure(figsize=(8, 4))
        bars = plt.bar(x_vals, counts, width=4, edgecolor='black')
        plt.title(f"{method} {metric_label} Threshold Distribution")
        plt.xlabel(metric_label)
        plt.ylabel("Number of Images")
        plt.xticks(x_vals)
        plt.ylim(0, max_freq + 1)

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width() / 2, height + 0.2, str(height),
                         ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        output_path = os.path.join(output_dir, f"{method}_threshold_bar.png")
        plt.savefig(output_path)
        plt.close()
        print(f"✅ Saved individual plot for {method} to {output_path}")


def plot_combined_distribution(thresholds_by_method: Dict[str, List[float]], results_root: str, output_file: str, metric_label: str, colors: Dict[str, str]):
    tested_thresholds = sorted(set(t for thresholds in thresholds_by_method.values() for t in thresholds))
    max_val = max(tested_thresholds)
    x_vals = list(range(0, int(max_val) + 5, 5))
    bar_width = 0.25
    x_indexes = np.arange(len(x_vals))

    plt.figure(figsize=(12, 6))
    for i, (method, thresholds) in enumerate(thresholds_by_method.items()):
        counter = Counter(thresholds)
        y_vals = [counter.get(x, 0) for x in x_vals]
        positions = x_indexes + (i - 1) * bar_width
        bars = plt.bar(positions, y_vals, bar_width, label=method,
                       color=colors.get(method, None), edgecolor='black')

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width() / 2, height + 0.3, str(height),
                         ha='center', va='bottom', fontsize=8)

    plt.title(f"Combined {metric_label} Threshold Distribution")
    plt.xlabel(metric_label)
    plt.ylabel("Number of Images")
    plt.xticks(x_indexes, [str(x) for x in x_vals])
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    output_path = os.path.join(results_root, output_file)
    plt.savefig(output_path)
    plt.close()
    print(f"✅ Combined plot saved to {output_path}")

def write_markdown_summary(df: pd.DataFrame, output_dir: str, attack_name: str, metric_label: str, methods: List[str]):
    os.makedirs(output_dir, exist_ok=True)
    md_path = os.path.join(output_dir, f"{attack_name}_summary.md")

    with open(md_path, "w") as f:
        f.write(f"# 📊 {attack_name.title()} Threshold Summary\n\n")
        f.write(f"This summary includes average, median, and standard deviation of {metric_label} thresholds at which watermark decoding failed.\n\n")

        f.write("| Method | Images | Failures | Avg Threshold | Median | Std Dev | Min | Max |\n")
        f.write("|--------|--------|----------|----------------|--------|---------|-----|-----|\n")

        for _, row in df.iterrows():
            f.write(f"| {row['method']} | {row['image_count']} | {row['failure_count']} | "
                    f"{row['average_threshold']:.2f} | {row['median_threshold']:.2f} | "
                    f"{row['std_dev_threshold']:.2f} | {row['min_threshold']} | {row['max_threshold']} |\n")

        f.write("\n---\n")

        for method in methods:
            f.write(f"### {method} Threshold Distribution\n")
            f.write(f"![{method} Bar Graph]({method}_threshold_bar.png)\n\n")

        f.write("## 🔄 Combined Threshold Distribution\n")
        f.write(f"![Combined Threshold Bar Graph]({attack_name}_combined_distribution.png)\n\n")


def summarize_thresholds(thresholds_by_method: Dict[str, List[float]]) -> pd.DataFrame:
    summary = []
    for method, thresholds in thresholds_by_method.items():
        total_images = len(thresholds)
        failure_count = sum(1 for t in thresholds if t == 0)

        summary.append({
            "method": method,
            "image_count": total_images,
            "failure_count": failure_count,
            "average_threshold": round(sum(thresholds) / total_images, 2),
            "median_threshold": round(np.median(thresholds), 2),
            "std_dev_threshold": round(np.std(thresholds), 2),
            "min_threshold": min(thresholds),
            "max_threshold": max(thresholds),
        })

    return pd.DataFrame(summary)


def summarize_all_threshold_results(results_root: str, attack_name: str, metric: str, metric_label: str, methods: List[str], colors: Dict[str, str]):
    thresholds_by_method = load_thresholds_by_method(results_root, methods, metric)
    df = summarize_thresholds(thresholds_by_method)

    df.to_csv(os.path.join(results_root, f"{attack_name}_summary.csv"), index=False)

    generate_individual_distributions(thresholds_by_method, results_root, metric_label)
    plot_combined_distribution(thresholds_by_method, results_root, f"{attack_name}_combined_distribution.png", metric_label, colors)
    write_markdown_summary(df, results_root, attack_name, metric_label, methods)
    print(df)


if __name__ == "__main__":
    summarize_all_threshold_results(
        results_root="threshold_tests/noise_test_results",
        attack_name="gaussian_noise",
        metric="std_dev",
        metric_label="Gaussian Noise Std Dev",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"}
    )
