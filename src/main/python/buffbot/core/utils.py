import os
import string


WINDOWS = os.name == "nt"


if WINDOWS:
    import msvcrt
    import win32file
    import win32gui
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

    def write_command(command):
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
