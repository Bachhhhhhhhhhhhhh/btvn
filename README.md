# 🐱 Doraemon LOG · Live Control Room

Dashboard khấu hao LOG — theme Doraemon, UI gọn, **realtime Excel watch**.

## Cách chạy (khuyến nghị — LIVE)

```bat
cd %USERPROFILE%\Downloads\log-depreciation-dashboard
start.bat
```

Hoặc:

```bat
py -3 server.py
```

Mở: **http://127.0.0.1:8765**

> Double-click `index.html` chỉ mở mode **STATIC** (đủ chart, không auto-update).

### Realtime

| Cách | Hành vi |
|------|---------|
| **Watch Excel** | Server theo dõi `Bản Log chính thức*.xlsx` mỗi 2s — Save Excel là web tự refresh |
| **Upload** | Kéo thả / chọn `.xlsx` trên web → extract ngay |
| **Reload** | Nút 🔄 Force re-extract |
| **Badge LIVE** | Chấm xanh nhấp nháy khi đang live |

## Tính năng

- KPI + Focus period, waterfall, heatmap, movers
- Compare 2 kỳ, favorites ⭐, status filter, night mode (lưu máy)
- Global search, sort bảng, export CSV (UTF-8 BOM), copy summary
- Mobile menu, scroll-spy nav, print stylesheet
- Helper Doraemon + party confetti (nút Party)

## Rebuild offline bundle

```bat
py -3 extract_data.py
py -3 build.py
```

## API (khi chạy server)

| Endpoint | Mô tả |
|----------|--------|
| `GET /api/data` | Full dataset + version |
| `GET /api/status` | mtime / source / version |
| `GET /api/reload` | Force re-extract |
| `POST /api/upload` | Upload Excel (multipart) |

## Files

| File | Role |
|------|------|
| `server.py` | Live HTTP + Excel watcher |
| `extract_data.py` | Excel → JSON |
| `app.js` | Dashboard logic |
| `styles.css` | Doraemon UI |
| `build.py` | Embed snapshot → `index.html` |
| `index.html` | Shell + embedded data |
| `data.json` | Latest extract |
| `start.bat` | One-click LIVE |
