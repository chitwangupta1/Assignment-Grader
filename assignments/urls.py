from django.urls import path
from . import views

app_name = 'assignments'

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('create/<int:classroom_id>/', views.create_assignment, name='create_assignment'),
    path('<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('<int:assignment_id>/submissions/', views.view_submissions, name='view_submissions'),
    path('edit/<int:pk>/', views.update_assignment, name='edit_assignment'),
    path('edit_submission_marks/<int:submission_id>/', views.edit_submission_marks, name='edit_submission_marks'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
