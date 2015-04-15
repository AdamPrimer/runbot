from __future__ import (absolute_import, print_function, division,
                        unicode_literals)
import os
import unittest
from plugins.runbot.config import (
    RunBotConfig,
    RunBotConfigDict,
)

class RunBotConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.config = RunBotConfig('test.conf')
        self.config2 = RunBotConfig('test2.conf')

    def test_list_add_str(self):
        self.config.list_add('variable1', 'Vulajin')
        self.config2._config.update({
            'variable1': {
                'vulajin': 'Vulajin'
            }
        })
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_list_add_int(self):
        self.config.list_add('variable1', 1)
        self.config2._config.update({
            'variable1': {
                1: 1 
            }
        })
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_list_add_tuple(self):
        self.config.list_add('variable1', ('Vulajin', 1234))
        self.config2._config.update({
            'variable1': {
                'vulajin': ['Vulajin', 1234]
            }
        })
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_list_rm_str(self):
        self.config.list_add('variable1', 'Vulajin')
        self.config.list_rm('variable1', 'Vulajin')
        self.config2._config.update({
            'variable1': {}
        })
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_list_rm_int(self):
        self.config.list_add('variable1', 1)
        self.config.list_rm('variable1', 1)
        self.config2._config.update({
            'variable1': {}
        })
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_list_rm_tuple(self):
        self.config.list_add('variable1', ('Vulajin', 1234))
        self.config.list_rm('variable1', ('Vulajin', 1234))
        self.config2._config.update({
            'variable1': {}
        })
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_list_rm_key_tuple(self):
        self.config.list_add('variable1', ('Vulajin', 1234))
        self.config.list_rm('variable1', 'Vulajin')
        self.config2._config.update({
            'variable1': {}
        })
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_list_rm_key_tuple_case_insensitive(self):
        self.config.list_add('variable1', ('Vulajin', 1234))
        self.config.list_rm('variable1', 'VULAJIN')
        self.config2._config.update({
            'variable1': {}
        })
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_list_rm_tuple_case_insensitive(self):
        self.config.list_add('variable1', ('Vulajin', 1234))
        self.config.list_rm('variable1', ('VULAJIN', 1234))
        self.config2._config.update({
            'variable1': {}
        })
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_list_rm_tuple_mismatch(self):
        self.config.list_add('variable1', ('Vulajin', 1234))
        
        exception_raise = False
        try:
            self.config.list_rm('variable1', ('Vulajin', 12345))
        except KeyError as e:
            exception_raised = True
            pass

        self.config2._config.update({
            'variable1': {
                'vulajin': ['Vulajin', 1234]
            }
        })
        self.assertTrue(exception_raised)
        self.assertEquals(repr(self.config), repr(self.config2))

    def test_save_and_load(self):
        self.config.list_add('variable1', ('Vulajin', 1234))
        self.config2.list_add('variable1', ('Vulajin', 1234))

        self.config.save()
        
        config3 = RunBotConfig('test.conf')
        self.assertEqual(repr(self.config), repr(config3))
        self.assertEqual(repr(self.config2), repr(config3))

    def test_get(self):
        self.config.list_add('variable1', 'Vulajin')
        self.assertEquals(repr(self.config.variable1), repr({
            'vulajin': 'Vulajin'
        }))

    def tearDown(self):
        if os.path.exists('test.conf'):
            os.remove('test.conf')
        if os.path.exists('test2.conf'):
            os.remove('test2.conf')

class RunBotConfigDictTestCase(unittest.TestCase):
    def setUp(self):
        self.rbd = RunBotConfigDict()
    
    def test_append(self):
        self.rbd.append(('Vulajin', 1234))
        self.rbd.append(('Gilmore', 9999))

        self.assertEquals(repr(self.rbd), repr({
            'vulajin': ['Vulajin', 1234],
            'gilmore': ['Gilmore', 9999],
        }))

    def test_append_update(self):
        self.rbd.append(('Vulajin', 1234))
        self.rbd.append(('Vulajin', 123456))

        self.assertEquals(repr(self.rbd), repr({
            'vulajin': ['Vulajin', 123456],
        }))

    def test_append_case_insensitive_update(self):
        self.rbd.append(('Vulajin', 1234))
        self.rbd.append(('vuLajin', 123456))

        self.assertEquals(repr(self.rbd), repr({
            'vulajin': ['vuLajin', 123456],
        }))

    def test_add_str(self):
        self.rbd.append("Item1")
        self.rbd.append("Item2")

        self.assertEquals(repr(self.rbd), repr({
            'item1': "Item1",
            'item2': "Item2"
        }))

    def test_add_int(self):
        self.rbd.append(1)
        self.rbd.append(2)

        self.assertEquals(repr(self.rbd), repr({
            1: 1,
            2: 2 
        }))

    def test_add_mixed(self):
        self.rbd.append(('Vulajin', 1234))
        self.rbd.append(1234)
        self.rbd.append("AdamPrimer")
        self.rbd.append(("Celestics", ))
        self.rbd.append(["mrasmus"])

        self.assertEquals(repr(self.rbd), repr({
            "vulajin": ["Vulajin", 1234],
            1234: 1234,
            "adamprimer": "AdamPrimer",
            "celestics": ["Celestics"],
            "mrasmus": ["mrasmus"],
        }))

    def test_contains(self):
        # Test contains on empty
        self.assertFalse('Vulajin' in self.rbd)

        self.rbd.append(('Vulajin', 1234));

        # Test case insensitive
        self.assertTrue('Vulajin' in self.rbd)
        self.assertTrue('vulajin' in self.rbd)
        self.assertTrue('vulAjin' in self.rbd)

        # Test listy of length one
        self.assertTrue(['vulAjin'] in self.rbd)
        self.assertTrue(('vulAjin', ) in self.rbd)
        
        # Test value match
        self.assertTrue(('vulAjin', 1234) in self.rbd)

        # Test value mismatch
        self.assertFalse(('Vulajin', 12345) in self.rbd)
        self.assertFalse(('vulAjin', 12345) in self.rbd)

        # Test not in
        self.assertFalse('Celestics' in self.rbd)
        self.assertFalse(('Celestics', 1234) in self.rbd)

    def test_iter(self):
        items = [
            'item1', 'item2', 'item3', 'item4'
        ]
        for item in items:
            self.rbd.append(item)

        _items = [item for item in self.rbd]

        self.assertEquals(sorted(items), sorted(_items))

    def test_iter_case(self):
        items = [
            'Item1', 'Item2', 'Item3', 'Item4'
        ]
        for item in items:
            self.rbd.append(item)

        _items = [item for item in self.rbd]

        self.assertEquals(sorted(items), sorted(_items))
    
    def test_iter_tuple(self):
        items = [
            ('Item1', 3), ('Item2', 5), ('Item3', 7), ('Item4', 9)
        ]
        for item in items:
            self.rbd.append(item)

        _items = [item for item in self.rbd]

        self.assertEquals(sorted(map(list, items)), sorted(_items))

    def test_get(self):
        self.rbd.append(('Vulajin', 1234));
        self.assertEquals(self.rbd['Vulajin'], ['Vulajin', 1234])
        self.assertEquals(self.rbd['vulajin'], ['Vulajin', 1234])
        self.assertEquals(self.rbd['vuLAjin'], ['Vulajin', 1234])

if __name__ == "__main__":
    unittest.main()
