# The Forensic Auditor — Documento de Planeación

**HACKMTY 2026 · Infosys Challenge Track**

*Fase 2 de 4 · Investigación → Planeación → Arquitectura → Desarrollo*

*Equipo de 4 personas · ~28 horas de calendario*

> [!NOTE]
> **Versión 1. Donde este documento y la [v2](Planeacion_v2_Forensic_Auditor.md) se contradigan, manda la v2** — sobre todo en la apuesta (aquí tres veredictos; en la v2 son `findings[]` con `scheme_type` y `leads_not_pursued`), en los niveles de alcance, en los checkpoints por hora y en los cortes.
>
> **Pero esto no es solo consulta histórica.** Varias secciones siguen siendo la única fuente que hay, porque la v2 no las cubre: el **guion literal del pitch de 0:00 a 3:00**, el **plan B con su umbral de 90 segundos**, la **pregunta sorpresa del jurado** (sección 2) y las **reglas de coordinación, perfiles y sueño** (sección 4).

---

## Resumen en una página

Si solo lees una página, que sea esta.

### La apuesta

```
Tres veredictos accionables,
probados con el flujo del dinero,
medidos con ground truth.
```

Todo lo demás se deriva de esa frase. Si una tarea no sirve a esa frase, se corta.

### Por qué esta apuesta

La mayoría de los equipos va a construir un detector: entra una lista de facturas, sale una lista de sospechosos. Nosotros construimos algo que un área de finanzas puede usar el lunes: por cada operación, qué hacer con ella.

```
DEFENDIBLE  -> hay expediente, preséntalo
CORREGIR    -> operación probablemente real,
               documentación insuficiente,
               sin señales de simulación
ACUSACIÓN   -> hay retorno de fondos comprobado
```

Las tres salidas corresponden a figuras que existen en el artículo 69-B. No las inventamos.

### Las tres reglas que no se negocian

1. Estar en la lista del SAT es sospecha; el retorno del dinero es prueba. No acusamos sin cadena completa.
2. Los montos en pesos salen de consultas a los datos, nunca del modelo de lenguaje.
3. El ground truth se usa para medir, nunca queda al alcance del agente.

### El checkpoint que importa

A las **14 horas** tiene que haber un pipeline completo corriendo de punta a punta, aunque sea feo. Si no lo hay, se detiene todo lo demás y el equipo entero se dedica a conectarlo.

Un pipeline mediocre completo gana a tres módulos excelentes desconectados. Siempre.

---

## 1 — La apuesta

### Qué descartamos y por qué

Evaluamos cuatro candidatas. La regla fue: una apuesta no es lo que hacemos bien, es lo que los demás no van a hacer.

| Candidata | Veredicto |
|---|---|
| Seguir el dinero con grafo en pantalla | Descartada como apuesta. Es el verbo del propio track: todos lo van a hacer. Entra como capacidad obligatoria y como evidencia visual de la apuesta real. |
| El agente que se niega a acusar | Absorbida. Es correcta pero es una capacidad negativa: «miren, no hizo nada» es un momento débil en tres minutos. Su contenido vive dentro de los tres veredictos. |
| Medir con precisión y recall | Adoptada como soporte, no como apuesta. Es una ventaja de pitch, no de producto. Si el agente es mediocre, medirlo solo documenta que es mediocre. |
| **Tres veredictos accionables** | **ADOPTADA.** Es la única que suena a producto que alguien compraría. |

### Por qué los tres veredictos

El hallazgo de la investigación que lo sostiene: cuando una operación no tiene soporte documental, hay tres causas posibles y desde afuera se ven idénticas.

```
1. Ocurrió y está documentada     -> defendible
2. Ocurrió pero no se documentó   -> corregir
3. No ocurrió                     -> acusación
```

Los casos 2 y 3 son indistinguibles en una lista: proveedor señalado, sin contrato, sin evidencia de entrega. Un despacho tarda semanas en separarlos, y si se equivoca o paga de más o defiende lo indefendible.

Lo único que los separa es a dónde fue el dinero. Por eso el flujo bancario no es un adorno del demo: es el mecanismo que evita acusar a un inocente.

> **IMPLICACIÓN DE DISEÑO — cómo se deriva todo lo demás**
>
> El demo tiene que enseñar los tres veredictos, no solo la acusación.
>
> El data estate necesita los cuatro tipos de proveedor sembrados obligatoriamente: legítimo, desordenado, simulador y recíproco.
>
> El recorrido del grafo es lo que separa «corregir» de «acusación».
>
> La pregunta sorpresa del jurado casi seguro será «¿por qué no acusaste a ese?», y la respuesta ya está estructurada.

### El rol de cada pieza

| Pieza | Función en la apuesta |
|---|---|
| Tres veredictos | La apuesta. Es lo que nos separa. |
| Flujo del dinero | La prueba. Sin él los veredictos no se distinguen. |
| Ground truth y métrica | La evidencia. Convierte el demo en dato. |

---

## 2 — El demo

Escrito antes de construir nada, y usado como filtro: lo que no aparece en estos tres minutos, no se construye.

### Formato

- **Demo en paralelo a la presentación.** No se interrumpe la narración para esperar al agente; el agente trabaja mientras se sigue hablando.
- **Tres minutos en total.** No cabe una presentación normal. No hay slide de arquitectura, ni de equipo, ni agradecimientos.
- **Uno narra, otro opera.** Cuatro personas hablando es un desastre.
- **El jurado suelta un archivo.** Es lo más intuitivo y no requiere que entiendan nuestro formato.
- **El grafo se construye progresivamente.** Da algo que mirar mientras corre.

### Los dos carriles

| Tiempo | Narración | Pantalla |
|---|---|---|
| 0:00 | Problema + hallazgo del 69-B: cuatro estatus | |
| 0:30 | La apuesta: tres veredictos | |
| 0:45 | «Suelten su archivo» | → `[drop]` |
| 0:50 | Cómo razona el agente: 69-B temporal, materialidad, seguir el dinero | ← grafo construyéndose |
| 1:40 | El contraste | ← dos nodos lado a lado |
| 2:20 | Cierre con métrica | ← tabla de resultados |

La narración de 0:50 a 1:40 es la que cubre el tiempo de cómputo. Son cincuenta segundos de contenido real —cómo razona el agente y de dónde salen sus criterios—, no relleno. Y es justamente material de proceso de pensamiento, que es lo que los organizadores dijeron que valorarían.

### El guion

**0:00 – 0:35 · El problema y el hallazgo**

> «En México hay empresas cuyo negocio es vender facturas por servicios que nunca prestaron. El SAT publica una lista de ellas, pero cuando sale, la empresa ya dedujo y ya está en problemas.
>
> Investigando encontramos algo que cambió nuestro diseño: esa lista tiene cuatro estatus, no dos. Dos de ellos significan que el contribuyente está limpio. Un agente que acusa por aparecer en la lista, acusa inocentes.
>
> Por eso el nuestro no da un score. Da tres veredictos: defendible, corregir, o acusación.»

En treinta y cinco segundos ya hay un hallazgo de investigación, la decisión de diseño que derivó de él, y la apuesta.

**0:35 – 0:50 · La inyección**

> «Este es el data estate de una empresa: facturas, contabilidad, movimientos bancarios, proveedores. El agente no lo ha visto. Suelten su archivo aquí.»

**0:50 – 1:40 · Cómo razona**

> «Primero descarta lo barato: cruza los RFC contra la lista del SAT, comparando la fecha de cada factura contra la fecha de publicación. No pregunta si están hoy en la lista, pregunta si lo estaban cuando facturaron.
>
> De los que quedan, revisa materialidad: contrato, evidencia de entrega, pago rastreable. Los tres elementos salen del artículo 69-B, no los inventamos nosotros.
>
> Y ahí sigue el dinero. Esto es lo único que separa a un proveedor desordenado de uno que simula.»

**1:40 – 2:20 · El contraste**

Este es el minuto que importa. Dos nodos lado a lado.

> «Los dos proveedores están en estatus definitivo. Los dos sin contrato. En una lista se ven idénticos.
>
> Este recibió el pago y ahí se quedó: nómina, sus propios proveedores. Operación real, papeles incompletos. Veredicto: corregir. No lo acusamos.
>
> Este otro dispersó el dinero en tres saltos y el 92.9% regresó en doce días a una cuenta del socio mayoritario. Veredicto: acusación, con el monto exacto y la ruta.
>
> Distinguir estos dos casos hoy le toma semanas a un despacho.»

**2:20 – 3:00 · El cierre**

> «Sobre veinte escenarios que no había visto, encontró X de Y esquemas con Z por ciento de falsos positivos.
>
> El expediente se exporta con el folio fiscal de cada factura y el número de oficio del SAT. Un auditor lo puede verificar a mano.»

### El plan B

Hay una corrida previa lista en otra pestaña, con el flujo completo.

- **Se anuncia en voz alta.** «Tenemos una corrida previa por si el tiempo aprieta», antes de cambiar de pestaña, no después de que alguien pregunte.
- **Nunca se presenta como si fuera la del jurado.** Suelen notarlo, porque preguntan por un dato específico del esquema que ellos metieron. Y todo nuestro diferenciador es credibilidad.
- **El operador decide, con umbral fijo.** Si a los 90 segundos no terminó, cambia sin consultar. Discutirlo en el momento cuesta quince segundos frente al jurado.

### La pregunta sorpresa

El jurado pregunta sobre el razonamiento del agente, no sobre el código.

La más probable: «¿por qué no acusaste a ese otro?». Es la pregunta obvia después de ver dos proveedores con el mismo estatus y distinto veredicto, y la respuesta es nuestra apuesta entera.

Otras candidatas: qué pasa si el fraude no involucra a nadie de la lista del SAT; cómo sabemos que no se escapó nada; qué haría falta para que sí lo acusara.

> **IMPLICACIÓN DE DISEÑO — cómo se contesta**
>
> Leyendo lo que el agente persistió. Cada hipótesis, cada consulta y cada lead descartado con su motivo quedan guardados y consultables.
>
> Que el agente conteste en vivo es un upgrade opcional, para el domingo si sobra tiempo. No entra en el camino crítico.

> **IMPLICACIÓN DE DISEÑO — lo que el guion obliga a construir**
>
> ```
> drop de archivo
> grafo progresivo
> vista comparativa de dos nodos
> los tres veredictos con su lógica
> % de retorno y monto en pesos
> métrica sobre ~20 escenarios
> export del expediente
> razonamiento persistido y consultable
> ```
>
> Todo lo demás se cae: sin dashboard, sin historial de investigaciones, sin las otras siete tipologías, sin generación de XML.

---

## 3 — Alcance y cortes

Tres niveles. Nadie toca el nivel 2 hasta que el nivel 1 esté completo y corriendo de punta a punta.

### Nivel 1 — sin esto no hay demo

```
Data estate generado, 5 tablas coherentes,
  con los cuatro tipos de proveedor sembrados
Ingesta del 69-B con los cuatro estatus y fechas
Ingesta de AMLSim (dataset pregenerado)
Detectores deterministas
Loop del agente con el gate de tres veredictos
Recorrido de grafo y cálculo del % de retorno
Case file en texto
UI: drop + grafo + dos nodos comparados
Razonamiento persistido
```

### Nivel 2 — lo que hace ganar

```
Métrica sobre ~20 escenarios
Grafo progresivo (vs. aparecer de golpe)
Export del expediente
Ruido en los datos (5% de registros sucios)
```

La métrica está en nivel 2 y no en 1 a propósito: es parte de la apuesta, pero si el pipeline no corre, la métrica no existe de todos modos.

### Nivel 3 — solo si sobra

```
Preguntarle al agente en vivo
Señales del artículo 69 a secas
Tipologías adicionales de AMLSim
```

### Checkpoints

| Hora | Tiene que estar | Si no está |
|---|---|---|
| H+4 | Contrato de datos congelado. Las 5 tablas definidas y acordadas. | Congelar lo que haya y seguir. Un schema imperfecto decidido gana a uno perfecto en discusión. |
| H+8 | Data estate generado y cargado. 69-B y AMLSim ingeridos. | Reducir a 20 proveedores y 3 escenarios. Menos datos, mismo agente. |
| H+14 | PIPELINE END-TO-END CORRIENDO. Feo, pero completo: entra archivo, sale veredicto. | Alto total a funciones nuevas. Todo el equipo a conectar lo que hay. |
| H+20 | Nivel 1 completo. UI funcionando. | Se corta el nivel 2 entero. Métrica a mano sobre 5 escenarios. |
| H+25 | Congelación de código. | — |
| H+25 a H+28 | Solo ensayo. | Nadie toca el código. |

> **IMPLICACIÓN DE DISEÑO — el checkpoint de las 14 horas**
>
> Es el único que se aplica sin discusión. Si a la mitad del tiempo el pipeline no corre completo, se deja de agregar y se hace que corra.
>
> El equipo que llega al domingo con tres módulos brillantes y sin integrar no tiene demo.

### Cortes decididos por adelantado

Esto es lo que salva la madrugada. Ya está decidido; no se discute a las cuatro de la mañana.

| Si vamos tarde a | Se corta |
|---|---|
| H+8 | El data estate baja a 20 proveedores y 3 escenarios sembrados. El agente no cambia. |
| H+14 | Cae el grafo progresivo. El grafo aparece completo de golpe. Feo pero funcional. |
| H+20 | Cae la métrica automatizada. Se corren 5 escenarios a mano y la tabla se hace en papel. Se conserva el número para el pitch. |
| Muy tarde | Cae el drop de archivo. El operador corre un comando en terminal con el archivo del jurado. Menos vistoso, mismo resultado. |

### Lo que nunca se corta

```
Los tres veredictos
El contraste de dos proveedores
El % de retorno calculado con consultas
```

Eso es la apuesta. Si sobrevive, hay pitch aunque el resto esté con alambres.

### Decisiones ya tomadas

Para no rediscutirlas en la madrugada.

- **AMLSim pregenerado desde el minuto uno.** Nadie intenta compilarlo. Está confirmado que el generador no corre en Python moderno: la librería que pide es de 2016 y falla al importar.
- **Nada de XML.** Todo relacional. Si el demo necesita mostrar una factura, es un recuadro con los campos.
- **Solo dos tipologías:** ciclo y dispersión. Las otras siete no salen en tres minutos.
- **Aritmética en consultas, nunca en el modelo.** Ningún monto en pesos sale del modelo de lenguaje.
- **Modelo local con caché desde el inicio.** El propio reto advierte que el nivel gratuito de las APIs comerciales tiene límite diario y este track hace muchas llamadas por investigación.

---

## 4 — Reparto

Con cuatro personas el riesgo no es falta de manos: son los bloqueos. Si dos esperan a que una termine, se perdieron dos personas.

Por eso el reparto se organiza de modo que nadie dependa del código de otro, solo del contrato de datos, que se congela en las primeras cuatro horas.

### Los cuatro roles

| Rol | Responsabilidad |
|---|---|
| **A · Datos** | Genera el data estate: las 5 tablas coherentes, los escenarios sembrados, el inyector. Es el rol más grande y el más crítico: todos dependen de que existan datos. |
| **B · Ingesta y consultas** | Carga el 69-B y AMLSim. Escribe los detectores deterministas y todas las consultas que el agente invoca como herramientas, incluido el recorrido de grafo y el cálculo del % de retorno. |
| **C · Agente** | El loop de investigación, el gate de tres veredictos, la persistencia del razonamiento. Consume las herramientas de B. |
| **D · Interfaz y demo** | Drop de archivo, grafo, vista comparativa, case file. Es el dueño del demo: quien opera y quien ensaya. |

### El orden temporal

```
H+0 a H+4    LOS CUATRO JUNTOS
             Contrato de datos. Nada de código.

H+4 a H+8    A: genera datos
             B: ingesta 69-B + AMLSim
             C: esqueleto del agente con datos
                falsos escritos a mano
             D: UI con datos falsos escritos
                a mano

H+8 a H+14   A termina y ayuda donde falte
             B entrega las herramientas
             C conecta con B
             D conecta con C

H+14         PIPELINE COMPLETO. Checkpoint duro.

H+14 a H+20  Nivel 2. A hace la métrica,
             porque ya conoce el ground truth.

H+20 a H+25  Integración, pulido, arreglos.
H+25 a H+28  Ensayo. Código congelado.
```

La clave del tramo H+4 a H+8: C y D trabajan con datos inventados a mano. No esperan a A. Eso es lo que evita que dos personas queden ociosas las primeras horas.

### Si el reparto acaba siendo más flexible

Lo más probable es que termine siendo una o dos personas cubriendo A, B y C, y otra en D. Está bien. Dos cosas siguen importando:

- **Que A-B-C no quede en una sola persona.** Datos, ingesta y agente son la ruta crítica entera. Si eso queda en una persona y las otras orbitan, hay un cuello de botella con tres personas esperando.
- **Que D tenga dueño claro.** Es lo único que el jurado ve, y alguien tiene que ensayar. Ese sí es un rol, no una tarea.

Los checkpoints por hora siguen sirviendo aunque el reparto sea difuso. De hecho sirven más: son lo único que estructura el tiempo cuando la gente se mueve entre tareas.

### Cómo asignar según perfiles

- Quien sepa más de datos y consultas → **A o B**
- Quien haya tocado APIs de modelos o prompting → **C**
- Quien sea más rápido en frontend → **D**
- Quien mejor explique → narra el pitch, idealmente alguien de A o C, porque son los que entienden el porqué

### Dos reglas de coordinación

- **Checkpoint cada 4 horas, cinco minutos, de pie.** Cada quien dice qué terminó y en qué está bloqueado. No es reporte de avance: es detección de bloqueos.
- **Ramas separadas, integración temprana.** La primera integración a H+8, no a H+20. Un merge a las dos de la mañana entre cuatro personas cansadas es una forma clásica de perder un hackathon.

### Sueño

Escalonado, no todos a la vez. Dos duermen en un bloque y dos en el siguiente, de modo que siempre haya dos personas despiertas y el proyecto no se detenga.

Y una regla dura: **nadie toca el código en las últimas tres horas.** Esas son para ensayar. El equipo que sigue programando a media hora del pitch es el que presenta algo roto.

---

## 5 — Pendientes

Decisiones abiertas que no bloquean el arranque.

### Color y comportamiento de los nodos

Hay una propuesta del equipo de colorear los nodos por porcentaje de probabilidad de fraude —amarillo entre 50 y 90, rojo arriba de 90— y que al hacer clic se muestre la explicación.

La parte visual es buena: un mapa de calor es la forma correcta de que el jurado entienda el resultado de un vistazo, y el clic para ver el detalle es acertado.

La objeción es sobre el número, no sobre el color. Un porcentaje invita a la pregunta «¿por qué 73 y no 68?», que no tiene respuesta defendible porque los pesos los pusimos nosotros. Y contradice la apuesta: los tres veredictos son categóricos y salen de reglas legales, no de un modelo estadístico.

Propuesta alternativa, conservando lo visual:

| Color | Veredicto | Definición |
|---|---|---|
| VERDE | DEFENDIBLE | hay expediente completo |
| AMARILLO | CORREGIR | falta documentación, sin señales de simulación |
| ROJO | ACUSACIÓN | retorno de fondos comprobado |
| GRIS | LIMPIO | desvirtuado o sin hallazgos |

Mismos colores, misma intuición, pero cada uno con una definición que se puede defender. Y al hacer clic se muestra la cadena de evidencia, no el cálculo.

Si se quiere conservar algo cuantitativo en el nodo, hay dos cifras que sí son defendibles porque salen de los datos y no de un modelo: el porcentaje de retorno del dinero y el monto en pesos.

Pendiente de discutir en equipo. No bloquea nada: el color es cómo se presenta el veredicto, no cómo se calcula, así que el backend no cambia según lo que se decida.

### Herramientas de otros premios

Falta decidir qué patrocinadores se integran. Afecta a la arquitectura, no a la planeación.

El caso más relevante es el almacén de datos: si se usa una base orientada a series de tiempo, eso define dónde viven las tablas y conviene saberlo antes de congelar el esquema en H+4.

---

## Siguiente fase

Con la planeación cerrada, sigue arquitectura: el esquema concreto de las cinco tablas, las herramientas que el agente invoca, el loop de investigación y dónde vive cada cosa.

El contrato de datos que sale de ahí es lo que se congela en H+4.

---

## Recordatorio

```
Tres veredictos accionables,
probados con el flujo del dinero,
medidos con ground truth.

Si una tarea no sirve a esa frase, se corta.
```
