"""
Fase 7 (frontend): arma el bloque `ui` que frontend/FRONTEND.md pide como
extension de submission.json -- nodos, aristas, el par de contraste y el
contexto para el clic de la pregunta sorpresa.

Bloque de nivel superior, aparte de findings/leads_not_pursued -- el
validador oficial solo revisa que las llaves requeridas existan, no
rechaza llaves adicionales, y esa es justo la regla dura del propio
FRONTEND.md: nunca meter campos de UI dentro de un finding o un lead.

Puro codigo, sin modelo: solo reorganiza lo que investigador/retador/
validador ya decidieron, mas una consulta al estate para traducir
RFC/CLABE/emp_id a nombres legibles (igual que report/case_file.py).

No importa nada de generate/ ni lee truth.json.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import tools

_CLABE_RE = re.compile(r"^\d{10,18}$")
MAX_NODES = 15


def _vendor_label(conn, rfc):
    v = tools.vendor(conn, rfc)
    return v["legal_name"] if v else rfc


def _employee_label(conn, emp_id):
    # a diferencia de vendors.rfc (sin prefijo), employees.emp_id ya
    # incluye el "EMP:" tal cual en el estate -- se busca con el id
    # completo, nunca recortado (mismo patron que report/case_file.py).
    row = conn.execute("SELECT name FROM employees WHERE emp_id = ?", (emp_id,)).fetchone()
    return row["name"] if row else emp_id


def _resolve(conn, empresa_rfc, raw):
    """Cualquier identificador que puede aparecer en un money_trail (CLABE
    de 18 digitos, el literal 'EMPRESA', 'RFC:xxx' o 'EMP:xxx') -> (id
    canonico, label, type). id canonico es 'COMPANY' para la empresa, o
    el mismo id con prefijo que ya usan entities/money_trail."""
    if raw == "EMPRESA":
        return "COMPANY", "Empresa investigada", "company"
    if raw.startswith("RFC:"):
        rfc = raw[4:]
        if rfc == empresa_rfc:
            return "COMPANY", "Empresa investigada", "company"
        return raw, _vendor_label(conn, rfc), "vendor"
    if raw.startswith("EMP:"):
        return raw, _employee_label(conn, raw), "employee"
    if _CLABE_RE.match(raw):
        quien = tools.whose_clabe(conn, raw)
        if quien["tipo"] == "vendor":
            return f"RFC:{quien['rfc']}", quien["nombre"], "vendor"
        if quien["tipo"] == "employee":
            # quien['emp_id'] ya trae el prefijo "EMP:" (viene tal cual
            # de la columna) -- no se vuelve a anteponer.
            return quien["emp_id"], quien["nombre"], "employee"
        return "COMPANY", "Empresa investigada", "company"
    return raw, raw, "vendor"


def build(conn, empresa_rfc, findings, leads, finding_meta):
    """finding_meta: lista paralela a `findings`, un dict {"signal":...,
    "tool_calls_made": [...]} por hallazgo -- ese dato ya no vive en el
    finding despues del Paso 4.1 (solo signal/tool_calls_made de
    leads_not_pursued lo conservan), pero FRONTEND.md pide que el
    contraste tambien lo tenga del lado acusado."""
    nodes = {}
    context = {}
    edges = []

    def nodo(id_, label, tipo, estado, step):
        actual = nodes.get(id_)
        if actual is None or step < actual["step"]:
            nodes[id_] = {"id": id_, "label": label, "type": tipo, "state": estado, "step": step}

    for lead in leads:
        id_, label, tipo = _resolve(conn, empresa_rfc, lead["entity"])
        if id_ == "COMPANY":
            continue
        nodo(id_, label, tipo, "dismissed", 2)
        context[id_] = {
            "signal": lead["signal"],
            "tool_calls_made": lead.get("tool_calls_made", []),
            "challenger_argument": lead["reason"],
            "result": f"cerrado por {lead['closed_by']}",
        }

    ids_principales = []  # uno por finding, en orden -- para el highlight

    for finding, meta in zip(findings, finding_meta):
        entidades = finding.get("entities") or []
        id_principal = None  # primera entity que NO sea la propia empresa
        # (revenue_inflation acusa a la empresa misma como entities[0];
        # ahi el "sospechoso" real para mostrar es el cliente, entities[1])

        for raw in entidades:
            id_, label, tipo = _resolve(conn, empresa_rfc, raw)
            if id_ == "COMPANY":
                continue
            if id_principal is None:
                id_principal = id_
                step = 3  # el sospechoso marcado desde el paso 3
            else:
                step = 6  # cualquier entity adicional (empleado/cliente)
                          # es el destino que el paso 6 revela al final
            nodo(id_, label, tipo, "accused", step)

        trail = finding.get("money_trail") or []
        n = len(trail)
        for i, hop in enumerate(trail):
            step = 6 if (n == 1 or i == n - 1) else (4 if i == 0 else 5)
            from_id, _, _ = _resolve(conn, empresa_rfc, hop["from"])
            to_id, _, _ = _resolve(conn, empresa_rfc, hop["to"])
            edges.append({
                "from": empresa_rfc if from_id == "COMPANY" else from_id,
                "to": empresa_rfc if to_id == "COMPANY" else to_id,
                "amount": hop["amount"],
                "date": hop["date"],
                "exhibit_id": hop["exhibit_id"],
                "step": step,
            })

        ids_principales.append(id_principal)
        if id_principal:
            context[id_principal] = {
                "signal": meta["signal"],
                "tool_calls_made": meta["tool_calls_made"],
                "challenger_argument": finding.get("challenger_argument", ""),
                "result": "ACUSACIÓN",
            }

    # maximo 12-15 nodos visibles (FRONTEND.md): los acusados primero,
    # luego los descartados por orden de step; si sobran, se recortan
    # los descartados, nunca los acusados.
    ordenados = sorted(
        nodes.values(),
        key=lambda n: (0 if n["state"] == "accused" else 1, n["step"], n["id"]),
    )[:MAX_NODES]
    ids_visibles = {n["id"] for n in ordenados}
    edges = [
        e for e in edges
        if e["from"] in ids_visibles or e["from"] == empresa_rfc
        if e["to"] in ids_visibles or e["to"] == empresa_rfc
    ]

    primer_acusado_visible = next((i for i in ids_principales if i in ids_visibles), None)
    primer_lead_visible = next(
        (l for l in leads if _resolve(conn, empresa_rfc, l["entity"])[0] in ids_visibles), None
    )
    highlight = {
        "accused": primer_acusado_visible,
        "dismissed": primer_lead_visible["entity"] if primer_lead_visible else None,
    }

    return {
        "company": {"rfc": empresa_rfc, "name": "Empresa investigada"},
        "nodes": [
            {"id": n["id"], "label": n["label"], "type": n["type"], "state": n["state"], "step": n["step"]}
            for n in ordenados
        ],
        "edges": edges,
        "highlight": highlight,
        "context": context,
    }
