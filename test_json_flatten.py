from json_flatten import flatten, unflatten
from hypothesis import given
from hypothesis.strategies import text
import pytest


@pytest.mark.parametrize(
    "test_name,unflattened,flattened",
    [
        # test_name, unflattened, flattened
        ("simple", {"foo": "bar"}, {"foo": "bar"}),
        ("nested", {"foo": {"bar": "baz"}}, {"foo.bar": "baz"}),
        ("list_with_one_item", {"foo": ["item"]}, {"foo.0": "item"}),
        ("nested_lists", {"foo": [["item"]]}, {"foo.0.0": "item"}),
        (
            "list",
            {"foo": {"bar": ["one", "two"]}},
            {"foo.bar.0": "one", "foo.bar.1": "two"},
        ),
        ("int", {"foo": 5}, {"foo$int": "5"}),
        ("none", {"foo": None}, {"foo$none": "None"}),
        ("bool_true", {"foo": True}, {"foo$bool": "True"}),
        ("bool_false", {"foo": False}, {"foo$bool": "False"}),
        ("float", {"foo": 2.5}, {"foo$float": "2.5"}),
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
                "this.is.nested.0.nested_dict_one$int": "10",
                "this.is.nested.1.nested_dict_two$float": "20.5",
                "this.other_types.true$bool": "True",
                "this.other_types.false$bool": "False",
                "this.other_types.none$none": "None",
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
                "foo.0.emails.0": "bar@example.com",
                "foo.0.phones._$!<home>!$_": "555-555-5555",
            },
        ),
        ("empty_object", {}, {"$empty": "{}"}),
        (
            "nested_empty_objects",
            {"nested": {"foo": {}, "bar": {}}},
            {"nested.foo$empty": "{}", "nested.bar$empty": "{}"},
        ),
    ],
)
def test_flatten_unflatten(test_name, unflattened, flattened):
    assert flatten(unflattened) == flattened
    assert unflatten(flattened) == unflattened


def test_integers_with_gaps_does_not_create_sparse_array():
    assert unflatten({"list.10": "three", "list.5": "two", "list.0": "one"}) == {
        "list": ["one", "two", "three"]
    }


@given(text(min_size=1))
def test_with_hypothesis(s):
    d = {s: s}
    flattened = flatten(d)
    unflattened = unflatten(flattened)
    assert d == unflattened
