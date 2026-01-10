"""
Performance Tracker - Consolidated Metrics Module
Extends db.py metrics with advanced analytics: Sharpe, Sortino, Max Drawdown, Strategy Ranking.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from servos.db import get_connection, calculate_performance_metrics
from psycopg2.extras import RealDictCursor


@dataclass
class PerformanceReport:
    """Complete performance report with all metrics."""
    # Basic Metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # P&L Metrics
    total_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # Advanced Metrics
    profit_factor: float = 0.0
    expectancy: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Risk Metrics
    max_drawdown: float = 0.0
    max_drawdown_duration: float = 0.0  # In hours
    avg_drawdown: float = 0.0
    
    # Trade Metrics
    avg_holding_time: float = 0.0  # In hours
    avg_trades_per_day: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    
    # Period Info
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    

class PerformanceTracker:
    """
    Advanced Performance Tracking System.
    
    Features:
    - Sharpe Ratio: Risk-adjusted return (excess return / std dev)
    - Sortino Ratio: Downside risk-adjusted return
    - Max Drawdown: Largest peak-to-trough decline
    - Calmar Ratio: Annual return / Max Drawdown
    - Strategy Ranking: Compare strategies by performance
    """
    
    RISK_FREE_RATE = 0.05  # 5% annual risk-free rate (T-bills)
    TRADING_DAYS_PER_YEAR = 365  # Crypto trades 24/7
    
    def __init__(self):
        self.cache: Dict[str, PerformanceReport] = {}
        self.cache_ttl = 300  # 5 minutes cache
        self.cache_timestamps: Dict[str, datetime] = {}
    
    def get_trades(self, chat_id: str, days: int = 30, 
                   strategy: str = None, symbol: str = None, 
                   exchange: str = None) -> List[Dict]:
        """Fetch closed trades from database."""
        conn = get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                conditions = ["chat_id = %s", "status = 'CLOSED'"]
                params = [chat_id]
                
                if strategy:
                    conditions.append("strategy = %s")
                    params.append(strategy)
                if symbol:
                    conditions.append("symbol = %s")
                    params.append(symbol)
                if exchange:
                    conditions.append("exchange = %s")
                    params.append(exchange)
                
                conditions.append("exit_time >= NOW() - INTERVAL '%s days'")
                params.append(days)
                
                where_clause = " AND ".join(conditions)
                
                cur.execute(f"""
                    SELECT id, symbol, side, strategy, exchange, 
                           entry_price, exit_price, quantity, leverage,
                           entry_time, exit_time, pnl, pnl_pct, fees, slippage
                    FROM trade_journal
                    WHERE {where_clause}
                    ORDER BY exit_time ASC
                """, params)
                
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"❌ PerformanceTracker.get_trades Error: {e}")
            return []
        finally:
            conn.close()
    
    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """
        Calculate Sharpe Ratio.
        Formula: (Mean Return - Risk Free Rate) / Std Dev of Returns
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        daily_rf = self.RISK_FREE_RATE / self.TRADING_DAYS_PER_YEAR
        
        # Standard deviation
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance) if variance > 0 else 0.0
        
        if std_dev == 0:
            return 0.0
        
        # Annualized Sharpe
        sharpe = (mean_return - daily_rf) / std_dev
        annualized_sharpe = sharpe * math.sqrt(self.TRADING_DAYS_PER_YEAR)
        
        return round(annualized_sharpe, 2)
    
    def calculate_sortino_ratio(self, returns: List[float]) -> float:
        """
        Calculate Sortino Ratio.
        Like Sharpe but only considers downside volatility.
        Formula: (Mean Return - Risk Free Rate) / Downside Std Dev
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        daily_rf = self.RISK_FREE_RATE / self.TRADING_DAYS_PER_YEAR
        
        # Downside returns only
        downside_returns = [r for r in returns if r < 0]
        
        if not downside_returns:
            return float('inf') if mean_return > daily_rf else 0.0
        
        # Downside std dev
        downside_mean = sum(downside_returns) / len(downside_returns)
        downside_variance = sum((r - downside_mean) ** 2 for r in downside_returns) / len(downside_returns)
        downside_std = math.sqrt(downside_variance) if downside_variance > 0 else 0.0
        
        if downside_std == 0:
            return 0.0
        
        sortino = (mean_return - daily_rf) / downside_std
        annualized_sortino = sortino * math.sqrt(self.TRADING_DAYS_PER_YEAR)
        
        return round(annualized_sortino, 2)
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> tuple:
        """
        Calculate Maximum Drawdown.
        Returns: (max_drawdown_pct, max_drawdown_duration_hours)
        """
        if not equity_curve or len(equity_curve) < 2:
            return 0.0, 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        max_dd_duration = 0
        current_dd_start = 0
        
        for i, equity in enumerate(equity_curve):
            if equity > peak:
                peak = equity
                current_dd_start = i
            
            dd = (peak - equity) / peak if peak > 0 else 0
            
            if dd > max_dd:
                max_dd = dd
                max_dd_duration = i - current_dd_start
        
        # Convert to percentage and estimate duration in hours (assuming ~1 trade/hour)
        return round(max_dd * 100, 2), max_dd_duration
    
    def build_equity_curve(self, trades: List[Dict], initial_balance: float = 1000.0) -> List[float]:
        """Build equity curve from trades."""
        equity = initial_balance
        curve = [equity]
        
        for trade in trades:
            pnl = float(trade.get('pnl', 0) or 0)
            equity += pnl
            curve.append(equity)
        
        return curve
    
    def calculate_streaks(self, trades: List[Dict]) -> tuple:
        """Calculate maximum consecutive wins and losses."""
        if not trades:
            return 0, 0
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            pnl = float(trade.get('pnl', 0) or 0)
            
            if pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif pnl < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return max_wins, max_losses
    
    def generate_report(self, chat_id: str, days: int = 30,
                       strategy: str = None, symbol: str = None,
                       exchange: str = None) -> PerformanceReport:
        """
        Generate comprehensive performance report.
        """
        # Check cache
        cache_key = f"{chat_id}:{days}:{strategy}:{symbol}:{exchange}"
        if cache_key in self.cache:
            cached_time = self.cache_timestamps.get(cache_key)
            if cached_time and (datetime.now() - cached_time).seconds < self.cache_ttl:
                return self.cache[cache_key]
        
        trades = self.get_trades(chat_id, days, strategy, symbol, exchange)
        
        if not trades:
            return PerformanceReport()
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if float(t.get('pnl', 0) or 0) > 0]
        losing_trades = [t for t in trades if float(t.get('pnl', 0) or 0) < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # P&L metrics
        pnls = [float(t.get('pnl', 0) or 0) for t in trades]
        total_pnl = sum(pnls)
        
        winning_pnls = [p for p in pnls if p > 0]
        losing_pnls = [p for p in pnls if p < 0]
        
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0
        largest_win = max(pnls) if pnls else 0
        largest_loss = min(pnls) if pnls else 0
        
        # Profit Factor
        total_wins = sum(winning_pnls)
        total_losses = abs(sum(losing_pnls))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # Returns for ratio calculations (as percentages)
        returns = [float(t.get('pnl_pct', 0) or 0) / 100 for t in trades]
        
        # Advanced ratios
        sharpe = self.calculate_sharpe_ratio(returns)
        sortino = self.calculate_sortino_ratio(returns)
        
        # Drawdown
        equity_curve = self.build_equity_curve(trades)
        max_dd, max_dd_duration = self.calculate_max_drawdown(equity_curve)
        
        # Calmar Ratio (annualized return / max drawdown)
        if trades:
            first_trade = trades[0]['exit_time']
            last_trade = trades[-1]['exit_time']
            trading_days = (last_trade - first_trade).days or 1
            annualized_return = (total_pnl / 1000) * (365 / trading_days) * 100  # Assuming 1000 initial
            calmar = annualized_return / max_dd if max_dd > 0 else 0
        else:
            calmar = 0
        
        # Streaks
        max_wins, max_losses = self.calculate_streaks(trades)
        
        # Holding time
        holding_times = []
        for t in trades:
            if t['exit_time'] and t['entry_time']:
                delta = t['exit_time'] - t['entry_time']
                holding_times.append(delta.total_seconds() / 3600)
        avg_holding = sum(holding_times) / len(holding_times) if holding_times else 0
        
        # Trades per day
        if trades:
            first_trade = trades[0]['exit_time']
            last_trade = trades[-1]['exit_time']
            trading_days = max((last_trade - first_trade).days, 1)
            avg_trades_per_day = total_trades / trading_days
        else:
            avg_trades_per_day = 0
        
        # Build report
        report = PerformanceReport(
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=round(win_rate, 4),
            total_pnl=round(total_pnl, 2),
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),
            profit_factor=round(min(profit_factor, 99.99), 2),
            expectancy=round(expectancy, 2),
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=round(calmar, 2),
            max_drawdown=max_dd,
            max_drawdown_duration=max_dd_duration,
            avg_drawdown=round(max_dd / 2, 2),
            avg_holding_time=round(avg_holding, 2),
            avg_trades_per_day=round(avg_trades_per_day, 2),
            consecutive_wins=max_wins,
            consecutive_losses=max_losses,
            period_start=trades[0]['entry_time'] if trades else None,
            period_end=trades[-1]['exit_time'] if trades else None
        )
        
        # Cache
        self.cache[cache_key] = report
        self.cache_timestamps[cache_key] = datetime.now()
        
        return report
    
    def rank_strategies(self, chat_id: str, days: int = 30) -> List[Dict]:
        """
        Rank all strategies by performance.
        Returns ordered list from best to worst.
        """
        conn = get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get distinct strategies
                cur.execute("""
                    SELECT DISTINCT strategy FROM trade_journal
                    WHERE chat_id = %s AND status = 'CLOSED'
                    AND exit_time >= NOW() - INTERVAL '%s days'
                """, (chat_id, days))
                
                strategies = [row['strategy'] for row in cur.fetchall()]
        except Exception as e:
            print(f"❌ rank_strategies Error: {e}")
            return []
        finally:
            conn.close()
        
        rankings = []
        for strat in strategies:
            report = self.generate_report(chat_id, days, strategy=strat)
            
            if report.total_trades < 5:
                continue  # Skip strategies with few trades
            
            # Composite score: Expectancy * Win Rate * Profit Factor / Max Drawdown
            dd_factor = max(report.max_drawdown, 1)  # Avoid division by zero
            score = (report.expectancy * report.win_rate * report.profit_factor) / dd_factor
            
            rankings.append({
                'strategy': strat,
                'score': round(score, 4),
                'trades': report.total_trades,
                'win_rate': report.win_rate,
                'expectancy': report.expectancy,
                'profit_factor': report.profit_factor,
                'sharpe': report.sharpe_ratio,
                'max_dd': report.max_drawdown,
                'total_pnl': report.total_pnl
            })
        
        # Sort by score descending
        rankings.sort(key=lambda x: x['score'], reverse=True)
        
        return rankings
    
    def format_report_message(self, report: PerformanceReport, title: str = "Performance Report") -> str:
        """Format report as Telegram message."""
        if report.total_trades == 0:
            return f"📊 *{title}*\n\n⚠️ No hay trades cerrados en el período seleccionado."
        
        # Emoji indicators
        win_emoji = "🟢" if report.win_rate >= 0.5 else "🔴"
        pnl_emoji = "💰" if report.total_pnl >= 0 else "📉"
        sharpe_emoji = "⭐" if report.sharpe_ratio >= 1.0 else "📈" if report.sharpe_ratio >= 0 else "⚠️"
        dd_emoji = "🛡️" if report.max_drawdown <= 10 else "⚠️" if report.max_drawdown <= 20 else "🔴"
        
        msg = f"""📊 *{title}*

*Trades*
├ Total: {report.total_trades}
├ Ganados: {report.winning_trades} {win_emoji}
└ Perdidos: {report.losing_trades}

*P&L* {pnl_emoji}
├ Total: ${report.total_pnl:,.2f}
├ Avg Win: ${report.avg_win:,.2f}
├ Avg Loss: ${report.avg_loss:,.2f}
├ Mayor Ganancia: ${report.largest_win:,.2f}
└ Mayor Pérdida: ${report.largest_loss:,.2f}

*Métricas Clave*
├ Win Rate: {report.win_rate:.1%}
├ Profit Factor: {report.profit_factor:.2f}
└ Expectancy: ${report.expectancy:.2f}

*Risk-Adjusted* {sharpe_emoji}
├ Sharpe Ratio: {report.sharpe_ratio:.2f}
├ Sortino Ratio: {report.sortino_ratio:.2f}
└ Calmar Ratio: {report.calmar_ratio:.2f}

*Drawdown* {dd_emoji}
├ Max DD: {report.max_drawdown:.2f}%
└ Duración DD: {report.max_drawdown_duration:.0f}h

*Operación*
├ Holding Prom: {report.avg_holding_time:.1f}h
├ Trades/Día: {report.avg_trades_per_day:.1f}
├ Racha Wins: {report.consecutive_wins}
└ Racha Losses: {report.consecutive_losses}
"""
        return msg


# Singleton instance
_tracker_instance: Optional[PerformanceTracker] = None

def get_performance_tracker() -> PerformanceTracker:
    """Get singleton PerformanceTracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = PerformanceTracker()
    return _tracker_instance
