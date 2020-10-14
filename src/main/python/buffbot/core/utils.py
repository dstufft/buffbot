import os


WINDOWS = os.name == "nt"


if WINDOWS:
    import msvcrt
    import win32file

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


else:

    def shared_open(filename):
        return open(filename, encoding="utf8")
