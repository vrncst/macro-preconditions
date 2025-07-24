import json

file_path = '/home/celeste/macro_preconditions/macro-preconditions/macroactions_data/kitting/database_plans.json'

def count_sequential_actions(plans, action_name, target_length):
    plans_with_target_seq = []
    for plan in plans:
        count = 0    
        trace = plan['trace']
        for step in trace:
            if step['action'] != 'null':
                if step['action']['name'] == action_name:
                    count += 1
                    if count == target_length:
                        plans_with_target_seq.append(plan)
                else:
                    count = 0
            else:
                count = 0
    print(f"Plans with sequential '{action_name}' actions of length {target_length}: {len(plans_with_target_seq)}")
    for idx, plan in enumerate(plans_with_target_seq):
        print(f"\nPlan #{idx+1}:")
        print(json.dumps(plan, indent=2))
    return len(plans_with_target_seq)

with open(file_path, 'r') as f:
    data = json.load(f)['dataset']

# Print all plans where there are 4 sequential 'prepare_unload' actions
count_sequential_actions(data, 'prepare_unload', 4)
