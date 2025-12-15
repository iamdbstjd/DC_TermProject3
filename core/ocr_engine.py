"""
Vision OCR Engine using GPT-4 Vision

Extracts text from images using OpenAI's GPT-4 Vision model.
No external dependencies required (no Tesseract).
"""
import os
import base64
from typing import Optional
from dataclasses import dataclass, field
from PIL import Image
import io

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import settings


@dataclass
class OCRResult:
    """Result of OCR processing."""
    text: str = ""
    confidence: float = 0.0
    language: str = "kor"
    
    def to_dict(self):
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language
        }


class VisionOCREngine:
    """
    OCR Engine using GPT-4 Vision.
    
    Sends images directly to GPT-4V for text extraction.
    Works with Korean and English documents.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Supports vision
    
    def extract_text(self, image_path: str) -> OCRResult:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            OCRResult with extracted text
        """
        try:
            # Read and encode image
            base64_image = self._encode_image(image_path)
            
            # Call GPT-4 Vision
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 한국 공공문서 OCR 전문가입니다.
이미지에서 모든 텍스트를 정확하게 추출해주세요.

규칙:
1. 이미지에 보이는 모든 텍스트를 그대로 추출
2. 줄바꿈과 구조를 최대한 유지
3. 표가 있으면 텍스트로 변환
4. 숫자, 날짜, 금액은 정확하게
5. 한글과 영어 모두 인식"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "이 공공문서 이미지에서 모든 텍스트를 추출해주세요."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )
            
            extracted_text = response.choices[0].message.content
            
            return OCRResult(
                text=extracted_text,
                confidence=95.0,  # GPT-4V is generally very accurate
                language="kor"
            )
            
        except Exception as e:
            return OCRResult(
                text=f"OCR 오류: {str(e)}",
                confidence=0.0,
                language="kor"
            )
    
    def extract_from_pil_image(self, image: Image.Image) -> OCRResult:
        """
        Extract text from a PIL Image object.
        
        Args:
            image: PIL Image
            
        Returns:
            OCRResult with extracted text
        """
        try:
            # Convert PIL Image to base64
            buffer = io.BytesIO()
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            image.save(buffer, format='JPEG', quality=95)
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Call GPT-4 Vision
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 한국 공공문서 OCR 전문가입니다.
이미지에서 모든 텍스트를 정확하게 추출해주세요.

규칙:
1. 이미지에 보이는 모든 텍스트를 그대로 추출
2. 줄바꿈과 구조를 최대한 유지
3. 표가 있으면 텍스트로 변환
4. 숫자, 날짜, 금액은 정확하게
5. 한글과 영어 모두 인식"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "이 공공문서 이미지에서 모든 텍스트를 추출해주세요."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )
            
            extracted_text = response.choices[0].message.content
            
            return OCRResult(
                text=extracted_text,
                confidence=95.0,
                language="kor"
            )
            
        except Exception as e:
            return OCRResult(
                text=f"OCR 오류: {str(e)}",
                confidence=0.0,
                language="kor"
            )
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


# Convenience function
def ocr_image(image_path: str) -> str:
    """Quick OCR function for a single image."""
    engine = VisionOCREngine()
    result = engine.extract_text(image_path)
    return result.text


# Keep backward compatibility with old OCREngine
OCREngine = VisionOCREngine
OCRBlock = None  # Not used in Vision OCR
