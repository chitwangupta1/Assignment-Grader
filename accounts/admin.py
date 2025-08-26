from django.contrib import admin
from .models import CustomUser, Subject,Administration, Teacher, Classroom, Student

# Register your models here.
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(CustomUser)
admin.site.register(Administration)
admin.site.register(Classroom)
admin.site.register(Student)
