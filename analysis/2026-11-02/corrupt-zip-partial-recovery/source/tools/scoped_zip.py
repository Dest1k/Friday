"""Bounded, exact reads of stored/deflated members from an in-memory ZIP."""
import struct
import zlib
from zipfile import BadZipFile, ZIP_DEFLATED, ZIP_STORED


class ZipMemberLimitError(BadZipFile):
    """The declared or actual member output exceeds its allowed bound."""


class ZipMemberDataError(BadZipFile):
    """A structurally admitted member's bounded payload is corrupt.

    Header, name, overlap, encryption and resource-limit failures deliberately
    remain different errors. Only this class can support explicit salvage.
    """


def read_zip_member(archive, data, info, max_bytes):
    """Read one member without ZipExtFile's unbounded final inflater flush.

    ``archive`` must describe ``data``. Headers, names, overlap, actual sizes,
    CRC and exact deflate end-of-stream are checked before returning bytes.
    """
    if type(max_bytes) is not int or max_bytes < 0:
        raise ValueError('invalid ZIP member limit')
    if (info.filename != info.orig_filename or '\x00' in info.orig_filename):
        raise BadZipFile('Ambiguous ZIP member name')
    if info.file_size > max_bytes:
        raise ZipMemberLimitError('ZIP member limit')
    if info.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
        raise NotImplementedError('Unsupported ZIP compression')
    # Keep the standard library's local-name/header and overlap validation.
    # Opening and closing alone neither decompresses nor flushes the member.
    try:
        with archive.open(info):
            pass
    except UnicodeError:
        raise BadZipFile('Invalid ZIP member name encoding') from None
    offset = info.header_offset
    flags, method = struct.unpack_from('<HH', data, offset + 6)
    crc, compressed_size, file_size = struct.unpack_from('<III', data, offset + 14)
    name_size, extra_size = struct.unpack_from('<HH', data, offset + 26)
    extra_start = offset + 30 + name_size
    start = extra_start + extra_size
    if flags != info.flag_bits or method != info.compress_type:
        raise BadZipFile('Inconsistent ZIP member header')
    if not flags & 8:
        if 0xffffffff in (file_size, compressed_size):
            extra = data[extra_start:start]
            position = 0
            zip64 = None
            while position + 4 <= len(extra):
                kind, size = struct.unpack_from('<HH', extra, position)
                end = position + 4 + size
                if end > len(extra):
                    raise BadZipFile('Truncated ZIP64 member header')
                if kind == 1:
                    if zip64 is not None:
                        raise BadZipFile('Ambiguous ZIP64 member header')
                    zip64 = extra[position + 4:end]
                position = end
            if zip64 is None:
                raise BadZipFile('Missing ZIP64 member sizes')
            try:
                if file_size == 0xffffffff:
                    file_size, = struct.unpack_from('<Q', zip64)
                    zip64 = zip64[8:]
                if compressed_size == 0xffffffff:
                    compressed_size, = struct.unpack_from('<Q', zip64)
            except struct.error:
                raise BadZipFile('Truncated ZIP64 member sizes') from None
        if (crc, compressed_size, file_size) != (info.CRC, info.compress_size, info.file_size):
            raise BadZipFile('Inconsistent ZIP member sizes or CRC')
    else:
        # A streaming writer records the authoritative local sizes and CRC in
        # a descriptor after the compressed bytes. Never read into the next
        # member or central directory while validating it.
        zip64_descriptor = 0xffffffff in (file_size, compressed_size)
        for extra in (data[extra_start:start], info.extra):
            position = 0
            while position + 4 <= len(extra):
                kind, size = struct.unpack_from('<HH', extra, position)
                position += 4 + size
                if position > len(extra):
                    raise BadZipFile('Truncated ZIP member extra field')
                if kind == 1:
                    zip64_descriptor = True
        descriptor_start = start + info.compress_size
        boundary = min(len(data), info._end_offset if info._end_offset is not None else len(data))
        descriptor_format = '<IQQ' if zip64_descriptor else '<III'
        descriptor_size = struct.calcsize(descriptor_format)
        # An unsigned descriptor's CRC can itself equal the optional signature.
        offsets = [descriptor_start]
        if data[descriptor_start:descriptor_start + 4] == b'PK\x07\x08':
            offsets.append(descriptor_start + 4)
        expected = (info.CRC, info.compress_size, info.file_size)
        if not any(offset + descriptor_size <= boundary and
                   struct.unpack_from(descriptor_format, data, offset) == expected
                   for offset in offsets):
            raise BadZipFile('Invalid ZIP member data descriptor')
    if info.compress_type == ZIP_STORED and info.compress_size != info.file_size:
        raise BadZipFile('Inconsistent stored ZIP member size')
    compressed = data[start:start + info.compress_size]
    if len(compressed) != info.compress_size:
        raise BadZipFile('Truncated ZIP member data')
    if info.compress_type == ZIP_DEFLATED:
        decoder = zlib.decompressobj(-zlib.MAX_WBITS)
        try:
            payload = decoder.decompress(compressed, min(info.file_size, max_bytes) + 1)
        except zlib.error:
            raise ZipMemberDataError('Invalid deflate stream') from None
        if len(payload) > info.file_size or len(payload) > max_bytes:
            raise ZipMemberLimitError('ZIP member limit')
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ZipMemberDataError('Incomplete or trailing deflate stream')
    else:
        payload = compressed
    if len(payload) != info.file_size or zlib.crc32(payload) != info.CRC:
        raise ZipMemberDataError('Inconsistent ZIP member output or CRC')
    return payload
