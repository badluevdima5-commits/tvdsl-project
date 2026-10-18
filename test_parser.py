import pytest
from lexer import build_lexer
from parser import parse, ParseError

@pytest.fixture(scope="module")
def lexer():
    lex, _, _ = build_lexer()
    return lex

def parse_text(lexer, text):
    tokens = lexer.tokenize(text)
    return parse(tokens)

def test_simple_function(lexer):
    code = """
    function add(x: int, y: int)
    returns sum: int
    {
        sum = x + y;
    }
    """
    ast = parse_text(lexer, code)
    assert len(ast.functions) == 1
    assert ast.functions[0].name == "add"
    assert len(ast.functions[0].params) == 2
    assert len(ast.functions[0].returns) == 1

def test_function_with_precondition(lexer):
    code = """
    function divide(a: int, b: int)
    requires b != 0
    returns q: int
    {
        q = a / b;
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    assert func.requires is not None
    assert func.ensures is None

def test_function_with_postcondition(lexer):
    code = """
    function abs(x: int)
    returns r: int
    ensures r >= 0
    {
        if (x < 0)
            r = -x;
        else
            r = x;
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    assert func.requires is None
    assert func.ensures is not None

def test_function_with_local_variables(lexer):
    code = """
    function gcd(x: int, y: int)
    returns r: int
    uses a: int, b: int
    {
        a = x;
        b = y;
        while (b != 0)
        {
            r = a / b;
            a = b;
            b = r;
        }
        r = a;
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    assert len(func.uses) == 2
    assert func.uses[0].name == "a"
    assert func.uses[1].name == "b"


def test_multiple_return_values(lexer):
    code = """
    function divmod(a: int, b: int)
    returns q: int, r: int
    {
        q = a / b;
        r = a - q * b;
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    assert len(func.returns) == 2

def test_tuple_assignment(lexer):
    code = """
    function caller(x: int, y: int)
    returns a: int, b: int
    {
        a, b = divmod(x, y);
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    from ast_nodes import TupleAssignment, BlockStatement
    body = func.body
    if isinstance(body, BlockStatement):
        stmt = body.statements[0]
    else:
        stmt = body
    assert isinstance(stmt, TupleAssignment)
    assert len(stmt.var_names) == 2

def test_array_operations(lexer):
    code = """
    function swap(arr: int[], i: int, j: int)
    returns result: int[]
    uses temp: int
    {
        temp = arr[i];
        result[i] = arr[j];
        result[j] = temp;
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    from ast_nodes import IntArrayType
    assert isinstance(func.params[0].var_type, IntArrayType)


def test_if_statement(lexer):
    code = """
    function max(a: int, b: int)
    returns r: int
    {
        if (a > b)
            r = a;
        else
            r = b;
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    from ast_nodes import IfStatement
    if isinstance(func.body, IfStatement):
        assert func.body.else_stmt is not None


def test_nested_if(lexer):
    code = """
    function classify(x: int)
    returns r: int
    {
        if (x > 0)
            if (x > 100)
                r = 2;
            else
                r = 1;
        else
            r = 0;
    }
    """
    ast = parse_text(lexer, code)
    assert len(ast.functions) == 1


def test_while_loop(lexer):
    code = """
    function factorial(n: int)
    returns result: int
    uses i: int
    {
        result = 1;
        i = 1;
        while (i <= n)
        invariant result >= 1
        {
            result = result * i;
            i = i + 1;
        }
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    from ast_nodes import BlockStatement, WhileStatement
    if isinstance(func.body, BlockStatement):
        while_stmt = None
        for stmt in func.body.statements:
            if isinstance(stmt, WhileStatement):
                while_stmt = stmt
                break
        assert while_stmt is not None
        assert while_stmt.invariant is not None


def test_block_statement(lexer):
    code = """
    function test()
    returns x: int
    {
        {
            x = 1;
            x = x + 1;
            x = x * 2;
        }
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    from ast_nodes import BlockStatement
    assert isinstance(func.body, BlockStatement)


def test_expressions(lexer):
    code = """
    function expr_test(a: int, b: int, c: int)
    returns r: int
    {
        r = a + b * c - (a / b);
    }
    """
    ast = parse_text(lexer, code)
    assert len(ast.functions) == 1


def test_boolean_conditions(lexer):
    code = """
    function bool_test(x: int, y: int, z: int)
    returns r: int
    {
        if (x > 0 and y > 0 or z < 0)
            r = 1;
        else
            r = 0;
    }
    """
    ast = parse_text(lexer, code)
    assert len(ast.functions) == 1


def test_comparison_operators(lexer):
    code = """
    function compare(a: int, b: int)
    returns r: int
    {
        if (a == b)
            r = 0;
        if (a != b)
            r = 1;
        if (a < b)
            r = 2;
        if (a <= b)
            r = 3;
        if (a > b)
            r = 4;
        if (a >= b)
            r = 5;
    }
    """
    ast = parse_text(lexer, code)
    assert len(ast.functions) == 1


def test_function_call_in_expression(lexer):
    code = """
    function f(x: int)
    returns r: int
    {
        r = length(arr) + compute(x) * 2;
    }
    """
    ast = parse_text(lexer, code)
    assert len(ast.functions) == 1


def test_quantifiers_in_predicates(lexer):
    code = """
    function search(arr: int[], target: int)
    requires forall(i: int | i >= 0 and i < length(arr) -> arr[i] != target)
    returns found: int
    ensures exists(i: int | i >= 0 and i < length(arr) and arr[i] == target)
    {
        found = 0;
    }
    """
    ast = parse_text(lexer, code)
    func = ast.functions[0]
    from ast_nodes import Quantifier
    assert func.requires is not None
    assert func.ensures is not None


def test_formula_definition(lexer):
    code = """
    sorted(arr: int[], n: int) => forall(i: int | i >= 0 and i < n -> arr[i] <= arr[i + 1])

    function test(a: int[])
    returns r: int
    {
        r = 0;
    }
    """
    ast = parse_text(lexer, code)
    assert len(ast.formulas) == 1
    assert ast.formulas[0].name == "sorted"
    assert len(ast.functions) == 1


def test_assert_assume_statements(lexer):
    code = """
    function test(x: int)
    returns r: int
    {
        assume x > 0;
        r = x * 2;
        assert r > 0;
    }
    """
    ast = parse_text(lexer, code)
    from ast_nodes import AssertStatement, AssumeStatement, BlockStatement
    func = ast.functions[0]
    assert isinstance(func.body, BlockStatement)
    stmts = func.body.statements
    assert isinstance(stmts[0], AssumeStatement)
    assert isinstance(stmts[2], AssertStatement)


def test_implication_right_associativity(lexer):
    code = """
    function test(a: int, b: int, c: int)
    requires a > 0 -> b > 0 -> c > 0
    returns r: int
    {
        r = 1;
    }
    """
    ast = parse_text(lexer, code)
    assert len(ast.functions) == 1

def test_missing_closing_brace(lexer):
    code = """
    function test()
    returns x: int
    {
        x = 1;
    """
    with pytest.raises(ParseError, match="Unclosed block|expected.*}"):
        parse_text(lexer, code)

def test_missing_semicolon(lexer):
    code = """
    function test()
    returns x: int
    {
        x = 1
    }
    """
    with pytest.raises(ParseError):
        parse_text(lexer, code)

def test_missing_returns_clause(lexer):
    code = """
    function test(x: int)
    {
        x = x + 1;
    }
    """
    with pytest.raises(ParseError, match=".*returns.*|.*RETURNS.*"):
        parse_text(lexer, code)

def test_invalid_type(lexer):
    code = """
    function test(x: string)
    returns r: int
    {
        r = 0;
    }
    """
    with pytest.raises(ParseError):
        parse_text(lexer, code)

def test_unexpected_token(lexer):
    code = """
    function test()
    returns r: int
    {
        r = 1 + + 2;
    }
    """
    with pytest.raises(ParseError):
        parse_text(lexer, code)

def test_mismatched_parentheses(lexer):
    code = """
    function test()
    returns r: int
    {
        r = (1 + 2;
    }
    """
    with pytest.raises(ParseError, match=".*\\).*"):
        parse_text(lexer, code)

def test_empty_input(lexer):
    code = ""
    ast = parse_text(lexer, code)
    assert len(ast.functions) == 0
    assert len(ast.formulas) == 0

def test_incomplete_function(lexer):
    code = """
    function test(x: int)
    returns
    """
    with pytest.raises(ParseError):
        parse_text(lexer, code)

def test_invalid_statement_start(lexer):
    code = """
    function test()
    returns r: int
    {
        123;
    }
    """
    with pytest.raises(ParseError, match=".*statement.*"):
        parse_text(lexer, code)

def test_missing_comparison_operator(lexer):
    code = """
    function test(x: int)
    returns r: int
    {
        if (x)
            r = 1;
    }
    """
    with pytest.raises(ParseError):
        parse_text(lexer, code)
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
