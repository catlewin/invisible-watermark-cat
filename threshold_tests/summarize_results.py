import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional


def load_thresholds_by_method(results_root: str, methods: List[str],
                              metric: str, threshold_mode: str = "max") -> Tuple[Dict[str, List[float]], Dict[str, int]]:
    thresholds_by_method = {}
    clean_failures = {}

    for method in methods:
        method_dir = os.path.join(results_root, method)
        thresholds = []
        fail_clean_count = 0

        for file in os.listdir(method_dir):
            if file.endswith("_results.csv"):
                file_path = os.path.join(method_dir, file)
                df = pd.read_csv(file_path)

                # Skip clean failure images
                if "can_decode_clean" in df.columns and not df["can_decode_clean"].iloc[0]:
                    thresholds.append(None)
                    fail_clean_count += 1
                    continue

                attacked_df = df[df["attack_type"] != "clean"]
                successful_attacks = attacked_df[attacked_df["success"] == True]

                if metric == "last_success" and "last_success" in attacked_df.columns:
                    last_success_vals = attacked_df["last_success"].dropna().unique()
                    value = float(last_success_vals[0]) if len(last_success_vals) > 0 else None
                elif not successful_attacks.empty and metric in successful_attacks.columns:
                    try:
                        values = pd.to_numeric(successful_attacks[metric], errors="coerce").dropna()
                        if not values.empty:
                            value = values.min() if threshold_mode == "min" else values.max()
                        else:
                            value = None
                    except Exception as e:
                        print(f"[ERROR] Could not parse {metric} in {file_path}: {e}")
                        value = None
                else:
                    value = None

                thresholds.append(value)

        thresholds_by_method[method] = thresholds
        clean_failures[method] = fail_clean_count

    return thresholds_by_method, clean_failures



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
            sum(np.isclose(t_val, x, atol=bin_width / 2) for t_val in thresholds if isinstance(t_val, (int, float)) and not pd.isnull(t_val))
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

        valid_thresholds = [float(t) for t in thresholds if t is not None and not pd.isnull(t)]

        counts = [sum(np.isclose(t, x, atol=bin_width / 2) for t in valid_thresholds) for x in x_vals]

        plt.figure(figsize=(8, 5))
        bars = plt.bar(x_vals, counts, width=bin_width * 0.9, edgecolor='black')

        plt.title(f"{method} {metric_label} Threshold Distribution", fontsize=12)
        plt.xlabel(metric_label, fontsize=10)
        plt.ylabel("Number of Images", fontsize=10)
        plt.xticks(x_vals, [str(x) for x in x_vals], rotation=45)
        plt.ylim(0, max(counts) + 1 if counts else 1)  # Dynamic y-limit
        plt.grid(axis="y", linestyle="--", alpha=0.4)

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
    bar_width = bin_width / num_methods * 0.9
    method_names = list(thresholds_by_method.keys())

    plt.figure(figsize=(12, 6))
    max_count = 0  # for dynamic y-axis scaling

    for i, method in enumerate(method_names):
        # Only use valid (non-None, numeric) thresholds
        thresholds = [float(t) for t in thresholds_by_method[method] if t is not None and not pd.isnull(t)]

        y_vals = [
            sum(np.isclose(t_val, x, atol=bin_width / 2) for t_val in thresholds)
            for x in bin_centers
        ]
        max_count = max(max_count, max(y_vals, default=0))

        # Offset x positions for grouped bars
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
                    height + 0.2,
                    str(int(height)),
                    ha='center',
                    va='bottom',
                    fontsize=8
                )

    plt.title(f"Combined {metric_label} Threshold Distribution", fontsize=13)
    plt.xlabel(metric_label, fontsize=11)
    plt.ylabel("Number of Images", fontsize=11)
    plt.xticks(bin_centers, [str(x) for x in bin_centers], rotation=45)
    plt.ylim(0, max_count + 1)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()  # add extra padding

    output_path = os.path.join(results_root, output_file)
    plt.savefig(output_path)
    plt.close()
    print(f"Combined plot saved to {output_path}")


def write_markdown_summary(df, output_dir, attack_name,
                           methods, thresholds_by_method=None,
                           blurb: str = None):
    os.makedirs(output_dir, exist_ok=True)
    md_path = os.path.join(output_dir, f"{attack_name}_summary.md")

    with open(md_path, "w") as f:
        f.write(f"# 📊 {attack_name.title()} Threshold Summary\n\n")

        if blurb:
            f.write(f"> 📘 {blurb}\n\n")

        f.write("This summary reports the robustness of each watermarking method under threshold-based attacks.\n")
        f.write("- **Clean Failures**: Number of images where the method failed to decode the original, "
                "unattacked watermarked image. These images are excluded from threshold calculations.\n")
        f.write("- **Attack Failures**: Number of images that failed decoding at all tested attack levels.\n")
        f.write("- **Threshold Statistics**: Calculated only from images that passed the clean test and at least "
                "one attack level. Includes average, median, standard deviation, minimum, and maximum threshold values observed.\n\n")

        f.write("| Method | Images | Clean Failures | Attack Failures | # Valid Thresholds | Avg Threshold | Median | Std Dev | Min | Max |\n")
        f.write("|--------|--------|----------------|------------------|---------------------|----------------|--------|---------|-----|-----|\n")

        for _, row in df.iterrows():
            valid_thresholds = [
                t for t in thresholds_by_method.get(row["method"], []) if t is not None
            ]
            contrib_count = len(valid_thresholds)
            avg = f"{row['average_threshold']:.2f}" if pd.notna(row['average_threshold']) else "--"
            med = f"{row['median_threshold']:.2f}" if pd.notna(row['median_threshold']) else "--"
            std = f"{row['std_dev_threshold']:.2f}" if pd.notna(row['std_dev_threshold']) else "--"
            min_thresh = f"{row['min_threshold']:.2f}" if pd.notna(row['min_threshold']) else "--"
            max_thresh = f"{row['max_threshold']:.2f}" if pd.notna(row['max_threshold']) else "--"

            f.write(f"| {row['method']} | {row['image_count']} | {row['fail_clean_count']} | {row['fail_attack_count']} | "
                    f"{contrib_count} | {avg} | {med} | {std} | {min_thresh} | {max_thresh} |\n")

        f.write("\n---\n")

        for method in methods:
            f.write(f"### {method} Threshold Distribution\n")
            f.write(f"![{method} Bar Graph]({method}_threshold_bar.png)\n\n")

        f.write("## Combined Threshold Distribution\n")
        f.write(f"![Combined Threshold Bar Graph]({attack_name}_combined_distribution.png)\n\n")



def summarize_thresholds(thresholds_by_method: Dict[str, List[float]],
                         clean_failures: Optional[Dict[str, int]] = None) -> pd.DataFrame:
    summary = []
    for method, thresholds in thresholds_by_method.items():
        valid_thresholds = [t for t in thresholds if t is not None]
        total_images = len(thresholds)
        failed_attack_count = total_images - len(valid_thresholds)
        failed_clean_count = clean_failures.get(method, 0) if clean_failures else None

        summary.append({
            "method": method,
            "image_count": total_images,
            "fail_clean_count": failed_clean_count,
            "fail_attack_count": failed_attack_count,
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
    threshold_mode: str = "last_success",
    bin_centers: List[float] = None,
    bin_width: float = 1.0,
    blurb: str = None
):
    thresholds_by_method, clean_failures = load_thresholds_by_method(results_root, methods, metric, threshold_mode=threshold_mode)
    df = summarize_thresholds(thresholds_by_method, clean_failures)

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

    write_markdown_summary(df, results_root, attack_name, methods, thresholds_by_method, blurb)
    print(df)


def summarize_noise_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str],
    bin_centers: List[float],
    bin_width: float = 1.0,
):
    bin_centers = list(range(0, 45, 5))
    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="noise",
        metric="std_dev",
        metric_label=metric_label,
        methods=methods,
        colors=colors,
        threshold_mode="max",
        bin_centers=bin_centers,
        bin_width=5,
        blurb = "**Gaussian noise thresholds represent the highest standard deviation (σ) of noise that the watermark"
                " could withstand before failing to decode.**"
    )


def summarize_jpeg_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str]
):
    bin_centers = list(range(0, 105, 5))  # JPEG quality levels 0–100
    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="jpeg",
        metric=metric,
        metric_label=metric_label,
        methods=methods,
        colors=colors,
        threshold_mode="min",  # lowest quality (i.e., most compression) that still passes
        bin_centers=bin_centers,
        bin_width=5,
        blurb = "**JPEG compression thresholds represent the lowest JPEG quality setting where the watermark"
                " could still be successfully decoded. Lower values indicate greater robustness.**"
    )

def summarize_decrease_brightness_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str]
):
    bin_centers = [round(x, 2) for x in np.arange(0.0, 1.05, 0.2)]  # Brightness 0.0–1.0
    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="brightness",
        metric="brightness_factor",  # this will be read now!
        metric_label=metric_label,
        methods=methods,
        colors=colors,
        threshold_mode="min",
        bin_centers=bin_centers,
        bin_width=0.2,
        blurb = "**Brightness Decrease thresholds indicate the lowest brightness factor (0.0–1.0) where watermark "
                "decoding remained successful. Lower values show better robustness to dimming.**"
    )


def summarize_increase_brightness_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str]
):
    bin_centers = [round(x, 2) for x in np.arange(1.0, 3.05, 0.2)]  # Brightness 1.0–2.0
    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="brightness",
        metric=metric,
        metric_label=metric_label,
        methods=methods,
        colors=colors,
        threshold_mode="max",  # highest brightness before failure
        bin_centers=bin_centers,
        bin_width=0.2,
        blurb = "**Brightness Increase thresholds indicate the highest brightness factor (1.0–2.0) where watermark "
                "decoding remained successful. Higher values show better robustness to brightening.**"
    )

def summarize_crop_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str]
):
    bin_centers = [round(x, 2) for x in np.arange(0.4, 1.05, 0.1)]  # Crop ratios 0.4–1.0
    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="crop",
        metric=metric,
        metric_label=metric_label,
        methods=methods,
        colors=colors,
        threshold_mode="min",  # smallest crop ratio that still works
        bin_centers=bin_centers,
        bin_width=0.1,
        blurb = ("**Crop thresholds represent the smallest percentage of the image that could be retained (centered)"
                 " while still allowing successful decoding. Lower values indicate greater robustness to cropping.**")
    )

def summarize_mask_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str]
):
    bin_centers = [round(x, 2) for x in np.arange(0.0, 1.05, 0.05)]  # Mask coverage from 0.0 to 1.0
    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="mask",
        metric=metric,
        metric_label=metric_label,
        methods=methods,
        colors=colors,
        threshold_mode="max",  # lowest masking level that still succeeds
        bin_centers=bin_centers,
        bin_width=0.05,
        blurb = "**Mask thresholds represent the largest proportion of the image that could be "
                "obscured with a mask while still allowing successful decoding. Higher values indicate stronger robustness.**"
    )

def summarize_overlay_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str]
):
    bin_centers = [round(x, 2) for x in np.arange(0.0, 1.05, 0.1)]  # Overlay strength from 0.0 to 1.0
    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="overlay",
        metric=metric,
        metric_label=metric_label,
        methods=methods,
        colors=colors,
        threshold_mode="max",  # Higher overlay strength = more attack, so max successful is most robust
        bin_centers=bin_centers,
        bin_width=0.1,
        blurb = "**Overlay thresholds represent the highest opacity (alpha) of a logo overlaid on the "
                "image where watermark decoding still succeeded. Higher values reflect better resistance to visual obstructions.**"
    )

def summarize_resize_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str]
):
    # We go from full size (1.0) down to 0.1 — smaller values are more severe attacks
    bin_centers = [round(x, 2) for x in np.arange(1.0, 0.05, -0.1)]

    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="resize",
        metric=metric,  # typically "scale_factor"
        metric_label=metric_label,  # e.g., "Resize Scale Factor"
        methods=methods,
        colors=colors,
        threshold_mode="min",  # we're finding the lowest scale factor that still works
        bin_centers=bin_centers,
        bin_width=0.1,
        blurb = "**Resize thresholds indicate the smallest scaling factor (as a fraction of original size) "
                "where watermark decoding still succeeded. Lower values reflect better robustness to downscaling.**"
    )

def summarize_rotate_threshold(
    results_root: str,
    metric: str,
    metric_label: str,
    methods: List[str],
    colors: Dict[str, str],
):
    bin_centers = list(range(0, 20, 2))  # Rotation angles: 0–18 degrees
    summarize_all_threshold_results(
        results_root=results_root,
        attack_name="rotate",
        metric="angle",  # column name in the CSV
        metric_label=metric_label,
        methods=methods,
        colors=colors,
        threshold_mode="max",  # max rotation angle the watermark can survive
        bin_centers=bin_centers,
        bin_width=2,
        blurb="**Rotation thresholds reflect the maximum degree of rotation where watermark decoding was still successful.**"
    )


if __name__ == "__main__":
    '''
    '''
    summarize_noise_threshold(
        results_root="threshold_tests/noise_test_results",
        metric="std_dev",
        metric_label="Gaussian Noise (σ)",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"},
        bin_centers=[0, 5, 10, 15, 20, 25, 30, 35, 40],
        bin_width= 5
    )

    summarize_jpeg_threshold(
        results_root="threshold_tests/jpeg_test_results",
        metric="jpeg_quality",
        metric_label="JPEG Quality",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"},
    )

    summarize_decrease_brightness_threshold(
        results_root="threshold_tests/decrease_brightness_test_results",
        metric="brightness_factor",
        metric_label="Brightness Decrease",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"},
    )

    summarize_increase_brightness_threshold(
        results_root="threshold_tests/increase_brightness_test_results",
        metric="brightness_factor",
        metric_label="Brightness Increase",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"},
    )

    summarize_crop_threshold(
        results_root="threshold_tests/crop_test_results",
        metric="crop_ratio",
        metric_label="Crop Ratio",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"}
    )
    
    summarize_mask_threshold(
        results_root="threshold_tests/mask_test_results",
        metric="mask_fraction",  # this should match the column name in your CSV
        metric_label="Mask Fraction",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue","dwtDctSvd": "lightgreen","rivaGan": "salmon"}
    )

    summarize_overlay_threshold(
        results_root="threshold_tests/overlay_test_results",
        metric="alpha",
        metric_label="Overlay Alpha",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "rivaGan": "salmon"},
    )
    
    summarize_resize_threshold(
        results_root="threshold_tests/resize_test_results",
        metric="scale",
        metric_label="Resize Scale Factor",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={"dwtDct": "skyblue", "dwtDctSvd": "lightgreen", "rivaGan": "salmon"},
    )

    summarize_rotate_threshold(
        results_root="threshold_tests/rotate_test_results",
        metric="angle",
        metric_label="Rotation Angle (°)",
        methods=["dwtDct", "dwtDctSvd", "rivaGan"],
        colors={
            "dwtDct": "skyblue",
            "dwtDctSvd": "lightgreen",
            "rivaGan": "salmon"
        }
    )
