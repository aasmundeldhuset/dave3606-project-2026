import struct
import sys


def read_exact(file_obj, n_bytes):
    data = file_obj.read(n_bytes)
    if len(data) != n_bytes:
        raise ValueError("Unexpected end of file")
    return data


def unpack_string(file_obj):
    length_bytes = read_exact(file_obj, 4)
    length = struct.unpack("!I", length_bytes)[0]
    string_bytes = read_exact(file_obj, length)
    return string_bytes.decode("utf-8")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 read_set_binary.py <binary_file>")
        return

    filename = sys.argv[1]

    with open(filename, "rb") as f:
        set_id = unpack_string(f)
        set_name = unpack_string(f)
        year = struct.unpack("!i", read_exact(f, 4))[0]
        category = unpack_string(f)
        preview_image_url = unpack_string(f)

        inventory_count = struct.unpack("!I", read_exact(f, 4))[0]

        print("Lego set")
        print(f"ID: {set_id}")
        print(f"Name: {set_name}")
        print(f"Year: {year if year != -1 else 'Unknown'}")
        print(f"Category: {category}")
        print(f"Preview image URL: {preview_image_url}")
        print()
        print(f"Inventory entries: {inventory_count}")
        print()

        for i in range(inventory_count):
            brick_type_id = unpack_string(f)
            color_id = struct.unpack("!i", read_exact(f, 4))[0]
            count = struct.unpack("!i", read_exact(f, 4))[0]
            brick_name = unpack_string(f)
            brick_preview_image_url = unpack_string(f)

            print(f"Entry {i + 1}:")
            print(f"  Brick type ID: {brick_type_id}")
            print(f"  Color ID: {color_id}")
            print(f"  Count: {count}")
            print(f"  Brick name: {brick_name}")
            print(f"  Brick preview image URL: {brick_preview_image_url}")
            print()


if __name__ == "__main__":
    main()
