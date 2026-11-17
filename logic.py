import sqlite3
import matplotlib

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
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0

    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))
            cities = [row[0] for row in cursor.fetchall()]
            return cities

    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates

    def create_graph(self, path, cities, marker_color='red'):
        fig = plt.figure(figsize=(10, 5))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

        ax.add_feature(cfeature.LAND, facecolor='#d9f0a3')
        ax.add_feature(cfeature.OCEAN, facecolor='#a6cee3')

        ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.6)
        ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='gray')
        ax.add_feature(cfeature.LAKES, facecolor='#a6cee3', edgecolor='blue', linewidth=0.3)
        ax.add_feature(cfeature.RIVERS, edgecolor='#1f78b4', linewidth=0.4)

        for city in cities:
            coordinates = self.get_coordinates(city)
            if coordinates:
                lat, long = coordinates
                ax.plot([long], [lat], color=marker_color, linewidth=1, marker="o", markersize=6, transform=ccrs.Geodetic())
                ax.text(long + 3, lat + 5, city, horizontalalignment='left', fontsize=9, transform=ccrs.Geodetic())
        
        plt.savefig(path, bbox_inches='tight')
        plt.close()
        
    def draw_distance(self, city1, city2):
        pass


if __name__ == "__main__":
    m = DB_Map("database.db")
    m.create_user_table()
