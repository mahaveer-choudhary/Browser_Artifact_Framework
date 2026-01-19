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

    return jsonify({"error": "File not found"}), 404

@app.route('/reports/<path:filename>')
def serve_report(filename):
    """Serve generated reports from dumps folder."""
    return send_from_directory(os.path.join(DATA_DIR, 'dumps'), filename)

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

@app.route('/api/export', methods=['POST'])
def export_report():
    """Generate a forensic report."""
    import html  # Import for escaping
    try:
        # Get options from request
        options = request.get_json() or {}
        
        # Get selected browsers (default to all if not specified)
        selected_browsers = options.get('browsers', ['chrome', 'edge', 'firefox', 'brave', 'opera', 'vivaldi'])
        
        # Options
        inc_logins = options.get('logins', True)
        inc_cookies = options.get('cookies', True)
        inc_history = options.get('history', True)
        inc_top10 = options.get('top10', True)

        report_lines = []
        report_lines.append("<html><head><title>Forensic Report</title>")
        report_lines.append("<style>")
        report_lines.append("body { font-family: monospace; padding: 20px; background: #f0f0f0; }")
        report_lines.append(".section { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }")
        report_lines.append("h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }")
        report_lines.append("h2 { color: #0066cc; margin-top: 0; }")
        report_lines.append("table { width: 100%; border-collapse: collapse; margin-top: 10px; }")
        report_lines.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; word-break: break-all; }")
        report_lines.append("th { background-color: #f8f9fa; font-weight: bold; }")
        report_lines.append(".encrypted { color: #dc3545; font-style: italic; }")
        report_lines.append("</style></head><body>")
        
        report_lines.append(f"<h1>Forensic Artifact Report</h1>")
        report_lines.append(f"<p>Generated: {html.escape(os.path.basename(os.getcwd()))}</p>")
        
        # Helper to safely get and escape dict values
        def safe_get(d, key):
            return html.escape(str(d.get(key, '')))

        for browser in selected_browsers:
            path = os.path.join(DATA_DIR, 'dumps', f"secrets_{browser}.json")
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        browser_data = data.get(browser, {})
                        
                        report_lines.append(f"<div class='section'><h2>{html.escape(browser.upper())}</h2>")
                        
                        history = browser_data.get('history', [])

                        # Top 10 Visited
                        if inc_top10 and history:
                            try:
                                top_visited = sorted(history, key=lambda x: int(x.get('visit_count', 0)), reverse=True)[:10]
                                report_lines.append(f"<h3>Top 10 Most Visited</h3>")
                                report_lines.append("<table><tr><th>URL</th><th>Title</th><th>Visit Count</th><th>Last Visit</th></tr>")
                                for item in top_visited:
                                    report_lines.append(f"<tr><td>{safe_get(item, 'url')}</td><td>{safe_get(item, 'title')}</td><td>{safe_get(item, 'visit_count')}</td><td>{safe_get(item, 'last_visit_time')}</td></tr>")
                                report_lines.append("</table>")
                            except Exception:
                                pass

                        # Logins
                        if inc_logins:
                            logins = browser_data.get('logins', [])
                            if logins:
                                report_lines.append(f"<h3>Logins ({len(logins)})</h3>")
                                report_lines.append("<table><tr><th>URL</th><th>Username</th><th>Password</th></tr>")
                                for item in logins:
                                    report_lines.append(f"<tr><td>{safe_get(item, 'origin')}</td><td>{safe_get(item, 'username')}</td><td>{safe_get(item, 'password')}</td></tr>")
                                report_lines.append("</table>")
                            
                        # Cookies
                        if inc_cookies:
                            cookies = browser_data.get('cookies', [])
                            if cookies:
                                report_lines.append(f"<h3>Cookies ({len(cookies)})</h3>")
                                report_lines.append("<table><tr><th>Host</th><th>Name</th><th>Value</th><th>Expires</th></tr>")
                                for item in cookies[:500]: 
                                    report_lines.append(f"<tr><td>{safe_get(item, 'host')}</td><td>{safe_get(item, 'name')}</td><td>{safe_get(item, 'value')}</td><td>{safe_get(item, 'expires')}</td></tr>")
                                report_lines.append("</table>")
                                if len(cookies) > 500:
                                    report_lines.append(f"<p><em>...and {len(cookies)-500} more cookies (truncated)</em></p>")

                        # Full History
                        if inc_history and history:
                            report_lines.append(f"<h3>Full History ({len(history)})</h3>")
                            report_lines.append("<table><tr><th>URL</th><th>Title</th><th>Last Visit</th><th>Count</th></tr>")
                            for item in history[:500]:
                                report_lines.append(f"<tr><td>{safe_get(item, 'url')}</td><td>{safe_get(item, 'title')}</td><td>{safe_get(item, 'last_visit_time')}</td><td>{safe_get(item, 'visit_count')}</td></tr>")
                            report_lines.append("</table>")
                            if len(history) > 500:
                                report_lines.append(f"<p><em>...and {len(history)-500} more history items (truncated)</em></p>")
                                
                        report_lines.append("</div>")
                        
                except Exception as e:
                    report_lines.append(f"<p class='encrypted'>Error processing {browser}: {html.escape(str(e))}</p>")

        report_lines.append("</body></html>")
        
        report_content = "\n".join(report_lines)
        report_file = os.path.join(DATA_DIR, "dumps", "forensic_report.html")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        return jsonify({
            "status": "success", 
            "file": "forensic_report.html",
            "path": report_file
        })
        
    except Exception as e:
        return jsonify({"status": "error", "log": str(e)})


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
