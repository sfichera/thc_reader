#!/usr/bin/env python3
# thc_metadata.py
# Usage:
#   python thc_metadata.py <tokenId>
#   python thc_metadata.py <tokenId> --type blob
#   python thc_metadata.py <tokenId> --type json
#
# Default: prints ONLY JSON with traits (attributes)
# --type blob : prints ONLY a tokenURI-like string:
#               data:application/json;base64,<base64(json)>
#               WITHOUT calling tokenURI() (to avoid OOG), but calling buildSVG().
# --type json : prints ONLY the raw JSON metadata (NOT base64-wrapped).
#

import os
import sys
import json
import base64
import argparse
from typing import Any, Dict, List, Optional

from web3 import Web3

# =========================
# CONFIG
# =========================
RPC_URL = os.getenv("RPC_URL", "https://rpc.hyperliquid.xyz/evm")
CONTRACT_ADDRESS = os.getenv(
    "CONTRACT_ADDRESS",
    "0xCC3D60fF11a268606C6a57bD6Db74b4208f1D30c",
)

# Token supply bounds
MIN_TOKEN_ID = 1
MAX_TOKEN_ID = 2222

# Minimal ABI:
# - tokenTraits(uint256) -> (background, fur, eyes, hat, special)
# - buildSVG(uint256) -> string
ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "tokenTraits",
        "outputs": [
            {"internalType": "uint256", "name": "background", "type": "uint256"},
            {"internalType": "uint256", "name": "fur", "type": "uint256"},
            {"internalType": "uint256", "name": "eyes", "type": "uint256"},
            {"internalType": "uint256", "name": "hat", "type": "uint256"},
            {"internalType": "uint256", "name": "special", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "buildSVG",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# =========================
# TRAITS (CatData.sol)
# =========================
BACKGROUND_TRAITS = [
    "Trade", "Mint", "Dark", "Forest", "Coral", "Olive", "Sage", "Aqua"
]

FUR_TRAITS = [
    "Alien", "Brown", "Tiger", "Gold", "Gray", "Robot", "White", "Zombie"
]

EYE_TRAITS = [
    "None", "3D", "Blindfold", "Bonzi", "Borg", "Classic", "Closed", "Cool", "Crying",
    "Gold", "Googly", "Hearts", "Mask", "Nerd", "Noggles", "Patch", "Shades", "Shocked",
    "Ski", "Stoned", "Stylish", "Vipers", "VR", "Yeeti"
]

HAT_TRAITS = [
    "None", "Backcap", "Band", "Bandana", "Baseball", "Beanie", "Bow", "Crown", "Degen",
    "Doo", "Fez", "Flip", "Halo", "Heart", "Jeff", "Knit", "Liono", "Miner", "Mohawk",
    "Party", "Pilot", "Pirate", "Punk", "Rain", "Rekt", "Rooster", "Safari", "Santa",
    "Sombrero", "Sprout", "Tassle", "Wizard"
]

SPECIAL_TRAITS = [
    "None", "Bubble", "Cig", "Pipe", "Puke", "Vape"
]


# =========================
# Helpers
# =========================
def pick_trait(arr: List[str], idx: int) -> str:
    if idx < 0 or idx >= len(arr):
        return f"Unknown({idx})"
    return arr[idx]


def as_int(v: Any) -> int:
    try:
        return int(v)
    except Exception:
        return 0


def b64_str(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def build_attributes(token_id: int, traits_tuple: Any) -> List[Dict[str, str]]:
    background_i, fur_i, eyes_i, hat_i, special_i = map(as_int, traits_tuple)
    return [
        {"trait_type": "Background", "value": pick_trait(BACKGROUND_TRAITS, background_i)},
        {"trait_type": "Fur", "value": pick_trait(FUR_TRAITS, fur_i)},
        {"trait_type": "Eyes", "value": pick_trait(EYE_TRAITS, eyes_i)},
        {"trait_type": "Hat", "value": pick_trait(HAT_TRAITS, hat_i)},
        {"trait_type": "Special", "value": pick_trait(SPECIAL_TRAITS, special_i)},
    ]


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="thc_metadata.py",
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Tiny Hyper Cat metadata helper.\n"
            "Default output: traits JSON (no SVG / no base64 tokenURI wrapper).\n"
        ),
    )
    p.add_argument("tokenId", type=int, help="Token id (uint256)")
    p.add_argument(
        "--type",
        choices=["traits", "json", "blob"],
        default="traits",
        help=(
            "Output type:\n"
            "  traits - { tokenId, attributes }\n"
            "  json   - full JSON metadata (NOT base64-wrapped)\n"
            "  blob   - data:application/json;base64,<base64(json)>"
        ),
    )
    return p.parse_args(argv)


def ensure_stdout_newline(s: str) -> None:
    sys.stdout.write(s)
    if not s.endswith("\n"):
        sys.stdout.write("\n")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    token_id = args.tokenId

    # ✅ HARD VALIDATION: tokenId range
    if token_id < MIN_TOKEN_ID or token_id > MAX_TOKEN_ID:
        print(
            f"ERROR: tokenId out of range. Valid range is "
            f"{MIN_TOKEN_ID}–{MAX_TOKEN_ID}. Received: {token_id}",
            file=sys.stderr,
        )
        return 2

    if not Web3.is_address(CONTRACT_ADDRESS):
        print(
            "ERROR: Invalid CONTRACT_ADDRESS. Set env CONTRACT_ADDRESS or edit the script.",
            file=sys.stderr,
        )
        return 2

    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        print(f"ERROR: Could not connect to RPC: {RPC_URL}", file=sys.stderr)
        return 1

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=ABI,
    )

    # Read traits (cheap call)
    try:
        traits_tuple = contract.functions.tokenTraits(token_id).call()
    except Exception as e:
        print(f"ERROR: tokenTraits({token_id}) call failed: {e}", file=sys.stderr)
        return 1

    attributes = build_attributes(token_id, traits_tuple)

    # traits-only mode (default)
    if args.type == "traits":
        ensure_stdout_newline(json.dumps(
            {"tokenId": token_id, "attributes": attributes},
            indent=2,
            ensure_ascii=False
        ))
        return 0

    # For json/blob we need SVG
    try:
        svg = contract.functions.buildSVG(token_id).call()
    except Exception as e:
        print(f"ERROR: buildSVG({token_id}) call failed: {e}", file=sys.stderr)
        return 1

    base64_image = b64_str(svg)

    meta_obj: Dict[str, Any] = {
        "name": f"Tiny Hyper Cat #{token_id}",
        "description": "Tiny Hyper Cats live 100% onchain on Hyperliquid",
        "attributes": attributes,
        "image": f"data:image/svg+xml;base64,{base64_image}",
    }

    if args.type == "json":
        ensure_stdout_newline(json.dumps(meta_obj, indent=2, ensure_ascii=False))
        return 0

    # blob
    meta_json_str = json.dumps(meta_obj, ensure_ascii=False, separators=(",", ":"))
    base64_json = base64.b64encode(meta_json_str.encode("utf-8")).decode("ascii")
    ensure_stdout_newline(f"data:application/json;base64,{base64_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
