from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Assignment, StudentSubmission
from .forms import AssignmentCreateForm, SubmissionForm, QuestionFeedbackFormSet
from accounts.models import Classroom
from assignments.grader import extract_text_from_pdf, parse_question_bank, grade_answer
from accounts.views import calculate_total_marks   # ← your helper
from django.http import HttpResponseForbidden

@login_required
def edit_submission_marks(request, submission_id):
    submission = get_object_or_404(StudentSubmission, id=submission_id)

    if request.user != submission.assignment.teacher:
        return HttpResponseForbidden("Not allowed")

    # Use queryset, not instance
    queryset = submission.question_feedback.all()

    if request.method == "POST":
        formset = QuestionFeedbackFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            submission.recompute_grade()
            return redirect('assignments:view_submissions', assignment_id=submission.assignment.id)
        else:
            print("Formset errors:", formset.errors)
    else:
        formset = QuestionFeedbackFormSet(queryset=queryset)

    return render(request, 'edit_submission_marks.html', {
        'formset': formset,
        'submission': submission
    })



@login_required
def update_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, teacher=request.user)

    if request.method == 'POST':
        form = AssignmentCreateForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            form.save()
            
            if 'question_solution_file' in request.FILES:
                assignment.total_marks = calculate_total_marks(assignment)
                assignment.save()
            return redirect('classroom_detail', pk=assignment.classroom.pk)
    else:
        form = AssignmentCreateForm(instance=assignment)

    return render(request, 'assignments/edit_assignment.html', {'form': form})


@login_required
def create_assignment(request, classroom_id):
    """
    Create a new assignment for the given classroom.
    Classroom is supplied only by the URL, never by the form.
    """
    classroom = get_object_or_404(Classroom, pk=classroom_id)

    if request.method == "POST":
        form = AssignmentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher   = request.user          # current teacher
            assignment.classroom = classroom             # from URL param
            assignment.save()                            # get PK first

            # ── Calculate & store total marks (solution PDF required) ──
            if assignment.question_solution_file:
                assignment.total_marks = calculate_total_marks(assignment)
                assignment.save(update_fields=["total_marks"])

            return redirect("accounts:classroom_detail", pk=classroom.pk)
    else:
        form = AssignmentCreateForm()

    return render(
        request,
        "create_assignment.html",
        {"form": form, "classroom": classroom}
    )

@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student = request.user
            submission.assignment = assignment
            submission.save()
            print(submission.submitted_file.path)
            return redirect('accounts:student_dashboard')  # or show a submission confirmation
    else:
        form = SubmissionForm()
    return render(request, 'submit_assignment.html', {'form': form, 'assignment': assignment})

def view_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = assignment.submissions.all()

    total_marks = calculate_total_marks(assignment)
    is_student = hasattr(request.user, 'student_profile')

    return render(request, 'view_submissions.html', {
        'assignment': assignment,
        'submissions': submissions,
        'total_marks': total_marks,
        'is_student': is_student,
    })

def calculate_total_marks(assignment):
    solution_pdf_path = assignment.question_solution_file.path
    try:
        text = extract_text_from_pdf(solution_pdf_path)
        parsed = parse_question_bank(text)

        total_marks = 0
        for qid, qdata in parsed.items():
            if qdata['subparts']:
                for sub in qdata['subparts'].values():
                    total_marks += sub['marks']
            else:
                total_marks += qdata['marks']
        return total_marks
    except Exception as e:
        print(f"Error calculating marks: {e}")
        return 0  # Fallback if parsing fails
