import sys
import os
import json
import pickle

def is_macro_prefix(macro_a, macro_b):
    for step_a, step_b in zip(macro_a, macro_b):
        if step_a['action'] != step_b['action']:
            return False
    return True

def format_contexts(examples):
    formatted_examples = []
    #TODO filter duplicates?
    for _, example in enumerate(examples, 1):
        state = example['state']
        params = example['params']
        param_str = ','.join(str(p) for p in params)
        fluents = []
        for entry in state:
            fluent = entry['fluent']
            args = entry['args'][:]
            if not isinstance(entry['value'], bool):
                args.append(str(entry['value']))
            if args:
                prefix = 'not_' if entry['value'] == False else ''
                fluent_str = f"{prefix}{fluent}({','.join(args)})."
                print(fluent_str)
            else:
                fluent_str = f"{fluent}."
            fluents.append(fluent_str)
        context_str = ' '.join(fluents)
        example = {'context': context_str, 'params': param_str}
        formatted_examples.append(example)
    return formatted_examples

def generate_examples(macro, plans):
    inc_examples_list = []
    exc_examples_list = []
    macro_action_names = []
    macro_variables = []
    _objects = {}
    for step in macro:
         macro_action_names.append(step['action'])
         macro_variables.append(v for v in step['variables'])
    unique_macro_variables = list(dict.fromkeys(v for sub in macro_variables for v in sub))
    macro_len = len(macro_action_names)
    for plan in plans:
        problem_objects = plan['problem_objects']
        trace = plan['trace'] 
        for key, obj in problem_objects.items():
            if key not in _objects:
                _objects[key] = set()
            _objects[key].update(obj)
        actions = [entry['action']['name'] if entry['action'] != 'null' else None for entry in trace]
        i=0
        while i < len(actions) - macro_len + 1:
            state_before_macro = trace[i - 1]['state']
            if actions[i:i + macro_len] == macro_action_names:
                macro_params = [trace[i + j]['action']['params'] for j in range(macro_len)]
                unique_macro_params = list(dict.fromkeys(p for sub in macro_params for p in sub))
                inc_examples_list.append({
                    "state": state_before_macro,
                    "params": unique_macro_params
                })
                i += macro_len - 1 # we're skipping intermediate states to avoid adding them as negative examples, not sure it's what we want
            else:
                exc_examples_list.append({
                    "state": state_before_macro,
                    "params": ['_' for _ in range(len(unique_macro_variables))]
                })
                i += 1
    objects = {key: list(values) for key, values in _objects.items()}
    inc_contexts = format_contexts(inc_examples_list)
    exc_contexts = format_contexts(exc_examples_list)
    return objects, inc_contexts, exc_contexts

def generate_background(objects):
    items = [f"{key.lower()}({item})." for key, items in objects.items() for item in items]
    bk = "\n".join(items)
    return bk

def generate_modeh(macro_name, macro, domain_actions):
    action_to_types = {action['name']: action['arg_types'] for action in domain_actions}
    
    seen_vars = {}
    for step in macro:
        action = step['action']
        variables = step['variables']
        arg_types = action_to_types.get(action, [])
        for i, var in enumerate(variables):
            if var not in seen_vars:
                t = arg_types[i] if i < len(arg_types) else arg_types[-1]
                seen_vars[var] = t.lower()

    args_str = ",".join(f"var({t})" for t in seen_vars.values())
    modeh_line = f"#modeh({macro_name}({args_str})).\n\n"
    return modeh_line

def format_examples(macro_name, inc_contexts, exc_contexts):
    inc_examples, exc_examples = [], []
    for idx, context in enumerate(inc_contexts):
        context_str = context['context']
        params_str = context['params']
        example = f"#pos(ex{idx}, {{{macro_name}({params_str})}}, {{}}, {{{context_str}}})."
        inc_examples.append(example)
    for idx, context in enumerate(exc_contexts):
        context_str = context['context']
        params_str = context['params']
        example = f"#pos(ex{len(inc_contexts)+idx}, {{}}, {{{macro_name}({params_str})}}, {{{context_str}}})."
        exc_examples.append(example)
    return inc_examples, exc_examples

def parse_data():
    if len(sys.argv) != 2:
        print("Usage: python task_generator.py <path_to_domain_folder>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isdir(file_path):
        print(f"Error: Directory '{file_path}' does not exist.")
        sys.exit(1)
    try:
        with open(os.path.join(file_path, 'selected_3vars.json'), 'r') as f:
            # list of macros, each macro is a list of <action, variables> dicts
            macros = json.load(f)             
    except json.JSONDecodeError as e:
        print(f"Error parsing macros JSON: {e}")
        sys.exit(1)
    try:
        with open(os.path.join(file_path, 'database_plans.json'), 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing plans JSON: {e}")
        sys.exit(1)
    domain = data['domain'] # dict containing fluents and actions
    plans = data['dataset'] # list of dicts, each contains problem_objects and trace,
                            # each trace is a list of <action, state> dicts
    return domain, macros, plans

def generate_macro_dataset(macros, plans):
    ilp_tasks_dir = os.path.join(sys.argv[1], "ilp_tasks")
    os.makedirs(ilp_tasks_dir, exist_ok=True)
    with open(os.path.join(sys.argv[1], "modebias.txt"), "r") as modeb_file:
        modebias = modeb_file.read().strip()
    if not modebias:
        print("Error: modebias.txt is empty or not found.")
        sys.exit(1)
    macro_tasks = {}
    for i, macro in enumerate(macros):
        macro_name = f"macro_{i}"
        objects, inc_contexts, exc_contexts = generate_examples(macro, plans)   
        macro_tasks.setdefault(macro_name, {})
        macro_tasks[macro_name]['lifted_actions'] = macro  
        inc, exc = format_examples(macro_name, inc_contexts, exc_contexts)      
        macro_tasks[macro_name]['inc_examples'] = inc
        macro_tasks[macro_name]['exc_examples'] = exc
        macro_tasks[macro_name]['background'] = generate_background(objects)
        bias = generate_modeh(macro_name, macro, domain['actions']) + modebias
        macro_tasks[macro_name]['bias'] = bias
    pickle_path = os.path.join(ilp_tasks_dir, "ilp_tasks.pkl")
    with open(pickle_path, "wb") as pf:
        pickle.dump(macro_tasks, pf)
    print(f"Macro dataset generated and saved to {pickle_path}")
    return macro_tasks
    
if __name__ == "__main__":
    domain, macros, plans = parse_data()
    macro_data = generate_macro_dataset(macros, plans)
    for macro_name, data in macro_data.items():
        task_file_path = os.path.join(sys.argv[1], "ilp_tasks", f"{macro_name}.las")
        with open(task_file_path, "w") as task_file:
            task_file.write(data['background'] + "\n")
            task_file.write("\n\n")
            for e in data['inc_examples']:
                task_file.write(e + "\n")
            for e in data['exc_examples']:
                task_file.write(e + "\n")
            task_file.write("\n\n\n")
            task_file.write(data['bias'] + "\n")
    print(f"ILP tasks generated and saved to {os.path.join(sys.argv[1], 'ilp_tasks')}")
