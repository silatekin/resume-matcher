import re
import spacy
import json
from collections import defaultdict
from datetime import datetime
from spacy.matcher import PhraseMatcher
from dateutil.parser import parse as parse_datetime
from dateutil.relativedelta import relativedelta
import logging

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


def load_skills(skill_file="data/skills.json"):
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
    "skills": r"^\s*(skills|technical\s*skills|technical\s*proficiency)\s*[:\n]",
    "education": r"^\s*(education|academic\s*background)\s*[:\n]",
    "experience": r"^\s*(experience|work\s*experience|employment\s*history)\s*[:\n]",
}

def segment_resume(text):
    if not text:
        return {}
    
    sections = {"header": ""}
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
        for key,pattern in compiled_patterns.items():
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

    #Remove if there are empty sections
    sections = {k: v for k, v in sections.items() if v}
    logging.info(f"Segmented resume into sections: {list(sections.keys())}")
    return sections 


def parse_date(date_string):
    if not date_string or not isinstance(date_string,str):
        return None
    
    date_string = date_string.strip()

    if date_string.lower() in ["present","current","now","today","til date"]:
        return datetime.now()
    try:
        return parse_datetime(date_string, default=datetime(1,1,1), fuzzy=False)
    except (ValueError, OverflowError):
        pass

    patterns = [
        r"(\d{4})",                 # Matches Year only (e.g., "2020")
        r"(\w+)\s+(\d{4})",         # Month Name + Year ("May 2021")
        r"(\d{1,2})/(\d{4})",       # MM/YYYY (e.g., "05/2022")
        r"(\d{1,2})-(\d{4})",       # MM-YYYY (e.g., "05-2022")
    ]

    #---Plan B(if try block fails)
    for pattern in patterns:
        match = re.search(pattern,date_string)
        if match:
            try:
                if len(match.groups()) == 1: #only year matched(pattern 1)
                    return datetime(int(match.group(1)),1,1) #assume Jan 1st
                elif len(match.groups()) == 2: #Month/Year MM/YYYY matched
                    month_str = match.group(1)
                    year_str = match.group(2)
                    try:
                        month = int(month_str)
                    except ValueError: #month is not a number ie May
                        # Try parsing the month name using dateutil again
                        try:
                            month_dt = parse_date(month_str,default=datetime(1, 1, 1))
                            month = month_dt.month #Gets the month number
                        except ValueError:
                            continue # Invalid month name, try next regex pattern
                    #Construct date assuming 1st day
                    return datetime(int(year_str), month, 1)
            except (ValueError, OverflowError):
                # Invalid number (e.g., year 99999, month 15)
                continue

    logging.warning(f"Could not parse date string: '{date_string}'")
    return None 


EDUCATION_LEVELS = {
    "phd": 5, "doctorate": 5,
    "master": 4, "masters": 4, "msc": 4, "mba": 4, "meng": 4, "ma": 4, "ms": 4,
    "bachelor": 3, "bachelors": 3, "bsc": 3, "beng": 3, "ba": 3, "bs": 3,
    "associate": 2, "associates": 2,
    "college": 1, # Ambiguous, rank low
    "high school": 0, "ged": 0
}

def get_education_level(text):
    highest_level = -1
    if not text:
        return highest_level
    
    text_lower = text.lower()

    for keyword,level in EDUCATION_LEVELS.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            # If found, update highest_level to be the max of current and new level
            highest_level = max(highest_level, level)

    logging.info(f"Determined highest education level found in text: {highest_level}")
    return highest_level


def parse_resume_sections(sections):

    parsed_resume = {
                "skills":[],
                "education_details":[],
                "contact_info":{},
                "experience":[],
                "total_years_experience":0.0,
                "education_level": -1,
                "raw_entities": defaultdict(list) #Storing all raw NER entities if needed later
    }

    #-------Skill Extraction--------
    if "skills" in sections:
        skills_text = sections["skills"]
        skills_doc = nlp(skills_text)
        found_skills = set() 

        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        patterns = [nlp(skill) for skill in tech_skills]
        matcher.add("TECH_SKILLS",patterns)
        matches = matcher(skills_doc)

        matched_indices = set() # store token indices
        for match_id,start,end in matches:
            span = skills_doc[start:end] 
            found_skills.add(span.text.strip())
            for i in range(start, end):
                matched_indices.add(i)

        # Token matching for single-word skills but only if the token wasn't already part of a phrase match
        for token in skills_doc:
            if token.i not in matched_indices: 
                if token.lemma_.lower() in tech_skills_set:
                     # avoiding adding very short words unless specific known skills
                     if len(token.lemma_) > 1 or token.lemma_.lower() in ['c', 'r', 'go']:
                        found_skills.add(token.lemma_.lower()) # Adding the base form


        parsed_resume["skills"] = sorted(list(found_skills))
        logging.info(f"Extracted {len(parsed_resume['skills'])} unique skills.")
    

    #-------Education Extraction--------
    highest_edu_level_found = -1
    if "education" in sections:
        education_text = sections["education"]
        highest_edu_level_found = get_education_level(education_text)
        parsed_resume["education_level"] = highest_edu_level_found 

        education_doc = nlp(education_text)
        for sent in education_doc.sents:
            degree_mention = None
            institution_mention = None
            date_mention = None

            sent_lower = sent.text.lower()

            for keyword,level in EDUCATION_LEVELS.items():
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern,sent_lower):
                    degree_mention = keyword
                    break
            
            for ent in sent.ents:
                #to simplify we say grab the first one you see and ignore the others for institution and date
                if ent.label_ == "ORG" and not institution_mention:
                    institution_mention = ent.text
                elif ent.label_ == "DATE" and not date_mention:
                    date_mention = ent.text
            
            
            if degree_mention or institution_mention or date_mention:
                parsed_resume["education_details"].append({
                   "degree_mention": degree_mention,
                    "institution_mention": institution_mention,
                    "date_mention": date_mention,
                    "text": sent.text.strip() 
                })

        logging.info(f"Extracted {len(parsed_resume['education_details'])} education details. Highest level: {highest_edu_level_found}")

    
    #-------Experience Extraction--------
    total_experience_duration_days = 0
    extracted_companies = set()
    experience_text = sections.get("experience", "")

    if experience_text: 
        logging.info("Parsing experience from 'experience' section.")

        current_role = {}
        potential_title_lines = []

        #we are processing line by line not sentence by sentence bc spacy keeps making mistakes while separating sentences
        for line in experience_text.splitlines():
            sent_text = line.strip()
            if not sent_text: continue
            print(f"\n--- Processing Experience Sentence ---")
            print(f"SENTENCE: '{sent_text}'")

            # we will look for the DATE RANGES first
            date_range_pattern =  r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{4}|\d{1,2}/\d{4})\s*(?:-|–|to|until)\s*(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{4}|\d{1,2}/\d{4}|Present|Current|Now)\b"

            date_match = re.search(date_range_pattern,sent_text,re.IGNORECASE)
            print(f"DATE MATCH FOUND: {bool(date_match)}")

            start_date_obj = None
            end_date_obj = None
            company_name = None
            job_title = None

            if date_match:              
                start_date_str = date_match.group(1)
                end_date_str = date_match.group(2)

                start_date_obj = parse_date(start_date_str)
                end_date_obj = parse_date(end_date_str)

                #if dates are parsed, then we will try to find company title
                if start_date_obj and end_date_obj:
                    for ent in nlp(sent_text).ents:
                        if ent.label_ == "ORG":
                            company_name = ent.text.strip()
                            extracted_companies.add(company_name)
                            break
                    if company_name and job_title is None: # Check if company was found and title is still missing
                        try:
                            # Find where the company name starts in the sentence
                            company_start_index = sent_text.find(company_name)
                            # Check if company name was found and isn't at the very beginning
                            if company_start_index != -1: #it returns -1 if not found
                            # Extract the text before the company name
                                text_before_company = sent_text[:company_start_index].strip()
                            # Remove common trailing separators (like comma or pipe) before the company
                                text_before_company = re.sub(r'[,|]\s*$', '', text_before_company).strip()
                            # Basic check: Is the remaining text non-empty and seem capitalized?
                                if text_before_company and text_before_company[0].isupper():
                                    job_title = text_before_company # Assign this as the guessed job title
                                    print(f"--> Guessed title from same line: '{job_title}'") # Debug print
                        except Exception as e:
                            # Log if something goes wrong during guessing
                            logging.warning(f"Error guessing title from same line: {e}")    
                    
                    
                    if potential_title_lines and job_title is None:
                        title_line = potential_title_lines[-1]
                        title_doc = nlp(title_line)
                        for chunk in title_doc.noun_chunks:
                            if chunk.text[0].isupper():
                                job_title = chunk.text
                                break
                        if not job_title and title_doc:
                            #if no chunk worked then we'll use whole line as title guess
                            job_title = title_doc.text

                    if current_role:
                            #if we have this then this means that role ended, now we calculate its duration          
                            prev_start = current_role.get("start_date")
                            prev_end = current_role.get("end_date")
                            if prev_end and prev_start:
                                try:
                                    duration = relativedelta(prev_end,prev_start)
                                    total_experience_duration_days += (duration.years * 365.25) + (duration.months * 30.4) + duration.days
                                except TypeError:
                                    logging.warning(f"Could not calculate duration for role: {current_role.get('job_title')}")
                            
                            print(f"===> APPENDING final role: {current_role}")
                            parsed_resume["experience"].append(current_role)

                    
                    description_from_date_line = ""

                    try:
                        date_end_index = date_match.end() # Get end position of the date range pattern
                        #Check if there is actually any text *after* the date pattern on this line.
                        # Is the end index of the date match *before* the total length of the line?
                        if date_end_index < len(sent_text):
                            potential_description = sent_text[date_end_index:].strip()
                            # This regex removes one or more hyphens, closing parentheses, asterisks,
                            # bullets (•·), or whitespace characters IF they appear right at the START (^)
                            # of the potential_description we just extracted.
                            potential_description = re.sub(r'^[-)*\u2022•·\s]+', '', potential_description).strip()
                            if potential_description:
                                description_from_date_line = potential_description
                                print(f"--> Found description on same line: '{description_from_date_line[:50]}...'")
                    except Exception as e:
                        logging.warning(f"Error extracting description from date line: {e}")


                    current_role = {
                        "job_title":job_title,
                        "company":company_name,
                        "start_date":start_date_obj,
                        "end_date":end_date_obj,
                        "description": description_from_date_line
                    }  
                    potential_title_lines = []
            
            #sentence does not contain a date range
            else:
                #we will guess if it is a title/company line
                is_potential_title = False
                if len(sent_text.split()) < 7 and any(word[0].isupper() for word in sent_text.split() if len(word)>1):
                    is_potential_title = True

                    for ent in nlp(sent_text).ents:
                        if ent.label_ == "ORG":
                            extracted_companies.add(ent.text.strip())
                            # If we are building a role that's missing a company, maybe fill it?
                            #if current_role and not current_role.get("company"):
                            #    current_role["company"] = ent.text
                            is_potential_title = False
                            break


                if is_potential_title:
                    potential_title_lines.append(sent_text)
                
                print(f"IS POTENTIAL TITLE GUESS: {is_potential_title}")

                if not is_potential_title and current_role:
                    print(f"APPENDING TO DESCRIPTION for role: {current_role.get('job_title') or current_role.get('company')}") # See what's being appended
                    # This is your existing append logic, ensure the key is "description" (no colon)
                    current_role["description"] = (current_role.get("description", "") + "\n" + sent_text).strip()
                    print(f"  New Description: '{current_role['description'][:50]}...'") # Print part of the updated description

                elif is_potential_title:
                    print(f"ADDING TO POTENTIAL TITLE LINES: '{sent_text}'") # See if it's treated as a title line
                elif not current_role:
                    print("SKIPPING (No current role established yet)")

        if current_role:
            print(f"\n--- Finalizing Last Role ---")
            print(f"LAST ROLE DETAILS: {current_role}")
            last_start = current_role.get("start_date")
            last_end = current_role.get("end_date")

            if last_start and last_end:
                try:
                    duration = relativedelta(last_end, last_start)
                    total_experience_duration_days += (duration.years * 365.25) + (duration.months * 30.4) + duration.days
                except TypeError:
                     logging.warning(f"Could not calculate duration for last role: {current_role.get('job_title')}")
            
            print(f"===> APPENDING previous role: {current_role}")
            parsed_resume["experience"].append(current_role)

        parsed_resume["total_years_experience"] = round(total_experience_duration_days / 365.25, 1)
        logging.info(f"Extracted {len(parsed_resume['experience'])} experience entries. Total calculated years: {parsed_resume['total_years_experience']}")


    text_for_contacts = sections.get("header", "")
    if not text_for_contacts: # Fallback to combined text
         text_for_contacts = "\n".join(sections.values())

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'

    emails = re.findall(email_pattern, text_for_contacts)
    
    if emails:
        parsed_resume["contact_info"]["emails"] = list(set(emails))
        logging.info(f"Found emails: {parsed_resume['contact_info']['emails']}")
    
    phones_found = []
    # Use finditer to get match objects
    for match in re.finditer(phone_pattern, text_for_contacts):
        full_match = match.group(0) # Get the whole matched string
        cleaned_phone = re.sub(r'[-.\s()]', '', full_match) # Clean it
        if cleaned_phone: # Avoid adding empty strings if cleaning fails unexpectedly
            phones_found.append(cleaned_phone)
    
    if phones_found:
        parsed_resume["contact_info"]["phones"] = list(set(phones_found)) # Keep unique
        logging.info(f"Found phones: {parsed_resume['contact_info']['phones']}")


    # --- Final Cleanup ---
    # Deduplicate companies extracted from experience
    parsed_resume["companies"] = sorted(list(extracted_companies))

    return parsed_resume
        
      
# --- Function to Save JSON ---
def save_to_json(data, output_file="output.json"):
    """Saves data to a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, default=str)
        logging.info(f"Parsed data successfully saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving data to JSON file {output_file}: {e}")


if __name__ == "__main__":
    resume_file_path = "data/resumes/resume_01.txt"
    output_json_path = "parsed_resume_output.json"
    skill_list_path = "data/skills.json"

    import os
    # --- Ensure skills file exists FIRST ---
    if not os.path.exists(skill_list_path):
        logging.warning(f"Skill file '{skill_list_path}' not found. Creating basic example.")
        example_skills = ["python", "java", "sql", "javascript", "react", "angular", "node.js",
                          "project management", "agile", "scrum", "data analysis", "machine learning",
                          "communication", "teamwork", "leadership", "html", "css", "django", # Added django etc.
                          "spring boot", "git", "docker", "aws", "jenkins"]
        try:
            os.makedirs(os.path.dirname(skill_list_path), exist_ok=True)
            with open(skill_list_path, 'w', encoding='utf-8') as sf:
                json.dump(example_skills, sf, indent=4)
        except Exception as e:
            logging.error(f"Could not create example skill file: {e}")

    # --- NOW load skills ---
    tech_skills = load_skills(skill_list_path) # Reload skills AFTER potential creation
    tech_skills_set = set(tech_skills)
    if not tech_skills:
         logging.error("Failed to load skills even after check/creation. Exiting.")
         exit() # Or handle appropriately

    # --- Ensure resume file exists ---
    # (Your existing code for creating example resume)
    if not os.path.exists(resume_file_path):
         # ... (rest of your example resume creation code) ...
         pass # Make sure this block doesn't overwrite your actual resume_01.txt if it exists

    # --- Run the Parsing Pipeline ---
    logging.info("Starting resume parsing process...")
    resume_text = read_text_file(resume_file_path)

    if resume_text:
        cleaned_text = clean_text(resume_text)
        sections = segment_resume(cleaned_text)
        # --->>> ADD PRINT HERE <<<---
        print("--- SEGMENTED SECTIONS ---")
        print(sections)
        print("-" * 25)

        parsed_data = parse_resume_sections(sections) # Pass the loaded nlp object if needed

        print("\n--- Parsed Resume Data ---")
        print(json.dumps(parsed_data, indent=4, default=str))

        save_to_json(parsed_data, output_json_path)
    else:
        logging.error("Could not read resume file. Exiting.")



