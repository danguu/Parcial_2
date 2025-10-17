#include <stdio.h>
#include <stdlib.h>

int yyparse(void);
extern FILE *yyin;

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Uso: %s archivo.crud [archivo2.crud ...]\n", argv[0]);
        return EXIT_FAILURE;
    }
    for (int i = 1; i < argc; ++i) {
        const char *filename = argv[i];
        FILE *file = fopen(filename, "r");
        if (!file) {
            perror(filename);
            continue;
        }
        yyin = file;
        int result = yyparse();
        if (result == 0) {
            printf("%s: análisis exitoso\n", filename);
        }
        fclose(file);
    }
    return EXIT_SUCCESS;
}
