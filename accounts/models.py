from django.contrib.auth.models import AbstractUser
import uuid
from django.db import models
# from accounts.models import CustomUser  # Import your custom user model

class Subject(models.Model):
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20, unique=True)
    branch = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('administration', 'Administration'),
    )
    user_type = models.CharField(max_length=15, choices=ROLE_CHOICES, default='student')

class Administration(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='admin_profile')
    admin_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30)
    college_email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)

    POSITION_CHOICES = [
        ('Dean', 'Dean'),
        ('Registrar', 'Registrar'),
        ('HOD', 'Head of Department'),
        ('AO', 'Administrative Officer'),
    ]
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position}"



class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    roll_no = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30)
    batch_year = models.IntegerField()
    branch = models.CharField(max_length=50)
    college_email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.roll_no} - {self.first_name} {self.last_name}"

class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30)
    branch = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    
    POST_CHOICES = [
        ('AP', 'Assistant Professor'),
        ('P', 'Professor'),
        ('T', 'Technician'),
    ]
    post = models.CharField(max_length=2, choices=POST_CHOICES)
    college_email = models.EmailField(unique=True)
    subjects = models.ManyToManyField(Subject)  # <-- New field

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_post_display()})"

class Classroom(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'teacher'})
    name = models.CharField(max_length=100)
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20)
    branch = models.CharField(max_length=50)
    batch = models.IntegerField()

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"
    
    