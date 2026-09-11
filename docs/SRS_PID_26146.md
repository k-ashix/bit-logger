# Software Requirements Specification (SRS)

**Project:** AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic
**Problem Statement ID:** 26146
**Organization:** National Technical Research Organisation (NTRO)
**Category:** Software | **Theme:** Blockchain & Cybersecurity
**Document Version:** 1.0.0
**Prepared for:** Offline, Linux-based investigative-analytics prototype (Docker-first reproducible deployment)

---

## 0. Problem Statement — Source Brief (NTRO / SIH 2026)

> This section is a verbatim-faithful, consolidated representation of the original NTRO problem statement for PS ID 26146. It is included here so the SRS is fully self-contained and every requirement can be traced back to the source brief. No paraphrasing has been added — only formatting and deduplication.

### 0.1 Identity

| Field | Value |
|---|---|
| **Problem Statement ID** | 26146 |
| **Title** | AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic |
| **Organization** | National Technical Research Organisation (NTRO) |
| **Department** | National Technical Research Organisation (NTRO) |
| **Category** | Software |
| **Theme** | Blockchain & Cybersecurity |

### 0.2 Background

Bitcoin's pseudonymous, peer-to-peer design lets criminal actors move, layer, and cash out illicit funds — ransomware payments, darknet-market proceeds, extortion, and laundering — while evading traditional financial surveillance.

The objective of this problem statement is to design and build a **complete offline system** that ingests bulk Bitcoin transaction/network metadata (CSV/JSON/XML), correlates network-layer (IP/port/timing) observations with blockchain-layer (wallet/TXID/amount) data, and applies AI/ML to detect anomalies, cluster entities, and generate prioritized, explainable investigative leads.

### 0.3 Challenge Objectives

1. **Ingest & Parse** — a bulk metadata dataset containing: `timestamp`, `src/dst IP & port`, `TXID`, `input/output wallet addresses`, `amounts`, `fee`, `script type`.
2. **Build a Graph** — an entity/transaction graph linking IP addresses, wallets, and transactions.
3. **Implement AI/ML Detection** — with a working model (not just rules) across the focus areas listed below.
4. **Generate Ranked Alerts** — an explainable alert list stating why a wallet/transaction was flagged, accompanied by a confidence score.
5. **Present Findings** — via a dashboard or link-analysis visualization showing flagged entities and evidence for each flag.

### 0.4 Suggested AI/ML Focus Areas

| Focus Area | What to Build |
|---|---|
| **Entity Clustering** | Group wallets likely owned by one entity using Common-Input-Ownership Heuristic (CIOH) + graph embeddings |
| **Anomaly Detection** | Flag statistically unusual transactions and flows |
| **Peeling-Chain / Mixing Detection** | Detect laundering-pattern transaction sequences — peeling chains and CoinJoin-like structures |
| **Risk Scoring** | Propagate risk scores from seed illicit wallets across the graph via graph algorithms |

### 0.5 Dataset Requirements

Participants work with a **synthetic dataset modelled on real Bitcoin P2P/transaction fields** — no real seized or live-intercept data is provided.

**Minimum required fields:**
```
timestamp, src_ip, dst_ip, src_port, dst_port, txid,
input_addresses[], output_addresses[],
input_amounts[], output_amounts[],
geo_country, asn   ← integrate an open-source, downloadable GeoIP database
```

### 0.6 Expected Deliverables

- A workable, complete **offline solution for the Linux platform**.
- A **working prototype** (code repository) with ingestion, correlation, and AI/ML models.
- A **short technical write-up** covering approach, model choices, and the explainability method used.
- A **dashboard / visualization** showing flagged entities and evidence for each flag.

---

## 1. Introduction

### 1.1 Purpose
This SRS defines the functional, data, and non-functional requirements for an **offline** system that ingests synthetic Bitcoin transaction and network-metadata records, fuses network-layer (IP/port/timing) signals with blockchain-layer (wallet/TXID/amount) signals, and applies AI/ML techniques to surface **explainable, ranked investigative leads** — flagged wallets/transactions with a confidence score and supporting evidence — through a link-analysis dashboard.

### 1.2 Scope
The system is a **closed, self-contained analytics pipeline**, not a live blockchain node or a real surveillance tool. It:
- Consumes **synthetic** datasets (CSV/JSON/XML) modeled on real Bitcoin P2P and transaction fields — no real seized data, no live wiretap/intercept data, and no attempt to deanonymize real individuals.
- Builds a graph joining IP addresses, wallet addresses, and transactions.
- Runs four **AI/ML and statistical detection modules**: entity clustering (heuristic + graph ML), anomaly detection (unsupervised ML), peeling-chain/CoinJoin detection (graph/statistical rules), and risk-score propagation (graph algorithm).
- Outputs a ranked, explainable alert list and a visual dashboard.
- Runs fully offline on Linux once all dependencies and reference databases (e.g., GeoIP) are pre-downloaded.

Out of scope: live mempool/P2P sniffing, real-money custody, deanonymizing real persons, or any production law-enforcement deployment (this is a research/hackathon prototype).

### 1.3 Intended Audience
Hackathon evaluators, the development team, and anyone extending the prototype into a fuller investigative tool.

### 1.4 Definitions
- **TXID** — Transaction ID (blockchain layer).
- **UTXO** — Unspent Transaction Output.
- **Peeling chain** — A laundering pattern where a large input is repeatedly split, sending a small "peel" to a destination and the remainder to a fresh change address, chained many times.
- **CoinJoin** — A privacy technique combining multiple users' inputs into one transaction with equal-sized outputs, obscuring which input funded which output.
- **CIOH** — Common-Input-Ownership Heuristic: addresses spent together as inputs in the same transaction are assumed to belong to one entity.
- **ASN** — Autonomous System Number, identifying the network/ISP that announces an IP block.

---

## 2. Overall System Architecture

```
 ┌────────────────────┐      ┌──────────────────────┐      ┌───────────────────────┐
 │ 1. Ingestion Layer │ ---> │ 2. Correlation &     │ ---> │ 3. AI/ML Detection    │
 │ (CSV/JSON/XML      │      │    Graph Builder     │      │    Layer              │
 │  parsers, schema   │      │ (IP–Wallet–TXID      │      │ - Entity clustering   │
 │  validation)       │      │  entity graph, GeoIP │      │ - Anomaly detection   │
 └────────────────────┘      │  enrichment)         │      │ - Peeling/CoinJoin    │
                             └──────────────────────┘      │ - Risk propagation    │
                                                           └───────────┬───────────┘
                                                                       │
                              ┌──────────────────────┐      ┌───────────▼───────────┐
                              │ 5. Dashboard /       │ <--- │ 4. Explainability &   │
                              │    Link-Analysis UI  │      │    Alert Ranking      │
                              │ (graph view, alert   │      │ (SHAP, rule traces,   │
                              │table, evidence pane) │      │  confidence scoring)  │
                              └──────────────────────┘      └───────────────────────┘
```

All five stages run as local batch jobs against a local datastore — no external network calls are required at run time once reference data is cached locally.

**Storage Architecture (resolved):** Two storage engines serve distinct roles:
- **PostgreSQL** — system of record for application state: ingested records, graph metadata, entities, alerts, run metadata, evidence objects. Managed via Alembic migrations.
- **DuckDB** — optional analytical query engine for fast ad-hoc analytics on large processed Parquet/CSV datasets (e.g., bulk feature aggregation, historical alert queries). Not required for core pipeline operation.

This split is intentional: PostgreSQL provides transactional integrity and a stable API data layer; DuckDB provides columnar analytics speed without replacing the system of record.

---

## 2.1 Operating Modes

The system supports three distinct operating modes. All three run fully offline once dependencies are installed.

| Mode | Description | Intended User | Dataset | Setup |
|------|-------------|---------------|---------|-------|
| **Demo Mode** | Bundled synthetic scenario packs run end-to-end automatically; zero analyst configuration required. Evaluators can observe the full pipeline — ingestion → graph → detection → alert — without supplying any files. | Hackathon evaluators, reviewers | Pre-bundled `data/synthetic/scenario_*/` | `docker compose --profile demo up` or `./scripts/run_demo.sh` |
| **Offline Analysis Mode** | Analyst supplies local CSV/JSON/XML files and (optionally) a local GeoIP `.mmdb`. The pipeline runs against analyst-supplied data. | Analysts, testers | Analyst-supplied local files mounted via volume | `docker compose up` with `./data` volume mounted |
| **Development Mode** | Notebooks, model experimentation, threshold tuning, test datasets. Individual pipeline stages are runnable in isolation. | Developers | Any dataset; test fixtures in `tests/fixtures/` | `jupyter lab` or `python -m backend.app.pipeline.stages --stage <name>` |

> **Why this matters:** During judging the system runs in Demo Mode (zero setup, deterministic output). During evaluation a reviewer can switch to Offline Analysis Mode to supply their own data. Development Mode supports reproducible experimentation and threshold tuning.

---

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-1 | The system shall parse bulk metadata files in CSV, JSON, and XML containing at minimum: `timestamp, src_ip, dst_ip, src_port, dst_port, txid, input_addresses[], output_addresses[], input_amounts[], output_amounts[], fee, script_type`. |
| FR-2 | The system shall validate and normalize records (type checks, address-format checks, timestamp normalization to UTC) and quarantine malformed rows with a reason code. |
| FR-3 | The system shall enrich every IP with `geo_country` and `asn` using a local, offline-queryable GeoIP database. |
| FR-4 | The system shall construct a heterogeneous graph with three node types — **IP**, **Wallet**, **Transaction** — and edges: `IP —observed_in→ Transaction`, `Wallet —input_to/output_of→ Transaction`. |
| FR-5 | The system shall cluster wallets into probable entities using the Common-Input-Ownership Heuristic (CIOH) plus a graph-embedding-based clustering step (Node2Vec/GraphSAGE embeddings + HDBSCAN/community detection), and shall handle known CIOH pitfalls (CoinJoin false-merges) by excluding transactions flagged as CoinJoin-like from the CIOH step. |
| FR-6 | The system shall run an unsupervised anomaly-detection model (e.g., Isolation Forest / Autoencoder) over per-transaction and per-wallet numeric features (amount, fee-rate, fan-in/fan-out, inter-arrival time, round-number ratio, new-address ratio) and output an anomaly score per entity. |
| FR-7 | The system shall detect peeling-chain sequences (a change output re-spent repeatedly with a shrinking "peel" pattern) and CoinJoin-like structures (many inputs/outputs of near-equal value in one transaction) via graph traversal + statistical tests. |
| FR-8 | The system shall propagate a **risk score** from a seed set of labeled illicit wallets across the graph (e.g., personalized PageRank / label propagation / guilt-by-association decay), producing a 0–100 risk score and a separate 0–100 **confidence score** for every wallet/entity. The risk score reflects how suspicious the entity appears; the confidence score reflects how strongly the available evidence supports that conclusion. |
| FR-9 | The system shall combine module outputs (clustering, anomaly, pattern flags, risk score) into a single ranked alert list. Each alert shall carry: `entity_id`, `run_id`, `detector`, `risk_score`, `confidence_score`, top contributing features/patterns (explanation), alert lifecycle state, and links to the underlying TXIDs/IPs. |
| FR-10 | The system shall provide a dashboard that shows: (a) an interactive link-analysis graph (IP–wallet–transaction), (b) a sortable/filterable alert table with lifecycle state, (c) an evidence panel per alert showing the specific transactions/edges that triggered it, and (d) a **Pipeline Status panel** displaying records processed/rejected, graph nodes/edges, entities discovered, anomalies, pattern flags, alerts, pipeline duration, and model/config version. |
| FR-11 | The system shall run end-to-end from the command line / a single script with no live internet access required at run time. |
| FR-12 | The system shall log every processing stage (records parsed, rejected, entities created, alerts generated) for auditability. |
| FR-13 | The system shall externalize all configurable parameters — including anomaly thresholds, peeling-chain minimum length, CoinJoin thresholds, PageRank damping factor, alert score weights, clustering parameters, and dataset paths — in a versioned configuration file (YAML/JSON). |
| FR-14 | The system shall record the exact parameter/configuration version (`config_version`) used for every pipeline run, so that two runs on the same data with the same config are reproducible. |
| FR-15 | The system shall support evaluation of detection modules against hidden synthetic ground-truth labels without exposing those labels to the dashboard or the alert UI. Evaluation shall report precision, recall, F1-score, and false-positive rate per detector. |
| FR-16 | The system shall preserve data lineage from every processed record to the originating input file and ingestion batch (`dataset_id`, `filename`, `SHA-256`, `record_count`, `schema_version`, `ingestion_batch_id`). |
| FR-17 | The system shall retain dataset checksum/hash (SHA-256) information for each pipeline run so that the exact input that produced a given alert can always be identified. |
| FR-18 | Reprocessing the same input batch shall not create duplicate records, entities, or alerts (idempotent processing via batch/dataset hash deduplication). |
| FR-19 | The system shall support incremental processing: supplying a new batch file shall process only new records without requiring a full rebuild of the graph, features, or scores from prior batches, where feasible. |
| FR-20 | The system shall export an investigation summary for a selected alert/entity as JSON and CSV, containing: scores, evidence, graph paths, transactions, IP context, explanations, and run metadata. |

---

## 4. AI/ML Focus Areas — Design Detail

### 4.1 Entity Clustering
- **Heuristic layer:** CIOH — all input addresses of a transaction are assumed co-owned, forming union-find clusters. Apply the well-known refinement of *excluding* transactions that look like CoinJoins (equal-value multi-output, many independent input clusters) before applying CIOH, since CoinJoin defeats this heuristic.
- **Change-address heuristic** (optional refinement): identify the likely "change" output (new address, non-round amount) to strengthen clusters.
- **Embedding layer:** represent the wallet–transaction graph with Node2Vec or GraphSAGE (unsupervised) to capture structural similarity beyond direct co-spending, then cluster embeddings with HDBSCAN (handles noise/outliers, no need to pre-set cluster count) or Louvain/Leiden community detection on the projected wallet graph.
- **Output:** entity_id → {wallet list, first/last seen, aggregate in/out volume}.

### 4.2 Anomaly Detection
- **Features per transaction/wallet:** amount (log-scaled), fee rate, number of inputs/outputs, time since address creation, time-of-day/periodicity, ratio of round-number amounts, address reuse rate, burst rate (transactions per hour).
- **Models:** start with **Isolation Forest** (fast, interpretable via path length) and/or a simple **Autoencoder** (reconstruction error as anomaly score) for comparison; z-score/IQR baselines as a sanity check.
- **Output:** anomaly_score per transaction and per wallet (aggregated).

### 4.3 Peeling-Chain / Mixing Detection
- **Peeling chain:** traverse the transaction graph following the "change" edge; flag chains of length ≥ N (configurable, e.g., 5) where one output is small/variable ("peel") and the other is the bulk being carried forward.
- **CoinJoin-like detection:** flag transactions with ≥ K inputs and ≥ K outputs where multiple outputs share the same (or near-equal) amount — a recognized fingerprint of CoinJoin/equal-output mixing.
- **Output:** pattern flags attached to transactions/entities (`peeling_chain`, `coinjoin_like`) with the matched subgraph for evidence.

> **Terminology note:** Peeling-chain and CoinJoin detection are **graph/statistical rule-based detectors**, not learned ML models. They are not presented as ML. The four AI/ML and statistical detection modules are: (1) entity clustering — heuristic + graph ML, (2) anomaly detection — unsupervised ML, (3) peeling-chain/CoinJoin detection — graph/statistical rules, (4) risk propagation — graph algorithm.

### 4.4 Risk Scoring
- **Seed labels:** a small set of "known-illicit" wallets (from the synthetic dataset's ground truth, or optionally style-matched against the public **Elliptic** or **BitcoinHeist** research datasets — see Section 5) act as seeds with risk = 1.
- **Propagation algorithm:** Personalized PageRank from seed nodes, or iterative label propagation with a decay factor per hop, so risk fades with distance/dilutes with mixing through many hops — a standard "taint analysis" approach used in blockchain forensics tools.
- **Output:** `risk_score` per wallet/entity, combinable with the anomaly and pattern-flag scores into the final alert ranking (e.g., weighted sum or a small supervised re-ranker if labels are available).

### 4.5 Explainability
- For anomaly detection: **SHAP** (TreeExplainer for Isolation Forest / KernelExplainer for the autoencoder) to show which features drove a high anomaly score.
- For clustering and risk propagation: **subgraph provenance** — store and display the exact path/edges that produced a cluster merge or a risk-score contribution ("this wallet's score comes from N hops from seed wallet X via transactions T1→T2→T3").
- For pattern detection: rule-trace text ("flagged as peeling chain: 7 consecutive hops, average peel 2% of balance, timestamps within 40 minutes of each other").
- Every alert must be traceable to concrete evidence, not just a black-box number.
- **Persistent evidence object:** every alert stores a structured evidence record containing: `alert_id`, `entity_id`, `run_id`, `detector`, `risk_score`, `confidence_score`, `evidence_type`, `source_transaction_ids[]`, `source_wallet_ids[]`, `source_ip_ids[]`, `graph_path`, `rule_trace`, `feature_contributions`.

### 4.6 Risk Score vs Confidence Score

The system explicitly separates two conceptually distinct numbers:

| Score | Meaning | Example |
|-------|---------|----------|
| **`risk_score`** (0–100) | How suspicious the entity appears, based on proximity to illicit seeds, anomaly magnitude, and pattern flags. | 91/100 — entity is structurally very close to known-illicit seeds |
| **`confidence_score`** (0–100) | How strongly the available evidence supports the risk conclusion. Low if evidence is sparse, noisy, or indirect. | 74/100 — multiple corroborating signals but graph path is 4 hops |

**Why this matters:** An entity can have a high risk score but weak evidence (e.g., 2-hop proximity to a seed with no corroborating anomaly). Separating these two numbers prevents the system from over-presenting uncertain detections and makes explainability substantially stronger. The dashboard displays both numbers side-by-side per alert.

### 4.7 Alert Lifecycle

Every alert transitions through the following states:

```
NEW → REVIEWING → CONFIRMED
                → DISMISSED
                → ESCALATED
```

Alert record fields: `alert_id`, `entity_id`, `run_id`, `state`, `risk_score`, `confidence_score`, `analyst_note`, `reviewed_at`, `reviewer`.

This turns a model output into a minimal investigative workflow visible in the dashboard.

---

## 5. Data Requirements

### 5.1 Minimum Schema
`timestamp, src_ip, src_port, dst_ip, dst_port, txid, input_addresses[], output_addresses[], input_amounts[], output_amounts[], fee, script_type, geo_country, asn`

### 5.2 Where to Get Synthetic / Reference Data (no real seized or intercepted data)

| Source | What it gives you | Access | Notes |
|---|---|---|---|
| **Self-generated synthetic dataset** (recommended primary source) | Full control over all required fields, including network layer (IP/port/timing), which real public datasets never expose (for privacy reasons) | Free, build yourself (see 5.3) | This is what the problem statement explicitly asks for — "synthetic dataset modelled on real Bitcoin P2P/transaction fields." |
| **Elliptic Data Set** (Kaggle) | ~203,769 real Bitcoin transactions, 234,355 edges, ~166 anonymized features, labeled illicit/licit/unknown — no IPs, only blockchain-layer data | Free, Kaggle account required: `kaggle.com/datasets/ellipticco/elliptic-data-set` | Use as a **statistical reference** to make your synthetic transaction-layer data realistic (amount distributions, fan-in/out patterns, label ratios ≈2% illicit / 21% licit / rest unknown), and optionally as an external validation set for your clustering/anomaly logic. |
| **Elliptic++ Dataset** (GitHub/Kaggle) | Extends Elliptic with an **actor/wallet-level** dataset (~822k addresses) in addition to transactions | Free, academic project (search "Elliptic++ dataset GitHub") | Useful if you want wallet-level features to model, not just transaction-level. |
| **BitcoinHeist Ransomware Address Dataset** (UCI ML Repository, ID 526) | ~2.9M address-level records with engineered features (`length, weight, count, looped, neighbors, income`) labeled by ransomware family or "white" (benign) | Free, CC BY 4.0: `archive.ics.uci.edu/dataset/526/bitcoinheistransomwareaddressdataset`, or `pip install ucimlrepo` then `fetch_ucirepo(id=526)` | Good source of realistic **feature engineering ideas** (their `weight`/`count`/`length` features are specifically designed to quantify merging/mixing behavior) and of ransomware-style seed wallets for your risk-propagation seeds. |
| **Public blockchain explorers** (blockchain.com, blockstream.info, mempool.space) via their public APIs | Real transaction structure (inputs, outputs, amounts, fees, script types) for calibrating synthetic-data realism | Free, rate-limited, used only offline/at generation time, not at run time | Use only to sample **structural statistics** (e.g., typical input/output counts, fee distributions) during synthetic-data generation — do not embed real live-fetched data as your working dataset, per the "offline, synthetic-only" requirement. |
| **Bitcoin Core regtest/testnet** | Ability to generate real, syntactically-valid Bitcoin transactions in a private sandbox network you fully control | Free, `bitcoind -regtest` | Optional advanced route: spin up a local regtest network, script many wallets transacting with each other (including deliberate peeling chains and CoinJoin-style joins via tools like `python-bitcoinlib`), and capture the actual TXIDs/scripts this produces — then bolt on synthetic IP/timestamp metadata since regtest has no real P2P diversity. |

### 5.3 Recommended Synthetic-Data Generation Approach
1. **Address/TXID generation:** use `python-bitcoinlib`, `bit`, or simple base58/bech32 encoders to generate syntactically valid-looking addresses and 64-hex-char TXIDs (no real key material needed — random keys never touch a real wallet).
2. **Transaction-graph generation:** use a graph generator (e.g., `networkx` with a preferential-attachment or scale-free model) to lay out a realistic wallet-transaction topology, then calibrate amount/fee/in-out-count distributions against the *published statistics* of Elliptic / BitcoinHeist (not the raw data itself) so your synthetic set "looks like" real chain data.
3. **Inject labeled patterns on purpose:** programmatically insert a known number of peeling chains, CoinJoin-like transactions, and layering sequences, and tag them in a hidden "ground truth" file — this is what lets you actually evaluate precision/recall of your detectors later.
4. **Network-layer simulation:** since no public dataset links real IPs to real wallets (that link is exactly what law enforcement protects), synthesize this layer yourself:
   - Assign each synthetic "actor" a small pool of realistic IPs drawn from publicly known IP/ASN ranges for categories you want to represent (Tor exit nodes, VPN provider ranges, known exchange hosting ranges, residential ISP ranges) — public exit-node lists (e.g., the Tor Project's public exit-node list) and public ASN/IP allocation data (RIPE/APNIC/ARIN delegated stats, both free and downloadable) are good free sources for realistic ranges.
   - Add jittered timestamps and port numbers to simulate P2P propagation delay and peer connections; tools like `scapy` or `mininet` can simulate an actual packet-capture-like feel if you want a literal synthetic pcap, though for this challenge a well-structured CSV/JSON of the same fields is sufficient.
5. **Faker-style noise:** use the `Faker` Python library for any incidental fields (e.g., synthetic node IDs, wallet labels) to avoid hand-authoring everything.
6. **Reproducible seeds:** every synthetic dataset generation run shall record `random_seed`, `dataset_seed`, and `scenario_seed` in a `dataset_metadata.json` alongside the generated files, so the exact dataset can be regenerated deterministically from the same seed.

### 5.3.1 Scenario Packs

Instead of one generic synthetic dataset, the generator produces named **scenario packs** — deterministic, purpose-built datasets that make demonstrations concrete:

| Scenario | Description | Primary pattern planted |
|----------|-------------|------------------------|
| `scenario_01_normal_activity` | Baseline — mostly benign transactions, low anomaly rate | None |
| `scenario_02_peeling_chain` | A multi-hop peeling chain routed through 3 entities | Peeling chain (length ≥ 7) |
| `scenario_03_coinjoin` | CoinJoin-like mixing transactions with equal outputs | CoinJoin structural fingerprint |
| `scenario_04_mixed_activity` | Normal + planted peeling + planted CoinJoin | Both patterns |
| `scenario_05_high_anomaly` | High-volume burst wallets, round-number amounts, fee outliers | Anomaly score spikes |
| `scenario_06_cross_ip_wallet_activity` | Same wallets observed from multiple geographic IP regions | IP–wallet cross-attribution |
| `scenario_07_noise_heavy` | High noise, low signal — tests false-positive rate | Noise robustness |

Each pack ships with a corresponding `ground_truth_<scenario>.json` of planted entity IDs and pattern labels. Demo Mode automatically runs `scenario_04_mixed_activity` as the default showcase.

**Demo story:** "Here is the dataset → here is the planted behavior → here is what the system detected." This is substantially stronger than showing a generic pile of synthetic data.

### 5.4 GeoIP (Free, Offline-usable)
- **MaxMind GeoLite2** (City/Country/ASN `.mmdb` files) — the standard free option. Requires a free MaxMind account and a license key to download; once downloaded, the `.mmdb` files are queried **fully offline** with the `geoip2`/`maxminddb` Python library (or `mmdblookup` CLI). Attribution ("This product includes GeoLite2 data created by MaxMind") must be kept per their terms.
- Alternatives if you want to avoid the sign-up step: **DB-IP Lite** (free monthly-updated City/ASN databases, same `.mmdb` format) or **IP2Location LITE** (free CSV databases) — both offline-queryable and swappable with the same lookup code.
- Because your dataset is synthetic, you will typically generate IPs first, then run them through the offline GeoIP database to attach `geo_country`/`asn` — this exercises the exact "integrate an open-source downloadable GeoIP database" requirement in the problem statement.

### 5.5 Evaluation & Ground Truth

The system shall evaluate each detection module against the hidden ground-truth labels embedded in the scenario packs. Evaluation is run as a standalone script (`scripts/evaluate.py`) that prints results to the console — it is intentionally separate from the dashboard so ground-truth labels are never exposed to the analyst UI.

**Metrics required per detector:**

| Metric | Applicability |
|--------|---------------|
| Precision | All detectors |
| Recall | All detectors |
| F1-score | All detectors |
| False-positive rate | All detectors |
| ROC-AUC | Anomaly detection, risk scoring |
| Cluster quality (silhouette, NMI) | Entity clustering |

**Schema versioning:** each processed record shall carry `schema_version`, `record_id`, and `ingestion_batch_id` fields so that future schema changes do not silently break ingestion or model pipelines.

**Dataset lineage record (per ingested file):**
```
dataset_id       — UUID assigned at ingest time
filename         — original filename
sha256           — SHA-256 hash of the file
record_count     — total records in the file
schema_version   — schema version at ingest time
created_at       — ingest timestamp
```

**FR-15** (see §3) ensures evaluation is a first-class pipeline step, not an afterthought.

---

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | **Offline operation:** after an initial one-time setup (installing Python packages, downloading the GeoIP `.mmdb`), the pipeline must run with no internet access. The Docker Compose stack for analysis containers shall use `network_mode: none` (or an isolated internal Docker network with no host/internet egress) so that "offline" is demonstrably enforced, not merely stated. |
| NFR-2 | **Reproducible deployment (Docker-first):** Docker-based deployment is the **recommended default execution method**. A `docker-compose.yml` shall define `backend`, `frontend`, `postgres`, and `pipeline` services with health checks and dependency ordering (`postgres healthy → backend ready → frontend available`). Native Linux execution (via `requirements.txt`) remains supported as a fallback. The GeoIP `.mmdb` is **not** baked into the image; it is mounted as a read-only volume (`./data/geoip:/app/data/geoip:ro`) to keep licensing and reference-data handling clean. |
| NFR-3 | **Performance:** the reference pipeline should process on the order of 100k–1M synthetic transaction records within a few minutes to low tens of minutes on a standard laptop (tune graph-embedding batch sizes accordingly). |
| NFR-4 | **Explainability:** every alert must expose a human-readable reason, a `risk_score`, and a `confidence_score` — no unexplained black-box flags. |
| NFR-5 | **Auditability:** all stages log inputs/outputs/timings; every pipeline execution receives a `run_id` so that any alert can be traced back to its exact dataset, config version, and model version. |
| NFR-6 | **Modularity:** ingestion, graph-building, each ML/statistical module, scoring, and the dashboard should be independently runnable/testable components. |
| NFR-7 | **Data ethics:** the system must only ever be demonstrated against synthetic or already-public research datasets; it must not be pointed at real financial-surveillance data in this challenge context. |

---

## 6.1 Security Requirements

Because this project is explicitly under the **Blockchain & Cybersecurity** theme category, application-level security is a first-class requirement:

| ID | Requirement |
|----|-------------|
| SEC-1 | **No external network calls during analysis mode.** The pipeline and API shall not initiate outbound connections at run time. All reference data (GeoIP `.mmdb`, model files, config) must be pre-downloaded. |
| SEC-2 | **Secrets via environment/config only.** Database credentials, GeoIP license keys, and any API tokens shall be loaded from environment variables or a `.env` file (gitignored). They shall never be hardcoded in source code. |
| SEC-3 | **Uploaded files treated as untrusted input.** Ingestion shall validate file size (configurable max, e.g. 500 MB), MIME type/extension, and path (no directory traversal — resolve and confirm the file is within the designated `data/raw/` directory before opening). |
| SEC-4 | **XML parser hardened against XXE.** The XML parser (`lxml`) shall disable external entity resolution: `etree.XMLParser(resolve_entities=False, no_network=True)`. |
| SEC-5 | **API parameter validation.** All FastAPI route parameters (entity IDs, run IDs, alert IDs, dataset IDs) shall be validated as UUID or integer types; free-text query parameters shall be length-limited and sanitized. |
| SEC-6 | **Path traversal protection.** File ingestion endpoints shall reject any `..` or absolute-path components in supplied filenames. |

---

## 7. Suggested Technology Stack

| Layer | Tooling |
|---|---|
| Language | Python 3.11+ |
| Parsing/validation | `pandas`, `pydantic` v2, `lxml` (XML — XXE-hardened per SEC-4) |
| Graph storage/algorithms | `networkx` (prototype scale) or `igraph`/Neo4j Community Edition (larger scale, still self-hostable offline) |
| Graph embeddings | `node2vec`, `torch-geometric` (GraphSAGE) |
| Clustering | `scikit-learn` (DBSCAN), `hdbscan`, `python-louvain`/`leidenalg` |
| Anomaly detection | `scikit-learn` (IsolationForest), `PyOD`, or a small `PyTorch`/`Keras` autoencoder |
| Explainability | `shap` |
| Risk propagation | custom personalized-PageRank via `networkx.pagerank(personalization=...)` |
| GeoIP | `geoip2`/`maxminddb` reading a local GeoLite2/DB-IP `.mmdb` (mounted as volume, never baked into image) |
| **Application storage** | **PostgreSQL 15+** — system of record for records, entities, alerts, runs, evidence (managed via Alembic) |
| **Analytics engine** | **DuckDB** — optional columnar engine for fast ad-hoc queries on Parquet/CSV; complements, does not replace, PostgreSQL |
| Dashboard | `Streamlit` or `Dash` for the app shell; `pyvis`/`streamlit-agraph`/`Cytoscape.js` for the interactive link-analysis graph |
| Packaging | **Docker + Docker Compose (default/recommended)**; native Linux via `requirements.txt` as fallback |

---

## 8. Data Flow Summary

### 8.1 Pipeline Stages

```
INGEST  (parse CSV/JSON/XML, validate, quarantine malformed → data/quarantine/)
  ↓
ENRICH  (GeoIP lookup, dataset lineage record, SHA-256 hash)
  ↓
GRAPH   (build IP–Wallet–Transaction heterogeneous graph)
  ↓
FEATURES (extract per-transaction / per-wallet / per-graph features)
  ↓
DETECTION (entity clustering, anomaly detection, pattern detection, risk propagation)
  ↓
SCORING  (fuse risk_score + confidence_score + pattern flags → ranked alert list)
  ↓
EXPLAIN  (SHAP values, rule traces, subgraph provenance → persistent evidence objects)
  ↓
PERSIST  (write alerts + evidence + run metadata to PostgreSQL)
```

Every execution is assigned a `run_id` (UUID) at stage INGEST. All downstream records reference this `run_id`, enabling full traceability: **Dataset → Run → Model → Score → Alert → Evidence**.

### 8.2 Quarantine Store

Malformed, rejected, or schema-invalid records are written to `data/quarantine/` rather than silently dropped:

```
data/
├── raw/
├── quarantine/
│   ├── malformed/    ← type/format errors
│   └── rejected/     ← policy rejections (file size, path traversal, etc.)
└── processed/
```

Each quarantine record stores: `record`, `reason_code`, `validation_stage`, `timestamp`, `source_file`, `ingestion_batch_id`.

### 8.3 Health Check Endpoints

The FastAPI backend exposes:
- `GET /health` — liveness check (returns 200 if the process is running)
- `GET /ready` — readiness check (returns 200 only when PostgreSQL is reachable and migrations are applied)

Docker Compose health checks enforce startup ordering: **Postgres healthy → Backend ready → Frontend available**.

---

## 9. Deliverables Checklist (mapped to the challenge's expected deliverables)
- [ ] Offline, Linux-runnable code repository (ingestion → correlation → ML → scoring → dashboard).
- [ ] Working ML models for all four focus areas (not rule-only).
- [ ] Ranked, explainable alert list with confidence scores.
- [ ] Interactive dashboard / link-analysis visualization.
- [ ] Synthetic dataset + generation scripts + hidden ground-truth labels for self-evaluation.
- [ ] Short technical write-up covering approach, model choices, and the explainability method used.

---

## 10. Risks & Assumptions
- **Assumption:** the evaluators will supply or accept a synthetic dataset generated per Section 5.3; no real chain-surveillance data is used or required.
- **Risk:** the Common-Input-Ownership heuristic can be poisoned by CoinJoin-style transactions in the synthetic data — mitigated by the CoinJoin-detection step in Section 4.3 running *before* CIOH clustering.
- **Risk:** graph-embedding methods (Node2Vec/GraphSAGE) can be slow at large scale — mitigate by capping graph size for the prototype (e.g., ≤500k edges) and documenting how it would scale to a graph database for production.
- **Risk:** GeoIP free databases (GeoLite2/DB-IP/IP2Location LITE) have lower precision than paid tiers — acceptable for a prototype; document the limitation in the write-up.

---

## 11. References (for further reading during implementation)
- Elliptic Data Set (Kaggle): `kaggle.com/datasets/ellipticco/elliptic-data-set`
- BitcoinHeist Ransomware Address Dataset (UCI, ID 526): `archive.ics.uci.edu/dataset/526/bitcoinheistransomwareaddressdataset`
- MaxMind GeoLite2 (free, sign-up required): `dev.maxmind.com/geoip/geolite2-free-geolocation-data`
- DB-IP Lite (free alternative GeoIP): `db-ip.com/db/lite.php`
- IP2Location LITE (free alternative GeoIP): `lite.ip2location.com`
- `node2vec`, `PyTorch Geometric` (GraphSAGE), `hdbscan`, `PyOD`, `shap` — standard open-source Python packages, installable via `pip`.

## Recommendation: 
    Build the link-analysis view in-house with an open-source graph-visualization library (`pyvis` / `streamlit-agraph` in Python, or `Cytoscape.js` / `Sigma.js` if the frontend is JS-based). This gives full control over node sizing (balance/volume), edge styling (confidence), and click-through to evidence — the same visual idea Bubblemaps uses, but working with our own data end to end.

-------

## 3. Repository Structure

```
bit-logger/
├── README.md
├── docker-compose.yml                 # backend + frontend + postgres + pipeline services
│                                      # (with health checks and dependency ordering)
├── .env.example                       # DB creds, GeoIP path, config flags (never committed)
├── config/
│   └── pipeline_config.yaml           # all externalized thresholds/params (FR-13, FR-14)
├── pyproject.toml / requirements.txt
│
├── data/
│   ├── raw/                           # untouched input CSV/JSON/XML batches
│   ├── synthetic/
│   │   ├── scenario_01_normal_activity/
│   │   │   ├── transactions.csv
│   │   │   ├── network.csv
│   │   │   ├── ground_truth.json      # hidden labels — not exposed to UI
│   │   │   └── dataset_metadata.json  # filename, SHA-256, record_count, seeds, schema_version
│   │   ├── scenario_02_peeling_chain/
│   │   ├── scenario_03_coinjoin/
│   │   ├── scenario_04_mixed_activity/ ← default Demo Mode scenario
│   │   ├── scenario_05_high_anomaly/
│   │   ├── scenario_06_cross_ip_wallet_activity/
│   │   └── scenario_07_noise_heavy/
│   ├── geoip/                         # local GeoLite2 / DB-IP .mmdb files
│   │                                  # MOUNTED as volume: ./data/geoip:/app/data/geoip:ro
│   │                                  # NOT baked into Docker image (licensing)
│   ├── quarantine/
│   │   ├── malformed/                 # records failing type/format checks
│   │   └── rejected/                  # records failing policy checks
│   └── processed/                     # cleaned/enriched parquet files
│
├── db/
│   ├── postgres/
│   │   ├── init.sql                   # schema DDL
│   │   └── migrations/                # Alembic migration scripts
│   └── schema_diagram.png
│
├── backend/
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint + /health + /ready endpoints
│   │   ├── core/
│   │   │   ├── config.py              # env/config loader (no hardcoded secrets)
│   │   │   └── logging.py
│   │   ├── api/
│   │   │   ├── routes_ingest.py       # POST /ingest (file-size/path/MIME validation)
│   │   │   ├── routes_graph.py        # GET /graph/{entity_id}
│   │   │   ├── routes_alerts.py       # GET /alerts, GET /alerts/{id}/evidence
│   │   │   │                          # PATCH /alerts/{id}/state
│   │   │   ├── routes_dashboard.py    # summary/stat + pipeline status endpoints
│   │   │   └── routes_export.py       # GET /alerts/{id}/export?fmt=json|csv (FR-20)
│   │   ├── ingestion/
│   │   │   ├── parsers/
│   │   │   │   ├── csv_parser.py
│   │   │   │   ├── json_parser.py
│   │   │   │   └── xml_parser.py      # XXE-hardened: resolve_entities=False (SEC-4)
│   │   │   ├── validators.py          # schema/type/address-format checks; path-traversal guard
│   │   │   ├── geoip_enricher.py      # attaches geo_country / asn
│   │   │   └── lineage.py             # dataset_id, SHA-256, record_count, schema_version
│   │   ├── graph/
│   │   │   ├── builder.py             # builds IP–Wallet–Transaction graph
│   │   │   └── graph_store.py         # networkx/igraph in-memory graph + (de)serialization
│   │   ├── features/                  # feature engineering layer (between graph and ML)
│   │   │   ├── transaction_features.py
│   │   │   ├── wallet_features.py
│   │   │   ├── graph_features.py
│   │   │   └── feature_store.py       # assembles feature matrix for ML modules
│   │   ├── ml/
│   │   │   ├── clustering/
│   │   │   │   ├── cioh.py            # common-input-ownership heuristic
│   │   │   │   ├── embeddings.py      # node2vec / GraphSAGE
│   │   │   │   └── cluster.py         # HDBSCAN / Louvain on embeddings
│   │   │   ├── anomaly/
│   │   │   │   ├── isolation_forest.py
│   │   │   │   └── autoencoder.py
│   │   │   ├── pattern_detection/     # graph/statistical rule-based detectors
│   │   │   │   ├── peeling_chain.py
│   │   │   │   └── coinjoin_detector.py
│   │   │   └── risk_scoring/
│   │   │       └── propagation.py     # personalized PageRank / label propagation
│   │   ├── explainability/
│   │   │   ├── shap_explainer.py
│   │   │   ├── rule_trace.py
│   │   │   └── evidence_builder.py    # assembles persistent evidence object per alert
│   │   ├── scoring/
│   │   │   └── alert_ranker.py        # fuses cluster+anomaly+pattern+risk → risk_score + confidence_score
│   │   ├── evaluation/                # ground-truth evaluation (FR-15) — separate from UI
│   │   │   ├── metrics.py             # precision, recall, F1, ROC-AUC, FPR
│   │   │   └── evaluator.py           # loads ground_truth.json, runs per-detector evaluation
│   │   ├── models/                    # SQLAlchemy ORM models + Pydantic schemas
│   │   │   ├── orm.py                 # includes run_id, config_version, risk_score, confidence_score
│   │   │   └── schemas.py
│   │   └── db/
│   │       ├── session.py             # PostgreSQL engine/session via SQLAlchemy
│   │       └── repositories.py        # query layer used by API/ML modules
│   ├── synthetic_data_generator/
│   │   ├── generate_addresses.py
│   │   ├── generate_transaction_graph.py
│   │   ├── generate_network_layer.py  # synthetic IP/port/timing + GeoIP pass
│   │   ├── inject_patterns.py         # embeds peeling chains / CoinJoins per scenario
│   │   ├── scenario_builder.py        # generates all 7 named scenario packs with seeds
│   │   └── ground_truth.py            # writes hidden labels + dataset_metadata.json
│   └── tests/
│       ├── fixtures/                  # small test datasets for each scenario type
│       ├── test_ingestion.py
│       ├── test_graph_builder.py
│       ├── test_ml_modules.py
│       └── test_scoring.py
│
├── frontend/
│   ├── Dockerfile
│   └── streamlit_app/
│       ├── Home.py                    # overview/summary stats + pipeline status panel
│       ├── pages/
│       │   ├── 1_Graph_View.py        # interactive link-analysis graph (pyvis/streamlit-agraph)
│       │   ├── 2_Alerts.py            # sortable/filterable ranked alert table + lifecycle state
│       │   └── 3_Evidence.py          # per-alert evidence panel (subgraph + rule trace + SHAP)
│       └── components/
│           ├── graph_widget.py
│           ├── alert_card.py          # shows risk_score + confidence_score side-by-side
│           └── pipeline_status.py     # pipeline status checklist widget
│
├── notebooks/                         # EDA, model prototyping, threshold tuning (Dev Mode)
│
├── docs/
│   ├── SRS.md                         → ../SRS_PID_26146.md
│   ├── PROJECT_STRUCTURE_AND_STACK.md
│   ├── architecture_diagram.png
│   ├── technical_writeup.md           # approach, model choices, explainability method
│   └── Phases_&_Improvements.md      # Book A (Agent-to-Agent Notes) + Book B (where it will be create - int the logs ```.\docs\log_book.md``` here - as log_book.md)
│       ├── Book A — Agents to Agents Notes, Dev to Dev Notes - with Date and time stamp, when added or completed
│       └── Book B — Changes: added / removed / refined / any FRS data - in bullet points with Date and time stamp with a short summerised details, when added or completed. This will help any new developer to understand the changes made in the project.
│
└── scripts/
    ├── download_geoip.sh              # fetches GeoLite2/DB-IP .mmdb (one-time, needs internet)
    ├── generate_synthetic_data.sh     # generates all 7 scenario packs with seeds
    ├── run_pipeline.sh                # ingest → graph → features → ML → scoring → dashboard
    ├── run_demo.sh                    # Demo Mode: runs scenario_04_mixed_activity end-to-end
    └── evaluate.py                    # prints P/R/F1/FPR per detector vs ground truth (FR-15)
```

---

## 13. Future Work / Production Roadmap [Skipped in submission]

The following capabilities are explicitly scoped as **post-hackathon production work**. They are acknowledged here to demonstrate architectural awareness; they are intentionally not implemented in the prototype to avoid scope creep during the judging window.

| Item | Rationale for deferral |
|------|------------------------|
| **Model registry** (`model_registry.py`, `model_metadata.json`) | With ~4 small models, a formal registry solves a scale problem the prototype doesn't have. Add when models are versioned and retrained independently. |
| **Formal feature store** | A `features.py` module is sufficient at prototype scale. Full feature-store infrastructure (versioning, serving, monitoring) is a production concern. |
| **Schema versioning system** | Schema is fixed for the challenge duration. Version the schema when the ingestion contract evolves in production. |
| **Incremental/idempotent processing** (FR-18, FR-19 — lightweight only) | FR-18 (hash deduplication) is implemented. Full incremental graph patching is deferred — the demo runs once on a batch file. |
| **Full pipeline orchestration** (`orchestrator.py`, `stages.py`, `run_manager.py`) | `run_pipeline.sh` calling stages in sequence is sufficient. Full mini-Airflow orchestration adds complexity without judging benefit. |
| **Live pipeline status dashboard** | Implemented as a static post-run summary panel. Real-time streaming status requires WebSocket infrastructure deferred to production. |
| **Alert lifecycle analyst workflow** (multi-state, multi-analyst) | State field exists on the alert record; full multi-analyst assignment/escalation workflow is a product feature for a deployed SaaS platform. |
| **PDF export** (FR-20) | JSON and CSV export are implemented. PDF generation (via `reportlab`/`weasyprint`) is deferred as a polish item. |
| **Full data lineage graph** | `dataset_id` + `SHA-256` + `run_id` chain is implemented. A visual lineage graph UI (like OpenLineage/Marquez) is a production observability tool. |

---