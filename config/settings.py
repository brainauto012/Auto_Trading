import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드
load_dotenv()

# --- 1. API KEY 설정 ---
# os.environ.get()을 사용하여 .env 파일의 값을 가져옵니다.
UPBIT_ACCESS_KEY = os.environ.get("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.environ.get("UPBIT_SECRET_KEY")

BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY")

EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY")


# --- 2. 매매 전략 기본 상수 ---
# 모든 전략에서 공통으로 사용되는 값
MONITORING_INTERVAL_SEC = 30  # 가격 조회 및 매매 로직 실행 주기 (30초)
TRADING_FEE_RATE = 0.0005     # 거래소 수수료율 (업비트 0.05% = 0.0005)

# --- 3. 매매 전략 기준 설정 ---

# ⚠️ USDT 매매에 사용할 총 시드머니 (원화 기준)
TOTAL_TRADE_SEED_KRW = 1_000_000 
# 실제 매매 시에는 이 금액을 기준으로 분할 매수 금액이 계산됩니다.

# USDT 매수 분할 기준 (김프 % 및 비중)
# [김프 기준 (%), 총 시드 대비 목표 비중 (%)]
KIMP_BUY_LEVELS = [
    (1.5, 15),  # 김프 1.5% 이하일 때 시드의 15%까지 매수
    (1.0, 35),  # 김프 1.0% 이하일 때 시드의 35%까지 매수
    (0.5, 60),  # 김프 0.5% 이하일 때 시드의 60%까지 매수
    (0.0, 85),  # 김프 0.0% 이하일 때 시드의 85%까지 매수
    (-1.0, 100),# 김프 -1.0% 이하일 때 시드의 100%까지 매수
]

# USDT 매도 분할 기준 (김프 % 및 비중)
# [김프 기준 (%), 총 잔고 대비 목표 매도 비중 (%)]
KIMP_SELL_LEVELS = [
    (3.0, 15),      # 김프 3.0% 이상일 때 총 잔고의 15%까지 매도 
    (3.5, 30),      # 김프 3.5% 이상일 때 총 잔고의 30%까지 매도 
    (4.0, 50),      # 김프 4.0% 이상일 때 총 잔고의 50%까지 매도 
    (4.5, 75),      # 김프 4.5% 이상일 때 총 잔고의 75%까지 매도 
    (5.0, 100),     # 김프 5.0% 이상일 때 총 잔고의 100%까지 매도 
]

# --- 4. 최소 주문 및 잔고 설정 (필수 추가) ---

# USDT 매수/매도 시, 최소한 이 수량 이상의 USDT를 보유해야 매도 주문을 실행합니다.
MIN_USDT_TO_TRADE = 1.0

# 매수 신호 발생 시, 최소한 이 금액(원화) 이상이어야 매매 주문을 실행합니다.
# (업비트 최소 주문 금액은 5,000 KRW이나, 안전을 위해 10,000 KRW로 설정)
MIN_TRADE_KRW_AMOUNT = 10000 

# 매도 기준 초기화 트리거 (매수 후 김프가 이 값을 넘었을 때 잔고 100% 기준을 확정)
SELL_BASE_RESET_THRESHOLD = 2.5 
# ----------------------------------------------------


# --- 4. 데이터 캐싱 및 API 제한 관련 설정 ---
# 환율 API의 최소 갱신 주기 설정 (예: 15분 = 900초)
# 무료 플랜의 '24시간 주기 업데이트'를 가정하면 이 값을 86400으로 설정해야 하지만,
# 실전 매매를 위해 분 단위 캐싱(900초/15분)을 우선 적용합니다.
MIN_FETCH_INTERVAL_SEC = 900