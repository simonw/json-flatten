"""
flatten() and unflatten()

A pair of functions that can convert an arbitrary JSON object into a
flat name/value pair dictionary and back again, preserving type 
information and handling both nested lists and nested dictionaries.

For example:

    {
        "this": {
            "is": {
                "nested": [{
                    "nested_dict_one": 10
                }, {
                    "nested_dict_two": 20.5
                }]
            },
            "other_types": {
                "true": True,
                "false": False,
                "none": None,
            }
        }
    }

Flattens to:

    {
        "this.is.nested.[0].nested_dict_one$int": "10",
        "this.is.nested.[1].nested_dict_two$float": "20.5",
        "this.other_types.true$bool": "True",
        "this.other_types.false$bool": "False",
        "this.other_types.none$none": "None",
    }
"""
import re


def _object_to_rows(obj, prefix=None):
    rows = []
    dot_prefix = prefix and (prefix + ".") or ""
    if isinstance(obj, dict):
        if not obj:
            rows.append(((prefix or "") + "$empty", "{}"))
        else:
            for key, item in obj.items():
                rows.extend(_object_to_rows(item, prefix=dot_prefix + key))
    elif isinstance(obj, (list, tuple)):
        if len(obj) == 0:
            rows.append(((prefix or "") + "$emptylist", "[]"))
        for i, item in enumerate(obj):
            rows.extend(_object_to_rows(item, prefix=dot_prefix + "[{}]".format(i)))
    elif obj is None:
        rows.append(((prefix or "") + "$none", "None"))
    elif isinstance(obj, bool):
        rows.append(((prefix or "") + "$bool", str(obj)))
    elif isinstance(obj, int):
        rows.append(((prefix or "") + "$int", str(obj)))
    elif isinstance(obj, float):
        rows.append(((prefix or "") + "$float", str(obj)))
    else:
        rows.append((prefix, str(obj)))
    return rows


def flatten(obj):
    if not isinstance(obj, dict):
        raise TypeError("Expected dict, got {}".format(type(obj)))
    return dict(_object_to_rows(obj))


_types_re = re.compile(r".*\$(none|bool|int|float|empty|emptylist)$")
_int_key_re = re.compile(r"\[(\d+)\]")


def unflatten(data):
    obj = {}
    for key, value in data.items():
        current = obj
        bits = key.split(".")
        path, lastkey = bits[:-1], bits[-1]
        for bit in path:
            current[bit] = current.get(bit) or {}
            current = current[bit]
        # Now deal with $type suffixes:
        if _types_re.match(lastkey):
            lastkey, lasttype = lastkey.rsplit("$", 2)
            value = {
                "int": int,
                "float": float,
                "empty": lambda v: {},
                "emptylist": lambda v: [],
                "bool": lambda v: v.lower() == "true",
                "none": lambda v: None,
            }.get(lasttype, lambda v: v)(value)
        current[lastkey] = value

    # We handle foo.[0].one, foo.[1].two syntax in a second pass,
    # by iterating through our structure looking for dictionaries
    # where all of the keys are stringified integers
    def replace_integer_keyed_dicts_with_lists(obj):
        if isinstance(obj, dict):
            if obj and all(_int_key_re.match(k) for k in obj):
                return [
                    i[1]
                    for i in sorted(
                        [
                            (
                                int(_int_key_re.match(k).group(1)),
                                replace_integer_keyed_dicts_with_lists(v),
                            )
                            for k, v in obj.items()
                        ]
                    )
                ]
            else:
                return dict(
                    (k, replace_integer_keyed_dicts_with_lists(v))
                    for k, v in obj.items()
                )
        elif isinstance(obj, list):
            return [replace_integer_keyed_dicts_with_lists(v) for v in obj]
        else:
            return obj

    obj = replace_integer_keyed_dicts_with_lists(obj)
    # Handle root units only, e.g. {'$empty': '{}'}
    if list(obj.keys()) == [""]:
        return list(obj.values())[0]
    return obj
