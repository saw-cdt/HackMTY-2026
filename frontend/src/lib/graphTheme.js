// Colores literales (no var()) para todo lo que se dibuja como atributo SVG
// crudo (fill/stroke en <path>/<circle>, no vía la prop style de React).
// Los navegadores resuelven var() de forma inconsistente en atributos de
// presentación SVG; para no arriesgar un grafo invisible en el demo, estos
// valores se escriben una sola vez aquí, tomados directo de DESIGN.md.
//
// Si más adelante se agrega un toggle de tema oscuro, este es el único
// archivo que necesita una segunda tabla de valores.

export const GRAPH_THEME = {
  company: {
    stroke: '#5B4BE1', // --violet-500, primario
    fill: 'rgba(91,75,225,0.08)',
    text: '#5B4BE1',
    text2: '#4A38C9',
  },
  employee: {
    stroke: '#0066A4', // --blue-600 (contraste 6.1:1 con blanco)
    fill: 'rgba(0,102,164,0.08)',
    text: '#0066A4',
    text2: '#6B75A0',
  },
  clabe: {
    // Nodo "de paso" sin identidad propia — discreto a propósito.
    stroke: '#CBD3E8', // --border-strong
    fill: '#F5F7FD', // --surface-2
    text: '#6B75A0', // --text-muted
    text2: '#6B75A0',
  },
  dimmed: {
    stroke: '#CBD3E8',
    fill: '#EDF0FA', // --surface-3
    text: '#6B75A0',
    text2: '#6B75A0',
  },
  fallback: {
    stroke: '#6B75A0', // --neutral
    fill: '#F2F4FB',
    text: '#6B75A0',
    text2: '#6B75A0',
  },
  edgeDefault: '#CBD3E8',
  edgeReturn: '#C4423B', // --danger — el tramo que cierra el ciclo hacia la empresa
}
