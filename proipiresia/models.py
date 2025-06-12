from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
import os
import uuid
import json

# Μοντέλο για τους ρόλους χρηστών (RBAC)
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Όνομα Ρόλου")
    description = models.TextField(blank=True, null=True, verbose_name="Περιγραφή")
    
    class Meta:
        verbose_name = "Ρόλος"
        verbose_name_plural = "Ρόλοι"
    
    def __str__(self):
        return self.name

# Επέκταση του μοντέλου User του Django για τους υπαλλήλους του τμήματος προσωπικού
class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ρόλος")
    
    # Προσθήκη related_name για την αποφυγή συγκρούσεων
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='proipiresia_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='proipiresia_user_set',
        related_query_name='user',
    )
    
    class Meta:
        verbose_name = "Χρήστης"
        verbose_name_plural = "Χρήστες"
    
    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"

# Μοντέλο για τις ειδικότητες των εκπαιδευτικών
class Specialty(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="Κωδικός Ειδικότητας")
    description = models.CharField(max_length=255, verbose_name="Περιγραφή Ειδικότητας")
    
    class Meta:
        verbose_name = "Ειδικότητα"
        verbose_name_plural = "Ειδικότητες"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.description}"

# Μοντέλο για τους εκπαιδευτικούς
class Teacher(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Όνομα")
    last_name = models.CharField(max_length=100, verbose_name="Επώνυμο")
    father_name = models.CharField(max_length=100, verbose_name="Πατρώνυμο")
    specialties = models.ManyToManyField(Specialty, through='TeacherSpecialty', verbose_name="Ειδικότητες")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Τηλέφωνο")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    
    class Meta:
        verbose_name = "Εκπαιδευτικός"
        verbose_name_plural = "Εκπαιδευτικοί"
        ordering = ['last_name', 'first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['first_name', 'last_name', 'father_name'],
                name='unique_teacher'
            )
        ]
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} του {self.father_name}"

# Μοντέλο για τη σύνδεση εκπαιδευτικών με ειδικότητες (Many-to-Many)
class TeacherSpecialty(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Εκπαιδευτικός")
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, verbose_name="Ειδικότητα")
    is_primary = models.BooleanField(default=False, verbose_name="Κύρια Ειδικότητα")
    
    class Meta:
        verbose_name = "Ειδικότητα Εκπαιδευτικού"
        verbose_name_plural = "Ειδικότητες Εκπαιδευτικών"
        unique_together = ['teacher', 'specialty']
    
    def __str__(self):
        return f"{self.teacher} - {self.specialty}"

# Μοντέλο για τις υπηρεσίες τοποθέτησης
class Service(models.Model):
    CATEGORIES = [
        ('ΚΕΔΑΣΥ', 'ΚΕΔΑΣΥ'),
        ('ΣΔΕΥ', 'ΣΔΕΥ'),
        ('ΣΜΕΑΕ', 'ΣΜΕΑΕ'),
        ('ΑΛΛΟ', 'ΑΛΛΟ'),
    ]
    
    PREFECTURES = [
        ('ΑΙΤΩΛΟΑΚΑΡΝΑΝΙΑ', 'ΑΙΤΩΛΟΑΚΑΡΝΑΝΙΑ'),
        ('ΑΧΑΪΑ', 'ΑΧΑΪΑ'),
        ('ΗΛΕΙΑ', 'ΗΛΕΙΑ'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Όνομα Υπηρεσίας")
    category = models.CharField(max_length=50, choices=CATEGORIES, verbose_name="Κατηγορία")
    prefecture = models.CharField(max_length=50, choices=PREFECTURES, verbose_name="Νομός")
    
    class Meta:
        verbose_name = "Υπηρεσία"
        verbose_name_plural = "Υπηρεσίες"
        ordering = ['prefecture', 'category', 'name']
        unique_together = ['name', 'category', 'prefecture']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()}, {self.get_prefecture_display()})"

# Μοντέλο για τα σχολικά έτη
class SchoolYear(models.Model):
    name = models.CharField(max_length=10, unique=True, verbose_name="Σχολικό Έτος")
    start_date = models.DateField(verbose_name="Ημερομηνία Έναρξης")
    end_date = models.DateField(verbose_name="Ημερομηνία Λήξης")
    is_active = models.BooleanField(default=False, verbose_name="Ενεργό")
    
    class Meta:
        verbose_name = "Σχολικό Έτος"
        verbose_name_plural = "Σχολικά Έτη"
        ordering = ['-name']
    
    def __str__(self):
        return self.name

# Μοντέλο για τους τύπους εκπαιδευτικών (Μόνιμος/Αναπληρωτής)
class EmployeeType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Τύπος Εκπαιδευτικού")
    
    class Meta:
        verbose_name = "Τύπος Εκπαιδευτικού"
        verbose_name_plural = "Τύποι Εκπαιδευτικών"
    
    def __str__(self):
        return self.name

# Μοντέλο για τα υπηρεσιακά συμβούλια ΠΥΣΕΕΠ
class PYSEEP(models.Model):
    act_number = models.CharField(max_length=50, verbose_name="Αριθμός Πράξης")
    date = models.DateField(verbose_name="Ημερομηνία")
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, verbose_name="Σχολικό Έτος")
    
    class Meta:
        verbose_name = "ΠΥΣΕΕΠ"
        verbose_name_plural = "ΠΥΣΕΕΠ"
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['act_number', 'date'],
                name='unique_pyseep'
            )
        ]
    
    def __str__(self):
        return f"ΠΥΣΕΕΠ {self.act_number} ({self.date.strftime('%d/%m/%Y')})"

# Μοντέλο για τους φορείς προϋπηρεσίας
class ServiceProvider(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Όνομα Φορέα")
    
    class Meta:
        verbose_name = "Φορέας Προϋπηρεσίας"
        verbose_name_plural = "Φορείς Προϋπηρεσίας"
        ordering = ['name']
    
    def __str__(self):
        return self.name

# Μοντέλο για τις σχέσεις εργασίας
class EmploymentRelation(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Σχέση Εργασίας")
    
    class Meta:
        verbose_name = "Σχέση Εργασίας"
        verbose_name_plural = "Σχέσεις Εργασίας"
    
    def __str__(self):
        return self.name

# Μοντέλο για τις αιτήσεις αναγνώρισης προϋπηρεσίας
class Application(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Νέα αίτηση'),
        ('PENDING_DOCS', 'Σε αναμονή δικαιολογητικών'),
        ('READY_FOR_PYSEEP', 'Έτοιμη για ΠΥΣΕΕΠ'),
        ('COMPLETED', 'Ολοκληρωμένη από ΠΥΣΕΕΠ'),
    ]
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Εκπαιδευτικός")
    current_service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Υπηρεσία Τρέχουσας Τοποθέτησης")
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, verbose_name="Σχολικό Έτος")
    employee_type = models.ForeignKey(EmployeeType, on_delete=models.CASCADE, verbose_name="Τύπος Εκπαιδευτικού")
    recruitment_phase = models.CharField(max_length=100, blank=True, null=True, verbose_name="Φάση Πρόσληψης")
    submission_date = models.DateField(blank=True, null=True, verbose_name="Ημερομηνία Υποβολής Αίτησης")
    submission_comments = models.CharField(max_length=255, blank=True, null=True, verbose_name="Σχόλια Ημερομηνίας Υποβολής")
    protocol_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Αρ. Πρωτοκόλλου Αίτησης")
    pyseep = models.ForeignKey(PYSEEP, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="ΠΥΣΕΕΠ που θα υποβληθεί")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', verbose_name="Κατάσταση")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ημερομηνία Δημιουργίας")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ημερομηνία Ενημέρωσης")
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='created_applications', verbose_name="Δημιουργήθηκε από")
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='updated_applications', verbose_name="Ενημερώθηκε από")
    version = models.PositiveIntegerField(default=1, verbose_name="Έκδοση")
    is_active = models.BooleanField(default=True, verbose_name="Ενεργή")
    
    def application_file_path(instance, filename):
        # Δημιουργία μοναδικού ονόματος αρχείου
        ext = filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        return os.path.join('applications', str(instance.teacher.id), filename)
    
    application_file = models.FileField(
        upload_to=application_file_path,
        blank=True,
        null=True,
        verbose_name="Αρχείο Αίτησης",
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
        ]
    )
    
    class Meta:
        verbose_name = "Αίτηση"
        verbose_name_plural = "Αιτήσεις"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Αίτηση {self.id} - {self.teacher} ({self.school_year})"
    
    def total_years(self):
        return sum(service.years for service in self.priorservice_set.all())
    
    def total_months(self):
        return sum(service.months for service in self.priorservice_set.all())
    
    def total_days(self):
        return sum(service.days for service in self.priorservice_set.all())
    
    def create_new_version(self):
        """Δημιουργεί νέα έκδοση της αίτησης"""
        self.is_active = False
        self.save()
        
        # Δημιουργία νέας αίτησης με αυξημένη έκδοση
        new_application = Application.objects.create(
            teacher=self.teacher,
            current_service=self.current_service,
            school_year=self.school_year,
            employee_type=self.employee_type,
            recruitment_phase=self.recruitment_phase,
            submission_date=self.submission_date,
            submission_comments=self.submission_comments,
            protocol_number=self.protocol_number,
            pyseep=self.pyseep,
            status='NEW',
            created_by=self.updated_by,
            version=self.version + 1,
            application_file=self.application_file
        )
        
        # Αντιγραφή των προϋπηρεσιών
        for service in self.priorservice_set.all():
            PriorService.objects.create(
                application=new_application,
                service_provider=service.service_provider,
                protocol_number=service.protocol_number,
                employment_relation=service.employment_relation,
                start_date=service.start_date,
                end_date=service.end_date,
                years=service.years,
                months=service.months,
                days=service.days,
                history=service.history,
                verified=None,
                notes=service.notes,
                internal_notes=service.internal_notes,
                created_by=new_application.created_by
            )
        
        return new_application

# Μοντέλο για τις προϋπηρεσίες
class PriorService(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name="Αίτηση")
    service_provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, verbose_name="Φορέας Προϋπηρεσίας")
    protocol_number = models.CharField(max_length=100, default="ΟΠΣΥΔ", verbose_name="Αρ. Πρωτοκόλλου/Βεβ. Προϋπηρεσίας")
    employment_relation = models.ForeignKey(EmploymentRelation, on_delete=models.CASCADE, verbose_name="Σχέση Εργασίας")
    start_date = models.DateField(verbose_name="Από")
    end_date = models.DateField(verbose_name="Έως")
    years = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Έτη")
    months = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(11)], verbose_name="Μήνες")
    days = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(30)], verbose_name="Ημέρες")
    history = models.TextField(blank=True, null=True, verbose_name="Ιστορικό")
    verified = models.DateTimeField(blank=True, null=True, verbose_name="Ελέγχθηκε")
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_services', verbose_name="Ελέγχθηκε από")
    notes = models.TextField(blank=True, null=True, verbose_name="Παρατηρήσεις")
    internal_notes = models.TextField(blank=True, null=True, verbose_name="Εσωτερικές Σημειώσεις")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ημερομηνία Δημιουργίας")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ημερομηνία Ενημέρωσης")
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='created_services', verbose_name="Δημιουργήθηκε από")
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='updated_services', verbose_name="Ενημερώθηκε από")
    version_id = models.PositiveIntegerField(default=1, verbose_name="ID Έκδοσης")
    is_active = models.BooleanField(default=True, verbose_name="Ενεργή")
    
    class Meta:
        verbose_name = "Προϋπηρεσία"
        verbose_name_plural = "Προϋπηρεσίες"
        ordering = ['start_date']
    
    def __str__(self):
        return f"{self.service_provider} ({self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Έλεγχος ότι η ημερομηνία λήξης είναι μεταγενέστερη της ημερομηνίας έναρξης
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'Η ημερομηνία λήξης πρέπει να είναι μεταγενέστερη της ημερομηνίας έναρξης.'})
        
        # Έλεγχος για αλληλεπικαλυπτόμενες περιόδους
        # Ελέγχουμε αν το πεδίο application έχει οριστεί
        if hasattr(self, 'application') and self.application is not None:
            overlapping = PriorService.objects.filter(
                application=self.application,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError('Υπάρχει αλληλεπικάλυψη με άλλη προϋπηρεσία στην ίδια αίτηση.')
    
    def save(self, *args, **kwargs):
        # Υπολογισμός ετών, μηνών, ημερών αν δεν έχουν οριστεί
        if self.start_date and self.end_date and (self.years == 0 and self.months == 0 and self.days == 0):
            # Απλός υπολογισμός - θα αντικατασταθεί με τον ακριβή τύπο αργότερα
            delta = self.end_date - self.start_date
            total_days = delta.days + 1  # Συμπεριλαμβάνουμε και την τελευταία ημέρα
            
            self.years = total_days // 365
            remaining_days = total_days % 365
            self.months = remaining_days // 30
            self.days = remaining_days % 30
        
        super().save(*args, **kwargs)
    
    def mark_as_verified(self, user):
        """Σημειώνει την προϋπηρεσία ως ελεγμένη"""
        self.verified = timezone.now()
        self.verified_by = user
        self.save()
    
    def create_new_version(self, application=None):
        """Δημιουργεί νέα έκδοση της προϋπηρεσίας"""
        self.is_active = False
        self.save()
        
        # Δημιουργία νέας προϋπηρεσίας με αυξημένο version_id
        return PriorService.objects.create(
            application=application or self.application,
            service_provider=self.service_provider,
            protocol_number=self.protocol_number,
            employment_relation=self.employment_relation,
            start_date=self.start_date,
            end_date=self.end_date,
            years=self.years,
            months=self.months,
            days=self.days,
            history=self.history,
            notes=self.notes,
            internal_notes=self.internal_notes,
            created_by=self.updated_by,
            version_id=self.version_id + 1
        )
    
    def get_history_records(self):
        """Επιστρέφει το ιστορικό της προϋπηρεσίας από προηγούμενες αιτήσεις"""
        # Αναζήτηση παρόμοιων προϋπηρεσιών με βάση τα κύρια χαρακτηριστικά
        similar_services = PriorService.objects.filter(
            service_provider=self.service_provider,
            start_date=self.start_date,
            end_date=self.end_date,
            application__teacher=self.application.teacher,
            application__status='COMPLETED'  # Μόνο ολοκληρωμένες αιτήσεις
        ).exclude(
            id=self.id
        ).select_related(
            'application',
            'application__pyseep',
            'application__school_year',
            'verified_by'
        ).order_by('-application__created_at')
        
        history_records = []
        for service in similar_services:
            record = {
                'application': service.application,
                'verified_by': service.verified_by,
                'verified_date': service.verified,
                'pyseep': service.application.pyseep,
                'service_id': service.id,
                'version': service.application.version,
                'school_year': service.application.school_year,
                'employment_relation': service.employment_relation,
                'protocol_number': service.protocol_number,
                'years': service.years,
                'months': service.months,
                'days': service.days
            }
            history_records.append(record)
        
        return history_records

# Μοντέλο για την καταγραφή ενεργειών (Audit Trail)
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Δημιουργία'),
        ('UPDATE', 'Ενημέρωση'),
        ('DELETE', 'Διαγραφή'),
        ('STATUS_CHANGE', 'Αλλαγή Κατάστασης'),
        ('VERIFY', 'Επαλήθευση'),
        ('LOGIN', 'Σύνδεση'),
        ('LOGOUT', 'Αποσύνδεση'),
    ]
    
    ENTITY_CHOICES = [
        ('APPLICATION', 'Αίτηση'),
        ('PRIOR_SERVICE', 'Προϋπηρεσία'),
        ('TEACHER', 'Εκπαιδευτικός'),
        ('USER', 'Χρήστης'),
        ('PYSEEP', 'ΠΥΣΕΕΠ'),
        ('OTHER', 'Άλλο'),
    ]
    
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name="Χρήστης")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Ενέργεια")
    entity = models.CharField(max_length=20, choices=ENTITY_CHOICES, verbose_name="Οντότητα")
    entity_id = models.PositiveIntegerField(verbose_name="ID Οντότητας")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Χρονική Στιγμή")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="Διεύθυνση IP")
    old_values = models.JSONField(blank=True, null=True, verbose_name="Παλιές Τιμές")
    new_values = models.JSONField(blank=True, null=True, verbose_name="Νέες Τιμές")
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name="Κλειδί Συνεδρίας")
    
    class Meta:
        verbose_name = "Καταγραφή Ενεργειών"
        verbose_name_plural = "Καταγραφές Ενεργειών"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} {self.get_entity_display()} {self.entity_id} από {self.user} στις {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}"
