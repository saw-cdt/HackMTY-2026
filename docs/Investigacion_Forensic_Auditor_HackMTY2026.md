# The Forensic Auditor — Documento de Investigación

**HACKMTY 2026 · Infosys Challenge Track**

*Fase 1 de 4 · Investigación → Planeación → Arquitectura → Desarrollo*

*Equipo de 4 personas · Septiembre 2026*

> [!NOTE]
> Este documento **sigue vigente completo** según la Planeación v2: lo que cambió fue la planeación y la arquitectura, no la investigación de dominio.

---

## Cómo leer este documento

Este documento asume que no sabes nada de facturación, impuestos ni fraude fiscal. Todo se explica desde cero. No necesitas leer nada más para entender el proyecto.

Está organizado así:

- **Parte 1 — El problema.** Qué es el fraude de facturas en México y por qué es difícil de detectar.
- **Parte 2 — La ley.** El artículo 69-B, que es la norma que define todo el caso.
- **Parte 3 — Los recursos.** Los cuatro datasets y herramientas que el reto nos sugiere, qué nos da cada uno y qué no.
- **Parte 4 — Cómo se prueba el fraude.** El razonamiento que nuestro agente tiene que reproducir.
- **Parte 5 — Lo que falta construir.** Las piezas que ningún recurso nos da.
- **Glosario y tarjeta rápida.** Al final, para consultar mientras programas.

### Los cuadros azules

A lo largo del documento vas a encontrar cuadros como este:

> **IMPLICACIÓN DE DISEÑO — ejemplo**
>
> Estos cuadros no son información del tema: son decisiones o consecuencias para nuestro proyecto. Son el puente entre la investigación y la planeación.

Todo lo demás son hechos del dominio. La distinción importa: los hechos no se discuten, las implicaciones sí.

### Terminología

Cada término se define la primera vez que aparece. Si algo se te olvida, el glosario está al final, dividido en tres secciones: términos fiscales, términos de fraude y términos técnicos.

**Regla del equipo: un concepto, un nombre.** Si el documento dice «factura falsa», no escribimos «CFDI apócrifo» ni «comprobante simulado» en otro lado. Ese vocabulario se va a convertir en nombres de tablas y de funciones, así que la consistencia aquí nos ahorra confusión en el código.

---

## Parte 1 — El problema

### Un caso que vamos a usar todo el documento

Imagina una empresa constructora en Monterrey. En marzo de 2024 registra en su contabilidad una factura:

```
Proveedor:  CONSULTORES DEL NORTE SA DE CV
Concepto:   "Servicios de consultoría administrativa"
Monto:      $2,400,000.00
Fecha:      15 de marzo de 2024
```

La factura es real. Está registrada ante la autoridad fiscal, tiene sello digital y folio oficial. Contablemente es impecable.

**El problema es que la consultoría nunca ocurrió.**

CONSULTORES DEL NORTE no tiene empleados. No tiene oficinas. Su domicilio fiscal es una casa en un fraccionamiento. Su único negocio es vender facturas: cobra una comisión del 8% y emite comprobantes por servicios que jamás presta.

La constructora usó esa factura para pagar menos impuestos. Y buena parte de los $2,400,000 regresó, después de dar tres vueltas por otras empresas, a la cuenta personal de uno de sus socios.

Ese es el fraude que nuestro agente tiene que encontrar y probar.

### Por qué esto es difícil

Si fuera cuestión de buscar facturas raras, ya estaría resuelto. Los tres obstáculos reales son:

- **La factura es válida.** No hay nada en el documento que delate el fraude. Cumple todos los requisitos legales. Lo que no existe es la operación detrás.
- **Las señales aisladas no prueban nada.** Un proveedor sin empleados puede ser un consultor independiente legítimo. Un pago grande puede ser una compra real. Una empresa en la lista negra puede haber sido exonerada. Ninguna señal sola sostiene una acusación.
- **Hay que seguir el dinero.** La prueba no está en la factura, está en el movimiento bancario posterior: a dónde fue el dinero después de pagarse.

El reto de Infosys lo plantea así: las herramientas actuales marcan cosas raras una por una y dejan que una persona las conecte. Nadie sigue el dinero hasta el final, nadie construye la prueba, y proveedores honestos que simplemente se ven raros terminan acusados.

### Los tres esquemas que menciona el reto

| Esquema | En qué consiste |
|---|---|
| Factura falsa | Una empresa fantasma cobra por trabajo que nunca hizo. El cliente deduce el gasto y paga menos impuestos. |
| Kickback (moche) | Un proveedor factura de más y devuelve la diferencia por debajo de la mesa, normalmente a través de una empresa intermedia. |
| Ventas simuladas | Se inventan ventas para inflar los números de la empresa, por ejemplo para conseguir un crédito o presentar mejores resultados. |

Esto importa para nuestra estrategia: solo el primero se detecta con la lista de la autoridad fiscal. Los otros dos únicamente se ven siguiendo el dinero.

---

## Parte 2 — La ley: artículo 69-B

El artículo 69-B del Código Fiscal de la Federación es la herramienta legal con la que el SAT ataca este fraude. Entenderlo no es un requisito burocrático: define exactamente qué puede y qué no puede afirmar nuestro agente.

El **SAT** es el Servicio de Administración Tributaria, la autoridad fiscal de México. Equivale al IRS estadounidense.

### Los dos lados: EFOS y EDOS

Esta distinción es la columna vertebral del tema.

| Término | Significado | En nuestro caso |
|---|---|---|
| **EFOS** | Empresa que Factura Operaciones Simuladas. Quien emite la factura falsa. | CONSULTORES DEL NORTE |
| **EDOS** | Empresa que Deduce Operaciones Simuladas. Quien recibe la factura y la usa para pagar menos impuestos. | La constructora |

Ninguno de los dos términos aparece en la ley. Son nombres prácticos que usa todo el mundo en la práctica fiscal.

**Dato importante:** la lista pública que publica el SAT es de EFOS. Si tu proveedor aparece ahí, el problema pasa a ser tuyo — te conviertes en EDOS.

Un matiz que importa para el modelo de datos: en rigor eres EDOS cuando le diste efecto fiscal a esas facturas, es decir cuando efectivamente las usaste para pagar menos impuestos. Si recibiste la factura pero nunca la usaste, no hay daño que reclamar.

### En qué se basa la sospecha del SAT

El SAT presume que las operaciones son inexistentes cuando detecta que una empresa emitió facturas sin contar con los activos, el personal, la infraestructura o la capacidad material para prestar esos servicios o entregar esos bienes. También basta con que la empresa esté «no localizada» en su domicilio fiscal.

Traducido: una empresa que facturó 40 millones en servicios de ingeniería pero no tiene un solo empleado registrado ni oficinas. Ese es el perfil.

### El procedimiento y sus plazos

| Etapa | Plazo |
|---|---|
| El SAT notifica la sospecha (buzón tributario, portal y Diario Oficial) | — |
| La empresa acusada aporta pruebas | 15 días hábiles |
| Prórroga automática | +5 días |
| La autoridad valora las pruebas y resuelve | 50 días |
| Publicación en el listado definitivo | — |
| El cliente (EDOS) acredita materialidad o corrige su declaración | 30 días desde la publicación |

Dos detalles que no son obvios:

- **El reloj se puede parar.** Si la autoridad pide información adicional durante la valoración, el plazo se suspende. Por eso una empresa puede quedarse en estatus de sospecha mucho más de 50 días sin que eso signifique nada.
- **El cliente tiene dos salidas, no una.** Puede acreditar la materialidad —demostrar que la operación sí ocurrió, con contrato, evidencia de entrega y pago bancario rastreable— o puede corregir, es decir presentar declaraciones nuevas que eliminen ese beneficio fiscal y pagar la diferencia.

> **IMPLICACIÓN DE DISEÑO — el gate de acusación sale de la ley**
>
> La materialidad se prueba con tres elementos: contrato, evidencia de entrega y pago rastreable. Esos tres son exactamente los campos que debe tener nuestra cadena de evidencia. No tenemos que inventar el criterio: el marco legal ya nos lo definió.
>
> Nuestro agente no acusa a nadie sin poder llenar esos tres huecos más el estatus del proveedor y un monto en pesos.

### Los cuatro estatus

Aquí está el matiz que casi nadie modela bien, y donde está nuestra mayor ventaja.

| Estatus | Qué significa | ¿Acusamos? |
|---|---|---|
| **Presunto** | El SAT inició el procedimiento. La empresa todavía está en plazo para defenderse. Sus facturas aún no son inválidas. | No. Solo es señal de riesgo. |
| **Definitivo** | No logró defenderse, o no contestó. Confirmado. | Solo con el resto de la evidencia. |
| **Desvirtuado** | Presentó pruebas suficientes. Sus facturas recuperan validez. | NO. Está limpia. |
| **Sentencia favorable** | Ganó en tribunales. | NO. Está limpia. |

Dos de los cuatro estatus significan que el contribuyente está limpio. Aparecer «en la lista 69-B» no equivale a ser culpable.

> **IMPLICACIÓN DE DISEÑO — los cuatro estatus son nuestro diferenciador**
>
> La mayoría de los equipos va a tratar la lista como binaria: si el RFC está, acusa. Eso va a marcar como fraude a empresas desvirtuadas y con sentencia favorable, que son justamente los «proveedores honestos que se ven raros» que el reto pide no acusar.
>
> Vamos a sembrar a propósito, en nuestros datos de prueba, un proveedor desvirtuado y uno con sentencia favorable que se vean estadísticamente sospechosos. Que el agente los descarte en vivo es nuestro mejor momento frente al jurado.

### El efecto es retroactivo

Esta es la parte que más nos sorprendió y la que define el problema del reto.

Cuando el SAT publica el listado definitivo, la ley dice que las facturas de esa empresa «no producen ni produjeron efecto fiscal alguno». Ese «ni produjeron» es retroactividad explícita.

En nuestro caso: si CONSULTORES DEL NORTE se vuelve definitivo en agosto de 2025, la factura que emitió en marzo de 2024 también queda invalidada. No importa que en ese momento estuviera limpia.

Por eso el reto dice que para cuando un proveedor aparece en la lista, la empresa ya usó las deducciones y ya está en problemas. El daño histórico es la mayor parte del daño.

> **IMPLICACIÓN DE DISEÑO — la consulta es temporal, de doble sentido**
>
> No preguntamos «¿está hoy en la lista?». Comparamos la fecha de la factura contra la fecha de publicación del estatus definitivo:
>
> ```
> factura ANTES del definitivo    -> problema fiscal real,
>                                    compatible con buena fe
>
> factura DESPUÉS del definitivo  -> contrató con una empresa
>                                    ya señalada públicamente:
>                                    indicio fuerte de intención
>
> estatus desvirtuado o           -> NO SE ACUSA
> sentencia favorable
> ```
>
> La fecha no decide si hay problema; decide qué tan grave es.

### La carga de la prueba

Un detalle legal con consecuencia directa en nuestro diseño: la ley pone la carga en el receptor. No es el SAT quien debe demostrar que la operación no ocurrió; es la empresa quien debe demostrar que sí ocurrió.

Un agente forense que replica esa lógica pide evidencia positiva de materialidad, no ausencia de sospecha. Es una diferencia sutil pero cambia cómo se escribe el razonamiento.

### Dos cosas que NO son parte de esto

- **El artículo 69-B Bis** es otra norma. Trata sobre transmisión indebida de pérdidas fiscales: una empresa con pérdidas se fusiona con otra para que esta las aproveche sin razón de negocio real. Tiene su propia lista. No lo mezclamos.
- **El artículo 69 a secas** es una lista distinta y también pública: empresas con adeudos fiscales firmes, no localizadas, con sentencia por delito fiscal, o con su certificado de sello digital cancelado. No prueba fraude de facturas, pero sirve como señal de riesgo secundaria.

---

## Parte 3 — Los recursos

El reto nos sugiere cuatro fuentes públicas y gratuitas. Investigamos las cuatro. Este es el resultado.

| Recurso | Qué nos da | Prioridad |
|---|---|---|
| Lista 69-B del SAT | Qué empresas están señaladas como emisoras de facturas falsas, y desde cuándo | Alta |
| CFDI 4.0 (Anexo 20) | La estructura real de una factura mexicana | Alta |
| IBM AMLSim | Movimientos bancarios sintéticos con patrones de fraude ya etiquetados | Alta |
| IEEE-CIS (Kaggle) | Referencia metodológica de detección de anomalías | Descartado |

### 3.1 — La lista 69-B del SAT

#### Qué es

El listado público de empresas bajo el procedimiento del artículo 69-B. Es un oráculo de estatus por RFC: le preguntas por una empresa y te dice en qué situación está.

**RFC** significa Registro Federal de Contribuyentes. Es el identificador fiscal único de toda persona o empresa en México, el equivalente al RUC o al EIN. Doce caracteres para empresas, trece para personas físicas. Ejemplo: `CDN190312AB1`.

En nuestro proyecto el RFC es la llave primaria de todo: es lo que conecta la lista del SAT con las facturas y con el catálogo de proveedores.

#### Dónde se descarga

```
Portal:
omawww.sat.gob.mx/cifras_sat/Paginas/datos/
    vinculo.html?page=ListCompleta69B.html

Descarga directa (usar SIEMPRE el listado completo):
omawww.sat.gob.mx/cifras_sat/Documents/
    Listado_Completo_69-B.csv
```

Hay cinco archivos disponibles: completo, presuntos, definitivos, desvirtuados y sentencias favorables. Usamos el completo, por la razón que se explica abajo.

#### Cómo viene por dentro

Esta fue la mejor sorpresa de la investigación. No es una tabla de «RFC más estatus». Es una fila por empresa con toda su historia en columnas:

```
id
rfc
nombre_Contribuyente
situacion_del_contribuyente          <- estatus actual
numero_y_fecha_oficio_global_presuncion
publicacion_pagina_SAT_presuntos
publicacion_DOF_presuntos
numero_fecha_oficio_global_contribuyentes_que_desvirtuaron
publicacion_pagina_SAT_desvirtuados
publicacion_DOF_desvirtuados
numero_fecha_oficio_global_definitivos
publicacion_pagina_SAT_definitivos
publicacion_DOF_definitivos
numero_fecha_oficio_global_sentencia_favorable
publicacion_pagina_SAT_sentencia_favorable
publicacion_DOF_sentencia_favorable
```

El archivo trae la línea de tiempo completa de cada empresa: cuándo fue sospechosa, cuándo definitiva, cuándo se defendió. Eso significa que la consulta temporal que necesitamos —«¿estaba señalada cuando me facturó?»— se resuelve con este solo archivo, sin cruzar listas.

**DOF** es el Diario Oficial de la Federación, donde se publican oficialmente las resoluciones. El «oficio» es el documento numerado con el que el SAT notifica, en formato `500-05-AAAA-NNNNN`. Ese número es una cita verificable: un auditor lo puede buscar.

#### Escala

Más de 14,000 RFCs históricos. Un conteo reciente da alrededor de 5,539 vigentes: 4,558 definitivos, 282 presuntos, 139 desvirtuados y 560 con sentencia favorable. El SAT sumó 903 definitivos solo entre enero y junio de 2026, así que la lista se mueve constantemente.

#### Lo que NO trae

- **Montos.** No dice cuánto facturó ninguna empresa.
- **La relación emisor–receptor.** Quién le compró a quién no es público.
- **Datos de capacidad:** empleados, activos, domicilio. La razón concreta por la que el SAT la señaló no viene explicada.
- **Sector o giro** de la empresa.

> **IMPLICACIÓN DE DISEÑO — la lista es oráculo, no evidencia**
>
> Confirma que un proveedor está señalado. No prueba nada sobre nuestro cliente. La evidencia sale del resto de nuestros datos.
>
> En el expediente final, una cita a la lista respalda el estatus del proveedor y nada más. El fraude se prueba con la cadena de materialidad.

> **IMPLICACIÓN DE DISEÑO — dos trampas técnicas detectadas**
>
> 1. **Encoding.** El servidor entrega el archivo como binario. Lo más probable es que sea Latin-1 o Windows-1252, no UTF-8. Si se abre asumiendo UTF-8, los acentos y las eñes se rompen.
> 2. **Posible desalineación de columnas.** En los ejemplos que revisamos, campos que deberían traer fecha traían el número de oficio con la fecha embebida en texto. Antes de escribir el parser: descargar, imprimir las primeras 20 filas crudas, revisar si hay líneas de preámbulo antes del encabezado, y validar columna por columna.
>
> Media hora aquí ahorra tres el sábado en la madrugada.

> **IMPLICACIÓN DE DISEÑO — normalizar en la carga, no en la consulta**
>
> RFC en mayúsculas sin espacios. Nombres con espacios sobrantes recortados. Fechas convertidas a tipo fecha real; si vienen embebidas en texto, extraerlas con expresión regular en este paso.
>
> Si normalizamos al momento de consultar, el agente va a fallar por un espacio en blanco y nadie va a entender por qué.

> **IMPLICACIÓN DE DISEÑO — pivotear a tabla de eventos**
>
> El archivo es ancho: una fila por empresa con cuatro etapas en columnas. Para consultar por fecha conviene una tabla larga:
>
> ```
> rfc | etapa | fecha_dof | fecha_portal | oficio
> ```
>
> Así «¿qué estatus tenía esta empresa el día D?» es una consulta normal. El agente la va a llamar decenas de veces por investigación, así que tiene que ser barata.

> **IMPLICACIÓN DE DISEÑO — la fecha del DOF es la que manda**
>
> Las dos fechas de publicación (portal y Diario Oficial) no coinciden. Usamos la del DOF para efectos legales y guardamos la del portal como referencia.

> **IMPLICACIÓN DE DISEÑO — congelar una copia**
>
> La lista se actualiza sin calendario fijo. Descargamos una copia el viernes y trabajamos con ella todo el fin de semana. No la volvemos a bajar.

### 3.2 — CFDI 4.0, la factura mexicana

#### Qué es

**CFDI** significa Comprobante Fiscal Digital por Internet. Es la factura electrónica mexicana, y no es un PDF: es un archivo XML con estructura definida por el SAT. El PDF que te dan en una tienda es solo una representación visual; el documento fiscal real es el XML.

Para que una factura sea válida, un tercero autorizado la sella digitalmente y le asigna un folio único. A eso se le llama **timbrado**, y al folio se le llama **UUID** o folio fiscal. Sin timbre, la factura no existe fiscalmente.

La guía técnica oficial que define todo esto se llama **Anexo 20** y la publica el SAT.

#### Anatomía

```
Comprobante  <- nodo raiz
|- Version, Fecha, Total, SubTotal, Moneda,
|  TipoDeComprobante, FormaPago, MetodoPago
|
|-- Emisor    -> Rfc, Nombre, RegimenFiscal
|-- Receptor  -> Rfc, Nombre, RegimenFiscal,
|                DomicilioFiscalReceptor, UsoCFDI
|-- Conceptos -> ClaveProdServ, Cantidad, Descripcion,
|                ValorUnitario, Importe, ObjetoImp
|-- Impuestos -> traslados / retenciones
|-- Complemento -> TimbreFiscalDigital (UUID, FechaTimbrado)
```

Tres campos importan más de lo que parece:

- **`TipoDeComprobante`** define la naturaleza del documento: `I` de ingreso (una venta), `E` de egreso (nota de crédito, para devoluciones y descuentos), `T` de traslado, `N` de nómina, `P` de pago.
- **`FormaPago` y `MetodoPago` no son lo mismo,** aunque suenen igual. `FormaPago` es *con qué* se pagó: efectivo, transferencia, cheque. `MetodoPago` es *cuándo*: PUE significa pago en una sola exhibición, PPD significa pago en parcialidades o diferido.
- **`ClaveProdServ`** es la clave del catálogo oficial que clasifica qué producto o servicio se está facturando. Es obligatoria en cada partida.

#### El hallazgo más útil: el complemento de Pagos

Cuando el método de pago es PPD (diferido), la ley obliga a emitir un comprobante adicional por cada pago que se recibe. A ese comprobante se le llama **REP**, Recepción de Pagos, y liga el pago con el folio de la factura original.

Eso es exactamente el puente entre las facturas y los movimientos bancarios que necesitamos. No hay que inventarlo: el marco fiscal mexicano ya lo definió.

Y nos da una señal de fraude gratis: una factura diferida sin su comprobante de pago correspondiente es una operación que se facturó pero nunca se pagó, o que se pagó fuera de libros.

> **IMPLICACIÓN DE DISEÑO — el REP es nuestra tabla de reconciliación**
>
> Modelamos una tabla de pagos con el folio de la factura relacionada, la fecha, el monto y la forma de pago. Ese es el adaptador hacia los movimientos bancarios, y tiene respaldo normativo en lugar de ser una invención nuestra.

#### Qué NO vamos a hacer

- **No validar el sello digital** ni generar la cadena original. Es criptografía con certificados del SAT. Se lleva medio hackathon y no da un solo punto de calificación. Nuestras facturas son sintéticas; nadie las va a timbrar.
- **No implementar los complementos completos** (Carta Porte, Comercio Exterior, Nómina). No los necesitamos.
- **No trabajar con XML en tiempo de ejecución.** Definimos la estructura una vez, generamos los datos y los guardamos en tablas.

> **IMPLICACIÓN DE DISEÑO — CFDI es nuestro contrato de datos, no una fuente de fraude**
>
> El Anexo 20 nos da la forma de la factura; el contenido fraudulento lo generamos nosotros. No hay que buscar señales de fraude en la norma: no existen.
>
> Lo que ganamos es credibilidad. Si nuestras facturas tienen los campos reales con los nombres reales, el jurado de Infosys las reconoce al instante.

> **IMPLICACIÓN DE DISEÑO — el folio (UUID) es nuestra ancla de citas**
>
> Toda afirmación del expediente apunta a un folio. «El proveedor X facturó 2.3 millones sin materialidad» no sirve. «Folio a3f2-…, $2,300,000, sin contrato ni evidencia de entrega» sí.
>
> Esto es lo que satisface el criterio de viabilidad del reto: un auditor real busca el folio y verifica.

> **IMPLICACIÓN DE DISEÑO — señales de fraude que salen de campos legítimos**
>
> Estas son baratas de implementar y suenan sofisticadas:
>
> ```
> - Clave de producto genérica en montos altos
>     (consultoria, asesoria, publicidad): el perfil
>     clasico, porque son servicios sin entregable
>     fisico verificable
> - Descripcion vaga y repetida identica en
>     facturas de distintos meses
> - Factura diferida sin su comprobante de pago
> - Notas de credito usadas para cancelar y
>     reciclar operaciones
> - Montos redondos y repetidos: la operacion real
>     rara vez da $500,000.00 exactos
> - Fecha de emision y fecha de timbrado muy
>     separadas, o timbrados en bloque a fin de mes
> ```
>
> Ninguna de estas prueba fraude por sí sola. Son heurísticas para decidir dónde vale la pena investigar, no para acusar. Esa distinción es el corazón de nuestro diferenciador.

> **IMPLICACIÓN DE DISEÑO — congelar el esquema desde el inicio**
>
> ```
> uuid, fecha, fecha_timbrado,
> rfc_emisor, nombre_emisor,
> rfc_receptor, nombre_receptor,
> tipo_comprobante, forma_pago, metodo_pago,
> uso_cfdi, subtotal, total, moneda,
> lugar_expedicion
> ```
>
> Más conceptos y pagos en sus propias tablas. Si agregamos campos después, hay que regenerar todos los datos.
>
> Los catálogos oficiales son enormes (el de productos tiene decenas de miles de entradas). Usamos entre 20 y 30 claves reales. Nadie va a verificar que usemos el catálogo completo; sí van a notar claves con formato inválido.

### 3.3 — IBM AMLSim

#### Para qué lo necesitamos

Esta es la pregunta que más costó trabajo responder, así que vale la pena ser explícito.

Hasta aquí tenemos dos fuentes. La lista del SAT nos dice qué empresas están señaladas, pero no trae un solo peso. Las facturas nos dicen que se facturó, pero no a dónde fue el dinero.

No tenemos movimientos bancarios. Y sin movimientos bancarios no hay dinero que seguir, que es el verbo central del reto.

AMLSim es esa pieza. Es un simulador que genera transferencias bancarias sintéticas con patrones de fraude incluidos y ya etiquetados.

En una frase: **la lista del SAT nos dice a quién sospechar; AMLSim nos deja probarlo.**

#### Los dos usos

- **Uso 1 — nos da los datos bancarios.** Un archivo de transferencias con cuenta de origen, cuenta de destino, monto y fecha. Es nuestro estado de cuenta sintético. El agente lo recorre para responder a dónde fue el dinero.
- **Uso 2 — nos da la respuesta correcta.** Este es el que más vale y es el menos obvio. Cada transferencia viene marcada según si pertenece a un esquema de fraude o no. A eso se le llama **ground truth**: la verdad conocida de antemano contra la cual mides tu sistema.

Gracias a eso podemos correr el agente y medir: de los 40 esquemas que sembré, encontró 31, y acusó a 4 cuentas limpias. Eso es un número que le podemos enseñar al jurado. Los otros equipos van a decir «nuestro agente funciona bien».

#### Las nueve tipologías

```
cycle           <- el dinero regresa al origen
fan_in          <- muchas cuentas -> una (recoleccion)
fan_out         <- una cuenta -> muchas (dispersion)
scatter_gather  <- dispersa y vuelve a juntar
gather_scatter  <- junta y vuelve a dispersar
bipartite       <- dos grupos, relaciones no obvias
stack           <- capas encadenadas
random
```

Se configuran en un archivo plano. Le decimos cuántos esquemas de cada tipo queremos, con cuántas cuentas, qué rango de montos y en qué ventana de tiempo:

```
count,type,min_accounts,max_accounts,
min_amount,max_amount,min_period,max_period,is_sar
40,cycle,5,10,100.0,200.0,5,20,True
30,fan_in,5,10,100.0,200.0,5,20,True
```

Eso es, en la práctica, nuestro inyector de esquemas parametrizado.

#### Qué archivos produce

```
transactions.csv
    tran_id, orig_acct, bene_acct, tx_type,
    base_amt, tran_timestamp, is_sar, alert_id

accounts.csv
    acct_id, dsply_nm, type, acct_stat, open_dt,
    close_dt, initial_deposit, bank_id, country, ...

alert_transactions.csv    <- GROUND TRUTH
    alert_id, alert_type, is_sar, tran_id,
    orig_acct, bene_acct, base_amt, tran_timestamp

alert_accounts.csv        <- GROUND TRUTH
    alert_id, alert_type, acct_id, is_sar,
    start, end, bank_id
```

Los dos últimos archivos son la respuesta correcta: qué cuentas y qué transacciones pertenecen a cada esquema sembrado.

> **IMPLICACIÓN DE DISEÑO — la respuesta correcta se usa para medir, nunca para decidir**
>
> Los archivos de alertas se guardan FUERA del alcance del agente. Si el agente puede leer la etiqueta de fraude, no estamos midiendo nada.
>
> Nuestra métrica sale de comparar lo que acusó contra esos archivos. De ahí salen la precisión (de todo lo que acusó, cuánto era realmente fraude) y el recall (de todo el fraude que había, cuánto encontró). Es el único dato duro que le vamos a poder enseñar al jurado.

#### Riesgos de instalación — verificados con pruebas

Descargamos el repositorio y lo probamos. Estos problemas están confirmados, no supuestos.

**El generador NO corre en Python moderno.** El proyecto pide una versión de la librería networkx de 2016. Al instalarla en Python 3.12, falla al importar:

```
ImportError: cannot import name 'gcd' from 'fractions'
```

Esa función se eliminó de Python en la versión 3.9. Se necesita Python 3.8. Si alguien intenta esto en su Python actual el sábado en la madrugada, va a perder horas sin entender por qué.

Otros dos: una de las dependencias requiere Graphviz instalado a nivel sistema (no basta con pip), y la parte del simulador compila en Java 8 con Maven.

#### La salida de emergencia

El repositorio incluye conjuntos de datos ya generados:

```
20K_cycle200.tgz           20,000 cuentas
20K_fanin200.tgz           945 marcadas como fraude
20K_fanin200cycle200.tgz   117,805 transacciones

Formato (mas simple que la salida actual):
nodes.csv         nodeid, isFraud, init_balance, fraudStep
transactions.csv  sourceNodeId, targetNodeId, value, time
```

Traen la etiqueta de fraude, que es lo que realmente necesitamos. Si la instalación se atora, descomprimimos uno de estos y seguimos trabajando.

> **IMPLICACIÓN DE DISEÑO — timebox de 2 horas, empezando por el archivo pregenerado**
>
> Descomprimir uno de los archivos de ejemplo en los primeros 15 minutos. Con eso ya hay datos de flujo con etiquetas y el resto del equipo puede avanzar.
>
> La instalación completa corre en paralelo, fuera de la ruta crítica. Si a las dos horas no compila, nos quedamos con el ejemplo y nadie pierde nada.

> **IMPLICACIÓN DE DISEÑO — el adaptador cuenta → RFC**
>
> AMLSim habla de cuentas bancarias; nuestro caso habla de contribuyentes. Hay que construir el puente:
>
> ```
> acct_id -> cuenta bancaria -> RFC del titular
>                            -> proveedor o cliente
> ```
>
> Un RFC puede tener varias cuentas. Eso es realista y además es un vector de fraude: dispersar pagos entre cuentas del mismo titular para no llamar la atención. No lo modelamos uno a uno.

> **IMPLICACIÓN DE DISEÑO — traducir tipologías a esquemas fiscales mexicanos**
>
> Esto es lo que convierte un dataset genérico en nuestro caso de negocio.
>
> ```
> cycle           -> el dinero pagado por la factura
>                    falsa regresa via terceros
> fan_out         -> la empresa dispersa pagos entre
>                    varias fantasmas
> fan_in          -> la factorera recolecta de muchos
>                    clientes: el mercado de facturas
> scatter_gather  -> moche con capas intermedias para
>                    romper el rastro
> ```
>
> En el expediente NO decimos «detecté un fan_in». Decimos: «este proveedor recibe pagos de ocho empresas sin relación entre sí, patrón típico de comercializadora de comprobantes».

> **IMPLICACIÓN DE DISEÑO — ajustes obligatorios a los datos**
>
> **Montos.** El valor por defecto va de 100 a 200 dólares. Necesitamos pesos y montos creíbles de facturación entre empresas: decenas o cientos de miles. Un ciclo de $150 no le va a parecer fraude a nadie.
>
> **Fechas.** La simulación usa pasos discretos con una fecha base de referencia, no fechas reales. Hay que convertir en la carga y alinear ese calendario con las fechas de nuestras facturas. Si las facturas son de 2024 y los pagos de 2017, la reconciliación no existe.
>
> **Formatos distintos.** El ejemplo pregenerado y la salida actual usan nombres de columna diferentes. Normalizamos a NUESTRO esquema en la carga, así podemos cambiar de fuente sin tocar nada más.
>
> **Campos personales.** El archivo de cuentas trae nombre, número de seguro social, fecha de nacimiento y coordenadas. Nada de eso aplica a proveedores mexicanos: lo descartamos en la carga, y de paso evitamos arrastrar datos personales a un demo público.

> **IMPLICACIÓN DE DISEÑO — aleatorizar para no sobreajustar**
>
> Si siempre generamos 200 ciclos de 5 a 10 cuentas con montos de 100 a 200, el agente aprende esa firma y no el fraude. Variamos número de cuentas, montos, periodos y cantidad de esquemas entre corridas.
>
> Y generamos al menos un conjunto SIN ningún patrón sembrado. Un agente que siempre encuentra algo es un agente que siempre acusa.

### 3.4 — IEEE-CIS (descartado)

Un conjunto de datos de Kaggle con transacciones reales de comercio electrónico: 590,540 registros con casi 400 características y una tasa de fraude del 3.5%.

Lo descartamos. Es fraude con tarjeta de crédito en comercio electrónico, no facturación entre empresas. No mapea a nuestro caso. El reto lo menciona solo como referencia de base, y eso es exactamente lo que es: sirve para calibrar qué tan desbalanceado se ve un conjunto de datos de fraude real, y poco más.

Si andamos cortos de tiempo, lo saltamos sin culpa.

---

## Parte 4 — Cómo se prueba el fraude

Esta es la parte central del proyecto. Hay dos preguntas distintas que conviene no confundir:

1. ¿Cómo decide el agente que algo es fraude?
2. ¿Cómo sabemos nosotros si el agente acertó?

La segunda es fácil: los datos son nuestros, así que sabemos las respuestas. Comparamos lo que acusó contra los esquemas que sembramos y sale la métrica. El agente nunca ve esa lista.

La primera es el corazón del proyecto.

### El principio: ninguna señal sola prueba nada

Lo que prueba es la combinación. Y el criterio nos lo da la propia ley: no se trata de demostrar que hubo fraude, se trata de que no se puede demostrar que la operación existió. La carga de la prueba está en el receptor.

De ahí salen las tres preguntas de materialidad:

```
1. ¿Hay contrato o soporte documental?
2. ¿Hay evidencia de entrega del bien o servicio?
3. ¿Hay pago bancario rastreable y limpio?
```

### La escalera de certeza

Cada nivel agrega peso. El agente sube hasta donde la evidencia le alcance.

| Nivel | Evidencia | Qué significa |
|---|---|---|
| 0 | La factura existe y está timbrada | Nada. Todas lo están. |
| 1 | El proveedor está en estatus definitivo | El proveedor está señalado. Todavía no dice nada de nuestro cliente. |
| 2 | + no hay contrato ni orden de compra | Falta soporte documental |
| 3 | + no hay evidencia de entrega | Falta materialidad |
| 4 | + el pago regresa a una cuenta ligada | **Esto es lo que prueba** |
| 5 | + la factura se usó para pagar menos impuestos | Hay daño cuantificable en pesos |

Nivel 1 solo: no se acusa, es sospecha. Nivel 4 o 5: se acusa, con la cadena completa.

El nivel 4 es el que solo se alcanza con datos bancarios. Por eso AMLSim.

### El caso completo

Retomamos la factura del inicio y seguimos el razonamiento del agente paso a paso.

```
Factura folio a3f2-...
Emisor:    CONSULTORES DEL NORTE SA
           RFC: CDN190312AB1
Concepto:  "Servicios de consultoria administrativa"
Monto:     $2,400,000.00
Fecha:     2024-03-15
```

**Paso 1 — ¿El proveedor está señalado?**

Sí. Estatus definitivo, publicado en el Diario Oficial el 20 de agosto de 2025.

La factura es de marzo de 2024; el estatus definitivo es de agosto de 2025. Por el efecto retroactivo, la deducción queda invalidada. Pero no hay indicio de intención: la contrató antes de que fuera pública la señalización.

*Resultado: sospecha, no prueba. El agente sigue investigando.*

**Paso 2 — ¿Hay soporte documental?**

No existe contrato ni orden de compra en el expediente. No hay evidencia de entrega del servicio.

*Resultado: falta materialidad. Sube el peso, pero todavía no basta.*

**Paso 3 — ¿A dónde fue el dinero?**

Se pagó por transferencia el 28 de marzo de 2024. El agente recorre el grafo de transferencias:

```
EMPRESA -> CDN          $2,400,000   28-mar
CDN -> SERVICIOS ABC    $  800,000   02-abr
CDN -> LOGISTICA XYZ    $  760,000   02-abr
CDN -> PROMO DEL SUR    $  700,000   03-abr
ABC -> cuenta 4471      $  790,000   09-abr
XYZ -> cuenta 4471      $  750,000   09-abr
SUR -> cuenta 4471      $  690,000   10-abr
                        ----------
cuenta 4471 = titular: socio mayoritario de EMPRESA
recuperado: $2,230,000 (92.9% del monto facturado)
```

Ahí está la prueba. El dinero salió, dio tres saltos y regresó al 93% en menos de dos semanas. Eso no es coincidencia estadística: es un ciclo.

**Paso 4 — ¿Hubo daño?**

Sí. La factura se usó en la declaración de marzo de 2024. El daño está cuantificado.

### El expediente que genera

```
ACUSACION

Proveedor: CONSULTORES DEL NORTE SA (CDN190312AB1)
Esquema:   Simulacion de operaciones con retorno
           de fondos
Monto:     $2,400,000.00 deducidos
           $2,230,000.00 retornados

EVIDENCIA
1. RFC en listado definitivo, oficio 500-05-2025-XXXXX,
   DOF 2025-08-20. El efecto retroactivo alcanza
   esta operacion.
2. Sin contrato ni orden de compra en el expediente.
3. Sin evidencia de entrega del servicio facturado.
4. Ruta de retorno de fondos en 3 saltos, 12 dias,
   a cuenta 4471 (socio mayoritario).
   Recuperacion 92.9%.
5. Deduccion aplicada en declaracion de marzo 2024.
```

Cada punto es verificable por un auditor real. Eso es lo que pide el criterio de viabilidad del reto.

### El otro lado: cuándo NO acusar

Igual de importante, porque es el criterio de juicio del reto.

```
PROVEEDOR: MATERIALES DEL GOLFO
    -> Estatus DESVIRTUADO desde 2024-11-03
    -> El SAT ya acepto su materialidad
    -> NO SE ACUSA

PROVEEDOR: TRANSPORTES REGIOMONTANOS
    -> Estatus definitivo desde 2025-01-15
    -> Sin contrato en el expediente
    -> PERO: pago unico, sin retorno detectado
    -> Hay evidencia de entrega (cartas porte)
    -> LEAD NO PERSEGUIDO: contingencia fiscal real,
       pero no hay elementos para sostener simulacion.
       Recomendacion: solicitar expediente de
       materialidad.
```

El segundo caso es nuestro mejor momento en el demo. El proveedor está en estatus definitivo —la señal más fuerte que existe— y aun así el agente no lo acusa, porque falta el resto de la cadena. Los otros equipos lo van a acusar.

> **IMPLICACIÓN DE DISEÑO — la regla que cierra todo**
>
> **Estar en la lista es sospecha. El retorno del dinero es prueba.**
>
> Por eso el reto dice que lo que separa a un auditor real de un adivinador es probar antes de acusar. Y por eso necesitamos las dos fuentes.

---

## Parte 5 — Lo que ningún recurso nos da

Esto es lo que tenemos que construir nosotros, y es donde se va la mayor parte del tiempo. Conviene tenerlo claro antes de planear.

| Pieza | Por qué no existe | Criticidad |
|---|---|---|
| El libro mayor (contabilidad de la empresa) | No hay uno público | Alta |
| El soporte documental: contratos, órdenes de compra, evidencias de entrega | Ninguna fuente lo tiene. Sin esto, dos de las tres preguntas de materialidad quedan siempre vacías y el agente nunca puede acusar. | **Crítica** |
| El puente factura ↔ pago bancario | Es la unión entre el mundo de las facturas y el de los movimientos. El complemento de Pagos nos da la forma, pero la liga la construimos nosotros. | **Crítica** |
| El catálogo de proveedores de la empresa ficticia | No hay uno público | Alta |
| El inyector de esquemas: la función que mete un fraude nuevo en datos limpios | Sin esto no hay demo. El jurado va a esconder un esquema fresco y el agente tiene que encontrarlo. | **Crítica** |

> **IMPLICACIÓN DE DISEÑO — la pieza que más fácil se nos olvida**
>
> El soporte documental. Es tentador pensar que la materialidad se resuelve cruzando facturas con transferencias, pero eso solo responde una de las tres preguntas: la del pago.
>
> Contrato y evidencia de entrega no existen en ninguna fuente. Si no los generamos, el agente se queda acusando solo por el retorno del dinero, que es lo mismo que va a hacer todo el mundo.
>
> Hay que generarlos con huecos sembrados a propósito: proveedores con contrato completo, proveedores sin nada, y casos intermedios.

> **IMPLICACIÓN DE DISEÑO — congelar el contrato de datos a las 4 horas**
>
> Las cinco tablas, sus llaves y la firma del inyector de esquemas se acuerdan en las primeras horas y no se tocan después. Cualquier cambio posterior cuesta más de lo que aporta, porque obliga a regenerar todo.
>
> Todos los demás módulos se construyen contra ese contrato.

> **IMPLICACIÓN DE DISEÑO — el modelo de lenguaje: local y con caché**
>
> El reto lo advierte explícitamente: este track hace muchas llamadas por investigación, y el nivel gratuito de las APIs comerciales tiene límite diario.
>
> Levantamos un modelo local con caché por contenido de la consulta desde el primer momento. Si el límite nos corta a las tres de la mañana del sábado, no hay demo.

---

## Glosario

Dividido en tres secciones, porque son tres idiomas distintos. Consulta la que necesites.

### Términos fiscales

**SAT** — Servicio de Administración Tributaria. La autoridad fiscal de México, equivalente al IRS.

**RFC** — Registro Federal de Contribuyentes. El identificador fiscal único de toda persona o empresa en México. Doce caracteres para empresas, trece para personas físicas.

**CFDI** — Comprobante Fiscal Digital por Internet. La factura electrónica mexicana. Es un archivo XML, no un PDF.

**UUID o folio fiscal** — El identificador único de cada factura timbrada. Nuestra ancla de trazabilidad.

**Timbrado** — El proceso por el que un tercero autorizado sella la factura y le asigna el folio. Sin timbre, la factura no existe fiscalmente.

**EFOS** — Empresa que Factura Operaciones Simuladas. Quien emite las facturas falsas.

**EDOS** — Empresa que Deduce Operaciones Simuladas. Quien las recibe y las usa para pagar menos impuestos.

**Deducir** — Restar un gasto de tus ingresos para pagar menos impuesto sobre la renta.

**Acreditar** — Restar el IVA que pagaste del IVA que debes. Junto con la deducción, es el beneficio que busca quien compra facturas falsas.

**Materialidad** — Que la operación realmente ocurrió. Se prueba con contrato, evidencia de entrega y pago bancario rastreable. Es el concepto central del proyecto.

**DOF** — Diario Oficial de la Federación. Donde se publican oficialmente las resoluciones. Es la fecha que cuenta para efectos legales.

**Oficio** — El documento numerado con el que el SAT notifica una resolución. Formato `500-05-AAAA-NNNNN`. Sirve como cita verificable.

**Anexo 20** — La guía técnica del SAT que define la estructura del CFDI.

**Definitivo** — El estatus que confirma que una empresa emitió facturas por operaciones inexistentes.

**Desvirtuado** — El estatus de quien logró probar que sus operaciones sí existieron. Está limpio.

**PUE y PPD** — Métodos de pago. PUE es pago en una sola exhibición; PPD es pago en parcialidades o diferido. Las facturas PPD obligan a emitir un comprobante por cada pago.

**REP** — Recepción de Pagos. El comprobante que liga cada pago con el folio de la factura original. Es nuestro puente hacia los movimientos bancarios.

### Términos de fraude

**Factura falsa** — Un comprobante emitido por una operación que nunca ocurrió. Es fiscalmente válido; lo que no existe es la operación.

**Empresa fantasma o factorera** — Una empresa que existe en papel pero no opera. Su único negocio es vender facturas.

**Round-tripping** — «Viaje redondo». El dinero sale de la empresa y regresa a ella o a sus dueños, dando vueltas por terceros para disimular. En un grafo se ve como un ciclo.

**Kickback** — Soborno o comisión oculta. En español coloquial, «moche». El proveedor factura de más y devuelve la diferencia por debajo de la mesa.

**Dispersión (fan-out)** — Repartir dinero de una cuenta a muchas, para que ningún movimiento se vea grande.

**Recolección (fan-in)** — Muchas cuentas pagando a una. Si un proveedor recibe de ocho empresas sin relación entre sí, huele a mercado de facturas.

**Capas (layering)** — Meter intermediarios entre el origen y el destino del dinero para romper el rastro.

**Dolo** — Intención de cometer el fraude, en contraste con buena fe.

### Términos técnicos

**Agente** — Un modelo de lenguaje que además de responder actúa: consulta datos, decide el siguiente paso, itera. La diferencia con un chatbot es que tiene herramientas y un ciclo.

**LLM** — Large Language Model. El modelo de lenguaje que razona en texto.

**Herramienta (tool)** — Una función que el agente puede invocar: «consulta el estatus de este RFC», «trae las facturas de este proveedor».

**Alucinación** — Cuando el modelo inventa datos con seguridad. Por eso los montos en pesos salen de consultas, nunca del modelo.

**Ground truth** — La respuesta correcta conocida de antemano, contra la cual mides tu sistema. Sin ella no puedes saber si tu agente funciona: solo puedes opinar.

**Precisión** — De todo lo que acusaste, cuánto era realmente fraude. Mide falsos positivos, es decir acusar inocentes.

**Recall** — De todo el fraude que había, cuánto encontraste. Mide lo que se te escapó.

**Falso positivo** — Acusar a alguien limpio. Es el error que el reto castiga más explícitamente.

**Sobreajuste** — Cuando el sistema aprende las particularidades de tus datos de prueba en vez del patrón general.

**Baseline** — Una solución simple contra la que comparas. Si el agente no le gana a tres reglas fijas, el modelo no está aportando.

**Datos sintéticos** — Datos generados artificialmente que imitan datos reales. Todo nuestro conjunto lo es.

**Grafo** — Nodos conectados por aristas. Aquí: cuentas conectadas por transferencias. Seguir el dinero es recorrer el grafo.

**Ledger** — Libro mayor. El registro contable de todas las operaciones de la empresa.

**Data estate** — El conjunto completo de datos de la empresa investigada: contabilidad, facturas, movimientos bancarios y proveedores.

**Esquema (schema)** — La estructura de las tablas: qué columnas, de qué tipo. «Congelar el esquema» es acordarlo y no cambiarlo.

**ETL** — Extract, Transform, Load. El proceso de tomar datos crudos, limpiarlos y cargarlos.

**Trazabilidad** — Que cada afirmación se pueda rastrear hasta su origen. Un expediente trazable dice «folio tal», no «una factura».

**Ollama** — Software para correr modelos de lenguaje localmente, sin API ni límites de uso.

**Caché** — Guardar la respuesta de una llamada para no repetirla. Crítico cuando se hacen cientos de llamadas.

**Case file (expediente)** — Lo que entrega el agente: el esquema detectado, los proveedores, la cadena de evidencia, el monto y los leads que decidió no perseguir.

**Cadena de evidencia** — La secuencia de hechos que sostiene una acusación. No «este proveedor es sospechoso», sino la lista verificable de hechos.

**Lead** — Una pista. El reto pide que el agente liste las que no persiguió y por qué: eso demuestra criterio, no pereza.

**Detector determinista** — Una regla fija, sin modelo: «si el RFC está en definitivo, marca». Sirve para que el agente sepa dónde mirar antes de gastar llamadas.

---

## Tarjeta de referencia rápida

Los diez términos que vas a usar todo el tiempo. Ten esta página abierta mientras programas.

| Término | En una línea |
|---|---|
| RFC | El identificador fiscal de una empresa. Nuestra llave primaria. |
| CFDI | La factura electrónica mexicana. Un XML. |
| UUID / folio | El identificador único de una factura. Nuestra ancla de citas. |
| EFOS | Quien emite facturas falsas (el proveedor fantasma). |
| EDOS | Quien las usa para pagar menos impuestos (el cliente). |
| Materialidad | Que la operación sí ocurrió. Contrato + entrega + pago rastreable. |
| Definitivo | El estatus que confirma que una empresa emitió facturas falsas. |
| Round-tripping | El dinero sale y regresa dando vueltas. Nuestra prueba principal. |
| Ground truth | La respuesta correcta que conocemos porque nosotros sembramos el fraude. |
| Case file | El expediente final: esquema, evidencia, monto y leads descartados. |

### Las tres reglas que no se negocian

1. Estar en la lista es sospecha; el retorno del dinero es prueba. No acusamos con nivel 1.
2. Los montos en pesos salen de consultas a los datos, nunca del modelo de lenguaje.
3. La respuesta correcta se usa para medir, nunca queda al alcance del agente.

---

## Siguiente fase

Con esta investigación cerrada, el siguiente paso es la planeación: decidir cuál es nuestra apuesta diferenciadora y derivar todo lo demás de ahí.

Las implicaciones de diseño de este documento son el insumo. No son el plan.
