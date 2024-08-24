# 
# Module holds web3 code to get balances and volumes
#
from web3 import Web3
import math
import pickle
import os
from pathlib import Path

# USDC contract address on Ethereum mainnet
tokens = {
    "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
}

def InfuraWeb3(api_key):
    infura_url = "https://mainnet.infura.io/v3/" + api_key
    return Web3(Web3.HTTPProvider(infura_url))

class Block:
    def __init__(self, block_nr, events):
        self.block_nr = block_nr
        self.events = events

    def __repr__(self):
        return str(self.block_nr)

    def save(self, cache_dir):
        path = os.path.join(cache_dir, str(self.block_nr))
        with open(path, 'wb') as f:
            pickle.dump(self, f)

def init():
    for token_name, token_address in tokens.items():
        tokens[token_name] = Web3.to_checksum_address(token_address.lower())

def get_balance(api_key, wallet_address, req_tokens):
    wallet_address = Web3.to_checksum_address(wallet_address)

    # Connect to the Ethereum node
    web3 = InfuraWeb3(api_key)

    # USDC contract ABI (Application Binary Interface)
    balance_abi = [
        {
            "constant": True,
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        }
    ]

    token_balances = {}
    response_index = 0
    if "ETH" in req_tokens:
        token_balances["ETH"] = web3.eth.get_balance(wallet_address) / 10**18

    with web3.batch_requests() as batch:
        for req_token in req_tokens:
            if req_token != "ETH":
                token_address = tokens[req_token]
                token_contract = web3.eth.contract(address=token_address, abi=balance_abi)
                batch.add(token_contract.functions.balanceOf(wallet_address))
                token_balances[req_token] = response_index
                response_index+=1

        responses = batch.execute()
        for key in token_balances.keys():
            if key != "ETH":
                token_balances[key] = responses[token_balances[key]] / 10**6
        
    return token_balances

def get_token_volume(cache_dir, token_id):
    '''
    Gets entire volume of all cached blocks
    '''
    full_cache_dir = os.path.join(cache_dir, token_id)
    volumes = {}
    for path in os.listdir(full_cache_dir):
        if not os.path.isfile(os.path.join(full_cache_dir, path)):
            continue

        filepath = os.path.join(full_cache_dir, path)
        block = None
        with open(filepath, 'rb') as f:
            block = pickle.load(f)
            
        for event in block.events:
            fro = str(event["from"]).lower()
            to = str(event["to"]).lower()
            if fro not in volumes: volumes[fro] = 0
            if to not in volumes: volumes[to] = 0

            volumes[fro] += event["value"]
            volumes[to] += event["value"]

    dividend = 1
    if token_id == "ETH": 
        dividend = 10**18
    else:
        dividend = 10**6

    for key in volumes.keys():
        volumes[key] = volumes[key] / dividend 

    return volumes

def get_volume(cache_dir, tokens):
    volumes = {}
    for token in tokens:
        volumes[token] = get_token_volume(cache_dir, token)
    return volumes

def download_blocks(cache_dir, api_key, token_id):
    if token_id == "ETH":
        return download_blocks_eth(cache_dir, api_key)

    full_cache_dir = os.path.join(cache_dir, token_id)
    web3 = InfuraWeb3(api_key)

    # USDC contract address and ABI (with Transfer event definition)
    usdc_abi = [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"},
            ],
            "name": "Transfer",
            "type": "event",
        }
    ]

    # Create a contract instance
    usdc_contract = web3.eth.contract(address=tokens[token_id], abi=usdc_abi)

    from_block, to_block = blocks_to_download(web3, full_cache_dir) 
    remove_old_blocks(web3, full_cache_dir)


    # Fetch Transfer events from the last 24 hours
    events = []

    pagesize = 100
    print("new blocks to donwload",to_block - from_block)
    for i in range(math.ceil((to_block - from_block)/pagesize)):
        blocks = {}
        start = from_block+pagesize*i
        end = from_block+pagesize*(i+1)

        if end > to_block:
            end = to_block

        transfer_event = usdc_contract.events.Transfer()
        for event in transfer_event.get_logs(from_block=start, to_block=end):
            blockNumber = event["blockNumber"]
            if blockNumber not in blocks.keys():
               blocks[blockNumber] = Block(blockNumber, [])

            event_dict = {"from": event["args"]["from"], "to": event["args"]["to"], "value": event["args"]["value"]}
            blocks[blockNumber].events.append(event_dict)

        for _, block in blocks.items():
            Path(full_cache_dir).mkdir(parents=True, exist_ok=True)
            block.save(full_cache_dir)

def download_blocks_eth(cache_dir, api_key):
    full_cache_dir = os.path.join(cache_dir, "ETH")

    web3 = InfuraWeb3(api_key)

    from_block, to_block = blocks_to_download(web3, full_cache_dir)
    remove_old_blocks(web3, full_cache_dir)

    print("new blocks to donwload",to_block - from_block)
    for	i in range(from_block, to_block):
        blockData = web3.eth.get_block(i, full_transactions=True)

        block = Block(i, [])

        for tx in blockData.transactions:
            event_dict = {"from": tx["from"], "to": tx["to"], "value": tx["value"]}
            block.events.append(event_dict)

        block.save(full_cache_dir)

## HELPER FUNCS ##
def blocks_to_download(web3, cache_dir):
    latest_block = web3.eth.block_number
    to_block = latest_block
    blocks_per_day = int((24 * 60 * 60) / 13.5)
    from_block = to_block - blocks_per_day

    highest = 0
    for path in os.listdir(cache_dir):
        fullpath = os.path.join(cache_dir, path)
        if os.path.isfile(fullpath):
            if int(path) > highest:
                highest = int(path)

    if highest > from_block:
        from_block = highest

    return from_block, to_block

def remove_old_blocks(web3, cache_dir):
    latest_block = web3.eth.block_number
    to_block = latest_block
    blocks_per_day = int((24 * 60 * 60) / 13.5)
    from_block = to_block - blocks_per_day

    for path in os.listdir(cache_dir):
        fullpath = os.path.join(cache_dir, path)
        remove_block = os.path.isfile(fullpath) and int(path) < from_block
        if remove_block:
            os.remove(fullpath)
