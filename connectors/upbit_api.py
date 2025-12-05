# 파일명: connectors/upbit_api.py
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
        """(레거시 지원) 업비트의 KRW-USDT 마켓 현재 가격을 조회합니다."""
        return self.get_current_price("KRW-USDT")

    def get_current_price(self, ticker):
        """
        특정 티커의 현재 가격을 조회합니다. (범용)
        
        :param ticker: 조회할 코인 티커 (예: "KRW-BTC", "KRW-USDT")
        :return: 현재 가격 (float) 또는 실패 시 None
        """
        try:
            price = pyupbit.get_current_price(ticker)
            
            if price is None:
                print(f"[ERROR] Upbit {ticker} 가격 조회 실패: None 반환")
                return None
            
            return price
        
        except Exception as e:
            print(f"[ERROR] {ticker} 가격 조회 중 예외 발생: {e}")
            return None

    def get_ohlcv(self, ticker, interval="day", count=200):
        """
        (확장 기능) 특정 티커의 캔들(OHLCV) 데이터를 조회합니다.
        향후 RSI, 빗각 자동 작도 등에 사용됩니다.
        """
        try:
            df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
            return df
        except Exception as e:
            print(f"[ERROR] OHLCV 조회 실패: {e}")
            return None

if __name__ == "__main__":
    # 테스트 코드
    api = UpbitAPI()
    print(f"USDT 가격: {api.get_current_price('KRW-USDT')}")
    print(f"BTC 가격: {api.get_current_price('KRW-BTC')}")