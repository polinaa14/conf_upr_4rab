import re
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom


class ConfigParser:
    def __init__(self):
        self.constants = {}

    def parse(self, text):
        # Удаляем комментарии
        lines = []
        for line in text.split('\n'):
            if '\\' in line:
                line = line[:line.index('\\')]
            lines.append(line.strip())

        full_text = ' '.join(lines)

        # Сначала парсим все константы
        const_pattern = r'let\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+?);'
        for match in re.finditer(const_pattern, full_text):
            name = match.group(1)
            expr = match.group(2).strip()
            self.constants[name] = self._evaluate_expression(expr)

        # Удаляем константы из текста
        full_text = re.sub(r'let\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*.+?;', '', full_text)
        full_text = full_text.strip()

        if not full_text:
            return ET.Element('config')

        root = ET.Element('config')

        # Парсим основную структуру
        self._parse_structure(full_text, root)

        return root

    def _evaluate_expression(self, expr):
        expr = expr.strip()

        # Убираем внешние | если есть
        if expr.startswith('|') and expr.endswith('|'):
            expr = expr[1:-1].strip()

        # Функция abs()
        if expr.startswith('abs(') and expr.endswith(')'):
            inner = expr[4:-1].strip()
            value = self._parse_value(inner)
            return abs(value)

        # Сложение
        if '+' in expr:
            parts = [p.strip() for p in expr.split('+')]
            if len(parts) == 2:
                left = self._parse_value(parts[0])
                right = self._parse_value(parts[1])
                return left + right

        # Просто значение
        return self._parse_value(expr)

    def _parse_value(self, value_str):
        value_str = value_str.strip()

        if not value_str:
            raise SyntaxError("Empty value")

        # Константа
        if value_str in self.constants:
            return self.constants[value_str]

        # Число
        if re.match(r'^-?\d+$', value_str):
            return int(value_str)

        # Строка q(...)
        if value_str.startswith('q('):
            if not value_str.endswith(')'):
                raise SyntaxError(f"Unclosed string: {value_str}")
            return value_str[2:-1]

        # Выражение в |...|
        if value_str.startswith('|') and value_str.endswith('|'):
            return self._evaluate_expression(value_str)

        # Массив
        if value_str.startswith('{'):
            if not value_str.endswith('}'):
                raise SyntaxError(f"Unclosed array: {value_str}")
            return self._parse_array(value_str[1:-1])

        # Словарь
        if value_str.startswith('$['):
            if not value_str.endswith(']'):
                raise SyntaxError(f"Unclosed dictionary: {value_str}")
            return self._parse_dict(value_str[2:-1])

        # Имя (должно быть константой)
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value_str):
            if value_str in self.constants:
                return self.constants[value_str]

        raise SyntaxError(f"Unknown value: {value_str}")

    def _parse_array(self, content):
        content = content.strip()
        if not content:
            return []

        items = []
        current = ''
        depth = 0

        for ch in content + ',':
            if ch == '{' or ch == '$' or ch == '(':
                depth += 1
            elif ch == '}' or ch == ']' or ch == ')':
                depth -= 1

            if ch == ',' and depth == 0:
                if current.strip():
                    items.append(self._parse_value(current.strip()))
                current = ''
            else:
                current += ch

        return items

    def _parse_dict(self, content):
        content = content.strip()
        if not content:
            return {}

        result = {}
        current_key = ''
        current_val = ''
        depth = 0
        in_key = True

        for ch in content + ',':
            if ch == '{' or ch == '$' or ch == '(':
                depth += 1
            elif ch == '}' or ch == ']' or ch == ')':
                depth -= 1

            if ch == ':' and depth == 0 and in_key:
                in_key = False
                continue

            if ch == ',' and depth == 0 and not in_key:
                key = current_key.strip()
                val = current_val.strip()

                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                    raise SyntaxError(f"Invalid key name: {key}")

                result[key] = self._parse_value(val)
                current_key = ''
                current_val = ''
                in_key = True
            elif in_key:
                current_key += ch
            else:
                current_val += ch

        return result

    def _parse_structure(self, text, parent):
        # Парсим словарь
        if text.startswith('$['):
            dict_data = self._parse_dict(text[2:-1])
            for key, value in dict_data.items():
                elem = ET.SubElement(parent, key)
                self._add_to_xml(value, elem)
        # Парсим массив
        elif text.startswith('{'):
            array_data = self._parse_array(text[1:-1])
            container = ET.SubElement(parent, 'items')
            for i, item in enumerate(array_data):
                item_elem = ET.SubElement(container, 'item')
                item_elem.set('index', str(i))
                self._add_to_xml(item, item_elem)

    def _add_to_xml(self, data, parent):
        if isinstance(data, dict):
            for key, value in data.items():
                elem = ET.SubElement(parent, key)
                self._add_to_xml(value, elem)
        elif isinstance(data, list):
            for item in data:
                item_elem = ET.SubElement(parent, 'item')
                self._add_to_xml(item, item_elem)
        else:
            parent.text = str(data)


def main():
    try:
        input_text = sys.stdin.read()
        parser = ConfigParser()
        root = parser.parse(input_text)
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        print(dom.toprettyxml(indent='  '))
    except SyntaxError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()