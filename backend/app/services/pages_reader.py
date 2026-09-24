"""Plain-text extraction from Apple Pages (.pages) documents.

Mac users write resumes and contracts in Pages the way Windows users write
them in Word, so the text-based tools (ATS Analyzer, Batch ATS, Contract
Analyzer, Doc Analyzer) accept .pages alongside .docx. Two generations of the
format exist and both are handled:

* Pages 5+ (2013 onward -- everything a current Mac produces): a zip of
  "IWA" files, Apple's snappy-compressed protobuf container. There is no PDF
  preview inside, so the text is decoded from the protobufs themselves.
* Pages '09 and older: a zip holding index.xml and usually QuickLook/Preview.pdf.

The IWA decoding reuses the protobuf classes that ship with numbers-parser
(already a dependency for .numbers uploads -- Pages and Numbers share the
same container and text/table archive types). numbers-parser's own document
loader is deliberately NOT used: it refuses any archive type it doesn't know,
and a Pages file is full of Pages-only types. Instead only the handful of
message types that carry text are decoded; everything else is skipped by
length without being parsed, so unfamiliar content can't break extraction.
"""
import io
import re
import zipfile
from datetime import datetime, timedelta
from struct import unpack
from xml.etree import ElementTree

PASSWORD_ERROR = (
    "This Pages file is password-protected. Remove the password in Pages "
    "(File > Set Password) or export it as PDF, then upload again."
)
UNREADABLE_ERROR = (
    "Could not read this Pages file. In Pages, choose File > Export To > PDF "
    "or Word, then upload that instead."
)

# Protobuf message type IDs inside IWA files (see numbers_parser.generated.mapping).
_TYPE_STORAGE = (2001, 2005)   # TSWP.StorageArchive -- a run of document text
_TYPE_TABLE_MODEL = 6001       # TST.TableModelArchive
_TYPE_TILE = 6002              # TST.Tile -- packed cell storage for a block of rows
_TYPE_DATA_LIST = 6005         # TST.TableDataList -- a table's string / rich-text lists
_TYPE_RICH_TEXT = 6218         # TST.RichTextPayloadArchive -- wraps a cell's StorageArchive

# TSWP.StorageArchive.KindType values.
_KIND_BODY = 0
_KIND_HEADER = 1               # headers and footers share this kind
_KIND_FOOTNOTE = 2
_KIND_TEXTBOX = 3
# Deliberately left out: NOTE (4) is reviewer comments, not document content;
# CELL (5) is rich-text table cells, which are read through their table so
# they come out in row order instead of as loose fragments.

# U+FFFC marks where an inline object (image, shape, table) is anchored in the
# text; U+2028/2029 are Apple's line/paragraph separators.
_TEXT_REPLACEMENTS = {"￼": "", " ": "\n", " ": "\n"}

_LIGATURES = str.maketrans({
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
    "\ufb04": "ffl", "\ufb05": "st", "\ufb06": "st",
})

_IWORK_EPOCH = datetime(2001, 1, 1)


def read_pages(data: bytes) -> str:
    """Return the text of a .pages document, raising ValueError with a
    user-facing message if the file can't be read."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        names = set(archive.namelist())
    except zipfile.BadZipFile:
        raise ValueError(UNREADABLE_ERROR)

    # Pages 5+ writes a .iwph password hint file next to the encrypted content.
    if any(name.endswith(".iwph") for name in names):
        raise ValueError(PASSWORD_ERROR)

    if any(name.startswith("Index/") and name.endswith(".iwa") for name in names):
        return _read_modern(archive)
    if "index.xml" in names or "QuickLook/Preview.pdf" in names:
        return _read_legacy(archive, names)
    raise ValueError(UNREADABLE_ERROR)


# ---------------------------------------------------------------------------
# Pages 5+ (IWA)
# ---------------------------------------------------------------------------

def _read_modern(archive: zipfile.ZipFile) -> str:
    objects = {}
    try:
        for name in archive.namelist():
            if name.endswith(".iwa"):
                objects.update(_decode_iwa(archive.read(name)))
    except ValueError:
        raise
    except Exception:
        # Truncated protobufs, unsupported zip compression, etc.
        raise ValueError(UNREADABLE_ERROR)

    headers, body, footnotes, textboxes = [], [], [], []
    for message_type, obj in objects.values():
        if message_type not in _TYPE_STORAGE:
            continue
        text = _clean("".join(obj.text))
        if not text:
            continue
        if obj.kind == _KIND_BODY:
            body.append(text)
        elif obj.kind == _KIND_HEADER:
            headers.append(text)
        elif obj.kind == _KIND_FOOTNOTE:
            footnotes.append(text)
        elif obj.kind == _KIND_TEXTBOX:
            textboxes.append(text)

    tables = [
        text for text in (
            _table_text(obj, objects)
            for message_type, obj in objects.values()
            if message_type == _TYPE_TABLE_MODEL
        ) if text
    ]

    # Headers/footers repeat per section, so keep one copy of each. They go
    # first because resumes commonly put the name and contact details there.
    parts = _dedupe(headers) + body + textboxes + tables + footnotes
    return "\n\n".join(parts)


def _decode_iwa(data: bytes) -> dict:
    """Decode one .iwa file into {object_id: (message_type, message)}, keeping
    only the message types this module reads."""
    import snappy
    from google.protobuf.internal.decoder import _DecodeVarint32
    from numbers_parser.generated.TSPArchiveMessages_pb2 import ArchiveInfo

    wanted = _message_classes()

    # An IWA file is a series of chunks: a 0x00 byte, a 3-byte little-endian
    # length, then that many bytes of raw (unframed) snappy data.
    raw = bytearray()
    pos = 0
    while pos < len(data):
        if data[pos] != 0 or pos + 4 > len(data):
            raise ValueError(UNREADABLE_ERROR)
        length = int.from_bytes(data[pos + 1:pos + 4], "little")
        try:
            raw += snappy.uncompress(bytes(data[pos + 4:pos + 4 + length]))
        except Exception:
            raise ValueError(UNREADABLE_ERROR)
        pos += 4 + length

    # The decompressed stream is a series of archives: a varint-prefixed
    # ArchiveInfo header, then the message payloads it describes back to back.
    objects = {}
    buf = bytes(raw)
    pos = 0
    while pos < len(buf):
        header_len, pos = _DecodeVarint32(buf, pos)
        info = ArchiveInfo.FromString(buf[pos:pos + header_len])
        pos += header_len
        for index, message_info in enumerate(info.message_infos):
            payload = buf[pos:pos + message_info.length]
            pos += message_info.length
            # Only the first message is the object itself; any others are
            # patches/extras that no text lives in.
            if index == 0 and message_info.type in wanted:
                message = wanted[message_info.type].FromString(payload)
                objects[info.identifier] = (message_info.type, message)
    return objects


def _message_classes() -> dict:
    from numbers_parser.generated import TSTArchives_pb2, TSWPArchives_pb2

    classes = {
        _TYPE_TABLE_MODEL: TSTArchives_pb2.TableModelArchive,
        _TYPE_TILE: TSTArchives_pb2.Tile,
        _TYPE_DATA_LIST: TSTArchives_pb2.TableDataList,
        _TYPE_RICH_TEXT: TSTArchives_pb2.RichTextPayloadArchive,
    }
    for message_type in _TYPE_STORAGE:
        classes[message_type] = TSWPArchives_pb2.StorageArchive
    return classes


def _table_text(table, objects: dict) -> str:
    """Render a table as one line per row, cells separated by " | ", so
    tabular resume sections (skills grids, job history) keep their structure."""
    from numbers_parser.model import get_storage_buffers_for_row

    store = table.base_data_store
    strings = _list_entries(objects, store.stringTable.identifier)
    rich = _list_entries(objects, store.rich_text_table.identifier)
    num_cols = table.number_of_columns

    rows = {}
    tile_size = store.tiles.tile_size or 256
    for tile_ref in store.tiles.tiles:
        tile = objects.get(tile_ref.tile.identifier)
        if not tile or tile[0] != _TYPE_TILE:
            continue
        for row_info in tile[1].rowInfos:
            # Pages since ~2019 writes the current ("BNC") cell layout; files
            # last saved by older Pages 5-7 only have the legacy one.
            if row_info.cell_storage_buffer:
                buffers = get_storage_buffers_for_row(
                    row_info.cell_storage_buffer,
                    row_info.cell_offsets,
                    num_cols,
                    row_info.has_wide_offsets,
                )
            else:
                buffers = get_storage_buffers_for_row(
                    row_info.cell_storage_buffer_pre_bnc,
                    row_info.cell_offsets_pre_bnc,
                    num_cols,
                    False,
                )
            cells = [_cell_text(b, strings, rich, objects) for b in buffers]
            if any(cells):
                row_index = tile_ref.tileid * tile_size + row_info.tile_row_index
                rows[row_index] = " | ".join(cells).rstrip(" |")

    lines = [rows[i] for i in sorted(rows)]
    if not lines:
        # Cell layout not decodable -- still surface the table's text, in the
        # order it was typed (list keys are assigned sequentially), rather
        # than silently dropping it.
        lines = [_clean(strings[k].string) for k in sorted(strings) if strings[k].string.strip()]
    if table.table_name_enabled and table.table_name:
        lines.insert(0, table.table_name)
    return "\n".join(lines)


def _list_entries(objects: dict, list_id: int) -> dict:
    data_list = objects.get(list_id)
    if not data_list or data_list[0] != _TYPE_DATA_LIST:
        return {}
    return {entry.key: entry for entry in data_list[1].entries}


def _cell_text(buffer, strings: dict, rich: dict, objects: dict) -> str:
    """Decode one cell's packed storage (layout version 5, per numbers-parser's
    Cell._from_storage) far enough to get a display value. Formatting,
    formulas and styles are ignored -- only the value matters for analysis."""
    if not buffer or len(buffer) < 12:
        return ""
    if buffer[0] == 4:
        return _legacy_cell_text(buffer, strings, rich, objects)
    if buffer[0] != 5:
        return ""
    flags = unpack("<i", buffer[8:12])[0]
    offset = 12
    decimal = number = seconds = string_id = rich_id = None
    try:
        if flags & 0x1:
            from numbers_parser.cell import _unpack_decimal128
            decimal = _unpack_decimal128(buffer[offset:offset + 16])
            offset += 16
        if flags & 0x2:
            number = unpack("<d", buffer[offset:offset + 8])[0]
            offset += 8
        if flags & 0x4:
            seconds = unpack("<d", buffer[offset:offset + 8])[0]
            offset += 8
        if flags & 0x8:
            string_id = unpack("<i", buffer[offset:offset + 4])[0]
            offset += 4
        if flags & 0x10:
            rich_id = unpack("<i", buffer[offset:offset + 4])[0]
    except Exception:
        return ""

    if string_id is not None and string_id in strings:
        return _clean(strings[string_id].string)
    if rich_id is not None:
        return _rich_cell_text(rich_id, rich, objects)
    if seconds is not None:
        return (_IWORK_EPOCH + timedelta(seconds=seconds)).strftime("%Y-%m-%d")
    value = decimal if decimal is not None else number
    if value is not None:
        return str(int(value)) if float(value).is_integer() else str(value)
    return ""


# Legacy (storage version 4) cell layout: byte 1 is the cell type, a flags
# word at bytes 4-8, then optional 4-byte fields in this fixed order. Only
# the fields before the text ID matter here; they're skipped by size.
_LEGACY_FIELDS_BEFORE_TEXT = (0x2, 0x80, 0x400, 0x800, 0x4, 0x8)
_LEGACY_TEXT_FLAG = 0x10
_LEGACY_TYPE_TEXT = 3
_LEGACY_TYPE_RICH_TEXT = 9


def _legacy_cell_text(buffer, strings: dict, rich: dict, objects: dict) -> str:
    """Text and rich-text cells only: numbers/dates in this layout aren't
    decoded, since no sample file exists to verify them against and a
    misread value is worse than a missing one."""
    cell_type = buffer[1]
    if cell_type not in (_LEGACY_TYPE_TEXT, _LEGACY_TYPE_RICH_TEXT):
        return ""
    flags = unpack("<i", buffer[4:8])[0]
    if not flags & _LEGACY_TEXT_FLAG:
        return ""
    offset = 12 + 4 * sum(1 for flag in _LEGACY_FIELDS_BEFORE_TEXT if flags & flag)
    if offset + 4 > len(buffer):
        return ""
    text_id = unpack("<i", buffer[offset:offset + 4])[0]
    if cell_type == _LEGACY_TYPE_TEXT:
        entry = strings.get(text_id)
        return _clean(entry.string) if entry else ""
    return _rich_cell_text(text_id, rich, objects)


def _rich_cell_text(rich_id: int, rich: dict, objects: dict) -> str:
    entry = rich.get(rich_id)
    if not entry:
        return ""
    payload = objects.get(entry.rich_text_payload.identifier)
    if payload and payload[0] == _TYPE_RICH_TEXT:
        storage = objects.get(payload[1].storage.identifier)
        if storage and storage[0] in _TYPE_STORAGE:
            return _clean("".join(storage[1].text))
    return ""


# ---------------------------------------------------------------------------
# Pages '09 and older
# ---------------------------------------------------------------------------

_SF_NS = "http://developer.apple.com/namespaces/sf"


def _read_legacy(archive: zipfile.ZipFile, names: set) -> str:
    # The QuickLook preview is a faithful render of the whole document
    # (headers, tables, text boxes), so prefer it when present.
    if "QuickLook/Preview.pdf" in names:
        from app.services.file_handler import _read_pdf_bytes
        text = _clean(_read_pdf_bytes(archive.read("QuickLook/Preview.pdf")))
        if text:
            return text

    if "index.xml" not in names:
        raise ValueError(UNREADABLE_ERROR)
    try:
        root = ElementTree.fromstring(archive.read("index.xml"))
    except (ElementTree.ParseError, NotImplementedError):
        # A password-protected '09 document stores index.xml encrypted, with a
        # zip compression method Python can't open.
        raise ValueError(PASSWORD_ERROR)

    paragraphs = []
    for body in root.iter(f"{{{_SF_NS}}}text-body"):
        for p in body.iter(f"{{{_SF_NS}}}p"):
            text = _clean("".join(p.itertext()))
            if text:
                paragraphs.append(text)
    return "\n".join(paragraphs)


# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    for old, new in _TEXT_REPLACEMENTS.items():
        text = text.replace(old, new)
    # Typographic ligatures (the "fi" in "finance" as one glyph) come out of
    # Pages' PDF previews and would hide words from ATS keyword matching.
    text = text.translate(_LIGATURES)
    # Empty paragraphs around images/page breaks otherwise pile up.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _dedupe(items: list) -> list:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
