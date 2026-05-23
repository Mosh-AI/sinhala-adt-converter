"""
Google Cloud Text-to-Speech engine for Sinhala (si-LK).
Uses REST API with API key authentication.
Caches audio as MP3 files to avoid repeated API calls.

Available voices:
  si-LK-Standard-A  Female
  si-LK-Standard-B  Male
  si-LK-Standard-C  Female
  si-LK-Standard-D  Male

Pricing: ~$4 per 1M characters (Standard voices)
"""
import hashlib
import base64
import requests
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "demo" / "audio"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TTS_ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"

DEFAULT_VOICE = ""  # Let Google auto-select the best available si-LK voice
LANGUAGE_CODE = "si-LK"


def _cache_key(text: str, voice: str, speed: float) -> str:
    raw = f"{voice}|{speed:.2f}|{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


class GoogleTTS:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def synthesize(self, text: str, speed: float = 1.0,
                   voice: str = DEFAULT_VOICE) -> bytes | None:
        """
        Convert text to MP3 bytes using Google Cloud TTS.
        Returns cached bytes if available, None on failure.
        """
        text = text.strip()
        if not text:
            return None

        # Clamp speed to Google's allowed range
        speed = round(max(0.25, min(4.0, speed)), 2)

        # Serve from cache if available
        key = _cache_key(text, voice, speed)
        cache_file = CACHE_DIR / f"{key}.mp3"
        if cache_file.exists():
            return cache_file.read_bytes()

        try:
            resp = requests.post(
                TTS_ENDPOINT,
                params={"key": self.api_key},
                json={
                    "input": {"text": text},
                    "voice": {
                        "languageCode": LANGUAGE_CODE,
                        **({"name": voice} if voice else {}),
                    },
                    "audioConfig": {
                        "audioEncoding": "MP3",
                        "speakingRate": speed,
                        "pitch": 0.0,
                        "volumeGainDb": 0.0,
                    },
                },
                timeout=20,
            )

            if resp.status_code == 200:
                audio_bytes = base64.b64decode(resp.json()["audioContent"])
                cache_file.write_bytes(audio_bytes)
                print(f"TTS synthesized {len(text)} chars → {len(audio_bytes):,} bytes (cached)")
                return audio_bytes

            print(f"Google TTS error {resp.status_code}: {resp.text[:200]}")
            return None

        except Exception as exc:
            print(f"Google TTS exception: {exc}")
            return None

    def available_voices(self) -> list[dict]:
        """Return list of available si-LK voices from the API."""
        try:
            resp = requests.get(
                "https://texttospeech.googleapis.com/v1/voices",
                params={"key": self.api_key, "languageCode": LANGUAGE_CODE},
                timeout=10,
            )
            if resp.status_code == 200:
                voices = resp.json().get("voices", [])
                return [
                    {
                        "name": v["name"],
                        "gender": v.get("ssmlGender", "NEUTRAL"),
                        "naturalSampleRateHertz": v.get("naturalSampleRateHertz", 24000),
                    }
                    for v in voices
                ]
        except Exception:
            pass
        return []

    def test_connection(self) -> bool:
        """Quick connectivity test with a short Sinhala string."""
        result = self.synthesize("ශ්‍රී ලංකාව", speed=1.0)
        return result is not None

    def clear_cache(self) -> int:
        """Delete all cached audio files. Returns count deleted."""
        count = 0
        for f in CACHE_DIR.glob("*.mp3"):
            f.unlink()
            count += 1
        return count
