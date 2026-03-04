# Utiliser une image Python légère
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier de dépendances
COPY requirements.txt .

# Installer les bibliothèques Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code (social_engine.py)
COPY . .

# Exposer le port par défaut de Railway
EXPOSE 5000

# Lancer l'application avec Gunicorn (plus stable que le serveur de dev Flask)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "social_engine:app"]
