from connectors.upbit_api import UpbitAPI
from config import settings

class OrderManager:
    """
    자산 조회, 매수/매도 주문 실행 등 거래소와의 상호작용을 관리합니다.
    """
    
    def __init__(self, upbit_api: UpbitAPI):
        self.upbit_api = upbit_api
        print("✅ OrderManager 초기화 완료")

    def get_current_balance(self, ticker="USDT"):
        """
        특정 코인(USDT)과 원화(KRW)의 현재 잔고를 조회합니다.
        
        :return: (USDT 잔고, KRW 잔고) 튜플
        """
        try:
            # UpbitAPI 인스턴스를 통해 pyupbit의 get_balances 호출
            balances = self.upbit_api.upbit.get_balances() 
            
            usdt_balance = 0.0
            krw_balance = 0.0
            
            for balance in balances:
                currency = balance['currency']
                # 잔고와 잠겨있는 잔고(주문 중)를 합산하여 총 잔고 계산
                total_balance = float(balance['balance']) + float(balance['locked'])
                
                if currency == ticker:
                    usdt_balance = total_balance
                elif currency == 'KRW':
                    krw_balance = total_balance
            
            return usdt_balance, krw_balance
        
        except Exception as e:
            print(f"[ERROR] 잔고 조회 중 예외 발생: {e}")
            return 0.0, 0.0

    def execute_market_order(self, action: str, amount_krw: float, usdt_balance: float):
        """
        시장가 주문을 실행합니다. (USDT/KRW 마켓)
        
        :param action: 'BUY' 또는 'SELL'
        :param amount_krw: 매수 시 사용할 원화 금액
        :param usdt_balance: 매도 시 사용할 USDT 수량
        :return: 주문 결과 (dict)
        """
        ticker = "KRW-USDT"
        
        # ⚠️ 주문 실행 대신 로그를 출력하도록 구현합니다. 실제 투입 시 주석 해제 필요!
        if settings.UPBIT_ACCESS_KEY == "YOUR_UPBIT_ACCESS_KEY":
            print(f"[SIMULATION] {action} 주문: {action} {amount_krw:,.0f} KRW 상당 USDT (잔고: {usdt_balance:.4f})")
            return {"uuid": "SIMULATED_ORDER_UUID", "state": "done"}

        if action == 'BUY':
            # 매수: 원화 마켓에서는 amount_krw 만큼의 시장가 매수
            # 리턴 값은 pyupbit.buy_market_order의 결과 (주문 UUID, 상태 등 포함)
            result = self.upbit_api.upbit.buy_market_order(ticker, amount_krw)
            print(f"[ORDER] USDT 매수 주문 실행. 금액: {amount_krw:,.0f} KRW. 결과: {result.get('uuid')}")
            return result
        
        elif action == 'SELL':
            # 매도: 보유한 USDT 전량을 시장가 매도
            # 수량은 usdt_balance를 사용
            result = self.upbit_api.upbit.sell_market_order(ticker, usdt_balance)
            print(f"[ORDER] USDT 전량 매도 주문 실행. 수량: {usdt_balance:.4f}. 결과: {result.get('uuid')}")
            return result
        
        else:
            print("[INFO] 유효하지 않은 주문 요청입니다.")
            return None