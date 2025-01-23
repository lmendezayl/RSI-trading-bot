from binance.client import Client
from ta.momentum import RSIIndicator
from dotenv import load_dotenv
import os
import time
import pandas as pd 

# esto carga las variables de entorno
load_dotenv()

# obtenemos la claves api del .env
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

# importante marcar testnet=True para que sepa que estamos en la cuenta de prueba
client = Client(api_key, api_secret, testnet=True) 

symbol = "BTCUSDT"
trade_quantity = 0.001
rsi_period = 12
buy_rsi_threshold = 30
sell_rsi_threshold = 70

def get_historical_data(symbol, interval='1h', limit=100):
    # obtiene los datos historicos de las velas
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    # open high low close volume
    ohlcv = pd.DataFrame(klines, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"], unit="ms")
    # hacemos que el index sea timestamp
    ohlcv.set_index("timestamp", inplace=True)
    ohlcv["close"] = ohlcv["close"].astype(float)
    return ohlcv

def calculate_rsi(df, period):
    # calcula el rsi para un df de precios
    rsi_indicator = RSIIndicator(df['close'], window=period)
    df['rsi'] = rsi_indicator.rsi()
    return df

def place_buy_order(symbol, quantity):
    order = client.order_market_buy(symbol=symbol, quantity = quantity)
    print(f"Placing buy order for {quantity} {symbol}")

def place_sell_order(symbol, quantity):
    order = client.order_market_sell(symbol=symbol, quantity = quantity)
    print(f"Placing sell order for {quantity} {symbol}")

def trading_bot():
    
    # esto es para indicar que el bot no compro antes
    in_position = False
    
    # llamamos el precio de btc en un endless loop
    while True:
        current_price = get_current_price(symbol)
        print(f"Current price of {symbol}: {current_price}")
        if not in_position:
            if current_price < buy_price_threshold:
                print(f"Price is below {buy_price_threshold}. Placing buy order.")
                place_buy_order(symbol, trade_quantity)
                in_position = True
        else: 
            if current_price > sell_price_threshold:
                print(f"Price is below {sell_price_threshold}. Placing sell order.")
                place_sell_order(symbol, trade_quantity)
                in_position = False
                
        time.sleep(3)

if __name__ == "__main__":
    get_historical_data(symbol)
    