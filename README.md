# 🐱 Doraemon LOG · Live Control Room v4

Dashboard khấu hao LOG — theme Doraemon + **realtime Excel watch**.

## Cách chạy (khuyến nghị — LIVE)

```bash
cd %USERPROFILE%\Downloads\log-depreciation-dashboard
py -3 server.py
```

Mở: **http://127.0.0.1:8765**

### Realtime làm gì?

| Cách | Hành vi |
|------|---------|
| **Watch Excel** | Server theo dõi file `Bản Log chính thức*.xlsx` mỗi 2 giây — lưu Excel là web tự refresh chart |
| **Upload** | Kéo thả / chọn file `.xlsx` trên web → extract ngay |
| **Reload** | Nút 🔄 Force reload Excel |
| **Badge LIVE** | Chấm xanh nhấp nháy khi đang live |

## Mở tĩnh (không realtime)

Double-click `index.html` → mode STATIC (vẫn đủ chart, không auto-update).

## Tính năng

- KPI + Focus period, waterfall, heatmap, movers
- Compare 2 kỳ, favorites ⭐, status filter, night mode
- Global search, sort bảng, export CSV, copy summary
- Helper Doraemon + confetti + chuông

## Refresh / rebuild offline bundle

```bash
py -3 extract_data.py
py -3 build.py
```

## API (khi chạy server)

- `GET /api/data` — full dataset + version
- `GET /api/status` — mtime / source / version
- `GET /api/reload` — force re-extract
- `POST /api/upload` — upload Excel multipart

## Files

| File | Role |
|------|------|
| `server.py` | Live HTTP + Excel watcher |
| `extract_data.py` | Excel → JSON |
| `app.js` | Dashboard logic |
| `styles.css` | Doraemon UI |
| `index.html` | Shell + embedded snapshot |
| `data.json` | Latest extract |
