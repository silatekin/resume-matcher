import streamlit as st
# --- Page Configuration MUST be the first Streamlit command ---
st.set_page_config(layout="wide", page_title="Resume Matcher - RemoteOK", initial_sidebar_state="expanded")

import pandas as pd
import ast 
import os
import spacy
import logging

# --- Import your custom modules ---
try:
    from matcher import calculate_match_score
    logging.info("Successfully imported 'matcher.py'")
except ImportError:
    st.error("CRITICAL ERROR: Could not import 'matcher.py'. Ensure it's in the correct path.")
    logging.error("Could not import 'matcher.py'.")
    calculate_match_score = None 
except Exception as e:
    st.error(f"CRITICAL ERROR: Error importing 'matcher.py': {e}")
    logging.error(f"Error importing 'matcher.py': {e}")
    calculate_match_score = None

try:
    from resume_parser import (
        process_streamlit_file,
        load_skills as load_resume_parser_skills,
        SECTION_HEADERS_GLOBAL,
        EDUCATION_LEVELS_GLOBAL
    )
    logging.info("Successfully imported 'resume_parser.py'")
except ImportError:
    st.error("CRITICAL ERROR: Could not import 'resume_parser.py'. Ensure it's in the correct path.")
    logging.error("Could not import 'resume_parser.py'.")
    def process_streamlit_file(*args, **kwargs): return None
    def load_resume_parser_skills(*args, **kwargs): return [], set() 
    SECTION_HEADERS_GLOBAL, EDUCATION_LEVELS_GLOBAL = {}, {}
except Exception as e:
    st.error(f"CRITICAL ERROR: Error importing 'resume_parser.py': {e}")
    logging.error(f"Error importing 'resume_parser.py': {e}")
    def process_streamlit_file(*args, **kwargs): return None
    def load_resume_parser_skills(*args, **kwargs): return [], set()
    SECTION_HEADERS_GLOBAL, EDUCATION_LEVELS_GLOBAL = {}, {}


EDUCATION_DISPLAY_MAP = {val: key.replace('.', '').replace('_', ' ').title() for key, val in EDUCATION_LEVELS_GLOBAL.items()}

def get_education_text(level_code):
    return EDUCATION_DISPLAY_MAP.get(level_code, f"Code {level_code}" if isinstance(level_code, int) else "Unknown")


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
)
def get_nlp_model_for_page():
    try:
        model = spacy.load("en_core_web_md") 
        logging.info("FindCandidatesPage: spaCy NLP model 'en_core_web_md' loaded.")
        return model
    except OSError: # Specific error for model not found
        logging.error("FindCandidatesPage: spaCy model 'en_core_web_md' not found. Please run: python -m spacy download en_core_web_md")
        return None 
    except Exception as e: # Catch any other potential errors during spacy.load
        logging.error(f"FindCandidatesPage: An unexpected error occurred while loading spaCy model: {e}")
        return None


NLP_MODEL = get_nlp_model_for_page()

APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ROOT_DIR = os.path.dirname(APP_BASE_DIR) 
PARSED_JOBS_CSV_PATH = os.path.join(APP_ROOT_DIR, "remoteok_parsed_jds.csv") 
SKILLS_JSON_PATH_FOR_RESUME_PARSER = os.path.join(APP_BASE_DIR, "tests", "data", "skills.json")


# --- Cached Data Loading Functions ---
@st.cache_data(ttl=3600) 
def load_and_preprocess_parsed_jds(csv_filepath):
    logging.info(f"Attempting to load parsed JDs from: {csv_filepath}")
    try:
        df = pd.read_csv(csv_filepath)
        logging.info(f"Successfully loaded {len(df)} parsed JDs from {csv_filepath}")

        # Columns that might be stored as string representations of lists in the CSV
        list_like_columns = [
            'responsibilities', 'qualifications', 'preferred_qualifications',
            'skills', 'education', 'compensation', 
            'matching_resume_titles' # From matcher output, not directly in parsed_jd from parser
        ]

        for col in list_like_columns:
            if col in df.columns:
                # Check if the column needs conversion
                # Apply ast.literal_eval only to strings that look like lists/tuples/dicts
                def safe_literal_eval(val):
                    if pd.isna(val):
                        return [] 
                    if isinstance(val, (list, tuple, dict)):
                        return val
                    if isinstance(val, str):
                        # Check if it's a representation of a list/tuple/dict
                        if (val.startswith('[') and val.endswith(']')) or \
                           (val.startswith('(') and val.endswith(')')) or \
                           (val.startswith('{') and val.endswith('}')):
                            try:
                                return ast.literal_eval(val)
                            except (ValueError, SyntaxError, TypeError):
                                logging.warning(f"Could not parse string '{val}' in column '{col}' as a list/dict, returning as single-item list if non-empty.")
                                return [val] if val.strip() else [] # Fallback for malformed list strings
                        else: # It's a plain string, not a list representation
                            return [val] if val.strip() else [] # Treat as a single-item list
                    return [] # Default for other types or if conversion fails

                df[col] = df[col].apply(safe_literal_eval)
                logging.info(f"Processed column '{col}' for list conversion.")
            # else:
                # logging.warning(f"Expected list-like column '{col}' not found in DataFrame.")
        
        # Convert DataFrame to list of dictionaries
        job_list = df.to_dict(orient='records')
        logging.info(f"Converted DataFrame to {len(job_list)} job dictionaries.")
        return job_list
        
    except FileNotFoundError:
        st.error(f"ERROR: Parsed job descriptions file not found: {csv_filepath}. Please run scraper and parser scripts.")
        logging.error(f"Parsed job descriptions file not found at {csv_filepath}")
        return []
    except Exception as e:
        st.error(f"ERROR: Failed to load or process parsed JDs from {csv_filepath}: {e}")
        logging.error(f"Failed to load or process parsed JDs: {e}")
        return []

@st.cache_resource 
def get_nlp_model():
    try:
        model = spacy.load("en_core_web_md")
        logging.info("spaCy NLP model 'en_core_web_md' loaded successfully for the app.")
        return model
    except OSError:
        st.error("App Error: spaCy model 'en_core_web_md' not found. Please run: python -m spacy download en_core_web_md")
        logging.error("spaCy model 'en_core_web_md' not found.")
        return None 

@st.cache_data 
def get_skills_data_for_resume_parser_cached(skill_file_path=None):
    skill_list = load_resume_parser_skills(skill_file_path) 
    skill_set = set(skill_list) # load_resume_parser_skills should return a list
    logging.info(f"Loaded {len(skill_list)} skills for resume parser from '{skill_file_path}'.")
    return skill_list, skill_set

# --- Load Global Resources ---
NLP_MODEL = get_nlp_model()
TECH_SKILLS_LIST_APP, TECH_SKILLS_SET_APP = get_skills_data_for_resume_parser_cached(SKILLS_JSON_PATH_FOR_RESUME_PARSER)
ALL_PARSED_JOBS_FULL_LIST = load_and_preprocess_parsed_jds(PARSED_JOBS_CSV_PATH) # Load RemoteOK jobs

# --- Initialize Session State for Filters ---
if 'selected_locations' not in st.session_state:
    st.session_state.selected_locations = []
# Work type filter removed for now as RemoteOK data doesn't have a clean field for it.
# If you add it back, initialize st.session_state.selected_work_types = []

# --- Prepare Filter Options ---
unique_locations = []
if ALL_PARSED_JOBS_FULL_LIST:
    locations_set = set()
    for job in ALL_PARSED_JOBS_FULL_LIST:
        loc = job.get('location') # Use 'location' from RemoteOK data
        if loc and isinstance(loc, str) and loc.strip():
            locations_set.add(loc.strip())
    unique_locations = sorted(list(locations_set))

# --- Streamlit UI ---
st.title("🎯 Resume to Job Matcher (RemoteOK Data)")
st.write("Upload your resume (TXT, DOCX, PDF) to find suitable job openings from RemoteOK. Use the sidebar to filter jobs.")

with st.sidebar:
    st.header("🔍 Job Filters")
    if not ALL_PARSED_JOBS_FULL_LIST:
        st.caption("Job data not loaded, filters unavailable.")
    else:
        if unique_locations:
            st.session_state.selected_locations = st.multiselect(
                "Filter by Location:", options=unique_locations,
                default=st.session_state.selected_locations,
                help="Select one or more locations."
            )
        # Work type filter is removed. Add back if you have a way to get this data.
        
        if st.button("Clear All Filters", key="clear_filters_button_remoteok"):
            st.session_state.selected_locations = []
            # st.session_state.selected_work_types = [] # If re-added
            st.rerun()

# --- Apply Filters ---
jobs_to_display_and_match = ALL_PARSED_JOBS_FULL_LIST
if ALL_PARSED_JOBS_FULL_LIST:
    if st.session_state.selected_locations:
        selected_locs_normalized = {loc.strip().lower() for loc in st.session_state.selected_locations}
        jobs_to_display_and_match = [
            job for job in jobs_to_display_and_match 
            if job.get('location') and isinstance(job.get('location'), str) and \
               job.get('location').strip().lower() in selected_locs_normalized
        ]
        logging.info(f"After location filter, count: {len(jobs_to_display_and_match)}")
    # Add work type filter logic here if you re-implement it
logging.info(f"Final job count for matching after filters: {len(jobs_to_display_and_match)}")


# --- Resume Upload and Processing ---
critical_error_occurred = False
if NLP_MODEL is None:
    # Error already shown by get_nlp_model()
    critical_error_occurred = True

if not ALL_PARSED_JOBS_FULL_LIST and not critical_error_occurred: 
    st.warning(f"Job descriptions could not be loaded from '{PARSED_JOBS_CSV_PATH}'. Matching may be limited or unavailable.")

uploaded_file = st.file_uploader("Choose a resume file", type=['txt', 'docx', 'pdf'], key="resume_uploader_remoteok")

if uploaded_file is not None:
    st.markdown("---")
    st.write(f"Uploaded file: **{uploaded_file.name}** (Type: {uploaded_file.type})")

    if critical_error_occurred:
        st.error("Cannot proceed due to critical resource loading errors mentioned above.")
    elif calculate_match_score is None: 
        st.error("Job matcher component (calculate_match_score) is not available.")
    else:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            parsed_resume_data = process_streamlit_file( # From resume_parser.py
                uploaded_file, NLP_MODEL, TECH_SKILLS_LIST_APP, TECH_SKILLS_SET_APP,
                SECTION_HEADERS_GLOBAL, EDUCATION_LEVELS_GLOBAL
            )
            processing_successful = False 
            if parsed_resume_data and "error" not in parsed_resume_data:
                st.session_state.parsed_resume_data = parsed_resume_data 
                processing_successful = True
                logging.info(f"Resume '{uploaded_file.name}' processed successfully.")
            else: # Handle error from parser
                error_msg = "Parser returned no data or an unknown error occurred."
                if isinstance(parsed_resume_data, dict) and "error" in parsed_resume_data:
                    error_msg = parsed_resume_data["error"]
                elif parsed_resume_data is None:
                     error_msg = "Parser returned None."
                st.error(f"Failed to process the resume: {error_msg} Check logs for details.")
                logging.error(f"Failed to process resume: {uploaded_file.name} - {error_msg}")
                if 'parsed_resume_data' in st.session_state:
                    del st.session_state.parsed_resume_data
        
        if processing_successful and 'parsed_resume_data' in st.session_state:
            st.success("✅ Resume processed successfully!")
            data_to_display_resume = st.session_state.parsed_resume_data
            
            st.markdown("---")
            st.subheader("📄 Your Parsed Resume Information:")

            # --- DETAILED PARSED RESUME DISPLAY (FROM YOUR ORIGINAL APP) ---
            if "summary_text" in data_to_display_resume and data_to_display_resume["summary_text"]:
                with st.expander("**Summary**", expanded=False): 
                    st.markdown(data_to_display_resume["summary_text"])

            if "experience" in data_to_display_resume and data_to_display_resume["experience"]:
                st.write("**Work Experience:**")
                for i, experience_entry in enumerate(data_to_display_resume["experience"]):
                    title = experience_entry.get("job_title", "Role Not Specified")
                    company = experience_entry.get("company", "Company Not Specified")
                    expander_label = f"{title} at {company}" if title != "Role Not Specified" and company != "Company Not Specified" else title if title != "Role Not Specified" else f"Experience Entry {i+1}"
                    with st.expander(expander_label):
                        st.markdown(f"**Job Title:** {title}")
                        st.markdown(f"**Company:** {company}")
                        st.markdown(f"**Dates:** {experience_entry.get('start_date', 'N/A')} - {experience_entry.get('end_date', 'N/A')}")
                        description = experience_entry.get("description", "")
                        if description and str(description).strip():
                            st.markdown("**Description:**")
                            for desc_line in str(description).split('\n'):
                                st.markdown(f"- {desc_line.strip()}")
                        else:
                            st.markdown("**Description:** No description provided.")
            else:
                st.write("**Work Experience:** Not found or empty.")
            
            if "total_years_experience" in data_to_display_resume and isinstance(data_to_display_resume["total_years_experience"], (int, float)) and data_to_display_resume["total_years_experience"] >= 0:
                st.write(f"**Total Calculated Years of Experience:** {data_to_display_resume['total_years_experience']:.1f} years")

            if "companies" in data_to_display_resume and data_to_display_resume["companies"]:
                with st.expander("**Companies Mentioned in Experience**", expanded=False):
                    for company_name in data_to_display_resume["companies"]:
                        st.markdown(f"- {company_name}")
            
            if "contact_info" in data_to_display_resume and data_to_display_resume["contact_info"]:
                with st.expander("**Contact Information**", expanded=False):
                    contact = data_to_display_resume["contact_info"]
                    if contact.get("emails"): st.write(f"- Email(s): {', '.join(contact['emails'])}")
                    if contact.get("phones"): st.write(f"- Phone(s): {', '.join(contact['phones'])}")
            
            if "skills" in data_to_display_resume and data_to_display_resume["skills"]:
                with st.expander("**Skills** (from Resume)", expanded=True):
                    st.markdown(f"`{', '.join(data_to_display_resume['skills'])}`")

            if "education_details" in data_to_display_resume and data_to_display_resume["education_details"]:
                st.write("**Education:**")
                for i, edu_entry in enumerate(data_to_display_resume["education_details"]):
                    degree = edu_entry.get("degree_mention", "N/A")
                    institution = edu_entry.get("institution_mention", "N/A")
                    date = edu_entry.get("date_mention", "N/A")
                    display_degree = ' '.join(word.capitalize() for word in str(degree).split()) if degree != "N/A" else "N/A"
                    exp_title = f"{display_degree} at {institution}" if institution != "N/A" and institution else display_degree
                    if display_degree == "N/A" and (institution == "N/A" or not institution): exp_title = f"Education Entry {i+1}"
                    elif display_degree == "N/A": exp_title = f"Education at {institution}"
                    with st.expander(exp_title):
                        st.markdown(f"**Degree Phrase:** {degree}")
                        st.markdown(f"**Institution:** {institution}")
                        st.markdown(f"**Date:** {date}")
            
            if "education_level" in data_to_display_resume and data_to_display_resume["education_level"] != -1:
                st.write(f"**Highest Education Level (Parsed Code):** {get_education_text(data_to_display_resume['education_level'])}") # Use get_education_text
            
            if "raw_text_snippet" in data_to_display_resume and data_to_display_resume["raw_text_snippet"]:
                with st.expander("View Raw Extracted Text Snippet (from Resume)", expanded=False):
                    st.text_area("raw_resume_text_display",
                                 str(data_to_display_resume.get("raw_text_snippet", "")),
                                 height=150, disabled=True, label_visibility="collapsed")
            # --- END OF DETAILED PARSED RESUME DISPLAY ---

            st.markdown("---")
            st.subheader("📊 Job Matching Results (RemoteOK Data):")
            
            if not jobs_to_display_and_match and (st.session_state.selected_locations): # Only location filter active now
                st.info("No jobs match your current filter selections. Try adjusting the filters in the sidebar.")
            elif not jobs_to_display_and_match and not ALL_PARSED_JOBS_FULL_LIST: # No jobs loaded at all
                 st.warning("Job data is not loaded. Cannot perform matching.")
            elif jobs_to_display_and_match and data_to_display_resume:
                all_job_match_results = []
                
                spinner_text = f"Calculating job matches against {len(jobs_to_display_and_match)} RemoteOK jobs..."
                if len(jobs_to_display_and_match) != len(ALL_PARSED_JOBS_FULL_LIST):
                     spinner_text = (f"Calculating job matches against {len(jobs_to_display_and_match)} filtered RemoteOK jobs "
                                     f"(out of {len(ALL_PARSED_JOBS_FULL_LIST)} total)...")

                with st.spinner(spinner_text):
                    for parsed_jd_dict_from_csv in jobs_to_display_and_match: # This is a dict from the loaded CSV
                        # The parsed_jd_dict_from_csv already has the structure your matcher expects
                        # because it was created by your job_description_parser.py
                        match_details = calculate_match_score(data_to_display_resume, parsed_jd_dict_from_csv,NLP_MODEL)
                        
                        all_job_match_results.append({
                            "job_title": parsed_jd_dict_from_csv.get("job_title", "N/A"), 
                            "company": parsed_jd_dict_from_csv.get("company_name", "N/A"), # Use company_name
                            "location": parsed_jd_dict_from_csv.get("location", "N/A"),
                            "url": parsed_jd_dict_from_csv.get("original_url", "#"), # Use original_url
                            "date_posted": parsed_jd_dict_from_csv.get("date_posted", "N/A"),
                            "description_snippet": str(parsed_jd_dict_from_csv.get("description_text", ""))[:250] + "...",
                            "match_details": match_details,
                            "original_job_data": parsed_jd_dict_from_csv # Keep the full parsed JD for detailed display
                        })
                
                sorted_matches = sorted(all_job_match_results, key=lambda x: x['match_details'].get('score', 0), reverse=True)
                
                if sorted_matches:
                    st.write(f"Showing top matches from {len(jobs_to_display_and_match)} currently displayed RemoteOK jobs:")
                    
                    # Adjust slider max_value based on available sorted_matches
                    slider_max = max(1, min(20, len(sorted_matches)))
                    slider_default = min(5, slider_max) # Default to 5 or less if fewer matches
                    num_matches_to_show = st.slider(
                        "Number of top matches to display:", 
                        min_value=1, 
                        max_value=slider_max,
                        value=slider_default, 
                        key="matches_slider_remoteok"
                    )

                    for i, result_entry in enumerate(sorted_matches[:num_matches_to_show]):
                        job_title_display = result_entry["job_title"]
                        company_display = result_entry["company"]
                        details = result_entry["match_details"]
                        overall_score_percent = details.get('score', 0) * 100
                        expander_title = f"{i+1}. {job_title_display} at {company_display} - Overall Match: {overall_score_percent:.1f}%"
                        
                        job_details_dict = result_entry.get("original_job_data", {}) # Get the full parsed JD

                        with st.expander(expander_title, expanded=(i < 1)): # Expand first match by default
                            st.markdown(f"**Location:** {result_entry.get('location', 'N/A')} | **Posted:** {result_entry.get('date_posted', 'N/A')}")
                            st.markdown(f"**[View Full Job Listing on RemoteOK]({result_entry.get('url', '#')})**", unsafe_allow_html=True)
                            
                            st.markdown("---")
                            st.subheader("Job Details (from Parsed Description):")

                            # --- Display Parsed JD Sections ---
                            sections_to_display = {
                                "Responsibilities": job_details_dict.get("responsibilities", []),
                                "Qualifications": job_details_dict.get("qualifications", []),
                                "Preferred Qualifications": job_details_dict.get("preferred_qualifications", []),
                                "Skills (from JD text)": job_details_dict.get("skills", []), # This will show skills extracted by your parser from text + API tags
                                "Education (from JD)": job_details_dict.get("education", []),
                                "Compensation/Benefits (from JD)": job_details_dict.get("compensation", [])
                            }

                            has_detailed_sections = False
                            for section_name, section_items in sections_to_display.items():
                                if section_items and isinstance(section_items, list) and any(str(item).strip() for item in section_items):
                                    has_detailed_sections = True
                                    st.markdown(f"**{section_name}:**")
                                    for item in section_items:
                                        if isinstance(item, str) and item.strip():
                                            st.markdown(f"- {item}")
                                    st.markdown("") # Add a little space
                            
                            # If no detailed sections were populated, show the description_snippet or full description_text
                            if not has_detailed_sections:
                                full_desc_text = job_details_dict.get("description_text", "")
                                if full_desc_text.strip():
                                    st.markdown("**Full Description Text:**")
                                    st.markdown(f"> _{full_desc_text}_")
                                else:
                                    st.markdown(f"> _{result_entry.get('description_snippet', 'No detailed description available.')}_")
                            # --- End of Display Parsed JD Sections ---
                            
                            st.markdown("---") 
                            st.markdown("**Match Score Breakdown:**")
                            # ... (Your existing detailed score breakdown using st.metric, cols, etc.) ...
                            # This part should remain as it was, displaying skill scores, experience, etc.
                            # Example for skills part of breakdown:
                            cols = st.columns(2)
                            with cols[0]:
                                skill_dtls = details.get('skill_details', {})
                                skill_score_percent = skill_dtls.get('score', 0) * 100
                                req_count = skill_dtls.get('required_count',0)
                                delta_skill = f"{skill_dtls.get('match_count',0)}/{req_count} req." if req_count > 0 else "N/A (No JD skills)"
                                st.metric(label="Skills Match", value=f"{skill_score_percent:.0f}%", delta=delta_skill)
                                if skill_dtls.get('matching_skills'): 
                                    st.success(f"Your Matching Skills: {', '.join(skill_dtls.get('matching_skills',[]))}")
                                
                                required_jd_skills = set(skill_dtls.get('required_skills', [])) # Skills from JD for matching
                                resume_matched_skills = set(skill_dtls.get('matching_skills', []))
                                missing_for_jd = list(required_jd_skills - resume_matched_skills)
                                if missing_for_jd:
                                    st.warning(f"Skills in JD to Explore: {', '.join(missing_for_jd)}")

                                title_dtls = details.get('title_details', {})
                                st.metric(label="Job Title Similarity", value=f"{title_dtls.get('score',0)*100:.0f}%")
                            
                            with cols[1]:
                                exp_dtls = details.get('experience_details', {})
                                exp_val_text = "Met" if exp_dtls.get('score',0) == 1.0 else "Not Met" if exp_dtls.get('required_years') is not None else "N/A"
                                st.metric(label="Experience Years", value=f"{exp_dtls.get('resume_years','N/A')} yrs", delta=f"{exp_val_text} (Req: {exp_dtls.get('required_years','N/A')} yrs)")
                                
                                edu_dtls = details.get('education_details', {})
                                resume_level_text = get_education_text(edu_dtls.get('resume_level', -1)) # Assuming get_education_text is defined
                                jd_req_level_text = get_education_text(edu_dtls.get('required_level', -1))
                                edu_delta_text = "Met" if edu_dtls.get('score',0) == 1.0 else "Not Met" if jd_req_level_text != "Unknown" else "N/A"
                                if jd_req_level_text == "Unknown": edu_delta_text += " (JD: N/A)"
                                else: edu_delta_text += f" (JD: {jd_req_level_text})"
                                st.metric(label="Education Level", value=f"Res: {resume_level_text}", delta=edu_delta_text)
                            
                            keyword_dtls = details.get('keyword_details',{})
                            keyword_score_percent = keyword_dtls.get('score',0)*100
                            total_jd_kws = keyword_dtls.get('jd_meaningful_tokens_count',0) # Use meaningful count
                            delta_keyword = f"{keyword_dtls.get('matching_keywords_count',0)}/{total_jd_kws} common" if total_jd_kws > 0 else "N/A (No JD keywords)"
                            st.metric(label="Description Keywords", value=f"{keyword_score_percent:.0f}%", delta=delta_keyword)
                            if keyword_dtls.get('matching_keywords'):
                                st.caption(f"Common Keywords (sample): {', '.join(keyword_dtls.get('matching_keywords',[])[:5])}...")


                else:
                    st.info("No job matches found for this resume within the current filter criteria.")
            else: 
                if not ALL_PARSED_JOBS_FULL_LIST: 
                    # Warning already shown if file not loaded
                    pass
                elif not ('parsed_resume_data' in st.session_state and st.session_state.parsed_resume_data):
                     st.info("Resume has not been processed yet or processing failed.")
else: 
    st.info("☝️ Upload a resume file to get started.")
    if 'parsed_resume_data' in st.session_state: 
        del st.session_state.parsed_resume_data

