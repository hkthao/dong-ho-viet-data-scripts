import json
import sys
import requests
import os

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")

def extract_info_with_ollama(markdown_content: str, model_name: str):
    """
    Sends markdown content to Ollama for structured data extraction.
    """
    prompt = f"""Bạn là một chuyên gia phân tích dữ liệu gia phả. Nhiệm vụ của bạn là trích xuất thông tin từ nội dung Markdown được cung cấp về thông tin chung của gia phả.
Hãy trích xuất các thông tin sau và trả về dưới dạng JSON.

Các trường cần trích xuất:
1.  **name**: Tên của gia phả. (ví dụ: Gia Phả Họ Cao Minh Triết)
2.  **address**: Địa chỉ của gia phả.
3.  **description**: Mô tả tổng quan về gia phả.
4.  **generations_count**: Số đời từ thuỷ tổ tới con cháu.
5.  **family_count**: Số lượng gia đình.
6.  **member_count**: Số người.
7.  **manager_info**: Thông tin người quản lý gia phả này.

Nếu không tìm thấy thông tin, hãy sử dụng giá trị `null` hoặc một chuỗi rỗng phù hợp.

Nội dung Markdown:
---
{markdown_content}
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


def extract_giapha_info_ollama(markdown_file_path: str, output_json_file_path: str, model_name: str):
    if os.path.exists(output_json_file_path):
        print(f"Tệp JSON đầu ra '{output_json_file_path}' đã tồn tại. Bỏ qua trích xuất.", file=sys.stderr)
        return
        
    print(f"Trích xuất thông tin gia phả từ '{markdown_file_path}' bằng Ollama với model '{model_name}'...")
    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        extracted_data = extract_info_with_ollama(markdown_content, model_name)
        
        with open(output_json_file_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print(f"Thông tin đã được trích xuất và lưu vào '{output_json_file_path}'.")

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp Markdown tại '{markdown_file_path}'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Lỗi trong quá trình trích xuất thông tin gia phả bằng Ollama: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Cách dùng: python extract_giapha_info_ollama.py <input_markdown_file_path> <output_json_file_path> <ollama_model_name>")
        sys.exit(1)
    
    input_md_file = sys.argv[1]
    output_json_file = sys.argv[2]
    ollama_model = sys.argv[3]

    extract_giapha_info_ollama(input_md_file, output_json_file, ollama_model)
