from functools import reduce
from operator import getitem


def get_nested_item(data, keys):
    return reduce(getitem, keys, data)
