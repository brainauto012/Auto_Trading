import requests
import json
import time # 시간 관리를 위해 time 모듈 추가
from config import settings
from config.settings import MIN_FETCH_INTERVAL_SEC

# 해외 USDT 가격을 1.0 USD로 가정 (스테이블 코인이므로)
GLOBAL_USDT_PRICE_USD = 1.0 

class ExternalData:
    """
    외부 데이터(환율 등)를 처리하고 김치 프리미엄을 계산하는 클래스입니다.
    요청 횟수 제한을 관리하기 위해 캐싱 로직을 추가했습니다.
    """

    def __init__(self):
        print("✅ ExternalData 초기화 완료")
        # 캐싱 변수 초기화
        self.cached_exchange_rate = None
        self.last_fetched_time = 0 # 마지막으로 성공적으로 요청한 Unix Time (초)
        
    def get_usd_krw_exchange_rate(self):
        """
        외부 API를 통해 실시간 USD/KRW 환율을 조회합니다.
        
        요청 횟수 제한 및 갱신 주기를 관리하기 위해 캐싱된 값을 우선 사용합니다.
        
        :return: USD/KRW 환율 (float) 또는 조회 실패 시 None
        """
        
        # 1. 갱신 주기 확인: 최소 갱신 주기가 지나지 않았으면 캐싱된 값을 반환
        current_time = time.time()
        if self.cached_exchange_rate is not None and \
           (current_time - self.last_fetched_time) < MIN_FETCH_INTERVAL_SEC:
            
            # print(f"[INFO] 환율 캐시 사용: {MIN_FETCH_INTERVAL_SEC}초 주기 미경과 ({int(current_time - self.last_fetched_time)}초 경과)")
            return self.cached_exchange_rate

        # 2. API 요청 시작 (갱신 주기가 지났거나 캐시가 없는 경우)
        api_key = settings.EXCHANGE_RATE_API_KEY
        api_url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD" 

        if "YOUR_EXCHANGE_RATE_API_KEY" in api_key:
            # 임시 값 사용 시에도 캐싱 로직을 테스트하기 위해 값을 업데이트
            exchange_rate = 1350.0 
            self.cached_exchange_rate = exchange_rate
            self.last_fetched_time = current_time
            print(f"[WARNING] API 키 누락. 임시값 {exchange_rate:,.2f}를 캐시에 저장.")
            return exchange_rate
            
        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status() 
            data = response.json()
            
            if data.get('result') == 'success' and 'KRW' in data.get('conversion_rates', {}):
                exchange_rate = data['conversion_rates']['KRW'] 
                
                # 3. 성공 시 캐시 업데이트
                self.cached_exchange_rate = exchange_rate
                self.last_fetched_time = current_time
                print(f"[SUCCESS] 환율 API 갱신 및 캐시 저장: {exchange_rate:,.2f}")
                return exchange_rate
            else:
                # 4. API 응답 오류 시: 최신 캐시 값을 사용 (프로그램 중단 방지)
                print(f"[ERROR] API 응답 오류. 캐시된 값 사용 시도.")
                return self.cached_exchange_rate if self.cached_exchange_rate is not None else None
            
        except requests.exceptions.RequestException as e:
            # 5. 통신 오류 시: 최신 캐시 값을 사용 (프로그램 중단 방지)
            print(f"[ERROR] API 통신 오류 발생: {e}. 캐시된 값 사용 시도.")
            return self.cached_exchange_rate if self.cached_exchange_rate is not None else None
        except (json.JSONDecodeError, KeyError) as e:
            # 6. 파싱 오류 시: 최신 캐시 값을 사용
            print(f"[ERROR] JSON/파싱 오류 발생: {e}. 캐시된 값 사용 시도.")
            return self.cached_exchange_rate if self.cached_exchange_rate is not None else None


    def calculate_kimchi_premium(self, upbit_usdt_krw_price: float):
        # (로직 변경 없음)
        if upbit_usdt_krw_price is None:
            return None

        # 캐싱 로직이 적용된 환율 조회 함수 호출
        exchange_rate = self.get_usd_krw_exchange_rate()
        
        if exchange_rate is None:
            # 캐시도 없고 API 요청도 실패했을 경우
            print("[ERROR] 환율 데이터 부족으로 김프 계산 불가.")
            return None

        # 해외 가격을 원화로 환산 (글로벌 USDT 가격은 1.0 USD로 가정)
        global_price_krw = GLOBAL_USDT_PRICE_USD * exchange_rate
        
        # 김치 프리미엄 계산 공식
        kimchi_premium_rate = (upbit_usdt_krw_price / global_price_krw - 1) * 100
        
        return kimchi_premium_rate

# ... (main 테스트 로직 유지)