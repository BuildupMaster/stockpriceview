# stockpriceview

토스증권 Open API로 내 주식 계좌(보유 종목, 평가손익, 예수금)를 불러와
로컬에서 실행하는 웹 대시보드로 시각화하는 개인용 도구입니다.

API 키가 없어도 샘플(mock) 데이터로 화면과 동작을 바로 확인할 수 있습니다.

## 화면 구성

- 상단 요약: 총 평가금액 / 총 매입금액 / 총 평가손익(수익률) / 예수금
- 포트폴리오 구성 도넛 차트 (보유 종목 평가금액 비중)
- 종목별 평가손익률 막대 차트 (국내 증시 관행에 따라 이익=빨강, 손실=파랑)
- 보유 종목 상세 테이블
- (실계좌 연동 시) 원본 API 응답을 확인할 수 있는 디버그 패널

## 1. 준비

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. 토스증권 Open API 키 발급 (실계좌 연동 시)

1. 토스증권 앱 → **더보기** → **Open API** 로 이동해 이용약관에 동의하고 신청합니다.
2. 발급받은 **Client ID / Client Secret**을 확인합니다.
3. 프로젝트 루트의 `.env.example`을 복사해 `.env` 파일을 만들고 값을 채웁니다.

```bash
cp .env.example .env
# .env 파일을 열어 TOSSINVEST_CLIENT_ID / TOSSINVEST_CLIENT_SECRET 입력
```

`.env`는 `.gitignore`에 포함되어 있어 커밋되지 않습니다. **Client Secret은 절대
코드, 커밋, 캡처 화면 등에 남기지 마세요.**

키를 설정하지 않으면 앱은 자동으로 샘플 데이터 모드로 동작합니다.

## 3. 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 이 자동으로 열립니다.

## 프로젝트 구조

```
app.py                     # Streamlit 대시보드 (화면/차트)
src/toss_client.py         # 토스증권 Open API REST 클라이언트 (OAuth2 + 계좌/보유종목/예수금 조회)
src/portfolio_service.py   # 실계좌 API / 샘플 데이터를 동일한 인터페이스로 감싸는 서비스 계층
src/mock_data.py           # API 키가 없을 때 사용하는 샘플 데이터
```

## 알아두어야 할 점

- **API 필드명 검증 필요**: 이 코드를 만든 네트워크 환경에서는 토스증권 공식 문서
  (`developers.tossinvest.com`)에 직접 접근할 수 없어, 공개된 비공식 SDK가 정리한
  엔드포인트 경로(`/oauth2/token`, `/api/v1/accounts`, `/api/v1/holdings`,
  `/api/v1/buying-power`)를 기준으로 구현했습니다. 실제 키로 처음 실행했을 때
  값이 이상하게 보이면, 대시보드 하단의 "원본 API 응답 디버그" 패널에서 실제 JSON
  필드명을 확인하고 `src/toss_client.py`의 `normalize_*` 함수에 있는 후보 키
  목록에 실제 필드명을 추가해 주세요.
- **예수금(현금) 조회**: `/api/v1/buying-power`는 원래 "특정 종목을 얼마에
  매수 가능한지" 확인하는 주문 전 점검용 API로 보입니다. 계좌 총 현금과 정확히
  일치하지 않을 수 있으니 참고용으로만 사용하세요.
- **다중 통화 미지원**: 현재 버전은 원화(KRW) 보유 종목 기준으로 합계를 계산합니다.
  해외 주식을 함께 보유한 경우 총액 계산 로직을 통화별로 분리해야 합니다.
- **조회 전용**: 이 도구는 계좌 조회만 수행하며 주문(매수/매도) 기능은 포함하지
  않습니다.
- **보안**: Client Secret은 서버(로컬 실행 환경) 밖으로 나가지 않아야 합니다.
  이 대시보드를 외부에 배포/공유할 계획이라면 키 저장 방식과 접근 제어를
  다시 설계해야 합니다.
