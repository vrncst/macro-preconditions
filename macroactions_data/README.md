# Synthesis of preconditions for Macro-Events

1. **database_macros.json** is a list of lifted macro-events. Each macro-event is a list of dictionaries where each dict is a lifted action: by replacing each variable with an object from the problem, one can generate its corresponding ground actions. For example, the macro with arity 3 *<load_at_depot(v1,v2), move(v1,v0)>* corresponds to
```python
[
    {
        "action": "load_at_depot",
        "variables": [
            "v1",
            "v2"
        ]
    },
    {
        "action": "move",
        "variables": [
            "v1",
            "v0"
        ]
    }
]
```



2. **database_plans.json** is a dictionary with keys *domain* and *dataset*. 
The *domain* key maps to a representation of the domain’s fluents and actions
```python
"domain": {
    "fluents": [
        {
            "predicate": "robot_at",
            "arg_types": [
                "Robot"
            ]
        },
        {
            "predicate": "robot_has",
            "arg_types": [
                "Robot"
            ]
        },
        ...
    ],
    "actions": [
        {
            "name": "move",
            "arg_types": [
                "Robot",
                "Position"
            ],
            "num_events": 2
        },
        {
            "name": "load_at_depot",
            "arg_types": [
                "Robot",
                "Pallet"
            ],
            "num_events": 1
        },
        ...
    ]
}
```
The *dataset* is a list of valid plans for that domain. In particular, it is a list of dictionaries that contains the objects of the problem instance (*problem_objects*), organized by type, and *trace* that maps to the actual execution trace, that is, a list of ground actions (or null for the initial state) and the corresponding states reached after applying each action. For example,
```python
"dataset": [
        {
            "problem_objects": {
                "Position": [
                    "UNKNOWN",
                    "DEPOT",
                    "p0"
                ],
                "Robot": [
                    "r0"
                ],
                ...
            },
            "trace": [
                {
                    "action": "null",
                    "state": [
                        {
                            "fluent": "robot_at",
                            "args": [
                                "r0"
                            ],
                            "value": "DEPOT"
                        },
                        {
                            "fluent": "robot_has",
                            "args": [
                                "r0"
                            ],
                            "value": "NOPALLET"
                        },
                        ...
                    ]
                },
                {
                    "action": {
                        "name": "load_at_depot",
                        "params": [
                            "r0",
                            "b0"
                        ],
                        "event": 0
                    },
                    "state": [
                        {
                            "fluent": "robot_at",
                            "args": [
                                "r0"
                            ],
                            "value": "DEPOT"
                        },
                        ...
                    ]
                },
                ...
            ]
        },
        ...
]
```

Each action is associated with a certain number of events (such as START, END, conditions, or effects that may occur during its execution). For this reason, the domain representation specifies, for each action, the number of associated events; accordingly, in the trace, each action occurrence is annotated with the specific event it corresponds to (starting from 0).