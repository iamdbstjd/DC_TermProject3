"""
Document Preprocessor Module

Handles image and PDF preprocessing for OCR.
"""
import os
from typing import List, Optional, Tuple
from PIL import Image
from dataclasses import dataclass

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


@dataclass
class PreprocessedImage:
    """Represents a preprocessed image."""
    image: Image.Image
    original_path: Optional[str]
    page_num: int
    width: int
    height: int


class DocumentPreprocessor:
    """
    Preprocesses documents (images/PDFs) for OCR processing.
    """
    
    def __init__(self):
        self.supported_image_formats = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
        self.supported_pdf_format = '.pdf'
    
    def preprocess_file(self, file_path: str) -> List[PreprocessedImage]:
        """
        Preprocess a document file (image or PDF).
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of PreprocessedImage objects
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == self.supported_pdf_format:
            return self._preprocess_pdf(file_path)
        elif ext in self.supported_image_formats:
            return self._preprocess_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _preprocess_image(self, image_path: str) -> List[PreprocessedImage]:
        """Preprocess a single image file."""
        image = Image.open(image_path)
        processed = self._enhance_image(image)
        
        return [PreprocessedImage(
            image=processed,
            original_path=image_path,
            page_num=1,
            width=processed.size[0],
            height=processed.size[1]
        )]
    
    def _preprocess_pdf(self, pdf_path: str) -> List[PreprocessedImage]:
        """Convert PDF pages to images and preprocess."""
        try:
            import fitz  # PyMuPDF
            
            images = []
            with fitz.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf, start=1):
                    # Render page to image
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to PIL Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    processed = self._enhance_image(img)
                    
                    images.append(PreprocessedImage(
                        image=processed,
                        original_path=pdf_path,
                        page_num=page_num,
                        width=processed.size[0],
                        height=processed.size[1]
                    ))
            
            return images
            
        except ImportError:
            # Fallback to pdf2image if PyMuPDF not available
            try:
                from pdf2image import convert_from_path
                
                pil_images = convert_from_path(pdf_path, dpi=200)
                images = []
                
                for page_num, img in enumerate(pil_images, start=1):
                    processed = self._enhance_image(img)
                    images.append(PreprocessedImage(
                        image=processed,
                        original_path=pdf_path,
                        page_num=page_num,
                        width=processed.size[0],
                        height=processed.size[1]
                    ))
                
                return images
                
            except ImportError:
                raise ImportError("Either PyMuPDF or pdf2image is required for PDF processing")
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image for better OCR results."""
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too small
        min_dimension = 1000
        if min(image.size) < min_dimension:
            scale = min_dimension / min(image.size)
            new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Resize if too large
        max_dimension = 4000
        if max(image.size) > max_dimension:
            scale = max_dimension / max(image.size)
            new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def auto_rotate(self, image: Image.Image) -> Tuple[Image.Image, int]:
        """
        Attempt to auto-rotate image based on EXIF data.
        
        Returns:
            Tuple of (rotated_image, rotation_degrees)
        """
        try:
            from PIL.ExifTags import TAGS
            
            exif = image._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'Orientation':
                        if value == 3:
                            return image.rotate(180, expand=True), 180
                        elif value == 6:
                            return image.rotate(270, expand=True), 270
                        elif value == 8:
                            return image.rotate(90, expand=True), 90
        except Exception:
            pass
        
        return image, 0
    
    def save_preprocessed_images(
        self, 
        images: List[PreprocessedImage], 
        output_dir: str
    ) -> List[str]:
        """Save preprocessed images to disk."""
        os.makedirs(output_dir, exist_ok=True)
        
        saved_paths = []
        for i, img_data in enumerate(images):
            filename = f"page_{img_data.page_num:03d}.png"
            output_path = os.path.join(output_dir, filename)
            img_data.image.save(output_path, "PNG")
            saved_paths.append(output_path)
        
        return saved_paths
