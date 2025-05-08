import json
import os
import pytest 
import sys
import datetime


tests_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(tests_dir)
sys.path.insert(0, project_root)

from matcher import calculate_match_score


def load_json_data(filename,data_type='resume'):
    if data_type == 'resume':
        subfolder = 'resumes'
    elif data_type == 'jd':
        subfolder = 'job_descriptions'
    else:
        pytest.fail(f"Invalid data_type '{data_type} for load_json_data. Use 'resume' or 'jd'.", pytrace=False)


    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir,'data',subfolder,filename) 

    try:
        with open(data_path,'r',encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        pytest.fail(f"Test data file not found: {data_path}", pytrace=False)
    except json.JSONDecodeError:
        pytest.fail(f"Error decoding JSON from test data file: {data_path}", pytrace=False)
    except Exception as e:
        pytest.fail(f"Unexpected error loading test data {data_path}: {e}", pytrace=False)


def test_specific_resume01_jd01_pair():
    """
    Tests the matching score for resume_01.json vs job_01.json.
    """
    
    print("\n--- Testing resume_01 vs job_01 ---")

    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_01.json','resume')
    jd_data = load_json_data('job_01.json', 'jd')
    print("Arrange: Data loaded.")


    print("Arrange: Defining expected results...")
    expected_skill_score = pytest.approx(2/11, abs=0.001) 
    expected_exp_score = pytest.approx(1.0)
    expected_education_score = pytest.approx(1.0)
    expected_title_score = pytest.approx(1.0)

    expected_total_jd_keywords_count = 49
    expected_matching_keywords = sorted(['and', 'to'])
    expected_keyword_score = pytest.approx(len(expected_matching_keywords) / expected_total_jd_keywords_count, abs=0.001) if expected_total_jd_keywords_count > 0 else pytest.approx(1.0) 

    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.3) +
        (expected_exp_score.expected * 0.2) +
        (expected_education_score.expected * 0.1) +
        (expected_title_score.expected * 0.1)+
        (expected_keyword_score.expected * 0.3),
        abs=0.001
        )

    expected_results = {
        'score': expected_overall_score,
        'skill_details': {
            'score': expected_skill_score,
            'matching_skills': sorted(["Python", "SQL"]), 
            'required_skills': sorted(["Azure", "GCP", "Docker", "CI/CD", "Django", "Python", "AWS", "SQL", "Flask", "Kubernetes", "Git"]),
            'resume_skills': sorted(["JavaScript", "Node.js", "Python", "React", "SQL"]), 
            'match_count': 2,
            'required_count': 11 
        },
        'experience_details': {
            'score': expected_exp_score,
            'resume_years': 7.3,
            'required_years': 5
        },
        'education_details': {
            'score': expected_education_score,
            'resume_level': 3,
            'required_level': 3 
        },
         'title_details': {
            'score': expected_title_score,
            'jd_title': 'Senior Python Developer',
            'resume_titles_checked': ['Senior Software Engineer', 'Software Developer'], 
            'matching_resume_titles': ['Senior Software Engineer'] # Based on first match
        },
        'keyword_details': {
            'score': expected_keyword_score,
            'matching_keywords': expected_matching_keywords, 
            'total_jd_keywords_count': expected_total_jd_keywords_count
        }
       
    }

    print("Arrange: Defined expected results.")

    # --- Act ---
    print("Act: Calling calculate_match_score...")
    actual_results = calculate_match_score(resume_data, jd_data)
    print("Act: Received results.")

    # --- Assert ---
    print("Assert: Checking results...")

    print(f"DEBUG TEST: actual_resume_titles_checked list: {actual_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: expected_resume_titles_checked list: {expected_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: actual_matching_resume_titles list: {actual_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: expected_matching_resume_titles list: {expected_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: actual_matching_keywords list: {actual_results.get('keyword_details', {}).get('matching_keywords', [])}")
    print(f"DEBUG TEST: expected_matching_keywords list: {expected_results.get('keyword_details', {}).get('matching_keywords', [])}")

    # Assert overall score
    assert actual_results.get('score') == expected_results.get('score'), f"Expected overall score {expected_results.get('score')}, but got {actual_results.get('score')}"
    
    # Assert skill details
    assert 'skill_details' in actual_results, "Skill details missing from results"
    assert actual_results['skill_details'].get('score') == expected_results['skill_details'].get('score'), f"Expected skill score {expected_results['skill_details'].get('score')}, but got {actual_results['skill_details'].get('score')}"
    assert sorted(actual_results['skill_details'].get('matching_skills', [])) == sorted(expected_results['skill_details'].get('matching_skills', [])), "Matching skills list mismatch"
    assert sorted(actual_results['skill_details'].get('required_skills', [])) == sorted(expected_results['skill_details'].get('required_skills', [])), "Required skills list mismatch"
    assert sorted(actual_results['skill_details'].get('resume_skills', [])) == sorted(expected_results['skill_details'].get('resume_skills', [])), "Resume skills list mismatch"
    assert actual_results['skill_details'].get('match_count') == expected_results['skill_details'].get('match_count'), "Skill match count mismatch"
    assert actual_results['skill_details'].get('required_count') == expected_results['skill_details'].get('required_count'), "Skill required count mismatch"

    # Assert experience details
    assert 'experience_details' in actual_results, "Experience details missing from results"
    assert actual_results['experience_details'].get('score') == expected_results['experience_details'].get('score'), f"Expected experience score {expected_results['experience_details'].get('score')}, but got {actual_results['experience_details'].get('score')}"
    assert actual_results['experience_details'].get('resume_years') == expected_results['experience_details'].get('resume_years'), "Resume years mismatch"
    assert actual_results['experience_details'].get('required_years') == expected_results['experience_details'].get('required_years'), "Required years mismatch"
    
    # Assert education details
    assert 'education_details' in actual_results, "Education details missing from results"
    assert actual_results['education_details'].get('score') == expected_results['education_details'].get('score'), f"Expected education score {expected_results['education_details'].get('score')}, but got {actual_results['education_details'].get('score')}"
    assert actual_results['education_details'].get('resume_level') == expected_results['education_details'].get('resume_level'), "Resume education level mismatch"
    assert actual_results['education_details'].get('required_level') == expected_results['education_details'].get('required_level'), "Required education level mismatch"
    
    # Assert title details
    assert 'title_details' in actual_results, "Title details missing from results"
    assert actual_results['title_details'].get('score') == expected_results['title_details'].get('score'), f"Expected title score {expected_results['title_details'].get('score')}, but got {actual_results['title_details'].get('score')}"
    assert actual_results['title_details'].get('jd_title') == expected_results['title_details'].get('jd_title'), "JD title mismatch"
    assert sorted(actual_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_results['title_details'].get('resume_titles_checked', [])), "Resume titles checked list mismatch"
    assert sorted(actual_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_results['title_details'].get('matching_resume_titles', [])), "Matching resume titles list mismatch"

     # Assert Keyword Details
    assert 'keyword_details' in actual_results, "Keyword details missing from results"
    assert actual_results['keyword_details'].get('score') == expected_results['keyword_details'].get('score'), f"Expected keyword score {expected_results['keyword_details'].get('score')}, but got {actual_results['keyword_details'].get('score')}"
    assert sorted(actual_results['keyword_details'].get('matching_keywords', [])) == sorted(expected_results['keyword_details'].get('matching_keywords', [])), "Matching keywords list mismatch"
    assert actual_results['keyword_details'].get('total_jd_keywords_count') == expected_results['keyword_details'].get('total_jd_keywords_count'), "Total JD keywords count mismatch"

    print("Assert: Checks passed!")



def test_specific_resume04_jd03_pair():
    """
    Tests the matching score for resume_04.json vs job_03.json.
    """

    print("\n--- Testing resume_04 vs job_03 ---")
    
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_04.json','resume')
    jd_data = load_json_data('job_03.json', 'jd')
    print("Arrange: Data loaded.")


    print("Arrange: Defining expected results...")
    expected_skill_score = pytest.approx(0.4,abs=0.001)
    expected_exp_score = pytest.approx(1.0)
    expected_education_score = pytest.approx(1.0)
    expected_title_score = pytest.approx(1.0)


    # These are verified with debug_matcher.py output 
    expected_total_jd_keywords_count = 32 
    expected_matching_keywords = sorted(['python', 'reports', 'using']) 
    expected_keyword_score = pytest.approx(len(expected_matching_keywords) / expected_total_jd_keywords_count, abs=0.001) if expected_total_jd_keywords_count > 0 else pytest.approx(1.0) # Calculated based on verified counts
   

    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.3) + 
        (expected_exp_score.expected * 0.2) + 
        (expected_education_score.expected * 0.1) + 
        (expected_title_score.expected * 0.1) + 
        (expected_keyword_score.expected * 0.3), 
        abs=0.001
    )

    expected_results = {
        'score': expected_overall_score, 
        'skill_details': {
            'score': expected_skill_score,
            'matching_skills': sorted(['Python', 'SQL']), 
            'required_skills': sorted(['NumPy', 'data analysis', 'pandas', 'Python', 'SQL']), 
            'resume_skills': sorted(['Python', 'SQL', 'Tableau']),
            'match_count': 2, 
            'required_count': 5 
        },
        'experience_details': {
            'score': expected_exp_score,
            'resume_years': 7.3, 
            'required_years': 2 
        },
        'education_details': {
            'score': expected_education_score,
            'resume_level': 3, 
            'required_level': None 
        },
        'title_details': {
            'score': expected_title_score,
            'jd_title': 'Data Analyst', 
            'resume_titles_checked': ['Data Analyst', 'Business Analyst'], 
            'matching_resume_titles': ['Data Analyst'] 
        },
        'keyword_details': {
            'score': expected_keyword_score,
            'matching_keywords': expected_matching_keywords, 
            'total_jd_keywords_count': expected_total_jd_keywords_count
        }
    }

    print("Arrange: Defined expected results.")


    # --- Act ---
    print("Act: Calling calculate_match_score...")
    actual_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={actual_results.get('score')}, skill_score={actual_results.get('skill_details',{}).get('score')}, exp_score={actual_results.get('experience_details',{}).get('score')}, edu_score={actual_results.get('education_details',{}).get('score')}, title_score={actual_results.get('title_details',{}).get('score')}, keyword_score={actual_results.get('keyword_details',{}).get('score')}")
    
    # --- Assert ---
    
    print("Assert: Checking results...")
    print(f"DEBUG TEST: actual_resume_titles_checked list: {actual_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: expected_resume_titles_checked list: {expected_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: actual_matching_resume_titles list: {actual_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: expected_matching_resume_titles list: {expected_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: actual_matching_keywords list: {actual_results.get('keyword_details', {}).get('matching_keywords', [])}")
    print(f"DEBUG TEST: expected_matching_keywords list: {expected_results.get('keyword_details', {}).get('matching_keywords', [])}")

    assert actual_results.get('score') == expected_results.get('score'), f"Expected overall score {expected_results.get('score')}, but got {actual_results.get('score')}"

    # Assert skill details
    assert 'skill_details' in actual_results, "Skill details missing from results"
    assert actual_results['skill_details'].get('score') == expected_results['skill_details'].get('score'), f"Expected skill score {expected_results['skill_details'].get('score')}, but got {actual_results['skill_details'].get('score')}"
    assert sorted(actual_results['skill_details'].get('matching_skills', [])) == sorted(expected_results['skill_details'].get('matching_skills', [])), "Matching skills list mismatch"
    assert sorted(actual_results['skill_details'].get('required_skills', [])) == sorted(expected_results['skill_details'].get('required_skills', [])), "Required skills list mismatch"
    assert sorted(actual_results['skill_details'].get('resume_skills', [])) == sorted(expected_results['skill_details'].get('resume_skills', [])), "Resume skills list mismatch"
    assert actual_results['skill_details'].get('match_count') == expected_results['skill_details'].get('match_count'), "Skill match count mismatch"
    assert actual_results['skill_details'].get('required_count') == expected_results['skill_details'].get('required_count'), "Skill required count mismatch"

    # Assert experience details
    assert 'experience_details' in actual_results, "Experience details missing from results"
    assert actual_results['experience_details'].get('score') == expected_results['experience_details'].get('score'), f"Expected experience score {expected_results['experience_details'].get('score')}, but got {actual_results['experience_details'].get('score')}"
    assert actual_results['experience_details'].get('resume_years') == expected_results['experience_details'].get('resume_years'), "Resume years mismatch"
    assert actual_results['experience_details'].get('required_years') == expected_results['experience_details'].get('required_years'), "Required years mismatch"

    # Assert education details
    assert 'education_details' in actual_results, "Education details missing from results"
    assert actual_results['education_details'].get('score') == expected_results['education_details'].get('score'), f"Expected education score {expected_results['education_details'].get('score')}, but got {actual_results['education_details'].get('score')}"
    assert actual_results['education_details'].get('resume_level') == expected_results['education_details'].get('resume_level'), "Resume education level mismatch"
    assert actual_results['education_details'].get('required_level') == expected_results['education_details'].get('required_level'), "Required education level mismatch"

    # Assert title details
    assert 'title_details' in actual_results, "Title details missing from results"
    assert actual_results['title_details'].get('score') == expected_results['title_details'].get('score'), f"Expected title score {expected_results['title_details'].get('score')}, but got {actual_results['title_details'].get('score')}"
    assert actual_results['title_details'].get('jd_title') == expected_results['title_details'].get('jd_title'), "JD title mismatch"
    assert sorted(actual_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_results['title_details'].get('resume_titles_checked', [])), "Resume titles checked list mismatch"
    assert sorted(actual_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_results['title_details'].get('matching_resume_titles', [])), "Matching resume titles list mismatch"

    #Assert Keyword Details 
    assert 'keyword_details' in actual_results, "Keyword details missing from results"
    assert actual_results['keyword_details'].get('score') == expected_results['keyword_details'].get('score'), f"Expected keyword score {expected_results['keyword_details'].get('score')}, but got {actual_results['keyword_details'].get('score')}"
    assert sorted(actual_results['keyword_details'].get('matching_keywords', [])) == sorted(expected_results['keyword_details'].get('matching_keywords', [])), "Matching keywords list mismatch"
    assert actual_results['keyword_details'].get('total_jd_keywords_count') == expected_results['keyword_details'].get('total_jd_keywords_count'), "Total JD keywords count mismatch"


    print("Assert: Checks passed!") 



def test_specific_resume07_jd09_pair():
    """
    Tests the matching score for resume_07.json vs job_09.json.

    This pair tests scenarios with:
    - No skills listed in either the resume or the JD.
    - JD has no minimum education requirement.
    - Resume has unusual or missing job titles in the experience section.
    - No job title overlap.
    - No keyword overlap.

    """

    print("\n--- Testing resume_07 vs job_09 ---")
    
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_07.json','resume')
    jd_data = load_json_data('job_09.json', 'jd')
    print("Arrange: Data loaded.")


    print("Arrange: Defining expected results...")
    expected_skill_score = pytest.approx(1.0)
    expected_exp_score = pytest.approx(1.0)
    expected_education_score = pytest.approx(1.0)
    expected_title_score = pytest.approx(0.0)

    expected_total_jd_keywords_count = 17 
    expected_matching_keywords = sorted([]) 
    expected_keyword_score = pytest.approx(len(expected_matching_keywords) / expected_total_jd_keywords_count, abs=0.001) if expected_total_jd_keywords_count > 0 else pytest.approx(1.0)
   

    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.3) + 
        (expected_exp_score.expected * 0.2) + 
        (expected_education_score.expected * 0.1) + 
        (expected_title_score.expected * 0.1) + 
        (expected_keyword_score.expected * 0.3), 
        abs=0.001 
    )

    expected_results = {
        'score': expected_overall_score,
        'skill_details': {
            'score': expected_skill_score,
            'matching_skills': sorted([]), # No matching skills
            'required_skills': sorted([]), # From job_09 data
            'resume_skills': sorted([]), # From resume_07 data
            'match_count': 0, # Count of matching skills
            'required_count': 0 # Count of required skills in JD
        },
        'experience_details': {
            'score': expected_exp_score,
            'resume_years': 10.3, # From resume_07 data
            'required_years': 3 # From job_09 data
        },
        'education_details': {
            'score': expected_education_score,
            'resume_level': 1, # From resume_07 data (M.Ed)
            'required_level': None # From job_09 data
        },
        'title_details': {
            'score': expected_title_score,
            'jd_title': 'HR Specialist', # From job_09 data
            # Titles from resume_07 experience: "Experience", null. Assuming matcher converts null to ''.
            'resume_titles_checked': ['Experience', ''],
            'matching_resume_titles': [] # No title match found
        },
        'keyword_details': {
            'score': expected_keyword_score,
            'matching_keywords': expected_matching_keywords, # Verified from debug output
            'total_jd_keywords_count': expected_total_jd_keywords_count # Verified from debug output
        }
    }

    print("Arrange: Defined expected results.")


    # --- Act ---
    print("Act: Calling calculate_match_score...")
    actual_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={actual_results.get('score')}, skill_score={actual_results.get('skill_details',{}).get('score')}, exp_score={actual_results.get('experience_details',{}).get('score')}, edu_score={actual_results.get('education_details',{}).get('score')}, title_score={actual_results.get('title_details',{}).get('score')}, keyword_score={actual_results.get('keyword_details',{}).get('score')}")

    # --- Assert ---
    print("Assert: Checking results...")

    print(f"DEBUG TEST: actual_resume_titles_checked list: {actual_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: expected_resume_titles_checked list: {expected_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: actual_matching_resume_titles list: {actual_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: expected_matching_resume_titles list: {expected_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: actual_matching_keywords list: {actual_results.get('keyword_details', {}).get('matching_keywords', [])}")
    print(f"DEBUG TEST: expected_matching_keywords list: {expected_results.get('keyword_details', {}).get('matching_keywords', [])}")
    print(f"DEBUG TEST: actual_resume_skills list: {actual_results.get('skill_details', {}).get('resume_skills', [])}")
    print(f"DEBUG TEST: expected_resume_skills list: {expected_results.get('skill_details', {}).get('resume_skills', [])}")
    print(f"DEBUG TEST: actual_matching_skills list: {actual_results.get('skill_details', {}).get('matching_skills', [])}")
    print(f"DEBUG TEST: expected_matching_skills list: {expected_results.get('skill_details', {}).get('matching_skills', [])}")
    print(f"DEBUG TEST: actual_required_skills list: {actual_results.get('skill_details', {}).get('required_skills', [])}")
    print(f"DEBUG TEST: expected_required_skills list: {expected_results.get('skill_details', {}).get('required_skills', [])}")


    assert actual_results.get('score') == expected_results.get('score'), f"Expected overall score {expected_results.get('score')}, but got {actual_results.get('score')}"

    # Assert skill details
    assert 'skill_details' in actual_results, "Skill details missing from results"
    assert actual_results['skill_details'].get('score') == expected_results['skill_details'].get('score'), f"Expected skill score {expected_results['skill_details'].get('score')}, but got {actual_results['skill_details'].get('score')}"
    assert sorted(actual_results['skill_details'].get('matching_skills', [])) == sorted(expected_results['skill_details'].get('matching_skills', [])), "Matching skills list mismatch"
    assert sorted(actual_results['skill_details'].get('required_skills', [])) == sorted(expected_results['skill_details'].get('required_skills', [])), "Required skills list mismatch"
    assert sorted(actual_results['skill_details'].get('resume_skills', [])) == sorted(expected_results['skill_details'].get('resume_skills', [])), "Resume skills list mismatch"
    assert actual_results['skill_details'].get('match_count') == expected_results['skill_details'].get('match_count'), "Skill match count mismatch"
    assert actual_results['skill_details'].get('required_count') == expected_results['skill_details'].get('required_count'), "Skill required count mismatch"

    
    # Assert experience details
    assert 'experience_details' in actual_results, "Experience details missing from results"
    assert actual_results['experience_details'].get('score') == expected_results['experience_details'].get('score'), f"Expected experience score {expected_results['experience_details'].get('score')}, but got {actual_results['experience_details'].get('score')}"
    assert actual_results['experience_details'].get('resume_years') == expected_results['experience_details'].get('resume_years'), "Resume years mismatch"
    assert actual_results['experience_details'].get('required_years') == expected_results['experience_details'].get('required_years'), "Required years mismatch"


    # Assert education details
    assert 'education_details' in actual_results, "Education details missing from results"
    assert actual_results['education_details'].get('score') == expected_results['education_details'].get('score'), f"Expected education score {expected_results['education_details'].get('score')}, but got {actual_results['education_details'].get('score')}"
    assert actual_results['education_details'].get('resume_level') == expected_results['education_details'].get('resume_level'), "Resume education level mismatch"
    assert actual_results['education_details'].get('required_level') == expected_results['education_details'].get('required_level'), "Required education level mismatch"

    # Assert title details
    assert 'title_details' in actual_results, "Title details missing from results"
    assert actual_results['title_details'].get('score') == expected_results['title_details'].get('score'), f"Expected title score {expected_results['title_details'].get('score')}, but got {actual_results['title_details'].get('score')}"
    assert actual_results['title_details'].get('jd_title') == expected_results['title_details'].get('jd_title'), "JD title mismatch"
    assert sorted(actual_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_results['title_details'].get('resume_titles_checked', [])), "Resume titles checked list mismatch"
    assert sorted(actual_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_results['title_details'].get('matching_resume_titles', [])), "Matching resume titles list mismatch"

    # Assert Keyword Details
    assert 'keyword_details' in actual_results, "Keyword details missing from results"
    assert actual_results['keyword_details'].get('score') == expected_results['keyword_details'].get('score'), f"Expected keyword score {expected_results['keyword_details'].get('score')}, but got {actual_results['keyword_details'].get('score')}"
    assert sorted(actual_results['keyword_details'].get('matching_keywords', [])) == sorted(expected_results['keyword_details'].get('matching_keywords', [])), "Matching keywords list mismatch"
    assert actual_results['keyword_details'].get('total_jd_keywords_count') == expected_results['keyword_details'].get('total_jd_keywords_count'), "Total JD keywords count mismatch"


    print("Assert: Checks passed!")



def test_specific_resume05_jd01_pair():

    """
    Tests the matching score for resume_05.json vs job_01.json.

    """

    print("\n--- Testing resume_05 vs job_01 ---")
    
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_05.json','resume')
    jd_data = load_json_data('job_01.json', 'jd')
    print("Arrange: Data loaded.")


    print("Arrange: Defining expected results...")
    expected_skill_score = pytest.approx(0.0)
    expected_exp_score = pytest.approx(1.0)
    expected_education_score = pytest.approx(0.0)
    expected_title_score = pytest.approx(0.0)
    

    expected_total_jd_keywords_count = 49 # Verified from debug output for resume_05 vs job_01
    expected_matching_keywords = sorted(['in']) # Verified from debug output for resume_05 vs job_01
    expected_keyword_score = pytest.approx(len(expected_matching_keywords) / expected_total_jd_keywords_count, abs=0.001) if expected_total_jd_keywords_count > 0 else pytest.approx(1.0)


    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.3) + 
        (expected_exp_score.expected * 0.2) + 
        (expected_education_score.expected * 0.1) + 
        (expected_title_score.expected * 0.1) + 
        (expected_keyword_score.expected * 0.3), 
        abs=0.001 
    )

    expected_results = {
        'score': expected_overall_score, # Calculated above
        'skill_details': {
            'score': expected_skill_score,
            'matching_skills': sorted([]), # No matching skills
            'required_skills': sorted(["Azure", "GCP", "Docker", "CI/CD", "Django", "Python", "AWS", "SQL", "Flask", "Kubernetes", "Git"]), # From job_01 data
            'resume_skills': sorted(["Figma", "Illustrator", "Photoshop"]), # From resume_05 data
            'match_count': 0, # Count of matching skills
            'required_count': 11 # Count of required skills in JD
        },
        'experience_details': {
            'score': expected_exp_score,
            'resume_years': 9.3, # From resume_05 data
            'required_years': 5 # From job_01 data
        },
        'education_details': {
            'score': expected_education_score,
            'resume_level': -1, # From resume_05 data
            'required_level': 3 # From job_01 data
        },
        'title_details': {
            'score': expected_title_score,
            'jd_title': 'Senior Python Developer', # From job_01 data
            'resume_titles_checked': ['Experience', 'Junior Designer'], # Titles from resume_05 experience
            'matching_resume_titles': [] # No title match found
        },
        # --- Add Keyword Details (NEW) ---
        'keyword_details': {
            'score': expected_keyword_score,
            'matching_keywords': expected_matching_keywords, # Verified from debug output
            'total_jd_keywords_count': expected_total_jd_keywords_count # Verified from debug output
        }
    }

    print("Arrange: Defined expected results.")

     # --- Act ---
    print("Act: Calling calculate_match_score...")
    actual_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={actual_results.get('score')}, skill_score={actual_results.get('skill_details',{}).get('score')}, exp_score={actual_results.get('experience_details',{}).get('score')}, edu_score={actual_results.get('education_details',{}).get('score')}, title_score={actual_results.get('title_details',{}).get('score')}, keyword_score={actual_results.get('keyword_details',{}).get('score')}")


    # --- Assert ---
    print("Assert: Checking results...")

    #debug prints
    print(f"DEBUG TEST: actual_resume_titles_checked list: {actual_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: expected_resume_titles_checked list: {expected_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: actual_matching_resume_titles list: {actual_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: expected_matching_resume_titles list: {expected_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: actual_matching_keywords list: {actual_results.get('keyword_details', {}).get('matching_keywords', [])}")
    print(f"DEBUG TEST: expected_matching_keywords list: {expected_results.get('keyword_details', {}).get('matching_keywords', [])}")
    print(f"DEBUG TEST: actual_resume_skills list: {actual_results.get('skill_details', {}).get('resume_skills', [])}")
    print(f"DEBUG TEST: expected_resume_skills list: {expected_results.get('skill_details', {}).get('resume_skills', [])}")
    print(f"DEBUG TEST: actual_matching_skills list: {actual_results.get('skill_details', {}).get('matching_skills', [])}")
    print(f"DEBUG TEST: expected_matching_skills list: {expected_results.get('skill_details', {}).get('matching_skills', [])}")
    print(f"DEBUG TEST: actual_required_skills list: {actual_results.get('skill_details', {}).get('required_skills', [])}")
    print(f"DEBUG TEST: expected_required_skills list: {expected_results.get('skill_details', {}).get('required_skills', [])}")


    # Assert overall score
    assert actual_results.get('score') == expected_results.get('score'), f"Expected overall score {expected_results.get('score')}, but got {actual_results.get('score')}"

    # Assert skill details
    assert 'skill_details' in actual_results, "Skill details missing from results"
    assert actual_results['skill_details'].get('score') == expected_results['skill_details'].get('score'), f"Expected skill score {expected_results['skill_details'].get('score')}, but got {actual_results['skill_details'].get('score')}"
    assert sorted(actual_results['skill_details'].get('matching_skills', [])) == sorted(expected_results['skill_details'].get('matching_skills', [])), "Matching skills list mismatch"
    assert sorted(actual_results['skill_details'].get('required_skills', [])) == sorted(expected_results['skill_details'].get('required_skills', [])), "Required skills list mismatch"
    assert sorted(actual_results['skill_details'].get('resume_skills', [])) == sorted(expected_results['skill_details'].get('resume_skills', [])), "Resume skills list mismatch"
    assert actual_results['skill_details'].get('match_count') == expected_results['skill_details'].get('match_count'), "Skill match count mismatch"
    assert actual_results['skill_details'].get('required_count') == expected_results['skill_details'].get('required_count'), "Skill required count mismatch"


    # Assert experience details
    assert 'experience_details' in actual_results, "Experience details missing from results"
    assert actual_results['experience_details'].get('score') == expected_results['experience_details'].get('score'), f"Expected experience score {expected_results['experience_details'].get('score')}, but got {actual_results['experience_details'].get('score')}"
    assert actual_results['experience_details'].get('resume_years') == expected_results['experience_details'].get('resume_years'), "Resume years mismatch"
    assert actual_results['experience_details'].get('required_years') == expected_results['experience_details'].get('required_years'), "Required years mismatch"


    # Assert education details
    assert 'education_details' in actual_results, "Education details missing from results"
    assert actual_results['education_details'].get('score') == expected_results['education_details'].get('score'), f"Expected education score {expected_results['education_details'].get('score')}, but got {actual_results['education_details'].get('score')}"
    assert actual_results['education_details'].get('resume_level') == expected_results['education_details'].get('resume_level'), "Resume education level mismatch"
    assert actual_results['education_details'].get('required_level') == expected_results['education_details'].get('required_level'), "Required education level mismatch"


    # Assert title details
    assert 'title_details' in actual_results, "Title details missing from results"
    assert actual_results['title_details'].get('score') == expected_results['title_details'].get('score'), f"Expected title score {expected_results['title_details'].get('score')}, but got {actual_results['title_details'].get('score')}"
    assert actual_results['title_details'].get('jd_title') == expected_results['title_details'].get('jd_title'), "JD title mismatch"
    assert sorted(actual_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_results['title_details'].get('resume_titles_checked', [])), "Resume titles checked list mismatch"
    assert sorted(actual_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_results['title_details'].get('matching_resume_titles', [])), "Matching resume titles list mismatch"


    # --- Assert Keyword Details (NEW) ---
    assert 'keyword_details' in actual_results, "Keyword details missing from results"
    assert actual_results['keyword_details'].get('score') == expected_results['keyword_details'].get('score'), f"Expected keyword score {expected_results['keyword_details'].get('score')}, but got {actual_results['keyword_details'].get('score')}"
    assert sorted(actual_results['keyword_details'].get('matching_keywords', [])) == sorted(expected_results['keyword_details'].get('matching_keywords', [])), "Matching keywords list mismatch"
    assert actual_results['keyword_details'].get('total_jd_keywords_count') == expected_results['keyword_details'].get('total_jd_keywords_count'), "Total JD keywords count mismatch"


    print("Assert: Checks passed!")

 

def test_specific_resume01_jd11_pair():
    """
    Tests the matching score for resume_01.json vs job_11.json(modified j01)

    """

    print("\n--- Testing resume_01 vs job_11 ---")
    
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_01.json','resume')
    jd_data = load_json_data('job_11.json', 'jd')
    print("Arrange: Data loaded.")


    print("Arrange: Defining expected results...")
    expected_skill_score = pytest.approx(2/11)
    expected_exp_score = pytest.approx(1.0)
    expected_education_score = pytest.approx(0.0)
    expected_title_score = pytest.approx(1.0)


    #Expected Keyword Details verified with debug_matcher.py output
    expected_total_jd_keywords_count = 49
    expected_matching_keywords = sorted(['and', 'to'])
    expected_keyword_score = pytest.approx(len(expected_matching_keywords) / expected_total_jd_keywords_count, abs=0.001) if expected_total_jd_keywords_count > 0 else pytest.approx(1.0)


    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.3) + 
        (expected_exp_score.expected * 0.2) + 
        (expected_education_score.expected * 0.1) + 
        (expected_title_score.expected * 0.1) + 
        (expected_keyword_score.expected * 0.3),
        abs=0.001 
    )
    
    expected_results = {
        'score': expected_overall_score,
        'skill_details': {
            'score': expected_skill_score,
            'matching_skills': sorted(["Python", "SQL"]), 
            'required_skills': sorted(["Azure", "GCP", "Docker", "CI/CD", "Django", "Python", "AWS", "SQL", "Flask", "Kubernetes", "Git"]), # From job_11 data
            'resume_skills': sorted(["JavaScript", "Node.js", "Python", "React", "SQL"]), 
            'match_count': 2, # Count of matching skills
            'required_count': 11 # Count of required skills in JD
        },
        'experience_details': {
            'score': expected_exp_score,
            'resume_years': 7.3, # From resume_01 data
            'required_years': 7 # From job_11 data
        },
        'education_details': {
            'score': expected_education_score,
            'resume_level': 3, # From resume_01 data
            'required_level': 4 # From job_11 data
        },
         'title_details': {
            'score': expected_title_score,
            'jd_title': 'Senior Python Developer', # From job_11 data
            'resume_titles_checked': ['Senior Software Engineer', 'Software Developer'], # From resume_01 data
            'matching_resume_titles': ['Senior Software Engineer'] # Based on first match
        },
        'keyword_details': {
            'score': expected_keyword_score,
            'matching_keywords': expected_matching_keywords, # Verified from debug output
            'total_jd_keywords_count': expected_total_jd_keywords_count # Verified from debug output
        }
    }

    print("Arrange: Defined expected results.")

    # Act 
    print("Act: Calling calculate_match_score...")
    actual_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={actual_results.get('score')}, skill_score={actual_results.get('skill_details',{}).get('score')}, exp_score={actual_results.get('experience_details',{}).get('score')}, edu_score={actual_results.get('education_details',{}).get('score')}, title_score={actual_results.get('title_details',{}).get('score')}, keyword_score={actual_results.get('keyword_details',{}).get('score')}")

    
    # --- Assert ---
    print("Assert: Checking results...")

    print(f"DEBUG TEST: actual_resume_titles_checked list: {actual_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: expected_resume_titles_checked list: {expected_results.get('title_details', {}).get('resume_titles_checked', [])}")
    print(f"DEBUG TEST: actual_matching_resume_titles list: {actual_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: expected_matching_resume_titles list: {expected_results.get('title_details', {}).get('matching_resume_titles', [])}")
    print(f"DEBUG TEST: actual_matching_keywords list: {actual_results.get('keyword_details', {}).get('matching_keywords', [])}")
    print(f"DEBUG TEST: expected_matching_keywords list: {expected_results.get('keyword_details', {}).get('matching_keywords', [])}")
    print(f"DEBUG TEST: actual_resume_skills list: {actual_results.get('skill_details', {}).get('resume_skills', [])}")
    print(f"DEBUG TEST: expected_resume_skills list: {expected_results.get('skill_details', {}).get('resume_skills', [])}")
    print(f"DEBUG TEST: actual_matching_skills list: {actual_results.get('skill_details', {}).get('matching_skills', [])}")
    print(f"DEBUG TEST: expected_matching_skills list: {expected_results.get('skill_details', {}).get('matching_skills', [])}")
    print(f"DEBUG TEST: actual_required_skills list: {actual_results.get('skill_details', {}).get('required_skills', [])}")
    print(f"DEBUG TEST: expected_required_skills list: {expected_results.get('skill_details', {}).get('required_skills', [])}")


    # Assert overall score
    assert actual_results.get('score') == expected_results.get('score'), f"Expected overall score {expected_results.get('score')}, but got {actual_results.get('score')}"

    # Assert skill details
    assert 'skill_details' in actual_results, "Skill details missing from results"
    assert actual_results['skill_details'].get('score') == expected_results['skill_details'].get('score'), f"Expected skill score {expected_results['skill_details'].get('score')}, but got {actual_results['skill_details'].get('score')}"
    assert sorted(actual_results['skill_details'].get('matching_skills', [])) == sorted(expected_results['skill_details'].get('matching_skills', [])), "Matching skills list mismatch"
    assert sorted(actual_results['skill_details'].get('required_skills', [])) == sorted(expected_results['skill_details'].get('required_skills', [])), "Required skills list mismatch"
    assert sorted(actual_results['skill_details'].get('resume_skills', [])) == sorted(expected_results['skill_details'].get('resume_skills', [])), "Resume skills list mismatch"
    assert actual_results['skill_details'].get('match_count') == expected_results['skill_details'].get('match_count'), "Skill match count mismatch"
    assert actual_results['skill_details'].get('required_count') == expected_results['skill_details'].get('required_count'), "Skill required count mismatch"


    # Assert experience details
    assert 'experience_details' in actual_results, "Experience details missing from results"
    assert actual_results['experience_details'].get('score') == expected_results['experience_details'].get('score'), f"Expected experience score {expected_results['experience_details'].get('score')}, but got {actual_results['experience_details'].get('score')}"
    assert actual_results['experience_details'].get('resume_years') == expected_results['experience_details'].get('resume_years'), "Resume years mismatch"
    assert actual_results['experience_details'].get('required_years') == expected_results['experience_details'].get('required_years'), "Required years mismatch"


    # Assert education details
    assert 'education_details' in actual_results, "Education details missing from results"
    assert actual_results['education_details'].get('score') == expected_results['education_details'].get('score'), f"Expected education score {expected_results['education_details'].get('score')}, but got {actual_results['education_details'].get('score')}"
    assert actual_results['education_details'].get('resume_level') == expected_results['education_details'].get('resume_level'), "Resume education level mismatch"
    assert actual_results['education_details'].get('required_level') == expected_results['education_details'].get('required_level'), "Required education level mismatch"


    # Assert title details
    assert 'title_details' in actual_results, "Title details missing from results"
    assert actual_results['title_details'].get('score') == expected_results['title_details'].get('score'), f"Expected title score {expected_results['title_details'].get('score')}, but got {actual_results['title_details'].get('score')}"
    assert actual_results['title_details'].get('jd_title') == expected_results['title_details'].get('jd_title'), "JD title mismatch"
    assert sorted(actual_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_results['title_details'].get('resume_titles_checked', [])), "Resume titles checked list mismatch"
    assert sorted(actual_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_results['title_details'].get('matching_resume_titles', [])), "Matching resume titles list mismatch"


    # Assert Keyword Details
    assert 'keyword_details' in actual_results, "Keyword details missing from results"
    assert actual_results['keyword_details'].get('score') == expected_results['keyword_details'].get('score'), f"Expected keyword score {expected_results['keyword_details'].get('score')}, but got {actual_results['keyword_details'].get('score')}"
    assert sorted(actual_results['keyword_details'].get('matching_keywords', [])) == sorted(expected_results['keyword_details'].get('matching_keywords', [])), "Matching keywords list mismatch"
    assert actual_results['keyword_details'].get('total_jd_keywords_count') == expected_results['keyword_details'].get('total_jd_keywords_count'), "Total JD keywords count mismatch"


    print("Assert: Checks passed!")