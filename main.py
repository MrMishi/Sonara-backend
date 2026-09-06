from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/download")
def download_audio(url: str):
    try:
        ydl_opts = {
            'format': 'ba/b',  # Busca bestaudio, y si no lo encuentra, toma el formato general disponible
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            audio_url = None
            # Intentar obtener el stream solo de audio
            for fmt in info.get('formats', []):
                if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                    audio_url = fmt.get('url')
                    break
            
            # Si no hay stream separado, tomar la URL directa del video/audio
            if not audio_url:
                audio_url = info.get('url')

            if not audio_url:
                raise HTTPException(status_code=400, detail="No se pudo extraer la URL de audio")

            # Transferir el stream directo al cliente para evitar bloqueos CORS
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
            
