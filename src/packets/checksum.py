"""
RFC 1071 16-bit One's Complement Internet Checksum Algorithm.
Used across IPv4 headers, TCP pseudo-headers, UDP pseudo-headers, and ICMP payloads.
"""

import struct


def calculate_internet_checksum(data: bytes) -> int:
    """
    Calculate the 16-bit One's Complement Checksum of a bytes buffer.
    Algorithm:
    1. Sum contiguous 16-bit words.
    2. If odd byte length, pad last byte with 0.
    3. Fold 32-bit sum carries back into 16 bits.
    4. Bitwise NOT (~sum & 0xFFFF).
    """
    if len(data) % 2 == 1:
        data += b"\x00"

    total = 0
    words = struct.unpack(f"!{len(data) // 2}H", data)
    for word in words:
        total += word

    # Fold 32-bit carries into lower 16 bits
    while (total >> 16) > 0:
        total = (total & 0xFFFF) + (total >> 16)

    # Invert bits (one's complement)
    checksum = (~total) & 0xFFFF
    return checksum


def verify_internet_checksum(data_with_checksum: bytes) -> bool:
    """
    Verify checksum over a packet buffer containing the checksum field.
    When the checksum is correct, sum over all 16-bit words (including checksum)
    evaluates to 0xFFFF (or 0 after inversion).
    """
    if len(data_with_checksum) % 2 == 1:
        data_with_checksum += b"\x00"

    total = 0
    words = struct.unpack(f"!{len(data_with_checksum) // 2}H", data_with_checksum)
    for word in words:
        total += word

    while (total >> 16) > 0:
        total = (total & 0xFFFF) + (total >> 16)

    # Result should be 0xFFFF (or ~total == 0)
    return total == 0xFFFF
