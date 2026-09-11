from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import yt_dlp
import requests
import pykakasi

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar pykakasi para conversión a Romaji
kks = pykakasi.kakasi()

class TranscribeRequest(BaseModel):
    text: str

@app.post("/api/transcribe")
def transcribe_to_romaji(data: TranscribeRequest):
    try:
        if not data.text.strip():
            raise HTTPException(status_code=400, detail="El texto no puede estar vacío")
        
        # Procesa el texto en japonés
        result = kks.convert(data.text)
        
        # Une la pronunciación en Romaji separada por espacios
        romaji_text = " ".join([item['hepburn'] for item in result])
        
        return {
            "original": data.text,
            "romaji": romaji_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download")
def download_audio(url: str):
    try:
        ydl_opts = {
            'format': 'ba/b',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            audio_url = None
            for fmt in info.get('formats', []):
                if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                    audio_url = fmt.get('url')
                    break
            
            if not audio_url:
                audio_url = info.get('url')

            if not audio_url:
                raise HTTPException(status_code=400, detail="No se pudo extraer la URL de audio")

            req = requests.get(audio_url, stream=True)
            
            return StreamingResponse(
                req.iter_content(chunk_size=1024 * 64),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f'attachment; filename="{info.get("title", "audio")}.mp3"',
                    "X-Audio-Title": info.get('title', ''),
                    "X-Audio-Thumbnail": info.get('thumbnail', '')
                }
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
