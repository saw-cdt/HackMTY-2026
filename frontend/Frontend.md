Frontend — especificación

The Forensic Auditor — HackMTY 2026

Esta es la pantalla del demo en vivo. Complementa la sección «2 — El demo» de docs/Planeacion_v2_Forensic_Auditor.md y la sección 5 de docs/Arquitectura_Forensic_Auditor_HackMTY2026.md (v1), que sigue siendo la única fuente de la coreografía del grafo.

Qué NO es

El frontend no es el case file. Son dos artefactos distintos:

	Case file	Frontend
Lo genera	El backend, como HTML autocontenido	Vite + React
Lo lee	Un juez, solo, sin narración	El jurado mientras el equipo narra
Se califica por	Clarity	Nada directamente; es el vehículo del demo

Si el frontend intenta ser las dos cosas, acaba siendo malo en las dos.

Lo que consume

Un solo submission.json. Pero el formato oficial no trae datos de visualización, así que hace falta un bloque extra.

El validador oficial solo verifica que existan las llaves requeridas; no rechaza llaves adicionales. Así que se agrega un bloque de nivel superior sin tocar findings:

json
{
  "seed": 1,
  "findings": [...],
  "leads_not_pursued": [...],
  "run_metadata": {...},

  "ui": {
    "company": {"rfc": "...", "name": "..."},

    "nodes": [
      {"id": "RFC:AAAA010101AA1",
       "label": "Consultores del Norte SA",
       "type": "vendor|employee|company",
       "state": "neutral|dismissed|flagged|accused",
       "step": 3}
    ],

    "edges": [
      {"from": "RFC:AAAA010101AA1",
       "to": "EMP:0001",
       "amount": 800000,
       "date": "2024-04-02",
       "exhibit_id": "EX-02",
       "step": 4}
    ],

    "highlight": {
      "accused":  "RFC:AAAA010101AA1",
      "dismissed": "RFC:BBBB020202BB2"
    },

    "context": {
      "RFC:AAAA010101AA1": {
        "signal": "efos_sin_soporte",
        "tool_calls_made": ["vendor", "support_for", "trace_money"],
        "challenger_argument": "..."
      }
    }
  }
}

Regla dura: nunca meter campos de UI dentro de findings. Ese objeto lo lee el validador oficial y se cita en el case file.

Lo que esto le pide al backend

Hoy signal y tool_calls_made solo existen en leads_not_pursued. Para que el contraste alinee sus filas, los hallazgos acusados también los necesitan — dentro de ui.context, no dentro del finding.

Las cuatro pantallas

Son cuatro estados, no cuatro páginas.

1. Reposo

Zona de drop y nada más. Logo, una línea de contexto, el área para soltar el .db.

Esto es lo que se ve durante los primeros 45 segundos del pitch, así que tiene que verse limpio en proyector.

2. Corriendo

El grafo construyéndose. Ocupa los ~50 segundos de narración mientras el agente trabaja.

3. Resultado

Grafo completo, el contraste abierto automáticamente, los tres números visibles.

4. Leads descartados

La lista completa, con búsqueda. No se muestra durante los tres minutos. Existe para la pregunta sorpresa.

El grafo
La coreografía

Seis pasos, de la arquitectura v1 §5, adaptados al esquema nuevo:

paso 1  empresa al centro, proveedores alrededor,
        todos en estado neutral
paso 2  se atenúan los descartados
paso 3  los candidatos se marcan
paso 4  salen aristas del sospechoso,
        aparecen los intermediarios
paso 5  las aristas convergen
paso 6  se revela el destino: un empleado
        o la propia empresa

El paso 2 es el diferenciador visual. Es el agente descartando. Nadie más va a mostrar lo que no persiguió, y mostrarlo es literalmente un criterio del track.

El paso 6 es el clímax. La revelación del titular de la cuenta se guarda para el final. Si desde el paso 4 ya dice «cuenta del empleado», se pierde el momento.

Cómo se anima sin streaming

El backend marca step en cada nodo y arista. El frontend recibe el JSON completo y va revelando los elementos con un retardo.

Es mucho más simple que abrir un canal en vivo, y si aplica el corte del grafo progresivo, se quita el retardo y aparece todo de golpe: misma estructura, menos código.

Restricciones duras
Posiciones fijas. Nada de auto-layout que reacomode los nodos al aparecer uno nuevo. El jurado pierde el hilo.
Sin zoom ni desplazamiento durante el demo. Una vista, completa y legible.
Máximo 12 a 15 nodos visibles. Con cuarenta no se ve nada.
Sin animación de partículas ni dinero volando. Se ve de juguete y distrae. Aristas que aparecen, y ya.
Estados y color
Estado	Significado
neutral	Aún no evaluado
dismissed	Descartado, se atenúa
flagged	Candidato bajo investigación
accused	Hallazgo publicado

El color sale del estado, nunca de un porcentaje de probabilidad.

El contraste

El momento del minuto 1:40. Dos tarjetas lado a lado, con las filas alineadas para que la comparación se lea de un vistazo.

                      ACUSADO            DESCARTADO
Señal que lo marcó    <signal>           <signal>
Herramientas          <tool_calls>       <tool_calls>
Qué mostró            <evidencia>        <evidencia>
Retador argumentó     <argument>         <argument>
Resultado             ACUSACIÓN          cerrado por challenger

Las dos entidades salen de ui.highlight, elegidas por el backend. No se hace clic en vivo: las tarjetas se abren solas al terminar la corrida.

La razón es de nervios, no de diseño. Un clic que no registra cuesta diez segundos en el minuto más importante.

El clic sí se implementa, pero se usa en la pregunta sorpresa, donde no está cronometrado.

La lista de leads

Existe por una regla concreta: los jueces escogen una entidad de los descartados y preguntan por qué no la señalaste. La respuesta tiene que leerse en menos de diez segundos, desde la pantalla, sin volver a correr nada.

Lo mínimo:

Búsqueda por RFC o por nombre
Una tarjeta por lead con: entidad, signal, reason, tool_calls_made, closed_by

Nada más. Si tecleas el RFC y sale la razón, ese punto está ganado.

Los tres números

Visibles en la pantalla de resultado, no escondidos en un menú:

llm_calls           <n>
mxn_cost            $0.00
wall_clock_seconds  <n>

El costo cero con Ollama local es un argumento de Feasibility, no una carencia: un despacho puede correr esto en su propia red sin que los datos del cliente salgan a ninguna API. Que se vea.

Restricción que se olvida

Todo offline. Sin CDN, sin fuentes de Google, sin librerías remotas.

La red del evento va a estar saturada, y los jueces pueden pedir que se demuestre con la conexión apagada.

Si se usa una librería de grafos, tiene que venir en el bundle. Alternativa: dibujar el SVG a mano — con 15 nodos en posiciones fijas es perfectamente viable y quita una dependencia.

Prueba obligatoria: apagar el wifi y recargar. Debe funcionar completo.

Orden de construcción

Si el tiempo aprieta, en este orden:

Drop + resultado estático — grafo completo de golpe
El contraste — las dos tarjetas alineadas
La lista de leads con búsqueda
El grafo progresivo — el retardo por step
La tabla de resultados

Los primeros tres son el demo. El cuarto es estética. El quinto puede ser una imagen estática si hace falta.

Checklist
 Funciona con el wifi apagado
 El contraste se abre solo al terminar, sin clic
 Buscar un RFC en la lista de leads da su razón en menos de 10 segundos
 Los tres números se ven en pantalla
 Máximo 15 nodos, posiciones fijas, sin zoom
 Se ve legible en proyector, no solo en la laptop
 El bloque ui no ensucia findings — make check-format sigue pasando