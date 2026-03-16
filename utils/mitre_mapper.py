MITRE_MAP = {
    "DNS_TUNNELING": {
        "technique": "T1071.004",
        "name": "DNS Tunneling",
        "tactic": "Command and Control"
    },
    "DATA_EXFILTRATION": {
        "technique": "T1041",
        "name": "Exfiltration Over C2 Channel",
        "tactic": "Exfiltration"
    }
}

def map_to_mitre(leakage_findings):
    mappings = []
    for f in leakage_findings:
        key = f.get("type")
        if key in MITRE_MAP:
            mappings.append(MITRE_MAP[key])
    return mappings
