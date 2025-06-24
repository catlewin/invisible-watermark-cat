import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Dict, List
import numpy as np

def load_thresholds_by_method(results_root: str, methods: List[str]) -> Dict[str, List[int]]:
    thresholds_by_method = {}
    for method in methods:
        method_dir = os.path.join(str(results_root), str(method))
        thresholds = []

        for file in os.listdir(method_dir):
            file_path = os.path.join(str(method_dir), str(file))
            if file.endswith("_gaussian_results.csv"):
                df = pd.read_csv(str(file_path))
                successful = df[df["success"] == True]
                if not successful.empty:
                    thresholds.append(successful["std_dev"].max())
                else:
                    thresholds.append(0)

        thresholds_by_method[method] = thresholds
    return thresholds_by_method


def plot_combined_distribution(results_root="threshold_tests/noise_test_results", output_file="combined_threshold_distribution.png"):
    methods = ["dwtDct", "dwtDctSvd", "rivaGan"]
    colors = {"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"}
    thresholds_by_method = load_thresholds_by_method(results_root, methods)

    all_thresholds = [t for thresholds in thresholds_by_method.values() for t in thresholds]
    max_val = max(all_thresholds)
    bins = range(0, int(max_val) + 6, 5)

    plt.figure(figsize=(10, 6))
    for method in methods:
        plt.hist(thresholds_by_method[method], bins=bins, alpha=0.7,
                 label=method, edgecolor='black', color=colors[method])

    plt.title("Combined Gaussian Noise Threshold Distribution")
    plt.xlabel("Gaussian Noise Std Dev")
    plt.ylabel("Number of Images")
    plt.legend()
    plt.grid(True)

    output_path = os.path.join(results_root, output_file)
    plt.savefig(output_path)
    plt.close()
    print(f"✅ Combined plot saved to {output_path}")


def plot_grouped_distribution(results_root="threshold_tests/noise_test_results", output_file="grouped_threshold_distribution.png"):
    methods = ["dwtDct", "dwtDctSvd", "rivaGan"]
    colors = ["skyblue", "lightgreen", "salmon"]
    thresholds_by_method = load_thresholds_by_method(results_root, methods)

    all_thresholds = [t for values in thresholds_by_method.values() for t in values]
    max_val = (max(all_thresholds) // 5 + 1) * 5
    bins = list(range(0, max_val + 5, 5))
    bar_width = 0.25
    index = np.arange(len(bins) - 1)

    plt.figure(figsize=(10, 6))
    for i, method in enumerate(methods):
        counts, _ = np.histogram(thresholds_by_method[method], bins=bins)
        positions = index + (i - 1) * bar_width
        bars = plt.bar(positions, counts, bar_width, label=method, color=colors[i], edgecolor='black')
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width() / 2, height + 0.3, str(height), ha='center', va='bottom', fontsize=8)

    plt.xlabel("Gaussian Noise Std Dev")
    plt.ylabel("Number of Images")
    plt.title("Grouped Threshold Distribution by Method")
    plt.xticks(index, [f"{bins[i]}–{bins[i + 1]}" for i in range(len(bins) - 1)], rotation=45)
    plt.legend()
    plt.tight_layout()

    output_path = os.path.join(results_root, output_file)
    plt.savefig(output_path)
    plt.close()
    print(f"✅ Grouped plot saved to {output_path}")


def write_markdown_summary(df: pd.DataFrame, output_dir: str, markdown_path: Optional[str] = None):
    os.makedirs(output_dir, exist_ok=True)
    if markdown_path is None:
        markdown_path = os.path.join(output_dir, "gaussian_noise_summary.md")

    with open(markdown_path, "w") as f:
        f.write("# 📊 Gaussian Noise Threshold Summary\n\n")
        f.write("This summary includes average, median, and standard deviation of the noise thresholds at which watermark decoding failed.\n\n")

        f.write("| Method | Images | Failures | Avg Threshold | Median | Std Dev | Min | Max |\n")
        f.write("|--------|--------|----------|----------------|--------|---------|-----|-----|\n")

        for _, row in df.iterrows():
            f.write(f"| {row['method']} | {row['image_count']} | {row['failure_count']} | "
                    f"{row['average_threshold']:.2f} | {row['median_threshold']:.2f} | "
                    f"{row['std_dev_threshold']:.2f} | {row['min_threshold']} | {row['max_threshold']} |\n")

        f.write("\n---\n")

        for _, row in df.iterrows():
            method = row['method']
            method_dir = os.path.join(output_dir, method)
            plot_path = os.path.join(output_dir, f"{method}_threshold_hist.png")

            thresholds = []
            csv_files = [f for f in os.listdir(method_dir) if f.endswith("_gaussian_results.csv")]
            for file in csv_files:
                csv_path = os.path.join(method_dir, file)
                data = pd.read_csv(csv_path)
                success_rows = data[data["success"] == True]
                if not success_rows.empty:
                    thresholds.append(success_rows["std_dev"].max())
                else:
                    thresholds.append(0)

            if not thresholds:
                f.write(f"### {method} Threshold Distribution\n")
                f.write(f"_No data available to plot._\n\n")
                continue

            plt.figure()
            plt.hist(thresholds, bins=range(0, max(thresholds) + 5, 5), edgecolor='black')
            plt.title(f"{method} Threshold Distribution")
            plt.xlabel("Gaussian Noise Std Dev")
            plt.ylabel("Number of Images")
            plt.tight_layout()
            plt.savefig(plot_path)
            plt.close()

            f.write(f"### {method} Threshold Distribution\n")
            f.write(f"![{method} Histogram]({os.path.basename(plot_path)})\n\n")

        f.write("---\n")
        f.write("## 🔄 Combined Threshold Distribution\n")
        f.write("This histogram compares the Gaussian noise decoding thresholds across all three watermarking methods.\n\n")
        f.write("![Combined Threshold Histogram](combined_threshold_distribution.png)\n")

        f.write("\n---\n")
        f.write("## 📊 Grouped Threshold Distribution\n")
        f.write("This chart separates decoding threshold bars by method for each noise level.\n\n")
        f.write("![Grouped Threshold Histogram](grouped_threshold_distribution.png)\n")

def summarize_noise_thresholds(results_root: str = "threshold_tests/noise_test_results"):
    summary = []

    for method in os.listdir(results_root):
        method_dir = os.path.join(results_root, method)
        if not os.path.isdir(method_dir):
            continue

        thresholds = []
        failure_count = 0
        total_images = 0

        for file in os.listdir(method_dir):
            if file.endswith("_gaussian_results.csv"):
                total_images += 1
                csv_path = os.path.join(method_dir, file)
                df = pd.read_csv(csv_path)

                successful = df[df["success"] == True]
                if not successful.empty:
                    max_success_std = successful["std_dev"].max()
                    thresholds.append(max_success_std)
                else:
                    thresholds.append(0)
                    failure_count += 1

        if thresholds:
            summary.append({
                "method": method,
                "image_count": total_images,
                "failure_count": failure_count,
                "average_threshold": round(sum(thresholds) / len(thresholds), 2),
                "median_threshold": round(np.median(thresholds), 2),
                "std_dev_threshold": round(np.std(thresholds), 2),
                "min_threshold": min(thresholds),
                "max_threshold": max(thresholds),
            })

    summary_df = pd.DataFrame(summary)
    output_csv_path = os.path.join(results_root, "gaussian_noise_summary.csv")
    summary_df.to_csv(output_csv_path, index=False)
    print(f"✅ Summary saved to {output_csv_path}")
    print(summary_df)

    # Generate markdown summary and plots
    plot_combined_distribution()
    plot_grouped_distribution()
    write_markdown_summary(summary_df, output_dir=results_root)

summarize_noise_thresholds()
