# import os
# import tempfile
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from groq import Groq
# from dotenv import load_dotenv

# from rag_engine import RAGEngine
# from tts_engine import TTSEngine

# load_dotenv()

# app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")

# groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# rag = RAGEngine()
# tts = TTSEngine()

# @app.get("/")
# async def get_index():
#     return FileResponse("static/index.html")

# @app.websocket("/ws/voice")
# async def voice_websocket(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             # Receive audio bytes from WebSockets
#             audio_data = await websocket.receive_bytes()
            
#             # Save chunk temporarily for Whisper transcription
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
#                 temp_audio.write(audio_data)
#                 temp_path = temp_audio.name
            
#             # 1. Speech-To-Text (Whisper via Groq)
#             with open(temp_path, "rb") as file:
#                 transcription = groq_client.audio.transcriptions.create(
#                     file=(temp_path, file.read()),
#                     model="whisper-large-v3",
#                     response_format="text"
#                 )
#             os.remove(temp_path)
            
#             transcribed_text = transcription.strip()
#             if not transcribed_text:
#                 continue

#             # Send transcript back to UI
#             await websocket.send_json({"type": "transcript", "text": transcribed_text})

#             # 2. Query RAG Vector Engine
#             rag_res = rag.query(transcribed_text)
#             answer_text = rag_res["answer"]
            
#             await websocket.send_json({"type": "answer", "text": answer_text, "sources": rag_res["sources"]})

#             # 3. Convert Answer to Speech Audio
#             audio_bytes = await tts.text_to_audio_bytes(answer_text)
            
#             # Send binary audio back
#             await websocket.send_bytes(audio_bytes)

#     except WebSocketDisconnect:
#         print("Client disconnected.")


import os
import tempfile
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from groq import Groq
from dotenv import load_dotenv

from rag_engine import RAGEngine
from tts_engine import TTSEngine

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
rag = RAGEngine()
tts = TTSEngine()

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1. Receive recorded audio bytes from the Web UI
            audio_data = await websocket.receive_bytes()
            
            # Save audio temporarily for Groq Whisper transcription
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(audio_data)
                temp_path = temp_audio.name
            
            # 2. Speech-To-Text (Whisper via Groq)
            with open(temp_path, "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                    file=(temp_path, file.read()),
                    model="whisper-large-v3",
                    response_format="text"
                )
            os.remove(temp_path)
            
            transcribed_text = transcription.strip()
            if not transcribed_text:
                continue

            # Send transcribed user query back to the frontend
            await websocket.send_json({"type": "transcript", "text": transcribed_text})

            # 3. Query RAG Vector Engine for the answer
            rag_res = rag.query(transcribed_text)
            answer_text = rag_res["answer"]
            
            # Send RAG answer text and document sources back to UI
            await websocket.send_json({
                "type": "answer", 
                "text": answer_text, 
                "sources": rag_res["sources"]
            })

            # 4. Convert Answer Text to Speech Audio (Base64)
            audio_bytes = await tts.text_to_audio_bytes(answer_text)
            
            # Convert binary audio bytes to a Base64 string for safe WebSockets delivery
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Send Base64 audio string back as JSON
            await websocket.send_json({"type": "audio", "audio": audio_b64})

    except WebSocketDisconnect:
        print("Client disconnected.")