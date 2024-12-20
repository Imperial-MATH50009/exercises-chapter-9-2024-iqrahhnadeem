import numbers  # noqa D100
from functools import singledispatch


class Expression():
    """Expressions class."""

    def __init__(self, *operands):
        self.operands = operands

    def __add__(self, other):
        if isinstance(other, numbers.Number):
            other = Number(other)
        return Add(self, other)

    def __radd__(self, other):
        if isinstance(other, numbers.Number):
            return Add(Number(other), self)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, numbers.Number):
            other = Number(other)
        return Sub(self, other)

    def __rsub__(self, other):
        if isinstance(other, numbers.Number):
            return Sub(Number(other), self)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, numbers.Number):
            other = Number(other)
        return Mul(self, other)

    def __rmul__(self, other):
        if isinstance(other, numbers.Number):
            return Mul(Number(other), self)
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, numbers.Number):
            other = Number(other)
        return Div(self, other)

    def __rtruediv__(self, other):
        if isinstance(other, numbers.Number):
            return Div(Number(other), self)
        return NotImplemented

    def __pow__(self, other):
        if isinstance(other, numbers.Number):
            other = Number(other)
        return Pow(self, other)

    def __rpow__(self, other):
        if isinstance(other, numbers.Number):
            return Pow(Number(other), self)
        return NotImplemented


class Operator(Expression):
    """Base class for operators."""

    def __repr__(self):
        return self.__class__.__name__ + repr(self.operands)

    def __str__(self):
        def paren(expr):
            if expr.precedence < self.precedence:
                return f"({expr!s})"
            else:
                return str(expr)
        return " ".join((paren(self.operands[0]),
                         self.symbol,
                         paren(self.operands[1])))


class Add(Operator):
    """Represents addition."""

    precedence = 0
    symbol = "+"


class Sub(Operator):
    """Represents subtraction."""

    precedence = 0
    symbol = "-"


class Mul(Operator):
    """Represents multiplication."""

    precedence = 1
    symbol = "*"


class Div(Operator):
    """Represents division."""

    precedence = 1
    symbol = "/"


class Pow(Operator):
    """Represents exponents."""

    precedence = 2
    symbol = "^"


class Terminal(Expression):
    """Represents terminal expressions like numbers and symbols."""

    precedence = 3

    def __init__(self, value):
        self.value = value
        super().__init__()

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)


class Symbol(Terminal):
    """Represents a symbolic variable."""

    def __init__(self, value):
        if not isinstance(value, str):
            raise TypeError("Symbol value must be a string.")
        super().__init__(value)


class Number(Terminal):
    """Represents a constant number."""

    def __init__(self, value):
        if not isinstance(value, numbers.Number):
            raise TypeError("Number value must be a number.")
        super().__init__(value)


def postvisitor(expr, fn, **kwargs):
    """
    Visit an Expression in postorder applying a function to every node.

    Parameters
    ----------
    expr: Expression
        The expression to be visited.
    fn: function(node, *o, **kwargs)
        A function to be applied at each node. The function should take
        the node to be visited as its first argument, and the results of
        visiting its operands as any further positional arguments. Any
        additional information that the visitor requires can be passed in
        as keyword arguments.
    **kwargs:
        Any additional keyword arguments to be passed to fn.
    """
    stack = []
    visited = {}
    stack.append(expr)
    while stack:
        e = stack.pop()
        unvisited_children = []
        for o in e.operands:
            if o not in visited:
                unvisited_children.append(o)

        if unvisited_children:
            stack.append(e)
            for uc in unvisited_children:
                stack.append(uc)
        else:
            visited[e] = fn(e, *(visited[o] for o in e.operands), **kwargs)

    return visited[expr]


@singledispatch
def differentiate(expr, *o, **kwargs):  # noqa D103
    raise NotImplementedError(
        f"Cannot differentiate a {type(expr).__name__}")


@differentiate.register(Number)
def _(expr, *o, **kwargs):
    return 0.0


@differentiate.register(Symbol)
def _(expr, *o, **kwargs):
    return 1.0 if kwargs['var'] == expr.value else 0.0


@differentiate.register(Add)
def _(expr, *o, **kwargs):
    return o[0] + o[1]


@differentiate.register(Sub)
def _(expr, *o, **kwargs):
    return o[0] - o[1]


@differentiate.register(Mul)
def _(expr, *o, **kwargs):
    return o[0] * expr.operands[1] + o[1] * expr.operands[0]


@differentiate.register(Div)
def _(expr, *o, **kwargs):
    return (o[0] * expr.operands[1] - expr.operands[0]
            * o[1]) / (expr.operands[1]**2)


@differentiate.register(Pow)
def _(expr, *o, **kwargs):
    return expr.operands[1] * \
        (expr.operands[0] ** (expr.operands[1] - 1)) * o[0]
