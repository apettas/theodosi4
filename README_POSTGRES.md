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

## Ubuntu Server Deployment

### Prerequisites στον Ubuntu Server

1. **Εγκατάσταση Docker και Docker Compose**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   sudo apt install -y docker.io
   sudo systemctl start docker
   sudo systemctl enable docker
   
   # Install Docker Compose
   sudo apt install -y docker-compose
   
   # Add user to docker group (optional)
   sudo usermod -aG docker $USER
   # Logout and login again for group changes to take effect
   ```

2. **Μεταφορά αρχείων στον Ubuntu Server**
   
   Μεταφέρε τα ακόλουθα αρχεία στον Ubuntu server:
   ```
   - docker-compose.yml
   - Dockerfile
   - requirements.txt
   - .env (με τις σωστές παραμέτρους για production)
   - Όλο το Django project directory
   ```

### Deployment Steps

1. **Κλωνοποίηση ή μεταφορά του project**
   ```bash
   # Αν χρησιμοποιείς Git
   git clone <repository-url>
   cd THEODOSI4
   
   # Ή μεταφορά αρχείων με scp
   scp -r /path/to/THEODOSI4 user@server:/path/to/destination/
   ```

2. **Δημιουργία .env file για production**
   ```bash
   # Δημιούργησε ή επεξεργάσου το .env file
   nano .env
   ```
   
   Παράδειγμα production `.env`:
   ```
   DEBUG=False
   SECRET_KEY=your-very-long-secret-key-here-make-it-unique
   ALLOWED_HOSTS=your-domain.com,your-server-ip,localhost
   
   # PostgreSQL settings
   DB_NAME=theodosi4_prod
   DB_USER=theodosi4_user
   DB_PASSWORD=secure-password-here-change-this
   DB_HOST=db
   DB_PORT=5432
   
   # Email settings (optional)
   EMAIL_HOST=smtp.your-provider.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@domain.com
   EMAIL_HOST_PASSWORD=your-email-password
   EMAIL_USE_TLS=True
   ```

3. **Build και εκτέλεση των containers**
   ```bash
   # Stop existing containers (if any)
   sudo docker-compose down
   
   # Build and start containers
   sudo docker-compose up --build -d
   
   # Check if containers are running
   sudo docker-compose ps
   ```

4. **Database migrations και superuser**
   ```bash
   # Run migrations
   sudo docker-compose exec web python manage.py migrate
   
   # Create superuser
   sudo docker-compose exec web python manage.py createsuperuser
   
   # Collect static files (handled automatically by WhiteNoise)
   sudo docker-compose exec web python manage.py collectstatic --noinput
   ```

5. **Έλεγχος λειτουργίας**
   ```bash
   # Check logs
   sudo docker-compose logs web
   sudo docker-compose logs db
   
   # Test the application
   curl http://localhost:8000
   curl http://localhost:8000/admin  # Should load with CSS
   ```

### Production Considerations

1. **Firewall Configuration**
   ```bash
   # Allow HTTP and HTTPS traffic
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw allow 8000  # Temporary for testing
   ```

2. **Nginx Reverse Proxy (Recommended)**
   ```bash
   # Install Nginx
   sudo apt install -y nginx
   
   # Create Nginx configuration
   sudo nano /etc/nginx/sites-available/theodosi4
   ```
   
   Nginx configuration:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com your-server-ip;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # Static files are handled by WhiteNoise in Django
       # No need for separate static file serving
   }
   ```
   
   ```bash
   # Enable site
   sudo ln -s /etc/nginx/sites-available/theodosi4 /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

3. **SSL Certificate με Let's Encrypt**
   ```bash
   # Install Certbot
   sudo apt install -y certbot python3-certbot-nginx
   
   # Get SSL certificate
   sudo certbot --nginx -d your-domain.com
   ```

4. **Auto-start containers**
   ```bash
   # Add restart policy to docker-compose.yml or use:
   sudo docker-compose up -d --restart unless-stopped
   ```

### Maintenance Commands

```bash
# View logs
sudo docker-compose logs -f web
sudo docker-compose logs -f db

# Restart services
sudo docker-compose restart web
sudo docker-compose restart db

# Update application
git pull origin main  # or your branch
sudo docker-compose up --build -d

# Backup database
sudo docker-compose exec db pg_dump -U theodosi4_user theodosi4_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
sudo docker-compose exec -T db psql -U theodosi4_user theodosi4_prod < backup_file.sql
```

## Επόμενα Βήματα

1. ✅ Ενημέρωση dependencies
2. ✅ Ρύθμιση PostgreSQL
3. ✅ Docker configuration
4. ✅ Static files με WhiteNoise (Django admin CSS λειτουργεί)
5. ✅ Testing στο production
6. 📝 Δημιουργία backup strategy
7. 🔒 Ενίσχυση security (production secrets)

---

**Σημειώσεις:**
- Μετά την επιτυχή μετακίνηση, μπορείτε να διαγράψετε το αρχείο `db.sqlite3` από το production server
- Το WhiteNoise middleware αναλαμβάνει αυτόματα το serving των static files (CSS, JS, images)
- Το Django admin interface τώρα φορτώνει σωστά στο production environment