import json
from typing import Any
from ast_nodes import *


class ASTPrinter:
    def __init__(self, indent_size: int = 2):
        self.indent_size = indent_size
        self.indent_level = 0

    def indent(self) -> str:
        return " " * (self.indent_level * self.indent_size)

    def print_module(self, module: Module) -> str:
        lines = ["Module"]
        self.indent_level += 1

        if module.formulas:
            lines.append(self.indent() + "Formulas:")
            self.indent_level += 1
            for formula in module.formulas:
                lines.extend(self.print_formula(formula).split('\n'))
            self.indent_level -= 1

        if module.functions:
            lines.append(self.indent() + "Functions:")
            self.indent_level += 1
            for func in module.functions:
                lines.extend(self.print_function(func).split('\n'))
            self.indent_level -= 1

        self.indent_level -= 1
        return '\n'.join(lines)

    def print_function(self, func: FunctionDef) -> str:
        lines = [self.indent() + f"Function {func.name}"]
        self.indent_level += 1

        # Parameters
        if func.params:
            params_str = ", ".join(str(p) for p in func.params)
            lines.append(self.indent() + f"params: ({params_str})")

        # Returns
        returns_str = ", ".join(str(r) for r in func.returns)
        lines.append(self.indent() + f"returns: ({returns_str})")

        # Requires
        if func.requires:
            lines.append(self.indent() + "requires:")
            self.indent_level += 1
            lines.append(self.indent() + self.print_predicate(func.requires))
            self.indent_level -= 1

        # Ensures
        if func.ensures:
            lines.append(self.indent() + "ensures:")
            self.indent_level += 1
            lines.append(self.indent() + self.print_predicate(func.ensures))
            self.indent_level -= 1

        # Uses
        if func.uses:
            uses_str = ", ".join(str(u) for u in func.uses)
            lines.append(self.indent() + f"uses: ({uses_str})")

        # Body
        lines.append(self.indent() + "body:")
        self.indent_level += 1
        lines.extend(self.print_statement(func.body).split('\n'))
        self.indent_level -= 1

        self.indent_level -= 1
        return '\n'.join(lines)

    def print_formula(self, formula: FormulaDef) -> str:
        lines = [self.indent() + f"Formula {formula.name}"]
        self.indent_level += 1

        if formula.params:
            params_str = ", ".join(str(p) for p in formula.params)
            lines.append(self.indent() + f"params: ({params_str})")

        lines.append(self.indent() + "=>")
        self.indent_level += 1
        lines.append(self.indent() + self.print_predicate(formula.body))
        self.indent_level -= 1

        self.indent_level -= 1
        return '\n'.join(lines)

    def print_statement(self, stmt: Statement) -> str:
        if isinstance(stmt, Assignment):
            return self.indent() + f"{stmt.var_name} = {self.print_expr(stmt.value)};"

        elif isinstance(stmt, ArrayUpdate):
            return self.indent() + f"{stmt.array_name}[{self.print_expr(stmt.index)}] = {self.print_expr(stmt.value)};"

        elif isinstance(stmt, TupleAssignment):
            vars_str = ", ".join(stmt.var_names)
            return self.indent() + f"{vars_str} = {self.print_expr(stmt.call)};"

        elif isinstance(stmt, IfStatement):
            lines = [self.indent() + f"if ({self.print_condition(stmt.condition)})"]
            self.indent_level += 1
            lines.extend(self.print_statement(stmt.then_stmt).split('\n'))
            self.indent_level -= 1
            if stmt.else_stmt:
                lines.append(self.indent() + "else")
                self.indent_level += 1
                lines.extend(self.print_statement(stmt.else_stmt).split('\n'))
                self.indent_level -= 1
            return '\n'.join(lines)

        elif isinstance(stmt, WhileStatement):
            lines = [self.indent() + f"while ({self.print_condition(stmt.condition)})"]
            if stmt.invariant:
                self.indent_level += 1
                lines.append(self.indent() + f"invariant: {self.print_predicate(stmt.invariant)}")
                self.indent_level -= 1
            self.indent_level += 1
            lines.extend(self.print_statement(stmt.body).split('\n'))
            self.indent_level -= 1
            return '\n'.join(lines)

        elif isinstance(stmt, BlockStatement):
            lines = [self.indent() + "{"]
            self.indent_level += 1
            for s in stmt.statements:
                lines.extend(self.print_statement(s).split('\n'))
            self.indent_level -= 1
            lines.append(self.indent() + "}")
            return '\n'.join(lines)

        elif isinstance(stmt, AssertStatement):
            return self.indent() + f"assert {self.print_condition(stmt.condition)};"

        elif isinstance(stmt, AssumeStatement):
            return self.indent() + f"assume {self.print_condition(stmt.condition)};"

        else:
            return self.indent() + f"<unknown statement: {type(stmt).__name__}>"

    def print_expr(self, expr: Expr) -> str:
        if isinstance(expr, IntLiteral):
            return str(expr.value)
        elif isinstance(expr, BoolLiteral):
            return "true" if expr.value else "false"
        elif isinstance(expr, VarRef):
            return expr.name
        elif isinstance(expr, UnaryOp):
            return f"({expr.op}{self.print_expr(expr.operand)})"
        elif isinstance(expr, BinaryOp):
            return f"({self.print_expr(expr.left)} {expr.op} {self.print_expr(expr.right)})"
        elif isinstance(expr, FunctionCall):
            args_str = ", ".join(self.print_expr(a) for a in expr.args)
            return f"{expr.name}({args_str})"
        elif isinstance(expr, ArrayAccess):
            return f"{expr.array}[{self.print_expr(expr.index)}]"
        else:
            return f"<unknown expr: {type(expr).__name__}>"

    def print_condition(self, cond: Condition) -> str:
        if isinstance(cond, BoolConst):
            return "true" if cond.value else "false"
        elif isinstance(cond, Comparison):
            return f"{self.print_expr(cond.left)} {cond.op} {self.print_expr(cond.right)}"
        elif isinstance(cond, NotCond):
            return f"not ({self.print_condition(cond.operand)})"
        elif isinstance(cond, BinaryLogical):
            return f"({self.print_condition(cond.left)} {cond.op} {self.print_condition(cond.right)})"
        else:
            return f"<unknown condition: {type(cond).__name__}>"

    def print_predicate(self, pred: Predicate) -> str:
        if isinstance(pred, PredicateBoolConst):
            return "true" if pred.value else "false"
        elif isinstance(pred, PredicateComparison):
            return f"{self.print_expr(pred.left)} {pred.op} {self.print_expr(pred.right)}"
        elif isinstance(pred, PredicateNot):
            return f"not ({self.print_predicate(pred.operand)})"
        elif isinstance(pred, PredicateBinary):
            return f"({self.print_predicate(pred.left)} {pred.op} {self.print_predicate(pred.right)})"
        elif isinstance(pred, Quantifier):
            return f"{pred.quantifier_type}({pred.var_def} | {self.print_predicate(pred.body)})"
        elif isinstance(pred, FormulaRef):
            args_str = ", ".join(self.print_expr(a) for a in pred.args)
            return f"{pred.name}({args_str})"
        else:
            return f"<unknown predicate: {type(pred).__name__}>"


class ASTJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (Module, FunctionDef, FormulaDef, VarDef,
                          Statement, Expr, Condition, Predicate, Type, Position)):
            result = {'_type': type(obj).__name__}
            result.update(obj.__dict__)
            return result
        return super().default(obj)


def ast_to_json(module: Module, indent: int = 2) -> str:
    return json.dumps(module, cls=ASTJSONEncoder, indent=indent)


def print_ast(module: Module) -> str:
    printer = ASTPrinter()
    return printer.print_module(module)
