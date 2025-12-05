# 파일명: strategies/USDT_kimchipremium.py
from strategies.base_strategy import BaseStrategy
from config import settings

class KimchiPremiumStrategy(BaseStrategy):
    """
    단계별 분할 매수/매도 (그리드) 전략 엔진입니다.
    """

    def __init__(self, strategy_config: dict):
        super().__init__(strategy_config)
        
        # --- 상태 관리 변수 초기화 ---
        self.total_usdt_base_for_sell = 0.0 
        self.total_usdt_sold = 0.0 
        self.is_sell_base_set = False 

        # --- 파라미터 로드 ---
        self.buy_levels = self.params['BUY_LEVELS']
        self.sell_levels = self.params['SELL_LEVELS']
        self.total_seed_krw = self.params['TOTAL_TRADE_SEED_KRW']
        self.reset_threshold = self.params['SELL_BASE_RESET_THRESHOLD']
        
        print(f"✅ {self.name} 전략 초기화 완료 (심볼: {self.symbol})")


    def _manage_sell_base(self, kimchi_premium: float, current_usdt_balance: float):
        """매도 시 기준이 되는 총 잔고(self.total_usdt_base_for_sell)를 관리합니다."""
        
        # 1. 매수 단계 확인 및 초기화 (USDT가 거의 없으면 초기화)
        if current_usdt_balance <= settings.MIN_USDT_TO_TRADE:
            self.total_usdt_base_for_sell = 0.0
            self.total_usdt_sold = 0.0
            self.is_sell_base_set = False
            return
            
        # 2. 매도 기준 설정 (매수 후 김프가 기준치(2.5%) 돌파 시)
        if not self.is_sell_base_set and kimchi_premium >= self.reset_threshold:
            self.total_usdt_base_for_sell = current_usdt_balance
            self.total_usdt_sold = 0.0 
            self.is_sell_base_set = True
            print(f"  [기준 설정] 매도 기준 김프({self.reset_threshold}%) 돌파. 총 잔고 기준: {self.total_usdt_base_for_sell:.4f} USDT로 설정.")


    def _determine_buy_amount(self, kimchi_premium: float, current_usdt_balance: float, usdt_price: float):
        """매수 로직: 현재 김프 레벨에 따라 매수해야 할 원화 금액을 계산합니다."""
        
        krw_to_buy = 0 
        
        # 1. 현재 김프 레벨 찾기 (김프가 낮아질수록 비중이 커짐)
        for kimp_level, target_ratio in self.buy_levels:
            if kimchi_premium <= kimp_level:
                target_krw_amount = self.total_seed_krw * (target_ratio / 100.0)
                current_usdt_krw_value = current_usdt_balance * usdt_price
                
                if current_usdt_krw_value < target_krw_amount:
                    needed_krw = target_krw_amount - current_usdt_krw_value
                    krw_to_buy = needed_krw
                    
                    # 최소 주문 금액 체크는 determine_action_and_amount에서 수행
                    print(f"  [매수 레벨] 김프 {kimp_level}% 이하 도달. 시드 목표 {target_ratio}%. 매수 필요: {needed_krw:,.0f} KRW")
                    return max(0, krw_to_buy) 
                
        return 0 

    def _determine_sell_amount(self, kimchi_premium: float):
        """매도 로직: 현재 김프 레벨에 따라 매도해야 할 USDT 수량을 계산합니다."""
        
        if not self.is_sell_base_set or self.total_usdt_base_for_sell <= settings.MIN_USDT_TO_TRADE:
            return 0.0

        usdt_to_sell = 0.0
        
        # 1. 현재 김프 레벨 찾기 (김프가 높아질수록 비중이 커짐)
        for kimp_level, target_ratio in self.sell_levels:
            if kimchi_premium >= kimp_level:
                target_usdt_sold = self.total_usdt_base_for_sell * (target_ratio / 100.0)
                needed_to_sell = target_usdt_sold - self.total_usdt_sold
                
                if needed_to_sell > settings.MIN_USDT_TO_TRADE:
                    usdt_to_sell = needed_to_sell
                    print(f"  [매도 레벨] 김프 {kimp_level}% 이상 도달. 총 잔고 목표 {target_ratio}%. 매도 필요: {needed_to_sell:.4f} USDT")
                    return max(0.0, usdt_to_sell)
                
        return 0.0


    def determine_action_and_amount(self, current_data: dict, krw_balance: float, symbol_balance: float):
        """
        메인 진입점: BaseStrategy의 추상 메서드 구현
        """
        
        # 1. 데이터 추출
        kimchi_premium = current_data.get('kimchi_premium')
        usdt_price = current_data.get('usdt_price') # 업비트 현재가
        
        # 환율 정보 가져오기 (ExternalData에서 계산 시 사용된 환율 역산 가능하지만, 명시적으로 가져오는 게 좋음)
        # main.py에서 usdt_krw_price 키로 환율을 넘겨주고 있음
        exchange_rate = current_data.get('usdt_krw_price') 

        if kimchi_premium is None or usdt_price is None:
            return 'WAIT', None, 0

        # 💡 [모니터링] USDT 상태 출력 추가
        # 글로벌 기준가(KRW) 계산 = 환율 * 1.0 (USDT는 $1 고정 가정)
        global_price_krw = exchange_rate * 1.0 if exchange_rate else 0
        
        print(f"  @매수 감시@ 기준가(환율): {global_price_krw:,.2f}원 | 현재가: {usdt_price:,.0f}원 | 김프: {kimchi_premium:+.2f}%")

        current_usdt_balance = symbol_balance 

        # 2. 매도 기준 잔고 관리
        self._manage_sell_base(kimchi_premium, current_usdt_balance)

        # 3. 매도 시그널 체크
        if self.is_sell_base_set:
            usdt_to_sell = self._determine_sell_amount(kimchi_premium)
            
            if usdt_to_sell > settings.MIN_USDT_TO_TRADE:
                self.total_usdt_sold += usdt_to_sell
                return 'SELL', 'USDT', usdt_to_sell

        # 4. 매수 시그널 체크
        elif not self.is_sell_base_set: 
            krw_to_buy = self._determine_buy_amount(kimchi_premium, current_usdt_balance, usdt_price)
            
            if krw_to_buy > settings.MIN_TRADE_KRW_AMOUNT:
                final_krw_amount = min(krw_to_buy, krw_balance)
                
                if final_krw_amount > settings.MIN_TRADE_KRW_AMOUNT:
                    # 매수 진입 시 매도 기준 초기화
                    self.total_usdt_base_for_sell = 0.0
                    self.total_usdt_sold = 0.0
                    self.is_sell_base_set = False 
                    
                    return 'BUY', 'KRW', final_krw_amount
        
        return 'WAIT', None, 0