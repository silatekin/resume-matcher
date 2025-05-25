import streamlit as st
# --- Page Configuration MUST be the first Streamlit command ---
st.set_page_config(layout="wide", page_title="Find Matching Candidates")

import json
import os
import logging
import re 
import spacy # For NLP model loading

# --- Assuming your matcher is accessible ---
from matcher import calculate_match_score 

# --- Define Base Directory (useful for finding files) ---
PAGE_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ROOT_DIR = os.path.dirname(PAGE_BASE_DIR) 

# --- Path to your FOLDER of pre-parsed resume JSON files ---
PARSED_RESUMES_FOLDER_PATH = os.path.join(APP_ROOT_DIR, "tests", "data", "resumes") 

# --- Basic Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
)

# --- Load NLP Model (Cached) - More Robust Error Handling ---
@st.cache_resource
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


# --- Load Parsed Resumes (Cached) ---
@st.cache_data 
def load_all_parsed_resumes_from_folder(folder_path):
    logging.info(f"FindCandidatesPage: Attempting to load all PARSED RESUMES from FOLDER: {folder_path}")
    all_resumes = []
    if not os.path.isdir(folder_path):
        # This error will be displayed in the main UI body later
        logging.error(f"FindCandidatesPage: Parsed resumes folder not found: {folder_path}")
        return []

    try:
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".json"):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        resume_data = json.load(f)
                        all_resumes.append(resume_data)
                        logging.debug(f"FindCandidatesPage: Loaded resume from {filename}")
                except json.JSONDecodeError as e_json:
                    logging.error(f"FindCandidatesPage: Error decoding JSON from {file_path}: {e_json}")
                except Exception as e_file:
                    logging.error(f"FindCandidatesPage: Error reading file {file_path}: {e_file}")
        
        if all_resumes:
            logging.info(f"FindCandidatesPage: Successfully loaded {len(all_resumes)} PARSED RESUMES from {folder_path}")
        else:
            logging.warning(f"FindCandidatesPage: No PARSED RESUME JSON files found or loaded from {folder_path}.")
        return all_resumes
    except Exception as e_oslistdir:
        # This error will be displayed in the main UI body later
        logging.error(f"FindCandidatesPage: Failed to list or load PARSED RESUMES from folder '{folder_path}': {e_oslistdir}")
        return []

# --- Load Global Resources for this page ---
NLP_MODEL_PAGE = get_nlp_model_for_page()
ALL_PARSED_RESUMES = load_all_parsed_resumes_from_folder(PARSED_RESUMES_FOLDER_PATH)


# --- Streamlit App UI ---
st.title("📄 Manually Enter Job Description to Find Candidates")
st.write("Enter the job details below to find the most compatible resumes from our candidate database.")

critical_page_error = False
if NLP_MODEL_PAGE is None: # This check should now always work as NLP_MODEL_PAGE will be defined
    st.error("CRITICAL PAGE ERROR: spaCy NLP model 'en_core_web_md' could not be loaded. Matching functionality is disabled. Please check logs and ensure the model is downloaded.")
    critical_page_error = True

if not ALL_PARSED_RESUMES:
    st.warning(f"Candidate resumes could not be loaded from the folder '{PARSED_RESUMES_FOLDER_PATH}'. "
               "Matching will be unavailable until this folder contains parsed resume JSON files.")
    # If this is critical enough to stop the form, set critical_page_error = True
    # For now, we allow the form but matching will fail if submitted.

st.header("📝 Enter Job Details")

with st.form("manual_jd_form"):
    job_title_input = st.text_input("Job Title*", help="E.g., Senior Software Engineer")
    skills_input = st.text_area("Required Skills (comma-separated)*", help="E.g., Python, Java, SQL, Project Leadership")
    min_experience_input = st.number_input("Minimum Years of Experience Required", min_value=0, max_value=50, step=1, value=0)

    education_level_options_map = {
        "Not Specified / Any": -1, "High School / GED / Diploma": 0,
        "Some College / Technical Training": 1, "Associate's Degree": 2,
        "Bachelor's Degree": 3, "Master's Degree": 4, "PhD / Doctorate": 5
    }
    education_display_options = list(education_level_options_map.keys())
    selected_education_display = st.selectbox("Required Education Level", options=education_display_options, index=0)
    required_education_code = education_level_options_map[selected_education_display]

    job_description_text_input = st.text_area(
        "Key Responsibilities / Qualifications / Description Text*", height=200,
        help="Paste the main text of the job description here."
    )
    submitted = st.form_submit_button("Find Matching Candidates")

if submitted:
    if critical_page_error: # Check if NLP model failed to load earlier
        st.error("Cannot proceed with matching due to critical resource loading errors mentioned above.")
    elif not job_title_input.strip(): st.warning("Please enter a Job Title.")
    elif not skills_input.strip(): st.warning("Please enter Required Skills.")
    elif not job_description_text_input.strip(): st.warning("Please enter Job Description text.")
    elif not ALL_PARSED_RESUMES:
        st.error(f"No candidate resumes loaded from '{PARSED_RESUMES_FOLDER_PATH}'. Cannot perform matching.")
    # elif NLP_MODEL_PAGE is None: # This specific check is now covered by critical_page_error
    #     st.error("NLP Model for matching is not available. Cannot proceed.")
    else:
        st.markdown("---"); st.subheader("⏳ Processing and Finding Matches...")
        manual_jd_skills = [skill.strip().lower() for skill in skills_input.split(',') if skill.strip()]
        manual_parsed_jd = {
            "job_title": job_title_input.strip(), "skills": manual_jd_skills,
            "minimum_years_experience": float(min_experience_input),
            "required_education_level": required_education_code,
            "responsibilities": [job_description_text_input.strip()], "qualifications": [],
            "job_description_text_raw_kaggle": job_description_text_input.strip(), 
            "preferred_qualifications": [], "skills_text_raw_kaggle": skills_input 
        }
        logging.info(f"Manual JD prepared for matching: {manual_parsed_jd.get('job_title')}")

        all_resume_match_results = []
        with st.spinner(f"Comparing against {len(ALL_PARSED_RESUMES)} candidate resumes..."):
            for idx, resume_data_from_file in enumerate(ALL_PARSED_RESUMES):
                if not isinstance(resume_data_from_file, dict):
                    logging.warning(f"Skipping resume at index {idx} as it's not a dictionary.")
                    continue
                # Pass the NLP_MODEL_PAGE to calculate_match_score
                match_details = calculate_match_score(resume_data_from_file, manual_parsed_jd, NLP_MODEL_PAGE) 
                
                resume_identifier = f"Resume (Index {idx})" 
                if resume_data_from_file.get('contact_info'):
                    if resume_data_from_file['contact_info'].get('name'): 
                        resume_identifier = resume_data_from_file['contact_info']['name']
                    elif resume_data_from_file['contact_info'].get('emails'):
                        resume_identifier = resume_data_from_file['contact_info']['emails'][0]
                elif resume_data_from_file.get('filepath_source'): 
                    resume_identifier = os.path.basename(resume_data_from_file.get('filepath_source'))

                all_resume_match_results.append({
                    "resume_identifier": resume_identifier,
                    "match_details": match_details,
                    "original_resume_data": resume_data_from_file
                })
        
        sorted_resume_matches = sorted(all_resume_match_results, key=lambda x: x['match_details'].get('score', 0), reverse=True)

        st.markdown("---"); st.subheader(f"🏆 Top Candidate Matches for '{manual_parsed_jd['job_title']}'")
        if sorted_resume_matches:
            num_to_show_key = "num_resume_matches_slider_candidates_page" 
            if len(sorted_resume_matches) == 1: num_resume_matches_to_show = 1
            elif len(sorted_resume_matches) > 1:
                num_resume_matches_to_show = st.slider(
                    "Number of top candidate resumes to display:", 1,
                    max(2, min(10, len(sorted_resume_matches))), 
                    min(3, len(sorted_resume_matches)), key=num_to_show_key
                )
            else: num_resume_matches_to_show = 0

            for i, result_entry in enumerate(sorted_resume_matches[:num_resume_matches_to_show]):
                resume_id_display = result_entry["resume_identifier"]
                details = result_entry["match_details"]
                overall_score_percent = details.get('score', 0) * 100
                expander_title = f"{i+1}. Candidate: {resume_id_display} - Overall Match: {overall_score_percent:.1f}%"
                
                with st.expander(expander_title, expanded=(i < 1)):
                    original_resume = result_entry.get("original_resume_data", {})
                    st.markdown(f"**Key Info for Candidate: {resume_id_display}**")
                    if original_resume.get("skills"):
                        st.markdown(f"**Skills:** `{', '.join(original_resume.get('skills',[]))}`")
                    if original_resume.get("total_years_experience") is not None:
                         st.markdown(f"**Total Experience:** {original_resume.get('total_years_experience')} years")
                    
                    resume_edu_code = original_resume.get("education_level", -1)
                    temp_edu_display_map = { 
                        5: "PhD/Doctorate", 4: "Master's Degree", 3: "Bachelor's Degree", 
                        2: "Associate's Degree", 1: "Some College", 0: "High School/GED/Diploma", -1: "Not Determined"
                    }
                    st.markdown(f"**Education Level:** {temp_edu_display_map.get(resume_edu_code, 'Unknown')}")
                    
                    summary = original_resume.get("summary_text", "")
                    if summary.strip():
                        st.text_area(f"Resume Summary {i}", summary, height=100, disabled=True, label_visibility="collapsed", key=f"summary_exp_cand_{i}") # Unique key

                    st.markdown("---"); st.markdown("**Match Score Breakdown (vs this JD):**")
                    cols_res = st.columns(2) # Ensure this is defined
                    with cols_res[0]:
                        skill_dtls_res = details.get('skill_details', {})
                        st.metric(label="Skills Match", value=f"{skill_dtls_res.get('score',0)*100:.0f}%", 
                                  delta=f"{skill_dtls_res.get('match_count',0)}/{skill_dtls_res.get('required_count',0)} req. JD skills")
                    with cols_res[1]:
                        exp_dtls_res = details.get('experience_details', {})
                        exp_delta_text_res = "Met" if exp_dtls_res.get('score') == 1.0 else "Not Met" if exp_dtls_res.get('required_years') is not None else "N/A"
                        st.metric(label="Experience Years", value=f"{exp_dtls_res.get('resume_years','N/A')} yrs", 
                                  delta=f"{exp_delta_text_res} (Req: {exp_dtls_res.get('required_years','N/A')} yrs)")
                    # (Add other metrics: Education, Title, Keywords for resume match)
        else:
            st.info("No matching resumes found for the entered job description.")

st.sidebar.markdown("---")

if not ALL_PARSED_RESUMES and os.path.exists(APP_ROOT_DIR): 
     st.sidebar.warning(f"The folder '{PARSED_RESUMES_FOLDER_PATH}' was not found or is empty. "
                        "This page requires pre-parsed resume data to function.")
