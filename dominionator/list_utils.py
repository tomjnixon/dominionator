def removed(l, item):
    """Return a copy of l with item removed."""
    l = l[:]
    l.remove(item)
    return l
