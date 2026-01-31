import yt_dlp
import requests
import os
from flask import Flask, render_template_string, request, Response, stream_with_context

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

def get_video_info(url):
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True, 
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen_res = set()
            if 'formats' in info:
                for f in info['formats']:
                    h = f.get('height')
                    # Filter for formats that have both audio and video (e.g., 720p, 360p)
                    if h and h not in seen_res and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                        formats.append({
                            'format_id': f['format_id'], 
                            'resolution': f'{h}p', 
                            'size': f.get('filesize') or f.get('filesize_approx')
                        })
                        seen_res.add(h)
            info['available_formats'] = sorted(formats, key=lambda x: int(x['resolution'].replace('p','')), reverse=True)
            return info
    except Exception as e:
        print(f"Error fetching info: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    video_data, show_dashboard = None, False
    if request.method == "POST":
        url = request.form.get("video_url")
        video_data = get_video_info(url)
        if video_data: 
            show_dashboard = True
    return render_template_string(TEMPLATE, video=video_data, show_dashboard=show_dashboard)

@app.route("/proxy_download")
def proxy_download():
    video_url = request.args.get('url')
    fid = request.args.get('format_id')
    mode = request.args.get('mode', 'video')
    title = request.args.get('title', 'video')
    
    f_select = fid if fid else ('best[ext=mp4]/best' if mode == 'video' else 'bestaudio/best')
    
    try:
        with yt_dlp.YoutubeDL({'format': f_select, 'quiet': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            stream_url = info['url']
            size = info.get('filesize') or info.get('filesize_approx')

        def generate():
            # This streams the video from the source through your server to the user
            with requests.get(stream_url, stream=True, timeout=60) as r:
                for chunk in r.iter_content(chunk_size=1024*1024): # 1MB chunks
                    if chunk:
                        yield chunk

        headers = {
            "Content-Disposition": f"attachment; filename=\"{title}.{'mp4' if mode=='video' else 'mp3'}\"",
            "Content-Type": "video/mp4" if mode=="video" else "audio/mpeg"
        }
        if size:
            headers["Content-Length"] = str(size)
            
        return Response(stream_with_context(generate()), headers=headers)
    except Exception as e:
        return f"Download failed: {str(e)}", 500

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamUltra | Elite Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;700&display=swap');
        body { background: #000; color: #fff; font-family: 'Space Grotesk', sans-serif; overflow-x: hidden; }
        .hero-img { position: fixed; inset: 0; width: 100%; height: 100%; object-fit: cover; filter: brightness(0.2) blur(15px); z-index: -2; }
        .tile { 
            background: rgba(255,255,255,0.03); 
            backdrop-filter: blur(15px); 
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.4s ease;
        }
        .tile:hover { background: #fff; color: #000; transform: translateY(-10px); }
        .stagger { animation: slide 0.8s ease forwards; opacity: 0; }
        @keyframes slide { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    {% if not show_dashboard %}
    <div class="h-screen w-full flex flex-col items-center justify-center p-6">
        <div class="text-center space-y-6">
            <h1 class="text-8xl font-bold tracking-tighter stagger">STREAM<span class="text-blue-500">ULTRA</span></h1>
            <p class="text-xs tracking-[1em] text-white/30 stagger" style="animation-delay:0.2s">DEVELOPED BY PRADEEP PAUDEL</p>
            <form method="POST" class="mt-10 relative max-w-xl mx-auto stagger" style="animation-delay:0.4s">
                <input name="video_url" type="url" placeholder="Paste URL here..." required 
                       class="w-full bg-white/5 border border-white/20 rounded-2xl py-6 px-8 outline-none focus:border-blue-500 text-xl text-center">
                <button type="submit" class="mt-4 w-full bg-blue-600 py-4 rounded-xl font-bold hover:bg-blue-500 transition-all">EXTRACT VIDEO</button>
            </form>
        </div>
    </div>
    {% else %}
    <div class="min-h-screen w-full p-8 md:p-12 relative">
        <img src="{{ video.thumbnail }}" class="hero-img">
        <header class="flex justify-between items-center mb-20 stagger">
            <h2 class="text-3xl font-bold italic">ULTRA<span class="text-blue-500">PROXY</span></h2>
            <a href="/" class="px-6 py-2 border border-white/20 rounded-full hover:bg-white hover:text-black transition-all">New Search</a>
        </header>

        <main class="max-w-6xl">
            <h1 class="text-5xl md:text-7xl font-bold tracking-tighter mb-6 stagger" style="animation-delay:0.2s">{{ video.title }}</h1>
            <div class="flex flex-wrap gap-4 mb-12 stagger" style="animation-delay:0.3s">
                {% for f in video.available_formats %}
                <a href="{{ url_for('proxy_download', url=video.webpage_url, title=video.title, format_id=f.format_id) }}" 
                   class="tile px-8 py-6 rounded-3xl text-center min-w-[120px]">
                    <span class="block text-2xl font-bold">{{ f.resolution }}</span>
                    <span class="text-[10px] opacity-50 uppercase font-black">MP4</span>
                </a>
                {% endfor %}
            </div>

            <div class="mt-20 flex items-center gap-6 stagger" style="animation-delay:0.5s">
                <img src="https://raw.githubusercontent.com/Pradeep3523/Video-Pusher/main/6.jpg" 
                     class="w-20 h-20 rounded-full border-2 border-blue-500 object-cover shadow-[0_0_30px_rgba(59,130,246,0.3)]">
                <div>
                    <p class="text-[10px] text-blue-400 font-black tracking-widest uppercase">Lead Architect</p>
                    <p class="text-2xl font-bold">Pradeep Paudel</p>
                </div>
            </div>
        </main>
    </div>
    {% endif %}
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)