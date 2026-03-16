# Placeholder for utils/ip_utils.py
"""
IP Utilities
Handles IP classification and basic reputation logic
"""

import ipaddress


def is_private_ip(ip: str) -> bool:
    """
    Check if IP address is private (RFC1918)
    """
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def is_public_ip(ip: str) -> bool:
    """
    Check if IP address is public
    """
    try:
        return not ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def ip_version(ip: str) -> int | None:
    """
    Returns IP version (4 or 6)
    """
    try:
        return ipaddress.ip_address(ip).version
    except ValueError:
        return None
