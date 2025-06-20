from django.urls import path
from . import views

urlpatterns = [
    # Αρχική σελίδα και σύνδεση/αποσύνδεση
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Εκπαιδευτικοί
    path('teachers/', views.TeacherListView.as_view(), name='teacher-list'),
    path('teachers/<int:pk>/', views.TeacherDetailView.as_view(), name='teacher-detail'),
    path('teachers/new/', views.TeacherCreateView.as_view(), name='teacher-create'),
    path('teachers/<int:pk>/edit/', views.TeacherUpdateView.as_view(), name='teacher-update'),
    path('teachers/<int:teacher_id>/add-specialty/', views.add_teacher_specialty, name='add-teacher-specialty'),
    
    # Αιτήσεις
    path('applications/', views.ApplicationListView.as_view(), name='application-list'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application-detail'),
    path('applications/new/', views.ApplicationCreateView.as_view(), name='application-create'),
    path('applications/<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='application-update'),
    path('applications/<int:pk>/delete/', views.ApplicationDeleteView.as_view(), name='application-delete'),
    path('applications/<int:pk>/change-status/', views.change_application_status, name='change-application-status'),
    path('applications/<int:pk>/new-version/', views.create_application_version, name='create-application-version'),
    
    # Προϋπηρεσίες
    path('applications/<int:application_id>/add-service/', views.add_prior_service, name='add-prior-service'),
    path('prior-services/<int:pk>/edit/', views.edit_prior_service, name='edit-prior-service'),
    path('prior-services/<int:pk>/delete/', views.delete_prior_service, name='delete-prior-service'),
    path('prior-services/<int:pk>/verify/', views.verify_prior_service, name='verify-prior-service'),
    
    # Αναφορές
    path('reports/', views.generate_report, name='generate-report'),
    path('reports/pyseep/', views.generate_pyseep_service_report, name='generate-pyseep-report'),
    path('reports/pyseep/pdf/<int:pyseep_id>/', views.generate_pyseep_direct_pdf, name='generate-pyseep-direct-pdf'),
    path('reports/pyseep/word/<int:pyseep_id>/', views.generate_pyseep_direct_word, name='generate-pyseep-direct-word'),
    
    # ΠΥΣΕΕΠ
    path('pyseep/new/', views.PYSEEPCreateView.as_view(), name='pyseep-create'),
    
    # AJAX endpoints
    path('ajax/create-service-provider/', views.create_service_provider_ajax, name='create-service-provider-ajax'),
    path('ajax/create-pyseep/', views.create_pyseep_ajax, name='create-pyseep-ajax'),
]