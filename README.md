# Test the API

A deployed instance is available at \
https://tunnel.tokahe.com

to get a wallets balance ( here binance ):\
https://tunnel.tokahe.com/balance/0x28C6c06298d514Db089934071355E5743bf21d60  \
to get a wallets 24h volume:\
https://tunnel.tokahe.com/volume/0x28C6c06298d514Db089934071355E5743bf21d60

# How to Run: 

## Install Dependencies
```pip3 install -r requirements.txt```

## Config
Edit infura_api_key and cache_path in app.py l11-l12

## Execute
```python3 app.py```

# Design:
The RESTful API is straightforward returning "code", "error", "error_description" fields and a data field on successfull requests

replace <custom_wallet_address> with any wallet_address

```/balance/<custom_wallet_address>```
returns a wallets balance of ETH, USDC and USDT

```/volume/<custom_wallet_address>```
returns a wallets volume of ETH, USDC and USDT, 
the volume is calculated by adding all outgoing and ingoing amounts together

Infura api is used

Volumes for wallets are summed up through block transactions and stored in a dict which is updated every x minutes ( 5min )
Blocks are cached via filesystem.
This approach returns results fast and saves api calls

Balances are retrieved easily via abi and pagination
    
## Possible Improvements

- Adding authentication ( bearer token, ... )
- Adding support for more tokens ( not just USDC, USDT )
- Adding Unit tests
- Make configurable via environment variables
