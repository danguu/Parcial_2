%{
#include <stdio.h>
#include <stdlib.h>

void yyerror(const char *msg);
int yylex(void);
%}

%define api.value.type {int}
%define parse.error verbose
%locations

%token CREATE TABLEKW READ UPDATE DELETE FROM WHEREKW AS ORDER BY ASC DESC LIMIT OFFSET SET DEFAULTKW INTKW TEXTKW BOOLKW FLOATKW TRUEKW FALSEKW ANDKW ORKW NOTKW
%token IDENT NUMBER STRING
%token PLUS MINUS STAR SLASH EQ NEQ LT LE GT GE
%token LPAREN RPAREN COMMA DOT SEMICOLON

%left ORKW
%left ANDKW
%right NOTKW
%nonassoc EQ NEQ LT LE GT GE
%left PLUS MINUS
%left STAR SLASH
%right UMINUS

%%
program
    : statements
    ;

statements
    : /* empty */
    | statements statement
    ;

statement
    : create_stmt SEMICOLON
    | read_stmt SEMICOLON
    | update_stmt SEMICOLON
    | delete_stmt SEMICOLON
    ;

create_stmt
    : CREATE TABLEKW IDENT LPAREN field_list RPAREN
    ;

field_list
    : field_decl
    | field_list COMMA field_decl
    ;

field_decl
    : IDENT type_spec default_opt
    ;

type_spec
    : INTKW
    | TEXTKW
    | BOOLKW
    | FLOATKW
    ;

default_opt
    : /* empty */
    | DEFAULTKW literal
    ;

read_stmt
    : READ source_spec where_opt order_opt limit_opt
    ;

source_spec
    : IDENT
    | IDENT AS IDENT
    ;

order_opt
    : /* empty */
    | ORDER BY order_list
    ;

order_list
    : order_item
    | order_list COMMA order_item
    ;

order_item
    : qualified_ident order_dir
    ;

order_dir
    : /* empty */
    | ASC
    | DESC
    ;

limit_opt
    : /* empty */
    | LIMIT NUMBER limit_tail
    ;

limit_tail
    : /* empty */
    | OFFSET NUMBER
    ;

update_stmt
    : UPDATE IDENT SET assignment_list where_opt
    ;

assignment_list
    : assignment
    | assignment_list COMMA assignment
    ;

assignment
    : qualified_ident EQ expr
    ;

delete_stmt
    : DELETE FROM IDENT where_opt
    ;

where_opt
    : /* empty */
    | WHEREKW disjunction
    ;

disjunction
    : conjunction
    | disjunction ORKW conjunction
    ;

conjunction
    : negation
    | conjunction ANDKW negation
    ;

negation
    : comparison
    | NOTKW negation
    ;

comparison
    : expr
    | expr EQ expr
    | expr NEQ expr
    | expr LT expr
    | expr LE expr
    | expr GT expr
    | expr GE expr
    ;

expr
    : expr PLUS expr
    | expr MINUS expr
    | expr STAR expr
    | expr SLASH expr
    | MINUS expr %prec UMINUS
    | LPAREN expr RPAREN
    | qualified_ident
    | literal
    ;

qualified_ident
    : IDENT
    | qualified_ident DOT IDENT
    ;

literal
    : NUMBER
    | STRING
    | TRUEKW
    | FALSEKW
    ;
%%

void yyerror(const char *msg) {
    fprintf(stderr, "Error sintáctico: %s en línea %d, columna %d\n", msg, yylloc.first_line, yylloc.first_column);
}
