import json
import sys
import requests
import os
from utils import remove_html_tag_attributes # Import the utility function

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b") # Default model, can be overridden

def extract_info_with_ollama(html_content: str, family_id: str, member_id: str):
    """
    Sends HTML content to Ollama for structured data extraction according to schema-member.txt.
    """
    # Clean the HTML content by removing all tags
    cleaned_html_content = remove_html_tag_attributes(html_content)

    prompt = f"""You are a genealogy data analysis expert. Your task is to extract information about a family member from the provided HTML content.
Extract the following information and return it as a JSON object, strictly adhering to the following structure and fields. For the "code" field, format it as "GPVN-M-{family_id}-{member_id}".

{{
  "lastName": "string", // Last name (e.g., Triết)
  "firstName": "string", // Middle and first name (e.g., Minh)
  "code": "GPVN-M-{family_id}-{member_id}", // Member code, format: GPVN-M-<family_id>-<member_id>
  "nickname": "string", // Nickname (e.g., Lý Triết)
  "dateOfBirth": "YYYY-MM-DDTHH:mm:ssZ", // Date of birth, ISO 8601 format. If only the year is available, use YYYY-01-01T00:00:00Z.
  "dateOfDeath": "YYYY-MM-DDTHH:mm:ssZ", // Date of death, ISO 8601 format. If only the year is available, use YYYY-01-01T00:00:00Z.
  "dateOfDeathLunar": "string", // Ngày mất âm lịch (nếu có định dạng ngày/tháng hoặc có từ "Âm Lịch", "AL").
  "placeOfBirth": "string", // Place of birth
  "placeOfDeath": "string", // Place of death
  "phone": "string", // Phone number
  "email": "string", // Email address
  "address": "string", // Address
  "gender": "string", // Gender ("Nam", "Nữ", or "Không rõ") - use Vietnamese for consistency with source data.
  "avatarUrl": "string", // Avatar URL
  "avatarBase64": "string", // Avatar Base64
  "occupation": "string", // Occupation
  "biography": "string", // Biography (Career, merits, notes)
  "isRoot": "boolean", // Is the progenitor (true/false)
  "isDeceased": "boolean", // Is deceased (true/false)
  "order": "integer", // Thứ tự con cái. Nếu không đề cập trong HTML, để giá trị 0.
  "generation": "integer", // Số đời (ví dụ: từ "Đời thứ: 10" hãy trích xuất số 10). Nếu không tìm thấy, để giá trị null.
  "father": {{ // Father's information, null if not available
    "lastName": "string",
    "firstName": "string",
    "code": "string",
    "gender": "string"
  }},
  "mother": {{ // Mother's information, null if not available
    "lastName": "string",
    "firstName": "string",
    "code": "string",
    "gender": "string"
  }},
  "husband": {{ // Husband's information, null if not available
    "lastName": "string",
    "firstName": "string",
    "code": "string",
    "gender": "string"
  }},
  "wife": [ // Array of wife objects, empty array if not available
    {{
      "lastName": "string",
      "firstName": "string",
      "code": "string",
      "gender": "string"
    }}
  ]
}}

If information for a field is not found, use `null` or an empty string/array appropriate for the field's data type. For date fields, if only the year is available, use the YYYY-01-01T00:00:00Z format. For `dateOfDeathLunar`, extract the day/month string if the death date contains "Âm Lịch", "AL", or is in "day/month" format; otherwise, use `null`.

HTML Content:
---
{cleaned_html_content}
---

Return ONLY valid JSON, with no additional text.
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


def extract_member_info_ollama(html_file_path: str, family_id: str):
    member_id = os.path.basename(html_file_path).replace('.html', '')
    
    output_dir = os.path.join("output", family_id, 'data', 'members')
    os.makedirs(output_dir, exist_ok=True)
    output_json_file_path = os.path.join(output_dir, f"{member_id}.json")

    if os.path.exists(output_json_file_path):
        print(f"Tệp JSON đầu ra '{output_json_file_path}' đã tồn tại. Bỏ qua trích xuất.", file=sys.stderr)
        return
    
    print(f"Trích xuất thông tin thành viên từ '{html_file_path}' bằng Ollama...")
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

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
    if len(sys.argv) < 3: # Reduced from 4 to 3 arguments
        print("Cách dùng: python extract_member_info_ollama.py <input_html_file_path> <family_id>")
        sys.exit(1)
    
    input_html_file = sys.argv[1]
    # output_json_file is now constructed inside the function
    family_id_arg = sys.argv[2] # family_id is now the second argument

    extract_member_info_ollama(input_html_file, family_id_arg)
