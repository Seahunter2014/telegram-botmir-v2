import ast
import unittest
from pathlib import Path
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
        tree = ast.parse((Path(__file__).parents[1] / "src" / "telegram_app.py").read_text(encoding="utf-8"))
        functions = {
            node.name: ast.unparse(node)
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertIn("is_private_chat", functions["admin_only"])
        self.assertIn("is_private_chat", functions["unknown_cmd"])
        self.assertIn("is_private_chat", functions["callback_handler"])
        self.assertIn("admin_only", functions["menu_text_handler"])

        # Every registered command must pass the private-admin guard, directly
        # or through the /help alias, before it can reply or change bot state.
        build_app = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "build_app"
        )
        command_functions = set()
        for node in ast.walk(build_app):
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "commands"
                for target in node.targets
            ) and isinstance(node.value, ast.List):
                for item in node.value.elts:
                    if isinstance(item, ast.Tuple) and len(item.elts) == 2 and isinstance(item.elts[1], ast.Name):
                        command_functions.add(item.elts[1].id)
        for name in command_functions:
            source = functions[name]
            self.assertTrue(
                "admin_only" in source or "start_cmd" in source,
                f"command handler {name} must enforce the private-admin guard",
            )


if __name__ == "__main__":
    unittest.main()

