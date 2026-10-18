from regex_parser import RegexParser

class NFA:
    def __init__(self):
        self.states = set()
        self.start_state = None
        self.accept_states = set()
        self.transitions = {}
        self.state_counter = 0

    def new_state(self):
        state = self.state_counter
        self.state_counter += 1
        self.states.add(state)
        return state

    def add_transition(self, from_state, to_state, symbol):
        if from_state not in self.transitions:
            self.transitions[from_state] = {}
        if symbol not in self.transitions[from_state]:
            self.transitions[from_state][symbol] = set()
        self.transitions[from_state][symbol].add(to_state)

class ThompsonNFABuilder:
    def __init__(self):
        pass

    def build(self, regex_ast):
        nfa = NFA()
        start, accept = self._build_recursive(regex_ast, nfa)
        nfa.start_state = start
        nfa.accept_states.add(accept)
        return nfa

    def _build_recursive(self, node, nfa):
        if node.node_type == "CHAR":
            start = nfa.new_state()
            accept = nfa.new_state()
            nfa.add_transition(start, accept, node.value)
            return start, accept

        elif node.node_type == "CHARSET":
            start = nfa.new_state()
            accept = nfa.new_state()
            for char_spec in node.value:
                if char_spec[0] == "CHAR":
                    nfa.add_transition(start, accept, char_spec[1])
                elif char_spec[0] == "RANGE":
                                                 
                    start_char = ord(char_spec[1])
                    end_char = ord(char_spec[2])
                    for code in range(start_char, end_char + 1):
                        nfa.add_transition(start, accept, chr(code))
            return start, accept

        elif node.node_type == "NEGATED_CHARSET":
                                              
            excluded = set()
            for char_spec in node.value:
                if char_spec[0] == "CHAR":
                    excluded.add(char_spec[1])
                elif char_spec[0] == "RANGE":
                    start_char = ord(char_spec[1])
                    end_char = ord(char_spec[2])
                    for code in range(start_char, end_char + 1):
                        excluded.add(chr(code))

                                                                        
            start = nfa.new_state()
            accept = nfa.new_state()
            for code in range(32, 127):                   
                char = chr(code)
                if char not in excluded:
                    nfa.add_transition(start, accept, char)
                          
            if '\t' not in excluded:
                nfa.add_transition(start, accept, '\t')
            return start, accept

        elif node.node_type == "CONCAT":
            left_start, left_accept = self._build_recursive(node.left, nfa)
            right_start, right_accept = self._build_recursive(node.right, nfa)
                                                             
            nfa.add_transition(left_accept, right_start, None)
            return left_start, right_accept

        elif node.node_type == "OR":
            left_start, left_accept = self._build_recursive(node.left, nfa)
            right_start, right_accept = self._build_recursive(node.right, nfa)

            start = nfa.new_state()
            accept = nfa.new_state()

                                                                 
            nfa.add_transition(start, left_start, None)
            nfa.add_transition(start, right_start, None)

                                                                  
            nfa.add_transition(left_accept, accept, None)
            nfa.add_transition(right_accept, accept, None)

            return start, accept

        elif node.node_type == "STAR":
            sub_start, sub_accept = self._build_recursive(node.left, nfa)

            start = nfa.new_state()
            accept = nfa.new_state()

                                                  
            nfa.add_transition(start, sub_start, None)
            nfa.add_transition(sub_accept, sub_start, None)
            nfa.add_transition(start, accept, None)
            nfa.add_transition(sub_accept, accept, None)

            return start, accept

        elif node.node_type == "PLUS":
                                     
            sub_start, sub_accept = self._build_recursive(node.left, nfa)

            start = nfa.new_state()
            accept = nfa.new_state()

                                                 
            nfa.add_transition(start, sub_start, None)
            nfa.add_transition(sub_accept, sub_start, None)
            nfa.add_transition(sub_accept, accept, None)

            return start, accept

        elif node.node_type == "QUESTION":
                               
            sub_start, sub_accept = self._build_recursive(node.left, nfa)

            start = nfa.new_state()
            accept = nfa.new_state()

                                              
            nfa.add_transition(start, sub_start, None)
            nfa.add_transition(sub_accept, accept, None)
            nfa.add_transition(start, accept, None)

            return start, accept

        else:
            raise ValueError(f"Unknown node type: {node.node_type}")

def build_combined_nfa(token_spec):
    combined_nfa = NFA()
    start = combined_nfa.new_state()
    combined_nfa.start_state = start

    builder = ThompsonNFABuilder()

    for token_name, regex_pattern in token_spec:
                     
        parser = RegexParser(regex_pattern)
        ast = parser.parse()
                                  
        token_nfa = builder.build(ast)
                      
        state_mapping = {}
        for state in token_nfa.states:
            state_mapping[state] = combined_nfa.new_state()
                                                                          
        combined_nfa.add_transition(start, state_mapping[token_nfa.start_state], None)

                          
        for from_state, transitions in token_nfa.transitions.items():
            for symbol, to_states in transitions.items():
                for to_state in to_states:
                    combined_nfa.add_transition(
                        state_mapping[from_state],
                        state_mapping[to_state],
                        symbol
                    )

                                           
        for accept_state in token_nfa.accept_states:
            mapped_accept = state_mapping[accept_state]
            combined_nfa.accept_states.add((mapped_accept, token_name))

    return combined_nfa
