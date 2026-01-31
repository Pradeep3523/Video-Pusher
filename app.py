import yt_dlp
import os
from flask import Flask, render_template_string, request

app = Flask(__name__)

# This function is optimized for Web Servers (Render/Koyeb)
def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        # This User-Agent is critical to stop YouTube from blocking the server
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen_res = set()
            
            if 'formats' in info:
                for f in info['formats']:
                    h = f.get('height')
                    # We only want files that have both Video and Audio to avoid "silent" videos
                    if h and h not in seen_res and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                        formats.append({
                            'url': f['url'],
                            'resolution': f'{h}p',
                            'ext': f.get('ext', 'mp4')
                        })
                        seen_res.add(h)
            
            info['available_formats'] = sorted(formats, key=lambda x: int(x['resolution'].replace('p','')), reverse=True)
            return info
    except Exception as e:
        print(f"Extraction Error: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    video_data = None
    if request.method == "POST":
        url = request.form.get("video_url")
        if url:
            video_data = get_video_info(url)
    
    return render_template_string(TEMPLATE, video=video_data)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamUltra | Elite</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); }
        .loader { border-top-color: #3b82f6; animation: spinner 1.5s linear infinite; }
        @keyframes spinner { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-6">
    <div class="max-w-xl w-full text-center">
        <h1 class="text-7xl font-bold mb-2 tracking-tighter">STREAM<span class="text-blue-500">ULTRA</span></h1>
        <p class="text-xs tracking-[0.5em] text-white/30 mb-10">BY PRADEEP PAUDEL</p>
        
        <form method="POST" onsubmit="showLoading()" class="mb-10">
            <input name="video_url" type="url" placeholder="Paste Video Link Here" required 
                   class="w-full bg-white/10 border border-white/20 rounded-2xl p-5 mb-4 outline-none focus:border-blue-500 text-center text-lg">
            <button id="btn-text" type="submit" class="w-full bg-blue-600 py-5 rounded-2xl font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/20">
                EXTRACT VIDEO
            </button>
            <div id="loading" class="hidden flex justify-center mt-4">
                <div class="loader ease-linear rounded-full border-4 border-t-4 border-gray-200 h-10 w-10"></div>
            </div>
        </form>

        {% if video %}
        <div class="glass p-8 rounded-[2rem] text-left animate-in fade-in slide-in-from-bottom-4 duration-500">
            <img src="{{ video.thumbnail }}" class="w-full rounded-xl mb-6 border border-white/10">
            <h2 class="text-xl font-bold mb-6 line-clamp-2">{{ video.title }}</h2>
            
            <div class="grid grid-cols-1 gap-3">
                {% for f in video.available_formats %}
                <a href="{{ f.url }}" target="_blank" rel="noopener noreferrer"
                   class="flex justify-between items-center bg-white/10 p-5 rounded-2xl hover:bg-white hover:text-black transition-all group">
                    <span class="font-bold text-lg">{{ f.resolution }} High Quality</span>
                    <span class="bg-blue-500 text-white text-[10px] px-3 py-1 rounded-full group-hover:bg-black uppercase">Download .{{ f.ext }}</span>
                </a>
                {% endfor %}
            </div>
        </div>
        {% elif request.method == 'POST' %}
        <p class="text-red-400 font-bold">Extraction failed. YouTube might be blocking the server. Try a different link.</p>
        {% endif %}

        <div class="mt-16 flex items-center gap-5 text-left border-t border-white/10 pt-8">
            <img src="https://raw.githubusercontent.com/Pradeep3523/Video-Pusher/main/6.jpg" class="w-16 h-16 rounded-full border-2 border-blue-500 object-cover shadow-xl">
            <div>
                <p class="text-[10px] text-blue-400 font-black uppercase tracking-widest">Lead Developer</p>
                <p class="text-xl font-bold">Pradeep Paudel</p>
            </div>
        </div>
    </div>

    <script>
        function showLoading() {
            document.getElementById('btn-text').innerText = "Processing...";
            document.getElementById('loading').classList.remove('hidden');
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)