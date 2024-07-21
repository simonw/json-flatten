from json_flatten import flatten, unflatten

print(flatten({}))

print(flatten({"hi": "str", "woo": "str"}))

print(flatten({"hi": {"woo": "str"}}))

print(unflatten({"hi.woo": "str"}))

print(flatten({"a": 1, "b": 2, "c": [{"d": [2, 3, 4], "e": [{"f": 1, "g": 2}]}]}))
print(
    unflatten(
        {
            "a": 1,
            "b": 2,
            "c.[0].d.[0]": 2,
            "c.[0].d.[1]": 3,
            "c.[0].d.[2]": 4,
            "c.[0].e.[0].f": 1,
            "c.[0].e.[0].g": 2,
        }
    )
)

print(
    flatten(
        {
            "a": "str",
            "b": "str",
            "c": [
                {
                    "d": "int",
                    "e": [
                        {
                            "f": "int",
                            "g": "int",
                        }
                    ],
                }
            ],
        }
    )
)


print(flatten({"hi": {"woo": [1, 2]}}))
print(flatten({"hi": {"woo": ["a", "b"]}}))
print(
    flatten(
        {
            "count": "int",
            "cost": "int",
            "budget_items": [
                {
                    "name": ["dog food", "cat food", "fish food"],
                    "total": [1, 2, 3],
                    "cost_over_time": [{"date": "str", "cost": "int"}],
                }
            ],
        }
    )
)

print(
    unflatten(
        {
            "count": "int",
            "cost": "int",
            "budget_items.[0].name": ["dog food", "cat food", "fish food"],
            "budget_items.[0].total": [1, 2, 3],
            "budget_items.[0].cost_over_time.[0].date": "str",
            "budget_items.[0].cost_over_time.[0].cost": "int",
        }
    )
)
