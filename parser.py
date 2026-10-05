from __future__ import annotations

from collections.abc import Sequence

from Lexer import Token, TokenKind
from ast_nodes import* 


TYPE_START = {TokenKind.KW_INT, TokenKind.KW_BOOL, TokenKind.KW_VOID}
EXPRESSION_START = {
    TokenKind.IDENTIFIER,
    TokenKind.INT_LITERAL,
    TokenKind.KW_FALSE,
    TokenKind.KW_TRUE,
    TokenKind.LEFT_PAREN,
    TokenKind.LOGICAL_NOT,
    TokenKind.MINUS,
}
STATEMENT_START = TYPE_START | {
    TokenKind.IDENTIFIER,
    TokenKind.KW_IF,
    TokenKind.KW_WHILE,
    TokenKind.KW_RETURN,
    TokenKind.KW_PRINT,
    TokenKind.LEFT_BRACE,
}


TYPE_BY_TOKEN = {
    TokenKind.KW_INT: TypeName.INT,
    TokenKind.KW_BOOL: TypeName.BOOL,
    TokenKind.KW_VOID: TypeName.VOID,
}


class ParserError(Exception):
    def __init__(self, token: Token, expected: set[TokenKind]):
        self.token = token
        self.expected = frozenset(expected)
        super().__init__()

    @property
    def line(self) -> int:
        return self.token.line

    @property
    def column(self) -> int:
        return self.token.column

    def __str__(self) -> str:
        names = ", ".join(kind.name for kind in sorted(
            self.expected,
            key=lambda kind: kind.value,
        ))
        return (
            f"erro sintático em {self.line}:{self.column}: esperado {{{names}}}, "
            f"encontrado {self.token.kind.name} ({self.token.lexeme!r})"
        )


class Parser:
    def __init__(self, tokens: Sequence[Token]):
        self.tokens = list(tokens)
        if not self.tokens:
            raise ValueError("a sequência de tokens deve terminar em EOF")
        if self.tokens[-1].kind is not TokenKind.EOF:
            raise ValueError("o último token deve ser EOF")
        if any(token.kind is TokenKind.EOF for token in self.tokens[:-1]):
            raise ValueError("EOF deve aparecer uma única vez, no final")
        self.current = 0

    def peek(self, offset: int = 0) -> Token:
        index = min(self.current + offset, len(self.tokens) - 1)
        return self.tokens[index]

    def check(self, kind: TokenKind) -> bool:
        return self.peek().kind is kind

    def advance(self) -> Token:
        token = self.peek()
        if self.current < len(self.tokens) - 1:
            self.current += 1
        return token

    def match(self, *kinds: TokenKind) -> Token | None:
        if self.peek().kind in kinds:
            return self.advance()
        return None

    def expect(self, kinds: TokenKind | set[TokenKind]) -> Token:
        expected = kinds if isinstance(kinds, set) else {kinds}
        token = self.peek()
        if token.kind not in expected:
            raise ParserError(token, set(expected))
        return self.advance()

    @staticmethod
    def _token_span(token: Token) -> SourceSpan:
        return SourceSpan(
            token.line,
            token.column,
            token.line,
            token.column + len(token.lexeme),
        )

    @staticmethod
    def _start(value: Token | Node) -> tuple[int, int]:
        if isinstance(value, Node):
            return value.span.start_line, value.span.start_column
        return value.line, value.column

    @staticmethod
    def _end(value: Token | Node) -> tuple[int, int]:
        if isinstance(value, Node):
            return value.span.end_line, value.span.end_column
        return value.line, value.column + len(value.lexeme)

    @classmethod
    def _span(cls, first: Token | Node, last: Token | Node) -> SourceSpan:
        start_line, start_column = cls._start(first)
        end_line, end_column = cls._end(last)
        return SourceSpan(start_line, start_column, end_line, end_column)

    def parse(self) -> Program:
        return self.parse_program()

    # program ::= function* EOF
    def parse_program(self) -> Program:
        start = self.peek()
        functions: list[FunctionDecl] = []
        while self.peek().kind in TYPE_START:
            functions.append(self.parse_function())
        eof = self.expect(TokenKind.EOF)
        return Program(functions, span = self._span(start, eof))

    # function ::= type IDENTIFIER ... block
    def parse_function(self) -> FunctionDecl:
        start = self.peek()
        return_type = self.parse_type()
        name = self.expect(TokenKind.IDENTIFIER)
        self.expect(TokenKind.LEFT_PAREN)
        parameters = (
            self.parse_parameter_list()
            if self.peek().kind in TYPE_START
            else []
        )
        self.expect(TokenKind.RIGHT_PAREN)
        body = self.parse_block()
        return FunctionDecl(
            return_type,
            name.lexeme,
            parameters,
            body,
            span = self._span(start, body),
        )

    # type ::= KW_INT | KW_BOOL | KW_VOID
    def parse_type(self) -> TypeName:
        token = self.expect(TYPE_START)
        return TYPE_BY_TOKEN[token.kind]

    def parse_parameter_list(self) -> list[Parameter]:
        params = [self.parse_parameter()]
        while self.match(TokenKind.COMMA):
            params.append(self.parse_parameter())
        return params

    def parse_parameter(self) -> Parameter:
        start = self.peek()
        param_type = self.parse_type()
        name = self.expect(TokenKind.IDENTIFIER)
        return Parameter(
            param_type,
            name.lexeme,
            span = self._span(start, name)
        )

    def parse_block(self) -> Block:
        start = self.peek()
        self.expect(TokenKind.LEFT_BRACE)
        statements = []
        while self.peek().kind != TokenKind.RIGHT_BRACE and(
            self.peek().kind != TokenKind.EOF
        ):
            statements.append(self.parse_statement())
       
        return Block(
            statements,
            span = self._span(start, self.expect(TokenKind.RIGHT_BRACE))
        )

    def parse_statement(self) -> Stmt:
        
        if self.peek().kind in TYPE_START:
            return self.parse_declaration()
        
        elif self.check(TokenKind.KW_IF):
            return self.parse_if_statement()
        
        elif self.check(TokenKind.KW_WHILE):
            return self.parse_while_statement()
        
        elif self.check(TokenKind.KW_RETURN):
            return self.parse_return_statement()
        
        elif self.check(TokenKind.KW_PRINT):
            return self.parse_print_statement()
        
        elif self.check(TokenKind.LEFT_BRACE):
            return self.parse_block()

        elif self.check(TokenKind.IDENTIFIER):
            return self.parse_id_or_call_statement()

        else:
            self.expect(STATEMENT_START)
        

    def parse_id_or_call_statement(self) -> Stmt:
        if self.peek(1).kind == TokenKind.LEFT_PAREN:
            start = self.peek()         
            expr = self.parse_expression()
            end = self.expect(TokenKind.SEMICOLON)
            return CallStmt(
                expr,
                span = self._span(start,end)
            )
        else:
            
            start = self.advance()
            target = IdentifierExpr(name = start.lexeme, span = self._span(start,start))
            self.expect(TokenKind.ASSIGN)
            expr = self.parse_expression()
            end = self.expect(TokenKind.SEMICOLON)
            return Assignment(
                target,
                expr,
                span = self._span(start,end)
            )

    def parse_declaration(self) -> Stmt:
        start = self.advance()
        self.expect(TokenKind.IDENTIFIER)
        expr = None
        if self.match(TokenKind.ASSIGN):
            expr = self.parse_expression()

        end = self.expect(TokenKind.SEMICOLON)
        return VarDecl(
            TypeName(start.lexeme),
            start.lexeme,
            expr,
            span = self._span(start,end)
        )
        


    def parse_if_statement(self) -> Stmt:
        start = self.advance()
        self.expect(TokenKind.LEFT_PAREN)
        expr = self.parse_expression()
        self.expect(TokenKind.RIGHT_PAREN)
        block = self.parse_block()
        else_block = None
        if self.match(TokenKind.KW_ELSE):
            else_block = self.parse_block()
            end = else_block
        else:
            end = block
        return IfStmt(
            expr,
            block,
            else_block,
            span = self._span(start,end)
            )
        

    def parse_while_statement(self) -> Stmt:
        start = self.advance()
        self.expect(TokenKind.LEFT_PAREN)
        expr = self.parse_expression()
        
        self.expect(TokenKind.RIGHT_PAREN)
        block = self.parse_block()
        
        return WhileStmt(expr,block,span = self._span(start,block))
       
    def parse_return_statement(self) -> Stmt:
        start = self.expect(TokenKind.KW_RETURN)
        expr = None
        if not self.check(TokenKind.SEMICOLON):
            expr = self.parse_expression()

        end = self.expect(TokenKind.SEMICOLON)
        return ReturnStmt(
            expr,
            span = self._span(start,end)
        )

       

    def parse_print_statement(self) -> Stmt:
        start = self.advance()
        itens = []
        self.expect(TokenKind.LEFT_PAREN)
        itens.append(self.parse_print_item())
        
        while self.match(TokenKind.COMMA):
            itens.append(self.parse_print_item())
        
        self.expect(TokenKind.RIGHT_PAREN)
        end = self.expect(TokenKind.SEMICOLON)

        return PrintStmt(itens, span = self._span(start,end))

    def parse_print_item(self) -> PrintItem:
        if self.check(TokenKind.STRING_LITERAL):
           return self.parse_string_literals()
        else:
            return self.parse_expression()

    def parse_string_literals(self) -> StringLiteral:
        start = self.advance()
        stri = start.value
        prox = start

        while self.check(TokenKind.STRING_LITERAL):
            prox = self.advance()
            stri += prox.value

        return StringLiteral(stri,span = self._span(start,prox))

    def parse_expression(self) -> Expr:
        return self.parse_logical_or()

    def parse_logical_or(self) -> Expr:
        left = self.parse_logical_and()

        while self.check(TokenKind.LOGICAL_OR):
            token = self.advance()
            right =self.parse_logical_and()

            left = BinaryExpr(
                BinaryOperator(token.lexeme),
                left, right,
                span = self._span(left,right)
            )
        return left

    def parse_logical_and(self) -> Expr:
        left = self.parse_equality()

        while self.check(TokenKind.LOGICAL_AND):
            token = self.advance()
            right = self.parse_equality()

            left = BinaryExpr(
                BinaryOperator(token.lexeme),
                left,right,
                span = self._span(left,right)
            )
        return left

    def parse_equality(self) -> Expr:
        left = self.parse_relational()

        while self.check(TokenKind.EQUAL_EQUAL) or self.check(TokenKind.NOT_EQUAL):
            token = self.advance()
            right = self.parse_relational()

            left = BinaryExpr(
                BinaryOperator(token.lexeme),
                left,right,
                span = self._span(left,right)
            )
        return left
       

    def parse_relational(self) -> Expr:
        left = self.parse_additive()

        while(
            self.check(TokenKind.LESS) or
            self.check(TokenKind.GREATER) or
            self.check(TokenKind.GREATER_EQUAL) or
            self.check(TokenKind.LESS_EQUAL) 
            ):
                token = self.advance()
                right = self.parse_additive()

                left = BinaryExpr(
                    BinaryOperator(token.lexeme),
                    left,right,
                    span = self._span(left,right)
                )
        return left

    def parse_additive(self) -> Expr:
        left = self.parse_multiplicative()
       
        while self.check(TokenKind.PLUS) or self.check(TokenKind.MINUS):
            token = self.advance()
            right = self.parse_multiplicative()

            left = BinaryExpr(
                BinaryOperator(token.lexeme),
                left,right,
                span = self._span(left,right)
            )
        return left
        
    def parse_multiplicative(self) -> Expr:
        left = self.parse_unary()

        while (self.check(TokenKind.STAR) or
               self.check(TokenKind.SLASH) or
               self.check(TokenKind.PERCENT) 
            ):
            token = self.advance()
            right = self.parse_unary()

            left = BinaryExpr(
                BinaryOperator(token.lexeme),
                left,right,
                span = self._span(left, right)
            )
        return left

    def parse_unary(self) -> Expr:
        if self.check(TokenKind.LOGICAL_NOT) or self.check(TokenKind.MINUS):
            token = self.advance()
            operand = self.parse_unary()
            return UnaryExpr(
                UnaryOperator(token.lexeme),
                operand,
                span = self._span(token,operand)
            )
        
        return self.parse_primary()
        

    def parse_primary(self) -> Expr:
        if self.check(TokenKind.INT_LITERAL):
            token = self.advance()
            return IntLiteral(token.value, span = self._span(token,token))

        elif self.check(TokenKind.KW_FALSE) or self.check(TokenKind.KW_TRUE):
            token = self.advance()
            return BoolLiteral(token.value, span = self._span(token,token))
        
        elif self.check(TokenKind.IDENTIFIER):
            token = self.advance()
            if self.check(TokenKind.LEFT_PAREN):
                self.advance()
                args = self.parse_arguments()
                end = self.expect(TokenKind.RIGHT_PAREN)

                return CallExpr(
                    token.lexeme,
                    args,
                    span = self._span(token,end)
                )
            
            return IdentifierExpr(name = token.lexeme, span = self._span(token,token))
        
        else:
            self.expect(TokenKind.LEFT_PAREN)
            expr = self.parse_expression()
            self.expect(TokenKind.RIGHT_PAREN)
            return expr


    def parse_arguments(self) -> list[Expr]:
        args = []
        if not self.check(TokenKind.RIGHT_PAREN):
            args.append(self.parse_expression())
            while self.match(TokenKind.COMMA):
                args.append(self.parse_expression())
        return args
        

