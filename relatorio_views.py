"""Relatório de visualizações do canal de cortes (só LEITURA da API do YouTube, gasta poucos pontos de cota).

Junta as estatísticas de cada vídeo com o que o robô registrou no dados/live_gta.log (gancho, duração, nota,
tipo) e grava dados/relatorio_views.json e dados/relatorio_views.md.
Roda pelo workflow "Relatório de visualizações" (usa o segredo YT_TOKEN).
"""
import json
import os
import re
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

DADOS = Path("dados")
info = json.loads(os.environ["YT_TOKEN"])
creds = Credentials.from_authorized_user_info(info, info.get("scopes"))
yt = build("youtube", "v3", credentials=creds, cache_discovery=False)

canal = yt.channels().list(part="contentDetails,statistics,snippet", mine=True).execute()["items"][0]
uploads = canal["contentDetails"]["relatedPlaylists"]["uploads"]
ids, token = [], None
while len(ids) < 500:
    r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
    ids += [i["contentDetails"]["videoId"] for i in r["items"]]
    token = r.get("nextPageToken")
    if not token:
        break

videos = []
for k in range(0, len(ids), 50):
    r = yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50])).execute()
    for v in r["items"]:
        d = v["contentDetails"]["duration"]
        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d)
        seg = sum(int(x or 0) * f for x, f in zip(m.groups(), (3600, 60, 1))) if m else 0
        st = v["statistics"]
        videos.append({"id": v["id"], "titulo": v["snippet"]["title"], "publicado": v["snippet"]["publishedAt"],
                       "duracao": seg, "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
                       "comentarios": int(st.get("commentCount", 0))})

# o que o robô sabe de cada vídeo (pelo log): linha "corte ..." seguida de "PUBLICADO ... <url>"
log = (DADOS / "live_gta.log").read_text(encoding="utf-8", errors="replace").splitlines() if (DADOS / "live_gta.log").exists() else []
extra, ultimo = {}, None
for ln in log:
    if re.search(r"\bcorte [0-9a-f]{8}\b", ln):
        ultimo = ln
    m = re.search(r"PUBLICADO.*?youtube\.com/shorts/([\w-]{11})", ln)
    if m and ultimo:
        g = re.search(r"gancho: (.*)$", ultimo)
        n = re.search(r"nota(?: IA)? ([\d.]+)", ultimo)
        extra[m.group(1)] = {"gancho": g.group(1) if g else "", "nota": float(n.group(1)) if n else None,
                             "desabafo": "DESABAFO" in ultimo, "linha": ultimo[:300]}
        ultimo = None
for v in videos:
    v.update(extra.get(v["id"], {}))

videos.sort(key=lambda v: -v["views"])
(DADOS / "relatorio_views.json").write_text(json.dumps({"canal": canal["statistics"], "videos": videos},
                                                       ensure_ascii=False, indent=1), encoding="utf-8")
linhas = [f"# Visualizações ({len(videos)} vídeos) — inscritos: {canal['statistics'].get('subscriberCount')}", "",
          "| views | likes | coment. | dur | publicado | título | gancho |", "|---|---|---|---|---|---|---|"]
for v in videos:
    linhas.append(f"| {v['views']} | {v['likes']} | {v['comentarios']} | {v['duracao']}s | {v['publicado'][:16]} | "
                  f"{v['titulo'][:70]} | {v.get('gancho', '')[:50]} |")
(DADOS / "relatorio_views.md").write_text("\n".join(linhas), encoding="utf-8")
print(f"{len(videos)} vídeos; top: {[(v['views'], v['titulo'][:40]) for v in videos[:5]]}")
