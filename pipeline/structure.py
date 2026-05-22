import json
import re
import sys
import os

def structure_content(extracted: dict, minimax_key: str = "") -> dict:
    """Structure extracted content for EPUB/web output."""
    structured = {
        "title": extracted.get("title", "Sinhala Textbook"),
        "language": "si",
        "language_name": "Sinhala",
        "publisher": "Ministry of Education Sri Lanka",
        "extraction_method": extracted.get("extraction_method", "unknown"),
        "ai_enhanced": extracted.get("ai_enhanced", False),
        "total_pages": extracted.get("total_pages", 0),
        "accessibility_features": [
            "alternativeText",
            "captions",
            "readingOrder",
            "structuralNavigation",
            "tableOfContents",
            "index",
        ],
        "chapters": []
    }

    for chapter in extracted.get("chapters", []):
        title = clean_text(chapter.get("title", ""))
        content = chapter.get("content", "")

        structured_chapter = {
            "number": chapter["number"],
            "title": title,
            "html_content": build_html_content(chapter),
            "images": chapter.get("images", []),
            "word_count": count_words(content),
            "reading_time_minutes": max(1, count_words(content) // 150),
            "summary": chapter.get("summary", ""),
            "has_exercise": chapter.get("has_exercise", False),
            "page_start": chapter.get("page_start", 1),
        }
        structured["chapters"].append(structured_chapter)

    return structured

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', str(text)).strip()
    return text.replace('\x00', '')

def build_html_content(chapter: dict) -> str:
    """Build semantic HTML5 for chapter."""
    n = chapter["number"]
    title = clean_text(chapter.get("title", ""))
    html = f'<section id="ch-{n}" role="region" aria-label="{title}" lang="si">\n'
    html += f'<h2 tabindex="0">{title}</h2>\n'

    summary = chapter.get("summary", "")
    if summary:
        html += f'''<aside class="summary-box" role="note" aria-label="Chapter summary">
  <strong>Summary:</strong> {summary}
</aside>\n'''

    for img in chapter.get("images", []):
        if img.get("is_page_scan"):
            alt = img.get("alt", f"Page content")
            html += f'''<figure role="img" aria-label="{alt}">
  <img src="{img['data']}" alt="{alt}" loading="lazy" class="page-scan" tabindex="0" lang="si"/>
  <figcaption class="sr-only">{alt}</figcaption>
</figure>\n'''

    for para in chapter.get("paragraphs", []):
        p = clean_text(para)
        if p and len(p) > 5:
            html += f'<p tabindex="0" lang="si">{p}</p>\n'

    for img in chapter.get("images", []):
        if not img.get("is_page_scan"):
            alt = img.get("alt", "Textbook image")
            html += f'''<figure>
  <img src="{img['data']}" alt="{alt}" class="content-image" tabindex="0"/>
  <figcaption>{alt}</figcaption>
</figure>\n'''

    html += '</section>\n'
    return html

def count_words(text: str) -> int:
    return len(str(text).split())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python structure.py <extracted.json>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    minimax_key = os.environ.get("MINIMAX_API_KEY", "")
    result = structure_content(data, minimax_key)
    out = sys.argv[2] if len(sys.argv) > 2 else "structured.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Structured: {len(result['chapters'])} chapters")
