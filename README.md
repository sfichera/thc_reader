# Tiny Hyper Cat – Metadata Reader

Just a tiny THC metadata reader :-) -> Python script to generate **on-chain friendly** metadata for Tiny Hyper Cats using Web3.
It avoids expensive `tokenURI()` calls and builds metadata using `tokenTraits()` and `buildSVG()`.

Supported output types:
- **traits** (default): attributes only
- **json**: full metadata as raw JSON (no base64 encoding)
- **blob**: full metadata as `data:application/json;base64,...`

---

## Requirements

- Python **3.9+**
- Access to an EVM-compatible RPC (Hyperliquid by default)

---

## Dependencies
pip install web3

## Usage
python thc_metadata.py tokenId [--type traits|json|blob]

ie: python thc_metadata.py 157 --type json

