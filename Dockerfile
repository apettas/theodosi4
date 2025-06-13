# Χρησιμοποίησε μια επίσημη Python runtime ως base image
FROM python:3.11-slim

# Ορισμός μεταβλητών περιβάλλοντος
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Ορισμός του working directory μέσα στο container
WORKDIR /app

# Εγκατάσταση system dependencies που μπορεί να χρειάζονται οι βιβλιοθήκες Python
# (π.χ. για Pillow, lxml). Προσαρμόστε ανάλογα με τις ανάγκες.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libxml2-dev \
    libxslt1-dev \
    libfreetype6-dev \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Αντιγραφή του αρχείου requirements.txt στο container
COPY requirements.txt /app/

# Εγκατάσταση των Python εξαρτήσεων
RUN pip install --no-cache-dir -r requirements.txt

# Αντιγραφή του υπόλοιπου κώδικα της εφαρμογής στο container
COPY . /app/

# Έκθεση της πόρτας 8000 που τρέχει η Django εφαρμογή
EXPOSE 8000

# Εντολή για εκτέλεση της εφαρμογής.
# Για development: CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# Για production (χρησιμοποιώντας Gunicorn):
#CMD ["gunicorn", "THEODOSI4.wsgi:application", "--bind", "0.0.0.0:8000"]

CMD ["gunicorn", "Theodosi4.wsgi:application", "--bind", "0.0.0.0:8000"]