import unittest
import io

import taskqueue.confparser

TEST_CONFIG = """
[DEFAULT]
non_override = defvalue
key1 = value1
override = defvalue

[section]
key1 = section_value1
key2 = section_value2
"""

class TestConfigParser(unittest.TestCase):
    """Tests for ConfigParser."""

    def setUp(self):
        pass

    def test_items(self):
        """Test ConfigParser.items()."""

        cfg = taskqueue.confparser.ConfigParser()
        cfg.readfp(io.BytesIO(TEST_CONFIG))

        items = cfg.items("section")
        items.sort()
        self.assertEqual([
            ("key1", "section_value1"),
            ("key2", "section_value2"),
            ("non_override", "defvalue"),
            ("override", "defvalue")
        ], items)

        items = cfg.items("section", defaults={})
        items.sort()
        self.assertEqual([
            ("key1", "section_value1"),
            ("key2", "section_value2")
        ], items)

        items = cfg.items("section", defaults={"override": "overridden"})
        items.sort()
        self.assertEqual([
            ("key1", "section_value1"),
            ("key2", "section_value2"),
            ("override", "overridden")
        ], items)
