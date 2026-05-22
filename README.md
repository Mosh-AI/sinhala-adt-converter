# Sinhala Accessible Digital Textbook Converter

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![WCAG 2.1](https://img.shields.io/badge/WCAG-2.1%20AA-green)](https://www.w3.org/WAI/WCAG21/quickref/)
[![EPUB3](https://img.shields.io/badge/Output-EPUB3-orange)](https://www.w3.org/publishing/epub3/)
[![Gemini AI](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-purple)](https://ai.google.dev/)
[![License MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> Proof of concept for UNICEF's Accessible Digital Textbooks (ADT) initiative — Sri Lanka

## Live Demo
**https://adt.skymaxsolution.com**

## About UNICEF ADT Initiative

UNICEF's Accessible Digital Textbooks initiative ensures children with disabilities have equal access to quality education in their native language. In Sri Lanka, 80,000+ children have visual or hearing impairments with limited access to accessible Sinhala educational materials.

This proof of concept demonstrates how AI can automate conversion of Sri Lanka Ministry of Education PDF textbooks into WCAG 2.1 AA compliant accessible digital formats.

## What This Does

Converts Sri Lanka Ministry of Education Sinhala PDF textbooks into WCAG 2.1 AA compliant digital textbooks.

**AI Pipeline:**
```
Scanned PDF → Gemini 1.5 Flash Vision OCR
              ↓
Extracted Sinhala → MiniMax M2.5 structuring + summaries
              ↓
Images → Gemini Vision → descriptive alt text
              ↓
WCAG 2.1 AA EPUB3 + Accessible Web Reader
```

## Accessibility Features

- ♿ WCAG 2.1 Level AA compliance (self-certified)
- 🔊 Sinhala TTS via Web Speech API (si-LK voice)
- ⌨️ Full keyboard navigation (Space, arrows, +/-, C)
- 🔆 High contrast / dark mode toggle
- 📏 Adjustable font size (S/M/L/XL) — Noto Sans Sinhala
- 📖 EPUB3 output for screen readers (JAWS, NVDA, VoiceOver)
- 🏷️ Semantic HTML5 with ARIA labels
- 🌐 `lang="si"` on all Sinhala content

## Quick Start (Docker)

```bash
git clone https://github.com/Mosh-AI/sinhala-adt-converter
cd sinhala-adt-converter
cp .env.example .env
# Edit .env and add your API keys
docker-compose up
# Open http://localhost
```

## Manual Setup

```bash
pip install -r requirements.txt
cd pipeline
GEMINI_API_KEY=your_key MINIMAX_API_KEY=your_key python app.py
# Open web/index.html in a browser
# API runs on http://localhost:5050
```

## API Keys (Free Tier)

| Service | Purpose | Free Limit |
|---------|---------|------------|
| [Gemini 1.5 Flash](https://ai.google.dev/) | OCR scanned PDFs, image alt text | 1,500 req/day |
| [MiniMax M2.5](https://api.minimax.io/) | Text structuring, summaries | Per plan |

The web reader works **without API keys** using built-in demo content.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health + AI status |
| GET | `/api/test-ai` | Test Gemini + MiniMax connections |
| POST | `/api/convert` | Convert PDF (multipart/form-data, field: `file`) |
| GET | `/api/demo-data` | Get latest conversion JSON |
| GET | `/api/download/epub` | Download latest EPUB3 |

## Pipeline Modules

```
pipeline/
├── gemini_ocr.py       # Gemini 1.5 Flash — OCR + alt text
├── minimax_processor.py # MiniMax M2.5 — text structuring
├── extract.py          # PDF extraction (text + scanned)
├── structure.py        # Semantic HTML5 builder
├── accessibility.py    # WCAG 2.1 AA metadata
├── epub_gen.py         # EPUB3 generator
└── app.py              # Flask API server
```

## Limitations (Honest)

- OCR quality depends on PDF scan resolution (150+ DPI recommended)
- Sinhala TTS requires Chrome/Android with **si-LK voice pack** installed
- WCAG compliance is **self-certified**, not independently audited
- This is a proof of concept — not production-hardened software
- MiniMax M2.5 is **text-only** — all image tasks use Gemini

## Tech Stack

| Layer | Technology |
|-------|-----------|
| PDF Extraction | Python + PyMuPDF |
| OCR | Google Gemini 1.5 Flash Vision |
| Text Processing | MiniMax M2.5 |
| EPUB Generation | ebooklib |
| API Server | Flask + flask-cors |
| Web Frontend | Vanilla HTML/CSS/JS |
| TTS | Web Speech API (si-LK) |
| Sinhala Font | Noto Sans Sinhala |
| Deployment | Docker + Nginx |

## Author

**Moshan Wijenayake**

Built as preparation for supporting UNICEF Sri Lanka's Accessible Digital Textbooks initiative.

[GitHub](https://github.com/Mosh-AI) · [Live Demo](https://adt.skymaxsolution.com)

## License

MIT — Free for educational and humanitarian use.

---

*Not affiliated with UNICEF or the Ministry of Education Sri Lanka. Independent proof of concept.*
