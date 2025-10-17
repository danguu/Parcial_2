%{
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int yylex(void);
static void yyerror(const char *s);

static int line_number = 1;

static char *copy_text(const char *src, size_t len) {
    char *dst = (char *)malloc(len + 1);
    if (!dst) {
        fprintf(stderr, "Error: memoria insuficiente\n");
        exit(EXIT_FAILURE);
    }
    memcpy(dst, src, len);
    dst[len] = '\0';
    return dst;
}
%}

%union {
    char *str;
}

%token DATABASE ENTITY CREATE READ UPDATE DELETE WITH FIELDS VALUES SET WHERE AND OR FROM TO TRUE FALSE INT_TYPE TEXT_TYPE BOOL_TYPE
%token <str> IDENT
%token <str> STRING_LITERAL
%token <str> NUMBER_LITERAL
%token EQ NEQ LT LE GT GE

%left OR
%left AND

%type <str> literal boolean_literal type_spec comp_op

%%
program
    : DATABASE IDENT '{' entity_decls statement_list '}'
      {
          printf("Programa válido. Base de datos: %s\n", $2);
          free($2);
      }
    ;

entity_decls
    : /* empty */
    | entity_decl entity_decls
    ;

entity_decl
    : ENTITY IDENT '{' field_decl_list '}'
      {
          printf("Entidad declarada: %s\n", $2);
          free($2);
      }
    ;

field_decl_list
    : field_decl field_decl_tail
    ;

field_decl_tail
    : /* empty */
    | ',' field_decl_list
    ;

field_decl
    : IDENT ':' type_spec
      {
          printf("  Campo %s : %s\n", $1, $3);
          free($1);
          free($3);
      }
    ;

type_spec
    : INT_TYPE   { $$ = copy_text("INT", 3); }
    | TEXT_TYPE  { $$ = copy_text("TEXT", 4); }
    | BOOL_TYPE  { $$ = copy_text("BOOL", 4); }
    ;

statement_list
    : /* empty */
    | statement statement_list
    ;

statement
    : create_stmt
    | read_stmt
    | update_stmt
    | delete_stmt
    ;

create_stmt
    : CREATE IDENT WITH field_value_list ';'
      {
          printf("Crear registros en %s\n", $2);
          free($2);
      }
    ;

field_value_list
    : '(' field_value_pairs ')'
    ;

field_value_pairs
    : field_value field_value_tail
    ;

field_value_tail
    : /* empty */
    | ',' field_value_pairs
    ;

field_value
    : IDENT EQ literal
      {
          printf("    %s = %s\n", $1, $3);
          free($1);
          free($3);
      }
    ;

read_stmt
    : READ IDENT opt_where ';'
      {
          printf("Leer registros de %s\n", $2);
          free($2);
      }
    ;

opt_where
    : /* empty */
    | WHERE boolean_expr
    ;

update_stmt
    : UPDATE IDENT SET assignment_list opt_where ';'
      {
          printf("Actualizar registros en %s\n", $2);
          free($2);
      }
    ;

assignment_list
    : assignment assignment_tail
    ;

assignment_tail
    : /* empty */
    | ',' assignment_list
    ;

assignment
    : IDENT EQ literal
      {
          printf("    asignar %s = %s\n", $1, $3);
          free($1);
          free($3);
      }
    ;

delete_stmt
    : DELETE IDENT opt_where ';'
      {
          printf("Eliminar registros de %s\n", $2);
          free($2);
      }
    ;

boolean_expr
    : boolean_term boolean_expr_tail
    ;

boolean_expr_tail
    : /* empty */
    | OR boolean_term boolean_expr_tail
    ;

boolean_term
    : boolean_factor boolean_term_tail
    ;

boolean_term_tail
    : /* empty */
    | AND boolean_factor boolean_term_tail
    ;

boolean_factor
    : comparison
    | '(' boolean_expr ')'
    ;

comparison
    : IDENT comp_op literal
      {
          printf("      condición %s %s %s\n", $1, $2, $3);
          free($1);
          free($2);
          free($3);
      }
    ;

comp_op
    : EQ { $$ = copy_text("=", 1); }
    | NEQ { $$ = copy_text("!=", 2); }
    | LT { $$ = copy_text("<", 1); }
    | LE { $$ = copy_text("<=", 2); }
    | GT { $$ = copy_text(">", 1); }
    | GE { $$ = copy_text(">=", 2); }
    ;

literal
    : NUMBER_LITERAL
    | STRING_LITERAL
    | boolean_literal
    ;

boolean_literal
    : TRUE { $$ = copy_text("TRUE", 4); }
    | FALSE { $$ = copy_text("FALSE", 5); }
    ;

%%

static int read_identifier(int c, char **out) {
    char buffer[256];
    size_t len = 0;
    buffer[len++] = (char)c;
    while ((c = getchar()) != EOF && (isalnum(c) || c == '_')) {
        if (len + 1 >= sizeof(buffer)) {
            fprintf(stderr, "Identificador demasiado largo\n");
            exit(EXIT_FAILURE);
        }
        buffer[len++] = (char)c;
    }
    buffer[len] = '\0';
    if (c != EOF) {
        ungetc(c, stdin);
    }
    *out = copy_text(buffer, len);
    return 0;
}

static int read_number(int c, char **out) {
    char buffer[256];
    size_t len = 0;
    buffer[len++] = (char)c;
    while ((c = getchar()) != EOF && isdigit(c)) {
        if (len + 1 >= sizeof(buffer)) {
            fprintf(stderr, "Número demasiado largo\n");
            exit(EXIT_FAILURE);
        }
        buffer[len++] = (char)c;
    }
    buffer[len] = '\0';
    if (c != EOF) {
        ungetc(c, stdin);
    }
    *out = copy_text(buffer, len);
    return 0;
}

static int read_string_literal(char **out) {
    char buffer[512];
    size_t len = 0;
    int c;
    while ((c = getchar()) != EOF) {
        if (c == '\n') {
            line_number++;
        }
        if (c == '\\') {
            int next = getchar();
            if (next == EOF) {
                break;
            }
            if (len + 2 >= sizeof(buffer)) {
                fprintf(stderr, "Cadena demasiado larga\n");
                exit(EXIT_FAILURE);
            }
            buffer[len++] = (char)c;
            buffer[len++] = (char)next;
        } else if (c == '"') {
            buffer[len] = '\0';
            *out = copy_text(buffer, len);
            return 0;
        } else {
            if (len + 1 >= sizeof(buffer)) {
                fprintf(stderr, "Cadena demasiado larga\n");
                exit(EXIT_FAILURE);
            }
            buffer[len++] = (char)c;
        }
    }
    fprintf(stderr, "Cadena no terminada en línea %d\n", line_number);
    exit(EXIT_FAILURE);
}

static int match_keyword(const char *text) {
    if (strcmp(text, "DATABASE") == 0) return DATABASE;
    if (strcmp(text, "ENTITY") == 0) return ENTITY;
    if (strcmp(text, "CREATE") == 0) return CREATE;
    if (strcmp(text, "READ") == 0) return READ;
    if (strcmp(text, "UPDATE") == 0) return UPDATE;
    if (strcmp(text, "DELETE") == 0) return DELETE;
    if (strcmp(text, "WITH") == 0) return WITH;
    if (strcmp(text, "FIELDS") == 0) return FIELDS;
    if (strcmp(text, "VALUES") == 0) return VALUES;
    if (strcmp(text, "SET") == 0) return SET;
    if (strcmp(text, "WHERE") == 0) return WHERE;
    if (strcmp(text, "AND") == 0) return AND;
    if (strcmp(text, "OR") == 0) return OR;
    if (strcmp(text, "FROM") == 0) return FROM;
    if (strcmp(text, "TO") == 0) return TO;
    if (strcmp(text, "TRUE") == 0) return TRUE;
    if (strcmp(text, "FALSE") == 0) return FALSE;
    if (strcmp(text, "INT") == 0) return INT_TYPE;
    if (strcmp(text, "TEXT") == 0) return TEXT_TYPE;
    if (strcmp(text, "BOOL") == 0) return BOOL_TYPE;
    return 0;
}

static int yylex(void) {
    int c;
    while ((c = getchar()) != EOF) {
        if (c == ' ' || c == '\t' || c == '\r') {
            continue;
        }
        if (c == '\n') {
            line_number++;
            continue;
        }
        if (isalpha(c) || c == '_') {
            char *text = NULL;
            read_identifier(c, &text);
            for (size_t i = 0; text[i]; ++i) {
                text[i] = (char)toupper((unsigned char)text[i]);
            }
            int keyword = match_keyword(text);
            if (keyword) {
                free(text);
                return keyword;
            }
            yylval.str = text;
            return IDENT;
        }
        if (isdigit(c)) {
            char *number = NULL;
            read_number(c, &number);
            yylval.str = number;
            return NUMBER_LITERAL;
        }
        switch (c) {
            case '"': {
                char *text = NULL;
                read_string_literal(&text);
                yylval.str = text;
                return STRING_LITERAL;
            }
            case '=': {
                int next = getchar();
                if (next == '=') {
                    return EQ;
                }
                if (next != EOF) {
                    ungetc(next, stdin);
                }
                return EQ;
            }
            case '!': {
                int next = getchar();
                if (next == '=') {
                    return NEQ;
                }
                fprintf(stderr, "Símbolo ! inválido en línea %d\n", line_number);
                exit(EXIT_FAILURE);
            }
            case '<': {
                int next = getchar();
                if (next == '=') {
                    return LE;
                }
                if (next != EOF) {
                    ungetc(next, stdin);
                }
                return LT;
            }
            case '>': {
                int next = getchar();
                if (next == '=') {
                    return GE;
                }
                if (next != EOF) {
                    ungetc(next, stdin);
                }
                return GT;
            }
            case ',':
            case ';':
            case '{':
            case '}':
            case '(':
            case ')':
            case ':':
                return c;
            default:
                fprintf(stderr, "Carácter inesperado '%c' en línea %d\n", c, line_number);
                exit(EXIT_FAILURE);
        }
    }
    return 0;
}

static void yyerror(const char *s) {
    fprintf(stderr, "Error de sintaxis en línea %d: %s\n", line_number, s);
}

int main(void) {
    if (yyparse() == 0) {
        return EXIT_SUCCESS;
    }
    return EXIT_FAILURE;
}
