import spacy
import logging
import string
import re


STOP_WORDS = set([
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is", "it", "its",
    "of", "on", "that", "the", "to", "was", "were", "will", "with", "i", "me", "my", "myself", "we",
    "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "him", "his", "himself",
    "she", "her", "hers", "herself", "they", "them", "their", "theirs", "themselves", "what", "which",
    "who", "whom", "this", "those", "am", "been", "being", "have", "had", "having", "do", "does",
    "did", "doing", "but", "if", "or", "because", "until", "while", "through", "about", "against",
    "between", "into", "through", "during", "before", "after", "above", "below", "from", "up", "down",
    "out", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "just", "don",
    "should", "now", "ve", "ll", "d", "m", "o", "re", "y", "ain", "aren", "couldn", "didn", "doesn",
    "hadn", "hasn", "haven", "isn", "let", "ma", "mightn", "mustn", "needn", "shan", "shouldn",
    "wasn", "weren", "won", "wouldn", "also"
])


def clean_and_tokenize(text, nlp_model = None):
    """
    Lowercases, removes punctuation, lemmatizes, removes stop words and short tokens.
    Uses spacy for lemmatization and stop word removal if available.
    """
    if not isinstance(text,str) or not text.strip():
        return set()
    
    text = text.lower()
    text = re.sub(f"[{re.escape(string.punctuation.replace('-', ''))}]", " ", text) 
    text = re.sub(r'\s+', ' ', text).strip()

  
    lemmatized_tokens = set()

    if nlp_model and hasattr(nlp_model, '__call__'):
        doc = nlp_model(text)
        for token in doc:
            if not token.is_stop and not token.is_punct and not token.is_space:
                lemma = token.lemma_.strip()
                if len(lemma) > 1:
                    lemmatized_tokens.add(lemma)
    else:
        tokens = text.split()
        for token in tokens:
            cleaned_token = token.strip()
            if len(cleaned_token)>1 and cleaned_token not in STOP_WORDS:
                lemmatized_tokens.add(cleaned_token)

    return lemmatized_tokens

def calculate_match_score(parsed_resume,parsed_jd,nlp_model):

    if not parsed_resume or not parsed_jd:
        logging.warning("Matcher: Received none for parsed_resume or parsed_jd.")
        return {}

    skill_score = 0.0
    final_score = 0.0

    #---Skill Matching---
    resume_skills_list = [str(s).lower() for s in parsed_resume.get('skills', []) if isinstance(s, str)]
    jd_skills_list = [str(s).lower() for s in parsed_jd.get('skills', []) if isinstance(s, str)]

    resume_skills_set = set(resume_skills_list)
    jd_skills_set = set(jd_skills_list)
    matching_skills_set = resume_skills_set.intersection(jd_skills_set)

    raw_skill_score = 0.0
    if jd_skills_set: 
        raw_skill_score = len(matching_skills_set) / len(jd_skills_set)
    
    # --- Tempering Logic ---
    num_jd_skills = len(jd_skills_set)
    skill_score_confidence = 1.0 # Default confidence
    
    # Define a threshold for what you consider a 'decent' number of skills in a JD
    MIN_SKILLS_FOR_FULL_CONFIDENCE = 4 # Example: need at least 4 skills for full confidence in the score
    
    if num_jd_skills > 0 and num_jd_skills < MIN_SKILLS_FOR_FULL_CONFIDENCE:
        # Scale down the confidence if fewer than threshold skills are in the JD
        skill_score_confidence = num_jd_skills / MIN_SKILLS_FOR_FULL_CONFIDENCE 
        # Example: if JD has 1 skill, confidence = 1/4 = 0.25
        # Example: if JD has 2 skills, confidence = 2/4 = 0.5
    elif num_jd_skills == 0:
        skill_score_confidence = 0.0 # No skills in JD, no confidence in skill match

    skill_score = raw_skill_score * skill_score_confidence
    # --- End of Tempering Logic ---
    
    logging.debug(f"MATCHER Skill Score: {skill_score:.2f} (Raw: {raw_skill_score:.2f}, Confidence: {skill_score_confidence:.2f}), "
                  f"Matching: {matching_skills_set}, Resume: {resume_skills_set}, JD: {jd_skills_set}")

    """
    if(len(jd_skills_set)) > 0:
        skill_score=len(matching_skills_set)/len(jd_skills_set)
    else:
        skill_score = 0.0 #if jd lists have no skills

    """

    #---Experience Years Matching---
    resume_experience_years = parsed_resume.get('total_years_experience',0)
    jd_experience_val = parsed_jd.get('minimum_years_experience',None)
    jd_experience_years = None
    experience_score = 0.0

    if jd_experience_val is not None:
        try:
            jd_experience_years = float(jd_experience_val)
        except(ValueError,TypeError):
            logging.warning(f"Matcher: Could not convert JD experience '{jd_experience_val}' to float.")
            jd_experience_years = None

    if jd_experience_years is None: 
        experience_score = 0.5 
    elif resume_experience_years >= jd_experience_years:
        experience_score = 1.0
    else: 
        experience_score = 0.0
    logging.debug(f"MATCHER Experience Score: {experience_score}, ResumeYrs: {resume_experience_years}, JDYrs: {jd_experience_years}")


    # ---Education Matching---
    resume_edu_level = parsed_resume.get('education_level',-1)
    jd_edu_val = parsed_jd.get('required_education_level',None)
    jd_edu_level = None
    education_score = 0.0

    if jd_edu_level is not None:
        try:
            jd_edu_level = int(jd_edu_level)
        except (ValueError, TypeError):
            logging.warning(f"Matcher: Could not convert JD education level '{jd_edu_val}' to int.")
            jd_edu_level = -1

    if jd_edu_level is None or jd_edu_level < 0: 
        education_score = 0.5 # give more score perhaps?? jd doesn't require or invalid
    elif resume_edu_level < 0: 
        education_score = 0.0 
    elif resume_edu_level >= jd_edu_level:
        education_score = 1.0
    else: #resume level below requirement
        education_score = 0.0
    logging.debug(f"MATCHER Education Score: {education_score}, ResumeLvl: {resume_edu_level}, JDLvl: {jd_edu_level}")


    # Job Title Matching
    jd_title_text = parsed_jd.get('job_title', '')
    resume_experience_list = parsed_resume.get('experience', [])
    title_score = 0.0
    matching_resume_titles_found = []
    all_resume_titles_checked_raw = [
        str(entry.get('job_title', '')) for exp_entry_outer in resume_experience_list
        for entry in (exp_entry_outer if isinstance(exp_entry_outer, list) else [exp_entry_outer])
        if entry and isinstance(entry,dict) and entry.get('job_title')
    ]

    if not jd_title_text.strip(): title_score = 0.5
    # Use the passed-in nlp_model for similarity; ensure it has vectors
    elif nlp_model is None or not hasattr(nlp_model, 'vocab') or not nlp_model.vocab.has_vector:
        logging.warning("MATCHER: Passed NLP model for titles has no vectors or is None. Falling back to Jaccard.")
        jd_title_tokens = clean_and_tokenize(jd_title_text, nlp_model) # Pass nlp_model for tokenization
        max_jaccard_score = 0.0
        if jd_title_tokens and resume_experience_list:
            for exp_entry_outer in resume_experience_list:
                for exp_entry in (exp_entry_outer if isinstance(exp_entry_outer, list) else [exp_entry_outer]):
                    if not exp_entry or not isinstance(exp_entry, dict): continue
                    resume_title_text = exp_entry.get('job_title')
                    if resume_title_text and isinstance(resume_title_text, str) and resume_title_text.strip():
                        resume_title_tokens = clean_and_tokenize(resume_title_text, nlp_model)
                        if resume_title_tokens:
                            common = jd_title_tokens.intersection(resume_title_tokens)
                            union = jd_title_tokens.union(resume_title_tokens)
                            jaccard = len(common) / len(union) if union else 0.0
                            if jaccard > max_jaccard_score: max_jaccard_score, matching_resume_titles_found = jaccard, [resume_title_text]
                            elif jaccard == max_jaccard_score and max_jaccard_score > 0 and resume_title_text not in matching_resume_titles_found:
                                matching_resume_titles_found.append(resume_title_text)
            title_score = max_jaccard_score
    else: # Use spaCy document similarity
        jd_doc = nlp_model(jd_title_text)
        max_similarity_score = 0.0
        if resume_experience_list:
            for exp_entry_outer in resume_experience_list:
                for exp_entry in (exp_entry_outer if isinstance(exp_entry_outer, list) else [exp_entry_outer]):
                    if not exp_entry or not isinstance(exp_entry, dict): continue
                    resume_title_text = exp_entry.get('job_title')
                    if resume_title_text and isinstance(resume_title_text, str) and resume_title_text.strip():
                        resume_doc = nlp_model(resume_title_text)
                        similarity = 0.0
                        if jd_doc.has_vector and resume_doc.has_vector and jd_doc.vector_norm and resume_doc.vector_norm:
                            similarity = jd_doc.similarity(resume_doc)
                        else: logging.warning(f"MATCHER: Missing/zero vectors for title: '{jd_title_text}' vs '{resume_title_text}'")
                        if similarity > max_similarity_score:
                            max_similarity_score, matching_resume_titles_found = similarity, [resume_title_text]
                        elif similarity == max_similarity_score and max_similarity_score > 0 and resume_title_text not in matching_resume_titles_found:
                            matching_resume_titles_found.append(resume_title_text)
            title_score = max_similarity_score
    logging.debug(f"MATCHER Final Title Score: {title_score}")


    # --- Keyword Matching
    jd_keyword_text_parts = []
    # Key JD sections for keywords
    jd_text_sources = ['responsibilities', 'qualifications', 'preferred_qualifications', 
                       'skills_text_raw_kaggle', 'job_description_text_raw_kaggle', 'job_title'] # Added job_title
    for key in jd_text_sources:
        content = parsed_jd.get(key)
        if isinstance(content, list): # e.g., responsibilities, qualifications
            jd_keyword_text_parts.extend([str(item) for item in content if isinstance(item, str)])
        elif isinstance(content, str): # e.g., raw text fields, job_title
            jd_keyword_text_parts.append(content)
    # Also add JD skills list as text
    if parsed_jd.get('skills'):
        jd_keyword_text_parts.append(" ".join([str(s) for s in parsed_jd.get('skills', []) if isinstance(s,str)]))
    jd_full_keyword_text = " ".join(jd_keyword_text_parts)

    resume_keyword_text_parts = []
    # Key resume sections for keywords
    if parsed_resume.get('summary_text'):
        resume_keyword_text_parts.append(str(parsed_resume.get('summary_text')))
    for entry in parsed_resume.get('experience', []):
        if isinstance(entry.get('description'), str):
            resume_keyword_text_parts.append(entry.get('description'))
        if isinstance(entry.get('job_title'), str): # Add job titles from experience
             resume_keyword_text_parts.append(entry.get('job_title'))
    # Also add resume skills list as text
    if parsed_resume.get('skills'):
        resume_keyword_text_parts.append(" ".join([str(s) for s in parsed_resume.get('skills',[]) if isinstance(s,str)]))
    resume_full_keyword_text = " ".join(resume_keyword_text_parts)

    logging.debug(f"MATCHER JD Keyword Text (first 200): {jd_full_keyword_text[:200]}")
    logging.debug(f"MATCHER Resume Keyword Text (first 200): {resume_full_keyword_text[:200]}")

    jd_keyword_tokens = clean_and_tokenize(jd_full_keyword_text)
    resume_keyword_tokens = clean_and_tokenize(resume_full_keyword_text)
    
    logging.debug(f"MATCHER JD Keyword Tokens (count {len(jd_keyword_tokens)}, sample): {list(jd_keyword_tokens)[:20]}")
    logging.debug(f"MATCHER Resume Keyword Tokens (count {len(resume_keyword_tokens)}, sample): {list(resume_keyword_tokens)[:20]}")

    matching_keyword_tokens_set = jd_keyword_tokens.intersection(resume_keyword_tokens)
    # Filter out very common words that might have slipped through basic stop word lists if NLP_TOKENIZER failed
    # This is an additional safeguard.
    common_generic_words = {'role', 'team', 'work', 'experience', 'responsibilities', 'requirements', 'skills', 'job', 'position'}
    final_matching_keywords = matching_keyword_tokens_set - common_generic_words
    matching_keywords_list = sorted(list(final_matching_keywords))


    keyword_score = 0.0
    # Score based on overlap with JD's non-generic keywords
    # Consider only JD tokens that are not too generic for the denominator
    jd_meaningful_tokens = jd_keyword_tokens - common_generic_words
    if jd_meaningful_tokens:
        keyword_score = len(final_matching_keywords) / len(jd_meaningful_tokens)
    elif jd_keyword_tokens: # If all JD tokens were generic, but some existed
        keyword_score = len(final_matching_keywords) / len(jd_keyword_tokens) # Fallback to original denominator

    logging.debug(f"MATCHER Keyword Score: {keyword_score}, Matching count: {len(final_matching_keywords)}, Meaningful JD Kwd Count: {len(jd_meaningful_tokens)}")


    #---Final Score Logic---
    skill_weight = 0.35
    experience_weight = 0.15
    education_weight = 0.05
    title_weight = 0.15
    keyword_weight = 0.30

    final_score = (skill_score * skill_weight) + (experience_score * experience_weight) + \
                 (education_score * education_weight) + (title_score * title_weight)+ \
                 (keyword_score * keyword_weight)
                 
    logging.info(f"MATCHER FINAL SCORE: {final_score:.4f} "
                 f"[Skills: {skill_score:.2f} (w:{skill_weight}), Exp: {experience_score:.2f} (w:{experience_weight}), "
                 f"Edu: {education_score:.2f} (w:{education_weight}), Title: {title_score:.2f} (w:{title_weight}), "
                 f"Keyword: {keyword_score:.2f} (w:{keyword_weight})]")
    
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
            'jd_title': jd_title_text,
            'resume_titles_checked':all_resume_titles_checked_raw,
            'matching_resume_titles': matching_resume_titles_found
        },
        'keyword_details':{
            'score':keyword_score,
            'matching_keywords': matching_keywords_list,
            'matching_keywords_count': len(matching_keywords_list),
            # JD keyword info:
            'jd_total_tokens_initially': len(jd_keyword_tokens), # Total tokens from JD text after initial tokenization
            'jd_meaningful_tokens_for_scoring': sorted(list(jd_meaningful_tokens)), # The set of JD tokens used as the denominator for score (after generic filter)
            'jd_meaningful_tokens_count': len(jd_meaningful_tokens), # The count of these tokens
            
            # Resume keyword info:
            'resume_total_tokens': len(resume_keyword_tokens) # Total tokens from resume text after tokenization
       
        }
    }  
    return results

