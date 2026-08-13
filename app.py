"""내 주식 계좌 대시보드 (토스증권 Open API 연동)

실행: streamlit run app.py
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from src.portfolio_service import PortfolioService

load_dotenv()

st.set_page_config(page_title="내 주식 계좌 대시보드", page_icon="📊", layout="wide")

# dataviz 팔레트: 고정 순서 카테고리 8색 + 국내 증시 관행(상승/이익=빨강, 하락/손실=파랑)
CATEGORICAL_COLORS = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
]
OTHER_COLOR = "#898781"
GAIN_COLOR = "#e34948"  # 국내 증권 관행: 상승/이익 = 빨강
LOSS_COLOR = "#2a78d6"  # 하락/손실 = 파랑


@st.cache_resource
def get_service() -> PortfolioService:
    return PortfolioService()


service = get_service()

st.title("📊 내 주식 계좌 대시보드")
st.caption("토스증권 Open API 연동 · 개인용 계좌 시각화 도구")

if service.mock_mode:
    st.info(
        "`TOSSINVEST_CLIENT_ID` / `TOSSINVEST_CLIENT_SECRET`이 설정되어 있지 않아 "
        "**샘플(mock) 데이터**로 동작 중입니다. 실제 계좌를 연동하려면 `.env` 파일에 "
        "토스증권 Open API 키를 설정한 뒤 앱을 다시 실행하세요. (자세한 방법은 README 참고)",
        icon="ℹ️",
    )

with st.sidebar:
    st.header("설정")
    st.write("모드: " + ("🧪 샘플 데이터" if service.mock_mode else "🔌 실계좌 연동"))
    if st.button("🔄 새로고침", use_container_width=True):
        get_service.clear()
        st.rerun()

    try:
        accounts = service.get_accounts()
    except Exception as e:
        st.error(f"계좌 목록을 불러오지 못했습니다: {e}")
        st.stop()

    if not accounts:
        st.warning("연동된 계좌가 없습니다.")
        st.stop()

    account_labels = {
        a["account_seq"]: f'{a.get("account_name") or "계좌"} ({a.get("account_number", "-")})'
        for a in accounts
    }
    selected_seq = st.selectbox(
        "계좌 선택", options=list(account_labels.keys()), format_func=lambda s: account_labels[s]
    )

try:
    holdings = service.get_holdings(selected_seq)
except Exception as e:
    st.error(f"보유 종목을 불러오지 못했습니다: {e}")
    st.stop()

try:
    cash = service.get_buying_power(selected_seq)
except Exception:
    cash = None

df = pd.DataFrame(holdings)

total_eval = float(df["eval_amount"].sum()) if not df.empty else 0.0
total_purchase = float(df["purchase_amount"].sum()) if not df.empty else 0.0
total_pnl = total_eval - total_purchase
total_pnl_rate = (total_pnl / total_purchase * 100) if total_purchase else 0.0
cash_amount = cash.get("cash") if cash else None

col1, col2, col3, col4 = st.columns(4)
col1.metric("총 평가금액", f"{total_eval:,.0f}원")
col2.metric("총 매입금액", f"{total_purchase:,.0f}원")
col3.metric("총 평가손익", f"{total_pnl:,.0f}원", f"{total_pnl_rate:+.2f}%")
col4.metric("예수금(현금)", f"{cash_amount:,.0f}원" if cash_amount is not None else "조회 불가")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("포트폴리오 구성")
    if df.empty:
        st.write("보유 종목이 없습니다.")
    else:
        alloc = df.sort_values("eval_amount", ascending=False).reset_index(drop=True)
        if len(alloc) > len(CATEGORICAL_COLORS):
            top = alloc.iloc[: len(CATEGORICAL_COLORS)][["name", "eval_amount"]]
            other_sum = float(alloc.iloc[len(CATEGORICAL_COLORS) :]["eval_amount"].sum())
            alloc = pd.concat(
                [top, pd.DataFrame([{"name": "기타", "eval_amount": other_sum}])], ignore_index=True
            )
            colors = CATEGORICAL_COLORS + [OTHER_COLOR]
        else:
            colors = CATEGORICAL_COLORS[: len(alloc)]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=alloc["name"],
                    values=alloc["eval_amount"],
                    hole=0.55,
                    marker=dict(colors=colors, line=dict(color="#fcfcfb", width=2)),
                    textinfo="label+percent",
                    sort=False,
                )
            ]
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=380, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("종목별 평가손익률")
    if df.empty:
        st.write("보유 종목이 없습니다.")
    else:
        bar_df = df.sort_values("profit_loss_rate")
        bar_colors = [GAIN_COLOR if v >= 0 else LOSS_COLOR for v in bar_df["profit_loss_rate"]]
        fig2 = go.Figure(
            data=[
                go.Bar(
                    x=bar_df["profit_loss_rate"],
                    y=bar_df["name"],
                    orientation="h",
                    marker_color=bar_colors,
                    text=[f"{v:+.2f}%" for v in bar_df["profit_loss_rate"]],
                    textposition="outside",
                )
            ]
        )
        rate_min = float(bar_df["profit_loss_rate"].min())
        rate_max = float(bar_df["profit_loss_rate"].max())
        pad = max(abs(rate_min), abs(rate_max), 1.0) * 0.35
        fig2.update_layout(
            margin=dict(t=10, b=10, l=40, r=40), height=380, xaxis_title="손익률(%)", yaxis_title=None
        )
        fig2.update_xaxes(range=[rate_min - pad, rate_max + pad])
        st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("보유 종목 상세")
if df.empty:
    st.write("보유 종목이 없습니다.")
else:
    display_df = df.rename(
        columns={
            "symbol": "종목코드",
            "name": "종목명",
            "quantity": "수량",
            "avg_price": "평균단가",
            "current_price": "현재가",
            "eval_amount": "평가금액",
            "purchase_amount": "매입금액",
            "profit_loss": "평가손익",
            "profit_loss_rate": "손익률(%)",
        }
    )
    ordered_cols = ["종목코드", "종목명", "수량", "평균단가", "현재가", "평가금액", "매입금액", "평가손익", "손익률(%)"]
    st.dataframe(
        display_df[ordered_cols].style.format(
            {
                "수량": "{:,.0f}",
                "평균단가": "{:,.0f}",
                "현재가": "{:,.0f}",
                "평가금액": "{:,.0f}",
                "매입금액": "{:,.0f}",
                "평가손익": "{:,.0f}",
                "손익률(%)": "{:+.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

if not service.mock_mode:
    with st.expander("🔧 원본 API 응답 디버그"):
        st.caption(
            "실제 응답 필드명이 src/toss_client.py의 normalize_* 함수가 가정한 이름과 다르다면 "
            "여기서 실제 키를 확인하고 해당 함수의 후보 키 목록에 추가하세요."
        )
        st.json(service.last_raw)
