# network/51-email-delivery-and-authentication — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고, 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> ⚠️ 이 질문 목록은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 질문

1. (그림) 앱이 보낸 메일이 Gmail 수신자 메일함에 들기까지의 경로를 그리고, SMTP의 `MAIL FROM`과 헤더의 `From:`이 각각 어디에 실리는지 표시하라.
2. (경계) SPF, DKIM, DMARC는 각각 어떤 질문에 답하나? SPF가 검사하는 도메인과 DMARC가 기준으로 삼는 도메인은 무엇인가?
3. (예측) `From: news@example.com`, `MAIL FROM:<b@esp-mail.net>`, `DKIM d=esp-mail.net`, SPF·DKIM 모두 pass다. DMARC 결과는? 무엇을 바꾸면 통과하나?
4. (왜) SPF 레코드에 `include:`를 하나 더 넣었더니 모든 메일이 스팸함으로 갔다. 어떤 규칙에 걸렸고 결과값은 무엇인가?
5. (적용) DKIM 키를 회전하려 한다. 전량 거부 없이 하려면 어떤 순서로 해야 하나? 옛 키는 언제 어떻게 폐기하나?
6. (경계) SMTP 응답 `451`과 `550`을 받았을 때 발송 시스템은 각각 무엇을 해야 하나? 이 구분을 틀리면 어떤 장기 피해가 생기나?
7. (적용) Gmail 대량 발송자 요건 중 인증·정렬·수신 거부에 관한 것을 나열하고, 원클릭 수신 거부 헤더 두 개와 그 헤더에 걸린 DKIM 조건을 적어라.
8. (왜) 메일 전달(forwarding)을 거치면 SPF는 흔히 깨지는데 DKIM은 살아남는 경우가 많다. 이유는?
9. (장애 진단) 받은 메일의 `Authentication-Results`가 `spf=pass smtp.mailfrom=bounce@esp.example; dkim=fail; dmarc=fail header.from=example.com`이다. 가능한 원인과 확인할 DNS 명령은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
