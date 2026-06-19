import os
import requests
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

def load_symbols():
    with open("symbols.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]

def scan_stock(symbol):
    try:
        df = yf.download(
            symbol,
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=True
        )

        if len(df) < 60:
            return None

        close = df["Close"]

        ema5 = close.ewm(span=5).mean().iloc[-1]
        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]

        rsi = RSIIndicator(close.squeeze(), window=14).rsi().iloc[-1]

        last_close = float(close.iloc[-1])

        if (
            last_close > 50
            and last_close < 6000
            and ema5 > ema20 > ema50
            and rsi > 60
        ):

            entry_low = round(last_close)
            entry_high = round(last_close * 1.005)

            sl = round(last_close * 0.96)
            tp1 = round(last_close * 1.08)
            tp2 = round(last_close * 1.12)

            return f"""
🔥 DAYTRADE SIGNAL

Kode : {symbol.replace('.JK','')}
Harga : {round(last_close)}

✅ Entry : {entry_low} - {entry_high}

🎯 TP1 : {tp1} (+8%)
🎯 TP2 : {tp2} (+12%)

🛑 SL : {sl} (-4%)

⚡ RSI : {round(rsi,1)}

Trend : EMA5 > EMA20 > EMA50
"""

    except Exception as e:
        print(symbol, e)

    return None

def main():
    symbols = load_symbols()

    found = 0

    for symbol in symbols:
        signal = scan_stock(symbol)

        if signal:
            send_telegram(signal)
            found += 1

    send_telegram(f"✅ Scan selesai\nSignal ditemukan: {found}")

if __name__ == "__main__":
    main()
