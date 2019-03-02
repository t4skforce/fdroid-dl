import os
import unittest
from fdroid_dl.model import Config
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

class ConfigTestSuite(unittest.TestCase):

    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch.object(Config, 'save')
    def test_prepare_dirs(self, save, exists, makedirs):
        exists.return_value = False
        with Config() as c:
            exists.assert_any_call('./repo')
            exists.assert_any_call('./metadata')
            exists.assert_any_call('.cache')
            makedirs.assert_any_call('./repo')
            makedirs.assert_any_call('./metadata')
            makedirs.assert_any_call('.cache')
            self.assertEqual(c.filename, 'fdroid-dl.json')
            self.assertEqual(c.repo_dir, './repo')
            self.assertEqual(c.metadata_dir, './metadata')
            self.assertEqual(c.cache_dir, '.cache')
            self.assertIsNot(c.get('f-droid'), None)
            self.assertEqual([x for x in iter(c)],
                             [x for x in iter(Config.DEFAULTS)])
            assert not save.called
        assert save.called
