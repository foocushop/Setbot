import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

# Installation automatique des supports SOCKS pour Railway
# Note: Railway nécessite 'requests[socks]' dans requirements.txt

app = Flask(__name__)
CORS(app)

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
    "93.190.141.73:11375", "109.236.84.37:11481", "194.233.68.54:1088", "89.38.99.47:11318",
    "43.160.195.20:20005", "93.190.141.73:11884", "190.2.134.118:11949", "89.38.97.145:11118",
    "62.112.11.41:11701", "109.236.94.37:12346", "62.112.11.191:11356", "104.248.197.67:1080",
    "104.248.203.234:1080", "62.112.11.41:11874", "109.236.80.126:11132", "91.229.23.194:11803",
    "91.229.23.194:11905", "91.232.105.69:12407", "93.190.141.112:11784", "93.190.143.27:11145",
    "109.236.80.126:11176", "109.236.83.71:11353", "43.131.9.114:1777", "89.38.99.28:12251",
    "190.2.132.231:11141", "109.236.81.34:11066", "109.236.82.247:11874", "134.119.205.55:11599",
    "202.154.19.11:8082", "103.176.96.50:8082", "41.223.119.156:3128", "109.236.80.175:12396",
    "89.39.107.223:11818", "95.143.190.56:12257", "190.2.134.28:11433", "62.112.9.200:12354",
    "121.169.46.116:1090", "109.236.82.104:12294", "89.38.96.16:11028", "62.112.10.189:11391",
    "89.39.107.223:11781", "62.112.11.191:15207", "62.112.10.200:11304", "62.112.10.200:11323",
    "190.2.142.30:12180", "103.75.118.84:1080", "194.233.70.123:8080", "194.233.93.114:8080",
    "194.233.74.238:8080", "194.233.73.195:8080", "109.236.85.78:11918", "134.199.159.23:1080",
    "91.229.23.128:11228", "35.234.17.221:1080", "211.171.114.154:3128", "109.236.80.126:12149",
    "58.69.182.53:8085", "62.112.10.200:11892", "119.93.207.214:8082", "95.190.193.74:3128"
]

def check_one_proxy(proxy):
    """Vérifie un proxy avec plusieurs protocoles et un timeout plus long"""
    start = time.time()
    
    # On va tester HTTP et SOCKS5
    protocols = [
        f"http://{proxy}",
        f"socks5://{proxy}",
        f"socks4://{proxy}"
    ]
    
    for proto_url in protocols:
        try:
            proxies = {"http": proto_url, "https": proto_url}
            # Timeout augmenté à 8s (standard pro)
            # On teste Google qui est la référence absolue de connectivité
            r = requests.get("https://www.google.com", proxies=proxies, timeout=8)
            
            if r.status_code == 200:
                return {
                    "ip": proxy, 
                    "status": "ALIVE", 
                    "lat": round(time.time() - start, 2),
                    "proto": proto_url.split(":")[0]
                }
        except:
            continue
            
    return {"ip": proxy, "status": "DEATH", "lat": round(time.time() - start, 2)}

@app.route('/create-account', methods=['POST'])
def full_check():
    # Parallélisation massive (50 threads)
    with ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(check_one_proxy, MY_PROXIES))
    
    alive_count = len([r for r in results if r['status'] == 'ALIVE'])
    
    return jsonify({
        "success": True,
        "details": results,
        "summary": f"{alive_count} vivants sur {len(MY_PROXIES)} testés"
    })

@app.route('/status')
def status():
    return jsonify({"status": "online", "mode": "ultra_checker", "total_proxies": len(MY_PROXIES)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
