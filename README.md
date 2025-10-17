# Parcial 2

Este repositorio contiene implementaciones y experimentos solicitados en el enunciado del parcial.

## 1. Gramática CRUD

La gramática propuesta para el lenguaje de operaciones CRUD se encuentra en [`docs/CRUD_grammar.md`](docs/CRUD_grammar.md).

## 2. Implementación con Bison

En el directorio [`bison/`](bison) se incluye el archivo [`crud.y`](bison/crud.y) junto con un ejemplo de entrada en [`examples/sample.crud`](bison/examples/sample.crud). Para compilar y probar el parser:

```bash
cd bison
bison -d crud.y
gcc crud.tab.c -o crud_parser
./crud_parser < examples/sample.crud
```

La salida describe las producciones aplicadas y confirma si el programa es válido.

## 3 y 4. Analizadores en Python

El módulo [`python/predictive_parser.py`](python/predictive_parser.py) implementa:

- Transformación LL(1) de la gramática de expresiones.
- Cálculo automático de conjuntos FIRST, FOLLOW y PREDICT.
- Un parser predictivo basado en pila.
- Un parser CYK y funciones para comparar su rendimiento con el parser predictivo.
- Un algoritmo de emparejamiento estilo descenso recursivo.

Para ejecutar la demostración interactiva:

```bash
python python/predictive_parser.py
```

## 5. Pruebas automatizadas

Las pruebas unitarias se encuentran en [`python/tests/test_parsers.py`](python/tests/test_parsers.py). Se pueden ejecutar con:

```bash
pytest
```
