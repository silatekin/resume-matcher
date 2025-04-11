import re
def read_text_file(file_path):
    with open(file_path,'r',encoding='utf-8') as file:
        text = file.read()
    return text

def clean_text(text):
    text = re.sub(r'\s+',' ',text)
    text = text.strip().lower()
    return text


resume_text = read_text_file("data/resumes/resume_01.txt")
cleaned_text = clean_text(resume_text)
print(cleaned_text[:200])