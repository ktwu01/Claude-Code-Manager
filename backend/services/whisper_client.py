import httpx
from io import BytesIO

from backend.config import settings


class WhisperClient:
    """Transcribe audio using OpenAI Whisper API."""

    URL = "https://api.openai.com/v1/audio/transcriptions"

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        content_type = "audio/webm"
        if filename.endswith(".wav"):
            content_type = "audio/wav"
        elif filename.endswith(".mp3"):
            content_type = "audio/mpeg"
        elif filename.endswith(".m4a"):
            content_type = "audio/mp4"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.URL,
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                files={"file": (filename, BytesIO(audio_bytes), content_type)},
                data={"model": "whisper-1"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()["text"]


whisper_client = WhisperClient()
