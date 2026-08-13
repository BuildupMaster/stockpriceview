"""토스증권(Toss Securities) Open API의 얇은 REST 클라이언트.

토스증권 공식 문서(https://developers.tossinvest.com/docs)는 이 저장소를 만든
네트워크 환경에서 직접 열람할 수 없었기 때문에, 공개된 비공식 SDK
(github.com/nbsp1221/tossinvest-openapi)가 정리해 둔 엔드포인트 경로를 기준으로
구현했습니다.

- 인증: OAuth2 Client Credentials (POST /oauth2/token) -> Bearer 토큰
- API origin: https://openapi.tossinvest.com
- 계좌 관련 호출은 X-Tossinvest-Account 헤더에 계좌 식별자(account_seq)가 필요합니다.

실제 응답 필드명은 공식 문서로 검증하지 못했으므로, normalize_* 함수들은 흔히
쓰이는 몇 가지 키 이름을 후보로 시도합니다. 실제 키로 호출한 뒤 앱 하단의
"원본 응답 디버그" 패널에서 실제 필드명을 확인하고, 다르다면 이 파일의
_pick(...) 후보 목록에 실제 키를 추가해 주세요.
"""

import time
from typing import Any, Optional

import requests

BASE_URL = "https://openapi.tossinvest.com"
TIMEOUT = 10


class TossInvestAPIError(Exception):
    pass


class TossInvestClient:
    def __init__(self, client_id: str, client_secret: str, base_url: str = BASE_URL):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self._session = requests.Session()
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def close(self):
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token
        resp = self._session.post(
            f"{self.base_url}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        self._access_token = payload["access_token"]
        self._token_expires_at = time.time() + float(payload.get("expires_in", 3600))
        return self._access_token

    def _request(
        self,
        method: str,
        path: str,
        account_seq: Optional[str] = None,
        params: Optional[dict] = None,
    ) -> Any:
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        if account_seq is not None:
            headers["X-Tossinvest-Account"] = str(account_seq)
        resp = self._session.request(
            method, f"{self.base_url}{path}", headers=headers, params=params, timeout=TIMEOUT
        )
        if not resp.ok:
            raise TossInvestAPIError(f"{method} {path} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def get_accounts(self):
        return self._request("GET", "/api/v1/accounts")

    def get_holdings(self, account_seq: str, symbol: Optional[str] = None):
        params = {"symbol": symbol} if symbol else None
        return self._request("GET", "/api/v1/holdings", account_seq=account_seq, params=params)

    def get_buying_power(self, account_seq: str, currency: str = "KRW", **extra_params):
        params = {"currency": currency, **extra_params}
        return self._request("GET", "/api/v1/buying-power", account_seq=account_seq, params=params)

    def get_prices(self, symbols: str):
        return self._request("GET", "/api/v1/prices", params={"symbols": symbols})


def _items(raw):
    if isinstance(raw, dict):
        return raw.get("data") or raw.get("items") or raw.get("accounts") or raw.get("holdings") or []
    if isinstance(raw, list):
        return raw
    return []


def _pick(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _to_number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_accounts(raw):
    accounts = []
    for item in _items(raw):
        accounts.append(
            {
                "account_seq": _pick(item, "accountSeq", "account_seq", "seq", "id"),
                "account_number": _pick(item, "accountNumber", "account_number", "number", default="-"),
                "account_name": _pick(item, "accountName", "nickname", "alias", "name", default="계좌"),
            }
        )
    return accounts


def normalize_holdings(raw):
    holdings = []
    for item in _items(raw):
        symbol = _pick(item, "symbol", "ticker", "stockCode", default="-")
        name = _pick(item, "name", "stockName", "koreanName", default=symbol)
        quantity = _to_number(_pick(item, "quantity", "qty", "holdingQuantity"))
        avg_price = _to_number(_pick(item, "avgPrice", "averagePrice", "purchasePrice"))
        current_price = _to_number(_pick(item, "currentPrice", "price", "lastPrice"))

        eval_amount = _pick(item, "evaluationAmount", "evalAmount", "marketValue")
        eval_amount = _to_number(eval_amount) if eval_amount is not None else current_price * quantity

        purchase_amount = _pick(item, "purchaseAmount", "totalPurchaseAmount", "costBasis")
        purchase_amount = _to_number(purchase_amount) if purchase_amount is not None else avg_price * quantity

        profit_loss = _pick(item, "profitLossAmount", "profitLoss", "pnl")
        profit_loss = _to_number(profit_loss) if profit_loss is not None else eval_amount - purchase_amount

        profit_loss_rate = _pick(item, "profitLossRate", "pnlRate", "returnRate")
        if profit_loss_rate is not None:
            profit_loss_rate = _to_number(profit_loss_rate)
        else:
            profit_loss_rate = (profit_loss / purchase_amount * 100) if purchase_amount else 0.0

        holdings.append(
            {
                "symbol": symbol,
                "name": name,
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": current_price,
                "eval_amount": eval_amount,
                "purchase_amount": purchase_amount,
                "profit_loss": profit_loss,
                "profit_loss_rate": profit_loss_rate,
                "currency": _pick(item, "currency", default="KRW"),
            }
        )
    return holdings


def normalize_buying_power(raw):
    if isinstance(raw, dict):
        cash = _pick(raw, "cash", "availableCash", "buyingPower", "availableAmount", default=None)
        return {
            "cash": _to_number(cash) if cash is not None else None,
            "currency": _pick(raw, "currency", default="KRW"),
        }
    return {"cash": None, "currency": "KRW"}
