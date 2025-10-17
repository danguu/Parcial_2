# Parcial 2 — Lenguajes y Compiladores

Este proyecto reúne la solución integral a los cinco puntos solicitados:

1. **Gramática CRUD** en EBNF con ejemplos y pruebas de aceptación. 【Fuente: `app/grammar/crud.ebnf`】
2. **Implementación en Bison/Flex** de la gramática CRUD con driver de línea de comandos. 【Fuente: `bison_or_antlr/`】
3. **Gramática aritmética**, transformación LL(1), FIRST/FOLLOW/PREDICT, parser ascendente SLR y pruebas. 【Fuentes: `app/grammar/arith_*.ebnf`, `app/parsing/*.py`】
4. **Parser CYK** en Python más conversión a FNC y benchmark comparativo frente al parser LL(1). 【Fuente: `app/parsing/cyk.py`, `app/cli.py`】
5. **Estrategia de emparejamiento para descenso recursivo** con memoización y trazas. 【Fuente: `app/parsing/recursive_descent.py`】

## Estructura del repositorio

```
app/
  cli.py                  # CLI principal (parse/bench)
  repl.py                 # REPL para expresiones aritméticas
  grammar/
    crud.ebnf             # Gramática CRUD completa
    arith_original.ebnf   # Gramática aritmética original
    arith_ll1.ebnf        # Versión LL(1)
  lexer/
    tokenizer.py          # Analizadores léxicos CRUD y aritmético
  parsing/
    grammars.py           # Especificaciones reutilizables de gramática
    first_follow.py       # FIRST/FOLLOW/PREDICT
    ll1_table.py          # Tabla LL(1) y parser predictivo
    shift_reduce.py       # Parser ascendente SLR(1)
    cyk.py                # Conversión a FNC y algoritmo CYK + benchmark
    recursive_descent.py  # Emparejamiento con memoización
bison_or_antlr/
  crud.y, crud.l, main.c, Makefile, examples/  # Implementación Bison/Flex
benchmark_results.json    # Última ejecución del benchmark CLI
tests/                    # Suite de pruebas pytest
```

## Gramática CRUD

* Archivo principal: [`app/grammar/crud.ebnf`](app/grammar/crud.ebnf).
* Se especifican tokens, precedencias (NOT > comparaciones > AND > OR) y comentarios tipo `#`.
* Ejemplos válidos e inválidos + lista mínima de pruebas de aceptación.
* La gramática factoriza identificadores calificados (`a.b.c`) y reusa la gramática aritmética para expresiones en `WHERE`.

### Parser LL(1) en Python

* `LL1Parser` se construye automáticamente a partir de los conjuntos PREDICT.
* El analizador léxico (`tokenize_crud`) gestiona cadenas, números, booleanos y comentarios.
* Se incluyen trazas detalladas (pila + entrada restante) al ejecutar `python -m app.cli parse --grammar crud --algo ll1`.

### Implementación Bison/Flex

* Fuentes: `bison_or_antlr/crud.y`, `bison_or_antlr/crud.l`, `bison_or_antlr/main.c`.
* Construcción multiplataforma (Linux/macOS/WSL):
  ```bash
  cd bison_or_antlr
  make            # genera crud_parser
  ./crud_parser examples/valid.crud
  ./crud_parser examples/invalid.crud
  ```
* El driver procesa uno o varios archivos `.crud`, reporta errores con línea/columna y produce mensajes de éxito.
* `examples/` contiene casos correctos y con errores sintácticos/léxicos.

## Gramática aritmética y análisis LL(1)

* Transformación LL(1) documentada en `app/grammar/arith_ll1.ebnf`.
* El módulo `first_follow.py` calcula FIRST, FOLLOW y PREDICT. Para `E` se obtiene:
  * `FIRST(E) = { LPAREN, ID }`
  * `FOLLOW(E) = { $, RPAREN }`
  * `PREDICT(E' → ε) = { $, RPAREN }`
* `ll1_table.py` genera la tabla LL(1) y ofrece un parser predictivo con trazas.

## Parser ascendente (SLR básico)

* Implementación en `shift_reduce.py`.
* Construye la colección canónica LR(0), tablas ACTION/GOTO y ejecuta shift/reduce con traza `(estados, entrada, acción)`.
* Evita conflictos al crear un símbolo inicial único (`E_start`).

## Conversión a FNC y algoritmo CYK

* `cyk.py` realiza:
  1. Eliminación de producciones ε y unitarias.
  2. Introducción de no terminales auxiliares para terminales en producciones largas.
  3. Descomposición a reglas binarias.
* `cyk_parse` devuelve aceptación + tabla triangular de conjuntos.
* `benchmark_vs_ll1` compara LL(1) vs CYK midiendo tiempo y memoria (vía `tracemalloc`).

### Benchmark

Se ejecuta con `python -m app.cli bench --lengths 5 10` y guarda resultados en `benchmark_results.json`. Resumen (ambos analizadores sobre expresiones válidas e inválidas):

| Caso       | Tokens | Tiempo LL(1) (s) | Tiempo CYK (s) | Pico memoria LL(1) (B) | Pico memoria CYK (B) | Acepta LL(1) | Acepta CYK |
|------------|--------|------------------|----------------|------------------------|----------------------|--------------|------------|
| valid_5    | 10     | 2.83e-4          | 4.79e-3        | 12 277                 | 21 160               | Sí           | Sí         |
| invalid_5  | 11     | 2.61e-4          | 5.87e-3        | 10 909                 | 25 392               | No           | No         |
| valid_10   | 20     | 4.73e-4          | 4.16e-2        | 20 743                 | 84 264               | Sí           | Sí         |
| invalid_10 | 21     | 4.54e-4          | 4.85e-2        | 22 183                 | 92 880               | No           | No         |

Conclusiones:
* El parser LL(1) es dos órdenes de magnitud más rápido y consume mucho menos memoria.
* CYK ofrece robustez (gramáticas arbitrarias) a costa de complejidad cúbica.
* El gráfico se genera automáticamente si `matplotlib` está disponible; en caso contrario se omite con un aviso.

## Descenso recursivo con memoización

* `RecursiveDescentMatcher` aplica memoización (`functools.lru_cache`) para evitar re-evaluaciones.
* Devuelve tanto el resultado de emparejamiento como una lista de trazas con `(no terminal, producción, índice inicial/final, éxito)`.
* Útil para visualizar backtracking y rutas exploradas.

## CLI y REPL

* **Parseo**: `python -m app.cli parse --grammar crud|arith --algo ll1|asc|cyk --input "..."`
  * `asc` (SLR) sólo para `arith`.
  * Traza completa en stdout y códigos de salida adecuados.
* **Benchmark**: `python -m app.cli bench --lengths 5 10 20`
  * Genera `benchmark_results.json` y (opcionalmente) `benchmark_results.png` si hay matplotlib.
* **REPL**: `python -m app.repl` para probar expresiones aritméticas interactiva y rápidamente.

## Pruebas automatizadas

* Ejecutar `pytest` desde la raíz. Cobertura básica: tokenización, FIRST/FOLLOW, parsers LL(1)/SLR/CYK, CRUD, y descenso recursivo.
* `tests/` incluye un `conftest.py` que añade el proyecto al `sys.path`.

## Dependencias

* Python 3.11+
* `pytest` para la suite de pruebas.
* `matplotlib` opcional para el gráfico de benchmark.
* Para el punto Bison/Flex: `bison`, `flex` y un compilador C (GCC/Clang).

## Notas finales

* Los archivos `.ebnf` documentan explícitamente tokens, precedencias y casos de prueba.
* `benchmark_results.json` conserva la última ejecución del benchmark para reproducibilidad.
* Toda la solución se implementa en Python 3.x salvo el parser Bison/Flex requerido en el Punto 2.
