import argparse
import json
import re
import os

def extract_precon(file_path):
    
    i = 0
    best_cex = None
    best_idx = None
    current_cex = None
    second_best_cex = None
    second_best_idx = None
    rules = []

    with open(file_path, 'r') as f:
        lines = f.readlines()

    while i < len(lines):
        line = lines[i]

        if "Found positive counterexample" in line:
            m = re.search(r"a total of (\d+)", line)
            if m:
                current_cex = int(m.group(1))
                if best_cex is None or current_cex < best_cex:
                    if best_cex is not None:
                        second_best_cex = best_cex
                        second_best_idx = best_idx
                    best_cex = current_cex
                    best_idx = i
                elif (second_best_cex is None or current_cex < second_best_cex) and current_cex != best_cex:
                    second_best_cex = current_cex
                    second_best_idx = i
        i += 1

    if second_best_idx is not None:

        if "macro" in lines[best_idx-2]:
            i = best_idx - 1
        else:
            i = second_best_idx - 1

        rules = []
        while not "Found hypothesis" in lines[i]:
            rule_line = lines[i].strip()
            if "macro_" in rule_line:
                clean_rule = rule_line.lstrip("%").strip()
                rules.append(clean_rule)
            i -= 1

    if not rules:
        return ['UNSAT']
    parsed_rules = []
    for rule in rules:
        right = rule.split(":-")[1]
        atoms = [(atom.strip().strip(".")).lower() for atom in right.split(";")]
        parsed_rules.append(atoms)

    return parsed_rules

def rename_macro_variables(macro):
    var_seen = {}
    var_counter = 0
    renamed_macro = []

    for action in macro:
        new_vars = []
        for var in action["variables"]:
            if var not in var_seen:
                var_seen[var] = f"v{var_counter}"
                var_counter += 1
            new_vars.append(var_seen[var])
        new_vars = [f"v{int(v[1:]) + 1}" if v.startswith("v") and v[1:].isdigit() else v for v in new_vars]
        renamed_macro.append({
            "action": action["action"],
            "variables": new_vars
        })

    return renamed_macro

def main():
    parser = argparse.ArgumentParser(description='Remove lines from macro files using regex patterns tied to their first action.')
    parser.add_argument('--folder', required=True, help='Path to domain folder')
        
    args = parser.parse_args()


    with open(os.path.join(args.folder, "selected_3vars.json"), "r") as f:
        macroactions = json.load(f)

    output = []

    for idx, macro in enumerate(macroactions):
        renamed_macro = rename_macro_variables(macro)
        file_path = os.path.join(args.folder, f"ilp_results/macro_{idx}.out")
        if os.path.exists(file_path):
            print(f"Processing file: {file_path}")
            preconds = extract_precon(file_path)
        else:
            print(f"File not found: {file_path}")
            preconds = ['UNSAT']

        if preconds != ['UNSAT']:
            output.append({
                "actions": renamed_macro,
                "preconditions": preconds
            })

    with open(os.path.join(args.folder,"extracted_precon.json"), "w") as f:
        json.dump(output, f, indent=4)


if __name__ == "__main__":
    main()
