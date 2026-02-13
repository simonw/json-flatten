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

Keys containing special characters (., $, [, ~) are escaped using
RFC 6901-style tilde escaping:

    ~0 = literal ~
    ~1 = literal .
    ~2 = literal $
    ~3 = literal [
"""

import re


def _escape_key(key):
    """Escape special characters in a dictionary key.

    Order matters: ~ must be escaped first to avoid double-escaping."""
    return key.replace("~", "~0").replace(".", "~1").replace("$", "~2").replace("[", "~3")


def _unescape_key(key):
    """Unescape a previously escaped key segment.

    Order matters: ~0 must be decoded last so ~03 doesn't prematurely
    become ~ + 3 then [."""
    return key.replace("~3", "[").replace("~2", "$").replace("~1", ".").replace("~0", "~")


def _object_to_rows(obj, prefix=None):
    rows = []
    dot_prefix = prefix and (prefix + ".") or ""
    if isinstance(obj, dict):
        if not obj:
            rows.append(((prefix or "") + "$empty", "{}"))
        else:
            for key, item in obj.items():
                rows.extend(
                    _object_to_rows(item, prefix=dot_prefix + _escape_key(key))
                )
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
_int_key_re = re.compile(r"\[(\d+)\]$")


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
            lastkey, lasttype = lastkey.rsplit("$", 1)
            value = {
                "int": int,
                "float": float,
                "empty": lambda v: {},
                "emptylist": lambda v: [],
                "bool": lambda v: v.lower() == "true",
                "none": lambda v: None,
            }.get(lasttype, lambda v: v)(value)
        # Keep lastkey in escaped form here -- unescaping happens in third pass
        # so that [N] detection in second pass isn't confused by literal bracket keys
        current[lastkey] = value

    # Second pass: convert dicts where all keys are [N] into lists.
    # This works on escaped keys, so real array indices [0] match but
    # escaped bracket keys like ~30] do not.
    def replace_integer_keyed_dicts_with_lists(obj):
        if isinstance(obj, dict):
            if obj and all(_int_key_re.fullmatch(k) for k in obj):
                return [
                    i[1]
                    for i in sorted(
                        [
                            (
                                int(_int_key_re.fullmatch(k).group(1)),
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

    # Third pass: unescape all remaining dict keys
    def unescape_keys(obj):
        if isinstance(obj, dict):
            return {_unescape_key(k): unescape_keys(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [unescape_keys(v) for v in obj]
        else:
            return obj

    obj = unescape_keys(obj)

    # Handle root units only, e.g. {'$empty': '{}'}
    if isinstance(obj, dict) and list(obj.keys()) == [""]:
        return list(obj.values())[0]
    return obj
