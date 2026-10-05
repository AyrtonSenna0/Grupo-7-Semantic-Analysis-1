from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Iterator


class TokenKind(enum.Enum):
    """Classe já implementada: nomes e números não devem ser alterados."""

    EOF = -1

    IDENTIFIER = 1
    INT_LITERAL = 2
    STRING_LITERAL = 3

    KW_INT = 10
    KW_BOOL = 11
    KW_VOID = 12
    KW_TRUE = 13
    KW_FALSE = 14
    KW_IF = 15
    KW_ELSE = 16
    KW_WHILE = 17
    KW_RETURN = 18
    KW_PRINT = 19

    PLUS = 20
    MINUS = 21
    STAR = 22
    SLASH = 23
    PERCENT = 24
    LESS = 25
    LESS_EQUAL = 26
    GREATER = 27
    GREATER_EQUAL = 28
    EQUAL_EQUAL = 29
    NOT_EQUAL = 30
    LOGICAL_AND = 31
    LOGICAL_OR = 32
    LOGICAL_NOT = 33
    ASSIGN = 34

    LEFT_PAREN = 40
    RIGHT_PAREN = 41
    LEFT_BRACE = 42
    RIGHT_BRACE = 43
    COMMA = 44
    SEMICOLON = 45


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    value: int | str | bool | None
    line: int
    column: int

    def __str__(self) -> str:
        return (
            f"<{self.kind.value}, {self.kind.name}, {self.lexeme!r}, "
            f"{self.value!r}, {self.line}, {self.column}>"
        )


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"erro léxico em {self.line}:{self.column}: {self.message}"


class Lexer:
    """Converte texto-fonte MicroC em uma sequência de tokens."""

    def __init__(self, source: str):
        self.source = source
        self.linha = 1
        self.coluna = 1
        self.posi = 0
        self.reservadas ={
                          "bool": TokenKind.KW_BOOL,"else": TokenKind.KW_ELSE,
                          "false": TokenKind.KW_FALSE,"if": TokenKind.KW_IF,
                          "int": TokenKind.KW_INT,"print": TokenKind.KW_PRINT,
                          "return": TokenKind.KW_RETURN,"true": TokenKind.KW_TRUE, 
                          "while": TokenKind.KW_WHILE, "void": TokenKind.KW_VOID
                        }

    def tokens(self) -> Iterator[Token]:
        """Produza todos os tokens significativos e um único EOF ao final."""
        if  not (self.__ver_ascii(self.source)):
            raise LexerError("Caracteres fora do padrao ASCII",self.linha,self.coluna)
        while self.posi < len(self.source):
            while  self.posi < len(self.source) and (
                   self.source[self.posi] == ' ' 
                   or self.source[self.posi] == '\t'
                   or self.source[self.posi] == '\n'
                   or (self.source[self.posi] == '/' and 
                   self.posi+1 < len(self.source) and (
                   self.source[self.posi+1] == '*' or self.source[self.posi+1] == '/'))
            ):
                if self.source[self.posi] == '/':
                    if self.source[self.posi+1] == '*':
                        linha = self.linha
                        coluna = self.coluna
                        self.coluna += 2
                        self.posi += 2
                        while((self.posi+1) < len(self.source) and not(
                            self.source[self.posi] == '*' and self.source[self.posi+1] == '/')
                        ):
                            if self.source[self.posi] == '\n':
                                self.linha += 1
                                self.coluna = 1
                            elif self.source[self.posi] == '\t':
                                self.coluna += 4
                            else:
                                self.coluna += 1
                            self.posi += 1
                        if (self.posi + 1) >= len(self.source) or self.source[self.posi] != '*':
                            raise LexerError("Esperando '*/'",linha,coluna)
                        else:
                            self.coluna += 2
                            self.posi += 2
                    elif self.source[self.posi+1] == '/':
                        self.coluna += 2
                        self.posi += 2
                        while self.posi < len(self.source) and self.source[self.posi] != '\n':
                            if self.source[self.posi] == '\t':
                                self.coluna += 4
                            else:
                                self.coluna += 1
                            self.posi +=1
                        if self.posi < len(self.source) and self.source[self.posi] == '\n':
                            self.linha += 1
                            self.coluna = 1
                            self.posi += 1
                while self.posi < len(self.source) and (
                      self.source[self.posi] == ' '
                      or self.source[self.posi] == '\t'
                      or self.source[self.posi] ==  '\n'
                ):
                    if self.source[self.posi] == '\n':
                        self.linha += 1
                        self.coluna = 1
                    elif self.source[self.posi] == '\t':
                        self.coluna += 4
                    else:
                        self.coluna += 1
                    self.posi += 1
            if self.posi < len(self.source):
                yield self.__iden_tokens()

        yield Token(TokenKind.EOF, '', None, self.linha, self.coluna)

    def scan(self) -> list[Token]:
        return list(self.tokens())

    def __iden_tokens(self):
        if self.source[self.posi].isdigit():
            return self.__trata_dig()
        
        elif self.source[self.posi].isalpha() or(
             self.source[self.posi] == '_'
        ):
            return self.__trata_identif()

        elif(self.source[self.posi] == '='
             or  self.source[self.posi] == '<'
             or  self.source[self.posi] == '>'
             or  self.source[self.posi] == '!'
             or  self.source[self.posi] == '&'
             or  self.source[self.posi] == '|'
        ):
            return self.__trata_relacional()
        
        elif(self.source[self.posi] == '+'
             or  self.source[self.posi] == '-'
             or  self.source[self.posi] == '*'
             or  self.source[self.posi] == '/'
             or  self.source[self.posi] == '%'
        ):
            return self.__trata_operacional()
        
        elif(self.source[self.posi] == '('
             or  self.source[self.posi] == ')'
             or  self.source[self.posi] == '{'
             or  self.source[self.posi] == '}'
             or  self.source[self.posi] == ','
             or  self.source[self.posi] == ';'
        ):
            return self.__trata_pontuacao()
        
        elif self.source[self.posi] == '"':
            return self.__trata_string()
        else:
            raise LexerError("Simbolo invalido", self.linha, self.coluna)

    def __trata_dig(self):
        digito = self.source[self.posi]
        coluna = self.coluna
        self.posi +=1
        self.coluna +=1
        while self.posi < len(self.source) and (
              self.source[self.posi].isdigit()
        ):
            self.coluna+=1
            digito += self.source[self.posi]
            self.posi+=1
        return Token(TokenKind.INT_LITERAL,digito,int(digito),self.linha,coluna )
            
    def __trata_identif(self):
        coluna = self.coluna
        lex = self.source[self.posi]
        self.posi +=1
        self.coluna +=1
        while self.posi < len(self.source) and(
              self.source[self.posi].isalpha() or
              self.source[self.posi].isdigit() or
              self.source[self.posi] == '_'
        ):
            lex += self.source[self.posi]
            self.coluna +=1
            self.posi +=1
        if lex in self.reservadas:
            kind = self.reservadas[lex]
            if kind == TokenKind.KW_TRUE:
                return Token(kind, lex,True,self.linha,coluna)
            elif kind == TokenKind.KW_FALSE:
                return Token(kind, lex,False,self.linha,coluna)
            else:
                return Token(kind, lex,None,self.linha,coluna)
        else:
            return Token(TokenKind.IDENTIFIER, lex, lex, self.linha, coluna)
        
    def __trata_relacional(self):
        if self.source[self.posi] == '=':
            if (self.posi+1) < len(self.source) and(
                self.source[self.posi+1] == '='
            ):
                self.posi += 2
                self.coluna += 2
                return Token(TokenKind.EQUAL_EQUAL,"==", None, self.linha, (self.coluna-2))
            else:
                self.posi +=1
                self.coluna+=1
                return Token(TokenKind.ASSIGN,'=', None, self.linha, (self.coluna-1))
            
        elif self.source[self.posi] == '<':
            if (self.posi+1) < len(self.source) and(
                self.source[self.posi+1] == '='
            ):
                self.posi += 2
                self.coluna += 2
                return Token(TokenKind.LESS_EQUAL,"<=", None, self.linha, (self.coluna-2))
            
            else:
                self.posi +=1
                self.coluna+=1
                return Token(TokenKind.LESS,'<', None, self.linha, (self.coluna-1))
            
        elif self.source[self.posi] == '>':
            if (self.posi+1) < len(self.source) and(
                self.source[self.posi+1] == '='
            ):
                self.posi += 2
                self.coluna += 2
                return Token(TokenKind.GREATER_EQUAL,">=", None, self.linha, (self.coluna-2))
            else:
                self.posi +=1
                self.coluna+=1
                return Token(TokenKind.GREATER,'>', None, self.linha, (self.coluna-1))
        elif self.source[self.posi] == '!':
            if (self.posi+1) < len(self.source) and(
            self.source[self.posi+1] == '='
            ):
                self.posi += 2
                self.coluna += 2
                return Token(TokenKind.NOT_EQUAL,"!=", None, self.linha, (self.coluna-2))
            else:
                self.posi +=1
                self.coluna+=1
                return Token(TokenKind.LOGICAL_NOT,'!', None, self.linha, (self.coluna-1))

        elif self.source[self.posi] == '&':
            if (self.posi+1) < len(self.source) and(
                self.source[self.posi+1] == '&'
            ):
                self.posi += 2
                self.coluna += 2
                return Token(TokenKind.LOGICAL_AND,"&&", None, self.linha, (self.coluna-2))
            else:
                raise LexerError("Simbolo invalido '&'", self.linha, self.coluna)

        elif self.source[self.posi] == '|':
            if (self.posi+1) < len(self.source) and(
                self.source[self.posi+1] == '|'
            ):
                self.posi += 2
                self.coluna += 2
                return Token(TokenKind.LOGICAL_OR,"||", None, self.linha, (self.coluna-2))
            else:
                raise LexerError("Simbolo invalido '|'", self.linha, self.coluna)

    def __trata_operacional(self):
        if self.source[self.posi] == '+':
            self.coluna +=1
            self.posi +=1
            return Token(TokenKind.PLUS,"+", None, self.linha, (self.coluna-1))

        elif self.source[self.posi] == '-':
            self.coluna +=1
            self.posi +=1
            return Token(TokenKind.MINUS,"-", None, self.linha, (self.coluna-1))

        elif self.source[self.posi] == '*':
            self.coluna +=1
            self.posi +=1
            return Token(TokenKind.STAR,"*", None, self.linha, (self.coluna-1))

        elif self.source[self.posi] == '/':
            self.coluna +=1
            self.posi +=1
            return Token(TokenKind.SLASH,"/", None, self.linha, (self.coluna-1))

        elif self.source[self.posi] == '%':
            self.coluna +=1
            self.posi +=1
            return Token(TokenKind.PERCENT,"%", None, self.linha, (self.coluna-1))
        
    def __trata_pontuacao(self):
            if self.source[self.posi] == '(':
                self.coluna +=1
                self.posi +=1
                return Token(TokenKind.LEFT_PAREN,"(", None, self.linha, (self.coluna-1))
    
            elif self.source[self.posi] == ')':
                self.coluna +=1
                self.posi +=1
                return Token(TokenKind.RIGHT_PAREN,")", None, self.linha, (self.coluna-1))
    
            elif self.source[self.posi] == '{':
                self.coluna +=1
                self.posi +=1
                return Token(TokenKind.LEFT_BRACE,"{", None, self.linha, (self.coluna-1))
    
            elif self.source[self.posi] == '}':
                self.coluna +=1
                self.posi +=1
                return Token(TokenKind.RIGHT_BRACE,"}", None, self.linha, (self.coluna-1))
    
            elif self.source[self.posi] == ',':
                self.coluna +=1
                self.posi +=1
                return Token(TokenKind.COMMA,",", None, self.linha, (self.coluna-1))

            elif self.source[self.posi] == ';':
                self.coluna +=1
                self.posi +=1
                return Token(TokenKind.SEMICOLON,";", None, self.linha, (self.coluna-1))

    def __trata_string(self):
        coluna = self.coluna
        self.posi +=1
        self.coluna +=1
        string = ""
        while self.posi < len(self.source) and(
              self.source[self.posi] != '"'
        ):
            if self.source[self.posi] == '\n':
                raise LexerError("'(' nao fechado",self.linha,coluna)
            
            if self.source[self.posi] == '\\':
               if (self.posi+1) < len(self.source):
                   if self.source[self.posi+1] == 'n':
                       string += '\n'
                       self.coluna +=2
                       self.posi +=2

                   elif self.source[self.posi+1] == 't':
                       string += '\t'
                       self.coluna +=2
                       self.posi +=2                      

                   elif self.source[self.posi+1] == '"':
                       string += '\"'
                       self.coluna +=2
                       self.posi +=2            

                   elif self.source[self.posi+1] == '\\':
                       string += '\\'
                       self.coluna +=2
                       self.posi +=2      

                   else:
                       raise LexerError("String Literal nao terminada", self.linha, coluna)
               else:
                   raise LexerError("String Literal nao terminada", self.linha, coluna)
            else:
                string += self.source[self.posi]
                self.coluna+=1
                self.posi+=1
        if self.posi < len(self.source) and self.source[self.posi] == '"':
            self.posi +=1
            self.coluna+=1
            return Token(TokenKind.STRING_LITERAL,string, string,self.linha, coluna)
        else:
            raise LexerError("String Literal nao terminada", self.linha, coluna)

    def __ver_ascii(self, lista) -> bool:
        for texto in lista:
            if not texto.isascii():
                return False
            if texto == '\n':
                self.linha += 1
                self.coluna = 1
            else:
                self.coluna += 1
           
        self.linha = 1
        self.coluna = 1
        return True