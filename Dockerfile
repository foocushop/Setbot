# Image de base avec Python et Playwright pré-installé
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installation du navigateur Chromium
RUN playwright install chromium

# Copie du code
COPY . .

# Exposition du port
EXPOSE 5000

# Commande de démarrage
CMD ["python", "social_engine.py"]
