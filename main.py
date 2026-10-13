import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import tasks

# --- SERVIDOR WEB FALSO PARA O RENDER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Blox Fruits Online!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Inicia o servidor web em segundo plano para o Render não dar timeout
threading.Thread(target=run_web_server, daemon=True).start()
# ---------------------------------------

intents = discord.Intents.default()
client = discord.Client(intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1559298800676245658

contas_enviadas = set()

FRUTAS_DESEJADAS = [
    "flame", "falcon", "ice", "sand", "dark", "diamond", "light", "rubber",
    "barrier", "ghost", "magma", "quake", "buddha", "love", "spider",
    "sound", "phoenix", "portal", "rumble", "pain", "blizzard", "gravity",
    "mammoth", "t-rex", "dough", "shadow", "venom", "control", "spirit",
    "dragon", "leopard", "kitsune", "gas", "magnet"
]

def verificar_frutas_perm(texto):
    texto_lower = texto.lower()
    if "perm" in texto_lower or "permanente" in texto_lower:
        for fruta in FRUTAS_DESEJADAS:
            if fruta in texto_lower:
                return True
    return False

@tasks.loop(seconds=20)
async def monitorar_loja():
    url = "https://legasforn.com.br"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, "html.parser")
        produtos = soup.find_all(["div", "a", "article"], class_=lambda c: c and ("product" in c.lower() or "card" in c.lower() or "item" in c.lower()))

        canal = client.get_channel(CHANNEL_ID)
        if not canal:
            print(f"Aviso: Canal com ID {CHANNEL_ID} não encontrado.")
            return

        for prod in produtos:
            texto_completo = prod.get_text(separator=" ", strip=True)
            texto_lower = texto_completo.lower()

            if "blox" not in texto_lower and "fruit" not in texto_lower:
                continue

            if not verificar_frutas_perm(texto_completo):
                continue

            link_tag = prod if prod.name == "a" else prod.find("a")
            if not link_tag or not link_tag.get("href"):
                continue

            link_compra = link_tag.get("href")
            if not link_compra.startswith("http"):
                link_compra = f"https://legasforn.com.br{link_compra if link_compra.startswith('/') else '/' + link_compra}"

            prod_id = f"{texto_completo[:30]}_{link_compra}"
            if prod_id in contas_enviadas:
                continue

            titulo_elem = prod.find(["h1", "h2", "h3", "h4", "span", "strong"])
            nickname = titulo_elem.get_text(strip=True) if titulo_elem else "Conta Blox Fruits"

            gamepasses_texto = texto_completo.replace(nickname, "").strip()
            if len(gamepasses_texto) > 300:
                gamepasses_texto = gamepasses_texto[:300] + "..."
            if not gamepasses_texto:
                gamepasses_texto = "Consulte as Gamepasses diretamente no site."

            preco = "Ver no site"
            if "r$" in texto_lower:
                partes = texto_completo.split("R$")
                if len(partes) > 1:
                    preco = "R$" + partes[1].split()[0]

            embed = discord.Embed(
                title="🚨 NOVA CONTA DISPONÍVEL / RESTOCK!",
                color=0x2ecc71
            )
            embed.add_field(name="👤 Nick / Título", value=f"**{nickname}**", inline=False)
            embed.add_field(name="🎮 Gamepasses / Descrição", value=gamepasses_texto, inline=False)
            embed.add_field(name="💰 Valor", value=preco, inline=True)
            embed.add_field(name="🔗 Link Direto para Compra", value=f"[👉 CLIQUE AQUI PARA COMPRAR]({link_compra})", inline=False)
            embed.set_footer(text="Legas Forn Monitor • Ciclo de 20s")

            await canal.send(embed=embed)
            contas_enviadas.add(prod_id)

    except Exception as e:
        print(f"Erro no monitoramento: {e}")

@client.event
async def on_ready():
    print(f"🤖 Bot conectado com sucesso como {client.user}")
    if not monitorar_loja.is_running():
        monitorar_loja.start()

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
    else:
        print("Erro: A variável de ambiente DISCORD_TOKEN não está definida!")
