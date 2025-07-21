import os
import re
import argparse

REGEX_FILE = 'refinement.txt'
SUBFOLDER_NAME = 'ilp_tasks'  
ENCODING = 'utf-8'

def load_patterns(regex_file):
    removal_patterns = []
    substitution_patterns = []
    with open(regex_file, 'r', encoding=ENCODING) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=>' in line:
                pattern, replacement = map(str.strip, line.split('=>', 1))
                substitution_patterns.append((re.compile(pattern), replacement))
            else:
                removal_patterns.append(re.compile(line))
    return removal_patterns, substitution_patterns

def clean_line(line, removal_patterns, substitution_patterns):
    for pattern in removal_patterns:
        line = pattern.sub('', line)
    for pattern, repl in substitution_patterns:
        line = pattern.sub(repl, line)
    return line

def process_file(file_path, removal_patterns, substitution_patterns):
    with open(file_path, 'r', encoding=ENCODING) as f:
        lines = f.readlines()

    cleaned_lines = []
    for line in lines:
        cleaned = clean_line(line, removal_patterns, substitution_patterns)
        if '{}).' in cleaned:
            continue  
        cleaned_lines.append(cleaned)

    with open(file_path, 'w', encoding=ENCODING) as f:
        f.writelines(cleaned_lines)

def main():
    parser = argparse.ArgumentParser(description='Postprocess ILP task files by removing specific patterns.')
    parser.add_argument('--folder', type=str, required=True, help='Path to the domain folder.')
    args = parser.parse_args()

    ilp_tasks_path = os.path.join(args.folder, SUBFOLDER_NAME)

    if not os.path.isdir(ilp_tasks_path):
        print(f"Error: '{ilp_tasks_path}' doesn't exist or is not a directory.")
        return

    removal_patterns, substitition_patterns = load_patterns(os.path.join(args.folder, REGEX_FILE))

    for filename in os.listdir(ilp_tasks_path):
        if filename.endswith('.las'):
            file_path = os.path.join(ilp_tasks_path, filename)
            print(f"Processing file {file_path}")
            process_file(file_path, removal_patterns, substitition_patterns)

    print("Postprocessing complete.")

if __name__ == '__main__':
    main()
