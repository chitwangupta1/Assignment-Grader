from django.db import models
from django.conf import settings
from accounts.models import Classroom  # assuming Classroom is in the 'accounts' app

# ───────────────────────────────────────────────
# Assignment Model (Unchanged except comments)
# ───────────────────────────────────────────────
class Assignment(models.Model):
    title = models.CharField(max_length=200)
    classroom = models.ForeignKey(Classroom, related_name='assignments', on_delete=models.CASCADE)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question_file = models.FileField(upload_to='assignments/questions/')
    question_solution_file = models.FileField(upload_to='assignments/solutions/')
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    # This can be used to show full score possible
    total_marks = models.FloatField(default=0)

    def __str__(self):
        return f"{self.title} - {self.classroom.name}"
    

# ───────────────────────────────────────────────
# StudentSubmission Model (with Total + Feedback)
# ───────────────────────────────────────────────
class StudentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, related_name='submissions', on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    submitted_file = models.FileField(upload_to='assignments/submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Total grade across all questions
    grade = models.FloatField(default=0)
    feedback = models.TextField(blank=True, default='')  # General comment if needed
    graded = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

    def recompute_grade(self, commit=True):
        """Automatically update total grade from per-question feedback."""
        total = self.question_feedback.aggregate(
            total=models.Sum('obtained_marks')
        )['total'] or 0.0
        self.grade = total
        if commit:
            self.save(update_fields=['grade'])
        return total


# ───────────────────────────────────────────────
# NEW: Per-Question Feedback
# ───────────────────────────────────────────────
class QuestionFeedback(models.Model):
    submission = models.ForeignKey(StudentSubmission, related_name='question_feedback', on_delete=models.CASCADE)
    question_number =  models.CharField(max_length=10)
    max_marks = models.FloatField()
    obtained_marks = models.FloatField()
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ('submission', 'question_number')  # Prevent duplicates
        ordering = ['question_number']

    def __str__(self):
        return f"Q{self.question_number}: {self.obtained_marks}/{self.max_marks}"
