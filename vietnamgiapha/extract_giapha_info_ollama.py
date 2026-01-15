import json
import sys
import requests
import os

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")

def extract_info_with_ollama(html_content: str, model_name: str):
    """
    Sends HTML content to Ollama for structured data extraction according to schema-family.txt.
    """
    prompt = f"""Bạn là một chuyên gia phân tích dữ liệu gia phả. Nhiệm vụ của bạn là trích xuất thông tin từ nội dung HTML được cung cấp về thông tin chung của gia phả.
Hãy trích xuất các thông tin sau và trả về dưới dạng JSON, tuân thủ chính xác cấu trúc và các trường sau:

{{
  "name": "string", // Tên của gia đình (bắt buộc)
  "code": "string", // Mã gia đình (tùy chọn)
  "description": "string", // Mô tả gia đình (tùy chọn)
  "address": "string", // Địa chỉ gia đình (tùy chọn)
  "genealogyRecord": "string", // Ghi chép gia phả (tùy chọn)
  "progenitorName": "string", // Tên người khởi thủy (tùy chọn)
  "familyCovenant": "string", // Giao ước gia đình (tùy chọn)
  "contactInfo": "string", // Thông tin liên hệ (tùy chọn)
  "avatarBase64": "string", // Ảnh đại diện dạng Base64 (tùy chọn)
  "visibility": "Private", // Chế độ hiển thị (mặc định là "Private", có thể là "Public")
  "managerIds": [ // Danh sách ID người quản lý (kiểu GUID, tùy chọn)
    "00000000-0000-0000-0000-000000000000"
  ],
  "viewerIds": [ // Danh sách ID người xem (kiểu GUID, tùy chọn)
    "00000000-0000-0000-0000-000000000000"
  ],
  "locationId": "00000000-0000-0000-0000-000000000000" // ID địa điểm (kiểu GUID, tùy chọn)
}}

Nếu không tìm thấy thông tin cho một trường nào đó, hãy sử dụng giá trị `null` hoặc một chuỗi/mảng rỗng phù hợp với kiểu dữ liệu của trường đó.

Nội dung HTML:
---
{html_content}
---

Hãy trả về CHỈ JSON hợp lệ, không có bất kỳ văn bản bổ sung nào.
"""

    headers = {"Content-Type": "application/json"}
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(OLLAMA_API_URL, headers=headers, json=data)
        response.raise_for_status() # Raise an exception for HTTP errors
        
        result = response.json()
        generated_text = result.get("response", "").strip()
        
        # Ollama's format="json" sometimes wraps the JSON in markdown code block.
        if generated_text.startswith("```json") and generated_text.endswith("```"):
            generated_text = generated_text[len("```json"):-len("```")].strip()

        return json.loads(generated_text)

    except requests.exceptions.ConnectionError as e:
        print(f"Lỗi kết nối đến Ollama API tại {OLLAMA_API_URL}. Vui lòng đảm bảo Ollama đang chạy.", file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"Lỗi HTTP từ Ollama API: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Lỗi khi giải mã JSON từ phản hồi của Ollama: {e}", file=sys.stderr)
        print(f"Phản hồi nhận được:\n{generated_text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Lỗi không xác định khi gọi Ollama API: {e}", file=sys.stderr)
        sys.exit(1)


def extract_giapha_info_ollama(html_file_path: str, output_json_file_path: str, model_name: str):
    if os.path.exists(output_json_file_path):
        print(f"Tệp JSON đầu ra '{output_json_file_path}' đã tồn tại. Bỏ qua trích xuất.", file=sys.stderr)
        return
        
    print(f"Trích xuất thông tin gia phả từ '{html_file_path}' bằng Ollama với model '{model_name}'...")
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        extracted_data = extract_info_with_ollama(html_content, model_name)
        
        with open(output_json_file_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print(f"Thông tin đã được trích xuất và lưu vào '{output_json_file_path}'.")

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp HTML tại '{html_file_path}'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Lỗi trong quá trình trích xuất thông tin gia phả bằng Ollama: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Cách dùng: python extract_giapha_info_ollama.py <input_html_file_path> <output_json_file_path> <ollama_model_name>")
        sys.exit(1)
    
    input_html_file = sys.argv[1]
    output_json_file = sys.argv[2]
    ollama_model = sys.argv[3]

    extract_giapha_info_ollama(input_html_file, output_json_file, ollama_model)
