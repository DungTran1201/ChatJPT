# UX Information Architecture & User Flows: Exam Management

## 1. Information Architecture (IA)
- Đường dẫn: `/exams` ("Kho Đề Thi & Tài Liệu").
- Cấu trúc trang:
  - **Header & Metrics**:
    - Tiêu đề: *Kho Đề Thi & Tài Liệu Tham Khảo (JLPT & Kaiwa Repository)*.
    - 4 Thẻ thống kê nhanh: Tổng số đề thi, Số đề theo Level N5..N1, Đề Kaiwa thực chiến, Tài liệu tham khảo chính thức.
  - **Tabs Navigation**:
    - `Tab 1: Kho Đề Thi (Exam Bank)`:
      - Bộ lọc cấp độ: `Tất Cả`, `N5`, `N4`, `N3`, `N2`, `N1`, `Kaiwa`.
      - Bộ lọc thể loại: `Tất Cả Thể Loại`, `Đề Thi Chuẩn JLPT`, `Luyện Nghe (Choukai)`, `Đọc Hiểu (Dokkai)`, `Từ Vựng & Ngữ Pháp`.
      - Thanh tìm kiếm theo tên đề hoặc năm.
      - Nút "Thêm Đề Thi Mới".
      - Lưới thẻ đề thi (Exam Cards): Cấp độ, Thời gian, Số câu hỏi, Link Drive, Nút "Thi Thử Trực Tuyến", Nút "Sửa".
    - `Tab 2: Tài Liệu Tham Khảo (Reference Materials)`:
      - Bộ sưu tập 6 thư mục Google Drive chính thức: N5, N4, N3, N2, N1, Kaiwa.
      - Thẻ Cẩm nang ngữ pháp Tae Kim's Japanese Grammar Guide.
      - Thẻ Kho từ điển & từ vựng tiếng Nhật.
      - Nút 1-chạm mở tài liệu Google Drive / Website.
      - Nút "Thêm Tài Liệu Mới".
  - **Modals**:
    - Modal Thi Thử Trực Tuyến (Online Exam Runner): Đồng hồ đếm ngược, danh sách câu hỏi trắc nghiệm, hiển thị Furigana, chấm điểm tự động và lời giải thích Sensei.
    - Modal Thêm/Sửa Đề Thi.
    - Modal Thêm Tài Liệu Tham Khảo.

---

## 2. User Flows (`UX-EXAM-01`, `UX-EXAM-02`)

### Flow 1: Khám phá đề thi và làm bài thi thử
```
[Sidebar: Kho Đề Thi] ──► Màn hình /exams (Tab Kho Đề Thi)
                                │
                                ├─► Chọn Filter cấp độ "N5"
                                ├─► Bấm "Mở Thư Mục Drive" ──► Mở Drive tab mới
                                └─► Bấm "Thi Thử Trực Tuyến"
                                          │
                                          ▼
                                [Modal Làm Bài Thi Thử]
                                (Làm trắc nghiệm + Countdown)
                                          │
                                          ▼
                                     [Nộp Bài]
                                          │
                                          ▼
                               [Bảng Kết Quả & Lời Giải Sensei]
```

### Flow 2: Khai thác kho tài liệu tham khảo
```
[Màn hình /exams] ──► Chuyển sang Tab "Tài Liệu Tham Khảo"
                              │
                              ├─► Chọn Thư mục Drive N1..N5 hoặc Kaiwa ──► Mở Google Drive
                              ├─► Chọn Tae Kim's Grammar Guide ──► Xem tóm tắt & Link
                              └─► Chọn Kho Từ Điển Tiếng Nhật ──► Xem kho từ vựng
```
