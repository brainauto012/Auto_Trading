# 파일명: strategies/TrendlineStrategy.py
import time
from math import floor
from strategies.base_strategy import BaseStrategy
from config import settings

class TrendlineStrategy(BaseStrategy):
    """
    수동 지정한 빗각(추세선)을 이용해 분할 매수 및 매도 신호를 생성하는 범용 전략입니다.
    매수 트렌드 라인과 매도 트렌드 라인을 각각 독립적으로 운영합니다.
    """
    
    def __init__(self, strategy_config: dict):
        super().__init__(strategy_config)
        print(f"✅ {self.name} 전략 초기화 완료 (심볼: {self.symbol})")
        
        # =========================================================
        # 1. 매수(Buy) 트렌드 라인 설정
        # =========================================================
        self.buy_t1 = self._convert_date_to_ms(self.params['BUY_TRENDLINE_START_DATE'])
        self.buy_t2 = self._convert_date_to_ms(self.params['BUY_TRENDLINE_END_DATE'])
        self.buy_valid_end_ms = self._convert_date_to_ms(self.params['BUY_TRENDLINE_VALID_END_DATE'])
        self.buy_p1 = self.params['BUY_TRENDLINE_START_PRICE_USD']
        self.buy_p2 = self.params['BUY_TRENDLINE_END_PRICE_USD']
        
        if self.buy_t2 > self.buy_t1:
            self.buy_slope = (self.buy_p2 - self.buy_p1) / (self.buy_t2 - self.buy_t1)
        else:
            self.buy_slope = 0
            
        self.buy_levels = self.params['BUY_LEVELS']
        self.total_seed_krw = self.params['TOTAL_TRADE_SEED_KRW']
        
        # =========================================================
        # 2. 매도(Sell) 트렌드 라인 및 전략 설정
        # =========================================================
        self.sell_partial_enabled = self.params.get('SELL_PARTIAL_ENABLED', False)
        
        self.sell_t1 = self._convert_date_to_ms(self.params.get('SELL_TRENDLINE_START_DATE', self.params['BUY_TRENDLINE_START_DATE']))
        self.sell_t2 = self._convert_date_to_ms(self.params.get('SELL_TRENDLINE_END_DATE', self.params['BUY_TRENDLINE_END_DATE']))
        self.sell_valid_end_ms = self._convert_date_to_ms(self.params.get('SELL_TRENDLINE_VALID_END_DATE', self.params['BUY_TRENDLINE_VALID_END_DATE']))
        self.sell_p1 = self.params.get('SELL_TRENDLINE_START_PRICE_USD', 0)
        self.sell_p2 = self.params.get('SELL_TRENDLINE_END_PRICE_USD', 0)

        if self.sell_t2 > self.sell_t1:
            self.sell_slope = (self.sell_p2 - self.sell_p1) / (self.sell_t2 - self.sell_t1)
        else:
            self.sell_slope = 0

        raw_sell_plan = self.params.get('SELL_PLAN', [])
        self.sell_plan = sorted(raw_sell_plan, key=lambda x: x[0])
        self.sell_stop_loss_ratio = self.params.get('SELL_STOP_LOSS_RATIO', -100.0)

        # =========================================================
        # 3. 상태 관리 변수
        # =========================================================
        self.current_krw_spent = 0.0    
        self.max_holdings = 0.0         
        self.last_sell_step_index = -1  
        self.avg_buy_price = 0.0        # [추가] 평단가 추적 (USD 기준)
        self.is_buying_disabled = False

    def _is_valid_time(self, current_time_ms: int, valid_end_ms: int) -> bool:
        if current_time_ms >= valid_end_ms:
            return False
        return True

    def _calculate_trendline_price(self, current_time_ms: int, slope: float, t1: int, p1: float) -> float:
        if current_time_ms < t1:
            return p1
        price = slope * (current_time_ms - t1) + p1
        return price
    
    def _determine_buy_amount(self, current_price_usd: float, krw_balance: float, price_trend: float):
        """매수 로직: 매수 트렌드 라인 기준"""
        
        deviation_percent = (current_price_usd - price_trend) / price_trend * 100.0
        
        # [수정] 오름차순 정렬 (낮은 편차부터 체크)
        sorted_levels = sorted(self.buy_levels, key=lambda x: x[0], reverse=False)

        for deviation_level, target_ratio in sorted_levels:
            if deviation_percent <= deviation_level:
                target_krw_amount = self.total_seed_krw * (target_ratio / 100.0)
                needed_krw = target_krw_amount - self.current_krw_spent

                if needed_krw > settings.MIN_TRADE_KRW_AMOUNT:
                    
                    if getattr(settings, 'IS_SIMULATION', False):
                        final_krw_amount = needed_krw
                    else:
                        final_krw_amount = min(needed_krw, krw_balance)

                    if final_krw_amount > settings.MIN_TRADE_KRW_AMOUNT:
                        print(f"  @매수 신호@ 편차 {deviation_level}% 이하 ({deviation_percent:.2f}%). 목표 {target_ratio}%. 주문액: {final_krw_amount:,.0f} KRW")
                        return final_krw_amount
                    else:
                        # 잔고 부족 등으로 실제 주문 가능 금액이 적을 때
                        print(f"  [SKIP] 매수 조건 만족했으나 KRW 잔고 부족. (주문가능액: {final_krw_amount:,.0f} < 최소주문액)")
                else:
                    # 이미 목표 비중만큼 매수했을 때
                    print(f"  [SKIP] 이미 목표 비중({target_ratio}%) 달성 완료. (추가 매수 불필요)")
                    pass        
        return 0

    def _determine_sell_amount(self, current_price_usd: float, symbol_balance: float, sell_trend_price: float, current_time_ms: int):
        """매도 로직: Stop Loss 우선 -> 유효기간 체크 -> 트렌드 라인 매도"""
        
        if symbol_balance < settings.MIN_USDT_TO_TRADE:
            return 0

        # 1. [최우선] 손절(Stop Loss) 체크
        # 평단가가 있을 때만 계산 가능
        if self.avg_buy_price > 0:
            current_profit_pct = (current_price_usd - self.avg_buy_price) / self.avg_buy_price * 100.0
            
            if current_profit_pct <= self.sell_stop_loss_ratio:
                print(f"[손절매] 수익률 {current_profit_pct:.2f}% 도달 (기준: {self.sell_stop_loss_ratio}%). 전량 매도.")
                return symbol_balance

        # 2. 매도 유효기간 체크
        # [수정] 기간 만료 시 '전량 매도'가 아니라 '매도 로직 중단(Stop Loss만 유지)'
        if not self._is_valid_time(current_time_ms, self.sell_valid_end_ms):
             # 유효기간이 지났으므로 트렌드라인 기반 매도는 하지 않음. 0 리턴.
             # (Stop Loss는 위에서 이미 체크했으므로 안전함)
             return 0

        # 3. 매도 트렌드 라인 이탈 체크 (분할 매도가 꺼져있을 때만 작동)
        # 분할 매도를 쓴다면, 이탈했다고 바로 팔지 않고 아래의 '분할 매도 플랜'을 따릅니다.
        if not self.sell_partial_enabled:
            if current_price_usd < sell_trend_price:
                 print(f"📉 [이탈 매도] 매도 추세선 하향 이탈 ({sell_trend_price:.2f} > {current_price_usd:.2f}). 전량 매도.")
                 return symbol_balance

        # 4. 분할 매도 (Partial Sell) 로직
        if self.sell_partial_enabled:
            deviation_percent = (current_price_usd - sell_trend_price) / sell_trend_price * 100.0
            
            for i, (target_deviation, target_ratio_percent) in enumerate(self.sell_plan):
                if i <= self.last_sell_step_index:
                    continue
                
                if deviation_percent >= target_deviation:
                    prev_ratio = self.sell_plan[i-1][1] if i > 0 else 0
                    current_ratio_step = target_ratio_percent - prev_ratio
                    
                    sell_amount = self.max_holdings * (current_ratio_step / 100.0)
                    sell_amount = min(sell_amount, symbol_balance)
                    
                    if sell_amount >= settings.MIN_USDT_TO_TRADE:
                        print(f"💸 [익절 신호] 매도선 편차 {target_deviation}% 돌파 ({deviation_percent:.2f}%). 비중 {current_ratio_step}% 매도.")
                        self.last_sell_step_index = i 
                        return sell_amount

        return 0

    def determine_action_and_amount(self, current_data: dict, krw_balance: float, symbol_balance: float):
        """메인 실행 함수"""
        
        price_key = f"{self.symbol.lower()}_usdt_price"
        current_symbol_price_usd = current_data.get(price_key)
        usdt_krw_price = current_data.get('usdt_krw_price')

        if current_symbol_price_usd is None or usdt_krw_price is None:
            return 'WAIT', None, 0
            
        current_time_ms = floor(time.time() * 1000)
        
        # 포지션 최대 보유량 및 초기화 로직
        if symbol_balance > self.max_holdings:
            self.max_holdings = symbol_balance
        
        # 잔고가 없으면 상태 초기화
        if symbol_balance < settings.MIN_USDT_TO_TRADE:
            self.max_holdings = 0.0
            self.current_krw_spent = 0.0
            self.last_sell_step_index = -1
            self.avg_buy_price = 0.0 # 평단가 초기화

        # =========================================================
        # 1. 매도(Sell) 로직 실행
        # =========================================================
        sell_trend_price = self._calculate_trendline_price(current_time_ms, self.sell_slope, self.sell_t1, self.sell_p1)

        # 💡 [모니터링] 매도 라인 상태 출력 (포지션이 있을 때만)
        if symbol_balance >= settings.MIN_USDT_TO_TRADE:
            sell_dev_percent = (current_symbol_price_usd - sell_trend_price) / sell_trend_price * 100.0
            print(f"  [매도 감시] 기준가: ${sell_trend_price:,.2f} | 현재가: ${current_symbol_price_usd:,.2f} | 편차: {sell_dev_percent:+.2f}%")

        sell_amount = self._determine_sell_amount(current_symbol_price_usd, symbol_balance, sell_trend_price, current_time_ms)
        
        if sell_amount > 0:
            self.is_buying_disabled = True
            return 'SELL', self.symbol, sell_amount

        # =========================================================
        # 2. 매수(Buy) 로직 실행
        # =========================================================
        if self.is_buying_disabled:
            return 'WAIT', None, 0
        
        if not self._is_valid_time(current_time_ms, self.buy_valid_end_ms):
             return 'WAIT', None, 0

        buy_trend_price = self._calculate_trendline_price(current_time_ms, self.buy_slope, self.buy_t1, self.buy_p1)

        # [모니터링] 매수 라인 - 💡 여기 하나만 출력됩니다 (중복 방지)
        buy_dev_percent = (current_symbol_price_usd - buy_trend_price) / buy_trend_price * 100.0
        print(f"  @매수 감시@ 기준가: ${buy_trend_price:,.2f} | 현재가: ${current_symbol_price_usd:,.2f} | 편차: {buy_dev_percent:+.2f}%")

        krw_to_buy = self._determine_buy_amount(current_symbol_price_usd, krw_balance, buy_trend_price)

        if krw_to_buy > 0:
            # [추가] 평단가 갱신 로직 (USD 기준)
            # 대략적인 매수 수량 계산 (수수료 제외 단순 계산)
            # 환율 적용: KRW 매수액 -> USD 가치
            buy_usd_value = krw_to_buy / usdt_krw_price
            approx_buy_qty = buy_usd_value / current_symbol_price_usd
            
            total_qty = symbol_balance + approx_buy_qty
            if total_qty > 0:
                # 가중 평균: (기존총액USD + 신규매수액USD) / 총수량
                old_value_usd = symbol_balance * self.avg_buy_price
                self.avg_buy_price = (old_value_usd + buy_usd_value) / total_qty

            self.current_krw_spent += krw_to_buy 
            return 'BUY', 'KRW', krw_to_buy
        
        return 'WAIT', None, 0