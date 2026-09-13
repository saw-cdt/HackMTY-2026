# Guía de usuario — The Forensic Auditor (interfaz)

Esta guía explica cómo arrancar y recorrer la interfaz que muestra el
expediente de fraude fiscal. Todo funciona sin backend y sin internet:
el `.db` (estate) y el `submission.json` (informe) se cargan en el
navegador.

---

## 1. Dónde está el proyecto

| Qué | Ruta |
|---|---|
| Repositorio completo | `HackMTY-2026/` |
| Interfaz (frontend) | `HackMTY-2026/frontend/` |
| Archivos de demo | `frontend/public/demo/` |

La interfaz está dentro de la carpeta `frontend/` del repositorio.

---

## 2. Requisitos

- Node.js 18 o superior (con `npm`).
- Un navegador moderno (Chrome, Edge, Firefox, Safari).

---

## 3. Arrancar la interfaz

Abre una terminal y ejecuta:

```
cd HackMTY-2026/frontend
npm install
npm run dev
```

Cuando aparezca el mensaje tipo:

```
➜  Local:   http://localhost:5173/
```

abre esa dirección en el navegador. Eso es todo.

> Nota: `npm install` solo se necesita la primera vez.

---

## 4. Recorrido de la interfaz

### Pantalla de inicio

Al entrar verás la portada con la frase
«Ningún hallazgo se imprime sin haber sido atacado», el esquema de las
tres capas (Investigador → Retador → Validador) y una zona para soltar
archivos.

La forma más rápida de ver todo es pulsar el botón **«Cargar demo»**
(carga un estate real más su informe). Si no hay nada cargado, hazlo:

1. Pulsa **«Cargar demo»** (o arrastra los archivos a la zona de soltar).
2. La app pasa automáticamente a la pestaña **Resumen**.

### Pestañas

Arriba hay 7 pestañas numeradas. Este es el orden del guion del demo:

| # | Pestaña | Qué vas a ver |
|---|---|---|
| 01 | **Resumen** | La empresa auditada (RFC HJD1210074J1), periodo, seed, los tres números (`llm_calls`, `mxn_cost`, `wall_clock_seconds`), y la exposición en pesos con la reconciliación al 2 % |
| 02 | **Hallazgos** | Una tarjeta por esquema detectado: regla rota, narrative, lo que argumentó el retador, el trail del dinero, la tabla de exhibits y el sello del validador |
| 03 | **Contraste** | El hallazgo acusado junto a un lead descartado, con las mismas filas alineadas: entidad, señal, documentos, monto, historia, ataque y quién lo cerró |
| 04 | **Leads** | Los descartados con su señal y la razón específica (cada uno tiene su `why_innocent`) |
| 05 | **Grafo** | El money trail que se construye **solo**, en 6 pasos: todo gris → los descartados se atenúan → los señalados se colorean → salen las flechas → convergen → desenlace con el % de retorno |
| 06 | **Estate** | El `.db` inspeccionado: las 8 tablas, el listado de proveedores con su estatus 69-B |
| 07 | **Resultados** | Las cargas acumuladas contra el ground truth de los seeds 1–10 |

### El grafo (plato fuerte)

En la pestaña **Grafo**:

- Elige el hallazgo a animar con las cápsulas de color de arriba.
- El grafo se reproduce automáticamente en 6 pasos (1.5 s por paso).
- Usa **Reproducir / Pausa / Paso / Reiniciar** para controlarlo.
- El marcador 📊 devuelve el **% de retorno** al CLABE de la empresa.
- Cada arista muestra el monto; los nodos con el mismo CLABE comparten posición (el dinero «pasa por» la misma cuenta).

---

## 5. Qué más puedes hacer

### Soltar archivos manualmente

En la pantalla de inicio o sobre la cabecera:

- **`submission.json`** → carga un informe (extensión `.json`).
- **`estate_seedNNN.db`** → abre el estate (extensión `.db` — funciona con
  los estates que genera el backend).

Cuando cargas un `.db`, el grafo resuelve los CLABEs con los nombres
reales de proveedores y empleados, y la pestaña Estate muestra las
8 tablas. Además verifica que cada exhibit citado exista de verdad en la
base.

### Cargar varios informes

Puedes cargar `submission_seed001.json`, `submission_seed002.json`, etc.,
uno tras otro. La pestaña **Resultados** acumula todos y los compara con
el ground truth de los seeds **001–010**.

---

## 6. Solución de problemas

| Problema | Solución |
|---|---|
| `npm install` da errores de espacio | Libera espacio en disco (la máquina está casi llena) y reintenta |
| El puerto `5173` está ocupado | `npm run dev -- --port 5174` y abre esa dirección |
| «No pude abrir el estate» | Verifica que el archivo termine en `.db` y sea un SQLite válido (los que produce `backend/src/generate/estate.py`) |
| Todo gris en el Grafo | El hallazgo no tiene `money_trail` en el informe; revisa la pestaña Hallazgos |
| Ventana minimizada o pantalla oscura | Dale scroll; el tema es oscuro por diseño (dossier forense) |

---

## 7. Producción (opcional)

Para generar una versión estática que se pueda enviar o hostear:

```
cd HackMTY-2026/frontend
npm run build
npm run preview
```

El resultado queda en `frontend/dist/` y se abre en `localhost:4173`.