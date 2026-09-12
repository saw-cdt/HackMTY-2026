# The Forensic Auditor — HackMTY 2026 (Infosys)

Agente que investiga fraude de facturación (EFOS/EDOS) en México y entrega
tres veredictos accionables — **DEFENDIBLE / CORREGIR / ACUSACIÓN** — probados
con el flujo del dinero, no con un score.

## Estado actual

Prototipo de la pieza de datos (Rol A) + parte de las herramientas (Rol B):

- `backend/generate/schema.sql` — el contrato de datos (9 tablas) en Postgres
- `backend/generate/generate_data.py` — genera un SQLite de prueba con los 4
  tipos de proveedor obligatorios (legítimo, desordenado, simulador, recíproco)
- `backend/ingest/ingest_69b.py` — parser del listado 69-B del SAT (formato
  ancho -> tabla larga `efos_evento`)
- `backend/tools/tools.py` — las 7 herramientas del agente + el gate de
  veredicto, verificado end-to-end contra los 4 arquetipos sembrados

## Pendiente (ver checklist del equipo)

- Ingesta real de AMLSim
- Loop del agente con modelo (LLM decidiendo a quién investigar)
- Persistencia del razonamiento + case file + JSON de salida
- Frontend: drop de archivo, grafo, vista comparativa

## Cómo correr el prototipo

```bash
cd backend/generate
python3 generate_data.py        # crea forensic_auditor.db con los 4 arquetipos

cd ../tools
cp ../generate/forensic_auditor.db .
python3 tools.py                # corre el loop + gate, imprime los 4 veredictos
```

## La apuesta

> Tres veredictos accionables, probados con el flujo del dinero, medidos con
> ground truth. Si una tarea no sirve a esa frase, se corta.
