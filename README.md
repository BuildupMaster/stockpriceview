# stockpriceview

personal stock price viewer

`index.html`을 브라우저로 열면 삼성전자(005930.KS)의 정보를 보여주는 대시보드입니다.

- 현재 주가 및 전일 대비 상승률 (한국 증시 관례에 따라 상승은 빨강, 하락은 파랑)
- 52주 고가·저가 및 현재가 위치를 보여주는 범위 바
- 52주 고가/저가 대비 현재가 등락률
- 최근 배당금과 배당수익률

데이터는 별도 서버 없이 브라우저에서 Yahoo Finance 비공식 공개 API를 직접 호출해서 가져옵니다.
CORS로 직접 호출이 막히면 공개 CORS 프록시(corsproxy.io, allorigins.win)를 자동으로 순차 시도합니다.
직전에 성공한 데이터는 `localStorage`에 캐시해서, 새 요청이 모두 실패해도 마지막으로 불러온 값을 보여줍니다.

다른 종목을 보고 싶다면 `index.html` 안의 `SYMBOL` 상수 값을 원하는 티커(예: `AAPL`, `005930.KS`)로 바꾸면 됩니다.

## 사용법

별도 빌드나 설치 없이 `index.html` 파일을 브라우저로 열면 됩니다. 로컬 서버로 띄우고 싶다면:

```bash
python3 -m http.server 8000
```

이후 `http://localhost:8000` 접속.

