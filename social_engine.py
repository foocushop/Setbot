import os
import time
import random
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app)

SESSION_DIR = "/tmp/sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def fetch_fresh_proxies():
    """Récupère une liste de proxies publics via plusieurs sources gratuites"""
    sources = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
        "https://www.proxy-list.download/api/v1/get?type=https"
    ]
    all_proxies = []
    for source in sources:
        try:
            r = requests.get(source, timeout=5)
            if r.status_code == 200:
                all_proxies.extend(r.text.splitlines())
        except:
            continue
    return list(set([p.strip() for p in all_proxies if p.strip()]))

@app.route('/create-account', methods=['POST'])
def create_account():
    data = request.json
    platform = data.get('platform', 'tiktok')
    bot_id = data.get('id', random.randint(100, 999))
    
    proxy_pool = fetch_fresh_proxies()
    random.shuffle(proxy_pool)
    
    target_url = "https://www.tiktok.com/signup/phone-or-email/email" if platform == 'tiktok' else "https://www.instagram.com/accounts/emailsignup/"
    
    tried_proxies = []
    
    # On va tenter jusqu'à 8 proxies avant d'abandonner
    for i in range(min(len(proxy_pool), 8)):
        current_proxy = proxy_pool[i]
        start_time = time.time()
        
        log_entry = {
            "proxy": current_proxy,
            "attempt": i + 1,
            "status": "Testing",
            "latency": 0
        }
        print(f"[*] Test du proxy {current_proxy}...")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', f'--proxy-server=http://{current_proxy}']
                )
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                page = context.new_page()
                
                # On tente de charger la page avec un timeout court pour ne pas perdre de temps
                try:
                    response = page.goto(target_url, timeout=20000, wait_until="commit")
                    latency = round(time.time() - start_time, 2)
                    
                    if response and response.status < 400:
                        # Succès de chargement !
                        print(f"[+] Succès avec {current_proxy} ({latency}s)")
                        
                        # Ici on pourrait continuer le remplissage...
                        session_path = os.path.join(SESSION_DIR, f"{platform}_{bot_id}.json")
                        context.storage_state(path=session_path)
                        
                        browser.close()
                        return jsonify({
                            "success": True, 
                            "proxy": current_proxy, 
                            "latency": latency,
                            "http_status": response.status,
                            "session": session_path
                        })
                    else:
                        status_code = response.status if response else "Banni/Bloqué"
                        print(f"[-] Proxy {current_proxy} rejeté par la cible (Code: {status_code})")
                        tried_proxies.append({"ip": current_proxy, "error": f"HTTP {status_code}", "lat": latency})
                
                except Exception as e:
                    latency = round(time.time() - start_time, 2)
                    print(f"[!] Erreur Timeout/Connexion sur {current_proxy}")
                    tried_proxies.append({"ip": current_proxy, "error": "Timeout/Refused", "lat": latency})
                
                browser.close()
                
        except Exception as e:
            continue

    return jsonify({
        "success": False, 
        "error": "Aucun proxy fonctionnel trouvé dans la pile de test.",
        "details": tried_proxies
    }), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "online", "engine": "playwright-stealth-v2"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
