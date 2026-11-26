# FreightUtils for Flow Steward — dangerous goods, freight calculators and customs data

<img src="icon.png" width="96" alt="FreightUtils for Flow Steward">

[![CI](https://img.shields.io/github/actions/workflow/status/Flow-Steward/ext-operations-freightutils/ci.yml?branch=main&label=CI)](https://github.com/Flow-Steward/ext-operations-freightutils/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/Flow-Steward/ext-operations-freightutils?label=release)](https://github.com/Flow-Steward/ext-operations-freightutils/releases/latest)

Give your logistics workflows and AI agents a freight reference desk. Look up a UN number and its ADR rules, check the ADR 1.1.3.6 exemption for a mixed load, work out loading metres, chargeable weight and CO2e, find an HS code and estimate UK or EU duty, check a container number — every answer with the source it comes from.

## What is this

[FreightUtils](https://www.freightutils.com) is a neutral freight reference service: dangerous goods, freight maths, customs codes and duty, locations, carriers and equipment, each answer citing its authority and edition. [Flow Steward](https://docs.flowsteward.org) runs workflows and AI agents that connect your business systems.

This extension puts FreightUtils into Flow Steward: **every one of the 40 operations of the FreightUtils API is a workflow step**, plus everyday shortcuts for the lookups you make most.

## What you can do

- **Check dangerous goods before dispatch.** Read the ADR entry of a UN number (class, packing group, labels, tunnel code, transport category), check whether a mixed load stays under the ADR 1.1.3.6 thresholds, check limited and excepted quantities, and see what ADR 2027 changes for your UN numbers.
- **Plan loads.** Loading metres on a trailer, CBM, air and sea chargeable weight, boxes per pallet, container capacity, ULD and vehicle dimensions, and unit conversion.
- **Report emissions.** CO2e of a shipment by mass, distance and mode under ISO 14083 and the GLEC Framework.
- **Prepare customs data.** Find HS 2022 codes, estimate UK import duty and VAT, read EU TARIC measures and calculate EU duty, and screen goods descriptions against the ICS2 list of vague words.
- **Check what customers send.** Validate container numbers (ISO 6346), air waybills and IMO numbers, or find and check every one in an email or booking line; check a road booking for what it lacks.
- **Resolve any code.** Turn a UN number, HS code, UN/LOCODE, airport, airline or Incoterm into ranked, cited candidates; read Incoterms 2020 rules and customs code lists.

## Why teams use it

- **Answers you can cite.** Each answer names its authority, dataset and edition — UNECE ADR, WCO HS 2022, UN/LOCODE, ICC Incoterms 2020, ISO 14083 / GLEC — and the step returns that source block next to the values.
- **Right edition for the date.** Ask for ADR 2025 or ADR 2027, or give the date of carriage and get the edition that applies.
- **Safe to automate.** Every step only reads. Nothing is booked, sent or changed, so steps can run in any workflow and in test runs.
- **Built for AI agents.** Clear step names and inputs let an agent pick the right lookup and quote the source with the answer.
- **Start free.** No account needed for 25 requests a day; a free API key gives 100 a day and Pro 50,000 a month.

## Steps by group

- **Dangerous goods (ADR)** — 8 steps
- **Freight calculators** — 6 steps
- **Consignments and bookings** — 4 steps
- **Customs and tariffs** — 5 steps
- **Locations and carriers** — 4 steps
- **Equipment** — 3 steps
- **Identifiers and references** — 5 steps
- **Check receipts** — 2 steps
- **Data sources and changes** — 3 steps

Everyday shortcuts: **Look up UN number**, **Look up HS code**, **Look up location code**, **Validate container number**, **Validate air waybill**. The extension's **API** tab lists every step with what it does; **API coverage** maps each one to its FreightUtils endpoint.

## Get started

1. In Flow Steward open **Extensions → FreightUtils → Connection**, choose your project and add a connection.
2. Optional: paste a FreightUtils API key from [freightutils.com/pricing](https://www.freightutils.com/pricing) (free or Pro). Leave it empty to start with 25 requests a day.
3. Select **Test connection**, then add FreightUtils steps to your workflows. The **Setup Guide** tab walks through each step.

## Requirements

- Flow Steward with extension support and outbound HTTPS access to www.freightutils.com.
- Optional: a FreightUtils API key for more than 25 requests a day.

## FAQ

**Do I need a FreightUtils account?**
No. Without an API key FreightUtils answers 25 requests a day per address. A free key (email only) raises it to 100 a day; Pro gives 50,000 a month.

**What happens when the allowance is spent?**
The step fails with `rate_limited` and says when the allowance resets. It is not repeated automatically, so no further requests are used.

**Can I store the answers?**
Yes. FreightUtils' terms let you store, show and cite answers in your own systems as long as the source line stays with the values. The step returns it in `source`.

**Which ADR edition do I get?**
The one that applies on the date you give, or today's. ADR 2027 applies from 1 January 2027 and ADR 2025 may still be used until 30 June 2027; set **Edition** to choose one.

**Does any step change data?**
No. Every step reads. The calculators and checks send your inputs to be computed and change nothing.

## In your language

**Русский.** Расширение подключает FreightUtils к workflow и AI-агентам Flow Steward: опасные грузы (ADR 2025 и 2027, исключение 1.1.3.6, LQ/EQ), погрузочные метры, CBM, платный вес, выбросы CO2e по ISO 14083, коды ТН ВЭД (HS), пошлины Великобритании и ЕС, Incoterms 2020, UN/LOCODE, аэропорты, авиакомпании, контейнеры и проверка номеров контейнеров и авианакладных. Каждый ответ — с указанием источника. Все 40 операций API — отдельные шаги; без ключа 25 запросов в день.

**Lietuviškai.** Plėtinys prijungia FreightUtils prie Flow Steward workflow ir AI agentų: pavojingi kroviniai (ADR), krovimo metrai, CBM, apmokestinamasis svoris, CO2e emisijos, HS kodai, JK ir ES muitai, Incoterms 2020, UN/LOCODE ir konteinerių numerių tikrinimas — kiekvienas atsakymas su šaltiniu.

**Polski.** Rozszerzenie łączy FreightUtils z workflow i agentami AI Flow Steward: towary niebezpieczne (ADR), metry ładowne, CBM, waga płatna, emisje CO2e, kody HS, cła w Wielkiej Brytanii i UE, Incoterms 2020, UN/LOCODE i sprawdzanie numerów kontenerów — każda odpowiedź ze źródłem.

## Links

- [FreightUtils API documentation](https://www.freightutils.com/api-docs)
- [FreightUtils pricing](https://www.freightutils.com/pricing)
- [FreightUtils data licensing](https://www.freightutils.com/data-licensing)
- [Flow Steward documentation](https://docs.flowsteward.org)
- [Report a problem](https://github.com/Flow-Steward/ext-operations-freightutils/issues)

## For developers

The steps are generated from FreightUtils' OpenAPI description, pinned in `reference/openapi.json`: `python3 scripts/build_contracts.py` writes the contracts, forms, actions, the runtime registry and the API pages, and `python3 scripts/check_upstream.py` compares the snapshot with the live description. The runtime (`runtime/`) checks every input against the registry, sends one HTTPS request to www.freightutils.com and returns the answer with its source block. Tests run with `python -m pytest tests`.

FreightUtils and its mark belong to their owner. This extension is not made or endorsed by FreightUtils.
