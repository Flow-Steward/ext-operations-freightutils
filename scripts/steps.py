"""Names, descriptions, groups and field labels of the FreightUtils steps.

Every operation of the pinned ``reference/openapi.json`` has one entry in ``STEPS``
(keyed by its ``operationId``); ``scripts/build_contracts.py`` refuses a snapshot with an
operation that is missing here or an entry for an operation that no longer exists.
``EVERYDAY`` are the shortcuts for the most common lookups: each calls one of those
operations with a fixed part of its inputs.
"""

from __future__ import annotations

from typing import NamedTuple


class Group(NamedTuple):
    group_id: str
    title: str
    summary: str


class Step(NamedTuple):
    step_id: str
    title: str
    description: str
    group: str


class Everyday(NamedTuple):
    step_id: str
    title: str
    description: str
    operation: str
    #: Query values the shortcut always sends.
    fixed: dict[str, str]
    #: The operation's inputs the shortcut offers, in form order.
    inputs: tuple[str, ...]
    #: Inputs renamed for the shortcut: shortcut name -> operation name.
    renamed: dict[str, str]
    #: Inputs the shortcut requires, though the operation itself may not.
    required: tuple[str, ...]


GROUPS: tuple[Group, ...] = (
    Group(
        "dangerous_goods",
        "Dangerous goods (ADR)",
        "UN numbers, the ADR 1.1.3.6 exemption, limited and excepted quantities, consignment "
        "checks, Table A codes and what ADR 2027 changes.",
    ),
    Group(
        "calculators",
        "Freight calculators",
        "Loading metres, CBM, chargeable weight, pallet fitting, unit conversion and "
        "ISO 14083 / GLEC emissions.",
    ),
    Group(
        "consignments",
        "Consignments and bookings",
        "Whole loads at once: totals per line, a shipment summary, a booking check and the "
        "consignment object.",
    ),
    Group(
        "customs",
        "Customs and tariffs",
        "HS codes, UK duty and VAT, EU TARIC measures and duty, and the ICS2 goods "
        "description check.",
    ),
    Group(
        "locations",
        "Locations and carriers",
        "UN/LOCODE transport locations, airports, the nearest airports to a point and "
        "airline codes.",
    ),
    Group(
        "equipment",
        "Equipment",
        "Shipping containers, air cargo ULDs and road vehicles and trailers.",
    ),
    Group(
        "references",
        "Identifiers and references",
        "Container, air waybill and IMO number checks, free-text resolution, Incoterms 2020 "
        "and customs code lists.",
    ),
    Group(
        "receipts",
        "Check receipts",
        "Read the receipt a check stored for your key, or confirm that a receipt exists.",
    ),
    Group(
        "data",
        "Data sources and changes",
        "Which datasets FreightUtils serves, their licensing and what changed in them.",
    ),
)

STEPS: dict[str, Step] = {
    # Dangerous goods (ADR)
    "lookupAdr": Step(
        "look_up_dangerous_goods",
        "Look up dangerous goods",
        "Finds ADR Table A entries by UN number, name or hazard class, or several UN numbers "
        "at once, with the ADR 2025 or 2027 edition.",
        "dangerous_goods",
    ),
    "calculateAdrExemptionGet": Step(
        "check_adr_exemption_for_substance",
        "Check ADR exemption for one substance",
        "Works out the ADR 1.1.3.6 points for one UN number and quantity and says whether the "
        "small-load exemption applies.",
        "dangerous_goods",
    ),
    "calculateAdrExemption": Step(
        "check_adr_exemption_for_load",
        "Check ADR exemption for a load",
        "Works out the ADR 1.1.3.6 points for a mixed load of several substances and says "
        "whether the small-load exemption applies.",
        "dangerous_goods",
    ),
    "checkLqEq": Step(
        "check_limited_quantities",
        "Check limited or excepted quantities",
        "Checks items against the ADR limited quantity (3.4) or excepted quantity (3.5) limits.",
        "dangerous_goods",
    ),
    "checkAdrConsignment": Step(
        "check_adr_consignment",
        "Check ADR consignment",
        "Checks a whole dangerous-goods consignment: 1.1.3.6, LQ/EQ, tunnels, document "
        "strings and mixed loading.",
        "dangerous_goods",
    ),
    "listAdrCodes": Step(
        "list_adr_codes",
        "List ADR codes",
        "Lists the ADR Table A code families, or the codes of one family, with what each means.",
        "dangerous_goods",
    ),
    "getAdrCode": Step(
        "get_adr_code",
        "Get ADR code",
        "Reads one ADR Table A code (special provision, packing instruction, tank code and "
        "others) and what it means.",
        "dangerous_goods",
    ),
    "checkAdr2027Changes": Step(
        "check_adr_2027_changes",
        "Check ADR 2027 changes",
        "Lists what ADR 2027 changes for each UN number you give.",
        "dangerous_goods",
    ),
    # Freight calculators
    "calculateLdm": Step(
        "calculate_loading_metres",
        "Calculate loading metres",
        "Works out the loading metres (LDM) of pallets on a truck or trailer and whether they fit.",
        "calculators",
    ),
    "calculateCbm": Step(
        "calculate_cbm",
        "Calculate CBM",
        "Works out the volume of pieces in cubic metres, litres and cubic feet.",
        "calculators",
    ),
    "calculateChargeableWeight": Step(
        "calculate_chargeable_weight",
        "Calculate chargeable weight",
        "Works out the air or sea chargeable weight from dimensions and gross weight.",
        "calculators",
    ),
    "calculatePalletFitting": Step(
        "calculate_pallet_fitting",
        "Calculate pallet fitting",
        "Works out how many boxes fit on a pallet, per layer and in total.",
        "calculators",
    ),
    "convertUnits": Step(
        "convert_units",
        "Convert units",
        "Converts weights, volumes and lengths, including freight units such as chargeable kg "
        "and freight tonnes.",
        "calculators",
    ),
    "calculateEmissions": Step(
        "calculate_emissions",
        "Calculate emissions",
        "Works out the CO2e of a shipment by mass, distance and transport mode under ISO 14083 "
        "and the GLEC Framework.",
        "calculators",
    ),
    # Consignments and bookings
    "calculateConsignment": Step(
        "calculate_consignment",
        "Calculate consignment",
        "Totals a multi-line consignment: volume, weights, chargeable weight and loading "
        "metres per line and in total.",
        "consignments",
    ),
    "shipmentSummary": Step(
        "summarize_shipment",
        "Summarize shipment",
        "Summarizes a shipment in one answer: totals, chargeable weight, dangerous goods, "
        "duty inputs and emissions.",
        "consignments",
    ),
    "checkBooking": Step(
        "check_booking",
        "Check booking",
        "Checks a road booking: what it lacks, what the job needs and what to ask the customer.",
        "consignments",
    ),
    "validateConsignmentObject": Step(
        "validate_consignment",
        "Validate consignment",
        "Validates a consignment object against its schema and says what is wrong in it.",
        "consignments",
    ),
    # Customs and tariffs
    "lookupHsCodes": Step(
        "look_up_hs_codes",
        "Look up HS codes",
        "Finds HS 2022 codes by code, description or section, or several codes at once.",
        "customs",
    ),
    "estimateDuty": Step(
        "estimate_uk_duty",
        "Estimate UK duty",
        "Estimates UK import duty and VAT for a commodity code, origin and customs value from "
        "the UK Trade Tariff.",
        "customs",
    ),
    "lookupEuTariff": Step(
        "look_up_eu_tariff",
        "Look up EU tariff",
        "Lists the EU TARIC measures on a CN or TARIC code for a date and origin.",
        "customs",
    ),
    "calculateEuDuty": Step(
        "calculate_eu_duty",
        "Calculate EU duty",
        "Calculates EU customs duty from every TARIC measure on the code for the origin and value.",
        "customs",
    ),
    "checkIcs2StopWords": Step(
        "check_ics2_description",
        "Check ICS2 goods description",
        "Screens a goods description against the ICS2 list of vague words customs refuse.",
        "customs",
    ),
    # Locations and carriers
    "searchUnlocode": Step(
        "look_up_locations",
        "Look up UN/LOCODE locations",
        "Finds ports, terminals and other transport locations by UN/LOCODE, name or country.",
        "locations",
    ),
    "lookupAirport": Step(
        "look_up_airports",
        "Look up airports",
        "Finds airports by IATA or ICAO code, name or type.",
        "locations",
    ),
    "nearestAirport": Step(
        "find_nearest_airports",
        "Find nearest airports",
        "Finds the airports nearest to a latitude and longitude.",
        "locations",
    ),
    "searchAirlines": Step(
        "look_up_airlines",
        "Look up airlines",
        "Finds airlines by IATA or ICAO code, AWB prefix, name or country.",
        "locations",
    ),
    # Equipment
    "getContainers": Step(
        "look_up_containers",
        "Look up containers",
        "Reads shipping container sizes and capacities, and how many items of a size fit in one.",
        "equipment",
    ),
    "getULDs": Step(
        "look_up_ulds",
        "Look up ULDs",
        "Reads air cargo unit load devices (ULDs) by code, category or deck.",
        "equipment",
    ),
    "getVehicles": Step(
        "look_up_vehicles",
        "Look up vehicles",
        "Reads road vehicle and trailer types with their dimensions and payloads.",
        "equipment",
    ),
    # Identifiers and references
    "validateIdentifier": Step(
        "validate_identifiers",
        "Validate identifiers",
        "Checks container numbers (ISO 6346), air waybills and IMO numbers, one at a time or "
        "every one found in a text.",
        "references",
    ),
    "resolveReference": Step(
        "resolve_reference",
        "Resolve reference",
        "Identifies any freight code or name (UN number, HS code, LOCODE, airport, airline "
        "and more) as ranked, cited candidates.",
        "references",
    ),
    "lookupIncoterms": Step(
        "look_up_incoterms",
        "Look up Incoterms",
        "Reads Incoterms 2020 rules: who pays, who carries the risk and where it passes.",
        "references",
    ),
    "listCodeLists": Step(
        "list_code_lists",
        "List code lists",
        "Lists the customs and trade code lists FreightUtils serves.",
        "references",
    ),
    "lookupCodeList": Step(
        "look_up_code_list",
        "Look up code list",
        "Finds codes in one code list, such as CDS procedure codes, by code or name.",
        "references",
    ),
    # Check receipts
    "getCheckReceipt": Step(
        "get_check_receipt",
        "Get check receipt",
        "Reads the receipt a check stored for your API key: inputs, edition, rules and result.",
        "receipts",
    ),
    "verifyCheckReceipt": Step(
        "verify_check_receipt",
        "Verify check receipt",
        "Confirms that a check receipt exists and reads its hash, without its contents.",
        "receipts",
    ),
    # Data sources and changes
    "getCoverageMatrix": Step(
        "get_data_coverage",
        "Get data coverage",
        "Reads which datasets FreightUtils serves, their editions and how they are verified.",
        "data",
    ),
    "getDataLicensing": Step(
        "get_data_licensing",
        "Get data licensing",
        "Reads the licensing and attribution of each dataset.",
        "data",
    ),
    "getChanges": Step(
        "list_data_changes",
        "List data changes",
        "Lists what changed in the served datasets since a date or a cursor.",
        "data",
    ),
}

EVERYDAY: tuple[Everyday, ...] = (
    Everyday(
        "look_up_un_number",
        "Look up UN number",
        "Reads the ADR entry of one UN number: name, class, packing group, labels, tunnel code "
        "and transport category.",
        "lookupAdr",
        {},
        ("un", "edition", "as_of"),
        {},
        ("un",),
    ),
    Everyday(
        "look_up_hs_code",
        "Look up HS code",
        "Reads one HS 2022 code with its description, parents and children.",
        "lookupHsCodes",
        {},
        ("code",),
        {},
        ("code",),
    ),
    Everyday(
        "look_up_location_code",
        "Look up location code",
        "Reads one UN/LOCODE: the place, its country, functions and coordinates.",
        "searchUnlocode",
        {},
        ("code",),
        {},
        ("code",),
    ),
    Everyday(
        "validate_container_number",
        "Validate container number",
        "Checks the check digit of a container number (ISO 6346) and reads its owner prefix "
        "and category.",
        "validateIdentifier",
        {"type": "container"},
        ("container_number",),
        {"container_number": "value"},
        ("container_number",),
    ),
    Everyday(
        "validate_air_waybill",
        "Validate air waybill",
        "Checks the check digit of an air waybill number and reads its airline prefix.",
        "validateIdentifier",
        {"type": "awb"},
        ("air_waybill",),
        {"air_waybill": "value"},
        ("air_waybill",),
    ),
)

#: Labels of inputs whose name alone does not say what they are; others are the name in
#: words. Per operation where one name means different things.
LABELS: dict[str, str] = {
    "as_of": "Date",
    "bh": "Box height (cm)",
    "bl": "Box length (cm)",
    "bw": "Box width (cm)",
    "bwt": "Box weight (kg)",
    "check_id": "Receipt ID",
    "client": "Caller label",
    "codes": "Codes",
    "customs_value": "Customs value",
    "distance_km": "Distance (km)",
    "envelope": "Response envelope",
    "freight_cost": "Freight cost",
    "from": "From unit",
    "gw": "Gross weight (kg)",
    "h": "Height (cm)",
    "iata": "IATA code",
    "icao": "ICAO code",
    "if_stale": "If data is stale",
    "include_all": "Include all airports",
    "include_codes": "Include codes",
    "include_deprecated": "Include deprecated codes",
    "insurance_cost": "Insurance cost",
    "l": "Length (cm)",
    "lat": "Latitude",
    "length": "Pallet length (mm)",
    "lon": "Longitude",
    "max_results": "Maximum results",
    "mpw": "Maximum payload (kg)",
    "pcs": "Pieces",
    "ph": "Pallet deck height (cm)",
    "pl": "Pallet length (cm)",
    "pmh": "Pallet maximum height (cm)",
    "pw": "Pallet width (cm)",
    "q": "Search",
    "qty": "Quantity",
    "radius_km": "Radius (km)",
    "sub_mode": "Sub-mode",
    "to": "To unit",
    "un": "UN number",
    "un_numbers": "UN numbers",
    "vehicle_length": "Vehicle length (m)",
    "w": "Width (cm)",
    "weight": "Weight per pallet (kg)",
    "width": "Pallet width (mm)",
    "wt": "Item weight (kg)",
    "container_number": "Container number",
    "air_waybill": "Air waybill number",
}

OPERATION_LABELS: dict[tuple[str, str], str] = {
    ("calculateAdrExemptionGet", "qty"): "Quantity (kg or litres)",
    ("calculateLdm", "qty"): "Number of pallets",
    ("getContainers", "qty"): "Number of items",
    ("convertUnits", "value"): "Value",
    ("validateIdentifier", "value"): "Identifier",
    ("validateIdentifier", "text"): "Text to scan",
    ("getContainers", "type"): "Container type",
    ("getULDs", "type"): "ULD type",
    ("lookupAirport", "type"): "Airport type",
    ("nearestAirport", "type"): "Airport type",
    ("validateIdentifier", "type"): "Identifier type",
    ("validateConsignmentObject", "type"): "Schema",
    ("lookupIncoterms", "code"): "Incoterm",
    ("lookupHsCodes", "code"): "HS code",
    ("searchUnlocode", "code"): "UN/LOCODE",
    ("getULDs", "code"): "ULD code",
    ("lookupCodeList", "code"): "Code",
    ("getAdrCode", "code"): "Code",
    ("lookupEuTariff", "code"): "CN or TARIC code",
    ("calculateEuDuty", "code"): "TARIC code",
    ("getChanges", "since"): "Since",
}

#: Help for inputs the snapshot documents without a description.
HELP: dict[str, str] = {
    "check_id": "The receipt ID a check answer gave (check_id).",
    "destination": "Where the shipment goes: an object with the same fields as origin.",
    "family": "The code family, for example sp, pi or tank_code.",
    "incoterm": "The Incoterms 2020 rule of the shipment, for example FOB or DAP.",
    "items": "The items, as FreightUtils documents them for this step.",
    "journey": "The journey: date, route and tunnels, as FreightUtils documents it.",
    "lines": "The lines of the load, as FreightUtils documents them for this step.",
    "mode": "The transport mode, for example road, sea or air.",
    "options": "Extra options, as FreightUtils documents them for this step.",
    "origin": "Where the shipment starts.",
    "origin_country": "ISO 3166 alpha-2 code of the country of origin, for example CN.",
    "type": "The type, as FreightUtils documents it for this step.",
    "vehicle": "The vehicle, as FreightUtils documents it for this step.",
    "container_number": "The container number, for example CSQU3054383.",
    "air_waybill": "The air waybill number, for example 020-12345675.",
}
