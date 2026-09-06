from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

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

            return {
                "status": "success",
                "title": info.get('title'),
                "uploader": info.get('uploader'),
                "thumbnail": info.get('thumbnail'),
                "download_url": audio_url
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
      
