import os
import json
import threading
import webbrowser
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__, 
            static_folder='dashboard',
            template_folder='dashboard')

PORT = 5000
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/<path:filename>')
def serve_dashboard_files(filename):
    return send_from_directory(os.path.join(DATA_DIR, 'dashboard'), filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def get_files():
    """List available JSON files."""
    files = []
    dumps_path = os.path.join(DATA_DIR, 'dumps')
    if os.path.exists(dumps_path):
        for f in os.listdir(dumps_path):
            if f.endswith('.json') and 'secrets' in f:
                files.append(f)
    return jsonify(files)

@app.route('/api/data/<filename>', methods=['GET'])
def get_data(filename):
    """Get data from a specific JSON file."""
    if not filename.endswith('.json'):
        return jsonify({"error": "Invalid file type"}), 400
        
    path = os.path.join(DATA_DIR, 'dumps', filename)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "File not found"}), 404

@app.route('/api/extract/<browser>', methods=['POST'])
def trigger_extraction(browser):
    """Trigger extraction for a specific browser."""
    # Output to dumps folder
    output_file = f"dumps/secrets_{browser}.json"
    
    try:
        import subprocess
        import sys
        
        # Kill browser processes first (but NOT python.exe)
        subprocess.run(
            "taskkill /F /IM chrome.exe /IM msedge.exe /IM brave.exe /IM firefox.exe", 
            shell=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        # Run extraction
        cmd = [sys.executable, "main.py", f"/b:{browser}", f"/f:{output_file}"]
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=DATA_DIR,
            timeout=120
        )
        
        if result.returncode == 0:
            return jsonify({
                "status": "success", 
                "file": os.path.basename(output_file),
                "log": result.stdout
            })
        else:
            return jsonify({
                "status": "error", 
                "log": result.stderr or result.stdout or "Unknown error"
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error", 
            "log": "Extraction timed out after 120 seconds"
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "log": str(e)
        })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get combined stats from all browsers."""
    stats = {
        "total_logins": 0,
        "total_cookies": 0,
        "total_history": 0,
        "browsers": []
    }
    
    browsers = ['chrome', 'edge', 'firefox', 'brave', 'opera', 'vivaldi', 'duckduckgo']
    
    for browser in browsers:
        path = os.path.join(DATA_DIR, 'dumps', f"secrets_{browser}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    browser_data = data.get(browser, {})
                    
                    logins = len(browser_data.get('logins', []))
                    cookies = len(browser_data.get('cookies', []))
                    history = len(browser_data.get('history', []))
                    
                    stats["total_logins"] += logins
                    stats["total_cookies"] += cookies
                    stats["total_history"] += history
                    stats["browsers"].append({
                        "name": browser,
                        "logins": logins,
                        "cookies": cookies,
                        "history": history
                    })
            except Exception:
                pass
    
    return jsonify(stats)

def open_browser():
    """Open browser after a short delay."""
    import time
    time.sleep(1)
    webbrowser.open(f'http://127.0.0.1:{PORT}')

def run_BAF(open_browser_flag=True):
    """Run the dashboard server."""
    print(f"\n{'='*50}")
    print(f"  Browser Artifact Framework (BAF) Dashboard")
    print(f"  Running on: http://127.0.0.1:{PORT}")
    print(f"{'='*50}\n")
    
    if open_browser_flag:
        threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(
        host='127.0.0.1', 
        port=PORT, 
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    run_BAF()
