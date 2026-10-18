def hopcroft_minimization(dfa):          
    state_to_int = {}
    int_to_state = {}
    for idx, state in enumerate(dfa.states):
        state_to_int[state] = idx
        int_to_state[idx] = state                                          
                                                              
    token_groups = {}
    non_accepting = set()

    for state in dfa.states:
        if state in dfa.accept_states:
            token = dfa.accept_states[state]
            if token not in token_groups:
                token_groups[token] = set()
            token_groups[token].add(state_to_int[state])
        else:
            non_accepting.add(state_to_int[state])

    partition = []
    if non_accepting:
        partition.append(frozenset(non_accepting))
    for token_group in token_groups.values():
        if token_group:
            partition.append(frozenset(token_group))
                                       
    alphabet = set()
    for (state, symbol) in dfa.transitions.keys():
        alphabet.add(symbol)
                      
    work_list = list(partition)

    while work_list:
        splitter = work_list.pop(0)

        for symbol in alphabet:
                                                               
            transitions_to_splitter = set()
            for state in range(len(state_to_int)):
                orig_state = int_to_state[state]
                if (orig_state, symbol) in dfa.transitions:
                    target = dfa.transitions[(orig_state, symbol)]
                    if state_to_int.get(target) in splitter:
                        transitions_to_splitter.add(state)
  
            new_partition = []
            for group in partition:
                in_split = frozenset(group & transitions_to_splitter)
                out_split = frozenset(group - transitions_to_splitter)

                if in_split and out_split:
                    new_partition.append(in_split)
                    new_partition.append(out_split)
                                      
                    if group in work_list:
                        work_list.remove(group)
                        work_list.append(in_split)
                        work_list.append(out_split)
                    else:
                        if len(in_split) <= len(out_split):
                            work_list.append(in_split)
                        else:
                            work_list.append(out_split)
                else:
                    new_partition.append(group)

            partition = new_partition
                         
    minimized = type(dfa)()
                                     
    state_to_partition = {}
    for idx, group in enumerate(partition):
        for state in group:
            state_to_partition[int_to_state[state]] = idx
                       
    for idx in range(len(partition)):
        minimized.states.add(idx)

                     
    minimized.start_state = state_to_partition[dfa.start_state]
                       
    for state, token in dfa.accept_states.items():
        new_state = state_to_partition[state]
        if new_state not in minimized.accept_states:
            minimized.accept_states[new_state] = token
                    
    if dfa.trap_state:
        minimized.trap_state = state_to_partition.get(dfa.trap_state)
                     
    added_transitions = set()
    for (from_state, symbol), to_state in dfa.transitions.items():
        new_from = state_to_partition[from_state]
        new_to = state_to_partition[to_state]

        if (new_from, symbol) not in added_transitions:
            minimized.add_transition(new_from, new_to, symbol)
            added_transitions.add((new_from, symbol))

    return minimized
