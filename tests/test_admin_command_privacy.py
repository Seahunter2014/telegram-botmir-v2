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

    def test_public_response_paths_are_private_only(self):
        import ast
        from pathlib import Path

        tree = ast.parse((Path(__file__).parents[1] / "src" / "telegram_app.py").read_text(encoding="utf-8"))
        functions = {
            node.name: ast.unparse(node)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertIn("is_private_chat", functions["admin_only"])
        self.assertIn("is_private_chat", functions["unknown_cmd"])
        self.assertIn("is_private_chat", functions["callback_handler"])


if __name__ == "__main__":
    unittest.main()
