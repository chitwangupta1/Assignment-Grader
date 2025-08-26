import fitz
import re
from pprint import pprint

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ''
    for page in doc:
        text += page.get_text()
    return text

def parse_question_bank(text):
    questions = {}
    current_q_no = None
    current_question = ""
    current_marks = 0
    subparts = {}
    question_lines = text.strip().split('\n')

    for line in question_lines:
        line = line.strip()

        # Match main question e.g. "Q1. Define ... (3 marks)"
        main_q_match = re.match(r'^(Q\d+)\.\s*(.*?)\s*\((\d+)\s*marks\)', line, re.IGNORECASE)
        if main_q_match:
            if current_q_no:
                # Save the previous question before moving on
                questions[current_q_no] = {
                    'question': current_question,
                    'marks': current_marks,
                    'answer': current_answer,
                    'subparts': subparts
                }
                subparts = {}

            current_q_no = main_q_match.group(1)
            current_question = main_q_match.group(2).strip()
            current_marks = int(main_q_match.group(3))
            current_answer = ""
            continue

        # Match subpart question e.g. (i) What is ...? (1 marks)
        subpart_match = re.match(r'^\((i+)\)\s*(.*?)\s*\((\d+)\s*marks\)', line)
        if subpart_match:
            roman = subpart_match.group(1)
            sub_q = subpart_match.group(2).strip()
            sub_m = int(subpart_match.group(3))
            subparts[roman] = {'question': sub_q, 'marks': sub_m, 'answer': ''}
            continue

        # Match subpart answer: Ans (i): ...
        ans_part_match = re.match(r'^Ans\s*\((i+)\)\s*:\s*(.*)', line)
        if ans_part_match:
            roman = ans_part_match.group(1)
            ans_text = ans_part_match.group(2).strip()
            if roman in subparts:
                subparts[roman]['answer'] = ans_text
            continue

        # Match main answer: Ans: ...
        ans_match = re.match(r'^Ans\s*:\s*(.*)', line)
        if ans_match:
            current_answer = ans_match.group(1).strip()
            continue

        # If it's a long answer continued from previous line
        elif current_answer != "":
            current_answer += ' ' + line

        elif any(subparts.values()) and any(p['answer'] == "" for p in subparts.values()):
            # Last subpart that doesn't have answer, keep appending
            for key in subparts:
                if subparts[key]['answer'] == "":
                    subparts[key]['answer'] = line
                    break

    # Save last question
    if current_q_no:
        questions[current_q_no] = {
            'question': current_question,
            'marks': current_marks,
            'answer': current_answer,
            'subparts': subparts
        }

    return questions

# === Main Usage ===
if __name__ == "__main__":
    pdf_path = "Question_teacher.pdf"  # Replace with your actual file
    text = extract_text_from_pdf(pdf_path)
    parsed_data = parse_question_bank(text)
    pprint(parsed_data, sort_dicts=False)
