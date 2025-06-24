import cv2
import numpy as np
import os
import re
from imwatermark import WatermarkEncoder, WatermarkDecoder
WatermarkEncoder.loadModel()

def sanitize_filename(name: str) -> str:
    """
    Removes or replaces characters that may break markdown or filesystem compatibility.
    """
    name = name.replace(" ", "_")
    name = name.replace("(", "").replace(")", "").replace("°", "")
    name = re.sub(r'[^A-Za-z0-9_.-]', '_', name)  # Replace problematic chars like % with _
    return f"{name}.jpg"

def embed_watermark_64bit(image: np.ndarray, watermark_str: str = "qingquan", method: str = "dwtDct") -> np.ndarray:
    """
    Embeds a 64-bit watermark into the image using the specified method.
    """
    assert image.shape[0] >= 256 and image.shape[1] >= 256, "Image must be at least 256x256"
    assert len(watermark_str.encode("utf-8")) == 8, "Watermark must be 8 ASCII characters (64 bits)"

    # Convert to bits
    wm_bytes = watermark_str.encode("utf-8")
    wm_bits = np.unpackbits(np.frombuffer(wm_bytes, dtype=np.uint8))[:64]

    # Encode
    encoder = WatermarkEncoder()
    encoder.set_by_bits(wm_bits.tolist())
    return encoder.encode(image, method=method)

def decode_watermark_64bit(image: np.ndarray, method: str = "dwtDct") -> str:
    """
    Decodes a 64-bit watermark from the image using the specified method.
    """
    decoder = WatermarkDecoder(wm_type="bits", length=64)
    wm_bits = decoder.decode(image, method=method)
    wm_bytes = np.packbits(wm_bits)
    return wm_bytes.tobytes().decode("utf-8")

def safe_decode_watermark(image: np.ndarray, expected_text: str, method: str = "dwtDct") -> tuple[str, bool]:
    """
    Attempts to decode the watermark and handles decoding/bit errors gracefully.
    Returns (message, success).
    """
    from imwatermark import WatermarkDecoder
    import numpy as np

    decoder = WatermarkDecoder(wm_type="bits", length=64)
    try:
        bits = decoder.decode(image, method=method)
    except Exception as e:
        return f"[Decode Error] {type(e).__name__}: {e}", False

    try:
        raw_bytes = np.packbits(bits)
    except Exception as e:
        return f"[PackBits Error] {type(e).__name__}: {e}", False

    try:
        decoded = raw_bytes.tobytes().decode("utf-8")
    except Exception as e:
        return f"[UTF-8 Error] {type(e).__name__}: {e} | Raw: {raw_bytes[:8]}", False
        #change to instead of raising error, compare original & decoded message
        # to be able to see the difference instead of all the same error

    return decoded, decoded == expected_text

def embed_watermark_32bit(image: np.ndarray, watermark_str: str, method: str = "rivaGan") -> np.ndarray:
    assert method == "rivaGan", "Only RivaGan supports 32-bit watermarking"
    assert len(watermark_str.encode("utf-8")) == 4, "Watermark must be 4 ASCII characters (32 bits)"

    wm_bits = np.unpackbits(np.frombuffer(watermark_str.encode("utf-8"), dtype=np.uint8))[:32]
    encoder = WatermarkEncoder()
    encoder.set_by_bits(wm_bits.tolist())
    return encoder.encode(image, method=method)

def decode_watermark_32bit(image: np.ndarray, method: str = "rivaGan") -> str:
    """
    Decodes a 32-bit watermark from the image using RivaGan.
    """
    decoder = WatermarkDecoder(wm_type="bits", length=32)
    wm_bits = decoder.decode(image, method=method)
    wm_bytes = np.packbits(wm_bits)
    return wm_bytes.tobytes().decode("utf-8", errors="replace")

def safe_decode_watermark_32bit(image: np.ndarray, expected_text: str, method: str = "rivaGan") -> tuple[str, bool]:
    """
    Attempts to decode a 32-bit watermark and handles decoding/bit errors gracefully.
    Returns (decoded_text_or_error, success_boolean).
    """
    from imwatermark import WatermarkDecoder
    import numpy as np

    decoder = WatermarkDecoder(wm_type="bits", length=32)
    try:
        bits = decoder.decode(image, method=method)
    except Exception as e:
        return f"[Decode Error] {type(e).__name__}: {e}", False

    try:
        raw_bytes = np.packbits(bits)
    except Exception as e:
        return f"[PackBits Error] {type(e).__name__}: {e}", False

    try:
        decoded = raw_bytes.tobytes().decode("utf-8")
    except Exception as e:
        return f"[UTF-8 Error] {type(e).__name__}: {e} | Raw: {raw_bytes[:4]}", False

    return decoded, decoded == expected_text

def jpeg_compression_attack(image: np.ndarray, quality: int = 50) -> np.ndarray:
    """
    Applies JPEG compression to an image and returns the decompressed version.
    """
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, encimg = cv2.imencode('.jpg', image, encode_param)
    return cv2.imdecode(encimg, cv2.IMREAD_COLOR)

def resize_attack(image: np.ndarray, scale: float = 0.5) -> np.ndarray:
    """
    Resizes image to smaller size and back to original to simulate degradation.
    """
    h, w = image.shape[:2]
    resized = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(resized, (w, h), interpolation=cv2.INTER_LINEAR)

def gaussian_noise_attack(image: np.ndarray, mean=0, std=10) -> np.ndarray:
    """
    Adds Gaussian noise to an image.
    """
    noise = np.random.normal(mean, std, image.shape).astype(np.float32)
    noisy_image = cv2.add(image.astype(np.float32), noise)
    return np.clip(noisy_image, 0, 255).astype(np.uint8)

def crop_attack(image: np.ndarray, crop_percent_h: float = 0.1, crop_percent_w: float = 0.1) -> np.ndarray:
    """
    Crops a percentage of the image from all sides and resizes back to original dimensions.
    """
    h, w = image.shape[:2]
    ch, cw = int(h * crop_percent_h), int(w * crop_percent_w)
    cropped = image[ch:h - ch, cw:w - cw]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)


def brightness_attack(image: np.ndarray, factor: float = 1.5) -> np.ndarray:
    return np.clip(image.astype(np.float32) * factor, 0, 255).astype(np.uint8)

def overlay_attack(image: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    overlay = np.zeros_like(image)
    return cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)

def overlay_with_smiley(image: np.ndarray) -> np.ndarray:
    """
    Draws a smiley face on the image as an overlay attack.
    """
    overlay = image.copy()
    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    # Face outline
    cv2.circle(overlay, center, min(h, w) // 6, (0, 255, 255), thickness=10)

    # Eyes
    eye_y = center[1] - min(h, w) // 12
    eye_x_offset = min(h, w) // 15
    eye_radius = min(h, w) // 40
    cv2.circle(overlay, (center[0] - eye_x_offset, eye_y), eye_radius, (0, 0, 0), -1)
    cv2.circle(overlay, (center[0] + eye_x_offset, eye_y), eye_radius, (0, 0, 0), -1)

    # Smile
    smile_radius = min(h, w) // 10
    smile_center = (center[0], center[1] + min(h, w) // 20)
    cv2.ellipse(overlay, smile_center, (smile_radius, smile_radius // 2), 0, 0, 180, (0, 0, 0), thickness=3)

    return overlay

def mask_attack(image: np.ndarray, mask_fraction: float = 0.2) -> np.ndarray:
    h, w = image.shape[:2]
    mh, mw = int(h * mask_fraction), int(w * mask_fraction)
    y1, y2 = h // 2 - mh // 2, h // 2 + mh // 2
    x1, x2 = w // 2 - mw // 2, w // 2 + mw // 2
    masked = image.copy()
    masked[y1:y2, x1:x2] = 0
    return masked

def rotate_attack(image: np.ndarray, angle: float = 30.0) -> np.ndarray:
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def run_watermark_tests(
    method_name: str,
    image: np.ndarray,
    embed_fn,
    decode_fn,
    attacks: dict,
    output_dir: str
):
    """
    Embeds a watermark, applies attacks, and evaluates decoding robustness.

    Args:
        method_name (str): Name of the watermarking method.
        image (np.ndarray): Original image.
        embed_fn (function): Embedding function.
        decode_fn (function): Decoding function.
        attacks (dict): Dictionary of attack functions.
        output_dir (str): Directory to save attacked images.
    """
    watermarked = embed_fn(image)
    method_dir = os.path.join(output_dir, method_name)
    os.makedirs(method_dir, exist_ok=True)
    cv2.imwrite(os.path.join(method_dir, "original_watermarked.jpg"), watermarked)

    results = []
    for name, attack_fn in attacks.items():
        attacked_img = attack_fn(watermarked)
        filename = sanitize_filename(name)
        save_path = os.path.join(method_dir, filename)
        cv2.imwrite(save_path, attacked_img)

        decoded, success = decode_fn(attacked_img)

        if success:
            match_type = "✅"
        elif isinstance(decoded, str) and decoded != "" and decoded[0:4] in ["qing", "QING"]:  # heuristic for partial match
            match_type = "🟡"
        else:
            match_type = "❌"

        results.append((name, decoded[:25], match_type))

    # Print results table
    print(f"\n📊 Robustness Test Results for {method_name}:")
    print(f"{'Attack':30} | {'Decoded Watermark':25} | Result")
    print("-" * 70)
    for attack, decoded, result in results:
        print(f"{attack:30} | {decoded:25} | {result}")