# The Forensic Auditor — Documento de Planeación

**HACKMTY 2026 · versión 2 — alineada al material oficial de los organizadores**

*Fase 2 de 4 · ~24 horas restantes*

---

## Qué cambió respecto a la versión 1

Los organizadores publicaron los formatos y las reglas de calificación. La investigación sigue válida completa; la planeación cambia en estos puntos.

| Antes | Ahora |
|---|---|
| Tres veredictos: DEFENDIBLE, CORREGIR, ACUSACIÓN | La salida es `findings[]` con `scheme_type` de un enum fijo de cinco, más `leads_not_pursued`. Nuestro CORREGIR se convierte en lead descartado, no en hallazgo. |
| Nuestras nueve tablas en español | Ocho tablas fijas en inglés, definidas en `estate_schema.sql`. Los jueces leen esos nombres de columna. |
| PostgreSQL / Tiger Data | SQLite. El validador oficial espera un archivo `.db`. Tiger queda como despliegue paralelo para la categoría. |
| Cuatro estatus del 69-B como diferenciador | `efos_list` solo tiene definitivo y presunto. El diferenciador pasa a ser el manejo de decoys: entidades honestas que disparan un detector. |
| Dos tipologías de AMLSim | Cinco tipos de esquema fijos. Generamos las transferencias nosotros, con seed. AMLSim sale. |
| Métrica como nivel 2 | Obligatoria: al menos cinco seeds de reserva, con seeds de tuning y de reporte disjuntos y nombrados en el pitch. |

> **IMPLICACIÓN DE DISEÑO — lo que NO cambió**
>
> - La investigación completa: 69-B, EFOS/EDOS, materialidad, retroactividad, retorno de fondos.
> - La aritmética fuera del modelo: ahora es regla dura, el `peso_amount` se verifica contra los exhibits citados dentro del 2%.
> - El ground truth aislado: ahora es regla con grep. Si se filtra al razonamiento del agente, Results topa en 2.
> - Los detectores deterministas antes del modelo.
> - Los leads descartados: son sección obligatoria del case file, en el cuerpo, no en anexo.

---

## Resumen en una página

### La apuesta

```
Ningún hallazgo se imprime sin haber sido atacado.

Investigador  arma el caso
Retador       intenta tumbarlo
Validador     verifica que cite y reconcilie
```

Lo que sobrevive se imprime con su prueba. Lo que no, se documenta como lead descartado, con el nombre de quién lo cerró.

### Por qué esta apuesta

Las reglas dicen que un sistema que acusa a todos alcanza recall perfecto y califica mal, y que las falsas acusaciones contra decoys pesan al menos tanto como el recall.

Además, el case file pide explícitamente que si hay revisión adversarial se incluya qué argumentó y por qué el hallazgo sobrevivió, porque un hallazgo que nadie intentó romper es más débil que uno atacado que resistió.

Y el campo `closed_by` del formato oficial acepta exactamente tres valores: `investigator`, `challenger`, `validator`. Los organizadores están señalando esta arquitectura.

### Las cuatro reglas que no se negocian

1. Ningún hallazgo se imprime sin pasar por retador y validador.
2. Los montos salen de consultas SQL, nunca del modelo. El validador oficial los verifica al 2%.
3. El ground truth vive en un archivo JSON aparte que el agente no puede abrir. Ni siquiera se importa.
4. El mismo seed produce el mismo case file. Los jueces lo corren dos veces.

### El checkpoint que importa

A las **12 horas restantes** debe haber un pipeline completo: entra un estate `.db`, sale un `submission.json` que pasa el validador oficial. Feo, pero completo.

Si no lo hay, se detiene todo lo demás y el equipo entero se dedica a conectarlo.

---

## 1 — Qué tenemos que producir

Dos artefactos, no uno.

### `submission.json`

Lo que se revisa por máquina: recall, tasa de falsas acusaciones y reconciliación de pesos.

```json
{
  "seed": 1,
  "findings": [ ... ],
  "leads_not_pursued": [ ... ],
  "run_metadata": {
    "llm_calls": 0,
    "mxn_cost": 0.0,
    "wall_clock_seconds": 0.0,
    "deterministic": true
  }
}
```

Una lista de hallazgos vacía es un resultado legítimo. Eso importa: si el estate del jurado no tiene fraude, no inventamos.

### El case file

Lo que lee un juez. Cinco secciones obligatorias, en orden: encabezado con los tres números, resumen ejecutivo, una sección por hallazgo, leads no perseguidos en el cuerpo, y método y límites.

Se califica por si un lector **NO técnico** lo puede seguir de principio a fin sin que nadie del equipo se lo explique.

> **IMPLICACIÓN DE DISEÑO — el money trail tiene que ser diagrama**
>
> El case file dice explícitamente que en prosa la Clarity topa en 3. Tiene que renderizarse como diagrama, y cada paso citar un exhibit.
>
> Y debe poder producirse sin conexión: los jueces pueden pedir que se demuestre con la red apagada.

### Los cinco tipos de esquema

| Tipo | Qué es |
|---|---|
| `phantom_vendor` | Proveedor que no existe o no opera. Factura servicios que nunca prestó. |
| `kickback` | El proveedor devuelve parte del pago a un empleado de la empresa. |
| `round_tripping` | El dinero sale y regresa a la propia empresa dando vueltas. |
| `threshold_splitting` | Se parten facturas para quedar bajo un límite de aprobación y evitar autorización superior. |
| `revenue_inflation` | La empresa emite facturas por ventas que no ocurrieron, para inflar sus números. |

Los dos últimos no estaban en la versión 1. `threshold_splitting` se detecta con `purchase_orders` y su campo `approver`; `revenue_inflation` se detecta en facturas donde la empresa es la emisora, no la receptora.

---

## 2 — El demo

Cambia poco respecto a la versión 1. El contraste sigue siendo el momento central, solo que ahora es entre un esquema acusado y un decoy descartado.

### Formato

- **Demo en paralelo a la presentación.** Tres minutos en total. Uno narra, otro opera.
- **El jurado suelta un estate `.db`.** La ruta se pasa en tiempo de ejecución; rutas hardcodeadas fallan.
- **El grafo se construye progresivamente.** Da algo que mirar mientras corre.
- **Plan B en otra pestaña.** Se anuncia en voz alta. El operador cambia a los 90 segundos sin consultar.

### Los dos carriles

| Tiempo | Narración | Pantalla |
|---|---|---|
| 0:00 | El problema + por qué acusar de más es peor que acusar de menos | |
| 0:30 | La apuesta: investigador, retador, validador | |
| 0:45 | «Suelten su estate» | → `[drop]` |
| 0:50 | Cómo razona el agente y cómo el retador lo intenta tumbar | ← grafo construyéndose |
| 1:40 | El contraste | ← hallazgo acusado vs decoy descartado |
| 2:20 | La tabla de resultados | ← seeds de reserva, recall y falsas acusaciones |

### Lo que hay que demostrar en vivo

Las reglas piden poder mostrar, en vivo y desde un registro, un lead descartado y la razón por la que se cerró. Y responder en menos de diez segundos a «¿por qué no señalaste a este proveedor?».

Volver a correr el sistema para averiguarlo es la respuesta incorrecta, aunque el resultado sea correcto.

> **IMPLICACIÓN DE DISEÑO — los tres números van en el encabezado**
>
> Llamadas al modelo, costo en pesos y segundos de reloj. «No sabemos» califica bajo en Feasibility.
>
> Con Ollama local el costo es cero pesos, y eso es un argumento fuerte: un despacho puede correr esto sin que los datos del cliente salgan de su red.

---

## 3 — Alcance y cortes

### Nivel 1 — sin esto no hay entrega

```
Generador del estate por seed, sobre las 8 tablas
  oficiales, con los 5 tipos de esquema y decoys
Ground truth en archivo JSON aparte, aislado
Detectores deterministas por tipo de esquema
Las 8 herramientas de consulta
Investigador -> Retador -> Validador
submission.json que pasa validate_format.py
Case file con las 5 secciones y money trail
  como diagrama
Los tres números de run_metadata
Ruta del estate en tiempo de ejecución
Determinismo por seed
```

### Nivel 2 — lo que hace ganar

```
Tabla de resultados sobre 5+ seeds de reserva
UI: drop + grafo + contraste
Grafo progresivo
Replay sin red
Esquemas entrelazados en el generador
Despliegue paralelo en Tiger Data y Vultr
```

### Nivel 3 — solo si sobra

```
Preguntarle al agente en vivo
Más decoys y casos límite
Voz con ElevenLabs
```

### Checkpoints

| Quedan | Tiene que estar | Si no está |
|---|---|---|
| 20 h | Estate generándose por seed contra las 8 tablas. Ground truth aparte. Validador oficial corriendo en el build. | Reducir a 3 tipos de esquema y 3 decoys. |
| 12 h | PIPELINE COMPLETO: entra `.db`, sale `submission.json` que pasa el validador. | Alto total a funciones nuevas. Todos a conectar. |
| 6 h | Nivel 1 completo. Case file renderizando. | Se corta nivel 2 entero. Tabla de resultados a mano. |
| 3 h | Código congelado. Solo ensayo. | Nadie toca el código. |

### Cortes decididos por adelantado

| Si vamos tarde | Se corta |
|---|---|
| A las 20 h | Bajar a 3 tipos de esquema: `phantom_vendor`, `kickback`, `round_tripping`. Los otros dos quedan documentados como fuera de alcance en la sección de límites. |
| A las 12 h | El grafo progresivo. Aparece completo de golpe. |
| A las 6 h | La UI entera. Se demuestra desde terminal y el case file en HTML. Menos vistoso, cumple igual. |
| Muy tarde | Tiger Data y Vultr. Se pierden esas categorías, no el track. |

### Lo que nunca se corta

```
El retador y el validador
Los leads descartados con razón específica
La reconciliación de pesos
Los tres números
```

Eso es la apuesta y son tres de los cuatro criterios. Si eso sobrevive, hay entrega aunque el resto esté con alambres.

> **IMPLICACIÓN DE DISEÑO — declarar los límites suma**
>
> El case file pide una sección de método y límites: qué quedó fuera de alcance y qué el sistema no puede detectar.
>
> Las reglas dicen que declarar límites con claridad califica mejor que insinuar una cobertura que no se puede defender. Si cortamos dos tipos de esquema, se dice, y eso no resta.

---

## 4 — Reparto

| Rol | Responsabilidad |
|---|---|
| **A · Estate** | El generador por seed: las 8 tablas, los 5 esquemas, los decoys, las transferencias. Y el ground truth aislado. Es el rol más grande. |
| **B · Consultas** | Los detectores deterministas y las 8 herramientas SQL sobre SQLite, incluido el rastreo por CLABE. |
| **C · Agente** | Investigador, retador y validador. El serializador de `submission.json`. |
| **D · Salida y demo** | El case file renderizado con su diagrama, la UI, y el ensayo del demo. |

Lo más probable es que A, B y C se repartan entre dos o tres personas de forma fluida. Está bien. Dos cosas siguen importando: que la ruta crítica no quede en una sola persona, y que D tenga dueño claro porque es lo único que el jurado ve.

### El orden temporal

```
Ahora - 1 h    Los cuatro juntos: acordar el
               contrato de arquitectura.
               Correr validate_format.py con
               submission_example.json.

1 h  - 4 h     A: generador del estate
               B: detectores y herramientas
               C: esqueleto de los tres roles
                  con datos escritos a mano
               D: case file en HTML con
                  datos escritos a mano

4 h  - 12 h    Integración progresiva.
               Primera conexión real a las 6 h,
               no a las 20.

12 h           PIPELINE COMPLETO.

12 h - 18 h    Nivel 2. A corre la tabla de
               resultados sobre seeds de reserva.

18 h - 21 h    Pulido e integración.
21 h - 24 h    Ensayo. Código congelado.
```

> **IMPLICACIÓN DE DISEÑO — los seeds se reparten desde el inicio**
>
> Se decide ahora cuáles son de tuning y cuáles de reporte, y no se tocan los de reporte durante el desarrollo.
>
> Si los números reportados vienen de los seeds con los que se afinó, hay penalización explícita. Ambos conjuntos se nombran en el pitch.
>
> Propuesta: tuning 1 al 10, reporte 101 al 110. Simple de recordar y de verificar.

---

## Recordatorio

```
Ningún hallazgo se imprime sin haber sido atacado.
Si una tarea no sirve a esa frase, se corta.
```

Y antes de escribir código: correr el validador oficial contra el ejemplo. Si no pasa ahí, no va a pasar con lo nuestro.
