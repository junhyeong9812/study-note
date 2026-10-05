# network/51-email-delivery-and-authentication — 이메일 전달과 인증: SMTP 경로, SPF·DKIM·DMARC, 정렬, 바운스, 대량 발송자 요건 — 정리 (힌트)

## 해결하는 문제

SMTP는 1980년대 설계라 **보낸 사람을 확인하지 않는다.**\
누구나 `From: ceo@bank.example`이라고 적어 보낼 수 있다.\
받는 쪽은 두 가지를 알고 싶다.

```text
  1. 이 메일을 보낸 서버가 그 도메인의 허락을 받았나?      -> SPF
  2. 내용이 도중에 안 바뀌었고, 그 도메인이 서명했나?        -> DKIM
  3. 사용자 눈에 보이는 From 도메인과 위 결과가 같은 주인인가? -> DMARC (정렬)
```

쉬운 예: 편지 봉투의 보낸 사람 주소와 편지지 안의 서명이 다를 수 있다.\
우체국은 봉투만 보고, 받는 사람은 편지지 서명만 본다.\
사기꾼은 봉투는 자기 주소로, 편지지 서명은 은행 이름으로 쓴다.

똑같은 구조다.\
SMTP에는 **봉투 주소**(MAIL FROM)와 **편지 머리글 주소**(`From:` 헤더)가 따로 있다.\
DMARC는 "사용자가 보는 `From:` 도메인"을 기준으로 SPF·DKIM 결과를 묶는다.

실무 예:
- 회원가입 인증 메일이 Gmail 스팸함으로 간다.
- 발송 대행사(ESP)로 옮겼더니 DMARC 실패로 전량 거절된다.
- 2024년부터 Gmail·Yahoo가 대량 발송자에게 인증과 원클릭 수신 거부를 요구한다.

## 동작·원리

### 1. 전달 경로 — MUA → MSA → MTA → MX → 메일함

```text
  보내는 쪽                                              받는 쪽
  [앱/메일 클라이언트]                                    [수신자 메일함]
        | 제출 (SMTP submission, 인증)                          ^
        v                                                      |
  [발신 MTA / ESP] --- DNS: 수신 도메인 MX 조회 ---> [수신 MX 서버]
        |   SMTP (TCP 25)                                  |  검사: SPF, DKIM, DMARC, 평판
        +--- EHLO / MAIL FROM:<bounce@esp.example>  ------>|
        +--- RCPT TO:<user@gmail.com>                ------>|  <- 250 OK / 4xx / 5xx
        +--- DATA  (헤더 + 본문, From: 헤더는 여기)   ------>|
```

- 발신 MTA는 수신 도메인의 **MX 레코드**로 받을 서버를 찾는다. MX가 없으면 A/AAAA로 대신한다(RFC 5321 §5.1).
- 한 번의 전달은 세 명령이다(RFC 5321 §3.3).
  - `MAIL FROM`: 봉투 발신자(reverse-path). 반송(bounce)이 돌아갈 주소다.
  - `RCPT TO`: 봉투 수신자.
  - `DATA`: 메시지 본체. 사용자가 보는 `From:`·`Subject:` 헤더는 이 안에 있다.
- 응답 코드 첫 자리(RFC 5321 §4.2.1)
  - `2yz` 성공. `DATA` 뒤 250을 받으면 수신 서버가 전달 또는 실패 통보의 책임을 진다(§6.1).
  - `4yz` 일시 실패 — 나중에 재시도한다. 재시도 간격은 보통 최소 30분(SHOULD), 포기까지는 일반적으로 최소 4~5일이 필요하다고 적는다(§4.5.4.1).
  - `5yz` 영구 실패 — 같은 요청을 그대로 반복하지 않는다(SHOULD NOT). 그중 주소 문제(`5.1.1` 없는 사용자 등 `5.1.x`)가 **하드 바운스**다.
    - 확장 상태 코드 `5.7.x`는 보안·정책 거절이다(RFC 3463 §3.8). 예: `5.7.26` DMARC 거절. 수신 주소가 아니라 발신 설정 문제다.
- 전달 실패 통보(반송 메일)는 `MAIL FROM:<>`(빈 주소)으로 보낸다. 반송의 반송이 무한히 도는 것을 막는다.

  - *MTA(Mail Transfer Agent)*: 메일을 서버 간에 넘기는 서버다. Postfix, 발송 대행사의 서버 등.
  - *MX 레코드*: "이 도메인 메일은 이 서버가 받는다"는 DNS 레코드다. 우선순위 숫자가 붙는다.
  - *봉투(envelope)*: SMTP 명령으로 주고받는 주소. 메시지 헤더와 별개다. RFC들은 `RFC5321.MailFrom`, `RFC5322.From`으로 구분해 부른다.

### 2. SPF — "이 IP가 이 도메인 이름으로 보내도 되나"

```text
  수신 MX: 접속 IP = 198.51.100.7,  MAIL FROM:<bounce@esp.example>
     |
     v  DNS TXT 조회: esp.example
  "v=spf1 ip4:198.51.100.0/24 include:_spf.other.example -all"
     |
     +-- ip4 매치 -> pass
     +-- include: -> 그 도메인 SPF를 재귀 평가 (DNS 조회 1회 소모)
     +-- 끝까지 매치 없음 -> -all -> fail
```

- 검사 대상은 **봉투 `MAIL FROM` 도메인**(없으면 HELO)이다(RFC 7208 §2.4). 사용자가 보는 `From:`이 아니다.
- 결과는 7가지다(§2.6): `none`, `neutral`, `pass`, `fail`, `softfail`, `temperror`, `permerror`.
- **DNS 조회 10회 한도**(§4.6.4)
  - `include`, `a`, `mx`, `ptr`, `exists`, `redirect`가 DNS 조회를 부른다. 이 항목 수를 평가 중 10개로 제한해야 한다(MUST).
  - 넘으면 결과는 `permerror`다.
  - 결과가 비는 조회(void lookup)는 2회로 제한하기를 권한다(SHOULD). 넘으면 역시 `permerror`다.
- 한 도메인에 SPF 레코드가 둘 이상 선택되면 안 된다(§3.2).

### 3. DKIM — "이 도메인이 서명했고 내용이 그대로다"

```text
  발신 쪽:  헤더·본문 정규화 -> 본문 해시(bh) -> 선택한 헤더 + bh 에 개인키로 서명
  DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=example.com; s=sel2026;
                  h=from:to:subject:date; bh=...; b=...

  수신 쪽:  DNS TXT 조회  sel2026._domainkey.example.com
            "v=DKIM1; k=rsa; p=MIIBIjAN..."   <- 공개키
            -> 같은 방식으로 정규화·해시 -> 서명 검증 -> pass / fail
```

- 공개키 위치는 `<selector>._domainkey.<domain>`이다(RFC 6376 §3.1).
  - *셀렉터(selector)*: 한 도메인이 키를 여러 개 두기 위한 이름표다. 키 회전·발송 경로별 분리에 쓴다.
- 주요 태그(§3.5): `d=` 서명 도메인, `s=` 셀렉터, `h=` 서명한 헤더 목록(비어 있으면 안 됨), `bh=` 본문 해시, `b=` 서명값.
- 정규화(canonicalization, §3.4)
  - `simple`: 거의 바꾸지 않는다. 중간 서버가 공백 하나만 바꿔도 깨진다.
  - `relaxed`: 공백을 정리하고 헤더 이름을 소문자로 바꾼다. 흔한 변형에 견딘다.
  - 기본은 `simple/simple`(헤더/본문)이다.
- 알고리즘: 서명자는 `rsa-sha256`을 구현해야 하고(MUST) 그것으로 서명하기를 권한다(SHOULD)(§3.3). RFC 8463이 `ed25519-sha256`을 추가했다.
  - RFC 8463은 전환기에 RSA 서명과 Ed25519 서명을 **둘 다** 붙이는 예를 든다.
- 키 레코드의 `p=`가 비어 있으면 "이 키는 폐기됐다"는 뜻이다(§3.6.1).
- DKIM은 봉투가 아니라 **메시지 자체**에 붙는다. 그래서 전달(forwarding)을 거쳐도 본문·서명 헤더가 안 바뀌면 살아남는다.

### 4. DMARC — 정렬과 정책

```text
  From: news@example.com          <- 사용자가 보는 도메인 (Author Domain)

  SPF  : MAIL FROM = bounce@esp-mail.net      pass,  정렬? example.com != esp-mail.net  -> X
  DKIM : d=example.com                          pass,  정렬? example.com == example.com   -> O
                                                              |
  DMARC pass  <-  "정렬된" 인증이 하나 이상 pass ---------------+

  정책 조회:  _dmarc.example.com  TXT  "v=DMARC1; p=reject; rua=mailto:dmarc@example.com"
```

- DMARC 통과 조건: `From:` 도메인에 DMARC 정책 레코드가 있고, SPF와 DKIM 중 **하나 이상이** pass이며, 그 pass가 `From:` 도메인과 **정렬된** 식별자에서 나와야 한다(RFC 7489 §4.2, RFC 9989 §4.1·§5.3.5, 정렬의 정의는 §4.4).
- 정렬(alignment) 두 방식
  - *relaxed(기본)*: 조직 도메인이 같으면 정렬이다. `mail.example.com`과 `example.com`은 정렬된다.
  - *strict*: 도메인이 정확히 같아야 한다.
  - `aspf=`(SPF), `adkim=`(DKIM) 태그로 고른다. 기본은 둘 다 `r`이다.
- 정책 `p=`: `none`(관찰만), `quarantine`(스팸함), `reject`(거절). `sp=`는 서브도메인 정책이다.
- 보고: `rua=`로 집계 보고를 받는다. 누가 내 도메인 이름으로 보내는지 보인다.
- 규격 변화: 2026년 5월 **RFC 9989**가 RFC 7489(와 PSD 실험 RFC 9091)를 대체했다(Standards Track).
  - `pct` 태그가 빠지고 `t`(테스트 모드) 태그가 생겼다.
  - 정책 조회·조직 도메인 판정이 Public Suffix List 대신 "DNS Tree Walk"로 바뀌었다(§4.10, 부록 C.3).

  - *조직 도메인(Organizational Domain)*: 등록 단위 도메인이다. 예(PSL 기준): `a.b.example.co.uk`의 조직 도메인은 `example.co.uk`다. RFC 9989에서는 DNS Tree Walk로 정한다.

### 5. 대량 발송자 요건 (Gmail·Yahoo, 2024-02~)

```text
  모든 발송자 (Gmail)             SPF 또는 DKIM, PTR(정·역방향 DNS), TLS, 스팸률 < 0.3%
  대량 발송자 (Gmail: 하루 5,000통+)
                                  SPF 그리고 DKIM
                                  DMARC 레코드 (p=none 이어도 됨)
                                  From: 이 SPF 또는 DKIM 도메인과 정렬
                                  마케팅·구독 메일은 원클릭 수신 거부 (RFC 8058)
                                  스팸률 0.30% 미만, 0.10% 미만 유지 권장
  Yahoo                           수신 거부 요청을 2일 안에 반영
```

- 원클릭 수신 거부(RFC 8058)
  - 헤더 두 개: `List-Unsubscribe: <https://...>`와 `List-Unsubscribe-Post: List-Unsubscribe=One-Click`.
  - 두 헤더는 유효한 DKIM 서명의 `h=`에 포함돼야 한다(MUST, §4).
  - 원클릭 POST 요청에는 쿠키·HTTP 인증 같은 맥락 정보를 싣지 않는다(MUST NOT, §3.1). 그래서 발신자 엔드포인트는 URI 안의 토큰만으로 처리할 수 있어야 한다.
  - 발신자는 HTTPS 리다이렉트로 답하지 않는다(MUST NOT, §3.1).
  - 수신 측의 POST 본문은 `multipart/form-data`(SHOULD) 또는 `application/x-www-form-urlencoded`(MAY)다(§3.2).

## 쓰이는 자료구조·알고리즘

- **DNS TXT 파싱** — SPF(`v=spf1 ...`), DKIM 키(`v=DKIM1; k=...; p=...`), DMARC(`v=DMARC1; p=...`)는 모두 TXT 레코드 안의 태그-값 문법이다. 태그 이름 → 값의 맵으로 읽는다.
- **SPF 평가 = 조회 예산이 있는 재귀 탐색** — `include`·`redirect`로 다른 도메인 레코드를 불러 깊이 우선으로 평가한다. 전체 조회 수 카운터가 10을 넘으면 멈춘다. [DFS](../../algorithm/12-dfs/2-summary.md) 참고.
- **CIDR 매칭** — `ip4:198.51.100.0/24`는 접두사 비교다(07번 노트 주제).
- **DKIM 서명 = 정규화 → 해시 → 전자서명**
  - 헤더·본문을 정해진 규칙으로 정규화한다. 그다음 SHA-256으로 해시하고, RSA 또는 Ed25519로 서명한다.
  - 정규화는 "사소한 변형에도 같은 바이트열"을 만드는 함수다. 서명 검증의 결정성을 준다.
- **조직 도메인 판정** — RFC 7489는 Public Suffix List 조회, RFC 9989는 PSL 대신 DNS Tree Walk(라벨을 하나씩 떼며 `_dmarc` 레코드를 찾는 탐색)를 쓴다(부록 C.3).
- **억제 목록(suppression list)** — 하드 바운스·수신 거부 주소를 집합(해시 셋)에 넣어 다음 발송에서 뺀다. 연결: [api-design/10-notification-delivery-pipeline](../../api-design/10-notification-delivery-pipeline/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 현재 레코드를 확인한다

```bash
# SPF
dig +short TXT example.com | grep spf1
# DKIM 공개키 (셀렉터는 수신 메일의 DKIM-Signature s= 에서 확인)
dig +short TXT sel2026._domainkey.example.com
# DMARC
dig +short TXT _dmarc.example.com
# 수신 MX
dig +short MX gmail.com
```

### 2. 받은 메일의 판정을 읽는다

수신 서버는 결과를 `Authentication-Results` 헤더에 남긴다(RFC 8601, Gmail "원본 보기"). 아래는 형태를 보이는 예시다.

```text
Authentication-Results: mx.google.com;
       dkim=pass header.i=@example.com header.s=sel2026;
       spf=pass smtp.mailfrom=bounce@esp-mail.net;
       dmarc=pass (p=REJECT) header.from=example.com
```

- `spf=pass`인데 `smtp.mailfrom` 도메인이 `header.from`과 다르면 SPF는 정렬되지 않은 것이다.
- 이 예에서 DMARC를 살린 것은 DKIM(`header.i=@example.com`)이다.

### 3. 발송 대행사(ESP)를 붙일 때의 순서

1. ESP가 **내 도메인으로 DKIM 서명**하게 한다. ESP가 준 CNAME/TXT를 `<selector>._domainkey.example.com`에 등록한다.
2. 가능하면 반송 주소(MAIL FROM)도 내 서브도메인으로 둔다(예: `bounce.example.com`). SPF 정렬까지 얻는다.
3. SPF에 ESP의 `include:`를 넣되 조회 수를 센다. 10을 넘으면 안 쓰는 include를 지운다. 또는 IP로 펼친다(flattening — 대신 ESP IP 변경을 직접 따라가야 한다).
4. DMARC는 `p=none; rua=...`로 시작해 보고를 본다. 정렬 실패 경로를 다 고친 뒤 `quarantine` → `reject`로 올린다.

### 4. 코드에서 — 원클릭 수신 거부 헤더와 바운스 분기

```ts
// Node (nodemailer 류) — 헤더 추가. DKIM 서명의 h= 에 두 헤더가 들어가야 한다.
const headers = {
  'List-Unsubscribe': `<https://example.com/u/${token}>`,
  'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
};

// SMTP 응답 코드로 재시도 여부를 가른다
// enhanced: 확장 상태 코드(RFC 3463), 예: '5.1.1', '5.7.26'
function classify(code: number, enhanced: string): 'retry' | 'suppress' | 'fix-sender' | 'ok' {
  if (code >= 200 && code < 300) return 'ok';
  if (code >= 400 && code < 500) return 'retry';   // 일시 실패: 백오프 후 재시도
  if (enhanced.startsWith('5.1.')) return 'suppress'; // 주소 문제(하드 바운스): 억제 목록
  return 'fix-sender';                             // 5.7.x 정책·인증 거절 등: 반복 말고 발신 설정 점검
}
```

```java
// 수신 거부 엔드포인트: 쿠키·로그인 없이 토큰만으로 처리, 리다이렉트 금지 (RFC 8058 §3.1)
// 수신 측은 multipart/form-data(SHOULD) 또는 urlencoded(MAY)로 보낸다(§3.2) — 둘 다 받는다
@PostMapping(path = "/u/{token}",
             consumes = {MediaType.MULTIPART_FORM_DATA_VALUE, MediaType.APPLICATION_FORM_URLENCODED_VALUE})
ResponseEntity<Void> unsubscribe(@PathVariable String token) {
    unsubscribeService.apply(token);          // 멱등: 여러 번 와도 같은 결과
    return ResponseEntity.ok().build();
}
```

## 장애 시나리오와 대처

### 1. SPF 조회 10회 초과 → permerror → 스팸함

- **현상**: 특정 시점부터 모든 메일이 스팸함으로 간다. SPF 레코드를 "조금" 고친 직후다.
- **보이는 형태**
  - `Authentication-Results: ... spf=permerror`
  - DMARC 집계 보고에서 SPF 결과가 permerror로 몰린다.
- **원인**
  - `include:`가 늘어 중첩까지 합친 DNS 조회 수가 10을 넘었다(RFC 7208 §4.6.4 — 넘으면 permerror).
  - 또는 SPF 레코드가 두 개가 됐다(§3.2).
- **대처**
  - SPF 검사 도구로 조회 수를 센다. 안 쓰는 include를 지운다.
  - 발송원별로 서브도메인을 나눈다(마케팅은 `news.example.com`).
  - 대량 발송이라면 DKIM 정렬을 확보해 SPF 하나에 DMARC를 기대지 않게 한다.

### 2. ESP로 보낸 메일이 DMARC 실패 — 정렬 안 됨

- **현상**: SPF도 pass, DKIM도 pass인데 DMARC fail로 거절된다.
- **보이는 형태**
  - `spf=pass smtp.mailfrom=...@esp-mail.net`, `dkim=pass header.d=esp-mail.net`, `dmarc=fail header.from=example.com`.
  - Gmail 반송: `550 5.7.26 Unauthenticated email from example.com is not accepted due to domain's DMARC policy.`
- **원인**
  - 두 인증 모두 **ESP 도메인**으로 통과했다.
  - `From:` 도메인(example.com)과 조직 도메인이 달라 정렬되지 않았다.
- **대처**
  - ESP에 커스텀 DKIM 도메인(`d=example.com`)을 설정한다.
  - 커스텀 반송 도메인을 설정한다(SPF 정렬).

### 3. DKIM 키 회전 중 옛 레코드를 먼저 지움 → 전량 거부

- **현상**: 키 회전 작업 뒤 발송 메일이 한꺼번에 DMARC fail로 거절된다.
- **보이는 형태**
  - `dkim=fail`(또는 `permerror`, 키 없음), 곧이어 `dmarc=fail`.
  - `dig TXT old._domainkey.example.com`이 빈 답이다.
- **원인**
  - 발송 서버는 아직 옛 셀렉터(`s=old`)로 서명하는데 DNS의 옛 공개키를 먼저 지웠다.
  - 이미 발송돼 재시도 큐에 있던 메일도 옛 셀렉터로 서명돼 있다.
  - SPF가 정렬되지 않은 경로라면 DMARC가 곧바로 실패한다.
- **대처**: 순서를 지킨다.
  1. 새 셀렉터 공개키를 DNS에 게시한다.
  2. 전파를 기다린다(TTL, 28번).
  3. 서명을 새 셀렉터로 바꾼다.
  4. 재시도 기간(수 일)이 지난 뒤 옛 키를 지우거나 `p=`를 비워 폐기 표시한다.

### 4. 대량 발송 요건 미충족 → 거절·속도 제한

- **현상**: 2024년 2월 이후 Gmail·Yahoo 수신자에게 가는 마케팅 메일의 도달률이 급락한다.
- **보이는 형태**
  - Gmail `4.7.27`/`5.7.27`(SPF 미통과), `4.7.30`/`5.7.30`(DKIM 미통과) 같은 속도 제한·거절 코드.
  - Postmaster Tools 스팸률 0.3% 초과.
- **원인**
  - 대량 발송자 요건 중 하나 이상을 못 맞췄다: SPF와 DKIM 둘 다, DMARC 레코드, From 정렬, 원클릭 수신 거부, 스팸률.
- **대처**
  - 요건 목록을 체크리스트로 점검한다.
  - `List-Unsubscribe-Post` 헤더를 붙이고 DKIM `h=`에 포함한다.
  - 수신 거부를 2일 안에 반영한다(Yahoo 요건).
  - 스팸 신고가 많은 목록을 정리한다.

### 5. 하드 바운스 주소로 계속 발송 → 평판 하락

- **현상**: 전체 도달률이 서서히 떨어진다.
- **보이는 형태**: `550 5.1.1 The email account that you tried to reach does not exist` 반송이 발송마다 반복된다.
- **원인**
  - `5.1.1` 같은 주소 문제 5xx를 4xx처럼 재시도하거나, 억제 목록에 넣지 않았다.
  - 없는 주소로 반복 발송하면 수신 측이 발송자를 스팸 발송원으로 본다.
- **대처**
  - 주소 문제 하드 바운스(`5.1.x`)는 즉시 억제 목록에 넣는다.
  - `5.7.x` 정책·인증 거절은 억제 목록에 넣지 않는다. 주소는 멀쩡하니 발신 설정(SPF·DKIM·DMARC)을 고친다(시나리오 2·4).
  - 4xx는 백오프 재시도 후 기한이 지나면 실패로 처리한다.

## 핵심 문장

- SMTP에는 봉투 발신자(`MAIL FROM`)와 헤더 발신자(`From:`)가 따로 있다. SPF는 봉투를, DMARC는 사용자가 보는 `From:`을 기준으로 삼는다.
- SPF는 "이 IP가 보내도 되나", DKIM은 "이 도메인이 서명했고 내용이 그대로인가", DMARC는 "그 통과가 `From:` 도메인과 정렬됐나"를 묻는다.
- DMARC는 SPF와 DKIM 중 정렬된 pass가 하나라도 있으면 통과다. 전달을 견디는 DKIM 정렬을 확보하는 것이 실무의 핵심이다.
- SPF는 DNS 조회 10회를 넘으면 `permerror`이고, DKIM 키 회전은 "새 키 게시 → 전환 → 옛 키 제거" 순서를 어기면 전량 실패한다.
- 4xx는 재시도, 5xx는 반복 금지다. 억제 목록에는 주소 문제(`5.1.x`)만 넣고, `5.7.x` 정책 거절은 발신 설정을 고친다. 이 구분이 발송 평판을 지킨다.

## 관련 주제·근거

- 선행
  - [27-dns-resolution](../27-dns-resolution/2-summary.md) — MX·TXT 레코드
  - [28-dns-caching-and-ttl](../28-dns-caching-and-ttl/2-summary.md) — 레코드 변경의 전파 시간
  - `security/06-public-key-and-signatures` — RSA·Ed25519 서명. 미작성([security 영역 표](../../security/README.md))
  - 해시: [foundations/security/sha256-and-digest.md](../../foundations/security/sha256-and-digest.md)
- 연결
  - [api-design/10-notification-delivery-pipeline](../../api-design/10-notification-delivery-pipeline/2-summary.md) — 발송 파이프라인·억제 목록·재시도.
  - [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) — SPF include 재귀 평가
- RFC 3463 확장 메일 상태 코드 — §3.2 주소(X.1.X) · §3.8 보안·정책(X.7.X) <https://www.rfc-editor.org/rfc/rfc3463>
- RFC 5321 SMTP — §3.3 트랜잭션 · §4.2.1 응답 코드 · §4.5.4.1 재시도 · §5.1 MX · §6.1 전달 책임 <https://www.rfc-editor.org/rfc/rfc5321>
- RFC 7208 SPF — §2.4 검사 대상 · §2.6 결과 · §3.2 레코드 중복 · §4.6.4 조회 한도 <https://www.rfc-editor.org/rfc/rfc7208>
- RFC 6376 DKIM — §3.1 셀렉터 · §3.3 알고리즘 · §3.4 정규화 · §3.5 태그 · §3.6.1 키 레코드 <https://www.rfc-editor.org/rfc/rfc6376>
- RFC 8463 DKIM Ed25519-SHA256 <https://www.rfc-editor.org/rfc/rfc8463>
- RFC 7489 DMARC(Informational, 2015) §3.1 정렬 · §4.2 통과 조건 · §6.3 태그 <https://www.rfc-editor.org/rfc/rfc7489>
- RFC 9989 DMARC(Standards Track, 2026-05, 7489·9091 대체) §4.1 기본(정책 레코드 + 정렬된 식별자 = pass) · §4.4 정렬 · §5.3.5 pass/fail 판정 · §4.10 DNS Tree Walk · 부록 A.6 `pct` 제거 <https://www.rfc-editor.org/rfc/rfc9989>
- RFC 8601 `Authentication-Results` 헤더 <https://www.rfc-editor.org/rfc/rfc8601>
- RFC 8058 원클릭 수신 거부 — §3.1 POST 제약 · §3.2 POST 본문 형식 · §4 DKIM 서명 요구 <https://www.rfc-editor.org/rfc/rfc8058>
- Google "Email sender guidelines" <https://support.google.com/a/answer/81126>
- Google Workspace "Gmail SMTP errors and codes" <https://knowledge.workspace.google.com/admin/support/troubleshooting/gmail-smtp-errors-and-codes>
- Yahoo Sender Best Practices <https://senders.yahooinc.com/best-practices/>
