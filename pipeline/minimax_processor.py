import requests
import json
import time

class MinimaxProcessor:
    """
    MiniMax M2.5 for text processing tasks.
    NOTE: Text ONLY — no image capabilities
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.minimax.io/anthropic/v1/messages"
        self.model = "MiniMax-M2.5"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

    def _call(self, prompt: str, max_tokens: int = 1000) -> str:
        """Make API call to MiniMax."""
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                # MiniMax may return thinking + text blocks; find the text block
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        return block["text"]
                return ""
            else:
                print(f"MiniMax error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            print(f"MiniMax call error: {e}")
            return ""

    def structure_text(self, raw_text: str, page_num: int) -> dict:
        """Structure extracted text into semantic components."""
        if not raw_text.strip():
            return {
                "title": None,
                "is_new_chapter": False,
                "paragraphs": [],
                "has_exercise": False,
                "exercise_text": ""
            }

        prompt = f"""Analyze this text extracted from page {page_num} of a Sri Lanka primary school Sinhala textbook.

Text:
{raw_text[:2000]}

Return a JSON object with this exact structure:
{{
  "title": "chapter or section heading if found, null otherwise",
  "is_new_chapter": true or false,
  "paragraphs": ["paragraph 1", "paragraph 2"],
  "has_exercise": true or false,
  "exercise_text": "exercise content if found, empty string otherwise"
}}

Rules:
- title: only if there is a clear heading/title
- is_new_chapter: true if this page starts a new chapter
- paragraphs: list of content paragraphs (Sinhala text preserved)
- Return ONLY valid JSON, no other text"""

        result = self._call(prompt, 800)
        try:
            if '```' in result:
                parts = result.split('```')
                for part in parts:
                    part = part.strip()
                    if part.startswith('json'):
                        part = part[4:]
                    if part.startswith('{'):
                        result = part
                        break
            return json.loads(result.strip())
        except:
            return {
                "title": None,
                "is_new_chapter": False,
                "paragraphs": [raw_text] if raw_text else [],
                "has_exercise": False,
                "exercise_text": ""
            }

    def generate_summary(self, chapter_text: str, chapter_title: str) -> str:
        """Generate simple English summary for accessibility."""
        if not chapter_text.strip():
            return ""

        prompt = f"""Chapter: {chapter_title}

Content: {chapter_text[:1500]}

Write a simple 2-3 sentence English summary that an 8-year-old child could understand.
Focus on the main educational topic. Be clear, simple, and encouraging.

Return ONLY the summary text:"""

        return self._call(prompt, 200).strip()

    def clean_sinhala_text(self, text: str) -> str:
        """Clean and normalize extracted Sinhala text."""
        if not text.strip():
            return text

        prompt = f"""Clean this Sinhala text extracted by OCR from a textbook. Fix obvious errors while preserving meaning.

Text: {text[:1000]}

Rules:
- Fix clear OCR errors in Sinhala characters
- Preserve original Sinhala Unicode
- Fix spacing issues
- Return ONLY the cleaned text, no explanation"""

        result = self._call(prompt, 500)
        return result.strip() if result else text

    def test_connection(self) -> bool:
        """Test MiniMax API connection."""
        result = self._call("Reply with exactly: MiniMax OK", 300)
        return "MiniMax OK" in result if result else False
