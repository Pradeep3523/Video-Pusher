import yt_dlp 
import requests 
import os 
from flask import Flask, render_template_string, request, Response, stream_with_context 

app = Flask(__name__) 
app.config['SECRET_KEY'] = os.urandom(24) 

def get_video_info(url): 
    # Use a modern browser identity to prevent the "Sign in" block
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
                    # Filter for formats that include both audio and video
                    if h and h not in seen_res and f.get('acodec') != 'none' and f.get('vcodec') != 'none': 
                        formats.append({
                            'format_id': f['format_id'], 
                            'resolution': f'{h}p', 
                            'size': f.get('filesize') or f.get('filesize_approx')
                        }) 
                        seen_res.add(h) 
            info['available_formats'] = sorted(formats, key=lambda x: int(x['resolution'].replace('p','')), reverse=True) 
            return info 
    except: 
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
    
    with yt_dlp.YoutubeDL({'format': f_select, 'quiet': True}) as ydl: 
        info = ydl.extract_info(video_url, download=False) 
        stream_url = info['url']
        size = info.get('filesize') or info.get('filesize_approx') 

    def generate(): 
        # Reduced chunk size to 1MB to prevent 502 Bad Gateway errors on Render
        with requests.get(stream_url, stream=True, timeout=60) as r: 
            for chunk in r.iter_content(chunk_size=1024*1024): 
                if chunk: 
                    yield chunk 

    headers = {
        "Content-Disposition": f"attachment; filename=\"{title}.{'mp4' if mode=='video' else 'mp3'}\"", 
        "Content-Type": "video/mp4" if mode=="video" else "audio/mpeg"
    } 
    if size: 
        headers["Content-Length"] = str(size) 
    
    return Response(stream_with_context(generate()), headers=headers) 

TEMPLATE = """ 
<!DOCTYPE html> 
<html lang="en"> 
<head> 
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"> 
    <title>StreamUltra | Elite</title> 
    <script src="https://cdn.tailwindcss.com"></script> 
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet"> 
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script> 
    <style> 
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;700&display=swap'); 
        body { background: #000; color: #fff; font-family: 'Space Grotesk', sans-serif; overflow-x: hidden; } 
        .hero-img { position: fixed; inset: 0; width: 100%; height: 100%; object-fit: cover; filter: brightness(0.3) blur(20px); z-index: -2; transform: scale(1.1); } 
        .vignette { position: fixed; inset: 0; background: radial-gradient(circle, transparent 20%, black 100%); z-index: -1; } 
        .tile { background: rgba(255,255,255,0.03); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1); } 
        .tile:hover { background: #fff; color: #000; transform: translateY(-15px); border-color: #fff; } 
        .qr-overlay { background: rgba(0,0,0,0.95); backdrop-filter: blur(20px); } 
        #qrcode img { margin: auto; border: 10px solid white; border-radius: 10px; } 
        @keyframes slide { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } } 
        .stagger { animation: slide 0.8s ease forwards; opacity: 0; } 
    </style> 
</head> 
<body> 
    <div id="welcome" class="h-screen w-full flex flex-col items-center justify-center relative z-10 {% if show_dashboard %}hidden{% endif %}"> 
        <div class="text-center space-y-4"> 
            <h1 class="text-[10vw] font-bold italic tracking-tighter leading-none stagger" style="animation-delay:0.1s">STREAM<br><span class="text-blue-500">ULTRA</span></h1> 
            <p class="text-xs tracking-[1em] text-white/30 stagger" style="animation-delay:0.3s">ENCRYPTED MEDIA BYPASS v4.0</p> 
            <div id="init-ui" class="pt-12 stagger" style="animation-delay:0.5s"> 
                <button onclick="openPortal()" class="border border-white/20 hover:bg-white hover:text-black px-16 py-5 rounded-full text-xs font-bold uppercase tracking-widest transition-all">Connect to Proxy</button> 
            </div> 
            <div id="portal" class="hidden mt-10 w-full max-w-xl animate-up"> 
                <form method="POST" class="relative group"> 
                    <input name="video_url" type="url" placeholder="DROP VIDEO LINK" required class="w-full bg-white/5 border border-white/20 rounded-2xl py-6 px-10 outline-none focus:border-blue-500 text-center text-xl"> 
                    <button type="submit" class="absolute right-3 top-3 bg-blue-500 text-white w-14 h-14 rounded-xl hover:scale-105 transition-all"><i class="fa-solid fa-bolt"></i></button> 
                </form> 
            </div> 
        </div> 
    </div> 

    {% if show_dashboard %} 
    <div class="min-h-screen w-full flex flex-col p-12 relative"> 
        <img src="{{ video.thumbnail }}" class="hero-img"> 
        <div class="vignette"></div> 
        <header class="flex justify-between items-start z-10"> 
            <div class="stagger" style="animation-delay:0.1s"> 
                <h2 class="text-4xl font-bold tracking-tighter italic">ULTRA<span class="text-blue-500">PROXY</span></h2> 
                <p class="text-[10px] text-white/40 uppercase tracking-widest mt-1">Source: {{ video.extractor_key }}</p> 
            </div> 
            <a href="/" class="w-14 h-14 tile rounded-full flex items-center justify-center stagger" style="animation-delay:0.2s"><i class="fa-solid fa-xmark"></i></a> 
        </header> 

        <main class="flex-1 flex flex-col justify-end gap-12 z-10"> 
            <div class="stagger" style="animation-delay:0.3s"> 
                <h1 class="text-5xl md:text-7xl font-bold tracking-tighter max-w-5xl leading-none">{{ video.title }}</h1> 
                <div class="flex gap-6 mt-6 text-sm font-bold text-white/50"> 
                    <span><i class="fa-regular fa-clock mr-2 text-blue-500"></i>{{ video.duration_string }}</span> 
                    <span><i class="fa-regular fa-eye mr-2 text-blue-500"></i>{{ video.view_count if video.view_count else 'Verified' }} Views</span> 
                    <span><i class="fa-regular fa-calendar mr-2 text-blue-500"></i>{{ video.upload_date[:4] if video.upload_date else '2026' }}</span> 
                </div> 
            </div> 

            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 stagger" style="animation-delay:0.4s"> 
                {% for f in video.available_formats %} 
                <a href="{{ url_for('proxy_download', url=video.webpage_url, title=video.title, format_id=f.format_id) }}" class="tile aspect-square rounded-[2rem] flex flex-col items-center justify-center p-6"> 
                    <span class="text-3xl font-bold tracking-tighter">{{ f.resolution }}</span> 
                    <span class="text-[10px] opacity-40 font-bold mt-1">MP4 HD</span> 
                    <span class="text-[10px] bg-white/10 px-2 py-1 rounded mt-4">{% if f.size %}{{ f.size // 1048576 }}MB{% else %}LINK{% endif %}</span> 
                </a> 
                {% endfor %} 
                <a href="{{ url_for('proxy_download', url=video.webpage_url, title=video.title, mode='audio') }}" class="tile aspect-square rounded-[2rem] flex flex-col items-center justify-center p-6 border-blue-500/30"> 
                    <i class="fa-solid fa-music text-3xl text-blue-500 mb-2"></i> 
                    <span class="text-[10px] font-bold tracking-widest uppercase">MP3 Studio</span> 
                </a> 
                <button onclick="genQR('{{ url_for('proxy_download', url=video.webpage_url, title=video.title, mode='video', _external=True) }}')" class="tile aspect-square rounded-[2rem] flex flex-col items-center justify-center p-6 text-blue-400"> 
                    <i class="fa-solid fa-qrcode text-3xl mb-2"></i> 
                    <span class="text-[10px] font-bold tracking-widest uppercase">QR Share</span> 
                </button> 
            </div> 
            
            <div class="mt-10 pt-6 border-t border-white/10 flex items-center gap-4 stagger" style="animation-delay:0.8s"> 
                <img src="https://raw.githubusercontent.com/Pradeep3523/Video-Pusher/main/6.jpg" class="w-14 h-14 rounded-full border-2 border-blue-500 object-cover ring-4 ring-blue-500/20"> 
                <div> 
                    <p class="text-[10px] text-blue-400 font-bold uppercase tracking-tighter">Developed By</p> 
                    <p class="text-lg font-black text-white">Pradeep Paudel</p> 
                </div> 
            </div> 
        </main> 

        <div id="qr-modal" class="hidden fixed inset-0 z-[100] qr-overlay flex items-center justify-center p-6" onclick="closeQR()"> 
            <div class="text-center space-y-6 animate-in zoom-in duration-300" onclick="event.stopPropagation()"> 
                <div id="qrcode" class="bg-white p-4 rounded-lg"></div> 
                <p class="text-xs font-bold tracking-widest text-white/40 uppercase">Scan to download on Mobile</p> 
                <button onclick="closeQR()" class="px-8 py-3 bg-white text-black rounded-full text-[10px] font-black uppercase">Close</button> 
            </div> 
        </div> 
    </div> 
    {% endif %} 

    <script> 
        function openPortal() { document.getElementById('init-ui').classList.add('hidden'); document.getElementById('portal').classList.remove('hidden'); } 
        function genQR(url) { document.getElementById('qr-modal').classList.remove('hidden'); document.getElementById('qrcode').innerHTML = ""; new QRCode(document.getElementById("qrcode"), { text: url, width: 200, height: 200 }); } 
        function closeQR() { document.getElementById('qr-modal').classList.add('hidden'); } 
    </script> 
</body> 
</html> 
""" 

if __name__ == "__main__": 
    # Use dynamic port for Render; fallback to 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)