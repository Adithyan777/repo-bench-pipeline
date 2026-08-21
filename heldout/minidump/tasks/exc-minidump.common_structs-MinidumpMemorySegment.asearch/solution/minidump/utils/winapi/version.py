import ctypes
from ctypes import Structure, byref, windll

from minidump.utils.winapi.defines import *  # noqa: F403


class _SYSTEM_INFO_OEM_ID_STRUCT(Structure):
    _fields_ = [
        ("wProcessorArchitecture", WORD),  # noqa: F405
        ("wReserved", WORD),  # noqa: F405
    ]


class _SYSTEM_INFO_OEM_ID(Union):  # noqa: F405
    _fields_ = [
        ("dwOemId", DWORD),  # noqa: F405
        ("w", _SYSTEM_INFO_OEM_ID_STRUCT),
    ]


class SYSTEM_INFO(Structure):
    _fields_ = [
        ("id", _SYSTEM_INFO_OEM_ID),
        ("dwPageSize", DWORD),  # noqa: F405
        ("lpMinimumApplicationAddress", LPVOID),  # noqa: F405
        ("lpMaximumApplicationAddress", LPVOID),  # noqa: F405
        ("dwActiveProcessorMask", DWORD_PTR),  # noqa: F405
        ("dwNumberOfProcessors", DWORD),  # noqa: F405
        ("dwProcessorType", DWORD),  # noqa: F405
        ("dwAllocationGranularity", DWORD),  # noqa: F405
        ("wProcessorLevel", WORD),  # noqa: F405
        ("wProcessorRevision", WORD),  # noqa: F405
    ]

    def __get_dwOemId(self):
        return self.id.dwOemId

    def __set_dwOemId(self, value):
        self.id.dwOemId = value

    dwOemId = property(__get_dwOemId, __set_dwOemId)

    def __get_wProcessorArchitecture(self):
        return self.id.w.wProcessorArchitecture

    def __set_wProcessorArchitecture(self, value):
        self.id.w.wProcessorArchitecture = value

    wProcessorArchitecture = property(
        __get_wProcessorArchitecture, __set_wProcessorArchitecture
    )


LPSYSTEM_INFO = ctypes.POINTER(SYSTEM_INFO)


class OSVERSIONINFOW(Structure):
    _fields_ = [
        ("dwOSVersionInfoSize", DWORD),  # noqa: F405
        ("dwMajorVersion", DWORD),  # noqa: F405
        ("dwMinorVersion", DWORD),  # noqa: F405
        ("dwBuildNumber", DWORD),  # noqa: F405
        ("dwPlatformId", DWORD),  # noqa: F405
        ("szCSDVersion", WCHAR * 128),  # noqa: F405
    ]


class OSVERSIONINFOEXW(Structure):
    _fields_ = [
        ("dwOSVersionInfoSize", DWORD),  # noqa: F405
        ("dwMajorVersion", DWORD),  # noqa: F405
        ("dwMinorVersion", DWORD),  # noqa: F405
        ("dwBuildNumber", DWORD),  # noqa: F405
        ("dwPlatformId", DWORD),  # noqa: F405
        ("szCSDVersion", WCHAR * 128),  # noqa: F405
        ("wServicePackMajor", WORD),  # noqa: F405
        ("wServicePackMinor", WORD),  # noqa: F405
        ("wSuiteMask", WORD),  # noqa: F405
        ("wProductType", BYTE),  # noqa: F405
        ("wReserved", BYTE),  # noqa: F405
    ]


def GetSystemInfo():
    _GetSystemInfo = windll.kernel32.GetSystemInfo
    _GetSystemInfo.argtypes = [LPSYSTEM_INFO]
    _GetSystemInfo.restype = None

    sysinfo = SYSTEM_INFO()
    _GetSystemInfo(byref(sysinfo))
    return sysinfo


def GetVersionExW():
    _GetVersionExW = windll.kernel32.GetVersionExW
    _GetVersionExW.argtypes = [POINTER(OSVERSIONINFOEXW)]  # noqa: F405
    _GetVersionExW.restype = bool
    _GetVersionExW.errcheck = RaiseIfZero  # noqa: F405

    osi = OSVERSIONINFOEXW()
    osi.dwOSVersionInfoSize = sizeof(osi)  # noqa: F405
    try:
        _GetVersionExW(byref(osi))
    except OSError:
        osi = OSVERSIONINFOW()
        osi.dwOSVersionInfoSize = sizeof(osi)  # noqa: F405
        _GetVersionExW.argtypes = [POINTER(OSVERSIONINFOW)]  # noqa: F405
        _GetVersionExW(byref(osi))
    return osi


def GetFileVersionInfoW(lptstrFilename):
    _GetFileVersionInfoW = windll.version.GetFileVersionInfoW
    _GetFileVersionInfoW.argtypes = [LPWSTR, DWORD, DWORD, LPVOID]  # noqa: F405
    _GetFileVersionInfoW.restype = bool
    _GetFileVersionInfoW.errcheck = RaiseIfZero  # noqa: F405

    _GetFileVersionInfoSizeW = windll.version.GetFileVersionInfoSizeW
    _GetFileVersionInfoSizeW.argtypes = [LPWSTR, LPVOID]  # noqa: F405
    _GetFileVersionInfoSizeW.restype = DWORD  # noqa: F405
    _GetFileVersionInfoSizeW.errcheck = RaiseIfZero  # noqa: F405

    dwLen = _GetFileVersionInfoSizeW(lptstrFilename, None)
    lpData = ctypes.create_string_buffer(dwLen)  # not a string!
    _GetFileVersionInfoW(lptstrFilename, 0, dwLen, byref(lpData))
    return lpData
