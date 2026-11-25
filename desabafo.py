"""DESABAFOS E HISTÓRIAS (25/11/2026).

Marco mostrou um short viral (1,46 mi de views, "Ele parou a gameplay só pra falar isso"): o Alanzoka para de
jogar e faz um desabafo de 59 s sobre GTA 6 (história com começo, meio e fim, sem grito nenhum). O robô só
achava picos de áudio (grito/risada) e o filtro de graça descartaria esse tipo de momento.

Aqui, a cada bloco de live: transcreve o bloco inteiro, a IA (sempre Claude Haiku 5.5, esforço baixo) garimpa
desabafos/opiniões fortes/polêmicas/histórias de 35-59 s com ideia completa e nota >= 7, e cada um vira um corte
com rosto em destaque, gancho no estilo "DESABAFO DO ALAN SOBRE GTA 6 (FIZERAM DE NOVO)" e título de
curiosidade. Esses cortes entram na fila com nota maior (saem antes das reações).

Sem chave da API ou com qualquer erro, o bloco segue só com os cortes de reação, como antes.
"""
from __future__ import annotations

import json
import os

from gancho_ia import ESFORCO, MODELO

NOTA_MINIMA = 7
MAX_POR_BLOCO = 2

SISTEMA_ACHAR = """Você garimpa cortes virais de lives para um canal brasileiro de cortes no YouTube Shorts.
Você recebe a transcrição automática (com tempos em segundos; pode ter erros) de até 1 hora de live de um
streamer jogando. Procure momentos em que ele PARA e fala algo que prende sozinho, mesmo para quem nunca viu a
live e nem está olhando o jogo: desabafo, opinião forte ou polêmica, história pessoal, revelação, comparação
marcante (ex.: dizer que GTA 6 é um mundo vivo como Red Dead Redemption 2), crítica, previsão, bastidor.

Regras:
- O momento precisa ter começo, meio e fim (uma ideia completa), entre 35 e 59 segundos.
- Comece no começo de uma frase que abre o assunto; termine depois que ele fecha a ideia (de preferência numa
  frase de efeito ou piada final). Use os tempos da transcrição.
- Ignore conversa à toa, leitura de chat sem graça, narração do que acontece no jogo e reação curta.
- Para cada momento devolva:
  inicio, fim (segundos);
  gancho: CAIXA ALTA, até 38 caracteres, o tipo do momento + o assunto (ex.: "DESABAFO DO ALAN SOBRE GTA 6",
  "ALAN REVELA O QUE ACHOU DE GTA 6");
  complemento: CAIXA ALTA, até 24 caracteres, uma provocação curta que vai entre parênteses
  (ex.: "FIZERAM DE NOVO", "ELE NÃO SEGUROU");
  titulo: até 70 caracteres, cria curiosidade sem entregar o que ele diz
  (ex.: "Ele parou a gameplay só pra falar isso"), sem hashtags;
  nota: 0 a 10, a chance de viralizar para quem nem conhece o streamer.
- Só afirme o que está na transcrição; sem palavrão e sem emoji no gancho/título.
- Devolva no máximo 3 momentos, os melhores; lista vazia se não houver nenhum bom."""

ESQUEMA_ACHAR = {
    "type": "object",
    "properties": {
        "momentos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "inicio": {"type": "number"},
                    "fim": {"type": "number"},
                    "gancho": {"type": "string"},
                    "complemento": {"type": "string"},
                    "titulo": {"type": "string"},
                    "nota": {"type": "number"},
                },
                "required": ["inicio", "fim", "gancho", "complemento", "titulo", "nota"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["momentos"],
    "additionalProperties": False,
}


def _limpa(s: str, n: int) -> str:
    s = " ".join(s.replace('"', "").replace("#", "").split()).strip(" .")
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0]


def transcrever_bloco(audio) -> list[dict]:
    """Transcrição rápida do bloco inteiro (sem tempo por palavra, beam 1): só para a IA achar os momentos."""
    from cortes import transcricao
    segs, _ = transcricao._modelo().transcribe(transcricao._audio_16k(audio), language="pt", beam_size=1,
                                               vad_filter=True, initial_prompt=transcricao.PROMPT_LIVE)
    return [{"ini": float(s.start), "fim": float(s.end), "texto": s.text.strip()} for s in segs if s.text.strip()]


def achar(segs: list[dict], nome: str, jogo: str) -> list[dict]:
    """Momentos de desabafo/história escolhidos pela IA (nota >= NOTA_MINIMA), já conferidos. Nunca levanta erro."""
    try:
        return _achar(segs, nome, jogo)
    except Exception as e:
        print(f"  desabafo IA falhou: {type(e).__name__}: {str(e)[:150]}", flush=True)
        return []


def _achar(segs, nome, jogo):
    if not os.environ.get("ANTHROPIC_API_KEY") or len(segs) < 10:
        return []
    import anthropic
    texto = "\n".join(f"[{s['ini']:7.1f} - {s['fim']:7.1f}] {s['texto']}" for s in segs)
    client = anthropic.Anthropic(max_retries=2, timeout=120.0)
    try:
        r = client.messages.create(
            model=MODELO, max_tokens=4000, system=SISTEMA_ACHAR,
            output_config={"effort": ESFORCO, "format": {"type": "json_schema", "schema": ESQUEMA_ACHAR}},
            messages=[{"role": "user", "content": f"Streamer: {nome}\nJogo: {jogo}\n\nTranscrição:\n{texto}"}],
        )
    except anthropic.APIError as e:
        print(f"  desabafo IA: erro da API: {str(e)[:150]}", flush=True)
        return []
    if r.stop_reason != "end_turn":
        return []
    achados = json.loads(next(b.text for b in r.content if b.type == "text"))["momentos"]
    bons = []
    for m in sorted(achados, key=lambda m: -m["nota"]):
        a = min((s["ini"] for s in segs), key=lambda x: abs(x - m["inicio"]))
        b = min((s["fim"] for s in segs), key=lambda x: abs(x - m["fim"])) + 0.6
        if m["nota"] < NOTA_MINIMA or not (30 <= b - a <= 60):
            continue
        if any(a < o["fim"] and b > o["inicio"] for o in bons):  # não repete o mesmo trecho
            continue
        gancho, compl = _limpa(m["gancho"], 40).upper(), _limpa(m["complemento"], 26).upper()
        bons.append({"inicio": a, "fim": b, "nota": float(m["nota"]), "titulo": _limpa(m["titulo"], 75),
                     "gancho": f"{gancho} ({compl})" if compl else gancho})
        if len(bons) >= MAX_POR_BLOCO:
            break
    return bons


def instalar_live(g: dict) -> None:
    """Troca processar_bloco do live_gta.py: antes dos cortes de reação, procura desabafos no bloco."""
    orig = g["processar_bloco"]

    def processar_bloco(live, ini, fim, publicar):
        feitos = 0
        try:
            feitos = _desabafos_do_bloco(g, live, ini, fim)
        except Exception as e:  # nunca atrapalha os cortes de reação
            g["log"](f"desabafos: erro {type(e).__name__}: {str(e)[:150]}")
        return feitos + orig(live, ini, fim, publicar)

    g["processar_bloco"] = processar_bloco


def _desabafos_do_bloco(g: dict, live: dict, ini: float, fim: float) -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return 0
    from cortes import fila, fontes, montagem, pipeline, transcricao
    log, canal = g["log"], g["CANAL"]
    audio = g["baixar_audio_bloco"](live["url"], live["chave"], ini, fim)  # fica guardado: o bloco normal reaproveita
    segs = transcrever_bloco(audio)
    achados = achar(segs, canal["nome"], "GTA 6")
    log(f"desabafos: {len(achados)} achado(s) no bloco")
    info = {"id": live["chave"], "webpage_url": live["url"], "title": live["titulo"]}
    pasta = montagem.pasta_do_dia()
    feitos = 0
    for m in achados:
        a, b = max(0.0, ini + m["inicio"] - 1.0), ini + m["fim"] + 1.0
        trecho = fontes.baixar_trecho(info, a, b)
        segs_t = transcricao.transcrever(trecho)  # tempo por palavra, para a legenda
        palavras = [p for s in segs_t for p in s["palavras"]]
        j_ini, j_fim = 1.0, min(b - a, m["fim"] - m["inicio"] + 1.0)
        saida = pasta / f"{live['chave']}_desabafo_{int(ini + m['inicio'])}.mp4"
        montagem.DESTAQUE_ROSTO = True
        try:
            montagem.short(trecho, j_ini, j_fim, palavras, canal["arroba"], canal["foco_x"], saida,
                           gancho=m["gancho"], pico=None)
        finally:
            montagem.DESTAQUE_ROSTO = False
        tag = canal["nome"].lower().replace(" ", "")
        desc = pipeline._descricao(canal["nome"], canal["arroba"], info, "GTA 6", canal["url_oficial"])
        item = fila.adicionar({
            "tipo": "short", "arquivo": str(saida), "canal": canal["nome"], "origem": live["url"],
            "canal_url": canal["url_oficial"], "titulo": f"{m['titulo']} #{tag} #gta6"[:95], "descricao": desc,
            "tags": [canal["nome"], "GTA 6", "GTA VI", f"{canal['nome']} GTA 6", "desabafo", "cortes"],
            "nota": round(1.5 + m["nota"] / 10, 3), "gancho": m["gancho"], "live_gta": True, "desabafo": True,
        }, aprovado=False)
        pipeline.guardar_trecho(item["id"], trecho, {"ini": j_ini, "fim": j_fim, "pico": None,
                                                     "arroba": canal["arroba"], "foco": canal["foco_x"],
                                                     "palavras": palavras, "frases": [s["texto"] for s in segs_t]})
        log(f"corte {item['id']} DESABAFO ({j_fim - j_ini:.0f}s, nota IA {m['nota']:.0f}) {item['titulo']} "
            f"| gancho: {m['gancho']}")
        feitos += 1
    return feitos
