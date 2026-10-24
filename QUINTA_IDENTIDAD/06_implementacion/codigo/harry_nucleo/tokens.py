"""Estimación de tokens sin tokenizador.

No hay un tokenizador de Qwen disponible sin instalar nada, así que la cuenta
es una estimación CONSERVADORA (tiende a sobrestimar):

    tokens(texto)    = ceil(caracteres / CARACTERES_POR_TOKEN)
    tokens(mensajes) = suma de tokens(contenido) + TOKENS_POR_MENSAJE por mensaje

Con 3.0 caracteres por token. En español, los tokenizadores BPE suelen dar
entre 3.5 y 4.5 caracteres por token. Los acentos, los emojis, los números
y las palabras raras bajan esa cifra, y por eso se usa 3.0. Los 6 tokens por
mensaje cubren las marcas de rol de la plantilla de chat.

Límites conocidos:
  - es una aproximación: puede sobrestimar entre 15 y 35 % en español común
    y subestimar en textos con muchos emojis o caracteres poco frecuentes;
  - no cuenta la plantilla exacta del modelo;
  - se calibra con datos reales: el adaptador de Ollama registra
    prompt_eval_count, y calibrar() compara la estimación con ese número.

Ambos parámetros se pueden cambiar por plataforma, en "contexto.estimacion".
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional

CARACTERES_POR_TOKEN = 3.0
TOKENS_POR_MENSAJE = 6


def estimar(texto: str, cpt: float = CARACTERES_POR_TOKEN) -> int:
    return int(math.ceil(len(texto) / cpt)) if texto else 0


def estimar_mensajes(mensajes: List[Dict[str, str]], cpt: float = CARACTERES_POR_TOKEN,
                     por_mensaje: int = TOKENS_POR_MENSAJE) -> int:
    return sum(estimar(m["content"], cpt) + por_mensaje for m in mensajes)


def calibrar(pares: Iterable[tuple]) -> Optional[float]:
    """pares: (caracteres_enviados, prompt_eval_count_real). Devuelve caracteres/token observado."""
    pares = [(c, t) for c, t in pares if c and t]
    if not pares:
        return None
    return round(sum(c for c, _ in pares) / sum(t for _, t in pares), 3)
