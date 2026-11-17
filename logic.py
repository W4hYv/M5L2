import sqlite3
import matplotlib
import requests

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


class DB_Map():
    def __init__(self, database):
        self.database = database

    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()

    def add_city(self, user_id, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city = ? COLLATE NOCASE", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            return 0

    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))
            return [row[0] for row in cursor.fetchall()]

    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ? COLLATE NOCASE''', (city_name,))
            return cursor.fetchone()

    def get_cities_by_country(self, country_name, limit=15):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT city FROM cities 
                              WHERE country = ? COLLATE NOCASE 
                              ORDER BY population DESC LIMIT ?''', (country_name, limit))
            return [row[0] for row in cursor.fetchall()]

    def get_cities_by_population(self, min_pop, limit=15):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT city FROM cities 
                              WHERE population >= ? 
                              ORDER BY population DESC LIMIT ?''', (min_pop, limit))
            return [row[0] for row in cursor.fetchall()]

    def get_cities_by_country_and_pop(self, country_name, min_pop, limit=15):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT city FROM cities 
                              WHERE country = ? COLLATE NOCASE AND population >= ? 
                              ORDER BY population DESC LIMIT ?''', (country_name, min_pop, limit))
            return [row[0] for row in cursor.fetchall()]

    def get_city_weather_and_time(self, city_name):
        coords = self.get_coordinates(city_name)
        if not coords:
            return None

        lat, lon = coords
        url = (
            f"https://open-meteo.com?"
            f"latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
        )
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            current = data.get("current_weather", {})
            timezone = data.get("timezone", "UTC")
            local_time = current.get("time", "").replace("T", " ")
            temp = current.get("temperature", "N/A")
            wind = current.get("windspeed", "N/A")
            weather_code = current.get("weathercode", 0)

            weather_desc = self._decode_weather(weather_code)
            return {
                "city": city_name.title(),
                "temp": temp,
                "wind": wind,
                "desc": weather_desc,
                "time": local_time,
                "timezone": timezone
            }
        except Exception:
            return None

    def _decode_weather(self, code):
        weather_map = {
            0: "Cerah ☀️",
            1: "Cerah Berawan 🌤️",
            2: "Berawan Sebagian ⛅",
            3: "Mendung ☁️",
            45: "Berkabut 🌫️",
            48: "Kabut Tebal 🌫️",
            51: "Gerimis Ringan 🌦️",
            53: "Gerimis Sedang 🌦️",
            55: "Gerimis Lebat 🌧️",
            61: "Hujan Ringan 🌧️",
            63: "Hujan Sedang 🌧️",
            65: "Hujan Lebat ⛈️",
            71: "Salju Ringan ❄️",
            73: "Salju Sedang ❄️",
            75: "Salju Lebat ❄️",
            80: "Hujan Lokal 🌦️",
            95: "Badai Petir ⚡"
        }
        return weather_map.get(code, "Kondisi Normal 🌍")

    def create_graph(self, path, cities, marker_color='red'):
        fig = plt.figure(figsize=(11, 5.5))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

        ax.add_feature(cfeature.LAND, facecolor='#d9f0a3')
        ax.add_feature(cfeature.OCEAN, facecolor='#a6cee3')

        # Menambahkan objek geografis
        ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='gray')
        ax.add_feature(cfeature.LAKES, facecolor='#a6cee3', edgecolor='blue', linewidth=0.3)
        ax.add_feature(cfeature.RIVERS, edgecolor='#1f78b4', linewidth=0.4)

        for city in cities:
            coordinates = self.get_coordinates(city)
            if coordinates:
                lat, long = coordinates
                ax.plot(
                    [long], [lat],
                    color=marker_color,
                    linewidth=1,
                    marker="o",
                    markersize=6,
                    transform=ccrs.Geodetic()
                )
                ax.text(
                    long + 2.5, lat + 2.5,
                    city,
                    horizontalalignment='left',
                    fontsize=8.5,
                    fontweight='bold',
                    transform=ccrs.Geodetic()
                )

        plt.savefig(path, bbox_inches='tight', dpi=150)
        plt.close()

    def draw_distance(self, path, city1, city2, line_color='blue'):
        coords1 = self.get_coordinates(city1)
        coords2 = self.get_coordinates(city2)
        if not coords1 or not coords2:
            return False

        fig = plt.figure(figsize=(11, 5.5))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, facecolor='#d9f0a3')
        ax.add_feature(cfeature.OCEAN, facecolor='#a6cee3')
        ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='gray')

        lat1, lon1 = coords1
        lat2, lon2 = coords2

        ax.plot([lon1, lon2], [lat1, lat2], color=line_color, linewidth=2, marker='o', transform=ccrs.Geodetic())
        ax.text(lon1 + 2, lat1 + 2, city1, transform=ccrs.Geodetic())
        ax.text(lon2 + 2, lat2 + 2, city2, transform=ccrs.Geodetic())

        plt.savefig(path, bbox_inches='tight', dpi=150)
        plt.close()
        return True


if __name__ == "__main__":
    m = DB_Map("database.db")
    m.create_user_table()
