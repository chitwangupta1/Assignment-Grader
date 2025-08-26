from django.urls import path
from django.contrib.auth import views as auth_views
from .views import role_login_view, home
# from .views import student_signup_view, teacher_signup_view, admin_signup_view
from .views import admin_signup_view, admin_dashboard_view, create_subject_view,teacher_dashboard_view,teacher_signup_view, create_classroom_view, student_signup_view, update_teacher_profile, update_student_profile,update_admin_profile, classroom_detail, student_dashboard, grade_all_submissions

app_name = 'accounts'

urlpatterns = [
    path('login/', role_login_view, name='role_login'),
    path('', home, name='home'),
    path('signup/student/', student_signup_view, name='student_signup'),
    path('signup/teacher/', teacher_signup_view, name='teacher_signup'),
    path('signup/admin/', admin_signup_view, name='admin_signup'),
    path('dashboard/admin/', admin_dashboard_view, name='admin_dashboard'),
    path('subjects/create/', create_subject_view, name='create_subject'),
    path('dashboard/teacher/', teacher_dashboard_view, name='teacher_dashboard'),
    path('classroom/create/', create_classroom_view, name='create_classroom'),
    path('update/teacher/', update_teacher_profile, name='update_teacher_profile'),
    path('update/student/', update_student_profile, name='update_student_profile'),
    path('update/admin/', update_admin_profile, name='update_admin_profile'),
    path('classroom/<int:pk>/', classroom_detail, name='classroom_detail'),
    path('student/dashboard/', student_dashboard, name='student_dashboard'),
    path('grade/<int:assignment_id>/', grade_all_submissions, name='grade_all_submissions'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:home'), name='logout'),
]

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
