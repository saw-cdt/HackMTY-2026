"""
Los cinco esquemas de fraude (seccion 3 de arquitectura) + los decoys.

Cada funcion `plant_*` recibe el `ctx` compartido del estate (listas de
tablas mutables, rng semillado, contadores de id) y:
  1. muta ctx.* in-place agregando lo que el esquema necesita (proveedor
     nuevo, facturas, transferencias, asientos...).
  2. devuelve el diccionario de esquema que va a ground_truth["schemes"],
     con el formato de ground_truth_schema.json.

Cada funcion `decoy_*` hace lo mismo pero devuelve una entrada de
ground_truth["decoys"]: una entidad honesta que dispara la misma señal
que un esquema real, con la razon documental que la limpia.

plant_all(ctx) decide, a partir de ctx.rng (semillado con el seed), CUANTOS
esquemas y decoys sembrar y de que tipo -- nunca un numero fijo.

Este modulo vive en src/generate/, junto con estate.py: es uno de los dos
unicos lugares (con eval/) donde puede aparecer la palabra ground_truth.

NO sembramos esquemas entrelazados (dos esquemas que comparten una
entidad, ej. un money trail que cruza de un scheme a otro) -- cada
plant_* usa su propio _new_vendor() nuevo, asi que dos esquemas nuestros
nunca comparten RFC. Es una simplificacion aceptada del generador, no una
limitacion del sistema completo.

Los jueces SI pueden sembrar esquemas entrelazados en sus estates. Eso
implica, para cuando existan tools/, agent/ y report/:
  - que una misma entidad aparezca en dos findings distintos no debe
    tronar nada, ni deduplicarse o colapsarse en un solo hallazgo -- cada
    finding es independiente, con su propia cadena de evidencia.
  - que la seccion "Metodo y limites" del case file diga, cerca de
    textualmente: "no generamos esquemas entrelazados en nuestro conjunto
    de prueba; el sistema los procesa pero no esta afinado para ellos."
"""
import datetime as dt

import estate as E

SCHEME_TYPES = [
    "phantom_vendor", "kickback", "round_tripping",
    "threshold_splitting", "revenue_inflation",
]

# Umbral de aprobacion: por encima de esto una compra necesita una
# segunda firma. threshold_splitting lo evade; su decoy lo respeta con
# un contrato marco que lo explica. Varia por seed (ctx.approval_threshold,
# elegido en plant_all) porque el detector real -- en tools/, no aqui --
# nunca debe conocer este numero de antemano: los jueces generan sus
# estates con su propio umbral, y el detector tiene que inferirlo de
# purchase_orders (ver plant_all para el razonamiento completo).
APPROVAL_THRESHOLD_CHOICES = [50_000, 100_000, 250_000]


# ---------------------------------------------------------------------
# Helpers compartidos entre esquemas y decoys
# ---------------------------------------------------------------------
def _new_vendor(ctx, category=None, registered=None):
    """Crea y agrega un proveedor nuevo a ctx.vendors.

    Regresa (rfc, clabe, name, category, registered) para que el llamador
    pueda seguir usando estos datos al construir facturas/pagos.
    """
    rng = ctx.rng
    is_moral = rng.random() < 0.85
    rfc = E.gen_rfc_moral(rng, ctx.used_rfcs) if is_moral else E.gen_rfc_fisica(rng, ctx.used_rfcs)
    clabe = E.gen_clabe(rng, ctx.used_clabes)
    category = category or rng.choice(E.CATEGORIES)
    name = E._moral_name(rng, category) if is_moral else E._fisica_name(rng)
    registered = registered or E._random_date(rng, dt.date(2010, 1, 1), dt.date(2024, 6, 1))

    ctx.vendors.append((
        rfc, name, registered.isoformat(), E._address(rng), clabe, category, E._email(name),
    ))
    return rfc, clabe, name, category, registered


def _add_invoice(ctx, issuer_rfc, receiver_rfc, total, issue_date, concepto,
                  metodo_pago="PUE", status="vigente", book_as="expense"):
    """Agrega una factura + sus 2 asientos contables. book_as="revenue"
    cuando el emisor es la propia empresa (revenue_inflation)."""
    uuid_ = f"INV-{next(ctx.inv_seq):05d}"
    subtotal = round(total / 1.16, 2)
    iva = round(total - subtotal, 2)
    ctx.invoices.append((
        uuid_, issuer_rfc, receiver_rfc, issue_date.isoformat(), subtotal, iva, total,
        concepto, "G03", "03", metodo_pago, status,
    ))

    approver = ctx.rng.choice(ctx.employee_names)
    cost_center = ctx.rng.choice(E.COST_CENTERS)
    if book_as == "expense":
        debit_code, debit_name, credit_code, credit_name = "5000", "Gastos operativos", "2100", "Cuentas por pagar"
    else:
        debit_code, debit_name, credit_code, credit_name = "1200", "Cuentas por cobrar", "4000", "Ventas"

    ctx.ledger.append((next(ctx.entry_seq), issue_date.isoformat(), debit_code, debit_name,
                        total, 0.0, f"Registro factura {uuid_}", uuid_, cost_center, approver))
    ctx.ledger.append((next(ctx.entry_seq), issue_date.isoformat(), credit_code, credit_name,
                        0.0, total, f"Registro factura {uuid_}", uuid_, cost_center, approver))
    return uuid_


def _add_bank_txn(ctx, from_clabe, to_clabe, amount, date, reference, channel="SPEI"):
    txn_id = f"BNK-{next(ctx.txn_seq):05d}"
    ctx.bank_txns.append((txn_id, date.isoformat(), from_clabe, to_clabe, amount, reference, channel))
    return txn_id


def _settle_invoice(ctx, invoice_uuid, from_clabe, to_clabe, amount, issue_date, delay_days=None):
    """Paga una factura (transferencia + 2 asientos de liquidacion)."""
    delay = ctx.rng.randint(3, 45) if delay_days is None else delay_days
    pay_date = issue_date + dt.timedelta(days=delay)
    txn_id = _add_bank_txn(ctx, from_clabe, to_clabe, amount, pay_date, f"Pago factura {invoice_uuid}")

    approver = ctx.rng.choice(ctx.employee_names)
    cost_center = ctx.rng.choice(E.COST_CENTERS)
    ctx.ledger.append((next(ctx.entry_seq), pay_date.isoformat(), "2100", "Cuentas por pagar",
                        amount, 0.0, f"Pago factura {invoice_uuid}", invoice_uuid, cost_center, approver))
    ctx.ledger.append((next(ctx.entry_seq), pay_date.isoformat(), "1100", "Bancos",
                        0.0, amount, f"Pago factura {invoice_uuid}", invoice_uuid, cost_center, approver))
    return txn_id, pay_date


# ---------------------------------------------------------------------
# Los cinco esquemas
# ---------------------------------------------------------------------
def plant_phantom_vendor(ctx, scheme_id):
    """Proveedor sin contrato ni OC, alta reciente, concepto generico,
    senalado en la lista 69-B. Nunca se le crea contrato ni purchase_order."""
    rng = ctx.rng
    registered = E._random_date(rng, dt.date(2024, 1, 1), dt.date(2024, 10, 1))
    rfc, clabe, name, _category, _ = _new_vendor(ctx, registered=registered)

    ctx.efos_list.append((
        rfc, name, "definitivo",
        E._random_date(rng, registered, dt.date(2025, 12, 31)).isoformat(),
    ))

    conceptos_genericos = [
        "Servicios de consultoria", "Asesoria administrativa", "Servicios profesionales",
    ]
    invoice_ids, txn_ids = [], []
    total_amount = 0.0
    for _ in range(rng.randint(1, 3)):
        issue = E._random_date(rng, registered + dt.timedelta(days=15), dt.date(2024, 12, 1))
        total = round(rng.uniform(80_000, 1_500_000), 2)
        uuid_ = _add_invoice(ctx, rfc, ctx.company_rfc, total, issue, rng.choice(conceptos_genericos))
        txn_id, _ = _settle_invoice(ctx, uuid_, ctx.company_clabe, clabe, total, issue)
        invoice_ids.append(uuid_)
        txn_ids.append(txn_id)
        total_amount += total

    return {
        "scheme_id": scheme_id,
        "type": "phantom_vendor",
        "entities": [f"RFC:{rfc}"],
        "supporting_invoices": invoice_ids,
        "supporting_txns": txn_ids,
        "peso_amount": round(total_amount, 2),
        "difficulty": "easy",
    }


def plant_kickback(ctx, scheme_id):
    """Proveedor con papeles normales (contrato + OC): el fraude esta en
    que, tras cobrar, transfiere una parte a la CLABE de un empleado."""
    rng = ctx.rng
    rfc, clabe, _name, category, registered = _new_vendor(ctx)

    ctx.contracts.append((
        f"CTR-{next(ctx.ctr_seq):05d}", rfc,
        E._random_date(rng, registered, dt.date(2024, 6, 1)).isoformat(),
        round(rng.uniform(200_000, 1_500_000), 2), f"Contrato de {category.lower()}",
    ))
    ctx.purchase_orders.append((
        f"PO-{next(ctx.po_seq):05d}", rfc,
        E._random_date(rng, registered, dt.date(2024, 6, 1)).isoformat(),
        round(rng.uniform(50_000, 400_000), 2),
        rng.choice(ctx.employee_names), rng.choice(ctx.employee_names),
        f"Orden de compra: {rng.choice(E.GIRO_CONCEPTOS[category])}",
    ))

    issue = E._random_date(rng, dt.date(2024, 2, 1), dt.date(2024, 10, 1))
    total = round(rng.uniform(150_000, 900_000), 2)
    uuid_ = _add_invoice(ctx, rfc, ctx.company_rfc, total, issue, rng.choice(E.GIRO_CONCEPTOS[category]))
    settle_txn, pay_date = _settle_invoice(ctx, uuid_, ctx.company_clabe, clabe, total, issue)

    employee = rng.choice(ctx.employees)
    kickback_amount = round(total * rng.uniform(0.08, 0.20), 2)
    kb_date = pay_date + dt.timedelta(days=rng.randint(2, 10))
    kb_txn = _add_bank_txn(ctx, clabe, employee["bank_clabe"], kickback_amount, kb_date,
                            "Reembolso de gastos")

    return {
        "scheme_id": scheme_id,
        "type": "kickback",
        "entities": [f"RFC:{rfc}", employee["emp_id"]],
        "supporting_invoices": [uuid_],
        "supporting_txns": [settle_txn, kb_txn],
        "peso_amount": kickback_amount,
        "difficulty": "medium",
    }


def plant_round_tripping(ctx, scheme_id):
    """El dinero sale de la empresa, pasa por 2-3 proveedores (solo el
    primero tiene una factura real detras) y regresa a la CLABE de la
    empresa."""
    rng = ctx.rng
    chain = [_new_vendor(ctx) for _ in range(rng.randint(2, 3))]

    issue = E._random_date(rng, dt.date(2024, 2, 1), dt.date(2024, 9, 1))
    total = round(rng.uniform(300_000, 2_000_000), 2)
    first_rfc, first_clabe, _n, first_cat, _r = chain[0]
    invoice_uuid = _add_invoice(ctx, first_rfc, ctx.company_rfc, total, issue,
                                 rng.choice(E.GIRO_CONCEPTOS[first_cat]))
    settle_txn, pay_date = _settle_invoice(ctx, invoice_uuid, ctx.company_clabe, first_clabe, total, issue)

    txn_ids = [settle_txn]
    current_amount, current_clabe, current_date = total, first_clabe, pay_date
    for rfc, clabe, *_rest in chain[1:]:
        current_amount = round(current_amount * rng.uniform(0.90, 0.98), 2)
        current_date = current_date + dt.timedelta(days=rng.randint(2, 8))
        txn_ids.append(_add_bank_txn(ctx, current_clabe, clabe, current_amount, current_date,
                                      "Transferencia entre empresas"))
        current_clabe = clabe

    current_amount = round(current_amount * rng.uniform(0.90, 0.98), 2)
    current_date = current_date + dt.timedelta(days=rng.randint(2, 8))
    txn_ids.append(_add_bank_txn(ctx, current_clabe, ctx.company_clabe, current_amount, current_date,
                                  "Transferencia entre empresas"))

    return {
        "scheme_id": scheme_id,
        "type": "round_tripping",
        "entities": [f"RFC:{rfc}" for rfc, *_rest in chain],
        "supporting_invoices": [invoice_uuid],
        "supporting_txns": txn_ids,
        "peso_amount": current_amount,
        "difficulty": "hard" if len(chain) == 3 else "medium",
    }


def plant_threshold_splitting(ctx, scheme_id):
    """Varias facturas del mismo proveedor, fechas cercanas, cada una
    justo debajo de ctx.approval_threshold, aprobadas por la misma persona."""
    rng = ctx.rng
    rfc, clabe, _name, category, _registered = _new_vendor(ctx)
    approver = rng.choice(ctx.employee_names)

    base_date = E._random_date(rng, dt.date(2024, 3, 1), dt.date(2024, 10, 1))
    invoice_ids, txn_ids = [], []
    total_amount = 0.0
    for i in range(rng.randint(3, 5)):
        issue = base_date + dt.timedelta(days=i * rng.randint(1, 3))
        total = round(ctx.approval_threshold * rng.uniform(0.85, 0.98), 2)
        ctx.purchase_orders.append((
            f"PO-{next(ctx.po_seq):05d}", rfc, issue.isoformat(), total,
            rng.choice(ctx.employee_names), approver,
            f"Orden de compra: {rng.choice(E.GIRO_CONCEPTOS[category])}",
        ))
        uuid_ = _add_invoice(ctx, rfc, ctx.company_rfc, total, issue, rng.choice(E.GIRO_CONCEPTOS[category]))
        txn_id, _ = _settle_invoice(ctx, uuid_, ctx.company_clabe, clabe, total, issue)
        invoice_ids.append(uuid_)
        txn_ids.append(txn_id)
        total_amount += total

    return {
        "scheme_id": scheme_id,
        "type": "threshold_splitting",
        "entities": [f"RFC:{rfc}"],
        "supporting_invoices": invoice_ids,
        "supporting_txns": txn_ids,
        "peso_amount": round(total_amount, 2),
        "difficulty": "medium",
    }


def plant_revenue_inflation(ctx, scheme_id):
    """La empresa emite facturas (como emisora) por ventas que ningun
    bank_txn llega a liquidar jamas."""
    rng = ctx.rng
    client_rfc, _clabe, _name, category, _registered = _new_vendor(ctx)

    invoice_ids = []
    total_amount = 0.0
    for _ in range(rng.randint(1, 3)):
        issue = E._random_date(rng, dt.date(2024, 3, 1), dt.date(2024, 11, 1))
        total = round(rng.uniform(100_000, 1_200_000), 2)
        uuid_ = _add_invoice(ctx, ctx.company_rfc, client_rfc, total, issue,
                              rng.choice(E.GIRO_CONCEPTOS[category]), book_as="revenue")
        invoice_ids.append(uuid_)
        total_amount += total

    return {
        "scheme_id": scheme_id,
        "type": "revenue_inflation",
        "entities": [f"RFC:{ctx.company_rfc}", f"RFC:{client_rfc}"],
        "supporting_invoices": invoice_ids,
        "supporting_txns": [],
        "peso_amount": round(total_amount, 2),
        "difficulty": "medium",
    }


# ---------------------------------------------------------------------
# Los decoys: honestos, disparan una senal, se limpian al inspeccionarlos.
# ---------------------------------------------------------------------
def decoy_efos_presunto_limpio(ctx):
    """Proveedor en efos_list con estatus presunto, pero con contrato y
    OC vigentes y pago unico sin retorno."""
    rng = ctx.rng
    candidatos = [
        (rfc, name) for (rfc, name, status, _pub) in ctx.efos_list
        if status == "presunto" and any(v[0] == rfc for v in ctx.vendors)
    ]
    if not candidatos:
        return None
    rfc, _name = rng.choice(candidatos)

    if not any(c[1] == rfc for c in ctx.contracts):
        registered = dt.date.fromisoformat(next(v[2] for v in ctx.vendors if v[0] == rfc))
        start = E._random_date(rng, registered, dt.date(2024, 6, 1))
        ctx.contracts.append((f"CTR-{next(ctx.ctr_seq):05d}", rfc, start.isoformat(),
                               round(rng.uniform(100_000, 1_000_000), 2), "Contrato de servicios"))
    if not any(po[1] == rfc for po in ctx.purchase_orders):
        ctx.purchase_orders.append((
            f"PO-{next(ctx.po_seq):05d}", rfc, dt.date(2024, 3, 1).isoformat(),
            round(rng.uniform(20_000, 200_000), 2),
            rng.choice(ctx.employee_names), rng.choice(ctx.employee_names),
            "Orden de compra de respaldo",
        ))

    invoice_ids = [inv[0] for inv in ctx.invoices if inv[1] == rfc]
    return {
        "entity": f"RFC:{rfc}",
        "signal": "efos_presunto_sin_materialidad_aparente",
        "why_innocent": ("Contrato vigente y orden de compra respaldan la operacion; pago "
                          "unico sin retorno de fondos, pese al estatus presunto en la lista 69-B."),
        "invoices": invoice_ids,
    }


def decoy_mismo_banco(ctx):
    """Empleado y proveedor bancan en la misma institucion (mismo prefijo
    de CLABE) pero son cuentas distintas: no hay transferencia entre ellas."""
    rng = ctx.rng
    employee = rng.choice(ctx.employees)
    bank_code = employee["bank_clabe"][:3]

    rfc, clabe, _name, category, _registered = _new_vendor(ctx)
    ctx.used_clabes.discard(clabe)
    plaza = clabe[3:6]
    while True:
        account = "".join(str(rng.randint(0, 9)) for _ in range(11))
        base17 = f"{bank_code}{plaza}{account}"
        new_clabe = base17 + E._clabe_check_digit(base17)
        if new_clabe not in ctx.used_clabes:
            ctx.used_clabes.add(new_clabe)
            break
    old = ctx.vendors[-1]
    ctx.vendors[-1] = old[:4] + (new_clabe,) + old[5:]

    issue = E._random_date(rng, dt.date(2024, 2, 1), dt.date(2024, 9, 1))
    total = round(rng.uniform(50_000, 300_000), 2)
    uuid_ = _add_invoice(ctx, rfc, ctx.company_rfc, total, issue, rng.choice(E.GIRO_CONCEPTOS[category]))
    _settle_invoice(ctx, uuid_, ctx.company_clabe, new_clabe, total, issue)

    return {
        "entity": f"RFC:{rfc}",
        "signal": "proveedor_empleado_mismo_banco",
        "why_innocent": (f"El proveedor y {employee['emp_id']} bancan en la misma institucion "
                          "(mismo prefijo de CLABE) pero son cuentas distintas; no existe "
                          "transferencia alguna entre ellas."),
        "invoices": [uuid_],
    }


def decoy_contrato_marco(ctx):
    """Facturacion mensual recurrente, cada factura bajo el umbral de
    aprobacion, pero explicada por un contrato marco con cuota fija."""
    rng = ctx.rng
    rfc, clabe, _name, category, registered = _new_vendor(ctx)
    start = E._random_date(rng, registered, dt.date(2024, 3, 1))
    cuota = round(ctx.approval_threshold * rng.uniform(0.6, 0.9), 2)
    ctx.contracts.append((
        f"CTR-{next(ctx.ctr_seq):05d}", rfc, start.isoformat(), round(cuota * 12, 2),
        f"Contrato marco de {category.lower()}, cuota mensual fija de ${cuota:,.2f}",
    ))

    invoice_ids = []
    for i in range(rng.randint(4, 6)):
        issue = start + dt.timedelta(days=30 * (i + 1))
        if issue > dt.date(2024, 12, 15):
            break
        uuid_ = _add_invoice(ctx, rfc, ctx.company_rfc, cuota, issue,
                              f"Cuota mensual - {rng.choice(E.GIRO_CONCEPTOS[category])}")
        _settle_invoice(ctx, uuid_, ctx.company_clabe, clabe, cuota, issue)
        invoice_ids.append(uuid_)

    return {
        "entity": f"RFC:{rfc}",
        "signal": "facturacion_repetida_bajo_limite_de_aprobacion",
        "why_innocent": ("Contrato marco vigente con cuota mensual fija; la facturacion "
                          "recurrente corresponde a pagos mensuales identicos, no a "
                          "fraccionamiento para evadir aprobacion."),
        "invoices": invoice_ids,
    }


def decoy_proveedor_cliente(ctx):
    """Proveedor que tambien es cliente: hay dinero de vuelta, pero con
    su propia factura en sentido contrario que lo justifica."""
    rng = ctx.rng
    rfc, clabe, _name, category, _registered = _new_vendor(ctx)

    issue1 = E._random_date(rng, dt.date(2024, 2, 1), dt.date(2024, 8, 1))
    total1 = round(rng.uniform(200_000, 1_000_000), 2)
    inv1 = _add_invoice(ctx, rfc, ctx.company_rfc, total1, issue1, rng.choice(E.GIRO_CONCEPTOS[category]))
    _settle_invoice(ctx, inv1, ctx.company_clabe, clabe, total1, issue1)

    issue2 = issue1 + dt.timedelta(days=rng.randint(10, 40))
    total2 = round(total1 * rng.uniform(0.7, 0.95), 2)
    inv2 = _add_invoice(ctx, ctx.company_rfc, rfc, total2, issue2,
                         "Venta de producto terminado", book_as="revenue")
    _settle_invoice(ctx, inv2, clabe, ctx.company_clabe, total2, issue2)

    return {
        "entity": f"RFC:{rfc}",
        "signal": "retorno_de_fondos_a_la_empresa",
        "why_innocent": (f"El proveedor tambien es cliente: el retorno corresponde al pago de "
                          f"su propia factura {inv2}, respaldada por una operacion de venta real."),
        "invoices": [inv1, inv2],
    }


def decoy_alta_reciente_contrato_previo(ctx):
    """Proveedor de alta reciente (misma firma temporal que phantom_vendor)
    pero con contrato firmado ANTES de su alta formal."""
    rng = ctx.rng
    registered = E._random_date(rng, dt.date(2024, 6, 1), dt.date(2024, 10, 1))
    rfc, clabe, _name, category, _ = _new_vendor(ctx, registered=registered)

    start = registered - dt.timedelta(days=rng.randint(60, 200))
    contract_id = f"CTR-{next(ctx.ctr_seq):05d}"
    ctx.contracts.append((
        contract_id, rfc, start.isoformat(), round(rng.uniform(200_000, 900_000), 2),
        f"Contrato de {category.lower()}, negociado antes del alta formal del RFC",
    ))

    issue = E._random_date(rng, registered + dt.timedelta(days=10), dt.date(2024, 12, 1))
    total = round(rng.uniform(80_000, 400_000), 2)
    uuid_ = _add_invoice(ctx, rfc, ctx.company_rfc, total, issue, rng.choice(E.GIRO_CONCEPTOS[category]))
    _settle_invoice(ctx, uuid_, ctx.company_clabe, clabe, total, issue)

    return {
        "entity": f"RFC:{rfc}",
        "signal": "alta_reciente_antes_de_primera_factura",
        "why_innocent": (f"El contrato {contract_id} esta firmado antes de la fecha de alta del "
                          "proveedor: la relacion comercial es anterior al registro formal del RFC."),
        "invoices": [uuid_],
    }


SCHEME_BUILDERS = {
    "phantom_vendor": plant_phantom_vendor,
    "kickback": plant_kickback,
    "round_tripping": plant_round_tripping,
    "threshold_splitting": plant_threshold_splitting,
    "revenue_inflation": plant_revenue_inflation,
}

DECOY_BUILDERS = [
    decoy_efos_presunto_limpio,
    decoy_mismo_banco,
    decoy_contrato_marco,
    decoy_proveedor_cliente,
    decoy_alta_reciente_contrato_previo,
]


def plant_all(ctx):
    """Decide con ctx.rng cuantos esquemas y decoys sembrar y de que tipo,
    los siembra, y regresa (schemes, decoys) listos para ground_truth."""
    rng = ctx.rng

    # El umbral de aprobacion varia por seed. Esto no es solo variedad:
    # el detector de threshold_splitting (en tools/, todavia no escrito)
    # NUNCA puede traer este numero hardcodeado, porque los jueces generan
    # sus propios estates con su propio umbral y nosotros no lo sabemos.
    # El detector real lo infiere de purchase_orders:
    #   SELECT approver, MAX(amount) AS techo
    #   FROM purchase_orders GROUP BY approver ORDER BY techo
    # Los aprobadores forman escalones; el techo del escalon mas bajo es
    # el umbral, redondeado al multiplo de 50,000 mas cercano por arriba.
    ctx.approval_threshold = rng.choice(APPROVAL_THRESHOLD_CHOICES)

    # 0 es un valor valido a proposito: un estate sin ningun esquema
    # sembrado (solo decoys) es un resultado legitimo, y un sistema que
    # siempre encuentra algo es un sistema que siempre acusa.
    chosen_types = rng.sample(SCHEME_TYPES, k=rng.randint(0, 3))
    schemes = [
        SCHEME_BUILDERS[scheme_type](ctx, f"S{i}_{scheme_type}_1")
        for i, scheme_type in enumerate(chosen_types, start=1)
    ]

    chosen_decoys = rng.sample(DECOY_BUILDERS, k=rng.randint(2, len(DECOY_BUILDERS)))
    decoys = [d for builder in chosen_decoys if (d := builder(ctx)) is not None]

    return schemes, decoys
