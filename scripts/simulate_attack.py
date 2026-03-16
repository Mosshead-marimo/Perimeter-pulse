# Placeholder for scripts/simulate_attack.py
"""
Attack Simulation Script
Creates synthetic firewall logs simulating data leakage
"""

from datetime import datetime, timedelta
import random

OUTPUT_FILE = "data/raw_logs/pfirewall.log"

ATTACK_IPS = [
    "185.199.108.153",
    "45.33.12.98"
]


def generate_entry(ts, dst_ip, bytes_sent):
    return (
        f"{ts.date()} {ts.time()} ALLOW TCP "
        f"192.168.1.10 {dst_ip} "
        f"{random.randint(50000,60000)} 443 "
        f"{bytes_sent} - - - - - SEND\n"
    )


def main():
    print("[+] Simulating data exfiltration attack...")

    start = datetime.now() - timedelta(minutes=10)

    with open(OUTPUT_FILE, "a") as f:
        for i in range(20):
            ts = start + timedelta(seconds=i * 30)
            dst_ip = random.choice(ATTACK_IPS)
            f.write(generate_entry(ts, dst_ip, random.randint(4000, 8000)))

    print("[✓] Attack simulation completed")


if __name__ == "__main__":
    main()
