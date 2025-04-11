import re
import spacy
import json
from collections import defaultdict
from datetime import datetime

nlp = spacy.load("en_core_web_sm")

def read_text_file(file_path):
    with open(file_path,'r',encoding='utf-8') as file:
        text = file.read()
    return text

def clean_text(text):
    text = re.sub(r'\s+',' ',text)
    text = text.strip().lower()
    return text


def load_skills(skill_file="skills.json"):
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
                "contact_info":[],
                "experience":[]
    }

    for ent in doc.ents:
        parsed_resume["entities"][ent.label_].append(ent.text)


    for chunk in doc.noun_chunks:

        if any(skill.lower() in chunk.text.lower() for skill in tech_skills):
            parsed_resume["skills"].append(chunk.text.strip())


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

