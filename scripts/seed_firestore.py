"""
Seed Firestore with realistic historical fault cases for demo.
Run once before recording the demo video.

Usage:
    cd backend
    python ../scripts/seed_firestore.py
"""

from google.cloud import firestore
from datetime import datetime, timezone, timedelta
import random

db = firestore.Client()
collection = db.collection("fault_cases")

CASES = [
    {
        "equipment_model": "SMA-Sunny5000",
        "industry": "solar",
        "fault_summary": "Red LED blinking 3 times — DC input overvoltage",
        "steps_taken": [
            "Checked DC string voltage with multimeter — measured 620V (limit 600V)",
            "Inspected string configuration — found extra panel added to string",
            "Reconfigured string to 10 panels from 11",
            "Verified voltage at 570V after reconfiguration",
        ],
        "resolution": "Reduced string size from 11 to 10 panels to bring DC voltage within spec",
        "note": "Common during summer peak hours — voltage rises with temperature",
        "parts_replaced": [],
        "resolved": True,
        "technician_id": "tech_001",
        "technician_count": 3,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=18),
    },
    {
        "equipment_model": "SMA-Sunny5000",
        "industry": "solar",
        "fault_summary": "No AC output despite green LED — grid impedance fault",
        "steps_taken": [
            "Verified AC grid voltage — within spec",
            "Checked grid impedance setting in installer menu",
            "Found impedance threshold set to 0.2 ohm (default) — actual was 0.35 ohm",
            "Adjusted threshold to 0.5 ohm per local grid spec",
        ],
        "resolution": "Adjusted grid impedance threshold in inverter settings to match local grid",
        "note": "Local utility has higher impedance than German default settings",
        "parts_replaced": [],
        "resolved": True,
        "technician_id": "tech_002",
        "technician_count": 2,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=35),
    },
    {
        "equipment_model": "SMA-Sunny5000",
        "industry": "solar",
        "fault_summary": "Ground fault indicator — insulation resistance low",
        "steps_taken": [
            "Disconnected all DC strings",
            "Measured insulation resistance per string with megohmmeter",
            "Found string 3 at 0.8 MOhm (threshold 1 MOhm)",
            "Traced fault to damaged cable insulation at roof penetration",
            "Replaced damaged cable section with UV-rated cable",
        ],
        "resolution": "Replaced damaged DC cable with compromised insulation at roof penetration point",
        "note": "Cable was rubbing against roof flashing — recommend conduit at penetration",
        "parts_replaced": ["4mm² DC solar cable (3m)", "Cable gland"],
        "resolved": True,
        "technician_id": "tech_001",
        "technician_count": 1,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=52),
    },
    {
        "equipment_model": "Carrier-30XA",
        "industry": "hvac",
        "fault_summary": "High discharge pressure alarm — compressor shutting down",
        "steps_taken": [
            "Checked condenser coil — found blocked by debris",
            "Cleaned condenser coil with coil cleaner",
            "Verified condenser fan operation — all 4 fans running",
            "Monitored discharge pressure after cleaning — returned to normal",
        ],
        "resolution": "Blocked condenser coil causing inadequate heat rejection",
        "note": "Schedule quarterly coil cleaning on this unit — dusty environment",
        "parts_replaced": [],
        "resolved": True,
        "technician_id": "tech_003",
        "technician_count": 1,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=7),
    },
    {
        "equipment_model": "Carrier-30XA",
        "industry": "hvac",
        "fault_summary": "Low refrigerant pressure — system short cycling",
        "steps_taken": [
            "Checked suction pressure — 45 PSI (normal 65-70 PSI)",
            "Performed leak detection with electronic leak detector",
            "Found leak at Schrader valve on liquid line service port",
            "Replaced valve core and recharged with R-410A",
            "Verified pressures after 1 hour operation",
        ],
        "resolution": "Leaking Schrader valve core on liquid line — replaced and recharged system",
        "note": "Check all service port caps are tight during PM visits",
        "parts_replaced": ["Schrader valve core", "R-410A (2 lbs)"],
        "resolved": True,
        "technician_id": "tech_004",
        "technician_count": 2,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=22),
    },
    {
        "equipment_model": "Cisco-ASR9000",
        "industry": "telecom",
        "fault_summary": "Line card LC0/5 reporting CRC errors on 10G interface",
        "steps_taken": [
            "Checked interface counters — 500+ CRC errors per minute",
            "Cleaned fiber connectors with IBC cleaner",
            "Measured optical power with OPM — Rx at -18 dBm (threshold -14 dBm)",
            "Replaced SFP+ optic module",
            "CRC errors stopped after replacement",
        ],
        "resolution": "Degraded SFP+ optic — replaced with new module",
        "note": "Original SFP+ was third-party. Replaced with Cisco-compatible unit",
        "parts_replaced": ["SFP-10G-SR"],
        "resolved": True,
        "technician_id": "tech_005",
        "technician_count": 1,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=14),
    },
    {
        "equipment_model": "Siemens-S7-1500",
        "industry": "factory",
        "fault_summary": "PLC CPU going to STOP mode — diagnostic buffer showing OB86 error",
        "steps_taken": [
            "Connected via TIA Portal and read diagnostic buffer",
            "OB86 (rack failure) triggered by ET200SP station 3",
            "Checked PROFINET cable to station 3 — found damaged connector",
            "Replaced RJ45 connector with industrial rated connector",
            "CPU returned to RUN mode — station 3 online",
        ],
        "resolution": "Damaged PROFINET RJ45 connector on ET200SP station 3 cable",
        "note": "Cable runs through high-vibration area — recommend shielded connectors",
        "parts_replaced": ["IE FC RJ45 Plug 4x2 (industrial connector)"],
        "resolved": True,
        "technician_id": "tech_006",
        "technician_count": 1,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=5),
    },
    {
        "equipment_model": "Agilent-HPLC",
        "industry": "lab",
        "fault_summary": "Pump pressure fluctuating — baseline drift on detector",
        "steps_taken": [
            "Checked solvent bottles — mobile phase level adequate",
            "Inspected inlet filter — found partially clogged",
            "Replaced inlet filter and purged system",
            "Ran blank gradient — pressure stable at 180 bar",
        ],
        "resolution": "Clogged inlet filter causing air aspiration and pressure fluctuation",
        "note": "Use filtered solvents and replace inlet filter monthly",
        "parts_replaced": ["Inlet solvent filter (2 µm)"],
        "resolved": True,
        "technician_id": "tech_007",
        "technician_count": 1,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=10),
    },
    {
        "equipment_model": "Fronius-Symo",
        "industry": "solar",
        "fault_summary": "State 306 — AC voltage too high causing derating",
        "steps_taken": [
            "Measured AC voltage at inverter terminals — 253V (limit 253V)",
            "Checked voltage at main panel — 248V",
            "Identified voltage rise due to long cable run from inverter to panel",
            "Upgraded cable from 6mm² to 10mm² on AC side",
        ],
        "resolution": "Voltage drop on undersized AC cable causing high voltage at inverter — upgraded cable",
        "note": "Cable run is 45m — always calculate voltage drop for long runs",
        "parts_replaced": ["10mm² AC cable (90m)", "Cable lugs"],
        "resolved": True,
        "technician_id": "tech_002",
        "technician_count": 2,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=28),
    },
    {
        "equipment_model": "Daikin-VRV",
        "industry": "hvac",
        "fault_summary": "Error code U4 — communication error between indoor and outdoor units",
        "steps_taken": [
            "Checked communication wiring between indoor unit #7 and outdoor unit",
            "Found loose terminal connection at indoor unit junction box",
            "Re-terminated communication wires and tightened screws",
            "Reset error code — system resumed normal operation",
        ],
        "resolution": "Loose communication wire terminal at indoor unit #7 junction box",
        "note": "Vibration from nearby compressor may have loosened terminal over time",
        "parts_replaced": [],
        "resolved": True,
        "technician_id": "tech_003",
        "technician_count": 1,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=3),
    },
]

if __name__ == "__main__":
    for case in CASES:
        collection.add(case)
        print(f"Added: {case['fault_summary'][:60]}...")

    print(f"\nSeeded {len(CASES)} cases into Firestore")
