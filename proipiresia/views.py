from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, JsonResponse, FileResponse
from django.db.models import Q, Sum, F, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied, ValidationError
from django.conf import settings

import os
import json
import datetime
import tempfile
from io import BytesIO
import xlsxwriter

# Βοηθητική συνάρτηση για τη μετατροπή του request.user σε πραγματικό αντικείμενο User
def get_real_user(request_user):
    """
    Μετατρέπει το request.user (SimpleLazyObject) σε πραγματικό αντικείμενο User
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if request_user.is_authenticated:
        try:
            return User.objects.get(id=request_user.id)
        except User.DoesNotExist:
            # Αν δεν βρεθεί ο χρήστης, επιστρέφουμε None
            return None
    return None
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document
from docx.shared import Inches

from .models import (
    User, Teacher, Specialty, TeacherSpecialty, Service, 
    SchoolYear, EmployeeType, PYSEEP, ServiceProvider, 
    EmploymentRelation, Application, PriorService, AuditLog
)
from .forms import (
    CustomAuthenticationForm, CustomUserCreationForm, TeacherForm, 
    TeacherSpecialtyForm, ApplicationForm, ApplicationStatusForm, 
    PriorServiceForm, VerifyPriorServiceForm, ApplicationSearchForm, 
    PriorServiceSearchForm, ReportForm
)

# Βοηθητική συνάρτηση για την καταγραφή ενεργειών
def log_action(request, action, entity, entity_id, old_values=None, new_values=None):
    # Έλεγχος αν ο χρήστης είναι συνδεδεμένος
    if not request.user.is_authenticated:
        return
    
    # Έλεγχος αν ο χρήστης είναι του προσαρμοσμένου μοντέλου User
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        # Προσπάθεια εύρεσης του χρήστη στο προσαρμοσμένο μοντέλο User
        custom_user = User.objects.get(username=request.user.username)
        
        AuditLog.objects.create(
            user=custom_user,
            action=action,
            entity=entity,
            entity_id=entity_id,
            ip_address=request.META.get('REMOTE_ADDR'),
            old_values=old_values,
            new_values=new_values,
            session_key=request.session.session_key
        )
    except User.DoesNotExist:
        # Αν ο χρήστης δεν υπάρχει στο προσαρμοσμένο μοντέλο User, δεν καταγράφουμε την ενέργεια
        pass

# Αρχική σελίδα
@login_required
def home(request):
    # Στατιστικά στοιχεία για την αρχική σελίδα
    total_applications = Application.objects.count()
    pending_applications = Application.objects.filter(status__in=['NEW', 'PENDING_DOCS']).count()
    ready_for_pyseep = Application.objects.filter(status='READY_FOR_PYSEEP').count()
    completed_applications = Application.objects.filter(status='COMPLETED').count()
    
    # Πρόσφατες αιτήσεις
    recent_applications = Application.objects.order_by('-created_at')[:10]
    
    # Επερχόμενα ΠΥΣΕΕΠ
    upcoming_pyseep = PYSEEP.objects.filter(date__gte=timezone.now()).order_by('date')[:5]
    
    context = {
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'ready_for_pyseep': ready_for_pyseep,
        'completed_applications': completed_applications,
        'recent_applications': recent_applications,
        'upcoming_pyseep': upcoming_pyseep,
    }
    
    return render(request, 'proipiresia/home.html', context)

# Σύνδεση χρήστη
def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_action(request, 'LOGIN', 'USER', user.id)
            messages.success(request, f'Καλωσήρθατε, {user.get_full_name() or user.username}!')
            return redirect('home')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'proipiresia/login.html', {'form': form})

# Αποσύνδεση χρήστη
@login_required
def user_logout(request):
    log_action(request, 'LOGOUT', 'USER', request.user.id)
    logout(request)
    messages.info(request, 'Αποσυνδεθήκατε επιτυχώς.')
    return redirect('login')

# Λίστα εκπαιδευτικών
class TeacherListView(LoginRequiredMixin, ListView):
    model = Teacher
    template_name = 'proipiresia/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = self.request.GET.get('search', '')
        
        if search_term:
            queryset = queryset.filter(
                Q(last_name__icontains=search_term) |
                Q(first_name__icontains=search_term) |
                Q(father_name__icontains=search_term) |
                Q(teacherspecialty__specialty__code__icontains=search_term)
            ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        return context

# Λεπτομέρειες εκπαιδευτικού
class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'proipiresia/teacher_detail.html'
    context_object_name = 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specialties'] = self.object.teacherspecialty_set.all()
        context['applications'] = Application.objects.filter(teacher=self.object).order_by('-created_at')
        
        # Συγκεντρωτικά στοιχεία προϋπηρεσιών
        prior_services = PriorService.objects.filter(
            application__teacher=self.object,
            application__status='COMPLETED',
            is_active=True
        )
        
        context['total_services'] = prior_services.count()
        
        totals = prior_services.aggregate(
            total_years=Sum('years'),
            total_months=Sum('months'),
            total_days=Sum('days')
        )
        
        years = totals['total_years'] or 0
        months = totals['total_months'] or 0
        days = totals['total_days'] or 0
        
        # Κανονικοποίηση
        months += days // 30
        days = days % 30
        years += months // 12
        months = months % 12
        
        context['total_experience'] = {
            'years': years,
            'months': months,
            'days': days
        }
        
        return context

# Δημιουργία εκπαιδευτικού
class TeacherCreateView(LoginRequiredMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'proipiresia/teacher_form.html'
    
    def get_success_url(self):
        return reverse('teacher-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            self.request, 
            'CREATE', 
            'TEACHER', 
            self.object.id,
            new_values=json.dumps({
                'first_name': self.object.first_name,
                'last_name': self.object.last_name,
                'father_name': self.object.father_name,
                'phone': self.object.phone,
                'email': self.object.email
            })
        )
        messages.success(self.request, f'Ο εκπαιδευτικός {self.object} δημιουργήθηκε επιτυχώς.')
        return response

# Ενημέρωση εκπαιδευτικού
class TeacherUpdateView(LoginRequiredMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'proipiresia/teacher_form.html'
    
    def get_success_url(self):
        return reverse('teacher-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        old_values = {
            'first_name': self.object.first_name,
            'last_name': self.object.last_name,
            'father_name': self.object.father_name,
            'phone': self.object.phone,
            'email': self.object.email
        }
        
        response = super().form_valid(form)
        
        log_action(
            self.request, 
            'UPDATE', 
            'TEACHER', 
            self.object.id,
            old_values=json.dumps(old_values),
            new_values=json.dumps({
                'first_name': self.object.first_name,
                'last_name': self.object.last_name,
                'father_name': self.object.father_name,
                'phone': self.object.phone,
                'email': self.object.email
            })
        )
        
        messages.success(self.request, f'Ο εκπαιδευτικός {self.object} ενημερώθηκε επιτυχώς.')
        return response

# Προσθήκη ειδικότητας σε εκπαιδευτικό
@login_required
def add_teacher_specialty(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    if request.method == 'POST':
        form = TeacherSpecialtyForm(request.POST)
        if form.is_valid():
            specialty = form.save(commit=False)
            specialty.teacher = teacher
            
            # Αν είναι κύρια ειδικότητα, απενεργοποιούμε τις άλλες κύριες
            if specialty.is_primary:
                TeacherSpecialty.objects.filter(teacher=teacher, is_primary=True).update(is_primary=False)
            
            specialty.save()
            
            log_action(
                request, 
                'CREATE', 
                'TEACHER', 
                teacher.id,
                new_values=json.dumps({
                    'specialty': specialty.specialty.code,
                    'is_primary': specialty.is_primary
                })
            )
            
            messages.success(request, f'Η ειδικότητα {specialty.specialty} προστέθηκε επιτυχώς στον εκπαιδευτικό {teacher}.')
            return redirect('teacher-detail', pk=teacher.id)
    else:
        form = TeacherSpecialtyForm()
    
    return render(request, 'proipiresia/teacher_specialty_form.html', {'form': form, 'teacher': teacher})

# Λίστα αιτήσεων
class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'proipiresia/application_list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        
        # Φιλτράρισμα με βάση τη φόρμα αναζήτησης
        form = ApplicationSearchForm(self.request.GET)
        
        if form.is_valid():
            teacher_name = form.cleaned_data.get('teacher_name')
            school_year = form.cleaned_data.get('school_year')
            current_service = form.cleaned_data.get('current_service')
            status = form.cleaned_data.get('status')
            pyseep = form.cleaned_data.get('pyseep')
            
            if teacher_name:
                queryset = queryset.filter(
                    Q(teacher__last_name__icontains=teacher_name) |
                    Q(teacher__first_name__icontains=teacher_name)
                )
            
            if school_year:
                queryset = queryset.filter(school_year=school_year)
            
            if current_service:
                queryset = queryset.filter(current_service=current_service)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if pyseep:
                queryset = queryset.filter(pyseep=pyseep)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ApplicationSearchForm(self.request.GET)
        return context

# Λεπτομέρειες αίτησης
class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = 'proipiresia/application_detail.html'
    context_object_name = 'application'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prior_services'] = self.object.priorservice_set.all().order_by('start_date')
        
        # Υπολογισμός συνολικής προϋπηρεσίας
        totals = self.object.priorservice_set.aggregate(
            total_years=Sum('years'),
            total_months=Sum('months'),
            total_days=Sum('days')
        )
        
        years = totals['total_years'] or 0
        months = totals['total_months'] or 0
        days = totals['total_days'] or 0
        
        # Κανονικοποίηση
        months += days // 30
        days = days % 30
        years += months // 12
        months = months % 12
        
        context['total_experience'] = {
            'years': years,
            'months': months,
            'days': days
        }
        
        # Φόρμα αλλαγής κατάστασης
        context['status_form'] = ApplicationStatusForm(instance=self.object)
        
        return context

# Δημιουργία αίτησης
class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'proipiresia/application_form.html'
    
    def get_success_url(self):
        return reverse('application-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Χρήση της βοηθητικής συνάρτησης για τη μετατροπή του request.user
        user = get_real_user(self.request.user)
        form.instance.created_by = user
        form.instance.updated_by = user
        
        response = super().form_valid(form)
        
        log_action(
            self.request, 
            'CREATE', 
            'APPLICATION', 
            self.object.id,
            new_values=json.dumps({
                'teacher': self.object.teacher.id,
                'current_service': self.object.current_service.id,
                'school_year': self.object.school_year.id,
                'employee_type': self.object.employee_type.id,
                'status': self.object.status
            })
        )
        
        messages.success(self.request, f'Η αίτηση για τον εκπαιδευτικό {self.object.teacher} δημιουργήθηκε επιτυχώς.')
        return response

# Ενημέρωση αίτησης
class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'proipiresia/application_form.html'
    
    def get_success_url(self):
        return reverse('application-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        old_values = {
            'teacher': self.object.teacher.id,
            'current_service': self.object.current_service.id,
            'school_year': self.object.school_year.id,
            'employee_type': self.object.employee_type.id,
            'recruitment_phase': self.object.recruitment_phase,
            'submission_date': self.object.submission_date.strftime('%Y-%m-%d') if self.object.submission_date else None,
            'protocol_number': self.object.protocol_number,
            'pyseep': self.object.pyseep.id if self.object.pyseep else None,
            'status': self.object.status
        }
        
        # Χρήση της βοηθητικής συνάρτησης για τη μετατροπή του request.user
        user = get_real_user(self.request.user)
        form.instance.updated_by = user
        
        response = super().form_valid(form)
        
        new_values = {
            'teacher': self.object.teacher.id,
            'current_service': self.object.current_service.id,
            'school_year': self.object.school_year.id,
            'employee_type': self.object.employee_type.id,
            'recruitment_phase': self.object.recruitment_phase,
            'submission_date': self.object.submission_date.strftime('%Y-%m-%d') if self.object.submission_date else None,
            'protocol_number': self.object.protocol_number,
            'pyseep': self.object.pyseep.id if self.object.pyseep else None,
            'status': self.object.status
        }
        
        log_action(
            self.request, 
            'UPDATE', 
            'APPLICATION', 
            self.object.id,
            old_values=json.dumps(old_values),
            new_values=json.dumps(new_values)
        )
        
        messages.success(self.request, f'Η αίτηση για τον εκπαιδευτικό {self.object.teacher} ενημερώθηκε επιτυχώς.')
        return response

# Αλλαγή κατάστασης αίτησης
@login_required
def change_application_status(request, pk):
    application = get_object_or_404(Application, pk=pk)
    
    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            old_status = application.status
            
            application = form.save(commit=False)
            application.updated_by = get_real_user(request.user)
            application.save()
            
            # Αν η κατάσταση άλλαξε σε "Ολοκληρωμένη από ΠΥΣΕΕΠ", ενημερώνουμε το ιστορικό των προϋπηρεσιών
            if old_status != 'COMPLETED' and application.status == 'COMPLETED' and application.pyseep:
                for service in application.priorservice_set.all():
                    if service.history:
                        service.history += f"\nΕγκρίθηκε από το ΠΥΣΕΕΠ πράξη {application.pyseep.act_number}, ημερομηνία {application.pyseep.date.strftime('%d/%m/%Y')}."
                    else:
                        service.history = f"Εγκρίθηκε από το ΠΥΣΕΕΠ πράξη {application.pyseep.act_number}, ημερομηνία {application.pyseep.date.strftime('%d/%m/%Y')}."
                    
                    service.updated_by = get_real_user(request.user)
                    service.save()
            
            log_action(
                request, 
                'STATUS_CHANGE', 
                'APPLICATION', 
                application.id,
                old_values=json.dumps({'status': old_status}),
                new_values=json.dumps({'status': application.status})
            )
            
            messages.success(request, f'Η κατάσταση της αίτησης άλλαξε σε "{application.get_status_display()}".')
            
            return redirect('application-detail', pk=application.id)
    
    return redirect('application-detail', pk=application.id)

# Δημιουργία νέας έκδοσης αίτησης
@login_required
def create_application_version(request, pk):
    application = get_object_or_404(Application, pk=pk)
    
    if application.status != 'COMPLETED':
        messages.error(request, 'Μόνο ολοκληρωμένες αιτήσεις μπορούν να έχουν νέα έκδοση.')
        return redirect('application-detail', pk=application.id)
    
    new_application = application.create_new_version()
    new_application.updated_by = get_real_user(request.user)
    new_application.save()
    
    log_action(
        request, 
        'CREATE', 
        'APPLICATION', 
        new_application.id,
        old_values=json.dumps({'original_application': application.id}),
        new_values=json.dumps({
            'version': new_application.version,
            'status': new_application.status
        })
    )
    
    messages.success(request, f'Δημιουργήθηκε νέα έκδοση της αίτησης (Έκδοση {new_application.version}).')
    
    return redirect('application-detail', pk=new_application.id)

# Προσθήκη προϋπηρεσίας σε αίτηση
@login_required
def add_prior_service(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    
    # Έλεγχος αν η αίτηση είναι ολοκληρωμένη
    if application.status == 'COMPLETED':
        messages.error(request, 'Δεν μπορείτε να προσθέσετε προϋπηρεσία σε ολοκληρωμένη αίτηση.')
        return redirect('application-detail', pk=application.id)
    
    if request.method == 'POST':
        form = PriorServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.application = application
            user = get_real_user(request.user)
            service.created_by = user
            service.updated_by = user
            
            try:
                service.clean()  # Έλεγχος για αλληλεπικαλυπτόμενες περιόδους
                service.save()
                
                log_action(
                    request, 
                    'CREATE', 
                    'PRIOR_SERVICE', 
                    service.id,
                    new_values=json.dumps({
                        'application': service.application.id,
                        'service_provider': service.service_provider.id,
                        'start_date': service.start_date.strftime('%Y-%m-%d'),
                        'end_date': service.end_date.strftime('%Y-%m-%d'),
                        'years': service.years,
                        'months': service.months,
                        'days': service.days
                    })
                )
                
                messages.success(request, f'Η προϋπηρεσία προστέθηκε επιτυχώς.')
                return redirect('application-detail', pk=application.id)
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
    else:
        # Φόρτωση προηγούμενων προϋπηρεσιών του εκπαιδευτικού
        previous_services = PriorService.objects.filter(
            application__teacher=application.teacher,
            application__status='COMPLETED',
            is_active=True
        ).exclude(application=application)
        
        if previous_services.exists() and request.GET.get('load_previous') == 'true':
            # Αντιγραφή προηγούμενων προϋπηρεσιών στην τρέχουσα αίτηση
            for prev_service in previous_services:
                # Έλεγχος αν η προϋπηρεσία υπάρχει ήδη στην τρέχουσα αίτηση
                existing = PriorService.objects.filter(
                    application=application,
                    service_provider=prev_service.service_provider,
                    start_date=prev_service.start_date,
                    end_date=prev_service.end_date
                ).exists()
                
                if not existing:
                    new_service = PriorService.objects.create(
                        application=application,
                        service_provider=prev_service.service_provider,
                        protocol_number=prev_service.protocol_number,
                        employment_relation=prev_service.employment_relation,
                        start_date=prev_service.start_date,
                        end_date=prev_service.end_date,
                        years=prev_service.years,
                        months=prev_service.months,
                        days=prev_service.days,
                        history=prev_service.history,
                        notes=prev_service.notes,
                        internal_notes=prev_service.internal_notes,
                        created_by=get_real_user(request.user),
                        updated_by=get_real_user(request.user),
                        version_id=prev_service.version_id
                    )
                    
                    log_action(
                        request, 
                        'CREATE', 
                        'PRIOR_SERVICE', 
                        new_service.id,
                        new_values=json.dumps({
                            'application': new_service.application.id,
                            'service_provider': new_service.service_provider.id,
                            'copied_from': prev_service.id
                        })
                    )
            
            messages.success(request, f'Οι προηγούμενες προϋπηρεσίες φορτώθηκαν επιτυχώς.')
            return redirect('application-detail', pk=application.id)
        
        form = PriorServiceForm()
    
    return render(request, 'proipiresia/prior_service_form.html', {
        'form': form, 
        'application': application,
        'has_previous': PriorService.objects.filter(
            application__teacher=application.teacher,
            application__status='COMPLETED',
            is_active=True
        ).exclude(application=application).exists()
    })

# Επεξεργασία προϋπηρεσίας
@login_required
def edit_prior_service(request, pk):
    service = get_object_or_404(PriorService, pk=pk)
    application = service.application
    
    # Έλεγχος αν η αίτηση είναι ολοκληρωμένη
    if application.status == 'COMPLETED':
        messages.error(request, 'Δεν μπορείτε να επεξεργαστείτε προϋπηρεσία σε ολοκληρωμένη αίτηση.')
        return redirect('application-detail', pk=application.id)
    
    # Έλεγχος αν η προϋπηρεσία έχει επαληθευτεί
    if service.verified and not request.user.is_superuser:
        messages.error(request, 'Δεν μπορείτε να επεξεργαστείτε επαληθευμένη προϋπηρεσία.')
        return redirect('application-detail', pk=application.id)
    
    if request.method == 'POST':
        form = PriorServiceForm(request.POST, instance=service)
        if form.is_valid():
            old_values = {
                'service_provider': service.service_provider.id,
                'protocol_number': service.protocol_number,
                'employment_relation': service.employment_relation.id,
                'start_date': service.start_date.strftime('%Y-%m-%d'),
                'end_date': service.end_date.strftime('%Y-%m-%d'),
                'years': service.years,
                'months': service.months,
                'days': service.days,
                'notes': service.notes,
                'internal_notes': service.internal_notes
            }
            
            service = form.save(commit=False)
            service.updated_by = get_real_user(request.user)
            
            try:
                service.clean()  # Έλεγχος για αλληλεπικαλυπτόμενες περιόδους
                service.save()
                
                new_values = {
                    'service_provider': service.service_provider.id,
                    'protocol_number': service.protocol_number,
                    'employment_relation': service.employment_relation.id,
                    'start_date': service.start_date.strftime('%Y-%m-%d'),
                    'end_date': service.end_date.strftime('%Y-%m-%d'),
                    'years': service.years,
                    'months': service.months,
                    'days': service.days,
                    'notes': service.notes,
                    'internal_notes': service.internal_notes
                }
                
                log_action(
                    request, 
                    'UPDATE', 
                    'PRIOR_SERVICE', 
                    service.id,
                    old_values=json.dumps(old_values),
                    new_values=json.dumps(new_values)
                )
                
                messages.success(request, f'Η προϋπηρεσία ενημερώθηκε επιτυχώς.')
                return redirect('application-detail', pk=application.id)
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
    else:
        form = PriorServiceForm(instance=service)
    
    return render(request, 'proipiresia/prior_service_form.html', {'form': form, 'application': application})

# Διαγραφή προϋπηρεσίας
@login_required
def delete_prior_service(request, pk):
    service = get_object_or_404(PriorService, pk=pk)
    application = service.application
    
    # Έλεγχος αν η αίτηση είναι ολοκληρωμένη
    if application.status == 'COMPLETED':
        messages.error(request, 'Δεν μπορείτε να διαγράψετε προϋπηρεσία από ολοκληρωμένη αίτηση.')
        return redirect('application-detail', pk=application.id)
    
    # Έλεγχος αν η προϋπηρεσία έχει επαληθευτεί
    if service.verified and not request.user.is_superuser:
        messages.error(request, 'Δεν μπορείτε να διαγράψετε επαληθευμένη προϋπηρεσία.')
        return redirect('application-detail', pk=application.id)
    
    if request.method == 'POST':
        service_id = service.id
        service_values = {
            'service_provider': service.service_provider.id,
            'start_date': service.start_date.strftime('%Y-%m-%d'),
            'end_date': service.end_date.strftime('%Y-%m-%d')
        }
        
        service.delete()
        
        log_action(
            request,
            'DELETE',
            'PRIOR_SERVICE',
            service_id,
            old_values=json.dumps(service_values)
        )
        
        messages.success(request, 'Η προϋπηρεσία διαγράφηκε επιτυχώς.')
        return redirect('application-detail', pk=application.id)
    
    return render(request, 'proipiresia/prior_service_confirm_delete.html', {'service': service, 'application': application})

# Επαλήθευση προϋπηρεσίας
@login_required
def verify_prior_service(request, pk):
    service = get_object_or_404(PriorService, pk=pk)
    application = service.application
    
    if request.method == 'POST':
        form = VerifyPriorServiceForm(request.POST)
        if form.is_valid():
            verified = form.cleaned_data.get('verified')
            
            if verified:
                # Επαλήθευση προϋπηρεσίας
                service.mark_as_verified(get_real_user(request.user))
                
                log_action(
                    request,
                    'VERIFY',
                    'PRIOR_SERVICE',
                    service.id,
                    new_values=json.dumps({
                        'verified': service.verified.strftime('%Y-%m-%d %H:%M:%S'),
                        'verified_by': service.verified_by.id
                    })
                )
                
                messages.success(request, 'Η προϋπηρεσία επαληθεύτηκε επιτυχώς.')
            else:
                # Αναίρεση επαλήθευσης
                service.verified = None
                service.verified_by = None
                service.save()
                
                log_action(
                    request,
                    'VERIFY',
                    'PRIOR_SERVICE',
                    service.id,
                    new_values=json.dumps({
                        'verified': None,
                        'verified_by': None
                    })
                )
                
                messages.success(request, 'Η επαλήθευση της προϋπηρεσίας αναιρέθηκε επιτυχώς.')
    
    return redirect('application-detail', pk=application.id)

# Δημιουργία αναφοράς
@login_required
def generate_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            pyseep = form.cleaned_data.get('pyseep')
            current_service = form.cleaned_data.get('current_service')
            report_format = form.cleaned_data.get('format')
            
            # Φιλτράρισμα αιτήσεων
            applications = Application.objects.filter(
                pyseep=pyseep,
                status='READY_FOR_PYSEEP'
            )
            
            if current_service:
                applications = applications.filter(current_service=current_service)
            
            # Ταξινόμηση αιτήσεων
            applications = applications.order_by('current_service__name', 'teacher__last_name', 'teacher__first_name')
            
            # Δημιουργία δεδομένων αναφοράς
            report_data = []
            
            for application in applications:
                teacher_data = {
                    'teacher': application.teacher,
                    'current_service': application.current_service,
                    'school_year': application.school_year,
                    'employee_type': application.employee_type,
                    'prior_services': []
                }
                
                for service in application.priorservice_set.all().order_by('start_date'):
                    teacher_data['prior_services'].append({
                        'service_provider': service.service_provider,
                        'protocol_number': service.protocol_number,
                        'employment_relation': service.employment_relation,
                        'start_date': service.start_date,
                        'end_date': service.end_date,
                        'years': service.years,
                        'months': service.months,
                        'days': service.days,
                        'verified': service.verified is not None
                    })
                
                report_data.append(teacher_data)
            
            # Δημιουργία αναφοράς στο επιλεγμένο format
            if report_format == 'xlsx':
                return generate_excel_report(pyseep, report_data)
            elif report_format == 'pdf':
                return generate_pdf_report(pyseep, report_data)
            elif report_format == 'docx':
                return generate_docx_report(pyseep, report_data)
    else:
        form = ReportForm()
    
    return render(request, 'proipiresia/report_form.html', {'form': form})

# Δημιουργία αναφοράς Excel
def generate_excel_report(pyseep, report_data):
    # Δημιουργία προσωρινού αρχείου
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # Στυλ
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#D7E4BC',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    })
    
    # Επικεφαλίδες
    headers = [
        'Επώνυμο', 'Όνομα', 'Πατρώνυμο', 'Υπηρεσία Τοποθέτησης', 'Τύπος Εκπ/κού',
        'Φορέας Προϋπηρεσίας', 'Αρ. Πρωτοκόλλου', 'Σχέση Εργασίας',
        'Από', 'Έως', 'Έτη', 'Μήνες', 'Ημέρες', 'Ελεγμένη'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Δεδομένα
    row = 1
    for teacher_data in report_data:
        teacher = teacher_data['teacher']
        
        for service in teacher_data['prior_services']:
            worksheet.write(row, 0, teacher.last_name, cell_format)
            worksheet.write(row, 1, teacher.first_name, cell_format)
            worksheet.write(row, 2, teacher.father_name, cell_format)
            worksheet.write(row, 3, teacher_data['current_service'].name, cell_format)
            worksheet.write(row, 4, teacher_data['employee_type'].name, cell_format)
            worksheet.write(row, 5, service['service_provider'].name, cell_format)
            worksheet.write(row, 6, service['protocol_number'], cell_format)
            worksheet.write(row, 7, service['employment_relation'].name, cell_format)
            worksheet.write(row, 8, service['start_date'].strftime('%d/%m/%Y'), cell_format)
            worksheet.write(row, 9, service['end_date'].strftime('%d/%m/%Y'), cell_format)
            worksheet.write(row, 10, service['years'], cell_format)
            worksheet.write(row, 11, service['months'], cell_format)
            worksheet.write(row, 12, service['days'], cell_format)
            worksheet.write(row, 13, 'Ναι' if service['verified'] else 'Όχι', cell_format)
            
            row += 1
    
    # Προσαρμογή πλάτους στηλών
    for col, header in enumerate(headers):
        worksheet.set_column(col, col, len(header) + 2)
    
    workbook.close()
    
    # Δημιουργία απάντησης
    output.seek(0)
    
    filename = f"ΠΥΣΕΕΠ_{pyseep.act_number}_{pyseep.date.strftime('%d_%m_%Y')}.xlsx"
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# Δημιουργία αναφοράς PDF
def generate_pdf_report(pyseep, report_data):
    # Δημιουργία προσωρινού αρχείου
    buffer = BytesIO()
    
    # Δημιουργία PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Στυλ
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Τίτλος
    elements.append(Paragraph(f"ΠΥΣΕΕΠ {pyseep.act_number} - {pyseep.date.strftime('%d/%m/%Y')}", title_style))
    elements.append(Paragraph("Αναφορά Προϋπηρεσιών", subtitle_style))
    elements.append(Paragraph(" ", normal_style))  # Κενή γραμμή
    
    # Δεδομένα πίνακα
    table_data = [
        ['Επώνυμο', 'Όνομα', 'Υπηρεσία', 'Φορέας Προϋπηρεσίας', 'Από', 'Έως', 'Έτη', 'Μήνες', 'Ημέρες']
    ]
    
    for teacher_data in report_data:
        teacher = teacher_data['teacher']
        
        for service in teacher_data['prior_services']:
            table_data.append([
                teacher.last_name,
                teacher.first_name,
                teacher_data['current_service'].name,
                service['service_provider'].name,
                service['start_date'].strftime('%d/%m/%Y'),
                service['end_date'].strftime('%d/%m/%Y'),
                str(service['years']),
                str(service['months']),
                str(service['days'])
            ])
    
    # Δημιουργία πίνακα
    table = Table(table_data)
    
    # Στυλ πίνακα
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Δημιουργία PDF
    doc.build(elements)
    
    # Δημιουργία απάντησης
    buffer.seek(0)
    
    filename = f"ΠΥΣΕΕΠ_{pyseep.act_number}_{pyseep.date.strftime('%d_%m_%Y')}.pdf"
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# Δημιουργία αναφοράς Word
def generate_docx_report(pyseep, report_data):
    # Δημιουργία εγγράφου
    document = Document()
    
    # Τίτλος
    document.add_heading(f"ΠΥΣΕΕΠ {pyseep.act_number} - {pyseep.date.strftime('%d/%m/%Y')}", 0)
    document.add_heading("Αναφορά Προϋπηρεσιών", 1)
    
    # Πίνακας
    table = document.add_table(rows=1, cols=9)
    table.style = 'Table Grid'
    
    # Επικεφαλίδες
    header_cells = table.rows[0].cells
    header_cells[0].text = 'Επώνυμο'
    header_cells[1].text = 'Όνομα'
    header_cells[2].text = 'Υπηρεσία'
    header_cells[3].text = 'Φορέας Προϋπηρεσίας'
    header_cells[4].text = 'Από'
    header_cells[5].text = 'Έως'
    header_cells[6].text = 'Έτη'
    header_cells[7].text = 'Μήνες'
    header_cells[8].text = 'Ημέρες'
    
    # Δεδομένα
    for teacher_data in report_data:
        teacher = teacher_data['teacher']
        
        for service in teacher_data['prior_services']:
            row_cells = table.add_row().cells
            row_cells[0].text = teacher.last_name
            row_cells[1].text = teacher.first_name
            row_cells[2].text = teacher_data['current_service'].name
            row_cells[3].text = service['service_provider'].name
            row_cells[4].text = service['start_date'].strftime('%d/%m/%Y')
            row_cells[5].text = service['end_date'].strftime('%d/%m/%Y')
            row_cells[6].text = str(service['years'])
            row_cells[7].text = str(service['months'])
            row_cells[8].text = str(service['days'])
    
    # Αποθήκευση σε προσωρινό αρχείο
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    document.save(temp_file.name)
    temp_file.close()
    
    # Δημιουργία απάντησης
    filename = f"ΠΥΣΕΕΠ_{pyseep.act_number}_{pyseep.date.strftime('%d_%m_%Y')}.docx"
    
    with open(temp_file.name, 'rb') as file:
        response = HttpResponse(
            file.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Διαγραφή προσωρινού αρχείου
    os.unlink(temp_file.name)
    
    return response
