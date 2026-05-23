'use strict';

class SinhalaReader {
  constructor() {
    this.data = null;
    this.currentChapter = 0;
    this.fontSize = 'md';
    this.highContrast = false;
    this.isPlaying = false;
    // Google Cloud TTS (backend)
    this.ttsConfigured = false;
    this.ttsVoice = 'si-LK-Standard-A';
    this.audio = null;           // HTML5 Audio element
    // Browser speechSynthesis fallback
    this.sinhalaVoice = null;
    this.utterance = null;
    this.synth = null;
  }

  async init() {
    this.showLoading(true);
    await this.loadContent();
    await this.setupTTS();   // probe backend before rendering
    this.buildSidebar();
    this.renderChapter(0);
    this.setupControls();
    this.setupKeyboard();
    this.showLoading(false);
  }

  async loadContent() {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      const res = await fetch('/api/demo-data', { signal: controller.signal });
      clearTimeout(timeout);
      if (res.ok) {
        this.data = await res.json();
        return;
      }
    } catch (e) {
      // Fall through to built-in data
    }
    this.data = this.getBuiltinData();
  }

  getBuiltinData() {
    // Sinhala fallback summaries — used only if /api/demo-data is unreachable
    const summaries = {
      1: "මෙම පාඩමේදී අපේ රටේ ලස්සන ස්වභාවය ගැන ඉගෙන ගනිමු. ශබ්ද හඳුනා ගන්නා ආකාරය ස්වභාවික උදාහරණ තුළින් දැනගනිමු.",
      2: "මෙම පාඩමේදී සිංහල භාෂාවෙන් මූලික ගණිතය ඉගෙන ගනිමු. ඉලක්කම් සහ එකතු කිරීම් ගැන ප්‍රීතිමත්ව ඉගෙනිමු.",
      3: "මෙම පාඩමේදී ළමයින් වර්ණ සහ කලාව ගැන ඉගෙන ගනිමු. චිත්‍ර ඇඳීමෙන් නිර්මාණශීලිත්වය වර්ධනය කරගනිමු.",
    };
    return {
      title: "සිංහල භාෂා පාඩම් — 3 ශ්‍රේණිය",
      language: "si",
      publisher: "Ministry of Education Sri Lanka",
      ai_enhanced: true,
      extraction_method: "builtin_fallback",
      wcag_metadata: {
        conformsTo: "WCAG 2.1 Level AA",
        accessibilityFeature: ["alternativeText", "readingOrder", "structuralNavigation", "tableOfContents"],
        accessibilityHazard: "none"
      },
      chapters: [
        {
          number: 1,
          title: "පාඩම 1 — ශබ්ද හඳුනා ගනිමු",
          summary: summaries[1],
          reading_time_minutes: 2,
          has_exercise: false,
          images: [],
          accessible_html: `<article lang="si" id="chapter-1" aria-labelledby="ch-1-heading" role="article">
<a href="#ch-1-main" class="skip-link" tabindex="0">පාඩම් අන්තර්ගතයට යන්න</a>
<div id="ch-1-main">
<section id="ch-1" role="region" aria-label="පාඩම 1 — ශබ්ද හඳුනා ගනිමු" lang="si">
<h2 id="ch-1-heading" tabindex="0">පාඩම 1 — ශබ්ද හඳුනා ගනිමු</h2>
<aside class="summary-box" role="note" lang="si" aria-label="පාඩම් සාරාංශය">
  <strong>සාරාංශය:</strong> ${summaries[1]}
</aside>
<p tabindex="0" lang="si">අපේ රටේ ලස්සන ස්වභාවය ගැන ඉගෙන ගනිමු. ගස් ගල් දිය ඇළ — ශබ්ද නිකුත් කරයි.</p>
<p tabindex="0" lang="si">කුරුළු ගීය ඇසෙයි. ගඟ ගලා යයි. ළමයි සෙල්ලම් කරති. සතුටෙන් ගෙදර යති.</p>
<p tabindex="0" lang="si">ශ්‍රී ලංකාව ලස්සන රටකි. එහි ළමයි දෙමාපියන් ආදරයෙන් ජීවත් වෙති.</p>
</section>
</div>
</article>`
        },
        {
          number: 2,
          title: "පාඩම 2 — ගණිතය ඉගෙනිමු",
          summary: summaries[2],
          reading_time_minutes: 2,
          has_exercise: true,
          images: [],
          accessible_html: `<article lang="si" id="chapter-2" aria-labelledby="ch-2-heading" role="article">
<a href="#ch-2-main" class="skip-link" tabindex="0">පාඩම් අන්තර්ගතයට යන්න</a>
<div id="ch-2-main">
<section id="ch-2" role="region" aria-label="පාඩම 2 — ගණිතය ඉගෙනිමු" lang="si">
<h2 id="ch-2-heading" tabindex="0">පාඩම 2 — ගණිතය ඉගෙනිමු</h2>
<aside class="summary-box" role="note" lang="si" aria-label="පාඩම් සාරාංශය">
  <strong>සාරාංශය:</strong> ${summaries[2]}
</aside>
<p tabindex="0" lang="si">එකක් + එකක් = දෙකයි. දෙකක් + දෙකක් = හතරයි.</p>
<p tabindex="0" lang="si">ගණිතය ඉගෙන ගැනීම ප්‍රීතිමත් කාර්යයකි. සංඛ්‍යා ගැන දැනගන්නෙමු.</p>
<p tabindex="0" lang="si">1, 2, 3, 4, 5 — ඉලක්කම් ගණිත කරමු. ජීවිතයේ ගණිතය ඉතා වැදගත් වේ.</p>
</section>
</div>
</article>`
        },
        {
          number: 3,
          title: "පාඩම 3 — ලලිත කලා",
          summary: summaries[3],
          reading_time_minutes: 2,
          has_exercise: false,
          images: [],
          accessible_html: `<article lang="si" id="chapter-3" aria-labelledby="ch-3-heading" role="article">
<a href="#ch-3-main" class="skip-link" tabindex="0">පාඩම් අන්තර්ගතයට යන්න</a>
<div id="ch-3-main">
<section id="ch-3" role="region" aria-label="පාඩම 3 — ලලිත කලා" lang="si">
<h2 id="ch-3-heading" tabindex="0">පාඩම 3 — ලලිත කලා</h2>
<aside class="summary-box" role="note" lang="si" aria-label="පාඩම් සාරාංශය">
  <strong>සාරාංශය:</strong> ${summaries[3]}
</aside>
<p tabindex="0" lang="si">චිත්‍ර ඇඳීම ලස්සන කලාවකි. පාට පාට රේඛා ඇඳ සිතුවමක් ගොඩ නඟමු.</p>
<p tabindex="0" lang="si">නිල් පාට, රතු පාට, කහ පාට — ලෝකය සරලයි.</p>
<p tabindex="0" lang="si">කලාව ළමයාගේ නිර්මාණශීලිත්වය වර්ධනය කරන හොඳ කුසලතාවකි.</p>
</section>
</div>
</article>`
        }
      ]
    };
  }

  buildSidebar() {
    const list = document.getElementById('chapter-list');
    if (!list) return;
    list.innerHTML = '';
    this.data.chapters.forEach((ch, i) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <button onclick="reader.goToChapter(${i})"
          aria-label="Go to chapter ${ch.number}: ${ch.title}"
          id="sidebar-ch-${i}">
          <span class="ch-num">${ch.number}</span>
          <span class="ch-info">
            <span class="ch-title">${ch.title}</span>
            <span class="ch-meta">${ch.reading_time_minutes || 1} min read${ch.has_exercise ? ' · Exercise' : ''}</span>
          </span>
        </button>`;
      list.appendChild(li);
    });
    const total = document.getElementById('total-chapters');
    if (total) total.textContent = this.data.chapters.length;
  }

  renderChapter(index) {
    if (!this.data || index < 0 || index >= this.data.chapters.length) return;
    this.stopTTS();   // stops both audio element and browser synth
    this.currentChapter = index;
    const ch = this.data.chapters[index];
    const content = document.getElementById('content');
    if (content) {
      content.innerHTML = ch.accessible_html || ch.html_content || '';
      content.setAttribute('lang', 'si');
    }
    this.highlightSidebar(index);
    this.updateProgress();
    const titleEl = document.getElementById('chapter-title');
    if (titleEl) titleEl.textContent = ch.title;
    this.updateNavButtons();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    // Focus main content for screen readers
    setTimeout(() => content?.focus(), 100);
  }

  async setupTTS() {
    // ── 1. Probe backend Google Cloud TTS ────────────────────
    try {
      const res = await fetch('/api/tts/status', { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        const s = await res.json();
        this.ttsConfigured = s.configured === true;
      }
    } catch (_) { /* backend unreachable — fall through */ }

    if (this.ttsConfigured) {
      // Fetch available voices and pick the best one
      try {
        const vRes = await fetch('/api/tts/voices', { signal: AbortSignal.timeout(5000) });
        if (vRes.ok) {
          const { voices } = await vRes.json();
          if (voices.length) {
            // Prefer female Standard-A, then first available
            const female = voices.find(v => v.gender === 'FEMALE') || voices[0];
            this.ttsVoice = female.name;
          }
        }
      } catch (_) { /* keep default voice */ }

      this.updateTTSStatus(`Google Cloud TTS ready · Voice: ${this.ttsVoice}`);
      return;
    }

    // ── 2. Browser speechSynthesis fallback ──────────────────
    if (!window.speechSynthesis) {
      this.updateTTSStatus('Text-to-speech not available in this browser');
      return;
    }
    this.synth = window.speechSynthesis;
    const findVoice = () => {
      const voices = this.synth.getVoices();
      return voices.find(v => v.lang === 'si-LK') ||
             voices.find(v => v.lang.startsWith('si')) ||
             null;
    };
    this.synth.onvoiceschanged = () => {
      this.sinhalaVoice = findVoice();
      this.updateTTSStatus(
        this.sinhalaVoice
          ? `Browser TTS · Voice: ${this.sinhalaVoice.name} (${this.sinhalaVoice.lang})`
          : 'Browser TTS · No si-LK voice installed — install Sinhala voice pack for best results'
      );
    };
    setTimeout(() => {
      if (!this.sinhalaVoice) {
        this.sinhalaVoice = findVoice();
        this.updateTTSStatus(this.sinhalaVoice
          ? `Browser TTS · ${this.sinhalaVoice.name}`
          : 'Browser TTS · No si-LK voice — using default'
        );
      }
    }, 800);
  }

  toggleTTS() {
    if (this.isPlaying) {
      this.stopTTS();
    } else {
      this.startTTS();
    }
  }

  async startTTS() {
    const content = document.getElementById('content');
    const text = content ? (content.innerText || content.textContent || '').trim() : '';
    if (!text) return;

    const speed = parseFloat(document.getElementById('speed-select')?.value || '1');

    // ── Google Cloud TTS (backend) ────────────────────────────
    if (this.ttsConfigured) {
      this.updateTTSStatus('Generating audio…');
      this.updatePlayButton(true);
      this.isPlaying = true;

      try {
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, speed, voice: this.ttsVoice }),
          signal: AbortSignal.timeout(25000),
        });

        if (!res.ok) throw new Error(`TTS API ${res.status}`);

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);

        // Release previous audio
        if (this.audio) {
          this.audio.pause();
          URL.revokeObjectURL(this.audio.src);
        }

        this.audio = new Audio(url);
        this.audio.playbackRate = speed;
        this.audio.onended = () => {
          this.isPlaying = false;
          this.updatePlayButton(false);
          this.updateTTSStatus(`Google Cloud TTS ready · Voice: ${this.ttsVoice}`);
          URL.revokeObjectURL(url);
        };
        this.audio.onerror = () => {
          this.isPlaying = false;
          this.updatePlayButton(false);
          this.updateTTSStatus('Audio playback error');
        };
        this.audio.play();
        this.updateTTSStatus(`Playing · ${this.ttsVoice} · ${speed}x`);
        return;

      } catch (err) {
        console.warn('Google TTS failed, falling back to browser:', err);
        this.isPlaying = false;
        this.updatePlayButton(false);
        this.updateTTSStatus('Cloud TTS unavailable — using browser fallback');
        // Fall through to browser TTS below
      }
    }

    // ── Browser speechSynthesis fallback ─────────────────────
    if (!this.synth) {
      this.updateTTSStatus('Text-to-speech not available');
      return;
    }
    this.synth.cancel();
    this.utterance = new SpeechSynthesisUtterance(text);
    if (this.sinhalaVoice) this.utterance.voice = this.sinhalaVoice;
    this.utterance.lang = 'si-LK';
    this.utterance.rate = speed;
    this.utterance.onend = () => {
      this.isPlaying = false;
      this.updatePlayButton(false);
    };
    this.utterance.onerror = (e) => {
      this.isPlaying = false;
      this.updatePlayButton(false);
      console.warn('Browser TTS error:', e);
    };
    this.synth.speak(this.utterance);
    this.isPlaying = true;
    this.updatePlayButton(true);
  }

  stopTTS() {
    // Stop Google Cloud TTS audio
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
    }
    // Stop browser TTS
    if (this.synth) this.synth.cancel();
    this.isPlaying = false;
    this.updatePlayButton(false);
    if (this.ttsConfigured) {
      this.updateTTSStatus(`Google Cloud TTS ready · Voice: ${this.ttsVoice}`);
    }
  }

  updatePlayButton(playing) {
    const btn = document.getElementById('play-btn');
    if (!btn) return;
    const iconPlay = btn.querySelector('.icon-play');
    const iconPause = btn.querySelector('.icon-pause');
    const label = btn.querySelector('.play-label');
    if (iconPlay) iconPlay.style.display = playing ? 'none' : '';
    if (iconPause) iconPause.style.display = playing ? '' : 'none';
    if (label) label.textContent = playing ? 'Pause' : 'Read aloud';
    btn.classList.toggle('playing', playing);
    btn.setAttribute('aria-pressed', playing);
    btn.setAttribute('aria-label', playing ? 'Pause reading' : 'Read chapter aloud');
  }

  updateTTSStatus(msg) {
    const el = document.getElementById('tts-status');
    if (el) el.textContent = msg;
  }

  setFontSize(size) {
    ['sm','md','lg','xl'].forEach(s => document.body.classList.remove(`font-${s}`));
    document.body.classList.add(`font-${size}`);
    this.fontSize = size;
    document.querySelectorAll('.font-btn').forEach(btn => {
      const isActive = btn.dataset.size === size;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-pressed', isActive);
    });
  }

  toggleContrast() {
    this.highContrast = !this.highContrast;
    document.body.classList.toggle('high-contrast', this.highContrast);
    const btn = document.getElementById('contrast-btn');
    if (btn) {
      btn.classList.toggle('active', this.highContrast);
      btn.setAttribute('aria-pressed', this.highContrast);
      btn.setAttribute('aria-label', this.highContrast ? 'Disable high contrast' : 'Enable high contrast mode');
    }
  }

  setupControls() {
    document.getElementById('play-btn')?.addEventListener('click', () => this.toggleTTS());
    document.getElementById('contrast-btn')?.addEventListener('click', () => this.toggleContrast());
    document.getElementById('speed-select')?.addEventListener('change', () => {
      if (this.isPlaying) { this.stopTTS(); this.startTTS(); }
    });
    document.querySelectorAll('.font-btn').forEach(btn =>
      btn.addEventListener('click', () => this.setFontSize(btn.dataset.size))
    );
    document.getElementById('prev-btn')?.addEventListener('click', () => this.prevChapter());
    document.getElementById('next-btn')?.addEventListener('click', () => this.nextChapter());
    document.getElementById('prev-btn-bottom')?.addEventListener('click', () => this.prevChapter());
    document.getElementById('next-btn-bottom')?.addEventListener('click', () => this.nextChapter());
    document.getElementById('sidebar-toggle')?.addEventListener('click', () => this.toggleSidebar());
    document.getElementById('download-btn')?.addEventListener('click', () => {
      window.open('/api/download/epub', '_blank');
    });

    // Help / shortcuts panel
    const helpBtn = document.getElementById('help-btn');
    const panel = document.getElementById('shortcuts-panel');
    const closeBtn = document.getElementById('close-shortcuts');

    helpBtn?.addEventListener('click', () => {
      const hidden = panel.hasAttribute('hidden');
      if (hidden) {
        panel.removeAttribute('hidden');
        helpBtn.setAttribute('aria-expanded', 'true');
        closeBtn?.focus();
      } else {
        panel.setAttribute('hidden', '');
        helpBtn.setAttribute('aria-expanded', 'false');
      }
    });
    closeBtn?.addEventListener('click', () => {
      panel?.setAttribute('hidden', '');
      helpBtn?.setAttribute('aria-expanded', 'false');
      helpBtn?.focus();
    });
    panel?.addEventListener('click', (e) => {
      if (e.target === panel) {
        panel.setAttribute('hidden', '');
        helpBtn?.setAttribute('aria-expanded', 'false');
      }
    });
  }

  setupKeyboard() {
    document.addEventListener('keydown', (e) => {
      if (['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;
      const panel = document.getElementById('shortcuts-panel');

      if (e.key === 'Escape') {
        if (!panel?.hasAttribute('hidden')) {
          panel.setAttribute('hidden', '');
          document.getElementById('help-btn')?.focus();
        }
        return;
      }
      if (e.key === '?' || (e.key === '/' && e.shiftKey)) {
        e.preventDefault();
        document.getElementById('help-btn')?.click();
        return;
      }

      switch (e.key) {
        case ' ':
          e.preventDefault();
          this.toggleTTS();
          break;
        case 'ArrowRight':
          if (!e.altKey) this.nextChapter();
          break;
        case 'ArrowLeft':
          if (!e.altKey) this.prevChapter();
          break;
        case '+':
        case '=':
          this.increaseFontSize();
          break;
        case '-':
        case '_':
          this.decreaseFontSize();
          break;
        case 'c':
        case 'C':
          this.toggleContrast();
          break;
      }
    });
  }

  nextChapter() {
    if (this.currentChapter < this.data.chapters.length - 1)
      this.renderChapter(this.currentChapter + 1);
  }

  prevChapter() {
    if (this.currentChapter > 0)
      this.renderChapter(this.currentChapter - 1);
  }

  goToChapter(i) {
    this.renderChapter(i);
  }

  increaseFontSize() {
    const s = ['sm','md','lg','xl'];
    const i = s.indexOf(this.fontSize);
    if (i < s.length - 1) this.setFontSize(s[i + 1]);
  }

  decreaseFontSize() {
    const s = ['sm','md','lg','xl'];
    const i = s.indexOf(this.fontSize);
    if (i > 0) this.setFontSize(s[i - 1]);
  }

  updateProgress() {
    const pct = Math.round((this.currentChapter + 1) / this.data.chapters.length * 100);
    const bar = document.getElementById('progress-bar');
    const txt = document.getElementById('progress-text');
    if (bar) {
      bar.style.width = pct + '%';
      bar.setAttribute('aria-valuenow', pct);
    }
    if (txt) txt.textContent = `${this.currentChapter + 1} of ${this.data.chapters.length}`;
  }

  updateNavButtons() {
    const prevBtns = [document.getElementById('prev-btn'), document.getElementById('prev-btn-bottom')];
    const nextBtns = [document.getElementById('next-btn'), document.getElementById('next-btn-bottom')];
    const atStart = this.currentChapter === 0;
    const atEnd = this.currentChapter === this.data.chapters.length - 1;
    prevBtns.forEach(b => { if (b) b.disabled = atStart; });
    nextBtns.forEach(b => { if (b) b.disabled = atEnd; });
  }

  highlightSidebar(index) {
    document.querySelectorAll('#chapter-list button').forEach((btn, i) => {
      const active = i === index;
      btn.classList.toggle('active', active);
      if (active) {
        btn.setAttribute('aria-current', 'page');
        btn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else {
        btn.removeAttribute('aria-current');
      }
    });
  }

  toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const btn = document.getElementById('sidebar-toggle');
    const open = sidebar?.classList.toggle('open');
    btn?.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  showLoading(show) {
    const el = document.getElementById('loading');
    if (el) el.style.display = show ? 'flex' : 'none';
  }
}

const reader = new SinhalaReader();
document.addEventListener('DOMContentLoaded', () => reader.init());
