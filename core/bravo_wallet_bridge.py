"""BravoWalletBridge - Unified wallet access with reserve and logging."""

import time
from dataclasses import dataclass, field
from typing import List, Dict

from solana.rpc.api import Client


@dataclass
class LedgerEntry:
    module: str
    amount: float
    action: str
    timestamp: float = field(default_factory=time.time)


class BravoWalletBridge:
    """Provides real-time wallet balance and immutable usage log."""

    def __init__(self, rpc_url: str, wallet_address: str):
        self.rpc_url = rpc_url
        self.wallet_address = wallet_address
        self.client = Client(rpc_url)
        self.reserve_amount = 0.0
        self.ledger: List[LedgerEntry] = []

    def get_balance(self) -> float:
        resp = self.client.get_balance(self.wallet_address)
        lamports = resp.get("result", {}).get("value", 0)
        return lamports / 1_000_000_000

    def reserve(self, amount: float) -> None:
        self.reserve_amount = max(self.reserve_amount, amount)

    def log_usage(self, module: str, amount: float, action: str) -> None:
        self.ledger.append(LedgerEntry(module, amount, action))

    def snapshot(self) -> Dict:
        return {
            "balance": self.get_balance(),
            "reserve": self.reserve_amount,
            "ledger_size": len(self.ledger),
        }
