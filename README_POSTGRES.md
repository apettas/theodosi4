# Μετακίνηση σε PostgreSQL - Οδηγίες

## Περίληψη Αλλαγών

Το project έχει ενημερωθεί για να υποστηρίζει PostgreSQL αντί για SQLite. Οι κύριες αλλαγές είναι:

### 1. Νέες Dependencies
- `psycopg2-binary`: PostgreSQL adapter για Python
- `python-dotenv`: Για environment variables
- `dj-database-url`: Για parsing PostgreSQL URLs

### 2. Ενημερωμένα Settings
- Υποστήριξη PostgreSQL με environment variables
- Fallback σε SQLite για local development
- Καλύτερη διαχείριση configurations

### 3. Docker Configuration
- PostgreSQL service στο docker-compose.yml
- Αυτόματο migration κατά την εκκίνηση
- Persistent volume για τα δεδομένα

## Οδηγίες Εγκατάστασης

### Για Local Development (Windows)

1. **Backup των υπαρχόντων δεδομένων:**
   ```bash
   python manage.py dumpdata --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.permission > data_backup.json
   ```

2. **Εγκατάσταση νέων dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Για Production (Ubuntu Server με Docker)

1. **Pull των νέων αλλαγών από GitHub:**
   ```bash
   git pull origin main
   ```

2. **Σταμάτημα των υπαρχόντων containers:**
   ```bash
   docker-compose down
   ```

3. **Καθαρισμός των παλιών images (προαιρετικό):**
   ```bash
   docker system prune -f
   docker volume prune -f
   ```

4. **Build και εκκίνηση με PostgreSQL:**
   ```bash
   docker-compose up --build -d
   ```

5. **Δημιουργία superuser (αν χρειάζεται):**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## Environment Variables

Στο production, μπορείτε να ορίσετε τις παρακάτω μεταβλητές:

```bash
SECRET_KEY=your-production-secret-key
DEBUG=False
DATABASE_URL=postgres://theodosi4_user:theodosi4_password@db:5432/theodosi4_db
```

## Έλεγχος Λειτουργίας

1. **Έλεγχος containers:**
   ```bash
   docker-compose ps
   ```

2. **Έλεγχος logs:**
   ```bash
   docker-compose logs web
   docker-compose logs db
   ```

3. **Σύνδεση στη βάση (debugging):**
   ```bash
   docker-compose exec db psql -U theodosi4_user -d theodosi4_db
   ```

## Migration Δεδομένων

Αν έχετε υπάρχοντα δεδομένα στο SQLite και θέλετε να τα μεταφέρετε:

1. **Εκτέλεση του migration script:**
   ```bash
   python migrate_to_postgres.py
   ```

2. **Ή manual migration:**
   ```bash
   # Export από SQLite
   python manage.py dumpdata > backup.json
   
   # Αλλαγή σε PostgreSQL settings
   # Import στο PostgreSQL
   python manage.py migrate
   python manage.py loaddata backup.json
   ```

## Troubleshooting

### Πρόβλημα: "PostgreSQL is unavailable"
- Περιμένετε λίγα δευτερόλεπτα μέχρι να ξεκινήσει η PostgreSQL
- Ελέγξτε: `docker-compose logs db`

### Πρόβλημα: "Connection refused"
- Βεβαιωθείτε ότι το PostgreSQL container τρέχει
- Ελέγξτε τις environment variables

### Πρόβλημα: "Migration errors"
- Καθαρίστε τα volumes: `docker-compose down -v`
- Ξεκινήστε από την αρχή: `docker-compose up --build`

## Backup Strategy

1. **Αυτόματο backup δεδομένων:**
   ```bash
   docker-compose exec db pg_dump -U theodosi4_user theodosi4_db > backup_$(date +%Y%m%d).sql
   ```

2. **Restore από backup:**
   ```bash
   docker-compose exec -T db psql -U theodosi4_user theodosi4_db < backup_20241213.sql
   ```

## Επόμενα Βήματα

1. ✅ Ενημέρωση dependencies
2. ✅ Ρύθμιση PostgreSQL
3. ✅ Docker configuration
4. 🔄 Testing στο production
5. 📝 Δημιουργία backup strategy
6. 🔒 Ενίσχυση security (production secrets)

---

**Σημείωση:** Μετά την επιτυχή μετακίνηση, μπορείτε να διαγράψετε το αρχείο `db.sqlite3` από το production server.