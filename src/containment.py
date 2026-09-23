import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
VICTIM_PRIVATE_KEY = os.getenv("VICTIM_PRIVATE_KEY")
TOKEN_ADDRESS = os.getenv("TOKEN_CONTRACT_ADDRESS")
SAFE_VAULT = os.getenv("SAFE_WALLET_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(VICTIM_PRIVATE_KEY) if VICTIM_PRIVATE_KEY else None

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]

token_contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=ERC20_ABI) if TOKEN_ADDRESS else None

def revoke_allowance(spender_address: str):
    """Sets allowance to 0 for a flagged malicious spender."""
    nonce = w3.eth.get_transaction_count(account.address)
    tx = token_contract.functions.approve(spender_address, 0).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 60000,
        "gasPrice": int(w3.eth.gas_price * 1.5),
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=VICTIM_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return w3.to_hex(tx_hash)

def emergency_sweep():
    """Transfers remaining token balance to a secure vault."""
    balance = token_contract.functions.balanceOf(account.address).call()
    if balance == 0:
        return None
    nonce = w3.eth.get_transaction_count(account.address)
    tx = token_contract.functions.transfer(SAFE_VAULT, balance).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 60000,
        "gasPrice": int(w3.eth.gas_price * 1.5),
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=VICTIM_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return w3.to_hex(tx_hash)
