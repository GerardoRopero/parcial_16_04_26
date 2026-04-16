#!/usr/bin/env python3
"""
Simulador de árbol sintáctico para el lenguaje NoQL.
Muestra cómo ANTLR construiría el árbol de parse para cadenas de ejemplo.
Útil para verificar la gramática antes de compilar con ANTLR.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

# Representación del árbol

@dataclass
class Node:
    rule: str
    children: List["Node"] = field(default_factory=list)
    token: Optional[str] = None

    def add(self, child: "Node") -> "Node":
        self.children.append(child)
        return child

    def pretty(self, indent: int = 0, last: bool = True) -> str:
        connector = "└── " if last else "├── "
        prefix    = "    " if last else "│   "
        if self.token is not None:
            label = f"\033[36m{self.rule}\033[0m: \033[33m{self.token!r}\033[0m"
        else:
            label = f"\033[32m{self.rule}\033[0m"
        lines = [("    " * indent) + (connector if indent > 0 else "") + label]
        for i, child in enumerate(self.children):
            is_last = (i == len(self.children) - 1)
            lines.append(child.pretty(indent + 1, is_last))
        return "\n".join(lines)


# Árboles de ejemplo 
def build_tree_insert_one() -> Node:
    """
    INSERT INTO usuarios { "nombre": "Ana", "edad": 30, "activo": true }
    """
    prog = Node("program")
    stmt = prog.add(Node("statement"))
    ins  = stmt.add(Node("insertStmt (insertOne)"))
    ins.add(Node("INSERT", token="INSERT"))
    ins.add(Node("INTO",   token="INTO"))
    ins.add(Node("collection", token="usuarios"))

    doc = ins.add(Node("document"))
    p1  = doc.add(Node("pair"))
    p1.add(Node("STRING", token='"nombre"'))
    p1.add(Node("COLON",  token=":"))
    p1.add(Node("value → stringVal", token='"Ana"'))
    p2  = doc.add(Node("pair"))
    p2.add(Node("STRING",  token='"edad"'))
    p2.add(Node("COLON",   token=":"))
    p2.add(Node("value → numberVal", token="30"))
    p3  = doc.add(Node("pair"))
    p3.add(Node("STRING",  token='"activo"'))
    p3.add(Node("COLON",   token=":"))
    p3.add(Node("value → trueVal", token="true"))
    return prog


def build_tree_find_complex() -> Node:
    """
    FIND SELECT nombre, email FROM usuarios
         WHERE edad >= 18 AND activo == true
         SORT BY edad DESC LIMIT 10
    """
    prog = Node("program")
    stmt = prog.add(Node("statement"))
    find = stmt.add(Node("findStmt"))
    find.add(Node("FIND", token="FIND"))

    sel = find.add(Node("selectClause"))
    sel.add(Node("SELECT", token="SELECT"))
    fl = sel.add(Node("fieldList"))
    fl.add(Node("field", token="nombre"))
    fl.add(Node("field", token="email"))

    find.add(Node("FROM", token="FROM"))
    find.add(Node("collection", token="usuarios"))

    where = find.add(Node("whereClause"))
    where.add(Node("WHERE", token="WHERE"))
    and_c = where.add(Node("condition → andCondition"))

    left = and_c.add(Node("condition → exprCondition"))
    ge   = left.add(Node("expression → gteExpr"))
    ge.add(Node("field", token="edad"))
    ge.add(Node("GTE",   token=">="))
    ge.add(Node("value → numberVal", token="18"))

    and_c.add(Node("AND", token="AND"))

    right = and_c.add(Node("condition → exprCondition"))
    eq    = right.add(Node("expression → eqExpr"))
    eq.add(Node("field",  token="activo"))
    eq.add(Node("EQ",     token="=="))
    eq.add(Node("value → trueVal", token="true"))

    sort = find.add(Node("sortClause"))
    sort.add(Node("SORT", token="SORT"))
    sort.add(Node("BY",   token="BY"))
    sf = sort.add(Node("sortField"))
    sf.add(Node("field", token="edad"))
    sf.add(Node("DESC",  token="DESC"))

    lim = find.add(Node("limitClause"))
    lim.add(Node("LIMIT",  token="LIMIT"))
    lim.add(Node("NUMBER", token="10"))

    return prog


def build_tree_update() -> Node:
    """
    UPDATE productos SET stock -= 5, precio += 50
           WHERE categoria == "electronica"
    """
    prog = Node("program")
    stmt = prog.add(Node("statement"))
    upd  = stmt.add(Node("updateStmt"))
    upd.add(Node("UPDATE",     token="UPDATE"))
    upd.add(Node("collection", token="productos"))
    upd.add(Node("SET",        token="SET"))

    body = upd.add(Node("updateBody → updateByAssignments"))
    al   = body.add(Node("assignmentList"))

    a1 = al.add(Node("assignment → decField"))
    a1.add(Node("field",   token="stock"))
    a1.add(Node("DEC",     token="-="))
    a1.add(Node("value → numberVal", token="5"))

    a2 = al.add(Node("assignment → incField"))
    a2.add(Node("field",   token="precio"))
    a2.add(Node("INC",     token="+="))
    a2.add(Node("value → numberVal", token="50"))

    where = upd.add(Node("whereClause"))
    where.add(Node("WHERE", token="WHERE"))
    expr = where.add(Node("condition → exprCondition"))
    eq   = expr.add(Node("expression → eqExpr"))
    eq.add(Node("field",  token="categoria"))
    eq.add(Node("EQ",     token="=="))
    eq.add(Node("value → stringVal", token='"electronica"'))
    return prog


def build_tree_delete() -> Node:
    """
    DELETE FROM usuarios WHERE activo == false AND edad < 18
    """
    prog = Node("program")
    stmt = prog.add(Node("statement"))
    dl   = stmt.add(Node("deleteStmt"))
    dl.add(Node("DELETE",     token="DELETE"))
    dl.add(Node("FROM",       token="FROM"))
    dl.add(Node("collection", token="usuarios"))

    where = dl.add(Node("whereClause"))
    where.add(Node("WHERE", token="WHERE"))
    and_c = where.add(Node("condition → andCondition"))

    left = and_c.add(Node("condition → exprCondition"))
    eq   = left.add(Node("expression → eqExpr"))
    eq.add(Node("field",  token="activo"))
    eq.add(Node("EQ",     token="=="))
    eq.add(Node("value → falseVal", token="false"))

    and_c.add(Node("AND", token="AND"))

    right = and_c.add(Node("condition → exprCondition"))
    lt    = right.add(Node("expression → ltExpr"))
    lt.add(Node("field",  token="edad"))
    lt.add(Node("LT",     token="<"))
    lt.add(Node("value → numberVal", token="18"))

    return prog


# Validador de cadenas 

TOKENS = {
    "keywords":  r"\b(INSERT|INTO|FIND|FROM|SELECT|WHERE|UPDATE|SET|DELETE|SORT|BY|LIMIT|SKIP|ORDER|ASC|DESC|AND|OR|NOT|IN|LIKE|CONTAINS|EXISTS|BETWEEN|true|false|null)\b",
    "operator":  r"(==|!=|<=|>=|<|>|\+=|-=|=)",
    "string":    r'"[^"]*"',
    "number":    r"-?\d+(\.\d+)?",
    "id":        r"[a-zA-Z_$][a-zA-Z_$0-9]*(\.[a-zA-Z_$][a-zA-Z_$0-9]*)*",
    "punct":     r"[{}\[\](),;:]",
    "star":      r"\*",
}

TEST_CASES = [
    ("✓ INSERT básico",
     'INSERT INTO usuarios { "nombre": "Ana", "edad": 30 }'),
    ("✓ INSERT múltiple",
     'INSERT INTO cats [{"a":1},{"a":2}]'),
    ("✓ FIND sin condición",
     'FIND FROM productos'),
    ("✓ FIND con SELECT y WHERE",
     'FIND SELECT nombre, email FROM usuarios WHERE activo == true'),
    ("✓ FIND con BETWEEN",
     'FIND FROM pedidos WHERE total BETWEEN 100 AND 500'),
    ("✓ FIND con IN",
     'FIND FROM usuarios WHERE rol IN ("admin", "editor")'),
    ("✓ FIND con EXISTS",
     'FIND FROM docs WHERE campo EXISTS'),
    ("✓ FIND complejo",
     'FIND SELECT nombre FROM clientes WHERE activo == true AND edad > 18 SORT BY nombre ASC LIMIT 20'),
    ("✓ UPDATE con asignaciones",
     'UPDATE productos SET precio = 99.9, stock -= 1 WHERE sku == "X1"'),
    ("✓ UPDATE con documento",
     'UPDATE config SET { "tema": "dark", "ver": 2 } WHERE uid == "u1"'),
    ("✓ DELETE con condición",
     'DELETE FROM logs WHERE nivel == "debug"'),
    ("✓ DELETE sin WHERE",
     'DELETE FROM cache'),
    ("✓ FIND con NOT",
     'FIND FROM empleados WHERE NOT departamento == "RRHH"'),
    ("✓ FIND con OR agrupado",
     'FIND FROM pedidos WHERE (estado == "pendiente" OR estado == "activo") AND prioridad == "alta"'),
    ("✓ FIND con dot notation",
     'FIND FROM clientes WHERE direccion.ciudad == "Bogota"'),
]

def tokenize(src: str) -> List[str]:
    combined = "|".join(f"(?P<{n}>{p})" for n, p in TOKENS.items())
    return [m.group() for m in re.finditer(combined, src, re.IGNORECASE)]

def validate(label: str, src: str) -> bool:
    tokens = tokenize(src)
    valid  = len(tokens) > 0
    status = "\033[32mOK\033[0m" if valid else "\033[31mFAIL\033[0m"
    print(f"  [{status}] {label}")
    if valid:
        print(f"        Tokens ({len(tokens)}): {' '.join(tokens[:12])}{'...' if len(tokens) > 12 else ''}")
    return valid


# Entrypoint

if __name__ == "__main__":
    print("\n" + "═" * 70)
    print("  ÁRBOLES SINTÁCTICOS — NoQL")
    print("═" * 70)

    examples = [
        ("INSERT INTO usuarios { \"nombre\": \"Ana\", \"edad\": 30, \"activo\": true }",
         build_tree_insert_one()),
        ("FIND SELECT nombre, email FROM usuarios WHERE edad >= 18 AND activo == true SORT BY edad DESC LIMIT 10",
         build_tree_find_complex()),
        ("UPDATE productos SET stock -= 5, precio += 50 WHERE categoria == \"electronica\"",
         build_tree_update()),
        ("DELETE FROM usuarios WHERE activo == false AND edad < 18",
         build_tree_delete()),
    ]

    for src, tree in examples:
        print(f"\n\033[1mSentencia:\033[0m {src}")
        print()
        print(tree.pretty())
        print()

    print("\n" + "═" * 70)
    print("  VALIDACIÓN DE CADENAS DE PRUEBA")
    print("═" * 70 + "\n")

    ok = sum(validate(lbl, src) for lbl, src in TEST_CASES)
    print(f"\n  Resultado: {ok}/{len(TEST_CASES)} cadenas válidas\n")
