# Bảo mật

Không đăng token, mật khẩu hoặc khóa riêng vào repository. BleBig chỉ đọc Release
công khai từ GitHub và không cần token trên máy người dùng. Gói update có manifest
và SHA-256 cho từng file; updater chặn đường dẫn thoát khỏi thư mục cài đặt và có
backup/rollback nếu sao chép thất bại.

Khi phát hiện lỗ hổng, hãy báo riêng cho chủ repository trước khi công khai.
