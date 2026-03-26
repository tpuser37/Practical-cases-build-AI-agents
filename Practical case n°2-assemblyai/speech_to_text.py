import os
import assemblyai as aai
from pathlib import Path

AUDIO_FILE = "AUDIO/Dollar Drop Prediction.mp3"

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
if not aai.settings.api_key:
    raise RuntimeError("ASSEMBLYAI_API_KEY is not set")

# --- Fonction de transcription + sentiment ---
def transcribe_audio_with_sentiment(audio_path: str):
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    config = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.best,
        sentiment_analysis=True   
    )

    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_path)

    if transcript.status == "error":
        raise RuntimeError(f"Transcription failed: {transcript.error}")

    return transcript

# --- Exécution ---
if __name__ == "__main__":
    transcript = transcribe_audio_with_sentiment(AUDIO_FILE)

    print("\n--- TRANSCRIPTION ---\n")
    print(transcript.text)

    print("\n--- SENTIMENT ANALYSIS ---\n")

    if transcript.sentiment_analysis:
        for segment in transcript.sentiment_analysis:
            print(
                f"[{segment.sentiment.upper()} | "
                f"Confidence: {segment.confidence:.2f}] "
                f"{segment.text}"
            )
    else:
        print("No sentiment analysis available.")
