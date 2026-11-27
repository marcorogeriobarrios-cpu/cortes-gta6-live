

# ---------------- ajustes.py (25/11/2026): início que prende + visual ----------------
# Marco: "melhore o visual para atrair mais pessoas, faça algo que prenda no início".
#  - SEM a abertura com o momento forte repetido + "POUCO ANTES…" (Marco não gostou: a fala aparecia
#    solta e depois se repetia).
#  - "punch" de zoom: o vídeo entra com zoom e solta no 1º meio segundo (o primeiro quadro já se mexe) e
#    dá um zoom rápido no rosto/na cena no instante da reação.
#  - barra de progresso amarela no pé da tela (quem vê a barra andando fica até o fim).
#  - gancho maior e pulsando nos 3 primeiros segundos.
ABERTURA = 2.5
# DESABAFOS (desabafo.py liga isto só durante o corte): o rosto é o que importa, então a câmera fica com 58% da
# tela (em vez de 40%) e há um zoom rápido a cada ~10 s, como o short viral do Alanzoka que o Marco mostrou.
DESTAQUE_ROSTO = False

_legenda_ass_original = legenda_ass


def legenda_ass(destino, palavras, ini, dur, credito, w, h, pos_leg, alinh_cred, gancho="", pergunta="",
                aviso_volta=None, gancho_y=150):
    p = _legenda_ass_original(destino, palavras, ini, dur, credito, w, h, pos_leg, alinh_cred, gancho, pergunta,
                              aviso_volta, gancho_y)
    if w != 1080:
        return p
    txt = p.read_text(encoding="utf-8-sig")
    # gancho: maior e com pulso nos primeiros 3 s (a linha do começo é a que tem o "pop" \t(0,120,...))
    txt = txt.replace("\\fscx85\\fscy85\\t(0,120,\\fscx100\\fscy100)}",
                      # 1º quadro já grande (é o que aparece rolando o feed), depois pulsa
                      "\\fscx112\\fscy112\\t(0,140,\\fscx122\\fscy122)\\t(140,260,\\fscx108\\fscy108)"
                      "\\t(900,1100,\\fscx114\\fscy114)\\t(1100,1300,\\fscx108\\fscy108)"
                      "\\t(2000,2200,\\fscx114\\fscy114)\\t(2200,2400,\\fscx108\\fscy108)}")
    extra = []
    ms = max(1, int(dur * 1000))
    # barra de progresso (14 px) que enche da esquerda para a direita durante o vídeo todo
    extra.append(f"Dialogue: 6,{_t(0)},{_t(dur)},Leg,,0,0,0,,"
                 f"{{\\an7\\pos(0,{h - 14})\\bord0\\shad0\\1c&H00E6FF&\\clip(0,{h - 14},1,{h})"
                 f"\\t(0,{ms},\\clip(0,{h - 14},{w},{h}))\\p1}}m 0 0 l {w} 0 {w} 14 0 14{{\\p0}}")
    if aviso_volta:
        t0 = aviso_volta[0]
        # flash branco na volta no tempo (separa a abertura do corte e dá o "tranco")
        extra.append(f"Dialogue: 7,{_t(t0)},{_t(min(dur, t0 + 0.3))},Leg,,0,0,0,,"
                     f"{{\\an7\\pos(0,0)\\bord0\\shad0\\1c&HFFFFFF&\\fad(0,280)\\p1}}m 0 0 l {w} 0 {w} {h} 0 {h}{{\\p0}}")
    p.write_text(txt + "\n" + "\n".join(extra), encoding="utf-8-sig")
    return p


def _zoom(picos: list[float], cy: int, H: int) -> str:
    """zoompan: entra com zoom e solta no 1º 0,4 s; zoom rápido (+16%) que solta em 1 s em cada reação."""
    z = "1+0.12*max(0,1-(in/30)/0.4)"
    for p in picos:
        z += f"+0.16*between(in/30,{p:.2f},{p + 1.0:.2f})*(1-((in/30)-{p:.2f})/1.0)"
    return (f"zoompan=z='{z}':x='iw/2-iw/zoom/2':y='max(0,min(ih-ih/zoom,{cy}-ih/zoom/2))'"
            f":d=1:s=1080x{H}:fps=30,")


# LEGENDA DO JOGO (25/11/2026, Marco: "transcrever a legenda do jogo... de uma cor diferente da do streamer"):
# o recorte vertical corta as laterais da legenda do jogo. O Tesseract lê a faixa de legenda da tela ORIGINAL
# (embaixo, no meio) 2x por segundo e ela é escrita de novo, inteira, em azul-claro numa tarja escura por cima
# do lugar onde ela fica no jogo. Sem Tesseract (ou sem legenda no jogo) o vídeo sai como antes.
_TESS_WIN = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
_QPS = 4  # quadros lidos por segundo
# 27/11/2026, Marco: "queria as falas dos personagens, mas poluindo menos" -> letra menor (38) e só uma caixinha
# escura semitransparente JUSTA atrás do texto (BorderStyle 3), no lugar da faixa preta na largura toda.
ESTILO_JOGO = ("Style: Jogo,Arial,38,&H00FFE14D,&H00FFE14D,&H30000000,&H30000000,-1,0,0,0,100,100,0,0,3,9,0,5,"
               "110,110,0,1")


def _tesseract() -> str | None:
    import shutil
    return shutil.which("tesseract") or (str(_TESS_WIN) if _TESS_WIN.exists() else None)


def _ler_quadro(exe: str, png: Path) -> str:
    import os
    import re as _re
    env = dict(os.environ)
    local = Path(__file__).resolve().parent.parent / "dados" / "tessdata"  # português baixado à parte (Windows)
    if local.exists():
        env["TESSDATA_PREFIX"] = str(local)
    # -c tessedit_create_tsv=1 (e não o atalho "tsv", que depende da pasta configs do tessdata)
    r = subprocess.run([exe, str(png), "stdout", "-l", "por", "--psm", "6", "-c", "tessedit_create_tsv=1"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    linhas = {}
    for ln in r.stdout.splitlines()[1:]:
        c = ln.split("\t")
        if len(c) < 12 or not c[11].strip():
            continue
        try:
            conf = float(c[10])
        except ValueError:
            continue
        linhas.setdefault((c[2], c[3], c[4]), []).append((conf, c[11].strip()))
    boas = []
    for pals in linhas.values():  # linha a linha: sujeira (grama, céu, placa, HUD) sai com nota baixa
        texto = " ".join(p for _, p in pals)
        letras = _re.findall(r"[A-Za-zÀ-ÿ]{2,}", texto)
        sem_espaco = texto.replace(" ", "")
        media = sum(cf for cf, _ in pals) / len(pals)
        if (media >= 70 and len(letras) >= 1 and sem_espaco
                and sum(map(len, letras)) / len(sem_espaco) >= 0.7 and len(sem_espaco) >= 4):
            boas.append(texto)
    texto = " ".join(boas).strip()
    if len(_re.findall(r"[A-Za-zÀ-ÿ]{2,}", texto)) < 2:
        return ""
    return texto


def legenda_do_jogo(trecho: Path, t_ini: float, t_fim: float) -> list[tuple[float, float, str]]:
    """[(ini, fim, texto)] no tempo do trecho."""
    import difflib
    import shutil
    import tempfile
    from collections import Counter
    from concurrent.futures import ThreadPoolExecutor
    exe = _tesseract()
    if not exe or t_fim - t_ini < 1:
        return []
    pasta = Path(tempfile.mkdtemp(prefix="legjogo_"))
    try:
        # faixa da legenda (70% do meio, 80-96% da altura), só o branco do texto, preto no branco, 2x maior
        # limiar 240 (só o branco puro das letras): com 190 a grama/céu claros viravam borrão e a leitura falhava;
        # se o 240 não acha nada no quadro, tenta 215
        for lim, pre in ((240, "a"), (215, "b")):
            subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t_ini:.2f}", "-t", f"{t_fim - t_ini:.2f}",
                            "-i", str(trecho), "-vf",
                            # 4x por segundo (falas curtas passavam entre os quadros) e faixa de 73% a 97% da
                            # altura (legenda de 3 linhas começa mais alto)
                            f"fps={_QPS},crop=iw*0.70:ih*0.24:iw*0.15:ih*0.73,format=gray,"
                            f"lut=y='if(gt(val,{lim}),0,255)',scale=iw*2:-1", str(pasta / f"{pre}%04d.png")],
                           capture_output=True, check=True)
        quadros = sorted(pasta.glob("a*.png"))
        with ThreadPoolExecutor(4) as ex:
            textos = list(ex.map(lambda q: _ler_quadro(exe, q), quadros))
            falta = [k for k, tx in enumerate(textos) if not tx]
            segunda = list(ex.map(lambda k: _ler_quadro(exe, pasta / f"b{k + 1:04d}.png"), falta))
        for k, tx in zip(falta, segunda):
            textos[k] = tx
    except Exception:
        return []
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
    import re as _re

    def parecido(a: str, b: str) -> bool:
        a, b = a.lower(), b.lower()
        return (difflib.SequenceMatcher(None, a, b).ratio() > 0.6
                or (min(len(a), len(b)) >= 8 and (a in b or b in a)))

    def limpa(s: str) -> str:
        s = _re.sub(r"^(?:\W*\w{0,2}\W+)(?=[A-ZÀ-Ý])", "", s.strip())  # "e. Caden O:" -> "Caden O:"
        return s.strip(" :;|-_—").strip()

    textos = [limpa(tx) if tx else "" for tx in textos]
    eventos, atual = [], None
    passo = 1 / _QPS
    for k, tx in enumerate(textos):
        t = t_ini + k * passo
        if atual and tx and parecido(atual["v"][-1], tx):
            atual["v"].append(tx)
            atual["fim"] = t + passo
            continue
        if atual:
            eventos.append(atual)
            atual = None
        if tx:
            atual = {"ini": t, "fim": t + passo, "v": [tx]}
    if atual:
        eventos.append(atual)
    # a mesma fala separada por um quadro ruim (ou um pedaço dela) vira uma legenda só
    juntos = []
    for e in eventos:
        if juntos and e["ini"] - juntos[-1]["fim"] <= 1.0 and any(parecido(a, b) for a in juntos[-1]["v"]
                                                                   for b in e["v"]):
            juntos[-1]["fim"] = e["fim"]
            juntos[-1]["v"] += e["v"]
        else:
            juntos.append(e)
    eventos = juntos
    saida = []
    for e in eventos:
        if len(e["v"]) < 2:  # apareceu num quadro só: provavelmente ruído
            continue
        # a melhor leitura é a que tem as palavras que mais se repetem nos outros quadros
        # (erro de leitura, tipo "Porgue" ou "gssa", aparece num quadro só)
        cont = Counter(p for v in e["v"] for p in set(v.lower().split()))

        def nota(v: str) -> int:
            return sum(cont[p] if cont[p] > 1 else -2 for p in v.lower().split())
        texto = max(e["v"], key=lambda v: (nota(v), len(v)))
        # 26/11/2026: o OCR leu o OVERLAY da live (mensagem do chat + "SUB COMBO") como legenda do jogo e ela
        # ficou travada na tela o vídeo todo. Overlay é texto parado e com palavras de alerta; legenda de jogo
        # muda a cada poucos segundos.
        if e["fim"] - e["ini"] > 9 or _OVERLAY.search(texto):
            continue
        saida.append((e["ini"], e["fim"], texto))
    return saida


import re as _re_ov
_OVERLAY = _re_ov.compile(r"(?i)(\b(sub|subs|combo|bits?|follow\w*|seguid\w*|donat\w*|doa[çc][aãõ]\w*|inscri\w*|"
                      r"prime|tier|raid|host|cheer|resgat\w*|pontos|meta|[úu]ltim[oa]\s+sub|x\d+)\b|@|https?:|www\.|\.com\b)")


_legenda_do_jogo_sem_cache = legenda_do_jogo
# 27/11/2026, Marco: "tela preta com a fala azul muito poluída" -> a tarja + fala azul sai da tela. A leitura
# (OCR) continua só para tirar da legenda do streamer as falas dos personagens.
LEGENDA_JOGO_NA_TELA = True  # de volta, mas discreta (caixinha justa, letra menor)


def _quebra(tx: str, largura: int = 34) -> str:
    """Quebra em no máximo 2 linhas equilibradas (a caixinha fica justa em cada linha)."""
    import re as _re
    pal = tx.split()
    if len(_re.sub(r"\{[^}]*\}", "", tx)) <= largura or len(pal) < 2:
        return tx
    melhor = min(range(1, len(pal)), key=lambda k: abs(len(" ".join(pal[:k])) - len(" ".join(pal[k:]))))
    return " ".join(pal[:melhor]) + "\\N" + " ".join(pal[melhor:])


_CACHE_LJ: dict = {}


def legenda_do_jogo(trecho: Path, t_ini: float, t_fim: float) -> list[tuple[float, float, str]]:  # noqa: F811
    """Mesma leitura, guardada: é usada para desenhar a legenda do jogo E para limpar a legenda do streamer."""
    k = (str(trecho), round(t_ini, 2), round(t_fim, 2))
    if k not in _CACHE_LJ:
        _CACHE_LJ[k] = _legenda_do_jogo_sem_cache(trecho, t_ini, t_fim)
    return _CACHE_LJ[k]


def _sem_falas_do_jogo(trecho: Path, ini: float, fim: float, palavras: list[dict]) -> list[dict]:
    """26/11/2026, Marco: "falas dos personagens aparecem no lugar da do youtuber". O Whisper transcreve TODO
    o áudio; a fala do personagem aparece escrita na legenda do jogo (OCR). Palavra do Whisper que cai no tempo
    de uma legenda do jogo (com folga) e está escrita nela é do personagem -> sai da legenda do streamer."""
    import re as _re
    try:
        eventos = legenda_do_jogo(trecho, ini, fim)
    except Exception:
        return palavras
    if not eventos:
        return palavras
    def norm(w: str) -> str:
        return _re.sub(r"[^\wà-ÿ]", "", w.lower())
    evs = [(e0 - 1.0, e1 + 1.0, {norm(w) for w in tx.split() if len(norm(w)) >= 2}) for e0, e1, tx in eventos]
    fora, saida = 0, []
    for p in palavras:
        w = norm(p.get("p", ""))
        meio = (p["ini"] + p["fim"]) / 2
        if w and any(a <= meio <= b and w in ws for a, b, ws in evs):
            fora += 1
            continue
        saida.append(p)
    if fora:
        print(f"  legenda: {fora} palavra(s) de personagem tiradas da fala do streamer", flush=True)
    return saida


def _borrar_legenda_original(filtro: str, trecho: Path, ini: float, fim: float, a0: float | None,
                             faixa: tuple[int, int] | None) -> str:
    """27/11/2026, Marco: "o texto atrás vai obstruir, tem que remover o texto do próprio jogo". Enquanto há
    fala do jogo, a faixa onde fica a legenda ORIGINAL é borrada (some o texto, a cena continua dando para ver)
    e a nossa legenda vai por cima. Sem fala do jogo, nada é borrado."""
    if faixa is None or "subtitles='{ASS}'[v]" not in filtro:
        return filtro
    jan_ini = min(ini, a0) if a0 is not None else ini
    jan_fim = max(fim, a0 + ABERTURA) if a0 is not None else fim
    eventos = legenda_do_jogo(trecho, jan_ini, jan_fim)
    if not eventos:
        return filtro
    desloc = ABERTURA if a0 is not None else 0
    janelas = []
    for e0, e1, _ in eventos:
        if a0 is not None:
            janelas.append((max(e0, a0) - a0 - 0.15, min(e1, a0 + ABERTURA) - a0 + 0.15))
        janelas.append((max(e0, ini) - ini + desloc - 0.15, min(e1, fim) - ini + desloc + 0.15))
    janelas = [(max(0.0, a), b) for a, b in janelas if b - a >= 0.3]
    if not janelas:
        return filtro
    y0, y1 = faixa
    alt = (y1 - y0) // 2 * 2
    quando = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in janelas)
    borra = (f"split[lgA][lgB];[lgB]crop=1080:{alt}:0:{y0},boxblur=luma_radius=16:luma_power=2[lgZ];"
             f"[lgA][lgZ]overlay=0:{y0}:enable='{quando}',subtitles='{{ASS}}'[v]")
    return filtro.replace("subtitles='{ASS}'[v]", borra, 1)


def _por_legenda_do_jogo(ass: Path, trecho: Path, ini: float, fim: float, a0: float | None,
                         faixa: tuple[int, int] | None) -> int:
    """faixa = (y0, y1) da área onde a legenda original do jogo aparece no vídeo final: enquanto há fala do
    jogo, uma faixa escura da largura toda cobre a legenda original (cortada nas laterais) e a nova vai por cima."""
    if faixa is None:
        return 0
    y0, y1 = faixa
    y = (y0 + y1) // 2
    jan_ini = min(ini, a0) if a0 is not None else ini
    jan_fim = max(fim, a0 + ABERTURA) if a0 is not None else fim
    eventos = legenda_do_jogo(trecho, jan_ini, jan_fim)
    if not eventos:
        return 0
    desloc = ABERTURA if a0 is not None else 0
    linhas = []
    # uma cor por personagem ("Caden O: ..."), na ordem em que aparecem; fala sem nome = quem falou por último.
    # Nunca amarelo/branco (cores do streamer). Cores em BGR do ASS: azul-claro, rosa, verde, laranja.
    import re as _re
    cores = ["&HFFE14D&", "&HC878FF&", "&H8CFF78&", "&H3CAAFF&"]
    de_quem, ultimo = {}, None
    for e0, e1, tx in eventos:
        tx = tx.replace("{", "").replace("}", "").replace("\\", "")
        nome = _re.match(r"^([A-ZÀ-Ý][\wÀ-ÿ'.\- ]{0,20}?)\s*:", tx)
        if nome:
            # só a 1ª palavra do nome ("Caden O", "Caden-O", "Caden'O" = o mesmo personagem)
            chave = (_re.findall(r"[a-zà-ÿ]+", nome.group(1).lower()) or ["?"])[0][:6]
            ultimo = de_quem.setdefault(chave, cores[len(de_quem) % len(cores)])
        cor = ultimo or cores[0]
        tx = f"{{\\1c{cor}}}" + tx
        partes = []
        if a0 is not None:
            partes.append((max(e0, a0) - a0, min(e1, a0 + ABERTURA) - a0))
        partes.append((max(e0, ini) - ini + desloc, min(e1, fim) - ini + desloc))
        for a, b in partes:
            if b - a >= 0.3:
                linhas.append(f"Dialogue: 5,{_t(a)},{_t(b)},Jogo,,0,0,0,,{{\\q0\\pos(540,{y})}}{_quebra(tx)}")
    if not linhas:
        return 0
    txt = ass.read_text(encoding="utf-8-sig")
    txt = txt.replace("\n[Events]", ESTILO_JOGO + "\n\n[Events]", 1)
    ass.write_text(txt + "\n" + "\n".join(linhas), encoding="utf-8-sig")
    return len(linhas)


def short(trecho: Path, ini: float, fim: float, palavras: list[dict], arroba: str, foco_x: float,
          saida: Path, gancho: str = "", pico: float | None = None, pergunta: str = "") -> Path:
    dur = fim - ini
    a0 = None
    palavras = _sem_falas_do_jogo(trecho, ini, fim, palavras)
    # SEM abertura repetida (25/11/2026, Marco: "mostra uma fala nada a ver, depois POUCO ANTES e repete a
    # fala"): o corte começa direto; o que prende é o gancho, o zoom de entrada e a barra de progresso
    if False and pico is not None and pico - ini >= 5.0:
        a0 = max(0.0, pico - 1.0)
    total = dur + (ABERTURA if a0 is not None else 0)
    pal = []
    if a0 is not None:
        pal += [{**p, "ini": p["ini"] - a0, "fim": p["fim"] - a0} for p in palavras
                if p["ini"] >= a0 and p["fim"] <= a0 + ABERTURA]
    desloc = ABERTURA if a0 is not None else 0
    pal += [{**p, "ini": p["ini"] - ini + desloc, "fim": p["fim"] - ini + desloc} for p in palavras
            if p["fim"] > ini and p["ini"] < fim]
    # instantes da reação no vídeo final (na abertura e no corte)
    picos = []
    if pico is not None:
        if a0 is not None:
            picos.append(pico - a0)
        picos.append(pico - ini + desloc)
    if DESTAQUE_ROSTO and not picos:
        picos = [6.0, 16.0, 26.0, 36.0, 46.0]
    picos = [p for p in picos if 0.5 <= p < total - 1.0]

    H = ALTURA_TOPO
    faixa = 1920 - H
    if faixa > 0:
        sat, off = _satisf("baixo", total)
        baixo = (f"[1:v]scale=1080:{faixa}:force_original_aspect_ratio=increase,"
                 f"crop=1080:{faixa},setsar=1[baixo];")
    else:
        sat, off = trecho, 0.0
        baixo = ""
    alt_cam = int(H * (0.58 if DESTAQUE_ROSTO else 0.40))
    alt_jogo_cam = H - alt_cam
    r = rosto.detectar(trecho, ini, dur, proporcao_cam=1080 / alt_cam)
    gancho_y = 150
    if r and r["tipo"] == "rosto":
        pos_leg = (540, H - 300)
        y_aviso = 420
        gancho_y = int(H * 0.60)
        cy = int(H * 0.35)
        y_leg_jogo = None  # rosto grande (podcast): não tem legenda de jogo
        x = f"'max(0,min(iw-1080,iw*{r['foco_x']:.4f}-540))'"
        topo = f"[SRC]scale=-2:{H},crop=1080:{H}:x={x}:y=0,setsar=1[topo];"
    elif r and r["tipo"] == "cam":
        larg_esc = round(alt_jogo_cam * 16 / 9)
        esq = (larg_esc - 1080) / 2
        # 25/11/2026 (Marco: "bug na lateral"): se a câmera do streamer só invade a BEIRA do recorte, o recorte
        # anda para o lado e a deixa de fora (sem borrão); o personagem fica no máx. 220 px fora do centro.
        # O borrão só fica quando a câmera está mais para o meio da tela.
        cx0, cx1 = r["x"] * larg_esc - esq, (r["x"] + r["w"]) * larg_esc - esq  # câmera no recorte central
        dx = 0
        if cx0 < 1080 and cx1 > 0:
            if cx0 >= 540 and 1080 - cx0 <= 220:      # câmera à direita, entrando pouco
                dx = -int(1080 - cx0 + 4)
            elif cx1 <= 540 and cx1 <= 220:            # câmera à esquerda, entrando pouco
                dx = int(cx1 + 4)
        dx = int(max(-esq, min(esq, dx)))
        bx0 = max(0, int(cx0 - dx))
        bx1 = min(1080, int(cx1 - dx))
        by0 = max(0, int(r["y"] * alt_jogo_cam))
        by1 = min(alt_jogo_cam, int((r["y"] + r["h"]) * alt_jogo_cam))
        jogo = (f"[j]scale=-2:{alt_jogo_cam},crop=1080:{alt_jogo_cam}:"
                f"x='max(0,min(iw-1080,(iw-1080)/2+{dx}))':y=0,setsar=1")
        bw, bh = (bx1 - bx0) // 2 * 2, (by1 - by0) // 2 * 2
        raio = min(30, min(bw, bh) // 4 - 1)  # boxblur: raio < metade do lado do croma (falhava com área pequena)
        if raio >= 2:
            jogo += (f",split[j1][j2];[j2]crop={bw}:{bh}:{bx0}:{by0},boxblur={raio}:3[tapa];"
                     f"[j1][tapa]overlay={bx0}:{by0}[jogo];")
        else:
            jogo += "[jogo];"
        gancho_y = alt_cam - 50
        pos_leg = (540, alt_cam + 330)
        y_aviso = alt_cam + 220
        cy = alt_cam // 2  # o zoom da reação vai no rosto (câmera em cima)
        # onde a legenda original fica no jogo (80-96% da altura da tela), sem cobrir a barra de progresso
        y_leg_jogo = (alt_cam + int(alt_jogo_cam * 0.72), min(H - 16, alt_cam + int(alt_jogo_cam * 0.97)))
        topo = ("[SRC]split[c][j];"
                f"[c]crop=w=iw*{r['w']:.4f}:h=ih*{r['h']:.4f}:x=iw*{r['x']:.4f}:y=ih*{r['y']:.4f},"
                f"scale=1080:{alt_cam}:force_original_aspect_ratio=increase,crop=1080:{alt_cam},setsar=1[cam];"
                + jogo + "[cam][jogo]vstack=inputs=2[topo];")
    else:
        alt_jogo = 900
        y_jogo = (H - alt_jogo) // 2
        pos_leg = (540, y_jogo + alt_jogo + 110)
        y_aviso = y_jogo + 80
        cy = H // 2
        y_leg_jogo = (y_jogo + int(alt_jogo * 0.72), y_jogo + int(alt_jogo * 0.97))
        topo = ("[SRC]split[f][j];"
                f"[f]scale=-2:{H},crop=1080:{H},boxblur=25:2,eq=brightness=-0.15,setsar=1[fundo];"
                f"[j]scale=-2:{alt_jogo},crop=1080:{alt_jogo}:x='(iw-1080)*{foco_x}':y=0,setsar=1[jogo];"
                f"[fundo][jogo]overlay=0:{y_jogo}[topo];")
    zoom = _zoom(picos, cy, H)
    if faixa > 0:
        fecha = f"[topo]fps=30,{zoom}setsar=1[topoz];[topoz][baixo]vstack=inputs=2,subtitles='{{ASS}}'[v]"
    else:
        fecha = f"[topo]fps=30,{zoom}setsar=1,subtitles='{{ASS}}'[v]"
    filtro = topo + baixo + fecha
    ass = legenda_ass(saida.with_suffix(".ass"), pal, 0, total, f"Créditos: {arroba}", 1080, 1920, pos_leg, 8,
                      gancho=gancho, pergunta=pergunta, gancho_y=gancho_y,
                      aviso_volta=(ABERTURA, y_aviso) if a0 is not None else None)
    try:
        if LEGENDA_JOGO_NA_TELA:
            _por_legenda_do_jogo(ass, trecho, ini, fim, a0, y_leg_jogo)
    except Exception as e:  # legenda do jogo é extra: nunca derruba o corte
        print(f"  legenda do jogo falhou: {str(e)[:150]}", flush=True)
    try:
        if LEGENDA_JOGO_NA_TELA:
            filtro = _borrar_legenda_original(filtro, trecho, ini, fim, a0, y_leg_jogo)
    except Exception as e:  # nunca derruba o corte
        print(f"  borrão da legenda do jogo falhou: {str(e)[:150]}", flush=True)
    _render(trecho, ini, dur, sat, off, filtro.replace("{ASS}", ass.name), saida, abertura=a0)
    return saida
