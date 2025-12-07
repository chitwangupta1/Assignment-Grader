import fitz
import re
import time
import random
# from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
import google.generativeai as genai
import os

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

        main_q_match = re.match(r'^(Q\d+)\.\s*(.*?)\s*\((\d+)\s*marks\)', line, re.IGNORECASE)
        if main_q_match:
            if current_q_no:
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

        subpart_match = re.match(r'^\((i+)\)\s*(.*?)\s*\((\d+)\s*marks\)', line)
        if subpart_match:
            roman = subpart_match.group(1)
            sub_q = subpart_match.group(2).strip()
            sub_m = int(subpart_match.group(3))
            subparts[roman] = {'question': sub_q, 'marks': sub_m, 'answer': ''}
            continue

        ans_part_match = re.match(r'^Ans\s*\((i+)\)\s*:\s*(.*)', line)
        if ans_part_match:
            roman = ans_part_match.group(1)
            ans_text = ans_part_match.group(2).strip()
            if roman in subparts:
                subparts[roman]['answer'] = ans_text
            continue

        ans_match = re.match(r'^Ans\s*:\s*(.*)', line)
        if ans_match:
            current_answer = ans_match.group(1).strip()
            continue

        elif current_answer != "":
            current_answer += ' ' + line

        elif any(subparts.values()) and any(p['answer'] == "" for p in subparts.values()):
            for key in subparts:
                if subparts[key]['answer'] == "":
                    subparts[key]['answer'] = line
                    break

    if current_q_no:
        questions[current_q_no] = {
            'question': current_question,
            'marks': current_marks,
            'answer': current_answer,
            'subparts': subparts
        }

    return questions


def grade_answer(teacher_ans, student_ans, marks, model, is_objective=False):
    if is_objective:
        return (marks if teacher_ans.strip().lower() == student_ans.strip().lower() else 0.0, f"Objective match: {'Correct' if teacher_ans.strip().lower() == student_ans.strip().lower() else 'Incorrect'}")

    prompt = f"""
    You are an extremely strict grader.

    Grade the student's answer compared to the teacher's answer. Maximum marks = {marks}. You may award partial marks (like 2.5 or 3.75). Use the scale below:

    - Full marks: Perfectly matches teacher's answer in content and depth.
    - Slightly less: Minor deviations but mostly correct.
    - Half marks: Basic understanding but missing minor elements.
    - Low marks: Many inaccuracies, shallow understanding and missing major elements.
    - Zero: Completely wrong or irrelevant.

    Teacher's Answer:
    {teacher_ans}

    Student's Answer:
    {student_ans}

    First line should contain just the score out of {marks}, then detailed feedback.
    Example:
    3.5
    Good explanation but lacks depth on edge cases.
    """

    try:
        response = model.generate_content(prompt)
        # response = model.invoke(prompt)
        raw = response.text.strip()
        score_line = raw.split('\n')[0]
        feedback = '\n'.join(raw.split('\n')[1:])
        score = float(score_line.strip())
        if score < 0 or score > marks:
            score = 0.0
            feedback = f"Invalid score parsed. Raw response:\n{raw}"
    except Exception as e:
        score = 0.0
        feedback = f"Error grading answer: {str(e)}"
    return score, feedback


def main():
    teacher_pdf = "Question_Answers_Teacher.pdf"
    student_pdf = "Question_Answers_Student.pdf"

    teacher_text = extract_text_from_pdf(teacher_pdf)
    student_text = extract_text_from_pdf(student_pdf)

    teacher_data = parse_question_bank(teacher_text)
    student_data = parse_question_bank(student_text)

    # llm = ChatGoogleGenerativeAI(model='models/gemini-2.0-flash-thinking-exp')
    
    API_KEY = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=API_KEY)
    
    model = genai.GenerativeModel("gemini-2.0-flash")
    # response = model.generate_content(prompt)

    total_score = 0.0
    total_marks = 0

    for qid in teacher_data:
        q_data = teacher_data[qid]
        s_data = student_data.get(qid, {})
        print(f"\n== Grading {qid}: {q_data['question']} ==")

        if q_data['subparts']:
            for sub_id, sub_q in q_data['subparts'].items():
                t_ans = sub_q['answer']
                s_ans = s_data.get('subparts', {}).get(sub_id, {}).get('answer', '')
                is_obj = sub_q['marks'] == 1
                score, feedback = grade_answer(t_ans, s_ans, sub_q['marks'], llm, is_objective=is_obj)
                total_score += score
                total_marks += sub_q['marks']
                print(f"(Subpart {sub_id}) Score: {score}/{sub_q['marks']}")
                print(f"Feedback: {feedback}\n")
        else:
            t_ans = q_data['answer']
            s_ans = s_data.get('answer', '')
            score, feedback = grade_answer(t_ans, s_ans, q_data['marks'], llm)
            total_score += score
            total_marks += q_data['marks']
            print(f"Score: {score}/{q_data['marks']}")
            print(f"Feedback: {feedback}\n")

    print("== Final Result ==")
    print(f"Total: {total_score:.2f}/{total_marks}")


if __name__ == "__main__":
    main()





