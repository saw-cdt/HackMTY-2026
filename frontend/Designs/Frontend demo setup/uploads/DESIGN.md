# DESIGN.md — The Forensic Auditor (Infosys · HackMTY 2026)

Sistema de diseño del frontend. Es la fuente de verdad para color, tipografía,
espaciado y componentes. Si un componente no se puede describir con los tokens de
aquí, el token falta — se agrega aquí primero y luego se usa.

---

## 1. De dónde sale la estética

| Referencia | Qué se toma | Qué se descarta |
|---|---|---|
| `diseño1.jpg` (dashboard fitness) | La **estructura y el sentimiento**: shell flotante con esquinas muy redondeadas, rail de iconos a la izquierda, card héroe con gradiente y gráfica, trío de cards blancas con barra de progreso, rail derecho con lista + mapa, sombras difusas, glassmorphism | **Todo el rosa/magenta** (`#F08BA8`, las píldoras rosas, el trazo rosa de la gráfica) |
| `infosys.com/mx` | La **paleta**: azul marino profundo → teal, el badge morado→azul, el peso tipográfico de los titulares | El layout de marketing (no aplica a un dashboard) |

**Resultado:** la misma estética de `diseño1.jpg`, con su violeta como color primario
y con el rol del rosa reasignado a **teal/azul Infosys**.

### Regla dura de color

> **Prohibido cualquier matiz rosa o magenta (hue 300°–350°) en toda la interfaz.**
> Incluye tintes: un rojo aclarado con blanco puro se vuelve rosado — los tintes se
> mezclan siempre contra `--slate-50`, nunca contra `#FFFFFF`.

Esta regla es verificable: cualquier color nuevo se convierte a HSL y si `h` cae
entre 300 y 350, se rechaza.

---

## 2. Principios

1. **El dinero manda.** Es una app forense: los montos son el dato más importante de
   la pantalla. Cifras con `tabular-nums`, alineadas a la derecha, nunca truncadas.
2. **Un hallazgo siempre muestra su estado.** Confirmado / retado / descartado nunca
   se distinguen solo por color — llevan icono + etiqueta.
3. **Profundidad por sombra y blur, no por bordes.** Los bordes son hairlines de
   apoyo; la jerarquía la da la elevación.
4. **Curvas generosas.** Nada por debajo de 12px de radio salvo chips y hairlines.
5. **El gradiente es un acento, no un fondo.** Máximo dos superficies con gradiente
   por pantalla.

---

## 3. Tokens de color

### 3.1 Neutros (tema claro)

| Token | Hex | Uso |
|---|---|---|
| `--page` | `#E2E6F5` | Fondo de la página (lavanda frío, como la referencia) |
| `--page-2` | `#D5DAEE` | Degradado sutil del fondo hacia abajo |
| `--surface` | `#FFFFFF` | Cards |
| `--surface-2` | `#F5F7FD` | Card anidada, filas alternas, input en reposo |
| `--surface-3` | `#EDF0FA` | Hover de fila, skeleton |
| `--slate-50` | `#F2F4FB` | Base de mezcla para todos los tintes |
| `--border` | `#E3E8F5` | Hairline 1px |
| `--border-strong` | `#CBD3E8` | Separador de sección, borde de input enfocado |
| `--text-strong` | `#111A3D` | Titulares, cifras (16.1:1 sobre blanco) |
| `--text` | `#2A3566` | Cuerpo (11.4:1) |
| `--text-muted` | `#6B75A0` | Labels secundarios, ejes (4.9:1 — mínimo legal) |
| `--text-on-fill` | `#FFFFFF` | Texto sobre relleno saturado |

`--text-muted` es el gris más claro permitido para texto. Para texto decorativo aún
más tenue, no se aclara el color: se baja el tamaño o se usa `--border-strong`.

### 3.2 Violeta — primario (el color del rail y de la card héroe)

| Paso | Hex | Notas |
|---|---|---|
| 50 | `#F0EEFE` | Tinte de fondo, chips |
| 100 | `#DCD7FC` | |
| 200 | `#BDB4F8` | Borde de chip |
| 300 | `#9A8CF2` | Paso más claro permitido en rampas ordinales (2.83:1) |
| 400 | `#7A66EA` | Hover de gradiente |
| **500** | **`#5B4BE1`** | **Primario.** Blanco encima = 5.9:1 ✔ |
| 600 | `#4A38C9` | Botón hover / fin del gradiente |
| 700 | `#3B2BA3` | Pressed |
| 800 | `#2C2079` | |
| 900 | `#1D1550` | Texto violeta sobre tinte |

### 3.3 Azul Infosys — secundario

| Paso | Hex | Notas |
|---|---|---|
| 50 | `#E6F3FB` | |
| 100 | `#C2E1F5` | |
| 200 | `#8CC8EC` | |
| 300 | `#4FAADF` | |
| 400 | `#1E8FD0` | |
| **500** | **`#007CC3`** | **Azul de marca Infosys.** Blanco encima = 4.49:1 → solo texto ≥18px o iconos |
| **600** | **`#0066A4`** | Usar este cuando lleve texto blanco normal (6.1:1 ✔) |
| 700 | `#0A4F80` | |
| 800 | `#0E3A5E` | |
| 900 | `#0B2545` | Navy de fondo oscuro / inicio del gradiente Infosys |

### 3.4 Teal — acento (ocupa el lugar del rosa)

| Paso | Hex | Notas |
|---|---|---|
| 50 | `#E4FAF6` | |
| 100 | `#BCF2E9` | |
| 200 | `#85E5D6` | |
| 300 | `#46D3BF` | |
| 400 | `#1CBCA8` | |
| 500 | `#10A895` | **Texto encima debe ser `--text-strong`, no blanco** (blanco = 2.98:1 ✘) |
| 600 | `#0B8878` | Blanco = 4.32:1 → solo texto grande |
| 700 | `#0A6B60` | Blanco = 6.4:1 ✔ — este es el que lleva texto blanco |

> El teal saturado es hermoso como relleno pero **traicionero con texto blanco**.
> Regla: relleno teal 300–500 → texto navy. Texto blanco → teal 700+.

### 3.5 Semánticos (mapeados al dominio forense)

| Rol | Token | Hex | Icono obligatorio | Significado en la app |
|---|---|---|---|---|
| Confirmado | `--ok` | `#0E8A5F` | `check-circle` | Hallazgo que sobrevivió al retador y al validador |
| Retado | `--warn` | `#B57209` | `shield-alert` | El retador presentó explicación inocente; en revisión |
| Crítico | `--danger` | `#C4423B` | `alert-octagon` | Falsa acusación / validador rechazó |
| Descartado | `--neutral` | `#6B75A0` | `archive` | `lead_not_pursued` |
| Informativo | `--info` | `#0066A4` | `info` | Metadata de la corrida |

Los tintes de fondo correspondientes se calculan como
`color-mix(in oklab, var(--ok) 12%, var(--slate-50))` — **nunca** mezclando con
blanco puro (ver regla dura del §1).

### 3.6 Gradientes

```css
/* Card héroe — el equivalente del "Overview" violeta de la referencia */
--grad-primary: linear-gradient(135deg, #6246EA 0%, #4A38C9 55%, #3B2BA3 100%);

/* Banda Infosys — navy → teal, igual que el hero de infosys.com */
--grad-infosys: linear-gradient(115deg, #0B2545 0%, #10307A 38%, #0E6E9C 72%, #10A895 100%);

/* Card de acento — REEMPLAZA la card rosa "My Jogging" */
--grad-accent:  linear-gradient(140deg, #1E3A8F 0%, #0E7C8C 100%);

/* Badge morado→azul (el recuadro "Top 100" de infosys.com) */
--grad-badge:   linear-gradient(135deg, #7A3FE4 0%, #3B5BDB 100%);

/* Fondo de página */
--grad-page:    linear-gradient(180deg, #E6EAF7 0%, #D5DAEE 100%);
```

`--grad-accent` y `--grad-infosys` están construidos para que el **extremo oscuro
quede donde va el texto**. Si volteás la dirección del gradiente, el texto blanco
pierde contraste — revalidá antes.

### 3.7 Tema oscuro

Pasos elegidos para la superficie oscura, no un `invert()` automático.

```css
--page:          #080D1F;
--surface:       #0F1733;
--surface-2:     #16204292;   /* sobre --surface */
--surface-3:     #1C2750;
--border:        #253061;
--border-strong: #32407A;
--text-strong:   #FFFFFF;
--text:          #D3DAF2;
--text-muted:    #94A0C8;

--primary:       #8B7CF8;   /* violeta 500 sube a 400-ish en oscuro */
--secondary:     #3A8ED2;
--accent:        #12A08B;
--ok:            #18A96F;
--warn:          #C08420;
--danger:        #DC4F4F;

--grad-primary:  linear-gradient(135deg, #3B2BA3 0%, #2C2079 60%, #1D1550 100%);
--grad-accent:   linear-gradient(140deg, #132A63 0%, #0A5566 100%);
```

En oscuro el glassmorphism cambia de `rgba(255,255,255,.55)` a
`rgba(255,255,255,.06)` con borde `rgba(255,255,255,.12)`.

---

## 4. Tipografía

```css
--font-display: "Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif;
--font-ui:      "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
--font-mono:    "JetBrains Mono", ui-monospace, "Cascadia Code", monospace;
```

- **Display** — titulares de card, cifras héroe. Geométrica y redondeada como la
  referencia.
- **UI** — todo lo demás.
- **Mono** — `invoice_id`, `vendor_id`, hashes de seed, rutas de tabla. Cualquier
  identificador que el jurado vaya a comparar carácter por carácter va en mono.

### Escala

| Token | px / line-height | Peso | Uso |
|---|---|---|---|
| `--t-display` | 44 / 1.05 | 800 | Cifra héroe (`$1,284,900`) |
| `--t-h1` | 32 / 1.15 | 700 | Título de pantalla |
| `--t-h2` | 24 / 1.2 | 700 | Título de card grande |
| `--t-h3` | 20 / 1.3 | 600 | Título de card |
| `--t-lg` | 16 / 1.5 | 500 | Cuerpo destacado |
| `--t-base` | 14 / 1.55 | 400 | Cuerpo, celdas de tabla |
| `--t-sm` | 13 / 1.45 | 500 | Labels, ejes |
| `--t-xs` | 11 / 1.35 | 600 | Overline, píldoras. `letter-spacing: .06em`, mayúsculas |

### Cifras

```css
.num { font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1; }
```

Obligatorio en: columnas de tabla, ticks de eje, cualquier lista vertical de montos.
Las cifras héroe sueltas usan figuras proporcionales (se ven mejor y no se alinean
con nada).

Formato de moneda MXN: `Intl.NumberFormat('es-MX', { style:'currency', currency:'MXN' })`.
**Nunca redondear un monto en la UI** — los montos salen de SQL y el validador
reconcilia al 2%; un redondeo visual hace que el jurado vea un número distinto al
del `submission.json`.

---

## 5. Espaciado, radio, elevación

```css
/* Espaciado — escala de 4 */
--s-1: 4px;  --s-2: 8px;   --s-3: 12px;  --s-4: 16px;
--s-5: 20px; --s-6: 24px;  --s-8: 32px;  --s-10: 40px; --s-12: 48px;

/* Radio — la referencia es MUY redondeada */
--r-xs: 8px;    /* chips, checkbox */
--r-sm: 12px;   /* input, botón pequeño */
--r-md: 16px;   /* botón, celda de icono */
--r-lg: 20px;   /* card anidada */
--r-xl: 28px;   /* card */
--r-2xl: 36px;  /* card héroe */
--r-shell: 40px;/* contenedor principal */
--r-pill: 999px;

/* Sombra — teñida de navy, nunca negro puro */
--sh-sm:   0 1px 2px rgba(16,26,64,.06);
--sh-md:   0 6px 16px -4px rgba(16,26,64,.10);
--sh-lg:   0 18px 40px -12px rgba(16,26,64,.16);
--sh-xl:   0 32px 64px -20px rgba(16,26,64,.22);
--sh-glow: 0 12px 32px -8px rgba(91,75,225,.45);  /* bajo la card violeta */
--sh-inset-top: inset 0 1px 0 rgba(255,255,255,.45);
```

### Glassmorphism

```css
.glass {
  background: rgba(255, 255, 255, .55);
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
  border: 1px solid rgba(255, 255, 255, .38);
  box-shadow: var(--sh-lg), var(--sh-inset-top);
}
/* Sobre superficie oscura (paneles dentro de la card héroe) */
.glass-on-dark {
  background: rgba(255, 255, 255, .12);
  border: 1px solid rgba(255, 255, 255, .18);
}
```

**Límite de rendimiento: máximo 4 capas con `backdrop-filter` por pantalla.** Más que
eso tira los FPS en el scroll. Si necesitás más superficies translúcidas, usá un
`background` sólido con la opacidad ya calculada.

---

## 6. Layout

```
┌─ page (--grad-page, padding 28px) ─────────────────────────────┐
│ ┌─ shell (.glass, --r-shell, --sh-xl) ───────────────────────┐ │
│ │ ┌──────┐ ┌──────────────────────────────┐ ┌──────────────┐ │ │
│ │ │ rail │ │  main                        │ │  aside       │ │ │
│ │ │ 76px │ │  1fr                         │ │  312px       │ │ │
│ │ └──────┘ └──────────────────────────────┘ └──────────────┘ │ │
│ └────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

```css
.shell { display: grid; grid-template-columns: 76px 1fr 312px; gap: var(--s-5); padding: var(--s-5); }
```

El `aside` tiene fondo `--surface` sólido (blanco) y esquina redondeada solo del
lado interior — igual que el panel de "Friends" de la referencia.

**Grid del `main`:** 12 columnas, `gap: 20px`.
La fila superior de la referencia es `7fr 5fr` (card héroe + dos cards apiladas).
La fila inferior es `repeat(3, 1fr)`.

### Breakpoints

| Nombre | Ancho | Comportamiento |
|---|---|---|
| `xl` | ≥1440 | Layout completo de 3 columnas |
| `lg` | 1100–1439 | `aside` baja a 280px, trío de cards sigue en 3 |
| `md` | 760–1099 | `aside` se colapsa a drawer; trío pasa a 2 columnas |
| `sm` | <760 | Rail pasa a barra inferior fija; una sola columna; el shell pierde el margen exterior y los radios bajan a `--r-xl` |

---

## 7. Componentes

### 7.1 Rail de navegación

76px de ancho, fondo `--grad-primary`, `--r-2xl`, altura completa.
Iconos de 22px en `rgba(255,255,255,.62)`. El activo lleva una pastilla
`rgba(255,255,255,.18)` de 44×44 con `--r-md` y el icono en blanco puro.
Logo de Infosys arriba, botón de salir abajo separado con `margin-top:auto`.

### 7.2 Card héroe — "Overview del estate"

Es la card violeta grande de la referencia. Contiene:
- Overline + título (`--t-h3`, blanco).
- Selector de rango a la derecha en `.glass-on-dark`, `--r-pill`.
- Gráfica de línea única con el punto activo resaltado (§8).
- Tres sub-stats al pie dentro de un panel `.glass-on-dark` con `--r-lg`; el del
  centro va elevado con `rgba(255,255,255,.18)` para marcar el valor principal.

En la app: total facturado analizado · número de facturas · monto en disputa.

### 7.3 Card de acción — "Cargar estate"

Ocupa el lugar de "Daily Jogging". Fondo `--violet-100`, texto `--violet-900`,
icono en cuadro blanco de 56px con `--r-lg`. Es un dropzone: en `dragover` el borde
pasa a `2px dashed var(--violet-500)` y el fondo a `--violet-50`.

### 7.4 Card de acento — "Corrida del agente"

**Es la card que era rosa.** Ahora `--grad-accent` (navy → teal), texto blanco,
flecha circular blanca al pie derecho. Muestra `wall_clock_seconds` y `llm_calls` de
`run_metadata`. La marca de agua es un `<svg>` de área en `rgba(255,255,255,.16)`.

### 7.5 Trío de cards de progreso — "Cobertura por esquema"

Reemplaza "Bicycle Drill / Jogging Hero / Healthy Busy". Una card por tipo de
esquema; con cinco tipos, se muestran tres y el resto va en un carrusel horizontal.

```
┌─────────────────────────────┐
│  [icono]              [⋮]   │  chip 44px, --violet-500 sobre --violet-50
│  Phantom vendor             │  --t-h3
│  12 facturas / 3 vendors    │  --t-sm, --text-muted
│                             │
│  Progreso            45%    │  --t-sm
│  ▓▓▓▓▓▓░░░░░░░░░░░░░        │  barra 6px, --r-pill
│  4 / 9 confirmados  [pill]  │  --t-xs
└─────────────────────────────┘
```

- Barra: track `--surface-3`, relleno `--ok`. Si el esquema tiene un hallazgo
  rechazado, el relleno es `--warn` y aparece el icono correspondiente.
- La píldora de la derecha (era rosa) ahora usa el tinte semántico del estado:
  `color-mix(in oklab, var(--warn) 14%, var(--slate-50))` con texto `--warn`
  oscurecido, más su icono.

### 7.6 Rail derecho — "Actividad del agente"

Lista de filas de 56px. Cada fila:
avatar 36px `--r-pill` con anillo de 2px del color del rol · nombre en `--t-base`
600 · acción en `--t-sm` `--text-muted` · timestamp relativo · chevron.

Colores de rol (fijos, no son series de datos):
Investigador `--violet-500` · Retador `--warn` · Validador `--secondary`.

Tabs "Actividad / Hallazgos" arriba: contenedor `--surface-2` con `--r-pill` y el
tab activo en blanco con `--sh-sm`.

### 7.7 Panel de grafo — "Vendor ↔ Invoice ↔ Bank"

Ocupa el lugar del "Live map". Alto 180px en el rail, expandible a pantalla completa.
- Fondo `--surface-2` con una malla de puntos de 1px en `--border` cada 16px.
- Nodos: vendor = círculo 14px, invoice = cuadro redondeado 12px, cuenta bancaria =
  rombo 12px. **La forma carga el tipo, el color carga el estado** (§3.5).
- Aristas: 1.5px `--border-strong`; la arista sospechosa 2px `--danger` con
  `stroke-dasharray` animado (desactivable).
- Nodo seleccionado: anillo de 2px del color de superficie + halo `--sh-glow`.

### 7.8 Contraste hallazgo vs. decoy

Card partida en dos, separada por un hairline vertical `--border`.
Izquierda `--ok` tinte, derecha `--neutral` tinte. Encabezado de cada mitad con
icono + etiqueta. Debajo, la misma estructura de exhibits en ambos lados para que la
comparación sea línea por línea. Nunca se usa solo el color de fondo para decir cuál
sobrevivió — el encabezado lo dice con palabras.

### 7.9 Tabla de exhibits

- Sin zebra. Separador hairline `--border` entre filas.
- Header `--t-xs` mayúsculas `--text-muted`, fondo `--surface-2`, sticky.
- Fila 48px; hover `--surface-3`.
- Montos alineados a la derecha con `.num`. IDs en `--font-mono` `--t-sm`.
- La columna `source_table` siempre visible — es lo que el jurado verifica.
- Fila expandible: chevron a la izquierda, detalle con fondo `--surface-2` y
  `--r-lg` con `margin: 0 var(--s-4) var(--s-3)`.

### 7.10 Botones

| Variante | Fondo | Texto | Hover |
|---|---|---|---|
| Primario | `--violet-500` | blanco | `--violet-600` + `--sh-glow` |
| Secundario | `--surface` + borde `--border-strong` | `--text` | `--surface-2` |
| Fantasma | transparente | `--text-muted` | `--surface-2` |
| Infosys | `--blue-600` | blanco | `--blue-700` |
| Destructivo | tinte `--danger` | `--danger` | relleno `--danger` / blanco |

Alto 40px (`sm` 32, `lg` 48), `--r-md`, padding `0 var(--s-5)`, peso 600.
Foco: `outline: 2px solid var(--violet-500); outline-offset: 2px` — **nunca**
`outline: none` sin reemplazo.

### 7.11 Píldoras de estado

`--r-pill`, `--t-xs`, padding `4px 10px`, fondo tinte semántico, texto del color
semántico al paso 700+, icono de 12px a la izquierda. Sin excepción: **icono + texto**.

### 7.12 Input / búsqueda

Alto 44px, `--r-pill`, fondo `--surface-2`, sin borde en reposo. Enfocado: fondo
`--surface`, borde `--border-strong`, y el anillo de foco. Icono de lupa 18px en
`--text-muted` a 16px del borde izquierdo.

---

## 8. Gráficas

La paleta de series está **validada**, no elegida a ojo. Se corrió el validador de
CVD y contraste sobre las superficies reales de esta app.

### 8.1 Paleta categórica — los 5 tipos de esquema

Orden fijo. **Nunca se cicla ni se reordena**: el color sigue a la entidad, no a su
posición en un ranking. Si un filtro cambia cuántas series hay, las que sobreviven
conservan su color.

| Slot | Esquema | Claro (sobre `#FFFFFF`) | Oscuro (sobre `#0F1733`) |
|---|---|---|---|
| 1 | `phantom_vendor` | `#5B4BE1` | `#8B7CF8` |
| 2 | `kickback` | `#0E9F8B` | `#12A08B` |
| 3 | `round_tripping` | `#B57209` | `#C08420` |
| 4 | `threshold_splitting` | `#2E90D9` | `#3A8ED2` |
| 5 | `revenue_inflation` | `#C4423B` | `#DC4F4F` |

**Resultado del validador:**

- Lista de pares **adyacentes** (barras, líneas, apiladas): los 5 slots **PASAN**
  todas las comprobaciones en ambos modos. Peor par adyacente: ΔE CVD 13.3 claro /
  12.1 oscuro (meta ≥8); visión normal 20.2 / 19.4 (piso ≥15); todos ≥3:1 contra la
  superficie.
- Lista de **todos los pares** (dispersión, nodos del grafo, small multiples): los 5
  **FALLAN** — `revenue_inflation` ↔ `round_tripping` cae a ΔE 5.8 CVD y 12.1 en
  visión normal. **Tope de 3 series** en esas formas (slots 1–3 pasan todos los
  pares en ambos modos: ΔE CVD 13.3 / 12.1). Más de 3 → agrupar en "Otros" o usar
  small multiples.
- En el grafo, la separación la carga **la forma del nodo**, no el matiz.

### 8.2 Rampa secuencial

Magnitud continua (heatmap de monto por vendor/mes, intensidad de arista) usa **una
sola rampa de violeta**, clara → oscura: `--violet-100` … `--violet-900`.
Para rampas **ordinales** (etapas discretas ordenadas, como el embudo
Investigador → Retador → Validador) el paso más claro es `--violet-300`
(`#9A8CF2`, 2.83:1) — nada más claro que eso.

### 8.3 Rampa divergente

Solo para desviación con signo (variación vs. contrato, delta contra el PO):
**azul ↔ rojo** con **gris neutro en el punto medio** (`--surface-3` en claro,
`#1C2750` en oscuro). Mismo número de pasos por brazo. Nunca un matiz en el centro,
nunca arcoíris.

### 8.4 Especificación de marcas

- Líneas 2px, sin sombra, esquinas `round`.
- Barras: extremo de dato redondeado 4px, anclado a la línea base (la base queda
  cuadrada).
- **2px de hueco del color de la superficie** entre rellenos: segmentos apilados y
  barras adyacentes por igual.
- Marcadores ≥8px de diámetro; el punto activo lleva un anillo de 2px del color de
  la superficie.
- Rejilla y ejes recesivos: hairline `--border`, ticks en `--text-muted` `--t-sm`.
- **Etiquetas directas selectivas** — nunca un número sobre cada punto. Se etiquetan
  el primero, el último y los extremos.
- **El texto usa tokens de texto, jamás el color de la serie.** El color vive en el
  cuadrito de la leyenda que va al lado.

### 8.5 Interacción

Una gráfica en HTML **es** interactiva. Por defecto:
- Línea/área: crosshair vertical + tooltip que muestra todas las series de ese punto.
- Barra/punto/celda: tooltip por marca al hover.
- Área de impacto más grande que la marca (mínimo 24px).
- Filtros en una sola fila arriba de las gráficas, nunca intercalados.
- Un solo eje. **Nunca dos escalas Y.** Dos medidas de escala distinta = dos
  gráficas, o indexadas a una base común.

### 8.6 Accesibilidad de gráficas

- ≥2 series → leyenda siempre presente; ≤4 series → además etiquetadas directamente.
  Una sola serie no lleva leyenda (el título la nombra).
- Siempre existe una **vista de tabla** del mismo dato (es una app forense: el jurado
  va a querer los números, no la curva).
- Modo oscuro con sus propios pasos, no un `filter: invert()`.
- Relleno de textura (líneas a 45°/135°) disponible para impresión y
  `forced-colors`; nunca activo por defecto.

---

## 9. Movimiento

```css
--ease: cubic-bezier(.32, .72, 0, 1);
--dur-fast: 140ms;   /* hover, foco */
--dur-base: 220ms;   /* entrada de card, tab */
--dur-slow: 380ms;   /* panel, drawer */
```

- Hover de card: `translateY(-2px)` + sombra sube un paso. Nada de `scale` en cards
  (mueve el texto y se ve barato).
- Entrada de lista: fade + `translateY(8px)`, escalonado de 40ms, tope de 8 elementos.
- La gráfica dibuja la línea una sola vez al montar; en actualizaciones interpola los
  valores sin redibujar.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
```

Esto incluye la animación de `stroke-dasharray` de la arista sospechosa del grafo.

---

## 10. Checklist de revisión

Antes de dar una pantalla por terminada:

- [ ] Ningún matiz entre 300° y 350° en toda la pantalla.
- [ ] Ningún tinte mezclado contra `#FFFFFF` puro.
- [ ] Texto blanco sobre teal solo en el paso 700+.
- [ ] Todo estado lleva icono + etiqueta, no solo color.
- [ ] Montos con `tabular-nums`, alineados a la derecha, sin redondear.
- [ ] Máximo 4 capas con `backdrop-filter`.
- [ ] Máximo 2 superficies con gradiente.
- [ ] Foco visible en todo elemento interactivo.
- [ ] Cada gráfica tiene tooltip y una vista de tabla equivalente.
- [ ] Ningún eje Y doble.
- [ ] Se abrió la pantalla y se miró: sin choques de etiquetas, sin desbordes.
- [ ] Revisado a 380px de ancho.

---

## 11. Implementación

### 11.1 `src/styles/tokens.css`

```css
:root {
  color-scheme: light;

  --page: #E2E6F5;  --page-2: #D5DAEE;
  --surface: #FFFFFF;  --surface-2: #F5F7FD;  --surface-3: #EDF0FA;
  --slate-50: #F2F4FB;
  --border: #E3E8F5;  --border-strong: #CBD3E8;
  --text-strong: #111A3D;  --text: #2A3566;  --text-muted: #6B75A0;

  --violet-50:#F0EEFE; --violet-100:#DCD7FC; --violet-200:#BDB4F8;
  --violet-300:#9A8CF2; --violet-400:#7A66EA; --violet-500:#5B4BE1;
  --violet-600:#4A38C9; --violet-700:#3B2BA3; --violet-800:#2C2079; --violet-900:#1D1550;

  --blue-50:#E6F3FB; --blue-100:#C2E1F5; --blue-200:#8CC8EC; --blue-300:#4FAADF;
  --blue-400:#1E8FD0; --blue-500:#007CC3; --blue-600:#0066A4; --blue-700:#0A4F80;
  --blue-800:#0E3A5E; --blue-900:#0B2545;

  --teal-50:#E4FAF6; --teal-100:#BCF2E9; --teal-200:#85E5D6; --teal-300:#46D3BF;
  --teal-400:#1CBCA8; --teal-500:#10A895; --teal-600:#0B8878; --teal-700:#0A6B60;

  --primary: var(--violet-500);
  --secondary: var(--blue-600);
  --accent: var(--teal-500);
  --ok:#0E8A5F; --warn:#B57209; --danger:#C4423B; --neutral:#6B75A0; --info:#0066A4;

  --series-1:#5B4BE1; --series-2:#0E9F8B; --series-3:#B57209;
  --series-4:#2E90D9; --series-5:#C4423B;
}

:root[data-theme="dark"] { /* … pasos del §3.7 … */ }
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) { /* … los mismos pasos … */ }
}
```

Los valores oscuros se declaran en **ambos** ámbitos: el `@media` cubre la preferencia
del sistema y el `data-theme` cubre el toggle, que debe ganar en las dos direcciones.

### 11.2 Tailwind

Si se usa Tailwind, los tokens se exponen en `theme.extend.colors` apuntando a las
variables CSS (`violet: { 500: 'var(--violet-500)' }`), no duplicando los hex. Un solo
lugar donde cambian los colores.

### 11.3 Fuentes

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

Siempre con stack de respaldo real en el `font-family` — si Google Fonts no carga
durante la demo, la pantalla no puede romperse.
