# Hệ thống thu thập và trích xuất dữ liệu gia phả Việt Nam

## Mô tả
Dự án này là một tập hợp các script Python được thiết kế để tự động thu thập (crawl) dữ liệu gia phả từ website VietnamGiapha.com và trích xuất thông tin chi tiết về các thành viên gia đình và các nhánh gia phả. Dữ liệu thu thập được sẽ được làm sạch và lưu trữ để sử dụng trong các ứng dụng gia phả.

## Tính năng chính
*   **Thu thập dữ liệu gia phả**: Tự động truy cập và tải về các trang HTML chứa thông tin gia phả của từng gia đình và từng thành viên.
*   **Xử lý lỗi mạnh mẽ**: Xử lý các trường hợp trang HTML lỗi hoặc trống. Có cơ chế dự phòng để thu thập dữ liệu thành viên theo dải ID và tự động bỏ qua xử lý nếu gặp quá nhiều lỗi liên tiếp (100 lỗi) ở cả cấp độ family_id và thành viên.
*   **Làm sạch dữ liệu HTML**: Loại bỏ các thẻ và thuộc tính HTML không cần thiết, bao gồm các thẻ `<a>`, `<b>`, `<i>`, để có được dữ liệu sạch hơn cho việc trích xuất.
*   **Trích xuất thông tin**: Sử dụng các công cụ (ví dụ: Ollama) để trích xuất thông tin có cấu trúc từ các trang HTML đã thu thập, với hướng dẫn chi tiết cho LLM về các trường như "generation" và "order".
*   **Hỗ trợ chạy theo ID hoặc dải ID**: Cho phép người dùng chỉ định một ID gia đình cụ thể hoặc một dải ID gia đình để xử lý cho cả quá trình thu thập và trích xuất, kèm theo tùy chọn giới hạn số lượng thành viên cần trích xuất.

## Cấu trúc dự án
*   `apis/`: Mô tả các API liên quan đến Family Tree.
*   `output/`: Thư mục chứa dữ liệu HTML thô đã thu thập và dữ liệu đã trích xuất (JSON).
    *   `output/<family_id>/raw_html/`: HTML thô cho một family ID.
    *   `output/<family_id>/raw_html/members/`: HTML thô của các thành viên trong gia đình.
    *   `output/<family_id>/data/`: Dữ liệu JSON đã trích xuất.
*   `vietnamgiapha/`: Thư mục chứa các module chính của hệ thống.
    *   `vietnamgiapha/crawling/`: Chứa các script chuyên trách thu thập dữ liệu web.
        *   `crawl_giapha.py`: Thu thập các trang chính của gia phả.
        *   `crawl_member_details.py`: Thu thập chi tiết thành viên.
    *   `vietnamgiapha/extraction/`: Chứa các script trích xuất dữ liệu có cấu trúc từ HTML thô.
        *   `vietnamgiapha/extraction/rule_based/`: Trích xuất dữ liệu dựa trên quy tắc (BeautifulSoup, regex).
            *   `extract_family.py`: Trích xuất thông tin cấp gia đình.
            *   `extract_member.py`: Trích xuất thông tin chi tiết thành viên.
        *   `vietnamgiapha/extraction/llm_based/`: Trích xuất dữ liệu sử dụng mô hình ngôn ngữ lớn (Ollama).
            *   `extract_family_ollama.py`: Trích xuất thông tin gia phả bằng Ollama.
            *   `extract_member_ollama.py`: Trích xuất thông tin thành viên bằng Ollama.
    *   `vietnamgiapha/pipelines/`: Chứa các script điều phối các quy trình nhiều bước.
        *   `crawl_pipeline.py`: Quản lý quy trình thu thập dữ liệu HTML.
        *   `extract_pipeline.py`: Quản lý quy trình trích xuất thông tin từ HTML.
        *   `main_pipeline.py`: Điều phối toàn bộ quy trình (thu thập và trích xuất) cho một ID hoặc dải ID.
    *   `vietnamgiapha/api_integration/`: Chứa các script tương tác với API bên ngoài để tạo/cập nhật dữ liệu.
        *   `create_family_members.py`: Tạo gia đình và thành viên qua API.
    *   `vietnamgiapha/utils/`: Chứa các hàm tiện ích và trợ giúp dùng chung.
        *   `utils.py`: Các hàm tiện ích chung.
    *   `vietnamgiapha/config/`: Chứa các tệp cấu hình, schema và các tài nguyên khác.
        *   `requirements.txt`: Các thư viện Python cần thiết.
        *   `schema-family.txt`: Schema JSON cho dữ liệu gia đình.
        *   `schema-member.txt`: Schema JSON cho dữ liệu thành viên.
    *   `vietnamgiapha/data/samples/`: Chứa các tệp HTML mẫu dùng để kiểm thử và phát triển.
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
    python3 vietnamgiapha/pipelines/main_pipeline.py <family_id>
    # Ví dụ: python3 vietnamgiapha/main_pipeline.py 1714
    ```
*   **Cho một dải Family ID**:
    ```bash
    python3 vietnamgiapha/pipelines/main_pipeline.py <start_id> <end_id>
    # Ví dụ: python3 vietnamgiapha/main_pipeline.py 1 100
    ```

### 2. Chỉ chạy pipeline thu thập dữ liệu (crawling)
Sử dụng `crawl_pipeline.py` để chỉ thu thập dữ liệu HTML:

*   **Cho một Family ID cụ thể**:
    ```bash
    python3 vietnamgiapha/pipelines/crawl_pipeline.py <family_id>
    # Ví dụ: python3 vietnamgiapha/crawl_pipeline.py 1714
    ```
*   **Cho một dải Family ID**:
    ```bash
    python3 vietnamgiapha/pipelines/crawl_pipeline.py <start_id> <end_id>
    # Ví dụ: python3 vietnamgiapha/crawl_pipeline.py 1 12000
    ```

### 3.1. Chỉ chạy pipeline trích xuất dữ liệu (Rule-based Extraction - `extract_pipeline_rulebase.py`)
Sử dụng `extract_pipeline_rulebase.py` để chỉ trích xuất dữ liệu từ HTML đã thu thập:

*   **Cho một Family ID cụ thể**:
    ```bash
    PYTHONPATH=. python3 vietnamgiapha/pipelines/extract_pipeline_rulebase.py --output_base_dir output --family_id <family_id> [--force]
    # Ví dụ: PYTHONPATH=. python3 vietnamgiapha/pipelines/extract_pipeline_rulebase.py --output_base_dir output --family_id 1714 --force
    ```
*   **Cho một dải Family ID**:
    ```bash
    PYTHONPATH=. python3 vietnamgiapha/pipelines/extract_pipeline_rulebase.py --output_base_dir output --start_id <start_id> --end_id <end_id> [--force]
    # Ví dụ: PYTHONPATH=. python3 vietnamgiapha/pipelines/extract_pipeline_rulebase.py --output_base_dir output --start_id 1 --end_id 12000 --force
    ```
*   **Với giới hạn số lượng thư mục (chỉ áp dụng khi không dùng --family_id hoặc --start_id/--end_id)**:
    ```bash
    PYTHONPATH=. python3 vietnamgiapha/pipelines/extract_pipeline_rulebase.py --output_base_dir output --limit <số_lượng> [--force]
    # Ví dụ: PYTHONPATH=. python3 vietnamgiapha/pipelines/extract_pipeline_rulebase.py --output_base_dir output --limit 100 --force
    ```
*   **Xử lý tất cả thư mục gia đình**:
    ```bash
    PYTHONPATH=. python3 vietnamgiapha/pipelines/extract_pipeline_rulebase.py --output_base_dir output [--force]
    # Ví dụ: PYTHONPATH=. python3 vietnamgiapha/pipelines/extract_pipeline_rulebase.py --output_base_dir output --force
    ```

### 3.2. Chỉ chạy pipeline trích xuất dữ liệu (LLM-based Extraction - `extract_pipeline.py`)
Sử dụng `extract_pipeline.py` để chỉ trích xuất dữ liệu từ HTML đã thu thập (sử dụng các script trích xuất dựa trên LLM):

*   **Cho một Family ID cụ thể**:
    ```bash
    python3 vietnamgiapha/pipelines/extract_pipeline.py <family_id> [limit]
    # Ví dụ: python3 vietnamgiapha/pipelines/extract_pipeline.py 1714
    # Ví dụ với giới hạn 10 thành viên: python3 vietnamgiapha/pipelines/extract_pipeline.py 1714 10
    ```
*   **Cho một dải Family ID**:
    ```bash
    # Hiện tại không hỗ trợ trực tiếp dải ID thông qua script này.
    # Bạn cần lặp qua các ID bằng script bash/shell bên ngoài hoặc sửa đổi script.
    # Ví dụ: for i in {1..100}; do python3 vietnamgiapha/pipelines/extract_pipeline.py $i; done
    ```

## Đóng góp
Các đóng góp được hoan nghênh! Vui lòng tạo một pull request hoặc mở một issue.

## Giấy phép
[Ghi thông tin giấy phép tại đây nếu có]