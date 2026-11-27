# ---------------- viral_diario.py (27/11/2026) ----------------
# Inserido pelo ajustes.py no diario.py, antes do `if __name__ == "__main__":`.
# Marco: "faça todos" (o que falta para viralizar):
#  a) CHEGAR ANTES: fora do horário (5h-17h59) pode sair até 2 cortes MUITO fortes em 18 h (_muito_forte, usado
#     pelo _pode_publicar_agora).
#  b) VARIAR: depois de 2 do Alanzoka seguidos, sai 1 de outro canal (se houver um bom pronto); e a produção
#     alterna entre o GTA do Alanzoka e os outros canais autorizados do canais.yaml.


def _muito_forte(i: dict) -> bool:
    """Corte acima do normal (cada fonte tem a sua escala de nota)."""
    n = i.get("nota", 0)
    if i.get("desabafo"):
        return n >= 2.3  # a IA deu 8+ de 10
    if i.get("live_gta"):
        return n >= 0.96  # reação muito forte
    return n >= 0.6


_publicar_um_original = publicar_um
_prontos_original = prontos


def publicar_um() -> bool:  # noqa: F811
    itens = sorted(_prontos_original(), key=lambda i: -i.get("nota", 0))
    try:
        ult = [ln for ln in lg.LOG.read_text(encoding="utf-8").splitlines() if "PUBLICADO (1/h)" in ln][-2:]
    except Exception:
        ult = []
    outros = [i for i in itens if i.get("canal") != "Alanzoka" and i.get("nota", 0) >= 0.45]
    if (len(ult) == 2 and all("Alanzoka:" in ln for ln in ult) and outros
            and not (itens and _muito_forte(itens[0]))):
        global prontos
        prontos = lambda: outros  # noqa: E731  (só durante esta publicação)
        try:
            return _publicar_um_original()
        finally:
            prontos = _prontos_original
    return _publicar_um_original()


_produzir_original = produzir
_VEZ = {"outros": True}


def produzir() -> bool:  # noqa: F811
    """Alterna: uma vez o GTA do Alanzoka, outra vez os outros canais autorizados."""
    _VEZ["outros"] = not _VEZ["outros"]
    if _VEZ["outros"]:
        antes = {i["id"] for i in fila.todos()}
        for canal in config()["canais"]:
            if not canal.get("autorizado", True) or canal["nome"] in FALHOS or canal["nome"] == "Alanzoka":
                continue
            try:
                novos = fontes.recentes(canal)
            except Exception as e:
                lg.log(f"diário: [{canal['nome']}] erro ao listar: {str(e)[:150]}")
                FALHOS.add(canal["nome"])
                continue
            for info in novos[:1]:
                lg.log(f"diário: [{canal['nome']}] cortando '{(info.get('title') or '')[:80]}'")
                try:
                    pipeline.processar_video(canal, info, fazer_longo=False)
                except Exception as e:
                    lg.log(f"diário: [{canal['nome']}] erro: {str(e)[:200]}")
                    fontes.marcar_visto(info["id"])
                    fontes.limpar(info)
                lg.log(f"diário: {_aprovar_novos(antes)} corte(s) prontos")
                return True
            FALHOS.add(canal["nome"])
    return _produzir_original()


