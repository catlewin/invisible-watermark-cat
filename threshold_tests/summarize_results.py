import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple


def load_thresholds_by_method(results_root: str, methods: List[str], metric: str, threshold_mode: str = "max") -> Dict[str, List[float]]:
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
                    value = (
                        successful[metric].min()
                        if threshold_mode == "min"
                        else successful[metric].max()
                    )
                    thresholds.append(value)
                else:
                    thresholds.append(None)

        thresholds_by_method[method] = thresholds
    return thresholds_by_method


def prepare_distribution_scale(
    thresholds_by_method: Dict[str, List[float]],
    bin_width: float = 1.0,
    bin_centers: List[float] = None
) -> Tuple[List[float], float]:
    if bin_centers is not None:
        x_vals = bin_centers
    else:
        all_values = [t for ts in thresholds_by_method.values() for t in ts if t is not None]
        min_thresh = np.floor(min(all_values) / bin_width) * bin_width
        max_thresh = np.ceil(max(all_values) / bin_width) * bin_width
        x_vals = np.round(np.arange(min_thresh, max_thresh + bin_width, bin_width), 2)

    max_freq = 0
    for thresholds in thresholds_by_method.values():
        counts = [
            sum(np.isclose(t_val, x, atol=bin_width / 2) for t_val in thresholds if t_val is not None)
            for x in x_vals
        ]

        max_freq = max(max_freq, max(counts))

    return list(x_vals), max_freq


def generate_individual_distributions(
    thresholds_by_method: Dict[str, List[float]],
    output_dir: str,
    metric_label: str,
    bin_width: float = 1.0,
    bin_centers: List[float] = None
):
    x_vals, max_freq = prepare_distribution_scale(thresholds_by_method, bin_width, bin_centers)

    for method, thresholds in thresholds_by_method.items():
        if not thresholds:
            continue

        counts = [sum(np.isclose(t_val, x, atol=bin_width / 2) for t_val in thresholds if t_val is not None) for x in x_vals]

        plt.figure(figsize=(8, 4))
        bars = plt.bar(x_vals, counts, width=bin_width * 0.9, edgecolor='black')
        plt.title(f"{method} {metric_label} Threshold Distribution")
        plt.xlabel(metric_label)
        plt.ylabel("Number of Images")
        plt.xticks(x_vals, [str(x) for x in x_vals], rotation=45)
        plt.ylim(0, max_freq + 1)

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width() / 2, height + 0.2, str(int(height)),
                         ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        output_path = os.path.join(output_dir, f"{method}_threshold_bar.png")
        plt.savefig(output_path)
        plt.close()
        print(f"Saved individual plot for {method} to {output_path}")


def plot_combined_distribution(
    thresholds_by_method: Dict[str, List[float]],
    results_root: str,
    output_file: str,
    metric_label: str,
    colors: Dict[str, str],
    bin_centers: List[float],
    bin_width: float = 1.0
):
    num_methods = len(thresholds_by_method)
    bar_width = bin_width / num_methods * 0.9  # smaller spread
    method_names = list(thresholds_by_method.keys())

    plt.figure(figsize=(12, 6))

    for i, method in enumerate(method_names):
        thresholds = thresholds_by_method[method]
        y_vals = [
            sum(np.isclose(t_val, x, atol=bin_width / 2) for t_val in thresholds if t_val is not None)
            for x in bin_centers
        ]

        # Shift bars around each bin_center instead of a fixed index
        x_offsets = [x + (i - (num_methods - 1) / 2) * bar_width for x in bin_centers]

        bars = plt.bar(
            x_offsets,
            y_vals,
            bar_width,
            label=method,
            color=colors.get(method, None),
            edgecolor='black'
        )

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + 0.3,
                    str(int(height)),
                    ha='center',
                    va='bottom',
                    fontsize=8
                )

    plt.title(f"Combined {metric_label} Threshold Distribution")
    plt.xlabel(metric_label)
    plt.ylabel("Number of Images")
    plt.xticks(bin_centers, [str(x) for x in bin_centers], rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    output_path = os.path.join(results_root, output_file)
    plt.savefig(output_path)
    plt.close()
    print(f"Combined plot saved to {output_path}")



def write_brightness_markdown_summary(df: pd.DataFrame, output_dir: str, methods: List[str]):
    md_path = os.path.join(output_dir, "brightness_summary.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# 📊 Brightness Threshold Summary\n\n")
        f.write("This summary includes average, median, and standard deviation of brightness thresholds at which watermark decoding failed.\n\n")

        f.write("| Method | Images | Failures | Avg Threshold | Median | Std Dev | Min | Max |\n")
        f.write("|--------|--------|----------|----------------|--------|---------|-----|-----|\n")

        for _, row in df.iterrows():
            f.write(f"| {row['method']} | {row['image_count']} | {row['failure_count']} | "
                    f"{row['average_threshold']:.2f} | {row['median_threshold']:.2f} | "
                    f"{row['std_dev_threshold']:.2f} | {row['min_threshold']} | {row['max_threshold']} |\n")

        f.write("\n---\n")

        for section, prefix, folder in [
            ("Lowest Brightness (0.0-1.0)", "low_brightness", "low_brightness"),
            ("Highest Brightness (1.0-2.0)", "high_brightness", "high_brightness")
        ]:
            f.write(f"## {section}\n\n")
            f.write("### Individual Distribution\n")
            for method in methods:
                f.write(f"![{method} Bar Graph]({folder}/{method}_threshold_bar.png)\n\n")

            f.write(f"### Combined Threshold Distribution\n")
            f.write(f"![Combined Threshold Bar Graph]({folder}/{prefix}_combined_distribution.png)\n\n")

def write_markdown_summary(df: pd.DataFrame, output_dir: str, attack_name: str, metric_label: str, methods: List[str]):
    os.makedirs(output_dir, exist_ok=True)
    md_path = os.path.join(output_dir, f"{attack_name}_summary.md")

    with open(md_path, "w") as f:
        f.write(f"# {attack_name.title()} Threshold Summary\n\n")
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

        f.write("## Combined Threshold Distribution\n")
        f.write(f"![Combined Threshold Bar Graph]({attack_name}_combined_distribution.png)\n\n")


def summarize_thresholds(thresholds_by_method: Dict[str, List[float]]) -> pd.DataFrame:
    summary = []
    for method, thresholds in thresholds_by_method.items():
        valid_thresholds = [t for t in thresholds if t is not None]
        total_images = len(thresholds)
        failure_count = total_images - len(valid_thresholds)

        summary.append({
            "method": method,
            "image_count": total_images,
            "failure_count": failure_count,
            "average_threshold": round(sum(valid_thresholds) / len(valid_thresholds), 2) if valid_thresholds else None,
            "median_threshold": round(np.median(valid_thresholds), 2) if valid_thresholds else None,
            "std_dev_threshold": round(np.std(valid_thresholds), 2) if valid_thresholds else None,
            "min_threshold": min(valid_thresholds) if valid_thresholds else None,
            "max_threshold": max(valid_thresholds) if valid_thresholds else None,
        })

    return pd.DataFrame(summary)


def summarize_all_threshold_results(
    results_root: str,
    attack_name: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str],
    threshold_mode: str = "max",
    bin_centers: List[float] = None,
    bin_width: float = 1.0
):
    thresholds_by_method = load_thresholds_by_method(results_root, methods, metric, threshold_mode=threshold_mode)
    df = summarize_thresholds(thresholds_by_method)

    df.to_csv(os.path.join(results_root, f"{attack_name}_summary.csv"), index=False)

    generate_individual_distributions(
        thresholds_by_method,
        output_dir=results_root,
        metric_label=metric_label,
        bin_width=bin_width,
        bin_centers=bin_centers
    )

    plot_combined_distribution(
        thresholds_by_method,
        results_root,
        f"{attack_name}_combined_distribution.png",
        metric_label,
        colors,
        bin_centers=bin_centers,
        bin_width=bin_width
    )

    write_markdown_summary(df, results_root, attack_name, metric_label, methods)
    print(df)


def summarize_noise_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str],
    bin_centers: List[float],
    bin_width: float = 1.0
):
    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="noise",
        metric=metric,
        metric_label=metric_label,
        methods=methods,
        colors=colors,
        threshold_mode="max",
        bin_centers=bin_centers,
        bin_width=bin_width
    )



def summarize_brightness_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str],
    low_range: List[float],
    high_range: List[float],
    bin_width: float = 0.2
):

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
                    min_val = successful[metric].min()
                    max_val = successful[metric].max()
                    thresholds.append((min_val, max_val))
                else:
                    thresholds.append((None, None))
        thresholds_by_method[method] = thresholds

    min_thresh_by_method = {
        method: [t[0] for t in t_list] for method, t_list in thresholds_by_method.items()
    }
    max_thresh_by_method = {
        method: [t[1] for t in t_list] for method, t_list in thresholds_by_method.items()
    }

    low_output_dir = os.path.join(results_root, "low_brightness")
    high_output_dir = os.path.join(results_root, "high_brightness")

    os.makedirs(low_output_dir, exist_ok=True)
    os.makedirs(high_output_dir, exist_ok=True)

    generate_individual_distributions(min_thresh_by_method, low_output_dir, f"{metric_label} (Min)", bin_width, low_range)
    plot_combined_distribution(min_thresh_by_method, low_output_dir, f"low_brightness_combined_distribution.png", f"{metric_label} (Min)", colors, low_range, bin_width)

    generate_individual_distributions(max_thresh_by_method, high_output_dir, f"{metric_label} (Max)", bin_width, high_range)
    plot_combined_distribution(max_thresh_by_method, high_output_dir, f"high_brightness_combined_distribution.png", f"{metric_label} (Max)", colors, high_range, bin_width)

    summary = []
    for method in methods:
        min_vals = [t for t in min_thresh_by_method[method] if t is not None]
        max_vals = [t for t in max_thresh_by_method[method] if t is not None]
        total = len(min_thresh_by_method[method])
        summary.append({
            "method": method,
            "image_count": total,
            "failure_count": total - len(min_vals),
            "average_threshold": round(sum(min_vals + max_vals) / (len(min_vals) + len(max_vals)), 2) if min_vals and max_vals else None,
            "median_threshold": round(np.median(min_vals + max_vals), 2) if min_vals and max_vals else None,
            "std_dev_threshold": round(np.std(min_vals + max_vals), 2) if min_vals and max_vals else None,
            "min_threshold": min(min_vals) if min_vals else None,
            "max_threshold": max(max_vals) if max_vals else None,
        })
    df = pd.DataFrame(summary)
    write_brightness_markdown_summary(df, results_root, methods)
    print(df)



if __name__ == "__main__":
    '''
    summarize_noise_threshold(
        results_root="threshold_tests/noise_test_results",
        metric="std_dev",
        metric_label="Gaussian Noise (σ)",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"},
        bin_centers=[0, 5, 10, 15, 20, 25, 30, 35, 40],
        bin_width=5
    )
    '''

    #'''
    summarize_brightness_threshold(
        results_root="threshold_tests/brightness_test_results",
        metric="brightness_factor",
        metric_label="Brightness",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"},
        low_range=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        high_range=[1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
    )
    #'''


