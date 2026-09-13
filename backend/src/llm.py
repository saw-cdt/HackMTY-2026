"""
Envoltorio del cliente de Ollama.

Temperatura 0, caché en disco (clave = sha256 del prompt) y los contadores
llm_calls / wall_clock_seconds que van en run_metadata del submission.json.

Modo "record": si el prompt no está en caché, llama a Ollama y guarda la
respuesta. Modo "replay": nunca llama a Ollama, solo lee el caché -> permite
reproducir una corrida con la conexión apagada.

llm_calls / wall_clock_seconds solo se mueven en una llamada real a
Ollama: miden cuánto costó/tardó esta corrida en particular, y un
cache-hit es instantáneo y gratis, así que no cuenta. logical_calls es
distinto: cuenta CADA vez que el agente le pidió algo al modelo, venga
de la red o del caché -- mide el trabajo de la investigación, no el
costo de esta corrida. Correr la misma investigación dos veces (la
segunda toda en caché) da el mismo logical_calls ambas veces, aunque
llm_calls baje a 0 y wall_clock_seconds a ~0 en la segunda.
"""
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_OLLAMA_URL = "http://localhost:11434"
TEMPERATURE = 0

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class CacheMiss(Exception):
    """Modo replay: el prompt pedido no está en el caché."""


class LLMClient:
    def __init__(self, model, cache_dir, mode="record", ollama_url=None):
        if mode not in ("record", "replay"):
            raise ValueError(f"mode debe ser 'record' o 'replay', no {mode!r}")

        self.model = model
        self.mode = mode
        self.ollama_url = ollama_url or DEFAULT_OLLAMA_URL
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.llm_calls = 0
        self.wall_clock_seconds = 0.0
        self.logical_calls = 0

    def chat(self, prompt, system=None):
        """Devuelve la respuesta de texto del modelo para `prompt`.

        Un cache-hit no toca llm_calls ni wall_clock_seconds: esos
        contadores miden llamadas reales a Ollama. logical_calls SI se
        mueve siempre -- es el contador que se reporta como
        run_metadata.llm_calls en submission.json, precisamente para que
        no dependa de si el caché ya tenia la respuesta.
        """
        self.logical_calls += 1
        key = self._cache_key(prompt, system)
        path = self._cache_path(key)

        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))["response"]

        if self.mode == "replay":
            raise CacheMiss(
                f"modo replay sin conexión: no hay caché para este prompt (key={key})"
            )

        start = time.monotonic()
        response = self._call_ollama(prompt, system)
        elapsed = time.monotonic() - start

        self.llm_calls += 1
        self.wall_clock_seconds += elapsed

        path.write_text(
            json.dumps({"response": response}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return response

    def chat_json(self, prompt, system=None, max_retries=2):
        """Como chat(), pero parsea la respuesta como JSON.

        Si el modelo devuelve algo que no parsea (o lo envuelve en
        ```json ... ```), reintenta pidiéndole que corrija, hasta
        max_retries veces. Cada reintento es un prompt distinto (por eso
        cae en una entrada de caché distinta), así que si vuelve a fallar
        no se queda repitiendo la misma respuesta rota para siempre.
        """
        current_prompt = prompt
        last_error = None
        last_raw = None

        for attempt in range(max_retries + 1):
            raw = self.chat(current_prompt, system=system)
            last_raw = raw
            try:
                return json.loads(_extract_json(raw))
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                current_prompt = (
                    f"{prompt}\n\n"
                    f"Tu respuesta anterior no era JSON válido:\n{raw}\n\n"
                    "Responde ÚNICAMENTE con JSON válido, sin texto antes ni después."
                )

        raise ValueError(
            f"El modelo no devolvió JSON válido tras {max_retries + 1} intento(s): "
            f"{last_error}\nÚltima respuesta: {last_raw!r}"
        )

    def _cache_key(self, prompt, system):
        payload = json.dumps(
            {
                "model": self.model,
                "system": system,
                "prompt": prompt,
                "temperature": TEMPERATURE,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _cache_path(self, key):
        return self.cache_dir / f"{key}.json"

    def _call_ollama(self, prompt, system):
        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": TEMPERATURE},
        }
        if system:
            body["system"] = system

        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"No se pudo llamar a Ollama en {self.ollama_url}: {e}"
            ) from e
        return data["response"]


def _extract_json(text):
    """Quita fences de markdown y recorta texto sobrante antes/después
    del primer objeto o arreglo JSON, para tolerar respuestas como
    "Claro, aquí está: ```json {...} ```" en vez de JSON puro."""
    text = text.strip()
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()

    starts = [i for i, c in enumerate(text) if c in "{["]
    ends = [i for i, c in enumerate(text) if c in "}]"]
    if starts and ends and ends[-1] > starts[0]:
        return text[starts[0] : ends[-1] + 1]
    return text
