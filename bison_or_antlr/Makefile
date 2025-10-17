CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra

all: crud_parser

crud_parser: crud.tab.c lex.yy.c main.o
$(CC) $(CFLAGS) -o $@ crud.tab.c lex.yy.c main.o

crud.tab.c crud.tab.h: crud.y
bison -d crud.y

lex.yy.c: crud.l crud.tab.h
flex crud.l

main.o: main.c
$(CC) $(CFLAGS) -c main.c

clean:
rm -f crud_parser crud.tab.c crud.tab.h lex.yy.c main.o

.PHONY: all clean
