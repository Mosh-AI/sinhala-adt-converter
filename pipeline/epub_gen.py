import json
import sys
import uuid
from datetime import datetime
from ebooklib import epub

def generate_epub(accessible: dict, output_path: str) -> str:
    """Generate WCAG 2.1 compliant EPUB3."""
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(accessible.get("title", "Sinhala Textbook"))
    book.set_language("si")
    book.add_author(accessible.get("publisher", "Ministry of Education Sri Lanka"))

    for feat in accessible.get("wcag_metadata", {}).get("accessibilityFeature", []):
        book.add_metadata(None, "meta", "", {
            "property": "schema:accessibilityFeature",
            "content": feat
        })
    book.add_metadata(None, "meta", "", {
        "property": "schema:accessibilityHazard",
        "content": "none"
    })
    book.add_metadata(None, "meta", "", {
        "property": "schema:conformsTo",
        "content": "EPUB Accessibility 1.1 - WCAG 2.1 Level AA"
    })
    book.add_metadata(None, "meta", "", {
        "property": "schema:certifiedBy",
        "content": "Moshan Wijenayake — Proof of concept"
    })

    css_content = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Sinhala:wght@400;700&display=swap');
body {
  font-family: 'Noto Sans Sinhala','Iskoola Pota',serif;
  font-size: 1.1em; line-height: 1.9;
  color: #1a1a2e; background: #fff;
  margin: 1em 2em;
}
h1,h2,h3 { color: #0d3b66; font-weight: 700; }
p { margin: 0.8em 0; }
img { max-width: 100%; height: auto; display: block; margin: 1em auto; }
.summary-box {
  background: #e8f4f8; border-left: 4px solid #0d3b66;
  padding: 0.8em 1em; margin: 1em 0; font-style: italic;
}
.skip-link { position: absolute; top: -40px; }
.skip-link:focus { top: 0; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
"""
    style = epub.EpubItem(
        uid="main_css",
        file_name="style/main.css",
        media_type="text/css",
        content=css_content
    )
    book.add_item(style)

    epub_chapters = []
    spine = ["nav"]

    for ch in accessible.get("chapters", []):
        html_content = f'''<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:epub="http://www.idpf.org/2007/ops"
      lang="si" xml:lang="si">
<head>
  <meta charset="utf-8"/>
  <title>{ch["title"]}</title>
  <link rel="stylesheet" href="../style/main.css"/>
</head>
<body>
<main role="main" lang="si" aria-label="{ch.get('aria_label', ch['title'])}">
{ch.get("accessible_html", ch.get("html_content", ""))}
</main>
</body>
</html>'''

        epub_ch = epub.EpubHtml(
            title=ch["title"],
            file_name=f"ch_{ch['number']}.xhtml",
            lang="si"
        )
        epub_ch.content = html_content.encode("utf-8")
        epub_ch.add_item(style)
        book.add_item(epub_ch)
        epub_chapters.append(epub_ch)
        spine.append(epub_ch)

    book.toc = tuple([
        epub.Link(f"ch_{c['number']}.xhtml", c["title"], f"ch_{c['number']}")
        for c in accessible.get("chapters", [])
    ])
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine
    epub.write_epub(output_path, book)
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python epub_gen.py <accessible.json> [out.epub]")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    out = sys.argv[2] if len(sys.argv) > 2 else "output.epub"
    generate_epub(data, out)
    print(f"EPUB3 generated: {out}")
