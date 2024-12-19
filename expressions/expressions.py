from abc import ABC, abstractmethod  # noqa D100
import numbers


class Expression(ABC):
    """Abstract base class for all expressions."""

    def __init__(self, *operands):
        self.operands = operands

    def __add__(self, other):
        if isinstance(other, Expression):
            return Add(self, other)
        elif isinstance(other, numbers.Number):
            return Add(self, Number(other))
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, numbers.Number):
            return Add(Number(other), self)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Expression):
            return Sub(self, other)
        elif isinstance(other, numbers.Number):
            return Sub(self, Number(other))
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, numbers.Number):
            return Sub(Number(other), self)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Expression):
            return Mul(self, other)
        elif isinstance(other, numbers.Number):
            return Mul(self, Number(other))
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, numbers.Number):
            return Mul(Number(other), self)
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, Expression):
            return Div(self, other)
        elif isinstance(other, numbers.Number):
            return Div(self, Number(other))
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, numbers.Number):
            return Div(Number(other), self)
        return NotImplemented

    def __pow__(self, other):
        if isinstance(other, Expression):
            return Pow(self, other)
        elif isinstance(other, numbers.Number):
            return Pow(self, Number(other))
        return NotImplemented

    def __rpow__(self, other):
        if isinstance(other, numbers.Number):
            return Pow(Number(other), self)
        return NotImplemented

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def evaluate(self, **kwargs):
        """Evaluate."""
        pass


class Terminal(Expression):
    """Represents terminal expressions like numbers and symbols."""

    def __init__(self, value):
        super().__init__()
        self.value = value

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.value)})"

    def __str__(self):
        return str(self.value)

    def evaluate(self, **kwargs):
        """Evaluate."""
        return self.value


class Symbol(Terminal):
    """Represents a symbolic variable."""

    def __init__(self, name):
        if not isinstance(name, str):
            raise TypeError("Symbol name must be a string.")
        super().__init__(name)

    def evaluate(self, **kwargs):
        """Evaluate."""
        if self.value in kwargs:
            return kwargs[self.value]
        raise ValueError(f"Value for symbol '{self.value}' not provided.")


class Number(Terminal):
    """Represents a constant number."""

    def __init__(self, value):
        if not isinstance(value, numbers.Number):
            raise TypeError("Number value must be a numeric type.")
        super().__init__(value)


class Operator(Expression):
    """Abstract base class for operators."""

    symbol = ''
    precedence = 0

    def __init__(self, *operands):
        if len(operands) != 2:
            raise ValueError
        super().__init__(*operands)

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"{repr(self.operands[0])}, {repr(self.operands[1])})"
        )

    def __str__(self):
        left, right = self.operands
        # Left operand parentheses
        left_str = (
            f"({left})"
            if isinstance(left, Operator) and left.precedence < self.precedence
            else str(left)
        )
        # Right operand parentheses
        right_str = (
            f"({right})"
            if isinstance(right, Operator) and right.precedence < self.precedence or (isinstance(right, Operator) and right.precedence == self.precedence and self.symbol not in ["+", "*"])  # noqa E501
            else str(right)
        )
        return f"{left_str} {self.symbol} {right_str}"


class Add(Operator):
    """Represents addition."""

    symbol = '+'
    precedence = 1

    def evaluate(self, **kwargs):
        """Evaluate."""
        return self.operands[0].evaluate(**kwargs) + self.operands[1].evaluate(**kwargs)  # noqa E501


class Sub(Operator):
    """Represents subtraction."""

    symbol = '-'
    precedence = 1

    def evaluate(self, **kwargs):
        """Evaluate."""
        return self.operands[0].evaluate(**kwargs) - self.operands[1].evaluate(**kwargs)  # noqa E501


class Mul(Operator):
    """Represents multiplication."""

    symbol = '*'
    precedence = 2

    def evaluate(self, **kwargs):
        """Evaluate."""
        return self.operands[0].evaluate(**kwargs) * self.operands[1].evaluate(**kwargs)  # noqa E501


class Div(Operator):
    """Represents division."""

    symbol = '/'
    precedence = 2

    def evaluate(self, **kwargs):
        """Evaluate."""
        return self.operands[0].evaluate(**kwargs) / self.operands[1].evaluate(**kwargs)  # noqa E501


class Pow(Operator):
    """Represents exponentiation."""

    symbol = '^'
    precedence = 3

    def evaluate(self, **kwargs):
        """Evaluate."""
        return self.operands[0].evaluate(**kwargs) ** self.operands[1].evaluate(**kwargs)  # noqa E501


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
    visited = {}
    stack = [(expr, False)]
    results = {}

    while stack:
        node, processed = stack.pop()
        if processed:
            results[node] = fn(node, *(results[c] for c in node.operands), **kwargs)  # noqa E501
        elif node not in visited:
            visited[node] = True
            stack.append((node, True))
            for operand in node.operands:
                if operand not in visited:
                    stack.append((operand, False))

    return results[expr]


def differentiate(expr, *operands, var=None, **kwargs):
    """
    Differentiate an Expression with respect to a given variable.

    Parameters
    ----------
    expr: Expression
        The expression to be differentiated.
    var: str
        The variable with respect to which differentiation is performed.
    """
    if isinstance(expr, Number):
        return Number(0)
    elif isinstance(expr, Symbol):
        return Number(1) if expr.value == var else Number(0)
    elif isinstance(expr, Add):
        return Add(*operands)
    elif isinstance(expr, Sub):
        return Sub(*operands)
    elif isinstance(expr, Mul):
        u, v = expr.operands
        return Add(Mul(differentiate(u, var=var), v), Mul(u, differentiate(v, var=var))) # noqa E501
    elif isinstance(expr, Div):
        u, v = expr.operands
        return Div(Sub(Mul(differentiate(u, var=var), v), Mul(u, differentiate(v, var=var))), Pow(v, Number(2)))  # noqa E501
    elif isinstance(expr, Pow):
        base, exponent = expr.operands
        if isinstance(exponent, Number):
            return Mul(Mul(Number(exponent.value), Pow(base, Number(exponent.value - 1))), differentiate(base, var=var))  # noqa E501
        else:
            raise NotImplementedError("Non-constant exponent.")
    else:
        raise TypeError(f"Unsupported expression type: {type(expr)}")
