# app.py
import os

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from analyzer import kodu_tara, fonksiyon_durumlarini_hesapla

app = Flask(__name__)
CORS(app) # Ön yüzün (HTML) sunucuyla sorunsuz konuşmasını sağlar

@app.route('/', methods=['GET'])
def home_page():
    return render_template("index.html")

@app.route('/health', methods=['GET'])
def health_endpoint():
    return jsonify({
        "status": "ok",
        "message": "Backend çalışıyor. Kod analizi için /api/scan endpoint'ine POST isteği atın."
    })

@app.route('/api/scan', methods=['GET', 'POST'])
def scan_endpoint():
    if request.method == 'GET':
        return jsonify({
            "status": "ready",
            "message": "Bu endpoint POST bekler. Örnek gövde: {\"code\": \"int main(){return 0;}\"}"
        })

    veri = request.get_json()
    
    if not veri or 'code' not in veri:
        return jsonify({"error": "Lütfen analiz edilecek kodu gönderin."}), 400
        
    c_kodu = veri['code']
    zafiyetler = kodu_tara(c_kodu)
    fonksiyon_durumlari = fonksiyon_durumlarini_hesapla(c_kodu, zafiyetler)
    
    return jsonify({
        "status": "success",
        "toplam_zafiyet": len(zafiyetler),
        "zafiyetler": zafiyetler,
        "fonksiyon_durumlari": fonksiyon_durumlari
    })

if __name__ == '__main__':
    print("Siber Tarayici Backend Basladi: http://localhost:5000")
    # Hata ayıklama modu yalnızca FLASK_DEBUG=1 verildiğinde açılır
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)
