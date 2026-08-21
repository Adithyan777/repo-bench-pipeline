import io

from minidump.constants import MINIDUMP_TYPE
from minidump.exceptions import (
    MinidumpHeaderFlagsException,
    MinidumpHeaderSignatureMismatchException,
)


# https://msdn.microsoft.com/en-us/library/windows/desktop/ms680378(v=vs.85).aspx
class MinidumpHeader:
    def __init__(self):
        self.Signature: str = "PMDM"
        self.Version: int = None
        self.ImplementationVersion: int = None
        self.NumberOfStreams: int = None
        self.StreamDirectoryRva: int = None
        self.CheckSum: int = 0
        self.TimeDateStamp: int = 0
        self.Flags: MINIDUMP_TYPE = None

    def to_bytes(self):
        t = self.Signature.encode("ascii")
        t += self.Version.to_bytes(2, byteorder="little", signed=False)
        t += self.ImplementationVersion.to_bytes(2, byteorder="little", signed=False)
        t += self.NumberOfStreams.to_bytes(4, byteorder="little", signed=False)
        t += self.StreamDirectoryRva.to_bytes(4, byteorder="little", signed=False)
        t += self.CheckSum.to_bytes(4, byteorder="little", signed=False)
        t += self.TimeDateStamp.to_bytes(4, byteorder="little", signed=False)
        t += self.Flags.value.to_bytes(4, byteorder="little", signed=False)

        return t

    @staticmethod
    def parse(buff):
        mh = MinidumpHeader()
        mh.Signature = buff.read(4).decode()[::-1]
        if mh.Signature != "PMDM":
            raise MinidumpHeaderSignatureMismatchException(mh.Signature)
        mh.Version = int.from_bytes(buff.read(2), byteorder="little", signed=False)
        mh.ImplementationVersion = int.from_bytes(
            buff.read(2), byteorder="little", signed=False
        )
        mh.NumberOfStreams = int.from_bytes(
            buff.read(4), byteorder="little", signed=False
        )
        mh.StreamDirectoryRva = int.from_bytes(
            buff.read(4), byteorder="little", signed=False
        )
        mh.CheckSum = int.from_bytes(buff.read(4), byteorder="little", signed=False)
        mh.TimeDateStamp = int.from_bytes(
            buff.read(4), byteorder="little", signed=False
        )
        try:
            mh.Flags = MINIDUMP_TYPE(
                int.from_bytes(buff.read(4), byteorder="little", signed=False)
            )
        except Exception:
            raise MinidumpHeaderFlagsException("Could not parse header flags!")  # noqa: B904

        return mh

    @staticmethod
    async def aparse(abuff):
        adata = await abuff.read(32)
        buff = io.BytesIO(adata)
        return MinidumpHeader.parse(buff)

    def __str__(self):
        t = "== MinidumpHeader ==\n"
        t += "Signature: %s\n" % self.Signature  # noqa: UP031
        t += "Version: %s\n" % self.Version  # noqa: UP031
        t += "ImplementationVersion: %s\n" % self.ImplementationVersion  # noqa: UP031
        t += "NumberOfStreams: %s\n" % self.NumberOfStreams  # noqa: UP031
        t += "StreamDirectoryRva: %s\n" % self.StreamDirectoryRva  # noqa: UP031
        t += "CheckSum: %s\n" % self.CheckSum  # noqa: UP031
        t += "TimeDateStamp: %s\n" % self.TimeDateStamp  # noqa: UP031
        t += "Flags: %s\n" % self.Flags  # noqa: UP031
        return t
