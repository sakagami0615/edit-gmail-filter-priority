import xml.etree.ElementTree as ET
from typing import Union

INDENT = "\t"


class XML:
    def __init__(self, filter_xml_path: Union[str, None] = None):
        self._tree: Union[ET.ElementTree, None] = None
        if filter_xml_path:
            self.read(filter_xml_path)

    @property
    def tree(self):
        return self._tree

    @tree.setter
    def tree(self, tree: ET.ElementTree) -> None:
        if isinstance(tree, ET.ElementTree):
            self._tree = tree

    def read(self, filter_xml_path: str) -> None:
        self._tree = ET.parse(filter_xml_path)

    def write(self, filter_xml_path: str) -> None:
        ET.indent(self._tree, INDENT)
        self._tree.write(filter_xml_path, encoding="UTF-8", xml_declaration=True)
