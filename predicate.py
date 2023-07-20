from abc import abstractmethod, ABC
from typing import List, Dict
from lxml.etree import _Comment as XmlComment
from lxml.etree import _Element as XmlElement


class PredicateNode(ABC):
    @abstractmethod
    def predicate(self, row: dict):
        pass


class PNAny(PredicateNode):
    def __init__(self, children: List[PredicateNode]):
        self.children = children

    def predicate(self, row: dict):
        return any(c.predicate(row) for c in self.children)


class PNAll(PredicateNode):
    def __init__(self, children: List[PredicateNode]):
        self.children = children

    def predicate(self, row: dict):
        return all(c.predicate(row) for c in self.children)


class PredicateTreeBuilder:
    def __init__(self):
        self._tag2cls: Dict[str, type] = {}

    def register(self, tag: str, cls: type):
        self._tag2cls[tag] = cls

    def build(self, ele: XmlElement) -> PredicateNode:
        return self.r_build(ele)

    def r_build(self, node: XmlElement):
        tag = node.tag
        if tag == "all" or tag == "any":
            children = []
            for child_ele in node.iterchildren():
                if type(child_ele) == XmlElement:
                    child_predicate = self.r_build(child_ele)
                    children.append(child_predicate)
            return PNAll(children) if tag == "all" else PNAny(children)
        else:
            pred_cls = self._tag2cls.get(node.tag)
            if pred_cls is None:
                raise NotImplementedError(f"Unknown predication config node of tag '{node.tag}'!")
            # Collect attributes.
            kwargs = {attr: val for attr, val in node.attrib.items()}
