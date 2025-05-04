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
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_01.json','resume')
    jd_data = load_json_data('job_01.json', 'jd')
    print("Arrange: Data loaded.")


    print("Arrange: Defining expected results...")
    expected_overall_score = pytest.approx(0.591, abs=0.001)
    expected_skill_score = pytest.approx(0.182, abs=0.001) 
    expected_exp_score = pytest.approx(1.0)
    expected_education_score = pytest.approx(1.0)
    expected_matching_skills = ['Python', 'SQL']

    # --- Act ---
    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 

    # --- Assert ---
    print("Assert: Checking results...")
    assert match_results['score'] == expected_overall_score
    assert match_results['skill_details']['score'] == expected_skill_score
    assert match_results['experience_details']['score'] == expected_exp_score
    assert match_results['education_details']['score'] == expected_education_score
    assert sorted(match_results['skill_details']['matching_skills']) == expected_matching_skills
    

    assert 'education_details' in match_results # Check the key exists
    assert match_results['education_details']['resume_level'] == 3 # Check correct resume level was used
    assert match_results['education_details']['required_level'] == 3

    print("Assert: Checks passed!")


def test_specific_resume04_jd03_pair():
    """
    Tests the matching score for resume_04.json vs job_03.json.
    """
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_04.json','resume')
    jd_data = load_json_data('job_03.json', 'jd')
    print("Arrange: Data loaded.")

    print("Arrange: Defining expected results for J03 and R04 ...")

    expected_overall_score = pytest.approx(0.7)
    expected_skill_score = pytest.approx(0.4)
    expected_exp_score = pytest.approx(1.0)
    expected_edu_score = pytest.approx(1.0)
    expected_matching_skills = ['Python', 'SQL']

    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 

    # --- Assert ---
    print("Assert: Checking results...")
    assert match_results['score'] == expected_overall_score
    assert match_results['skill_details']['score'] == expected_skill_score
    assert match_results['experience_details']['score'] == expected_exp_score
    assert match_results['education_details']['score'] == expected_edu_score
    assert sorted(match_results['skill_details']['matching_skills']) == expected_matching_skills
        
    assert 'education_details' in match_results 
    assert match_results['education_details']['resume_level'] == 3 
    assert match_results['education_details']['required_level'] == None
    
    
    print("Assert: Checks passed!")


def test_specific_resume07_jd09_pair():
    """
    Tests the matching score for resume_07.json vs job_09.json.
    """
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_07.json','resume')
    jd_data = load_json_data('job_09.json', 'jd')
    print("Arrange: Data loaded.")

    print("Arrange: Defining expected results for J09 and R07 ...")

    expected_overall_score = pytest.approx(1.0)
    expected_skill_score = pytest.approx(1.0)
    expected_exp_score = pytest.approx(1.0)
    expected_edu_score = pytest.approx(1.0)
    expected_matching_skills = []

    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 

    # --- Assert ---
    print("Assert: Checking results...")
    assert match_results['score'] == expected_overall_score
    assert match_results['skill_details']['score'] == expected_skill_score
    assert match_results['experience_details']['score'] == expected_exp_score
    assert match_results['education_details']['score'] == expected_edu_score
    assert sorted(match_results['skill_details']['matching_skills']) == expected_matching_skills
        
    assert match_results['skill_details']['match_count'] == 0
    assert match_results['skill_details']['required_count'] == 0
    assert match_results['skill_details']['required_skills'] == [] 
    assert match_results['skill_details']['resume_skills'] == [] 

    assert 'education_details' in match_results 
    assert match_results['education_details']['resume_level'] == 1
    assert match_results['education_details']['required_level'] == None

    print("Assert: Checks passed!")


def test_specific_resume09_jd09_pair():
    """
    Tests the matching score for resume_09.json vs job_09.json.
    Changes resume09.json to have 0 years experience
    """
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_09.json','resume')
    jd_data = load_json_data('job_09.json', 'jd')
    print("Arrange: Data loaded.")

    print("Arrange: Defining expected results for J09 and R09 ...")

    expected_overall_score = pytest.approx(1.0)
    expected_skill_score = pytest.approx(1.0)
    expected_exp_score = pytest.approx(1.0)
    expected_edu_score = pytest.approx(1.0)
    expected_matching_skills = []

    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 

    # --- Assert ---
    print("Assert: Checking results...")
    assert match_results['score'] == expected_overall_score
    assert match_results['skill_details']['score'] == expected_skill_score
    assert match_results['experience_details']['score'] == expected_exp_score
    assert match_results['education_details']['score'] == expected_edu_score
    assert sorted(match_results['skill_details']['matching_skills']) == expected_matching_skills

    assert 'education_details' in match_results 
    assert match_results['education_details']['resume_level'] == 3
    assert match_results['education_details']['required_level'] == None
        

    print("Assert: Checks passed!")

def test_specific_resume05_jd01_pair():

    """
    Tests the matching score for resume_05.json vs job_01.json.
    """
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_05.json','resume')
    jd_data = load_json_data('job_01.json', 'jd')
    print("Arrange: Data loaded.")

    print("Arrange: Defining expected results for J01 and R05 ...")

    expected_overall_score = pytest.approx(0.3)
    expected_skill_score = pytest.approx(0.0)
    expected_exp_score = pytest.approx(1.0)
    expected_edu_score = pytest.approx(0.0)
    expected_matching_skills = []

    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 

    # --- Assert ---
    print("Assert: Checking results...")
    assert match_results['score'] == expected_overall_score
    assert match_results['skill_details']['score'] == expected_skill_score
    assert match_results['experience_details']['score'] == expected_exp_score
    assert match_results['education_details']['score'] == expected_edu_score
    assert sorted(match_results['skill_details']['matching_skills']) == expected_matching_skills

    assert 'education_details' in match_results 
    assert match_results['education_details']['resume_level'] == -1
    assert match_results['education_details']['required_level'] == 3
        
    print("Assert: Checks passed!")

def test_specific_resume01_jd11_pair():
    """
    Tests the matching score for resume_01.json vs job_11.json.
    Uses resume_01 and job_11(modified J01).
    """
    #---Arrange---
    print("\nArrange: Loading test data...")
    resume_data = load_json_data('resume_01.json','resume')
    jd_data = load_json_data('job_11.json', 'jd')
    print("Arrange: Data loaded.")

    print("Arrange: Defining expected results for R01 and J11 ...")

    expected_overall_score = pytest.approx(0.3909, abs=0.0001)
    expected_skill_score = pytest.approx(0.1818, abs=0.0001)
    expected_exp_score = pytest.approx(1.0)
    expected_edu_score = pytest.approx(0.0)
    expected_matching_skills = ['Python', 'SQL']

    print("Act: Calling calculate_match_score...")
    match_results = calculate_match_score(resume_data, jd_data)
    print(f"Act: Got results: score={match_results.get('score')}, skill_score={match_results.get('skill_details',{}).get('score')}, exp_score={match_results.get('experience_details',{}).get('score')}, edu_score={match_results.get('education_details',{}).get('score')}") 

    # --- Assert ---
    print("Assert: Checking results...")
    assert match_results['score'] == expected_overall_score
    assert match_results['skill_details']['score'] == expected_skill_score
    assert match_results['experience_details']['score'] == expected_exp_score
    assert match_results['education_details']['score'] == expected_edu_score
    
    assert sorted(match_results['skill_details']['matching_skills']) == expected_matching_skills

    assert 'education_details' in match_results 
    assert match_results['education_details']['resume_level'] == 3
    assert match_results['education_details']['required_level'] == 4
        
    print("Assert: Checks passed!")