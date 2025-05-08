import json
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from matcher import calculate_match_score

PARSED_DATA_DIR = os.path.join(project_root, 'tests', 'data')
RESUME_DATA_PATH = os.path.join(PARSED_DATA_DIR, 'resumes') 
JD_DATA_PATH = os.path.join(PARSED_DATA_DIR, 'job_descriptions')

def load_json_data(filename, data_type='resume'):
        """Loads parsed JSON data from the test data directory."""
        if data_type == 'resume':
            subfolder = 'resumes'
        elif data_type == 'jd':
            subfolder = 'job_descriptions'
        else:
            print(f"Error: Invalid data_type '{data_type}'. Use 'resume' or 'jd'.")
            return None

        data_path = os.path.join(PARSED_DATA_DIR, subfolder, filename)

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"Error: Test data file not found: {data_path}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Error decoding JSON from test data file: {data_path}")
            return None
        except Exception as e:
            print(f"Error: Unexpected error loading test data {data_path}: {e}")
            return None


    # --- Load the specific resume and JD data ---
resume_filename = 'resume_01.json'
jd_filename = 'job_11.json'

parsed_resume = load_json_data(resume_filename, 'resume')
parsed_jd = load_json_data(jd_filename, 'jd')


if parsed_resume is None or parsed_jd is None:
        print("Failed to load test data. Exiting.")
        sys.exit(1)



print(f"Calculating match score for {resume_filename} vs {jd_filename}...")
match_results = calculate_match_score(parsed_resume, parsed_jd)


print("\n--- Keyword Matching Details from Results ---")
keyword_details = match_results.get('keyword_details', {})
print(f"Keyword Score: {keyword_details.get('score')}")
print(f"Matching Keywords Count: {len(keyword_details.get('matching_keywords', []))}")
print(f"Matching Keywords: {keyword_details.get('matching_keywords')}")
print(f"Total JD Keywords Count: {keyword_details.get('total_jd_keywords_count')}")

print("\n--- All Results ---")