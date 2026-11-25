

# ---------------- ajustes.py (25/11/2026): início que prende + visual ----------------
# Marco: "melhore o visual para atrair mais pessoas, faça algo que prenda no início".
#  - SEMPRE abre com o momento forte (antes só quando o pico estava no fim do corte): 2,5 s do pico,
#    flash branco e "POUCO ANTES…", e aí o corte do começo.
#  - "punch" de zoom: o vídeo entra com zoom e solta no 1º meio segundo (o primeiro quadro já se mexe) e
#    dá um zoom rápido no rosto/na cena no instante da reação.
#  - barra de progresso amarela no pé da tela (quem vê a barra andando fica até o fim).
#  - gancho maior e pulsando nos 3 primeiros segundos.
ABERTURA = 2.5

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


def short(trecho: Path, ini: float, fim: float, palavras: list[dict], arroba: str, foco_x: float,
          saida: Path, gancho: str = "", pico: float | None = None, pergunta: str = "") -> Path:
    dur = fim - ini
    a0 = None
    # abertura com o momento forte sempre que ele não está logo no começo do corte
    if pico is not None and pico - ini >= 5.0:
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
    alt_cam = int(H * 0.40)
    alt_jogo_cam = H - alt_cam
    r = rosto.detectar(trecho, ini, dur, proporcao_cam=1080 / alt_cam)
    gancho_y = 150
    if r and r["tipo"] == "rosto":
        pos_leg = (540, H - 300)
        y_aviso = 420
        gancho_y = int(H * 0.60)
        cy = int(H * 0.35)
        x = f"'max(0,min(iw-1080,iw*{r['foco_x']:.4f}-540))'"
        topo = f"[SRC]scale=-2:{H},crop=1080:{H}:x={x}:y=0,setsar=1[topo];"
    elif r and r["tipo"] == "cam":
        larg_esc = round(alt_jogo_cam * 16 / 9)
        esq = (larg_esc - 1080) / 2
        bx0 = max(0, int(r["x"] * larg_esc - esq))
        bx1 = min(1080, int((r["x"] + r["w"]) * larg_esc - esq))
        by0 = max(0, int(r["y"] * alt_jogo_cam))
        by1 = min(alt_jogo_cam, int((r["y"] + r["h"]) * alt_jogo_cam))
        jogo = f"[j]scale=-2:{alt_jogo_cam},crop=1080:{alt_jogo_cam}:x='(iw-1080)/2':y=0,setsar=1"
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
    _render(trecho, ini, dur, sat, off, filtro.replace("{ASS}", ass.name), saida, abertura=a0)
    return saida
