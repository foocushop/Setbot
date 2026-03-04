# Utilisation d'une image Python légère
FROM python:3.11-slim

# Empêcher Python de générer des fichiers .pyc et forcer l'affichage des logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Exposer le port (Railway utilise la variable d'environnement PORT)
EXPOSE 5000

# Commande pour lancer l'application avec Gunicorn (plus stable que le serveur Flask de base)
CMD gunicorn --bind 0.0.0.0:$PORT social_engine:app
