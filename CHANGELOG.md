# BleBig 0.3.1

- UNDO/REDO khôi phục ảnh trước/sau mỗi lần tràn thành công, không thay đổi thông số.
- Sau UNDO, lần tràn mới dùng đúng ảnh đang được khôi phục và bỏ nhánh REDO cũ.
- Hỗ trợ hoàn tác cả lượt xử lý nhiều ảnh.
- Chọn bộ ảnh mới bắt đầu lịch sử mới; không cho thao tác lịch sử khi đang xử lý.
- Không tự mở thư mục đầu ra sau khi hoàn thành.
- File đã xuất vẫn được giữ trên ổ đĩa; UNDO không xóa chúng. Lịch sử chỉ tồn tại trong phiên đang mở.

## Đưa bản mới lên GitHub

Giải nén gói nguồn, upload các file thay đổi vào đúng đường dẫn:

- blebig/app.py
- blebig/__init__.py
- installer/BleBig.iss
- CHANGELOG.md

Commit xong, chạy workflow trên main để kiểm thử bộ cài. Khi đã thử thành công,
tạo Release với tag v0.3.1 trên main. Workflow gắn với tag sẽ tạo và đính kèm
BleBig-Setup.exe cùng BleBig-Update-v0.3.1.zip. Chỉ sau khi ZIP update được đính
kèm, ứng dụng ở máy người dùng mới có gói để tải tự động.
