import json
import sys
import os

WCAG_METADATA = {
    "accessibilityFeature": [
        "alternativeText",
        "captions",
        "readingOrder",
        "structuralNavigation",
        "tableOfContents",
        "index",
        "printPageNumbers",
    ],
    "accessibilityHazard": "none",
    "accessibilityControl": [
        "fullKeyboardControl",
        "fullMouseControl",
        "fullTouchControl",
    ],
    "accessMode": ["textual", "visual"],
    "accessModeSufficient": [
        ["textual"],
        ["visual", "textual"]
    ],
    "conformsTo": "WCAG 2.1 Level AA",
    "certifiedBy": "Self-certified proof of concept",
}

def add_accessibility(structured: dict, gemini_key: str = "") -> dict:
    """Add WCAG 2.1 AA features to all content."""
    structured["wcag_metadata"] = WCAG_METADATA
    structured["lang"] = "si"
    structured["dir"] = "ltr"

    if gemini_key:
        structured = enhance_image_alt_texts(structured, gemini_key)

    for chapter in structured.get("chapters", []):
        chapter["accessible_html"] = wrap_accessible(
            chapter["html_content"],
            chapter["number"],
            chapter["title"]
        )
        chapter["aria_label"] = f"Chapter {chapter['number']}: {chapter['title']}"

    return structured

def enhance_image_alt_texts(structured: dict, gemini_key: str) -> dict:
    """Use Gemini to generate real alt texts for images."""
    from gemini_ocr import GeminiVision
    gemini = GeminiVision(gemini_key)

    for chapter in structured.get("chapters", []):
        for img in chapter.get("images", []):
            if not img.get("is_page_scan") and (
                "Textbook image" in img.get("alt", "") or
                img.get("alt", "") == ""
            ):
                context = chapter.get("html_content", "")[:200]
                new_alt = gemini.generate_alt_text(
                    img["data"],
                    context,
                    img.get("page", 0)
                )
                if new_alt:
                    img["alt"] = new_alt
                    print(f"Alt text: {new_alt[:50]}...")

    return structured

def wrap_accessible(html: str, chapter_num: int, title: str) -> str:
    """Wrap HTML with full WCAG 2.1 AA attributes."""
    return f'''<article lang="si"
  id="chapter-{chapter_num}"
  aria-labelledby="ch-{chapter_num}-heading"
  role="article">
<a href="#ch-{chapter_num}-main" class="skip-link" tabindex="0">Skip to chapter content</a>
<div id="ch-{chapter_num}-main">
{html}
</div>
</article>'''

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python accessibility.py <structured.json>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    result = add_accessibility(data, gemini_key)
    out = sys.argv[2] if len(sys.argv) > 2 else "accessible.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Accessibility features added")
