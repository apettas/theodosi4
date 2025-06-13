# Γρήγορος Οδηγός Deployment για Ubuntu Server 🚀

## Συνοπτικά Βήματα

### 1. Προετοιμασία Ubuntu Server
```bash
# Σύνδεση στον server
ssh username@your-server-ip

# Ενημέρωση συστήματος
sudo apt update && sudo apt upgrade -y

# Εγκατάσταση Git (αν δεν υπάρχει)
sudo apt install -y git
```

### 2. Κλωνοποίηση Project
```bash
# Κλωνοποίηση από GitHub
git clone https://github.com/your-username/THEODOSI4.git
cd THEODOSI4

# Ή μεταφορά αρχείων με scp
scp -r /path/to/THEODOSI4 username@server-ip:/home/username/
```

### 3. Ρύθμιση Environment
```bash
# Δημιουργία .env file από template
cp .env.production.template .env

# Επεξεργασία .env με τις production τιμές
nano .env
```

**Σημαντικό:** Άλλαξε τα εξής στο `.env`:
- `SECRET_KEY` → Μακρύ random string
- `ALLOWED_HOSTS` → Το domain και IP του server σου
- `DB_PASSWORD` → Ασφαλές password για τη βάση
- Email settings (αν χρειάζεται)

### 4. Εκτέλεση Deployment Script
```bash
# Κάνε το script εκτελέσιμο
chmod +x deploy_ubuntu.sh

# Εκτέλεση deployment
./deploy_ubuntu.sh
```

Το script θα:
- ✅ Εγκαταστήσει Docker και Docker Compose (αν δεν υπάρχουν)
- ✅ Ελέγξει το .env file
- ✅ Κάνει build τα containers
- ✅ Εκτελέσει migrations
- ✅ Συλλέξει static files
- ✅ Προσφέρει δημιουργία superuser
- ✅ Θα ελέγξει ότι όλα λειτουργούν

### 5. Έλεγχος Λειτουργίας
```bash
# Έλεγχος containers
sudo docker-compose ps

# Έλεγχος logs
sudo docker-compose logs web

# Test στο browser
curl http://localhost:8000
curl http://localhost:8000/admin
```

### 6. Firewall & Nginx (Προαιρετικό)
```bash
# Άνοιγμα port
sudo ufw allow 8000

# Για production με Nginx
sudo apt install -y nginx
# Δες το README_POSTGRES.md για πλήρη οδηγίες Nginx
```

---

## Χρήσιμες Εντολές

### Logs
```bash
sudo docker-compose logs -f web    # Django logs
sudo docker-compose logs -f db     # PostgreSQL logs
```

### Restart
```bash
sudo docker-compose restart web    # Restart Django
sudo docker-compose restart db     # Restart PostgreSQL
```

### Backup
```bash
# Backup database
sudo docker-compose exec db pg_dump -U theodosi4_user theodosi4_prod > backup_$(date +%Y%m%d).sql
```

### Update
```bash
git pull origin main
sudo docker-compose up --build -d
```

---

## Troubleshooting

### Το admin δεν φορτώνει CSS
✅ **Επιλύθηκε!** Το WhiteNoise middleware αναλαμβάνει τα static files

### Δεν μπορώ να συνδεθώ στη βάση
- Έλεγξε το `.env` file
- Βεβαιώσου ότι το DB container τρέχει: `sudo docker-compose ps`

### Permission errors
```bash
sudo chown -R $USER:$USER /path/to/THEODOSI4
```

---

## 🎯 Έτοιμο για Production!

Μετά το deployment, η εφαρμογή θα είναι διαθέσιμη στο:
- **Main site:** `http://your-server-ip:8000`
- **Admin:** `http://your-server-ip:8000/admin`

Για παραγωγή προτείνεται:
1. Nginx reverse proxy
2. SSL certificate (Let's Encrypt)
3. Automated backups
4. Monitoring

Δες το `README_POSTGRES.md` για πλήρεις οδηγίες παραγωγής.