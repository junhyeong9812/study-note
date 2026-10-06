# security/21-same-origin-and-cors — 질문

## 질문

1. (경계) 출처(origin)는 무엇으로 정의되나? `https://a.com`, `https://a.com:8443`, `http://a.com`은 서로 같은 출처인가? SOP는 무엇을 막나?
2. (왜) 교차 출처 단순 요청(simple request)에서 CORS가 막는 것은 "보내기"인가 "읽기"인가? "서버 로그엔 200인데 브라우저는 CORS 에러"가 왜 생기나?
3. (연결) 이 사실이 CSRF(20번)와 어떻게 이어지나? CORS가 CSRF를 못 막는 이유를 한 문장으로.
4. (경계) `credentials: 'include'` 요청에 서버가 `Access-Control-Allow-Origin: *`로 답하면 어떻게 되나? 올바른 설정은?
5. (예측) 교차 출처 `PUT application/json` 요청을 보낸다. 브라우저는 무엇을 먼저 보내나? 서버가 그 `OPTIONS`를 `405`로 답하면 본 `PUT`은 서버에 도착하나?
6. (장애 진단) 서버가 요청 `Origin`을 검증 없이 그대로 `ACAO`로 되돌리고 `ACAC: true`를 준다. 무엇이 위험하고 어떻게 고치나?
7. (경계) SameSite(20번)와 SOP/CORS(21번)의 기준은 각각 "사이트"인가 "출처"인가? 둘은 각각 읽기·쓰기 중 무엇을 막나?
8. (장애 진단) 교차 출처 API 호출에서 CORS 에러가 난다. DevTools와 서버 로그로 "읽기 차단(단순 요청)"과 "preflight 실패"를 어떻게 구분하나?
9. (경계) 에러를 없애려 `mode: 'no-cors'`로 바꿨다. 데이터를 읽을 수 있게 되나? 응답은 어떤 상태가 되나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
