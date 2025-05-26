import re
import spacy
import json
from collections import defaultdict
from datetime import datetime
from spacy.matcher import PhraseMatcher
from dateutil.parser import parse as parse_datetime
from dateutil.relativedelta import relativedelta
import logging
import pprint
import os

try:
    nlp = spacy.load("en_core_web_md")
    logging.info("Model loaded succesfully.")
except OSError:
    logging.error("Spacy model not found.")

def read_text_file(file_path):
    try:
        with open(file_path,'r',encoding='utf-8') as file:
            text = file.read()
        logging.info(f"Succesfully read file: {file_path}")
        return text
    except FileNotFoundError:
        logging.error(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        logging.error(f"Error reading file {file_path}:{e}")
        return None


def clean_text(text):
    text = text.strip()
    return text


def load_skills(skill_file=None):
    if skill_file is None:  
        script_dir = os.path.dirname(os.path.abspath(__file__)) 
        skill_file = os.path.join(script_dir, 'tests', 'data', 'skills.json') 
    
    try:
        with open(skill_file,"r",encoding="utf-8") as f:
            skills_data = json.load(f)

            valid_skills = [str(skill).lower()
                            for skill in skills_data 
                            if isinstance(skill,str)]
            logging.info(f"Loaded {len(valid_skills)} skills from {skill_file}")
            return valid_skills
    except FileNotFoundError:
        logging.error(f"Skill file not found.")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from skill file.")
        return []
    except Exception as e:
        logging.error("Error loading skills.")
        return []

tech_skills = load_skills()
tech_skills_set = set(tech_skills)

SECTION_HEADERS = {
    "about": r"(?i)^\s*(about\s*us|about\s*the\s*company|who\s*we\s*are)\s*[:]?\s*$",
    "responsibilities": r"(?i)^\s*(responsibilities|what\s*you['’]?ll\s*do|what\s*you\s*will\s*be\s*doing|duties|the\s*role\s*is|role\s*summary|job\s*responsibilities|key\s*responsibilities|day-to-day|your\s*impact)\s*[:]?\s*$",
    "qualifications": r"(?i)^\s*(qualifications|requirements|minimum\s*qualifications|basic\s*qualifications|required\s*skills|key\s*skills|what\s*we['’]?re\s*looking\s*for|who\s*you\s*are|ideal\s*candidate|your\s*profile|must-have)\s*[:]?\s*$",
    "preferred": r"(?i)^\s*(preferred\s*qualifications|nice\s*to\s*have|bonus\s*points|desired\s*skills|additional\s*qualifications|good\s*to\s*have)\s*[:]?\s*",
    "skills": r"(?i)^\s*(skills|technical\s*skills|technical\s*proficiency|tools|technologies|stack)\s*[:]?\s*$",
    "experience": r"(?i)^\s*(experience|work\s*experience|professional\s*experience|employment\s*history|required\s*experience)\s*[:]?\s*$",
    "education": r"(?i)^\s*(education|academic\s*background|educational\s*requirements|education\s*requirements)\s*[:]?\s*$",
    "location": r"(?i)^\s*(location|where\s*you['’]?ll\s*work)\s*[:]?\s*",
    "compensation": r"(?i)^\s*(compensation|salary|pay|benefits|perks|what\s*we\s*offer)\s*[:]?\s*", # Removed trailing $ for more flexibility
}

EDUCATION_LEVELS = {
    "phd": 5, "doctorate": 5,
    "master": 4, "masters": 4, "msc": 4, "mba": 4, "meng": 4, "ma": 4, "ms": 4,
    "bachelor": 3, "bachelors": 3, "bsc": 3, "beng": 3, "ba": 3, "bs": 3,
    "associate": 2, "associates": 2,
    "college": 1, 
    "high school": 0, "ged": 0
}

def segment_jd(text):
    if not text:
        return {}
    
    sections = {"header":""}
    current_section_key = "header"
    lines = text.splitlines()
    compiled_patterns = {}

    for key,pattern in SECTION_HEADERS.items():
        try:
            compiled_patterns[key] = re.compile(pattern,re.IGNORECASE|re.MULTILINE)
        except re.error as e:
            logging.error(f"Regex error in pattern for '{key}': {pattern} - {e}")
            return sections
        

    current_section_content = []

    for line in lines:
        print(f"Segmenter checking line: '{line}'")
        matched_key = None
        for key, pattern in compiled_patterns.items():
            if pattern.match(line):
                print(f"  ---> MATCHED {key}!")
                matched_key = key
                break
        
        if matched_key:
            if current_section_content:
                sections[current_section_key] = "\n".join(current_section_content).strip()

            current_section_key = matched_key
            current_section_content = [line]

        else:
            if line.strip():
                current_section_content.append(line)
    

    if current_section_content: 
        sections[current_section_key] = "\n".join(current_section_content).strip()

    sections = {k: v for k, v in sections.items() if v}
    logging.info(f"Segmented resume into sections: {list(sections.keys())}")
    return sections 


def parse_jd_sections(sections):
    parsed_jd = {
        "job_title":None,
        "company_name":None,
        "location":None,
        "about": None,
        "responsibilities":[],
        "qualifications":[],
        "preferred_qualifications":[],
        "skills":[],
        "education":[],
        "compensation":[],
        "minimum_years_experience": None 
    }

    # ---Parsing logic---
    # Extract job title, company, location
    if "header" in sections:
        header_text = sections.get("header","")
        if header_text:
            header_doc = nlp(header_text)

            logging.info(f"Header Entities: {[(ent.text,ent.label_) for ent in header_doc.ents]}")

            for ent in header_doc.ents:
                if ent.label_ == "ORG" and parsed_jd["company_name"] is None:
                    parsed_jd["company_name"] = ent.text.strip()
                    logging.info(f"Found potential company: {ent.text}")
                    break #stop after first ORG

            
            for ent in header_doc.ents:
                if ent.label_ in ["GPE","LOC"] and parsed_jd["location"] is None:
                    parsed_jd["location"] = ent.text.strip()
                    logging.info("Found potential location in header: {ent.text}")
                    break

            
            if parsed_jd["job_title"] is None:
                prefix_pattern = r"(?i)^\s*(job\s*title|position|role)\s*[:]?\s*"

                header_lines = header_text.splitlines()
                for i, line in enumerate(header_lines):
                    cleaned_title = line.strip()

                    title_without_prefix = re.sub(prefix_pattern,"",cleaned_title)

                    if title_without_prefix != cleaned_title or (i==0 and title_without_prefix):
                        if title_without_prefix and title_without_prefix != parsed_jd["company_name"]:
                            parsed_jd["job_title"] = title_without_prefix
                            logging.info(f"Extracted job title: {title_without_prefix}")
                            break

    # To refine location
    if "location" in sections:
        location_text = sections.get("location","").strip()
        location_text_cleaned_block = re.sub(r"(?i)^\s*location\s*[:]?\s*", "", location_text).strip()

        if location_text_cleaned_block:
            location_lines = location_text_cleaned_block.splitlines()
            if location_lines:
                first_line = location_lines[0].strip()

                if first_line:
                    logging.info(f"Overriding/setting location from dedicated section: {first_line}")
                    parsed_jd["location"] = first_line
                else:
                    logging.info("Location section found, but first line empty after cleaning.")
            else:
                 logging.info("Location section found, but text empty after splitting lines.")

        

    # 3. Process sections.get('responsibilities') - split by lines/bullets
    if "responsibilities" in sections:
        responsibilites_text = sections["responsibilities"]
        if responsibilites_text:
            lines = responsibilites_text.splitlines()
            marker_pattern = r"^\s*[-*•]\s*"
            header_pattern = SECTION_HEADERS['responsibilities'] 

            cleaned_responsibilities = []

            for line in lines:
                stripped_line = line.strip()
                if stripped_line and not re.match(header_pattern,line):
                    cleaned_line = re.sub(marker_pattern,"",stripped_line)
                    if cleaned_line:
                        cleaned_responsibilities.append(cleaned_line)

            if cleaned_responsibilities:
                parsed_jd["responsibilities"] = cleaned_responsibilities
                logging.info(f"Extracted {len(cleaned_responsibilities)} responsibility points.")

            else:
                logging.info("Found responsibility section but no valid points extracted.")

        else:
            logging.info("Responsibility section found but text is empty.")

            
    # 4. Process sections.get('qualifications') 
    # Extracting Minimum Years of Experience 
    if "qualifications" in sections:
        qualifications_text = sections.get("qualifications", "")

        if qualifications_text:
            qualification_lines = qualifications_text.splitlines()
            marker_pattern = r"^\s*[-*•]\s*"
            year_pattern = r"(\d+)\+?\s*\byears?\b" 
            header_pattern = SECTION_HEADERS['qualifications']
            
            cleaned_qualifications_list = []
            first_years_found = None

            print("--- Finding Experience Years ---")
            
            for line in qualification_lines:
                stripped_line = line.strip()
                
                if not stripped_line or re.match(header_pattern, line):  
                    continue

                cleaned_line = re.sub(marker_pattern,"",stripped_line).strip()

                if cleaned_line:
                    cleaned_qualifications_list.append(cleaned_line)


                if first_years_found is None:
                    match = re.search(year_pattern,cleaned_line,re.IGNORECASE)
                    if match:
                        years_number_str = match.group(1)
                        print(f"Found pattern in: '{line}' -> Extracted years: {years_number_str}")
                        try:
                            current_years = int(years_number_str)
                            first_years_found = current_years     
                        except ValueError:   
                            logging.warning(f"Could not convert extracted years '{years_number_str}' to int.")

            if cleaned_qualifications_list:
                parsed_jd["qualifications"] = cleaned_qualifications_list
                logging.info(f"Extracted {len(cleaned_qualifications_list)} qualification points.")

            if first_years_found is not None:
                parsed_jd["minimum_years_experience"] = first_years_found
                logging.info(f"Stored first extracted years experience: {first_years_found}")
            
            else:
                logging.info("No year pattern found in qualifications.")


    # 5. Process sections.get('preferred') 
    if "preferred" in sections:
        preferred_qualifications_text = sections.get("preferred","")

        if preferred_qualifications_text:
            preferred_qualifications_lines = preferred_qualifications_text.splitlines()
            marker_pattern = r"^\s*[-*•]\s*"
            header_pattern = SECTION_HEADERS['preferred']

            preferred_qualifications_list = []

            for line in preferred_qualifications_lines:
                stripped_line = line.strip()
                
                if not stripped_line or re.match(header_pattern, line):  
                    continue

                cleaned_line = re.sub(marker_pattern,"",stripped_line).strip()

                if cleaned_line:
                    preferred_qualifications_list.append(cleaned_line)

            if preferred_qualifications_list:
                parsed_jd["preferred_qualifications"] = preferred_qualifications_list
                logging.info(f"Extracted {len(preferred_qualifications_list)} preferred qualification points.")
            
            else:
                logging.info("Preferred qualifications section found, but no points extracted after cleaning.")

    # 6. Process sections.get('skills')
    if "skills" in sections or "qualifications" in sections:
        skill_sources_keys = ["skills", "qualifications"]
        text_pieces = [sections.get(key, "") for key in skill_sources_keys]

        skill_search_text = "\n".join(text_pieces).strip()

        if skill_search_text:
            logging.info(f"Text from {skill_sources_keys} for skill extraction.")

            skills_doc = nlp(skill_search_text)
            found_skills = set()

            matcher = PhraseMatcher(nlp.vocab,attr="LOWER")
            pattern = [nlp(skill) for skill in tech_skills]
            matcher.add("TECH_SKILLS", pattern)
            matches = matcher(skills_doc)

            matched_indices = set()
            for match_id,start,end in matches:
                span = skills_doc[start:end]
                found_skills.add(span.text.strip())
                for i in range(start,end):
                    matched_indices.add(i)
            
            for token in skills_doc:
                if token.i not in matched_indices:
                    if token.lemma_.lower() in tech_skills_set:
                        found_skills.add(token.lemma_.lower())
            
            unique_skills = list(set(found_skills))

            if unique_skills:
                parsed_jd["skills"] = unique_skills
                logging.info(f"Extracted {len(unique_skills)} unique skills.")
            else:
                logging.info("No skills extracted from relevant sections.")
        else:
            logging.info("No text found in 'skills' or 'qualifications' sections to search for skills.")

    # 7. Process sections.get('education')
    if "education" in sections:
        education_text = sections["education"]
        if education_text:
            lines = education_text.splitlines()
            marker_pattern = r"^\s*[-*•]\s*"
            header_pattern = SECTION_HEADERS['education'] 

            education_list=[]

            for line in lines:
                stripped_line = line.strip()
                if stripped_line and not re.match(header_pattern,line):
                    cleaned_line = re.sub(marker_pattern,"",stripped_line).strip()
                    if cleaned_line:
                        education_list.append(cleaned_line)

            if education_list:
                parsed_jd["education"] = education_list
                logging.info(f"Extracted education info: {len(education_list)}")

            else:
                logging.info("Found education section but no valid points extracted.")

        else:
            logging.info("Education section found but text is empty.")
        
        
        logging.info("--- Determining LOWEST Education Level Mentioned ---")
        lowest_level_found = None
        text_to_search = (sections.get('education', '') + "\n" + sections.get('qualifications', '')).lower()

        if text_to_search.strip():
            for keyword, level in sorted(EDUCATION_LEVELS.items(), key=lambda item: item[1]):
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_to_search):
                    lowest_level_found = level
                    logging.info(f"Found lowest level mention: {keyword} (Level {level})")
                    break 

        parsed_jd['required_education_level'] = lowest_level_found 
        logging.info(f"Assigned lowest education level mentioned: {lowest_level_found}")


    # 8. Process sections.get('about')
    if "about" in sections:
        about_text = sections.get("about", "") 

        if about_text:
            header_pattern_string = SECTION_HEADERS["about"]
            removal_pattern = header_pattern_string.rstrip('$') + r'\n?'
            cleaned_about_text = re.sub(removal_pattern, "", about_text, count=1).strip() 

            if cleaned_about_text:
               parsed_jd["about"] = cleaned_about_text
               logging.info(f"Extracted about section text.")
            
            else: 
                logging.info("Found about section but text was empty after cleaning header.")

        else:
            logging.info("About section found but text is empty.")
            

    # 9. Process sections.get('compensation')
    if "compensation" in sections:
        compensation_text = sections["compensation"]
        header_pattern = SECTION_HEADERS["compensation"]

        compensation_list = []

        if compensation_text:
            lines = compensation_text.splitlines()
            marker_pattern = r"^\s*[-*•]\s*"
            header_pattern = SECTION_HEADERS['compensation'] 

            for line in lines:
                stripped_line = line.strip()
                if stripped_line and not re.match(header_pattern,line):
                    cleaned_line = re.sub(marker_pattern,"",stripped_line).strip()
                    if cleaned_line:
                        compensation_list.append(cleaned_line)

            if compensation_list:
                parsed_jd["compensation"] = compensation_list
                logging.info(f"Extracted compensation info: {len(compensation_list)}")

            else:
                logging.info("Found compensation section but no valid points extracted.")

        else:
            logging.info("Compensation section found but text is empty.")


    logging.info(f"Parsed JD sections. Found keys: {list(parsed_jd.keys())}")
    return parsed_jd


def parse_jd_file(filepath):
    """
    Parses a job description text file and returns a structured dictionary.
    This acts as the main entry point for parsing a single JD file.
    """
    logging.info(f"Starting parsing for JD file: {filepath}")
    try:
        raw_text = read_text_file(filepath)
        if raw_text is None:
            return None 

        raw_text = clean_text(raw_text) 

        sections = segment_jd(raw_text)
        if not sections:
             logging.warning(f"Segmentation returned no sections for {filepath}")
             return None 

        final_dictionary = parse_jd_sections(sections)

        logging.info(f"Finished parsing JD file: {filepath}")
        return final_dictionary

    except Exception as e:
        logging.error(f"An unexpected error occurred parsing JD file {filepath}: {e}", exc_info=True)
        return None 


def process_scraped_job_data(job_description_text, api_title=None, api_company=None, api_location=None, api_tags=None):
    """
    Processes a job description string and incorporates metadata from an API/scraped source.
    This function uses the other parsing functions (clean_text, segment_jd, parse_jd_sections)
    already defined in this file.
    """
    logging.info("Starting processing for a scraped job description with API metadata.")
    
    api_title_str = str(api_title) if api_title is not None else ""
    api_company_str = str(api_company) if api_company is not None else ""
    api_location_str = str(api_location) if api_location is not None else ""

    if not job_description_text:
        logging.warning("Received empty job description text. Cannot process.")
        # Return the basic structure with API data if available, or None
        if api_title_str or api_company_str or api_location_str: 
            return {
                "job_title": api_title_str,
                "company_name": api_company_str,
                "location": api_location_str,
                "about": None,
                "responsibilities": [],
                "qualifications": [],
                "preferred_qualifications": [],
                "skills": api_tags if api_tags else [],
                "education": [],
                "compensation": [],
                "minimum_years_experience": None,
                "required_education_level": None
            }
        return None

    cleaned_jd_text = clean_text(job_description_text)
    if not cleaned_jd_text:
        logging.warning("Cleaned job description text is empty. Cannot process further text analysis.")
        if api_title_str or api_company_str or api_location_str:
            return {
                "job_title": api_title_str,
                "company_name": api_company_str,
                "location": api_location_str,
                "about": None,
                "responsibilities": [],
                "qualifications": [],
                "preferred_qualifications": [],
                "skills": api_tags if api_tags else [],
                "education": [],
                "compensation": [],
                "minimum_years_experience": None,
                "required_education_level": None
            }
        return None

    sections = segment_jd(cleaned_jd_text) 
    parsed_data_from_text = parse_jd_sections(sections)

    if api_title_str: 
        parsed_title_from_text_str = str(parsed_data_from_text.get("job_title", "")) 

        if not parsed_data_from_text.get("job_title") or parsed_data_from_text.get("job_title") == 'N/A' or not parsed_title_from_text_str.strip():
            parsed_data_from_text["job_title"] = api_title_str
            logging.info(f"Using API job title: {api_title_str}")
        elif api_title_str.lower() != parsed_title_from_text_str.lower():
            logging.info(f"API title '{api_title_str}' differs from parsed title '{parsed_title_from_text_str}'. Prioritizing API title.")
            parsed_data_from_text["job_title"] = api_title_str

    if api_company_str: 
        parsed_company_from_text_str = str(parsed_data_from_text.get("company_name", ""))

        if not parsed_data_from_text.get("company_name") or parsed_data_from_text.get("company_name") == 'N/A' or not parsed_company_from_text_str.strip():
            parsed_data_from_text["company_name"] = api_company_str
            logging.info(f"Using API company name: {api_company_str}")
        elif api_company_str.lower() != parsed_company_from_text_str.lower():
            logging.info(f"API company '{api_company_str}' differs from parsed company '{parsed_company_from_text_str}'. Prioritizing API company.")
            parsed_data_from_text["company_name"] = api_company_str

    # Location
    if api_location_str: 
        parsed_location_from_text_str = str(parsed_data_from_text.get("location", ""))
        if not parsed_data_from_text.get("location") or parsed_data_from_text.get("location") == 'N/A' or not parsed_location_from_text_str.strip():
            parsed_data_from_text["location"] = api_location_str
            logging.info(f"Using API location: {api_location_str}")

    # Integrate API tags with skills found by the parser
    current_text_skills = set(skill.lower() for skill in parsed_data_from_text.get("skills", []))
    if api_tags: 
        for tag in api_tags:
            if isinstance(tag, str): 
                current_text_skills.add(tag.lower()) 
    parsed_data_from_text["skills"] = sorted(list(current_text_skills))
    if api_tags:
        logging.info(f"Merged API tags with extracted skills. Total unique skills: {len(parsed_data_from_text['skills'])}")
    
    logging.info("Finished processing scraped job data with API enhancements.")
    return parsed_data_from_text








"""

# ==================================================
#  TESTING BLOCK
# ==================================================
if __name__ == "__main__":

    logging.info("Starting JD Parsing Test...") 

    file_path = "tests/data/raw_jds/job_01.txt"

    example_jd_text = read_text_file(file_path)

    if example_jd_text: 
        cleaned_jd_text = clean_text(example_jd_text)

        # --- Run the segmentation function ---
        if cleaned_jd_text: # 
            print("\n--- Running Segmentation ---")
            segmented_data = segment_jd(cleaned_jd_text) 
            print("\n--- Segmentation Complete ---")

            print("\n--- Running Extraction ---")
            extracted_data = parse_jd_sections(segmented_data) 
            print("\n--- Extraction Complete ---") 

            print("\n--- Extracted Job Description Data ---") 
            pprint.pprint(extracted_data) 

        else:
            logging.error(f"Cleaned JD text from {file_path} is empty, cannot parse.")

    logging.info("JD Parsing Test Finished.")

    
"""