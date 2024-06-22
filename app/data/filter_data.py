import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Union

from app.common.xml import XML


@dataclass
class FilterProperty:
    name: str
    value: str


@dataclass
class FilterEntry:
    category: str
    title: str
    id: str
    updated: str
    property: list[FilterProperty]


class FilterData(XML):

    ATOM_SYNDICATION_FORMAT_URL = "http://www.w3.org/2005/Atom"
    GOOGLE_SCHEMA_URL = "http://schemas.google.com/apps/2006"

    def __init__(self, filter_xml_path: Union[str, None] = None):
        super().__init__(filter_xml_path)
        self._entry_list = [] if filter_xml_path is None else self._get_entry_list()
        ET.register_namespace("", self.ATOM_SYNDICATION_FORMAT_URL)
        ET.register_namespace("apps", self.GOOGLE_SCHEMA_URL)

    @property
    def entry_list(self) -> list[FilterEntry]:
        return self._entry_list

    def _get_entry_list(self) -> list[FilterEntry]:
        root = self._tree.getroot()
        entry_list = []
        for entry in root.findall(f"{"{"}{self.ATOM_SYNDICATION_FORMAT_URL}{"}"}entry"):
            category = entry.find(f"{"{"}{self.ATOM_SYNDICATION_FORMAT_URL}{"}"}category").attrib[
                "term"
            ]
            title = entry.find(f"{"{"}{self.ATOM_SYNDICATION_FORMAT_URL}{"}"}title").text
            id = entry.find(f"{"{"}{self.ATOM_SYNDICATION_FORMAT_URL}{"}"}id").text
            updated = entry.find(f"{"{"}{self.ATOM_SYNDICATION_FORMAT_URL}{"}"}updated").text

            property_list = []
            for prop in entry.findall(f"{"{"}{self.GOOGLE_SCHEMA_URL}{"}"}property"):
                name = prop.get("name")
                value = prop.get("value")
                property_list.append(FilterProperty(name, value))

            entry_list.append(FilterEntry(category, title, id, updated, property_list))

        return entry_list

    def _update_entry_tree(self) -> None:
        """xml treeのentryの要素を更新する"""

        def append_entry_sub_element(elem, tag, value="", namespace=None, attributes={}):
            sub_elem = (
                ET.SubElement(elem, tag)
                if namespace is None
                else ET.SubElement(elem, f"{"{"}{self.GOOGLE_SCHEMA_URL}{"}"}{tag}")
            )
            sub_elem.text = value
            for key, value in attributes.items():
                sub_elem.set(key, value)

        def append_entry_element(root, entry):
            elem = ET.SubElement(root, "entry")
            append_entry_sub_element(elem, "category", attributes={"term": entry.category})
            append_entry_sub_element(elem, "title", entry.title)
            append_entry_sub_element(elem, "id", entry.id)
            append_entry_sub_element(elem, "updated", entry.updated)
            append_entry_sub_element(elem, "content")
            for property in entry.property:
                append_entry_sub_element(
                    elem,
                    "property",
                    namespace=self.GOOGLE_SCHEMA_URL,
                    attributes={"name": property.name, "value": property.value},
                )

        # entry要素を全削除する
        root = self._tree.getroot()
        for entry in root.findall(f"{"{"}{self.ATOM_SYNDICATION_FORMAT_URL}{"}"}entry"):
            root.remove(entry)
        # entry_listからentry要素を作成する
        for entry in self._entry_list:
            append_entry_element(root, entry)

    def to_table_data(self) -> list[list[str]]:
        def condition_string(name, value):
            return f"{name}:({value})"

        def others_string(name, value):
            return f"{name}:{"{"}{value}{"}"}"

        def get_property_data(properties):
            conditions = []
            label = "-"
            others = []
            for property in properties:
                if property.name in ["from", "subject"]:
                    conditions.append(condition_string(property.name, property.value))
                elif property.name == "label":
                    label = property.value
                elif property.name not in ["sizeOperator", "sizeUnit"]:
                    others.append(others_string(property.name, property.value))
            condition = ", ".join(conditions) if conditions else "-"
            process = ", ".join(others) if others else "-"
            return condition, label, process

        table_data = []
        for idx, entry in enumerate(self._entry_list):
            condition, label, process = get_property_data(entry.property)
            table_data.append([str(idx + 1), entry.category, condition, label, process])

        return table_data

    def sort_entry_list(self, index_list: list[int]) -> None:
        entry_list = []
        for idx in index_list:
            entry_list.append(self._entry_list[idx])
        self._entry_list = [entry for entry in entry_list]

    def import_xml(self, filter_xml_path: str) -> None:
        self.read(filter_xml_path)
        self._entry_list = self._get_entry_list()

    def export_xml(self, filter_xml_path: str) -> None:
        self._update_entry_tree()
        self.write(filter_xml_path)
