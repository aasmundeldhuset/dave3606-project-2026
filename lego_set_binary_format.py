import io
import struct


MAGIC = b"LGS1"
VERSION = 1


class BinaryFormatError(Exception):
    pass


def _write_u32(buffer, value):
    buffer.write(struct.pack("<I", value))


def _write_i32(buffer, value):
    buffer.write(struct.pack("<i", value))


def _write_u16(buffer, value):
    buffer.write(struct.pack("<H", value))


def _write_bool(buffer, value):
    buffer.write(struct.pack("<?", value))


def _write_text(buffer, value):
    encoded = value.encode("utf-8")
    _write_u32(buffer, len(encoded))
    buffer.write(encoded)


def _write_optional_text(buffer, value):
    _write_bool(buffer, value is not None)
    if value is not None:
        _write_text(buffer, value)


def _read_exact(stream, size):
    data = stream.read(size)
    if len(data) != size:
        raise BinaryFormatError("Unexpected end of file")
    return data


def _read_u32(stream):
    return struct.unpack("<I", _read_exact(stream, 4))[0]


def _read_i32(stream):
    return struct.unpack("<i", _read_exact(stream, 4))[0]


def _read_u16(stream):
    return struct.unpack("<H", _read_exact(stream, 2))[0]


def _read_bool(stream):
    return struct.unpack("<?", _read_exact(stream, 1))[0]


def _read_text(stream):
    length = _read_u32(stream)
    return _read_exact(stream, length).decode("utf-8")


def _read_optional_text(stream):
    if not _read_bool(stream):
        return None
    return _read_text(stream)


def encode_lego_set_binary(data):
    buffer = io.BytesIO()
    buffer.write(MAGIC)
    _write_u16(buffer, VERSION)

    lego_set = data["set"]
    _write_text(buffer, lego_set["id"])
    _write_text(buffer, lego_set["name"])
    _write_i32(buffer, -1 if lego_set["year"] is None else lego_set["year"])
    _write_optional_text(buffer, lego_set["category"])
    _write_optional_text(buffer, lego_set["previewImageUrl"])

    inventory = data["inventory"]
    _write_u32(buffer, len(inventory))
    for item in inventory:
        _write_text(buffer, item["brickTypeId"])
        _write_i32(buffer, item["colorId"])
        _write_i32(buffer, item["count"])
        _write_text(buffer, item["name"])
        _write_optional_text(buffer, item["previewImageUrl"])

    return buffer.getvalue()


def decode_lego_set_binary(binary_data):
    stream = io.BytesIO(binary_data)

    if _read_exact(stream, len(MAGIC)) != MAGIC:
        raise BinaryFormatError("Invalid magic header")

    version = _read_u16(stream)
    if version != VERSION:
        raise BinaryFormatError(f"Unsupported binary format version: {version}")

    lego_set = {
        "id": _read_text(stream),
        "name": _read_text(stream),
        "year": _read_i32(stream),
        "category": _read_optional_text(stream),
        "previewImageUrl": _read_optional_text(stream),
    }
    if lego_set["year"] == -1:
        lego_set["year"] = None

    inventory_count = _read_u32(stream)
    inventory = []
    for _ in range(inventory_count):
        inventory.append(
            {
                "brickTypeId": _read_text(stream),
                "colorId": _read_i32(stream),
                "count": _read_i32(stream),
                "name": _read_text(stream),
                "previewImageUrl": _read_optional_text(stream),
            }
        )

    return {"set": lego_set, "inventory": inventory}