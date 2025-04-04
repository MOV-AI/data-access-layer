class ChildrenCmpMixin(object):
    """Implement _children comparison functions"""

    def __eq__(self, other):
        try:
            # in case it has `_children`
            return self._children == other._children
        except AttributeError:
            # in case we're comparing to a `dict`
            return self._children == other


class ValueCmpMixin(object):
    """Implement _value comparison functions"""

    def __eq__(self, other):
        try:
            # in case they have `_value`
            return self._value == other._value
        except AttributeError:
            # in case we're comparing to a literal
            return self._value == other
