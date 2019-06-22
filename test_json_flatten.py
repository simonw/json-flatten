from json_flatten import flatten, unflatten
import unittest

test_examples = [
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
                "is": {"nested": [{"nested_dict_one": 10}, {"nested_dict_two": 20.5}]},
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
]

# Dynamically construct the TestCase, to ensure each flatten/unflatten
# method has the correct name (so test failures will be displayed nicely)


class FlattenUnflattenTests(unittest.TestCase):
    def test_integers_with_gaps_does_not_create_sparse_array(self):
        # This test doesn't round-trip, so it can't be created using
        # the _make_test_pair function
        self.assertEqual(
            unflatten({"list.10": "three", "list.5": "two", "list.0": "one"}),
            {"list": ["one", "two", "three"]},
        )


def _make_test_pair(test_name, unflattened, flattened):
    def test_flatten(self):
        self.assertEqual(flatten(unflattened), flattened)

    def test_unflatten(self):
        self.assertEqual(unflatten(flattened), unflattened)

    return test_flatten, test_unflatten


for test_name, unflattened, flattened in test_examples:
    test_flatten, test_unflatten = _make_test_pair(test_name, unflattened, flattened)
    test_flatten.__name__ = "test_flatten_%s" % test_name
    test_unflatten.__name__ = "test_unflatten_%s" % test_name
    setattr(FlattenUnflattenTests, test_flatten.__name__, test_flatten)
    setattr(FlattenUnflattenTests, test_unflatten.__name__, test_unflatten)


if __name__ == "__main__":
    unittest.main()
