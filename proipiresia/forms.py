from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    User, Teacher, Specialty, TeacherSpecialty, Service, 
    SchoolYear, EmployeeType, PYSEEP, ServiceProvider, 
    EmploymentRelation, Application, PriorService
)

# Φόρμα σύνδεσης χρήστη
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Όνομα Χρήστη',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Όνομα Χρήστη'})
    )
    password = forms.CharField(
        label='Κωδικός Πρόσβασης',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Κωδικός Πρόσβασης'})
    )

# Φόρμα δημιουργίας χρήστη
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

# Φόρμα για το μοντέλο Teacher
class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ('first_name', 'last_name', 'father_name', 'phone', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# Φόρμα για το μοντέλο TeacherSpecialty
class TeacherSpecialtyForm(forms.ModelForm):
    class Meta:
        model = TeacherSpecialty
        fields = ('specialty', 'is_primary')
        widgets = {
            'specialty': forms.Select(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# Φόρμα για το μοντέλο Application
class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = (
            'teacher', 'current_service', 'school_year', 'employee_type',
            'recruitment_phase', 'submission_date', 'submission_comments',
            'protocol_number', 'pyseep', 'application_file'
        )
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'current_service': forms.Select(attrs={'class': 'form-control'}),
            'school_year': forms.Select(attrs={'class': 'form-control'}),
            'employee_type': forms.Select(attrs={'class': 'form-control'}),
            'recruitment_phase': forms.TextInput(attrs={'class': 'form-control'}),
            'submission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'submission_comments': forms.TextInput(attrs={'class': 'form-control'}),
            'protocol_number': forms.TextInput(attrs={'class': 'form-control'}),
            'pyseep': forms.Select(attrs={'class': 'form-control'}),
            'application_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_application_file(self):
        file = self.cleaned_data.get('application_file')
        if file:
            # Έλεγχος μεγέθους αρχείου (20MB)
            if file.size > 20 * 1024 * 1024:
                raise ValidationError('Το μέγεθος του αρχείου δεν μπορεί να υπερβαίνει τα 20MB.')
            
            # Έλεγχος τύπου αρχείου
            if not file.name.endswith('.pdf'):
                raise ValidationError('Μόνο αρχεία PDF επιτρέπονται.')
        
        return file

# Φόρμα για την αλλαγή κατάστασης αίτησης
class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('status',)
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

# Φόρμα για το μοντέλο PriorService
class PriorServiceForm(forms.ModelForm):
    class Meta:
        model = PriorService
        fields = (
            'service_provider', 'protocol_number', 'employment_relation',
            'start_date', 'end_date', 'years', 'months', 'days',
            'notes', 'internal_notes'
        )
        widgets = {
            'service_provider': forms.Select(attrs={'class': 'form-control'}),
            'protocol_number': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_relation': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'months': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '11'}),
            'days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '30'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError('Η ημερομηνία λήξης πρέπει να είναι μεταγενέστερη της ημερομηνίας έναρξης.')
        
        return cleaned_data

# Φόρμα για την επαλήθευση προϋπηρεσίας
class VerifyPriorServiceForm(forms.Form):
    verified = forms.BooleanField(
        required=False,
        label='Επαλήθευση',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

# Φόρμα για την αναζήτηση αιτήσεων
class ApplicationSearchForm(forms.Form):
    teacher_name = forms.CharField(
        required=False,
        label='Όνομα/Επώνυμο Εκπαιδευτικού',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    school_year = forms.ModelChoiceField(
        required=False,
        queryset=SchoolYear.objects.all(),
        label='Σχολικό Έτος',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    current_service = forms.ModelChoiceField(
        required=False,
        queryset=Service.objects.all(),
        label='Υπηρεσία Τοποθέτησης',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + list(Application.STATUS_CHOICES),
        label='Κατάσταση',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    pyseep = forms.ModelChoiceField(
        required=False,
        queryset=PYSEEP.objects.all(),
        label='ΠΥΣΕΕΠ',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

# Φόρμα για την αναζήτηση προϋπηρεσιών
class PriorServiceSearchForm(forms.Form):
    teacher_name = forms.CharField(
        required=False,
        label='Όνομα/Επώνυμο Εκπαιδευτικού',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    service_provider = forms.ModelChoiceField(
        required=False,
        queryset=ServiceProvider.objects.all(),
        label='Φορέας Προϋπηρεσίας',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date_from = forms.DateField(
        required=False,
        label='Ημερομηνία Έναρξης Από',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    start_date_to = forms.DateField(
        required=False,
        label='Ημερομηνία Έναρξης Έως',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    verified = forms.ChoiceField(
        required=False,
        choices=[
            ('', '---------'),
            ('yes', 'Ναι'),
            ('no', 'Όχι')
        ],
        label='Επαληθευμένη',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

# Φόρμα για την εξαγωγή αναφοράς
class ReportForm(forms.Form):
    pyseep = forms.ModelChoiceField(
        required=True,
        queryset=PYSEEP.objects.all(),
        label='ΠΥΣΕΕΠ',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    current_service = forms.ModelChoiceField(
        required=False,
        queryset=Service.objects.all(),
        label='Υπηρεσία Τοποθέτησης',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    format = forms.ChoiceField(
        required=True,
        choices=[
            ('xlsx', 'Excel'),
            ('pdf', 'PDF'),
            ('docx', 'Word')
        ],
        label='Μορφή Αρχείου',
        widget=forms.Select(attrs={'class': 'form-control'})
    )