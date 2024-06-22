class FilterXmlAdjuster:

    def __init__(self):
        pass

    def _read(sel, xml_path: str) -> list[str]:
        with open(xml_path, mode="r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines

    def _write(sel, xml_path: str, lines: str) -> None:
        with open(xml_path, mode="w", encoding="utf-8") as f:
            f.writelines(lines)

    def _get_tag_name(self, line: str) -> str:
        tokens = line.strip().replace("<", "").split(" ")
        tag_name = tokens[0]
        return tag_name

    def _double_quotation_to_single_quotation(self, line: str) -> str:
        line = line.replace('"', "'")
        return line

    def _add_close_tag(self, line: str) -> str:
        if " />" not in line:
            return line

        tag_name = self._get_tag_name(line)
        if tag_name == "apps:property":
            return line.replace(" />", "/>")

        return line.replace(" /", "").replace("\n", "") + f"</{tag_name}>\n"

    def _update_line(self, line: str) -> str:
        line = self._double_quotation_to_single_quotation(line)
        line = self._add_close_tag(line)
        return line

    def minor_adjustment(self, xml_path: str) -> None:
        lines = self._read(xml_path)
        update_lines = [self._update_line(line) for line in lines]
        self._write(xml_path, update_lines)
