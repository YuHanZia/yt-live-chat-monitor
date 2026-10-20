import unittest
from tkinter import ttk

import customtkinter as ctk

import gui_app


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class TypographyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_app.App()
        cls.app.update()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    @staticmethod
    def font_size(widget):
        font = widget.cget("font")
        if hasattr(font, "cget"):
            return int(font.cget("size"))
        return int(font[1])

    def find_label(self, text):
        return next(
            widget
            for widget in descendants(self.app)
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == text
        )

    def test_title_and_section_font_sizes_match_readability_contract(self):
        self.assertEqual(self.font_size(self.find_label("YT 直播留言監控")), 26)
        for text in ("目前狀態", "監控設定", "追蹤名單"):
            with self.subTest(text=text):
                self.assertEqual(self.font_size(self.find_label(text)), 18)

    def test_inputs_and_buttons_use_readable_body_font(self):
        controls = [
            widget
            for widget in descendants(self.app)
            if isinstance(widget, (ctk.CTkEntry, ctk.CTkButton))
        ]
        self.assertTrue(controls)
        self.assertTrue(all(self.font_size(widget) >= 15 for widget in controls))

    def test_window_and_table_are_enlarged(self):
        self.assertTrue(self.app.geometry().startswith("920x920"))
        self.assertEqual((self.app._min_width, self.app._min_height), (760, 680))
        style = ttk.Style(self.app)
        self.assertEqual(int(style.lookup("Dark.Treeview", "rowheight")), 36)


if __name__ == "__main__":
    unittest.main()
