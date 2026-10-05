from __future__ import annotations
from ast_nodes import*
from symbols import*
from semantic_errors import*

def _resolve_bloc(block: Block, scope: Scope, erros: list[SemanticDiagnostic])->None:
    block.metadata["scope"] = scope 
    
    for stmt in block.statements:
            _resolve_node(stmt,scope,erros)

def _resolve_if(se: IfStmt, scope: Scope, erros: list[SemanticDiagnostic])->None:
    _resolve_node(se.condition,scope,erros)

    th_sco = Scope(parent = scope)
    _resolve_bloc(se.then_block,th_sco,erros)
    
    if se.else_block:
        el_sco = Scope(parent = scope)
        _resolve_bloc(se.else_block,el_sco,erros)

def _resolve_var(dec: VarDecl, scope: Scope, erros: list[SemanticDiagnostic])->None:
    if dec in scope.symbols:
        erros.append(
            SemanticDiagnostic(
                SemanticErrorKind.DUPLICATE_DECLARATION,
                f"Nome da variável '{dec.name}' duplicada!",
                span = dec.span
            )
        )
    else:
        var_sim = Symbol(
            dec.name,SymbolKind.VARIABLE,
            dec.type,dec
        )
        scope.symbols[dec.name] = var_sim
        dec.metadata["symbol"] = var_sim

def _resolve_bi_exp(expr: BinaryExpr, scope: Scope, erros: list[SemanticDiagnostic])-> None:
    _resolve_node(expr.left, scope, erros)
    _resolve_node(expr.right,scope, erros)

def _resolve_un_exp(expr: UnaryExpr, scope: Scope, erros: list[SemanticDiagnostic])->None:
    _resolve_node(expr.operand)

def _resolve_while(stmt: WhileStmt, scope: Scope, erros: list[SemanticDiagnostic])->None:
    _resolve_node(stmt.condition,scope,erros)
    
    wh_scop = Scope(parent = scope)
    _resolve_node(stmt.body, wh_scop, erros)

def _resolve_atri(ass: Assignment, scope: Scope, erros: list[SemanticDiagnostic])->None:
    _resolve_node(ass.target, scope, erros)
    _resolve_node(ass.value)

def _resolve_id(id: IdentifierExpr, scope: Scope, erros: list[SemanticDiagnostic])->None:
    cur = scope
    sim = None
    while not cur:
        if id.name in cur
def _resolve_node(node, scope: Scope, erros: list[SemanticDiagnostic])->None:
    if isinstance(node,Block):
        bloc_scop = Scope(parent = scope)
        _resolve_bloc(node,bloc_scop,erros)
  
    elif isinstance(node,VarDecl):
        _resolve_var(node,scope,erros)

    elif isinstance(node,IfStmt):
        _resolve_if(node,scope,erros)
    
    elif isinstance(node,BinaryExpr):
        _resolve_bi_exp(node,scope, erros)

    elif isinstance(node,UnaryExpr):
        _resolve_un_exp(node,scope,erros)
    

def resolve_names(program: Program) -> None:
    """Construa escopos, símbolos e vínculos entre usos e declarações."""
    glob_scop = Scope(None)
    erros = []
    for  func in program.functions:
        if func.name in glob_scop.symbols:
            erros.append(
                SemanticDiagnostic(
                    SemanticErrorKind.DUPLICATE_FUNCTION,
                    f"Função '{func.name}' já declarada",
                    span =func.span
                )
            )
        else:
            func_sim = FunctionSymbol(
                func.name,
                SymbolKind.FUNCTION,
                func.return_type,
                func, 
                parameter_types = tuple(p.type for p in func.parameters)
            )
            glob_scop.symbols[func_sim.name] = func_sim
            func.metadata["symbol"] = func_sim
   
        
    # 2. Valide a existência e a assinatura de main.
    main_sim = glob_scop.symbols.get("main")
    if not main_sim:
        erros.append(
            SemanticDiagnostic(
                SemanticErrorKind.INVALID_MAIN,
                f"Função 'main' não declarada",
                span = program.span
            )
        )       

    elif isinstance(main_sim, FunctionSymbol):
        if main_sim.type != TypeName.INT:
            erros.append(
                SemanticDiagnostic(
                    SemanticErrorKind.INVALID_MAIN,
                    f"Tipo de Retorno de 'main' deve ser(int), encontrado({TypeName(main_sim.type)})",
                    span = main_sim.declaration.span
                )
            )
        elif len(main_sim.parameter_types) > 0:
            erros.append(
                SemanticDiagnostic(
                    SemanticErrorKind.INVALID_MAIN,
                    "A função 'main' não deve receber argumentos!",
                    span = main_sim.declaration.span
                )
            )            
    # 3. Percorra os corpos em ordem, criando um escopo para cada bloco.
    for func in program.functions:
        fun_scop = Scope(parent = glob_scop)
        
        for param in func.parameters:
            if param.name in fun_scop.symbols:
                erros.append(
                    SemanticDiagnostic(
                        SemanticErrorKind.DUPLICATE_DECLARATION,
                        f"Parâmetro '{param.name}' Duplicado",
                        span = param.span
                    )
                )
            else:
                par_sim = Symbol(
                    param.name,
                    SymbolKind.PARAMETER,
                    param.type,
                    param
                )
                fun_scop.symbols[param.name] = par_sim
                param.metadata["symbol"] = par_sim
        _resolve_node(func,fun_scop,erros)
    if erros:
        raise SemanticError(erros)
    # 4. Anote declarações, usos e blocos na AST.
    # 5. Acumule os diagnósticos desta passagem antes de lançar SemanticError.
    
