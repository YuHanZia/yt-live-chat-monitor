import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import storage


class StoragePathTests(unittest.TestCase):
    def test_frozen_app_uses_local_app_data(self):
        """Catches packaged builds writing settings into PyInstaller internals."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(sys, "frozen", True, create=True):
                with mock.patch.dict(os.environ, {"LOCALAPPDATA": temp_dir}):
                    self.assertEqual(
                        storage.get_data_dir(),
                        Path(temp_dir) / "YT直播留言監控" / "data",
                    )

    def test_source_app_uses_project_data(self):
        """Catches source development unexpectedly switching to user app data."""
        with mock.patch.object(sys, "frozen", False, create=True):
            self.assertEqual(
                storage.get_data_dir(),
                Path(storage.__file__).resolve().parent / "data",
            )

    def test_frozen_app_falls_back_to_windows_user_path(self):
        """Catches packaged startup failing when LOCALAPPDATA is unavailable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(sys, "frozen", True, create=True):
                with mock.patch.dict(os.environ, {}, clear=True):
                    with mock.patch.object(Path, "home", return_value=Path(temp_dir)):
                        self.assertEqual(
                            storage.get_data_dir(),
                            Path(temp_dir)
                            / "AppData"
                            / "Local"
                            / "YT直播留言監控"
                            / "data",
                        )


if __name__ == "__main__":
    unittest.main()
