import os
import json
import sys 
"""
Goal of this file is to automatically read each .txt file from raw_resumes
and raw_jds, using existing parser functions from parsers to convert the text
into dictionaries, and then save those dicts as .json files in the 
resumes and job_descriptions folders
"""
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,project_root)

try:
    from resume_parser import parse_resume_file
    from job_description_parser import parse_jd_file
except ImportError as e:
    print(f"Error importing parser functions: {e}")
    print("ACTION NEEDED: Edit the import statements above in prepare_test_data.py.")
    sys.exit(1)


RAW_RESUME_TXT_DIR = os.path.join('tests', 'data', 'raw_resumes')
RAW_JD_TXT_DIR = os.path.join('tests', 'data', 'raw_jds')

OUTPUT_RESUME_JSON_DIR = os.path.join('tests', 'data', 'resumes')
OUTPUT_JD_JSON_DIR = os.path.join('tests', 'data', 'job_descriptions')

print("Ensuring output directories exist...")
os.makedirs(OUTPUT_RESUME_JSON_DIR,exist_ok=True)
os.makedirs(OUTPUT_JD_JSON_DIR,exist_ok=True)

print(f"\nProcessing resumes from: {RAW_RESUME_TXT_DIR}")
if not os.path.isdir(RAW_RESUME_TXT_DIR):
    print(f"  ERROR: Input directory not found: {RAW_RESUME_TXT_DIR}")
else:
    for txt_filename in os.listdir(RAW_RESUME_TXT_DIR):
        if txt_filename.lower().endswith(".txt"):
            txt_filepath = os.path.join(RAW_RESUME_TXT_DIR,txt_filename)
            print(f"Processing: {txt_filename}")
            try:
                parsed_resume_dict = parse_resume_file(txt_filepath)

                if parsed_resume_dict and isinstance(parsed_resume_dict,dict):
                    json_filename = os.path.splitext(txt_filename)[0] + '.json'
                    json_filepath = os.path.join(OUTPUT_RESUME_JSON_DIR, json_filename)

                    with open(json_filepath,'w',encoding='utf-8') as f:
                        json.dump(parsed_resume_dict,f,ensure_ascii=False,indent=4)
                    print(f"    --> Saved to: {json_filepath}")
                else:
                    print(f"    WARNING: Parser did not return a valid dictionary for {txt_filename}. Skipping.")

            except Exception as e:
                print(f"    ERROR processing {txt_filename}: {e}")

                    
# --- 5. Process Job Descriptions ---
print(f"\nProcessing job descriptions from: {RAW_JD_TXT_DIR}")

if not os.path.isdir(RAW_JD_TXT_DIR):
    print(f"  ERROR: Input directory not found: {RAW_JD_TXT_DIR}")
else:
    for txt_filename in os.listdir(RAW_JD_TXT_DIR):
        if txt_filename.lower().endswith(".txt"):
            txt_filepath = os.path.join(RAW_JD_TXT_DIR, txt_filename)
            print(f"  Processing: {txt_filename}")
            try:
                parsed_jd_dict = parse_jd_file(txt_filepath)

                if parsed_jd_dict and isinstance(parsed_jd_dict,dict):
                    json_filename = os.path.splitext(txt_filename)[0]+'.json'
                    json_filepath = os.path.join(OUTPUT_JD_JSON_DIR, json_filename)

                    with open(json_filepath, 'w', encoding='utf-8') as f:
                        json.dump(parsed_jd_dict, f, ensure_ascii=False, indent=4)
                    print(f"    --> Saved to: {json_filepath}")   
                else:
                    print(f"    WARNING: Parser did not return a valid dictionary for {txt_filename}. Skipping.")
            
            except Exception as e:
                print(f"    ERROR processing {txt_filename}: {e}")


print("\nTest data preparation script finished.")