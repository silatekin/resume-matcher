"""

#-------Experience Extraction--------
    total_experience_duration_days = 0
    extracted_companies = set()
    experience_text = sections.get("experience", "") 

    if "experience" not in parsed_resume:
        parsed_resume["experience"] = []


    COMMON_SECTION_HEADERS = ["experience", "education", "skills", "summary", "objective",
                            "projects", "awards", "references", "publications", "interests",
                            "activities", "volunteer"]

    if experience_text:
        logging.info("Parsing experience from 'experience' section.")

        current_role = {}
        potential_header_lines = [] # Stores text of lines that might be part of a job header

        lines = experience_text.splitlines()
        if lines:
            first_line_cleaned = lines[0].strip().lower()
            # More robust check for experience section header
            if first_line_cleaned.startswith("experience"):
                lines = lines[1:]

        for line_content in lines:
            sent_text = line_content.strip()
            if not sent_text:
                continue

            date_range_pattern = r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{4}|\d{1,2}/\d{4})\s*(?:-|–|to|until)\s*(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{4}|\d{1,2}/\d{4}|Present|Current|Now)\b"
            date_match = re.search(date_range_pattern, sent_text, re.IGNORECASE)
            
            line_is_date = bool(date_match)

            if line_is_date:
                # Date line found: this anchors a new role.
                # Finalize the PREVIOUS role if it was being built from potential_header_lines but hadn't hit its date yet,
                # OR if current_role has a start_date (meaning it was already formed and this is a NEW distinct role).
                if current_role.get("start_date"): # A role was fully formed and active
                    prev_start = current_role.get("start_date")
                    prev_end = current_role.get("end_date")
                    if prev_start and prev_end:
                        try:
                            duration = relativedelta(prev_end, prev_start)
                            total_experience_duration_days += (duration.years * 365.25) + (duration.months * 30.4) + duration.days
                        except TypeError:
                            logging.warning(f"Could not calculate duration for role: {current_role.get('job_title')}")
                    parsed_resume["experience"].append(current_role)
                    logging.debug(f"===> Appended role (new date line found): {current_role.get('job_title') or current_role.get('company')}")
                
                current_role = {} # Reset for the new role defined by this date line
                new_job_title = None
                new_company_name = None

                # 1. Prioritize information from the date line itself (e.g., "Title, Company (Date-Range)")
                start_date_str = date_match.group(1)
                end_date_str = date_match.group(2)
                start_date_obj = kit.parse_date(start_date_str)
                end_date_obj = kit.parse_date(end_date_str)
                
                description_from_date_line = ""
                text_before_date_on_date_line = sent_text[:date_match.start()].strip()
                text_after_date_on_date_line = sent_text[date_match.end():].strip()

                ###trying sth new
                if text_after_date_on_date_line:
                    potential_description = re.sub(r'^[-)*\u2022•·\s]+', '', text_after_date_on_date_line).strip()
                    if potential_description:
                        description_from_date_line = potential_description
                
                if text_before_date_on_date_line: # Contains Title/Company potentially
                    doc_before_date = kit.nlp(text_before_date_on_date_line)
                    for ent in doc_before_date.ents:
                        if ent.label_ == "ORG":
                            new_company_name = ent.text.strip()
                            extracted_companies.add(new_company_name)
                            break 
                    
                    if new_company_name:
                        company_idx = text_before_date_on_date_line.lower().find(new_company_name.lower())
                        if company_idx > 0:
                            title_candidate = text_before_date_on_date_line[:company_idx].strip()
                            title_candidate = re.sub(r'[,|@\s]*at\s*$', '', title_candidate, flags=re.IGNORECASE).strip()
                            title_candidate = re.sub(r'[,|]\s*$', '', title_candidate).strip()
                            if title_candidate and (title_candidate[0].isupper() or title_candidate[0].isnumeric()): # Allow numeric like "1st engineer"
                                new_job_title = title_candidate
                    elif text_before_date_on_date_line and (text_before_date_on_date_line[0].isupper() or text_before_date_on_date_line[0].isnumeric()):
                        # If no company, the whole text before date might be the title
                        new_job_title = text_before_date_on_date_line


                # 2. If title or company still missing, use potential_header_lines (lines before this date line)
                if new_job_title is None or new_company_name is None:
                    for header_text in reversed(potential_header_lines): # Process most recent first
                        if new_job_title and new_company_name: break # Both found

                        doc_header = kit.nlp(header_text)
                        current_header_company = None
                        current_header_title = None

                        # Try to find company on this header line
                        if new_company_name is None:
                            for ent in doc_header.ents:
                                if ent.label_ == "ORG":
                                    new_company_name = ent.text.strip()
                                    extracted_companies.add(new_company_name)
                                    current_header_company = new_company_name # Mark that company came from this line
                                    break
                        
                        # Try to find title on this header line
                        if new_job_title is None:
                            title_candidate_from_header = None
                            if current_header_company: # Company was found on THIS header_text
                                company_idx_h = header_text.lower().find(current_header_company.lower())
                                if company_idx_h > 0:
                                    title_candidate_from_header = header_text[:company_idx_h].strip()
                                    title_candidate_from_header = re.sub(r'[,|@\s]*at\s*$', '', title_candidate_from_header, flags=re.IGNORECASE).strip()
                                    title_candidate_from_header = re.sub(r'[,|]\s*$', '', title_candidate_from_header).strip()
                            
                            if title_candidate_from_header and (title_candidate_from_header[0].isupper() or title_candidate_from_header[0].isnumeric()):
                                new_job_title = title_candidate_from_header
                            else: # Fallback: check for "Title | Possibly Company" or just "Title"
                                parts = header_text.split('|', 1)
                                cand_from_pipe = parts[0].strip()
                                # Avoid using a known section header as job title
                                if cand_from_pipe.lower() not in COMMON_SECTION_HEADERS and \
                                cand_from_pipe and (cand_from_pipe[0].isupper() or cand_from_pipe[0].isnumeric()):
                                    # If it's not an ORG itself (unless it's a very short ORG like "IBM")
                                    is_org_cand = any(e.label_ == "ORG" for e in kit.nlp(cand_from_pipe).ents)
                                    if not is_org_cand or len(cand_from_pipe.split()) <= 2 : # Allow short ORGs as titles if no other title
                                        new_job_title = cand_from_pipe


                current_role = {
                    "job_title": new_job_title,
                    "company": new_company_name,
                    "start_date": start_date_obj,
                    "end_date": end_date_obj,
                    "description": description_from_date_line
                }
                potential_header_lines = [] # Clear buffer

            else: # Line is NOT a date line
                # Determine if this line is a new role's header or part of current role's description
                line_doc = kit.nlp(sent_text)
                is_this_line_a_new_standalone_header = False

                # Stricter check for what constitutes a "new role header" if a role is already active.
                # A new header usually isn't a bullet point and is relatively short / structured.
                if not sent_text.startswith(('-', '*', '\u2022', '•', '·')) and len(sent_text.split()) < 10:
                    temp_title_sh = None
                    temp_company_sh = None
                    has_org_sh = False

                    for ent in line_doc.ents:
                        if ent.label_ == "ORG":
                            has_org_sh = True
                            temp_company_sh = ent.text.strip() # Keep first ORG for potential company
                            extracted_companies.add(temp_company_sh) # Add all ORGs found to global set
                            # break # Don't break, collect all ORGs for extracted_companies

                    if has_org_sh: # Line contains an ORG
                        # If line is like "Title, Company" or "Title | Company" or just "Company"
                        company_idx_sh = sent_text.lower().find(temp_company_sh.lower()) if temp_company_sh else -1
                        if company_idx_sh != -1 : # Company is present
                            if company_idx_sh > 0 : # Potential title before it
                                cand_sh = sent_text[:company_idx_sh].strip()
                                cand_sh = re.sub(r'[,|@\s]*at\s*$', '', cand_sh, flags=re.IGNORECASE).strip()
                                cand_sh = re.sub(r'[,|]\s*$', '', cand_sh).strip()
                                if cand_sh and (cand_sh[0].isupper() or cand_sh[0].isnumeric()) and len(cand_sh.split()) < 7:
                                    temp_title_sh = cand_sh
                            if temp_title_sh or len(sent_text.split()) <=5 : # "Title, Comp" or short "Comp" line
                                is_this_line_a_new_standalone_header = True
                    
                    elif len(sent_text.split()) < 7 and (sent_text[0].isupper() or sent_text[0].isnumeric()) and \
                        sent_text.lower() not in COMMON_SECTION_HEADERS:
                        # Likely a title-only line
                        is_this_line_a_new_standalone_header = True
                
                if is_this_line_a_new_standalone_header:
                    if current_role.get("start_date"): # A role was active, finalize it
                        prev_start_h = current_role.get("start_date")
                        prev_end_h = current_role.get("end_date")
                        if prev_start_h and prev_end_h:
                            try:
                                duration_h = relativedelta(prev_end_h, prev_start_h)
                                total_experience_duration_days += (duration_h.years * 365.25) + (duration_h.months * 30.4) + duration_h.days
                            except TypeError: logging.warning(f"Could not calculate duration: {current_role.get('job_title')}")
                        parsed_resume["experience"].append(current_role)
                        logging.debug(f"===> Appended role (new standalone header found): {current_role.get('job_title') or current_role.get('company')}")
                        current_role = {} # Reset for the new context implied by this header
                    
                    potential_header_lines.append(sent_text)
                
                elif current_role.get("start_date"): # Line is not a date, not a new standalone header, but a role is active
                    current_role["description"] = (current_role.get("description", "") + "\n" + sent_text).strip()
                
                else: # No role active, and not a new standalone header. Add to buffer.
                    # Could be part of a multi-line header or stray text.
                    potential_header_lines.append(sent_text)


        # After the loop, finalize the last current_role if it exists and has data
        if current_role.get("start_date"):
            last_start = current_role.get("start_date")
            last_end = current_role.get("end_date")
            if last_start and last_end:
                try:
                    duration = relativedelta(last_end, last_start)
                    total_experience_duration_days += (duration.years * 365.25) + (duration.months * 30.4) + duration.days
                except TypeError:
                    logging.warning(f"Could not calculate duration for last role: {current_role.get('job_title')}")
            
            parsed_resume["experience"].append(current_role)
            logging.debug(f"\n--- Appending Last Role ---: {current_role.get('job_title') or current_role.get('company')}")

        parsed_resume["total_years_experience"] = round(total_experience_duration_days / 365.25, 1)
        # Storing all mentioned companies, ensure 'parsed_resume' is the main dict for your results
        # parsed_resume["companies_mentioned_in_experience"] = sorted(list(extracted_companies)) 
        logging.info(f"Extracted {len(parsed_resume.get('experience', []))} experience entries. Total calculated years: {parsed_resume.get('total_years_experience',0)}")

    else: # No experience_text found
        parsed_resume["total_years_experience"] = 0
        if "experience" not in parsed_resume: # Defensive
            parsed_resume["experience"] = []
        # parsed_resume["companies_mentioned_in_experience"] = []

"""

#EDU VERSİON V1
"""
#-------Education Extraction--------
    highest_edu_level_found = -1
    if "education" in sections:
        education_text = sections["education"]
        highest_edu_level_found = kit.get_education_level(education_text)
        parsed_resume["education_level"] = highest_edu_level_found 
        education_doc = kit.nlp(education_text)

        for sent in education_doc.sents:
            degree_mention = None
            institution_mention = None
            date_mention = None

            sent_original_text = sent.text.strip() 
            sent_lower = sent_original_text.lower().replace('\xa0', ' ')
            sent_lower = re.sub(r'\b([a-z])\.', r'\1', sent_lower) 

            for keyword,level in sorted(kit.EDUCATION_LEVELS.items(), key=lambda item: len(item[0]), reverse=True):
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern,sent_lower):
                    degree_mention = keyword
                    break
            
            potential_institutions = []
            sentence_entities = sent.ents # Process entities once for the sentence
            for ent in sentence_entities: 
                if ent.label_ == "ORG":
                    is_likely_degree_phrase = False
                    for edu_keyword in kit.EDUCATION_LEVELS.keys(): # Check against education keywords
                        if edu_keyword in ent.text.lower():
                            is_likely_degree_phrase = True
                            break
                    if not is_likely_degree_phrase:
                        potential_institutions.append(ent.text.strip())
                elif ent.label_ == "DATE" and not date_mention: 
                    date_mention = ent.text.strip() # Capture first DATE entity as date_mention
            
            if potential_institutions:
                institution_mention = max(potential_institutions, key=len) # Pick longest ORG as institution

                if institution_mention:
                    # Try to extract a year if it's at the end, possibly in parentheses
                    year_match = re.search(r'^(.*?)(?:\s*\(?(\d{4})\)?\s*)?$', institution_mention)
                    if year_match:
                        cleaned_institution = year_match.group(1).strip()
                        year_from_institution = year_match.group(2)

                        if cleaned_institution: # Ensure there's something left after stripping year
                             institution_mention = cleaned_institution
                        # If date_mention wasn't found from a DATE entity, use the year from institution
                        if year_from_institution and date_mention is None:
                            date_mention = year_from_institution
                        elif year_from_institution and date_mention is not None:
                            # If a DATE entity was found AND a year in institution, prefer specific DATE entity
                            # but log if they are different for review.
                            if year_from_institution not in date_mention:
                                logging.debug(f"Date entity '{date_mention}' differs from year '{year_from_institution}' in institution string: '{sent_original_text}'")
                    
                    # Further cleanup for trailing commas or specific patterns if needed
                    institution_mention = institution_mention.rstrip(',').strip()


            # If date_mention is still None, try a broader search for a year in the sentence
            if date_mention is None:
                year_search = re.search(r'\b(\d{4})\b', sent_original_text)
                if year_search:
                    date_mention = year_search.group(1)

            if degree_mention or institution_mention or date_mention:
                parsed_resume["education_details"].append({
                    "degree_mention": degree_mention, 
                    "institution_mention": institution_mention,
                    "date_mention": date_mention, 
                    "text": sent_original_text 
                })
        logging.info(f"Extracted {len(parsed_resume['education_details'])} education details. Highest level: {highest_edu_level_found}")
    else:
        logging.info("No 'education' section found. Education level remains default.")
        parsed_resume["education_level"] = -1 

"""