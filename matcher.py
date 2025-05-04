import math
import logging

#TODO
#Add Job Title Matching:
#Add Keyword Matching:

def calculate_match_score(parsed_resume,parsed_jd):

    skill_score = 0.0
    final_score = 0.0

    #---Skill Matching Logic---
    resume_skills_list = parsed_resume.get('skills',[])
    jd_skills_list = parsed_jd.get('skills',[])

    resume_skills_set = set(resume_skills_list)
    jd_skills_set = set(jd_skills_list)

    matching_skills_set = resume_skills_set.intersection(jd_skills_set)

    
    if(len(jd_skills_set)) > 0:
        skill_score=len(matching_skills_set)/len(jd_skills_set)
    else:
        skill_score = 1.0 #if jd lists have no skills

    #---Experience Years Matching Logic---
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



    #---Final Score Logic---
    skill_weight = 0.5
    experience_weight = 0.3
    education_weight = 0.2
    final_score = (skill_score * skill_weight) + (experience_score * experience_weight) + (education_score * education_weight)
    
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
        }
    }
    
    return results


"""
dummy_resume = {'skills': ['Python', 'SQL', 'Data Analysis'], 'total_years_experience': 5}
dummy_jd = {'skills': ['Python', 'Java', 'SQL', 'Cloud'], 'minimum_years_experience': 3}

match_results = calculate_match_score(dummy_resume, dummy_jd)

print(f"Calculated Overall Match Score: {match_results['score']:.2f}")
print("\n--- Skill Match Details ---")
print(f"Final Score: {match_results['score']:.2f}")
print(f"Skill Score: {match_results['skill_details']['score']:.2f}")
print(f"Experience score: {match_results['experience_details']['score']}")
print(f"Matching Skills ({match_results['skill_details']['match_count']}/{match_results['skill_details']['required_count']}): {match_results['skill_details']['matching_skills']}")
"""
