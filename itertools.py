import collections


def groupby(iterable, key):
    """
    Similar to 'itertools.groupby', but this function can work on unsorted data.
    * 'itertools.groupby' works only on ordered data.
    """
    res_dict = collections.defaultdict(list)
    for item in iterable:
        res_dict[key(item)].append(item)
    return res_dict.items()
