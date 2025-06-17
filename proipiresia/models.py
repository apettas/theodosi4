from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
import os
import uuid
import json
import math # Import math module for rounding
import datetime # Import datetime for timedelta

# Helper function to calculate days between dates using the 360-day year (European method)
def days360_european(start_date, end_date):
    """
    Calculates the number of days between two dates based on a 360-day year
    (twelve 30-day months), using the European method.
    """
    start_day = start_date.day
    start_month = start_date.month
    start_year = start_date.year

    end_day = end_date.day
    end_month = end_date.month
    end_year = end_date.year

    # If the start day is 31, it becomes 30.
    if start_day == 31:
        start_day = 30

    # If the end day is 31, it becomes 30.
    if end_day == 31:
        end_day = 30

    return (end_year - start_year) * 360 + (end_month - start_month) * 30 + (end_day - start_day)

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
    
    @property
    def total_calculated_years(self):
        # I11
        total_years_raw = self.priorservice_set.aggregate(Sum('years'))['years__sum'] or 0
        # J11
        total_months_raw = self.priorservice_set.aggregate(Sum('months'))['months__sum'] or 0
        # K11
        total_days_raw = self.priorservice_set.aggregate(Sum('days'))['days__sum'] or 0

        # Excel equivalent: =I11+QUOTIENT((J11+QUOTIENT(K11;30));12)
        # K11/30 = QUOTIENT(K11;30)
        days_to_months = math.floor(total_days_raw / 30)
        
        # J11 + QUOTIENT(K11;30) = total_months_raw + days_to_months
        months_total_temp = total_months_raw + days_to_months
        
        # QUOTIENT((J11+QUOTIENT(K11;30));12) = months_total_temp / 12
        months_to_years = math.floor(months_total_temp / 12)
        
        return total_years_raw + months_to_years

    @property
    def total_calculated_months(self):
        # J11
        total_months_raw = self.priorservice_set.aggregate(Sum('months'))['months__sum'] or 0
        # K11
        total_days_raw = self.priorservice_set.aggregate(Sum('days'))['days__sum'] or 0

        # Excel equivalent: =MOD((J11+QUOTIENT(K11;30));12)
        days_to_months = math.floor(total_days_raw / 30)
        months_total_temp = total_months_raw + days_to_months
        
        return months_total_temp % 12

    @property
    def total_calculated_days(self):
        # K11
        total_days_raw = self.priorservice_set.aggregate(Sum('days'))['days__sum'] or 0
        
        # Excel equivalent: =MOD(K11;30)
        return total_days_raw % 30 # This correctly applies MOD 30 to raw days, then it's calculated from the sum values

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
                reduced_hours=service.reduced_hours,
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
    # Τα πεδία διάρκειας υπολογίζονται αυτόματα
    years = models.PositiveSmallIntegerField(default=0, verbose_name="Έτη")
    months = models.PositiveSmallIntegerField(default=0, verbose_name="Μήνες")
    days = models.PositiveSmallIntegerField(default=0, verbose_name="Ημέρες")
    # Νέο πεδίο για ώρες μειωμένου ωραρίου
    reduced_hours = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(40)],
        verbose_name="Ώρες Μειωμένου/Υποχρεωτικού",
        default=40 # Προσθήκη default τιμής
    )
    history = models.TextField(blank=True, null=True, verbose_name="Ιστορικό")
    # Νέο πεδίο για χειροκίνητη παράκαμψη του υπολογισμού
    manual_override = models.BooleanField(default=False, verbose_name="Χειροκίνητη Παράκαμψη")
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
        # Τα πεδία διάρκειας υπολογίζονται αυτόματα
        # Δεν χρειάζεται να ορίσουμε 'fields' εδώ, καθώς δεν χρησιμοποιούμε ModelForm για αυτό το μοντέλο
        # fields = '__all__' # Αφαίρεση αυτής της γραμμής
 
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
        
        # Έλεγχος για το νέο πεδίο reduced_hours
        reduced_hours = self.reduced_hours
        if reduced_hours is not None:
            if not (1 <= reduced_hours <= 40):
                 raise ValidationError({'reduced_hours': 'Οι ώρες μειωμένου/υποχρεωτικού πρέπει να είναι μεταξύ 1 και 40.'})
 
    def save(self, *args, **kwargs):
        # Υπολογισμός ετών, μηνών, ημερών με βάση τους τύπους του Excel, ΜΟΝΟ αν manual_override είναι False
        if not self.manual_override and self.start_date and self.end_date and self.reduced_hours is not None:
            # Υπολογισμός συνολικών ημερών με DAYS360 (Ευρωπαϊκή μέθοδος)
            # Προσθήκη 1 ημέρας στην end_date όπως στον τύπο του Excel
            total_days_360 = days360_european(self.start_date, self.end_date + datetime.timedelta(days=1))
 
            # Υπολογισμός συνολικών "κανονικοποιημένων" ημερών (D9 στο Excel)
            # =ROUND((F6*D6/E6);0) όπου F6=total_days_360, D6=reduced_hours, E6=40
            total_normalized_days = round((total_days_360 * self.reduced_hours / 40))
 
            # Υπολογισμός ετών, μηνών, ημερών από τις total_normalized_days
            # =INT(D9/360)
            self.years = math.floor(total_normalized_days / 360)
            
            # =INT((D9-(C15*360))/30) όπου C15=years
            remaining_days_after_years = total_normalized_days - (self.years * 360)
            self.months = math.floor(remaining_days_after_years / 30)
            
            # =D9-(C15*360)-(D15*30) όπου C15=years, D15=months
            self.days = total_normalized_days - (self.years * 360) - (self.months * 30)
        elif self.manual_override:
            # Εάν είναι χειροκίνητη παράκαμψη, βεβαιωνόμαστε ότι οι τιμές είναι εντός των ορίων
            self.years = max(0, self.years)
            self.months = max(0, min(11, self.months))
            self.days = max(0, min(30, self.days))
        else:
            # Αν δεν υπάρχουν οι απαραίτητες τιμές και δεν είναι manual override, μηδενίζουμε τα πεδία διάρκειας
            self.years = 0
            self.months = 0
            self.days = 0
 
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
            years=self.years, # Αντιγραφή του υπολογισμένου/χειροκίνητου πεδίου
            months=self.months, # Αντιγραφή του υπολογισμένου/χειροκίνητου πεδίου
            days=self.days, # Αντιγραφή του υπολογισμένου/χειροκίνητου πεδίου
            reduced_hours=self.reduced_hours, # Αντιγραφή του νέου πεδίου
            manual_override=self.manual_override, # Αντιγραφή του νέου πεδίου
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
                'years': service.years, # Συμπερίληψη του υπολογισμένου/χειροκίνητου πεδίου
                'months': service.months, # Συμπερίληψη του υπολογισμένου/χειροκίνητου πεδίου
                'days': service.days, # Συμπερίληψη του υπολογισμένου/χειροκίνητου πεδίου
                'reduced_hours': service.reduced_hours, # Προσθήκη του νέου πεδίου στο ιστορικό
                'manual_override': service.manual_override # Προσθήκη του νέου πεδίου στο ιστορικό
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
