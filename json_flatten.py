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
            }
            "other_types": {
                "true": True,
                "false": False,
                "none": None,
            }
        }
    }

Flattens to:

    {
        "this.is.nested.0.nested_dict_one$int": "10",
        "this.is.nested.1.nested_dict_two$float": "20.5",
        "this.other_types.true$bool": "True",
        "this.other_types.false$bool": "False",
        "this.other_types.true$none": "None"
    }

"""

def _object_to_rows(obj, prefix=None):
    rows = []
    dot_prefix = (prefix and (prefix + '.') or '')
    if isinstance(obj, dict):
        for key, item in obj.items():
            rows.extend(_object_to_rows(item, prefix=dot_prefix + key))
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            rows.extend(_object_to_rows(item, prefix=dot_prefix + str(i)))
    elif obj is None:
        rows.append(((prefix or '') + '$none', 'None'))
    elif isinstance(obj, bool):
        rows.append(((prefix or '') + '$bool', str(obj)))
    elif isinstance(obj, int):
        rows.append(((prefix or '') + '$int', str(obj)))
    elif isinstance(obj, float):
        rows.append(((prefix or '') + '$float', str(obj)))
    else:
        rows.append((prefix, str(obj)))
    return rows

def flatten(obj):
    return dict(_object_to_rows(obj))


def unflatten(data):
    obj = {}
    for key, value in data.items():
        current = obj
        bits = key.split('.')
        path, lastkey = bits[:-1], bits[-1]
        for bit in path:
            current[bit] = current.get(bit) or {}
            current = current[bit]
        # Now deal with $type suffixes:
        if '$' in lastkey:
            lastkey, lasttype = lastkey.rsplit('$', 2)
            value = {
                'int': int,
                'float': float,
                'bool': lambda v: v.lower() == 'true',
                'none': lambda v: None
            }.get(lasttype, lambda v: v)(value)
        current[lastkey] = value

    # We handle foo.0.one, foo.1.two syntax in a second pass,
    # by iterating through our structure looking for dictionaries
    # where all of the keys are stringified integers
    def replace_integer_keyed_dicts_with_lists(d):
        for key, value in d.items():
            if isinstance(value, dict):
                if all(k.isdigit() for k in value):
                    d[key] = [i[1] for i in sorted([
                        (int(k), value[k]) for k in value
                    ])]
                else:
                    replace_integer_keyed_dicts_with_lists(value)

    replace_integer_keyed_dicts_with_lists(obj)
    return obj


test_examples = [
    # test_name, unflattened, flattened
    ('simple', {
        'foo': 'bar'
    }, {
        'foo': 'bar'
    }),
    ('nested', {
        'foo': {
            'bar': 'baz'
        }
    }, {
        'foo.bar': 'baz'
    }),
    ('list', {
        'foo': {
            'bar': ['one', 'two']
        }
    }, {
        'foo.bar.0': 'one',
        'foo.bar.1': 'two'
    }),
    ('int', {
        'foo': 5
    }, {
        'foo$int': '5'
    }),
    ('none', {
        'foo': None,
    }, {
        'foo$none': 'None',
    }),
    ('bool_true', {
        'foo': True,
    }, {
        'foo$bool': 'True'
    }),
    ('bool_false', {
        'foo': False
    }, {
        'foo$bool': 'False'
    }),
    ('float', {
        'foo': 2.5
    }, {
        'foo$float': '2.5'
    }),
    ('complex', {
        'this': {
            'is': {
                'nested': [{
                    'nested_dict_one': 10
                }, {
                    'nested_dict_two': 20.5
                }]
            },
            'other_types': {
                'false': False,
                'true': True,
                'none': None
            }
        }
    }, {
        'this.is.nested.0.nested_dict_one$int': '10',
        'this.is.nested.1.nested_dict_two$float': '20.5',
        'this.other_types.true$bool': 'True',
        'this.other_types.false$bool': 'False',
        'this.other_types.none$none': 'None'
    }),
]

# Dynamically construct the TestCase, to ensure each flatten/unflatten
# method has the correct name (so test failures will be displayed nicely)
import unittest
class FlattenUnflattenTests(unittest.TestCase):
    pass

def _make_test_pair(test_name, unflattened, flattened):
    def test_flatten(self):
        self.assertEqual(flatten(unflattened), flattened)
    def test_unflatten(self):
        self.assertEqual(unflatten(flattened), unflattened)
    return test_flatten, test_unflatten

for test_name, unflattened, flattened in test_examples:
    test_flatten, test_unflatten = _make_test_pair(test_name, unflattened, flattened)
    test_flatten.__name__ = 'test_flatten_%s' % test_name
    test_unflatten.__name__ = 'test_unflatten_%s' % test_name
    setattr(FlattenUnflattenTests, test_flatten.__name__, test_flatten)
    setattr(FlattenUnflattenTests, test_unflatten.__name__, test_unflatten)


if __name__ == '__main__':
    unittest.main()
