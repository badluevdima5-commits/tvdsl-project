import json
from token_spec import TOKEN_SPEC, SKIP_TOKENS
from nfa_builder import build_combined_nfa
from dfa_builder import subset_construction, complete_dfa_alphabet
from minimization import hopcroft_minimization


class Lexer:
    def __init__(self, dfa, skip_tokens):
        self.dfa = dfa
        self.skip_tokens = skip_tokens
                                                   
        self.keywords = {
            'FUNCTION', 'RETURNS', 'REQUIRES', 'ENSURES', 'USES',
            'IF', 'ELSE', 'WHILE', 'INVARIANT',
            'ASSERT', 'ASSUME', 'FORALL', 'EXISTS',
            'TRUE', 'FALSE', 'AND', 'OR', 'NOT', 'LENGTH'
        }

    def _is_keyword(self, token_type):
        return token_type in self.keywords

    def tokenize(self, input_string):
        tokens = []
        pos = 0
        line = 1
        column = 1

        while pos < len(input_string):
                                                              
            state = self.dfa.start_state
            last_accept_pos = None
            last_accept_token = None
            current_pos = pos

            while current_pos < len(input_string):
                char = input_string[current_pos]

                                               
                if (state, char) in self.dfa.transitions:
                    state = self.dfa.transitions[(state, char)]
                    current_pos += 1

                                                         
                    if state in self.dfa.accept_states:
                        token_type = self.dfa.accept_states[state]

                                                           
                        if self._is_keyword(token_type):
                                                                             
                            if current_pos < len(input_string):
                                next_char = input_string[current_pos]
                                if next_char.isalnum() or next_char == '_':
                                                                                           
                                                                      
                                    pass
                                else:
                                                            
                                    last_accept_pos = current_pos
                                    last_accept_token = token_type
                            else:
                                                               
                                last_accept_pos = current_pos
                                last_accept_token = token_type
                        else:
                                                            
                            last_accept_pos = current_pos
                            last_accept_token = token_type
                else:
                    break

                                 
            if last_accept_pos is not None:
                lexeme = input_string[pos:last_accept_pos]

                                                    
                if last_accept_token not in self.skip_tokens:
                    tokens.append({
                        'type': last_accept_token,
                        'value': lexeme,
                        'line': line,
                        'column': column
                    })

                                 
                for char in lexeme:
                    if char == '\n':
                        line += 1
                        column = 1
                    else:
                        column += 1

                pos = last_accept_pos
            else:
                                  
                char = input_string[pos]
                raise ValueError(
                    f"Unexpected character '{char}' at line {line}, column {column}"
                )

        return tokens


def build_lexer():
    nfa = build_combined_nfa(TOKEN_SPEC)
    print(f"  NFA has {len(nfa.states)} states")

    dfa, alphabet = subset_construction(nfa, TOKEN_SPEC)
    print(f"  DFA has {len(dfa.states)} states")

    dfa = complete_dfa_alphabet(dfa, alphabet)
    print(f"  DFA with trap has {len(dfa.states)} states")

    minimized_dfa = hopcroft_minimization(dfa)
    print(f"  Minimized DFA has {len(minimized_dfa.states)} states")

    return Lexer(minimized_dfa, SKIP_TOKENS), len(dfa.states), len(minimized_dfa.states)

def serialize_dfa(dfa, filename):
    serialized = {
        'start_state': str(dfa.start_state),
        'accept_states': {str(k): v for k, v in dfa.accept_states.items()},
        'trap_state': str(dfa.trap_state) if dfa.trap_state else None,
        'transitions': [
            {
                'from': str(from_state),
                'to': str(to_state),
                'symbol': symbol
            }
            for (from_state, symbol), to_state in dfa.transitions.items()
        ]
    }

    with open(filename, 'w') as f:
        json.dump(serialized, f, indent=2)

    print(f"DFA serialized to {filename}")


def main():
    lexer, dfa_size, minimized_size = build_lexer()

    print("LEXER BUILD SUMMARY")
    print("="*60)
    print(f"Token specifications: {len(TOKEN_SPEC)}")
    print(f"DFA size before minimization: {dfa_size} states")
    print(f"DFA size after minimization: {minimized_size} states")
    print(f"Reduction: {dfa_size - minimized_size} states ({100*(dfa_size-minimized_size)/dfa_size:.1f}%)")
    print(f"Skip tokens: {SKIP_TOKENS}")

                                 
    serialize_dfa(lexer.dfa, 'dfa_table.json')

                                
    test_input = "function add(x: int, y: int) returns sum: int { sum = x + y; }"
    print(f"\nTest input: {test_input}")

    try:
        tokens = lexer.tokenize(test_input)
        print("\nTokens:")
        for token in tokens:
            print(f"  {token['type']:15} {token['value']}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
