from flask import Flask, render_template, request
import requests
import sqlite3

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

# Utiliser ipstack pour obtenir des informations complètes de géolocalisation
def get_location(ip):
    api_key = 'e608845372e7c9381a72758eee424748'  # Remplace par ta clé API ipstack
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

if __name__ == '__main__':
    init_db()  # Initialise la base de données
    app.run(debug=False, host='0.0.0.0', port=5000)