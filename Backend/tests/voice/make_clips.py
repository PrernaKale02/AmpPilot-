"""Creates the test questions as audio: Hindi/Marathi via Gemini TTS, extra English via macOS say."""
import subprocess, sys, wave
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # Backend folder, for app.core.config
from google import genai
from google.genai import types
from app.core.config import get_settings

HERE = Path(__file__).parent
client = genai.Client(api_key=get_settings().gemini_api_key)
TTS_MODELS = ["gemini-3.8-flash-tts", "gemini-2.5-flash-preview-tts"]

CLIPS = {
    "hi_01": "मेरी बैटरी कितनी है?",
    "hi_02": "सबसे पास का चार्जिंग स्टेशन दिखाओ",
    "hi_03": "बैटरी में कितना चार्ज बचा है?",
    "hi_04": "पास में गाड़ी कहाँ चार्ज कर सकते हैं?",
    "hi_05": "मेरी बैटरी का प्रतिशत बताओ",
    "mr_01": "माझी बॅटरी किती आहे?",
    "mr_02": "जवळचे चार्जिंग स्टेशन दाखव",
    "mr_03": "बॅटरीमध्ये किती चार्ज शिल्लक आहे?",
    "mr_04": "जवळपास गाडी कुठे चार्ज करू शकतो?",
    "mr_05": "माझ्या बॅटरीची टक्केवारी सांग",
}

def tts(text):
    for model in TTS_MODELS:
        try:
            r = client.models.generate_content(
                model=model, contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
            return r.candidates[0].content.parts[0].inline_data.data
        except Exception as exc:
            print(f"  {model} failed: {exc}")
    raise SystemExit("All TTS models failed.")

import time
for name, text in CLIPS.items():
    if (HERE / f'{name}.m4a').exists():
        print('skip', name); continue
    pcm = tts(text)
    time.sleep(25)  # free tier: 3 TTS requests per minute
    with wave.open(str(HERE / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
    subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", f"{name}.wav", f"{name}.m4a"], cwd=HERE, check=True)
    print("made", name)

for name, text in {"en_03": "How much charge is left in my battery",
                   "en_04": "Where can I charge my car nearby",
                   "en_05": "Tell me my battery percentage"}.items():
    subprocess.run(["say", "-o", f"{name}.aiff", text], cwd=HERE, check=True)
    subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", f"{name}.aiff", f"{name}.m4a"], cwd=HERE, check=True)
    print("made", name)
