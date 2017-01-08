# -*- coding: utf-8 -*-

from collections import defaultdict
import functools

from voluptuous import Invalid, Schema

from .tree import Node


def instantiate(cls):
    return cls()


def positional_arguments_as_a_list(meth):
    @functools.wraps(meth)
    def decorator(self, *args):
        return meth(self, list(args))
    return decorator


def validate(schema):
    def wrapper(meth):
        @functools.wraps(meth)
        def decorator(self, *args, **kwargs):
            schema(*args, **kwargs)
            return meth(self, *args, **kwargs)
        return decorator
    return wrapper


def node_or_size_one_dict(operand, msg=None):
    if not (isinstance(operand, Node) or
            isinstance(operand, dict) and len(operand) == 1):
        raise Invalid(msg or 'expected Node or size-1 dict')


def non_node(operand, msg=None):
    if isinstance(operand, Node):
        raise Invalid(msg or 'expected non-Node value')


class Operation(object):

    operator = None

    def make_node(self, operand):
        if isinstance(operand, dict):
            name, value = operand.items()[0]
            if not isinstance(value, Node):
                value = Node('operator', 'eq', [self.make_node(value)])
            operand = Node('identifier', name, [value])
        elif not isinstance(operand, Node):
            operand = Node('value', operand)
        return operand

    def make_op(self, operands):
        children = [self.make_node(operand) for operand in operands]
        node = Node('operator', self.operator, children)
        return self.trim(node)

    def trim(self, node):
        return node

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


@instantiate
class And(Operation):
    """Logic and."""

    operator = 'and'

    def merge_identifiers(self, node):
        identifiers = defaultdict(list)
        for child in node.children:
            if child.type == 'identifier':
                identifiers[child.value].append(child)

        for value, children in identifiers.iteritems():
            if len(children) == len(node.children):
                node = Node('identifier', value, [node.shift_up_grandchildren()])
            elif len(children) > 1:
                compound_child = Node(node.type, node.value,
                                      Node.merge_all_children(children))
                # Replace the first
                index = node.children.index(children[0])
                node.children[index] = Node('identifier', value, compound_child)
                # Remove the rest
                for c in children[1:]:
                    node.children.remove(c)

        return node

    def trim(self, node):
        if len(node.children) == 1:
            # Remove current node
            node = node.children[0]

        if all(child.resemble(node) for child in node.children):
            node = node.shift_up_grandchildren()

        return self.merge_identifiers(node)

    @positional_arguments_as_a_list
    @validate(Schema([node_or_size_one_dict]))
    def __call__(self, operands):
        return self.make_op(operands)


@instantiate
class Filter(And.__class__):

    def __call__(self, **criteria):
        operands = [{name: value} for name, value in criteria.iteritems()]
        return self.make_op(operands)

F = Filter


@instantiate
class Or(And.__class__):
    """Logic or."""

    operator = 'or'


@instantiate
class Not(Operation):
    """Logic not."""

    operator = 'not'

    def trim(self, node):
        if len(node.children) == 1:
            child = node.children[0]
            if child.resemble(node):
                # Remove current node and its single child
                node = child.children[0]
        return node

    @validate(Schema(Node))
    def __call__(self, operand):
        return self.make_op([operand])


@instantiate
class Eq(Operation):
    """Equal."""

    operator = 'eq'

    @validate(Schema(non_node))
    def __call__(self, operand):
        return self.make_op([operand])


@instantiate
class In(Operation):

    operator = 'in'

    @positional_arguments_as_a_list
    @validate(Schema([non_node]))
    def __call__(self, items):
        return self.make_op([items])


@instantiate
class Gt(Eq.__class__):
    """Greater than."""

    operator = 'gt'


@instantiate
class Gte(Gt.__class__):
    """Greater than or equal."""

    operator = 'gte'


@instantiate
class Lt(Eq.__class__):
    """Lower than."""

    operator = 'lt'


@instantiate
class Lte(Lt.__class__):
    """Lower than or equal."""

    operator = 'lte'


@instantiate
class Exists(Operation):
    """Exists or not."""

    operator = 'exists'

    @validate(Schema(bool))
    def __call__(self, value):
        return self.make_op([value])
