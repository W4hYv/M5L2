from config import *
from logic import *
import discord
from discord.ext import commands
from config import TOKEN
import matplotlib.colors as mcolors

manager = DB_Map("database.db")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot started")

@bot.command()
async def start(ctx: commands.Context):
    await ctx.send(f"Halo, {ctx.author.name}. Masukkan !help_me untuk mengeksplorasi daftar perintah yang tersedia")

@bot.command()
async def help_me(ctx: commands.Context):
    await ctx.send(
        "`!start` - mulai menggunakan bot dan menerima pesan sambutan.\n"
        "`!help_me` - dapatkan daftar perintah yang tersedia.\n"
        "`!show_city <city_name> [color]` - tampilkan kota di peta (warna opsional, misal: `!show_city Jakarta blue`).\n"
        "`!remember_city <city_name>` - simpan kota ke daftar favorit.\n"
        "`!show_my_cities [color]` - tampilkan semua kota yang tersimpan (warna opsional, misal: `!show_my_cities green`)."
    )

@bot.command()
async def show_city(ctx: commands.Context, *, args=""):
    if not args:
        await ctx.send("Silakan masukkan nama kota dengan benar. Contoh: `!show_city Jakarta blue`")
        return

    parts = args.split()
    marker_color = "red"

    if len(parts) > 1 and mcolors.is_color_like(parts[-1].lower()):
        marker_color = parts[-1].lower()
        city_name = " ".join(parts[:-1])
    else:
        city_name = args

    if not manager.get_coordinates(city_name):
        await ctx.send(f"Kota **{city_name}** tidak ditemukan dalam database. Pastikan menggunakan bahasa Inggris.")
        return

    file_name = f'{ctx.author.id}.png'
    manager.create_graph(file_name, [city_name], marker_color=marker_color)
    await ctx.send(file=discord.File(file_name))

@bot.command()
async def show_my_cities(ctx: commands.Context, color: str = "red"):
    cities = manager.select_cities(ctx.author.id)
    if not mcolors.is_color_like(color.lower()):
        await ctx.send(f"Warna `{color}` tidak dikenali. Menggunakan warna default (`red`).")
        color = "red"

    if cities:
        file_name = f'{ctx.author.id}_cities.png'
        manager.create_graph(file_name, cities, marker_color=color.lower())
        await ctx.send(file=discord.File(file_name))
    else:
        await ctx.send('Belom ada kota yg disimpan')

@bot.command()
async def remember_city(ctx: commands.Context, *, city_name=""):
    if manager.add_city(ctx.author.id, city_name):
        await ctx.send(f'Kota {city_name} telah berhasil disimpan!')
    else:
        await ctx.send("Format tidak benar. Silakan masukkan nama kota dalam bahasa Inggris, dengan spasi setelah perintah.")

if __name__ == "__main__":
    bot.run(TOKEN)
