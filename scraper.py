import requests
import json
from bs4 import BeautifulSoup
import unicodedata
import ftfy
import csv
import logging 


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - SCRAPER - %(message)s')

api_url = "https://remoteok.io/api"

logging.info(f"Attempting to fetch data from API: {api_url}")

try:
    headers = {
        'User-Agent': 'MyResumeParserProject/1.0 academic use only'
    }
    response = requests.get(api_url, headers=headers, timeout=15) 
    response.raise_for_status()

    logging.info("Successfully fetched data from the API!")
    jobs_data_from_api = response.json()

except requests.exceptions.HTTPError as http_err:
    logging.error(f"HTTP error occurred: {http_err}")
    logging.error(f"Response content: {response.text if 'response' in locals() else 'No response object'}")
    jobs_data_from_api = None
except requests.exceptions.RequestException as e:
    logging.error(f"An error occurred: {e}")
    jobs_data_from_api = None
except json.JSONDecodeError:
    logging.error("Failed to decode JSON from the API response.")
    logging.error(f"Response text was: {response.text[:500] if 'response' in locals() else 'No response object'}")
    jobs_data_from_api = None

cleaned_jobs_list = []

if jobs_data_from_api:
    logging.info(f"Total items received from API: {len(jobs_data_from_api)}")

    start_index = 0
    if isinstance(jobs_data_from_api, list) and len(jobs_data_from_api) > 0:
        if 'legal' in jobs_data_from_api[0] or not jobs_data_from_api[0].get('company'):
            logging.info("Note: First item in API response appears to be metadata/legal notice, skipping it.")
            start_index = 1
    
    logging.info(f"Processing job entries starting from index {start_index}...")
    for i, job_json_entry in enumerate(jobs_data_from_api[start_index:]):
        logging.debug(f"Processing raw API entry {i+start_index}...")
        title = job_json_entry.get('position', 'N/A')
        company = job_json_entry.get('company', 'N/A')
        date_posted_str = job_json_entry.get('date', 'N/A') 
        tags_list = job_json_entry.get('tags', [])
        location = job_json_entry.get('location', 'N/A')
        job_url = job_json_entry.get('url', 'N/A')
        api_salary_min = job_json_entry.get('salary_min')
        api_salary_max = job_json_entry.get('salary_max')
        epoch_time = job_json_entry.get('epoch')

        html_description = job_json_entry.get('description', '')
        plain_text_description = "No description provided." 
        if html_description:
            soup = BeautifulSoup(html_description, 'html.parser')
            
            plain_text_description_raw = soup.get_text(separator='\n', strip=True)
            
            normalized_text = unicodedata.normalize('NFKC', plain_text_description_raw)
            plain_text_description = ftfy.fix_text(normalized_text)
            
        processed_job_data = {
            'title': title,
            'company': company,
            'date_posted': date_posted_str,
            'epoch_time': epoch_time,
            'location': location,
            'tags': ", ".join(tags_list) if tags_list else '', 
            'description_text': plain_text_description,
            'url': job_url,
            'api_salary_min': api_salary_min,
            'api_salary_max': api_salary_max,
            'id': job_json_entry.get('id') 
        }
        cleaned_jobs_list.append(processed_job_data)

    logging.info(f"Finished processing. Total jobs added to list: {len(cleaned_jobs_list)}")

    if cleaned_jobs_list:
        csv_file_name = 'remoteok_jobs_data.csv'
        headers = cleaned_jobs_list[0].keys()
        try:
            with open(csv_file_name, 'w', newline='', encoding='utf-8') as output_file:
                dict_writer = csv.DictWriter(output_file, fieldnames=headers)
                dict_writer.writeheader()
                dict_writer.writerows(cleaned_jobs_list)
            logging.info(f"Successfully saved {len(cleaned_jobs_list)} jobs to {csv_file_name}")
        except IOError:
            logging.error(f"I/O error writing to {csv_file_name}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while writing to CSV: {e}")
    else:
        logging.info("No data processed to save to CSV.")
else:
    logging.info("No data received from API to process.")