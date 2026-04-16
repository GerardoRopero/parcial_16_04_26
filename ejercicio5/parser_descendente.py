"""
Parser Descendente Recursivo con Algoritmo de Emparejamiento
=============================================================
Gramática soportada:

    programa     → sentencia*
    sentencia    → asignacion | condicional
    asignacion   → ID '=' expresion ';'
    condicional  → 'if' '(' expresion ')' '{' sentencia* '}'
                   ( 'else' '{' sentencia* '}' )?
    expresion    → termino ( ('+' | '-') termino )*
    termino      → factor ( ('*' | '/') factor )*
    factor       → NUM | ID | '(' expresion ')'
                 | comparacion
    comparacion  → expresion_simple (('==' | '!=' | '<' | '>' | '<=' | '>=') expresion_simple)?
    expresion_simple → termino ( ('+' | '-') termino )*
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# 1. TOKENS
# ─────────────────────────────────────────────

@dataclass
class Token:
    tipo: str
    valor: str
    linea: int

    def __repr__(self):
        return f"Token({self.tipo}, {self.valor!r}, línea={self.linea})"


PATRONES = [
    ("NUM",    r'\d+(\.\d+)?'),
    ("ID",     r'[a-zA-Z_]\w*'),
    ("OP_CMP", r'==|!=|<=|>=|<|>'),
    ("OP_AS",  r'='),
    ("OP_ADD", r'[+\-]'),
    ("OP_MUL", r'[*/]'),
    ("LPAR",   r'\('),
    ("RPAR",   r'\)'),
    ("LBRACE", r'\{'),
    ("RBRACE", r'\}'),
    ("SEMI",   r';'),
    ("WS",     r'[ \t\n\r]+'),
]

PALABRAS_RESERVADAS = {"if", "else"}


def tokenizar(codigo: str) -> list[Token]:
    """
    Algoritmo de emparejamiento:
    Recorre el código fuente e intenta emparejar cada patrón
    en el orden definido. El primer patrón que coincide en la
    posición actual determina el tipo del token (maximal munch).
    """
    tokens = []
    pos = 0
    linea = 1
    regex_compilado = [(tipo, re.compile(patron)) for tipo, patron in PATRONES]

    while pos < len(codigo):
        emparejado = False
        for tipo, regex in regex_compilado:
            m = regex.match(codigo, pos)          # ← punto clave: match desde 'pos'
            if m:
                lexema = m.group(0)
                if tipo == "WS":
                    linea += lexema.count('\n')   # contar saltos de línea
                elif tipo == "ID" and lexema in PALABRAS_RESERVADAS:
                    tokens.append(Token(lexema.upper(), lexema, linea))
                else:
                    tokens.append(Token(tipo, lexema, linea))
                pos = m.end()
                emparejado = True
                break
        if not emparejado:
            raise SyntaxError(f"Carácter inesperado {codigo[pos]!r} en línea {linea}")

    tokens.append(Token("EOF", "", linea))
    return tokens


# ─────────────────────────────────────────────
# 2. NODOS DEL AST
# ─────────────────────────────────────────────

@dataclass
class NodoNum:
    valor: float

@dataclass
class NodoID:
    nombre: str

@dataclass
class NodoBinOp:
    op: str
    izq: object
    der: object

@dataclass
class NodoAsignacion:
    nombre: str
    expr: object

@dataclass
class NodoCondicional:
    condicion: object
    entonces: list
    sino: list = field(default_factory=list)

@dataclass
class NodoPrograma:
    sentencias: list


# ─────────────────────────────────────────────
# 3. PARSER DESCENDENTE RECURSIVO
# ─────────────────────────────────────────────

class Parser:
    """
    Implementa un parser LL(1) descendente recursivo.
    Cada función no-terminal de la gramática tiene su método.
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── Utilidades ──────────────────────────

    @property
    def actual(self) -> Token:
        return self.tokens[self.pos]

    def consumir(self, tipo_esperado: str) -> Token:
        """Algoritmo de emparejamiento de token individual."""
        tok = self.actual
        if tok.tipo != tipo_esperado:
            raise SyntaxError(
                f"Línea {tok.linea}: se esperaba '{tipo_esperado}', "
                f"se encontró '{tok.tipo}' ({tok.valor!r})"
            )
        self.pos += 1
        return tok

    def ver(self, tipo: str) -> bool:
        """Previsión (lookahead) de 1 token sin consumir."""
        return self.actual.tipo == tipo

    # ── Reglas gramaticales ─────────────────

    def programa(self) -> NodoPrograma:
        sentencias = []
        while not self.ver("EOF"):
            sentencias.append(self.sentencia())
        return NodoPrograma(sentencias)

    def sentencia(self):
        if self.ver("IF"):
            return self.condicional()
        elif self.ver("ID"):
            return self.asignacion()
        else:
            raise SyntaxError(
                f"Línea {self.actual.linea}: sentencia inesperada '{self.actual.valor}'"
            )

    def asignacion(self) -> NodoAsignacion:
        tok_id = self.consumir("ID")
        self.consumir("OP_AS")
        expr = self.expresion()
        self.consumir("SEMI")
        return NodoAsignacion(tok_id.valor, expr)

    def condicional(self) -> NodoCondicional:
        self.consumir("IF")
        self.consumir("LPAR")
        cond = self.expresion()
        self.consumir("RPAR")
        self.consumir("LBRACE")
        entonces = []
        while not self.ver("RBRACE"):
            entonces.append(self.sentencia())
        self.consumir("RBRACE")
        sino = []
        if self.ver("ELSE"):
            self.consumir("ELSE")
            self.consumir("LBRACE")
            while not self.ver("RBRACE"):
                sino.append(self.sentencia())
            self.consumir("RBRACE")
        return NodoCondicional(cond, entonces, sino)

    def expresion(self):
        """expresion → termino ( ('+' | '-') termino )*"""
        nodo = self.termino()
        while self.ver("OP_ADD"):
            op = self.consumir("OP_ADD").valor
            der = self.termino()
            nodo = NodoBinOp(op, nodo, der)
        # Verificar comparación al nivel de expresión
        if self.ver("OP_CMP"):
            op = self.consumir("OP_CMP").valor
            der = self.termino()
            while self.ver("OP_ADD"):
                op2 = self.consumir("OP_ADD").valor
                der2 = self.termino()
                der = NodoBinOp(op2, der, der2)
            nodo = NodoBinOp(op, nodo, der)
        return nodo

    def termino(self):
        """termino → factor ( ('*' | '/') factor )*"""
        nodo = self.factor()
        while self.ver("OP_MUL"):
            op = self.consumir("OP_MUL").valor
            der = self.factor()
            nodo = NodoBinOp(op, nodo, der)
        return nodo

    def factor(self):
        """factor → NUM | ID | '(' expresion ')'"""
        tok = self.actual
        if tok.tipo == "NUM":
            self.consumir("NUM")
            return NodoNum(float(tok.valor))
        elif tok.tipo == "ID":
            self.consumir("ID")
            return NodoID(tok.valor)
        elif tok.tipo == "LPAR":
            self.consumir("LPAR")
            nodo = self.expresion()
            self.consumir("RPAR")
            return nodo
        else:
            raise SyntaxError(
                f"Línea {tok.linea}: factor inesperado '{tok.valor}'"
            )


# ─────────────────────────────────────────────
# 4. INTÉRPRETE / EVALUADOR
# ─────────────────────────────────────────────

class Interprete:
    def __init__(self):
        self.env: dict[str, float] = {}

    def evaluar(self, nodo) -> Optional[float]:
        match nodo:
            case NodoPrograma(sentencias=ss):
                for s in ss:
                    self.evaluar(s)

            case NodoAsignacion(nombre=n, expr=e):
                val = self.evaluar(e)
                self.env[n] = val
                print(f"  {n} = {val}")

            case NodoCondicional(condicion=c, entonces=t, sino=f):
                if self.evaluar(c):
                    for s in t:
                        self.evaluar(s)
                else:
                    for s in f:
                        self.evaluar(s)

            case NodoBinOp(op=op, izq=i, der=d):
                vi, vd = self.evaluar(i), self.evaluar(d)
                match op:
                    case '+':  return vi + vd
                    case '-':  return vi - vd
                    case '*':  return vi * vd
                    case '/':  return vi / vd
                    case '==': return float(vi == vd)
                    case '!=': return float(vi != vd)
                    case '<':  return float(vi < vd)
                    case '>':  return float(vi > vd)
                    case '<=': return float(vi <= vd)
                    case '>=': return float(vi >= vd)

            case NodoNum(valor=v):
                return v

            case NodoID(nombre=n):
                if n not in self.env:
                    raise NameError(f"Variable no definida: '{n}'")
                return self.env[n]

        return None


# ─────────────────────────────────────────────
# 5. FUNCIÓN PRINCIPAL + CASOS DE PRUEBA
# ─────────────────────────────────────────────

def ejecutar(codigo: str, titulo: str = ""):
    separador = "─" * 55
    print(f"\n{separador}")
    if titulo:
        print(f"  {titulo}")
        print(separador)
    print("Código fuente:")
    print(codigo)
    print(separador)
    try:
        tokens = tokenizar(codigo)
        print("Tokens:")
        for t in tokens:
            if t.tipo != "EOF":
                print(f"  {t}")
        print(separador)
        ast = Parser(tokens).programa()
        print("AST:")
        print(f"  {ast}")
        print(separador)
        interp = Interprete()
        print("Ejecución:")
        interp.evaluar(ast)
        print("Estado final de variables:")
        for k, v in interp.env.items():
            print(f"  {k} = {v}")
    except (SyntaxError, NameError) as e:
        print(f"Error: {e}")
    print(separador)


# ── Casos de prueba ───────────────────────────

if __name__ == "__main__":

    # Prueba 1: asignaciones simples
    ejecutar("""
x = 10;
y = 3 * 4 + 2;
z = x + y;
""", "Prueba 1 – Asignaciones simples")

    # Prueba 2: condicional if/else
    ejecutar("""
a = 8;
b = 5;
if (a > b) {
    mayor = a;
} else {
    mayor = b;
}
""", "Prueba 2 – Condicional if/else")

    # Prueba 3: condicionales anidados
    ejecutar("""
x = 10;
if (x >= 10) {
    clase = 1;
    if (x == 10) {
        exacto = 1;
    } else {
        exacto = 0;
    }
} else {
    clase = 0;
    exacto = 0;
}
""", "Prueba 3 – Condicionales anidados")

    # Prueba 4: expresiones complejas
    ejecutar("""
base = 5;
altura = 12;
hipotenusa = base * base + altura * altura;
""", "Prueba 4 – Expresiones complejas")

    # Prueba 5: error sintáctico esperado
    ejecutar("""
x = ;
""", "Prueba 5 – Error sintáctico (esperado)")
