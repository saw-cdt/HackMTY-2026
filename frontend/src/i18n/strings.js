// Diccionario de la interfaz fija (labels, botones, encabezados). El texto
// libre que redacta el agente (narrativas, argumentos, razones, señales
// fuera del enum de 5 esquemas) NO se traduce -- siempre queda en español,
// tal cual sale del pipeline.

const STRINGS = {
  es: {
    brandName: 'Forensic Auditor',
    brandSub: 'HackMTY 2026',
    navAudit: 'Auditoría',
    leadsTitle: 'Leads descartados',
    stageRunning: 'Corriendo',
    stageResult: 'Resultado',
    newRun: '↺ Nueva corrida',

    statLlmCalls: 'Llamadas al modelo',
    statCost: 'Costo',
    statTime: 'Tiempo total',
    statOllamaLocal: 'Ollama local',
    statNoExternalApi: 'Modelo local, sin API externa',
    statDeterministic: 'Corrida determinista',
    statNonDeterministic: 'Corrida no determinista',

    contrastTitle: 'El contraste',
    contrastSub: 'La misma pregunta, dos respuestas: por qué a uno se le acusa y al otro se le cerró el caso.',
    colAccused: 'Acusado',
    colDismissed: 'Descartado',
    resultAccusation: 'ACUSACIÓN',
    resultClosedByChallengerFallback: 'Cerrado por challenger',
    resultClosedByPrefix: 'Cerrado por',
    rowSignal: 'Señal que lo marcó',
    rowTools: 'Herramientas consultadas',
    rowWhatShowed: 'Qué mostró',
    rowChallengerArgued: 'Retador argumentó',
    rowResult: 'Resultado',

    leadsSub: 'Todo lo que el agente investigó y decidió no acusar, con la razón exacta. Busca por RFC o nombre.',
    leadsSearchPlaceholder: 'Buscar por RFC, nombre o señal…',
    leadsCountOf: (a, b) => `${a} de ${b}`,
    leadsEmpty: (q) => `No hay leads que coincidan con «${q}».`,
    leadFieldSignal: 'Señal',
    leadFieldReason: 'Razón',
    leadFieldTools: 'Herramientas',

    graphAriaLabel: 'Grafo de la investigación',

    drawerClose: 'Cerrar',
    drawerWhatOrArgued: 'Qué mostró / argumentó el retador',
    drawerNoContext: 'Sin contexto adicional para esta entidad.',

    dropProductTitle: 'The Forensic Auditor',
    dropSubtitle:
      'Suelta el estate de una empresa (.db) y el agente reconstruye, sin ayuda humana, quién se llevó el dinero y por qué el resto no calificó.',
    dropTitle: 'Suelta el archivo .db aquí',
    dropHint: 'o haz clic para elegirlo — funciona sin conexión',
    dropDemoBtn: 'Cargar demo — estate_seed004.db',

    skipAnimation: 'Saltar animación',
    runningBanner: (step, max) => `Reconstruyendo el rastro del dinero — paso ${step} de ${max}`,
    leadsAvailableNote: 'Disponible para la pregunta sorpresa del jurado',

    errNoSubmissionFor: (name) => `No hay submission.json preparado para ${name}.`,
    errDropDbOrJson: 'Suelta un archivo .db o un submission.json.',
    errCouldNotRead: 'No se pudo leer el archivo.',
    errNoDemoFound: 'No se encontró el submission.json de demo.',
    errCouldNotLoadDemo: 'No se pudo cargar la demo.',

    langToggleAriaLabel: 'Cambiar idioma',
    langToggleTitle: 'Cambiar español / inglés',
  },

  en: {
    brandName: 'Forensic Auditor',
    brandSub: 'HackMTY 2026',
    navAudit: 'Audit',
    leadsTitle: 'Dismissed leads',
    stageRunning: 'Running',
    stageResult: 'Result',
    newRun: '↺ New run',

    statLlmCalls: 'Model calls',
    statCost: 'Cost',
    statTime: 'Total time',
    statOllamaLocal: 'Local Ollama',
    statNoExternalApi: 'Local model, no external API',
    statDeterministic: 'Deterministic run',
    statNonDeterministic: 'Non-deterministic run',

    contrastTitle: 'The contrast',
    contrastSub: 'The same question, two answers: why one gets accused and the other gets closed out.',
    colAccused: 'Accused',
    colDismissed: 'Dismissed',
    resultAccusation: 'ACCUSATION',
    resultClosedByChallengerFallback: 'Closed by challenger',
    resultClosedByPrefix: 'Closed by',
    rowSignal: 'Signal that flagged it',
    rowTools: 'Tools consulted',
    rowWhatShowed: 'What it showed',
    rowChallengerArgued: 'Challenger argued',
    rowResult: 'Result',

    leadsSub: 'Everything the agent investigated and decided not to accuse, with the exact reason. Search by RFC or name.',
    leadsSearchPlaceholder: 'Search by RFC, name or signal…',
    leadsCountOf: (a, b) => `${a} of ${b}`,
    leadsEmpty: (q) => `No leads match «${q}».`,
    leadFieldSignal: 'Signal',
    leadFieldReason: 'Reason',
    leadFieldTools: 'Tools',

    graphAriaLabel: 'Investigation graph',

    drawerClose: 'Close',
    drawerWhatOrArgued: 'What it showed / challenger argued',
    drawerNoContext: 'No additional context for this entity.',

    dropProductTitle: 'The Forensic Auditor',
    dropSubtitle:
      "Drop a company's estate (.db) and the agent reconstructs, with no human help, who took the money and why the rest didn't qualify.",
    dropTitle: 'Drop the .db file here',
    dropHint: 'or click to choose it — works offline',
    dropDemoBtn: 'Load demo — estate_seed004.db',

    skipAnimation: 'Skip animation',
    runningBanner: (step, max) => `Reconstructing the money trail — step ${step} of ${max}`,
    leadsAvailableNote: "Available for the jury's surprise question",

    errNoSubmissionFor: (name) => `No submission.json is ready for ${name}.`,
    errDropDbOrJson: 'Drop a .db file or a submission.json.',
    errCouldNotRead: 'Could not read the file.',
    errNoDemoFound: 'Demo submission.json not found.',
    errCouldNotLoadDemo: 'Could not load the demo.',

    langToggleAriaLabel: 'Switch language',
    langToggleTitle: 'Switch Spanish / English',
  },
}

export function t(lang, key, ...args) {
  const dict = STRINGS[lang] || STRINGS.es
  const val = dict[key] ?? STRINGS.es[key]
  return typeof val === 'function' ? val(...args) : val
}

const STATE_LABELS = {
  es: { neutral: 'Sin evaluar', dismissed: 'Descartado', flagged: 'Candidato', accused: 'Hallazgo' },
  en: { neutral: 'Not evaluated', dismissed: 'Dismissed', flagged: 'Candidate', accused: 'Finding' },
}

export function stateLabel(lang, state) {
  return STATE_LABELS[lang]?.[state] || STATE_LABELS.es[state] || state
}

const ROLE_LABELS = {
  es: { investigator: 'Investigador', challenger: 'Retador', validator: 'Validador' },
  en: { investigator: 'Investigator', challenger: 'Challenger', validator: 'Validator' },
}

export function roleLabel(lang, role) {
  return ROLE_LABELS[lang]?.[role] || ROLE_LABELS.es[role] || role
}

const SCHEME_LABELS = {
  es: {
    phantom_vendor: 'Proveedor fantasma',
    kickback: 'Retorno indebido (kickback)',
    round_tripping: 'Triangulación de fondos',
    threshold_splitting: 'Fraccionamiento de montos',
    revenue_inflation: 'Inflación de ingresos',
  },
  en: {
    phantom_vendor: 'Phantom vendor',
    kickback: 'Kickback',
    round_tripping: 'Round-tripping',
    threshold_splitting: 'Threshold splitting',
    revenue_inflation: 'Revenue inflation',
  },
}

export function schemeLabel(lang, scheme) {
  return SCHEME_LABELS[lang]?.[scheme] || null
}

// ctx.result hoy es un string ya armado en español por adaptUi.js
// ('ACUSACIÓN' o 'cerrado por <closed_by>'). En vez de tocar el adaptador,
// se reconoce el patron aqui y se relocaliza -- si no encaja con ninguno
// (ej. un ui.context escrito a mano con su propio texto), se regresa tal
// cual para que el llamador decida si lo manda a traduccion dinamica.
export function localizeResult(lang, resultRaw, kind) {
  if (!resultRaw) {
    return kind === 'accused' ? t(lang, 'resultAccusation') : t(lang, 'resultClosedByChallengerFallback')
  }
  if (resultRaw === 'ACUSACIÓN') return t(lang, 'resultAccusation')
  const m = /^cerrado por (.+)$/i.exec(resultRaw)
  if (m) return `${t(lang, 'resultClosedByPrefix')} ${roleLabel(lang, m[1].trim())}`
  return resultRaw
}
