class RegexNode:
    def __init__(self, node_type, value=None, left=None, right=None):
        self.node_type = node_type
        self.value = value
        self.left = left
        self.right = right

class RegexParser:
    def __init__(self, regex):
        self.regex = regex
        self.pos = 0

    def peek(self):
        if self.pos >= len(self.regex):
            return None
        return self.regex[self.pos]
    
    def consume(self):
        if self.pos >= len(self.regex):
            return None
        s = self.regex[self.pos]
        self.pos += 1
        return s

    def parse_atom(self):
        char = self.peek()

        if char is None:
            raise ValueError("Unexpected end of regex")

        if char == '(':
            self.consume()
            node = self.parse_expression()
            if self.peek() != ')':
                raise ValueError("Expected ')'")
            self.consume()
            return node
        if char == '[':
            return self.parse_character_class()

        if char == '\\':
            self.consume()
            s = self.consume()
            if s is None:
                raise ValueError("Incomplete escape sequence")
            return RegexNode("CHAR", s)
        
        self.consume()
        return RegexNode("CHAR", char)
    def parse_character_class(self):
        self.consume()
        characters = []
        negated = False

                            
        if self.peek() == '^':
            negated = True
            self.consume()

        while True:
            char = self.peek()
            if char == None:
                raise ValueError("Unclosed character class")
            if char == ']':
                self.consume()
                break

                                     
            if char == '\\':
                self.consume()
                escaped = self.consume()
                if escaped is None:
                    raise ValueError("Incomplete escape sequence in character class")

                                                               
                escape_map = {
                    't': '\t',
                    'n': '\n',
                    'r': '\r',
                    '\\': '\\',
                    '[': '[',
                    ']': ']',
                    '-': '-'
                }
                start = escape_map.get(escaped, escaped)
            else:
                start = self.consume()

            if self.peek() == '-' and self.peek() != ']':
                self.consume()               

                                            
                if self.peek() == '\\':
                    self.consume()
                    escaped = self.consume()
                    if escaped is None:
                        raise ValueError("Incomplete escape sequence in character class")
                    escape_map = {
                        't': '\t',
                        'n': '\n',
                        'r': '\r',
                        '\\': '\\',
                        '[': '[',
                        ']': ']',
                        '-': '-'
                    }
                    end = escape_map.get(escaped, escaped)
                else:
                    end = self.consume()

                if end is None:
                    raise ValueError("Incorrect character range")
                characters.append(("RANGE", start, end))
            else:
                characters.append(("CHAR", start))

        if negated:
            return RegexNode("NEGATED_CHARSET", characters)
        return RegexNode("CHARSET", characters)
    
    def parse_expression(self):
        node = self.parse_concatenation()

        while self.peek() == '|':
            self.consume()
            right = self.parse_concatenation()

            node = RegexNode(
                "OR",
                left=node,
                right=right
            )
        return node
    
    def starts_atom(self):
        char = self.peek()
        if char is None:
            return False

        if char in '|)*+?':
            return False
        return True
    
    def parse_concatenation(self):
        node = self.parse_repetition()

        while self.starts_atom():
            right = self.parse_repetition()
            node = RegexNode(
                "CONCAT",
                left=node,
                right=right
            )
        return node

    def parse_repetition(self):
        node = self.parse_atom()

        if self.peek() == '*':
            self.consume()
            node = RegexNode("STAR", left = node)
        elif self.peek() == '+':
            self.consume()
            node = RegexNode("PLUS", left = node)
        elif self.peek() == '?':
            self.consume()
            node = RegexNode("QUESTION", left=node)
        return node
    
    def parse(self):
        node = self.parse_expression()

        if self.peek() is not None:
            raise ValueError(f"Unexpected character: {self.peek()}")
        return node
        