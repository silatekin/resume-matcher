import pandas as pd
import re
import json
import spacy
from job_description_parser import parse_jd_file
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from job_description_parser import (
        clean_text,
        segment_jd,
        parse_jd_sections,
        nlp, 
        tech_skills_set, 
        SECTION_HEADERS, 
        EDUCATION_LEVELS 
    )
    logging.info("Successfully imported functions and variables from job_description_parser.py")
    if nlp.meta['name'] == 'en_core_web_md': 
        logging.info(f"spaCy model '{nlp.meta['name']}' from job_description_parser.py is ready.")
    else:
        logging.warning(f"A spaCy model is loaded, but it's '{nlp.meta['name']}'. Check if this is intended.")

except ImportError:
    logging.error("Failed to import from job_description_parser.py. "
                  "Make sure the file is in the correct location and has no import errors itself.")
    exit()
except AttributeError as e:
    logging.error(f"Attribute error during import from job_description_parser: {e}. "
                  "This might mean some global variables (nlp, tech_skills_set etc.) are not available as expected.")
    exit()


# Load Kaggle dataset
try:
    df = pd.read_csv('job_descriptions.csv', nrows=150)
    print(f"Successfully loaded dataset. Total jobs: {len(df)}")
    df_sample = df
except FileNotFoundError:
    print("Error: Dataset CSV not found.")
    exit()
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit()

def parse_experience_to_min_years(experience_str):
    if pd.isna(experience_str) or not isinstance(experience_str, str):
        return None
    numbers = re.findall(r'\d+', str(experience_str)) # Find all numbers
    if numbers:
        return int(numbers[0]) # Take the first number as the minimum
    return None

jobs_to_process_further = []
logging.info(f"Preparing {len(df_sample)} job entries for text parsing...")
for index, row in df_sample.iterrows():
    text_parts_for_parser = []
    job_title = str(row.get('Job Title', ''))
    responsibilities = str(row.get('Responsibilities', ''))
    qualifications_text = str(row.get('Qualifications', ''))
    skills_text_from_csv = str(row.get('skills', ''))
    job_description_main = str(row.get('Job Description', ''))
    benefits_text = str(row.get('Benefits', ''))

    if job_title: text_parts_for_parser.append(f"Job Title:\n{job_title}")
    if responsibilities: text_parts_for_parser.append(f"Responsibilities:\n{responsibilities}")
    if qualifications_text: text_parts_for_parser.append(f"Qualifications:\n{qualifications_text}")
    if skills_text_from_csv: text_parts_for_parser.append(f"Skills Required Description:\n{skills_text_from_csv}")
    if job_description_main: text_parts_for_parser.append(f"Detailed Job Description:\n{job_description_main}")
    if benefits_text: text_parts_for_parser.append(f"Benefits:\n{benefits_text}")
    full_text_for_segmentation = "\n\n".join(text_parts_for_parser)
    
    # 'full_text_for_segmentation':
    # "Job Title:
    # Software Engineer
    #
    # Responsibilities:
    # Develop cool stuff...
    #
    # Skills Required Description:
    # Python, Java, Problem solving...
    #
    # Detailed Job Description:
    # This role involves..."

    job_data_entry = {
        'text_to_parse': full_text_for_segmentation,
        'job_id_kaggle': row.get('Job Id'),
        'job_title_kaggle': job_title,
        'company_name_kaggle': str(row.get('Company', '')),
        'experience_raw_kaggle': str(row.get('Experience', '')),
        'min_years_from_kaggle_experience_col': parse_experience_to_min_years(row.get('Experience')),
        'qualifications_text_raw_kaggle': qualifications_text,
        'skills_text_raw_kaggle': skills_text_from_csv,
        'role_kaggle': str(row.get('Role', '')),
        'salary_range_kaggle': str(row.get('Salary Range', '')),
        'location_kaggle': str(row.get('location', '')),
        'country_kaggle': str(row.get('Country', '')),
        'work_type_kaggle': str(row.get('Work Type', '')),
        'job_posting_date_kaggle': str(row.get('Job Posting Date', '')),
        'company_profile_text_kaggle': str(row.get('Company Profile', ''))
        
    }
    """
    Maybe add these to dictionary?
        'role_kaggle': str(row.get('Role', '')),
        'salary_range_kaggle': str(row.get('Salary Range', '')),
        'location_kaggle': str(row.get('location', '')), # Remember this was lowercase 'location'
        'country_kaggle': str(row.get('Country', '')),
        'work_type_kaggle': str(row.get('Work Type', '')),
        'job_posting_date_kaggle': str(row.get('Job Posting Date', '')), # Useful for UI
        'company_profile_text_kaggle': str(row.get('Company Profile', '')), # Useful for UI or context
        'responsibilities_text_raw_kaggle': responsibilities, # Already fetched
        'job_description_text_raw_kaggle': job_description_main, # Already fetched
        'benefits_text_raw_kaggle': benefits_text # Already fetched
    """

    jobs_to_process_further.append(job_data_entry)

logging.info(f"\nPrepared {len(jobs_to_process_further)} job entries for text parsing.")


all_final_jds_for_matcher = []
logging.info(f"\nStarting NLP parsing of {len(jobs_to_process_further)} job descriptions...")


for i, entry in enumerate(jobs_to_process_further):
    logging.info(f"  Parsing job {i+1}/{len(jobs_to_process_further)}: {entry.get('job_title_kaggle', 'Unknown Title')}")
    text_to_feed_to_parser = entry['text_to_parse']
    

    cleaned_text = clean_text(text_to_feed_to_parser)
    segmented_sections = segment_jd(cleaned_text)
    
    if not segmented_sections:
        logging.warning(f"    Job {entry.get('job_id_kaggle', 'N/A')} - {entry.get('job_title_kaggle', 'N/A')}: Segmentation returned no sections. Skipping detailed parsing.")
        parsed_data_from_nlp = {}
    else:
        parsed_data_from_nlp = parse_jd_sections(segmented_sections) 


    final_jd = {}
    # Job Title: Prefer parser's output, fallback to Kaggle's direct 'job_title_kaggle'
    final_jd['job_title'] = parsed_data_from_nlp.get('job_title') if parsed_data_from_nlp.get('job_title') else entry['job_title_kaggle']
    
    # Skills: From your parser's 'skills' key
    final_jd['skills'] = parsed_data_from_nlp.get('skills', []) 
    
    # Minimum Years Experience:
    # Your parser puts this in 'minimum_years_experience'. Fallback to Kaggle pre-parsed.
    parsed_experience_nlp = parsed_data_from_nlp.get('minimum_years_experience')
    if parsed_experience_nlp is not None:
        final_jd['minimum_years_experience'] = parsed_experience_nlp
    else:
        final_jd['minimum_years_experience'] = entry['min_years_from_kaggle_experience_col']

    # Required Education Level: From your parser's 'required_education_level' key (numeric code)
    final_jd['required_education_level'] = parsed_data_from_nlp.get('required_education_level')

    # Responsibilities, Qualifications, Preferred Qualifications: From your parser
    final_jd['responsibilities'] = parsed_data_from_nlp.get('responsibilities', [])
    final_jd['qualifications'] = parsed_data_from_nlp.get('qualifications', [])
    final_jd['preferred_qualifications'] = parsed_data_from_nlp.get('preferred_qualifications', [])
    
    # Company Name and Location from parser if found, else keep from Kaggle
    final_jd['company_name'] = parsed_data_from_nlp.get('company_name') if parsed_data_from_nlp.get('company_name') else entry['company_name_kaggle']
    final_jd['location'] = parsed_data_from_nlp.get('location') if parsed_data_from_nlp.get('location') else entry['location_kaggle']


    # Add all other useful fields from the Kaggle data (stored in 'entry')
    for key, value in entry.items():
        if key not in final_jd and key != 'text_to_parse':
            final_jd[key] = value
            
    all_final_jds_for_matcher.append(final_jd)
# --- End of the loop processing each job entry ---

logging.info(f"\nFinished NLP parsing. {len(all_final_jds_for_matcher)} job descriptions are structured.")

#JDs to a JSON file
output_filename = 'parsed_kaggle_jobs_sample.json'
try:
    with open(output_filename, 'w', encoding='utf-8') as f:
        # Using default=str to handle any non-serializable types like datetime if they sneak in
        json.dump(all_final_jds_for_matcher, f, ensure_ascii=False, indent=4, default=str)
    logging.info(f"Successfully saved {len(all_final_jds_for_matcher)} parsed JDs to {output_filename}")
except Exception as e:
    logging.error(f"Error saving to JSON: {e}")

#To inspect the first processed entry
if all_final_jds_for_matcher:
    logging.info("\nExample of the first fully processed job entry (for matcher):")
    import pprint 
    logging.info(pprint.pformat(all_final_jds_for_matcher[0]))
   
  