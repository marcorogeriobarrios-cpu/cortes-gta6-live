"""Gancho (texto da tela) e título do corte escritos por IA (25/11/2026).

Marco: o gancho tem que dizer o ASSUNTO do corte ("ALANZOKA REAGE AO GTA 6 A 60 FPS"), escolhendo o que ele
falou de mais polêmico / mais novo, e não uma frase solta. A IA lê a transcrição do corte e escreve gancho e
título. Sempre o Claude Haiku 5.5 com esforço baixo (o mais leve e barato, ~US$ 1/mês), pedido do Marco.

Só roda com o segredo ANTHROPIC_API_KEY. Sem a chave, sem a biblioteca, com erro ou recusa da IA, o robô usa
o gancho antigo (a frase dita no corte) — nunca trava um corte por causa disso.
"""
from __future__ import annotations

import json
import os

MODELO = "claude-haiku-5-5"  # SEMPRE o Haiku (leve); não trocar sem o Marco pedir
ESFORCO = "low"

SISTEMA = """Você escreve a capa de cortes (YouTube Shorts) de um canal brasileiro de cortes de streamers.
Você recebe a transcrição automática de um corte de live (a fala do streamer, com o tempo em segundos; pode ter
erros de transcrição) e devolve:

- gancho: o texto que fica na tela o vídeo todo. CAIXA ALTA, no máximo 45 caracteres. Tem que dizer do que se
  trata o corte, como fazem os canais de corte grandes: o streamer + a situação. Exemplos do formato:
  "ALANZOKA REAGE AO GTA 6 A 60 FPS", "ALANZOKA É PERSEGUIDO PELA POLÍCIA EM VICE CITY",
  "ALANZOKA DESCOBRE QUE DÁ PRA RESTAURAR CARRO". Escolha o assunto mais chamativo do trecho: o mais polêmico,
  o mais novo, o mais surpreendente ou o mais engraçado. Nunca uma frase solta de conversa.
- titulo: o título do YouTube, no máximo 70 caracteres, a situação em CAIXA ALTA, no mesmo espírito do gancho
  mas com outras palavras; pode terminar com KKKK se ele riu de verdade no trecho.

Regras: só afirme o que está na transcrição (não invente mortes, brigas, valores, nomes ou acontecimentos);
sem palavrão; sem emoji; sem aspas; sem hashtags (elas são colocadas depois)."""

ESQUEMA = {
    "type": "object",
    "properties": {
        "gancho": {"type": "string"},
        "titulo": {"type": "string"},
    },
    "required": ["gancho", "titulo"],
    "additionalProperties": False,
}


def _transcricao(segs: list[dict], ini: float, fim: float) -> str:
    linhas = [f"[{max(0.0, s['ini'] - ini):5.1f}s] {s['texto'].strip()}" for s in segs
              if s["fim"] > ini and s["ini"] < fim and s["texto"].strip()]
    return "\n".join(linhas)


def gerar(segs: list[dict], ini: float, fim: float, nome: str, jogo: str) -> tuple[str, str] | None:
    """(gancho, titulo) escritos pela IA, ou None (sem chave, erro ou resposta ruim). Nunca levanta erro."""
    try:
        return _gerar(segs, ini, fim, nome, jogo)
    except Exception as e:  # qualquer surpresa (versão da biblioteca etc.): fica o gancho antigo
        print(f"  gancho IA falhou: {type(e).__name__}: {str(e)[:150]}", flush=True)
        return None


def _gerar(segs: list[dict], ini: float, fim: float, nome: str, jogo: str) -> tuple[str, str] | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    texto = _transcricao(segs, ini, fim)
    if len(texto.split()) < 8:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic(max_retries=2, timeout=60.0)
        r = client.messages.create(
            model=MODELO,
            max_tokens=4000,
            system=SISTEMA,
            output_config={"effort": ESFORCO, "format": {"type": "json_schema", "schema": ESQUEMA}},
            messages=[{"role": "user", "content": f"Streamer: {nome}\nJogo: {jogo}\n\n"
                                                  f"Transcrição do corte:\n{texto}"}],
        )
    except anthropic.RateLimitError:
        print("  gancho IA: limite de uso da API, usando o gancho antigo", flush=True)
        return None
    except anthropic.APIStatusError as e:
        print(f"  gancho IA: erro {e.status_code} da API: {str(e.message)[:150]}", flush=True)
        return None
    except anthropic.APIConnectionError:
        print("  gancho IA: sem conexão com a API, usando o gancho antigo", flush=True)
        return None
    if r.stop_reason != "end_turn":  # recusa ou corte no meio: fica com o gancho antigo
        print(f"  gancho IA: parou com {r.stop_reason}, usando o gancho antigo", flush=True)
        return None
    try:
        d = json.loads(next(b.text for b in r.content if b.type == "text"))
    except (StopIteration, ValueError):
        return None
    gancho = " ".join(d["gancho"].replace('"', "").split()).upper().strip(" .")
    titulo = " ".join(d["titulo"].replace('"', "").replace("#", "").split()).strip()
    if len(gancho) < 8 or len(titulo) < 8:
        return None
    if len(gancho) > 48:
        gancho = gancho[:48].rsplit(" ", 1)[0]
    if len(titulo) > 75:
        titulo = titulo[:75].rsplit(" ", 1)[0]
    print(f"  gancho IA: {gancho} | título: {titulo}", flush=True)
    return gancho, titulo


def instalar_live(g: dict) -> None:
    """Troca gancho_gta/titulo_gta do live_gta.py (chamar com globals() no fim do arquivo)."""
    orig_gancho, orig_titulo = g["gancho_gta"], g["titulo_gta"]
    ultimo: dict = {}

    def gancho_gta(segs, j_ini, j_fim, pico):
        r = gerar(segs, j_ini, j_fim, g["CANAL"]["nome"], "GTA 6")
        if r:
            ultimo["par"] = r
            return r[0]
        ultimo.clear()
        return orig_gancho(segs, j_ini, j_fim, pico)

    def titulo_gta(segs, pico, gancho):
        if ultimo.get("par") and ultimo["par"][0] == gancho:
            tag = g["CANAL"]["nome"].lower().replace(" ", "")
            return f"{ultimo['par'][1]} #{tag} #gta6"[:95]
        return orig_titulo(segs, pico, gancho)

    g["gancho_gta"], g["titulo_gta"] = gancho_gta, titulo_gta


def instalar_pipeline(g: dict) -> None:
    """Troca _titulo do cortes/pipeline.py (o gancho é a parte antes do " | ")."""
    orig = g["_titulo"]

    def _titulo(segs, pico, nome, jogo):
        r = gerar(segs, pico - 25, pico + 20, nome, jogo or "")
        if not r:
            return orig(segs, pico, nome, jogo)
        sufixo = f" | {nome}" + (f" {jogo.title()}" if jogo and len(nome) + len(jogo) < 40 else "")
        return (r[0] + sufixo)[:100]

    g["_titulo"] = _titulo
