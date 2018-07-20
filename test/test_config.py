import unittest
import fdroid_dl
from unittest.mock import patch


class ConfigTestSuite(unittest.TestCase):

    @patch('os.makedirs')
    @patch.object(fdroid_dl.Config, 'save')
    def test_prepare_dirs(self, save, makedirs):
        print(save, makedirs)
        with fdroid_dl.Config() as c:
            makedirs.assert_any_call('./repo', exist_ok=True)
            makedirs.assert_any_call('./metadata', exist_ok=True)
            makedirs.assert_any_call('.cache', exist_ok=True)
            self.assertEqual(c.filename, 'fdroid-dl.json')
            self.assertEqual(c.repo_dir, './repo')
            self.assertEqual(c.metadata_dir, './metadata')
            self.assertEqual(c.cache_dir, '.cache')
            self.assertIsNot(c.get('f-droid'), None)
            self.assertEqual([x for x in iter(c)],
                             [x for x in iter(fdroid_dl.Config.DEFAULTS)])
            assert not save.called
        assert save.called
