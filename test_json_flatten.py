from json_flatten import flatten, unflatten
import pytest


@pytest.mark.parametrize(
    "test_name,unflattened,flattened",
    [
        # test_name, unflattened, flattened
        ("simple", {"foo": "bar"}, {"foo": "bar"}),
        ("nested", {"foo": {"bar": "baz"}}, {"foo.bar": "baz"}),
        ("list_with_one_item", {"foo": ["item"]}, {"foo.[0]": "item"}),
        ("nested_lists", {"foo": [["item"]]}, {"foo.[0].[0]": "item"}),
        (
            "list",
            {"foo": {"bar": ["one", "two"]}},
            {"foo.bar.[0]": "one", "foo.bar.[1]": "two"},
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
                "this.is.nested.[0].nested_dict_one$int": "10",
                "this.is.nested.[1].nested_dict_two$float": "20.5",
                "this.other_types.true$bool": "True",
                "this.other_types.false$bool": "False",
                "this.other_types.none$none": "None",
            },
        ),
        (
            "dollar_signs_escaped",
            {
                "foo": [
                    {
                        "emails": ["bar@example.com"],
                        "phones": {"_$!<home>!$_": "555-555-5555"},
                    }
                ]
            },
            {
                "foo.[0].emails.[0]": "bar@example.com",
                "foo.[0].phones._~2!<home>!~2_": "555-555-5555",
            },
        ),
        ("empty_object", {}, {"$empty": "{}"}),
        (
            "nested_empty_objects",
            {"nested": {"foo": {}, "bar": {}}},
            {"nested.foo$empty": "{}", "nested.bar$empty": "{}"},
        ),
        ("empty_nested_list", {"empty": []}, {"empty$emptylist": "[]"}),
        (
            "empty_nested_list_complex",
            {"foo": {"bar": []}, "nested": [[], []]},
            {
                "foo.bar$emptylist": "[]",
                "nested.[0]$emptylist": "[]",
                "nested.[1]$emptylist": "[]",
            },
        ),
        ("dict_with_numeric_key", {"bob": {"24": 4}}, {"bob.24$int": "4"}),
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


# --- RED phase: tests for tilde escaping (RFC 6901-style) ---


class TestDotInKeys:
    """Issue #1: Keys containing dots must round-trip correctly."""

    def test_simple_dot_in_key(self):
        obj = {"a.b": "value"}
        assert unflatten(flatten(obj)) == obj

    def test_dot_key_distinct_from_nested(self):
        """Dotted key and nested key must produce different flattened forms."""
        dotted = flatten({"a.b": "value"})
        nested = flatten({"a": {"b": "value"}})
        assert dotted != nested

    def test_dot_key_flattened_form(self):
        assert flatten({"a.b": "value"}) == {"a~1b": "value"}

    def test_dot_key_with_type_suffix(self):
        obj = {"a.b": 5}
        assert flatten(obj) == {"a~1b$int": "5"}
        assert unflatten(flatten(obj)) == obj

    def test_multiple_dots_in_key(self):
        obj = {"a.b.c": "value"}
        assert unflatten(flatten(obj)) == obj

    def test_dot_key_nested_in_object(self):
        obj = {"outer": {"a.b": "value"}}
        assert unflatten(flatten(obj)) == obj


class TestDollarInKeys:
    """Issue #2: Keys containing $ must not crash rsplit."""

    def test_dollar_in_key_with_int_value(self):
        obj = {"my$key": 5}
        assert unflatten(flatten(obj)) == obj

    def test_dollar_in_key_flattened_form(self):
        assert flatten({"my$key": 5}) == {"my~2key$int": "5"}

    def test_dollar_in_key_with_string_value(self):
        obj = {"my$key": "hello"}
        assert unflatten(flatten(obj)) == obj

    def test_multiple_dollars_in_key(self):
        obj = {"a$b$c": 10}
        assert unflatten(flatten(obj)) == obj


class TestAmbiguousTypeSuffix:
    """Issue #3: Keys ending with type suffix names must not be misinterpreted."""

    def test_key_ending_with_dollar_int_string_value(self):
        obj = {"price$int": "hello"}
        assert unflatten(flatten(obj)) == obj

    def test_key_ending_with_dollar_none_string_value(self):
        obj = {"flag$none": "active"}
        assert unflatten(flatten(obj)) == obj

    def test_key_ending_with_dollar_bool_string_value(self):
        obj = {"x$bool": "maybe"}
        assert unflatten(flatten(obj)) == obj

    def test_key_ending_with_dollar_float_string_value(self):
        obj = {"val$float": "text"}
        assert unflatten(flatten(obj)) == obj

    def test_key_ending_with_dollar_empty_string_value(self):
        obj = {"obj$empty": "not empty"}
        assert unflatten(flatten(obj)) == obj

    def test_key_ending_with_dollar_emptylist_string_value(self):
        obj = {"arr$emptylist": "not a list"}
        assert unflatten(flatten(obj)) == obj


class TestBracketKeys:
    """Issue #4: Keys in [N] format must not crash or be treated as array indices."""

    def test_bracket_key_round_trip(self):
        obj = {"[0]": "value"}
        assert unflatten(flatten(obj)) == obj

    def test_bracket_key_flattened_form(self):
        assert flatten({"[0]": "value"}) == {"~30]": "value"}

    def test_bracket_key_not_confused_with_list(self):
        """A dict with [N] keys must stay a dict, not become a list."""
        obj = {"[0]": "a", "[1]": "b"}
        result = unflatten(flatten(obj))
        assert isinstance(result, dict)
        assert result == obj

    def test_bracket_key_nested(self):
        obj = {"outer": {"[0]": "value"}}
        assert unflatten(flatten(obj)) == obj


class TestTildeInKeys:
    """Self-consistency: keys containing ~ must round-trip correctly."""

    def test_tilde_in_key(self):
        obj = {"a~b": "value"}
        assert unflatten(flatten(obj)) == obj

    def test_tilde_in_key_flattened_form(self):
        assert flatten({"a~b": "value"}) == {"a~0b": "value"}

    def test_tilde_escape_sequence_in_key(self):
        """A key that looks like an escape sequence must round-trip."""
        obj = {"a~1b": "value"}
        assert unflatten(flatten(obj)) == obj

    def test_tilde_with_type_suffix(self):
        obj = {"a~b": 5}
        assert unflatten(flatten(obj)) == obj


class TestCombinationEscaping:
    """Multiple special characters in the same key."""

    def test_dot_and_dollar_in_key(self):
        obj = {"a.b$int": "hello"}
        assert unflatten(flatten(obj)) == obj

    def test_all_special_chars_in_key(self):
        obj = {"a.b$c[0]~d": "value"}
        assert unflatten(flatten(obj)) == obj

    def test_existing_dollar_sign_test_updated(self):
        """The _$!<home>!$_ key must still round-trip with escaping."""
        obj = {
            "foo": [
                {
                    "emails": ["bar@example.com"],
                    "phones": {"_$!<home>!$_": "555-555-5555"},
                }
            ]
        }
        assert unflatten(flatten(obj)) == obj
