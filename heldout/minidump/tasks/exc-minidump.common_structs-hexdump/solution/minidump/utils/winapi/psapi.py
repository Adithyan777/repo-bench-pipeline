from minidump.utils.winapi.defines import *  # noqa: F403


# typedef struct _MODULEINFO {
#   LPVOID lpBaseOfDll;
#   DWORD  SizeOfImage;
#   LPVOID EntryPoint;
# } MODULEINFO, *LPMODULEINFO;
class MODULEINFO(Structure):  # noqa: F405
    _fields_ = [
        ("lpBaseOfDll", LPVOID),  # remote pointer  # noqa: F405
        ("SizeOfImage", DWORD),  # noqa: F405
        ("EntryPoint", LPVOID),  # remote pointer  # noqa: F405
    ]


LPMODULEINFO = POINTER(MODULEINFO)  # noqa: F405


# BOOL WINAPI EnumProcessModules(
#   __in   HANDLE hProcess,
#   __out  HMODULE *lphModule,
#   __in   DWORD cb,
#   __out  LPDWORD lpcbNeeded
# );
def EnumProcessModules(hProcess):
    _EnumProcessModules = windll.psapi.EnumProcessModules  # noqa: F405
    _EnumProcessModules.argtypes = [HANDLE, LPVOID, DWORD, LPDWORD]  # noqa: F405
    _EnumProcessModules.restype = bool
    _EnumProcessModules.errcheck = RaiseIfZero  # noqa: F405

    size = 0x1000
    lpcbNeeded = DWORD(size)  # noqa: F405
    unit = sizeof(HMODULE)  # noqa: F405
    while 1:
        lphModule = (HMODULE * (size // unit))()  # noqa: F405
        _EnumProcessModules(hProcess, byref(lphModule), lpcbNeeded, byref(lpcbNeeded))  # noqa: F405
        needed = lpcbNeeded.value
        if needed <= size:
            break
        size = needed
    return [lphModule[index] for index in range(0, int(needed // unit))]


def GetModuleFileNameExW(hProcess, hModule=None):
    _GetModuleFileNameExW = ctypes.windll.psapi.GetModuleFileNameExW  # noqa: F405
    _GetModuleFileNameExW.argtypes = [HANDLE, HMODULE, LPWSTR, DWORD]  # noqa: F405
    _GetModuleFileNameExW.restype = DWORD  # noqa: F405

    nSize = MAX_PATH  # noqa: F405
    while 1:
        lpFilename = ctypes.create_unicode_buffer("", nSize)  # noqa: F405
        nCopied = _GetModuleFileNameExW(hProcess, hModule, lpFilename, nSize)
        if nCopied == 0:
            raise ctypes.WinError()  # noqa: F405
        if nCopied < (nSize - 1):
            break
        nSize = nSize + MAX_PATH  # noqa: F405
    return lpFilename.value


# BOOL WINAPI GetModuleInformation(
#   __in   HANDLE hProcess,
#   __in   HMODULE hModule,
#   __out  LPMODULEINFO lpmodinfo,
#   __in   DWORD cb
# );
def GetModuleInformation(hProcess, hModule, lpmodinfo=None):
    _GetModuleInformation = windll.psapi.GetModuleInformation  # noqa: F405
    _GetModuleInformation.argtypes = [HANDLE, HMODULE, LPMODULEINFO, DWORD]  # noqa: F405
    _GetModuleInformation.restype = bool
    _GetModuleInformation.errcheck = RaiseIfZero  # noqa: F405

    if lpmodinfo is None:
        lpmodinfo = MODULEINFO()
    _GetModuleInformation(hProcess, hModule, byref(lpmodinfo), sizeof(lpmodinfo))  # noqa: F405
    return lpmodinfo
