import re
import spacy
import json
from collections import defaultdict
from datetime import datetime
from spacy.matcher import PhraseMatcher

nlp = spacy.load("en_core_web_sm")

def read_text_file(file_path):
    with open(file_path,'r',encoding='utf-8') as file:
        text = file.read()
    return text

def clean_text(text):
    text = re.sub(r'\s+',' ',text)
    return text


def load_skills(skill_file="data/skills.json"):
    with open(skill_file, "r") as f:
        return json.load(f)

tech_skills = load_skills()

SECTION_HEADERS = {
    "skills": r"^\s*(skills|technical\s*skills|technical\s*proficiency)\s*[:\n]",
    "education": r"^\s*(education|academic\s*background)\s*[:\n]",
    "experience": r"^\s*(experience|work\s*experience|employment\s*history)\s*[:\n]",
}


def segment_resume(text):
    #header key will act as a default key to catch any text at the very beginning before the first first recognized section heading
    #contact info,name,initial summary etc
    sections = {"header": ""}

    #to keep which section we are currently adding lines t
    current_section_key = "header"

    lines = text.splitlines()

    compiled_patterns = {}


    for key,pattern in SECTION_HEADERS.items():

        compiled_patterns[key] = re.compile(pattern,re.IGNORECASE|re.MULTILINE)

        #temporarily holds all the lines of text belong to section currently being processed
    
    
    current_section_content = []

    for line in lines:
        #to decide if the current line is a section header or regular content
        found_new_section = False

        for key,pattern in compiled_patterns.items():
            if pattern.match(line):
                # Save previous section's content
                sections[current_section_key] = "\n".join(current_section_content).strip()

                #start new section
                current_section_key=key
                current_section_content=[line]
                found_new_section=True
                break
        if not found_new_section:
            current_section_content.append(line)

    sections[current_section_key] = "\n".join(current_section_content).strip()

    return sections



def parse_resume_sections(sections):

    parsed_resume = {
                "entities":defaultdict(list),
                "skills":[],
                "companies":[],
                "education":[],
                "contact_info":{},
                "experience":[]
    }

    #-------Skill Extraction--------
    if "skills" in sections:
        skills_text = sections["skills"]
        skills_doc = nlp(skills_text)

        #PhraseMatcher on skills_doc
        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        patterns = [nlp(skill) for skill in tech_skills if " " in skill]
        matcher.add("TECH_SKILLS",patterns)
        matches = matcher(skills_doc)
        for match_id,start,end in matches:
            span = skills_doc[start:end]
            parsed_resume["skills"].append(span.text)

        #Using Token Matching on skills_doc
        for token in skills_doc:
            lemma = token.lemma_.lower()
            #Avoid adding parts of multiword skills already caught by PhraseMatcher
            #This check is basic, might need refinement
            already_added_multiword = any(lemma in multi for multi in parsed_resume["skills"] if " " in multi) 
            if lemma in tech_skills and token.pos_ in {"NOUN", "PROPN"} and not already_added_multiword:
                # Check if this lemma is part of an already added phrase match? More complex check needed ideally.
                # For simplicity now, we'll add it, duplicates handled later.
                parsed_resume["skills"].append(lemma) # Or token.text


    #-------Education Extraction--------
    if "education" in sections:
        education_text = sections["education"]
        education_doc = nlp(education_text)

        for sent in education_doc.sents:
            edu_info = {
                "text": sent.text,
                "entities": [{"text": ent.text, "type": ent.label_} 
                            for ent in sent.ents]
            }
            parsed_resume["education"].append(edu_info)

    
    #-------Experience Extraction--------

    if "experience" in sections:
        experience_text = sections["experience"]
        experience_doc = nlp(experience_text)

        for ent in experience_doc.ents:
            parsed_resume["entities"][ent.label_].append(ent.text)

            if ent.label_== 'ORG':
                parsed_resume["companies"].append(ent.text)

        # More logic to added here to parse job titles, dates, descriptions


    #-------Contact Info--------
    full_text = "\n".join(sections.values())
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'
    
    emails = re.findall(email_pattern, full_text)
    phones = re.findall(phone_pattern, full_text)
    if emails:
        parsed_resume["contact_info"]["emails"] = list(set(emails))
    if phones:
        parsed_resume["contact_info"]["phones"] = list(set(phones))
        
    
    # --- Final Skill Cleanup ---
    parsed_resume["skills"] = list(set(parsed_resume["skills"]))
    # Remove duplicates from companies too
    parsed_resume["companies"] = list(set(parsed_resume["companies"]))  

    return parsed_resume 
        
      
def save_to_json(data,output_file="output.json"):
    with open(output_file,'w') as f:
        json.dump(data,f,indent=2)



resume_text = read_text_file("data/resumes/resume_01.txt")

segmented_resume = segment_resume(resume_text) 

print("--- Segments Found ---")
print(segmented_resume.keys()) #which sections were identified
print("--- Skills Section Text ---")
print(segmented_resume.get("skills", "Not Found"))
print("--- Experience Section Text ---")
print(segmented_resume.get("experience", "Not Found"))
print("--- Education Section Text ---")
print(segmented_resume.get("education", "Not Found"))
print("--- End Sections ---")

parsed = parse_resume_sections(segmented_resume) 

print("\nCompanies found (likely from Experience):")
for company in parsed["companies"]:
    print("-", company)

print("\nSkills found (likely from Skills section):")
for skill in parsed["skills"]:
    print("-", skill)

print("\nEducation Info found (likely from Education section):")
for edu in parsed["education"]:
    print("-", edu["text"]) 

save_to_json(parsed, "output_segmented.json")