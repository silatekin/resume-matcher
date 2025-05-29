import os
import json
import sys 
import logging

"""
Goal of this file is to automatically read each .txt file from raw_resumes
and raw_jds, using existing parser functions from parsers to convert the text
into dictionaries, and then save those dicts as .json files in the 
resumes and job_descriptions folders
"""
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,project_root)

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from resume_parser import parse_resume_file
    from job_description_parser import parse_jd_file
    
    from resume_parser import (
        NLP_MODEL_GLOBAL,
        TECH_SKILLS_LIST_GLOBAL, 
        TECH_SKILLS_SET_GLOBAL,  
        SECTION_HEADERS_GLOBAL,  
        EDUCATION_LEVELS_GLOBAL  
    )

    if NLP_MODEL_GLOBAL is None:
        logging.critical("NLP_MODEL_GLOBAL from resume_parser.py is None. Cannot proceed.")
        sys.exit(1)
    if not TECH_SKILLS_LIST_GLOBAL or not SECTION_HEADERS_GLOBAL or not EDUCATION_LEVELS_GLOBAL:
        logging.warning("One or more global configurations (skills, section headers, education levels) from resume_parser.py might be empty or not loaded.")
except ImportError as e:
    print(f"Error importing parser functions: {e}")
    print("ACTION NEEDED: Edit the import statements above in prepare_test_data.py.")
    sys.exit(1)
except AttributeError as e: 
    logging.critical(f"Missing a required global variable in resume_parser.py: {e}")
    sys.exit(1)


RAW_RESUME_DIR = os.path.join('tests', 'data', 'raw_resumes')
RAW_JD_TXT_DIR = os.path.join('tests', 'data', 'raw_jds')

OUTPUT_RESUME_JSON_DIR = os.path.join('tests', 'data', 'resumes')
OUTPUT_JD_JSON_DIR = os.path.join('tests', 'data', 'job_descriptions')

logging.info("Ensuring output directories exist...")
os.makedirs(OUTPUT_RESUME_JSON_DIR,exist_ok=True)
os.makedirs(OUTPUT_JD_JSON_DIR,exist_ok=True)

print(f"\nProcessing resumes from: {RAW_RESUME_DIR}")
if not os.path.isdir(RAW_RESUME_DIR):
    print(f"  ERROR: Input directory not found: {RAW_RESUME_DIR}")
else:
    processed_resume_count = 0
    for filename in os.listdir(RAW_RESUME_DIR):
        if filename.lower().endswith((".txt", ".docx")):
            file_path = os.path.join(RAW_RESUME_DIR, filename)
            logging.info(f"Processing resume: {filename}")
            try:
                parsed_resume_dict = parse_resume_file(
                    file_path,
                    NLP_MODEL_GLOBAL,          
                    TECH_SKILLS_LIST_GLOBAL, 
                    TECH_SKILLS_SET_GLOBAL,  
                    SECTION_HEADERS_GLOBAL,  
                    EDUCATION_LEVELS_GLOBAL  
                )

                if parsed_resume_dict and isinstance(parsed_resume_dict,dict) and "error" not in parsed_resume_dict:
                    json_filename = os.path.splitext(filename)[0] + '.json'
                    json_filepath = os.path.join(OUTPUT_RESUME_JSON_DIR, json_filename)

                    with open(json_filepath,'w',encoding='utf-8') as f:
                        json.dump(parsed_resume_dict,f,ensure_ascii=False,indent=4)
                    logging.info(f"    --> Saved to: {json_filepath}")
                    processed_resume_count += 1
                elif parsed_resume_dict and "error" in parsed_resume_dict:
                    logging.warning(f"    WARNING: Parser returned an error for {filename}: {parsed_resume_dict.get('error')}. Skipping save.")
                else:
                    logging.warning(f"    WARNING: Parser did not return a valid dictionary for {filename} (returned None or unexpected type). Skipping save.")
            except Exception as e:
                logging.error(f"    ERROR processing {filename}: {e}", exc_info=True) 
    logging.info(f"Finished processing resumes. {processed_resume_count} resumes saved as JSON.")

              
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
