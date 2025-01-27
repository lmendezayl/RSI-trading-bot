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
formatter = logging.Formatter('%(levelname)-8s %(message)s')
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
    except Exception as e:
        logging.exception("Error al obtener datos")
        return None

def calculate_rsi(df, period):
    # calcula el rsi para un df de precios
    rsi_indicator = RSIIndicator(df['close'], window=period)
    df['rsi'] = rsi_indicator.rsi()
    return df

def place_buy_order(symbol, quantity):
    logging.info("Creando orden de compra por %d %s...", quantity, symbol)
    try:
        client.order_market_buy(symbol=symbol, quantity = quantity)
        logging.info("Orden de compra exitosa")
    except Exception as e:
        logging.exception("Error al crear la orden de compra")


def place_sell_order(symbol, quantity):
    logging.info("Creando orden de venta por %d %s...", quantity, symbol)
    try: 
        client.order_market_sell(symbol=symbol, quantity = quantity)
        logging.info("Orden de venta exitosa")
    except Exception as e:
        logging.exception("Error al crear la orden de venta")
    
def trading_bot():
    # queremos que compre si el rsi actual es menor al umbral de compra y que venda si es mayor al umbral de venta
    # esto es para indicar que el bot no compro antes
    in_position = False
    print(chr(27) + "[2J")
    # todas las opciones disp
    print("""
        Indique con que criptomoneda operar
        1. BTC/USDT  (Bitcoin)
        2. ETH/USDT  (Ethereum)
        3. BNB/USDT  (Binance Coin)
        4. XRP/USDT  (Ripple)
        5. ADA/USDT  (Cardano)
        6. DOGE/USDT (Dogecoin)
        7. SOL/USDT  (Solana)
        8. MATIC/USDT (Polygon)
        9. DOT/USDT  (Polkadot)
        10. LTC/USDT (Litecoin)
        """)
    choice = input()
    match choice:
        case "1":
            symbol = "BTCUSDT"
        case "2":
            symbol = "ETHUSDT"
        case "3":
            symbol = "BNBUSDT"
        case "4":
            symbol = "XRPUSDT"
        case "5":
            symbol = "ADAUSDT"
        case "6":
            symbol = "DOGEUSDT"
        case "7":
            symbol = "SOLUSDT"
        case "8":
            symbol = "MATICUSDT"
        case "9":
            symbol = "DOTUSDT"
        case "10":
            symbol = "LTCUSDT"
        case _:
            print("Opción no valida")
            exit()
    # god bless clear screen
    print("")
    logging.info(f"Ud. ha elegido {symbol}\n")
    time.sleep(2)
    print(chr(27) + "[2J")
    logging.info("Indique la cantidad de %s con la que desea operar", symbol)
    trade_quantity = input()
    print(chr(27) + "[2J")
    logging.info("Ud. ha elegido operar con %d %s", trade_quantity, symbol)
    try:
        while True:
            df = get_historical_data(symbol)
            if df is None:
                logging.error("Error al obtener datos historicos. Reintentando en 5 segundos...")
                time.sleep(5)
                continue
            # pongo 14 porque es el rsi recomendado 
            df = calculate_rsi(df, period=14)
            current_rsi = df['rsi'].iloc[-1]

            logging.info("RSI: %d ", current_rsi)
            if not in_position and current_rsi < buy_rsi_threshold:
                logging.info("RSI esta por debajo de %d.", buy_rsi_threshold)
                place_buy_order(symbol, trade_quantity)
                in_position = True
            elif in_position and current_rsi > sell_rsi_threshold:
                logging.info("RSI esta por encima de %d.", sell_rsi_threshold)
                place_sell_order(symbol, trade_quantity)
                in_position = False
                
            time.sleep(5)
    except:
        logging.exception("Error de ejecucion")

def get_client_data():
    print(client.get_account())

if __name__ == "__main__":
    trading_bot()