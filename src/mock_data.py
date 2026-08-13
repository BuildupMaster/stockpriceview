"""토스증권 API 키가 없을 때 대시보드를 바로 확인할 수 있게 해주는 샘플 데이터.

실제 API 키(TOSSINVEST_CLIENT_ID / TOSSINVEST_CLIENT_SECRET)를 .env에 설정하면
이 모듈 대신 toss_client를 통해 실제 계좌 데이터를 불러옵니다.
"""

_HOLDINGS = [
    {"symbol": "005930", "name": "삼성전자", "quantity": 30, "avg_price": 68000, "current_price": 74500},
    {"symbol": "000660", "name": "SK하이닉스", "quantity": 10, "avg_price": 145000, "current_price": 198000},
    {"symbol": "035420", "name": "NAVER", "quantity": 8, "avg_price": 210000, "current_price": 189000},
    {"symbol": "035720", "name": "카카오", "quantity": 25, "avg_price": 52000, "current_price": 41500},
    {"symbol": "005380", "name": "현대차", "quantity": 12, "avg_price": 195000, "current_price": 232000},
    {"symbol": "051910", "name": "LG화학", "quantity": 5, "avg_price": 420000, "current_price": 388000},
    {"symbol": "006400", "name": "삼성SDI", "quantity": 6, "avg_price": 380000, "current_price": 401000},
]


def accounts():
    return [
        {"account_seq": "mock-1", "account_number": "123-456-789012", "account_name": "위탁종합계좌 (샘플)"},
    ]


def holdings(account_seq):
    result = []
    for h in _HOLDINGS:
        eval_amount = h["current_price"] * h["quantity"]
        purchase_amount = h["avg_price"] * h["quantity"]
        profit_loss = eval_amount - purchase_amount
        profit_loss_rate = (profit_loss / purchase_amount * 100) if purchase_amount else 0.0
        result.append(
            {
                **h,
                "eval_amount": eval_amount,
                "purchase_amount": purchase_amount,
                "profit_loss": profit_loss,
                "profit_loss_rate": profit_loss_rate,
                "currency": "KRW",
            }
        )
    return result


def buying_power(account_seq):
    return {"cash": 3_250_000, "currency": "KRW"}
