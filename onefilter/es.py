# -*- coding: utf-8 -*-

from .tree import Node


class ESBuilder(object):

    @staticmethod
    def is_term_operator(node):
        return (
            node.type == 'merged_operator' or
            node.type == 'operator' and
            node.value not in ('and', 'or', 'not')
        )

    @staticmethod
    def is_compound_operator(node):
        return (
            node.type == 'operator' and
            node.value in ('and', 'or', 'not')
        )

    @staticmethod
    def build_compound_clauses(operator, sub_clauses):
        clauses = {
            'and': {'bool': {'must': sub_clauses}},
            'or': {'bool': {'should': sub_clauses}},
            'not': {'bool': {'must_not': sub_clauses}}
        }
        return clauses[operator]

    @staticmethod
    def build_term_level_clause(operator, identifier, value):
        exists_clause = {'exists': {'field': identifier}}
        clauses = {
            'eq': {'term': {identifier: value}},
            'in': {'terms': {identifier: value}},
            'gt': {'range': {identifier: {'gt': value}}},
            'gte': {'range': {identifier: {'gte': value}}},
            'lt': {'range': {identifier: {'lt': value}}},
            'lte': {'range': {identifier: {'lte': value}}},
            'exists': exists_clause if value else {'must_not': exists_clause}
        }
        return clauses[operator]

    @staticmethod
    def merge_compare_operators(tree):
        for parent, index, node in tree.walk():
            if node.value == 'and':
                operators = [(i, child) for i, child in enumerate(node.children)
                             if child.value in ('gt', 'gte', 'lt', 'lte')]
                if len(operators) > 1:
                    merged_value = [(operator.value, operator.children[0].value)
                                    for _, operator in operators]
                    merged_operator = Node('merged_operator', merged_value)
                    if len(operators) == len(node.children):
                        parent.children[index] = merged_operator
                    else:
                        # Replace the first
                        node.children[operators[0][0]] = merged_operator
                        # Remove the rest
                        for _, c in operators[1:]:
                            node.children.remove(c)
            elif node.value == 'not':
                child = node.children[0]
                negatives = {
                    'gt': 'lte',
                    'gte': 'lt',
                    'lt': 'gte',
                    'lte': 'gt'
                }
                if child.value in negatives:
                    operator = Node('operator', negatives[child.value],
                                    child.children)
                    parent.children[index] = operator

        return tree

    @classmethod
    def combine_operators_with_identifiers(cls, tree):
        for parent, index, node in tree.walk():
            if node.type == 'identifier':
                identifier = node
                child = identifier.children[0]
                if cls.is_term_operator(child):
                    continue

                for c_parent, c_index, c_node in child.walk(identifier):
                    if cls.is_term_operator(c_node):
                        c_parent.children[c_index] = Node('identifier',
                                                          identifier.value,
                                                          children=[c_node])

                if not parent:
                    return child
                parent.children[index] = child

        return tree

    @classmethod
    def build_clauses(cls, node):
        if cls.is_compound_operator(node):
            if node.value == 'not':
                sub_clauses = cls.build_clauses(node.children[0])
            else:
                sub_clauses = [cls.build_clauses(child)
                               for child in node.children]
            return cls.build_compound_clauses(node.value, sub_clauses)
        elif node.type == 'identifier':
            identifier = node
            child = node.children[0]
            if child.type == 'merged_operator':
                return {'range': {identifier.value: dict(child.value)}}
            elif cls.is_term_operator(child):
                value = child.children[0]
                return cls.build_term_level_clause(
                    child.value, identifier.value, value.value
                )

    @classmethod
    def build(cls, tree):
        tree = tree.copy()
        tree = cls.merge_compare_operators(tree)
        tree = cls.combine_operators_with_identifiers(tree)
        clauses = cls.build_clauses(tree)
        return clauses


ES = ESBuilder.build