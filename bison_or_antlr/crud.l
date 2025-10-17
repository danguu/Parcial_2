%option noyywrap nodefault yylineno
%option nounput noinput

%{
#include "crud.tab.h"
#include <string.h>

static int column = 1;
#define YY_USER_ACTION \
    yylloc.first_line = yylineno; \
    yylloc.first_column = column; \
    column += yyleng; \
    yylloc.last_line = yylineno; \
    yylloc.last_column = column - 1;
%}

ws      [ \t\r]+
ident   [A-Za-z_][A-Za-z0-9_]*
number  [0-9]+(\.[0-9]+)?
string  "([^"\\]|\\.)*"

%%
{ws}           ;
"\n"           { column = 1; }
"#"[^\n]*    ;
"CREATE"      { return CREATE; }
"TABLE"       { return TABLEKW; }
"READ"        { return READ; }
"UPDATE"      { return UPDATE; }
"DELETE"      { return DELETE; }
"FROM"        { return FROM; }
"WHERE"       { return WHEREKW; }
"AS"          { return AS; }
"ORDER"       { return ORDER; }
"BY"          { return BY; }
"ASC"         { return ASC; }
"DESC"        { return DESC; }
"LIMIT"       { return LIMIT; }
"OFFSET"      { return OFFSET; }
"SET"         { return SET; }
"DEFAULT"     { return DEFAULTKW; }
"INT"         { return INTKW; }
"TEXT"        { return TEXTKW; }
"BOOL"        { return BOOLKW; }
"FLOAT"       { return FLOATKW; }
"TRUE"        { return TRUEKW; }
"FALSE"       { return FALSEKW; }
"AND"         { return ANDKW; }
"OR"          { return ORKW; }
"NOT"         { return NOTKW; }
"+"          { return PLUS; }
"-"          { return MINUS; }
"*"          { return STAR; }
"/"          { return SLASH; }
"="          { return EQ; }
"!="         { return NEQ; }
"<="         { return LE; }
">="         { return GE; }
"<"          { return LT; }
">"          { return GT; }
"("          { return LPAREN; }
")"          { return RPAREN; }
","          { return COMMA; }
"."          { return DOT; }
";"          { return SEMICOLON; }
{number}      { return NUMBER; }
{string}      { return STRING; }
{ident}       { return IDENT; }
.              { fprintf(stderr, "Caracter inesperado '%s' en línea %d, columna %d\n", yytext, yylineno, column); return 0; }
%%
