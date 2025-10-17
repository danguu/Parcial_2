# Parcial

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

## 3. Analizador LL(1) en Python

El módulo [`python/ll1_parser.py`](python/ll1_parser.py) implementa:

- Transformación LL(1) de la gramática de expresiones.
- Cálculo automático de conjuntos FIRST, FOLLOW y tablas de predicción.
- Un parser predictivo basado en pila con una demostración en línea de comandos.

Para ejecutar la demostración:

```bash
python python/ll1_parser.py
```

## 4. Parser CYK y comparación de rendimiento

El módulo [`python/cyk_parser.py`](python/cyk_parser.py) contiene una versión simplificada del algoritmo CYK aplicada a la misma gramática. También incluye la función `compare_with_ll1` para medir el rendimiento frente al parser predictivo.

Ejemplo de uso:

```bash
python python/cyk_parser.py
```

Para obtener una comparación rápida:

```python
from cyk_parser import compare_with_ll1
print(compare_with_ll1(["id + id", "id * id + id"]))
```

## 5. Emparejamiento por descenso recursivo

El archivo [`python/recursive_descent.py`](python/recursive_descent.py) muestra un algoritmo de emparejamiento manual basado en descenso recursivo. Se centra en claridad antes que en optimización y se puede ejecutar directamente desde la línea de comandos.

## 6. Pruebas automatizadas

Las pruebas unitarias se encuentran en [`python/tests/test_parsers.py`](python/tests/test_parsers.py). Se pueden ejecutar con:

```bash
pytest
```
