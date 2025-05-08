import math
import logging
import string

#TODO
#Add Job Title Matching:
#Add Keyword Matching:

def clean_and_tokenize(text):
    """
    Lowercases, removes punctuation, splits into words.
    Filters tokens longer than 1 character.
    """
    if not isinstance(text,str):
        return set()
    
    text = text.lower()
    text = ''.join(char for char in text if char not in string.punctuation)

    tokens = text.split()
    cleaned_tokens = {token for token in tokens if len(token)>1}

    return cleaned_tokens

def calculate_match_score(parsed_resume,parsed_jd):

    skill_score = 0.0
    final_score = 0.0

    #---Skill Matching---
    resume_skills_list = parsed_resume.get('skills',[])
    jd_skills_list = parsed_jd.get('skills',[])

    resume_skills_set = set(resume_skills_list)
    jd_skills_set = set(jd_skills_list)

    matching_skills_set = resume_skills_set.intersection(jd_skills_set)

    
    if(len(jd_skills_set)) > 0:
        skill_score=len(matching_skills_set)/len(jd_skills_set)
    else:
        skill_score = 1.0 #if jd lists have no skills

    #---Experience Years Matching---
    resume_experience_years = parsed_resume.get('total_years_experience',0)
    jd_experience_years = parsed_jd.get('minimum_years_experience',None)
    experience_score = 0.0

    
    if jd_experience_years is None:
        experience_score = 1.0
    elif resume_experience_years>=jd_experience_years:
        experience_score = 1.0
    else:
        experience_score = 0.0

    # ---Education Matching---
    resume_edu_level = parsed_resume.get('education_level',-1)
    jd_edu_level = parsed_jd.get('required_education_level',None)

    education_score = 0.0

    if jd_edu_level is None or jd_edu_level < 0:
        education_score = 1.0
        logging.info("JD requires no specific education level or requirement is invalid.")
    
    elif resume_edu_level < 0:
        education_score = 0.0
        logging.info("Resume education level unknown, cannot meet requirement.")

    elif resume_edu_level >= jd_edu_level:
        education_score = 1.0
        logging.info(f"Resume level ({resume_edu_level}) meets/exceeds requirement ({jd_edu_level}).")

    else:
        education_score = 0.0
        logging.info(f"Resume level ({resume_edu_level}) is below requirement ({jd_edu_level}).")

    # ---Job Title Matching---
    jd_title = parsed_jd.get('job_title', '')
    resume_experience = parsed_resume.get('experience', [])

    jd_tokens = clean_and_tokenize(jd_title)
    print(f"DEBUG MATCHER: JD Title tokens: {jd_tokens}")

    title_score = 0.0
    matching_resume_titles = []
    all_resume_titles_checked = [entry.get('job_title') if entry.get('job_title') is not None else '' for entry in resume_experience]

    if jd_tokens:
        for entry in resume_experience:
            resume_title = entry.get('job_title')
            
            if resume_title:
                resume_tokens = clean_and_tokenize(resume_title)
                print(f"DEBUG MATCHER: Checking resume title '{resume_title}' tokens: {resume_tokens}")

                common_tokens = jd_tokens.intersection(resume_tokens)
                print(f"DEBUG MATCHER: Common tokens: {common_tokens}")

                if any(len(token)>1 for token in common_tokens):
                    title_score = 1.0
                    if resume_title not in matching_resume_titles:
                        matching_resume_titles.append(resume_title)
                    break
    print(f"DEBUG MATCHER: Job Title Score: {title_score}")

    #---Keyword Matching---
    """
    Look for keywords in responsibilities and qualifications sections in jd
    Look for experience or summary sections in resume
    Check overlapping tokens 
    """
    jd_keyword_sections = []
    
    if parsed_jd.get('responsibilities'):
        jd_keyword_sections.extend(parsed_jd['responsibilities'])
    if parsed_jd.get('qualifications'):
        jd_keyword_sections.extend(parsed_jd['qualifications'])
    if parsed_jd.get('preferred_qualifications'):
        jd_keyword_sections.extend(parsed_jd['preferred_qualifications'])
    
    jd_keyword_text = " ".join(jd_keyword_sections)
    
    print(f"DEBUG MATCHER: Combined JD Keyword Text (first 100 chars): {jd_keyword_text[:100]}...") 

    resume_keyword_sections = []
    resume_experience = parsed_resume.get('experience',[])

    for entry in resume_experience:
        description = entry.get('description','')
        if description:
            resume_keyword_sections.append(description)


    resume_keyword_text = " ".join(resume_keyword_sections)

    print(f"DEBUG MATCHER: Combined Resume Keyword Text (first 100 chars): {resume_keyword_text[:100]}...") 

    jd_keyword_tokens = clean_and_tokenize(jd_keyword_text)
    resume_keyword_tokens = clean_and_tokenize(resume_keyword_text)

    print(f"DEBUG MATCHER: JD Keyword tokens count: {len(jd_keyword_tokens)}") 
    print(f"DEBUG MATCHER: Resume Keyword tokens count: {len(resume_keyword_tokens)}") 


    matching_keyword_tokens = jd_keyword_tokens.intersection(resume_keyword_tokens)
    matching_keywords = sorted(list(matching_keyword_tokens))

    print(f"DEBUG MATCHER: Matching keyword tokens count: {len(matching_keywords)}") 
    print(f"DEBUG MATCHER: Matching keywords: {matching_keywords}")

    total_jd_keywords_count = len(jd_keyword_tokens)
    matching_keywords_count = len(matching_keywords)

    keyword_score = 0.0

    if total_jd_keywords_count > 0:
        keyword_score = matching_keywords_count / total_jd_keywords_count
    else:
        keyword_score = 1.0

    print(f"DEBUG MATCHER: Keyword Score: {keyword_score}")


    #---Final Score Logic---
    skill_weight = 0.3
    experience_weight = 0.2
    education_weight = 0.1
    title_weight = 0.1
    keyword_weight = 0.3

    final_score = (skill_score * skill_weight) + (experience_score * experience_weight) + \
                 (education_score * education_weight) + (title_score * title_weight)+ \
                 (keyword_score * keyword_weight)
    
    results = {
        'score':final_score,
        'skill_details':{
            'score':skill_score,
            'matching_skills':sorted(list(matching_skills_set)),
            'required_skills':sorted(list(jd_skills_set)),
            'resume_skills': sorted(list(resume_skills_set)),
            'match_count': len(matching_skills_set),
            'required_count':len(jd_skills_set)
        },
        'experience_details': {
            'score':experience_score,
            'resume_years':resume_experience_years,
            'required_years':jd_experience_years
        },
        'education_details':{
            'score':education_score,
            'resume_level':resume_edu_level,
            'required_level':jd_edu_level
        },
        'title_details':{
            'score': title_score,
            'jd_title': jd_title,
            'resume_titles_checked':all_resume_titles_checked,
            'matching_resume_titles': matching_resume_titles
        },
        'keyword_details':{
            'score':keyword_score,
            'matching_keywords': matching_keywords,
            'total_jd_keywords_count':total_jd_keywords_count
        }

    }
    
    return results

