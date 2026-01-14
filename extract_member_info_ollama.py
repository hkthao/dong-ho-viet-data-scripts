import json
import sys
import requests
import os

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b") # Default model, can be overridden

def extract_info_with_ollama(markdown_content: str):
    """
    Sends markdown content to Ollama for structured data extraction.
    """
    prompt = f"""Bạn là một chuyên gia phân tích dữ liệu gia phả. Nhiệm vụ của bạn là trích xuất thông tin từ nội dung Markdown được cung cấp về một thành viên gia đình và các mối quan hệ của họ.
Hãy trích xuất các thông tin sau và trả về dưới dạng JSON.

Các trường cần trích xuất:
1.  **main_person**: Thông tin của người chính trong bài viết.
    *   `name`: Tên của người.
    *   `gender`: Giới tính ("Nam", "Nữ", hoặc "Không rõ").
    *   `nickname`: Tên thường gọi.
    *   `alias`: Tên Tự.
    *   `child_order`: Là con thứ mấy.
    *   `dob`: Ngày sinh (định dạng YYYY-MM-DD nếu có ngày tháng đầy đủ, hoặc YYYY-01-01 nếu chỉ có năm).
    *   `dod`: Ngày mất (định dạng YYYY-MM-DD nếu có ngày tháng đầy đủ, hoặc YYYY-01-01 nếu chỉ có năm).
    *   `age_at_death`: Hưởng thọ.
    *   `posthumous_name`: Thụy hiệu.
    *   `burial_place`: Nơi an táng.
    *   `description`: Sự nghiệp, công đức, ghi chú.
    *   `generation`: Đời thứ.
    *   `father_name`: Tên của người cha (từ "Là con của").
    *   `father_url`: URL của người cha (từ "Là con của").

2.  **spouses**: Một danh sách các đối tượng, mỗi đối tượng là thông tin về vợ/chồng của người chính.
    *   `name`: Tên vợ/chồng.
    *   `gender`: Giới tính ("Nam", "Nữ", hoặc "Không rõ").
    *   `dob`: Ngày sinh (định dạng YYYY-MM-DD nếu có ngày tháng đầy đủ, hoặc YYYY-01-01 nếu chỉ có năm).
    *   `dod`: Ngày mất (định dạng YYYY-MM-DD nếu có ngày tháng đầy đủ, hoặc YYYY-01-01 nếu chỉ có năm).
    *   `description`: Ghi chú về vợ/chồng.

Nếu không tìm thấy thông tin, hãy sử dụng giá trị `null` hoặc một chuỗi rỗng phù hợp.

Nội dung Markdown:
---
{markdown_content}
---

Hãy trả về CHỈ JSON hợp lệ, không có bất kỳ văn bản bổ sung nào.
"""

    headers = {"Content-Type": "application/json"}
    data = {
        "model": OLLAMA_MODEL,
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


def extract_member_info_ollama(markdown_file_path: str, output_json_file_path: str):
    if os.path.exists(output_json_file_path):
        print(f"Tệp JSON đầu ra '{output_json_file_path}' đã tồn tại. Bỏ qua trích xuất.", file=sys.stderr)
        return
    
    print(f"Trích xuất thông tin thành viên từ '{markdown_file_path}' bằng Ollama...")
    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        extracted_data = extract_info_with_ollama(markdown_content)
        
        with open(output_json_file_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print(f"Thông tin đã được trích xuất và lưu vào '{output_json_file_path}'.")

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp Markdown tại '{markdown_file_path}'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Lỗi trong quá trình trích xuất thông tin thành viên bằng Ollama: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Cách dùng: python extract_member_info_ollama.py <input_markdown_file_path> <output_json_file_path>")
        sys.exit(1)
    
    input_md_file = sys.argv[1]
    output_json_file = sys.argv[2]

    extract_member_info_ollama(input_md_file, output_json_file)
