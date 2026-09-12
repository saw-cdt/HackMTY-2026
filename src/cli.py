"""Punto de entrada del pipeline. Recibe la ruta del estate en tiempo de
ejecución — rutas hardcodeadas fallan según las reglas del track.

El pipeline (investigador -> retador -> validador -> case file) se
conecta aquí conforme cada pieza (agent/, tools/, report/) esté lista.
"""
import argparse


def main():
    parser = argparse.ArgumentParser(description="The Forensic Auditor")
    parser.add_argument("--estate", required=True, help="ruta al estate .db")
    parser.add_argument("--out", default="out", help="directorio de salida")
    args = parser.parse_args()
    raise NotImplementedError("pipeline pendiente: agent/, tools/, report/")


if __name__ == "__main__":
    main()
