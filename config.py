# -*- coding: utf-8 -*-
# @Time         : 14:52 2021/11/10
# @Author       : Chris
# @Description  :
import _datetime
import copy
import json
import os.path
from lxml import etree
from lxml.etree import _ElementTree as XmlDocument
from lxml.etree import _Attrib as XmlAttribute
from lxml.etree import _Element as XmlElement
from lxml.etree import _Comment as XmlComment
from string import Template
from typing import Dict, List, Union
import glob
import yaml


class CascadeConfig:
    """
    层叠配置。设计目标是减少配置冗余。
    """
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config'))

    def __init__(self, site_id: str, bases: List[str] = ("default",)):
        """
        :param site_id: Top level folder name of the set of config files under 'root'.
        :param bases: Base sites of this config site.
            The first base site has the highest priority when cascading.
            The lower the second one and so on.
        """
        self.root = CascadeConfig.ROOT
        self.site_id = site_id
        self._site_seq = [site_id, *bases]  # The highest priority to the lowest priority.
        self._dynamic_config = {}

    def read_text(self, rel_path: str, **top_side_conf) -> str:
        """
        读取文本配置。文本配置可以附有JSON格式子配置文件。子配置文件的命名规则为：文本配置文件名.json。注意：文本配置文件名包含扩展名。
        Side config priority: top > dynamic > exclusive > exclusive common > base > base common.
        :param top_side_conf: Top side config, a config which has the highest priority.
        :param rel_path: The relative path of config file. e.g: sqls/abc.sql
        :return: The built config string.
        """
        # 1. Read Cascaded side config.
        cascade_paths = self._get_cascade_paths(rel_path)
        side_conf_paths = [y
                           for x in reversed(cascade_paths)  # Base of the lowest priority first.
                           for y in [f'{os.path.dirname(x)}/common.json', f'{x}.json']]
        kwargs = self._get_global_side_config_dict()
        for path in side_conf_paths:
            if not os.path.isfile(path):
                continue
            with open(path, 'r', encoding='utf-8') as f:
                conf_dict = json.load(f)
                kwargs.update(conf_dict)
        kwargs.update(self._dynamic_config)
        kwargs.update(top_side_conf)  # Top side config has the highest priority.
        # 2. Load master text config file.
        conf_text = None
        for path in cascade_paths:  # Exclusive first.
            if not os.path.isfile(path):
                continue
            with open(path, 'r', encoding='utf-8') as f:
                conf_text = f.read()
                break
        if conf_text is None:
            raise FileNotFoundError(f'找不到配置 {self.root}/{"|".join(self._site_seq)}/{rel_path}')
        # 3. Fill master config text with side config parameters.
        try:
            if rel_path.endswith(".json"):  # There's something special required to do for json plain config.
                conf_text = Template(conf_text).substitute(**kwargs)
            else:
                conf_text = conf_text.format(**kwargs)
            return conf_text
        except KeyError as ke:
            args_str = str.join(', ', ke.args)
            raise KeyError(f'读取配置 "{rel_path}" 时出错, 缺少参数 "{args_str}"！')
        finally:
            pass

    def read_json(self, rel_path: str) -> Union[dict, list]:
        """
        Read json text file and fill the text with named arguments provided by this config. Then deserialize the \
        formatted text as python object.
        :param rel_path:
        :return:
        """
        str_json = self.read_text(rel_path)
        obj = json.loads(str_json)
        return obj

    def read_json_fortified(self, rel_path: str) -> dict:
        """
        Strong cascading. The cascaded config dicts will be stacked from bottom to top.
        :param rel_path:
        :return:
        """
        cascade_paths = self._get_cascade_paths(rel_path)
        result = {}
        for path in reversed(cascade_paths):
            if not os.path.isfile(path):
                continue
            with open(path, 'r', encoding='utf-8') as f:
                json_dict = json.load(f)
                result.update(json_dict)
        return result

    def write_json(self, obj, rel_path):
        path = self.detect_abs_path(rel_path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent='\t')

    def read_xml(self, rel_path: str) -> XmlDocument:
        xml_conf = XmlConfig(self)
        return xml_conf.load(rel_path)

    def read_yaml(self, rel_path: str) -> Union[dict, list]:
        """
        Read yaml text file and fill the text with named arguments provided by this config. Then serialize the \
        formatted text as python object.
        :param rel_path:
        :return:
        """
        str_yml = self.read_text(rel_path)
        obj = yaml.safe_load(str_yml)
        return obj

    def format(self, tpl_string: str, **kwargs) -> str:
        """
        Use parameters stored in config to format a string. 'kwargs' are included.
        Return 'None' when tpl_string is None.
        """
        if tpl_string is None:
            return None
        kwargs.update(self._get_global_side_config_dict())
        kwargs.update(self._dynamic_config)
        return Template(tpl_string).substitute(**kwargs)

    def list_dir(self, rel_dir: str, pattern="*") -> List[str]:
        """List files inside the given directory. Return list of relative file paths."""
        abs_dir = self.detect_abs_path(rel_dir)
        return [f"{rel_dir}/{x}" for x in glob.glob1(abs_dir, pattern)]

    def detect_abs_path(self, rel_path: str) -> str:
        """
        Detect config file path of given 'rel_path'
        :param rel_path:
        :return: Absolute path of hit config file.
        """
        paths = self._get_cascade_paths(rel_path)
        for path in reversed(paths):
            if os.path.exists(path):
                return path
        raise FileNotFoundError(f'找不到配置文件或目录 "{self.root}/{"|".join(self._site_seq)}/{rel_path}"。')

    def _get_cascade_paths(self, rel_path: str):
        """From the highest priority to the lowest priority."""
        return [f'{self.root}/{x}/{rel_path}' for x in self._site_seq]

    def _get_global_side_config_dict(self) -> dict:
        """
        Global side config。The config items are usually dynamic, such as date and time.
        :return: A newly created dict with config items.
        """
        sc_dict = {}
        # 日期
        today = _datetime.date.today()
        date_format = "%Y%m%d"
        sc_dict['yesterday'] = (today + _datetime.timedelta(days=-1)).strftime(date_format)
        sc_dict['today'] = today.strftime(date_format)
        sc_dict['tomorrow'] = (today + _datetime.timedelta(days=1)).strftime(date_format)
        # site_id
        sc_dict['site_id'] = self.site_id
        # Environment variables.
        sc_dict['FISHING_DATA'] = os.environ.get("FISHING_DATA")
        return sc_dict

    def __setitem__(self, key, value):
        """
        Push dynamic config.
        :param key:
        :param value:
        :return:
        """
        self._dynamic_config[key] = value


class XmlConfig:
    def __init__(self, parent: CascadeConfig):
        self.parent = parent

    def load(self, rel_path: str) -> XmlDocument:
        doc: XmlDocument = self._r_compile(os.path.dirname(rel_path), os.path.basename(rel_path), {}, set())
        root: XmlElement = doc.getroot()
        for c in list(root.iterchildren("import")):  # Remove imports.
            root.remove(c)
        return doc

    def abspath(self, rel_working_dir: str, rel_file_path: str):
        rel_path = f"{rel_working_dir}/{rel_file_path}" if rel_working_dir.strip() else rel_file_path
        abs_path = f"{self.parent.root}/{rel_path}" if rel_path.startswith("/") \
            else self.parent.detect_abs_path(rel_path)
        return os.path.abspath(abs_path)  # Format path.

    def _r_compile(self, rel_wd: str, rel_fp: str, path2doc: Dict[str, XmlDocument], ref_set: set) -> XmlDocument:
        # 1 Load file.
        abs_path = self.abspath(rel_wd, rel_fp)
        xml_doc: XmlDocument = etree.parse(abs_path)
        root: XmlElement = xml_doc.getroot()
        ref_set.add(abs_path)
        # 2 Import.
        imports: Dict[str, XmlDocument] = {"self": xml_doc}
        for c in root.iterchildren("import"):
            c: XmlElement
            import_rel_path = c.get("file")
            import_abs_path = self.abspath(rel_wd, c.get("file"))
            if import_abs_path in ref_set:
                raise Exception(f"Circular reference found! File: '{abs_path}' and '{import_abs_path}'")
            as_ = c.get("as")
            if as_ == "self":
                raise KeyError("Import-as name is conflict with built-in keyword 'self'!")
            imports[as_] = path2doc.get(import_abs_path) or \
                           self._r_compile(rel_wd, import_rel_path, path2doc, ref_set)
        for import_ele in list(root.iterchildren("import")):
            root.remove(import_ele)
        # 3 Compile elements.
        self._r_compile_node(root, imports)
        path2doc[abs_path] = xml_doc
        ref_set.remove(abs_path)
        return xml_doc

    def _r_compile_node(self, node: XmlElement, imports: Dict[str, XmlDocument]):
        org_children = list(node.iterchildren())
        # 1 Inherit.
        extends: str = node.get("_extends_")
        if extends is not None:
            doc_name, xpath = extends.split("::", 1)
            doc_import: XmlDocument = imports.get(doc_name)
            if doc_import is None:
                raise Exception(f"XML: Document named '{doc_name}' not imported!")
            supers = doc_import.xpath(xpath)
            if len(supers) == 0:
                raise Exception(f"XML: Unable to inherit. Element at '{extends}' not found!")
            elif len(supers) > 1:
                cr_lf = "\r\n"
                raise Exception(f"XML: Unable to inherit multiple elements at '{extends}'!\r\n"
                                f"Elements found: \r\n{cr_lf.join(self.desc(x) for x in supers)}")
            super_ele: XmlElement = supers[0]
            # 1.1 Inherit attributes.
            for name, value in super_ele.attrib.iteritems():
                if not node.get(name):
                    node.set(name, value)  # Use parent's attribute if absent.
            # 1.2 Inherit child elements.
            for super_child in super_ele.iterchildren():
                node.append(copy.deepcopy(super_child))
            # 1.3 Delete meta attribute.
            del node.attrib["_extends_"]
        # 2 Override.
        override: str = node.get("_override_")
        if override is not None:
            members: list = node.getparent().xpath(override)
            if node in members:
                members.remove(node)
            if len(members) == 0:
                raise Exception(f"XML: Unable to find overriding target member '{override}'. \r\n"
                                f"Element: {self.desc(node)}")
            elif len(members) > 1:
                raise Exception(f"XML: Cannot override multiple target members. "
                                f"Query='{override}'. Element: \r\n{self.desc(node)}")
            node.getparent().remove(members[0])  # Delete overridden member from parent's children.
            del node.attrib["_override_"]  # Delete meta attribute.
        # 3 Recurse.
        for child in org_children:
            self._r_compile_node(child, imports)

    @staticmethod
    def desc(ele: XmlElement) -> str:
        return str(etree.tostring(ele, encoding="utf-8", pretty_print=True), encoding="utf-8")
