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
        """USDT 또는 BTC 등 특정 코인과 KRW 잔고를 조회합니다."""
        try:
            balances = self.upbit_api.upbit.get_balances() 
            symbol_balance = 0.0
            krw_balance = 0.0
            
            for balance in balances:
                currency = balance['currency']
                # 주문 중인 금액(locked)까지 포함하여 총 잔고 계산
                total_balance = float(balance['balance']) + float(balance['locked'])
                
                if currency == ticker:
                    symbol_balance = total_balance
                elif currency == 'KRW':
                    krw_balance = total_balance
            
            return symbol_balance, krw_balance
        
        except Exception as e:
            print(f"[ERROR] 잔고 조회 중 예외 발생: {e}")
            return 0.0, 0.0

    def execute_market_order(self, action: str, amount: float, symbol: str):
        """
        시장가 주문을 실행합니다.
        
        :param action: 'BUY' 또는 'SELL'
        :param amount: 매수 시에는 '원화 금액(KRW)', 매도 시에는 '매도 수량(Coin Volume)'
        :param symbol: 매매할 코인 (USDT, BTC 등)
        """
        ticker = f"KRW-{symbol}"
        
        # 1. 시뮬레이션 모드 확인 (최우선)
        # settings.py의 IS_SIMULATION이 True이면 실제 주문을 넣지 않음
        if getattr(settings, 'IS_SIMULATION', False):
            target_unit = "KRW" if action == "BUY" else symbol
            print(f"  @🚨EXECUTE@ {action} {symbol} 주문 (가상): {amount:,.0f} {target_unit} 상당")
            return {"uuid": "SIMULATED_ORDER_UUID", "state": "done"}

        # 2. API 키 미설정 확인 (이중 안전장치)
        if settings.UPBIT_ACCESS_KEY == "YOUR_UPBIT_ACCESS_KEY":
            target_unit = "KRW" if action == "BUY" else symbol
            print(f"  @⚠️WARNING@ API 키 미설정. {action} {symbol} 주문 시뮬레이션 처리: {amount:,.0f} {target_unit}")
            return {"uuid": "SIMULATED_ORDER_UUID", "state": "done"}

        # 3. 실제 주문 실행
        try:
            if action == 'BUY':
                # 매수: 금액(KRW) 기준 시장가 매수
                result = self.upbit_api.upbit.buy_market_order(ticker, amount)
                print(f"[ORDER] 🚨 {symbol} 실제 매수 주문 실행. 금액: {amount:,.0f} KRW.")
                return result
            
            elif action == 'SELL':
                # 매도: 수량(Volume) 기준 시장가 매도
                result = self.upbit_api.upbit.sell_market_order(ticker, amount)
                print(f"[ORDER] 🚨 {symbol} 실제 매도 주문 실행. 수량: {amount:,.8f} {symbol}.")
                return result
            
            else:
                print(f"[ERROR] 알 수 없는 주문 액션: {action}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 주문 실행 중 오류 발생 ({action} {symbol}): {e}")
            return None