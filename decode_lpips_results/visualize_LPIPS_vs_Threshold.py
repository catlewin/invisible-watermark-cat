import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns


def plot_lpips_vs_threshold(df, attack_name, method, image_name, output_dir):
    # Drop rows with missing threshold or lpips_score
    df_clean = df.dropna(subset=["threshold", "lpips_score"])
    if df_clean.empty:
        print(f"⚠️  Skipping {image_name} - no valid data.")
        return

    plt.figure()
    plt.plot(df_clean["threshold"], df_clean["lpips_score"], marker="o")
    plt.title(f"LPIPS vs Threshold\n{attack_name} - {method} - {image_name}")
    plt.xlabel("Attack Threshold")
    plt.ylabel("LPIPS Score")
    plt.grid(True)
    plt.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{image_name}_lpips_vs_threshold.png")
    plt.savefig(output_path)
    plt.close()
    print(f"✅ Saved plot: {output_path}")

def visualize_all_lpips_vs_threshold(base_dir="decode_lpips_results"):
    print("🔍 Starting visualization loop...")
    for attack_dir in os.listdir(base_dir):
        if not attack_dir.endswith("_test_results"):
            continue  # 🚫 Skip __pycache__ or unrelated folders

        attack_path = os.path.join(base_dir, attack_dir)
        if not os.path.isdir(attack_path):
            continue

        print(f"📂 Attack folder: {attack_dir}")

        attack_name = attack_dir.replace("_test_results", "")

        # ✅ Dive into 512x512 subdirectory
        resolution_path = os.path.join(attack_path, "512x512")
        if not os.path.isdir(resolution_path):
            print(f"⚠️  Missing resolution folder in {attack_path}")
            continue

        for method in os.listdir(resolution_path):
            method_path = os.path.join(resolution_path, method)
            if not os.path.isdir(method_path):
                continue
            print(f"  📁 Method folder: {method}")

            for file in os.listdir(method_path):
                if not file.endswith("_merged_results.csv"):
                    continue
                print(f"    🧾 File: {file}")

                image_name = file.replace("_merged_results.csv", "")
                csv_path = os.path.join(method_path, file)
                df = pd.read_csv(csv_path)

                output_dir = os.path.join(method_path, "lpips_graphs")
                plot_lpips_vs_threshold(df, attack_name, method, image_name, output_dir)

def plot_avg_lpips_vs_threshold(base_dir="decode_lpips_results"):
    for attack_dir in os.listdir(base_dir):
        if not attack_dir.endswith("_test_results"):
            continue  # 🚫 Skip __pycache__ or unrelated folders

        attack_path = os.path.join(base_dir, attack_dir)
        if not os.path.isdir(attack_path):
            continue

        attack_name = attack_dir.replace("_test_results", "")
        for method in os.listdir(os.path.join(attack_path, "512x512")):
            method_path = os.path.join(attack_path, "512x512", method)
            if not os.path.isdir(method_path):
                continue

            dfs = []
            for file in os.listdir(method_path):
                if not file.endswith("_merged_results.csv"):
                    continue

                df = pd.read_csv(os.path.join(method_path, file))
                if "threshold" not in df.columns or "lpips_score" not in df.columns:
                    continue
                df_clean = df.dropna(subset=["threshold", "lpips_score"])
                dfs.append(df_clean[["threshold", "lpips_score"]])

            if not dfs:
                print(f"⚠️  No valid LPIPS data found for {attack_name} - {method}")
                continue

            combined_df = pd.concat(dfs, ignore_index=True)
            avg_df = combined_df.groupby("threshold", as_index=False).mean()

            plt.figure()
            plt.plot(avg_df["threshold"], avg_df["lpips_score"], marker="o")
            plt.title(f"Average LPIPS vs Threshold\n{attack_name} - {method}")
            plt.xlabel("Attack Threshold")
            plt.ylabel("Average LPIPS Score")
            plt.grid(True)
            plt.tight_layout()

            output_dir = os.path.join(method_path, "lpips_graphs")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"avg_lpips_vs_threshold_{attack_name}_{method}.png")
            plt.savefig(output_path)
            plt.close()
            print(f"✅ Saved average plot: {output_path}")


def load_all_merged_data(base_dir):
    data = []
    for attack_dir in os.listdir(base_dir):
        if not attack_dir.endswith("_test_results"):
            continue
        attack_path = os.path.join(base_dir, attack_dir, "512x512")
        if not os.path.isdir(attack_path):
            continue
        attack_name = attack_dir.replace("_test_results", "")
        for method in os.listdir(attack_path):
            method_path = os.path.join(attack_path, method)
            if not os.path.isdir(method_path):
                continue
            for file in os.listdir(method_path):
                if file.endswith("_merged_results.csv"):
                    image_name = file.replace("_merged_results.csv", "")
                    csv_path = os.path.join(method_path, file)
                    df = pd.read_csv(csv_path)
                    df["attack"] = attack_name
                    df["method"] = method
                    df["image"] = image_name
                    data.append(df)
    return pd.concat(data, ignore_index=True)

def compute_semantic_severity(df):
    """
    Adds a 'semantic_severity' column to a DataFrame based on attack-specific normalization.
    The severity reflects how strongly an attack alters the image, normalized to 0-1.
    """

    # Define which attacks get more severe as threshold decreases (inverted scale)
    inverted_attacks = {"crop", "jpeg", "decrease_brightness", "resize"}

    # Prepare new column
    df = df.copy()
    df["semantic_severity"] = float("nan")

    # Process each attack individually
    for attack in df["attack"].unique():
        subset = df[df["attack"] == attack]
        min_val = subset["threshold"].min()
        max_val = subset["threshold"].max()

        # Avoid divide-by-zero
        if min_val == max_val:
            df.loc[df["attack"] == attack, "semantic_severity"] = 0.0
            continue

        # Normalize thresholds
        norm = (subset["threshold"] - min_val) / (max_val - min_val)

        # Reverse if needed
        if attack in inverted_attacks:
            severity = 1.0 - norm
        else:
            severity = norm

        # Assign back
        df.loc[df["attack"] == attack, "semantic_severity"] = severity

    return df


def plot_avg_lpips_by_threshold(base_dir="decode_lpips_results"):
    df_all = load_all_merged_data(base_dir)
    df_clean = df_all.dropna(subset=["threshold", "lpips_score"])

    # ✅ Add semantic severity
    df_clean = compute_semantic_severity(df_clean)

    # 🔢 Average LPIPS grouped by method + attack + severity
    df_grouped = df_clean.groupby(["method", "attack", "semantic_severity"]).agg(
        avg_lpips_score=("lpips_score", "mean")
    ).reset_index()

    # 📊 Plot 1 graph per method
    methods = df_grouped["method"].unique()
    for method in methods:
        df_method = df_grouped[df_grouped["method"] == method]

        plt.figure(figsize=(10, 6))
        sns.lineplot(data=df_method, x="semantic_severity", y="avg_lpips_score", hue="attack", marker="o")
        plt.title(f"Average LPIPS vs Semantic Severity — {method}")
        plt.xlabel("Semantic Severity (0 = weakest attack, 1 = strongest)")
        plt.ylabel("Average LPIPS Score")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"avg_lpips_vs_semantic_severity_{method}.png")
        print(f"✅ Saved: avg_lpips_vs_semantic_severity_{method}.png")

def compute_semantic_severity_row(row, ranges_lookup):
    attack = row["attack"]
    threshold = row["threshold"]

    if attack not in ranges_lookup:
        return None

    min_val = ranges_lookup[attack]["min_val"]
    max_val = ranges_lookup[attack]["max_val"]

    # Reverse only for known cases
    reverse = attack in {"crop", "jpeg", "decrease_brightness", "resize"}

    try:
        severity = (threshold - min_val) / (max_val - min_val)
        severity = max(0.0, min(severity, 1.0))  # Clamp
        if reverse:
            severity = 1.0 - severity
        return severity
    except:
        return None



def plot_lpips_vs_severity_with_decode_markers(base_dir="decode_lpips_results", method="rivaGan"):
    df_all = load_all_merged_data(base_dir)
    df_all = df_all[df_all["method"] == method]

    # Ensure threshold column exists by mapping known variants
    threshold_column_candidates = ["threshold", "crop_ratio", "mask_fraction", "jpeg_quality", "brightness_factor",
                                   "noise_level", "overlay_opacity", "resize_factor", "rotate_degrees"]

    # Find which one is actually in the DataFrame
    found_threshold_col = next((col for col in threshold_column_candidates if col in df_all.columns), None)

    if not found_threshold_col:
        raise ValueError("❌ Could not find any known threshold column in merged CSV.")

    # Rename it to 'threshold' for consistency
    if found_threshold_col != "threshold":
        df_all = df_all.rename(columns={found_threshold_col: "threshold"})

    # Drop rows missing critical values
    df_all = df_all.dropna(subset=["threshold", "lpips_score", "success"])

    # Get actual threshold min/max for each attack
    attack_threshold_ranges = (
        df_all.groupby("attack")["threshold"]
        .agg(["min", "max"])
        .rename(columns={"min": "min_val", "max": "max_val"})
        .to_dict(orient="index")
    )

    # Compute semantic severity
    df_all["semantic_severity"] = df_all.apply(
        lambda row: compute_semantic_severity_row(row, attack_threshold_ranges), axis=1
    )

    # Group by image
    images = df_all["image"].unique()
    for image in images:
        df_image = df_all[df_all["image"] == image]

        # Get a distinct color per attack
        attack_list = df_image["attack"].unique()
        color_map = {attack: color for attack, color in zip(attack_list, plt.cm.tab20.colors)}

        # Find and verify clean row
        clean_rows = df_image[(df_image["semantic_severity"] == 0) & (df_image["success"] == True)]
        if clean_rows.empty:
            print(f"⛔ Skipping {image}: no successful clean row found")
            continue

        plt.figure(figsize=(10, 6))
        for attack in attack_list:
            if attack == "clean":
                continue

            df_attack = df_image[df_image["attack"] == attack]
            df_attack = df_attack[df_attack["semantic_severity"].notna()]
            df_attack = df_attack.sort_values(by="semantic_severity")

            color = color_map[attack]

            # Plot full line (success + failure) with correct color
            plt.plot(df_attack["semantic_severity"], df_attack["lpips_score"], "-", color=color)

            # Overlay markers for success/failure
            success = df_attack[df_attack["success"] == True]
            failure = df_attack[df_attack["success"] == False]

            plt.plot(success["semantic_severity"], success["lpips_score"], "o", color=color, label=f"{attack} ✓")
            plt.plot(failure["semantic_severity"], failure["lpips_score"], "x", color=color, label=f"{attack} ✗")

        plt.title(f"LPIPS vs Semantic Severity with Decode Status — {image} ({method})")
        plt.xlabel("Semantic Severity (0 = weakest attack, 1 = strongest)")
        plt.ylabel("LPIPS Score")

        # Convert lpips_score to float, ignoring non-numeric entries
        df_image["lpips_score"] = pd.to_numeric(df_image["lpips_score"], errors="coerce")

        # Get max LPIPS score from valid values
        lpips_max = df_image["lpips_score"].dropna().max()

        # Slight padding, allow overflow up to 1.1 if needed
        ymax = max(1.0, min(1.1, lpips_max * 1.1))
        plt.ylim(0, ymax)

        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        save_dir = os.path.join(base_dir, f"{method}_imagewise_decode_graphs")
        os.makedirs(save_dir, exist_ok=True)
        plt.savefig(os.path.join(save_dir, f"{image}_lpips_decode_status.png"))
        plt.close()
        print(f"✅ Saved: {image}_lpips_decode_status.png")

def extract_first_failure_lpips_from_csv(base_dir="decode_lpips_results"):
    from collections import defaultdict

    df_all = load_all_merged_data(base_dir)
    df_all = df_all[df_all["can_decode_clean"] == True]
    df_all = df_all[df_all["attack_type"] != "clean"]

    # Infer correct threshold column
    threshold_candidates = [
        "threshold", "crop_ratio", "jpeg_quality", "brightness_factor", "std_dev",
        "alpha", "scale", "angle", "mask_fraction"
    ]
    found_threshold = next((col for col in threshold_candidates if col in df_all.columns), None)
    if not found_threshold:
        raise ValueError("❌ Could not find a known threshold column in merged data.")

    if found_threshold != "threshold":
        df_all = df_all.rename(columns={found_threshold: "threshold"})

    df_all = df_all.dropna(subset=["threshold", "lpips_score", "success"])

    # Compute semantic severity
    attack_threshold_ranges = (
        df_all.groupby("attack")["threshold"]
        .agg(["min", "max"])
        .rename(columns={"min": "min_val", "max": "max_val"})
        .to_dict(orient="index")
    )
    df_all["semantic_severity"] = df_all.apply(
        lambda row: compute_semantic_severity_row(row, attack_threshold_ranges), axis=1
    )

    # Sort and collect first failures
    records = []
    grouped = df_all.groupby(["method", "image", "attack"])
    for (method, image, attack), group in grouped:
        group_sorted = group.sort_values("semantic_severity")
        for _, row in group_sorted.iterrows():
            if not row["success"]:
                records.append({
                    "method": method,
                    "image": image,
                    "attack": attack,
                    "lpips_score": row["lpips_score"],
                    "semantic_severity": row["semantic_severity"]
                })
                break  # first failure only

    # debugging
    # for record in records:
    #    print(record)

    return pd.DataFrame(records)


def plot_first_failure_lpips_by_image_per_method(df_summary, save_dir="first_failure_lpips_plots"):
    os.makedirs(save_dir, exist_ok=True)

    for method in df_summary["method"].unique():
        df_method = df_summary[df_summary["method"] == method]

        plt.figure(figsize=(14, 7))
        sns.barplot(
            data=df_method,
            x="image", y="lpips_score", hue="attack", ci=None
        )
        plt.title(f"LPIPS Score at First Decode Failure — {method}")
        plt.ylabel("LPIPS Score at First Failure")
        plt.xlabel("Image")

        # Get max LPIPS score from valid values
        lpips_max = df_method["lpips_score"].dropna().max()

        # Slight padding
        ymax = lpips_max + 0.05
        print(ymax, "\n\n")
        plt.ylim(0, ymax)

        plt.xticks(rotation=45)
        plt.legend(title="Attack", bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.tight_layout()

        save_path = os.path.join(save_dir, f"{method}_lpips_first_failure_by_image.png")
        plt.savefig(save_path)
        plt.close()
        print(f"✅ Saved: {save_path}")


def plot_avg_first_failure_lpips(df_summary, save_path=None, base_dir="decode_lpips_results"):
    import numpy as np

    # Start from existing grouped data
    avg_df = df_summary.groupby(["attack", "method"])["lpips_score"].mean().reset_index()

    # 💡 Add static attacks (denoising, upscale) manually
    static_attacks = ["denoising", "upscale"]
    records = []

    for attack in static_attacks:
        attack_dir = os.path.join(base_dir, f"{attack}_test_results", "512x512")
        if not os.path.isdir(attack_dir):
            print(f"⚠️ Missing folder for {attack}, skipping.")
            continue

        for method in os.listdir(attack_dir):
            method_path = os.path.join(attack_dir, method)
            if not os.path.isdir(method_path):
                continue

            lpips_scores = []

            for file in os.listdir(method_path):
                if not file.endswith("_merged_results.csv"):
                    continue

                df = pd.read_csv(os.path.join(method_path, file))

                # Ensure 'attack' column exists (fallback to 'attack_type')
                if "attack" not in df.columns and "attack_type" in df.columns:
                    df = df.rename(columns={"attack_type": "attack"})

                # Skip if we still don't have an 'attack' column
                if "attack" not in df.columns:
                    print(f"⚠️ Skipping {file} — no 'attack' column.")
                    continue

                # Make sure clean image decoded
                if not df[df["attack"] == "clean"]["success"].any():
                    continue

                df = df[df["attack"] == attack]

                df = df.sort_values("lpips_score")

                for _, row in df.iterrows():
                    if not row["success"]:
                        lpips_scores.append(row["lpips_score"])
                        break

            if lpips_scores:
                avg_score = np.mean(lpips_scores)
                records.append({
                    "attack": attack,
                    "method": method,
                    "lpips_score": avg_score
                })
            else:
                print(f"⚠️ No failures found for {attack} - {method}")

    # Append to avg_df
    if records:
        static_df = pd.DataFrame(records)
        avg_df = pd.concat([avg_df, static_df], ignore_index=True)

    # 📊 Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=avg_df,
        x="attack", y="lpips_score", hue="method", ci=None
    )
    plt.title("Average LPIPS Score at First Decode Failure (Per Attack)")
    plt.ylabel("Average LPIPS Score at First Failure")
    plt.xlabel("Attack Type")
    lpips_max = avg_df["lpips_score"].max()
    plt.ylim(0, lpips_max + 0.05)
    plt.xticks(rotation=45)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        print(f"✅ Saved: {save_path}")
    else:
        plt.show()





if __name__ == "__main__":
    #plot_avg_lpips_by_threshold("decode_lpips_results")
    #plot_lpips_vs_severity_with_decode_markers(method="dwtDctSvd")

    df_summary = extract_first_failure_lpips_from_csv()
    plot_avg_first_failure_lpips(df_summary, "LPIPS_Threshold_Graphs/avg_first_failure_lpips.png")

    '''
    # Step 1: Extract the summary from the CSVs
    df_summary = extract_first_failure_lpips_from_csv()

    # Step 2: Plot per-image bar chart
    plot_first_failure_lpips_by_image_per_method(df_summary)

    # Step 3: Plot per-attack average across all images
    plot_avg_first_failure_lpips(df_summary, save_path="decode_lpips_results/avg_first_failure_lpips.png")
'''