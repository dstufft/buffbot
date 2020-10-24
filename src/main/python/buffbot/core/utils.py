# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import string


WINDOWS = os.name == "nt"


if WINDOWS:
    import msvcrt
    import win32clipboard
    import win32file
    import win32gui
    import pywintypes
    import pydirectinput as kb

    def shared_open(filename):
        handle = win32file.CreateFile(
            filename,
            win32file.GENERIC_READ,
            win32file.FILE_SHARE_DELETE
            | win32file.FILE_SHARE_READ
            | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
        detached_handle = handle.Detach()
        fd = msvcrt.open_osfhandle(detached_handle, os.O_RDONLY)

        return open(fd, encoding="utf8")

    _UPPERCASE_SYMBOLS = {
        "!": "1",
        "@": "2",
        "#": "3",
        "$": "4",
        "%": "5",
        "^": "6",
        "&": "7",
        "*": "8",
        "(": "9",
        ")": "0",
    }

    def _write_command_typed(command):
        for c in command:
            # Determine if this character needs the shift key entered or not,
            shifted = c in string.ascii_uppercase or c in _UPPERCASE_SYMBOLS

            # Determine the actual letter to type, it has to be the "lowercase"
            # variant to make it work.
            c = _UPPERCASE_SYMBOLS.get(c, c.lower())

            # Actually write out the character, holding down shift as required
            if shifted:
                kb.keyDown("shift", _pause=False)
            kb.press(c, _pause=False)
            if shifted:
                kb.keyUp("shift", _pause=False)

        kb.press("enter", _pause=False)

    def _write_command_paste(command):
        win32clipboard.OpenClipboard()
        win32clipboard.SetClipboardText(command)
        win32clipboard.CloseClipboard()

        kb.press("enter", _pause=False)
        kb.keyDown("ctrl", _pause=False)
        kb.press("v", _pause=False)
        kb.keyUp("ctrl", _pause=False)
        kb.press("enter", _pause=False)

    def write_command(command):
        try:
            _write_command_paste(command)
        except pywintypes.error:
            _write_command_typed(command)

    def is_current_window(window_name):
        handle = win32gui.GetForegroundWindow()
        name = win32gui.GetWindowText(handle)

        return window_name == name


else:

    def shared_open(filename):
        return open(filename, encoding="utf8")

    def write_command(command):
        raise NotImplementedError(
            "Writing commands is not implemented for non Windows platforms."
        )

    def is_current_window(window_name):
        return True
