from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import io
import os
import tempfile
import threading
from pathlib import Path
from extract import extract_pdf
from structure import structure_content
from accessibility import add_accessibility
from epub_gen import generate_epub

app = Flask(__name__)
CORS(app, origins=["http://localhost", "https://adt.skymaxsolution.com", "*"])

DEMO_DIR = Path(__file__).parent.parent / "demo"
DEMO_DIR.mkdir(exist_ok=True)

GEMINI_KEY  = os.environ.get("GEMINI_API_KEY", "")
MINIMAX_KEY = os.environ.get("MINIMAX_API_KEY", "")
GOOGLE_TTS_KEY = os.environ.get("GOOGLE_TTS_KEY", "")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Sinhala ADT Converter",
        "gemini_configured": bool(GEMINI_KEY),
        "minimax_configured": bool(MINIMAX_KEY),
        "tts_configured": bool(GOOGLE_TTS_KEY),
        "ai_enabled": bool(GEMINI_KEY),
    })

@app.route("/test-ai", methods=["GET"])
def test_ai():
    """Test all AI service connections."""
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

    if GOOGLE_TTS_KEY:
        try:
            from tts_engine import GoogleTTS
            t = GoogleTTS(GOOGLE_TTS_KEY)
            results["tts"] = "Connected" if t.test_connection() else "Failed"
        except Exception as e:
            results["tts"] = f"Error: {e}"
    else:
        results["tts"] = "Not configured"

    return jsonify(results)


@app.route("/tts", methods=["POST"])
def text_to_speech():
    """
    Convert Sinhala text to MP3 using Google Cloud TTS.
    POST body: {"text": "...", "speed": 1.0, "voice": "si-LK-Standard-A"}
    Returns: audio/mpeg binary stream
    """
    if not GOOGLE_TTS_KEY:
        return jsonify({"error": "Google TTS not configured"}), 503

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    speed = float(data.get("speed", 1.0))
    voice = data.get("voice", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Limit to ~5000 chars per request (Google's recommended chunk size)
    text = text[:5000]

    from tts_engine import GoogleTTS
    tts = GoogleTTS(GOOGLE_TTS_KEY)
    audio = tts.synthesize(text, speed=speed, voice=voice)

    if audio:
        return send_file(
            io.BytesIO(audio),
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="sinhala_tts.mp3",
        )

    return jsonify({"error": "TTS synthesis failed"}), 500


@app.route("/tts/voices", methods=["GET"])
def tts_voices():
    """Return available si-LK voices from Google Cloud TTS."""
    if not GOOGLE_TTS_KEY:
        return jsonify({"voices": [], "configured": False})
    from tts_engine import GoogleTTS
    tts = GoogleTTS(GOOGLE_TTS_KEY)
    voices = tts.available_voices()
    return jsonify({"voices": voices, "configured": True})


@app.route("/tts/status", methods=["GET"])
def tts_status():
    """Quick status check for TTS configuration."""
    return jsonify({
        "configured": bool(GOOGLE_TTS_KEY),
        "provider": "Google Cloud Text-to-Speech",
        "language": "si-LK",
        "default_voice": "auto (si-LK)",
    })

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
    """Return canonical Sinhala demo data for the reader."""
    sample_path = DEMO_DIR / "sample_output.json"
    if sample_path.exists():
        with open(sample_path, encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify(generate_demo_data())

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


# ── Dynamic demo generation ──────────────────────────────────────────────────

CHAPTERS_CONTENT = [
    {
        "number": 1,
        "title": "පාඩම 1 — ශබ්ද හඳුනා ගනිමු",
        "content": (
            "අපේ රටේ ලස්සන ස්වභාවය ගැන ඉගෙන ගනිමු. "
            "ගස් ගල් දිය ඇළ ශබ්ද නිකුත් කරයි. "
            "කුරුළු ගීය ඇසෙයි. ගඟ ගලා යයි. "
            "ළමයි සෙල්ලම් කරති. සතුටෙන් ගෙදර යති. "
            "ශ්‍රී ලංකාව ලස්සන රටකි."
        ),
        "paragraphs": [
            "අපේ රටේ ලස්සන ස්වභාවය ගැන ඉගෙන ගනිමු.",
            "ගස් ගල් දිය ඇළ — ශබ්ද නිකුත් කරයි.",
            "කුරුළු ගීය ඇසෙයි. ගඟ ගලා යයි.",
            "ළමයි සෙල්ලම් කරති. සතුටෙන් ගෙදර යති.",
            "ශ්‍රී ලංකාව ලස්සන රටකි.",
        ],
        "has_exercise": False,
    },
    {
        "number": 2,
        "title": "පාඩම 2 — ගණිතය ඉගෙනිමු",
        "content": (
            "එකක් + එකක් = දෙකයි. දෙකක් + දෙකක් = හතරයි. "
            "ගණිතය ඉගෙන ගැනීම ප්‍රීතිමත් කාර්යයකි. "
            "1, 2, 3, 4, 5 — ඉලක්කම් ගණිත කරමු. "
            "ජීවිතයේ ගණිතය ඉතා වැදගත් වේ."
        ),
        "paragraphs": [
            "එකක් + එකක් = දෙකයි.",
            "ගණිතය ඉගෙන ගැනීම ප්‍රීතිමත් කාර්යයකි.",
            "1, 2, 3, 4, 5 — ඉලක්කම් ගණිත කරමු.",
            "ජීවිතයේ ගණිතය ඉතා වැදගත් වේ.",
        ],
        "has_exercise": True,
    },
    {
        "number": 3,
        "title": "පාඩම 3 — ලලිත කලා",
        "content": (
            "චිත්‍ර ඇඳීම ලස්සන කලාවකි. "
            "පාට පාට රේඛා ඇඳ සිතුවමක් ගොඩ නඟමු. "
            "නිල් පාට, රතු පාට, කහ පාට — ලෝකය සරලයි. "
            "කලාව ළමයාගේ නිර්මාණශීලිත්වය වර්ධනය කරන හොඳ කුසලතාවකි."
        ),
        "paragraphs": [
            "චිත්‍ර ඇඳීම ලස්සන කලාවකි.",
            "නිල් පාට, රතු පාට, කහ පාට — ලෝකය සරලයි.",
            "කලාව ළමයාගේ නිර්මාණශීලිත්වය වර්ධනය කරයි.",
        ],
        "has_exercise": False,
    },
]

FALLBACK_SUMMARIES = {
    1: "මෙම පාඩමේදී අපේ රටේ ලස්සන ස්වභාවය ගැන ඉගෙන ගනිමු. ශබ්ද හඳුනා ගන්නා ආකාරය ස්වභාවික උදාහරණ තුළින් දැනගනිමු.",
    2: "මෙම පාඩමේදී සිංහල භාෂාවෙන් මූලික ගණිතය ඉගෙන ගනිමු. ඉලක්කම් සහ එකතු කිරීම් ගැන ප්‍රීතිමත්ව ඉගෙනිමු.",
    3: "මෙම පාඩමේදී ළමයින් වර්ණ සහ කලාව ගැන ඉගෙන ගනිමු. චිත්‍ර ඇඳීමෙන් නිර්මාණශීලිත්වය වර්ධනය කරගනිමු.",
}


def build_chapter_html(number: int, title: str, paragraphs: list,
                       summary: str, has_exercise: bool = False) -> str:
    """Build accessible HTML for a chapter dynamically."""
    html = f'<article lang="si" id="chapter-{number}" aria-labelledby="ch-{number}-heading" role="article">\n'
    html += f'<a href="#ch-{number}-main" class="skip-link" tabindex="0">පාඩම් අන්තර්ගතයට යන්න</a>\n'
    html += f'<div id="ch-{number}-main">\n'
    html += f'<section id="ch-{number}" role="region" aria-label="{title}" lang="si">\n'
    html += f'<h2 id="ch-{number}-heading" tabindex="0">{title}</h2>\n'

    if summary:
        html += f'<aside class="summary-box" role="note" lang="si" aria-label="පාඩම් සාරාංශය">\n'
        html += f'  <strong>සාරාංශය:</strong> {summary}\n'
        html += f'</aside>\n'

    for para in paragraphs:
        if para.strip():
            html += f'<p tabindex="0" lang="si">{para}</p>\n'

    if has_exercise:
        html += '<aside class="exercise-box" role="note">\n'
        html += '  <strong>අභ්‍යාසය:</strong>\n'
        html += '  <p lang="si">ඉහත ඉගෙන ගත් දේ ගැන ලිවිය.</p>\n'
        html += '</aside>\n'

    html += '</section>\n</div>\n</article>\n'
    return html


def generate_demo_data() -> dict:
    """Generate demo data dynamically with Sinhala summaries from MiniMax."""
    summaries = {}
    if MINIMAX_KEY:
        try:
            from minimax_processor import MinimaxProcessor
            m = MinimaxProcessor(MINIMAX_KEY)
            for ch in CHAPTERS_CONTENT:
                print(f"Generating summary for {ch['title']}...")
                summary = m.generate_summary(ch["content"], ch["title"])
                if summary:
                    summaries[ch["number"]] = summary
                    print(f"  ✓ {summary[:60]}")
        except Exception as e:
            print(f"MiniMax summary generation error: {e}")

    final_chapters = []
    for ch in CHAPTERS_CONTENT:
        summary = summaries.get(ch["number"]) or FALLBACK_SUMMARIES.get(ch["number"], "")
        final_chapters.append({
            "number": ch["number"],
            "title": ch["title"],
            "summary": summary,
            "reading_time_minutes": max(1, len(ch["content"].split()) // 150),
            "accessible_html": build_chapter_html(
                ch["number"], ch["title"], ch["paragraphs"],
                summary, ch.get("has_exercise", False)
            ),
            "images": [],
            "has_exercise": ch.get("has_exercise", False),
            "word_count": len(ch["content"].split()),
        })

    return {
        "title": "සිංහල භාෂා පාඩම් — 3 ශ්‍රේණිය",
        "language": "si",
        "publisher": "Ministry of Education Sri Lanka",
        "ai_enhanced": bool(MINIMAX_KEY),
        "extraction_method": "dynamic_generation",
        "wcag_metadata": {
            "conformsTo": "WCAG 2.1 Level AA",
            "accessibilityFeature": [
                "alternativeText",
                "readingOrder",
                "structuralNavigation",
                "tableOfContents",
            ],
            "accessibilityHazard": "none",
        },
        "chapters": final_chapters,
    }


def generate_and_cache_demo():
    """Generate demo data on startup and cache to sample_output.json."""
    sample_path = DEMO_DIR / "sample_output.json"
    if not sample_path.exists() and MINIMAX_KEY:
        print("Generating Sinhala demo data on startup...")
        try:
            data = generate_demo_data()
            with open(sample_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Demo data cached to sample_output.json")
        except Exception as e:
            print(f"Demo generation error: {e}")


threading.Thread(target=generate_and_cache_demo, daemon=True).start()


if __name__ == "__main__":
    print(f"Gemini:      {'configured' if GEMINI_KEY else 'not set'}")
    print(f"MiniMax:     {'configured' if MINIMAX_KEY else 'not set'}")
    print(f"Google TTS:  {'configured' if GOOGLE_TTS_KEY else 'not set — add GOOGLE_TTS_KEY to .env'}")
    app.run(host="0.0.0.0", port=5050, debug=False)
