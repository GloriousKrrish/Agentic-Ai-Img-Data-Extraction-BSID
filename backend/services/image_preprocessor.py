import io
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

def preprocess_image(file_bytes: bytes) -> tuple[bytes, dict]:
    """
    Enhances image quality for OCR and Vision models:
    - Auto-rotates using EXIF orientation metadata
    - Adjusts contrast and sharpness
    - Converts to RGB if needed
    Returns enhanced image bytes and quality metadata.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        
        # 1. Normalize orientation from EXIF
        img = ImageOps.exif_transpose(img)
        
        # 2. Convert palette/grayscale/RGBA to RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # 3. Apply subtle contrast enhancement & sharpening
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        sharpener = ImageEnhance.Sharpness(img)
        img = sharpener.enhance(1.3)
        
        # Output enhanced JPEG bytes
        output_buffer = io.BytesIO()
        img.save(output_buffer, format='JPEG', quality=95)
        enhanced_bytes = output_buffer.getvalue()
        
        metadata = {
            "processed": True,
            "width": img.width,
            "height": img.height,
            "orientation_corrected": True,
            "enhanced": True
        }
        return enhanced_bytes, metadata
    except Exception as e:
        return file_bytes, {"processed": False, "error": str(e)}
