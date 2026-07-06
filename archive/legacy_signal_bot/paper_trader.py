"""
paper_trader.py - مدیریت Paper Trading
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List

try:
    from config import (
        PAPER_TRADING_LOG_FILE, PAPER_TRADING_BALANCE,
        PAPER_TRADING_MAKER_FEE, PAPER_TRADING_TAKER_FEE
    )
except:
    PAPER_TRADING_LOG_FILE = "paper_trading_log.json"
    PAPER_TRADING_BALANCE = 10000
    PAPER_TRADING_MAKER_FEE = 0.001
    PAPER_TRADING_TAKER_FEE = 0.0015


class PaperTrader:
    """مدیریت معاملات Paper Trading"""
    
    def __init__(self, exchange: str = "binance", log_file: str = None):
        self.exchange = exchange
        self.log_file = log_file or str(PAPER_TRADING_LOG_FILE)
        self.balance = PAPER_TRADING_BALANCE
        self.positions: List[Dict] = []
        self.trades: List[Dict] = []
        self.load_from_file()
    
    def load_from_file(self):
        """بارگذاری داده‌های قبلی"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.exchange = data.get("exchange", "binance")
                self.balance = data.get("balance", PAPER_TRADING_BALANCE)
                self.positions = data.get("positions", [])
                self.trades = data.get("trades", [])
                print(f"✅ Paper Trading بارگذاری شد")
                print(f"   Exchange: {self.exchange}")
                print(f"   Balance: ${self.balance:,.2f}")
                print(f"   Trades: {len(self.trades)}")
        except FileNotFoundError:
            print(f"⚠️ فایل لاگ یافت نشد، شروع از صفر...")
            self.save()
    
    def open_position(self, symbol: str, side: str, price: float, 
                     quantity: float, timestamp: datetime = None) -> bool:
        """باز کردن موضع جدید"""
        fee = price * quantity * PAPER_TRADING_TAKER_FEE
        cost = price * quantity + fee
        
        if cost > self.balance:
            print(f"❌ موجودی کافی نیست")
            print(f"   نیاز: ${cost:,.2f} | دارا: ${self.balance:,.2f}")
            return False
        
        position = {
            "id": len(self.positions) + 1,
            "symbol": symbol,
            "side": side,
            "entry_price": price,
            "quantity": quantity,
            "entry_time": (timestamp or datetime.now()).isoformat(),
            "entry_value": cost,
            "fees": fee
        }
        
        self.positions.append(position)
        self.balance -= cost
        
        print(f"✅ موضع باز: {side.upper()} {quantity} {symbol}")
        print(f"   قیمت: ${price:,.2f} | کارمزد: ${fee:,.2f}")
        print(f"   موجودی: ${self.balance:,.2f}")
        self.save()
        return True
    
    def close_position(self, symbol: str, price: float, 
                      timestamp: datetime = None) -> bool:
        """بستن موضع"""
        matching = [p for p in self.positions if p["symbol"] == symbol]
        
        if not matching:
            print(f"❌ موضع برای {symbol} یافت نشد")
            return False
        
        position = matching[0]
        fee = price * position["quantity"] * PAPER_TRADING_TAKER_FEE
        exit_value = price * position["quantity"] - fee
        profit = exit_value - (position["entry_value"] - position["fees"])
        profit_percent = (profit / (position["entry_value"] - position["fees"])) * 100 if position["entry_value"] > 0 else 0
        
        trade = {
            "id": len(self.trades) + 1,
            "symbol": symbol,
            "side": position["side"],
            "entry_price": position["entry_price"],
            "exit_price": price,
            "quantity": position["quantity"],
            "profit": round(profit, 2),
            "profit_percent": round(profit_percent, 2),
            "entry_time": position["entry_time"],
            "exit_time": (timestamp or datetime.now()).isoformat(),
            "entry_fees": round(position["fees"], 2),
            "exit_fees": round(fee, 2)
        }
        
        self.trades.append(trade)
        self.positions.remove(position)
        self.balance += exit_value
        
        status = "✅ سود" if profit > 0 else "❌ ضرر" if profit < 0 else "〰️ بی نقص"
        print(f"{status}: {symbol}")
        print(f"   Profit: ${profit:,.2f} ({profit_percent:+.2f}%)")
        print(f"   موجودی: ${self.balance:,.2f}")
        
        self.save()
        return True
    
    def get_stats(self) -> Dict:
        """دریافت آمار معاملات"""
        if not self.trades:
            return {
                "total_trades": 0,
                "exchange": self.exchange,
                "balance": self.balance
            }
        
        winning = [t for t in self.trades if t["profit"] > 0]
        losing = [t for t in self.trades if t["profit"] < 0]
        
        total_profit = sum(t["profit"] for t in self.trades)
        initial_balance = PAPER_TRADING_BALANCE
        
        return {
            "exchange": self.exchange,
            "total_trades": len(self.trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": round((len(winning) / len(self.trades)) * 100, 2) if self.trades else 0,
            "total_profit": round(total_profit, 2),
            "total_profit_percent": round((total_profit / initial_balance) * 100, 2),
            "current_balance": round(self.balance, 2),
            "initial_balance": initial_balance,
        }
    
    def print_stats(self):
        """چاپ آمار"""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("📊 خلاصهی Paper Trading")
        print("=" * 60)
        print(f"Exchange: {stats['exchange']}")
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Win Rate: {stats.get('win_rate', 0):.2f}%")
        print(f"Total Profit: ${stats['total_profit']:,.2f}")
        print(f"Profit %: {stats['total_profit_percent']:+.2f}%")
        print(f"Current Balance: ${stats['current_balance']:,.2f}")
        print("=" * 60)
    
    def save(self):
        """ذخیرهی داده‌ها"""
        data = {
            "exchange": self.exchange,
            "balance": round(self.balance, 2),
            "positions": self.positions,
            "trades": self.trades,
            "stats": self.get_stats(),
            "last_update": datetime.now().isoformat()
        }
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    trader = PaperTrader(exchange="binance")
    trader.print_stats()