# -*- coding: utf-8 -*-
# @Time         : 19:10 2023/6/10
# @Author       : Chris
# @Description  : Extract list of data tree to data rows([{field1: value11, ...}, {field1: value21, ...}]).
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from jsonpath_ng import ext as jsonpath

from . import config as xml


class MappingTreeNode:
    def __init__(self):
        self.tag: str = None
        self.engine: TreeExtractor = None
        self.children: List[MappingTreeNode] = []

    def has_attr(self, name: str):
        """
        Check whether this node has a dynamic attr of given name.
        :param name:
        :return:
        """
        return name in self.__dict__

    def get_attr(self, name: str, default):
        """
        Get dynamic attribute. Returns default if absent.
        :param default: The default value to be returned if target attribute is absent.
        :param name:
        :return:
        """
        return self.__dict__[name] if name in self.__dict__ else default

    def __str__(self):
        attr_str = ", ".join(f"{name}={value}" for name, value in self.__dict__.items()
                             if name != "children" and name != "tag")
        return f"{self.tag}({attr_str})"


class TreeExtractor(ABC):
    @abstractmethod
    def parse(self, data_node, path, conf_node: MappingTreeNode):
        """
        :rtype: List[Any]
        """
        pass


class JsonExtractor(TreeExtractor):
    def parse(self, data_node, path, conf_node: MappingTreeNode):
        extracted = jsonpath.parse(path).find(data_node)
        extracted = [e.value for e in extracted]
        return extracted

    def __str__(self):
        return "jsonpath-ng"


class ObjectExtractor(TreeExtractor):
    """
    Extract date by object's attribute name.
    """
    def parse(self, data_node, path, conf_node: MappingTreeNode):
        if hasattr(data_node, path):
            return [getattr(data_node, path)]
        return []

    def __str__(self):
        return "object"


class MappingTree:
    __name2engine: Dict[str, TreeExtractor] = {}

    @staticmethod
    def register(name: str, engine: TreeExtractor):
        if name in MappingTree.__name2engine:
            raise Exception(f"There's already an engine registered as name '{name}'!")
        MappingTree.__name2engine[name] = engine

    @staticmethod
    def compile(xml_doc: xml.XmlDocument) -> MappingTreeNode:
        return MappingTree._r_compile(xml_doc.getroot(), JsonExtractor())  # Json engine as default.

    @staticmethod
    def _r_compile(xml_node: xml.XmlElement, parent_engine: TreeExtractor):
        m_node = MappingTreeNode()
        # 1 Collect attributes.
        # 1.1 General collecting.
        m_node.tag = xml_node.tag
        for attr in xml_node.attrib.items():
            m_node.__dict__[attr[0]] = attr[1]
        # 1.2 Convert some data.
        if m_node.has_attr("optional"):
            m_node.__dict__["optional"] = m_node.get_attr("optional", "True") == "True"
        # 2 Create engine.
        engine_name = m_node.engine
        if isinstance(engine_name, str):
            engine = MappingTree.__name2engine.get(engine_name)
            if engine is None:
                raise NotImplementedError(f"Unimplemented extractor of type '{engine_name}'")
        else:  # 'engine' is None, inherit parent's engine.
            engine = parent_engine
        m_node.engine = engine
        # 3. Collect children.
        for x_child_node in xml_node.iterchildren():
            if isinstance(x_child_node, xml.XmlComment):  # Ignore comment.
                continue
            m_child_node = MappingTree._r_compile(x_child_node, engine)
            m_node.children.append(m_child_node)
        return m_node

    @staticmethod
    def _r_check():
        # TODO: Compile time check.
        pass


MappingTree.register("json", JsonExtractor())
MappingTree.register("object", ObjectExtractor())


class TreeExtractor:
    """
    Extract data tree to flat dict.
    """
    def __init__(self, config: xml.XmlDocument):
        self._mapping = MappingTree.compile(config)

    def extract_items(self, items: List[Any]) -> List[Dict[str, Any]]:
        """
        Extract a list of items.
        """
        rows = [self.extract_item(item) for item in items]
        return rows

    def extract_item(self, item: Any) -> Dict[str, Any]:
        """
        Extract a single data item.
        """
        flat_dict: Dict[str, List] = {}
        self._r_extract(self._mapping, item, flat_dict)
        return flat_dict

    def _r_extract(self, config_node: MappingTreeNode, data_node, res: dict):
        # 1. Check input and prepare data.
        extractor = config_node.engine
        is_optional = config_node.get_attr("optional", False)
        if data_node is None and not is_optional:
            raise RuntimeError(f"{config_node}: Input data for non-optional '{config_node.tag}' shouldn't be 'None'.")
        path = config_node.get_attr("path", None)
        if path:
            extracted_data_nodes = [] if data_node is None else extractor.parse(data_node, path, config_node)
        else:
            extracted_data_nodes = [] if data_node is None else [data_node]
        extracted_data_nodes = self._remove_empty_str(extracted_data_nodes)
        tag = config_node.tag
        field = config_node.get_attr("field", "value")
        ele_children = config_node.children
        # 2. Parse.
        if tag == "table":
            if len(ele_children) > 1:
                raise NotImplementedError()
            for child_data_node in extracted_data_nodes:
                for child_conf in ele_children:
                    self._r_extract(child_conf, child_data_node, res)
        elif tag == "rows":
            if len(extracted_data_nodes) == 0 and not is_optional:
                raise RuntimeError(f"{config_node}: Path of non-optional 'rows' extracted nothing.")
            for child_data_node in extracted_data_nodes:  # 1 row per child_data_node.
                field2data_item = {}  # 1 row.
                for child_conf in ele_children:
                    self._r_extract(child_conf, child_data_node, field2data_item)
                # Merge with other 'rows' node.
                for field, data_item in field2data_item.items():
                    if field in res:
                        res[field].append(data_item)
                    else:
                        res[field] = [data_item]
        elif tag == "items":  # Returns {field1: data_item1, field2: data_item2, ...}
            if len(extracted_data_nodes) > 1:
                raise RuntimeError(f"{config_node}: There shouldn't be more than 1 extracted data nodes.")
            elif len(extracted_data_nodes) == 0:
                if not is_optional:
                    raise RuntimeError(f"{config_node}: Non-optional 'items' needs at least 1 "
                                       f"extracted data node.")
                extracted_data_nodes = [None]
            field2child_data_item = {}
            for child_conf in ele_children:
                self._r_extract(child_conf, extracted_data_nodes[0], field2child_data_item)
            # Update final result.
            res.update(field2child_data_item)
        elif tag == "itemAny":  # Returns {field: data_item}
            if len(extracted_data_nodes) == 0:
                if not is_optional:
                    raise Exception(f"{config_node}: Non-optional itemAny should provide "
                                    f"at lease 1 extracted data node.")
                res[field] = None
            elif len(ele_children) == 0:  # A leaf 'itemAny'.
                res[field] = extracted_data_nodes[0]
            else:  # Branch 'itemAny', extract data using child config nodes.
                for child_data_node in extracted_data_nodes:
                    for child_conf in ele_children:
                        field2child_data_item = {}
                        self._r_extract(child_conf, child_data_node, field2child_data_item)
                        child_res_value = field2child_data_item["value"]
                        if child_res_value:  # Not none.
                            res[field] = child_res_value
                            return
                if not is_optional:
                    raise RuntimeError(f"{config_node}: Non-optional itemAny should return 1 data node.")
                res[field] = None  # Nothing found.
        elif tag == "itemAll":  # Returns {field: data_item(of list type)}.
            # Collect items as list.
            if len(extracted_data_nodes) == 0 and not is_optional:
                raise RuntimeError(f"{config_node}: Non-optional itemAll should provide "
                                   f"at least 1 extracted data node.")
            items = []
            for child_data_node in extracted_data_nodes:
                if self._is_basic_data(child_data_node):
                    items.append(child_data_node)
                elif len(ele_children) == 0:  # No child extractor.
                    items = extracted_data_nodes
                else:  # Run child extractors.
                    for child_conf in ele_children:
                        field2child_data_item = {}
                        self._r_extract(child_conf, child_data_node, field2child_data_item)
                        child_data_item = next(iter(field2child_data_item.values()))
                        if child_data_item is not None:
                            items.append(child_data_item)
            if len(items) == 0:
                if not is_optional:
                    raise RuntimeError(f"{config_node}: Non-optional itemAll should return at lease 1 data item.")
                else:
                    res[field] = None
            else:
                res[field] = items  # List item. i.e. An item of list type.
        elif tag == "itemJoin":
            if len(extracted_data_nodes) == 0:
                if not is_optional:
                    raise RuntimeError(f"{config_node}: Non-optional itemJoin should provide "
                                       f"at least 1 extracted data node.")
                res[field] = None
                return
            data_strs = []
            for child_data_node in extracted_data_nodes:
                if self._is_basic_data(child_data_node):
                    data_strs.append(str(child_data_node))
                else:
                    for child_conf_node in ele_children:
                        field2child_data_item = {}
                        self._r_extract(child_conf_node, child_data_node, field2child_data_item)
                        child_data_item = next(iter(field2child_data_item.values()))
                        if child_data_item is not None:
                            data_strs.append(str(child_data_item))
            filtered: List[str] = []
            for s in data_strs:  # Strip string and remove empty string.
                stripped = s.strip()
                if stripped != "":
                    filtered.append(stripped)
            if len(filtered) == 0:
                if is_optional:
                    res[field] = None
                else:
                    raise f"{config_node}: Non-optional itemJoin should return 1 non-empty string."
            else:
                delimiter = config_node.get_attr("delimiter", ",")
                res[field] = delimiter.join(x.strip() for x in filtered)
        elif tag == "item":
            if len(extracted_data_nodes) > 1:
                raise Exception(f"{config_node}: 'item' node is forbidden extracting multiple pieces of data. "
                                f"Data extracted: [{', '.join(extracted_data_nodes)}]")
            elif len(extracted_data_nodes) == 0:
                if not is_optional:
                    raise RuntimeError(f"{config_node}: Non-optional 'item' should extract 1 data item.")
                res[field] = None  # Nothing found.
            else:  # == 1
                data_item = extracted_data_nodes[0]
                if not self._is_basic_data(data_item):
                    raise RuntimeError(f"{config_node}: Simple 'item' node should return some data of basic types. "
                                       f"Got {type(data_item)}.")
                res[field] = data_item
        else:
            raise NotImplementedError(f"Unsupported config node type '{config_node.tag}'")

    @staticmethod
    def _is_basic_data(data_item):
        return isinstance(data_item, (str, int, float, type(None)))

    @staticmethod
    def _remove_empty_str(data_items: list):
        """
        Returns a new list instance.
        1. Remove 'space' or emtpy string from list.
        """
        res = []
        for x in data_items:
            if isinstance(x, str):
                if x.isspace() or x == "":
                    continue
            res.append(x)
        return res
