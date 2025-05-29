import pandas as pd
import logging 
import json

try:
    import job_description_parser 
    logging.info("Successfully imported 'job_description_parser'")
except ImportError:
    logging.error("Could not import 'job_description_parser'. Make sure it's in the same directory or Python path.")
    job_description_parser = None 
except Exception as e:
    logging.error(f"An unexpected error occurred during import of 'job_description_parser': {e}")
    job_description_parser = None


def load_jobs_from_csv(csv_filepath='remoteok_jobs_data.csv'):
    """
    Loads job data from a CSV file into a Pandas DataFrame.
    """
    try:
        df_jobs = pd.read_csv(csv_filepath)
        logging.info(f"Successfully loaded {len(df_jobs)} jobs from {csv_filepath}")
        required_cols = ['title', 'company', 'location', 'tags', 'description_text', 'url']
        if not all(col in df_jobs.columns for col in required_cols):
            logging.warning(f"CSV file {csv_filepath} is missing one or more required columns: {required_cols}")
        return df_jobs
    except FileNotFoundError:
        logging.error(f"Error: CSV file not found at {csv_filepath}")
        return pd.DataFrame() 
    except Exception as e:
        logging.error(f"An error occurred while loading the CSV {csv_filepath}: {e}")
        return pd.DataFrame() 

def main():
    """
    Main function to load job data, parse it, and store/display results.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    if not job_description_parser:
        logging.error("Job parser module ('job_description_parser.py') could not be loaded. Exiting.")
        return

    df_jobs = load_jobs_from_csv('remoteok_jobs_data.csv')

    if df_jobs.empty:
        logging.info("No jobs loaded from CSV. Exiting.")
        return

    all_parsed_jds = []

    logging.info("\nStarting to parse job descriptions from the DataFrame...")
    
    # Loop through all jobs
    for index, row in df_jobs.iterrows():
        original_title = row.get('title', 'N/A')
        original_company = row.get('company', 'N/A')
        
        logging.info(f"\n\n======================================================================")
        logging.info(f"--- Processing Job {index + 1} / {len(df_jobs)}: '{original_title}' by '{original_company}' ---")
        logging.info(f"======================================================================")
        
        description_text = str(row.get('description_text', ''))
        api_title = str(row.get('title', '')) #
        api_company = str(row.get('company', '')) 
        api_location = str(row.get('location', '')) 
        
        api_tags_str = str(row.get('tags', ''))
        api_tags_list = [tag.strip() for tag in api_tags_str.split(',') if tag.strip()] if api_tags_str else []

        parsed_jd_data = job_description_parser.process_scraped_job_data(
            job_description_text=description_text,
            api_title=api_title,
            api_company=api_company,
            api_location=api_location,
            api_tags=api_tags_list 
        )

        if parsed_jd_data:
            parsed_jd_data['original_url'] = row.get('url')
            parsed_jd_data['original_epoch_time'] = row.get('epoch_time')
            parsed_jd_data['original_api_salary_min'] = row.get('api_salary_min')
            parsed_jd_data['original_api_salary_max'] = row.get('api_salary_max')
            parsed_jd_data['original_id'] = row.get('id') # If you added 'id' in scraper.py
            
            all_parsed_jds.append(parsed_jd_data)
            
            # This print block is for detailed inspection of each job
            print(f"\n--- PARSED DATA FOR JOB: '{parsed_jd_data.get('job_title', original_title)}' ---")
            print(json.dumps(parsed_jd_data, indent=4, ensure_ascii=False))
            print(f"--- END OF PARSED DATA FOR: '{parsed_jd_data.get('job_title', original_title)}' ---")
        
        else:
            logging.warning(f"Could not parse JD for '{original_title}'")

    logging.info(f"\nFinished processing. Parsed {len(all_parsed_jds)} job descriptions (out of {len(df_jobs)} loaded from CSV).")

    if all_parsed_jds:
        df_parsed_jds = pd.DataFrame(all_parsed_jds)
        
        logging.info("\n--- DataFrame of Parsed JDs (first 5 rows) ---") 
        print(df_parsed_jds.head())
        
        try:
            parsed_csv_filename = 'remoteok_parsed_jds.csv'
            df_parsed_jds.to_csv(parsed_csv_filename, index=False, encoding='utf-8')
            logging.info(f"Successfully saved {len(df_parsed_jds)} parsed job descriptions to {parsed_csv_filename}")
        except Exception as e:
            logging.error(f"Error saving parsed JDs to CSV: {e}")
            
    else:
        logging.info("No job descriptions were successfully parsed.") 

if __name__ == "__main__":
    main()