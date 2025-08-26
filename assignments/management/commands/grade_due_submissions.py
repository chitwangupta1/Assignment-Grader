from django.core.management.base import BaseCommand
from django.utils.timezone import now
from assignments.models import Assignment

class Command(BaseCommand):
    help = 'Auto-grade all ungraded submissions for assignments whose deadline passed'

    def handle(self, *args, **options):
        current_time = now()
        assignments_due = Assignment.objects.filter(deadline__lte=current_time)

        for assignment in assignments_due:
            ungraded_submissions = assignment.submissions.filter(graded=False)
            if not ungraded_submissions.exists():
                continue
            self.stdout.write(f"Grading submissions for assignment '{assignment.title}' (ID: {assignment.id})...")

            for submission in ungraded_submissions:
                grade_single_submission(submission)

            self.stdout.write(f"Completed grading assignment '{assignment.title}'.")


def grade_single_submission(submission):
    from assignments.utils import grade_single_submission as grade_func
    grade_func(submission)
