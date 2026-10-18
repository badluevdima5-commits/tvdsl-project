from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class Position:
    line: int
    column: int

    def __str__(self):
        return f"{self.line}:{self.column}"

@dataclass
class Type:
    pass

@dataclass
class IntType(Type):
    def __str__(self):
        return "int"

@dataclass
class IntArrayType(Type):
    def __str__(self):
        return "int[]"

@dataclass
class VarDef:
    name: str
    var_type: Type
    pos: Position

    def __str__(self):
        return f"{self.name}: {self.var_type}"

@dataclass
class Expr:
    pos: Position


@dataclass
class IntLiteral(Expr):
    value: int


@dataclass
class BoolLiteral(Expr):
    value: bool


@dataclass
class VarRef(Expr):
    name: str


@dataclass
class UnaryOp(Expr):
    op: str
    operand: Expr


@dataclass
class BinaryOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class FunctionCall(Expr):
    name: str
    args: List[Expr]


@dataclass
class ArrayAccess(Expr):
    array: str
    index: Expr

@dataclass
class Condition:
    pos: Position


@dataclass
class BoolConst(Condition):
    value: bool


@dataclass
class Comparison(Condition):
    op: str
    left: Expr
    right: Expr


@dataclass
class NotCond(Condition):
    operand: Condition


@dataclass
class BinaryLogical(Condition):
    op: str
    left: Condition
    right: Condition

@dataclass
class Predicate:
    pos: Position


@dataclass
class PredicateBoolConst(Predicate):
    value: bool


@dataclass
class PredicateComparison(Predicate):
    op: str
    left: Expr
    right: Expr


@dataclass
class PredicateNot(Predicate):
    operand: Predicate


@dataclass
class PredicateBinary(Predicate):
    op: str
    left: Predicate
    right: Predicate


@dataclass
class Quantifier(Predicate):
    quantifier_type: str
    var_def: VarDef
    body: Predicate


@dataclass
class FormulaRef(Predicate):
    name: str
    args: List[Expr]

@dataclass
class Statement:
    pos: Position


@dataclass
class Assignment(Statement):
    var_name: str
    value: Expr


@dataclass
class ArrayUpdate(Statement):
    array_name: str
    index: Expr
    value: Expr


@dataclass
class TupleAssignment(Statement):
    var_names: List[str]
    call: FunctionCall


@dataclass
class IfStatement(Statement):
    condition: Condition
    then_stmt: Statement
    else_stmt: Optional[Statement]


@dataclass
class WhileStatement(Statement):
    condition: Condition
    invariant: Optional[Predicate]
    body: Statement


@dataclass
class BlockStatement(Statement):
    statements: List[Statement]


@dataclass
class AssertStatement(Statement):
    condition: Condition


@dataclass
class AssumeStatement(Statement):
    condition: Condition

@dataclass
class FunctionDef:
    name: str
    params: List[VarDef]
    returns: List[VarDef]
    requires: Optional[Predicate]
    ensures: Optional[Predicate]
    uses: List[VarDef]
    body: Statement
    pos: Position


@dataclass
class FormulaDef:
    name: str
    params: List[VarDef]
    body: Predicate
    pos: Position

@dataclass
class Module:
    functions: List[FunctionDef]
    formulas: List[FormulaDef]
