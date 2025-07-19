"""AlphaMainnetLock - Ensures real Solana mainnet connectivity."""

from solana.rpc.api import Client


class AlphaMainnetLock:
    """Verify mainnet RPC connection and wallet funding."""

    def __init__(self, rpc_url: str, wallet_address: str, min_balance: float = 0.05):
        self.rpc_url = rpc_url
        self.wallet_address = wallet_address
        self.min_balance = min_balance
        self.client = Client(rpc_url)

    def verify(self) -> None:
        """Raise RuntimeError if mainnet connection or balance check fails."""
        try:
            # fetch a recent slot as heartbeat
            self.client.get_slot(commitment="confirmed")
        except Exception as exc:
            raise RuntimeError("RPC connection failed") from exc

        balance_resp = self.client.get_balance(self.wallet_address)
        if not balance_resp or "result" not in balance_resp:
            raise RuntimeError("Balance query failed")

        lamports = balance_resp["result"]["value"]
        sol_balance = lamports / 1_000_000_000
        if sol_balance < self.min_balance:
            raise RuntimeError("Insufficient SOL balance for lock")
