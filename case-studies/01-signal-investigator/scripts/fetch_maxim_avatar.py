"""Download a fixed, free-for-commercial-use DiceBear Avataaars character.

Network is required only once, on the developer's Mac. Commit the SVG to
assets/ to avoid a third-party image request from the deployed application.
"""
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "maxim-avatar.svg"
URL = "https://api.dicebear.com/10.x/avataaars/svg?seed=MaximSignalInvestigator"


def main():
    request = Request(URL, headers={"User-Agent": "SignalInvestigator/1.0"})
    with urlopen(request, timeout=20) as response:
        image = response.read(1024 * 1024 + 1)
    source = image.lower().lstrip()
    if len(image) > 1024 * 1024 or b"<svg" not in source[:500] or any(
        unsafe in source for unsafe in (b"<script", b"onload=", b"javascript:")
    ):
        raise ValueError("Avatar service returned unexpected or unsafe content")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(image)
    print("Saved:", OUTPUT)
    print("Style: Avataaars by Pablo Stanley, free for personal/commercial use")
    print("License: https://www.dicebear.com/styles/avataaars/")


if __name__ == "__main__":
    main()
