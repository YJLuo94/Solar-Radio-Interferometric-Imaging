"""Generate final science images and radio/EUV context plots."""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Generating science images using configuration: {config_file}")
    print("TODO: call CASA tclean/exportfits and generate science image products.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c imaging/sci_image.py CONFIG.yml")
    main(sys.argv[-1])
