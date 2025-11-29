from config import settings

class KimchiPremiumStrategy:
    """
    단계별 분할 매수/매도 (그리드) 전략 엔진입니다.
    """
    
    # ... (self.total_usdt_base_for_sell, self.total_usdt_sold, self.is_sell_base_set 등 상태 관리 변수 유지)

    def __init__(self):
        print("✅ KimchiPremiumStrategy 초기화 완료")
        
        # --- 상태 관리 변수 ---
        self.total_usdt_base_for_sell = 0.0 
        self.total_usdt_sold = 0.0 
        self.is_sell_base_set = False 

        # --- 설정값 로드 ---
        self.buy_levels = settings.KIMP_BUY_LEVELS
        self.sell_levels = settings.KIMP_SELL_LEVELS
        self.total_seed_krw = settings.TOTAL_TRADE_SEED_KRW
        self.reset_threshold = settings.SELL_BASE_RESET_THRESHOLD


    def _manage_sell_base(self, kimchi_premium: float, current_usdt_balance: float):
        """매도 시 기준이 되는 총 잔고(self.total_usdt_base_for_sell)를 관리합니다."""
        
        # 1. 매수 단계 확인 및 초기화
        if current_usdt_balance <= settings.MIN_USDT_TO_TRADE:
            # USDT가 거의 없으면 매도 포지션 관련 상태 모두 초기화
            self.total_usdt_base_for_sell = 0.0
            self.total_usdt_sold = 0.0
            self.is_sell_base_set = False
            return
            
        # 2. 매도 기준 설정 (매수 후 김프 2.5% 돌파 시)
        if not self.is_sell_base_set and kimchi_premium >= self.reset_threshold:
            self.total_usdt_base_for_sell = current_usdt_balance
            self.total_usdt_sold = 0.0 
            self.is_sell_base_set = True
            print(f"  [기준 설정] 매도 기준 김프({self.reset_threshold}%) 돌파. 총 잔고 기준: {self.total_usdt_base_for_sell:.4f} USDT로 설정.")


    def _determine_buy_amount(self, kimchi_premium: float, current_usdt_balance: float, usdt_price: float):
        """매수 로직: 현재 김프 레벨에 따라 매수해야 할 원화 금액을 계산합니다."""
        
        krw_to_buy = 0 
        
        # 1. 현재 김프 레벨 찾기 (김프가 낮아질수록 (인덱스 증가) 비중이 커집니다.)
        for kimp_level, target_ratio in self.buy_levels:
            if kimchi_premium <= kimp_level:
                # 목표 원화 금액 계산
                target_krw_amount = self.total_seed_krw * (target_ratio / 100.0)
                
                # 현재 보유 중인 USDT의 원화 가치 (현재가 기준)
                current_usdt_krw_value = current_usdt_balance * usdt_price
                
                # 모자란 금액 계산
                if current_usdt_krw_value < target_krw_amount:
                    needed_krw = target_krw_amount - current_usdt_krw_value
                    
                    # 가장 낮은 김프 레벨에서 필요한 금액을 krw_to_buy에 저장하고 즉시 종료
                    # 이 금액은 모자란 만큼 채우는 금액이 됩니다.
                    krw_to_buy = needed_krw
                    
                    print(f"  [매수 레벨] 김프 {kimp_level}% 이하 도달. 시드 목표 {target_ratio}%. 매수 필요 KRW: {needed_krw:,.0f}원")
                    return max(0, krw_to_buy) 
                
        return 0 # 매수 조건에 해당되는 레벨이 없거나, 목표 비중을 이미 초과 달성함


    # ... (_determine_sell_amount 로직은 변경 없음)


    def determine_action_and_amount(self, kimchi_premium: float, current_usdt_balance: float, krw_balance: float, usdt_price: float):
        """
        메인 진입점: 매매 행동('BUY', 'SELL', 'WAIT')과 거래할 수량(KRW 또는 USDT)을 결정합니다.
        """
        if kimchi_premium is None:
            return 'WAIT', None, 0

        # 매도 기준 잔고 관리 (매 루프마다 실행)
        self._manage_sell_base(kimchi_premium, current_usdt_balance)

        # 1. 매도 시그널 체크 (매도 기준이 설정되어 있어야 함)
        if self.is_sell_base_set:
            usdt_to_sell = self._determine_sell_amount(kimchi_premium)
            
            # 최소 거래 수량 및 실제 잔고 확인은 main.py에서 최종 처리
            if usdt_to_sell > settings.MIN_USDT_TO_TRADE:
                self.total_usdt_sold += usdt_to_sell
                return 'SELL', 'USDT', usdt_to_sell

        # 2. 매수 시그널 체크 (USDT를 팔기 위한 기준이 초기화되었을 때만 매수 가능)
        elif not self.is_sell_base_set: 
            krw_to_buy = self._determine_buy_amount(kimchi_premium, current_usdt_balance, usdt_price)
            
            # 최소 거래 금액(MIN_TRADE_KRW_AMOUNT) 이상이어야 매수 시그널 발생
            if krw_to_buy > settings.MIN_TRADE_KRW_AMOUNT:
                # 실제 KRW 잔고를 초과하지 않도록 보정
                final_krw_amount = min(krw_to_buy, krw_balance)
                
                if final_krw_amount > settings.MIN_TRADE_KRW_AMOUNT:
                    # 매수 포지션 진입 시 매도 기준 강제 초기화 (안전장치)
                    self.total_usdt_base_for_sell = 0.0
                    self.total_usdt_sold = 0.0
                    self.is_sell_base_set = False 
                    
                    return 'BUY', 'KRW', final_krw_amount
        
        return 'WAIT', None, 0