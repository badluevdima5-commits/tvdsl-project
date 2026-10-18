# Funny Language Parser (HW02)

Синтаксический анализатор для языка Funny, интегрированный с лексером из HW01.

## Описание

Парсер реализован методом рекурсивного спуска (LL(1) подход) и строит абстрактное синтаксическое дерево (AST) для программ на языке Funny. Поддерживает все конструкции языка согласно спецификации: функции с пред- и постусловиями, формулы, циклы с инвариантами, операторы assert/assume, массивы, кванторы в предикатах.

## Структура проекта

```
lexer-project/
├── lexer.py              # Лексер из HW01
├── token_spec.py         # Спецификация токенов
├── nfa_builder.py        # Построение НКА (HW01)
├── dfa_builder.py        # Построение ДКА (HW01)
├── minimization.py       # Минимизация ДКА (HW01)
├── ast_nodes.py          # Классы узлов AST
├── parser.py             # Рекурсивный спуск парсер
├── ast_printer.py        # Вывод AST (текст и JSON)
├── main.py               # Главный файл
├── test_parser.py        # Тесты парсера
├── examples/             # Примеры программ
│   ├── gcd.funny
│   ├── factorial.funny
│   ├── array_max.funny
│   ├── divmod.funny
│   ├── binary_search.funny
│   ├── error_*.funny     # Негативные примеры
└── README.md
```

## Требования

- Python 3.8+
- pytest (для запуска тестов)

## Установка

```bash
#Установка зависимостей для тестирования
pip install pytest
```

## Использование

### Запуск парсера

```bash
#Парсинг файла с выводом AST в текстовом формате
python3 main.py examples/gcd.funny
#Парсинг файла с выводом AST в JSON формате
python3 main.py examples/factorial.funny --json
#Чтение из stdin
echo "function test() returns x: int { x = 1; }" | python3 main.py --stdin
```

### Запуск тестов

```bash
#Запуск всех тестов
pytest test_parser.py -v
#Запуск конкретного теста
pytest test_parser.py::test_simple_function -v
```

## Грамматика

Парсер реализует следующую грамматику языка Funny (из спецификации `docs/funny.md`):

### Модуль
```
module = {function | formula}
```

### Функции
```
function = "function" IDENT "(" [varDef {"," varDef}] ")"
           ["requires" predicate]
           "returns" varDef {"," varDef}
           ["ensures" predicate]
           ["uses" varDef {"," varDef}]
           statement

varDef = IDENT ":" type
type = "int" | "int[]"
```

### Формулы
```
formula = IDENT "(" [varDef {"," varDef}] ")" "=>" predicate
```

### Операторы
```
statement = assignment
          | "if" "(" condition ")" statement ["else" statement]
          | "while" "(" condition ")" ["invariant" predicate] statement
          | "{" {statement} "}"
          | "assert" condition ";"
          | "assume" condition ";"

assignment = IDENT "=" expr ";"
           | IDENT "[" expr "]" "=" expr ";"
           | IDENT {"," IDENT} "=" functionCall ";"
```

### Выражения
```
expr = additive

additive = multiplicative {("+" | "-") multiplicative}
multiplicative = unary {("*" | "/") unary}
unary = "-" unary | primary
primary = INT | "true" | "false" | IDENT
        | functionCall | arrayAccess | "(" expr ")"

functionCall = IDENT "(" [expr {"," expr}] ")"
arrayAccess = IDENT "[" expr "]"
```

### Условия
```
condition = implication

implication = or ["->" implication]
or = and {"or" and}
and = not {"and" not}
not = ["not"] condPrimary

condPrimary = "true" | "false" | comparison | "(" condition ")"
comparison = expr ("==" | "!=" | "<" | ">" | "<=" | ">=") expr
```

### Предикаты
```
predicate = predImplication

predImplication = predOr ["->" predImplication]
predOr = predAnd {"or" predAnd}
predAnd = predNot {"and" predNot}
predNot = ["not"] predPrimary

predPrimary = "true" | "false" | comparison
            | quantifier | formulaRef | "(" predicate ")"

quantifier = ("forall" | "exists") "(" varDef "|" predicate ")"
formulaRef = IDENT "(" [expr {"," expr}] ")"
```

## Приоритеты операторов

### В арифметических выражениях:
1. Унарный минус `-` 
2. Умножение и деление `*`, `/`
3. Сложение и вычитание `+`, `-`

### В условиях и предикатах:
1. Отрицание `not` 
2. Конъюнкция `and`
3. Дизъюнкция `or`
4. Импликация `->` 

## AST структура

AST представлен классами из `ast_nodes.py`:

- **Module**: корень дерева, содержит списки функций и формул
- **FunctionDef**: определение функции
- **FormulaDef**: определение формулы
- **Statement**: базовый класс для операторов (Assignment, IfStatement, WhileStatement, BlockStatement, Assert, Assume)
- **Expr**: базовый класс для выражений (IntLiteral, VarRef, BinaryOp, FunctionCall, ArrayAccess)
- **Condition**: условные выражения
- **Predicate**: предикаты с кванторами

## Обработка ошибок

Парсер использует режим паники: при обнаружении синтаксической ошибки выдается сообщение с позицией (строка:столбец) и описанием проблемы. Примеры:

```
Parse error: Expected SEMICOLON but got IDENT ('x') at 5:5
Parse error: Unclosed block (expected '}') at 3:1
Parse error: Expected returns but got LBRACE ('{') at 4:1
```

Позиции токенов берутся из лексера (HW01), который отслеживает строки и столбцы.

## Примеры

### Пример 1: Простая функция
```funny
function add(x: int, y: int)
returns sum: int
{
    sum = x + y;
}
```

### Пример 2: Функция с предусловием и циклом
```funny
function factorial(n: int)
requires n >= 0
returns result: int
ensures result >= 1
uses i: int
{
    result = 1;
    i = 1;
    while (i <= n)
    invariant result >= 1 and i >= 1
    {
        result = result * i;
        i = i + 1;
    }
}
```

### Пример 3: Формула и квантор
```funny
sorted(arr: int[], len: int) =>
    forall(i: int | i >= 0 and i < len - 1 -> arr[i] <= arr[i + 1])

function binarySearch(arr: int[], target: int, n: int)
requires sorted(arr, n)
returns index: int
{
    // ... реализация
}
```

## Тесты

Набор тестов в `test_parser.py` включает:

### Позитивные тесты:
- Простые функции
- Функции с пред- и постусловиями
- Функции с локальными переменными
- Множественные возвращаемые значения
- Tuple assignment
- Работа с массивами
- Условные операторы (if/else, вложенные)
- Циклы с инвариантами
- Блоки операторов
- Арифметические выражения
- Булевы условия
- Операторы сравнения
- Вызовы функций
- Кванторы в предикатах
- Определения формул
- Assert/assume операторы
- Правоассоциативность импликации

### Негативные тесты:
- Незакрытые блоки
- Отсутствие точки с запятой
- Отсутствие returns
- Неверные типы
- Неожиданные токены
- Несоответствующие скобки
- Пустой ввод (валиден - пустой модуль)
- Неполные определения функций
- Неверные операторы
- Отсутствие операторов сравнения в условиях

## Особенности реализации

1. **Рекурсивный спуск**: Каждая продукция грамматики представлена методом класса Parser
2. **Обработка приоритетов**: Операторы обрабатываются через цепочку методов (additive → multiplicative → unary → primary)
3. **Правая ассоциативность**: Импликация `->` реализована через рекурсивный вызов
4. **Lookahead**: Используется для различения formula ref и comparison в предикатах
5. **Позиции**: Каждый узел AST содержит информацию о позиции в исходном коде
6. **Ключевые слова**: Обрабатываются лексером, парсер получает уже распознанные токены
