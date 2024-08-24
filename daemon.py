from crypto import init, download_blocks_eth, download_blocks, get_balance, get_volume
import time
from datetime import datetime

# Downloads blocks required to calculate wallet volume
def block_download_daemon(download_dir, infura_api_key):
    tokens = ["ETH", "USDC", "USDT"]

    prev_time = datetime(1, 1, 1, 0, 0)
    while True:
        current_time = datetime.now() 
        elapsed_time = current_time - prev_time
        elapsed_minutes = int(elapsed_time.seconds/60)
        if elapsed_minutes > 5:
            for token in tokens:
                download_blocks(download_dir, infura_api_key, token)

            yield get_volume(download_dir, tokens)

        prev_time = current_time
        time.sleep(1)
