"""
Envoltorio del cliente de Ollama.

Temperatura 0, caché en disco (clave = sha256 del prompt) y los contadores
llm_calls / wall_clock_seconds que van en run_metadata del submission.json.

Modo "record": si el prompt no está en caché, llama a Ollama y guarda la
respuesta. Modo "replay": nunca llama a Ollama, solo lee el caché -> permite
reproducir una corrida con la conexión apagada.
"""
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_OLLAMA_URL = "http://localhost:11434"
TEMPERATURE = 0


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

    def chat(self, prompt, system=None):
        """Devuelve la respuesta de texto del modelo para `prompt`.

        Cuenta como una llamada (llm_calls += 1) tanto si viene de caché
        como si viene de Ollama, porque el número mide cuántas veces el
        agente le preguntó algo al modelo, no cuántas veces cruzó la red.
        """
        start = time.monotonic()
        key = self._cache_key(prompt, system)
        path = self._cache_path(key)

        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))["response"]

            if self.mode == "replay":
                raise CacheMiss(
                    f"modo replay sin conexión: no hay caché para este prompt (key={key})"
                )

            response = self._call_ollama(prompt, system)
            path.write_text(
                json.dumps({"response": response}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return response
        finally:
            self.llm_calls += 1
            self.wall_clock_seconds += time.monotonic() - start

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
