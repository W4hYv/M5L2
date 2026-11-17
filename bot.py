import os
import discord
from discord.ext import commands
import matplotlib.colors as mcolors
from config import TOKEN
from logic import DB_Map

manager = DB_Map("database.db")
manager.create_user_table()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


def parse_color_and_text(args: str, default_color: str = "red"):
    parts = args.split()
    if len(parts) > 1 and mcolors.is_color_like(parts[-1].lower()):
        return " ".join(parts[:-1]), parts[-1].lower()
    return args, default_color


@bot.event
async def on_ready():
    print(f"Bot berhasil berjalan sebagai {bot.user}")


@bot.command()
async def start(ctx: commands.Context):
    await ctx.send(
        f"Halo, **{ctx.author.name}**! 🌍\n"
        f"Ketik `!help_me` untuk melihat semua fitur peta interaktif, cuaca, dan waktu dunia."
    )


@bot.command()
async def help_me(ctx: commands.Context):
    await ctx.send(
        "**Daftar Perintah Bot Peta:**\n"
        "`!start` - Memulai bot.\n"
        "`!show_city <kota> [warna]` - Tampilkan satu kota di peta (contoh: `!show_city Jakarta blue`).\n"
        "`!remember_city <kota>` - Simpan kota ke daftar favorit.\n"
        "`!show_my_cities [warna]` - Tampilkan semua kota favoritmu di peta.\n"
        "`!country_cities <negara> [warna]` - Tampilkan kota-kota dari negara tertentu (contoh: `!country_cities Indonesia red`).\n"
        "`!pop_cities <jumlah_penduduk> [warna]` - Tampilkan kota dengan penduduk minimal X (contoh: `!pop_cities 10000000 purple`).\n"
        "`!filter_cities <negara> <jumlah_penduduk> [warna]` - Filter negara & penduduk (contoh: `!filter_cities Japan 2000000 orange`).\n"
        "`!city_info <kota>` - Cek cuaca & waktu lokal terkini di suatu kota (contoh: `!city_info Tokyo`)."
    )


@bot.command()
async def show_city(ctx: commands.Context, *, args=""):
    if not args:
        await ctx.send("Masukkan nama kota! Contoh: `!show_city Jakarta blue`")
        return

    city_name, marker_color = parse_color_and_text(args)

    if not manager.get_coordinates(city_name):
        await ctx.send(f"Kota **{city_name}** tidak ditemukan dalam database. Gunakan nama dalam bahasa Inggris.")
        return

    file_name = f"{ctx.author.id}_city.png"
    manager.create_graph(file_name, [city_name], marker_color=marker_color)
    await ctx.send(file=discord.File(file_name))
    os.remove(file_name)


@bot.command()
async def remember_city(ctx: commands.Context, *, city_name=""):
    if not city_name:
        await ctx.send("Masukkan nama kota yang ingin disimpan! Contoh: `!remember_city London`")
        return

    if manager.add_city(ctx.author.id, city_name):
        await ctx.send(f"Kota **{city_name}** berhasil disimpan ke daftar favoritmu!")
    else:
        await ctx.send("Kota tidak ditemukan. Pastikan penulisan menggunakan bahasa Inggris.")


@bot.command()
async def show_my_cities(ctx: commands.Context, color: str = "red"):
    cities = manager.select_cities(ctx.author.id)
    if not cities:
        await ctx.send("Belum ada kota yang disimpan. Gunakan `!remember_city <kota>` terlebih dahulu.")
        return

    if not mcolors.is_color_like(color.lower()):
        color = "red"

    file_name = f"{ctx.author.id}_my_cities.png"
    manager.create_graph(file_name, cities, marker_color=color.lower())
    await ctx.send(file=discord.File(file_name))
    os.remove(file_name)


@bot.command()
async def country_cities(ctx: commands.Context, *, args=""):
    if not args:
        await ctx.send("Masukkan nama negara! Contoh: `!country_cities Indonesia blue`")
        return

    country_name, marker_color = parse_color_and_text(args)
    cities = manager.get_cities_by_country(country_name)

    if not cities:
        await ctx.send(f"Tidak ditemukan kota untuk negara **{country_name}**. Gunakan bahasa Inggris (misal: `Indonesia`, `Japan`, `United States`).")
        return

    file_name = f"{ctx.author.id}_country.png"
    manager.create_graph(file_name, cities, marker_color=marker_color)
    await ctx.send(
        f"Menampilkan **{len(cities)}** kota utama di **{country_name.title()}**:",
        file=discord.File(file_name)
    )
    os.remove(file_name)


@bot.command()
async def pop_cities(ctx: commands.Context, min_pop: int = 0, color: str = "red"):
    if min_pop <= 0:
        await ctx.send("Masukkan angka minimal populasi! Contoh: `!pop_cities 10000000 green`")
        return

    if not mcolors.is_color_like(color.lower()):
        color = "red"

    cities = manager.get_cities_by_population(min_pop)
    if not cities:
        await ctx.send(f"Tidak ada kota dengan populasi di atas **{min_pop:,}**.")
        return

    file_name = f"{ctx.author.id}_pop.png"
    manager.create_graph(file_name, cities, marker_color=color.lower())
    await ctx.send(
        f"Menampilkan **{len(cities)}** kota dengan populasi minimal **{min_pop:,}**:",
        file=discord.File(file_name)
    )
    os.remove(file_name)


@bot.command()
async def filter_cities(ctx: commands.Context, *, args=""):
    parts = args.split()
    if len(parts) < 2:
        await ctx.send("Format salah! Contoh: `!filter_cities Indonesia 1000000 yellow` atau `!filter_cities United States 2000000 red`")
        return

    marker_color = "red"
    if mcolors.is_color_like(parts[-1].lower()):
        marker_color = parts[-1].lower()
        parts = parts[:-1]

    if len(parts) < 2 or not parts[-1].isdigit():
        await ctx.send("Pastikan memasukkan angka populasi setelah nama negara! Contoh: `!filter_cities Japan 3000000 blue`")
        return

    min_pop = int(parts[-1])
    country_name = " ".join(parts[:-1])

    cities = manager.get_cities_by_country_and_pop(country_name, min_pop)
    if not cities:
        await ctx.send(f"Tidak ada kota di **{country_name}** dengan populasi minimal **{min_pop:,}**.")
        return

    file_name = f"{ctx.author.id}_filter.png"
    manager.create_graph(file_name, cities, marker_color=marker_color)
    await ctx.send(
        f"Menampilkan **{len(cities)}** kota di **{country_name.title()}** dengan populasi ≥ **{min_pop:,}**:",
        file=discord.File(file_name)
    )
    os.remove(file_name)


@bot.command()
async def city_info(ctx: commands.Context, *, city_name=""):
    if not city_name:
        await ctx.send("Masukkan nama kota! Contoh: `!city_info Jakarta`")
        return

    info = manager.get_city_weather_and_time(city_name)
    if not info:
        await ctx.send(f"Kota **{city_name}** tidak ditemukan atau gagal mengambil data cuaca.")
        return

    embed = discord.Embed(
        title=f"🌍 Informasi Kota: {info['city']}",
        color=discord.Color.blue()
    )
    embed.add_field(name="🕒 Waktu Lokal", value=f"`{info['time']}` ({info['timezone']})", inline=False)
    embed.add_field(name="🌡️ Suhu", value=f"**{info['temp']}°C**", inline=True)
    embed.add_field(name="☁️ Cuaca", value=info['desc'], inline=True)
    embed.add_field(name="💨 Kecepatan Angin", value=f"{info['wind']} km/h", inline=True)

    await ctx.send(embed=embed)


if __name__ == "__main__":
    bot.run(TOKEN)
