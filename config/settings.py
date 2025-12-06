# 파일명: config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- 0. 시뮬레이션 모드 설정 ---
# True: 실제 주문을 넣지 않고 로그만 출력 (테스트용)
# False: 실제 거래소 주문 실행 (실전용)
IS_SIMULATION = False

# --- 1. API KEY 설정 (API 키는 .env 파일에서 로드) ---
UPBIT_ACCESS_KEY = os.environ.get("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.environ.get("UPBIT_SECRET_KEY")
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY")
EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY")
EXCHANGE_RATE_URL = os.environ.get("EXCHANGE_RATE_URL")

# --- 2. 공통 설정 ---
MONITORING_INTERVAL_SEC = 60  # 가격 조회 및 매매 로직 실행 주기
MIN_TRADE_KRW_AMOUNT = 10000  # 최소 주문 금액 (KRW)
MIN_USDT_TO_TRADE = 1.0       # 최소 주문 수량 (USDT/BTC 등)

# --- 3. 통합 전략 리스트 (GUI/DB 대체) ---
STRATEGY_LIST = [
    {
        "name": "USDT_Kimp_Grid_V1",
        "is_active": True,
        "exchange": "UPBIT",
        "symbol": "USDT",
        "strategy_type": "KIMP_GRID",
        "params": {
            "TOTAL_TRADE_SEED_KRW": 2_000_000,
            # 분할 매수 레벨 [USDT 김프 레벨 (%), 총 시드 대비 목표 비중 %]
            "BUY_LEVELS": [
                (1.5, 20), 
                (1.0, 40), 
                (0.5, 60), 
                (0.0, 80), 
                (-1.0, 100),
            ],
            # 분할 매도 레벨 [USDT 김프 레벨 (%), 총 잔고 대비 목표 비중 %]
            "SELL_LEVELS": [
                (2.5, 20), 
                (3.0, 40), 
                (3.5, 60), 
                (4.5, 80), 
                (5.0, 100),
            ],
            # 총 잔고 확정 Threshold
            "SELL_BASE_RESET_THRESHOLD": 2.0,
        }
    },

    {
        "name": "BTC_Trendline_Buy_V1",
        "is_active": False,
        "exchange": "UPBIT",  # 주문은 업비트에서 하지만, 가격은 바이낸스(EXTERNAL) 참조
        "symbol": "BTC",
        "strategy_type": "TRENDLINE",
        "params": {
            "TOTAL_TRADE_SEED_KRW": 1_000_000,
            # ========================================================
            # ✨ 매수 전략 설정
            # ========================================================
            # 매수 트렌드 라인 설정 (매수 시점 기준점)
            "BUY_TRENDLINE_START_DATE":         "2025-01-20", 
            "BUY_TRENDLINE_START_PRICE_USD":    109588.0,
            "BUY_TRENDLINE_END_DATE":           "2025-05-18", 
            "BUY_TRENDLINE_END_PRICE_USD":      103126.0,
            "BUY_TRENDLINE_VALID_END_DATE":     "2026-01-01", 
            # 분할 매수 레벨 [추세선 대비 가격 편차 (%), 총 시드 대비 목표 비중 %]
            "BUY_LEVELS": [
                (0.3, 15), 
                (0.2, 30), 
                (0.0, 50), 
                (-0.2, 75), 
                (-0.3, 100),
            ],

            # ========================================================
            # ✨ 매도 전략 설정
            # ========================================================
            "SELL_PARTIAL_ENABLED": True, # 분할 매도 활성화 여부

            # 매도 트렌드 라인 설정 (매도 시점 기준점)
            "SELL_TRENDLINE_START_DATE":        "2025-01-20",
            "SELL_TRENDLINE_START_PRICE_USD":   110588.0,
            "SELL_TRENDLINE_END_DATE":          "2025-05-18",
            "SELL_TRENDLINE_END_PRICE_USD":     104126.0,
            "SELL_TRENDLINE_VALID_END_DATE":    "2026-01-01",
            
            # 분할 매도 레벨 [추세선 대비 가격 편차 (%), 총 잔고 대비 목표 비중 %]
            "SELL_PLAN": [
                (-0.2, 30),     # 추세선 기준값 대비 -2% 지점 도달시, 총 잔고의 30% 까지 매도
                (0.0, 50),      # 추세선 기준값 대비 -0% 지점 도달시, 총 잔고의 50% 까지 매도
                (0.2, 100)     # 추세선 기준값 대비 5% 지점 도달시, 총 잔고의 100% 까지 매도
            ],

            # 손절 및 트렌드 라인 이탈 시 전량 매도
            "SELL_STOP_LOSS_RATIO": -10.0, # -5% 손실 시 전량 매도
        }
    },

    {
        "name": "ETH_Trendline_Buy_V1",
        "is_active": True,
        "exchange": "UPBIT",  # 주문은 업비트에서 하지만, 가격은 바이낸스(EXTERNAL) 참조
        "symbol": "ETH",
        "strategy_type": "TRENDLINE",
        "params": {
            "TOTAL_TRADE_SEED_KRW": 3_000_000,
            # ========================================================
            # ✨ 매수 전략 설정
            # ========================================================
            # 매수 트렌드 라인 설정 (매수 시점 기준점)
            "BUY_TRENDLINE_START_DATE":         "2022-07-13", 
            "BUY_TRENDLINE_START_PRICE_USD":    1006.32,
            "BUY_TRENDLINE_END_DATE":           "2025-03-24", 
            "BUY_TRENDLINE_END_PRICE_USD":      2078.07,
            "BUY_TRENDLINE_VALID_END_DATE":     "2026-07-01", 
            # 분할 매수 레벨 [추세선 대비 가격 편차 (%), 총 시드 대비 목표 비중 %]
            "BUY_LEVELS": [
                (2.0, 20), 
                (0.0, 30), 
                (-3.0, 50), 
            ],

            # ========================================================
            # ✨ 매도 전략 설정
            # ========================================================
            "SELL_PARTIAL_ENABLED": True, # 분할 매도 활성화 여부

            # 매도 트렌드 라인 설정 (매도 시점 기준점)
            "SELL_TRENDLINE_START_DATE":        "2021-05-12",
            "SELL_TRENDLINE_START_PRICE_USD":   4372.72,
            "SELL_TRENDLINE_END_DATE":          "2025-12-04",
            "SELL_TRENDLINE_END_PRICE_USD":     6201.20,
            "SELL_TRENDLINE_VALID_END_DATE":    "2026-07-01",
            
            # 분할 매도 레벨 [추세선 대비 가격 편차 (%), 총 잔고 대비 목표 비중 %]
            "SELL_PLAN": [
                (-3.0, 30),     
                (-0.0, 70),     
                (10.0, 100)     # 추세선 기준값 대비 10% 지점 도달시, 총 잔고의 100% 까지 매도
            ],

            # 손절 및 트렌드 라인 이탈 시 전량 매도
            "SELL_STOP_LOSS_RATIO": -99.0, # -5% 손실 시 전량 매도
        }
    }
]