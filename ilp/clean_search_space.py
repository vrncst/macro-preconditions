import os
import re
import json
import argparse

ENCODING = 'utf-8'

def load_macroactions(json_path):
    with open(json_path, 'r', encoding=ENCODING) as f:
        return json.load(f)

def load_pattern_dict(txt_path):
    pattern_dict = {}
    current_action = None

    with open(txt_path, 'r', encoding=ENCODING) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('[') and line.endswith(']'):
                current_action = line[1:-1].strip()
                pattern_dict[current_action] = []
            elif current_action:
                pattern_dict[current_action].append(re.compile(line))
            else:
                raise ValueError(f"Pattern found outside of any [action]: {line}")
    return pattern_dict

def should_remove_line(line, compiled_patterns):
    return any(p.search(line) for p in compiled_patterns)

def process_file(file_path, patterns):
    with open(file_path, 'r', encoding=ENCODING) as f:
        lines = f.readlines()

    cleaned = [line for line in lines if not should_remove_line(line, patterns)]

    #TODO auto append search space to files
    with open(file_path, 'w', encoding=ENCODING) as f:
        f.writelines(cleaned)

def main():
    parser = argparse.ArgumentParser(description='Remove lines from macro files using regex patterns tied to their first action.')
    parser.add_argument('--folder', required=True, help='Path to domain folder')
    
    args = parser.parse_args()

    macroactions = load_macroactions(os.path.join(args.folder, "selected_3vars.json"))
    pattern_dict = load_pattern_dict(os.path.join(args.folder, "precon_filtering.txt"))

    for i, macro in enumerate(macroactions):
        if not macro:
            print(f"Macro {i} is empty. Skipping.")
            continue

        first_action = macro[0]['action']
        patterns = pattern_dict.get(first_action)

        if not patterns:
            print(f"No patterns found for action '{first_action}' in macro {i}. Skipping.")
            continue

        file_name = f"macro_{i}.las"
        file_path = os.path.join(args.folder, f"ilp_tasks/{file_name}")

        if not os.path.isfile(file_path):
            print(f"File {file_path} not found. Skipping.")
            continue

        print(f"Processing {file_name} using patterns for action '{first_action}'")
        process_file(file_path, patterns)

    print("Processing complete.")

if __name__ == '__main__':
    main()
