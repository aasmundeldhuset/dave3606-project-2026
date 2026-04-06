import argparse

from lego_set_binary_format import BinaryFormatError, decode_lego_set_binary


def main():
    parser = argparse.ArgumentParser(description="Read a LEGO set binary export and print its contents.")
    parser.add_argument("path", help="Path to a .bin file produced by /api/set.bin")
    args = parser.parse_args()

    with open(args.path, "rb") as file_handle:
        binary_data = file_handle.read()

    try:
        data = decode_lego_set_binary(binary_data)
    except BinaryFormatError as error:
        raise SystemExit(f"Failed to read binary file: {error}") from error

    lego_set = data["set"]
    print(f"Set id: {lego_set['id']}")
    print(f"Name: {lego_set['name']}")
    print(f"Year: {lego_set['year'] if lego_set['year'] is not None else 'unknown'}")
    print(f"Category: {lego_set['category'] if lego_set['category'] is not None else 'unknown'}")
    print(f"Preview image URL: {lego_set['previewImageUrl'] if lego_set['previewImageUrl'] is not None else 'unknown'}")
    print()
    print("Inventory:")
    for item in data["inventory"]:
        print(
            f"- {item['brickTypeId']} / color {item['colorId']}: {item['count']} x {item['name']}"
            + (
                f" ({item['previewImageUrl']})"
                if item["previewImageUrl"] is not None
                else ""
            )
        )


if __name__ == "__main__":
    main()