"""Login do canal de cortes COM a permissão de estatísticas (retenção / % assistido).

Como usar (no PC, uma vez só):
  1. Baixe este arquivo para uma pasta e coloque junto o client_secret.json (o mesmo do login antigo;
     no projeto do PC ele fica em dados/client_secret.json).
  2. No terminal, nessa pasta:   pip install google-auth-oauthlib google-api-python-client
                                 python login_youtube.py
  3. Abre o navegador: escolha o canal de CORTES (@clipesyoutubersbr) e autorize tudo.
  4. Ele cria o arquivo token_youtube_novo.json. Abra no Bloco de Notas, copie TUDO e cole no segredo YT_TOKEN
     do GitHub (repositório -> Settings -> Secrets and variables -> Actions -> YT_TOKEN -> Update).
  5. Apague o token_youtube_novo.json do PC depois (é uma senha).
"""
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

ESCOPOS = ["https://www.googleapis.com/auth/youtube.upload",
           "https://www.googleapis.com/auth/youtube.readonly",
           "https://www.googleapis.com/auth/youtube.force-ssl",
           "https://www.googleapis.com/auth/yt-analytics.readonly"]  # novo: retenção / % assistido
CANAL_CORTES = "UCS7cQkm3pbnjZDS9CMzjTCg"  # @clipesyoutubersbr

segredo = next((p for p in (Path("client_secret.json"), Path("dados/client_secret.json")) if p.exists()), None)
if not segredo:
    sys.exit("Não achei o client_secret.json nesta pasta (nem em dados/).")
creds = InstalledAppFlow.from_client_secrets_file(str(segredo), ESCOPOS).run_local_server(port=0, prompt="consent")

from googleapiclient.discovery import build  # noqa: E402

canal = build("youtube", "v3", credentials=creds).channels().list(part="snippet", mine=True).execute()["items"][0]
if canal["id"] != CANAL_CORTES:
    sys.exit(f"Você escolheu o canal ERRADO ({canal['snippet']['title']}). Rode de novo e escolha @clipesyoutubersbr.")
Path("token_youtube_novo.json").write_text(creds.to_json(), encoding="utf-8")
print(f"OK, canal {canal['snippet']['title']}. Agora copie o conteúdo de token_youtube_novo.json para o segredo YT_TOKEN.")
