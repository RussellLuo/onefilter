# -*- coding: utf-8 -*-


class Node(object):

    def __init__(self, type_, value, children=None):
        self.type = type_  # Options: 'operator', 'identifier', 'value'
        self.value = value
        self.children = children or []

    def dump(self, recursive=False):
        """Return a formatted dump of the tree in current node.

        :param recursive: whether show children recursively
        """
        if recursive:
            dumped_children = ', '.join(child.dump(recursive)
                                        for child in self.children)
        else:
            dumped_children = '...'
        return '{}(value={!r}, children={})'.format(
            self.type.capitalize(), self.value,
            '[{}]'.format(dumped_children if self.children else '')
        )

    __repr__ = __str__ = dump

    @staticmethod
    def merge_all_children(nodes):
        """Merge all the children of `nodes` together.
        """
        merged = []
        for node in nodes:
            merged.extend(node.children)
        return merged

    def resemble(self, node):
        """Whether current node has the same *type* and *value* with `node`.

        :param node: the node to compare with
        """
        return self.type == node.type and self.value == node.value

    def shift_up_grandchildren(self):
        """Remove the children of current node, and merge all the original
        grandchildren together as the new children.
        """
        self.children = self.merge_all_children(self.children)
        return self

    def copy(self):
        """Deep copy the tree in current code."""
        children = [child.copy() for child in self.children]
        return Node(self.type, self.value, children)

    def walk(self, parent=None, index=None):
        """Recursively yield all descendant nodes in the tree starting at
        current node (including current node).

        :param parent: the parent node of current node
        :param index: the index of current node in parent's children
        """
        yield (parent, index, self)
        for i, child in enumerate(self.children):
            for grandchild in child.walk(self, i):
                yield grandchild
