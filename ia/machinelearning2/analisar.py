"""Analisa a foto mais recente de uma pasta com DeepFace (idade, gênero, emoção, raça).

Uso:
    python analisar.py                      # usa a pasta padrão
    python analisar.py /outra/pasta         # outra pasta
    python analisar.py --acoes emotion age  # só algumas ações (menos RAM/CPU)
    python analisar.py --sem-janela         # só salva o resultado, sem abrir janela
    python analisar.py --forcar-cpu         # força execução em CPU para evitar crash de GPU
"""
import argparse
import os
import sys
from pathlib import Path

# --- CONTROLE DE RECURSOS (Mitigação de estresse no hardware) ---
# Limita o uso de threads para evitar que a CPU entre em pico máximo imediato
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["TF_NUM_INTRAOP_THREADS"] = "2"
os.environ["TF_NUM_INTEROP_THREADS"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import cv2

PASTA_PADRAO = str(Path.home() / "Images" / "webcam")
EXTENSOES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
TODAS_ACOES = ["age", "gender", "emotion", "race"]


def imagem_mais_recente(pasta: Path) -> Path | None:
    imagens = [f for f in pasta.iterdir() if f.is_file() and f.suffix.lower() in EXTENSOES]
    return max(imagens, key=lambda f: f.stat().st_mtime) if imagens else None


def desenhar(img, rosto, acoes):
    r = rosto["region"]
    x, y, w, h = r["x"], r["y"], r["w"], r["h"]
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    linhas = []
    if "age" in acoes and "age" in rosto:
        linhas.append(f"Age: {int(0.8*rosto['age'])}")
    if "gender" in acoes and "dominant_gender" in rosto:
        linhas.append(f"Gender: {rosto['dominant_gender']}")
    if "emotion" in acoes and "dominant_emotion" in rosto:
        linhas.append(f"Emotion: {rosto['dominant_emotion']}")
    if "race" in acoes and "dominant_race" in rosto:
        linhas.append(f"Race: {rosto['dominant_race']}")

    topo = y - 10 - (len(linhas) - 1) * 25
    pos_y0 = topo if topo > 15 else y + 25
    for i, linha in enumerate(linhas):
        cv2.putText(img, linha, (x, pos_y0 + i * 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta", nargs="?", default=PASTA_PADRAO)
    ap.add_argument("--acoes", nargs="+", default=TODAS_ACOES, choices=TODAS_ACOES)
    ap.add_argument("--sem-janela", action="store_true", help="não abre janela, só salva o PNG")
    ap.add_argument("--forcar-cpu", action="store_true", help="desativa GPU para evitar falhas de driver/alimentação")
    args = ap.parse_args()

    if args.forcar_cpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    # Importação diferida do DeepFace após configurar as variáveis de ambiente do TF
    from deepface import DeepFace

    pasta = Path(args.pasta)
    if not pasta.is_dir():
        sys.exit(f"Pasta não encontrada: {pasta}")

    caminho = imagem_mais_recente(pasta)
    if caminho is None:
        sys.exit(f"Nenhuma imagem encontrada em {pasta}")
    print(f"Analisando: {caminho}")

    img = cv2.imread(str(caminho))
    if img is None:
        sys.exit("Não consegui ler a imagem.")

    # Otimização: Redimensiona imagens muito grandes (ex: fotos de webcam HD/4K)
    # reduz a carga computacional no DeepFace mantendo precisão suficiente.
    altura, largura = img.shape[:2]
    max_dim = 1024
    if max(altura, largura) > max_dim:
        escala = max_dim / float(max(altura, largura))
        img_analise = cv2.resize(img, (int(largura * escala), int(altura * escala)))
    else:
        img_analise = img.copy()

    try:
        resultados = DeepFace.analyze(
            img_path=img_analise,
            actions=args.acoes,
            enforce_detection=False,
        )
    except Exception as e:
        sys.exit(f"Erro durante a análise com DeepFace: {e}")

    for rosto in resultados:
        desenhar(img_analise, rosto, args.acoes)

    saida = Path(__file__).with_name("resultado.png")
    cv2.imwrite(str(saida), img_analise)
    print(f"Resultado salvo em: {saida}")

    if not args.sem_janela:
        cv2.imshow("Resultado", img_analise)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
