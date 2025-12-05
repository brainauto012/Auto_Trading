# 파일명: main.py
import time
import datetime
from config import settings
from connectors.upbit_api import UpbitAPI
from connectors.external_data import ExternalData
from execution.order_manager import OrderManager
# 💡 모든 전략 import
from strategies.USDT_kimchipremium import KimchiPremiumStrategy
from strategies.TrendlineStrategy import TrendlineStrategy

def get_strategy_class(strategy_type):
    if strategy_type == "KIMP_GRID":
        return KimchiPremiumStrategy
    elif strategy_type == "TRENDLINE":
        return TrendlineStrategy
    return None

def fetch_all_data(upbit_conn, external_conn) -> dict:
    data = {}
    
    # 1. 공통 데이터 (USDT, 환율, 김프)
    data['usdt_price'] = upbit_conn.get_usdt_krw_price()
    data['usdt_krw_price'] = external_conn.get_usd_krw_exchange_rate() 
    data['kimchi_premium'] = external_conn.calculate_kimchi_premium(data['usdt_price'])

    # 2. 전략별 필요 데이터 자동 수집 (동적 할당)
    # settings에 정의된 활성 전략들에서 symbol을 추출 (중복 제거를 위해 set 사용)
    target_symbols = set()
    for strategy_conf in settings.STRATEGY_LIST:
        # 활성화된 전략이고, 외부 데이터(바이낸스)가 필요한 전략(Trendline 등)인 경우
        if strategy_conf.get('is_active') and strategy_conf.get('symbol') != "USDT":
            target_symbols.add(strategy_conf['symbol'])
    
    # 추출된 종목들의 바이낸스 가격 조회
    for symbol in target_symbols:
        # 바이낸스 심볼 형식: BTC -> BTCUSDT
        binance_symbol = f"{symbol.upper()}USDT"
        price = external_conn.get_binance_price(binance_symbol)
        
        # 전략 파일이 기대하는 키 형식: BTC -> btc_usdt_price
        key_name = f"{symbol.lower()}_usdt_price"
        data[key_name] = price

    return data

def main_loop():
    """자동매매 프로그램의 메인 실행 루프입니다."""
    print("-" * 50)
    print("🤖 자동매매 프로그램 시작")
    print("-" * 50)

    # 1. 모듈 초기화
    try:
        upbit_conn = UpbitAPI()
        external_conn = ExternalData()
        order_mgr = OrderManager(upbit_conn)
        
        active_strategies = []
        for config in settings.STRATEGY_LIST:
            if config.get("is_active"):
                StrategyClass = get_strategy_class(config["strategy_type"])
                if StrategyClass:
                    active_strategies.append(StrategyClass(config))
                
    except Exception as e:
        print(f"[FATAL] 초기화 중 심각한 오류 발생: {e}")
        return

    while True:
        start_time = time.time()
        
        try:
            # 1. 시간 출력 및 모니터링 시작
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{now}] === 모니터링 시작 (활성 전략: {len(active_strategies)}개) === ")

            # 2. 모든 데이터 수집
            current_data = fetch_all_data(upbit_conn, external_conn)
            
            # 3. 잔고 조회 
            usdt_balance, krw_balance = order_mgr.get_current_balance("USDT")
            btc_balance, _ = order_mgr.get_current_balance("BTC")
            
            # 4. 각 전략 실행 및 주문 판단
            for strategy in active_strategies:
                print(f"\n[🔍 {strategy.name} ({strategy.symbol})] 분석 시작")
                
                # 심볼에 따라 사용할 잔고 결정
                symbol_balance = usdt_balance if strategy.symbol == "USDT" else btc_balance
                
                # 전략 실행 및 매매 신호 수신
                action, amount_type, amount_value = strategy.determine_action_and_amount(
                    current_data, krw_balance, symbol_balance
                )
                
                # 5. 주문 실행
                if action in ['BUY', 'SELL'] and amount_value > 0:
                    # OrderManager 호출 (USDT, BTC 모두 처리 가능)
                    order_mgr.execute_market_order(action, amount_value, symbol=strategy.symbol) 

            # 6. 다음 루프 대기 시간 계산 (정상 실행 시 대기)
            end_time = time.time()
            elapsed_time = end_time - start_time
            sleep_time = max(0, settings.MONITORING_INTERVAL_SEC - elapsed_time)
            
            print(f".................")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n👋 사용자 요청으로 프로그램 종료.")
            break
        except Exception as e:
            print(f"[FATAL] 루프 실행 중 예상치 못한 오류 발생: {e}")
            time.sleep(settings.MONITORING_INTERVAL_SEC)
            
if __name__ == "__main__":
    main_loop()