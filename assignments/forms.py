from django import forms
from .models import Assignment, StudentSubmission, QuestionFeedback
from django.forms import modelformset_factory
from django.forms import inlineformset_factory, NumberInput, Textarea


from django import forms
from .models import Assignment

class AssignmentCreateForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'question_file', 'question_solution_file', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter assignment title'
            }),
            'question_file': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'question_solution_file': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = StudentSubmission
        fields = ['submitted_file']
        
        def recompute_grade(self):
            total = sum(f.obtained_marks for f in self.feedback_items.all())
            self.grade = total
            self.save(update_fields=['grade'])


class QuestionFeedbackForm(forms.ModelForm):
    class Meta:
        model = QuestionFeedback
        fields = ['question_number', 'max_marks', 'obtained_marks', 'feedback']
        widgets = {
            'question_number': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'max_marks': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'obtained_marks': forms.NumberInput(attrs={'step': '0.5'}),
            'feedback': forms.Textarea(attrs={'rows': 2}),
        }

# QuestionFeedbackFormSet = inlineformset_factory(
#     parent_model   = StudentSubmission,
#     model          = QuestionFeedback,
#     fields         = ['question_number', 'max_marks', 'obtained_marks', 'feedback'],
#     extra          = 0,          # one row per existing question, no blanks
#     can_delete     = False,      # don’t let teachers delete questions here
#     widgets = {
#         'question_number': NumberInput(attrs={
#             'readonly': 'readonly',
#             'class': 'form-control-plaintext',
#             'style': 'border:none; background:transparent; padding:0;'
#         }),
#         'max_marks': NumberInput(attrs={
#             'readonly': 'readonly',
#             'class': 'form-control-plaintext',
#             'style': 'border:none; background:transparent; padding:0;'
#         }),
#         'obtained_marks': NumberInput(attrs={
#             'step': '0.5',
#             'class': 'form-control'
#         }),
#         'feedback': Textarea(attrs={
#             'rows': 2,
#             'class': 'form-control'
#         }),
#     }
# )

QuestionFeedbackFormSet = modelformset_factory(
    QuestionFeedback,
    fields=('question_number', 'max_marks', 'obtained_marks', 'feedback'),
    extra=0,
    can_delete=False
)