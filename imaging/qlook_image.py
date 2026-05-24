"""Generate quick-look images for data inspection."""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Generating quick-look images using configuration: {config_file}")
    print("TODO: call CASA tclean with conservative quick-look parameters.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c imaging/qlook_image.py CONFIG.yml")
    main(sys.argv[-1])
