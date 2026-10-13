import os
import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import re

# ==================== CONFIGURAÇÕES ====================
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1559298800676245658  # ID do canal do Discord
SITE_BASE_URL = "https://legasforn.com.br"

# Lista de Frutas Perm consideradas valiosas (da Flame para cima)
FRUTAS_RELEVANTES = [
    "flame", "chama", "ice", "gelo", "sand", "areia", "dark", "escuridao", 
    "light", "luz", "magma", "quake", "terremoto", "buddha", "buda", "love", 
    "amor", "spider", "aranha", "sound", "som", "phoenix", "fenix", "portal", 
    "rumble", "trovao", "pain", "dor", "blizzard", "nevasca", "gravity", "gravidade", 
    "mammoth", "mamute", "t-rex", "trex", "dough", "massa", "shadow", "sombra", 
    "venom", "veneno", "control", "controle", "spirit", "espirito", "dragon", 
    "dragao", "leopard", "leopardo", "kitsune", "yeti", "gas"
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)

vistos = set()

def extrair_frutas_perm(texto):
    texto_lower = texto.lower()
    frutas_encontradas = []
    
    for fruta in FRUTAS_RELEVANTES:
        if fruta in texto_lower:
            frutas_encontradas.append(fruta.capitalize())
            
    if not frutas_encontradas:
        return "Nenhuma fruta Perm (Flame+) informada"
    
    return ", ".join(list(dict.fromkeys(frutas_encontradas)))

@tasks.loop(seconds=20)
async def verificar_estoque_rapido():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for pagina in range(1, 6):
        url_pagina = f"{SITE_BASE_URL}/loja?page={pagina}" if pagina > 1 else f"{SITE_BASE_URL}/loja"
        
        try:
            response = requests.get(url_pagina, headers=headers, timeout=5)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            links_produtos = soup.find_all('a', href=True)

            for tag_a in links_produtos:
                href = tag_a['href']
                
                if "/produto/" in href or "/item/" in href or "/conta/" in href or "/loja/" in href:
                    link_completo = href if href.startswith("http") else f"{SITE_BASE_URL}{href}"

                    if link_completo in vistos:
                        continue

                    res_prod = requests.get(link_completo, headers=headers, timeout=5)
                    if res_prod.status_code != 200:
                        continue
                    
                    soup_prod = BeautifulSoup(res_prod.text, 'html.parser')
                    texto_pagina = soup_prod.get_text(separator=" ", strip=True)

                    tag_titulo = soup_prod.find(['h1', 'h2'])
                    titulo = tag_titulo.get_text(strip=True) if tag_titulo else "Conta Blox Fruits"

                    precos = re.findall(r'R\$\s*[\d\.,]+', texto_pagina)
                    preco = precos[0] if precos else "Consulte no site"

                    gamepasses_match = re.search(r'(gamepass|gamepasses|passes)[:\s]+([^\.\n]+)', texto_pagina, re.IGNORECASE)
                    gamepasses = gamepasses_match.group(0) if gamepasses_match else "Verifique na descrição do site"

                    frutas_perm = extrair_frutas_perm(texto_pagina)

                    embed = discord.Embed(
                        title="🚨 NOVA CONTA LANÇADA / RESTOCK!",
                        description=f"**{titulo}**",
                        color=0x00FF66
                    )
                    embed.add_field(name="💰 Valor", value=f"`{preco}`", inline=True)
                    embed.add_field(name="🎮 Gamepasses", value=gamepasses[:1024], inline=False)
                    embed.add_field(name="🍇 Frutas Perm (Flame+)", value=frutas_perm[:1024], inline=False)
                    embed.add_field(
                        name="🔗 Link Direto para Compra", 
                        value=f"👉 **[CLIQUE AQUI PARA COMPRAR ESTA CONTA]({link_completo})**", 
                        inline=False
                    )
                    embed.set_footer(text=f"Legas Forn Monitor • Ciclo de 20s")

                    await channel.send(embed=embed)
                    vistos.add(link_completo)

        except Exception as e:
            pass

@client.event
async def on_ready():
    print(f'🤖 Bot conectado como {client.user}!')
    verificar_estoque_rapido.start()

client.run(TOKEN)
