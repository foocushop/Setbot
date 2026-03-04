import os
import time
import random
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app)

# Dossier pour les sessions (persistance limitée sur Railway)
SESSION_DIR = "/tmp/sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def get_public_proxies():
    try:
        # API gratuite pour récupérer des proxies
        response = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all")
        if response.status_code == 200:
            return [p for p in response.text.split('\r\n') if p]
    except:
        return []

@app.route('/create-account', methods=['POST'])
def create_account():
    data = request.json
    platform = data.get('platform', 'tiktok')
    bot_id = data.get('id', random.randint(100, 999))
    proxy_list = get_public_proxies()
    random.shuffle(proxy_list)
    
    target_url = "https://www.tiktok.com/signup/phone-or-email/email" if platform == 'tiktok' else "https://www.instagram.com/accounts/emailsignup/"

    # On tente les 5 premiers proxies
    for i in range(min(len(proxy_list), 5)):
        current_proxy = proxy_list[i]
        try:
            with sync_playwright() as p:
                # IMPORTANT: Pas de fenêtre sur Railway (headless=True)
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', f'--proxy-server=http://{current_proxy}']
                )
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                page = context.new_page()
                page.set_default_timeout(45000)

                page.goto(target_url)
                time.sleep(5)

                # Simulation de remplissage de base
                email_field = "input[name='email']" if platform == 'tiktok' else "input[name='emailOrPhone']"
                if page.query_selector(email_field):
                    page.fill(email_field, f"bot{random.randint(1000,9999)}@outlook.com")
                    
                session_path = os.path.join(SESSION_DIR, f"{platform}_{bot_id}.json")
                context.storage_state(path=session_path)
                browser.close()
                return jsonify({"success": True, "proxy": current_proxy, "session": session_path})
        except Exception as e:
            print(f"Proxy {current_proxy} échoué: {e}")
            continue

    return jsonify({"success": False, "error": "Échec total des proxies publics"}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "running", "platform": "Railway"})

if __name__ == '__main__':
    # Railway définit automatiquement la variable PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

