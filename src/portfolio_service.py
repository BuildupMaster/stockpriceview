"""실제 토스증권 API와 샘플(mock) 데이터를 동일한 인터페이스로 감싸는 서비스 계층.

TOSSINVEST_CLIENT_ID / TOSSINVEST_CLIENT_SECRET 환경변수가 모두 설정되어 있으면
실제 API를 호출하고, 하나라도 비어 있으면 mock_data로 자동 전환됩니다.
"""

import os
from typing import Optional

from . import mock_data
from .toss_client import (
    TossInvestClient,
    normalize_accounts,
    normalize_buying_power,
    normalize_holdings,
)


class PortfolioService:
    def __init__(self):
        client_id = os.getenv("TOSSINVEST_CLIENT_ID")
        client_secret = os.getenv("TOSSINVEST_CLIENT_SECRET")
        self.mock_mode = not (client_id and client_secret)
        self._client: Optional[TossInvestClient] = (
            None if self.mock_mode else TossInvestClient(client_id, client_secret)
        )
        self.last_raw: dict = {}

    def get_accounts(self):
        if self.mock_mode:
            return mock_data.accounts()
        raw = self._client.get_accounts()
        self.last_raw["accounts"] = raw
        return normalize_accounts(raw)

    def get_holdings(self, account_seq):
        if self.mock_mode:
            return mock_data.holdings(account_seq)
        raw = self._client.get_holdings(account_seq)
        self.last_raw["holdings"] = raw
        return normalize_holdings(raw)

    def get_buying_power(self, account_seq):
        if self.mock_mode:
            return mock_data.buying_power(account_seq)
        raw = self._client.get_buying_power(account_seq, currency="KRW")
        self.last_raw["buying_power"] = raw
        return normalize_buying_power(raw)
