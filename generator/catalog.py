"""Static reference lists for the synthetic FE Bar caseload.

Every name, address, facility, payer member id and tax id here is FICTIONAL. Payer names are
generic market labels used only to exercise the routing logic (BCBS -> BCBS criteria, else CMS).
CPT/HCPCS and ICD-10 codes are real code values chosen to fit each denial reason; the CO55 code
(63650, neurostimulator electrode array) is used as an investigational-service example only.
"""

FIRST_NAMES_F = (
    "Elena", "Marisol", "Dana", "Renee", "Priya", "Helen", "Tamara", "Joanna", "Nadia", "Carmen",
    "Lydia", "Sofia", "Grace", "Ingrid", "Monica", "Yvette", "Alma", "Brooke", "Hannah", "Lucia",
)
FIRST_NAMES_M = (
    "Thomas", "Victor", "Daniel", "Raymond", "Samuel", "Gerald", "Marcus", "Ivan", "Felix", "Owen",
    "Antonio", "Corey", "Hector", "Nathan", "Peter", "Russell", "Derek", "Gabriel", "Leonard", "Miles",
)
LAST_NAMES = (
    "Marquez", "Whitcombe", "Okafor", "Lindqvist", "Ramaswamy", "Tadesse", "Brennan", "Castellanos",
    "Holloway", "Nakamura", "Delgado", "Fairbanks", "Quintero", "Ostrowski", "Abernathy", "Villanueva",
    "Kessler", "Montgomery", "Sandoval", "Yildiz", "Pemberton", "Gallagher", "Iwasaki", "Reyes",
)

FACILITIES = (
    {"FACILITY_ID": 101, "PROVIDER_NAME": "Desert Ridge Medical Center", "SITEID": 1,
     "FEDERAL_TAX_ID": 861234501, "STREET": "1200 Saguaro Pkwy", "CSZ": "Mesa, AZ 85201", "weight": 0.5},
    {"FACILITY_ID": 102, "PROVIDER_NAME": "Saguaro Valley Hospital", "SITEID": 2,
     "FEDERAL_TAX_ID": 861234502, "STREET": "88 Canyon Rd", "CSZ": "Tucson, AZ 85701", "weight": 0.3},
    {"FACILITY_ID": 103, "PROVIDER_NAME": "Mesa Pines Surgical Center", "SITEID": 3,
     "FEDERAL_TAX_ID": 861234503, "STREET": "415 Pine Ave", "CSZ": "Mesa, AZ 85210", "weight": 0.2},
)

# appeal limit (days from DENIAL_DATE) per payer type, as specified in SPEC.
PAYER_LIMITS = {"COMMERCIAL": 180, "MEDICARE_ADVANTAGE": 65, "MEDICAID": 60}

# name, payer_type, health plan id, payer street, payer city/state/zip, mix weight.
# The first entry is the hero payer and must stay first.
PAYERS = (
    {"name": "BCBS of Arizona", "type": "COMMERCIAL", "plan": "BCBSAZ-PPO-4471",
     "street": "PO Box 13000", "csz": "Phoenix, AZ 85002", "weight": 30},
    {"name": "BCBS of Arizona Medicare Advantage", "type": "MEDICARE_ADVANTAGE", "plan": "BCBSAZ-MA-0912",
     "street": "PO Box 13000", "csz": "Phoenix, AZ 85002", "weight": 8},
    {"name": "UnitedHealthcare", "type": "COMMERCIAL", "plan": "UHC-COM-7710",
     "street": "PO Box 30555", "csz": "Salt Lake City, UT 84130", "weight": 15},
    {"name": "Aetna", "type": "COMMERCIAL", "plan": "AET-HMO-2280",
     "street": "PO Box 14079", "csz": "Lexington, KY 40512", "weight": 12},
    {"name": "Cigna", "type": "COMMERCIAL", "plan": "CIG-PPO-5531",
     "street": "PO Box 188011", "csz": "Chattanooga, TN 37422", "weight": 10},
    {"name": "Humana Medicare Advantage", "type": "MEDICARE_ADVANTAGE", "plan": "HUM-MA-3398",
     "street": "PO Box 14601", "csz": "Lexington, KY 40512", "weight": 7},
    {"name": "UnitedHealthcare Medicare Advantage", "type": "MEDICARE_ADVANTAGE", "plan": "UHC-MA-4465",
     "street": "PO Box 30555", "csz": "Salt Lake City, UT 84130", "weight": 8},
    {"name": "AHCCCS Medicaid", "type": "MEDICAID", "plan": "AHCCCS-FFS-1020",
     "street": "PO Box 6940", "csz": "Phoenix, AZ 85005", "weight": 10},
)

CARC_MIX = {"CO50": 0.34, "CO55": 0.12, "CO57": 0.16, "CO150": 0.16, "CO186": 0.22}

# Procedure families. exp = (lo, hi) expected (contracted/allowed) dollars for the primary line.
# anc = optional ancillary line (cpt, lo, hi). lat=True means ICD-10 laterality follows the modifier.
FAMILIES = {
    # ---- CO50: medical necessity -------------------------------------------------------------
    "tka": {"carc": "CO50", "weight": 0.30, "cpt": "27447", "mods": ("RT", "LT"), "lat": True,
            "dx": ("M17.11",), "extra": ("M25.561", "Z68.31"), "pos": 22, "rev": 360, "tob": "0131",
            "exp": (16000.0, 21000.0), "anc": ("01402", 600.0, 900.0), "los": 0, "inpatient": False},
    "lumbar_fusion": {"carc": "CO50", "weight": 0.20, "cpt": "22612", "mods": None, "lat": False,
            "dx": ("M48.062", "M43.16", "M51.16"), "extra": ("M54.16", "Z72.0"), "pos": 21, "rev": 360,
            "tob": "0111", "exp": (13500.0, 17000.0), "anc": ("22840", 2500.0, 3500.0), "los": 2,
            "inpatient": True},
    "lumbar_mri": {"carc": "CO50", "weight": 0.20, "cpt": "72148", "mods": None, "lat": False,
            "dx": ("M54.16", "M54.50", "M51.16"), "extra": ("M79.604",), "pos": 22, "rev": 610,
            "tob": "0131", "exp": (350.0, 700.0), "anc": None, "los": 0, "inpatient": False},
    "sleep_study": {"carc": "CO50", "weight": 0.15, "cpt": "95810", "mods": None, "lat": False,
            "dx": ("G47.33",), "extra": ("R06.83", "I50.22"), "pos": 22, "rev": 300, "tob": "0131",
            "exp": (650.0, 1100.0), "anc": None, "los": 0, "inpatient": False},
    "bariatric": {"carc": "CO50", "weight": 0.15, "cpt": "43775", "mods": None, "lat": False,
            "dx": ("E66.01",), "extra": ("Z68.41", "E11.9"), "pos": 21, "rev": 360, "tob": "0111",
            "exp": (12000.0, 16500.0), "anc": None, "los": 1, "inpatient": True},
    # ---- CO55: experimental / investigational ------------------------------------------------
    "scs_trial": {"carc": "CO55", "weight": 1.0, "cpt": "63650", "mods": None, "lat": False,
            "dx": ("M54.16", "M51.16"), "extra": ("G89.29",), "pos": 22, "rev": 360, "tob": "0131",
            "exp": (4000.0, 9000.0), "anc": None, "los": 0, "inpatient": False},
    # ---- CO57: level of service (critical care) ----------------------------------------------
    "critical_care": {"carc": "CO57", "weight": 1.0, "cpt": "99291", "mods": None, "lat": False,
            "dx": ("A41.9",), "extra": ("R65.20", "I95.9"), "pos": 21, "rev": 120, "tob": "0111",
            "exp": (1400.0, 2300.0), "anc": None, "los": 2, "inpatient": True},
    # ---- CO150: level of service (ED / office) -----------------------------------------------
    "ed_visit": {"carc": "CO150", "weight": 0.5, "cpt": "99285", "mods": None, "lat": False,
            "dx": ("R10.9", "R07.9", "J06.9"), "extra": (), "pos": 23, "rev": 450, "tob": "0131",
            "exp": (250.0, 420.0), "anc": None, "los": 0, "inpatient": False},
    "office_visit": {"carc": "CO150", "weight": 0.5, "cpt": "99215", "mods": None, "lat": False,
            "dx": ("I10", "E11.65"), "extra": ("E11.9",), "pos": 11, "rev": None, "tob": None,
            "exp": (120.0, 190.0), "anc": None, "los": 0, "inpatient": False},
    # ---- CO186: level of care (inpatient vs observation) -------------------------------------
    "inpatient_cardiac": {"carc": "CO186", "weight": 0.6, "cpt": "99223", "mods": None, "lat": False,
            "dx": ("I21.4", "I20.0"), "extra": ("I10",), "pos": 21, "rev": 120, "tob": "0111",
            "exp": (3200.0, 6500.0), "anc": None, "los": 2, "inpatient": True},
    "inpatient_syncope": {"carc": "CO186", "weight": 0.4, "cpt": "99223", "mods": None, "lat": False,
            "dx": ("R55",), "extra": ("I49.9",), "pos": 21, "rev": 120, "tob": "0111",
            "exp": (2600.0, 4200.0), "anc": None, "los": 1, "inpatient": True},
}

# Note author roles and event tags used by the clinical-note templates.
ROLES = ("ORTHOPEDIC_SURGEON", "PHYSICAL_THERAPIST", "PRIMARY_CARE", "RADIOLOGIST", "PAIN_MANAGEMENT",
         "SLEEP_MEDICINE", "BARIATRIC_SURGEON", "NUTRITIONIST", "PSYCHOLOGIST", "EMERGENCY_PHYSICIAN",
         "CRITICAL_CARE", "HOSPITALIST", "CARDIOLOGY", "UR_NURSE", "ANESTHESIA")
