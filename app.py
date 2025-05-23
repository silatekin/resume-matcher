import streamlit as st
# --- Page Configuration MUST be the first Streamlit command ---
st.set_page_config(layout="wide", page_title="Resume Matcher", initial_sidebar_state="auto")

from matcher import calculate_match_score # Ensure matcher.py is in the same directory or accessible
import json
import os
import spacy
import logging
from resume_parser import (
    process_streamlit_file,
    load_skills, # This function is used by get_skills_data_for_resume_parser_cached
    SECTION_HEADERS_GLOBAL, 
    EDUCATION_LEVELS_GLOBAL 
)

# --- Basic Logging Configuration ---
# It's okay for logging to be configured before st.set_page_config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
)

# --- Define Application Base Directory and Paths ---
APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARSED_KAGGLE_JOBS_PATH = os.path.join(APP_BASE_DIR, "parsed_kaggle_jobs_sample.json")
SKILLS_JSON_PATH_FOR_RESUME_PARSER = os.path.join(APP_BASE_DIR, "tests", "data", "skills.json")


# --- Data Loading Function for Parsed Kaggle Jobs ---
@st.cache_data # Cache the loaded job data
def load_parsed_kaggle_jobs(path_to_json_file):
    """Loads the pre-parsed job descriptions from a JSON file."""
    logging.info(f"Attempting to load PARSED KAGGLE job descriptions from: {path_to_json_file}")
    try:
        with open(path_to_json_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        if jobs:
            logging.info(f"Successfully loaded {len(jobs)} PARSED KAGGLE job descriptions from {path_to_json_file}")
        else:
            logging.warning(f"No PARSED KAGGLE job descriptions found or loaded from {path_to_json_file}. File might be empty.")
        return jobs
    except FileNotFoundError:
        # We'll display errors later in the main app body if loading fails
        logging.error(f"Parsed job descriptions file not found: {path_to_json_file}")
        return [] # Return empty list, handle error display in main app flow
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from '{path_to_json_file}': {e}")
        return []
    except Exception as e:
        logging.error(f"Failed to load PARSED KAGGLE job descriptions: {e}")
        return []

# --- Load NLP Model (Cached) ---
@st.cache_resource # Cache the NLP model resource
def get_nlp_model():
    """Loads the spaCy NLP model."""
    try:
        model = spacy.load("en_core_web_md")
        logging.info("spaCy NLP model 'en_core_web_md' loaded successfully for the app.")
        return model
    except OSError:
        logging.error("spaCy model 'en_core_web_md' not found. App functionality will be severely limited.")
        return None # Return None, handle error display in main app flow

# --- Load Skills Data for Resume Parser (Cached) ---
@st.cache_data # Cache the loaded skills data
def get_skills_data_for_resume_parser_cached(skill_file_path=None):
    """Loads skills from the JSON file and creates a list and a set."""
    skill_list = load_skills(skill_file_path) # from resume_parser_copy
    skill_set = set(skill_list)
    logging.info(f"Loaded {len(skill_list)} skills, created set of {len(skill_set)} skills for resume parser from '{skill_file_path}'.")
    return skill_list, skill_set


# --- Load Global Resources ---
# These function calls are fine here as long as they don't call st.something() directly at this stage
# The st.error/st.warning calls were removed from the global execution path of these functions
NLP_MODEL = get_nlp_model()
TECH_SKILLS_LIST_APP, TECH_SKILLS_SET_APP = get_skills_data_for_resume_parser_cached(SKILLS_JSON_PATH_FOR_RESUME_PARSER)
ALL_PARSED_JOBS = load_parsed_kaggle_jobs(PARSED_KAGGLE_JOBS_PATH)


# --- Streamlit App UI ---
st.title("🎯 Resume to Job Matcher")
st.write("Upload your resume (TXT, DOCX, PDF) to find suitable job openings from our database of pre-parsed job descriptions.")

# --- Display errors for critical resource loading failures AFTER set_page_config ---
critical_error_occurred = False
if NLP_MODEL is None:
    st.error("CRITICAL APP ERROR: spaCy model 'en_core_web_md' not found. "
             "Please download it by running: `python -m spacy download en_core_web_md`. Resume parsing is disabled.")
    critical_error_occurred = True

if not ALL_PARSED_JOBS:
    st.warning(f"Job descriptions could not be loaded from '{PARSED_KAGGLE_JOBS_PATH}'. "
               "Matching will be unavailable. Ensure the file exists and is not empty. "
               "You might need to run the preprocessing script.")
    # If job loading is critical for the app to function at all, you might set critical_error_occurred = True

uploaded_file = st.file_uploader("Choose a resume file", type=['txt', 'docx', 'pdf'])

if uploaded_file is not None:
    st.markdown("---")
    st.write(f"Uploaded file: **{uploaded_file.name}** (Type: {uploaded_file.type})")

    if critical_error_occurred:
        st.error("Cannot proceed due to critical resource loading errors mentioned above.")
    elif calculate_match_score is None: 
        st.error("Job matcher component (calculate_match_score) is not available. Cannot perform matching.")
    else:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            parsed_resume_data = process_streamlit_file(
                uploaded_file,
                NLP_MODEL, # This will be None if loading failed, process_streamlit_file should handle it
                TECH_SKILLS_LIST_APP,
                TECH_SKILLS_SET_APP,
                SECTION_HEADERS_GLOBAL,
                EDUCATION_LEVELS_GLOBAL
            )

            processing_successful = False 
            if parsed_resume_data:
                st.session_state.parsed_resume_data = parsed_resume_data 
                processing_successful = True
                logging.info(f"Resume '{uploaded_file.name}' processed successfully.")
            else:
                st.error("Failed to process the resume. The parser returned no data or an error occurred. Check logs for details.")
                logging.error(f"Failed to process resume: {uploaded_file.name}")
                if 'parsed_resume_data' in st.session_state:
                    del st.session_state.parsed_resume_data
        
        if processing_successful and 'parsed_resume_data' in st.session_state:
            st.success("✅ Resume processed successfully!")
            
            data_to_display_resume = st.session_state.parsed_resume_data
            
            st.markdown("---")
            st.subheader("📄 Your Parsed Resume Information:")

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
                        if description.strip():
                            st.markdown("**Description:**")
                            for desc_line in description.split('\n'):
                                st.markdown(f"- {desc_line.strip()}")
            else:
                st.write("**Work Experience:** Not found or empty.")

            if "total_years_experience" in data_to_display_resume and isinstance(data_to_display_resume["total_years_experience"], (int, float)):
                st.write(f"**Total Calculated Years of Experience:** {data_to_display_resume['total_years_experience']:.1f} years")

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
                for edu_entry in data_to_display_resume["education_details"]:
                    degree = edu_entry.get("degree_mention", "N/A")
                    institution = edu_entry.get("institution_mention", "N/A")
                    date = edu_entry.get("date_mention", "N/A")
                    exp_title = f"{degree.capitalize() if degree != 'N/A' else 'Degree N/A'} at {institution if institution != 'N/A' else 'Institution N/A'}"
                    with st.expander(exp_title):
                        st.markdown(f"**Degree Phrase:** {degree}")
                        st.markdown(f"**Institution:** {institution}")
                        st.markdown(f"**Date:** {date}")
            
            if "education_level" in data_to_display_resume and data_to_display_resume["education_level"] != -1:
                st.write(f"**Highest Education Level (Parsed Code):** {data_to_display_resume['education_level']}")
            
            if "raw_text_snippet" in data_to_display_resume and data_to_display_resume["raw_text_snippet"]:
                with st.expander("View Raw Extracted Text Snippet (from Resume)", expanded=False):
                    st.text_area("raw_resume_text_display",
                                 str(data_to_display_resume.get("raw_text_snippet", "")),
                                 height=150, disabled=True, label_visibility="collapsed")

            st.markdown("---")
            st.subheader("📊 Job Matching Results:")
            
            if ALL_PARSED_JOBS and data_to_display_resume:
                all_job_match_results = []
                with st.spinner(f"Calculating job matches against {len(ALL_PARSED_JOBS)} available jobs..."):
                    for job_data_from_file in ALL_PARSED_JOBS:
                        match_details = calculate_match_score(data_to_display_resume, job_data_from_file,NLP_MODEL)
                        
                        desc_text_source = job_data_from_file.get('job_description_text_raw_kaggle', '')
                        if not desc_text_source.strip() and job_data_from_file.get('responsibilities'):
                            desc_text_source = " ".join(job_data_from_file.get('responsibilities', []))
                        
                        description_snippet = (desc_text_source[:250] + "...") if len(desc_text_source) > 250 else desc_text_source
                        if not description_snippet.strip(): description_snippet = "No detailed description available."

                        all_job_match_results.append({
                            "job_title": job_data_from_file.get("job_title", "N/A"), 
                            "company": job_data_from_file.get("company_name_kaggle", "N/A"),
                            "location": job_data_from_file.get("location_kaggle", "N/A"),
                            "date_posted": job_data_from_file.get("job_posting_date_kaggle", "N/A"),
                            "description_snippet": description_snippet,
                            "match_details": match_details,
                            "job_id_for_debug": job_data_from_file.get("job_id_kaggle", "N/A"),
                            "original_job_data": job_data_from_file 
                        })
                
                sorted_matches = sorted(all_job_match_results, key=lambda x: x['match_details'].get('score', 0), reverse=True)

                if sorted_matches:
                    st.write(f"Showing top matches from {len(ALL_PARSED_JOBS)} available jobs:")
                    num_matches_to_show = st.slider(
                        "Number of top matches to display:", 1, 
                        max(1, min(20, len(sorted_matches))),
                        min(5, len(sorted_matches)), 
                        key="matches_slider"
                    )

                    for i, result_entry in enumerate(sorted_matches[:num_matches_to_show]):
                        job_title_display = result_entry["job_title"]
                        company_display = result_entry["company"]
                        details = result_entry["match_details"]
                        overall_score_percent = details.get('score', 0) * 100

                        expander_title = f"{i+1}. {job_title_display} at {company_display} - Overall Match: {overall_score_percent:.1f}%"
                        
                        with st.expander(expander_title, expanded=(i < 1)):
                            st.markdown(f"**Location:** {result_entry.get('location', 'N/A')} | **Posted:** {result_entry.get('date_posted', 'N/A')}")
                            job_url = result_entry['original_job_data'].get('job_portal_kaggle', '#')
                            if job_url and job_url != '#':
                                st.markdown(f"**[View Original Job Posting (if available)]({job_url})**", unsafe_allow_html=True)
                            else:
                                st.markdown(f"**Original Job ID (Kaggle):** `{result_entry.get('job_id_for_debug', 'N/A')}`")
                            
                            st.markdown("---")
                            job_details_json = result_entry.get("original_job_data", {})

                            for section_key, section_title in [
                                ("responsibilities", "Responsibilities"),
                                ("qualifications", "Qualifications"),
                                ("preferred_qualifications", "Preferred Qualifications"),
                                ("skills", "Skills Required (from JD)")
                            ]:
                                section_content = job_details_json.get(section_key, [])
                                if section_content:
                                    st.markdown(f"**{section_title}:**")
                                    if isinstance(section_content, list):
                                        for item in section_content: st.markdown(f"- {item}")
                                    else: 
                                        st.markdown(f"- {section_content}") 
                                    st.markdown("") 
                            
                            if not job_details_json.get("responsibilities") and \
                               not job_details_json.get("qualifications") and \
                               not job_details_json.get("preferred_qualifications"):
                                st.markdown("**Description Snippet:**")
                                st.markdown(f"> _{result_entry.get('description_snippet', 'No detailed description sections found.')}_")

                            
                            # --- NEW: Detailed Keyword Match Insights ---
                            st.markdown("---")
                            st.markdown("**Keyword Match Insights:**")
                            keyword_dtls = details.get('keyword_details', {})
                            
                            # Display the keyword metric here for context
                            key_score_display = keyword_dtls.get('score',0)*100
                            meaningful_jd_kws_count = keyword_dtls.get('jd_meaningful_tokens_count',0)
                            delta_key_display = (f"{keyword_dtls.get('matching_keywords_count',0)}/"
                                           f"{meaningful_jd_kws_count} relevant JD keywords") if meaningful_jd_kws_count > 0 else "N/A"
                            
                            st.metric(label="Description Keywords Score", value=f"{key_score_display:.0f}%", delta=delta_key_display)

                            matching_kws_display = keyword_dtls.get('matching_keywords', [])
                            if matching_kws_display:
                                st.success(f"**Common Relevant Keywords ({len(matching_kws_display)}):**")
                                st.markdown(f"`{', '.join(matching_kws_display)}`")
                            else:
                                st.info("No common relevant keywords found between resume and job description sections.")

                            jd_meaningful_kws_display = keyword_dtls.get('jd_meaningful_tokens_for_scoring', [])
                            if jd_meaningful_kws_display:
                                st.markdown("**JD Keywords Used for Scoring (Sample if long):**") # New title for this section
                                if len(jd_meaningful_kws_display) > 75: # Increased sample limit slightly
                                    st.caption(f"(Showing a sample of 75 out of {len(jd_meaningful_kws_display)} keywords)")
                                    st.markdown(f"`{', '.join(jd_meaningful_kws_display[:75])}...`")
                                else:
                                    st.markdown(f"`{', '.join(jd_meaningful_kws_display)}`")
                            # --- End of Detailed Keyword Match Insights ---
                            
                            st.markdown("**Match Score Breakdown:**")
                            cols = st.columns(2)
                            with cols[0]:
                                skill_dtls = details.get('skill_details', {})
                                skill_score_percent = skill_dtls.get('score', 0) * 100
                                req_count = skill_dtls.get('required_count',0)
                                delta_skill = f"{skill_dtls.get('match_count',0)}/{req_count} req." if req_count > 0 else "N/A"
                                st.metric(label="Skills Match", value=f"{skill_score_percent:.0f}%", delta=delta_skill)
                                if skill_dtls.get('matching_skills'): st.success(f"Matching: {', '.join(skill_dtls['matching_skills'])}")
                                missing_skills = list(set(skill_dtls.get('required_skills', [])) - set(skill_dtls.get('matching_skills', [])))
                                if missing_skills: st.warning(f"To Explore: {', '.join(missing_skills)}")

                                title_dtls = details.get('title_details', {})
                                st.metric(label="Job Title Similarity", value=f"{title_dtls.get('score',0)*100:.0f}%")
                            
                            with cols[1]:
                                exp_dtls = details.get('experience_details', {})
                                exp_val = "Met" if exp_dtls.get('score',0) == 1.0 else "Not Met" if exp_dtls.get('required_years') is not None else "N/A"
                                st.metric(label="Experience Years", value=f"{exp_dtls.get('resume_years','N/A')} yrs", delta=f"{exp_val} (Req: {exp_dtls.get('required_years','N/A')} yrs)")

                                edu_dtls = details.get('education_details', {})
                                edu_val = "Met" if edu_dtls.get('score',0) == 1.0 else "Not Met" if edu_dtls.get('required_level') is not None else "N/A"
                                st.metric(label="Education Level", value=f"Res: {edu_dtls.get('resume_level','N/A')}", delta=f"{edu_val} (Req: {edu_dtls.get('required_level','N/A')})")

                            keyword_dtls = details.get('keyword_details',{})
                            key_score = keyword_dtls.get('score',0)*100
                            key_total = keyword_dtls.get('total_jd_keywords_count',0)
                            delta_key = f"{len(keyword_dtls.get('matching_keywords',[]))}/{key_total} common" if key_total > 0 else "N/A"
                            st.metric(label="Description Keywords Match", value=f"{key_score:.0f}%", delta=delta_key)
                            if keyword_dtls.get('matching_keywords'): st.caption(f"Common (sample): {', '.join(keyword_dtls['matching_keywords'][:5])}...")
                else:
                    st.info("No job matches found or an issue occurred during matching.")
            else:
                if not ALL_PARSED_JOBS:
                    st.warning("Job data (ALL_PARSED_JOBS) is not loaded. Cannot perform matching.")
                elif not ('parsed_resume_data' in st.session_state and st.session_state.parsed_resume_data):
                     st.info("Resume has not been processed yet or processing failed.")
else: 
    st.info("☝️ Upload a resume file to get started.")
    if 'parsed_resume_data' in st.session_state: 
        del st.session_state.parsed_resume_data
