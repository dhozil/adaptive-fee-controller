<div align="center">

# Adaptive Fee Controller

**AI-driven fee curves — validators agree on the exact next fee (basis points) from live market conditions.**

![GenLayer](https://img.shields.io/badge/GenLayer-Intelligent%20Contract-6a4cff)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Status](https://img.shields.io/badge/status-live%20on%20studionet-2ea44f)
![Tests](https://img.shields.io/badge/tests-6%20passed-2ea44f)

[Live Contract](https://explorer-studio.genlayer.com/address/0x00425a326C32093Da6B10C243203a0B7512D739C) ·
[GenLayer Docs](https://docs.genlayer.com)

</div>

---

## Why

Static or formula-based fees can't adapt to volatility, liquidity or demand. This primitive puts fee governance on-chain: an **LLM analyzes the market** and GenLayer validators **agree on the exact next fee** — bounded by min/max and a max per-update step — so any protocol can run adaptive pricing without an oracle or a human.

## Live Deployment

| | |
|---|---|
| **Contract** | [AdaptiveFeeController](https://explorer-studio.genlayer.com/address/0x00425a326C32093Da6B10C243203a0B7512D739C) |
| **Address** | `0x00425a326C32093Da6B10C243203a0B7512D739C` |
| **Network** | GenLayer studionet (chain `61999`) |
| **Status** | ✅ deployed + audited on-chain |

## Highlights

- 📈 **Market-aware** — contract independently fetches market data from a public API URL (`gl.nondet.web.get`), not just owner-supplied text
- 🎚️ **Basis-point safety** — fees are integers (bp), bounded `[min, max]` and capped to a max step per update
- 🧮 **Exact consensus** — validators must agree on the EXACT fee value (zero tolerance), preserving current and future behavior
- 🔒 **Owner-only mutation** — creator can `adjust_fee`, `record_volume`, pause/resume
- 📚 **Full audit trail** — every adjustment stored with reason + fetched market data

## How It Works

```
create_fee_profile (owner: type, base/min/max bp, step)
      │
      ▼
adjust_fee(profile, market_data) ──► LLM analyzes market
      │
      ▼
    run_nondet_unsafe ──► validators recompute, must agree within tolerance
      │
      ▼
 new_fee clamped to [min, max] and |new - current| ≤ step ──► stored + recorded
```

## Methods

| Role | Method | Guard |
|---|---|---|
| Owner | `create_fee_profile`, `adjust_fee`, `record_volume`, `pause_profile`, `resume_profile` | owner-only |
| Any | `get_profile`, `get_current_fee`, `get_all_profiles`, `get_profile_adjustments`, `get_protocol_profiles`, `analyze_fee_performance` | read-only |

## Security Model

- All fee math in **integer basis points** (no float serialization on the GenVM/calldata layer)
- Validator re-runs the identical market analysis and enforces `[min,max]` + step bound on the leader's proposal
- Adjustments disabled while `paused`; pause/resume owner-only
- Append-only adjustment history; every mutation returns an ID

## Deploy

```bash
genlayer deploy --contract contracts/adaptive_fee_controller.py
```

## Test

```bash
pip install -r requirements.txt
pytest tests/
```