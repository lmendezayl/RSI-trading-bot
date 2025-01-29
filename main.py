from binance.client import Client
from ta.momentum import RSIIndicator
from dotenv import load_dotenv
import os
import time
import pandas as pd     
import logging # first timer

# esto carga las variables de entorno
load_dotenv()
# log config
logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s', 
        datefmt='%m-%d %H:%M:%S',
        filename="trading_bot.log",
        filemode='a'
)
# src: https://stackoverflow.com/questions/9321741/printing-to-screen-and-writing-to-a-file-at-the-same-time
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger().addHandler(console)

# obtenemos la claves api del .env
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')

# importante marcar testnet=True para que sepa que estamos en la cuenta de prueba
client = Client(api_key, api_secret, testnet=True) 

buy_rsi_threshold = 30
sell_rsi_threshold = 70

def get_historical_data(symbol, interval='1h', limit=100):
    try:
        # obtiene los datos historicos de las velas
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        # open high low close volume
        ohlcv = pd.DataFrame(klines, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])
        ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"], unit="ms")
        # hacemos que el index sea timestamp
        ohlcv.set_index("timestamp", inplace=True)
        ohlcv["close"] = ohlcv["close"].astype(float)
        return ohlcv
    except:
        logging.exception("Error al obtener datos")
        return None
    
def calculate_rsi(df, period):
    # calcula el rsi para un df de precios
    rsi_indicator = RSIIndicator(df['close'], window=period)
    df['rsi'] = rsi_indicator.rsi()
    return df

def place_buy_order(symbol, quantity):
    try:
        client.order_market_buy(symbol=symbol, quantity = quantity)
        logging.info("Orden de compra exitosa")
    except:
        logging.exception("Error al crear la orden de compra")


def place_sell_order(symbol, quantity):
    logging.info("Creando orden de venta por", quantity, symbol, "...")
    try: 
        client.order_market_sell(symbol=symbol, quantity = quantity)
        logging.info("Orden de venta exitosa")
    except:
        logging.exception("Error al crear la orden de venta")
    
def print_wallet():
    balances = client.get_account()['balances']
    print("Cartera: ")
    for i in range (10):
        print(balances[i]['asset'], " ", balances[i]['free'] )
    print("")

def get_price(symbol):
    print(symbol, ": $", float(client.get_symbol_ticker(symbol=symbol)['price']))      
    print("")

def trading_bot():
    # queremos que compre si el rsi actual es menor al umbral de compra y que venda si es mayor al umbral de venta
    # esto es para indicar que el bot no compro antes
    in_position = False
    
    print(chr(27) + "[2J")
    
    print_wallet()
    
    logging.info("Indique con que criptomoneda operar")
    balances = client.get_account()['balances']
    for i in range(10):
        print(i+1, ". ", balances[i]['asset'], "/ USDT")
        
    choice = input()
    
    match choice:
        case "1":
            symbol = "ETHUSDT"
        case "2":
            symbol = "BTCUSDT"
        case "3":
            symbol = "LTCUSDT"
        case "4":
            symbol = "BNBUSDT"
        case "5":
            symbol = "USDTUSDT"
        case "6":
            symbol = "TRXUSDT"
        case "7":
            symbol = "XRPUSDT"
        case "8":
            symbol = "NEOUSDT"
        case "9":
            symbol = "QTUMUSDT"
        case "10":
            symbol = "EOSUSDT"
        case _:
            print("Opción no valida")
            exit()
    # god bless clear screen
    asset = client.get_account()['balances'][int(choice)-1]['asset']
    free = client.get_account()['balances'][int(choice)-1]['free']
    print("")
    print("Ud. ha elegido ", asset)
    time.sleep(2)
    
    print(chr(27) + "[2J")
    
    print("Saldo estimado:")
    print(asset, " ", free)
      
    print("Indique la cantidad de ", symbol, "con la que desea operar", )
    trade_quantity = input()
    
    print(chr(27) + "[2J")
    print("Ud. ha elegido operar con ", trade_quantity , symbol)
    try:
        while True:
            df = get_historical_data(symbol)
            if df is None:
                print("Error al obtener datos historicos. Reintentando en 5 segundos...")
                time.sleep(5)
                continue
            # pongo 14 porque es el rsi recomendado 
            df = calculate_rsi(df, period=14)
            current_rsi = df['rsi'].iloc[-1]
            
            print("RSI: ", current_rsi)
            
            get_price(symbol)
            
            if not in_position and current_rsi < buy_rsi_threshold:
                print("RSI esta por debajo de %d.", buy_rsi_threshold)
                place_buy_order(symbol, trade_quantity)
                in_position = True
            elif in_position and current_rsi > sell_rsi_threshold:
                print("RSI esta por encima de %d.", sell_rsi_threshold)
                place_sell_order(symbol, trade_quantity)
                in_position = False
                
            time.sleep(5)
    except:
        logging.exception("Error de ejecucion")

if __name__ == "__main__":
    trading_bot()