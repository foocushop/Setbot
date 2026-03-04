import os
import time
import random
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app)

# Sources de proxies publics "Elite" et "Anonymous"
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=anonymous",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
]

def get_live_proxy_list():
    """Récupère et nettoie les listes de proxies"""
    combined = []
    for url in PROXY_SOURCES:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                combined.extend(r.text.splitlines())
        except:
            continue
    # Nettoyage (supprime les doublons et espaces)
    return list(set([p.strip() for p in combined if ":" in p]))

def is_proxy_alive(proxy_url):
    """Vérifie si le proxy répond réellement à une requête simple"""
    try:
        proxies = {"http": f"http://{proxy_url}", "https": f"http://{proxy_url}"}
        # Test sur un endpoint léger (Cloudflare)
        r = requests.get("http://1.1.1.1", proxies=proxies, timeout=3)
        return r.status_code == 200
    except:
        return False

@app.route('/create-account', methods=['POST'])
def create_account():
    data = request.json
    platform = data.get('platform', 'tiktok')
    
    all_proxies = get_live_proxy_list()
    random.shuffle(all_proxies)
    
    tested_details = []
    
    # On teste les 10 premiers proxies de la liste mélangée
    for i in range(min(len(all_proxies), 10)):
        proxy = all_proxies[i]
        start_check = time.time()
        
        # ÉTAPE 1 : Vérification de "vie" (Alive Check)
        alive = is_proxy_alive(proxy)
        latency = round(time.time() - start_check, 2)
        
        if not alive:
            tested_details.append({"ip": proxy, "status": "Mort/Timeout", "lat": latency})
            continue
            
        # ÉTAPE 2 : Tentative de navigation si le proxy est "Alive"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', f'--proxy-server=http://{proxy}'])
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
                page = context.new_page()
                
                target = "https://www.tiktok.com/signup" if platform == 'tiktok' else "https://www.instagram.com/"
                
                resp = page.goto(target, timeout=15000)
                if resp and resp.status < 400:
                    browser.close()
                    return jsonify({
                        "success": True,
                        "proxy": proxy,
                        "latency": latency,
                        "source": "Live Scrape",
                        "details": tested_details # On renvoie aussi les échecs pour la console
                    })
                else:
                    tested_details.append({"ip": proxy, "status": f"Bloqué (HTTP {resp.status})", "lat": latency})
                browser.close()
        except Exception as e:
            tested_details.append({"ip": proxy, "status": "Erreur Navigation", "lat": latency})

    return jsonify({
        "success": False,
        "error": "Aucun proxy n'a passé le test de navigation.",
        "details": tested_details
    }), 500

@app.route('/status')
def status():
    return jsonify({"status": "online", "proxies_available": len(get_live_proxy_list())})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
