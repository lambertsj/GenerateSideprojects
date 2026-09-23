"""Built-in seeds. Data sources are per target market; unknown countries get a generic prompt."""

SECTORS = [
    "HVAC and installation", "childcare", "physiotherapy", "homeowners' associations", "agriculture",
    "road transport", "hospitality", "accountancy", "real estate agencies", "municipal services",
    "home care", "construction subcontracting", "vocational education", "independent retail",
    "sports clubs", "notaries", "veterinary practices", "dental practices", "commercial cleaning",
    "landscaping", "small housing associations", "events", "small law firms", "print shops",
]

TRIGGERS = [
    "new or changed regulation", "cheaper LLM inference", "newly available open dataset",
    "labour shortage", "energy transition", "ageing business owners",
    "reporting obligation trickling down the supply chain", "a platform opening or closing an API",
    "rising purchasing costs",
]

GENERIC_SOURCES = [
    "exports supplied by the customer", "emails and PDFs in the customer's inbox",
    "accounting exports", "none (manual service)",
]

COUNTRY_SOURCES = {
    "netherlands": [
        "TenderNed / TED", "KVK trade register", "CBS StatLine", "PDOK / BAG", "EP-online energy labels",
        "wetten.overheid.nl", "officielebekendmakingen.nl", "RDW open data", "rechtspraak.nl rulings",
        "KNMI data", "NVWA inspections", "RVO open data", "lokaleregelgeving.overheid.nl (CVDR)",
    ],
    "belgium": [
        "KBO/BCE company register", "Belgian Official Gazette (Staatsblad/Moniteur)",
        "e-Procurement / TED", "Statbel", "data.gov.be", "EPC registers of the regions",
    ],
    "germany": [
        "Handelsregister", "Bundesanzeiger", "Destatis", "GovData", "TED public procurement",
        "Marktstammdatenregister", "Bundesgesetzblatt",
    ],
    "united kingdom": [
        "Companies House", "Contracts Finder / Find a Tender", "ONS", "data.gov.uk",
        "HM Land Registry price paid", "EPC register", "Food Hygiene Rating Scheme", "legislation.gov.uk",
    ],
    "united states": [
        "SAM.gov contract opportunities", "SEC EDGAR", "Census Bureau data", "data.gov", "USAspending",
        "OSHA inspection data", "FDA databases", "Federal Register", "state business registries",
    ],
}
COUNTRY_ALIASES = {
    "nederland": "netherlands", "the netherlands": "netherlands", "nl": "netherlands",
    "belgië": "belgium", "belgie": "belgium", "be": "belgium",
    "deutschland": "germany", "duitsland": "germany", "de": "germany",
    "uk": "united kingdom", "great britain": "united kingdom", "england": "united kingdom",
    "usa": "united states", "us": "united states", "united states of america": "united states",
}


def sources_for(country: str) -> list[str]:
    key = country.strip().lower()
    key = COUNTRY_ALIASES.get(key, key)
    specific = COUNTRY_SOURCES.get(key)
    if specific:
        return specific + GENERIC_SOURCES
    return [f"public registers or open data in {country} (choose a concrete one)"] + GENERIC_SOURCES
