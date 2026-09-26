#!/bin/bash
# Sempre roda a partir da pasta onde este script está, independente de onde foi chamado
DIR_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR_SCRIPT" || exit 1

source venv/bin/activate

# Define o caminho da pasta a ser monitorada (mesmo padrão usado em analisar.py)
PASTA_MONITORADA="$HOME/Images/webcam"
mkdir -p "$PASTA_MONITORADA"

# Monitora movimentação de arquivos para a pasta (moved_to)
inotifywait -m -e moved_to --format '%f' "$PASTA_MONITORADA" | while read -r ARQUIVO; do
    # Evita executar ações para diretórios criados (opcional)
    if [ -f "$PASTA_MONITORADA/$ARQUIVO" ]; then
        echo "Novo arquivo detectado: $ARQUIVO"
        python3 analisar.py
    fi
done
