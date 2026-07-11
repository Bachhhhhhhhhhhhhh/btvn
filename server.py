# -*- coding: utf-8 -*-
"""
Live server for Doraemon LOG dashboard.
- Watches Excel file for changes and re-extracts automatically
- Serves static UI + /api/data for realtime updates
- Accepts Excel upload at /api/upload

Run:
  py -3 server.py
  open http://127.0.0.1:8765
"""
from __future__ import annotations

import json
import mimetypes
import threading
import time
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from extract_data import CANDIDATES, DOWNLOADS, extract_and_save, extract_from_path, find_xlsx

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8765
POLL_SEC = 2.0
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

_state = {
    "data": None,
    "error": None,
    "xlsx": None,
    "version": 0,
    "last_extract": None,
    "lock": threading.Lock(),
}


def load_initial():
    xlsx = find_xlsx()
    # prefer uploaded if newer
    uploads = sorted(UPLOAD_DIR.glob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if uploads and (not xlsx or uploads[0].stat().st_mtime >= xlsx.stat().st_mtime):
        xlsx = uploads[0]
    if not xlsx:
        # fallback to existing data.json
        dj = ROOT / "data.json"
        if dj.exists():
            with _state["lock"]:
                _state["data"] = json.loads(dj.read_text(encoding="utf-8"))
                _state["data"]["meta"]["live"] = True
                _state["data"]["meta"]["server"] = True
                _state["version"] += 1
                _state["last_extract"] = time.time()
            print("Loaded cached data.json (no Excel found)")
            return
        raise FileNotFoundError("No Excel and no data.json")
    refresh(xlsx, force=True)


def refresh(xlsx: Path, force: bool = False):
    xlsx = Path(xlsx)
    with _state["lock"]:
        cur = _state.get("xlsx")
        if (
            not force
            and cur
            and Path(cur) == xlsx
            and _state["data"]
            and abs(xlsx.stat().st_mtime - (_state["data"]["meta"].get("fileMtime") or 0)) < 0.01
        ):
            return False
    try:
        data = extract_from_path(xlsx)
        data["meta"]["live"] = True
        data["meta"]["server"] = True
        data["meta"]["pollSec"] = POLL_SEC
        (ROOT / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        with _state["lock"]:
            _state["data"] = data
            _state["xlsx"] = str(xlsx)
            _state["error"] = None
            _state["version"] += 1
            _state["last_extract"] = time.time()
            ver = _state["version"]
        print(f"[live] extract v{ver} ← {xlsx.name} @ {data['meta']['fileMtimeIso']}")
        return True
    except Exception as e:
        with _state["lock"]:
            _state["error"] = str(e)
        print("[live] extract error:", e)
        traceback.print_exc()
        return False


def watcher():
    while True:
        try:
            xlsx = None
            with _state["lock"]:
                if _state["xlsx"]:
                    xlsx = Path(_state["xlsx"])
            if not xlsx or not xlsx.exists():
                xlsx = find_xlsx()
            # also check newest upload
            uploads = list(UPLOAD_DIR.glob("*.xlsx"))
            candidates = [p for p in ([xlsx] if xlsx else []) + uploads if p and p.exists()]
            if candidates:
                newest = max(candidates, key=lambda p: p.stat().st_mtime)
                refresh(newest, force=False)
        except Exception as e:
            print("[watch]", e)
        time.sleep(POLL_SEC)


class Handler(BaseHTTPRequestHandler):
    server_version = "DoraLive/1.0"

    def log_message(self, fmt, *args):
        print("[http]", self.address_string(), fmt % args)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/api/data", "/api/data.json"):
            with _state["lock"]:
                payload = {
                    "ok": True,
                    "version": _state["version"],
                    "error": _state["error"],
                    "data": _state["data"],
                    "serverTime": time.time(),
                }
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._cors()
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if path == "/api/status":
            with _state["lock"]:
                payload = {
                    "ok": True,
                    "version": _state["version"],
                    "error": _state["error"],
                    "xlsx": _state["xlsx"],
                    "lastExtract": _state["last_extract"],
                    "fileMtime": (_state["data"] or {}).get("meta", {}).get("fileMtime"),
                    "fileMtimeIso": (_state["data"] or {}).get("meta", {}).get("fileMtimeIso"),
                    "source": (_state["data"] or {}).get("meta", {}).get("source"),
                    "pollSec": POLL_SEC,
                }
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._cors()
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if path == "/api/reload":
            xlsx = find_xlsx(Path(_state["xlsx"]) if _state["xlsx"] else None)
            if xlsx:
                refresh(xlsx, force=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            with _state["lock"]:
                self.wfile.write(
                    json.dumps({"ok": True, "version": _state["version"]}).encode()
                )
            return

        # static files
        rel = path.lstrip("/") or "index.html"
        rel = urllib.parse.unquote(rel)
        if ".." in rel:
            self.send_error(400)
            return
        fp = (ROOT / rel).resolve()
        if not str(fp).startswith(str(ROOT)) or not fp.exists() or not fp.is_file():
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
        raw = fp.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self._cors()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/upload":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        ctype = self.headers.get("Content-Type", "")

        # multipart or raw xlsx
        filename = "upload.xlsx"
        content = body
        if "multipart/form-data" in ctype:
            # naive multipart parse for one file field
            boundary = ctype.split("boundary=")[-1].encode()
            parts = body.split(b"--" + boundary)
            for part in parts:
                if b"filename=" in part:
                    head, _, filebody = part.partition(b"\r\n\r\n")
                    filebody = filebody.rstrip(b"\r\n--")
                    for line in head.split(b"\r\n"):
                        if b"filename=" in line:
                            filename = line.decode(errors="ignore").split("filename=")[-1].strip().strip('"')
                    content = filebody
                    break
        if not filename.lower().endswith((".xlsx", ".xlsm")):
            filename += ".xlsx"
        # sanitize
        filename = Path(filename).name
        dest = UPLOAD_DIR / f"{int(time.time())}_{filename}"
        dest.write_bytes(content)
        ok = refresh(dest, force=True)
        payload = {
            "ok": ok,
            "version": _state["version"],
            "source": dest.name,
            "error": _state["error"],
        }
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200 if ok else 500)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def main():
    print("=" * 56)
    print("  Doraemon LOG · LIVE Dashboard Server")
    print("=" * 56)
    load_initial()
    t = threading.Thread(target=watcher, daemon=True)
    t.start()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"  Open: {url}")
    print(f"  Watching Excel every {POLL_SEC}s")
    print(f"  Upload: POST {url}api/upload")
    print("  Ctrl+C to stop")
    print("=" * 56)
    try:
        # open browser
        import webbrowser

        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()
