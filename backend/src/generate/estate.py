"""
Generador determinista del data estate de The Forensic Auditor.

    python3 src/generate/estate.py --seed 1 --out out/
    -> out/estate_seed001.db
    -> out/truth_seed001.json

Todo lo aleatorio pasa por UNA instancia random.Random(seed), pasada como
parametro a cada helper. Nada de random global, nada de datetime.now(),
nada de uuid4 sin semilla -- el mismo seed debe reproducir exactamente
el mismo archivo (mismo md5).

Primero siembra las 8 tablas oficiales con operacion limpia y coherente
entre si (empresa investigada, proveedores, empleados, facturas con su
asiento contable y su pago, ordenes de compra, contratos, 69-B). Despues
llama a schemes.plant_all() para sembrar, sobre esos mismos datos, un
numero de esquemas de fraude y decoys que decide ctx.rng (nunca fijo).

ground_truth (schemes + decoys) se escribe aparte, en
out/truth_seedNNN.json -- el agente y sus herramientas (tools/, agent/)
nunca deben importar este archivo ni la palabra "ground_truth". Este
modulo y schemes.py son, junto con eval/, los unicos lugares donde esa
palabra puede aparecer.
"""
import argparse
import datetime as dt
import itertools
import json
import random
import re
import sqlite3
import string
from pathlib import Path
from types import SimpleNamespace

import schemes

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

N_VENDORS_RANGE = (30, 50)
N_EMPLOYEES_RANGE = (8, 15)

BANK_CODES = ["002", "012", "014", "021", "030", "036", "044", "058", "072", "127"]
PLAZA_CODES = ["001", "010", "014", "019", "022", "039"]
CLABE_WEIGHTS = [3, 7, 1] * 5 + [3, 7]  # 17 pesos para las primeras 17 posiciones

MORAL_SUFFIXES = ["SA DE CV", "SC", "SA", "SAPI DE CV", "SRL DE CV"]
EMPRESA_PALABRA_1 = [
    "Consultores", "Servicios", "Grupo", "Constructora", "Comercializadora",
    "Soluciones", "Distribuidora", "Tecnologia", "Suministros", "Operadora",
]
EMPRESA_PALABRA_2 = [
    "del Norte", "Integral", "Nacional", "Regiomontana", "del Bajio",
    "Industrial", "Profesional", "Mexicana", "del Centro", "Empresarial",
]

NOMBRES = [
    "Juan", "Maria", "Carlos", "Ana", "Luis", "Patricia", "Jorge", "Laura",
    "Roberto", "Sofia", "Miguel", "Claudia", "Ricardo", "Veronica", "Eduardo",
]
APELLIDOS = [
    "Garcia", "Martinez", "Lopez", "Hernandez", "Gonzalez", "Perez",
    "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Morales",
]

ROLES = [
    "Gerente de Compras", "Director de Finanzas", "Analista Contable",
    "Comprador", "Contralor", "Auxiliar Contable", "Gerente de Operaciones",
    "Tesorero", "Asistente de Compras", "Contador General",
]

CALLES = [
    "Calle Hidalgo", "Av. Constitucion", "Calle Morelos", "Av. Revolucion",
    "Calle Juarez", "Blvd. Diaz Ordaz", "Av. Gonzalitos", "Calle Allende",
]
COLONIAS = [
    "Centro", "Del Valle", "Contry", "Cumbres", "San Jeronimo",
    "Mitras Centro", "Obispado", "Roma",
]
COST_CENTERS = ["CC-100 Produccion", "CC-200 Administracion", "CC-300 Ventas"]

USO_CFDI_CODES = ["G01", "G02", "G03"]
USO_CFDI_WEIGHTS = [15, 10, 75]
FORMA_PAGO_CODES = ["01", "03", "04"]
FORMA_PAGO_WEIGHTS = [15, 75, 10]

CATEGORY_PALABRA_1 = {
    "Consultoria administrativa": ["Consultores", "Grupo"],
    "Servicios de mantenimiento": ["Servicios", "Operadora"],
    "Logistica y transporte": ["Distribuidora", "Operadora"],
    "Publicidad y marketing": ["Grupo", "Soluciones"],
    "Construccion y obra civil": ["Constructora", "Grupo"],
    "Tecnologia de la informacion": ["Tecnologia", "Soluciones"],
    "Suministro de materiales": ["Suministros", "Distribuidora"],
    "Servicios profesionales": ["Consultores", "Servicios"],
    "Limpieza industrial": ["Servicios", "Operadora"],
    "Renta de equipo": ["Operadora", "Comercializadora"],
}

GIRO_CONCEPTOS = {
    "Consultoria administrativa": [
        "Servicios de consultoria administrativa",
        "Asesoria en procesos de negocio",
        "Diagnostico organizacional",
    ],
    "Servicios de mantenimiento": [
        "Mantenimiento preventivo de instalaciones",
        "Mantenimiento correctivo de equipo",
        "Servicio tecnico especializado",
    ],
    "Logistica y transporte": [
        "Transporte de materiales", "Servicio de fletes",
        "Distribucion de mercancia",
    ],
    "Publicidad y marketing": [
        "Servicios de publicidad", "Campana de marketing digital",
        "Diseno de material promocional",
    ],
    "Construccion y obra civil": [
        "Obra civil menor", "Remodelacion de instalaciones",
        "Suministro de materiales de construccion",
    ],
    "Tecnologia de la informacion": [
        "Desarrollo de software a la medida", "Soporte tecnico de sistemas",
        "Licenciamiento de software",
    ],
    "Suministro de materiales": [
        "Suministro de material electrico", "Suministro de refacciones",
        "Venta de insumos industriales",
    ],
    "Servicios profesionales": [
        "Asesoria legal", "Auditoria externa",
        "Servicios de recursos humanos",
    ],
    "Limpieza industrial": [
        "Servicio de limpieza industrial", "Limpieza de areas comunes",
        "Manejo de residuos",
    ],
    "Renta de equipo": [
        "Renta de equipo de computo", "Renta de maquinaria",
        "Renta de mobiliario",
    ],
}
CATEGORIES = list(GIRO_CONCEPTOS)

EFOS_STATUSES = ["definitivo", "presunto"]
EFOS_WEIGHTS = [60, 40]


# ---------------------------------------------------------------------
# Helpers deterministas: todos reciben `rng` como parametro.
# ---------------------------------------------------------------------
def _random_date(rng: random.Random, start: dt.date, end: dt.date) -> dt.date:
    if end < start:
        start, end = end, start
    return start + dt.timedelta(days=rng.randint(0, (end - start).days))


def _clabe_check_digit(seventeen_digits: str) -> str:
    total = sum((int(d) * w) % 10 for d, w in zip(seventeen_digits, CLABE_WEIGHTS))
    return str((10 - (total % 10)) % 10)


def gen_clabe(rng: random.Random, used: set) -> str:
    while True:
        bank = rng.choice(BANK_CODES)
        plaza = rng.choice(PLAZA_CODES)
        account = "".join(str(rng.randint(0, 9)) for _ in range(11))
        base17 = f"{bank}{plaza}{account}"
        clabe = base17 + _clabe_check_digit(base17)
        if clabe not in used:
            used.add(clabe)
            return clabe


def _homoclave(rng: random.Random) -> str:
    alnum = string.ascii_uppercase + string.digits
    return "".join(rng.choice(alnum) for _ in range(2)) + str(rng.randint(0, 9))


def gen_rfc_moral(rng: random.Random, used: set) -> str:
    while True:
        letters = "".join(rng.choice(string.ascii_uppercase) for _ in range(3))
        date_part = _random_date(rng, dt.date(1995, 1, 1), dt.date(2022, 12, 31))
        rfc = f"{letters}{date_part.strftime('%y%m%d')}{_homoclave(rng)}"  # 3+6+3=12
        if rfc not in used:
            used.add(rfc)
            return rfc


def gen_rfc_fisica(rng: random.Random, used: set) -> str:
    while True:
        letters = "".join(rng.choice(string.ascii_uppercase) for _ in range(4))
        date_part = _random_date(rng, dt.date(1960, 1, 1), dt.date(2005, 12, 31))
        rfc = f"{letters}{date_part.strftime('%y%m%d')}{_homoclave(rng)}"  # 4+6+3=13
        if rfc not in used:
            used.add(rfc)
            return rfc


def _moral_name(rng: random.Random, category=None) -> str:
    palabra_1 = CATEGORY_PALABRA_1.get(category, EMPRESA_PALABRA_1)
    w1 = rng.choice(palabra_1)
    w2 = rng.choice(EMPRESA_PALABRA_2)
    suffix = rng.choice(MORAL_SUFFIXES)
    return f"{w1} {w2} {suffix}".upper()


def _fisica_name(rng: random.Random) -> str:
    nombre = rng.choice(NOMBRES)
    ap1 = rng.choice(APELLIDOS)
    ap2 = rng.choice(APELLIDOS)
    return f"{nombre} {ap1} {ap2}".upper()


def _email(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", ".", name.lower()).strip(".")
    return f"{slug}@example.mx"


def _address(rng: random.Random) -> str:
    calle = rng.choice(CALLES)
    numero = rng.randint(1, 999)
    colonia = rng.choice(COLONIAS)
    return f"{calle} #{numero}, Col. {colonia}, Monterrey, NL"


def _make_employee(rng: random.Random, i: int, used_clabes: set, role: str = None) -> dict:
    nombre = rng.choice(NOMBRES)
    ap1 = rng.choice(APELLIDOS)
    ap2 = rng.choice(APELLIDOS)
    hire = _random_date(rng, dt.date(2015, 1, 1), dt.date(2024, 1, 1))
    return {
        "emp_id": f"EMP:{i:04d}",
        "name": f"{nombre} {ap1} {ap2}".upper(),
        "role": role or rng.choice(ROLES),
        "bank_clabe": gen_clabe(rng, used_clabes),
        "hire_date": hire.isoformat(),
    }


# ---------------------------------------------------------------------
# Escalones de aprobacion. El umbral que "threshold_splitting" evade no
# es un numero flotando solo: es el techo real del nivel mas bajo, y por
# eso infer_approval_threshold() (en tools/) lo puede inferir agrupando
# purchase_orders por approver. Sin aprobadores con techo real, agrupar
# por approver es puro ruido -- no hay escalon que inferir.
# ---------------------------------------------------------------------
APPROVAL_THRESHOLD_CHOICES = [50_000, 100_000, 250_000]
APPROVER_TIERS = {
    "coordinador": "Coordinador de Compras",
    "gerente": "Gerente de Compras",
    "director": "Director de Compras",
}


def _make_approval_tiers(rng, used_clabes, next_emp_id):
    """2 o 3 personas por nivel. Regresa (tiers, empleados, siguiente_id)
    donde tiers = {"coordinador": [nombre, ...], "gerente": [...], ...}."""
    tiers = {}
    empleados = []
    i = next_emp_id
    for nivel, role in APPROVER_TIERS.items():
        nombres = []
        for _ in range(rng.randint(2, 3)):
            emp = _make_employee(rng, i, used_clabes, role=role)
            empleados.append(emp)
            nombres.append(emp["name"])
            i += 1
        tiers[nivel] = nombres
    return tiers, empleados, i


def _approver_for_amount(rng, amount, threshold, tiers):
    """El nivel MAS BAJO cuyo techo cubre el monto firma la orden de
    compra: coordinador hasta threshold, gerente hasta threshold*5,
    director sin techo."""
    if amount <= threshold:
        nivel = "coordinador"
    elif amount <= threshold * 5:
        nivel = "gerente"
    else:
        nivel = "director"
    return rng.choice(tiers[nivel])


# ---------------------------------------------------------------------
# Construccion del estate
# ---------------------------------------------------------------------
def build_estate(seed: int, out_dir: Path) -> tuple[Path, dict]:
    rng = random.Random(seed)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / f"estate_seed{seed:03d}.db"
    db_path.unlink(missing_ok=True)

    used_rfcs: set = set()
    used_clabes: set = set()

    company_rfc = gen_rfc_moral(rng, used_rfcs)
    company_clabe = gen_clabe(rng, used_clabes)

    # El umbral se elige aqui, antes de generar aprobadores u ordenes de
    # compra: todo el estate (limpio y sembrado) tiene que ser consistente
    # con el mismo escalon de autoridad.
    approval_threshold = rng.choice(APPROVAL_THRESHOLD_CHOICES)
    tiers, tier_employees, next_emp_id = _make_approval_tiers(rng, used_clabes, 1)

    n_vendors = rng.randint(*N_VENDORS_RANGE)
    n_employees = rng.randint(*N_EMPLOYEES_RANGE)

    employees = tier_employees + [
        _make_employee(rng, i, used_clabes) for i in range(next_emp_id, next_emp_id + n_employees)
    ]
    employee_names = [e["name"] for e in employees]

    vendors, contracts, purchase_orders = [], [], []
    invoices, ledger, bank_txns = [], [], []

    entry_seq = itertools.count(1)
    inv_seq = itertools.count(1)
    po_seq = itertools.count(1)
    ctr_seq = itertools.count(1)
    txn_seq = itertools.count(1)

    for _ in range(n_vendors):
        is_moral = rng.random() < 0.85
        rfc = gen_rfc_moral(rng, used_rfcs) if is_moral else gen_rfc_fisica(rng, used_rfcs)
        clabe = gen_clabe(rng, used_clabes)
        category = rng.choice(CATEGORIES)
        name = _moral_name(rng, category) if is_moral else _fisica_name(rng)
        registered = _random_date(rng, dt.date(2010, 1, 1), dt.date(2024, 6, 1))

        vendors.append((
            rfc, name, registered.isoformat(), _address(rng), clabe,
            category, _email(name),
        ))

        if rng.random() < 0.4:
            value = round(rng.uniform(100_000, 3_000_000), 2)
            start = _random_date(rng, registered, dt.date(2024, 6, 1))
            contracts.append((
                f"CTR-{next(ctr_seq):05d}", rfc, start.isoformat(), value,
                f"Contrato de {category.lower()}",
            ))

        n_po = rng.randint(1, 3) if rng.random() < 0.7 else 0
        for _ in range(n_po):
            po_date = _random_date(rng, registered, dt.date(2024, 6, 1))
            po_amount = round(rng.uniform(5_000, 400_000), 2)
            purchase_orders.append((
                f"PO-{next(po_seq):05d}", rfc, po_date.isoformat(), po_amount,
                rng.choice(employee_names),
                _approver_for_amount(rng, po_amount, approval_threshold, tiers),
                f"Orden de compra: {rng.choice(GIRO_CONCEPTOS[category])}",
            ))

        for _ in range(rng.randint(1, 6)):
            issue = _random_date(rng, max(registered, dt.date(2024, 1, 1)), dt.date(2024, 12, 31))
            subtotal = round(rng.uniform(5_000, 500_000), 2)
            iva = round(subtotal * 0.16, 2)
            total = round(subtotal + iva, 2)
            status = "vigente" if rng.random() < 0.95 else "cancelado"
            uuid_ = f"INV-{next(inv_seq):05d}"

            invoices.append((
                uuid_, rfc, company_rfc, issue.isoformat(), subtotal, iva, total,
                rng.choice(GIRO_CONCEPTOS[category]),
                rng.choices(USO_CFDI_CODES, weights=USO_CFDI_WEIGHTS)[0],
                rng.choices(FORMA_PAGO_CODES, weights=FORMA_PAGO_WEIGHTS)[0],
                rng.choices(["PUE", "PPD"], weights=[75, 25])[0],
                status,
            ))

            approver = rng.choice(employee_names)
            cost_center = rng.choice(COST_CENTERS)

            ledger.append((next(entry_seq), issue.isoformat(), "5000", "Gastos operativos",
                            total, 0.0, f"Registro factura {uuid_}", uuid_, cost_center, approver))
            ledger.append((next(entry_seq), issue.isoformat(), "2100", "Cuentas por pagar",
                            0.0, total, f"Registro factura {uuid_}", uuid_, cost_center, approver))

            if status == "vigente":
                pay_date = issue + dt.timedelta(days=rng.randint(3, 45))
                txn_id = f"BNK-{next(txn_seq):05d}"
                bank_txns.append((
                    txn_id, pay_date.isoformat(), company_clabe, clabe, total,
                    f"Pago factura {uuid_}", "SPEI",
                ))
                ledger.append((next(entry_seq), pay_date.isoformat(), "2100", "Cuentas por pagar",
                                total, 0.0, f"Pago factura {uuid_}", uuid_, cost_center, approver))
                ledger.append((next(entry_seq), pay_date.isoformat(), "1100", "Bancos",
                                0.0, total, f"Pago factura {uuid_}", uuid_, cost_center, approver))

    efos_list = _make_efos_list(rng, vendors, used_rfcs)

    ctx = SimpleNamespace(
        rng=rng, company_rfc=company_rfc, company_clabe=company_clabe,
        employees=employees, employee_names=employee_names,
        approval_threshold=approval_threshold, tiers=tiers,
        used_rfcs=used_rfcs, used_clabes=used_clabes,
        vendors=vendors, invoices=invoices, ledger=ledger, bank_txns=bank_txns,
        purchase_orders=purchase_orders, contracts=contracts, efos_list=efos_list,
        inv_seq=inv_seq, txn_seq=txn_seq, po_seq=po_seq, ctr_seq=ctr_seq, entry_seq=entry_seq,
    )
    schemes_planted, decoys_planted = schemes.plant_all(ctx)

    ground_truth = {
        "seed": seed,
        "company_rfc": company_rfc,
        "schemes": schemes_planted,
        "decoys": decoys_planted,
    }
    truth_path = out_dir / f"truth_seed{seed:03d}.json"
    truth_path.write_text(json.dumps(ground_truth, ensure_ascii=False, indent=2), encoding="utf-8")

    _write_db(db_path, {
        "vendors": vendors,
        "invoices": invoices,
        "ledger": ledger,
        "bank_txns": bank_txns,
        "purchase_orders": purchase_orders,
        "contracts": contracts,
        "employees": [(e["emp_id"], e["name"], e["role"], e["bank_clabe"], e["hire_date"])
                       for e in employees],
        "efos_list": efos_list,
    })

    stats = {
        "seed": seed,
        "company_rfc": company_rfc,
        "n_vendors": len(vendors),
        "n_employees": len(employees),
        "n_invoices": len(invoices),
        "n_efos": len(efos_list),
        "n_schemes": len(schemes_planted),
        "n_decoys": len(decoys_planted),
        "truth_path": truth_path,
    }
    return db_path, stats


def _make_efos_list(rng: random.Random, vendors: list, used_rfcs: set) -> list:
    rows = []

    propios = list(vendors)
    rng.shuffle(propios)
    n_flagged = max(2, round(len(vendors) * rng.uniform(0.10, 0.20)))
    for rfc, legal_name, *_ in propios[:n_flagged]:
        status = rng.choices(EFOS_STATUSES, weights=EFOS_WEIGHTS)[0]
        pub = _random_date(rng, dt.date(2022, 1, 1), dt.date(2025, 12, 31))
        rows.append((rfc, legal_name, status, pub.isoformat()))

    # ruido realista: RFC del universo 69-B sin relacion con esta empresa
    for _ in range(rng.randint(5, 10)):
        is_moral = rng.random() < 0.85
        rfc = gen_rfc_moral(rng, used_rfcs) if is_moral else gen_rfc_fisica(rng, used_rfcs)
        name = _moral_name(rng) if is_moral else _fisica_name(rng)
        status = rng.choices(EFOS_STATUSES, weights=EFOS_WEIGHTS)[0]
        pub = _random_date(rng, dt.date(2022, 1, 1), dt.date(2025, 12, 31))
        rows.append((rfc, name, status, pub.isoformat()))

    return rows


def _write_db(db_path: Path, tables: dict) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.executemany("INSERT INTO vendors VALUES (?,?,?,?,?,?,?)", tables["vendors"])
        conn.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", tables["invoices"])
        conn.executemany("INSERT INTO ledger VALUES (?,?,?,?,?,?,?,?,?,?)", tables["ledger"])
        conn.executemany("INSERT INTO bank_txns VALUES (?,?,?,?,?,?,?)", tables["bank_txns"])
        conn.executemany("INSERT INTO purchase_orders VALUES (?,?,?,?,?,?,?)", tables["purchase_orders"])
        conn.executemany("INSERT INTO contracts VALUES (?,?,?,?,?)", tables["contracts"])
        conn.executemany("INSERT INTO employees VALUES (?,?,?,?,?)", tables["employees"])
        conn.executemany("INSERT INTO efos_list VALUES (?,?,?,?)", tables["efos_list"])
        conn.commit()
        conn.execute("VACUUM")
        conn.commit()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Genera el data estate con esquemas y decoys")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    db_path, stats = build_estate(args.seed, args.out)
    print(f"OK -> {db_path}")
    print(f"     -> {stats['truth_path']}")
    print(f"   empresa investigada: {stats['company_rfc']}")
    print(f"   proveedores: {stats['n_vendors']}  empleados: {stats['n_employees']}  "
          f"facturas: {stats['n_invoices']}  en efos_list: {stats['n_efos']}")
    print(f"   esquemas sembrados: {stats['n_schemes']}  decoys sembrados: {stats['n_decoys']}")


if __name__ == "__main__":
    main()
