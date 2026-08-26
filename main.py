# ==============================================================================
# 👑 BANK NIFTY PRO MAX v1.0 : SMART WEEKLY ENGINE (TELEGRAM CLOUD)
# ==============================================================================
import datetime
import time
import json
import urllib.request
import os
import pytz
import yfinance as yf
import pandas as pd
import requests
import warnings
warnings.filterwarnings("ignore")

# 🔐 TELEGRAM CREDENTIALS
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

MAX_TRADES_PER_DAY = 5  
TRADES_TAKEN_TODAY = 0
DAILY_SIGNALS_COUNT = 0 
TODAYS_DATE = None
LAST_SIGNAL = None

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f" [🔴 ERROR] Telegram connection error: {e}")

def fire_startup_test():
    ist = pytz.timezone("Asia/Kolkata")
    now_str = datetime.datetime.now(ist).strftime('%d-%b-%Y %I:%M:%S %p IST')
    
    msg = "*🟢 BANK NIFTY PRO MAX v1.0 ACTIVE!*\n\n"
    msg += "⚡ Status: Smart Weekly Engine Started 🚀\n"
    msg += f"📅 Time: {now_str}\n"
    msg += f"🛡️ Mode: BankNifty Tuned + Wednesday Theta Shield\n"
    msg += f"📊 Quota Cap: {MAX_TRADES_PER_DAY} Trades/Day\n\n"
    msg += "👉 System Check: Ready to capture Bank Nifty Spikes!"
    print("\n [🔔] Firing Startup Test Notification...")
    send_telegram_msg(msg)

def to_float(val):
    try:
        if isinstance(val, (pd.Series, pd.DataFrame)): return float(val.iloc[-1])
        if hasattr(val, 'item'): return float(val.item())
        return float(val)
    except Exception:
        return 0.0

def clean_df(df):
    if df.empty: return df
    if isinstance(df.columns, pd.MultiIndex):
        if 'Close' in df.columns.get_level_values(0): df.columns = df.columns.get_level_values(0)
        else: df.columns = df.columns.get_level_values(1)
    return df.dropna()

# --- 🏦 BANK NIFTY OPTION CHAIN LOGIC ---
def get_nse_option_chain():
    try:
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None

def analyze_oi_data(spot_price):
    oi_data = get_nse_option_chain()
    if not oi_data: return None, None, "OI Fetch Failed", None
    
    try:
        records = oi_data['records']['data']
        all_expiries = oi_data['records']['expiryDates']
        
        # Current Week Only Logic
        current_expiry = all_expiries[0]
        
        total_ce_oi = 0
        total_pe_oi = 0
        atm_strike = round(spot_price / 100) * 100
        
        for record in records:
            if record.get('expiryDate') == current_expiry:
                strike = record.get('strikePrice', 0)
                # Checking wider range for Bank Nifty (500 pts)
                if abs(strike - atm_strike) <= 500:
                    if 'CE' in record: total_ce_oi += record['CE'].get('openInterest', 0)
                    if 'PE' in record: total_pe_oi += record['PE'].get('openInterest', 0)
        
        if total_ce_oi == 0: return None, None, "No CE OI Data", None
        pcr = round(total_pe_oi / total_ce_oi, 2)
        
        # 🛡️ SMART THETA SHIELD (Wednesday Only for Bank Nifty)
        now_ist = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        current_weekday = now_ist.weekday() # 0=Mon, 1=Tue, 2=Wed
        
        if current_weekday == 2 and len(all_expiries) > 1:
            suggested_expiry = f"⚠️ NEXT WEEK ({all_expiries[1]}) - Avoid Expiry Theta!"
        else:
            suggested_expiry = f"Current Week ({current_expiry})"
        
        if pcr > 1.2: return pcr, "CE", "BULLISH (Put Writers Active)", suggested_expiry
        elif pcr < 0.8: return pcr, "PE", "BEARISH (Call Writers Active)", suggested_expiry
        else: return pcr, "NEUTRAL", "NEUTRAL", suggested_expiry
    except Exception as e:
        return None, None, f"Error: {e}", None

def check_daily_reset():
    global TRADES_TAKEN_TODAY, DAILY_SIGNALS_COUNT, TODAYS_DATE, LAST_SIGNAL
    ist = pytz.timezone("Asia/Kolkata")
    current_date = datetime.datetime.now(ist).date()
    if TODAYS_DATE != current_date:
        TODAYS_DATE = current_date
        TRADES_TAKEN_TODAY = 0
        DAILY_SIGNALS_COUNT = 0  
        LAST_SIGNAL = None

def fire_telegram_alert(trade):
    msg = "*👑 BANK NIFTY PRO MAX v1.0*\n\n"
    msg += f"⚡ Action: *BUY {trade['Type']}*\n"
    msg += f"📌 Strike: {trade['Symbol']} {trade['Strike']}\n"
    msg += f"📅 Expiry: *{trade['Expiry']}*\n"
    msg += f"📉 Spot CMP: ₹{trade['Spot_CMP']}\n\n"
    msg += f"🧠 Logic: {trade['Logic']}\n"
    msg += f"🧲 OI Data: {trade['OI_Info']}\n"
    msg += f"🔥 VIX: {trade['VIX']}\n"
    msg += f"📊 Quota: {TRADES_TAKEN_TODAY}/{MAX_TRADES_PER_DAY}\n\n"
    msg += "👉 Aggressive Bank Nifty Move Detected!"
    send_telegram_msg(msg)

# --- THE SCANNER ENGINE ---
def run_yfinance_scan():
    global LAST_SIGNAL, TRADES_TAKEN_TODAY, DAILY_SIGNALS_COUNT
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.datetime.now(ist)
    now_time = now_ist.strftime('%I:%M:%S %p IST')
    
    if TRADES_TAKEN_TODAY >= MAX_TRADES_PER_DAY: return

    print(f"\n 🔓 SCANNING MARKET (BANK NIFTY MASTER)... [{now_time}]")

    try:
        # 🛡️ 15:20 (3:20 PM) NEW EOD SHIELD
        if now_ist.time() >= datetime.time(15, 20):
            print(" 🛑 Filtered: EOD Shield Active (Post 03:20 PM).")
            return

        nifty = clean_df(yf.download("^NSEBANK", period="5d", interval="5m", progress=False, threads=False))
        bees = clean_df(yf.download("BANKBEES.NS", period="5d", interval="5m", progress=False, threads=False))
        if not bees.empty and 'Volume' in bees.columns: nifty['Volume'] = bees['Volume'].reindex(nifty.index).fillna(0)
        else: nifty['Volume'] = 1.0

        current_block_start = now_ist.replace(minute=(now_ist.minute // 5) * 5, second=0, microsecond=0)
        nifty = nifty[nifty.index < current_block_start]
        if nifty.empty or len(nifty) < 15: return

        vix = clean_df(yf.download("^INDIAVIX", period="5d", interval="5m", progress=False, threads=False))
        live_vix = 15.0 if vix.empty else to_float(vix['Close'].iloc[-1])
        if live_vix < 11.0: return

        daily_data = clean_df(yf.download("^NSEBANK", period="2d", interval="1d", progress=False, threads=False))
        prev_day_high = to_float(daily_data['High'].iloc[-2]) if len(daily_data) >= 2 else 999999.0
        prev_day_low = to_float(daily_data['Low'].iloc[-2]) if len(daily_data) >= 2 else 0.0
        prev_day_close = to_float(daily_data['Close'].iloc[-2]) if len(daily_data) >= 2 else 0.0

        nifty['Typ'] = (nifty['High'] + nifty['Low'] + nifty['Close']) / 3
        nifty['Date'] = nifty.index.date
        nifty['PV'] = nifty['Typ'] * nifty['Volume']
        cum_pv = nifty.groupby('Date')['PV'].cumsum()
        cum_vol = nifty.groupby('Date')['Volume'].cumsum()
        nifty['VWAP'] = cum_pv / cum_vol
        nifty['VWAP'] = nifty['VWAP'].fillna(nifty['Typ'])
        nifty['EMA_20'] = nifty['Close'].ewm(span=20, adjust=False).mean()

        live_close = to_float(nifty['Close'].iloc[-1])
        live_open = to_float(nifty['Open'].iloc[-1])
        live_high = to_float(nifty['High'].iloc[-1])
        live_low = to_float(nifty['Low'].iloc[-1])
        live_vwap = to_float(nifty['VWAP'].iloc[-1])
        live_ema = to_float(nifty['EMA_20'].iloc[-1])
        current_vol = to_float(nifty['Volume'].iloc[-1])
        avg_vol = to_float(nifty['Volume'].rolling(window=5).mean().shift(1).iloc[-1])
        
        print(f" 🎯 BANK NIFTY: ₹{live_close:.2f} | VWAP: ₹{live_vwap:.2f} | EMA: ₹{live_ema:.2f}")

        nifty['Body'] = abs(nifty['Close'] - nifty['Open'])
        avg_body = to_float(nifty['Body'].rolling(window=10).mean().iloc[-1])
        candle_body = abs(live_close - live_open)
        upper_wick = live_high - max(live_open, live_close)
        lower_wick = min(live_open, live_close) - live_low
            
        ce_wick_safe = bool(upper_wick <= (candle_body * 1.2)) if candle_body > 0 else False
        pe_wick_safe = bool(lower_wick <= (candle_body * 1.2)) if candle_body > 0 else False

        if now_ist.time() < datetime.time(9, 45) and prev_day_close > 0:
            if abs(live_close - prev_day_close) / prev_day_close > 0.005: return
        if datetime.time(11, 30) <= now_ist.time() <= datetime.time(13, 15): return

        # 🚀 BANK NIFTY TUNED: 100 pt Choppy Box
        last_1_hour = nifty.iloc[-12:]
        if (to_float(last_1_hour['High'].max()) - to_float(last_1_hour['Low'].min())) < 100.0: return

        ema_slope = live_ema - to_float(nifty['EMA_20'].iloc[-4]) 
        vol_condition = bool(current_vol > (avg_vol * 1.2)) if current_vol > 10 else True
        
        # 🚀 BANK NIFTY TUNED: Requires 20pt VWAP gap, Max 80pt from EMA
        min_distance_passed = bool((abs(live_close - live_vwap) >= 20.0) and (abs(live_close - live_ema) >= 15.0))
        fomo_ceiling_passed = bool(abs(live_close - live_ema) <= 80.0)

        pcr, oi_bias, oi_sentiment, suggested_expiry = analyze_oi_data(live_close)
        if pcr: print(f" 🧲 SMART WEEKLY OI -> PCR: {pcr} | Bias: {oi_sentiment} | Expiry: {suggested_expiry}")

        # 🚀 BANK NIFTY TUNED: 100 pt Strike Gap
        strike_gap = 100 if now_ist.weekday() == 2 else 0
        ce_strike = (round(live_close / 100) * 100) - strike_gap
        pe_strike = (round(live_close / 100) * 100) + strike_gap

        current_signal = None
        logic_string = ""
        
        if (live_close > live_vwap) and (live_close > live_ema):
            if not ce_wick_safe or ema_slope >= 15.0 or ema_slope < 5.0 or not min_distance_passed or not fomo_ceiling_passed or not vol_condition or 0 < (prev_day_high - live_close) < 25 or oi_bias == "PE":
                pass
            else:
                current_signal = "CE"
                logic_string = f"BankNifty Bullish (Slope: +{ema_slope:.1f}) + VWAP"
                
        elif (live_close < live_vwap) and (live_close < live_ema):
            if not pe_wick_safe or ema_slope <= -15.0 or ema_slope > -5.0 or not min_distance_passed or not fomo_ceiling_passed or not vol_condition or 0 < (live_close - prev_day_low) < 25 or oi_bias == "CE":
                pass
            else:
                current_signal = "PE"
                logic_string = f"BankNifty Bearish (Slope: {ema_slope:.1f}) + VWAP"
            
        if current_signal:
            strike_to_fire = ce_strike if current_signal == "CE" else pe_strike
            if current_signal != LAST_SIGNAL:
                TRADES_TAKEN_TODAY += 1
                DAILY_SIGNALS_COUNT += 1  
                trade_info = {
                    "Type": current_signal, "Symbol": "BANKNIFTY", "Strike": f"{strike_to_fire} {current_signal}",
                    "Spot_CMP": round(live_close, 2), "Logic": logic_string, "VIX": round(live_vix, 2),
                    "OI_Info": f"PCR {pcr} ({oi_sentiment})" if pcr else "Unavailable",
                    "Expiry": suggested_expiry
                }
                print(f" 🟢 🔥 ULTIMATE SIGNAL DETECTED: {current_signal}!")
                fire_telegram_alert(trade_info)
                LAST_SIGNAL = current_signal 
            
    except Exception as e:
        print(f" 🔴 Error: {e}")

# ------------------------------------------------------------------------------
# 🔄 CONTINUOUS SYNC ENGINE
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 75)
    print(" 👑 BANK NIFTY PRO MAX (CONTINUOUS CLOUD LOOP)")
    print("=" * 75)

    fire_startup_test()

    while True:
        ist = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.datetime.now(ist)

        if now_ist.weekday() >= 5: break

        # 🛑 3:41 PM IST पर डेली ब्रीफ
        if now_ist.time() >= datetime.time(15, 41):
            brief_msg = f"📊 *BANK NIFTY - DAILY BRIEF*\n\n🔹 *Signals Today:* {DAILY_SIGNALS_COUNT}\n🛑 *Market Closed.* System Shutting Down."
            send_telegram_msg(brief_msg)
            break 

        if now_ist.time() < datetime.time(9, 30):
            target_time = now_ist.replace(hour=9, minute=30, second=0, microsecond=0)
            time.sleep(max(10, (target_time - now_ist).total_seconds()))
            continue

        check_daily_reset()
        run_yfinance_scan()
        
        now = datetime.datetime.now(ist)
        next_minute = (now.minute // 5 + 1) * 5
        if next_minute >= 60: next_scan_time = now.replace(hour=(now.hour + 1) % 24, minute=0, second=20, microsecond=0)
        else: next_scan_time = now.replace(minute=next_minute, second=20, microsecond=0)
        if next_scan_time <= now: next_scan_time += datetime.timedelta(minutes=5)
            
        time.sleep((next_scan_time - now).total_seconds())
