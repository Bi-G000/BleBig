# BleBig 0.3.0

BleBig là ứng dụng Windows tràn nền ảnh tự động, ưu tiên quy trình thiết kế và in ấn.

## Tính năng của bản MVP

- Mở ảnh PNG, JPG, JPEG, WEBP, TIFF.
- Đổi khung theo kích thước pixel hoặc tỉ lệ có sẵn.
- Tràn đều hoặc neo ảnh sang trái, phải, trên, dưới.
- Chế độ Nhanh chạy offline bằng OpenCV.
- Chế độ AI dùng LaMa; model tự tải trong lần chạy đầu tiên.
- Luôn ghép lại ảnh gốc sau khi sinh nền để vùng ảnh gốc không bị thay đổi.
- Nhật ký hoạt động và chẩn đoán cấu hình ngay trong ứng dụng.
- Xuất PNG/JPEG/TIFF, thiết lập DPI cho file in.
- Bộ cài Windows và trình gỡ cài đặt tiêu chuẩn.
- Giao diện xanh đen, icon và hiệu ứng mở ứng dụng mang nhận diện BleBig.
- Chọn nhiều ảnh và xử lý hàng loạt vào một thư mục đầu ra.
- Kích thước theo cm, DPI, khoảng tràn mặc định 0.3 cm.
- Hai chế độ: tràn ra ngoài khổ đã chọn hoặc tràn bên trong khổ đã chọn.
- Cập nhật tăng dần bằng ZIP trong thư mục `Update`, có xác thực SHA-256 và rollback.
- Tự kiểm tra GitHub Releases khi mở, cho phép **Cập nhật ngay** hoặc **Để sau**.

## Chạy mã nguồn

Yêu cầu Windows 10/11, Python 3.11 64-bit.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m blebig
```

## Tạo bộ cài

### Cách dễ nhất

1. Chọn **Extract All** để giải nén toàn bộ ZIP; không chạy trực tiếp bên trong ZIP.
2. Nhấp đúp `TAO_BO_CAI_BLEBIG.bat`.
3. Chọn **Yes** nếu Windows hỏi quyền quản trị.
4. Chờ cửa sổ báo `HOAN TAT`; lần đầu có thể mất 10–30 phút.
5. Mở thư mục `release` và nhấp đúp `BleBig-Setup.exe` để cài.

Máy cần kết nối Internet trong lần tạo bộ cài đầu tiên.

### Dùng PowerShell

Mở PowerShell tại thư mục dự án:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build_windows.ps1
```

Script tự tạo môi trường, cài thư viện, đóng gói ứng dụng và cài Inno Setup qua
`winget` nếu máy build chưa có. File kết quả nằm trong `release\BleBig-Setup.exe`.

Ngoài ra có thể đưa mã nguồn lên GitHub rồi chạy workflow **Build and Release BleBig**.
Người dùng cuối chỉ cần tải `BleBig-Setup.exe`; không cần Python hay mã nguồn.

## Phát hành qua GitHub

1. Tạo một repository **Public** trên GitHub và tải toàn bộ nội dung dự án này lên.
2. Vào **Settings → Actions → General → Workflow permissions**, chọn **Read and write permissions**.
3. Tạo tag theo đúng phiên bản rồi đẩy tag:

```powershell
git tag v0.3.0
git push origin v0.3.0
```

GitHub Actions sẽ tự tạo một Release gồm:

- `BleBig-Setup.exe`: tệp duy nhất dành cho cài mới.
- `BleBig-Update-v0.3.0.zip`: gói cập nhật tăng dần mà ứng dụng tự tải.

Workflow tự ghi tên repository vào ứng dụng khi build. Không sửa thủ công
`assets/update-channel.json`. Repository cần để Public để ứng dụng kiểm tra bản phát
hành mà không phải lưu token GitHub trên máy người dùng.

## Dữ liệu và log

- Log: `%LOCALAPPDATA%\BleBig\logs\blebig.log`
- Model: `%LOCALAPPDATA%\BleBig\models`
- Cấu hình: `%LOCALAPPDATA%\BleBig\config.json`

Gỡ BleBig trong **Settings > Apps > Installed apps**. Có thể chọn xóa cả model,
cấu hình và log khi gỡ.

## Cập nhật tăng dần

Chép gói `BleBig-Update-x.y.z.zip` vào thư mục `Update` cạnh `BleBig.exe`, sau đó
mở BleBig. Ứng dụng hiển thị phiên bản và danh sách thay đổi, tự cập nhật, tự mở
lại và xóa ZIP sau khi thành công. Gói sai manifest hoặc SHA-256 bị đổi đuôi
`.rejected`; khi sao chép lỗi, updater tự phục hồi file cũ.

Khi có Internet, BleBig cũng tự kiểm tra bản Release mới trên GitHub sau khi giao
diện đã mở. Người dùng có thể cập nhật ngay hoặc để lần sau. Việc tải diễn ra nền;
gói được kiểm tra trước khi chạy updater, tự xóa sau khi thành công và ứng dụng tự
mở lại. Nếu mất mạng, BleBig vẫn hoạt động bình thường.

## Cài đặt trên máy người dùng

Người dùng chỉ cần nhấp đúp `BleBig-Setup.exe`. Bộ cài hoạt động theo
tài khoản Windows, không yêu cầu quyền quản trị, tự cài vào
`%LOCALAPPDATA%\Programs\BleBig`, tạo shortcut và ẩn cửa sổ trong giai đoạn sao
chép. Không có file phụ nào được tạo cạnh tệp Setup đã tải. Khi cài đè, file hiện
có được Inno Setup so sánh và chỉ thay thế khi cần.

## Ghi chú

Chế độ AI cần Internet ở lần tải model đầu tiên. Chế độ Nhanh không cần mạng.
Ảnh rất lớn được thu nhỏ riêng cho bước AI, sau đó ảnh gốc được ghép trả lại để
không mất nét vùng nội dung ban đầu.
