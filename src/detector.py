import time
import os
from web3 import Web3
from dotenv import load_dotenv
from containment import revoke_allowance, emergency_sweep

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
TOKEN_ADDRESS = os.getenv("TOKEN_CONTRACT_ADDRESS")
VICTIM_ADDRESS = os.getenv("VICTIM_WALLET_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Keccak-256 for Approval(address,address,uint256)
APPROVAL_TOPIC = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"

def listen_for_approvals(poll_interval: float = 0.5):
    print(f"[*] Monitoring Approval events on: {TOKEN_ADDRESS}")
    latest_block = w3.eth.block_number

    while True:
        current_block = w3.eth.block_number
        if current_block > latest_block:
            event_filter = {
                "fromBlock": latest_block + 1,
                "toBlock": current_block,
                "address": TOKEN_ADDRESS,
                "topics": [APPROVAL_TOPIC],
            }
            logs = w3.eth.get_logs(event_filter)
            for log in logs:
                owner = "0x" + log["topics"][1].hex()[-40:]
                spender = "0x" + log["topics"][2].hex()[-40:]
                value = int(log["data"].hex(), 16)

                if owner.lower() == VICTIM_ADDRESS.lower() and value > 0:
                    print(f"[!] Unauthorized approval detected: Spender={spender}, Value={value}")
                    print("[*] Initiating automated containment...")
                    
                    rev_tx = revoke_allowance(spender)
                    print(f"[+] Revocation TX dispatched: {rev_tx}")
                    
                    sweep_tx = emergency_sweep()
                    if sweep_tx:
                        print(f"[+] Assets swept to safety: {sweep_tx}")

            latest_block = current_block
        time.sleep(poll_interval)

if __name__ == "__main__":
    listen_for_approvals()
