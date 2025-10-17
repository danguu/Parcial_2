"""Command line interface for the parsing toolkit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

from .lexer.tokenizer import LexicalError, tokenize_arith, tokenize_crud
from .parsing.cyk import benchmark_vs_ll1, cyk_parse, to_cnf
from .parsing.grammars import arithmetic_ll1, crud_grammar
from .parsing.ll1_table import LL1ParseError, LL1Parser
from .parsing.shift_reduce import SLRParser


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mini lenguaje CRUD y parsers aritméticos")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser("parse", help="Parsea una cadena con la gramática seleccionada")
    parse_parser.add_argument("--grammar", choices=["crud", "arith"], required=True)
    parse_parser.add_argument("--algo", choices=["asc", "ll1", "cyk"], required=True)
    parse_parser.add_argument("--input", required=True, help="Cadena a analizar")

    bench_parser = subparsers.add_parser("bench", help="Ejecuta el benchmark LL(1) vs CYK")
    bench_parser.add_argument("--lengths", nargs="*", type=int, default=[5, 10, 20], help="Número de operandos a generar")
    bench_parser.add_argument("--output", type=Path, default=Path("benchmark_results.json"))

    return parser.parse_args(argv)


def _run_parse(args: argparse.Namespace) -> int:
    try:
        if args.grammar == "arith":
            tokens = tokenize_arith(args.input)
            token_types = [token.type for token in tokens]
            if args.algo == "ll1":
                parser = LL1Parser(arithmetic_ll1())
                trace = parser.parse(token_types)
                print("Entrada aceptada por LL(1). Traza:")
                for step in trace:
                    print(f"  Stack={step.stack} Input={step.remaining_input} Action={step.action}")
                return 0
            if args.algo == "asc":
                parser = SLRParser(arithmetic_ll1())
                trace = parser.parse(token_types)
                print("Entrada aceptada por shift-reduce SLR. Traza:")
                for stack, remaining, action in trace:
                    print(f"  States={stack} Input={remaining} Action={action}")
                return 0
            if args.algo == "cyk":
                cnf = to_cnf(arithmetic_ll1())
                accepted, table = cyk_parse(cnf, [t.type for t in tokens if t.type != "EOF"])
                print(f"CYK {'acepta' if accepted else 'rechaza'} la cadena.")
                print("Tabla triangular de conjuntos:")
                for row in table:
                    print("  ", row)
                return 0 if accepted else 1
        else:
            tokens = tokenize_crud(args.input)
            token_types = [token.type for token in tokens]
            if args.algo == "ll1":
                parser = LL1Parser(crud_grammar())
                trace = parser.parse(token_types)
                print("Programa CRUD aceptado. Traza:")
                for step in trace:
                    print(f"  Stack={step.stack} Input={step.remaining_input} Action={step.action}")
                return 0
            if args.algo == "cyk":
                cnf = to_cnf(crud_grammar())
                accepted, _ = cyk_parse(cnf, [t.type for t in tokens if t.type != "EOF"])
                print(f"CYK {'acepta' if accepted else 'rechaza'} el programa.")
                return 0 if accepted else 1
            if args.algo == "asc":
                raise ValueError("El algoritmo ascendente solo está disponible para la gramática aritmética")
    except LexicalError as exc:
        print(f"Error léxico: {exc}", file=sys.stderr)
        return 1
    except LL1ParseError as exc:
        print(f"Error sintáctico LL(1): {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("No se pudo reconocer la cadena.", file=sys.stderr)
    return 1


def _build_expression(term_count: int) -> str:
    tokens: List[str] = []
    for i in range(term_count):
        tokens.append(f"id{i}")
        if i < term_count - 1:
            tokens.append("+")
    return " ".join(tokens)


def _benchmark_inputs(lengths: Sequence[int]) -> List[Tuple[str, str]]:
    inputs: List[Tuple[str, str]] = []
    for length in lengths:
        valid = _build_expression(length)
        invalid = valid + " +"
        inputs.append((f"valid_{length}", valid))
        inputs.append((f"invalid_{length}", invalid))
    return inputs


def _run_bench(args: argparse.Namespace) -> int:
    parser = LL1Parser(arithmetic_ll1())
    inputs = _benchmark_inputs(args.lengths)
    results = benchmark_vs_ll1(inputs, parser, tokenize_arith)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Resultados guardados en {args.output}")
    _print_table(results)
    _maybe_plot(results, args.output.with_suffix(".png"))
    return 0


def _print_table(results: Sequence[dict]) -> None:
    headers = ["Caso", "Tokens", "LL1 (s)", "CYK (s)", "Mem LL1", "Mem CYK", "Acepta LL1", "Acepta CYK"]
    print("\n" + " | ".join(headers))
    print("-" * 80)
    for row in results:
        print(
            f"{row['case']:<12} | {row['tokens']:<6} | {row['ll1_time']:.6f} | {row['cyk_time']:.6f} | "
            f"{row['ll1_peak_mem']} | {row['cyk_peak_mem']} | {row['ll1_success']} | {row['cyk_success']}"
        )


def _maybe_plot(results: Sequence[dict], path: Path) -> None:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        print("Matplotlib no disponible, se omite el gráfico.")
        return
    tokens = [row["tokens"] for row in results if row["case"].startswith("valid_")]
    ll1_times = [row["ll1_time"] for row in results if row["case"].startswith("valid_")]
    cyk_times = [row["cyk_time"] for row in results if row["case"].startswith("valid_")]
    plt.figure(figsize=(6, 4))
    plt.plot(tokens, ll1_times, marker="o", label="LL(1)")
    plt.plot(tokens, cyk_times, marker="o", label="CYK")
    plt.xlabel("Tokens")
    plt.ylabel("Tiempo (s)")
    plt.title("Comparación LL(1) vs CYK (casos válidos)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    print(f"Gráfico guardado en {path}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    if args.command == "parse":
        return _run_parse(args)
    if args.command == "bench":
        return _run_bench(args)
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
