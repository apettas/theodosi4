from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from .models import (
    Role, User, Specialty, Teacher, TeacherSpecialty, Service,
    SchoolYear, EmployeeType, PYSEEP, ServiceProvider,
    EmploymentRelation, Application, PriorService, AuditLog
)

# Προσαρμοσμένο UserAdmin για το μοντέλο User
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role')
    fieldsets = UserAdmin.fieldsets + (
        ('Ρόλος', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Ρόλος', {'fields': ('role',)}),
    )

# Inline για τη σύνδεση εκπαιδευτικών με ειδικότητες
class TeacherSpecialtyInline(admin.TabularInline):
    model = TeacherSpecialty
    extra = 1

# Inline για τις προϋπηρεσίες σε μια αίτηση
class PriorServiceInline(admin.TabularInline):
    model = PriorService
    extra = 1
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'verified', 'verified_by')
    fieldsets = (
        (None, {
            'fields': ('service_provider', 'protocol_number', 'employment_relation', 'start_date', 'end_date')
        }),
        ('Διάρκεια', {
            'fields': ('years', 'months', 'days')
        }),
        ('Σημειώσεις', {
            'fields': ('history', 'notes', 'internal_notes')
        }),
        ('Έλεγχος', {
            'fields': ('verified', 'verified_by')
        }),
        ('Πληροφορίες Συστήματος', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'version_id', 'is_active'),
            'classes': ('collapse',)
        }),
    )

# Admin για το μοντέλο Role
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

# Admin για το μοντέλο Specialty
@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')
    search_fields = ('code', 'description')
    ordering = ('code',)

# Admin για το μοντέλο Teacher
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'father_name', 'get_specialties', 'phone', 'email')
    search_fields = ('last_name', 'first_name', 'father_name', 'phone', 'email')
    list_filter = ('teacherspecialty__specialty',)
    inlines = [TeacherSpecialtyInline]
    
    def get_specialties(self, obj):
        return ", ".join([ts.specialty.code for ts in obj.teacherspecialty_set.all()])
    get_specialties.short_description = 'Ειδικότητες'

# Admin για το μοντέλο Service
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'prefecture')
    list_filter = ('category', 'prefecture')
    search_fields = ('name',)

# Admin για το μοντέλο SchoolYear
@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    
    def save_model(self, request, obj, form, change):
        # Αν ορίζουμε ένα σχολικό έτος ως ενεργό, απενεργοποιούμε όλα τα άλλα
        if obj.is_active:
            SchoolYear.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)

# Admin για το μοντέλο EmployeeType
@admin.register(EmployeeType)
class EmployeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Admin για το μοντέλο PYSEEP
@admin.register(PYSEEP)
class PYSEEPAdmin(admin.ModelAdmin):
    list_display = ('act_number', 'date', 'school_year')
    list_filter = ('school_year',)
    search_fields = ('act_number',)
    date_hierarchy = 'date'

# Admin για το μοντέλο ServiceProvider
@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Admin για το μοντέλο EmploymentRelation
@admin.register(EmploymentRelation)
class EmploymentRelationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Admin για το μοντέλο Application
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'teacher', 'current_service', 'school_year', 'employee_type', 'status', 'submission_date', 'created_at')
    list_filter = ('status', 'school_year', 'current_service', 'employee_type', 'pyseep')
    search_fields = ('teacher__last_name', 'teacher__first_name', 'protocol_number')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'version', 'get_total_service')
    date_hierarchy = 'created_at'
    inlines = [PriorServiceInline]
    
    fieldsets = (
        (None, {
            'fields': ('teacher', 'current_service', 'school_year', 'employee_type')
        }),
        ('Στοιχεία Αίτησης', {
            'fields': ('recruitment_phase', 'submission_date', 'submission_comments', 'protocol_number', 'pyseep', 'status')
        }),
        ('Αρχείο', {
            'fields': ('application_file',)
        }),
        ('Συνολική Προϋπηρεσία', {
            'fields': ('get_total_service',)
        }),
        ('Πληροφορίες Συστήματος', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'version', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_service(self, obj):
        totals = obj.priorservice_set.aggregate(
            total_years=Sum('years'),
            total_months=Sum('months'),
            total_days=Sum('days')
        )
        
        years = totals['total_years'] or 0
        months = totals['total_months'] or 0
        days = totals['total_days'] or 0
        
        # Κανονικοποίηση (30 μέρες = 1 μήνας, 12 μήνες = 1 έτος)
        months += days // 30
        days = days % 30
        years += months // 12
        months = months % 12
        
        return f"{years} έτη, {months} μήνες, {days} ημέρες"
    get_total_service.short_description = 'Συνολική Προϋπηρεσία'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Αν είναι νέα εγγραφή
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, PriorService):
                if not instance.pk:  # Αν είναι νέα εγγραφή
                    instance.created_by = request.user
                instance.updated_by = request.user
            instance.save()
        formset.save_m2m()

# Admin για το μοντέλο PriorService
@admin.register(PriorService)
class PriorServiceAdmin(admin.ModelAdmin):
    list_display = ('service_provider', 'application', 'start_date', 'end_date', 'years', 'months', 'days', 'is_verified')
    list_filter = ('application__status', 'service_provider', 'employment_relation', 'is_active')
    search_fields = ('application__teacher__last_name', 'application__teacher__first_name', 'service_provider__name')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'verified', 'verified_by')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (None, {
            'fields': ('application', 'service_provider', 'protocol_number', 'employment_relation')
        }),
        ('Χρονικό Διάστημα', {
            'fields': ('start_date', 'end_date', 'years', 'months', 'days')
        }),
        ('Σημειώσεις', {
            'fields': ('history', 'notes', 'internal_notes')
        }),
        ('Έλεγχος', {
            'fields': ('verified', 'verified_by')
        }),
        ('Πληροφορίες Συστήματος', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'version_id', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def is_verified(self, obj):
        return obj.verified is not None
    is_verified.boolean = True
    is_verified.short_description = 'Ελεγμένη'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Αν είναι νέα εγγραφή
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

# Admin για το μοντέλο AuditLog
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'entity', 'entity_id', 'ip_address')
    list_filter = ('action', 'entity', 'user')
    search_fields = ('user__username', 'entity_id', 'ip_address')
    readonly_fields = ('user', 'action', 'entity', 'entity_id', 'timestamp', 'ip_address', 'old_values', 'new_values', 'session_key')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

# Εγγραφή του προσαρμοσμένου UserAdmin
admin.site.register(User, CustomUserAdmin)
