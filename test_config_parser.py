import unittest
from io import StringIO
import sys
from config_to_xml import ConfigParser


class TestConfigParser(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser()

    # Тест 1: Числа
    def test_number(self):
        text = "$[value: 42]"
        root = self.parser.parse(text)
        self.assertEqual(root[0].text, "42")

    # Тест 2: Строки
    def test_string(self):
        text = '$[message: q(Hello, World!)]'
        root = self.parser.parse(text)
        self.assertEqual(root[0].text, "Hello, World!")

    # Тест 3: Массивы
    def test_array(self):
        text = '$[items: {1, 2, q(three)}]'
        root = self.parser.parse(text)
        items = root[0]
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].text, "1")
        self.assertEqual(items[1].text, "2")
        self.assertEqual(items[2].text, "three")

    # Тест 4: Словари (вложенные)
    def test_dict(self):
        text = '$[user: $[name: q(Alice), age: 30]]'
        root = self.parser.parse(text)
        user = root[0]
        self.assertEqual(user[0].tag, "name")
        self.assertEqual(user[0].text, "Alice")
        self.assertEqual(user[1].tag, "age")
        self.assertEqual(user[1].text, "30")

    # Тест 5: Константы
    def test_constant(self):
        text = "let MAX = 100;\n$[limit: |MAX|]"
        root = self.parser.parse(text)
        self.assertEqual(root[0].text, "100")

    # Тест 6: Сложение в константных выражениях
    def test_addition(self):
        text = "let A = 10;\nlet B = 20;\n$[sum: |A + B|]"
        root = self.parser.parse(text)
        self.assertEqual(root[0].text, "30")

    # Тест 7: Функция abs()
    def test_abs(self):
        text = "let X = -42;\n$[abs_val: |abs(X)|]"
        root = self.parser.parse(text)
        self.assertEqual(root[0].text, "42")

    # Тест 8: Вложенные структуры
    def test_nested(self):
        text = """
        let DEFAULT = q(unknown);
        $[
          config: $[
            db: $[host: q(localhost), port: 5432],
            features: {q(auth), q(logging)},
            fallback: |DEFAULT|
          ]
        ]
        """
        root = self.parser.parse(text)
        config = root[0]
        db = config[0]
        self.assertEqual(db[0].text, "localhost")
        self.assertEqual(db[1].text, "5432")
        features = config[1]
        self.assertEqual(len(features), 2)
        self.assertEqual(features[0].text, "auth")