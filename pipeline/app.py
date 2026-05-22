from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import tempfile
from pathlib import Path
from extract import extract_pdf
from structure import structure_content
from accessibility import add_accessibility
from epub_gen import generate_epub

app = Flask(__name__)
CORS(app, origins=["http://localhost", "https://adt.skymaxsolution.com", "*"])

DEMO_DIR = Path(__file__).parent.parent / "demo"
DEMO_DIR.mkdir(exist_ok=True)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
MINIMAX_KEY = os.environ.get("MINIMAX_API_KEY", "")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Sinhala ADT Converter",
        "gemini_configured": bool(GEMINI_KEY),
        "minimax_configured": bool(MINIMAX_KEY),
        "ai_enabled": bool(GEMINI_KEY),
    })

@app.route("/test-ai", methods=["GET"])
def test_ai():
    """Test both AI connections."""
    results = {}
    if GEMINI_KEY:
        try:
            from gemini_ocr import GeminiVision
            g = GeminiVision(GEMINI_KEY)
            results["gemini"] = "Connected" if g.test_connection() else "Failed"
        except Exception as e:
            results["gemini"] = f"Error: {e}"
    else:
        results["gemini"] = "Not configured"

    if MINIMAX_KEY:
        try:
            from minimax_processor import MinimaxProcessor
            m = MinimaxProcessor(MINIMAX_KEY)
            results["minimax"] = "Connected" if m.test_connection() else "Failed"
        except Exception as e:
            results["minimax"] = f"Error: {e}"
    else:
        results["minimax"] = "Not configured"

    return jsonify(results)

@app.route("/convert", methods=["POST"])
def convert_pdf():
    """Full pipeline: PDF -> accessible EPUB3 + JSON."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "PDF files only"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "input.pdf")
        file.save(pdf_path)

        extracted = extract_pdf(pdf_path, GEMINI_KEY, MINIMAX_KEY)
        structured = structure_content(extracted, MINIMAX_KEY)
        accessible = add_accessibility(structured, GEMINI_KEY)

        json_path = DEMO_DIR / "latest_output.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(accessible, f, ensure_ascii=False, indent=2)

        epub_path = str(DEMO_DIR / "latest_output.epub")
        generate_epub(accessible, epub_path)

        return jsonify({
            "success": True,
            "title": accessible["title"],
            "chapters": len(accessible["chapters"]),
            "method": extracted["extraction_method"],
            "is_text_based": extracted["is_text_based"],
            "ai_enhanced": extracted.get("ai_enhanced", False),
            "gemini_used": bool(GEMINI_KEY),
            "minimax_used": bool(MINIMAX_KEY),
        })

@app.route("/demo-data", methods=["GET"])
def demo_data():
    """Return demo data for the reader."""
    json_path = DEMO_DIR / "latest_output.json"
    if not json_path.exists():
        json_path = DEMO_DIR / "sample_output.json"
    if not json_path.exists():
        return jsonify(get_builtin_demo())
    with open(json_path, encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/download/epub", methods=["GET"])
def download_epub():
    epub_path = DEMO_DIR / "latest_output.epub"
    if not epub_path.exists():
        return jsonify({"error": "No EPUB yet"}), 404
    return send_file(
        str(epub_path),
        as_attachment=True,
        download_name="sinhala_textbook_accessible.epub"
    )

def get_builtin_demo():
    """Built-in Sinhala demo content."""
    return {
        "title": "සිංහල භාෂා පාඩම් — 3 ශ්‍රේණිය",
        "language": "si",
        "publisher": "Ministry of Education Sri Lanka",
        "ai_enhanced": True,
        "extraction_method": "gemini_vision_ocr",
        "wcag_metadata": {
            "conformsTo": "WCAG 2.1 Level AA",
            "accessibilityFeature": [
                "alternativeText",
                "readingOrder",
                "structuralNavigation",
                "tableOfContents"
            ],
            "accessibilityHazard": "none"
        },
        "chapters": [
            {
                "number": 1,
                "title": "පාඩම 1 — ශබ්ද හඳුනා ගනිමු",
                "summary": "Students learn to identify and pronounce Sinhala sounds through nature examples.",
                "reading_time_minutes": 2,
                "has_exercise": False,
                "images": [],
                "accessible_html": """<article lang="si" id="chapter-1" aria-labelledby="ch-1-heading" role="article">
<a href="#ch-1-main" class="skip-link" tabindex="0">Skip to chapter content</a>
<div id="ch-1-main">
<section id="ch-1" role="region" aria-label="පාඩම 1 — ශබ්ද හඳුනා ගනිමු" lang="si">
<h2 tabindex="0">පාඩම 1 — ශබ්ද හඳුනා ගනිමු</h2>
<aside class="summary-box" role="note" aria-label="Chapter summary">
  <strong>Summary:</strong> Students learn to identify and pronounce Sinhala sounds through nature examples.
</aside>
<p tabindex="0" lang="si">අපේ රටේ ලස්සන ස්වභාවය ගැන ඉගෙන ගනිමු. ගස් ගල් දිය ඇළ — ඒ සෑම දෙයක්ම ශබ්ද නිකුත් කරයි.</p>
<p tabindex="0" lang="si">කුරුළු ගීය ඇසෙයි. ගඟ ගලා යයි. ළමයි සෙල්ලම් කරති. සතුටෙන් ගෙදර යති.</p>
<p tabindex="0" lang="si">ශ්‍රී ලංකාව ලස්සන රටකි. එහි ළමයි දෙමාපියන් ආදරයෙන් ජීවත් වෙති.</p>
</section>
</div>
</article>"""
            },
            {
                "number": 2,
                "title": "පාඩම 2 — ගණිතය ඉගෙනිමු",
                "summary": "Introduction to basic addition and numbers in Sinhala.",
                "reading_time_minutes": 2,
                "has_exercise": True,
                "images": [],
                "accessible_html": """<article lang="si" id="chapter-2" aria-labelledby="ch-2-heading" role="article">
<a href="#ch-2-main" class="skip-link" tabindex="0">Skip to chapter content</a>
<div id="ch-2-main">
<section id="ch-2" role="region" aria-label="පාඩම 2 — ගණිතය ඉගෙනිමු" lang="si">
<h2 tabindex="0">පාඩම 2 — ගණිතය ඉගෙනිමු</h2>
<aside class="summary-box" role="note" aria-label="Chapter summary">
  <strong>Summary:</strong> Introduction to basic addition and numbers in Sinhala.
</aside>
<p tabindex="0" lang="si">එකක් + එකක් = දෙකයි. දෙකක් + දෙකක් = හතරයි.</p>
<p tabindex="0" lang="si">ගණිතය ඉගෙන ගැනීම ප්‍රීතිමත් කාර්යයකි. සංඛ්‍යා ගැන දැනගන්නෙමු.</p>
<p tabindex="0" lang="si">1, 2, 3, 4, 5 — ඉලක්කම් ගණිත කරමු. ජීවිතයේ ගණිතය ඉතා වැදගත් වේ.</p>
</section>
</div>
</article>"""
            },
            {
                "number": 3,
                "title": "පාඩම 3 — ලලිත කලා",
                "summary": "Children explore colors and art as a means of creative expression.",
                "reading_time_minutes": 2,
                "has_exercise": False,
                "images": [],
                "accessible_html": """<article lang="si" id="chapter-3" aria-labelledby="ch-3-heading" role="article">
<a href="#ch-3-main" class="skip-link" tabindex="0">Skip to chapter content</a>
<div id="ch-3-main">
<section id="ch-3" role="region" aria-label="පාඩම 3 — ලලිත කලා" lang="si">
<h2 tabindex="0">පාඩම 3 — ලලිත කලා</h2>
<aside class="summary-box" role="note" aria-label="Chapter summary">
  <strong>Summary:</strong> Children explore colors and art as a means of creative expression.
</aside>
<p tabindex="0" lang="si">චිත්‍ර ඇඳීම ලස්සන කලාවකි. පාට පාට රේඛා ඇඳ සිතුවමක් ගොඩ නඟමු.</p>
<p tabindex="0" lang="si">නිල් පාට, රතු පාට, කහ පාට — ඒ සෑම පාටකම ලෝකය සරලයි.</p>
<p tabindex="0" lang="si">කලාව ළමයාගේ නිර්මාණශීලිත්වය වර්ධනය කරන හොඳ කුසලතාවකි.</p>
</section>
</div>
</article>"""
            }
        ]
    }

if __name__ == "__main__":
    print(f"Gemini: {'configured' if GEMINI_KEY else 'not set'}")
    print(f"MiniMax: {'configured' if MINIMAX_KEY else 'not set'}")
    app.run(host="0.0.0.0", port=5050, debug=False)
