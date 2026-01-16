import os
import json
import argparse
from vietnamgiapha.extraction.rule_based import extract_family_tree
from vietnamgiapha.extraction.rule_based import extract_family
from vietnamgiapha.extraction.rule_based import extract_member

def main():
    parser = argparse.ArgumentParser(description="Process family tree data from HTML files in subfolders.")
    parser.add_argument("--output_base_dir", type=str, default="output",
                        help="Base directory containing family folders (e.g., 'output/1', 'output/10').")
    parser.add_argument("--limit", type=int,
                        help="Limit the number of family folders to process for testing purposes.")
    parser.add_argument("--force", action="store_true",
                        help="Force reprocessing even if output JSON files already exist.")
    parser.add_argument("--family_id", type=str,
                        help="Process only a specific family ID (e.g., '1691'). Overrides --limit if provided.")
    parser.add_argument("--start_id", type=int,
                        help="Start processing from this family ID (inclusive). Requires --end_id.")
    parser.add_argument("--end_id", type=int,
                        help="End processing at this family ID (inclusive). Requires --start_id.")
    args = parser.parse_args()

    # Resolve absolute path for the output base directory
    output_base_path = os.path.abspath(args.output_base_dir)

    processed_count = 0
    
    # Get list of family folders to process
    family_folders_to_process = []
    if args.family_id:
        specific_family_folder_path = os.path.join(output_base_path, args.family_id)
        if os.path.isdir(specific_family_folder_path):
            family_folders_to_process.append(args.family_id)
        else:
            print(f"Lỗi: Không tìm thấy thư mục gia đình '{args.family_id}' tại '{output_base_path}'.")
            return
    elif args.start_id is not None and args.end_id is not None:
        if args.start_id > args.end_id:
            print("Lỗi: --start_id phải nhỏ hơn hoặc bằng --end_id.")
            return
        
        for i in range(args.start_id, args.end_id + 1):
            folder_name = str(i)
            family_folder_path = os.path.join(output_base_path, folder_name)
            if os.path.isdir(family_folder_path):
                family_folders_to_process.append(folder_name)
            # else: We don't print a warning here, as it's expected that not all IDs in a range might exist.
    else: # Process all folders if no specific family_id or range is provided
        for entry_name in sorted(os.listdir(output_base_path)):
            if os.path.isdir(os.path.join(output_base_path, entry_name)) and entry_name.isdigit():
                family_folders_to_process.append(entry_name)

    for entry_name in family_folders_to_process:
        family_folder_path = os.path.join(output_base_path, entry_name)

        if args.limit and processed_count >= args.limit:
            print(f"Đã đạt đến giới hạn {args.limit} thư mục. Dừng xử lý.")
            break

        print(f"Đang xử lý thư mục gia đình: {family_folder_path}")

        raw_html_dir = os.path.join(family_folder_path, "raw_html")
        output_data_dir = os.path.join(family_folder_path, "data")
        os.makedirs(output_data_dir, exist_ok=True)

        # --- Process Family Overview (giapha.html, thuy_to.html, pha_ky_gia_su.html, toc_uoc.html) ---
        family_output_json_file = os.path.join(output_data_dir, "family.json")
        if not os.path.exists(family_output_json_file) or args.force:
            try:
                giapha_html_content = ""
                thuy_to_html_content = ""
                phaky_html_content = ""
                tocuoc_html_content = ""

                # Read HTML files for family extraction
                giapha_path = os.path.join(raw_html_dir, "giapha.html")
                if os.path.exists(giapha_path):
                    with open(giapha_path, "r", encoding="utf-8") as f:
                        giapha_html_content = f.read()

                thuy_to_path = os.path.join(raw_html_dir, "thuy_to.html")
                if os.path.exists(thuy_to_path):
                    with open(thuy_to_path, "r", encoding="utf-8") as f:
                        thuy_to_html_content = f.read()
                
                pha_ky_gia_su_path = os.path.join(raw_html_dir, "pha_ky_gia_su.html")
                if os.path.exists(pha_ky_gia_su_path):
                    with open(pha_ky_gia_su_path, "r", encoding="utf-8") as f:
                        phaky_html_content = f.read()

                toc_uoc_path = os.path.join(raw_html_dir, "toc_uoc.html")
                if os.path.exists(toc_uoc_path):
                    with open(toc_uoc_path, "r", encoding="utf-8") as f:
                        tocuoc_html_content = f.read()

                overview_data = extract_family.extract_overview(giapha_html_content)
                progenitor_data = extract_family.extract_progenitor(thuy_to_html_content)
                phaky_data = extract_family.extract_phaky(phaky_html_content)
                tocuoc_data = extract_family.extract_tocuoc(tocuoc_html_content)
                
                final_family_data = extract_family.build_schema(overview_data, progenitor_data, phaky_data, tocuoc_data)

                with open(family_output_json_file, 'w', encoding='utf-8') as f:
                    json.dump(final_family_data, f, ensure_ascii=False, indent=2)
                print(f"  Dữ liệu gia đình đã trích xuất thành công và lưu vào: {family_output_json_file}")
            except Exception as e:
                print(f"  Lỗi khi xử lý dữ liệu gia đình cho {family_folder_path}: {e}")
        else:
            print(f"  File '{family_output_json_file}' đã tồn tại. Bỏ qua.")

        # --- Process Family Tree (pha_he.html) ---
        pha_he_output_json_file = os.path.join(output_data_dir, "pha_he.json")
        html_file_path_for_tree = os.path.join(raw_html_dir, "pha_he.html")
        if not os.path.exists(pha_he_output_json_file) or args.force:
            if os.path.exists(html_file_path_for_tree):
                try:
                    family_tree_data = extract_family_tree.extract_data(html_file_path_for_tree)
                    with open(pha_he_output_json_file, 'w', encoding='utf-8') as f:
                        json.dump(family_tree_data, f, ensure_ascii=False, indent=2)
                    print(f"  Dữ liệu cây gia đình đã trích xuất thành công và lưu vào: {pha_he_output_json_file}")
                except Exception as e:
                    print(f"  Lỗi khi xử lý cây gia đình cho {family_folder_path}: {e}")
            else:
                print(f"  Không tìm thấy file pha_he.html tại {html_file_path_for_tree}. Bỏ qua trích xuất cây gia đình.")
        else:
            print(f"  File '{pha_he_output_json_file}' đã tồn tại. Bỏ qua.")

        # --- Process Individual Members (raw_html/members/*.html) ---
        members_raw_html_dir = os.path.join(raw_html_dir, "members")
        if os.path.isdir(members_raw_html_dir):
            members_output_data_dir = os.path.join(output_data_dir, "members")
            os.makedirs(members_output_data_dir, exist_ok=True)

            for member_html_filename in sorted(os.listdir(members_raw_html_dir)):
                if member_html_filename.endswith(".html"):
                    member_html_file_path = os.path.join(members_raw_html_dir, member_html_filename)
                    base_member_name = os.path.splitext(member_html_filename)[0]
                    member_output_json_file = os.path.join(members_output_data_dir, f"{base_member_name}.json")

                    if not os.path.exists(member_output_json_file) or args.force:
                        try:
                            with open(member_html_file_path, "r", encoding="utf-8") as f:
                                member_html_content = f.read()
                            
                            member_data_json_str = extract_member.parse_family_html(
                                member_html_content, 
                                family_id=entry_name, 
                                member_filename=member_html_filename
                            )
                            member_data = json.loads(member_data_json_str)

                            final_member_output_json_file = os.path.join(members_output_data_dir, f"{base_member_name}.json")

                            with open(final_member_output_json_file, 'w', encoding='utf-8') as f:
                                json.dump(member_data, f, ensure_ascii=False, indent=2)
                            print(f"  Dữ liệu thành viên '{base_member_name}' đã trích xuất thành công và lưu vào: {final_member_output_json_file}")
                        except Exception as e:
                            print(f"  Lỗi khi xử lý thành viên '{member_html_filename}' cho {family_folder_path}: {e}")
                    else:
                        print(f"  File '{member_output_json_file}' đã tồn tại. Bỏ qua.")
        else:
            print(f"  Không tìm thấy thư mục 'members' tại {members_raw_html_dir}. Bỏ qua trích xuất thành viên.")
        
        processed_count += 1
        print("-" * 50) # Separator for better readability

if __name__ == "__main__":
    main()

