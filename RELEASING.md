# Phát hành BleBig

## Chuẩn bị

- Repository GitHub phải ở chế độ Public để máy người dùng kiểm tra update không cần token.
- Actions có quyền `Read and write permissions`.
- Sửa `blebig/__init__.py` và `installer/BleBig.iss` thành cùng một số phiên bản.
- Ghi thay đổi của phiên bản vào commit/tag hoặc phần ghi chú Release.

## Tạo bản phát hành

```powershell
git add .
git commit -m "Release BleBig 0.3.0"
git tag v0.3.0
git push origin main --tags
```

Workflow `.github/workflows/build-windows.yml` tự:

1. cấu hình địa chỉ repository cho kênh cập nhật;
2. chạy smoke test;
3. đóng gói ứng dụng và updater;
4. tạo bộ cài một tệp EXE;
5. tạo ZIP cập nhật có manifest và SHA-256 cho từng file;
6. đăng cả hai tệp lên GitHub Release.

Không đổi tên gói cập nhật: ứng dụng tìm mẫu `BleBig-Update-v*.zip`.

## Kiểm thử trước khi công bố

- Cài `BleBig-Setup.exe` trên Windows 10/11 bằng tài khoản thường.
- Mở ảnh và thử A4 dọc, tràn trong 0.3 cm, khu vực giữa/trái.
- Xác nhận mở lại ứng dụng hiển thị bản mới hơn và nút **Để sau** không tải file.
- Xác nhận **Cập nhật ngay** tải ZIP, tự mở updater, khởi động lại và xóa ZIP.
- Kiểm tra `%LOCALAPPDATA%\BleBig\logs\blebig.log` nếu có lỗi.
