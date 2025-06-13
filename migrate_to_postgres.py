#!/usr/bin/env python
"""
Script για μετακίνηση δεδομένων από SQLite σε PostgreSQL
Χρήση: python migrate_to_postgres.py
"""

import os
import sys
import django
from django.core.management import call_command
from django.db import connections
from django.conf import settings

def migrate_data():
    """Μεταφέρει δεδομένα από SQLite σε PostgreSQL"""
    
    print("🔄 Ξεκινάει η μετακίνηση δεδομένων από SQLite σε PostgreSQL...")
    
    # Ελέγχουμε αν υπάρχει το SQLite file
    sqlite_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    if not os.path.exists(sqlite_path):
        print("❌ Δεν βρέθηκε το αρχείο db.sqlite3")
        return False
    
    try:
        # Backup των δεδομένων από SQLite
        print("📦 Δημιουργία backup από SQLite...")
        
        # Δημιουργούμε προσωρινή ρύθμιση για SQLite
        old_databases = settings.DATABASES.copy()
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': sqlite_path,
            }
        }
        
        # Export δεδομένων
        with open('data_backup.json', 'w', encoding='utf-8') as f:
            call_command('dumpdata', '--natural-foreign', '--natural-primary', 
                        '--exclude=contenttypes', '--exclude=auth.permission',
                        stdout=f, verbosity=0)
        
        print("✅ Backup ολοκληρώθηκε: data_backup.json")
        
        # Επαναφορά PostgreSQL ρυθμίσεων
        settings.DATABASES = old_databases
        
        # Δημιουργία tables στο PostgreSQL
        print("🏗️  Δημιουργία tables στο PostgreSQL...")
        call_command('migrate', verbosity=0)
        
        # Import δεδομένων στο PostgreSQL
        print("📥 Εισαγωγή δεδομένων στο PostgreSQL...")
        call_command('loaddata', 'data_backup.json', verbosity=0)
        
        print("✅ Μετακίνηση ολοκληρώθηκε επιτυχώς!")
        print("📝 Το backup αρχείο data_backup.json διατηρήθηκε για ασφάλεια")
        
        return True
        
    except Exception as e:
        print(f"❌ Σφάλμα κατά τη μετακίνηση: {e}")
        return False

if __name__ == '__main__':
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Theodosi4.settings')
    django.setup()
    
    # Εκτέλεση migration
    success = migrate_data()
    
    if success:
        print("\n🎉 Η μετακίνηση ολοκληρώθηκε!")
        print("Μπορείτε τώρα να τρέξετε το Docker container με PostgreSQL.")
    else:
        print("\n❌ Η μετακίνηση απέτυχε!")
        sys.exit(1)