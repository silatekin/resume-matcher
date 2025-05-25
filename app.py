import streamlit as st
# --- Page Configuration MUST be the first Streamlit command ---
st.set_page_config(layout="wide", page_title="Resume Matcher", initial_sidebar_state="expanded")

from matcher import calculate_match_score 
import json
import os
import spacy
import logging
from resume_parser import ( 
    process_streamlit_file,
    load_skills, 
    SECTION_HEADERS_GLOBAL, 
    EDUCATION_LEVELS_GLOBAL 
)

EDUCATION_DISPLAY_MAP = {val: key.replace('.', '').replace('_', ' ').title() for key, val in EDUCATION_LEVELS_GLOBAL.items()}

def get_education_text(level_code):
    return EDUCATION_DISPLAY_MAP.get(level_code, "Unknown")

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
)

APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARSED_KAGGLE_JOBS_PATH = os.path.join(APP_BASE_DIR, "parsed_kaggle_jobs_sample.json")
SKILLS_JSON_PATH_FOR_RESUME_PARSER = os.path.join(APP_BASE_DIR, "tests", "data", "skills.json")

@st.cache_data
def load_parsed_kaggle_jobs(path_to_json_file):
    logging.info(f"Attempting to load PARSED KAGGLE job descriptions from: {path_to_json_file}")
    try:
        with open(path_to_json_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        if jobs:
            logging.info(f"Successfully loaded {len(jobs)} PARSED KAGGLE job descriptions from {path_to_json_file}")
        else:
            logging.warning(f"No PARSED KAGGLE job descriptions found or loaded from {path_to_json_file}.")
        return jobs
    except FileNotFoundError:
        logging.error(f"Parsed job descriptions file not found: {path_to_json_file}")
        return [] 
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from '{path_to_json_file}': {e}")
        return []
    except Exception as e:
        logging.error(f"Failed to load PARSED KAGGLE job descriptions: {e}")
        return []

@st.cache_resource 
def get_nlp_model():
    try:
        model = spacy.load("en_core_web_md")
        logging.info("spaCy NLP model 'en_core_web_md' loaded successfully for the app.")
        return model
    except OSError:
        logging.error("spaCy model 'en_core_web_md' not found.")
        return None 

@st.cache_data 
def get_skills_data_for_resume_parser_cached(skill_file_path=None):
    skill_list = load_skills(skill_file_path) 
    skill_set = set(skill_list)
    logging.info(f"Loaded {len(skill_list)} skills for resume parser from '{skill_file_path}'.")
    return skill_list, skill_set

NLP_MODEL = get_nlp_model()
TECH_SKILLS_LIST_APP, TECH_SKILLS_SET_APP = get_skills_data_for_resume_parser_cached(SKILLS_JSON_PATH_FOR_RESUME_PARSER)
ALL_PARSED_JOBS_FULL_LIST = load_parsed_kaggle_jobs(PARSED_KAGGLE_JOBS_PATH)

if 'selected_locations' not in st.session_state:
    st.session_state.selected_locations = []
if 'selected_work_types' not in st.session_state:
    st.session_state.selected_work_types = []

unique_locations = []
unique_work_types = []
if ALL_PARSED_JOBS_FULL_LIST:
    locations_set = set()
    for job in ALL_PARSED_JOBS_FULL_LIST:
        loc = job.get('location_kaggle')
        if loc and isinstance(loc, str) and loc.strip():
            locations_set.add(loc.strip())
    unique_locations = sorted(list(locations_set))

    work_types_set = set()
    for job in ALL_PARSED_JOBS_FULL_LIST:
        wt = job.get('work_type_kaggle')
        if wt and isinstance(wt, str) and wt.strip():
            work_types_set.add(wt.strip())
    unique_work_types = sorted(list(work_types_set))

st.title("🎯 Resume to Job Matcher")
st.write("Upload your resume (TXT, DOCX, PDF) to find suitable job openings. Use the sidebar to filter jobs.")

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
        if unique_work_types:
            st.session_state.selected_work_types = st.multiselect(
                "Filter by Work Type:", options=unique_work_types,
                default=st.session_state.selected_work_types,
                help="Select one or more work types."
            )
    if st.button("Clear All Filters", key="clear_filters_button"):
        st.session_state.selected_locations = []
        st.session_state.selected_work_types = []
        st.rerun()

jobs_to_display_and_match = ALL_PARSED_JOBS_FULL_LIST
logging.debug(f"Initial job count for matching: {len(jobs_to_display_and_match)}")
logging.debug(f"Session state locations: {st.session_state.selected_locations}")
logging.debug(f"Session state work types: {st.session_state.selected_work_types}")

if ALL_PARSED_JOBS_FULL_LIST:
    if st.session_state.selected_locations:
        selected_locs_normalized = {loc.strip().lower() for loc in st.session_state.selected_locations}
        jobs_to_display_and_match = [
            job for job in jobs_to_display_and_match 
            if job.get('location_kaggle') and isinstance(job.get('location_kaggle'), str) and \
               job.get('location_kaggle').strip().lower() in selected_locs_normalized
        ]
        logging.info(f"After location filter ({st.session_state.selected_locations}), count: {len(jobs_to_display_and_match)}")

    if st.session_state.selected_work_types:
        selected_work_types_normalized = {wt.strip().lower() for wt in st.session_state.selected_work_types}
        jobs_to_display_and_match = [
            job for job in jobs_to_display_and_match
            if job.get('work_type_kaggle') and isinstance(job.get('work_type_kaggle'), str) and \
               job.get('work_type_kaggle').strip().lower() in selected_work_types_normalized
        ]
        logging.info(f"After work type filter ({st.session_state.selected_work_types}), count: {len(jobs_to_display_and_match)}")
logging.info(f"Final job count for matching after filters: {len(jobs_to_display_and_match)}")

critical_error_occurred = False
if NLP_MODEL is None:
    st.error("CRITICAL APP ERROR: spaCy model 'en_core_web_md' not found. Resume parsing is disabled.")
    critical_error_occurred = True

if not ALL_PARSED_JOBS_FULL_LIST: 
    st.warning(f"Initial job descriptions could not be loaded from '{PARSED_KAGGLE_JOBS_PATH}'. Matching may be limited or unavailable.")

uploaded_file = st.file_uploader("Choose a resume file", type=['txt', 'docx', 'pdf'])

if uploaded_file is not None:
    st.markdown("---")
    st.write(f"Uploaded file: **{uploaded_file.name}** (Type: {uploaded_file.type})")

    if critical_error_occurred:
        st.error("Cannot proceed due to critical resource loading errors mentioned above.")
    elif calculate_match_score is None: 
        st.error("Job matcher component (calculate_match_score) is not available.")
    else:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            parsed_resume_data = process_streamlit_file(
                uploaded_file, NLP_MODEL, TECH_SKILLS_LIST_APP, TECH_SKILLS_SET_APP,
                SECTION_HEADERS_GLOBAL, EDUCATION_LEVELS_GLOBAL
            )
            processing_successful = False 
            if parsed_resume_data and "error" not in parsed_resume_data: # Check for error key from parser
                st.session_state.parsed_resume_data = parsed_resume_data 
                processing_successful = True
                logging.info(f"Resume '{uploaded_file.name}' processed successfully.")
            else:
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
                        if description and str(description).strip(): # Ensure description is not None and not just whitespace
                            st.markdown("**Description:**")
                            for desc_line in str(description).split('\n'): # Ensure description is string
                                st.markdown(f"- {desc_line.strip()}")
                        else:
                            st.markdown("**Description:** No description provided.")
            else:
                st.write("**Work Experience:** Not found or empty in parsed resume data.")
            
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
                    if display_degree == "N/A" and (institution == "N/A" or not institution):
                        exp_title = f"Education Entry {i+1}"
                    elif display_degree == "N/A":
                        exp_title = f"Education at {institution}"
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
            # --- END OF RESTORED RESUME DISPLAY ---


            st.markdown("---")
            st.subheader("📊 Job Matching Results:")
            
            if not jobs_to_display_and_match and (st.session_state.selected_locations or st.session_state.selected_work_types):
                st.info("No jobs match your current filter selections. Try adjusting the filters in the sidebar.")
            elif not jobs_to_display_and_match and not ALL_PARSED_JOBS_FULL_LIST:
                 st.warning("Job data is not loaded. Cannot perform matching.")
            elif jobs_to_display_and_match and data_to_display_resume:
                all_job_match_results = []
                
                spinner_text = f"Calculating job matches against {len(jobs_to_display_and_match)} jobs..."
                if len(jobs_to_display_and_match) != len(ALL_PARSED_JOBS_FULL_LIST):
                     spinner_text = (f"Calculating job matches against {len(jobs_to_display_and_match)} filtered jobs "
                                f"(out of {len(ALL_PARSED_JOBS_FULL_LIST)} total)...")

                with st.spinner(spinner_text):
                    for job_data_from_file in jobs_to_display_and_match: 
                        match_details = calculate_match_score(data_to_display_resume, job_data_from_file, NLP_MODEL)
                        
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
                    st.write(f"Showing top matches from {len(jobs_to_display_and_match)} currently displayed jobs:")
                    
                    if len(sorted_matches) == 1:
                        num_matches_to_show = 1
                    elif len(sorted_matches) > 1:
                        num_matches_to_show = st.slider(
                            "Number of top matches to display:", 
                            min_value=1, 
                            max_value=max(2, min(20, len(sorted_matches))),
                            value=min(5, len(sorted_matches)), 
                            key="matches_slider"
                        )
                    else: 
                        num_matches_to_show = 0

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
                            ]:
                                section_content = job_details_json.get(section_key, [])
                                if section_content:
                                    st.markdown(f"**{section_title}:**")
                                    if isinstance(section_content, list):
                                        for item in section_content: st.markdown(f"- {item}")
                                    else: st.markdown(f"- {section_content}") 
                                    st.markdown("") 
                            
                            if not job_details_json.get("responsibilities") and \
                               not job_details_json.get("qualifications") and \
                               not job_details_json.get("preferred_qualifications"):
                                st.markdown("**Description Snippet:**")
                                st.markdown(f"> _{result_entry.get('description_snippet', 'No detailed description sections found.')}_")
                            
                            st.markdown("---") 
                            st.markdown("**Keyword Match Insights:**")
                            keyword_dtls = details.get('keyword_details', {})
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
                                st.info("No common relevant keywords found.")
                            jd_meaningful_kws_display = keyword_dtls.get('jd_meaningful_tokens_for_scoring', [])
                            if jd_meaningful_kws_display:
                                st.markdown("**JD Keywords Used for Scoring (Sample if long):**")
                                if len(jd_meaningful_kws_display) > 75:
                                    st.caption(f"(Showing a sample of 75 out of {len(jd_meaningful_kws_display)} keywords)")
                                    st.markdown(f"`{', '.join(jd_meaningful_kws_display[:75])}...`")
                                else:
                                    st.markdown(f"`{', '.join(jd_meaningful_kws_display)}`")
                            
                            st.markdown("---")
                            st.markdown("**Overall Score Component Breakdown:**")
                            cols = st.columns(2)
                            with cols[0]:
                                skill_dtls = details.get('skill_details', {})
                                skill_score_percent = skill_dtls.get('score', 0) * 100
                                req_count = skill_dtls.get('required_count',0)
                                delta_skill = f"{skill_dtls.get('match_count',0)}/{req_count} req." if req_count > 0 else "N/A"
                                st.metric(label="Skills Match", value=f"{skill_score_percent:.0f}%", delta=delta_skill)
                                if skill_dtls.get('matching_skills'): st.success(f"Matching: {', '.join(skill_dtls['matching_skills'])}")
                                missing_skills = list(set(skill_dtls.get('required_skills', [])) - set(skill_dtls.get('matching_skills', [])))
                                if missing_skills: st.warning(f"To Explore in JD: {', '.join(missing_skills)}")
                                title_dtls = details.get('title_details', {})
                                st.metric(label="Job Title Similarity", value=f"{title_dtls.get('score',0)*100:.0f}%")
                            with cols[1]:
                                exp_dtls = details.get('experience_details', {})
                                exp_val = "Met" if exp_dtls.get('score',0) == 1.0 else "Not Met" if exp_dtls.get('required_years') is not None else "N/A"
                                st.metric(label="Experience Years", value=f"{exp_dtls.get('resume_years','N/A')} yrs", delta=f"{exp_val} (Req: {exp_dtls.get('required_years','N/A')} yrs)")
                                
                                # --- CORRECTED EDUCATION LOGIC ---
                                edu_dtls = details.get('education_details', {})
                                edu_score_val = edu_dtls.get('score', 0.0) 
                                resume_level_code = edu_dtls.get('resume_level', -1)
                                jd_req_level_code = edu_dtls.get('required_level', -1) # Should be an int from matcher

                                resume_level_display_text = get_education_text(resume_level_code)
                                
                                edu_delta_description = "Status: N/A" # Default delta text

                                if jd_req_level_code >= 0:  # A specific education level (0-5) is required by the JD
                                    jd_req_level_display_text = get_education_text(jd_req_level_code)
                                    if edu_score_val == 1.0:
                                        edu_delta_description = f"Met (JD Requires: {jd_req_level_display_text})"
                                    elif resume_level_code == -1: # Resume level not determined, but JD has a requirement
                                        edu_delta_description = f"Not Met (Resume level unknown; JD Requires: {jd_req_level_display_text})"
                                    else: # Resume level is known but less than JD requirement
                                        edu_delta_description = f"Not Met (JD Requires: {jd_req_level_display_text})"
                                elif jd_req_level_code < 0:  # JD has no specific requirement (matcher returned -1)
                                    if resume_level_code != -1 : # Resume has some education
                                        edu_delta_description = "Satisfactory (JD has no specific education requirement)"
                                    else: # Both resume and JD education are not specified/determined
                                        edu_delta_description = "N/A (JD: No specific requirement; Resume: Level unknown)"
                                
                                st.metric(label="Education Level", 
                                          value=f"Res: {resume_level_display_text}", 
                                          delta=edu_delta_description)
                                
                                # --- END OF CORRECTED EDUCATION DELTA LOGIC ---
                else: 
                    st.info("No job matches found for this resume within the current filter criteria.")
            else: 
                if not ALL_PARSED_JOBS_FULL_LIST: 
                    st.warning("Job data is not loaded. Cannot perform matching.")
                elif not ('parsed_resume_data' in st.session_state and st.session_state.parsed_resume_data):
                     st.info("Resume has not been processed yet or processing failed.")
else: 
    st.info("☝️ Upload a resume file to get started.")
    if 'parsed_resume_data' in st.session_state: 
        del st.session_state.parsed_resume_data
