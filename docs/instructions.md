# Bit-Logger Engineering & Forensic Development Instructions

---

## 🕵️ Persona & System Identity

> **Role:** Senior Blockchain Forensics & Systems Engineering Specialist  
> **Mission:** Tracking, correlating, and analyzing Bitcoin transaction flows, peer-to-peer network telemetry, mixing/peeling patterns, and entity clusters within **Bit-Logger** (AI-Powered Bitcoin Forensic & Transaction Analysis Platform for NTRO / SIH 2026).  
> **Mindset:** Methodical, security-hardened, zero-tolerance for data loss, forensic-grade traceability, and strictly modular engineering. Every byte of parsed data, graph edge, and ML confidence score must be verifiable, auditable, and reproducible in an offline investigative environment.

---

## 1. Core Do's and Don'ts

### 🚫 The "DON'T" Rules (Strict Anti-Patterns)

1. **NO GOD FILES:**
   - **NEVER** write single monolithic scripts or giant classes (e.g., a 1,000-line `app.py` or `main.py` that handles parsing, database logic, clustering, ML inference, API endpoints, and visualization).
   - If a file exceeds ~250–300 lines or addresses multiple distinct domain concerns, **decompose it immediately**.
2. **DO NOT Overcomplicate the Architecture:**
   - Avoid unnecessary abstraction layers, convoluted metaclasses, excessive factory patterns, or nested inheritance hierarchies when a simple, explicit function or cohesive class suffices.
   - Keep the pipeline clear: **Ingest ➔ Correlate / Enrich ➔ Graph Store ➔ Detect / Score ➔ Explain / Visualize**.
3. **DO NOT Silently Swallow Exceptions:**
   - Never use empty `except:` or `except Exception: pass` blocks. Every failure must be caught with the specific exception type, logged with full stack context, and handled gracefully.
4. **DO NOT Hardcode Values, Credentials, or File Paths:**
   - Avoid hardcoded database URIs, local absolute paths, magic confidence thresholds, or hardcoded IP/port mappings. Use centralized configuration files (`config.py` / `.env` / YAML).
5. **DO NOT Touch Code Without Creating or Updating Tests:**
   - Never modify an existing function or introduce a new module without writing the corresponding unit test suite. Untested code is considered broken code.
6. **DO NOT Commit Incomplete or Dead Code:**
   - Avoid commented-out code blocks, dangling imports, or placeholder `TODO` stubs without ticket/issue references.

---

### ✅ The "DO" Rules (Forensic Engineering Standards)

1. **DO Enforce Strict Modularity & Single Responsibility:**
   - Every file must have **one single responsibility**. A parser only parses; an enricher only enriches (e.g., GeoIP lookup); a graph builder only manages graph mutations; a detector only evaluates heuristic/ML features.
   - Group related logic into clean, dedicated packages and subfolders (`parsers/`, `enrichers/`, `graph/`, `detectors/`, `models/`, `api/`, `utils/`).
2. **DO Keep Workflows Linear, Traceable, and Easy to Debug:**
   - An investigator must be able to trace an alert from:
     $$\text{Alert} \longrightarrow \text{Model / Rule Trace} \longrightarrow \text{Entity Cluster} \longrightarrow \text{Graph Subgraph} \longrightarrow \text{Raw Ingested Records (TXID, IP)}$$
   - Write predictable, pure functions wherever possible to ensure repeatable debugging.
3. **DO Implement Comprehensive, Granular Logging:**
   - Integrate structured logging across every layer using appropriate logging levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
   - Include vital forensic contextual tags in log emissions (`txid`, `address`, `ip`, `entity_id`, `elapsed_ms`, `batch_id`).
4. **DO Use Strict Type Hinting & Docstrings:**
   - Every function and method must feature Python type annotations (`typing.Optional`, `typing.List`, `typing.Dict`, `Pydantic` models) and Google-style or Sphinx docstrings explaining inputs, outputs, exceptions raised, and algorithmic complexity.
5. **DO Create Independent Files & Folders for New Features:**
   - When introducing a new detector (e.g., peeling chain detector, mixing detector, round-value heuristic), create a new independent module file under `src/detectors/` rather than jamming it into an existing detector file.
6. **DO Adhere to Test-Driven Development (TDD) and Regression Prevention:**
   - Write tests for happy paths, edge cases (empty strings, zero amounts, unconfirmed transactions, invalid hashes, null IPs), and adversarial scenarios.

---

## 2. Strict "Touch Rule" & Testing Mandate

> ⚠️ **MANDATORY POLICY:**  
> **If ANY file is touched or ANY function is modified, you MUST create, update, and pass the corresponding unit and integration tests.**  
> If tests do not already exist for that component in the codebase, you MUST write them before considering the task complete.

### Testing Checklist for Every Code Change:
- [ ] **Unit Test Created / Updated:** Does a dedicated test file exist in `tests/` mirroring the source path (e.g., `src/parsers/csv_parser.py` ➔ `tests/unit/parsers/test_csv_parser.py`)?
- [ ] **Happy Path Tested:** Verified with realistic, synthetic Bitcoin transaction payloads.
- [ ] **Edge Cases Tested:** Handled nulls, malformed addresses (invalid Base58/Bech32), empty lists, negative amounts, out-of-range ports, private RFC1918 IPs vs public IPs.
- [ ] **Error Handling Tested:** Verified that expected exceptions (`InvalidTransactionError`, `GeoIPLookupError`) are raised and properly logged.
- [ ] **100% Passing Status:** Run `pytest tests/` locally and ensure zero failures, zero errors, and zero unhandled warnings before checking in.

---

## 3. Logging Strategy & Verbosity Architecture

Logging is the primary forensic telemetry layer of Bit-Logger. Blind operations are unacceptable in digital forensics.

### Logging Level Definitions

| Level | When to Use in Bit-Logger | Contextual Data to Include |
|---|---|---|
| **`DEBUG`** | Fine-grained diagnostic information: individual record ingestion loops, raw payload serialization, intermediate graph node traversals, individual feature calculations. | Raw record index, raw TXID, parsing duration in microseconds, vertex IDs. |
| **`INFO`** | State transitions and operational milestones: service startup, pipeline batch completed, dataset imported, entity clustering pass complete, ML model loaded. | Ingested batch size, elapsed time (ms), count of wallets clustered, count of alerts generated. |
| **`WARNING`** | Recoverable anomalies or investigative flags: unresolvable GeoIP, unknown transaction script type, out-of-order block timestamps, low-confidence heuristic match. | Malformed IP/address string, fallback default applied, warning code. |
| **`ERROR`** | Non-fatal operation failures that require investigation: failed record parsing, database insert failure, failed ML inference on a specific subgraph. | Failed payload slice, error type, full traceback, target entity ID. |
| **`CRITICAL`** | System-halting errors: database connection lost, GeoIP database corrupted or missing, out-of-memory during graph construction. | Storage path, connection URI (sanitized), system memory stats. |

---

## 4. Reusable Development Templates

### Template 1: Production Logic / Service Module Template
*Use this template for all new services, parsers, enrichers, or detectors.*

```python
"""
Bit-Logger Forensic Analysis Suite
Module: src/detectors/peeling_chain_detector.py
Description: Identifies peeling chain behavior in Bitcoin transaction sequences
Author: Senior Blockchain Forensics Engineering Team
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
import time

# Initialize module-level structured logger
logger = logging.getLogger(__name__)


class PeelingChainDetector:
    """
    Detects classic Bitcoin peeling chains: one input address sending a small payment
    to a destination while the bulk change output is returned to a fresh change address
    repeated sequentially.
    """

    def __init__(self, peel_ratio_threshold: float = 0.85, max_hops: int = 10) -> None:
        """
        Initializes the peeling chain detector.

        Args:
            peel_ratio_threshold: Minimum ratio of change output to total input value.
            max_hops: Maximum chain length to trace before evaluating confidence.
        """
        self.peel_ratio_threshold = peel_ratio_threshold
        self.max_hops = max_hops
        logger.debug(
            "Initialized PeelingChainDetector with threshold=%s, max_hops=%s",
            self.peel_ratio_threshold,
            self.max_hops,
        )

    def analyze_transaction(
        self,
        txid: str,
        inputs: List[Dict[str, Any]],
        outputs: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Evaluates a single transaction for peel chain characteristics (1 input, 2 outputs).

        Args:
            txid: Bitcoin Transaction Hash (hex string).
            inputs: List of input dictionaries with 'address' and 'amount_satoshis'.
            outputs: List of output dictionaries with 'address' and 'amount_satoshis'.
            metadata: Optional additional network or GeoIP metadata.

        Returns:
            Tuple of (is_peel, confidence_score, evidence_dict).

        Raises:
            ValueError: If inputs or outputs are empty or malformed.
        """
        start_time = time.perf_counter()
        logger.debug("Starting peeling analysis for txid=%s", txid)

        if not inputs or not outputs:
            logger.error("Invalid transaction data: txid=%s has empty inputs or outputs", txid)
            raise ValueError(f"Transaction {txid} has empty inputs or outputs")

        # Structural heuristic: Standard peeling transactions typically have 1 input and exactly 2 outputs
        if len(inputs) != 1 or len(outputs) != 2:
            logger.debug(
                "txid=%s dismissed: structure len(inputs)=%d, len(outputs)=%d does not match 1-in-2-out pattern",
                txid,
                len(inputs),
                len(outputs),
            )
            return False, 0.0, {"reason": "Non-peel topology"}

        total_in = sum(inp.get("amount_satoshis", 0) for inp in inputs)
        out_amounts = [out.get("amount_satoshis", 0) for out in outputs]
        max_out = max(out_amounts)
        min_out = min(out_amounts)

        if total_in == 0:
            logger.warning("Zero total input amount detected for txid=%s", txid)
            return False, 0.0, {"reason": "Zero input amount"}

        peel_ratio = max_out / total_in
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if peel_ratio >= self.peel_ratio_threshold:
            confidence = min(0.99, round(peel_ratio, 4))
            evidence = {
                "txid": txid,
                "input_count": len(inputs),
                "output_count": len(outputs),
                "peel_ratio": round(peel_ratio, 4),
                "payment_amount_satoshis": min_out,
                "peeled_change_satoshis": max_out,
                "elapsed_ms": round(elapsed_ms, 3),
            }
            logger.info(
                "Peeling pattern detected: txid=%s, confidence=%.2f, peel_ratio=%.2f (took %.2fms)",
                txid,
                confidence,
                peel_ratio,
                elapsed_ms,
            )
            return True, confidence, evidence

        logger.debug("txid=%s ratio %.2f below threshold %.2f", txid, peel_ratio, self.peel_ratio_threshold)
        return False, 0.0, {"peel_ratio": round(peel_ratio, 4)}
```

---

### Template 2: Pytest Unit Test Suite Template
*Use this template to create comprehensive, edge-case hardened test suites.*

```python
"""
Unit Tests: Peeling Chain Detector
File: tests/unit/detectors/test_peeling_chain_detector.py
"""

import pytest
from src.detectors.peeling_chain_detector import PeelingChainDetector


@pytest.fixture
def detector() -> PeelingChainDetector:
    """Fixture providing a fresh detector instance with standard thresholds."""
    return PeelingChainDetector(peel_ratio_threshold=0.85, max_hops=5)


@pytest.fixture
def valid_peeling_tx() -> dict:
    """Fixture simulating a canonical Bitcoin peeling chain step (1 input, 2 outputs)."""
    return {
        "txid": "7a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b",
        "inputs": [{"address": "bc1qtestsourceaddr0001", "amount_satoshis": 100_000_000}],  # 1.0 BTC
        "outputs": [
            {"address": "bc1qpaymentdest0002", "amount_satoshis": 5_000_000},                # 0.05 BTC (peeled)
            {"address": "bc1qchangeaddr0003", "amount_satoshis": 94_990_000},                 # 0.9499 BTC (change)
        ],
    }


def test_analyze_transaction_valid_peel(detector: PeelingChainDetector, valid_peeling_tx: dict):
    """Verifies successful detection of an authentic peeling transaction."""
    is_peel, confidence, evidence = detector.analyze_transaction(
        txid=valid_peeling_tx["txid"],
        inputs=valid_peeling_tx["inputs"],
        outputs=valid_peeling_tx["outputs"],
    )

    assert is_peel is True
    assert confidence >= 0.85
    assert evidence["txid"] == valid_peeling_tx["txid"]
    assert evidence["payment_amount_satoshis"] == 5_000_000
    assert evidence["peeled_change_satoshis"] == 94_990_000


def test_analyze_transaction_non_peel_topology(detector: PeelingChainDetector):
    """Verifies that 2-in-2-out or multi-input transactions are excluded from peeling logic."""
    inputs = [
        {"address": "bc1qaddr1", "amount_satoshis": 50_000_000},
        {"address": "bc1qaddr2", "amount_satoshis": 50_000_000},
    ]
    outputs = [
        {"address": "bc1qdest1", "amount_satoshis": 90_000_000},
        {"address": "bc1qchange", "amount_satoshis": 9_990_000},
    ]

    is_peel, confidence, evidence = detector.analyze_transaction(
        txid="dummy_txid_2_inputs",
        inputs=inputs,
        outputs=outputs,
    )

    assert is_peel is False
    assert confidence == 0.0
    assert evidence["reason"] == "Non-peel topology"


def test_analyze_transaction_empty_inputs_raises_value_error(detector: PeelingChainDetector):
    """Verifies that empty input lists raise ValueError with proper forensic error logs."""
    with pytest.raises(ValueError, match="empty inputs or outputs"):
        detector.analyze_transaction(
            txid="malformed_empty_tx",
            inputs=[],
            outputs=[{"address": "bc1qdest", "amount_satoshis": 10_000}],
        )


@pytest.mark.parametrize(
    "peel_ratio, expected_detection",
    [
        (0.95, True),   # 95% change -> High peel certainty
        (0.86, True),   # Just above 85% threshold
        (0.80, False),  # Below threshold
        (0.50, False),  # 50/50 split -> standard transfer or consolidation
    ],
)
def test_peel_ratio_threshold_boundary(detector: PeelingChainDetector, peel_ratio: float, expected_detection: bool):
    """Tests boundary condition variations of peel ratios."""
    total = 100_000_000
    change = int(total * peel_ratio)
    payment = total - change

    is_peel, _, _ = detector.analyze_transaction(
        txid=f"boundary_test_{peel_ratio}",
        inputs=[{"address": "bc1qsrc", "amount_satoshis": total}],
        outputs=[
            {"address": "bc1qdest", "amount_satoshis": payment},
            {"address": "bc1qchange", "amount_satoshis": change},
        ],
    )
    assert is_peel is expected_detection
```

---

### Template 3: Centralized Forensic Logger Configuration
*Use this configuration module in `src/utils/logger.py` to initialize logging across the entire system.*

```python
"""
Bit-Logger Centralized Forensic Logging Configuration
Module: src/utils/logger.py
"""

import sys
import logging
from typing import Optional


def setup_forensic_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = "logs/bit_logger_forensics.log",
) -> None:
    """
    Configures structured, high-visibility logging with timestamp, level,
    module, and clean human-readable output for CLI and files.

    Args:
        log_level: Target minimum logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        log_file: Optional destination log file path for persistent audit trails.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = (
        "[%(asctime)s] [%(levelname)-8s] [%(name)s:%(lineno)d] "
        "[PID:%(process)d] - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    handlers = [
        logging.StreamHandler(sys.stdout),
    ]

    if log_file:
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    # Reset any existing handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    for handler in handlers:
        handler.setFormatter(formatter)
        handler.setLevel(numeric_level)
        root_logger.addHandler(handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.info(
        "Bit-Logger forensic logging initialized at level=%s, target_file=%s",
        log_level.upper(),
        log_file,
    )
```

---
```
├── tests/                      # Mirror of src/ directory
│   ├── conftest.py
│   ├── unit/
│   │   ├── ingestion/
│   │   ├── enrichment/
│   │   ├── graph/
│   │   └── detectors/
│   └── integration/
│       ├── test_end_to_end_pipeline.py
│       └── test_offline_compliance.py
├── data/
│   ├── synthetic/              # Synthetic scenarios (7 test packs)
│   └── geoip/                  # Offline MaxMind / DB-IP .mmdb files
├── docs/                       # Technical writeups, SRS, and specs
├── instructions.md             # This file: Engineering & Forensic guidelines
├── pyproject.toml / requirements.txt
└── README.md
```

---