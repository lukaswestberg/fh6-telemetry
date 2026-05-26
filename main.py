import json
import os

from lib.fh6 import listen


def main():
    clear_cmd = "cls" if os.name == "nt" else "clear"
    for packet in listen():
        os.system(clear_cmd)
        print(json.dumps(packet, indent=4))


if __name__ == "__main__":
    main()
