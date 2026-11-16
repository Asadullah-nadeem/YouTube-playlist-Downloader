import os
import threading
from flask import Flask, request, jsonify, render_template_string
import socketio

from src.core.downloader import downloader
from src.core.playlist import PlaylistManager
from src.utils.config import config
from src.utils.history import history_manager
from src.utils.logger import logger
from src.utils.ffmpeg_checker import FFmpegChecker

# Initialize Flask and SocketIO
sio = socketio.Server(async_mode='threading', cors_allowed_origins='*')
app = Flask(__name__)
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Studio Pro - Web Dashboard</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }</style>
</head>
<body class="min-h-screen p-6 md:p-10 flex flex-col items-center">
    <div class="w-full max-w-4xl space-y-6">
        <!-- Header -->
        <header class="flex items-center justify-between border-b border-slate-700/60 pb-6">
            <div class="flex items-center space-x-3">
                <span class="text-3xl">🎬</span>
                <div>
                    <h1 class="text-2xl font-bold text-white tracking-tight">YouTube Studio Pro</h1>
                    <p class="text-xs text-slate-400">High-Performance Media & Playlist Downloader</p>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <span id="socket-status" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    ● Connected
                </span>
            </div>
        </header>

        <!-- Input Card -->
        <div class="bg-slate-800/80 border border-slate-700/50 rounded-2xl p-6 shadow-xl space-y-4">
            <label class="block text-sm font-semibold text-slate-200">Video or Playlist URL</label>
            <div class="flex flex-col sm:flex-row gap-3">
                <input id="url-input" type="text" placeholder="Paste YouTube link here..." 
                    class="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-slate-500">
                <button onclick="analyzeUrl()" class="px-6 py-3 bg-teal-600 hover:bg-teal-500 font-semibold rounded-xl text-sm transition shadow-lg shadow-teal-900/30">
                    🔍 Analyze
                </button>
            </div>

            <!-- Preview Card -->
            <div id="preview-box" class="hidden bg-slate-900/60 border border-slate-700/60 rounded-xl p-4 flex flex-col sm:flex-row gap-4 items-center">
                <img id="prev-img" class="w-36 h-20 object-cover rounded-lg bg-slate-800" src="" alt="Thumbnail">
                <div class="flex-1 text-left">
                    <h3 id="prev-title" class="font-bold text-slate-100 text-sm md:text-base line-clamp-2"></h3>
                    <p id="prev-meta" class="text-xs text-slate-400 mt-1"></p>
                </div>
            </div>

            <!-- Controls Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                <div>
                    <label class="block text-xs font-medium text-slate-400 mb-1">Type</label>
                    <select id="media-type" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200">
                        <option value="video">Video (MP4 / MKV)</option>
                        <option value="audio">Audio Only (MP3)</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-400 mb-1">Resolution / Quality</label>
                    <select id="resolution" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200">
                        <option value="1080p">1080p Full HD</option>
                        <option value="best">Best Available (4K/2K)</option>
                        <option value="720p">720p HD</option>
                        <option value="480p">480p</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-400 mb-1">Speed Boost (Fragments)</label>
                    <select id="threads" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200">
                        <option value="8">8 Parallel Connections (Fast)</option>
                        <option value="16">16 Connections (Turbo)</option>
                        <option value="4">4 Connections</option>
                    </select>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex gap-3 pt-2">
                <button id="download-btn" onclick="startDownload()" class="flex-1 py-3.5 bg-blue-600 hover:bg-blue-500 font-bold rounded-xl text-sm transition shadow-lg shadow-blue-900/30">
                    🚀 Download Now
                </button>
                <button id="cancel-btn" onclick="cancelDownload()" disabled class="px-6 py-3.5 bg-red-600/30 hover:bg-red-600 disabled:opacity-40 font-bold rounded-xl text-sm text-red-200 transition">
                    ⏹ Cancel
                </button>
            </div>
        </div>

        <!-- Progress HUD -->
        <div class="bg-slate-800/80 border border-slate-700/50 rounded-2xl p-6 shadow-xl space-y-3">
            <div class="flex justify-between items-center text-sm font-semibold">
                <span id="prog-status" class="text-slate-300">Ready</span>
                <span id="prog-pct" class="text-blue-400">0%</span>
            </div>
            <div class="w-full bg-slate-900 rounded-full h-3 overflow-hidden border border-slate-700/50">
                <div id="prog-bar" class="bg-blue-500 h-full w-0 transition-all duration-300"></div>
            </div>
            <div class="flex justify-between text-xs text-slate-400 pt-1">
                <span id="prog-speed">Speed: -- MB/s</span>
                <span id="prog-eta">ETA: --:--</span>
                <span id="prog-transferred">0 B / 0 B</span>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        socket.on('connect', () => {
            document.getElementById('socket-status').innerText = '● Connected';
        });
        socket.on('disconnect', () => {
            document.getElementById('socket-status').innerText = '○ Disconnected';
        });
        socket.on('progress', (data) => {
            if (data.status === 'downloading') {
                const pct = data.percent.toFixed(1);
                document.getElementById('prog-pct').innerText = pct + '%';
                document.getElementById('prog-bar').style.width = pct + '%';
                document.getElementById('prog-status').innerText = 'Downloading ' + (data.filename || '');
                document.getElementById('prog-speed').innerText = 'Speed: ' + (data.speed_str || '--');
                document.getElementById('prog-eta').innerText = 'ETA: ' + (data.eta_str || '--:--');
                document.getElementById('prog-transferred').innerText = (data.downloaded_str || '0 B') + ' / ' + (data.total_str || '0 B');
            } else if (data.status === 'processing') {
                document.getElementById('prog-status').innerText = 'Finalizing & Merging...';
            } else if (data.status === 'finished') {
                document.getElementById('prog-pct').innerText = '100%';
                document.getElementById('prog-bar').style.width = '100%';
                document.getElementById('prog-status').innerText = 'Completed! 🎉';
                document.getElementById('download-btn').disabled = false;
                document.getElementById('cancel-btn').disabled = true;
            }
        });

        async function analyzeUrl() {
            const url = document.getElementById('url-input').value.trim();
            if (!url) return;
            const res = await fetch('/api/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url})
            });
            const data = await res.json();
            if (data.success) {
                const p = data.info;
                document.getElementById('preview-box').classList.remove('hidden');
                document.getElementById('prev-title').innerText = p.title;
                document.getElementById('prev-meta').innerText = 'Channel: ' + p.uploader + ' | ' + (p.is_playlist ? p.count + ' videos' : p.videos[0].duration);
                if (p.thumbnail) document.getElementById('prev-img').src = p.thumbnail;
            }
        }

        async function startDownload() {
            const url = document.getElementById('url-input').value.trim();
            if (!url) return;
            document.getElementById('download-btn').disabled = true;
            document.getElementById('cancel-btn').disabled = false;
            await fetch('/api/download', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    url: url,
                    type: document.getElementById('media-type').value,
                    resolution: document.getElementById('resolution').value,
                    threads: parseInt(document.getElementById('threads').value)
                })
            });
        }

        async function cancelDownload() {
            await fetch('/api/cancel', {method: 'POST'});
            document.getElementById('prog-status').innerText = 'Cancelled by user';
            document.getElementById('download-btn').disabled = false;
            document.getElementById('cancel-btn').disabled = true;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    info = PlaylistManager.get_playlist_info(url)
    if info:
        return jsonify({'success': True, 'info': info})
    return jsonify({'success': False, 'error': 'Could not inspect media'}), 400

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    media_type = data.get('type', 'video')
    resolution = data.get('resolution', '1080p')
    threads = int(data.get('threads', 8))

    def worker():
        downloader.download(
            url=url,
            media_type=media_type,
            resolution=resolution,
            concurrent_fragments=threads,
            progress_callback=lambda d: sio.emit('progress', d)
        )

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({'success': True, 'message': 'Download started'})

@app.route('/api/cancel', methods=['POST'])
def api_cancel():
    downloader.cancel()
    return jsonify({'success': True, 'message': 'Download cancelled'})

@app.route('/api/history', methods=['GET'])
def api_history():
    return jsonify({'history': history_manager.get_all()})

if __name__ == '__main__':
    print("🚀 Starting YouTube Studio Web Server at http://127.0.0.1:5000 ...")
    from werkzeug.serving import run_simple
    run_simple('127.0.0.1', 5000, app.wsgi_app, use_reloader=False)
