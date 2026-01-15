import json
import sys
import requests
import os

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b") # Default model, can be overridden

def extract_info_with_ollama(html_content: str, family_id: str, member_id: str):
    """
    Sends HTML content to Ollama for structured data extraction according to schema-member.txt.
    """
    prompt = f"""Bạn là một chuyên gia phân tích dữ liệu gia phả. Nhiệm vụ của bạn là trích xuất thông tin từ nội dung HTML được cung cấp về một thành viên gia đình.
Hãy trích xuất các thông tin sau và trả về dưới dạng JSON, tuân thủ chính xác cấu trúc và các trường sau. Đối với trường "code", hãy định dạng nó theo mẫu "GPVN-M-{family_id}-{member_id}".

{{
  "lastName": "string", // Tên (ví dụ: Triết)
  "firstName": "string", // Tên đệm và tên (ví dụ: Minh)
  "code": "GPVN-M-{family_id}-{member_id}", // Mã thành viên, định dạng: GPVN-M-<family_id>-<member_id>
  "nickname": "string", // Tên thường gọi (Lý Triết)
  "dateOfBirth": "YYYY-MM-DDTHH:mm:ssZ", // Ngày sinh, định dạng ISO 8601. Nếu chỉ có năm, dùng YYYY-01-01T00:00:00Z.
  "dateOfDeath": "YYYY-MM-DDTHH:mm:ssZ", // Ngày mất, định dạng ISO 8601. Nếu chỉ có năm, dùng YYYY-01-01T00:00:00Z.
  "placeOfBirth": "string", // Nơi sinh
  "placeOfDeath": "string", // Nơi mất
  "phone": "string", // Điện thoại
  "email": "string", // Email
  "address": "string", // Địa chỉ
  "gender": "string", // Giới tính ("Nam", "Nữ", hoặc "Không rõ")
  "avatarUrl": "string", // URL ảnh đại diện
  "avatarBase64": "string", // Ảnh đại diện Base64
  "occupation": "string", // Nghề nghiệp
  "biography": "string", // Tiểu sử (Sự nghiệp, công đức, ghi chú)
  "isRoot": "boolean", // Có phải thủy tổ không (true/false)
  "isDeceased": "boolean", // Đã mất (true/false)
  "order": "integer", // Thứ tự con (ví dụ: 1)
  "generation": "integer", // Đời thứ (ví dụ: 0, 1, 2,...)
  "father": {{ // Thông tin cha, null nếu không có
    "lastName": "string",
    "firstName": "string",
    "code": "string",
    "gender": "string"
  }},
  "mother": {{ // Thông tin mẹ, null nếu không có
    "lastName": "string",
    "firstName": "string",
    "code": "string",
    "gender": "string"
  }},
  "husband": {{ // Thông tin chồng, null nếu không có
    "lastName": "string",
    "firstName": "string",
    "code": "string",
    "gender": "string"
  }},
  "wife": [ // Mảng các đối tượng vợ, mảng rỗng nếu không có
    {{
      "lastName": "string",
      "firstName": "string",
      "code": "string",
      "gender": "string"
    }}
  ]
}}

Nếu không tìm thấy thông tin cho một trường nào đó, hãy sử dụng giá trị `null` hoặc một chuỗi/mảng rỗng phù hợp với kiểu dữ liệu của trường đó. Đối với các trường ngày tháng, nếu chỉ có năm, hãy sử dụng định dạng YYYY-01-01T00:00:00Z.

Nội dung HTML:
---
{html_content}
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


def extract_member_info_ollama(html_file_path: str, output_json_file_path: str, family_id: str):
    if os.path.exists(output_json_file_path):
        print(f"Tệp JSON đầu ra '{output_json_file_path}' đã tồn tại. Bỏ qua trích xuất.", file=sys.stderr)
        return
    
    print(f"Trích xuất thông tin thành viên từ '{html_file_path}' bằng Ollama...")
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        member_id = os.path.basename(html_file_path).replace('.html', '')
        extracted_data = extract_info_with_ollama(html_content, family_id, member_id)
        
        with open(output_json_file_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print(f"Thông tin đã được trích xuất và lưu vào '{output_json_file_path}'.")

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp HTML tại '{html_file_path}'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Lỗi trong quá trình trích xuất thông tin thành viên bằng Ollama: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Cách dùng: python extract_member_info_ollama.py <input_html_file_path> <output_json_file_path> <family_id>")
        sys.exit(1)
    
    input_html_file = sys.argv[1]
    output_json_file = sys.argv[2]
    family_id_arg = sys.argv[3]

    extract_member_info_ollama(input_html_file, output_json_file, family_id_arg)
