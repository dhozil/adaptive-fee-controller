# Submission: Adaptive Fee Controller

## Category
Intelligent Contracts

## Contract Name
Adaptive Fee Controller

## Summary
A reusable GenLayer primitive for AI-powered dynamic fee adjustment. Uses LLM reasoning to analyze market conditions and recommend optimal fees within defined bounds, considering factors that rigid algorithms cannot capture.

## What Makes This Unique
- **Market-aware adjustments**: LLM analyzes volatility, volume, competition, and congestion holistically
- **Bounded safety**: Min/max bounds prevent extreme adjustments while allowing AI flexibility
- **Multiple fee types**: Supports fixed, percentage, and fully dynamic fee models
- **Performance analysis**: AI reviews fee effectiveness and suggests improvements
- **Reusable primitive**: Foundation for any protocol with dynamic pricing needs

## How Consensus Is Used
The contract uses `gl.vm.run_nondet_unsafe()` with a custom validator function. Each validator independently re-runs the LLM analysis on the same contract-fetched market data. Consensus is reached when validators agree on the exact fee value (no tolerance) and the exact analysis fields (`fee_effectiveness`, `volume_impact`, `optimal_fee_range`). This prevents conflicting analyses from passing.

**Field binding / trust boundary**: the fee-adjustment prompt only feeds contract-fetched market data plus stored integer state, and the validator binds the exact `new_fee`. The performance-analysis prompt is built **only from deterministic stored fields** (old/new/current fee, volume, fees collected) — the leader-written `adjustment_reason` and `market_summary` text remains visible via `get_profile_adjustments` but is excluded from every consequential prompt. Since GenVM eth_call cannot execute nondeterministic blocks, `analyze_fee_performance` runs as a write that stores its consensus-bound result, readable via the `get_last_analysis` view.

## Technical Details
- Python-based GenLayer Intelligent Contract
- Uses `gl.nondet.exec_prompt()` for LLM market analysis
- Custom validator ensures adjustment consistency
- TreeMap for scalable profile and adjustment storage
- Volume and fee collection tracking

## Use Case
DEX fees, lending rates, service pricing, gas optimization - any protocol where fees should adapt to real-time market conditions rather than remain static.

## Live Deployment
- **Address**: `0xa1CCfD57Ad6b0DB6513799cF215150D488ea5Cf3`
- **Network**: GenLayer studionet (chain `61999`)
- **Explorer**: https://explorer-studio.genlayer.com/address/0xa1CCfD57Ad6b0DB6513799cF215150D488ea5Cf3

## Source Code
See `contracts/adaptive_fee_controller.py`
