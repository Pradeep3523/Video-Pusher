import yt_dlp
import os
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

def get_video_info(url):
    # We use a modern User-Agent to avoid the "Sign in" block
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen_res = set()
            
            # Filter for files that contain BOTH video and audio
            if 'formats' in info:
                for f in info['formats']:
                    h = f.get('height')
                    if h and h not in seen_res and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                        formats.append({
                            'url': f['url'], # This is the direct Google Video URL
                            'resolution': f'{h}p',
                            'ext': f.get('ext', 'mp4')
                        })
                        seen_res.add(h)
            
            info['available_formats'] = sorted(formats, key=lambda x: int(x['resolution'].replace('p','')), reverse=True)
            return info
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    video_data = None
    if request.method == "POST":
        url = request.form.get("video_url")
        video_data = get_video_info(url)
    return render_template_string(TEMPLATE, video=video_data)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>StreamUltra | Elite</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-6">
    <div class="max-w-xl w-full text-center">
        <h1 class="text-6xl font-bold mb-8">STREAM<span class="text-blue-500">ULTRA</span></h1>
        
        <form method="POST" class="mb-10">
            <input name="video_url" type="url" placeholder="Paste link..." required 
                   class="w-full bg-white/10 border border-white/20 rounded-xl p-4 mb-4 outline-none focus:border-blue-500">
            <button type="submit" class="w-full bg-blue-600 py-4 rounded-xl font-bold hover:bg-blue-700">FETCH VIDEO</button>
        </form>

        {% if video %}
        <div class="glass p-6 rounded-3xl text-left">
            <h2 class="text-xl font-bold mb-4">{{ video.title }}</h2>
            <div class="grid grid-cols-2 gap-3">
                {% for f in video.available_formats %}
                <a href="{{ f.url }}" target="_blank" download="{{ video.title }}.{{ f.ext }}"
                   class="bg-white/10 p-4 rounded-xl text-center hover:bg-white hover:text-black transition-all">
                    <span class="font-bold">{{ f.resolution }}</span><br>
                    <span class="text-xs opacity-50">Download .{{ f.ext }}</span>
                </a>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <div class="mt-10 flex items-center gap-4 text-left border-t border-white/10 pt-6">
            <img src="https://raw.githubusercontent.com/Pradeep3523/Video-Pusher/main/6.jpg" class="w-12 h-12 rounded-full border border-blue-500">
            <div>
                <p class="text-[10px] text-blue-400 font-bold uppercase">Developer</p>
                <p class="font-bold">Pradeep Paudel</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)