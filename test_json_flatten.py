import pytest

from json_flatten import flatten, unflatten


@pytest.mark.parametrize(
    "test_name,unflattened,flattened",
    [
        # test_name, unflattened, flattened
        ("simple", {"foo": "bar"}, {"foo": "bar"}),
        ("nested", {"foo": {"bar": "baz"}}, {"foo.bar": "baz"}),
        ("list_with_one_item", {"foo": ["item"]}, {"foo": ["item"]}),
        ("nested_lists", {"foo": [["item"]]}, {"foo.[0]": ["item"]}),
        (
            "list",
            {"foo": {"bar": ["one", "two"]}},
            {"foo.bar": ["one", "two"]},
        ),
        ("int", {"foo": 5}, {"foo": 5}),
        ("none", {"foo": None}, {"foo": None}),
        ("bool_true", {"foo": True}, {"foo": True}),
        ("bool_false", {"foo": False}, {"foo": False}),
        ("float", {"foo": 2.5}, {"foo": 2.5}),
        (
            "complex",
            {
                "this": {
                    "is": {
                        "nested": [{"nested_dict_one": 10}, {"nested_dict_two": 20.5}]
                    },
                    "other_types": {"false": False, "true": True, "none": None},
                }
            },
            {
                "this.is.nested.[0].nested_dict_one": 10,
                "this.is.nested.[1].nested_dict_two": 20.5,
                "this.other_types.true": True,
                "this.other_types.false": False,
                "this.other_types.none": None,
            },
        ),
        (
            "dollar_signs_that_are_not_type_indicators",
            {
                "foo": [
                    {
                        "emails": ["bar@example.com"],
                        "phones": {"_$!<home>!$_": "555-555-5555"},
                    }
                ]
            },
            {
                "foo.[0].emails": ["bar@example.com"],
                "foo.[0].phones._$!<home>!$_": "555-555-5555",
            },
        ),
        ("empty_object", {}, {}),
        (
            "nested_empty_objects",
            {"nested": {"foo": {}, "bar": {}}},
            {"nested.foo": {}, "nested.bar": {}},
        ),
        ("empty_nested_list", {"empty": []}, {"empty": []}),
        (
            "empty_nested_list_complex",
            {"foo": {"bar": []}, "nested": [[], []]},
            {
                "foo.bar": [],
                "nested.[0]": [],
                "nested.[1]": [],
            },
        ),
        ("dict_with_numeric_key", {"bob": {"24": 4}}, {"bob.24": 4}),
        (
            "list_as_enum",
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
            },
            {
                "count": "int",
                "cost": "int",
                "budget_items.[0].name": ["dog food", "cat food", "fish food"],
                "budget_items.[0].total": [1, 2, 3],
                "budget_items.[0].cost_over_time.[0].date": "str",
                "budget_items.[0].cost_over_time.[0].cost": "int",
            },
        ),
    ],
)
def test_flatten_unflatten(test_name, unflattened, flattened):
    actual_flattened = flatten(unflattened)
    assert actual_flattened == flattened
    actual_unflattened = unflatten(actual_flattened)
    assert actual_unflattened == unflattened


def test_integers_with_gaps_does_not_create_sparse_array():
    assert unflatten({"list.[10]": "three", "list.[5]": "two", "list.[0]": "one"}) == {
        "list": ["one", "two", "three"]
    }


def test_list_as_base_level_object_rejected_with_error():
    with pytest.raises(TypeError):
        flatten([{"name": "john"}])
