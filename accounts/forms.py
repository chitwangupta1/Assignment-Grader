from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from .models import CustomUser, Subject,Administration, Teacher, Classroom, Student
User = get_user_model()


class TeacherUpdateForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['first_name', 'middle_name', 'last_name', 'branch', 'contact_number', 'post', 'college_email', 'subjects']
        widgets = {
            'subjects':  forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super(TeacherUpdateForm, self).__init__(*args, **kwargs)

class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'middle_name', 'last_name', 'roll_no', 'batch_year', 'branch', 'college_email', 'contact_number']
        
    def __init__(self, *args, **kwargs):
        super(StudentUpdateForm, self).__init__(*args, **kwargs)

class AdminUpdateForm(forms.ModelForm):
    class Meta:
        model = Administration
        fields = ['first_name', 'middle_name', 'last_name', 'college_email', 'contact_number', 'position']

    def __init__(self, *args, **kwargs):
        super(AdminUpdateForm, self).__init__(*args, **kwargs)

class ClassroomCreateForm(forms.ModelForm):
    subject = forms.ModelChoiceField(queryset=Subject.objects.none(), required=True, label="Subject (Choose from your subjects)")

    class Meta:
        model = Classroom
        fields = ['name', 'subject', 'subject_name', 'subject_code', 'branch', 'batch']
        widgets = {
            'subject_name': forms.TextInput(attrs={'readonly': True}),
            'subject_code': forms.TextInput(attrs={'readonly': True}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['subject'].queryset = teacher.subjects.all()



    # def save(self, commit=True):
    #     instance = super().save(commit=False)
    #     subject = self.cleaned_data.get('subject')
    #     if subject:
    #         instance.subject_name = subject.subject_name
    #         instance.subject_code = subject.subject_code
    #     if commit:
    #         instance.save()
    #     return instance




class RoleLoginForm(AuthenticationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)

class SubjectCreateForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['subject_name', 'subject_code', 'branch']
        widgets = {
            'subject_name': forms.TextInput(attrs={'placeholder': 'e.g., Data Structures'}),
            'subject_code': forms.TextInput(attrs={'placeholder': 'e.g., CS202'}),
            'branch': forms.TextInput(attrs={'placeholder': 'e.g., CSE'}),
    
        }

class TeacherSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30)
    middle_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30)
    branch = forms.CharField(max_length=50)
    post = forms.ChoiceField(choices=Teacher.POST_CHOICES)
    college_email = forms.EmailField()
    contact_number = forms.CharField(max_length=15, required=False)
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Subjects to Teach"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        if commit:
            user.save()
            teacher = Teacher.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                middle_name=self.cleaned_data['middle_name'],
                last_name=self.cleaned_data['last_name'],
                branch=self.cleaned_data['branch'],
                post=self.cleaned_data['post'],
                contact_number=self.cleaned_data['contact_number'],
                college_email=self.cleaned_data['college_email']
            )
            teacher.subjects.set(self.cleaned_data['subjects'])
        return user


class StudentSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30)
    middle_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30)
    roll_no = forms.CharField(max_length=20)
    batch_year = forms.IntegerField()
    branch = forms.CharField(max_length=50)
    college_email = forms.EmailField()
    contact_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        if commit:
            user.save()
            Student.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                middle_name=self.cleaned_data.get('middle_name'),
                last_name=self.cleaned_data['last_name'],
                roll_no=self.cleaned_data['roll_no'],
                batch_year=self.cleaned_data['batch_year'],
                branch=self.cleaned_data['branch'],
                college_email=self.cleaned_data['college_email'],
                contact_number=self.cleaned_data.get('contact_number')
            )
        return user


class AdminSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30)
    middle_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30)
    college_email = forms.EmailField()
    contact_number = forms.CharField(max_length=15, required=False)
    position = forms.ChoiceField(choices=Administration.POSITION_CHOICES)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'administration'
        if commit:
            user.save()
            Administration.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                middle_name=self.cleaned_data['middle_name'],
                last_name=self.cleaned_data['last_name'],
                college_email=self.cleaned_data['college_email'],
                contact_number=self.cleaned_data['contact_number'],
                position=self.cleaned_data['position']
            )
        return user

