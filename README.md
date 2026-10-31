# Vietnamese Long Audio TTS

API tạo MP3 từ văn bản tiếng Việt dài, dùng Edge-TTS. Có chia đoạn, theo dõi tiến độ và tải file MP3.

## API
- `GET /health`: kiểm tra dịch vụ.
- `POST /v1/jobs`: tạo tác vụ, trả về `job_id`.
- `GET /v1/jobs/{job_id}`: xem trạng thái.
- `GET /v1/jobs/{job_id}/audio`: tải MP3 khi hoàn tất.

Mọi endpoint `/v1` yêu cầu header `X-API-Key`.

### Tạo tác vụ
```bash
curl -X POST "$TTS_URL/v1/jobs" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $TTS_API_KEY" \
  -d '{"text":"Nội dung truyện cần đọc","voice":"Nam Minh","rate":1.0}'
```

API trả về `job_id`. Poll `status_url` đến khi `status` là `completed`, sau đó tải từ `audio_url`.

Giọng hỗ trợ: `Nam Minh`, `Hoài My`. Tốc độ: 0.5–2.0. Văn bản tối đa 1.000.000 ký tự mỗi job.

## Chạy local
```bash
python -m pip install -r requirements.txt
# PowerShell:
$env:TTS_API_KEY = "your-secret-key"
uvicorn api:app --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000/docs` để thử API.

## Triển khai cloud
Repo có `render.yaml` để tạo Web Service trên Render. Kết nối repo, deploy, rồi lấy giá trị `TTS_API_KEY` trong Environment. Gói lưu trữ tạm ở `/tmp`; job và MP3 có thể mất khi instance khởi động lại hoặc bị thay thế. Đây là bản nền tảng; production nên bổ sung Redis/queue và object storage bền vững.

## Lưu ý quyền riêng tư
Repo đang Public. Không commit truyện, API key hay file MP3 vào Git. Khi gửi nội dung tới dịch vụ cloud, nội dung được xử lý trên máy chủ triển khai.
