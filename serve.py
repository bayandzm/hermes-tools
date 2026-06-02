#!/usr/bin/env python3
"""
Hermes Hub — Unified Project Monitor
Simple HTTP server using Python stdlib (no deps required)
"""

import json
import subprocess
import http.server
import socketserver
import urllib.parse
import time
import os
from pathlib import Path

PORT = 3000
BASE_DIR = Path(__file__).parent

def wsl(cmd):
    """Run command in WSL2 Ubuntu and return output"""
    try:
        r = subprocess.run(
            ["wsl", "-d", "Ubuntu", "-e", "bash", "-c", cmd],
            capture_output=True, text=True, timeout=30
        )
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", -1
    except FileNotFoundError:
        return "WSL not available", -1

def check_project(name, port, check_cmd, restart_cmd=""):
    """Check if a project is running"""
    out, code = wsl(check_cmd)
    is_running = code == 0 and "RUNNING" in out

    status_data = {
        "name": name,
        "port": port,
        "running": is_running,
        "detail": out[:200] if out else "",
        "restart_cmd": restart_cmd,
        "checked_at": time.strftime("%H:%M:%S"),
    }

    # Try to fetch from API if available
    if port and is_running:
        api_data = {}
        for endpoint in ["/api/summary", "/api/status", "/health"]:
            try:
                r = subprocess.run(
                    ["wsl", "-d", "Ubuntu", "-e", "bash", "-c",
                     f"curl -sf http://localhost:{port}{endpoint} 2>/dev/null || true"],
                    capture_output=True, text=True, timeout=10
                )
                if r.stdout.strip():
                    try:
                        api_data[endpoint] = json.loads(r.stdout)
                    except json.JSONDecodeError:
                        api_data[endpoint] = r.stdout[:200]
            except:
                pass
        if api_data:
            status_data["api"] = api_data

    return status_data

def get_all_status():
    """Get status for all projects"""
    projects = [
        {
            "name": "Microstock Factory",
            "port": None,
            "check": "ls -t ~/microstock-factory/*report*.json 2>/dev/null | head -1 && echo '---FOUND---' || echo 'NOT FOUND'",
            "restart": ""
        },
        {
            "name": "Charon (Trench Agent)",
            "port": 5151,
            "check": "curl -sf http://localhost:5151/api/summary >/dev/null 2>&1 && echo 'RUNNING' || echo 'DOWN'",
            "restart": "cd ~/charon && node dashboard.js &"
        },
        {
            "name": "Gengar PolyBot",
            "port": 5154,
            "check": "ss -tlnp | grep -q :5154 && echo 'RUNNING' || echo 'DOWN'",
            "restart": ""
        },
        {
            "name": "Meridian Bot",
            "port": 5150,
            "check": "curl -sf http://localhost:5150/api/status >/dev/null 2>&1 && echo 'RUNNING' || echo 'DOWN'",
            "restart": "cd ~/meridian && node server.js &"
        },
        {
            "name": "GeoForge",
            "port": 5050,
            "check": "curl -sf http://localhost:5050/ >/dev/null 2>&1 && echo 'RUNNING' || echo 'DOWN'",
            "restart": "cd ~/GeoForge && python app.py &"
        },
        {
            "name": "PRL Miner",
            "port": None,
            "check": "pgrep -a pearl-miner-v8 2>/dev/null && echo '---RUNNING---' || echo 'NOT RUNNING'",
            "restart": "cd ~/pearl && screen -dmS prl ./pearl-miner-v8 --host 84.32.220.219:9000 --user prl1p06w50e0h0hqrx6rnkumgzyank5ym5asdu7u9qdewgdswdeves0as5nda9e"
        },
    ]

    results = {}
    for p in projects:
        results[p["name"]] = check_project(p["name"], p["port"], p["check"], p["restart"])
    return results

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = get_all_status()
            self.wfile.write(json.dumps(data, indent=2).encode())
            return

        if parsed.path == "/api/restart":
            params = urllib.parse.parse_qs(parsed.query)
            project = params.get("project", [""])[0]
            results = get_all_status()
            if project in results:
                restart_cmd = results[project].get("restart_cmd", "")
                if restart_cmd:
                    out, code = wsl(restart_cmd)
                    result = {"success": code == 0, "output": out[:200]}
                else:
                    result = {"success": False, "error": "No restart command configured"}
            else:
                result = {"success": False, "error": f"Unknown project: {project}"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            return

        # Serve static files
        return super().do_GET()

    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]} {args[1]} {args[2]}")

if __name__ == "__main__":
    os.chdir(BASE_DIR / "static")
    print(f"🚀 Hermes Hub running at http://localhost:{PORT}")
    print(f"   API: http://localhost:{PORT}/api/status")
    print(f"   Press Ctrl+C to stop")
    with socketserver.TCPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Stopped.")
