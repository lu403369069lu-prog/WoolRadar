import unittest
from core.browser_guard import is_dedicated_chrome


class BrowserGuardTests(unittest.TestCase):
    def test_only_dedicated_absolute_profile_can_attach(self):
        profile = r'C:\WoolRadar\nodes\twitter-monitor\chrome-profile'
        self.assertTrue(is_dedicated_chrome('chrome.exe', f'chrome --user-data-dir="{profile}"', profile))
        for name, command in [('chrome.exe', 'chrome'), ('chrome.exe', 'chrome --user-data-dir="C:\\Users\\example-user\\daily"'),
                              ('other.exe', f'--user-data-dir="{profile}"'),
                              ('chrome.exe', f'--user-data-dir="{profile}-daily"')]:
            self.assertFalse(is_dedicated_chrome(name, command, profile))

    def test_relative_and_parent_paths_are_rejected(self):
        profile = r'C:\WoolRadar\nodes\twitter-monitor\chrome-profile'
        for path in ['chrome-profile', r'C:\WoolRadar\nodes\twitter-monitor\..\chrome-profile']:
            self.assertFalse(is_dedicated_chrome('chrome.exe', f'--user-data-dir="{path}"', profile))
