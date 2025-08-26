from assignments.models import StudentSubmission
from assignments.grader import extract_text_from_pdf, parse_question_bank, grade_answer
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI


def grade_single_submission(submission: StudentSubmission):
    """
    Grades one StudentSubmission object and updates it with total marks, feedback, and graded status.
    """

    # Extract teacher's solution from assignment
    teacher_text = extract_text_from_pdf(submission.assignment.question_solution_file.path)
    teacher_data = parse_question_bank(teacher_text)
    
    # Initialize your AI grading model (or whatever grading logic you have)
    model = ChatGoogleGenerativeAI(model='models/gemini-2.0-flash-thinking-exp')

    # Extract student's submitted answers
    student_text = extract_text_from_pdf(submission.submitted_file.path)
    student_data = parse_question_bank(student_text)

    total_score = 0
    feedback_parts = []

    # Loop over questions
    for qid in teacher_data:
        q_data = teacher_data[qid]
        s_data = student_data.get(qid, {})

        if q_data['subparts']:
            for sub_id, sub_q in q_data['subparts'].items():
                t_ans = sub_q['answer']
                s_ans = s_data.get('subparts', {}).get(sub_id, {}).get('answer', '')
                is_obj = sub_q['marks'] == 1
                score, fb = grade_answer(t_ans, s_ans, sub_q['marks'], model, is_obj)
                total_score += score
                feedback_parts.append(f"Q{qid}({sub_id}): {fb}")
        else:
            t_ans = q_data['answer']
            s_ans = s_data.get('answer', '')
            score, fb = grade_answer(t_ans, s_ans, q_data['marks'], model)
            total_score += score
            feedback_parts.append(f"Q{qid}: {fb}")

    # Save results in the submission object
    submission.grade = total_score
    submission.feedback = "\n\n".join(feedback_parts)
    submission.graded = True
    submission.save()
