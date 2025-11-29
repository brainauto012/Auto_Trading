import pyupbit
from config import settings # settings.py에서 API 키를 가져오기 위함

class UpbitAPI:
    """
    업비트(Upbit) API와 상호작용하는 클래스입니다.
    데이터 조회, 주문 실행 등 모든 Upbit 관련 기능을 통합 관리합니다.
    """
    
    def __init__(self):
        """
        API 키를 사용하여 pyupbit 객체를 초기화합니다.
        실제 주문 기능 사용 시 settings.py의 키를 사용합니다.
        """
        self.upbit = pyupbit.Upbit(settings.UPBIT_ACCESS_KEY, settings.UPBIT_SECRET_KEY)
        print("✅ UpbitAPI 초기화 완료")


    def get_usdt_krw_price(self):
        """
        업비트의 KRW-USDT 마켓 현재 가격을 조회합니다. (데이터 수집)
        
        :return: 현재 KRW-USDT 가격 (float) 또는 조회 실패 시 None
        """
        ticker = "KRW-USDT"
        try:
            # pyupbit.get_current_price는 인증 없이도 사용 가능
            price = pyupbit.get_current_price(ticker) 
            
            if price is None:
                print(f"[ERROR] Upbit {ticker} 가격 조회 실패: None 반환")
                return None
            
            # print(f"[INFO] Upbit KRW-USDT 가격: {price:,.2f} KRW")
            return price
        
        except Exception as e:
            print(f"[ERROR] Upbit 가격 조회 중 예외 발생: {e}")
            return None

    # (향후 추가될 기능: get_balance, buy_market_order, sell_market_order 등)
    
    # 예시를 위해 현재는 USDT 가격 조회만 구현
    pass

if __name__ == "__main__":
    # 이 파일 단독 테스트용 코드 (main.py에서 import하여 사용될 예정)
    upbit_connector = UpbitAPI()
    usdt_price = upbit_connector.get_usdt_krw_price()
    if usdt_price:
        print(f"테스트 결과: 현재 KRW-USDT 가격은 {usdt_price:,.2f} KRW 입니다.")