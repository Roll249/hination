# HINATION — Dự báo rủi ro thiên tai Điện Biên

HINATION tạo dự báo thời tiết theo giờ và đánh giá nguy cơ lũ, sạt lở, bão và cháy rừng cho 9 khu vực tại Điện Biên. Pipeline lấy dự báo GFS Seamless từ Open-Meteo, tạo chuỗi dự báo 168 giờ và tính mức cảnh báo dựa trên địa hình, lịch sử thiên tai cùng các ngưỡng VNDMS.

## Luồng pipeline

1. `model/hourly_pipeline.py` tải dữ liệu GFS 13 km cho 9 khu vực, các ô lân cận và 6 tỉnh lân cận.
2. Pipeline tạo `data/predictions/hourly_forecast.json` và `data/predictions/daily_summary.json`.
3. `model/disaster_model.py` đọc dự báo theo giờ, tính rủi ro thiên tai và tạo `data/predictions/disaster_forecast.json`.
4. `demo/disaster_dashboard.html` đọc các file dự báo trên để hiển thị dashboard.

## Cài đặt

Yêu cầu Python 3.10 trở lên.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Chạy pipeline đầy đủ

Chạy các lệnh từ thư mục gốc của repository:

```bash
python model/hourly_pipeline.py
python model/disaster_model.py
```

Pipeline cần kết nối Internet để gọi Open-Meteo. Sau khi chạy xong, các file JSON cần thiết cho dashboard sẽ được tạo trong `data/predictions/`.

Để xem dashboard, khởi động một HTTP server tại thư mục gốc rồi mở đường dẫn được in ra:

```bash
python -m http.server 8000
```

Truy cập `http://localhost:8000/demo/disaster_dashboard.html`.

## Tự động cập nhật mỗi giờ

```bash
bash run_hourly_scheduler.sh
```

Scheduler chạy pipeline GFS ngay khi khởi động, sau đó cập nhật dự báo thời tiết mỗi giờ. Khi cần làm mới cả lớp rủi ro thiên tai, chạy thêm:

```bash
python model/disaster_model.py
```

## Chính sách dữ liệu và model

Repository **không lưu hoặc phân phối dữ liệu train, dữ liệu tải về, dự báo được sinh ra hay checkpoint/trọng số model**. Toàn bộ các artifact này đã được khai báo trong `.gitignore` vì pipeline có thể tái tạo chúng.

Vì vậy:

- Không dùng `git add -f` để đưa `data/`, checkpoint hoặc trọng số model vào commit.
- `git clone` và `git pull` chỉ lấy source code cùng dữ liệu địa lý tĩnh trong `data/geo/`; Git không tải dữ liệu runtime hoặc dữ liệu train về máy.
- Sau khi clone, chạy pipeline đầy đủ để tạo dữ liệu cục bộ.
- `git pull` không ghi đè các artifact cục bộ đã bị ignore.
- `data/geo/dien_bien_boundary.geojson` vẫn được theo dõi vì đây là tài nguyên tĩnh mà dashboard cần để vẽ ranh giới.

Các nhóm bị ignore gồm:

- Mọi nội dung động dưới `data/`, ngoại trừ `data/geo/`.
- `model/checkpoints/` và các file `*.pt`, `*.pth`, `*.ckpt`, `*.onnx`.
- Các thư mục artifact phổ biến như `artifacts/`, `outputs/`, `runs/` và `wandb/`.

Lưu ý: `.gitignore` ngăn dữ liệu xuất hiện trong các commit mới và lần pull sau, nhưng không xóa blob đã tồn tại trong lịch sử Git. Nếu cần giảm kích thước toàn bộ lịch sử repository, phải thực hiện một lần dọn lịch sử riêng bằng `git filter-repo` và phối hợp với tất cả contributor.

## Cấu trúc chính

```text
.
├── data/
│   ├── geo/                         # Tài nguyên địa lý tĩnh, có theo dõi Git
│   └── predictions/                 # Kết quả pipeline, chỉ lưu local
├── demo/
│   └── disaster_dashboard.html
├── model/
│   ├── disaster_model.py
│   ├── hourly_pipeline.py
│   └── checkpoints/                 # Model artifacts, chỉ lưu local
├── requirements.txt
└── run_hourly_scheduler.sh
```

## Nguồn dữ liệu và phương pháp

- Dự báo thời tiết: NOAA GFS 13 km thông qua Open-Meteo.
- Thời hạn dự báo: 168 giờ, tương đương 7 ngày.
- Rủi ro: lũ, sạt lở, bão và cháy rừng.
- Ngữ cảnh địa lý: 9 khu vực tại Điện Biên, 4 ô lân cận cho mỗi khu vực và 6 tỉnh lân cận.

Kết quả chỉ phục vụ mục đích thử nghiệm/hackathon, không thay thế cảnh báo chính thức của cơ quan phòng chống thiên tai.
