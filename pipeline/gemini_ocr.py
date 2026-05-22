from google import genai
from google.genai import types
import base64
import time
import os


class GeminiVision:
    """
    Gemini 1.5 Flash for vision tasks:
    1. OCR scanned PDF pages (extract Sinhala text from images)
    2. Generate descriptive alt text for textbook images
    """
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        self.request_count = 0
        self.last_request_time = 0

    def _rate_limit(self):
        """Respect 15 req/min free tier limit."""
        now = time.time()
        if now - self.last_request_time < 4:
            time.sleep(4 - (now - self.last_request_time))
        self.last_request_time = time.time()
        self.request_count += 1

    def ocr_page(self, image_base64: str, page_num: int) -> dict:
        """Extract text from scanned PDF page using Gemini Vision."""
        self._rate_limit()
        try:
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]

            image_bytes = base64.b64decode(image_base64)

            prompt = f"""You are processing page {page_num} of a Sri Lanka Ministry of Education Sinhala textbook for children.

Extract ALL visible text from this page:
- Preserve exact Sinhala Unicode characters
- Include headings, paragraphs, captions, page numbers
- Include exercise numbers and questions
- Include any English text you see
- Preserve line structure where meaningful
- Do NOT add any commentary or explanation

Output ONLY the extracted text:"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                ]
            )
            extracted = response.text.strip()

            return {
                "success": True,
                "text": extracted,
                "page": page_num,
                "method": "gemini_vision"
            }

        except Exception as e:
            print(f"Gemini OCR error page {page_num}: {e}")
            return {
                "success": False,
                "text": f"[Page {page_num} — OCR failed: {e}]",
                "page": page_num,
                "method": "gemini_error"
            }

    def generate_alt_text(self, image_base64: str,
                          context: str = "", page_num: int = 0) -> str:
        """Generate meaningful alt text for accessibility."""
        self._rate_limit()
        try:
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]

            image_bytes = base64.b64decode(image_base64)

            prompt = f"""This image is from a Sri Lanka primary school Sinhala textbook for children aged 6-14.

Surrounding text context: {context[:300] if context else 'None'}

Write clear descriptive alt text for a blind child:
- Be specific: describe what you see
- Mention colors, shapes, people, animals, objects
- Describe any text or labels in the image
- Keep under 150 characters
- Write in simple English
- Focus on educational content shown

Return ONLY the alt text, nothing else:"""

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                ]
            )
            return response.text.strip()[:200]

        except Exception as e:
            print(f"Alt text error: {e}")
            return f"Textbook illustration on page {page_num}"

    def test_connection(self) -> bool:
        """Test if Gemini API is working."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents="Say 'Gemini OK' in exactly those words"
            )
            return "Gemini OK" in response.text
        except Exception as e:
            print(f"Gemini test error: {e}")
            return False
