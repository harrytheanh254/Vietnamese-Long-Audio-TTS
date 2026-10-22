# Vietnamese-Long-Audio-TTS

Bộ tạo một file MP3 từ toàn bộ văn bản tiếng Việt bằng Edge-TTS, dùng trực tiếp hoặc qua GitHub Actions của ứng dụng SẢNH TRUYỆN.

## Chức năng

- Đọc toàn bộ file TXT UTF-8 và tạo ra một file MP3 duy nhất.
- Hỗ trợ giọng `Nam Minh` và `Hoài My`; tốc độ từ 0.5 đến 2.0.
- Thử lại theo số lần được chỉ định nếu dịch vụ TTS gặp lỗi.
- Workflow GitHub Actions nhận nội dung đã nén từ ứng dụng, chia theo ranh giới đoạn/câu (mục tiêu khoảng 3.000 ký tự mỗi phần), tạo tối đa 4 phần song song, rồi ghép thành một MP3 dưới artifact tên `AU <run_number>`. Ứng dụng vẫn chỉ tải về một file cuối.

## Dùng trong ứng dụng SẢNH TRUYỆN

Repository này cần được đặt ở chế độ **Private**. Trên máy Windows, cài GitHub CLI nếu chưa có, sau đó mở PowerShell và đăng nhập:

```powershell
winget install --id GitHub.cli -e
gh auth login
```

Nếu đã cài GitHub CLI, chỉ cần chạy `gh auth login`. Chọn đăng nhập GitHub.com và hoàn tất hướng dẫn trong trình duyệt. Tài khoản đăng nhập phải có quyền truy cập repository này và được phép chạy GitHub Actions.

Trong SẢNH TRUYỆN, dán nội dung truyện hoặc mở file TXT, chọn giọng đọc và tốc độ rồi nhấn **TẠO AUDIO**. Khi tác vụ thành công, ứng dụng tự tải MP3 về thư mục `D:\\NovelStudio\\data\\audio`.

## Chạy cục bộ

Cần Python 3.10 trở lên. Cài phụ thuộc và chạy:

```powershell
python -m pip install -r requirements.txt
python generate_audio.py --input .\\truyen.txt --output .\\output.mp3 --voice "Nam Minh" --rate 1.0 --attempts 1
```

## Bảo mật nội dung

- **Không commit hoặc tải file truyện riêng tư lên repository.** Không tạo commit chứa `kichban.txt`, bản dịch hay nội dung chương.
- Workflow chỉ chấp nhận xử lý khi repository là Private và không in nội dung truyện vào log.
- Ứng dụng gửi văn bản đã nén và mã hóa base64 trong dữ liệu kích hoạt workflow. Nén/base64 **không phải mã hóa bảo mật**; nội dung có thể được khôi phục bởi người có quyền xem dữ liệu lần chạy. Chỉ cấp quyền repository cho người mà bạn tin cậy.
- MP3 được lưu trong artifact riêng tư `AU <run_number>`, với thời hạn lưu 7 ngày; ứng dụng tự tải về máy sau khi tạo xong.
- Edge-TTS là dịch vụ trực tuyến và có thể lỗi hoặc bị giới hạn ở phía dịch vụ. Tạo nhiều phần cùng lúc có thể nhanh hơn, nhưng không bảo đảm nhanh hơn trong mọi lần; nếu dịch vụ giới hạn các yêu cầu đồng thời, một số phần có thể cần thử lại.
- Mỗi phần dùng một runner GitHub Actions riêng. Tăng mức song song có thể rút ngắn thời gian chờ nhưng tiêu thụ nhiều Actions minutes hơn tổng thời gian chạy song song; tài khoản Private có hạn mức phút dùng miễn phí tùy gói.

## Phụ thuộc

- `edge-tts==7.3.1`
- GitHub Actions: `actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`
