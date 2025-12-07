from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now
from django.db.models import Prefetch, Sum

from .forms import RoleLoginForm, AdminSignUpForm, SubjectCreateForm, TeacherSignUpForm,  ClassroomCreateForm 
from .forms import AdminUpdateForm, StudentSignUpForm, TeacherUpdateForm, StudentUpdateForm

from .models import Subject, Classroom, Teacher
from assignments.models import Assignment, StudentSubmission
from assignments.grader import extract_text_from_pdf, parse_question_bank, grade_answer
# from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
import google.generativeai as genai


from assignments.models import Assignment, StudentSubmission, QuestionFeedback

from assignments.models import Assignment   # or your path

def calculate_total_marks(assignment: Assignment, *, save=False) -> float:
    """
    Parse the solution PDF once, sum all marks (including sub-parts),
    and optionally store the value on the Assignment.
    """
    try:
        text   = extract_text_from_pdf(assignment.question_solution_file.path)
        parsed = parse_question_bank(text)

        total_marks = 0
        for q in parsed.values():
            if q["subparts"]:
                total_marks += sum(sub["marks"] for sub in q["subparts"].values())
            else:
                total_marks += q["marks"]

        if save:
            assignment.total_marks = total_marks
            assignment.save(update_fields=["total_marks"])

        return total_marks

    except Exception as exc:
        print(f"[calculate_total_marks] {exc}")
        return 0.0



from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect

from assignments.models import Assignment, QuestionFeedback


@login_required
def grade_all_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # We grade only on POST to avoid accidental triggers
    if request.method != "POST":
        return redirect("accounts:classroom_detail", pk=assignment.classroom.id)

    # ───────────────────────────────────────────────────────────────
    # 0. Ensure the assignment has an accurate total_max.
    # ───────────────────────────────────────────────────────────────
    if assignment.total_marks == 0:
        calculate_total_marks(assignment, save=True)

    # ───────────────────────────────────────────────────────────────
    # 1. Parse teacher’s solution once and build a dict.
    # ───────────────────────────────────────────────────────────────
    teacher_text = extract_text_from_pdf(assignment.question_solution_file.path)
    teacher_data = parse_question_bank(teacher_text)

    genai.configure(api_key=GOOGLE_API_KEY)

    model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp")


    # ───────────────────────────────────────────────────────────────
    # 2. Loop over every ungraded submission.
    # ───────────────────────────────────────────────────────────────
    for submission in assignment.submissions.filter(graded=False):

        # Parse the student PDF only once
        student_text = extract_text_from_pdf(submission.submitted_file.path)
        student_data = parse_question_bank(student_text)

        # Reset totals for this submission
        total_obtained = 0.0
        per_question_results = []   # list of (qid, max_m, got_m, feedback)

        # ───── Grade question by question ─────
        for qid, q_t in teacher_data.items():

            q_max = 0.0
            q_got = 0.0
            q_fb  = []  # feedback lines for this single question

            # ——— With sub-parts ———
            if q_t["subparts"]:
                for sub_id, sub_t in q_t["subparts"].items():
                    t_ans  = sub_t["answer"]
                    s_ans  = student_data.get(qid, {}).get("subparts", {}).get(sub_id, {}).get("answer", "")
                    is_mcq = sub_t["marks"] == 1

                    marks_got, fb = grade_answer(t_ans, s_ans, sub_t["marks"], model, is_mcq)
                    print(marks_got, fb)
                    q_max += sub_t["marks"]
                    q_got += marks_got
                    q_fb.append(f"({sub_id}) {fb}")

            # ——— No sub-parts ———
            else:
                t_ans  = q_t["answer"]
                s_ans  = student_data.get(qid, {}).get("answer", "")
                marks_got, fb = grade_answer(t_ans, s_ans, q_t["marks"], model)
                q_max += q_t["marks"]
                q_got += marks_got
                q_fb.append(fb)

            per_question_results.append((qid, q_max, q_got, " | ".join(q_fb)))
            total_obtained += q_got

        # ─────────────────────────────────────────────────────────
        # 3. Write everything in *one* transaction per submission.
        # ─────────────────────────────────────────────────────────
        with transaction.atomic():

            # (a) Per-question rows
            for qid, q_max, q_got, q_fb in per_question_results:
                QuestionFeedback.objects.update_or_create(
                    submission      = submission,
                    question_number = qid,
                    defaults        = {
                        "max_marks":      q_max,
                        "obtained_marks": q_got,
                        "feedback":       q_fb,
                    },
                )

            # (b) Submission summary
            submission.feedback = "Overall feedback auto-generated on " + now().strftime("%d %b %Y, %H:%M")
            submission.graded   = True
            submission.save(update_fields=["graded", "feedback"])

            # (c) Recompute total (sets submission.grade)
            submission.recompute_grade()

    # ───────────────────────────────────────────────────────────────
    # 4. Back to classroom page.
    # ───────────────────────────────────────────────────────────────
    return redirect("accounts:classroom_detail", pk=assignment.classroom.id)


def is_teacher(user):
    return hasattr(user, 'teacher_profile')

def is_student(user):
    return hasattr(user, 'student_profile')

def is_admin(user):
    return user.role == 'admin'

@login_required
def update_teacher_profile(request):
    teacher = request.user.teacher_profile
    if request.method == 'POST':
        form = TeacherUpdateForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            return redirect('accounts:teacher_dashboard')
    else:
        form = TeacherUpdateForm(instance=teacher)
    return render(request, 'update_teacher.html', {'form': form})

@login_required
def update_student_profile(request):
    student = request.user.student_profile
    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('accounts:student_dashboard')
    else:
        form = StudentUpdateForm(instance=student)
    return render(request, 'update_student.html', {'form': form})

@login_required
def update_admin_profile(request):
    user = request.user.admin_profile
    if request.method == 'POST':
        form = AdminUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('accounts:admin_dashboard')
    else:
        form = AdminUpdateForm(instance=user)
    return render(request, 'update_admin.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def create_classroom_view(request):
    teacher = request.user.teacher_profile

    if request.method == 'POST':
        form = ClassroomCreateForm(request.POST, teacher=teacher)
        if form.is_valid():
            classroom = form.save(commit=False)
            subject = form.cleaned_data['subject']
            classroom.subject_name = subject.subject_name
            classroom.subject_code = subject.subject_code
            classroom.teacher = request.user
            classroom.save()
            return redirect('accounts:teacher_dashboard')
    else:
        form = ClassroomCreateForm(teacher=teacher)

    classrooms = Classroom.objects.filter(teacher=request.user)

    return render(request, 'teacher_dashboard.html', {
        'form': form,
        'classrooms': classrooms,
        'teacher': teacher,
    })

def teacher_signup_view(request):
    if request.method == 'POST':
        form = TeacherSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:teacher_dashboard')  # Redirect to teacher dashboard
    else:
        form = TeacherSignUpForm()
    return render(request, 'signup_teacher.html', {'form': form})


def is_admin(user):
    return user.is_authenticated and user.user_type == 'administration'

@login_required
@user_passes_test(is_admin)
def create_subject_view(request):
    if request.method == 'POST':
        form = SubjectCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')  # or admin_dashboard
    else:
        form = SubjectCreateForm()
    return render(request, 'create_subject.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    if request.user.user_type != 'administration':
        return redirect('login')

    if request.method == 'POST':
        form = SubjectCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:admin_dashboard')
    else:
        form = SubjectCreateForm()

    subjects = Subject.objects.all()
    return render(request, 'admin_dashboard.html', {
        'form': form,
        'subjects': subjects
    })


def home(request):
    return render(request, 'home.html')


def role_login_view(request):
    if request.method == 'POST':
        form = RoleLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            user = authenticate(request, username=username, password=password)
            if user is not None and user.user_type == role:
                login(request, user)
                # Redirect based on role
                if role == 'administration':
                    return redirect('accounts:admin_dashboard')
                elif role == 'teacher':
                    return redirect('accounts:teacher_dashboard')
                elif role == 'student':
                    return redirect('accounts:student_dashboard')
            else:
                form.add_error(None, "Invalid credentials or role.")
    else:
        form = RoleLoginForm()

    return render(request, 'login.html', {'form': form})


def admin_signup_view(request):
    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Optionally login the user
            from django.contrib.auth import login
            login(request, user)

            return redirect('accounts:admin_dashboard')  # 👈 make sure this name matches your URLconf
    else:
        form = AdminSignUpForm()

    return render(request, 'signup_admin.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def classroom_detail(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)

    all_assignments = Assignment.objects.filter(classroom=classroom)

    graded_assignments = Assignment.objects.filter(
        classroom=classroom,
        submissions__graded=True
    ).distinct()

    pending_grading = Assignment.objects.filter(
        classroom=classroom
    ).exclude(
        submissions__graded=True
    ).distinct()

    return render(request, 'classroom_detail.html', {
        'classroom': classroom,
        'all_assignments': all_assignments,
        'graded_assignments': graded_assignments,
        'pending_grading': pending_grading,
    })



@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def teacher_dashboard_view(request):
    teacher = request.user.teacher_profile

    if request.method == 'POST':
        form = ClassroomCreateForm(request.POST, teacher=teacher)
        if form.is_valid():
            classroom = form.save(commit=False)
            subject = form.cleaned_data['subject']
            classroom.teacher = request.user
            classroom.subject_name = subject.subject_name
            classroom.subject_code = subject.subject_code
            classroom.save()
            return redirect('accounts:teacher_dashboard')
    else:
        form = ClassroomCreateForm(teacher=teacher)

    classrooms = Classroom.objects.filter(teacher=request.user)
    return render(request, 'teacher_dashboard.html', {
        'form': form,
        'classrooms': classrooms,
        'teacher': teacher,
    })

def student_signup_view(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Optional: Log the user in after signup
            return redirect('accounts:student_dashboard')  # Replace with your actual dashboard URL name
    else:
        form = StudentSignUpForm()
    return render(request, 'signup_student.html', {'form': form})


@login_required
def student_dashboard(request):
    student = request.user.student_profile
    branch  = student.branch
    batch   = student.batch_year

    # ────────────────────────────────────────────────────────────────────
    # 1. All assignments that belong to the student’s classrooms
    # ────────────────────────────────────────────────────────────────────
    all_assignments = (
        Assignment.objects
        .filter(classroom__branch=branch, classroom__batch=batch)
        .order_by("-deadline")
    )

    # ────────────────────────────────────────────────────────────────────
    # 2. All submissions by *this* student, with pre-fetched feedback
    #    • select_related grabs the foreign-key objects in the same query
    #    • prefetch_related pulls in every QuestionFeedback row
    #    • annotate adds total_obtained on the fly
    # ────────────────────────────────────────────────────────────────────
    submissions_qs = (
        StudentSubmission.objects
        .filter(student=request.user)
        .select_related("assignment", "assignment__classroom")
        .prefetch_related(
            Prefetch(
                "question_feedback",
                queryset=QuestionFeedback.objects.order_by("question_number")
            )
        )
        .annotate(total_obtained=Sum("question_feedback__obtained_marks"))
    )

    submitted_ids = submissions_qs.values_list("assignment_id", flat=True)

    # ────────────────────────────────────────────────────────────────────
    # 3. Buckets
    # ────────────────────────────────────────────────────────────────────
    pending_assignments   = all_assignments.exclude(id__in=submitted_ids).filter(deadline__gte=now())
    submitted_assignments = submissions_qs.filter(graded=False)
    graded_assignments    = submissions_qs.filter(graded=True)

    # ────────────────────────────────────────────────────────────────────
    # 4. Context → template
    # ────────────────────────────────────────────────────────────────────
    context = {
        "pending_assignments":   pending_assignments,
        "submitted_assignments": submitted_assignments,
        "graded_assignments":    graded_assignments,
        # total_obtained is now a property on every graded submission
        # so you no longer need a separate total_marks dict
    }
    return render(request, "student_dashboard.html", context)



