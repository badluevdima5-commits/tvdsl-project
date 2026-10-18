from typing import List, Optional
from ast_nodes import *

class ParseError(Exception):
    def __init__(self, message: str, pos: Optional[Position] = None):
        self.message = message
        self.pos = pos
        super().__init__(f"{message} at {pos}" if pos else message)

class Parser:
    def __init__(self, tokens: List[dict]):
        self.tokens = tokens
        self.pos = 0

    def current_token(self) -> Optional[dict]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def peek_type(self) -> Optional[str]:
        tok = self.current_token()
        return tok['type'] if tok else None

    def current_pos(self) -> Position:
        tok = self.current_token()
        if tok:
            return Position(tok['line'], tok['column'])
        if self.tokens:
            last = self.tokens[-1]
            return Position(last['line'], last['column'])
        return Position(1, 1)

    def consume(self, expected_type: str) -> dict:
        tok = self.current_token()
        if not tok:
            raise ParseError(f"Expected {expected_type} but got EOF", self.current_pos())
        if tok['type'] != expected_type:
            raise ParseError(
                f"Expected {expected_type} but got {tok['type']} ('{tok['value']}')",
                Position(tok['line'], tok['column'])
            )
        self.pos += 1
        return tok

    def match(self, token_type: str) -> bool:
        return self.peek_type() == token_type

    def accept(self, token_type: str) -> Optional[dict]:
        if self.match(token_type):
            tok = self.current_token()
            self.pos += 1
            return tok
        return None
    # Module parsing

    def parse_module(self) -> Module:
        functions = []
        formulas = []
        while self.current_token():
            if self.match('FUNCTION'):
                functions.append(self.parse_function())
            else:
                formulas.append(self.parse_formula())
        return Module(functions=functions, formulas=formulas)

    # Function and Formula definitions

    def parse_function(self) -> FunctionDef:

        pos = self.current_pos()
        self.consume('FUNCTION')

        name_tok = self.consume('IDENT')
        name = name_tok['value']

        self.consume('LPAREN')
        params = self.parse_var_def_list()
        self.consume('RPAREN')

        requires = None
        if self.accept('REQUIRES'):
            requires = self.parse_predicate()

        self.consume('RETURNS')
        returns = self.parse_var_def_list_nonempty()

        ensures = None
        if self.accept('ENSURES'):
            ensures = self.parse_predicate()
        uses = []
        if self.accept('USES'):
            uses = self.parse_var_def_list_nonempty()

        body = self.parse_statement()

        return FunctionDef(
            name=name,
            params=params,
            returns=returns,
            requires=requires,
            ensures=ensures,
            uses=uses,
            body=body,
            pos=pos
        )

    def parse_formula(self) -> FormulaDef:
        pos = self.current_pos()
        name_tok = self.consume('IDENT')
        name = name_tok['value']
        self.consume('LPAREN')
        params = self.parse_var_def_list()
        self.consume('RPAREN')
        self.consume('ARROW_DOUBLE')
        body = self.parse_predicate()
        return FormulaDef(name=name, params=params, body=body, pos=pos)

    def parse_var_def_list(self) -> List[VarDef]:
        var_defs = []
        if self.match('IDENT'):
            var_defs.append(self.parse_var_def())
            while self.accept('COMMA'):
                var_defs.append(self.parse_var_def())
        return var_defs

    def parse_var_def_list_nonempty(self) -> List[VarDef]:
        var_defs = [self.parse_var_def()]
        while self.accept('COMMA'):
            var_defs.append(self.parse_var_def())
        return var_defs

    def parse_var_def(self) -> VarDef:
        pos = self.current_pos()
        name_tok = self.consume('IDENT')
        name = name_tok['value']
        self.consume('COLON')
        var_type = self.parse_type()
        return VarDef(name=name, var_type=var_type, pos=pos)

    def parse_type(self) -> Type:
        int_tok = self.consume('IDENT')
        if int_tok['value'] != 'int':
            raise ParseError(f"Expected type 'int' or 'int[]', got '{int_tok['value']}'",
                           Position(int_tok['line'], int_tok['column']))

        if self.accept('LBRACKET'):
            self.consume('RBRACKET')
            return IntArrayType()
        return IntType()
    # Statements

    def parse_statement(self) -> Statement:
        pos = self.current_pos()

        if self.match('LBRACE'):
            return self.parse_block()
        elif self.match('IF'):
            return self.parse_if()
        elif self.match('WHILE'):
            return self.parse_while()
        elif self.match('ASSERT'):
            return self.parse_assert()
        elif self.match('ASSUME'):
            return self.parse_assume()
        elif self.match('IDENT'):
            return self.parse_assignment()
        else:
            raise ParseError(f"Expected statement, got {self.peek_type()}", pos)

    def parse_assignment(self) -> Statement:
        pos = self.current_pos()
        first_name = self.consume('IDENT')['value']
        if self.match('LBRACKET'):
            self.consume('LBRACKET')
            index = self.parse_expr()
            self.consume('RBRACKET')
            self.consume('ASSIGN')
            value = self.parse_expr()
            self.consume('SEMICOLON')
            return ArrayUpdate(array_name=first_name, index=index, value=value, pos=pos)

        elif self.match('COMMA'):
            var_names = [first_name]
            while self.accept('COMMA'):
                var_names.append(self.consume('IDENT')['value'])
            self.consume('ASSIGN')
            call = self.parse_function_call_expr()
            self.consume('SEMICOLON')
            if not isinstance(call, FunctionCall):
                raise ParseError("Tuple assignment requires function call on right side", pos)
            return TupleAssignment(var_names=var_names, call=call, pos=pos)

        elif self.match('ASSIGN'):
            self.consume('ASSIGN')
            value = self.parse_expr()
            self.consume('SEMICOLON')
            return Assignment(var_name=first_name, value=value, pos=pos)

        else:
            raise ParseError(f"Expected '=', ',', or '[' after identifier in assignment", pos)

    def parse_if(self) -> IfStatement:
        pos = self.current_pos()
        self.consume('IF')
        self.consume('LPAREN')
        cond = self.parse_condition()
        self.consume('RPAREN')
        then_stmt = self.parse_statement()
        else_stmt = None
        if self.accept('ELSE'):
            else_stmt = self.parse_statement()

        return IfStatement(condition=cond, then_stmt=then_stmt, else_stmt=else_stmt, pos=pos)

    def parse_while(self) -> WhileStatement:
        pos = self.current_pos()
        self.consume('WHILE')
        self.consume('LPAREN')
        cond = self.parse_condition()
        self.consume('RPAREN')

        invariant = None
        if self.accept('INVARIANT'):
            invariant = self.parse_predicate()
        body = self.parse_statement()
        return WhileStatement(condition=cond, invariant=invariant, body=body, pos=pos)

    def parse_block(self) -> BlockStatement:
        pos = self.current_pos()
        self.consume('LBRACE')
        statements = []
        while not self.match('RBRACE'):
            if not self.current_token():
                raise ParseError("Unclosed block (expected '}')", pos)
            statements.append(self.parse_statement())
        self.consume('RBRACE')
        return BlockStatement(statements=statements, pos=pos)

    def parse_assert(self) -> AssertStatement:
        pos = self.current_pos()
        self.consume('ASSERT')
        cond = self.parse_condition()
        self.consume('SEMICOLON')
        return AssertStatement(condition=cond, pos=pos)

    def parse_assume(self) -> AssumeStatement:
        pos = self.current_pos()
        self.consume('ASSUME')
        cond = self.parse_condition()
        self.consume('SEMICOLON')
        return AssumeStatement(condition=cond, pos=pos)
    # Expressions

    def parse_expr(self) -> Expr:
        return self.parse_additive()

    def parse_additive(self) -> Expr:
        left = self.parse_multiplicative()
        while self.match('PLUS') or self.match('MINUS'):
            op_tok = self.current_token()
            op = op_tok['value']
            pos = Position(op_tok['line'], op_tok['column'])
            self.pos += 1
            right = self.parse_multiplicative()
            left = BinaryOp(op=op, left=left, right=right, pos=pos)
        return left

    def parse_multiplicative(self) -> Expr:
        left = self.parse_unary()
        while self.match('TIMES') or self.match('DIVIDE'):
            op_tok = self.current_token()
            op = op_tok['value']
            pos = Position(op_tok['line'], op_tok['column'])
            self.pos += 1
            right = self.parse_unary()
            left = BinaryOp(op=op, left=left, right=right, pos=pos)
        return left

    def parse_unary(self) -> Expr:
        if self.match('MINUS'):
            op_tok = self.current_token()
            pos = Position(op_tok['line'], op_tok['column'])
            self.pos += 1
            operand = self.parse_unary()
            return UnaryOp(op='-', operand=operand, pos=pos)
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        pos = self.current_pos()

        if self.match('INT'):
            tok = self.consume('INT')
            return IntLiteral(value=int(tok['value']), pos=Position(tok['line'], tok['column']))
        if self.match('TRUE'):
            tok = self.consume('TRUE')
            return BoolLiteral(value=True, pos=Position(tok['line'], tok['column']))
        if self.match('FALSE'):
            tok = self.consume('FALSE')
            return BoolLiteral(value=False, pos=Position(tok['line'], tok['column']))

        if self.match('LPAREN'):
            self.consume('LPAREN')
            expr = self.parse_expr()
            self.consume('RPAREN')
            return expr
        if self.match('LENGTH'):
            tok = self.consume('LENGTH')
            name = tok['value']
            pos = Position(tok['line'], tok['column'])
            self.consume('LPAREN')
            args = self.parse_expr_list()
            self.consume('RPAREN')
            return FunctionCall(name=name, args=args, pos=pos)
        if self.match('IDENT'):
            return self.parse_ident_expr()

        raise ParseError(f"Unexpected token in expression: {self.peek_type()}", pos)

    def parse_ident_expr(self) -> Expr:
        tok = self.consume('IDENT')
        name = tok['value']
        pos = Position(tok['line'], tok['column'])
        if self.match('LPAREN'):
            self.consume('LPAREN')
            args = self.parse_expr_list()
            self.consume('RPAREN')
            return FunctionCall(name=name, args=args, pos=pos)
        if self.match('LBRACKET'):
            self.consume('LBRACKET')
            index = self.parse_expr()
            self.consume('RBRACKET')
            return ArrayAccess(array=name, index=index, pos=pos)
        return VarRef(name=name, pos=pos)

    def parse_function_call_expr(self) -> FunctionCall:
        tok = self.consume('IDENT')
        name = tok['value']
        pos = Position(tok['line'], tok['column'])
        self.consume('LPAREN')
        args = self.parse_expr_list()
        self.consume('RPAREN')
        return FunctionCall(name=name, args=args, pos=pos)

    def parse_expr_list(self) -> List[Expr]:
        exprs = []
        if not self.match('RPAREN'):
            exprs.append(self.parse_expr())
            while self.accept('COMMA'):
                exprs.append(self.parse_expr())
        return exprs
    # Conditions

    def parse_condition(self) -> Condition:
        return self.parse_implication()

    def parse_implication(self) -> Condition:
        left = self.parse_or()
        if self.match('ARROW'):
            pos = self.current_pos()
            self.consume('ARROW')
            right = self.parse_implication()
            return BinaryLogical(op='->', left=left, right=right, pos=pos)
        return left

    def parse_or(self) -> Condition:
        left = self.parse_and()
        while self.match('OR'):
            pos = self.current_pos()
            self.consume('OR')
            right = self.parse_and()
            left = BinaryLogical(op='or', left=left, right=right, pos=pos)
        return left

    def parse_and(self) -> Condition:
        left = self.parse_not()
        while self.match('AND'):
            pos = self.current_pos()
            self.consume('AND')
            right = self.parse_not()
            left = BinaryLogical(op='and', left=left, right=right, pos=pos)
        return left

    def parse_not(self) -> Condition:
        if self.match('NOT'):
            pos = self.current_pos()
            self.consume('NOT')
            operand = self.parse_not()
            return NotCond(operand=operand, pos=pos)
        return self.parse_condition_primary()

    def parse_condition_primary(self) -> Condition:
        pos = self.current_pos()
        if self.match('TRUE'):
            self.consume('TRUE')
            return BoolConst(value=True, pos=pos)
        if self.match('FALSE'):
            self.consume('FALSE')
            return BoolConst(value=False, pos=pos)
        if self.match('LPAREN'):
            self.consume('LPAREN')
            cond = self.parse_condition()
            self.consume('RPAREN')
            return cond
        return self.parse_comparison()

    def parse_comparison(self) -> Comparison:
        pos = self.current_pos()
        left = self.parse_expr()
        if self.match('EQ'):
            op = '=='
            self.consume('EQ')
        elif self.match('NEQ'):
            op = '!='
            self.consume('NEQ')
        elif self.match('LEQ'):
            op = '<='
            self.consume('LEQ')
        elif self.match('GEQ'):
            op = '>='
            self.consume('GEQ')
        elif self.match('LT'):
            op = '<'
            self.consume('LT')
        elif self.match('GT'):
            op = '>'
            self.consume('GT')
        else:
            raise ParseError(f"Expected comparison operator", pos)

        right = self.parse_expr()
        return Comparison(op=op, left=left, right=right, pos=pos)

    #Predicates

    def parse_predicate(self) -> Predicate:
        return self.parse_predicate_implication()

    def parse_predicate_implication(self) -> Predicate:
        left = self.parse_predicate_or()
        if self.match('ARROW'):
            pos = self.current_pos()
            self.consume('ARROW')
            right = self.parse_predicate_implication()
            return PredicateBinary(op='->', left=left, right=right, pos=pos)
        return left

    def parse_predicate_or(self) -> Predicate:
        left = self.parse_predicate_and()
        while self.match('OR'):
            pos = self.current_pos()
            self.consume('OR')
            right = self.parse_predicate_and()
            left = PredicateBinary(op='or', left=left, right=right, pos=pos)
        return left

    def parse_predicate_and(self) -> Predicate:
        left = self.parse_predicate_not()
        while self.match('AND'):
            pos = self.current_pos()
            self.consume('AND')
            right = self.parse_predicate_not()
            left = PredicateBinary(op='and', left=left, right=right, pos=pos)
        return left

    def parse_predicate_not(self) -> Predicate:
        if self.match('NOT'):
            pos = self.current_pos()
            self.consume('NOT')
            operand = self.parse_predicate_not()
            return PredicateNot(operand=operand, pos=pos)
        return self.parse_predicate_primary()

    def parse_predicate_primary(self) -> Predicate:
        pos = self.current_pos()

        if self.match('FORALL') or self.match('EXISTS'):
            return self.parse_quantifier()
        if self.match('TRUE'):
            self.consume('TRUE')
            return PredicateBoolConst(value=True, pos=pos)
        if self.match('FALSE'):
            self.consume('FALSE')
            return PredicateBoolConst(value=False, pos=pos)

        if self.match('LPAREN'):
            self.consume('LPAREN')
            pred = self.parse_predicate()
            self.consume('RPAREN')
            return pred
        if self.match('IDENT'):
            saved_pos = self.pos
            name_tok = self.consume('IDENT')

            if self.match('LPAREN'):
                # Formula reference
                name = name_tok['value']
                pos = Position(name_tok['line'], name_tok['column'])
                self.consume('LPAREN')
                args = self.parse_expr_list()
                self.consume('RPAREN')
                return FormulaRef(name=name, args=args, pos=pos)
            else:
                self.pos = saved_pos
                return self.parse_predicate_comparison()
        return self.parse_predicate_comparison()

    def parse_quantifier(self) -> Quantifier:
        pos = self.current_pos()
        if self.match('FORALL'):
            self.consume('FORALL')
            q_type = 'forall'
        else:
            self.consume('EXISTS')
            q_type = 'exists'
        self.consume('LPAREN')
        var_def = self.parse_var_def()
        self.consume('PIPE')
        body = self.parse_predicate()
        self.consume('RPAREN')
        return Quantifier(quantifier_type=q_type, var_def=var_def, body=body, pos=pos)

    def parse_predicate_comparison(self) -> PredicateComparison:
        """Parse comparison in predicate context"""
        pos = self.current_pos()
        left = self.parse_expr()
        if self.match('EQ'):
            op = '=='
            self.consume('EQ')
        elif self.match('NEQ'):
            op = '!='
            self.consume('NEQ')
        elif self.match('LEQ'):
            op = '<='
            self.consume('LEQ')
        elif self.match('GEQ'):
            op = '>='
            self.consume('GEQ')
        elif self.match('LT'):
            op = '<'
            self.consume('LT')
        elif self.match('GT'):
            op = '>'
            self.consume('GT')
        else:
            raise ParseError(f"Expected comparison operator", pos)
        right = self.parse_expr()
        return PredicateComparison(op=op, left=left, right=right, pos=pos)
def parse(tokens: List[dict]) -> Module:
    """Parse tokens into AST"""
    parser = Parser(tokens)
    return parser.parse_module()
