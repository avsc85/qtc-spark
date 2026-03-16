"""
Scope of work definitions and milestone descriptions for each contract template type.
Used by render_html_contract() to populate the Scope of Work section.
"""

TEMPLATE_SCOPES: dict[str, dict] = {
    "adu_legalization": {
        "description": "Drawings to obtain planning and building permits for ADU legalization.",
        "scope": [
            "1 Site Visit",
            "As-Built Floor Plan (Existing Conditions)",
            "Site Plan (property lines, setbacks, easements)",
            "Utility Layout (if required by city)",
            "Title 24 Energy Compliance Report",
            "Building Permit Drawing Set",
            "3 rounds of plan check corrections included",
            "Title Block with all required city sheets",
            "Final PDF delivery of approved plans",
        ],
        "milestone_descriptions": [
            "Upon signing of agreement & completion of site visit",
            "Upon city submission of permit drawings",
            "Upon permit approval / final plan delivery",
        ],
    },
    "remodeling": {
        "description": "Drawings for interior remodeling and construction permit.",
        "scope": [
            "1 Site Visit",
            "As-Built Floor Plan (Existing Conditions)",
            "Demolition Plan",
            "Proposed Floor Plan",
            "Electrical Plan",
            "Plumbing Schematic (if applicable)",
            "Interior Elevations (key rooms)",
            "Exterior Elevations (if required by city)",
            "Title 24 Energy Compliance Report",
            "Building Permit Drawing Set",
            "3 rounds of plan check corrections included",
            "Structural coordination notes (structural engineering by others)",
            "Final PDF delivery of approved plans",
        ],
        "milestone_descriptions": [
            "Upon signing of agreement & completion of site visit",
            "Upon city submission of permit drawings",
            "Upon permit approval / final plan delivery",
        ],
    },
    "home_addition": {
        "description": "Drawings for residential home addition and permit set.",
        "scope": [
            "1 Site Visit",
            "As-Built Floor Plan (Existing Conditions)",
            "Proposed Addition Floor Plan",
            "Site Plan (property lines, setbacks, addition footprint)",
            "All Elevations (front, rear, left, right)",
            "Roof Plan",
            "Cross-Sections (as required by city)",
            "Window & Door Schedule",
            "Title 24 Energy Compliance Report",
            "Building Permit Drawing Set",
            "3 rounds of plan check corrections included",
            "Structural coordination notes (structural engineering by others — not included)",
            "Final PDF delivery of approved plans",
        ],
        "milestone_descriptions": [
            "Upon signing of agreement & completion of site visit",
            "Upon city submission of permit drawings",
            "Upon permit approval / final plan delivery",
        ],
    },
    "electrical_permit": {
        "description": "Drawings for electrical permit including panel upgrade, EV charger, or solar installation.",
        "scope": [
            "1 Site Visit",
            "Single-Line Electrical Diagram",
            "Panel Schedule (existing and proposed)",
            "Load Calculations",
            "Service Upgrade Documentation (if applicable)",
            "EV Charger Installation Details (if applicable)",
            "Solar PV System Details (if applicable)",
            "Site Plan showing electrical service location",
            "Electrical Floor Plan",
            "Building Permit Drawing Set",
            "3 rounds of plan check corrections included",
        ],
        "milestone_descriptions": [
            "Upon signing of agreement & completion of site visit",
            "Upon city submission of permit drawings",
            "Upon permit approval / final plan delivery",
        ],
    },
}
