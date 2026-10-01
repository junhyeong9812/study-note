# network/51-email-delivery-and-authentication — 정답

## 정답

### 1. 전달 경로와 두 발신자

```text
  [앱] --제출(SMTP submission)--> [발신 MTA / ESP]
                                       | dig MX gmail.com
                                       v
                                  [Gmail MX]  --검사--> [메일함]
     SMTP 대화:
       MAIL FROM:<bounce@esp.example>    <- 봉투 발신자 (RFC5321.MailFrom). 반송이 오는 곳
       RCPT TO:<user@gmail.com>
       DATA
         From: news@example.com           <- 헤더 발신자 (RFC5322.From). 사용자가 보는 곳
         Subject: ...
```

- 봉투 주소는 SMTP 명령에, `From:` 헤더는 `DATA` 안의 메시지에 실린다(RFC 5321 §3.3).

### 2. 세 기술의 질문

- SPF: "이 접속 IP가 이 도메인 이름으로 보내도 되나?" 검사 대상은 봉투 `MAIL FROM` 도메인이다(없으면 HELO)(RFC 7208 §2.4).
- DKIM: "`d=` 도메인이 서명했고 서명된 헤더·본문이 그대로인가?"
- DMARC: "SPF 또는 DKIM의 pass가 `From:` 헤더 도메인과 정렬됐나?" 기준은 사용자가 보는 `From:` 도메인이다.

### 3. 정렬 실패 예측

- DMARC **fail**이다.
  - SPF pass의 도메인은 esp-mail.net이고 DKIM pass의 도메인도 esp-mail.net이다.
  - `From:` 도메인 example.com과 조직 도메인이 달라 둘 다 정렬되지 않았다.
- 고치는 법(하나만 해도 통과)
  - ESP가 `d=example.com`으로 DKIM 서명하게 한다(권장 — 전달에도 강하다).
  - 반송 도메인을 `bounce.example.com`처럼 내 도메인으로 바꾼다. 그 도메인 SPF에 ESP를 허용한다.

### 4. SPF 조회 한도

- `include`, `a`, `mx`, `ptr`, `exists`, `redirect`는 DNS 조회를 부른다. 평가 중 이 항목 수가 **10**을 넘으면 안 된다(MUST, RFC 7208 §4.6.4).
- 중첩된 include 안의 항목도 합산된다.
- 넘으면 결과는 **`permerror`**다. DMARC 관점에서 SPF가 pass가 아니게 된다. 정렬된 DKIM이 없으면 DMARC도 실패한다.

### 5. DKIM 키 회전 순서

1. 새 키쌍을 만들고 새 셀렉터로 공개키를 게시한다(`new._domainkey.example.com`).
2. DNS 전파를 기다린다(TTL 이상).
3. 발송 서버의 서명을 새 셀렉터로 전환한다.
4. 옛 셀렉터로 서명된 메일이 더는 검증되지 않을 때까지 기다린다. 재시도 큐는 수 일 걸릴 수 있다(RFC 5321 §4.5.4.1 — 포기 시간은 일반적으로 최소 4~5일).
5. 옛 키는 레코드를 지우거나 `p=`를 비워 폐기를 표시한다(빈 `p=` = 폐기, RFC 6376 §3.6.1).

- 옛 레코드를 먼저 지우면 옛 서명 메일이 전부 `dkim=fail`이 된다. SPF가 정렬되지 않은 경로라면 DMARC 실패로 거절된다.

### 6. 451 vs 550

- `451`(4yz): 일시 실패다. 백오프를 두고 재시도한다. RFC 5321은 간격 최소 30분(SHOULD), 포기까지 일반적으로 최소 4~5일이라고 적는다(§4.5.4.1).
- `550`(5yz): 영구 실패다. 같은 요청을 그대로 반복하지 않는다(SHOULD NOT, §4.2.1).
  - 확장 코드가 `5.1.1`(없는 사용자) 같은 주소 문제면 **억제 목록**에 넣는다.
  - `5.7.x`(예: `5.7.26` DMARC 거절)는 정책·인증 거절이다(RFC 3463 §3.8). 주소는 멀쩡하니 억제하지 말고 발신 설정을 고친다.
- 틀렸을 때의 피해
  - 주소 문제 5xx를 재시도하면 없는 주소로 반복 발송한다. 수신 측 평판 점수가 떨어져 정상 메일까지 스팸함으로 간다.
  - 4xx를 영구 실패로 처리하면 일시 장애 때 멀쩡한 주소를 잃는다.
  - `5.7.x` 정책 거절을 억제 목록에 넣으면, 설정을 고친 뒤에도 멀쩡한 수신자에게 영영 보내지 않게 된다.

### 7. 대량 발송자 요건 (Gmail, 하루 5,000통 이상)

- 인증·정렬
  - SPF **그리고** DKIM.
  - DMARC 레코드 게시(`p=none` 허용).
  - `From:` 도메인이 SPF 또는 DKIM 도메인과 정렬.
- 수신 거부: 마케팅·구독 메일은 원클릭 수신 거부. Yahoo는 요청을 2일 안에 반영할 것을 요구한다.
- 그 밖에 스팸률 0.30% 미만, PTR, TLS.
- 헤더 두 개(RFC 8058)
  - `List-Unsubscribe: <https://...>`
  - `List-Unsubscribe-Post: List-Unsubscribe=One-Click`
- DKIM 조건: 두 헤더가 유효한 DKIM 서명의 `h=` 목록에 포함돼야 한다(MUST, §4).

### 8. 전달과 SPF·DKIM

- 전달 서버가 메일을 다시 보낼 때 **접속 IP가 전달 서버 IP**로 바뀐다.
  - 봉투 `MAIL FROM`이 원래 도메인 그대로면, 그 도메인 SPF에 전달 서버 IP가 없어 SPF가 실패한다.
- DKIM은 메시지 헤더·본문에 붙은 서명이다.
  - 전달 서버가 서명된 헤더나 본문을 바꾸지 않으면 그대로 검증된다.
  - 단, 메일링 리스트처럼 제목에 태그를 붙이거나 본문 끝에 문구를 붙이면 DKIM도 깨진다.
- 그래서 DMARC 통과는 DKIM 정렬에 기대는 편이 안정적이다.

### 9. SPF는 pass인데 DMARC fail

- SPF pass의 도메인(esp.example)은 `From:`(example.com)과 정렬되지 않는다. 정렬된 DKIM pass가 필요했는데 DKIM이 fail이다.
- DKIM이 실패하는 가능한 원인
  - 셀렉터 공개키가 DNS에 없다. 회전 중 삭제했거나 오타가 있다.
  - 게시된 키와 서명 키가 다르다.
  - 중간에서 서명된 헤더·본문이 바뀌었다. `simple` 정규화라면 공백 변경에도 깨진다.
- 확인 명령
  - `dig +short TXT <s값>._domainkey.<d값>` — 서명 헤더의 `s=`·`d=` 값으로 조회한다.
  - `dig +short TXT _dmarc.example.com`
