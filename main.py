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
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            audio_url = None
            for fmt in info.get('formats', []):
                if fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
                    audio_url = fmt.get('url')
                    break
            
            if not audio_url:
                audio_url = info.get('url')

            # Hacer proxy del audio para saltarse bloqueos CORS de YouTube
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
            
