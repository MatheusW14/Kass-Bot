import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import re
import difflib
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Puxa os dados básicos
TOKEN_SECRETO = os.getenv("DISCORD_TOKEN")
MEU_ID = int(os.getenv("MEU_ID"))
ID_MESTRE = int(os.getenv("ID_DO_MESTRE"))

# --- TRATANDO MÚLTIPLOS SERVIDORES ---
servidores_str = os.getenv("IDS_SERVIDORES")

# Separa a string pelas vírgulas e converte cada número num discord.Object
MEUS_SERVIDORES = [
    discord.Object(id=int(id_serv.strip())) for id_serv in servidores_str.split(",")
]

# --- TRATANDO O ACESSO DAS HABILIDADES ---
USUARIOS_PERMITIDOS = [MEU_ID, ID_MESTRE]

# Carrega os bancos de dados
with open("habilidades.json", "r", encoding="utf-8") as f:
    bd_habilidades = json.load(f)

with open("fichas.json", "r", encoding="utf-8") as f:
    fichas_jogadores = json.load(f)

# Mapeamento de Imagens por Categoria
icones_categorias = {
    "Pika Pika": "https://cdn.discordapp.com/attachments/1489040723457212436/1505637592555589722/pika_pika_no_mi_by_aminekakaroto_dcgu19s-fullview.png?ex=6a0b59c7&is=6a0a0847&hm=8f94d35f276d212a8d582f3cd8b89f204e6e4d03c3c094a4887e70dea2a31bff&",
    "Moku Moku": "https://cdn.discordapp.com/attachments/1489040723457212436/1505640270857768980/content.png?ex=6a0b5c46&is=6a0a0ac6&hm=a18af9b3ec71a4ff1918b861367dfebda2e823209f493970cfbc5c53d59a9d88&",
    "Kiku Kiku": "https://cdn.discordapp.com/attachments/1489040723457212436/1505638175459119175/content.png?ex=6a0b5a52&is=6a0a08d2&hm=ec5fa14c95d60cb16b4b0f431b23db09a123e389f92695ada924a3b984b2b8e4&",
    "Guarda-chuva": "https://cdn.discordapp.com/attachments/1489040723457212436/1495926294641115186/WhatsApp_Image_2026-04-20_at_20.16.25.jpeg?ex=6a0af52d&is=6a09a3ad&hm=11354a41750fd46c66751a5a2229e90ca4d394c02901a7db30781ad0f0ef5eb1&",
    "Combos": "https://cdn.discordapp.com/attachments/1489040723457212436/1505638830009745479/content.png?ex=6a0b5aee&is=6a0a096e&hm=b2128e1b58e2fa81838ad2c839dd25517496b4c29e77a8950c9fcbd709838fea&",
    # === NOVAS CATEGORIAS DA SUA CLASSE ===
    "Arqueólogo": "",
    "Espionagem": "",
    "Rokushiki": "",
    "Combate": "",
}


class OnePieceBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        # O laço percorre a lista e sincroniza os comandos em um servidor de cada vez
        for servidor in MEUS_SERVIDORES:
            self.tree.copy_global_to(guild=servidor)
            await self.tree.sync(guild=servidor)

        print(f"Logado como {self.user} e comandos sincronizados nos servidores!")


bot = OnePieceBot()


def rolar_dano(dano_str):
    if not dano_str or dano_str == "—" or "Base" in dano_str:
        return dano_str

    match = re.match(r"(\d+)d(\d+)", dano_str)
    if match:
        quantidade = int(match.group(1))
        faces = int(match.group(2))
        resultado = sum(random.randint(1, faces) for _ in range(quantidade))
        return f"**{resultado}** (Rolado: {dano_str})"

    return dano_str


# Comando com o nome atualizado para /tecnica
@bot.tree.command(name="tecnica", description="Usa uma técnica do seu arsenal")
@app_commands.describe(nome="Nome da técnica (ex: Sniper Fotonico)")
async def usar_tecnica(interaction: discord.Interaction, nome: str):

    # --- TRAVA DE SEGURANÇA ---
    if interaction.user.id not in USUARIOS_PERMITIDOS:
        await interaction.response.send_message(
            "❌ Acesso Negado! Apenas o Matheus e o Mestre podem usar este grimório.",
            ephemeral=True,
        )
        return
    # --------------------------

    nome_buscado = nome.strip().lower()

    # 1. Tenta achar a técnica escrita exatamente igual
    tecnica = bd_habilidades.get(nome_buscado)

    # 2. Corretor Inteligente: Se não achou exato, procura o mais parecido!
    if not tecnica:
        # Busca semelhanças com 60% ou mais de precisão
        sugestoes = difflib.get_close_matches(
            nome_buscado, bd_habilidades.keys(), n=1, cutoff=0.6
        )

        if sugestoes:
            chave_corrigida = sugestoes[0]
            tecnica = bd_habilidades[chave_corrigida]
        else:
            # Se errar muito feio (ex: "abacate"), aí ele avisa que não achou
            await interaction.response.send_message(
                f"❌ A técnica **{nome}** não foi encontrada nem pelo corretor. Verifique o nome!",
                ephemeral=True,
            )
            return

    # Processa o dano dinamicamente
    resultado_dano = rolar_dano(tecnica["dano"])

    texto_dano_final = f"➔ {resultado_dano}"
    if tecnica["tipo_dano"] != "—":
        texto_dano_final += f" ({tecnica['tipo_dano']})"

    descricao_formatada = (
        f"*{tecnica['descricao']}*\n\n"
        f"**⏱️ Duração:** {tecnica['duracao']}  |  **🎯 Alcance:** {tecnica['alcance']}\n"
        f"**💥 Dano:** {texto_dano_final}  |  **🔗 Combo:** {tecnica['atq_combinado']}"
    )

    embed = discord.Embed(
        title=f"{tecnica['icone']} {tecnica['nome_exibicao']} ({tecnica['grau']})",
        description=descricao_formatada,
        color=tecnica["cor"],
    )

    embed.add_field(name="⚠️ Efeitos", value=f"> {tecnica['efeitos']}", inline=False)

    url_imagem = icones_categorias.get(tecnica["categoria"])

    if url_imagem:
        embed.set_thumbnail(url=url_imagem)

    embed.set_footer(text=f"Categoria: {tecnica['categoria']}")

    await interaction.response.send_message(embed=embed)


# Comando de inventário mantido
@bot.tree.command(
    name="habilidades",
    description="Lista todas as técnicas do seu arsenal separadas por categoria",
)
async def minhas_habilidades(interaction: discord.Interaction):

    # --- TRAVA DE SEGURANÇA ---
    if interaction.user.id not in USUARIOS_PERMITIDOS:
        await interaction.response.send_message(
            "❌ Acesso Negado! Você não tem permissão para vasculhar o inventário do Matheus.",
            ephemeral=True,
        )
        return
    # --------------------------

    arsenal_agrupado = {}

    for _, tecnica in bd_habilidades.items():
        categoria = tecnica["categoria"]

        if categoria not in arsenal_agrupado:
            arsenal_agrupado[categoria] = []

        linha = f"{tecnica['icone']} **{tecnica['nome_exibicao']}** ({tecnica['grau']})"
        arsenal_agrupado[categoria].append(linha)

    embed = discord.Embed(
        title="🎒 Arsenal de Técnicas",
        description="Aqui estão todas as habilidades disponíveis no seu grimório para consulta rápida:",
        color=discord.Color.blurple(),
    )

    for categoria, lista_habilidades in arsenal_agrupado.items():
        texto_bloco = "\n".join(lista_habilidades)
        embed.add_field(name=f"__**{categoria}**__", value=texto_bloco, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="teste",
    description="Rola um d20 e soma o modificador da sua ficha automaticamente",
)
@app_commands.choices(
    personagem=[
        app_commands.Choice(name="Kass", value="Kass"),
        app_commands.Choice(name="Cunhã", value="Cunhã"),
        app_commands.Choice(name="Mihn", value="Mihn"),
        app_commands.Choice(name="Chinchar", value="Chinchar"),
        app_commands.Choice(name="Ubiratã (Exclusivo Mestre)", value="Ubiratã"),
        app_commands.Choice(name="Mestre (NPCs)", value="Mestre"),
    ]
)
@app_commands.choices(
    pericia=[
        # Atributos Puros
        app_commands.Choice(name="💪 Força", value="Força"),
        app_commands.Choice(name="🏃 Destreza", value="Destreza"),
        app_commands.Choice(name="🛡️ Constituição", value="Constituição"),
        app_commands.Choice(name="🦉 Sabedoria", value="Sabedoria"),
        app_commands.Choice(name="✨ Presença", value="Presença"),
        app_commands.Choice(name="🔥 Vontade", value="Vontade"),
        # Perícias
        app_commands.Choice(name="🤸 Acrobacia", value="Acrobacia"),
        app_commands.Choice(name="🏋️ Atletismo", value="Atletismo"),
        app_commands.Choice(name="🎭 Atuação", value="Atuação"),
        app_commands.Choice(name="🤥 Enganação", value="Enganação"),
        app_commands.Choice(name="🥷 Furtividade", value="Furtividade"),
        app_commands.Choice(name="👑 Haki", value="Haki"),
        app_commands.Choice(name="📚 História", value="História"),
        app_commands.Choice(name="💢 Intimidação", value="Intimidação"),
        app_commands.Choice(name="💡 Intuição", value="Intuição"),
        app_commands.Choice(name="🔍 Investigação", value="Investigação"),
        app_commands.Choice(name="⚕️ Medicina", value="Medicina"),
        app_commands.Choice(name="🌿 Natureza", value="Natureza"),
        app_commands.Choice(name="👁️ Percepção", value="Percepção"),
        app_commands.Choice(name="🤝 Persuasão", value="Persuasão"),
        app_commands.Choice(name="🪄 Prestidigitação", value="Prestidigitação"),
        app_commands.Choice(name="🤬 Provocação", value="Provocação"),
        app_commands.Choice(name="👻 Sobrenatural", value="Sobrenatural"),
        app_commands.Choice(name="🏕️ Sobrevivência", value="Sobrevivência"),
        app_commands.Choice(name="🍀 Sorte", value="Sorte"),
    ]
)
async def rolar_teste(
    interaction: discord.Interaction,
    personagem: app_commands.Choice[str],
    pericia: app_commands.Choice[str],
):

    nome_person = personagem.value
    nome_pericia = pericia.value

    # --- TRAVA DE SEGURANÇA EXCLUSIVA PARA O UBIRATÃ ---
    if nome_person == "Ubiratã" and interaction.user.id != ID_MESTRE:
        await interaction.response.send_message(
            "❌ Acesso Negado! Apenas o Mestre tem autoridade para rolar testes para o **Ubiratã**.",
            ephemeral=True,
        )
        return
    # --------------------------------------------------

    if nome_person == "Mestre":
        modificador = 0
    else:
        modificador = fichas_jogadores.get(nome_person, {}).get(nome_pericia, 0)

    dado = random.randint(1, 20)
    total = dado + modificador

    texto_extra = ""
    if dado == 20:
        texto_extra = " 🌟 **SUCESSO CRÍTICO!**"
    elif dado == 1:
        texto_extra = " 💀 **FALHA CRÍTICA!**"

    embed = discord.Embed(
        title=f"🎲 Teste de {nome_pericia}",
        description=f"**{interaction.user.display_name}** rolou para **{nome_person}**!{texto_extra}",
        color=discord.Color.green() if dado >= 10 else discord.Color.red(),
    )

    embed.add_field(name="Resultado Final", value=f"## {total}", inline=False)
    embed.add_field(
        name="Detalhes",
        value=f"Dado: **{dado}**\nModificador: **{modificador:+d}**",
        inline=False,
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="iniciativa",
    description="Rola a iniciativa de todos os personagens e organiza a ordem de combate",
)
async def rolar_iniciativa(interaction: discord.Interaction):
    resultados = []

    # O bot percorre automaticamente todos os personagens cadastrados no seu JSON
    for personagem, atributos in fichas_jogadores.items():
        # Puxa a Destreza de cada um (se por acaso a ficha não tiver, assume 0)
        modificador = atributos.get("Destreza", 0)

        dado = random.randint(1, 20)
        total = dado + modificador

        # Guarda os dados numa lista para podermos ordenar depois
        resultados.append(
            {
                "personagem": personagem,
                "total": total,
                "dado": dado,
                "modificador": modificador,
            }
        )

    # A mágica do Python: ordena a lista baseada na chave 'total' de forma decrescente (reverse=True)
    resultados_ordenados = sorted(resultados, key=lambda x: x["total"], reverse=True)

    # Monta o card visual da Iniciativa
    embed = discord.Embed(
        title="⚔️ Ordem de Iniciativa",
        description="Os dados foram lançados! Preparem-se para o combate:",
        color=discord.Color.brand_red(),
    )

    # Formata cada linha do ranking
    linhas_texto = []
    for posicao, res in enumerate(resultados_ordenados, start=1):
        # Destaca quem tirou 20 natural na iniciativa
        icone = "🔥" if res["dado"] == 20 else "🔸"
        linha = f"**{posicao}º** {icone} **{res['personagem']}** ➔ **{res['total']}** *(d20: {res['dado']} | Mod: {res['modificador']:+d})*"
        linhas_texto.append(linha)

    # Junta todas as linhas com uma quebra de linha (\n)
    embed.add_field(name="Turnos", value="\n".join(linhas_texto), inline=False)

    # Menciona quem chamou o comando
    embed.set_footer(text=f"Iniciativa rolada por {interaction.user.display_name}")

    await interaction.response.send_message(embed=embed)


# === INSIRA SEU TOKEN AQUI ===
if __name__ == "__main__":
    bot.run(TOKEN_SECRETO)
