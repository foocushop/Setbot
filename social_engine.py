import os
import time
import random
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)

# Ta liste de proxies
MY_PROXIES = [
    "46.249.103.192:443", "121.128.121.54:3128", "61.72.221.94:3128", "61.72.221.194:3128",
    "14.56.177.44:3128", "61.72.110.94:3128", "173.249.5.133:1080", "185.100.232.163:11035",
    "91.232.105.90:13545", "185.100.232.132:12443", "213.165.58.7:1080", "175.110.113.245:16801",
    "190.2.150.45:11486", "212.34.135.86:5000", "109.236.88.88:12279", "91.229.23.128:11420",
    "62.112.10.189:12460", "93.183.124.28:1080", "93.190.141.108:11997", "62.112.11.191:12611",
    "109.236.84.70:12100", "109.236.94.58:11033", "93.190.138.89:12254", "134.119.214.69:12182",
    "93.190.140.175:11481", "91.229.23.128:11495", "89.38.97.60:11385", "185.100.232.132:11547",
    "62.112.11.77:11458", "89.38.98.64:12095", "159.223.53.194:1080", "91.232.105.4:12056",
    "93.190.139.245:12059", "212.8.249.177:11220", "93.190.139.73:11747", "62.112.11.191:12136",
    "93.190.137.73:11375", "109.236.84.37:11481", "194.233.68.54:1088", "89.38.99.47:11318"
]

def check_one_proxy(proxy):
    """Vérifie un proxy unique et renvoie son statut"""
    start = time.time()
    try:
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        # On interroge un service ultra-léger pour tester la vie
        r = requests.get("http://azenv.net/", proxies=proxies, timeout=3)
        lat = round(time.time() - start, 2)
        if r.status_code == 200:
            return {"ip": proxy, "status": "ALIVE", "lat": lat, "code": 200}
        return {"ip": proxy, "status": "DEATH", "lat": lat, "code": r.status_code}
    except:
        return {"ip": proxy, "status": "DEATH", "lat": 3.0, "code": "Timeout"}

@app.route('/create-account', methods=['POST'])
def bulk_check():
    # On prend 20 proxies au hasard dans ta liste
    test_sample = random.sample(MY_PROXIES, min(len(MY_PROXIES), 20))
    
    # On utilise le multi-threading pour tester tout le monde en même temps (très rapide)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_one_proxy, test_sample))
    
    # On sépare les vivants des morts pour le retour
    alive_count = len([r for r in results if r['status'] == 'ALIVE'])
    
    return jsonify({
        "success": alive_count > 0,
        "details": results,
        "summary": f"{alive_count} proxies vivants sur {len(results)} testés"
    })

@app.route('/status')
def status():
    return jsonify({"status": "online", "mode": "fast_checker"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
