# Gramática para lenguaje CRUD

Esta gramática describe un lenguaje imperativo minimalista centrado en operaciones CRUD sobre una base de datos relacional. Se apoya en un conjunto reducido de tipos y expresiones booleanas para filtrar registros.

## Conjuntos léxicos

- `IDENT`: identificadores alfanuméricos que comienzan con letra.
- `STRING`: cadenas entre comillas dobles con escapado `\"`.
- `NUMBER`: enteros positivos o cero.
- Palabras reservadas en mayúsculas: `DATABASE`, `ENTITY`, `CREATE`, `READ`, `UPDATE`, `DELETE`, `WITH`, `FIELDS`, `VALUES`, `SET`, `WHERE`, `AND`, `OR`, `FROM`, `TO`.
- Símbolos: `;`, `,`, `(`, `)`, `{`, `}`, `=`, `!=`, `<`, `<=`, `>`, `>=`.

## Gramática libre de contexto

```
program        -> DATABASE IDENT '{' entity_decls statement_list '}'
entity_decls   -> entity_decl entity_decls | ε
entity_decl    -> ENTITY IDENT '{' field_decl_list '}'
field_decl_list-> field_decl field_decl_tail
field_decl_tail-> ',' field_decl_list | ε
field_decl     -> IDENT ':' type_spec

type_spec      -> 'INT' | 'TEXT' | 'BOOL'

statement_list -> statement statement_list | ε
statement      -> create_stmt | read_stmt | update_stmt | delete_stmt

create_stmt    -> CREATE IDENT WITH field_value_list ';'
field_value_list -> '(' field_value_pairs ')'
field_value_pairs -> field_value field_value_tail
field_value_tail  -> ',' field_value_pairs | ε
field_value    -> IDENT '=' literal

read_stmt      -> READ IDENT opt_where ';'
opt_where      -> WHERE boolean_expr | ε

update_stmt    -> UPDATE IDENT SET assignment_list opt_where ';'
assignment_list-> assignment assignment_tail
assignment_tail-> ',' assignment_list | ε
assignment     -> IDENT '=' literal

delete_stmt    -> DELETE IDENT opt_where ';'

boolean_expr   -> boolean_term boolean_expr_tail
boolean_expr_tail -> OR boolean_term boolean_expr_tail | ε
boolean_term   -> boolean_factor boolean_term_tail
boolean_term_tail -> AND boolean_factor boolean_term_tail | ε
boolean_factor -> comparison | '(' boolean_expr ')'
comparison     -> IDENT comp_op literal
comp_op        -> '=' | '!=' | '<' | '<=' | '>' | '>='

literal        -> NUMBER | STRING | boolean_literal
boolean_literal-> 'TRUE' | 'FALSE'
```

## Observaciones

- El bloque `DATABASE` agrupa las definiciones de entidades y las instrucciones.
- El lenguaje permite múltiples operaciones CRUD secuenciales.
- Las expresiones booleanas usan precedencia estándar (`AND` sobre `OR`).
- Los valores válidos para asignaciones son literales; se puede extender con expresiones aritméticas si es necesario.
```
