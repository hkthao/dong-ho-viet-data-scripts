# Hệ thống thu thập và trích xuất dữ liệu gia phả Việt Nam

## Mô tả
Dự án này là một tập hợp các script Python được thiết kế để tự động thu thập (crawl) dữ liệu gia phả từ website VietnamGiapha.com và trích xuất thông tin chi tiết về các thành viên gia đình và các nhánh gia phả. Dữ liệu thu thập được sẽ được làm sạch và lưu trữ để sử dụng trong các ứng dụng gia phả.

## Tính năng chính
*   **Thu thập dữ liệu gia phả**: Tự động truy cập và tải về các trang HTML chứa thông tin gia phả của từng gia đình và từng thành viên.
*   **Xử lý lỗi mạnh mẽ**: Xử lý các trường hợp trang HTML lỗi hoặc trống, với cơ chế dự phòng để thu thập dữ liệu thành viên theo dải ID.
*   **Làm sạch dữ liệu HTML**: Loại bỏ các thẻ và thuộc tính HTML không cần thiết để có được dữ liệu sạch hơn cho việc trích xuất.
*   **Trích xuất thông tin**: Sử dụng các công cụ (ví dụ: Ollama) để trích xuất thông tin có cấu trúc từ các trang HTML đã thu thập.
*   **Hỗ trợ chạy theo ID hoặc dải ID**: Cho phép người dùng chỉ định một ID gia đình cụ thể hoặc một dải ID gia đình để xử lý.

## Cấu trúc dự án
*   `apis/`: Mô tả các API liên quan đến Family Tree.
*   `output/`: Thư mục chứa dữ liệu HTML thô đã thu thập và dữ liệu đã trích xuất (JSON).
    *   `output/<family_id>/raw_html/`: HTML thô cho một family ID.
    *   `output/<family_id>/raw_html/members/`: HTML thô của các thành viên trong gia đình.
    *   `output/<family_id>/data/`: Dữ liệu JSON đã trích xuất.
*   `vietnamgiapha/`: Chứa các script Python chính cho việc thu thập và trích xuất.
    *   `crawl_pipeline.py`: Quản lý quy trình thu thập dữ liệu HTML.
    *   `crawl_member_details.py`: Thu thập chi tiết thành viên.
    *   `crawl_giapha.py`: Thu thập các trang chính của gia phả.
    *   `extract_pipeline.py`: Quản lý quy trình trích xuất thông tin từ HTML.
    *   `extract_giapha_info_ollama.py`: Trích xuất thông tin gia phả bằng Ollama.
    *   `extract_member_info_ollama.py`: Trích xuất thông tin thành viên bằng Ollama.
    *   `main_pipeline.py`: Điều phối toàn bộ quy trình (thu thập và trích xuất) cho một ID hoặc dải ID.
    *   `utils.py`: Các hàm tiện ích.
*   `failed_crawls.txt`: Ghi lại các ID gia đình không thể thu thập được.

## Công nghệ sử dụng
*   **Python 3**: Ngôn ngữ lập trình chính.
*   **`aiohttp`**: Để thực hiện các yêu cầu HTTP không đồng bộ.
*   **`beautifulsoup4`**: Để phân tích cú pháp HTML và trích xuất dữ liệu.
*   **`Ollama`**: Để trích xuất thông tin có cấu trúc từ dữ liệu HTML (yêu cầu cài đặt và chạy Ollama với mô hình `llama3:8b`).

## Cài đặt
1.  **Clone repository**:
    ```bash
    git clone [URL_CUA_REPOSITORY]
    cd dong-ho-viet-data-scripts
    ```
2.  **Tạo và kích hoạt môi trường ảo (khuyến nghị)**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate # Trên Linux/macOS
    # venv\Scripts\activate # Trên Windows
    ```
3.  **Cài đặt các thư viện Python cần thiết**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Cài đặt và chạy Ollama**:
    *   Tải xuống và cài đặt Ollama từ [ollama.com](https://ollama.com/).
    *   Tải mô hình `llama3:8b` (hoặc mô hình tương thích khác):
        ```bash
        ollama pull llama3:8b
        ```
    *   Đảm bảo Ollama đang chạy trên hệ thống của bạn.

## Cách sử dụng

### 1. Chạy toàn bộ pipeline (thu thập và trích xuất)
Sử dụng `main_pipeline.py` để chạy cả hai giai đoạn:

*   **Cho một Family ID cụ thể**:
    ```bash
    python3 vietnamgiapha/main_pipeline.py <family_id>
    # Ví dụ: python3 vietnamgiapha/main_pipeline.py 1714
    ```
*   **Cho một dải Family ID**:
    ```bash
    python3 vietnamgiapha/main_pipeline.py <start_id> <end_id>
    # Ví dụ: python3 vietnamgiapha/main_pipeline.py 1 100
    ```

### 2. Chỉ chạy pipeline thu thập dữ liệu (crawling)
Sử dụng `crawl_pipeline.py` để chỉ thu thập dữ liệu HTML:

*   **Cho một Family ID cụ thể**:
    ```bash
    python3 vietnamgiapha/crawl_pipeline.py <family_id>
    # Ví dụ: python3 vietnamgiapha/crawl_pipeline.py 1714
    ```
*   **Cho một dải Family ID**:
    ```bash
    python3 vietnamgiapha/crawl_pipeline.py <start_id> <end_id>
    # Ví dụ: python3 vietnamgiapha/crawl_pipeline.py 1 12000
    ```

## Đóng góp
Các đóng góp được hoan nghênh! Vui lòng tạo một pull request hoặc mở một issue.

## Giấy phép
[Ghi thông tin giấy phép tại đây nếu có]