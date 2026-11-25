"""Ajustes no código da nuvem (rodar logo depois de desempacotar o pacote.b64).

24/11/2026:
  1) RITMO: o robô diário postava 1 por hora (até 71 num dia) e o alcance caiu para 1-19 views por vídeo;
     dias com 2 a 9 shorts tiveram ~1.000-1.500. Agora: no máximo 6 por dia, a cada 2 h, das 11h às 22h59 (Marco: 4 era pouco).
  2) PERSONAGEM CENTRALIZADO: com câmera no canto, o jogo de baixo era recortado só do lado sem câmera e o
     personagem (3ª pessoa, no meio da tela) saía deslocado. Agora recorta pelo centro e borra a câmera.
Se o código mudar e algum ajuste não encaixar, falha de propósito (melhor parar do que voltar a 1/h).
"""
from pathlib import Path

TROCAS = {
 "diario.py": [
  [
   "INTERVALO = 3600\n",
   "INTERVALO = 2 * 3600  # ajustes.py\n"
  ],
  [
   "FILA_MIN = 3\n",
   "FILA_MIN = 3\n\nMAX_POR_DIA = 6  # ajustes.py\n\n\ndef _pode_publicar_agora() -> bool:\n    agora = dt.datetime.now(BRT)\n    if not (11 <= agora.hour < 23):\n        return False\n    hoje = agora.strftime('%d/%m')\n    try:\n        linhas = lg.LOG.read_text(encoding='utf-8').splitlines()\n    except Exception:\n        linhas = []\n    return sum(1 for l in linhas if l.startswith(hoje) and 'PUBLICADO' in l) < MAX_POR_DIA\n"
  ],
  [
   "if not cota_esgotada() and time.time() - ultimo_post()",
   "if not cota_esgotada() and _pode_publicar_agora() and time.time() - ultimo_post()"
  ]
 ],
 "cortes/montagem.py": [
  [
   "        centro_cam = r[\"x\"] + r[\"w\"] / 2\n        if centro_cam < 0.5:\n            gx0, gx1 = min(0.55, r[\"x\"] + r[\"w\"]), 1.0\n        else:\n            gx0, gx1 = 0.0, max(0.45, r[\"x\"])\n        gancho_y = alt_cam - 50     # gancho na emenda câmera/jogo (como os canais grandes), sem cobrir o rosto\n        pos_leg = (540, alt_cam + 330)  # legenda já dentro da área do jogo\n        y_aviso = alt_cam + 220\n        filtro = (\"[SRC]split[c][j];\"\n                  f\"[c]crop=w=iw*{r['w']:.4f}:h=ih*{r['h']:.4f}:x=iw*{r['x']:.4f}:y=ih*{r['y']:.4f},\"\n                  f\"scale=1080:{alt_cam}:force_original_aspect_ratio=increase,crop=1080:{alt_cam},setsar=1[cam];\"\n                  f\"[j]crop=w=iw*{gx1 - gx0:.4f}:h=ih:x=iw*{gx0:.4f}:y=0,\"\n                  f\"scale=1080:{alt_jogo_cam}:force_original_aspect_ratio=increase,crop=1080:{alt_jogo_cam},\"\n                  f\"setsar=1[jogo];\"\n",
   "        # 24/11/2026: o jogo de baixo é recortado no CENTRO da tela, onde fica o personagem em 3ª pessoa\n        # (antes recortava só o lado sem câmera e o personagem saía deslocado). A parte da câmera que cair\n        # dentro do recorte é borrada, para não duplicar a câmera.\n        larg_esc = round(alt_jogo_cam * 16 / 9)   # largura do vídeo escalado para a altura da faixa\n        esq = (larg_esc - 1080) / 2                # onde começa o recorte central\n        bx0 = max(0, int(r[\"x\"] * larg_esc - esq))\n        bx1 = min(1080, int((r[\"x\"] + r[\"w\"]) * larg_esc - esq))\n        by0 = max(0, int(r[\"y\"] * alt_jogo_cam))\n        by1 = min(alt_jogo_cam, int((r[\"y\"] + r[\"h\"]) * alt_jogo_cam))\n        jogo = f\"[j]scale=-2:{alt_jogo_cam},crop=1080:{alt_jogo_cam}:x='(iw-1080)/2':y=0,setsar=1\"\n        if bx1 - bx0 > 8 and by1 - by0 > 8:\n            bw, bh = (bx1 - bx0) // 2 * 2, (by1 - by0) // 2 * 2\n            jogo += (f\",split[j1][j2];[j2]crop={bw}:{bh}:{bx0}:{by0},boxblur=30:3[tapa];\"\n                     f\"[j1][tapa]overlay={bx0}:{by0}[jogo];\")\n        else:\n            jogo += \"[jogo];\"\n        gancho_y = alt_cam - 50     # gancho na emenda câmera/jogo (como os canais grandes), sem cobrir o rosto\n        pos_leg = (540, alt_cam + 330)  # legenda já dentro da área do jogo\n        y_aviso = alt_cam + 220\n        filtro = (\"[SRC]split[c][j];\"\n                  f\"[c]crop=w=iw*{r['w']:.4f}:h=ih*{r['h']:.4f}:x=iw*{r['x']:.4f}:y=ih*{r['y']:.4f},\"\n                  f\"scale=1080:{alt_cam}:force_original_aspect_ratio=increase,crop=1080:{alt_cam},setsar=1[cam];\"\n                  + jogo +\n"
  ],
  # 3) MENSAGEM DO FIM: a pergunta vermelha genérica nos últimos 3,5 s ("VOCÊ JÁ COMPROU O GTA 6?") saiu
  #    do vídeo (Marco: "é ruim"). Ela continua só no comentário fixado.
  ["    if pergunta and dur > 6:", "    if False and pergunta and dur > 6:  # ajustes.py: sem pergunta no vídeo"]
 ],
 "live_gta.py": [
  # 4) SEM FRASE FORTE = SEM GRAÇA: quando não acha nenhuma frase boa o gancho vira um texto genérico
  #    ("ALANZOKA EXPLORANDO O GTA 6"); esses cortes eram os mais fracos, agora são descartados.
  ["        gancho = gancho_gta(segs, j_ini, j_fim, pico)\n",
   "        gancho = gancho_gta(segs, j_ini, j_fim, pico)\n"
   "        if gancho in NEUTROS:  # ajustes.py: sem frase forte, sem graça\n"
   "            log(f\"descartado (sem frase forte, nota {nota:.2f})\")\n"
   "            continue\n"]
 ]
}

# Código acrescentado no FIM do arquivo: redefine o que precisa (o Python usa a última definição).
ACRESCIMOS = {
 "cortes/transcricao.py": r'''

# ---------------- ajustes.py (24/11/2026) ----------------
# 5) DICIONÁRIO: termos de jogo em inglês que o Whisper escrevia errado ("espaum" no lugar de "spawn").
PROMPT_LIVE = ("Live de streamer brasileiro jogando GTA 6. Salve, chat! Mano, velho, cara, caralho, porra, kkkkk, "
               "meu Deus, não acredito, que isso, bora, tá ligado. Spawn, spawnou, respawn, lag, lagou, bug, bugou, "
               "glitch, crashou, headshot, kill, loot, drop, skin, farmar, nerfar, buffar, tankar, noob, trollar, "
               "rushar, quest, checkpoint, save, cutscene, hitbox, hype, GG, nice, fui scamado, Kick, Twitch, "
               "Vice City, Leonida, Lucia, Jason, Rockstar, NPC, procurado, polícia, missão.")
CORRECOES.update({
    "espaum": "spawn", "espaun": "spawn", "espalm": "spawn", "espawn": "spawn", "spaun": "spawn", "spawm": "spawn",
    "espaunou": "spawnou", "espalmou": "spawnou", "espaumou": "spawnou", "spaunou": "spawnou", "espawnou": "spawnou",
    "espaunar": "spawnar", "espalmar": "spawnar", "espaumar": "spawnar",
    "respaum": "respawn", "respaun": "respawn", "respalm": "respawn", "respawm": "respawn", "rispaum": "respawn",
    "léguei": "lag", "légue": "lag", "laguei": "lagou", "lagô": "lagou",
    "bagou": "bugou", "bugô": "bugou", "bagado": "bugado", "bagada": "bugada",
    "glíti": "glitch", "gliti": "glitch", "glitchi": "glitch",
    "crachou": "crashou", "crashô": "crashou",
    "redishot": "headshot", "hedshot": "headshot", "headshoot": "headshot",
    "nubi": "noob", "nub": "noob", "núbi": "noob",
    "kétiscene": "cutscene", "catscene": "cutscene", "catsin": "cutscene",
    "checkpointe": "checkpoint", "chequipoint": "checkpoint", "chekpoint": "checkpoint",
    "jeison": "Jason", "jéison": "Jason", "djeison": "Jason", "jeisson": "Jason", "jéisson": "Jason",
    "lúcia": "Lucia", "rockstá": "Rockstar", "roquistar": "Rockstar",
    "énepecê": "NPC", "enepecê": "NPC", "npcê": "NPC",
    "gegê": "GG", "guigui": "GG", "náice": "nice", "naice": "nice",
    "raipe": "hype", "raype": "hype", "haipe": "hype",
    "trolar": "trollar", "tróllar": "trollar", "ruxar": "rushar",
})

# 6) GRAÇA DE VERDADE: "mano", "cara", "velho", "para", "não", "o que" aparecem em qualquer conversa e
#    valiam o mesmo que risada; conversa normal virava "reação forte". Agora palavra de enchimento vale 0,25
#    e o corte só tem nota alta com risada, grito, palavrão, espanto ou repetição ("não, não, não").
_FORTE = re.compile(
    r"k{3,}|(?:ha){2,}|(?:he){3,}|(?:rs){2,}|caralh\w*|porra|meu deus|n[ãa]o acredito|que isso|socorro|puta|"
    r"vish|eita|morri|nossa senhora|pelo amor de deus|cacete|fala s[ée]rio|t[áa] de brincadeira|que absurdo|"
    r"bizarro|olha isso|rindo|risada|mds|aaa+|ah+ não|o+ loco|o+ louco|surreal|inacredit\w+|"
    # palavrão conta como reação forte (Marco: "xingar muito")
    r"merda\w*|fod[aeiu]\w*|fdp|pqp|vsf|tnc|desgra[çc]\w*|arromb\w*|bosta|filh[ao] da put\w*", re.IGNORECASE)

# 7) TOM DE VOZ: grito pesa na nota. Guarda o áudio do último trecho transcrito (a nota é calculada logo
#    depois da transcrição, nos dois robôs) e compara o volume das falas do corte com o normal dele no trecho.
_transcrever_original = transcrever
_AUDIO = {"a": None}


def transcrever(video):
    out = _transcrever_original(video)
    try:
        _AUDIO["a"] = _audio_16k(video)
    except Exception:
        _AUDIO["a"] = None
    return out


def _grito(segs: list[dict], ini: float, fim: float) -> float:
    """0..1: quanto ele fala mais alto que o normal dele dentro do corte (só nas falas, não no jogo)."""
    a = _AUDIO["a"]
    if a is None or not len(a):
        return 0.0

    def db(t0, t1):
        x = a[int(t0 * 16000):int(t1 * 16000)]
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-6) if len(x) > 160 else None

    pal = [p for s in segs for p in s["palavras"]]
    tudo = [d for d in (db(p["ini"], p["fim"]) for p in pal) if d is not None]
    dentro = [d for d in (db(p["ini"], p["fim"]) for p in pal if p["fim"] > ini and p["ini"] < fim) if d is not None]
    if len(tudo) < 10 or len(dentro) < 5:
        return 0.0
    alto, base = float(np.percentile(dentro, 90)), float(np.median(tudo))
    return float(min(1.0, max(0.0, (alto - base - 4) / 8)))  # +4 dB = começa a contar; +12 dB = grito


_PALAVRAO = re.compile(r"(?i)\b(caralh\w*|porra\w*|puta\w*|merda\w*|fod[aeiu]\w*|fdp|pqp|vsf|tnc|cacete|"
                       r"desgra[çc]\w*|arromb\w*|bosta)\b")


def _gatilhos(t: str) -> float:
    forte = len(_FORTE.findall(t))
    fraco = max(0, len(_REACAO.findall(t)) - forte)
    return forte * 1.0 + fraco * 0.25 + len(_PALAVRAO.findall(t)) * 0.6  # xingar muito = reação


def _repeticoes(t: str) -> int:
    pal = [p.strip(",.!?…") for p in t.lower().split()]
    return sum(1 for a, b in zip(pal, pal[1:]) if a and a == b)


def _intensidade(s: dict) -> float:
    t = s["texto"]
    dur = max(0.8, s["fim"] - s["ini"])
    return (_gatilhos(t) + 0.4 * (t.count("!") + t.count("?")) + 0.8 * _repeticoes(t)) / dur


def nota_reacao(segs: list[dict], ini: float, fim: float) -> float:
    """0..1: quanto o trecho tem graça (risada, grito, palavrão, espanto), não só conversa."""
    dentro = [s for s in segs if s["fim"] > ini and s["ini"] < fim]
    texto = " ".join(s["texto"] for s in dentro)
    if len(texto.split()) < 8:  # quase ninguém falando: provavelmente só o jogo
        return 0.0
    dur = max(1.0, fim - ini)
    fortes = len(_FORTE.findall(texto))
    rep = _repeticoes(texto)
    bruto = (_gatilhos(texto) + 0.4 * (texto.count("!") + texto.count("?")) + 0.8 * rep) / dur * 10
    nota = min(1.0, bruto / 6)
    g = _grito(segs, ini, fim)
    if fortes == 0 and rep < 2 and g < 0.5:  # nenhuma risada/grito/espanto/palavrão: é conversa
        nota *= 0.4
    return round(min(1.0, nota + 0.35 * g), 3)
''',
}

for arquivo, lista in TROCAS.items():
    p = Path(arquivo)
    cod = p.read_text(encoding="utf-8")
    for velho, novo in lista:
        if velho not in cod:
            raise SystemExit(f"ajustes.py: não achei o trecho em {arquivo}: {velho[:70]!r}")
        cod = cod.replace(velho, novo, 1)
    p.write_text(cod, encoding="utf-8")
for arquivo, extra in ACRESCIMOS.items():
    p = Path(arquivo)
    p.write_text(p.read_text(encoding="utf-8") + extra, encoding="utf-8")
print("ajustes aplicados: 6 por dia (2 h, 11h-22h59), personagem centralizado, sem pergunta no fim, "
      "dicionário de jogo, filtro de graça (risada, palavrão, grito)")

# 25/11/2026: visual novo (abertura com o pico, zoom na reação, barra de progresso, gancho pulsando).
# O código fica no visual_inicio.py do repositório e é acrescentado no fim do montagem.py.
_v = Path("visual_inicio.py")
if not _v.exists():
    raise SystemExit("ajustes.py: falta o visual_inicio.py")
_m = Path("cortes/montagem.py")
_m.write_text(_m.read_text(encoding="utf-8") + _v.read_text(encoding="utf-8"), encoding="utf-8")
print("visual novo aplicado: abertura com o pico, zoom, barra de progresso, gancho pulsando")
