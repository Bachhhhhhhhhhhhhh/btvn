# -*- coding: utf-8 -*-
"""
LOG Depreciation Live Server
----------------------------
  py -3 server.py
  → http://127.0.0.1:8765

Watches Excel for changes, re-extracts, serves UI + JSON API.
"""
from __future__ import annotations

import json
import mimetypes
import threading
import time
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from extract_data import extract_from_path, find_xlsx

ROOT = Path(__file__).resolve().parent
HOST, PORT = "127.0.0.1", 8765
POLL_SEC = 2.0
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

_lock = threading.Lock()
_state = {
    "data": None,
    "error": None,
    "xlsx": None,
    "version": 0,
    "last_extract": None,
}


def _set_data(data, xlsx: Path | None = None):
    data = dict(data)
    data.setdefault("meta", {})
    data["meta"]["live"] = True
    data["meta"]["server"] = True
    data["meta"]["pollSec"] = POLL_SEC
    with _lock:
        _state["data"] = data
        if xlsx:
            _state["xlsx"] = str(xlsx)
        _state["error"] = None
        _state["version"] += 1
        _state["last_extract"] = time.time()
        ver = _state["version"]
    (ROOT / "data.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
    return ver


def refresh(xlsx: Path, force: bool = False) -> bool:
    xlsx = Path(xlsx)
    if not xlsx.exists():
        return False
    with _lock:
        cur = _state.get("xlsx")
        prev_mtime = (_state.get("data") or {}).get("meta", {}).get("fileMtime")
        if (
            not force
            and cur
            and Path(cur) == xlsx
            and prev_mtime is not None
            and abs(xlsx.stat().st_mtime - prev_mtime) < 0.05
        ):
            return False
    try:
        data = extract_from_path(xlsx)
        ver = _set_data(data, xlsx)
        print(f"[live] v{ver} ← {xlsx.name} @ {data['meta'].get('fileMtimeIso')}")
        return True
    except Exception as e:
        with _lock:
            _state["error"] = str(e)
        print("[live] ERROR:", e)
        traceback.print_exc()
        return False


def pick_source() -> Path | None:
    uploads = sorted(
        UPLOAD_DIR.glob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    found = find_xlsx()
    candidates = [p for p in uploads + ([found] if found else []) if p and p.exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def load_initial():
    xlsx = pick_source()
    if xlsx:
        refresh(xlsx, force=True)
        return
    cached = ROOT / "data.json"
    if cached.exists():
        data = json.loads(cached.read_text(encoding="utf-8"))
        _set_data(data)
        print("[live] using cached data.json")
        return
    raise SystemExit("No Excel file and no data.json found.")


def watcher():
    while True:
        try:
            xlsx = pick_source()
            if xlsx:
                refresh(xlsx, force=False)
        except Exception as e:
            print("[watch]", e)
        time.sleep(POLL_SEC)


def json_response(handler: BaseHTTPRequestHandler, obj, code=200):
    raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


class Handler(BaseHTTPRequestHandler):
    server_version = "DoraLive/4"

    def log_message(self, fmt, *args):
        print("[http]", fmt % args)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path in ("/api/data", "/api/data.json"):
            with _lock:
                payload = {
                    "ok": _state["data"] is not None,
                    "version": _state["version"],
                    "error": _state["error"],
                    "data": _state["data"],
                    "serverTime": time.time(),
                }
            json_response(self, payload)
            return

        if path == "/api/status":
            with _lock:
                meta = (_state["data"] or {}).get("meta", {})
                payload = {
                    "ok": True,
                    "version": _state["version"],
                    "error": _state["error"],
                    "xlsx": _state["xlsx"],
                    "lastExtract": _state["last_extract"],
                    "fileMtime": meta.get("fileMtime"),
                    "fileMtimeIso": meta.get("fileMtimeIso"),
                    "source": meta.get("source"),
                    "pollSec": POLL_SEC,
                    "assetCount": (_state["data"] or {}).get("kpi", {}).get("assetCount"),
                }
            json_response(self, payload)
            return

        if path == "/api/reload":
            xlsx = pick_source()
            ok = refresh(xlsx, force=True) if xlsx else False
            with _lock:
                json_response(
                    self,
                    {"ok": ok, "version": _state["version"], "error": _state["error"]},
                    200 if ok else 500,
                )
            return

        # static
        rel = urllib.parse.unquote(path.lstrip("/") or "index.html")
        if ".." in rel.replace("\\", "/").split("/"):
            self.send_error(400)
            return
        fp = (ROOT / rel).resolve()
        if not str(fp).startswith(str(ROOT)) or not fp.is_file():
            self.send_error(404)
            return
        raw = fp.read_bytes()
        ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path != "/api/upload":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        ctype = self.headers.get("Content-Type", "")
        filename = "upload.xlsx"
        content = body

        if "multipart/form-data" in ctype and "boundary=" in ctype:
            boundary = ctype.split("boundary=")[-1].strip().encode()
            for part in body.split(b"--" + boundary):
                if b"filename=" not in part:
                    continue
                head, _, filebody = part.partition(b"\r\n\r\n")
                filebody = filebody.rstrip(b"\r\n--").rstrip(b"\r\n")
                for line in head.split(b"\r\n"):
                    if b"filename=" in line:
                        raw_name = line.decode(errors="ignore").split("filename=")[-1]
                        filename = raw_name.strip().strip('"') or filename
                content = filebody
                break

        name = Path(filename).name
        if not name.lower().endswith((".xlsx", ".xlsm")):
            name += ".xlsx"
        dest = UPLOAD_DIR / f"{int(time.time())}_{name}"
        dest.write_bytes(content)
        ok = refresh(dest, force=True)
        with _lock:
            json_response(
                self,
                {
                    "ok": ok,
                    "version": _state["version"],
                    "source": dest.name,
                    "error": _state["error"],
                },
                200 if ok else 500,
            )


def main():
    print()
    print("  ========================================")
    print("   Doraemon LOG  ·  Live Dashboard")
    print("  ========================================")
    load_initial()
    threading.Thread(target=watcher, daemon=True).start()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"   URL     : {url}")
    print(f"   Watch   : every {POLL_SEC:.0f}s")
    print(f"   Upload  : {url}api/upload")
    print("   Stop    : Ctrl+C")
    print("  ========================================")
    print()
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
