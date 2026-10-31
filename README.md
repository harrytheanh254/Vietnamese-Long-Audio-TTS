# Vietnamese Long Audio TTS

Tạo một file MP3 truyện tiếng Việt bằng **GitHub Actions** (không cần dựng API server).

## Cách chạy
1. Mở tab **Actions** của repository.
2. Chọn **Generate Vietnamese audiobook** → **Run workflow**.
3. Nhập nội dung, chọn giọng Nam Minh/Hoài My và tốc độ đọc.
4. Chờ workflow hoàn tất.
5. Mở phần **Artifacts** của lần chạy và tải `audiobook-<run_id>` (bên trong là `audiobook.mp3`).

## Cơ chế
- Tự chia truyện theo ranh giới đoạn/câu, mỗi đoạn khoảng 2.800 ký tự.
- Chạy tối đa **4 đoạn đồng thời**.
- Đợi tất cả đoạn hoàn tất; nếu một đoạn lỗi sau 3 lần thử thì workflow báo thất bại.
- Ghép các MP3 theo đúng thứ tự ban đầu thành một file.
- Artifact được lưu 3 ngày.

## Giới hạn hiện tại
GitHub `workflow_dispatch` giới hạn tổng dữ liệu đầu vào; workflow này đặt giới hạn an toàn 60.000 ký tự cho nội dung truyện. Bản nhận truyện dài hơn cần cơ chế chuyển file riêng thay vì nhét toàn bộ văn bản vào input.

## Chạy local để kiểm thử
```bash
python -m pip install -r requirements.txt
$env:STORY_TEXT = "Nội dung truyện"
$env:STORY_VOICE = "Nam Minh"
$env:STORY_RATE = "1.0"
python run_workflow.py
```

Không commit truyện hoặc MP3 vào repository.
