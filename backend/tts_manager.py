import os
import hashlib
from gtts import gTTS

# Define where audio files are stored
TTS_CACHE_DIR = "static/tts_cache"
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

def get_tts_file(text: str, lang: str = 'en') -> str:
    """
    Checks for an existing file via MD5 hash.
    If not found, creates a new TTS mp3 file.
    """
    # 1. Check: Create a unique ID for the text to avoid duplicate work
    text_hash = hashlib.md5(text.encode()).hexdigest()
    file_name = f"{text_hash}.mp3"
    file_path = os.path.join(TTS_CACHE_DIR, file_name)

    # If the file exists, return the path immediately (Task: Check)
    if os.path.exists(file_path):
        print(f"✅ Cache hit for: {text_hash}")
        return file_path

    # 2. Create: Generate the file if it doesn't exist (Task: Create)
    try:
        print(f"🎙️ Generating new audio for: {text[:20]}...")
        tts = gTTS(text=text, lang=lang)
        tts.save(file_path)
        return file_path
    except Exception as e:
        print(f"❌ TTS Generation Error: {e}")
        return ""