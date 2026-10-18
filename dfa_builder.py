class DFA:
    def __init__(self):
        self.states = set()
        self.start_state = None
        self.accept_states = {}                       
        self.transitions = {}                            
        self.trap_state = None

    def add_transition(self, from_state, to_state, symbol):
        self.transitions[(from_state, symbol)] = to_state

def epsilon_closure(nfa, states):
    stack = list(states)
    closure = set(states)

    while stack:
        state = stack.pop()
        if state in nfa.transitions and None in nfa.transitions[state]:
            for next_state in nfa.transitions[state][None]:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)

    return frozenset(closure)

def move(nfa, states, symbol):
    result = set()
    for state in states:
        if state in nfa.transitions and symbol in nfa.transitions[state]:
            result.update(nfa.transitions[state][symbol])
    return result

def get_alphabet(nfa):
    alphabet = set()
    for transitions in nfa.transitions.values():
        for symbol in transitions.keys():
            if symbol is not None:
                alphabet.add(symbol)
    return alphabet

def subset_construction(nfa, token_spec):
    dfa = DFA()
    alphabet = get_alphabet(nfa)

                                                       
    start_closure = epsilon_closure(nfa, {nfa.start_state})
    dfa.start_state = start_closure
    dfa.states.add(start_closure)

                           
    unmarked = [start_closure]
    state_map = {start_closure: start_closure}

                                       
    token_name = get_accepting_token(nfa, start_closure, token_spec)
    if token_name:
        dfa.accept_states[start_closure] = token_name

    while unmarked:
        current = unmarked.pop()

        for symbol in alphabet:
                                              
            next_states = move(nfa, current, symbol)
            if not next_states:
                continue

            next_closure = epsilon_closure(nfa, next_states)

            if next_closure not in dfa.states:
                dfa.states.add(next_closure)
                unmarked.append(next_closure)
                state_map[next_closure] = next_closure

                                                     
                token_name = get_accepting_token(nfa, next_closure, token_spec)
                if token_name:
                    dfa.accept_states[next_closure] = token_name

            dfa.add_transition(current, next_closure, symbol)

    return dfa, alphabet

def get_accepting_token(nfa, state_set, token_spec):
                                           
    accepting_tokens = []

    for state in state_set:
        for accept_state, token_name in nfa.accept_states:
            if state == accept_state:
                accepting_tokens.append(token_name)

    if not accepting_tokens:
        return None

                                                            
    token_priority = {name: idx for idx, (name, _) in enumerate(token_spec)}
    accepting_tokens.sort(key=lambda t: token_priority.get(t, float('inf')))

    return accepting_tokens[0] if accepting_tokens else None

def add_trap_state(dfa, alphabet):
    trap = "TRAP"
    dfa.trap_state = trap
    dfa.states.add(trap)

                                                                  
    for state in list(dfa.states):
        for symbol in alphabet:
            if (state, symbol) not in dfa.transitions:
                dfa.add_transition(state, trap, symbol)

                                         
    for symbol in alphabet:
        dfa.add_transition(trap, trap, symbol)

    return dfa

def complete_dfa_alphabet(dfa, alphabet):
                                                                
    full_alphabet = set()
    for i in range(128):
        full_alphabet.add(chr(i))

                                                            
    trap = "TRAP"
    if trap not in dfa.states:
        dfa.states.add(trap)
        dfa.trap_state = trap

    for state in list(dfa.states):
        for symbol in full_alphabet:
            if (state, symbol) not in dfa.transitions:
                dfa.add_transition(state, trap, symbol)

    return dfa
