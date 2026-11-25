# import edge_tts
# import io

# class TTSEngine:
#     def __init__(self, voice: str = "en-US-JennyNeural"):
#         self.voice = voice

#     async def text_to_audio_bytes(self, text: str) -> bytes:
#         communicate = edge_tts.Communicate(text, self.voice)
#         audio_stream = io.BytesIO()
#         async for chunk in communicate.stream():
#             if chunk["type"] == "audio":
#                 audio_stream.write(chunk["data"])
#         return audio_stream.getvalue()

# import edge_tts

# class TTSEngine:
#     def __init__(self, voice: str = "en-US-SteffanNeural"):
#         self.voice = voice

#     async def text_to_audio_bytes(self, text: str) -> bytes:
#         communicate = edge_tts.Communicate(text, self.voice)
#         audio_data = bytearray()
#         async for chunk in communicate.stream():
#             if chunk["type"] == "audio":
#                 audio_data.extend(chunk["data"])
#         return bytes(audio_data)


import edge_tts
import tempfile
import os

class TTSEngine:
    def __init__(self, voice: str = "en-US-SteffanNeural"):
        self.voice = voice

    async def text_to_audio_bytes(self, text: str) -> bytes:
        if not text.strip():
            return b""
            
        # Create temporary MP3 file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_path = temp_file.name

        # Generate audio using Edge TTS
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(temp_path)

        # Read generated audio bytes
        with open(temp_path, "rb") as f:
            audio_bytes = f.read()

        # Clean up temporary file
        os.remove(temp_path)
        return audio_bytes