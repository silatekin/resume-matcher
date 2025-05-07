import json
import os
import pytest 
import sys
import datetime

"""Follow the Arrange-Act-Assert (AAA) pattern
#
Arrange: Set up the necessary inputs. This involves:
Loading or defining a specific parsed_resume dictionary.
Loading or defining a specific parsed_jd dictionary.
Defining the expected output dictionary 

Act: Call your calculate_match_score function with the arranged inputs.

Assert: Use the testing framework's assertion functions to check if the actual 
output from the function matches your expected output.
"""

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
    
    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.4) +
        (expected_exp_score.expected * 0.3) +
        (expected_education_score.expected * 0.1) +
        (expected_title_score.expected * 0.2),
        abs=0.001
    )

    expected_matching_skills = ['Python', 'SQL']
    expected_jd_title = 'Senior Python Developer'
    expected_resume_titles_checked = ['Senior Software Engineer', 'Software Developer']
    expected_matching_resume_titles = ['Senior Software Engineer']

    print("Arrange: Defined expected results.")

    # --- Act ---
    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}, title_score = {match_results.get('title_details',{}).get('score')}") 

    # --- Assert ---
    print("Assert: Checking results...")

    assert match_results['score'] == expected_overall_score, f"Expected overall score {expected_overall_score.expected}, but got {match_results.get('score')}"
    
    # Assert skill details
    assert 'skill_details' in match_results, "Skill details missing from results"
    assert match_results['skill_details'].get('score') == expected_skill_score, f"Expected skill score {expected_skill_score.expected}, but got {match_results['skill_details'].get('score')}"
    assert sorted(match_results['skill_details'].get('matching_skills', [])) == sorted(expected_matching_skills), "Matching skills list mismatch"

    # Assert experience details
    assert 'experience_details' in match_results, "Experience details missing from results"
    assert match_results['experience_details'].get('score') == expected_exp_score, f"Expected experience score {expected_exp_score.expected}, but got {match_results['experience_details'].get('score')}"
    
    # Assert education details
    assert 'education_details' in match_results, "Education details missing from results"
    assert match_results['education_details'].get('score') == expected_education_score, f"Expected education score {expected_education_score.expected}, but got {match_results['education_details'].get('score')}"
    assert match_results['education_details'].get('resume_level') == 3 
    assert match_results['education_details'].get('required_level') == 3
    
    # Assert title details
    assert 'title_details' in match_results, "Title details missing from results"
    assert match_results['title_details'].get('score') == expected_title_score, f"Expected title score {expected_title_score.expected}, but got {match_results['title_details'].get('score')}"
    assert match_results['title_details'].get('jd_title') == expected_jd_title, f"Expected JD title '{expected_jd_title}', but got '{match_results['title_details'].get('jd_title')}'"
    
    assert sorted(match_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_resume_titles_checked), "Resume titles checked list mismatch"
    assert sorted(match_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_matching_resume_titles), "Matching resume titles list mismatch"

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
    expected_skill_score = pytest.approx(0.4)
    expected_exp_score = pytest.approx(1.0)
    expected_education_score = pytest.approx(1.0)
    expected_title_score = pytest.approx(1.0)

    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.4) +
        (expected_exp_score.expected * 0.3) +
        (expected_education_score.expected * 0.1) +
        (expected_title_score.expected * 0.2),
        abs=0.001
    )
    
    expected_matching_skills = ['Python', 'SQL']
    expected_jd_title = 'Data Analyst'
    expected_resume_titles_checked = ['Data Analyst','Business Analyst']
    expected_matching_resume_titles = ['Data Analyst']

    print("Arrange: Defined expected results.")


    # --- Act ---
    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 
    
    # --- Assert ---
    print("Assert: Checking results...")

    assert match_results['score'] == expected_overall_score, f"Expected overall score {expected_overall_score.expected}, but got {match_results.get('score')}"

    # Assert skill details
    assert 'skill_details' in match_results, "Skill details missing from results"
    assert match_results['skill_details'].get('score') == expected_skill_score, f"Expected skill score {expected_skill_score.expected}, but got {match_results['skill_details'].get('score')}"
    assert sorted(match_results['skill_details'].get('matching_skills', [])) == sorted(expected_matching_skills), "Matching skills list mismatch"
    
    # Assert experience details
    assert 'experience_details' in match_results, "Experience details missing from results"
    assert match_results['experience_details'].get('score') == expected_exp_score, f"Expected experience score {expected_exp_score.expected}, but got {match_results['experience_details'].get('score')}"
    assert match_results['experience_details']['score'] == expected_exp_score
    
    
   # Assert education details
    assert 'education_details' in match_results, "Education details missing from results"
    assert match_results['education_details'].get('score') == expected_education_score, f"Expected education score {expected_education_score.expected}, but got {match_results['education_details'].get('score')}"
    assert match_results['education_details'].get('resume_level') == 3 
    assert match_results['education_details'].get('required_level') == None
        
    # Assert title details
    assert 'title_details' in match_results, "Title details missing from results"
    assert match_results['title_details'].get('score') == expected_title_score, f"Expected title score {expected_title_score.expected}, but got {match_results['title_details'].get('score')}"
    assert match_results['title_details'].get('jd_title') == expected_jd_title, f"Expected JD title '{expected_jd_title}', but got '{match_results['title_details'].get('jd_title')}'"
    
    assert sorted(match_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_resume_titles_checked), "Resume titles checked list mismatch"
    assert sorted(match_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_matching_resume_titles), "Matching resume titles list mismatch"
    
    
    print("Assert: Checks passed!")


def test_specific_resume07_jd09_pair():
    """
    Tests the matching score for resume_07.json vs job_09.json.

    There are no skills listed in either the resume or the JD.

    The JD has no minimum education requirement.

    The resume has unusual or missing job titles in the experience section.

    There is no job title overlap.
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

    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.4) +
        (expected_exp_score.expected * 0.3) +
        (expected_education_score.expected * 0.1) +
        (expected_title_score.expected * 0.2),
        abs=0.001
    )
    
    expected_matching_skills = []
    expected_jd_title = 'HR Specialist'
    expected_resume_titles_checked = ['Experience', '']
    expected_matching_resume_titles = []

    print("Arrange: Defined expected results.")


    # --- Act ---
    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 
    
    # --- Assert ---
    print("Assert: Checking results...")

    assert match_results['score'] == expected_overall_score, f"Expected overall score {expected_overall_score.expected}, but got {match_results.get('score')}"

    # Assert skill details
    assert 'skill_details' in match_results, "Skill details missing from results"
    assert match_results['skill_details'].get('score') == expected_skill_score, f"Expected skill score {expected_skill_score.expected}, but got {match_results['skill_details'].get('score')}"
    assert sorted(match_results['skill_details'].get('matching_skills', [])) == sorted(expected_matching_skills), "Matching skills list mismatch"
    
    # Assert experience details
    assert 'experience_details' in match_results, "Experience details missing from results"
    assert match_results['experience_details'].get('score') == expected_exp_score, f"Expected experience score {expected_exp_score.expected}, but got {match_results['experience_details'].get('score')}"
    assert match_results['experience_details']['score'] == expected_exp_score
    
    
   # Assert education details
    assert 'education_details' in match_results, "Education details missing from results"
    assert match_results['education_details'].get('score') == expected_education_score, f"Expected education score {expected_education_score.expected}, but got {match_results['education_details'].get('score')}"
    assert match_results['education_details'].get('resume_level') == 1 , f"Expected resume education level 1, but got {match_results['education_details'].get('resume_level')}"
    assert match_results['education_details'].get('required_level') is None, f"Expected required education level None, but got {match_results['education_details'].get('required_level')}"
        
    # Assert title details
    assert 'title_details' in match_results, "Title details missing from results"
    assert match_results['title_details'].get('score') == expected_title_score, f"Expected title score {expected_title_score.expected}, but got {match_results['title_details'].get('score')}"
    assert match_results['title_details'].get('jd_title') == expected_jd_title, f"Expected JD title '{expected_jd_title}', but got '{match_results['title_details'].get('jd_title')}'"
    
    assert sorted(match_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_resume_titles_checked), "Resume titles checked list mismatch"
    assert sorted(match_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_matching_resume_titles), "Matching resume titles list mismatch"
    
    
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

    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.4) +
        (expected_exp_score.expected * 0.3) +
        (expected_education_score.expected * 0.1) +
        (expected_title_score.expected * 0.2),
        abs=0.001
    )
    
    expected_matching_skills = []
    expected_jd_title = 'Senior Python Developer'
    expected_resume_titles_checked = ['Experience', 'Junior Designer']
    expected_matching_resume_titles = []

    print("Arrange: Defined expected results.")


    # --- Act ---
    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 
    
    # --- Assert ---
    print("Assert: Checking results...")

    assert match_results['score'] == expected_overall_score, f"Expected overall score {expected_overall_score.expected}, but got {match_results.get('score')}"

    # Assert skill details
    assert 'skill_details' in match_results, "Skill details missing from results"
    assert match_results['skill_details'].get('score') == expected_skill_score, f"Expected skill score {expected_skill_score.expected}, but got {match_results['skill_details'].get('score')}"
    assert sorted(match_results['skill_details'].get('matching_skills', [])) == sorted(expected_matching_skills), "Matching skills list mismatch"
    
    # Assert experience details
    assert 'experience_details' in match_results, "Experience details missing from results"
    assert match_results['experience_details'].get('score') == expected_exp_score, f"Expected experience score {expected_exp_score.expected}, but got {match_results['experience_details'].get('score')}"
    assert match_results['experience_details']['score'] == expected_exp_score
    
    
   # Assert education details
    assert 'education_details' in match_results, "Education details missing from results"
    assert match_results['education_details'].get('score') == expected_education_score, f"Expected education score {expected_education_score.expected}, but got {match_results['education_details'].get('score')}"
    assert match_results['education_details'].get('resume_level') == -1 , f"Expected resume education level 1, but got {match_results['education_details'].get('resume_level')}"
    assert match_results['education_details'].get('required_level') == 3, f"Expected required education level None, but got {match_results['education_details'].get('required_level')}"
        
    # Assert title details
    assert 'title_details' in match_results, "Title details missing from results"
    assert match_results['title_details'].get('score') == expected_title_score, f"Expected title score {expected_title_score.expected}, but got {match_results['title_details'].get('score')}"
    assert match_results['title_details'].get('jd_title') == expected_jd_title, f"Expected JD title '{expected_jd_title}', but got '{match_results['title_details'].get('jd_title')}'"
    
    assert sorted(match_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_resume_titles_checked), "Resume titles checked list mismatch"
    assert sorted(match_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_matching_resume_titles), "Matching resume titles list mismatch"
    
    
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

    expected_overall_score = pytest.approx(
        (expected_skill_score.expected * 0.4) +
        (expected_exp_score.expected * 0.3) +
        (expected_education_score.expected * 0.1) +
        (expected_title_score.expected * 0.2),
        abs=0.001
    )
    
    expected_matching_skills = ['Python', 'SQL']
    expected_jd_title = 'Senior Python Developer'
    expected_resume_titles_checked = ['Senior Software Engineer', 'Software Developer']
    expected_matching_resume_titles = ['Senior Software Engineer']

    print("Arrange: Defined expected results.")


    # --- Act ---
    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 
    
    # --- Assert ---
    print("Assert: Checking results...")

    assert match_results['score'] == expected_overall_score, f"Expected overall score {expected_overall_score.expected}, but got {match_results.get('score')}"

    # Assert skill details
    assert 'skill_details' in match_results, "Skill details missing from results"
    assert match_results['skill_details'].get('score') == expected_skill_score, f"Expected skill score {expected_skill_score.expected}, but got {match_results['skill_details'].get('score')}"
    assert sorted(match_results['skill_details'].get('matching_skills', [])) == sorted(expected_matching_skills), "Matching skills list mismatch"
    
    # Assert experience details
    assert 'experience_details' in match_results, "Experience details missing from results"
    assert match_results['experience_details'].get('score') == expected_exp_score, f"Expected experience score {expected_exp_score.expected}, but got {match_results['experience_details'].get('score')}"
    assert match_results['experience_details']['score'] == expected_exp_score
    
   # Assert education details
    assert 'education_details' in match_results, "Education details missing from results"
    assert match_results['education_details'].get('score') == expected_education_score, f"Expected education score {expected_education_score.expected}, but got {match_results['education_details'].get('score')}"
    assert match_results['education_details'].get('resume_level') == 3 , f"Expected resume education level 1, but got {match_results['education_details'].get('resume_level')}"
    assert match_results['education_details'].get('required_level') == 4, f"Expected required education level None, but got {match_results['education_details'].get('required_level')}"
        
    # Assert title details
    assert 'title_details' in match_results, "Title details missing from results"
    assert match_results['title_details'].get('score') == expected_title_score, f"Expected title score {expected_title_score.expected}, but got {match_results['title_details'].get('score')}"
    assert match_results['title_details'].get('jd_title') == expected_jd_title, f"Expected JD title '{expected_jd_title}', but got '{match_results['title_details'].get('jd_title')}'"
    
    assert sorted(match_results['title_details'].get('resume_titles_checked', [])) == sorted(expected_resume_titles_checked), "Resume titles checked list mismatch"
    assert sorted(match_results['title_details'].get('matching_resume_titles', [])) == sorted(expected_matching_resume_titles), "Matching resume titles list mismatch"
    
    
    print("Assert: Checks passed!")