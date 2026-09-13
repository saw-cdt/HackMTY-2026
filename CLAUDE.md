# Plan de trabajo con Claude Code

*The Forensic Auditor — HackMTY 2026*

Una tarea a la vez. Cada paso trae el prompt para copiar y cómo verificar que quedó bien antes de seguir.

Si un paso no verifica, no avances. Arréglalo ahí.

---

## Documentación de referencia

Este archivo es solo el plan de ejecución. **El resto del contexto del proyecto —y las bases para construir el frontend— está en `docs/`.** Antes de escribir código, y sobre todo antes de tocar la Fase 7, hay que leerlos.

| Documento | Qué contiene |
|---|---|
| [`docs/Arquitectura_v2_Forensic_Auditor.md`](docs/Arquitectura_v2_Forensic_Auditor.md) | **Arquitectura vigente.** Las secciones 3, 4 y 6 que se citan en los pasos de abajo se refieren a este documento |
| [`docs/Planeacion_v2_Forensic_Auditor.md`](docs/Planeacion_v2_Forensic_Auditor.md) | **Planeación vigente:** alcance, fases, guion del demo y criterios de corte |
| [`docs/Investigacion_Forensic_Auditor_HackMTY2026.md`](docs/Investigacion_Forensic_Auditor_HackMTY2026.md) | Investigación de fondo: el problema, el artículo 69-B, los tipos de fraude y el glosario. Sigue vigente completa |
| [`docs/Arquitectura_Forensic_Auditor_HackMTY2026.md`](docs/Arquitectura_Forensic_Auditor_HackMTY2026.md) | Arquitectura v1. Superada en el contrato de datos, pero **sigue siendo la única fuente de varios temas** (ver abajo) |
| [`docs/Planeacion_Forensic_Auditor_HackMTY2026.md`](docs/Planeacion_Forensic_Auditor_HackMTY2026.md) | Planeación v1. Igual: superada en alcance, pero **única fuente del guion del demo y de las reglas de equipo** |

### Cómo se leen juntas

**La v2 manda donde ambas hablan del mismo tema. La v1 sigue valiendo donde la v2 no dice nada.** Las v2 se escribieron como un delta sobre el material oficial de los organizadores, no como un reemplazo completo: dan por hecho lo que ya estaba decidido y no lo repiten.

Lo que **solo existe en la v1** y sigue aplicando:

| Tema | Dónde | Por qué importa |
|---|---|---|
| La secuencia del grafo, paso 1 a 6 | Arquitectura v1 §5 | Es la coreografía del grafo progresivo. La v2 pide «grafo progresivo» pero no dice cómo |
| Restricciones de la visualización | Arquitectura v1 §5 | Posiciones fijas, sin zoom, máx. 12-15 nodos, sin partículas. Reglas duras para el frontend |
| El campo `paso` para animar sin streaming | Arquitectura v1 §5 | Decide la arquitectura del frontend: recibe todo y revela con retardo, en vez de abrir un canal en vivo |
| El guion literal del pitch, 0:00 a 3:00 | Planeación v1 §2 | La v2 solo trae la tabla de los dos carriles; el texto a decir está aquí |
| El plan B y su umbral de 90 segundos | Planeación v1 §2 | Cómo se anuncia y cuándo cambia el operador, sin consultar |
| La pregunta sorpresa del jurado | Planeación v1 §2 | «¿Por qué no acusaste a ese?» y cómo se contesta desde el registro |
| Presupuesto de latencia y elección de modelo | Arquitectura v1 §4 | Cómo medir y a qué modelo bajarse si no cabe |
| Variables de entorno, reglas de equipo, sueño | Arquitectura v1 §6, Planeación v1 §4 | Coordinación, ramas, integración temprana |

Lo que la v2 **sí reemplazó** y no debe tomarse de la v1: las 9 tablas en español, PostgreSQL, los tres veredictos (DEFENDIBLE / CORREGIR / ACUSACIÓN), el gate de veredicto, el contrato de salida JSON viejo, AMLSim, y los cuatro estatus del 69-B como diferenciador.

Notas prácticas:

- Los materiales oficiales de los organizadores ya están en el repo, en `backend/`: `src/generate/schema.sql` (era `estate_schema.sql`, copiado tal cual — nombre de archivo distinto, columnas idénticas), `validate_format.py`, `submission_schema.json`, `ground_truth_schema.json`, `case_file_structure.md`, y su `OFFICIAL_SPEC_README.md` (renombrado para no chocar con el README del proyecto). También `submission_example.json` y `results_table_template.csv`, que no estaban en esta lista pero son del mismo paquete oficial.
- El diseño descrito en esos documentos está cerrado. No se proponen cambios.

---

## Reglas permanentes

Estas se le dicen una vez al inicio y se repiten si se desvía:

- No propone cambios al diseño. Está cerrado.
- Los nombres de columna de estate_schema.sql no se renombran ni se traducen.
- La palabra ground_truth solo puede aparecer en src/generate/ y eval/. Nunca en src/tools/ ni src/agent/.
- El modelo nunca calcula montos ni decide si un hallazgo se publica.
- Los prompts al modelo piden JSON corto de 2 o 3 campos. La única excepción es el narrative, bajo 150 palabras.
- Rutas del estate por argumento. Nada hardcodeado.

---

## Estado actual

*Última actualización: 2026-09-12 (tarde). Si retomas después de que se
llenó la ventana de contexto o se compactó la conversación, lee esto
primero — te ahorra rehacer trabajo ya hecho y verificado.*

**Todo el código vive bajo `backend/`, no en la raíz del repo.** Cuando
un paso de abajo dice `src/algo.py` o `eval/algo.py`, en realidad es
`backend/src/algo.py` / `backend/eval/algo.py`. Es una decisión
deliberada (se pidió así para separar visualmente back de front), no un
error ni un desvío por corregir. El `Makefile` y `validate_format.py`
también están en `backend/`, no en la raíz.

Progreso, paso por paso:

- [x] **Paso 0**
- [x] **Paso 1.1** — `backend/src/llm.py`.
- [x] **Paso 1.2** — estructura completa + `backend/src/generate/schema.sql` + `backend/Makefile` (`check-format`, `check-isolation`).
- [x] **Paso 2.1** — `backend/src/generate/estate.py`: las 8 tablas limpias.
- [x] **Paso 2.2** — `backend/src/generate/schemes.py`: los 5 esquemas **y también los 5 decoys** (se adelantaron aquí en vez de en 2.3, porque `ground_truth_schema.json` los pide juntos en el mismo archivo).
- [x] **Paso 2.3** — lo único que faltaba tras el 2.2 era permitir seeds con `schemes: []`; ya está.
- [x] **Fase 3** — `backend/src/tools/{db,detectors,tools}.py`. Las 8 funciones + los 5 detectores completos. `infer_approval_threshold()` tiene DOS métodos (escalones por approver; si no son concluyentes, el hueco en la distribución de montos) y devuelve `None` si ninguno concluye — `detect_threshold_splitting` simplemente no corre en ese caso, en vez de inventar un umbral.
  - Esto obligó a un ajuste retroactivo en `estate.py`/`schemes.py`: los aprobadores de `purchase_orders` ya no se asignan al azar. Hay 3 niveles reales (coordinador/gerente/director, 2-3 personas cada uno) con techo de autoridad (`approval_threshold`, `approval_threshold*5`, sin techo), elegidos una vez por seed antes de generar ninguna OC. Sin esto, agrupar por approver era ruido puro.
  - `trace_money` y el detector de `round_tripping` exigen causalidad temporal entre saltos (`b.date >= a.date`) — sin esto, un salto podía "viajar al pasado" usando una transferencia vieja sin relación.
  - Verificado: barrido de 40 seeds, recall 100% en los 5 detectores. `check-isolation` pasa.
- [x] **Paso 4.1** — `backend/src/agent/investigator.py`. Recibe un candidato, consulta herramientas, y hace 2 llamadas cortas al modelo (decisión hallazgo/cerrar; redacción). `peso_amount`, `exhibits`, `entities`, `money_trail` se arman en código, nunca el modelo.
  - Enriquecí los candidatos de `round_tripping` en `detectors.py` con la ruta completa (montos/fechas/CLABEs), no solo `txn_id` — el investigador no tenía forma de citar un `bank_txn` por id con las 8 herramientas.
  - `threshold_splitting` y `revenue_inflation` no traían `money_trail` al principio (el validador oficial lo marca como error de formato, no solo advertencia). Corregido: ahora los 5 tipos de esquema pasan `validate_format.py --estate` limpio.
  - El modelo local (qwen2.5:7b) necesitó 2 rondas de ajuste de prompt: primero inventaba un artículo legal genérico en vez de citar 69-B; luego daba razones de cierre vagas ("evidencia insuficiente") pese a tener los datos correctos — se resolvió exigiendo que la primera frase cite los números exactos (contratos, OC) antes de razonar.
  - Verificado: `phantom_vendor` sembrado → arma hallazgo (monto exacto); decoy 1 → cierra. Los 5 tipos de esquema probados individualmente, todos pasan el validador oficial.
  - **Bug real encontrado y corregido (2026-09-13), en `_construir_caso` para `round_tripping`**: el validador reconcilia `peso_amount` SUMANDO POR TABLA (misma regla que el oficial) — pero el código original citaba CADA salto del ciclo como su propio exhibit de `bank_txns`, mientras `peso_amount` solo tomaba el monto del PRIMER salto. En un ciclo de 3 saltos con montos decrecientes (cada salto se queda con una comisión), la tabla `bank_txns` sumaba ~3x el `peso_amount` reportado — el validador rechazaba el hallazgo citando la aritmética rota, no una razón forense real. Confirmado en los 3 seeds con `round_tripping` que existían en este momento (501, 503, 507): en los 3, uno de los intermediarios del mismo ciclo "se salvaba" por pura suerte (su factura propia, sin relación real con el monto en disputa, resultaba casualmente la tabla más cercana a `peso_amount` dentro del 2%), mientras los demás caían con el mensaje de arreglo roto.
    - Corregido: ahora solo el PRIMER salto (el monto que salió de la empresa) es un exhibit de `bank_txns`, y `peso_amount` reconcilia exactamente (0% de diferencia) contra ese único exhibit. Los demás saltos siguen en `money_trail` (se necesitan para el diagrama y la conectividad), pero con `exhibit_id: null` — el validador solo exige que el id exista si no es `null`.
    - Consecuencia esperada, no un bug nuevo: un intermediario de un ciclo de `round_tripping` que no tiene NINGÚN contrato/OC/factura propia (un vehículo puramente de paso, sin rastro documental — la firma clásica de un shell en layering) ya no acumula 3 exhibits solo con los saltos del ciclo, así que cae por debajo del mínimo y el investigador lo cierra por su cuenta (`closed_by: investigator`) con una razón específica y verídica ("Tiene 0 contratos y 0 ordenes de compra registrados..."), en vez de armar un hallazgo forzado que el validador iba a tumbar de todos modos con un mensaje sin sentido para un juez. Esto es correcto siempre que OTRO intermediario del mismo ciclo sí produzca un hallazgo válido — y en los 3 seeds probados, siempre lo hace.
    - **Verificado con `eval/harness.py` (`score_seed`, el mismo criterio de "cualquier traslape de entities cuenta como encontrado" que usará la Fase 6)**: recall de estos 3 seeds era 100% (2/2, 3/3, 2/2) tanto ANTES como DESPUÉS del fix — no cambia el recall medido así, porque en los 3 casos ya había al menos un intermediario que "se salvaba" por la suerte de la factura. El valor real del fix es de calidad/robustez, no de recall en esta muestra: (a) elimina razones de cierre sin sentido para un juez ("peso_amount no reconcilia" en vez de una razón forense), y (b) quita un riesgo latente para la Fase 6/`eval/harness.py` (que todavía no corrió sobre los 10 seeds de tuning ni los 10 de reporte): si algún seed tiene un ciclo de `round_tripping` donde NINGÚN intermediario tiene una factura que casualmente reconcilie, el esquema completo se habría perdido (recall 0 para ese seed), un caso que la muestra de 3 seeds no alcanzó a exhibir pero que el mecanismo del bug permite en general.
    - Determinismo y formato reverificados tras el fix: `make check-isolation` en 0, `validate_format.py --estate` limpio en los 3 seeds, y una corrida en `--mode replay` reproduce el `submission.json` byte-idéntico salvo `wall_clock_seconds`.
- [x] **Paso 4.2** — `backend/src/agent/challenger.py`. Recibe el hallazgo en borrador, vuelve a consultar el estate por su cuenta (nunca confía solo en lo que el investigador citó), nunca ve el candidato original ni su `signal`.
  - El campo `survives` fue el problema real de este paso: pedirle al modelo el booleano directo lo invertía con frecuencia (argumento correcto, polaridad al revés, en ambas direcciones, en pruebas distintas). Se resolvió pidiéndole una palabra sin ambigüedad de sentido (`queda_explicado` / `sigue_pareciendo_fraude`) y traduciéndola en código.
  - Aun así, con los 3 hechos en "NO" el modelo a veces decía `queda_explicado` sin base. Como esos hechos (contrato, OC, reciprocidad real) ya se calculan con certeza en código, se agregó una red de seguridad: si ninguno existe, `survives` se fuerza a `true` sin importar al modelo.
  - **Se encontró un hueco real en esa red de seguridad**: el decoy 2 (empleado y proveedor en el mismo banco, sin transferencia entre ellos) no tiene contrato, OC, ni reciprocidad — caía como falsa acusación. Se agregó un **4º hecho, verificado en código antes de llamar al modelo**: si el hallazgo acusa a 2+ entidades de estar vinculadas por dinero, ¿existe una transferencia directa entre sus CLABEs en `bank_txns`? Si no, se tumba ahí mismo — nunca se consulta al modelo, porque es una contradicción factual, no de criterio.
  - Verificado: los 5 decoys armados como hallazgos fabricados, los 5 caen. Decoy 2 cae por código (nunca llama al modelo); los otros 4 caen por el modelo usando la tabla de hechos.
  - **Hueco real encontrado después (2026-09-12), y corregido**: la tabla de hechos era la MISMA para los 5 tipos de esquema (contrato, OC, reciprocidad), y un contrato del proveedor con la empresa (que explica por qué la empresa le paga al proveedor) se usaba para cerrar un `kickback` (el hecho acusado es que el proveedor le manda dinero a un empleado — un hecho totalmente distinto). Rediseñado: los hechos ahora están acotados al tipo de esquema. `kickback`/`round_tripping`: el único hecho relevante es si existe una factura de quien RECIBIÓ el último tramo del `money_trail` hacia quien lo ENVIÓ (`_factura_de_retorno_existe`) — para `kickback` esto es estructuralmente imposible (un empleado no tiene RFC, nunca puede facturar), así que ahora *siempre* sobrevive, forzado en código, sin depender del modelo. `revenue_inflation`: el único hecho es si existe un `bank_txn` que de verdad cobre la factura acusada (`_cobro_real_existe`). `phantom_vendor`/`threshold_splitting`: se quedan con contrato/OC/alcance — pero para `threshold_splitting` específicamente, una orden de compra sola YA NO cuenta como exculpatoria (se genera una por cada factura del fraccionamiento, sea o no fraude; solo un contrato -marco, recurrente- explica el patrón).
  - Verificado con hallazgos sintéticos construidos directamente de los datos sembrados (sin pasar por el investigador, porque el retador solo lee `entities`/`scheme_type`/`money_trail` del hallazgo y vuelve a consultar el estate el mismo): los 5 esquemas reales sobreviven (`survives=True`), los 5 decoys caen (`survives=False`) — 10/10. Ciclo completo en seed 17 (el caso que originó este fix): el `kickback` real ahora aparece en `findings`, y el decoy de `round_tripping` (retorno de fondos) se sigue cerrando correctamente por el retador.
- [x] **Paso 4.3** — `backend/src/agent/validator.py`. Sin modelo, solo código. Las 6 reglas (record_id existe, peso_amount al 2% por tabla, ≥3 exhibits, money_trail conecta y cita exhibit_id válido, narrative <150 palabras, entities con prefijo, scheme_type en el enum) espejan exactamente `validate_format.py` oficial — misma columna de id por tabla, misma tolerancia. Si algo falla, `gate()` regresa `leads_not_pursued` con `closed_by: "validator"` y el motivo (concatena TODAS las fallas, no solo la primera).
  - Verificado: record_id inventado → rechaza citando tabla+id exacto. peso_amount 5% fuera → rechaza mostrando la aritmética; 1% fuera → pasa (confirma que el borde del 2% no es demasiado estricto). Un hallazgo real armado por el investigador → pasa limpio. Además, por separado: <3 exhibits, narrative de 151 palabras, entity sin prefijo, scheme_type inventado, money_trail que no conecta, y money_trail con exhibit_id inexistente — los 8 casos se comportan como deben.
- [x] **Paso 4.4** — `backend/src/cli.py`. Conecta el ciclo completo por cada candidato de `prioritized_candidates()`: investigador → (retador, solo si armó hallazgo) → validador. Escribe `out/submission.json`. Uso: `python -m src.cli --estate ... --out ...` desde `backend/` (funciona sin `__init__.py`, `src/` califica como namespace package).
  - Bug real encontrado al correr el ciclo de punta a punta por primera vez: `phantom_vendor`/`threshold_splitting` con más de una factura agregaban un paso de `money_trail` por factura, todas empezando en "EMPRESA" — la propia regla de conectividad del validador (Paso 4.3) las rechazaba, correctamente, porque son pagos en paralelo, no una cadena. Corregido en `investigator.py`: todas las facturas siguen siendo exhibits (para que `peso_amount` reconcilie la suma completa), pero `money_trail` solo lleva un paso representativo.
  - Verificado: `make check-format` pasa; también la versión estricta (`--estate`, checa que cada `record_id` exista). Ciclo completo corrido contra 7 seeds distintos, los 7 pasan el validador. Cero falsas acusaciones contra decoys en las corridas con contenido.
  - **Determinismo de `run_metadata`**: `llm_calls` y `wall_clock_seconds` de `llm.py` solo cuentan llamadas reales a Ollama (por diseño del Paso 1.1: un cache-hit no debe inflar el costo de una corrida). Eso significa que dos corridas del mismo seed —una en frío, otra ya cacheada— producían un `submission.json` distinto en esos dos campos. Se decidió: `llm.py` ahora tiene un contador nuevo y separado, `logical_calls` (cuenta CADA llamada, venga de la red o del caché — mide el trabajo del agente, no el costo de la corrida). `cli.py` reporta `run_metadata.llm_calls` desde `logical_calls`, no desde `llm.llm_calls`. Con esto, `llm_calls` **sí** es idéntico entre una corrida en frío y una cacheada (verificado: 15 en ambas). `wall_clock_seconds` y `mxn_cost` siguen sin ser idénticos entre corridas, y eso es intencional: miden el costo real de *esa* corrida en particular, no una propiedad del seed — un replay cacheado legítimamente cuesta ~0. El determinismo que importa (y el que juzgan los jueces) es el de `findings`/`leads_not_pursued`, que sí es byte-idéntico.
- [x] **Fase 5** — `backend/src/report/case_file.py`. HTML autocontenido con las 5 secciones de `case_file_structure.md`, en orden. Lee el estate (solo para traducir RFC/CLABE/`emp_id` a nombres legibles) y `submission.json` ya producido; no corre el agente ni conoce al modelo. El money trail se dibuja como SVG generado en código (cajas + flechas, sin librerías externas). La reconciliación de pesos reutiliza `agent/validator._monto_por_tabla` — misma tolerancia del 2%, una sola fuente de verdad para esa aritmética. Incluye, casi verbatim, la limitante de esquemas entrelazados en la sección de método y límites.
  - Bug encontrado y corregido durante la verificación: el encabezado de cada hallazgo escapaba dos veces el HTML de "entidades" (le aplicaba `html.escape` a un fragmento que ya traía `<code>` embebido), y el `<code>` salía literal en pantalla. Corregido separando la etiqueta plana de la primera entidad (para el `<h3>`) del HTML completo con `<code>` (para el párrafo de abajo).
  - Verificado: corrido contra 3 seeds reales (uno con `round_tripping`, uno con `phantom_vendor`+`revenue_inflation` con 4 hallazgos, uno sin esquemas sembrados) — abre completo, sin red (solo referencia externa en el archivo es el namespace XML `http://www.w3.org/2000/svg` del propio SVG, que el navegador nunca resuelve por red). Conteo de tags balanceado en los 3 archivos.
  - **Hallazgo colateral encontrado durante la verificación, y ya corregido** (ver bullet siguiente): un proveedor de la generación limpia podía, por azar, cumplir la firma de un detector sin estar en `schemes` ni `decoys`.
- [x] **Regla nueva en `generate/`: población limpia sin falsos positivos.** `backend/src/generate/estate.py` agrega `enforce_clean_population()` (+ `_protected_rfcs`, `_build_memory_conn`, `_tiene_respaldo_documental`, `_dar_contrato`), llamada en `build_estate()` justo después de `schemes.plant_all(ctx)`, antes de escribir el `.db`. Arma una copia en memoria del estate y corre ahí los 5 detectores reales de `tools/detectors.py` (import `generate/` → `tools/`, la única dirección permitida). Cualquier proveedor que dispare un detector y NO esté en `schemes` ni `decoys`, y que no tenga ya contrato ni OC, recibe un contrato determinista (nunca una OC nueva, para no mover `infer_approval_threshold()` y de paso afectar a otros proveedores — ningún detector lee `contracts` salvo `phantom_vendor`). Una sola pasada basta: como nunca se toca `purchase_orders`, ningún candidato cambia de estatus por el arreglo de otro proveedor.
  - **Escala del bug, medida con un barrido de 40 seeds (solo generación, sin LLM)**: 35 de 40 (87.5%) tenían al menos un proveedor así; algunos hasta 4.
  - **Verificado con comparación antes/después en 4 seeds, ciclo completo con el modelo**: seed 2 (0→0, control, sin cambios), seed 17 (3→0 hallazgos), seed 22 (3→0), seed 38 (2→0) — 8 falsas acusaciones eliminadas en total, cero cambios en la detección de esquemas reales o en el comportamiento de los decoys ya sembrados. Determinismo confirmado (md5 idéntico corriendo el mismo seed dos veces).
  - **Hallazgo colateral encontrado aquí, ya corregido**: en el seed 17, el esquema `kickback` real (`RFC:UMA020831DK4` + `EMP:0019`) se cerró por el retador tanto ANTES como DESPUÉS de este fix — citando el contrato normal que `plant_kickback` le da al proveedor (para que "se vea legítimo" aparte de la transferencia ilícita) como si explicara esa misma transferencia. Era un hueco preexistente en el razonamiento de `agent/challenger.py`, no relacionado con este fix — corregido junto con el Paso 4.2 de arriba (ver esa entrada).
  - **Nota de coordinación (dos personas encontraron y corrigieron el mismo hueco en paralelo)**: mientras este fix se preparaba aquí, otra sesión corrió `eval/harness.py` (ver bullet de Fase 6 abajo) contra el `challenger.py` **de ANTES de este commit** y confirmó el síntoma con números: recall 53.8% (7/13 esquemas) en seeds 1-10, con `kickback` en 0/2 y `threshold_splitting` en 0/4 — los únicos dos tipos con error, los otros tres en 100%. Esa sesión llegó a un diagnóstico y una corrección propia de `challenger.py`, menos precisa que la de este commit (usaba una lista fija de "hechos que no cuentan" por tipo en vez de re-derivar el hecho pertinente de cada flujo de dinero, como `_factura_de_retorno_existe`/`_cobro_real_existe` hacen aquí) — se descartó esa versión al integrar y se mantuvo esta. Lo que sigue siendo cierto y útil de esa sesión: **el diagnóstico por número (53.8%, 0/2, 0/4) describe código que ya no existe en `main`** — hay que volver a correr el harness contra el `challenger.py` de este commit para tener números reales.
- [ ] **← Empieza aquí (en `main`): Fase 6, a medias.** `backend/eval/harness.py` ya existe y corre el ciclo completo por seed (genera estate+truth si faltan, corre `cli.run()`, compara contra `truth_seedNNN.json`). Escribe `out/results_<nombre>.csv` (columnas exactas de `results_table_template.csv`, fila `TOTAL` con `llm_calls`/`mxn_cost`/`wall_clock_s` en PROMEDIO, el resto en suma) y además `out/results_<nombre>_by_type.csv` (recall por `scheme_type`, que el CSV oficial de una fila por seed no puede expresar). `parse_seeds()` acepta `"tuning"` (1-10), `"report"` (101-110), o rangos (`"1-5,8"`). Uso:
  ```
  cd backend
  python -m eval.harness --seeds tuning --out out/results_tuning.csv
  ```
  **Pendiente al retomar — el harness todavía NO se ha corrido contra el `challenger.py` ya corregido (este commit).** Los únicos números que existen (53.8% recall, `kickback`/`threshold_splitting` en 0%) son de la versión vieja del retador — descartados, ver bullet de arriba. `out/` está en `.gitignore`, así que no hay estates/truth/submissions/cache subidos; cualquier máquina que retome empieza de cero. Al retomar:
    1. Necesitas Ollama corriendo con el modelo bajado: `ollama pull qwen2.5:7b` (si no, `cli.py`/`harness.py` fallan al primer `llm.chat`).
    2. Corre `cd backend && python -m eval.harness --seeds tuning --out out/results_tuning.csv`. La primera corrida completa (10 seeds, investigador + retador, todo en frío) tardó **~82 minutos** — es local, secuencial, no hay atajo.
    3. Revisa `out/results_tuning_by_type.csv` por tipo de esquema — esta es la primera medición real del fix ya integrado.
    4. Solo después de confirmar el recall ahí, correr los seeds de reporte (**101-110, todavía sin tocar — no se usan para tunear**): `python -m eval.harness --seeds report --out out/results_report.csv`.

**Fase 7 avanza en paralelo, en la rama `frontend`** (no en `main`), adelantada respecto al orden del plan porque el equipo decidió trabajar back y front a la vez en vez de esperar a que cerrara la Fase 6. Estado:

- [x] Andamiaje Vite + React en `frontend/` (sin `package.json`/lockfile previos — se crearon de cero; `react`, `react-dom` y `vite` ya estaban en `node_modules`). Bundle sin CDN ni fuentes remotas, `npm run build` limpio.
- [x] Las 4 pantallas como estados de una sola app (no rutas): reposo (`DropZone`), corriendo (`GraphView` con revelado progresivo por `step`, sin streaming), resultado (grafo completo + `StatCards` con los tres números + `ContrastPanel` auto-abierto), leads descartados (`LeadsList` con búsqueda). Grafo dibujado a mano en SVG (`GraphView.jsx`): posiciones fijas en anillo calculadas una sola vez, sin auto-layout, aristas en abanico cuando comparten origen/destino para no encimarse.
- [x] Estética tomada de una referencia visual (dashboard "Business Analytics" light/dark) — paleta en `src/styles/theme.css`, sin tocar la estructura de pantallas que pide `frontend/FRONTEND.md`.
- [x] Verificado con un agente de navegador (Playwright): flujo completo en claro/oscuro, animación y salto, clic en nodo (drawer de detalle para la pregunta sorpresa), búsqueda de leads, y sin overflow horizontal a 400px de ancho — cero errores de consola. Encontró y ya se corrigió: etiquetas de monto encimadas en aristas paralelas, la fila "Qué mostró" del contraste vacía, y tres reglas CSS que rompían en móvil.
- [x] **`backend/src/cli.py` ya escribe el bloque `ui`** que pedía `frontend/FRONTEND.md` (2026-09-12, hecho en `main` mientras la Fase 6 corría en otra máquina). Nuevo módulo `backend/src/report/ui_block.py` (`build(conn, empresa_rfc, findings, leads, finding_meta)`), sin modelo — puro código, reconsulta el estate solo para traducir RFC/CLABE/`emp_id` a nombres legibles (mismo patrón que `report/case_file.py`). `cli.py` acumula `finding_meta` (signal + `tool_calls_made`) por hallazgo durante el ciclo — ese dato no vivía en el finding tras el Paso 4.1, y el FRONTEND.md pide que el contraste lo tenga también del lado acusado, no solo en `leads_not_pursued`.
  - Reglas de armado: nodos = solo entidades que el agente investigó (hallazgos + leads), nunca la población completa (30-50 proveedores) — así el tope de 12-15 nodos de FRONTEND.md se respeta solo. La empresa nunca es un nodo propio (el frontend ya la agrega como `COMPANY`); en `ui.edges` sus apariciones usan el RFC pelón (sin prefijo) para que `adaptUi.js` la traduzca. Steps: entities[0] de cada hallazgo (el sospechoso) → paso 3; cualquier entity adicional (empleado en kickback, cliente en revenue_inflation) → paso 6; aristas del `money_trail` → 4 (primera), 5 (intermedias), 6 (última o único salto) — un solo salto va directo a 6 porque ES el clímax (kickback: revela la cuenta del empleado).
  - **Dos bugs reales encontrados al probar contra corridas de verdad (no en el diseño ya cerrado, en este código nuevo) y corregidos antes de dar el paso por hecho**: (1) `employees.emp_id` en el estate YA incluye el prefijo `EMP:` (a diferencia de `vendors.rfc`, que es el RFC pelón) — el primer intento recortaba el prefijo antes de buscar el nombre y nunca encontraba coincidencia, dejando el label como el id crudo (`"0005"` en vez de `"CLAUDIA RAMIREZ MORALES"`). (2) `revenue_inflation` acusa a la propia empresa como `entities[0]` (el candidato real es el RFC de la empresa) — `highlight.accused` y `ui.context` tomaban ese primer entity a ciegas, así que si ese hallazgo caía primero, apuntaban a la empresa en vez del cliente acusado. Se corrigió tomando la primera entity que NO sea la empresa como "id principal" para ambos casos.
  - Verificado contra 3 seeds reales generados en esta corrida (501: `round_tripping` de 3 saltos + `threshold_splitting`, con un lead rechazado por el validador y otro por el retador; 502: `kickback` puro; 505: `revenue_inflation` + `kickback` con la empresa como entity primaria en uno de los hallazgos) — los 3 pasan `validate_format.py --estate` limpio, `make check-isolation` sigue en 0, y una corrida en modo `replay` (cache) reproduce el `submission.json` byte-idéntico salvo `wall_clock_seconds` (determinismo intacto).
  - **Hallazgo colateral encontrado aquí, corregido por separado** (ver la entrada nueva bajo el Paso 4.1 más abajo, 2026-09-13): el candidato de `round_tripping` del seed 501 que el validador rechazaba por no reconciliar `peso_amount` ya no lo hace.
  - Sigue pendiente: `frontend/public/demo/submission_seed004.json` (escrito a mano) y `frontend/src/data/adaptUi.js` (el adaptador de respaldo) todavía no se probaron contra un `submission.json` real de `cli.py` con este bloque `ui` — la próxima vez que se toque el frontend, correr `cli.py` sobre un seed con hallazgos variados y cargar ESE archivo en la app en vez del de mano, para confirmar que `GraphView`/`ContrastPanel`/`NodeDetailDrawer` lo consumen sin ajustes.
- [ ] Solo hay un seed de demo con datos completos (004). Sin tabla de resultados (seeds 101-110, punto 5 del "orden de construcción" del FRONTEND.md — el propio doc permite dejarla como imagen estática). Sin prueba física de wifi apagado ni de legibilidad en proyector.

Historial completo en `git log --oneline` (rama `main`); cada commit
describe qué paso o fix cubre, en español. El trabajo de Fase 7 vive en
commits de la rama `frontend`, todavía sin mezclar a `main`.

---

## Paso 0 — Verificar que entendió


Lee los documentos del proyecto y el material oficial de los
organizadores: estate_schema.sql, submission_schema.json,
ground_truth_schema.json, case_file_structure.md,
validate_format.py y README.md.

No propongas cambios al diseño. Está cerrado.

Resume en 10 líneas: qué construimos, cuáles son las 8 tablas,
los 5 tipos de esquema, y qué hacen el investigador, el retador
y el validador.


*Verifica:* que nombre las 8 tablas en inglés, los 5 scheme_type exactos, y que el validador sea código y no modelo.

Si algo falla, corrígelo antes de seguir. Cuesta un minuto aquí y horas después.

---

## Fase 1 — Cimientos

### Paso 1.1 — El envoltorio del modelo

Va primero porque todo lo demás lo usa.


Crea src/llm.py: un envoltorio del cliente de Ollama.

- temperatura 0
- caché en disco, clave = sha256 del prompt
- contadores: llm_calls y wall_clock_seconds acumulados
- modo grabación (escribe al caché) y modo replay (solo lee,
  falla si no hay entrada) para poder correr sin red
- función helper que pida y parsee JSON, con reintento si
  el modelo devuelve algo que no parsea

Nada más. No toques el resto del proyecto.


*Verifica:* corre dos veces el mismo prompt. La segunda debe ser instantánea y no incrementar llm_calls.

### Paso 1.2 — Estructura y schema


Crea la estructura de src/ según la sección 6 de arquitectura:
generate/, tools/, agent/, report/, cli.py, más eval/ y out/.

Copia estate_schema.sql tal cual como src/generate/schema.sql.
No renombres ninguna columna ni traduzcas nada.

Agrega un Makefile con dos comprobaciones:
  check-format: corre validate_format.py sobre out/submission.json
  check-isolation: grep -r 'ground_truth' src/ --include='*.py'
                   y falla si aparece fuera de src/generate/


*Verifica:* make check-isolation pasa con el proyecto vacío.

---

## Fase 2 — El generador

Es la pieza más grande. Pídela por partes.

### Paso 2.1 — Tablas base


Crea src/generate/estate.py.

Entrada: --seed N --out DIR
Salida: out/estate_seedNNN.db

Genera las 8 tablas con datos coherentes y realistas:
- una empresa investigada con su RFC y CLABE
- entre 30 y 50 proveedores
- entre 8 y 15 empleados
- facturas, asientos contables, transferencias, órdenes de
  compra y contratos consistentes entre sí
- efos_list con algunos RFC en definitivo y presunto

Todo lo aleatorio pasa por UNA instancia de random sembrada
con el seed. Nada de random global, nada de datetime.now(),
nada de uuid4 sin semilla.

Los RFC deben tener formato válido: 12 caracteres para
personas morales, 13 para físicas.
Los CLABE son 18 dígitos: 3 de banco, 3 de plaza, 11 de
cuenta, 1 verificador.

Todavía SIN fraude sembrado. Solo operación limpia.


*Verifica:* corre el mismo seed dos veces y compara los .db con md5. Deben ser idénticos.

### Paso 2.2 — Los cinco esquemas


Agrega a src/generate/ la siembra de los 5 tipos de esquema,
según la sección 3 de arquitectura. Cada uno en su propio
módulo o función:

phantom_vendor       proveedor sin contrato ni OC, alta
                     reciente, concepto genérico, en efos_list
kickback             el proveedor transfiere parte del pago
                     al CLABE de un empleado
round_tripping       el dinero sale de la empresa, pasa por
                     2-3 proveedores y regresa a su CLABE
threshold_splitting  varias facturas del mismo proveedor,
                     fechas cercanas, cada una justo debajo
                     del límite de aprobación
revenue_inflation    la empresa emite facturas por ventas
                     que nunca cobró

Escribe además out/truth_seedNNN.json con el formato de
ground_truth_schema.json: seed, company_rfc, schemes, decoys.

El cuántos esquemas y de qué tipo se decide con el seed.


*Verifica:* abre un .db con sqlite3 y comprueba a mano que un esquema sembrado se ve como debe. El truth.json debe validar contra su schema.

### Paso 2.3 — Los decoys


Agrega la siembra de decoys: entidades honestas que disparan
un detector y se limpian al inspeccionarlas. Los cinco de la
sección 3 de arquitectura:

1. proveedor en efos_list presunto, con contrato, OC y pago
   único sin retorno
2. empleado y proveedor en el mismo banco (mismos 3 dígitos
   iniciales de CLABE, cuentas distintas, sin transferencia
   entre ellos)
3. facturación recurrente bajo el límite de aprobación, por
   contrato marco con cuota mensual fija
4. proveedor que también es cliente: hay dinero de vuelta,
   pero con facturas propias en sentido contrario
5. proveedor de alta reciente pero con contrato firmado antes
   del alta

Cada decoy se registra en truth.json con su why_innocent.

Agrega también soporte para seeds sin ningún esquema sembrado,
solo decoys.


*Verifica:* genera un seed sin fraude y confirma que truth.json trae schemes: [] y decoys poblados.

---

## Fase 3 — Las herramientas


Crea src/tools/ con las 8 funciones de la sección 4 de
arquitectura, sobre SQLite:

prioritized_candidates()      detectores deterministas
vendor(rfc)                   fila de vendors + efos_list
invoices_by(rfc, role)        role = issuer | receiver
support_for(rfc)              contracts + purchase_orders
trace_money(clabe, max_hops)  WITH RECURSIVE sobre bank_txns
whose_clabe(clabe)            vendors | employees | empresa
reciprocity(rfc_a, rfc_b)     facturas en sentido contrario
ledger_for(uuid)              asientos de esa factura

Reglas:
- devuelven datos, nunca juicios. Nada de campos tipo
  "sospechoso" o "riesgo".
- whose_clabe compara el CLABE COMPLETO, nunca por prefijo.
  Dos personas en el mismo banco no están vinculadas.
- prioritized_candidates devuelve orden estable: por señal y
  desempate por rfc.
- ninguna de estas funciones puede importar nada de generate/
  ni leer truth.json.


*Verifica:* make check-isolation sigue pasando. Y prueba trace_money contra un round_tripping sembrado: debe devolver el ciclo.

### Los detectores


Dentro de prioritized_candidates, implementa un detector por
tipo de esquema:

phantom_vendor       cruce con efos_list + ausencia de
                     contracts y purchase_orders
kickback             bank_txns cuyo to_clabe aparece en
                     employees
round_tripping       recorrido recursivo que cierra el ciclo
                     en el CLABE de la empresa
threshold_splitting  agrupar por proveedor y ventana de
                     fechas, comparar contra el límite
                     inferido de purchase_orders
revenue_inflation    invoices donde issuer_rfc es la empresa
                     y no hay bank_txn que las liquide

Cada candidato devuelve qué detector lo señaló. Ese texto se
usa después en el campo "signal" de leads_not_pursued.


---

## Fase 4 — El agente

### Paso 4.1 — Investigador


Crea src/agent/investigator.py.

Recibe un candidato de prioritized_candidates y decide si arma
un hallazgo o cierra el lead.

- consulta herramientas según la hipótesis
- si arma hallazgo: scheme_type, entities con prefijo RFC: o
  EMP:, exhibits (mínimo 3), peso_amount, money_trail
- si lo cierra: entity, signal, reason específico citando la
  evidencia examinada, tool_calls_made, closed_by: investigator

Los prompts piden JSON corto de 2 o 3 campos. Nada de prosa.
El peso_amount lo calcula código a partir de los exhibits,
nunca el modelo.


*Verifica:* corre contra un phantom_vendor sembrado. Debe armar el hallazgo. Corre contra el decoy 1. Debe cerrarlo.

### Paso 4.2 — Retador


Crea src/agent/challenger.py.

Recibe un hallazgo en borrador con toda su evidencia. Su ÚNICA
tarea es construir la explicación inocente más fuerte que
encaje con esos datos.

Devuelve JSON corto:
  {"survives": true|false, "argument": "<bajo 40 palabras>"}

Si survives es false, el lead se cierra con closed_by:
challenger y el argument va como reason.
Si es true, el argument se guarda igual: va en el case file
como lo que se argumentó y por qué no bastó.

No puede ver el ground truth ni saber qué detector disparó.


*Verifica:* pásale un decoy armado como si fuera hallazgo. Debe tumbarlo.

### Paso 4.3 — Validador


Crea src/agent/validator.py. SIN modelo, solo código.

Verifica cada hallazgo antes de publicarlo:
- cada record_id citado existe en el estate
- peso_amount reconcilia contra los exhibits dentro del 2%,
  sumando POR TABLA y comparando contra la tabla que mejor
  empate (una factura y la transferencia que la liquidó son
  los mismos pesos vistos dos veces)
- al menos 3 exhibits
- el money_trail conecta: el destino de cada paso es el origen
  del siguiente, y cada paso cita un exhibit_id que existe en
  la lista de exhibits
- narrative bajo 150 palabras
- entities con prefijo
- scheme_type dentro del enum

Si algo falla, el hallazgo NO se publica: pasa a
leads_not_pursued con closed_by: validator y el motivo.


*Verifica:* mete a mano un hallazgo con un record_id inventado. Debe rechazarlo.

### Paso 4.4 — El ciclo


Crea src/cli.py que reciba la ruta del estate por argumento y
corra el ciclo completo: detectores, investigador, retador,
validador, y escriba out/submission.json.

Incluye run_metadata con llm_calls, mxn_cost (0.0 con Ollama)
y wall_clock_seconds tomados del envoltorio de llm.py.

Uso: python -m src.cli --estate out/estate_seed001.db \
                       --out out/submission.json


*Verifica:* make check-format pasa.

---

## Fase 5 — El case file


Crea src/report/case_file.py: genera un HTML autocontenido con
las 5 secciones de case_file_structure.md, en ese orden.

1. Encabezado: empresa, periodo, seed, los tres números, y si
   la corrida es determinista
2. Resumen ejecutivo con tabla de hallazgos, exposición total
   y leads cerrados
3. Una sección por hallazgo: encabezado, regla rota, monto y
   confianza, narrative, MONEY TRAIL COMO DIAGRAMA, tabla de
   exhibits, la aritmética de la reconciliación, y lo que
   argumentó el retador
4. Leads no perseguidos, en el cuerpo
5. Método y límites: arquitectura, qué quedó fuera de alcance,
   qué el sistema NO puede detectar, cómo reproducir

El money trail se renderiza como SVG generado localmente y
embebido en el HTML. Sin CDN, sin librerías externas, sin
llamadas de red. Debe abrirse con la conexión apagada.


*Verifica:* ábrelo en el navegador con el wifi apagado. Debe verse completo.

---

## Fase 6 — La métrica


Crea eval/harness.py.

Corre el sistema sobre una lista de seeds, compara
out/submission.json contra out/truth_seedNNN.json y produce
una tabla con:
- esquemas sembrados vs encontrados (recall)
- decoys acusados (falsas acusaciones)
- por tipo de esquema
- llm_calls, mxn_cost y wall_clock promedio

Seeds de tuning: 1 al 10. Seeds de reporte: 101 al 110.
Los de reporte NO se usan durante el desarrollo.

Este archivo SÍ puede leer truth.json. Es el único, junto con
generate/.


*Verifica:* make check-isolation sigue pasando.

---

## Fase 7 — La interfaz

Solo cuando todo lo anterior corra.

Antes de empezar: lee [`docs/Arquitectura_v2_Forensic_Auditor.md`](docs/Arquitectura_v2_Forensic_Auditor.md) y [`docs/Planeacion_v2_Forensic_Auditor.md`](docs/Planeacion_v2_Forensic_Auditor.md), sobre todo la sección «2 — El demo» de la planeación. Ahí están las bases de la interfaz —qué muestra, en qué orden y qué se demuestra en vivo—. Lo de abajo es el resumen operativo, no la especificación completa.


Crea frontend/ con Vite + React:
- zona para soltar un archivo .db
- grafo del money trail que se construye progresivamente
- vista de contraste: un hallazgo acusado junto a un decoy
  descartado, con las mismas filas alineadas
- tabla de resultados

Consume el submission.json que ya produce el backend. No
cambies el formato de salida.


---

## Si van tarde

Cortes ya decididos. No se discuten en el momento.

| Quedan | Se corta |
|---|---|
| 20 h | Bajar a 3 tipos de esquema: phantom_vendor, kickback, round_tripping. threshold_splitting y revenue_inflation quedan documentados como fuera de alcance en la sección de límites del case file. |
| 12 h sin pipeline completo | Alto a funciones nuevas. Todos a conectar lo que hay. El grafo progresivo también se corta aquí: aparece completo de golpe. |
| 6 h | La interfaz entera. Se demuestra desde terminal más el case file en HTML. |
| Muy tarde | Tiger Data y Vultr. Se pierden esas categorías, no el track. |

*Nunca se corta:* el retador, el validador, los leads con razón específica, la reconciliación de pesos, y los tres números.

(Alineado a [`docs/Planeacion_v2_Forensic_Auditor.md`](docs/Planeacion_v2_Forensic_Auditor.md), secciones «Checkpoints» y «Cortes decididos por adelantado» — la versión que manda.)

---

## Antes de presentar

- [ ] make check-format sale en 0
- [ ] make check-isolation sale en 0
- [ ] El mismo seed corrido dos veces da el mismo submission.json
- [ ] El case file abre con la red apagada
- [ ] La tabla de resultados está llena con seeds 101-110
- [ ] Puedes señalar un lead descartado y leer su razón en menos de 10 segundos
- [ ] Tienes los tres números a la mano
- [ ] Sabes qué cortaron y por qué