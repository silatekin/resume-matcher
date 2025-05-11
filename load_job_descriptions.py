import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOB_DESCRIPTIONS_DIR = os.path.join(BASE_DIR,"tests","data","job_descriptions")

def load_all_job_descriptions_from_folder(directory_path=JOB_DESCRIPTIONS_DIR):
    """
    Loads all JSON files from the specified directory.
    Each JSON file is expected to be a dictionary representing one job.
    Uses the directory_path argument, defaulting to JOB_DESCRIPTIONS_DIR.
    """

    all_jobs = []
    current_id = 1

    if not os.path.exists(directory_path):
        logging.error((f"Job descriptions directory not found: {directory_path}"))
        return all_jobs
    
    logging.info(f"Loading jobs from: {directory_path}")

    job_files_found = 0
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            job_files_found +=1
            file_path = os.path.join(directory_path,filename)
            try:
                with open(file_path,'r',encoding='utf-8') as f:
                    job_data = json.load(f)

                job_data['id'] = current_id
                current_id += 1  
                all_jobs.append(job_data)

            except json.JSONDecodeError:
                logging.warning(f"Could not decode JSON from {filename} in {directory_path}. Skipping.")
            except Exception as e:
                 logging.error(f"Error loading job description {filename} from {directory_path}: {e}")

    if job_files_found == 0:
       logging.warning(f"No JSON files found in {directory_path}. No jobs loaded.")
    elif all_jobs:
       logging.info(f"Successfully loaded {len(all_jobs)} job descriptions from {directory_path}.")

    return all_jobs



if __name__ == '__main__':
    print("Testing job loading...")
    jobs = load_all_job_descriptions_from_folder()
    if jobs:
        print(f"Loaded {len(jobs)} jobs. First job: {jobs[0]}")
        for job in jobs[:3]:
            print(f"  Job ID: {job.get('id')}, Title: {job.get('title')}")
    else:
        print("No jobs were loaded.")




