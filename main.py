from connectors.upbit_api import UpbitAPI
from connectors.external_data import ExternalData
from execution.order_manager import OrderManager
from strategies.USDT_kimchipremium import KimchiPremiumStrategy
from config import settings
import time
import datetime

def main_loop():
    """자동매매 프로그램의 메인 실행 루프입니다."""
    print("-" * 50)
    print("🤖 김치 프리미엄 그리드 자동매매 프로그램 시작")
    print("-" * 50)

    # 1. 모듈 초기화
    try:
        upbit_conn = UpbitAPI()
        external_conn = ExternalData()
        order_mgr = OrderManager(upbit_conn)
        strategy = KimchiPremiumStrategy()
    except Exception as e:
        print(f"[FATAL] 초기화 중 심각한 오류 발생: {e}")
        return

    while True:
        start_time = time.time()
        
        try:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{now}] === 모니터링 시작 === ")

            # 2. 데이터 수집
            usdt_price = upbit_conn.get_usdt_krw_price()
            if usdt_price is None:
                print("[SKIP] USDT 가격 수집 실패. 다음 루프 대기.")
                time.sleep(settings.MONITORING_INTERVAL_SEC)
                continue

            # 3. 김프 계산
            kimchi_premium = external_conn.calculate_kimchi_premium(usdt_price)
            if kimchi_premium is None:
                print("[SKIP] 김치 프리미엄 계산 실패. 다음 루프 대기.")
                time.sleep(settings.MONITORING_INTERVAL_SEC)
                continue
            
            # 💡 김프값 출력 추가
            print(f"  [현재 김프] {kimchi_premium:.4f}%") 

            # 4. 잔고 조회
            usdt_balance, krw_balance = order_mgr.get_current_balance("USDT")
            print(f"  [자산 현황] KRW 잔고: {krw_balance:,.0f}원 | USDT 보유 수량: {usdt_balance:.4f}")

            # 5. 전략 판단
            action, amount_type, amount_value = strategy.determine_action_and_amount(
                kimchi_premium, usdt_balance, krw_balance, usdt_price
            )

            # 6. 주문 실행
            if action == 'BUY' and amount_type == 'KRW':
                krw_to_buy = amount_value
                
                # 최종 매수 실행
                order_mgr.execute_market_order('BUY', krw_to_buy, 0)
                
            elif action == 'SELL' and amount_type == 'USDT':
                usdt_to_sell = amount_value
                
                # 매도 수량이 현재 잔고를 초과할 수 없으므로, 현재 잔고 내에서 매도 실행
                final_usdt_amount = min(usdt_to_sell, usdt_balance)
                
                if final_usdt_amount > settings.MIN_USDT_TO_TRADE:
                    order_mgr.execute_market_order('SELL', 0, final_usdt_amount)
                else:
                    print(f"[WAIT] 매도 신호 발생했지만, USDT 잔고 부족 ({usdt_balance:.4f}).")
            
            else:
                print("[WAIT] 매매 기준 미달 또는 이미 포지션 보유 중. 대기합니다.")

            # 7. 다음 루프 대기 시간 계산
            end_time = time.time()
            elapsed_time = end_time - start_time
            sleep_time = max(0, settings.MONITORING_INTERVAL_SEC - elapsed_time)
            
            print(f"  [대기] {int(elapsed_time):d}초 소요. 다음 모니터링까지 {int(sleep_time):d}초 대기...")
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n👋 사용자 요청으로 프로그램 종료.")
            break
        except Exception as e:
            print(f"[FATAL] 루프 실행 중 예상치 못한 오류 발생: {e}")
            time.sleep(settings.MONITORING_INTERVAL_SEC)
            
if __name__ == "__main__":
    main_loop()