"""COMPILAÇÕES (27/11/2026, pedidos do Marco):
  finais -> "todos os finais do GTA 6" com a reação do Alanzoka, legenda e título em INGLÊS (longo + short)
  niko   -> youtubers reagindo ao protagonista do GTA 4 (Niko Bellic) no GTA 6, em INGLÊS (longo + short)
  davy   -> as burrices do Davy Jones no GTA 6 (o meme de que ele é ruim nos jogos), em português (longo + short)

Como funciona (python -u compilacao.py --tema niko [--modo buscar|publicar] [--dias 10]):
  1) BUSCA: pega as lives/vídeos de GTA 6 dos canais do tema (últimos N dias), baixa só o ÁUDIO, transcreve com
     o Whisper "small" (rápido) e procura as palavras do tema. Grava o que achou em dados/compilacao_<tema>.md.
  2) MONTAGEM (modo publicar): escolhe os melhores trechos, baixa o vídeo deles, transcreve direito (Whisper
     turbo), traduz para inglês com o Claude Haiku quando o tema pede, e monta:
       - vídeo LONGO 1920x1080 (trechos em sequência, legenda embaixo, crédito do streamer no canto);
       - SHORT vertical com o melhor trecho (formato normal do canal).
     Publica os dois (se a cota deixar) e anota em dados/compilacoes.json para não repetir.
Só usa canais com autorizado: true no canais.yaml (crédito sempre na tela e na descrição).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yt_dlp

import live_gta as lg
from cortes import fontes, montagem, transcricao, youtube
from cortes.base import BAIXADOS, DADOS, config

FEITAS = DADOS / "compilacoes.json"
GTA6 = re.compile(r"(?i)\bgta\s*(?:6|vi)\b|vice\s*city|leonida|grand theft auto\s*(?:6|vi)")

TEMAS = {
    "finais": {
        "canais": ["Alanzoka"],
        "palavras": r"(?i)cr[ée]ditos|\bzerei\b|\bzeramos\b|\bzerou\b|final do jogo|\bending\b|acabou o jogo|"
                    r"final (bom|ruim|verdadeiro|secreto|alternativo)|outro final",
        "antes": 150, "depois": 30, "max_trechos": 6, "por_canal": 6, "ingles": True,
        "titulo": "GTA 6 ALL ENDINGS - BRAZILIAN STREAMER REACTS (ALANZOKA)",
        "titulo_short": "HIS REACTION TO THE GTA 6 ENDING 😳",
        "gancho_short": "HE JUST FINISHED GTA 6",
        "tags": ["GTA 6", "GTA 6 ending", "GTA 6 all endings", "GTA VI", "Alanzoka", "GTA 6 reaction"],
    },
    "niko": {
        "canais": "todos",
        "palavras": r"(?i)\bniko\b|\bnico bel|bellic|\bbelic\b|gta (4|iv|quatro)\b|\broman\b",
        "antes": 20, "depois": 25, "max_trechos": 8, "por_canal": 2, "ingles": True,
        "titulo": "BRAZILIAN STREAMERS REACT TO NIKO BELLIC IN GTA 6",
        "titulo_short": "THEY SAW NIKO BELLIC IN GTA 6 😱",
        "gancho_short": "NIKO BELLIC IS IN GTA 6?!",
        "tags": ["GTA 6", "Niko Bellic", "GTA 4", "GTA 6 Niko", "GTA 6 easter egg", "GTA 6 reaction"],
    },
    "davy": {
        "canais": ["Davy Jones"],
        "palavras": r"(?i)\bmorri\b|\bmorreu\b|\bburr[oa]\b|\berrei\b|n[ãa]o acredito|\bca[íi]\b|\bbati\b|"
                    r"como assim|\bperdi\b|socorro|que isso|n[ãa]o sei jogar|sou ruim|\bruim\b|capotei|atropelei",
        "antes": 18, "depois": 12, "max_trechos": 10, "por_canal": 10, "ingles": False,
        "titulo": "AS MAIORES BURRICES DO DAVY JONES NO GTA 6",
        "titulo_short": "DAVY JONES SENDO DAVY JONES NO GTA 6 KKKK",
        "gancho_short": "DAVY JONES NO GTA 6 KKKK",
        "tags": ["Davy Jones", "GTA 6", "Davy Jones GTA 6", "Davy Jones ruim", "cortes", "GTA VI"],
    },
}


def log(msg: str) -> None:
    lg.log(f"compilação: {msg}")


# ---------------------------------------------------------------- 1) busca
def _canais(tema: dict) -> list[dict]:
    todos = [c for c in config()["canais"] if c.get("autorizado")]
    if tema["canais"] != "todos":
        todos = [c for c in todos if c["nome"] in tema["canais"]]
    if any(c["nome"] == "Alanzoka" for c in todos):  # só a Twitch dele (as mesmas lives, inteiras; sem repetir)
        todos = [c for c in todos if c["nome"] != "Alanzoka"] + [{**lg.CANAL, "nome": "Alanzoka"}]
    return todos


def _videos_gta(canal: dict, dias: int) -> list[dict]:
    limite = time.time() - dias * 86400
    achados = []
    for aba in fontes._abas(canal["url"]):
        try:
            with yt_dlp.YoutubeDL({**fontes.OPC_BASE, "extract_flat": True, "playlistend": 12}) as y:
                lista = y.extract_info(aba, download=False) or {}
        except Exception as e:
            log(f"[{canal['nome']}] não listou {aba}: {str(e)[:120]}")
            continue
        for e in [e for e in (lista.get("entries") or []) if e]:
            if e.get("title") and not GTA6.search(e["title"]):
                continue
            url = fontes._url_do_item(e, canal["url"])
            try:
                with yt_dlp.YoutubeDL(fontes.OPC_BASE) as y:
                    i = y.extract_info(url, download=False)
            except Exception as ex:
                log(f"[{canal['nome']}] sem detalhes de {url}: {str(ex)[:100]}")
                continue
            ts = i.get("timestamp") or i.get("release_timestamp") or 0
            if not ts and i.get("upload_date"):
                ts = dt.datetime.strptime(i["upload_date"], "%Y%m%d").timestamp()
            if (not GTA6.search(i.get("title") or "") or ts < limite or (i.get("duration") or 0) < 300
                    or i.get("live_status") in ("is_live", "is_upcoming")):
                continue
            achados.append({"url": i.get("webpage_url") or url, "titulo": i.get("title") or "",
                            "duracao": i.get("duration") or 0, "canal": canal["nome"],
                            "arroba": canal.get("arroba", ""), "canal_url": canal.get("url_oficial") or canal["url"],
                            "id": fontes.chave(i.get("webpage_url") or url)})
    vistos, unicos = set(), []
    for v in achados:
        if v["id"] not in vistos:
            vistos.add(v["id"])
            unicos.append(v)
    return unicos


_SMALL = None


def _whisper_small():
    global _SMALL
    if _SMALL is None:
        from faster_whisper import WhisperModel
        _SMALL = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
    return _SMALL


def _audio_pedaco(v: dict, ini: float, fim: float) -> Path:
    destino = BAIXADOS / f"{v['id']}_busca_{int(ini)}.m4a"
    if "twitch.tv" in v["url"]:
        return fontes._hls_range(v["url"], "audio_only/bestaudio/worst", ini, fim, destino, so_audio=True)
    opc = {**fontes.OPC_BASE, "format": "bestaudio[ext=m4a]/bestaudio/worst",
           "outtmpl": str(destino.with_suffix(".%(ext)s")),
           "download_ranges": yt_dlp.utils.download_range_func(None, [(ini, fim)])}
    with yt_dlp.YoutubeDL(opc) as y:
        y.download([v["url"]])
    return next(BAIXADOS.glob(f"{v['id']}_busca_{int(ini)}.*"))


def buscar(nome: str, tema: dict, dias: int, prazo: float) -> list[dict]:
    """[{url, canal, t, texto, ...}] de todas as falas com as palavras do tema."""
    rx = re.compile(tema["palavras"])
    hits = []
    for canal in _canais(tema):
        if time.time() > prazo:
            break
        try:
            videos = _videos_gta(canal, dias)
        except Exception as e:
            log(f"[{canal['nome']}] erro ao listar: {str(e)[:150]}")
            continue
        log(f"[{canal['nome']}] {len(videos)} vídeo(s) de GTA 6")
        for v in videos[:4]:
            for ini in range(0, int(v["duracao"]), 1800):  # meia hora por vez
                if time.time() > prazo:
                    break
                fim = min(v["duracao"], ini + 1800)
                try:
                    aud = _audio_pedaco(v, ini, fim)
                    segs, _ = _whisper_small().transcribe(transcricao._audio_16k(aud), language="pt",
                                                          vad_filter=True, beam_size=1)
                    for s in segs:
                        if rx.search(s.text):
                            hits.append({**v, "t": ini + s.start, "texto": s.text.strip()})
                    aud.unlink(missing_ok=True)
                except Exception as e:
                    log(f"[{canal['nome']}] erro na busca em {v['url']} {ini/60:.0f} min: {str(e)[:150]}")
                    break
            log(f"[{canal['nome']}] '{v['titulo'][:50]}': {sum(h['id'] == v['id'] for h in hits)} trecho(s)")
    linhas = [f"# Busca '{nome}' ({dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))):%d/%m %H:%M})", ""]
    linhas += [f"- {h['canal']} | {h['url']} | {int(h['t'] // 3600)}:{int(h['t'] % 3600 // 60):02d}:"
               f"{int(h['t'] % 60):02d} | {h['texto'][:120]}" for h in hits]
    (DADOS / f"compilacao_{nome}.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    (DADOS / f"compilacao_{nome}.json").write_text(json.dumps({"quando": time.time(), "hits": hits},
                                                              ensure_ascii=False), encoding="utf-8")
    return hits


def escolher(tema: dict, hits: list[dict]) -> list[dict]:
    """Junta falas próximas num trecho só; respeita o limite por canal e o total."""
    trechos = []
    for h in sorted(hits, key=lambda h: (h["id"], h["t"])):
        a, b = max(0.0, h["t"] - tema["antes"]), h["t"] + tema["depois"]
        if trechos and trechos[-1]["id"] == h["id"] and a <= trechos[-1]["fim"] + 10:
            trechos[-1]["fim"] = max(trechos[-1]["fim"], min(b, trechos[-1]["ini"] + 240))
            trechos[-1]["n"] += 1
            continue
        trechos.append({**h, "ini": a, "fim": min(b, h["duracao"] or b), "n": 1})
    por_canal, escolhidos = {}, []
    for t in sorted(trechos, key=lambda t: -t["n"]):  # mais falas do tema = momento mais "sobre" o tema
        if por_canal.get(t["canal"], 0) >= tema["por_canal"] or len(escolhidos) >= tema["max_trechos"]:
            continue
        por_canal[t["canal"]] = por_canal.get(t["canal"], 0) + 1
        escolhidos.append(t)
    return sorted(escolhidos, key=lambda t: (t["canal"], t["t"]))


# ---------------------------------------------------------------- 2) tradução
def traduzir(textos: list[str]) -> list[str] | None:
    if not textos or not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    import anthropic
    from gancho_ia import MODELO
    esquema = {"type": "object", "additionalProperties": False, "required": ["linhas"],
               "properties": {"linhas": {"type": "array", "items": {"type": "string"}}}}
    pedido = "\n".join(f"{k}: {t}" for k, t in enumerate(textos))
    try:
        r = anthropic.Anthropic(max_retries=2, timeout=90.0).messages.create(
            model=MODELO, max_tokens=8000,
            system=("Translate each numbered line of a Brazilian Portuguese live-stream transcript (automatic, may "
                    "have errors) into natural, casual English subtitles, keeping slang and swearing tone but "
                    "short. Return exactly one English line per input line, same order, without the numbers."),
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": esquema}},
            messages=[{"role": "user", "content": pedido}])
        linhas = json.loads(next(b.text for b in r.content if b.type == "text"))["linhas"]
    except Exception as e:
        log(f"tradução falhou: {str(e)[:150]}")
        return None
    return linhas if len(linhas) == len(textos) else None


# ---------------------------------------------------------------- 3) montagem
def _ass_longo(destino: Path, falas: list[tuple[float, float, str]], credito: str, dur: float) -> Path:
    def t(s: float) -> str:
        s = max(0.0, s)
        return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
    linhas = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "",
              "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
              "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
              "Alignment, MarginL, MarginR, MarginV, Encoding",
              "Style: Leg,Arial Black,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,"
              "120,120,70,1",
              "Style: Cred,Arial,34,&H00FFFFFF,&H00FFFFFF,&H70000000,&H70000000,-1,0,0,0,100,100,0,0,3,8,0,7,"
              "40,40,30,1", "",
              "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
              f"Dialogue: 1,{t(0)},{t(dur)},Cred,,0,0,0,,{credito}"]
    for a, b, tx in falas:
        tx = tx.replace("{", "").replace("}", "").replace("\\", "").strip()
        if tx and b - a > 0.2:
            linhas.append(f"Dialogue: 0,{t(a)},{t(b)},Leg,,0,0,0,,{tx}")
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8-sig")
    return destino


def _falas(tr: dict, segs: list[dict], ingles: bool) -> list[tuple[float, float, str]]:
    dentro = [s for s in segs if s["fim"] > tr["a_rel"] and s["ini"] < tr["b_rel"] and s["texto"].strip()]
    textos = [s["texto"].strip() for s in dentro]
    if ingles:
        en = traduzir(textos)
        if en is None:
            return []  # sem tradução: melhor sem legenda do que português num vídeo para gringo
        textos = en
    return [(max(0.0, s["ini"] - tr["a_rel"]), min(tr["b_rel"], s["fim"]) - tr["a_rel"], tx)
            for s, tx in zip(dentro, textos)]


def montar(nome: str, tema: dict, trechos: list[dict]) -> tuple[Path | None, Path | None, list[dict]]:
    pasta = montagem.pasta_do_dia()
    partes, usados, melhor = [], [], None
    for k, tr in enumerate(trechos):
        info = {"id": tr["id"], "webpage_url": tr["url"], "title": tr["titulo"]}
        try:
            trecho = fontes.baixar_trecho(info, tr["ini"], tr["fim"])
            segs = transcricao.transcrever(trecho)
        except Exception as e:
            log(f"trecho {k + 1} ({tr['canal']}) falhou: {str(e)[:150]}")
            continue
        tr = {**tr, "a_rel": 0.0, "b_rel": tr["fim"] - tr["ini"], "arquivo": trecho, "segs": segs}
        falas = _falas(tr, segs, tema["ingles"])
        dur = tr["b_rel"]
        cred = f"{tr['canal']} {tr['arroba']}".strip()
        ass = _ass_longo(pasta / f"comp_{nome}_{k:02d}.ass", falas, cred, dur)
        saida = pasta / f"comp_{nome}_{k:02d}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(trecho), "-t", f"{dur:.2f}", "-vf",
                        "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
                        f"setsar=1,fps=30,subtitles='{ass.name}'", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "20", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k", str(saida)],
                       check=True, cwd=str(pasta), capture_output=True)
        partes.append(saida)
        usados.append(tr)
        nota = transcricao.nota_reacao(segs, 0, dur) if segs else 0
        if melhor is None or nota > melhor[0]:
            melhor = (nota, tr, falas)
        log(f"trecho {k + 1}/{len(trechos)} pronto ({tr['canal']}, {dur:.0f} s)")
    if not partes:
        return None, None, []
    lista = pasta / f"comp_{nome}.txt"
    lista.write_text("".join(f"file '{p.name}'\n" for p in partes), encoding="utf-8")
    longo = pasta / f"comp_{nome}_LONGO.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista.name,
                    "-c", "copy", longo.name], check=True, cwd=str(pasta), capture_output=True)
    # SHORT: o melhor trecho, no formato normal do canal (até 30 s em volta da reação mais forte)
    short = None
    try:
        _, tr, falas = melhor
        segs = tr["segs"]
        jan = transcricao.janela_emocao(segs, tr["t"] - tr["ini"], 15, 30) if segs else None
        a, b, pico = jan if jan else (max(0.0, tr["t"] - tr["ini"] - 10), min(tr["b_rel"], tr["t"] - tr["ini"] + 15),
                                      tr["t"] - tr["ini"])
        if tema["ingles"]:  # palavras em inglês espalhadas no tempo de cada fala (a legenda segue a fala)
            palavras = []
            for fa, fb, tx in falas:
                ws = tx.split()
                for j, w in enumerate(ws):
                    palavras.append({"ini": fa + (fb - fa) * j / len(ws), "fim": fa + (fb - fa) * (j + 1) / len(ws),
                                     "p": w})
        else:
            palavras = [p for s in segs for p in s["palavras"]]
        short = pasta / f"comp_{nome}_SHORT.mp4"
        montagem.short(tr["arquivo"], a, b, palavras, tr["arroba"] or tr["canal"], 0.5, short,
                       gancho=tema["gancho_short"], pico=pico)
    except Exception as e:
        log(f"short falhou: {str(e)[:150]}")
        short = None
    return longo, short, usados


def publicar(nome: str, tema: dict, longo: Path, short: Path | None, usados: list[dict]) -> list[str]:
    if lg._cota_esgotada():
        log("cota do YouTube acabou hoje: fica para amanhã")
        return []
    creditos = "\n".join(sorted({f"▶ {t['canal']}: {t['canal_url']}" for t in usados}))
    originais = "\n".join(f"- {t['url']}" for t in usados)
    if tema["ingles"]:
        desc = (f"{tema['titulo']}\n\nAll clips with credit to the original creators (they authorize clips with "
                f"credit). Go watch them:\n{creditos}\n\nOriginal streams:\n{originais}\n\n#GTA6 #GTAVI")
    else:
        desc = (f"{tema['titulo']}\n\nCortes com crédito aos criadores originais. Siga:\n{creditos}\n\n"
                f"Lives originais:\n{originais}\n\n#GTA6 #cortes")
    urls = []
    for arq, titulo, eh_short in ((longo, tema["titulo"], False), (short, tema["titulo_short"], True)):
        if not arq or not arq.exists():
            continue
        try:
            u = youtube.enviar(arq, titulo, desc, tema["tags"], short=eh_short)
            urls.append(u)
            log(f"PUBLICADO ({'short' if eh_short else 'longo'}) {u} | {titulo}")
        except Exception as e:
            if "quotaExceeded" in str(e) or "uploadLimitExceeded" in str(e):
                lg._marcar_cota()
            log(f"publicação falhou: {str(e)[:200]}")
    return urls


def main() -> None:
    arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d  # noqa: E731
    nome, modo, dias = arg("--tema", "niko"), arg("--modo", "publicar"), int(arg("--dias", "10"))
    tema = TEMAS[nome]
    feitas = json.loads(FEITAS.read_text(encoding="utf-8")) if FEITAS.exists() else {}
    if modo == "publicar" and nome in feitas and "--forcar" not in sys.argv:
        log(f"'{nome}' já foi publicada em {feitas[nome]['quando']}: {feitas[nome]['urls']}")
        return
    prazo = time.time() + 3.2 * 3600  # deixa ~2 h para montar e publicar dentro das 6 h do GitHub
    salvo = DADOS / f"compilacao_{nome}.json"
    try:  # a busca é a parte demorada (horas de áudio): no "publicar" reaproveita uma busca de menos de 24 h
        d = json.loads(salvo.read_text(encoding="utf-8"))
        hits = d["hits"] if modo == "publicar" and time.time() - d["quando"] < 86400 else None
    except Exception:
        hits = None
    if hits is not None:
        log(f"'{nome}': usando a busca de {(time.time() - d['quando']) / 3600:.1f} h atrás ({len(hits)} falas)")
    else:
        hits = buscar(nome, tema, dias, prazo)
    trechos = escolher(tema, hits)
    log(f"'{nome}': {len(hits)} fala(s) achada(s), {len(trechos)} trecho(s) escolhido(s)")
    if modo != "publicar" or not trechos:
        return
    if nome == "finais" and not any(re.search(r"(?i)cr[ée]ditos|zer(ei|amos|ou)|final do jogo|acabou o jogo",
                                              t["texto"]) for t in trechos):
        log("'finais': ainda não achei o fim do jogo nas lives (ele não zerou?). Tento de novo depois.")
        return
    longo, short, usados = montar(nome, tema, trechos)
    if not longo:
        log(f"'{nome}': nenhum trecho deu certo para montar")
        return
    urls = publicar(nome, tema, longo, short, usados)
    if urls:
        feitas[nome] = {"quando": dt.datetime.now().isoformat(timespec="minutes"), "urls": urls}
        FEITAS.write_text(json.dumps(feitas, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
    lg.salvar_estado_na_nuvem()
