from chartparse.datastructures import ImmutableSortedList


def AlreadySortedImmutableSortedList(xs):
    return ImmutableSortedList(xs, already_sorted=True)
