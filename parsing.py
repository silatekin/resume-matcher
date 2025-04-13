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



def parse_resume(text):
    

    doc = nlp(text)

    parsed_resume = {
                "entities":defaultdict(list),
                "skills":[],
                "companies":[],
                "education":[],
                "contact_info":{},
                "experience":[]
    }

    for ent in doc.ents:
        parsed_resume["entities"][ent.label_].append(ent.text)
        if ent.label_ == "ORG":
            parsed_resume["companies"].append(ent.text)


    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp(skill) for skill in tech_skills if " " in skill]
    matcher.add("TECH_SKILLS",patterns)

    matches = matcher(doc)
    for match_id,start,end in matches:
        span = doc[start:end]
        parsed_resume["skills"].append(span.text)


    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in tech_skills and token.pos_ in{"NOUN","PROPN"}:
            parsed_resume["skills"].append(lemma)
            

    #to remove the duplicates
    parsed_resume["skills"] = list(set(parsed_resume["skills"]))


    education_keywords = ["degree", "university", "college", "bachelor", "master", "phd", "school", "education"]
         
    for sent in doc.sents:
        sent_text = sent.text.lower()

        if any(keyword in sent_text for keyword in education_keywords):

            edu_info={
                "text":sent.text,
                "entities":[{"text":ent.text,"type":ent.label_}
                            for ent in sent.ents]            
            }

            parsed_resume["education"].append(edu_info)

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'
    
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)


    if emails:
        parsed_resume["contact_info"]["emails"] = emails
    if phones:
        parsed_resume["contact_info"]["phones"] = phones
        
    return parsed_resume
        
        
      
def save_to_json(data,output_file="output.json"):
    with open(output_file,'w') as f:
        json.dump(data,f,indent=2)


resume_text = read_text_file("data/resumes/resume_01.txt")
cleaned_text = clean_text(resume_text)
parsed = parse_resume(cleaned_text)

print("Companies found:")
for company in parsed["companies"]:
    print("-", company)