"""Ajustes no código da nuvem (rodar logo depois de desempacotar o pacote.b64).

24/11/2026:
  1) RITMO: o robô diário postava 1 por hora (até 71 num dia) e o alcance caiu para 1-19 views por vídeo;
     dias com 2 a 9 shorts tiveram ~1.000-1.500. Agora: no máximo 4 por dia, a cada 3 h, das 11h às 22h59.
  2) PERSONAGEM CENTRALIZADO: com câmera no canto, o jogo de baixo era recortado só do lado sem câmera e o
     personagem (3ª pessoa, no meio da tela) saía deslocado. Agora recorta pelo centro e borra a câmera.
Se o código mudar e algum ajuste não encaixar, falha de propósito (melhor parar do que voltar a 1/h).
"""
from pathlib import Path

TROCAS = {
 "diario.py": [
  [
   "INTERVALO = 3600\n",
   "INTERVALO = 3 * 3600  # ajustes.py\n"
  ],
  [
   "FILA_MIN = 3\n",
   "FILA_MIN = 3\n\nMAX_POR_DIA = 4  # ajustes.py\n\n\ndef _pode_publicar_agora() -> bool:\n    agora = dt.datetime.now(BRT)\n    if not (11 <= agora.hour < 23):\n        return False\n    hoje = agora.strftime('%d/%m')\n    try:\n        linhas = lg.LOG.read_text(encoding='utf-8').splitlines()\n    except Exception:\n        linhas = []\n    return sum(1 for l in linhas if l.startswith(hoje) and 'PUBLICADO' in l) < MAX_POR_DIA\n"
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
  ]
 ]
}

for arquivo, lista in TROCAS.items():
    p = Path(arquivo)
    cod = p.read_text(encoding="utf-8")
    for velho, novo in lista:
        if velho not in cod:
            raise SystemExit(f"ajustes.py: não achei o trecho em {arquivo}: {velho[:70]!r}")
        cod = cod.replace(velho, novo, 1)
    p.write_text(cod, encoding="utf-8")
print("ajustes aplicados: ritmo 4 por dia (3 h, 11h-22h59) e personagem centralizado")
