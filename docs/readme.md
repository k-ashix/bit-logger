# Bit-Logger — AI-Powered Bitcoin Transaction Forensics

**Problem Statement ID:** 26146 &nbsp;|&nbsp; **Organization:** National Technical Research Organisation (NTRO)  
**Theme:** Blockchain & Cybersecurity &nbsp;|&nbsp; **Category:** Software  
**Reference:** [Software Requirements Specification (SRS v1.0.0)](./SRS_PID_26146.md)

---

## 1. Bitcoin — Brief Background

Introduced in 2008 by the pseudonymous Satoshi Nakamoto and live since January 2009, **Bitcoin** is the world's first decentralized, peer-to-peer electronic cash system. It operates on a distributed proof-of-work blockchain — a public, immutable ledger — without any financial intermediary, enabling cryptographically secured value transfers across the globe.

---

## 2. What We Are Building

**Bit-Logger** is an offline investigative analytics pipeline and link-analysis dashboard built to detect illicit financial activity within Bitcoin transaction traffic.

The system fuses two distinct data layers:

- **Network layer** — IP addresses, ports, connection timing, and ASN/geolocation metadata.
- **Blockchain layer** — wallet addresses, transaction IDs (TXIDs), amounts, fee rates, and script types.

These are correlated into a heterogeneous graph and processed through four detection engines — entity clustering, unsupervised anomaly detection, peeling-chain / CoinJoin pattern recognition, and risk-score propagation — to produce ranked, explainable investigative leads for intelligence analysts.

---

## 3. Project Scope & Asset Focus

| Dimension | Detail |
|---|---|
| **Primary asset** | Bitcoin (BTC) exclusively — UTXO-based transaction graphs |
| **Live network (Mainnet)** | The production Bitcoin blockchain; real settled economic value |
| **Test networks** | Bitcoin Testnet / Regtest — identical consensus rules, zero real-world value |

> **Scope boundary:** This system does **not** connect to the live Bitcoin Mainnet, perform live packet capture, or attempt to de-anonymize real individuals. All ingestion and analytics operate strictly **offline** on **synthetic datasets** modeled on real Bitcoin P2P and transaction structures. Testnet / Regtest environments may be explored as future test generation tools.

---

## 4. Bitcoin Transaction Fees

Unlike account-based chains (e.g., Ethereum) that price computation as "gas," Bitcoin fees are determined purely by **transaction data size**, measured in virtual bytes (**vB**) and priced in **satoshis per virtual byte (sat/vB)**:

$$\text{Fee} = \text{Virtual Size (vB)} \times \text{Fee Rate (sat/vB)}$$

Key implications:

- Fee cost is **independent of BTC value transferred** — a 100 BTC transaction can be cheaper than a 0.001 BTC one if it has fewer inputs and simpler scripts.
- Higher fee rates give miners an incentive to prioritize transactions during mempool congestion.
- The **script type** directly governs transaction byte weight and therefore fee cost.

---

## 5. Bitcoin Address Standards & Script Formats

Addresses encode the cryptographic lock on an Unspent Transaction Output (UTXO), defining the conditions required to spend it.

**Example address:** `bc1qevjgchvqhhe2nshrgh6cx065rdk6ecyxvke6fe` *(Native SegWit / P2WPKH Bech32)*

### Script Type Comparison

#### 1. Legacy — P2PKH (Pay to Public Key Hash)
- **Prefix:** `1` (e.g., `1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2`)
- The original 2009 format. Signatures and public keys are embedded directly in the base transaction payload, producing the **largest byte weight** and therefore the **highest fees** of all formats. Largely deprecated in modern wallets.

#### 2. Native SegWit — P2WPKH (Pay to Witness Public Key Hash)
- **Prefix:** `bc1q` (e.g., `bc1qevjgchvqhhe2nshrgh6cx065rdk6ecyxvke6fe`)
- Introduced via BIP 141 / BIP 173 (Bech32 encoding). Separates ("segregates") the cryptographic witness (signature) from the base transaction data. Witness data receives a **75% weight discount**, reducing fees by roughly 30–40% vs. Legacy. Also resolves transaction malleability and adds built-in checksum validation. The most widely adopted standard today.

#### 3. Taproot — P2TR (Pay to Taproot)
- **Prefix:** `bc1p` (e.g., `bc1p5d7rjq7g6rd22...`)
- Activated November 2021 (BIP 340/341/342). Upgrades Bitcoin to **Schnorr signatures** and Merklized Alternative Script Trees (MAST). Multi-signature transactions, timelocks, and complex spending conditions appear on-chain **identical to simple single-key transfers**, delivering enhanced privacy, smaller transaction sizes for complex scripts, and lower fees.

---

## 6. End-to-End Data Flow

The platform operates as a deterministic, air-gapped investigative pipeline:

```
[ Local Input: CSV / JSON / XML ]
               |
               v
+---------------------------------------------+
|  Stage 1 - Ingestion & Validation           |
|  . Schema validation & path sanitization    |
|  . Quarantines malformed rows with codes    |
|  . Offline GeoIP enrichment (ASN, Country)  |
+-------------------+-------------------------+
                    |
                    v
+---------------------------------------------+
|  Stage 2 - Correlation & Graph Build        |
|  . Nodes: IP  .  Wallet  .  Transaction     |
|  . Edges: observed_in  .  input_to          |
|           output_of                         |
+-------------------+-------------------------+
                    |
                    v
+---------------------------------------------+
|  Stage 3 - Feature Extraction               |
|  . Per-wallet: fan-in/out, velocity, balance|
|  . Per-TX: fee rate, roundness, size        |
+-------------------+-------------------------+
                    |
                    v
+---------------------------------------------+
|  Stage 4 - AI/ML & Statistical Detection   |
|  . CIOH + Graph Embeddings  (Clustering)   |
|  . Isolation Forest / Autoencoder (Anomaly) |
|  . Peeling-Chain & CoinJoin Detectors       |
|  . Personalized PageRank   (Risk Spread)   |
+-------------------+-------------------------+
                    |
                    v
+---------------------------------------------+
|  Stage 5 - Scoring, Explainability & Alerts |
|  . Risk Score (0-100) & Confidence (0-100)  |
|  . SHAP values & rule-provenance subgraphs  |
|  . Exports: JSON / CSV evidence dossiers    |
+---------------------------------------------+
```

---

## 7. Design System & Theming

The UI is built exclusively on **CSS Custom Properties (Design Tokens)**. No component may use hardcoded hex values or inline color literals — every color reference must resolve to a token. This guarantees theme switching is instantaneous and regression-free: flipping `data-theme` on the document root is the only change needed to move between **Dark Mode** (default) and **Light Mode**.

### Color Token Rationale

The palette is anchored to Bitcoin's iconic orange-gold signature. In dark mode, cold neutral greys are deliberately avoided — they read as lifeless against the warm primary and create visual dissonance. Instead, background layers use deep blue-charcoal tones (which feel premium and intentional), and secondary text uses a warm amber-tinted tone that harmonizes with the brand orange rather than competing with it.

### Bitcoin-Inspired Color Palette

| Token | Dark Mode (Default) | Light Mode | Where & Why |
|---|---|---|---|
| `--color-btc-primary` | `#F7931A` · Bitcoin Orange | `#E07E0B` · Burnt Amber | Primary CTAs, active nav items, key accents — the brand anchor; darkened in light mode for sufficient contrast on white |
| `--color-btc-secondary` | `#FFAB40` · Warm Gold | `#D97706` · Deep Amber | Warning badges, secondary highlights, hover rings — lighter than primary to create clear visual hierarchy |
| `--color-bg-base` | `#0B0F1A` · Deep Navy-Black | `#F5F7FA` · Off-White | Full-page canvas — navy-black feels intentional vs. flat black; off-white avoids harsh pure white in light mode |
| `--color-bg-surface` | `#131929` · Midnight Blue | `#FFFFFF` · White | Cards, sidebars, modal panels — one shade lighter than base to create depth without relying on grey |
| `--color-bg-elevated` | `#1C2540` · Indigo-Charcoal | `#EDF0F5` · Cool Mist | Dropdown menus, table headers, hover states — clearly distinct from surface, warm-cool not cold-grey |
| `--color-border` | `rgba(247,147,26,0.18)` · Orange Glow | `rgba(15,23,42,0.10)` · Ink Whisper | Card edges, dividers — orange-tinted in dark mode ties borders to brand; near-invisible in light mode |
| `--color-text-primary` | `#EDF2FF` · Warm Lavender-White | `#0F172A` · Deep Ink | Body headings and primary text — slightly warm-tinted white avoids harshness of pure `#FFFFFF` on dark backgrounds |
| `--color-text-secondary` | `#A89478` · Warm Parchment | `#5A6680` · Slate | Labels, timestamps, metadata — warm parchment in dark mode pairs with the orange brand instead of clashing as cold grey |
| `--color-risk-critical` | `#FF4D4D` · Alert Red | `#DC2626` · Deep Red | High-risk score, illicit-seed flags — saturated red reads as danger immediately in both modes |
| `--color-risk-safe` | `#34D399` · Emerald | `#059669` · Deep Emerald | Low-risk, confirmed-benign status — emerald chosen over pure green for better readability at small sizes on dark surfaces |

> **Token-only rule:** All stylesheets must reference tokens (e.g., `color: var(--color-text-secondary)`) — never raw hex values. Adding a new color means adding a new token pair (dark + light), not an inline override.

Theme switching is handled via `data-theme="dark"` / `data-theme="light"` on the document root, toggled through the navbar control.

---

## 8. Frontend Layout & User Experience

### 8.1 Public Landing Page

```
+--------------------------------------------------+
|  B Bit-Logger  [Theme]  [Login]                  |
+--------------------------------------------------+
```

On first launch, the web client presents a Bitcoin-themed command-center overview:

1. **Hero Header**
   - Title: **Bit-Logger** — *Autonomous Bitcoin Traffic Forensics & Intelligence*
   - Badge: Smart India Hackathon (SIH) 2026 · NTRO Problem Statement ID `26146`

2. **Access Control**
   - A prominent **"Portal Login"** button in the hero and top navigation.
   - **No public registration** — self-service account creation is intentionally disallowed.
   - All investigator accounts are provisioned, managed, and revoked exclusively by the system administrator through an internal admin console.

3. **What is Bit-Logger? (2-4 lines)**
   An offline investigative framework that joins network-layer metadata with on-chain transaction records, enabling analysts to uncover obfuscated laundering structures — peeling chains, CoinJoin rings, cross-IP wallet clusters — without exposing live systems to the internet.

4. **How It Works — Interactive 4-Step Cards**

   | Step | Label | Description |
   |------|-------|-------------|
   | 📥 | **Load** | Upload CSV / JSON / XML batches or select from pre-bundled synthetic scenario packs |
   | 🕸️ | **Map Connections** | Link IP addresses, wallets, and transactions into a single relationship map — each entry tagged with its real-world location using an offline geo-database |
   | 🤖 | **Detect** | Run AI/ML anomaly detection alongside heuristic peeling and mixing rules |
   | 🔍 | **Investigate** | Inspect ranked leads, review SHAP explainability charts, and export evidence dossiers |

5. **Headline Metrics**

   | Metric | Value |
   |--------|-------|
   | Synthetic transactions indexed | **50 k+** |
   | Specialized detection engines | **4** (Clustering · Anomaly · Mixing · Risk Propagation) |
   | Operational standard | **100% air-gapped / offline** |
   | Avg. subgraph correlation latency | **< 1.2 s** |

6. **Attribution**
   Built for the **National Technical Research Organisation (NTRO)** under SIH 2026. Team credits, developer roles, and project version tag (`v1.0.0`) are displayed in the footer.

---

### 8.2 Analyst Workspace & Navigation

Once logged in, analysts land on a full-screen investigation workspace. A persistent top bar stays visible on every page and provides one-click access to all five sections:

```
+---------------------------------------------------------------------------------------------------------------------+
|  B Bit-Logger   [Dashboard]  [Link Graph]  [Alerts {consumed live from codebase}]  [Data]  [Theme]  [Logout]        |
+---------------------------------------------------------------------------------------------------------------------+
```

#### What Each Section Does

| # | Tab | What you see & do |
|---|-----|-------------------|
| 1 | **📊 Dashboard** | A live summary of everything the system has processed — how many wallets and transactions are loaded, how many were flagged, and whether the analysis pipeline has finished. A good starting point after uploading a dataset. |
| 2 | **🕸️ Link Graph** | A visual map of connections between IP addresses, wallets, and transactions. Color-coded by type (Blue = IP · Gold = Wallet · Purple = Transaction). Click any node to zoom in on its neighbors and see the full transaction trail. Filter by suspicion level or geographic region. |
| 3 | **🚨 Alerts** | The ranked list of suspicious wallets and transactions the system found. Each entry shows two scores: how suspicious it looks (**Risk Score**) and how certain the system is (**Confidence Score**). Analysts can mark each alert as Under Review, Confirmed, Dismissed, or Escalated. |
| 4 | **🔍 Evidence** | The detail view behind any alert. Shows exactly which transactions and wallet connections triggered the flag, a chart of the features that contributed most to the score, and a step-by-step trace of the money trail. Download the full report as JSON or CSV with one click. |
| 5 | **📂 Data** | Upload your own CSV, JSON, or XML files by dragging them in, or pick one of seven ready-made demo scenarios that ship with the system. Any records that failed validation appear here with a plain-English reason so you can fix or review them. |

---

## 9. Architecture & Documentation

For comprehensive engineering specifications, database schemas, and AI/ML model definitions, refer to:

- [SRS_PID_26146.md](./SRS_PID_26146.md) — Full System Requirements Specification (v1.0.0)
- [docs/technical_writeup.md](./docs/technical_writeup.md) — AI/ML Methodology & Explainability

---

## Subject To Change If needed (if changed must be loggeed here along with SRS)

   ## 10. Technology Stack

   | Layer | Tooling |
   |---|---|
   | **Language** | Python 3.11+ |
   | **Parsing & Validation** | `pandas`, `pydantic` v2, `lxml` (XML — XXE-hardened) |
   | **Graph Engine** | `networkx` / `igraph` in-memory; Apache AGE (openCypher) if graph queries are needed at scale |
   | **Graph Embeddings** | `node2vec`, `torch-geometric` (GraphSAGE) |
   | **Clustering** | `hdbscan`, `python-louvain` / `leidenalg`, `scikit-learn` (DBSCAN) |
   | **Anomaly Detection** | `scikit-learn` (Isolation Forest), `PyOD`, PyTorch / Keras Autoencoder |
   | **Explainability** | `shap` (TreeExplainer for Isolation Forest, KernelExplainer for Autoencoder) |
   | **Risk Propagation** | Personalized PageRank via `networkx.pagerank(personalization=...)` |
   | **GeoIP** | `geoip2` / `maxminddb` reading a local GeoLite2 or DB-IP `.mmdb` (mounted as volume, never baked into image) |
   | **Primary Storage** | PostgreSQL 15+ — system of record for records, entities, alerts, runs, evidence (Alembic migrations) |
   | **Analytics Engine** | DuckDB — optional columnar engine for fast ad-hoc queries on Parquet / CSV exports |
   | **API Backend** | FastAPI — `/health`, `/ready`, `/ingest`, `/graph`, `/alerts`, `/evidence`, `/export` |
   | **Frontend** | Streamlit app shell; PyVis / `streamlit-agraph` / Cytoscape.js for the link-analysis graph |
   | **Packaging** | Docker + Docker Compose (default); native Linux via `requirements.txt` as fallback |
   | **Configuration** | Versioned `config/pipeline_config.yaml` — all thresholds, params, and dataset paths externalized |

   ---

   ## 11. Deliverables Checklist

   Mapped directly to the NTRO Problem Statement (PS ID 26146) expected deliverables:

   - [ ] Offline, Linux-runnable code repository — ingestion → graph → ML → scoring → dashboard
   - [ ] Working AI/ML models for all four focus areas (not rule-only)
   - [ ] Ranked, explainable alert list with dual scoring (Risk Score + Confidence Score)
   - [ ] Interactive link-analysis dashboard and graph visualization
   - [ ] Synthetic dataset generation scripts + 7 named scenario packs + hidden ground-truth labels
   - [ ] Evaluation script reporting Precision / Recall / F1 / FPR per detector against ground truth
   - [ ] Short technical write-up covering approach, model choices, and explainability method used
   - [ ] Docker Compose stack (`docker compose --profile demo up`) for zero-setup judging demo

---

## 12. Local Verification & Forensic Test Runner (`test_helper_scripts`)

Bit-Logger includes an automated test, architectural modularity, and encoding verification suite located in [`test_helper_scripts/`](../test_helper_scripts).

### 📁 Test Run Logs & Forensic Artifacts

Every test run automatically organizes artifacts under a daily date folder `test_helper_scripts/logs/run_{YYYY_MM_DD}/` with a 12-hour clock run subfolder (no seconds, with AM/PM to prevent collisions):
```text
./test_helper_scripts/logs/run_{YYYY_MM_DD}/run_{HH_MM_AM/PM}/
├── master_run_{YYYYMMDD_HH_MM_AM/PM}.log   # Complete raw execution console output
├── master_run_{YYYYMMDD_HH_MM_AM/PM}.md    # Formatted Markdown report with metrics & failure snippets
├── dead_code_{YYYYMMDD_HH_MM_AM/PM}.log    # Raw dead code & unreachable logic scan log
└── dead_code_{YYYYMMDD_HH_MM_AM/PM}.md     # Formatted dead code audit report & code snippets
```

Multiple runs on the same day reuse the existing date folder `run_{YYYY_MM_DD}`, creating distinct timestamped subdirectories (`run_05_08_PM/`, `run_05_09_PM/`) to eliminate root noise and prevent collisions.

Whenever a test fails, the Markdown report automatically isolates:
- The exact **failing file** and **test function name**
- The **line number** where the failure occurred
- An annotated **source code context snippet** with the failing line marked with `>>`
- The complete cleaned **stack trace**

---

### 🚀 Execution Profiles & Parallelism

Bit-Logger supports pre-configured test profiles and **bounded parallel worker threads** (1 to 9 threads, default: 3):

| Profile | Command | What It Runs | Timeout Budget | Default Threads |
|---|---|---|---|---|
| **`full`** *(default)* | `python test_master.py --profile full` | All 4 static audits (LOC, Imports, Mojibake, Dead Code) + all test suites | 60s per suite | 3 workers |
| **`quick`** | `python test_master.py --profile quick` | LOC audit + Import audit + Fast tests | 15s per suite | 3 workers |
| **`audit`** | `python test_master.py --profile audit` | Static audits only (LOC, Imports, Mojibake, Dead Code) | N/A (no tests) | N/A |
| **`tests`** | `python test_master.py --profile tests` | Test runner execution only | 60s per suite | 3 workers |
| **`strict`** | `python test_master.py --profile strict` | Zero-tolerance: fails on any warning, dead code, or untested file | 60s per suite | 3 workers |

---

### 🛠️ CLI Usage, Threads & Customization

#### Why 2 Test Master Exist?

```text
When we run scripts in root terminal (.\SIH_2026\), having the root wrapper lets us run:
   python test_master.py --3 --all

instead of having to type the longer directory path:
   python test_helper_scripts/test_master.py --3 --all

Why it has Number / digits in the command (if you don't understand it, use default --3):
   It lets you set the number of parallel worker threads to run the tests in. 
   like --1 , --2 , --3 , --4 , --5 , --6 , --7 , --8 , --9 
```

```bash
# 1. Run full verification with default 3 parallel workers
python test_master.py --all
# Or with explicit thread shorthand (--1 to --9):
python test_master.py --3 --all

# 2. Maximum parallelism (9 worker threads)
python test_master.py --9 --all
# Or explicitly configure threads:
python test_master.py --workers 5 --all

# 3. Run fast smoke tests (15s timeout, 4 threads)
python test_master.py --4 --profile quick

# 4. Run individual audits
python test_master.py --audit-loc        # Check >100 LOC anti-god-file limit
python test_master.py --audit-imports    # Check stale/broken imports & coverage
python test_master.py --mojibake         # Check corrupted text encoding
python test_master.py --dead-code        # Check unreachable code & dead statements
python test_master.py --tests            # Run tests with default concurrency

# 5. Zero-tolerance strict mode (fails on warnings or untested modules)
python test_master.py --strict

# 6. Customize thresholds on demand
python test_master.py --timeout 30 --max-loc 100 --workers 6 --root .
```

