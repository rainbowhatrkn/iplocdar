from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()
app = Flask(__name__)

# Connexion à la base de données SQLite
def init_db():
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tracking 
                 (id INTEGER PRIMARY KEY, ip TEXT, location TEXT, city TEXT, region TEXT, country TEXT)''')
    conn.commit()
    conn.close()

# Enregistrement de l'IP, la localisation et les détails
def save_tracking(ip, location, city, region, country):
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute("INSERT INTO tracking (ip, location, city, region, country) VALUES (?, ?, ?, ?, ?)", 
              (ip, location, city, region, country))
    conn.commit()
    conn.close()

# Récupérer toutes les entrées enregistrées
def get_all_trackings():
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute("SELECT id, ip, location, city, region, country FROM tracking")
    trackings = c.fetchall()
    conn.close()
    return trackings

# Récupérer les détails d'une IP spécifique
def get_tracking_by_ip(ip):
    conn = sqlite3.connect('tracker.db')
    c = conn.cursor()
    c.execute("SELECT ip, location, city, region, country FROM tracking WHERE ip = ?", (ip,))
    tracking = c.fetchone()
    conn.close()
    return tracking

# Utiliser ipstack pour obtenir des informations complètes de géolocalisation
def get_location(ip):
    api_key = os.getenv('API_KEY')  # Récupère la clé API depuis l'environnement
    url = f"http://api.ipstack.com/{ip}?access_key={api_key}"
    response = requests.get(url)
    data = response.json()

    if 'error' not in data:
        location = (data['latitude'], data['longitude'])
        city = data['city']
        region = data['region_name']
        country = data['country_name']
        return location, city, region, country
    else:
        return None, None, None, None
        
@app.route('/', methods=['GET', 'POST'])
def index():
    lat, lon = None, None
    city, region, country = None, None, None
    if request.method == 'POST':
        ip = request.form['ip']
        location, city, region, country = get_location(ip)

        if location:
            lat, lon = location
            save_tracking(ip, str(location), city, region, country)

    return render_template('index.html', lat=lat, lon=lon, city=city, region=region, country=country)

# Nouvelle route pour afficher les IPs suivies
@app.route('/trackings', methods=['GET'])
def trackings():
    trackings = get_all_trackings()
    return render_template('trackings.html', trackings=trackings)

# Route pour afficher les détails d'une IP et sa localisation sur une carte
@app.route('/tracking/<ip>', methods=['GET'])
def show_tracking(ip):
    tracking = get_tracking_by_ip(ip)
    if tracking:
        location = tracking[1].strip('()').split(', ')
        lat, lon = float(location[0]), float(location[1])
        city, region, country = tracking[2], tracking[3], tracking[4]
        return render_template('tracking_detail.html', ip=ip, lat=lat, lon=lon, city=city, region=region, country=country)
    else:
        return "IP non trouvée", 404

@app.route('/api/location/<ip>', methods=['GET'])
def get_ip_location(ip):
    tracking = get_tracking_by_ip(ip)
    if tracking:
        location = tracking[1].strip('()').split(', ')
        lat, lon = float(location[0]), float(location[1])
        return {
            'latitude': lat,
            'longitude': lon,
            'city': tracking[2],
            'region': tracking[3],
            'country': tracking[4]
        }
    else:
        return {"error": "IP non trouvée"}, 404

if __name__ == '__main__':
    init_db()  # Initialise la base de données
    app.run(debug=False, host='0.0.0.0', port=80)