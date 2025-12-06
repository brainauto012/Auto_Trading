# 파일명: strategies/base_strategy.py
from abc import ABC, abstractmethod
import datetime

class BaseStrategy(ABC):
    """모든 자동매매 전략의 기본 클래스입니다."""
    
    # 👇 중요: 이 __init__ 함수가 class 내부로 들여쓰기 되어 있어야 합니다.
    def __init__(self, strategy_config: dict):
        self.config = strategy_config
        self.name = strategy_config.get('name', 'Unknown Strategy')
        self.symbol = strategy_config.get('symbol', 'UNKNOWN')
        self.exchange = strategy_config.get('exchange', 'UPBIT')
        self.params = strategy_config.get('params', {})
        self.current_krw_spent = 0.0 # 자산 관리 및 수익률 계산에 필수
        
    # 날짜-밀리초 변환 헬퍼 함수
    def _convert_date_to_ms(self, date_str: str) -> int:
        try:
            dt_object = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            timestamp_sec = datetime.datetime(dt_object.year, dt_object.month, dt_object.day, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
            return int(timestamp_sec * 1000)
        except ValueError as e:
            print(f"[FATAL ERROR] 날짜 형식 오류 ({date_str}): {e}")
            return 0
    
    @abstractmethod
    def determine_action_and_amount(self, current_data: dict, krw_balance: float, symbol_balance: float):
        """
        주어진 시장 데이터와 잔고를 기반으로 매매 행동을 결정합니다.
        """
        pass