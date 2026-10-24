"""QR Code generation and URL routing utilities for GreenScore.

Person 1: Student Experience & QR integration.
Handles bin QR code generation and direct simulation links.
"""

import os
from typing import Optional
from PIL import Image
import qrcode


def get_local_ip() -> str:
    """Return the local machine's LAN IP so phones on the same Wi-Fi can scan and open GreenScore."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "10.61.25.235"


def get_bin_direct_url(bin_id: str, base_url: Optional[str] = None) -> str:
    """Return the direct navigation target URL for a specific bin QR code.

    Target URL format: {base_url}/?bin_id={bin_id}
    Falls back to environment variable APP_BASE_URL or http://localhost:8501.
    """
    if not base_url:
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8501")

    clean_base = base_url.rstrip("/")
    return f"{clean_base}/?bin_id={bin_id}"


def generate_bin_qr(bin_id: str, base_url: Optional[str] = None) -> Image.Image:
    """Generate a stylized scannable QR code PIL Image for a given bin_id.

    - Target URL format: {base_url}/?bin_id={bin_id}
    - Base URL fetched from os.getenv("APP_BASE_URL", "http://localhost:8501")
    - Styled in dark green (#1b4332) fill over white background.
    - PIL image factory with RGB conversion.
    """
    target_url = get_bin_direct_url(bin_id=bin_id, base_url=base_url)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    # PIL image factory with dark green (#1b4332) fill and white background
    img = qr.make_image(fill_color="#1b4332", back_color="white")

    # Explicit RGB conversion as per contract
    rgb_image = img.convert("RGB")
    return rgb_image
