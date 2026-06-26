import os
import time
from datetime import datetime

import requests
import yfinance as yf
from ta.momentum import RSIIndicator

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Menyimpan status sinyal terakhir tiap saham
signal_state = {}


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        r = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=30
        )
        print(f"Telegram: {r.status_code}")

    except Exception as e:
        print(f"Telegram Error: {e}")


def load_symbols():
    with open("symbols.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]


def scan_stock(symbol):
    try:
        print(f"Scanning {symbol}")

        df = yf.download(
            symbol,
            period="6mo",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df.empty or len(df) < 60:
            return None

        close = df["Close"].squeeze()

        ema5 = close.ewm(span=5).mean().iloc[-1]
        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]

        rsi = RSIIndicator(close, window=14).rsi().iloc[-1]

        last_close = float(close.iloc[-1])

        if (
            60 < last_close < 8000
            and ema5 > ema20 > ema50
            and rsi > 60
        ):

            entry_low = round(last_close)
            entry_high = round(last_close * 1.005)

            sl = round(last_close * 0.96)
            tp1 = round(last_close * 1.05)
            tp2 = round(last_close * 1.12)

            return f"""🔥 DAYTRADE SIGNAL

Kode : {symbol.replace('.JK','')}
Harga : {round(last_close)}

✅ Entry : {entry_low} - {entry_high}

🎯 TP1 : {tp1} (+5%)
🎯 TP2 : {tp2} (+12%)

🛑 SL : {sl} (-4%)

⚡ RSI : {round(rsi,1)}

Trend : EMA5 > EMA20 > EMA50"""

    except Exception as e:
        print(f"ERROR {symbol}: {e}")

    return None


def main():
    global signal_state

    symbols = load_symbols()

    active_signal = 0
    new_signal = 0

    for symbol in symbols:

        signal = scan_stock(symbol)

        current = signal is not None
        previous = signal_state.get(symbol, False)

        if current:
            active_signal += 1

        # Kirim hanya jika sinyal baru muncul
        if current and not previous:
            send_telegram(signal)
            new_signal += 1
            print(f"NEW SIGNAL -> {symbol}")

        # Update status
        signal_state[symbol] = current

    print("=" * 60)
    print(f"Total Saham     : {len(symbols)}")
    print(f"Signal Aktif    : {active_signal}")
    print(f"Signal Baru     : {new_signal}")
    print("=" * 60)


if __name__ == "__main__":

    INTERVAL = 300  # 5 menit

    while True:

        try:
            print()
            print("=" * 60)
            print(f"SCAN : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            main()

        except Exception as e:
            print(f"MAIN ERROR: {e}")

        print(f"Sleep {INTERVAL} seconds...\n")
        time.sleep(INTERVAL)
