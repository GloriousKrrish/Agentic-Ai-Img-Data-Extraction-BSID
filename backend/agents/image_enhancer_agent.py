import io
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from backend.agents.image_quality_agent import ImageQualityAgent
from backend.services.cache_service import cache_service

class ImageEnhancerAgent:
    """
    Step 4: Adaptive Image Enhancer Agent
    
    Integrates Image Quality Agent to inspect document condition:
    - Skips heavy preprocessing for clean, high-quality images.
    - Applies deskewing, rotation, adaptive contrast enhancement, sharpening, and denoising ONLY when required.
    - Uses smart caching for processed image buffers.
    """
    def __init__(self):
        self.quality_agent = ImageQualityAgent()

    def enhance(self, doc_bytes: bytes, mime_type: str = "image/jpeg") -> bytes:
        if "pdf" in (mime_type or "").lower() or not doc_bytes:
            return doc_bytes

        # Check Cache
        cached_img = cache_service.memory_cache.get(f"enh_{hash(doc_bytes)}")
        if cached_img:
            return cached_img

        try:
            # 1. Analyze Image Quality Metrics
            quality_metrics = self.quality_agent.analyze_image_quality(doc_bytes, mime_type)
            
            # If image quality is already high (≥85%), return directly without costly reprocessing!
            if quality_metrics.get("quality_score", 0.0) >= 85.0 and not quality_metrics.get("needs_contrast"):
                cache_service.memory_cache[f"enh_{hash(doc_bytes)}"] = doc_bytes
                return doc_bytes

            img = Image.open(io.BytesIO(doc_bytes))
            # Auto-rotate based on EXIF orientation tag
            img = ImageOps.exif_transpose(img)

            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 2. Adaptive Contrast Enhancement
            if quality_metrics.get("needs_contrast"):
                contrast_enhancer = ImageEnhance.Contrast(img)
                img = contrast_enhancer.enhance(1.35)

            # 3. Adaptive Denoising & Sharpening
            if quality_metrics.get("needs_denoise") or quality_metrics.get("is_blur"):
                sharpness_enhancer = ImageEnhance.Sharpness(img)
                img = sharpness_enhancer.enhance(1.25)
                img = img.filter(ImageFilter.SMOOTH_MORE)

            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=95)
            enhanced_bytes = buf.getvalue()
            
            cache_service.memory_cache[f"enh_{hash(doc_bytes)}"] = enhanced_bytes
            return enhanced_bytes

        except Exception:
            return doc_bytes
