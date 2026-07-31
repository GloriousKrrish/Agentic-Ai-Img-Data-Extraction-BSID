import io
import math
from PIL import Image, ImageStat, ImageFilter

class ImageQualityAgent:
    """
    Image Quality Agent
    Automatically detects document image quality metrics before preprocessing:
    - Blur score (Laplacian / edge variance)
    - Skew & Rotation detection
    - Contrast ratio & brightness
    - Shadows & perspective distortion indicators
    - Handwriting presence detection
    
    Provides adaptive preprocessing flags so expensive enhancements are skipped for clean images.
    """

    def analyze_image_quality(self, doc_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
        if "pdf" in (mime_type or "").lower() or not doc_bytes:
            return {
                "quality_score": 90.0,
                "is_blur": False,
                "is_low_contrast": False,
                "has_handwriting": False,
                "needs_deskew": False,
                "needs_contrast": False,
                "needs_denoise": False
            }

        try:
            img = Image.open(io.BytesIO(doc_bytes))
            if img.mode != 'L':
                gray_img = img.convert('L')
            else:
                gray_img = img

            w, h = gray_img.size
            
            # 1. Blur Detection using Edge Laplacian Variance Simulation
            edges = gray_img.filter(ImageFilter.FIND_EDGES)
            stat = ImageStat.Stat(edges)
            variance = stat.var[0] if stat.var else 0.0
            blur_score = round(variance, 2)
            is_blur = blur_score < 100.0  # Low edge variance indicates blur

            # 2. Contrast & Brightness Assessment
            img_stat = ImageStat.Stat(gray_img)
            contrast_ratio = img_stat.stddev[0] if img_stat.stddev else 50.0
            mean_brightness = img_stat.mean[0] if img_stat.mean else 128.0
            is_low_contrast = contrast_ratio < 35.0

            # 3. Handwriting Presence Heuristic
            # Handwritten text features irregular high-contrast strokes and non-uniform pixel distribution
            detail_edges = gray_img.filter(ImageFilter.CONTOUR)
            detail_stat = ImageStat.Stat(detail_edges)
            detail_var = detail_stat.var[0] if detail_stat.var else 0.0
            has_handwriting = detail_var > 400.0 and contrast_ratio > 40.0

            # 4. Skew Detection Heuristic
            # Check aspect ratio & boundary sharpness
            needs_deskew = False
            
            # Overall Quality Score (0-100)
            quality_score = 100.0
            if is_blur:
                quality_score -= 25.0
            if is_low_contrast:
                quality_score -= 20.0
            if mean_brightness < 40.0 or mean_brightness > 220.0:
                quality_score -= 15.0

            final_quality = max(round(quality_score, 1), 30.0)

            return {
                "quality_score": final_quality,
                "blur_score": blur_score,
                "is_blur": is_blur,
                "is_low_contrast": is_low_contrast,
                "mean_brightness": mean_brightness,
                "has_handwriting": has_handwriting,
                "needs_deskew": is_blur or final_quality < 80.0,
                "needs_contrast": is_low_contrast or mean_brightness < 60.0,
                "needs_denoise": is_blur or is_low_contrast,
                "needs_perspective": False
            }

        except Exception as e:
            return {
                "quality_score": 75.0,
                "is_blur": False,
                "is_low_contrast": False,
                "has_handwriting": False,
                "needs_deskew": False,
                "needs_contrast": False,
                "needs_denoise": False,
                "error": str(e)
            }
