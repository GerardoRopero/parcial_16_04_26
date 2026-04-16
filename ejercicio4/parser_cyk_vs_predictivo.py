"""
  PARSER CYK vs PARSER PREDICTIVO LL(1) — Calculadora de Expresiones
  Comparativa de Tiempo y Memoria

  Gramática de la calculadora:
      E  → E + T | E - T | T
      T  → T * F | T / F | F
      F  → num | ( E )

  Para CYK se convierte a Forma Normal de Chomsky (CNF).
  Para el Predictivo se elimina la recursión izquierda:
      E  → T E'
      E' → + T E' | - T E' | ε
      T  → F T'
      T' → * F T' | / F T' | ε
      F  → num | ( E )

"""

import time
import tracemalloc
import sys
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any


def header(title):
    print(f"\n {title}")

def section(title):
    print(f"\n {title}")


#  TOKENIZADOR

@dataclass
class Token:
    type: str   # 'NUM', '+', '-', '*', '/', '(', ')', 'EOF', 'ERR'
    val: str
    pos: int

def tokenize(expr: str) -> List[Token]:
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isspace():
            i += 1
            continue
        if expr[i].isdigit() or (expr[i] == '.' and i+1 < len(expr) and expr[i+1].isdigit()):
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            tokens.append(Token('NUM', expr[i:j], i))
            i = j
        elif expr[i] in '+-*/()':
            tokens.append(Token(expr[i], expr[i], i))
            i += 1
        else:
            tokens.append(Token('ERR', expr[i], i))
            i += 1
    tokens.append(Token('EOF', '$', len(expr)))
    return tokens


#  PARSER CYK
#
#  Gramática CNF usada:
#    Terminales → No-terminales:
#      NUM  → F
#      '+'  → PLUS
#      '-'  → MINUS
#      '*'  → STAR
#      '/'  → SLASH
#      '('  → LPAR
#      ')'  → RPAR
#
#    Reglas binarias:
#      E_PLUS  → E  PLUS      (acumulador: E seguido de +)
#      E_MINUS → E  MINUS
#      T_STAR  → T  STAR
#      T_SLASH → T  SLASH
#      E       → E_PLUS  T   (suma completa)
#      E       → E_MINUS T   (resta completa)
#      T       → T_STAR  F   (mult completa)
#      T       → T_SLASH F   (div completa)
#      LPAR_E  → LPAR  E     (( seguido de expresión)
#      F       → LPAR_E RPAR (expresión entre paréntesis)
#
#    Propagación unitaria:
#      F  → NUM   ⟹  T → F, E → T
#      T  → ...   ⟹  E → T

# Símbolos no-terminales
ALL_SYMS = ['E','T','F','PLUS','MINUS','STAR','SLASH','LPAR','RPAR','E_PLUS','E_MINUS','T_STAR','T_SLASH','LPAR_E']

def _tok_to_syms(tok: Token) -> List[str]:
    return {
        'NUM': ['F', 'T', 'E'],   # unit chain
        '+':   ['PLUS'],
        '-':   ['MINUS'],
        '*':   ['STAR'],
        '/':   ['SLASH'],
        '(':   ['LPAR'],
        ')':   ['RPAR'],
    }.get(tok.type, [])

def cyk_parse(tokens: List[Token]) -> Tuple[bool, List[List[set]], int]:
    """
    Retorna (aceptado, tabla, operaciones_realizadas).
    La tabla[i][j] contiene el conjunto de no-terminales que derivan tokens[i..j].
    """
    # Excluir EOF
    toks = [t for t in tokens if t.type != 'EOF']
    n = len(toks)
    if n == 0:
        return False, [], 0

    # Inicializar tabla n×n de conjuntos
    table: List[List[set]] = [[set() for _ in range(n)] for _ in range(n)]
    ops = 0

    # Paso 1: llenar diagonal (longitud 1)
    for i in range(n):
        table[i][i].update(_tok_to_syms(toks[i]))
        ops += 1

    # Paso 2: llenar por longitudes crecientes
    for length in range(2, n + 1):          # longitud del substring
        for i in range(n - length + 1):     # inicio
            j = i + length - 1              # fin
            for k in range(i, j):           # punto de corte
                L = table[i][k]
                R = table[k+1][j]
                ops += 1

                # Acumuladores de operadores
                if 'E' in L and 'PLUS'  in R: table[i][j].add('E_PLUS')
                if 'E' in L and 'MINUS' in R: table[i][j].add('E_MINUS')
                if 'T' in L and 'STAR'  in R: table[i][j].add('T_STAR')
                if 'T' in L and 'SLASH' in R: table[i][j].add('T_SLASH')

                # Reglas completas
                if 'E_PLUS'  in L and 'T' in R: table[i][j].update(['E', 'T'])
                if 'E_MINUS' in L and 'T' in R: table[i][j].update(['E', 'T'])
                if 'T_STAR'  in L and 'F' in R: table[i][j].update(['T', 'E'])
                if 'T_SLASH' in L and 'F' in R: table[i][j].update(['T', 'E'])

                # Paréntesis: LPAR_E → LPAR E
                if 'LPAR' in L and 'E' in R: table[i][j].add('LPAR_E')
                # F → LPAR_E RPAR
                if 'LPAR_E' in L and 'RPAR' in R:
                    table[i][j].update(['F', 'T', 'E'])

    accepted = 'E' in table[0][n-1]
    return accepted, table, ops


def cyk_table_str(table: List[List[set]], tokens: List[Token]) -> str:
    """Genera string con la tabla CYK para impresión."""
    toks = [t for t in tokens if t.type != 'EOF']
    n = len(toks)
    if n == 0 or n > 12:
        return "  (tabla omitida: expresión demasiado larga)"

    col_w = 16
    # Encabezado
    header_row = " " * 6
    for j, t in enumerate(toks):
        header_row += f"j={j}({t.val})".ljust(col_w)
    lines = [header_row]

    for i in range(n):
        row = f"i={i}({toks[i].val}) ".ljust(6)
        for j in range(n):
            if j < i:
                row += "·".ljust(col_w)
            else:
                cell_syms = {s for s in table[i][j] if s in ('E','T','F')}
                cell = ','.join(sorted(cell_syms)) if cell_syms else '∅'
                row += cell.ljust(col_w)
        lines.append(row)
    return "\n".join(f"    {l}" for l in lines)


#  PARSER PREDICTIVO LL(1) — Descenso Recursivo

class PredictiveParser:
    """
    Parser LL(1) con descenso recursivo para la gramática:
      E  → T E'
      E' → + T E' | - T E' | ε
      T  → F T'
      T' → * F T' | / F T' | ε
      F  → num | ( E )
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != 'EOF'] + [Token('EOF','$',0)]
        self.pos = 0
        self.ops = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def consume(self, expected_type: str) -> Token:
        tok = self.peek()
        if tok.type != expected_type:
            raise SyntaxError(
                f"Error en posición {tok.pos}: "
                f"se esperaba '{expected_type}', se encontró '{tok.val}'"
            )
        self.pos += 1
        self.ops += 1
        return tok

    def parse(self) -> Tuple[bool, Optional[float], str]:
        try:
            val = self._E()
            if self.peek().type != 'EOF':
                raise SyntaxError(
                    f"Token inesperado '{self.peek().val}' en posición {self.peek().pos}"
                )
            return True, val, ""
        except SyntaxError as e:
            return False, None, str(e)
        except ZeroDivisionError:
            return False, None, "División por cero"

    def _E(self) -> float:
        self.ops += 1
        val = self._T()
        return self._Ep(val)

    def _Ep(self, left: float) -> float:
        self.ops += 1
        tok = self.peek()
        if tok.type == '+':
            self.consume('+')
            r = self._T()
            return self._Ep(left + r)
        elif tok.type == '-':
            self.consume('-')
            r = self._T()
            return self._Ep(left - r)
        return left  # ε

    def _T(self) -> float:
        self.ops += 1
        val = self._F()
        return self._Tp(val)

    def _Tp(self, left: float) -> float:
        self.ops += 1
        tok = self.peek()
        if tok.type == '*':
            self.consume('*')
            r = self._F()
            return self._Tp(left * r)
        elif tok.type == '/':
            self.consume('/')
            r = self._F()
            return self._Tp(left / r)
        return left  # ε

    def _F(self) -> float:
        self.ops += 1
        tok = self.peek()
        if tok.type == 'NUM':
            self.consume('NUM')
            return float(tok.val)
        elif tok.type == '(':
            self.consume('(')
            val = self._E()
            self.consume(')')
            return val
        else:
            raise SyntaxError(
                f"Error en posición {tok.pos}: "
                f"token inesperado '{tok.val}' en F"
            )


#  MEDICIÓN: tiempo + memoria con tracemalloc

@dataclass
class Measurement:
    accepted: bool
    value: Optional[float]
    error: str
    time_ns: int          # nanosegundos
    mem_peak_bytes: int   # bytes pico
    mem_current_bytes: int
    ops: int
    extra: Any = None     # tabla CYK o None

def measure_cyk(expr: str) -> Measurement:
    tokens = tokenize(expr)
    tracemalloc.start()
    t0 = time.perf_counter_ns()
    accepted, table, ops = cyk_parse(tokens)
    t1 = time.perf_counter_ns()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return Measurement(
        accepted=accepted,
        value=None,
        error="" if accepted else "Expresión inválida (rechazada por CYK)",
        time_ns=t1 - t0,
        mem_peak_bytes=peak,
        mem_current_bytes=current,
        ops=ops,
        extra=table
    )

def measure_pred(expr: str) -> Measurement:
    tokens = tokenize(expr)
    tracemalloc.start()
    t0 = time.perf_counter_ns()
    parser = PredictiveParser(tokens)
    accepted, value, error = parser.parse()
    t1 = time.perf_counter_ns()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return Measurement(
        accepted=accepted,
        value=value,
        error=error,
        time_ns=t1 - t0,
        mem_peak_bytes=peak,
        mem_current_bytes=current,
        ops=parser.ops,
        extra=None
    )


#  BENCHMARK: múltiples iteraciones para promedios estables

@dataclass
class BenchResult:
    avg_time_ns: float
    min_time_ns: int
    max_time_ns: int
    avg_mem_bytes: float
    peak_mem_bytes: int

def benchmark(expr: str, parser: str, iterations: int = 500) -> BenchResult:
    times = []
    mems  = []
    tokens = tokenize(expr)

    for _ in range(iterations):
        tracemalloc.start()
        t0 = time.perf_counter_ns()
        if parser == 'cyk':
            cyk_parse(tokens)
        else:
            p = PredictiveParser(tokens)
            p.parse()
        t1 = time.perf_counter_ns()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        times.append(t1 - t0)
        mems.append(peak)

    return BenchResult(
        avg_time_ns=sum(times) / len(times),
        min_time_ns=min(times),
        max_time_ns=max(times),
        avg_mem_bytes=sum(mems) / len(mems),
        peak_mem_bytes=max(mems),
    )


#  FORMATO DE NÚMEROS

def fmt_time(ns: float) -> str:
    if ns < 1_000:
        return f"{ns:.1f} ns"
    elif ns < 1_000_000:
        return f"{ns/1_000:.2f} µs"
    else:
        return f"{ns/1_000_000:.3f} ms"

def fmt_bytes(b: float) -> str:
    if b < 1024:
        return f"{b:.0f} B"
    elif b < 1024**2:
        return f"{b/1024:.2f} KB"
    else:
        return f"{b/1024**2:.3f} MB"



#  IMPRESIÓN DE RESULTADOS

def print_single_result(expr: str, cyk_m: Measurement, pred_m: Measurement, tokens: List[Token]):
    n_toks = len([t for t in tokens if t.type != 'EOF'])
    section(f"Expresion: {repr(expr)}  [{n_toks} tokens]")

    cyk_status  = "ACEPTADO" if cyk_m.accepted  else "RECHAZADO"
    pred_status = "ACEPTADO" if pred_m.accepted else "RECHAZADO"
    pred_val = f"= {pred_m.value}" if pred_m.value is not None else "N/A"

    print(f"  CYK        : {cyk_status}  |  tiempo: {fmt_time(cyk_m.time_ns)}  |  memoria: {fmt_bytes(cyk_m.mem_peak_bytes)}")
    print(f"  Predictivo : {pred_status}  |  tiempo: {fmt_time(pred_m.time_ns)}  |  memoria: {fmt_bytes(pred_m.mem_peak_bytes)}  |  resultado: {pred_val}")
    if pred_m.error and not pred_m.accepted:
        print(f"  Error: {pred_m.error}")

    ratio_t = cyk_m.time_ns / pred_m.time_ns if pred_m.time_ns > 0 else float('inf')
    ratio_m = cyk_m.mem_peak_bytes / pred_m.mem_peak_bytes if pred_m.mem_peak_bytes > 0 else float('inf')
    print(f"  CYK es {ratio_t:.1f}x mas lento y usa {ratio_m:.1f}x mas memoria")


def print_cyk_table(expr: str, cyk_m: Measurement, tokens: List[Token]):
    n_toks = len([t for t in tokens if t.type != 'EOF'])
    if n_toks > 12:
        return
    section("Tabla CYK [i,j]")
    print(cyk_table_str(cyk_m.extra, tokens))
    n = n_toks
    accepted = 'E' in cyk_m.extra[0][n-1] if cyk_m.extra else False
    print(f"  E en tabla[0][{n-1}]: {accepted}")


def print_benchmark_table(results: list):
    header("BENCHMARK (500 iteraciones por expresion)")
    print(f"  {'Expresion':<30} {'CYK t':>10} {'Pred t':>10} {'Ratio t':>8} {'CYK mem':>10} {'Pred mem':>10}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*8} {'-'*10} {'-'*10}")

    total_rt = 0
    total_rm = 0
    for r in results:
        ratio_t = r['cyk_t'] / r['pred_t'] if r['pred_t'] > 0 else 0
        ratio_m = r['cyk_m'] / r['pred_m'] if r['pred_m'] > 0 else 0
        total_rt += ratio_t
        total_rm += ratio_m
        expr_short = r['expr'][:28] + ('..' if len(r['expr']) > 28 else '')
        print(f"  {expr_short:<30} {fmt_time(r['cyk_t']):>10} {fmt_time(r['pred_t']):>10} {ratio_t:>7.1f}x {fmt_bytes(r['cyk_m']):>10} {fmt_bytes(r['pred_m']):>10}")

    n = len(results)
    print(f"\n  Promedio tiempo  CYK/Predictivo: {total_rt/n:.1f}x")
    print(f"  Promedio memoria CYK/Predictivo: {total_rm/n:.1f}x")


def print_theoretical_comparison():
    header("COMPARACION TEORICA")
    rows = [
        ("Complejidad tiempo",  "O(n^3 * |G|)",       "O(n)"),
        ("Complejidad memoria", "O(n^2 * |V|)",       "O(n)"),
        ("Tipo de gramatica",   "Cualquier GLC (CNF)", "Solo LL(1)"),
        ("Recursion izquierda", "Soportada",           "Requiere eliminar"),
        ("Ambiguedad",          "La detecta",          "Falla"),
        ("Evalua resultado",    "No",                  "Si"),
        ("Uso practico",        "NLP, linguistica",    "Compiladores reales"),
    ]
    print(f"  {'Caracteristica':<25} {'CYK':<28} {'Predictivo LL(1)'}")
    print(f"  {'-'*25} {'-'*28} {'-'*20}")
    for feat, cyk_v, pred_v in rows:
        print(f"  {feat:<25} {cyk_v:<28} {pred_v}")


def print_complexity_growth():
    section("Crecimiento teorico de operaciones")
    print(f"  {'n':<6} {'CYK O(n^3)':<14} {'Predictivo O(n)':<14} {'Ratio'}")
    print(f"  {'-'*6} {'-'*14} {'-'*14} {'-'*8}")
    for n in [2, 4, 6, 8, 10, 15, 20, 30]:
        print(f"  {n:<6} {n**3:<14} {n:<14} {n**3//n}x")


#  PROGRAMA PRINCIPAL

TEST_EXPRS = [
    ("3 + 5",                  True),
    ("( 3 + 5 ) * 2",          True),
    ("10 / 2 - 1",             True),
    ("( 1 + 2 ) * ( 3 + 4 )",  True),
    ("1 + 2 * 3 - 4 / 2",      True),
    ("( ( 3 ) )",               True),
    ("5 + 6 * 7 - 8 / 2 + 1",  True),
    ("100 / 4 * ( 2 + 3 )",    True),
    ("5 + + 3",                False),
    ("( 3 + 5",                False),
    ("* 2",                    False),
    ("3 + 5 )",                False),
]


def main():
    print(f"\nCYK vs Parser Predictivo LL(1) - Calculadora de expresiones")
    print(f"Python {sys.version.split()[0]} | tracemalloc + perf_counter_ns")

    header("ANALISIS INDIVIDUAL")
    for expr, _ in TEST_EXPRS:
        tokens = tokenize(expr)
        cyk_m  = measure_cyk(expr)
        pred_m = measure_pred(expr)
        print_single_result(expr, cyk_m, pred_m, tokens)
        if expr == "3 + 5":
            print_cyk_table(expr, cyk_m, tokens)

    header("BENCHMARK (500 iteraciones por expresion)")
    print("Ejecutando...")
    bench_rows = []
    for expr, _ in TEST_EXPRS:
        b_cyk  = benchmark(expr, 'cyk',  500)
        b_pred = benchmark(expr, 'pred', 500)
        print(f"  {repr(expr)}")
        bench_rows.append({
            'expr':   expr,
            'cyk_t':  b_cyk.avg_time_ns,
            'pred_t': b_pred.avg_time_ns,
            'cyk_m':  b_cyk.avg_mem_bytes,
            'pred_m': b_pred.avg_mem_bytes,
        })
    print_benchmark_table(bench_rows)

    print_complexity_growth()
    print_theoretical_comparison()

    header("CONCLUSION")
    print("  CYK: O(n^3), usa tabla n×n, acepta cualquier GLC en CNF.")
    print("  Predictivo LL(1): O(n), lineal, evalua el resultado.")
    print("  Para una calculadora el predictivo es la eleccion correcta.")
    print("  CYK es util cuando la gramatica no puede reducirse a LL(1).")
    print()


if __name__ == "__main__":
    main()
