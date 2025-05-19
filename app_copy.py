import streamlit as st
from matcher import calculate_match_score
from load_job_descriptions import load_all_job_descriptions_from_folder
import os
import spacy
from resume_parser_copy import (
    process_streamlit_file,
    load_skills, 
    SECTION_HEADERS_GLOBAL, 
    EDUCATION_LEVELS_GLOBAL 
)

# parsed_resume = {
#     "skills": [],  # DONE
#     "education_details": [  #DONE
#      {
#       "degree_mention": degree_mention,     # bachelor", "msc" (from EDUCATION_LEVELS keys)
#       "institution_mention": institution_mention, # "Stanford University" (from NER ORG)
#       "date_mention": date_mention,         # e."2018" (from NER DATE)
#       "text": sent.text.strip()             
#      } ],
#     "contact_info": {},  # MOSTLY DONE BUT MAYBE ADD NAME EXTRACTION?
#     "experience": [], # DONE
#     "total_years_experience": 0.0, # DONE
#     "education_level": -1, # DONE
#     "companies": [], DONE
# }

APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOB_DATA_FOLDER_PATH = os.path.join(APP_BASE_DIR,"tests","data", "job_descriptions")

def get_cached_job_data(path_to_jobs_folder):
    print(f"APP.PY: Cache miss or first run. Calling load_all_job_descriptions_from_folder with path: {path_to_jobs_folder}")
    return load_all_job_descriptions_from_folder(path_to_jobs_folder)


DUMMY_JOBS = get_cached_job_data(JOB_DATA_FOLDER_PATH)

if not DUMMY_JOBS:
    st.error("Failed to load job descriptions. Job matching will be unavailable.")

# In app.py

@st.cache_resource
def get_nlp_model():
    try:
        model = spacy.load("en_core_web_md")
        st.info("NLP model loaded for app.") # Optional
        return model
    except OSError:
        st.error("App Error: Spacy model 'en_core_web_md' not found.")
        return None

@st.cache_data
def get_skills_data(skill_file_path=None): 
    
    skill_list = load_skills(skill_file_path)
    skill_set = set(skill_list)
    return skill_list, skill_set


nlp_model_app = get_nlp_model() 

base_app_dir = os.path.dirname(os.path.abspath(__file__))
skills_json_path_app = os.path.join(base_app_dir, "tests", "data", "skills.json")
tech_skills_list_app, tech_skills_set_app = get_skills_data(skills_json_path_app)



st.title("Resume to Job Matcher")
st.write("Upload your resume to find suitable job openings.")

uploaded_file = st.file_uploader("Choose a resume file (TXT, DOCX, PDF)", type=['txt', 'docx', 'pdf'])

if uploaded_file is not None:
    st.markdown("---")
    st.write(f"Uploaded file: **{uploaded_file.name}** (Type: {uploaded_file.type})")

    with st.spinner(f"Processing {uploaded_file.name} with our Resume Parser..."):
        
        parsed_data = process_streamlit_file(
                uploaded_file,
                nlp_model_app,         
                tech_skills_list_app,  
                tech_skills_set_app,   
                SECTION_HEADERS_GLOBAL,       
                EDUCATION_LEVELS_GLOBAL       
        )

        if parsed_data:
            st.session_state.parsed_resume_data = parsed_data
            processing_successful = True

        else:
            st.error("Failed to process the resume. The parser returned no data or an error occurred.")
            processing_successful = False
            if 'parsed_resume_data' in st.session_state:
                del st.session_state.parsed_resume_data
    
    if processing_successful and 'parsed_resume_data' in st.session_state:
        st.success("Resume processed successfully by our system!")
        data_to_display = st.session_state.parsed_resume_data
        
        st.markdown("---")

        st.subheader("Parsed Resume Information (from your `resume_parser`):")

        data_to_display = st.session_state.parsed_resume_data

        if "summary_text" in data_to_display and data_to_display["summary_text"]:
            st.write("**Summary:**")
            st.markdown(data_to_display["summary_text"])

        if "experience" in data_to_display and data_to_display["experience"]:
            st.write("**Work Experience:**")
            for experience_entry in data_to_display["experience"]:
                title = experience_entry.get("job_title","N/A")
                company = experience_entry.get("company","N/A")

                with st.expander(f"{title} at {company}"):
                    start_date = experience_entry.get("start_date", "N/A") 
                    end_date = experience_entry.get("end_date", "N/A")     
                    st.markdown(f"**Dates:** {start_date} - {end_date}")

                    description = experience_entry.get("description","No description provided.")

                    if description:
                        st.markdown("**Description:**")
                        for desc_line in description.split('\n'):
                            st.markdown(f"- {desc_line.strip()}")
                    else:
                        st.markdown("No description provided.")
        else:
            st.write("**Work Experience:** Not found or empty.")
        

        if "total_years_experience" in data_to_display:
            years_exp = data_to_display["total_years_experience"]

            if isinstance(years_exp,(int,float)) and years_exp>=0:
                st.write(f"**Total Calculated Years of Experience:** {years_exp:.1f} years")
            elif years_exp:
                st.write(f"**Total Calculated Years of Experience:** {years_exp}")
            else:
               st.write("**Total Calculated Years of Experience:** Not calculated or N/A")
        

        if "companies" in data_to_display and data_to_display["companies"]:
            st.write("**Companies Mentioned in Experience:**")

            for company_name in data_to_display["companies"]:
               st.markdown(f"- {company_name}")
        else: 
            st.write("**Companies Mentioned in Experience:** None listed or found.")


        if "contact_info" in data_to_display and data_to_display["contact_info"]:
            st.write("**Contact Information:**")
            contact = data_to_display["contact_info"]

            if "emails" in contact and contact["emails"]:
                st.write(f"- Email(s): {', '.join(contact['emails'])}")
            
            if "phones" in contact and contact["phones"]:
                st.write(f"- Phone(s): {', '.join(contact['phones'])}")

        else:
            st.write("**Contact Information:** Not found")
            

        if "skills" in data_to_display and data_to_display["skills"]:
            st.write("**Skills:**")
            for skill in data_to_display["skills"]:
                st.markdown(f"- {skill}")

        if "education_details" in data_to_display and data_to_display["education_details"]:
            st.write("**Education:**")
            for i, edu_entry in enumerate(data_to_display["education_details"]):
                # st.write(f"DEBUG: Processing edu_entry {i}: {edu_entry}") # Keep for debugging if needed

                degree = edu_entry.get("degree_mention", "N/A")
                institution = edu_entry.get("institution_mention", "N/A")
                date = edu_entry.get("date_mention", "N/A")
                original_text = edu_entry.get("text", "N/A")

                # Capitalize each word in the degree for a nice display
                display_degree = ' '.join(word.capitalize() for word in degree.split()) if degree != "N/A" else "N/A"
                display_institution = institution # Already looks good

                expander_title = f"{display_degree} at {display_institution}"
                if display_degree == "N/A" and display_institution == "N/A":
                     expander_title = f"Education Entry {i+1} (Details)" # Fallback title
                elif display_degree == "N/A":
                    expander_title = f"Education at {display_institution}"
                elif display_institution == "N/A":
                    expander_title = display_degree

                with st.expander(expander_title):
                    st.markdown(f"**Degree:** {degree}") # Shows the parsed degree phrase
                    st.markdown(f"**Institution:** {institution}")
                    st.markdown(f"**Date:** {date}")
                    # Optionally display the original text if different or for reference
                    # if original_text != "N/A" and original_text not in [degree, institution, date]:
                    #    st.markdown(f"**Source Text:** {original_text}")
        else:
            st.write("**Education:** Not found or empty.")

        
        if "education_level" in data_to_display:
            level_num = data_to_display["education_level"]
            if level_num != -1:
                level_description = f"Level {level_num}"
                st.write(f"**Highest Education Level (Parsed):** {level_description}")
            else:
                st.write("**Highest Education Level (Parsed):** Not determined.")

        with st.expander("View Raw Extracted Text Snippet:"):
            st.text_area("raw_text_display", 
                         data_to_display.get("raw_text_snippet", "No text snippet available."),
                         height=200, 
                         disabled=True,
                         label_visibility="collapsed")
        
        st.markdown("---")
        st.subheader("Job Matching Results:")
        
        if DUMMY_JOBS and data_to_display:
            all_job_match_results = []
            with st.spinner("Calculating job matches..."):
                for job_data_from_file in DUMMY_JOBS:
                    match_details_for_this_job = calculate_match_score(data_to_display, job_data_from_file)

                    all_job_match_results.append({
                        "job_info": job_data_from_file,
                        "match_details": match_details_for_this_job
                    })
            
            if all_job_match_results:
                st.write("Here are the best matches for you based on the current criteria:")
                for result_entry in all_job_match_results:
                    job = result_entry["job_info"]          
                    details = result_entry["match_details"]

                    job_title_from_json = job.get("job_title", job.get("title", "N/A")) 
                    company_from_json = job.get("company", "N/A")
                    overall_score_from_matcher = details.get('score', 0) * 100

                    expander_title = f"{job_title_from_json} at {company_from_json} - Match Score: {overall_score_from_matcher:.1f}%"

                    with st.expander(expander_title):
                        
                        st.markdown(f"**Job ID (from file):** `{job.get('id', 'N/A')}`")
                        
                        
                        st.markdown(f"**Description:** {job.get('description', 'No description provided.')}")
                        st.markdown("---") 

                        st.markdown("**Match Score Breakdown:**")

                        # Skill Details
                        skill_dtls = details.get('skill_details', {})
                        skill_score_percent = skill_dtls.get('score', 0) * 100
                        st.write(f"Skills Match: {skill_score_percent:.0f}% (Matched: {skill_dtls.get('match_count',0)} of {skill_dtls.get('required_count',0)} required)")
                        if skill_dtls.get('matching_skills'):
                            st.success(f"  Your Matching Skills: {', '.join(skill_dtls.get('matching_skills',[]))}")

                        required_skills_in_jd = set(skill_dtls.get('required_skills', []))
                        matched_skills_from_resume = set(skill_dtls.get('matching_skills', []))
                        missing_skills_for_job = list(required_skills_in_jd - matched_skills_from_resume)

                        if missing_skills_for_job:
                             st.warning(f"  Skills to Explore for this Role: {', '.join(missing_skills_for_job)}")
                        elif required_skills_in_jd : # If there were required skills and none are missing
                            st.info("  You appear to have all the listed required skills for this role!")

                        # Experience Details
                        exp_dtls = details.get('experience_details', {})
                        exp_score_val = exp_dtls.get('score',0)
                        exp_status = "Met" if exp_score_val == 1.0 else "Not Met" if exp_score_val == 0.0 else "Partially Met/Info Missing"
                        st.write(f"Experience Years Match: {exp_status} (Resume: {exp_dtls.get('resume_years', 'N/A')} yrs, Required: {exp_dtls.get('required_years', 'N/A')} yrs)")


                        # Education Details
                        edu_dtls = details.get('education_details', {})
                        edu_score_val = edu_dtls.get('score',0)
                        edu_status = "Met" if edu_score_val == 1.0 else "Not Met" if edu_score_val == 0.0 else "Partially Met/Info Missing"
                        st.write(f"Education Level Match: {edu_status} (Resume Level: {edu_dtls.get('resume_level', 'N/A')}, Required Level: {edu_dtls.get('required_level', 'N/A')})")

                        # Job Title Details
                        title_dtls = details.get('title_details', {})
                        title_score_val = title_dtls.get('score',0)
                        title_status = "Potential Match Found" if title_score_val == 1.0 else "No Direct Title Match"
                        st.write(f"Job Title Match: {title_status}")
                        if title_dtls.get('matching_resume_titles'):
                            st.info(f"  Resume titles considered a match: {', '.join(title_dtls.get('matching_resume_titles',[]))}")
                        # mybe display title_dtls.get('jd_title') if useful

                        # Keyword Details
                        keyword_dtls = details.get('keyword_details',{})
                        keyword_score_percent = keyword_dtls.get('score',0)*100
                        st.write(f"Description Keywords Match: {keyword_score_percent:.0f}% ({keyword_dtls.get('matching_keywords_count',0)} of {keyword_dtls.get('total_jd_keywords_count',0)} JD keywords found in resume)")
                        if keyword_dtls.get('matching_keywords'):
                             st.caption(f"  Common Keywords (up to 10): {', '.join(keyword_dtls.get('matching_keywords',[])[:10])}...")

            else:
               st.info("No job matches found based on the current criteria or matcher logic.")            
        else:
            if not DUMMY_JOBS:
                 st.warning("Job data is not loaded. Cannot perform matching.")

else:
    st.info("Upload a resume file to get started.")
    if 'parsed_resume_data' in st.session_state:
        del st.session_state.parsed_resume_data


