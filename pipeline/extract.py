import fitz
import json
import os
import sys
import base64
from pathlib import Path

def extract_pdf(pdf_path: str, gemini_key: str = "", minimax_key: str = "") -> dict:
    """Extract content from PDF."""
    doc = fitz.open(pdf_path)

    result = {
        "title": Path(pdf_path).stem,
        "language": "si",
        "language_name": "Sinhala",
        "total_pages": len(doc),
        "is_text_based": False,
        "extraction_method": "unknown",
        "ai_enhanced": False,
        "chapters": [],
        "metadata": {
            "author": "Ministry of Education Sri Lanka",
            "subject": "Primary Education",
        }
    }

    sample_text = ""
    for i, page in enumerate(doc):
        if i >= 3:
            break
        sample_text += page.get_text()

    result["is_text_based"] = len(sample_text.strip()) > 100

    print(f"PDF type: {'text-based' if result['is_text_based'] else 'scanned'}")
    print(f"Pages: {len(doc)}")

    if result["is_text_based"]:
        result["extraction_method"] = "direct_text"
        result["chapters"] = extract_text_based(doc, minimax_key)
    elif gemini_key:
        result["extraction_method"] = "gemini_vision_ocr"
        result["ai_enhanced"] = True
        result["chapters"] = extract_scanned_with_gemini(doc, gemini_key, minimax_key)
    else:
        result["extraction_method"] = "render_pages"
        result["chapters"] = extract_rendered_pages(doc)

    doc.close()
    return result

def extract_text_based(doc, minimax_key: str = "") -> list:
    """Extract from text-based PDF."""
    from minimax_processor import MinimaxProcessor

    minimax = MinimaxProcessor(minimax_key) if minimax_key else None
    chapters = []
    current_chapter = None
    chapter_num = 0

    for page_num, page in enumerate(doc):
        text = page.get_text().strip()
        if not text:
            continue

        images = extract_page_images(page, page_num)

        if minimax and text:
            structured = minimax.structure_text(text, page_num + 1)
            if structured.get("is_new_chapter") or structured.get("title"):
                chapter_num += 1
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = {
                    "number": chapter_num,
                    "title": structured.get("title") or f"Chapter {chapter_num}",
                    "content": text,
                    "paragraphs": structured.get("paragraphs", [text]),
                    "images": images,
                    "page_start": page_num + 1,
                    "summary": "",
                    "has_exercise": structured.get("has_exercise", False),
                }
            else:
                if current_chapter is None:
                    chapter_num += 1
                    current_chapter = {
                        "number": chapter_num,
                        "title": "Introduction",
                        "content": "",
                        "paragraphs": [],
                        "images": [],
                        "page_start": 1,
                        "summary": "",
                        "has_exercise": False,
                    }
                current_chapter["content"] += "\n" + text
                current_chapter["paragraphs"].extend(structured.get("paragraphs", []))
                current_chapter["images"].extend(images)
        else:
            if chapter_num == 0:
                chapter_num = 1
                current_chapter = {
                    "number": 1,
                    "title": "Content",
                    "content": text,
                    "paragraphs": [p for p in text.split('\n') if p.strip()],
                    "images": images,
                    "page_start": 1,
                    "summary": "",
                    "has_exercise": False,
                }
            else:
                current_chapter["content"] += "\n" + text
                current_chapter["images"].extend(images)

    if current_chapter:
        chapters.append(current_chapter)

    if minimax:
        for ch in chapters:
            if ch["content"]:
                ch["summary"] = minimax.generate_summary(ch["content"], ch["title"])
                print(f"Summary: {ch['title'][:40]}...")

    if not chapters:
        chapters = [create_empty_chapter(1)]

    return chapters

def extract_scanned_with_gemini(doc, gemini_key: str, minimax_key: str = "") -> list:
    """Use Gemini Vision to OCR scanned PDF pages."""
    from gemini_ocr import GeminiVision
    from minimax_processor import MinimaxProcessor

    gemini = GeminiVision(gemini_key)
    minimax = MinimaxProcessor(minimax_key) if minimax_key else None

    print("Using Gemini Vision for OCR...")
    chapters = []
    chapter_num = 0
    current_chapter = None

    for page_num, page in enumerate(doc):
        print(f"Processing page {page_num + 1}/{len(doc)}...")

        mat = fitz.Matrix(180/72, 180/72)
        pix = page.get_pixmap(matrix=mat)
        img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        img_data_url = f"data:image/png;base64,{img_b64}"

        ocr_result = gemini.ocr_page(img_b64, page_num + 1)
        extracted_text = ocr_result.get("text", "")

        if minimax and extracted_text:
            extracted_text = minimax.clean_sinhala_text(extracted_text)

        structured = {}
        if minimax and extracted_text:
            structured = minimax.structure_text(extracted_text, page_num + 1)

        is_new_chapter = structured.get("is_new_chapter", False)
        page_title = structured.get("title")

        if is_new_chapter or page_title or chapter_num == 0:
            chapter_num += 1
            if current_chapter:
                if minimax and current_chapter["content"]:
                    current_chapter["summary"] = minimax.generate_summary(
                        current_chapter["content"][:1000],
                        current_chapter["title"]
                    )
                chapters.append(current_chapter)

            current_chapter = {
                "number": chapter_num,
                "title": page_title or f"Page {page_num + 1}",
                "content": extracted_text,
                "paragraphs": structured.get("paragraphs", [extracted_text]) if extracted_text else [],
                "images": [{
                    "index": 0,
                    "page": page_num + 1,
                    "data": img_data_url,
                    "alt": f"Page {page_num + 1} content",
                    "is_page_scan": True,
                    "width": pix.width,
                    "height": pix.height,
                }],
                "page_start": page_num + 1,
                "summary": "",
                "has_exercise": structured.get("has_exercise", False),
                "extraction_method": "gemini_vision"
            }
        else:
            if current_chapter is None:
                chapter_num = 1
                current_chapter = create_empty_chapter(1)

            current_chapter["content"] += "\n" + extracted_text
            current_chapter["paragraphs"].extend(structured.get("paragraphs", []))
            current_chapter["images"].append({
                "index": len(current_chapter["images"]),
                "page": page_num + 1,
                "data": img_data_url,
                "alt": f"Page {page_num + 1}",
                "is_page_scan": True,
            })

        pix = None

    if current_chapter:
        if minimax and current_chapter["content"]:
            current_chapter["summary"] = minimax.generate_summary(
                current_chapter["content"][:1000],
                current_chapter["title"]
            )
        chapters.append(current_chapter)

    return chapters or [create_empty_chapter(1)]

def extract_rendered_pages(doc) -> list:
    """Fallback: render pages as images, no OCR."""
    chapters = []
    for page_num, page in enumerate(doc):
        mat = fitz.Matrix(150/72, 150/72)
        pix = page.get_pixmap(matrix=mat)
        img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        chapters.append({
            "number": page_num + 1,
            "title": f"Page {page_num + 1}",
            "content": "[Scanned page — add GEMINI_API_KEY for OCR]",
            "paragraphs": [
                "This page is a scanned image.",
                "Configure GEMINI_API_KEY for automatic text extraction."
            ],
            "images": [{
                "index": 0,
                "page": page_num + 1,
                "data": f"data:image/png;base64,{img_b64}",
                "alt": f"Scanned page {page_num + 1}",
                "is_page_scan": True,
            }],
            "page_start": page_num + 1,
            "summary": "",
            "has_exercise": False,
        })
        pix = None
    return chapters

def extract_page_images(page, page_num: int) -> list:
    """Extract embedded images (non-scan)."""
    images = []
    for img_idx, img in enumerate(page.get_images(full=True)):
        try:
            xref = img[0]
            pix = fitz.Pixmap(page.parent, xref)
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            if pix.width < 50 or pix.height < 50:
                pix = None
                continue
            img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
            images.append({
                "index": img_idx,
                "page": page_num + 1,
                "data": f"data:image/png;base64,{img_b64}",
                "alt": f"Textbook image on page {page_num + 1}",
                "width": pix.width,
                "height": pix.height,
                "is_page_scan": False,
            })
            pix = None
        except Exception as e:
            print(f"Image extract error: {e}")
    return images

def create_empty_chapter(num: int) -> dict:
    return {
        "number": num,
        "title": f"Chapter {num}",
        "content": "",
        "paragraphs": [],
        "images": [],
        "page_start": num,
        "summary": "",
        "has_exercise": False,
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract.py <pdf> [output.json]")
        sys.exit(1)
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    minimax_key = os.environ.get("MINIMAX_API_KEY", "")
    result = extract_pdf(sys.argv[1], gemini_key, minimax_key)
    out = sys.argv[2] if len(sys.argv) > 2 else "extracted.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Done: {len(result['chapters'])} chapters → {out}")
