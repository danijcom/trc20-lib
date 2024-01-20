# TRC20 Library
Small Python library to manage TRC20 wallet. Allows to send USDT, TRX, and swap USDT&lt;->TRX

The main API for TRX-USDT rate is [CoinGecko](https://www.coingecko.com/) but as they made their API very limited to non-paid users, it's better to use some backup API ([LiveCoinWatch](https://www.livecoinwatch.com/) for example).

Also, I hardly handle any errors in the library, so it is advisable to do it externally when using it.

# Requirements
[tronpy](https://pypi.org/project/tronpy/) >= 0.4.0 (tested on 0.4.0)

[loguru](https://pypi.org/project/loguru/) >= 0.7.2 (tested on 0.7.2)

[TronGrid](https://www.trongrid.io/) API key

[LiveCoinWatch](https://www.livecoinwatch.com/) API key

# Example usage
```
#import library
import tronLib

#I use loguru in my projects so its better for you to configure the logs path for the logger, or change loguru to something you like (in the tronLib file)
from loguru import logger

#Setup logger, you can use your path and max filesize
logger.add("LOGS_PATH", rotation="5 MB")

#Initialize client
my_wallet = tronLib.MyTron(LIVE_COIN_WATCH_API_KEY, TRON_GRID_API_KEY, WALLET_PRIVATE_KEY)

#Get TRX balance
my_trx_balance = my_wallet.get_trx_balance()
print(f'TRX balance: {my_balance}')

#Get USDT balance
my_usdt_balance = my_wallet.get_coin_balance(tronLib.Contract.USDT)
print(f'USDT balance: {my_balance}')

#Check the given address for validity
is_valid_address(SOME_TRC20_ADDRESS)

#Send TRX
tx_id, status, data = my_wallet.send_trx(RECIPIENT_ADDRESS, AMOUNT_TRX_TO_SEND)

#Send USDT (you can add another token contract address to the Contracts enum and use it to send another token)
tx_id, status, data = my_wallet.send_coin(tronLib.Contract.USDT, RECIPIENT_ADDRESS, AMOUNT_TRX_TO_SEND)

#Swap TRX to USDT via SunSwap contract
tx_id, status, data = my_wallet.trx_to_usdt(AMOUNT_TRX_TO_SWAP)

#Swap USDT to TRX via SunSwap contract
tx_id, status, data = my_wallet.usdt_to_trx(AMOUNT_USDT_TO_SWAP)
```
