import unittest
from types import SimpleNamespace

from src.security import is_private_chat


class PrivateAdminChatTests(unittest.TestCase):
    def test_only_private_chat_is_accepted(self):
        self.assertTrue(is_private_chat(SimpleNamespace(type="private")))
        self.assertFalse(is_private_chat(SimpleNamespace(type="group")))
        self.assertFalse(is_private_chat(SimpleNamespace(type="supergroup")))
        self.assertFalse(is_private_chat(SimpleNamespace(type="channel")))
        self.assertFalse(is_private_chat(None))


if __name__ == "__main__":
    unittest.main()
