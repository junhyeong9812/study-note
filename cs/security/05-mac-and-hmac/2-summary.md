# security/05-mac-and-hmac — 무결성+출처 인증, HMAC 이중 해시, 상수 시간 비교, 서명 원문 정규화 — 정리 (힌트)

## 해결하는 문제

웹훅·서버 간 요청을 받을 때 "**키를 아는 쪽이 보냈고, 그 뒤로 안 바뀌었다**"를 확인하고 싶다.

```text
  HMAC은 맞게 계산했는데 생기는 사고 두 가지
  ① 태그를 String.equals 로 비교      → 처음 다른 바이트에서 멈춤 → 응답 시간 차이(CWE-208)
  ② 본문을 JSON 파싱 후 다시 직렬화해서 검증 → 공백·키 순서·이스케이프가 바뀜 → 정상 요청이 401
```

- 기초(문제 정의, `HMAC(K, m) = H((K⊕opad) ‖ H((K⊕ipad) ‖ m))`, 이중 해시 이유, 대칭 키의 성질, 재전송 한계)는 원본에 있다: [foundations/security/hmac.md](../../foundations/security/hmac.md) §1~§8.
- 이 노트는 원본 위에 **테스트 벡터 재현·비교 시간 측정·정규화 사고·적용·질문**을 채운다.

쉬운 예: 둘만 아는 도장이다.
- 보내는 쪽은 편지와 비밀 도장으로 찍은 자국을 같이 보낸다.
- 받는 쪽은 같은 도장으로 다시 찍어 자국을 비교한다.
- 편지를 복사기로 다시 뽑으면(재직렬화) 글자 간격이 달라져, 진짜 편지인데도 자국이 안 맞는다.

똑같은 구조다.\
HMAC은 **바이트**에 대한 도장이다. 의미가 같아도 바이트가 다르면 다른 편지다.

## 동작·원리

### 1. HMAC 이중 해시 — 그림

```text
  K ──(B=64바이트로 맞춤: 길면 H(K), 짧으면 0 채움)──▶ K0
                                                        │
             K0 ⊕ ipad(0x36×64) ──┐                      │
                                  ├─▶ H ──▶ inner(32바이트)
                       메시지 m ──┘             │
             K0 ⊕ opad(0x5c×64) ──────────────┐ │
                                              ├─┴─▶ H ──▶ 태그(32바이트)
```

- *MAC(Message Authentication Code)*: 비밀 키로 만든 짧은 인증 태그. 진위(키를 아는 쪽)와 무결성을 함께 증명한다.
- RFC 2104 §2: B = 해시 블록 크기(SHA-256은 64바이트), ipad = 0x36을 B번, opad = 0x5C를 B번. §3: 키가 B보다 길면 먼저 해시한다. 출력 길이 L(SHA-256은 32바이트)보다 짧은 키는 "강하게 권하지 않는다".
- 바깥 해시가 안쪽 결과를 감싸므로, 04번의 Merkle–Damgård 길이 확장 성질이 태그로 이어지지 않는다(원본 §3).

로컬 재현(실험 E5 [A]) — RFC 4231 테스트 벡터를 JDK `Mac`, 위 그림대로 `MessageDigest`로 손계산, 호스트 openssl로 세 번 계산했다.

```text
  (실험, OpenJDK 21.0.12 eclipse-temurin, --network none, 2026-10-07)
  [A] TC1 JDK=b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7  손계산==JDK:true  RFC값==JDK:true
  [A] TC2 JDK=5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843  손계산==JDK:true  RFC값==JDK:true
  [A] TC6 JDK=60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54  손계산==JDK:true  RFC값==JDK:true

  (호스트 OpenSSL 3.0.13)
  $ printf 'Hi There' | openssl dgst -sha256 -mac HMAC -macopt hexkey:0b0b…0b(20바이트)
  SHA2-256(stdin)= b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7
  $ printf 'what do ya want for nothing?' | openssl dgst -sha256 -hmac Jefe
  SHA2-256(stdin)= 5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843
```

- TC1: 키 `0x0b`×20, 데이터 `"Hi There"`. TC2: 키 `"Jefe"`(4바이트 — 짧은 키도 계산은 된다). TC6: 키 `0xaa`×131 — 블록(64)보다 길어 먼저 해시되는 경로.
- 세 구현이 같은 값을 낸다는 것은 그림의 식이 표준 구현과 같다는 뜻이다.
- 잘라 쓰기: RFC 2104 §5는 태그를 자를 때 해시 출력의 절반 이상, 80비트 이상을 권한다.

### 2. 비교 — 첫 불일치에서 멈추면 시간이 샌다

```text
  일반 비교                                    상수 시간 비교 (MessageDigest.isEqual)
  for i: if a[i] != b[i] return false          result |= a[i] ^ b[i]  (끝까지)
  → 앞부분이 많이 맞을수록 오래 걸림            → 시간이 내용과 무관, 길이에만 의존
```

- JDK 21 `MessageDigest.isEqual` 문서(Implementation Note): 첫 인자의 모든 바이트를 검사하고, 계산 시간은 첫 인자의 길이에만 의존하며 두 번째 인자의 길이나 두 인자의 내용에는 의존하지 않는다.
- *타이밍 부채널(CWE-208 Observable Timing Discrepancy)*: 처리 시간 차이가 비밀에 대한 정보를 흘리는 것.

로컬 측정(실험 E5 `Timing.java`) — 같은 JVM 안에서 비교 함수만 잰 값이다(네트워크 없음). 31회 측정의 중앙값, 3회 실행.

```text
  (실험, OpenJDK 21.0.12 eclipse-temurin, --cpus=2, 2026-10-07)  단위 ns, "첫 바이트 불일치 → 마지막 바이트 불일치"
                            len=32                       len=4096
  손코딩 조기 종료 루프       25.5~32.8 → 51.7~140.0        23.1~29.6 → 3,227~13,179
  Arrays.equals             28.9~32.1 → 27.7~31.8         25.3~32.0 → 328~425
  MessageDigest.isEqual     84.0~97.1 → 92.1~98.4         9,220~10,223 → 9,548~10,614
```

- 손코딩 루프와 `Arrays.equals`는 마지막 바이트까지 맞을 때 오래 걸린다(4096바이트에서 뚜렷). 32바이트에서는 `Arrays.equals`(벡터화)의 차이가 측정 노이즈 안에 묻혔다.
- `isEqual`은 불일치 위치와 상관없이 같은 수준이다. 집필 때 실행에서는 4096바이트의 마지막-불일치 쪽이 0.7~4% 더 걸렸지만, 사실 점검 재실행 5회(정순 3·역순 2)에서는 −6%~+8%로 방향이 일정하지 않았다. 노이즈로 본다. 불일치 위치에 비례해 늘어나는 모양은 아니다.
- 재실행(같은 이미지·`--cpus=2`, 2026-10-07)의 4096바이트 범위: 손코딩 루프 22~29 → 3,069~11,268 ns, `Arrays.equals` 28~34 → 297~418 ns, `isEqual` 7,506~10,545 ns. 절대값은 실행마다 크게 흔들리고, 경향(조기 종료 비교만 불일치 위치에 따라 늘어남)은 같았다.
- 한계: 이 측정은 "차이가 존재한다"까지만 보인다. 네트워크 너머에서 그 차이를 얼마나 잴 수 있는지는 지터·반복 수에 달렸고, 여기서는 재지 않았다. 측정이 어렵다는 것이 안전하다는 뜻은 아니다 — GitHub 웹훅 문서도 "평범한 `==`를 쓰지 말라"고 적는다.

### 3. 서명 원문 — 바이트가 같아야 한다

```text
  보내는 쪽: raw = {"id":"evt_1","amount":100,"memo":"가"}   sig = HMAC(secret, raw)
                │
  받는 쪽  ─────┼──▶ raw 바이트로 HMAC  ─────────────▶ 일치 → 200
                └──▶ JSON 파싱 → 다시 직렬화 → HMAC  ──▶ {"id": "evt_1", "amount": 100, "memo": "가"}  → 401
```

로컬 재현(실험 E5 `canon.py`, 가짜 비밀):

```text
  (실험, Python 3.12.14 표준 라이브러리, --network none, 2026-10-07)
  A 원문 바이트로 검증              -> 200
  B 파싱 후 json.dumps 재직렬화      -> 401 b'{"id": "evt_1", "amount": 100, "memo": "\\uac00"}'
  C 공백 없이·ensure_ascii=False    -> 200 True
  D C + sort_keys=True(키 순서 변경) -> 401 b'{"amount":100,"id":"evt_1","memo":"\xea\xb0\x80"}'
```

- B: 기본 `json.dumps`가 `:`·`,` 뒤에 공백을 넣고 비ASCII를 `\uXXXX`로 바꿨다.
- C: 옵션을 맞추면 **이번 입력에서는** 원문과 같아졌다. 일반적으로 보장되지 않는다(숫자 표기 `1.0`/`1`, 이스케이프 `\/`, 중복 키 등).
- D: 키 순서만 바뀌어도 401.
- 결론: 정규화를 맞추려 하지 말고 **수신한 원문 바이트로 검증**한다. 서명 규격이 정규화를 정의한 경우(예: JSON Canonicalization Scheme RFC 8785)에만 그 규칙을 양쪽이 쓴다.

## 쓰이는 자료구조·알고리즘

- **HMAC 이중 해시**: 한 해시 함수 H를 키 섞인 두 패드로 두 번 호출. 입력 = 블록 정렬된 패드 + 메시지, 출력 길이 = H의 출력.
- **상수 시간 비교**: 분기 없이 XOR을 OR로 누적하고 마지막에 한 번만 판정. 데이터 의존 분기·조기 종료를 없앤다([algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md)).
- **정규화(canonicalization)**: 같은 의미를 하나의 바이트 표현으로 사상하는 함수. 서명 전후에 같아야 하며, 없으면 "원문 보존"이 정규화를 대신한다.
- **재전송 방어 자료구조**: 처리한 요청 ID를 TTL 집합에 넣는다. 타임스탬프 창 × 2 이상 보관([reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md), [api-design/09](../../api-design/09-async-apis-and-webhooks/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. Spring MVC 웹훅 검증 — 원문 바이트로, 상수 시간으로

```java
// 취약: 객체로 받은 뒤 다시 직렬화해서 검증 + String.equals
@PostMapping("/webhooks/pay")
ResponseEntity<Void> bad(@RequestBody PayEvent ev, @RequestHeader("X-Signature") String sig) throws Exception {
    String body = objectMapper.writeValueAsString(ev);            // 원문과 바이트가 다르다
    String calc = HexFormat.of().formatHex(hmac(secret, body.getBytes(UTF_8)));
    return calc.equals(sig) ? ok() : status(401).build();         // 조기 종료 비교
}

// 고친 판: 원문 바이트 → 검증 → 그다음 파싱
@PostMapping(value = "/webhooks/pay", consumes = "application/json")
ResponseEntity<Void> good(@RequestBody byte[] raw, @RequestHeader("X-Signature") String sigHex) throws Exception {
    byte[] expected = hmac(secret, raw);
    byte[] given;
    try { given = HexFormat.of().parseHex(sigHex.replaceFirst("^sha256=", "")); }
    catch (IllegalArgumentException e) { return ResponseEntity.status(401).build(); }
    if (!MessageDigest.isEqual(expected, given)) return ResponseEntity.status(401).build();
    PayEvent ev = objectMapper.readValue(raw, PayEvent.class);    // 검증 통과 후에만 파싱
    // ... 타임스탬프 창·요청 ID 중복 확인(재전송) → 처리
    return ResponseEntity.ok().build();
}

static byte[] hmac(byte[] key, byte[] msg) throws GeneralSecurityException {
    Mac mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(key, "HmacSHA256"));
    return mac.doFinal(msg);
}
```

- 서명 범위에 타임스탬프·요청 ID를 넣어야 재전송 창을 강제할 수 있다(원본 §8, [api-design/09](../../api-design/09-async-apis-and-webhooks/2-summary.md)의 Standard Webhooks 형식).
- 키는 L(32바이트) 이상 무작위로(RFC 2104 §3). 회전 중에는 옛 키·새 키를 함께 검사한다.
- GitHub 웹훅: `X-Hub-Signature-256` 헤더, 값은 `sha256=`로 시작, 평범한 `==` 금지, 본문은 UTF-8로 다룬다(GitHub 문서).

### 2. 브라우저·Node 쪽 — 같은 원칙

```ts
// Node.js: 비교는 crypto.timingSafeEqual (길이가 다르면 예외를 던지므로 먼저 길이 확인)
import { createHmac, timingSafeEqual } from "node:crypto";
function verify(raw: Buffer, sigHex: string, secret: Buffer): boolean {
  const expected = createHmac("sha256", secret).update(raw).digest();
  const given = Buffer.from(sigHex.replace(/^sha256=/, ""), "hex");
  return given.length === expected.length && timingSafeEqual(given, expected);
}
```

- Express라면 `express.json()`이 원문을 소비하기 전에 `express.raw({ type: "application/json" })`로 웹훅 경로만 원문을 받는다.

### 3. 진단 — 401이 날 때 보는 순서

1. 받는 쪽이 계산에 쓴 바이트를 그대로 덤프(로그는 해시값만, 본문은 디버그 환경에서만).
2. 보내는 쪽 문서의 서명 대상 정의(본문만? `id.timestamp.body`?)와 대조.
3. 프록시·미들웨어가 본문을 바꾸는지(압축 해제·문자셋 변환·JSON 재포맷).
4. 키 형식(base64 디코드 여부, `whsec_` 접두 제거)과 16진/base64 인코딩.
5. 호스트에서 재계산: `openssl dgst -sha256 -mac HMAC -macopt hexkey:<키 16진> < body.bin`.

## 장애 시나리오와 대처

### 1. 비상수 시간 비교 → 타이밍 공격 ⚠

- **현상**: 보안 점검에서 태그 비교가 `String.equals`·`==`·`Arrays.equals`로 발견된다. 운영 중에는 증상이 없다 — 조용한 결함이다.
- **보이는 형태**: 한 출처가 같은 메시지에 태그만 조금씩 바꾼 요청을 대량으로 보낸다. 응답은 모두 401.
- **원인**: 첫 불일치에서 멈추는 비교. 실험 E5에서 손코딩 루프는 마지막 바이트까지 맞을 때 4096바이트 기준 수천~1만 ns 더 걸렸다.
- **대처**: `MessageDigest.isEqual`(Java)·`crypto.timingSafeEqual`(Node)·`hmac.compare_digest`(Python). 정적 분석 규칙으로 태그 비교의 `equals` 사용을 막는다. 같은 출처의 검증 실패에 속도 제한.

### 2. 서명 원문 정규화 불일치 → 정상 웹훅이 401 ⚠

- **현상**: 결제사 웹훅이 일부(한글이 든 것, 특정 필드가 있는 것)만 401로 실패하고 재시도가 쌓인다.
- **보이는 형태**: 401 응답 로그. 보내는 쪽 대시보드에 "signature verification failed" 재시도. 비ASCII나 소수점이 든 이벤트에서만 실패.
- **원인**: 원문 대신 파싱 후 재직렬화한 바이트로 검증했다. 공백·키 순서·이스케이프가 달라졌다(실험 E5 B·D).
- **대처**: `@RequestBody byte[]`·`express.raw`로 원문을 받아 검증 후 파싱. 본문을 바꾸는 미들웨어를 웹훅 경로에서 뺀다. 재시도로 쌓인 이벤트는 원문 검증으로 재처리.

### 3. 키 회전 직후 401 폭증

- **현상**: 비밀을 새로 발급한 직후 모든 웹훅이 실패한다.
- **보이는 형태**: 특정 시각부터 401 100%. 보내는 쪽은 옛 키, 받는 쪽은 새 키만.
- **원인**: 양쪽 전환 시점이 어긋났다.
- **대처**: 받는 쪽이 일정 기간 옛 키·새 키를 둘 다 검사(서명 목록 형식이면 하나라도 맞으면 통과). 기간이 끝나면 옛 키 제거(원본 [Claude 추가], [api-design/09](../../api-design/09-async-apis-and-webhooks/2-summary.md)).

### 4. HMAC은 맞는데 같은 요청이 두 번 처리됨

- **현상**: 결제 완료 웹훅이 두 번 처리돼 포인트가 두 번 적립됐다.
- **보이는 형태**: 같은 요청 ID·같은 태그의 요청이 두 번 200.
- **원인**: HMAC은 재전송(freshness)을 막지 않는다(원본 §8). 정상 재시도도 같은 모양이다.
- **대처**: 타임스탬프 창 + 요청 ID 중복 제거(TTL ≥ 창 × 2), 처리 자체를 멱등하게([reliability/13](../../reliability/13-idempotency/2-summary.md)).

## 핵심 문장

- MAC은 키를 아는 쪽이 만들었고 그 뒤 바뀌지 않았음을 증명한다. HMAC은 해시를 키 섞인 두 패드로 두 번 써서 길이 확장 성질이 태그로 이어지지 않게 한다.
- HMAC 구현은 RFC 4231 테스트 벡터로 확인한다. 블록보다 긴 키는 먼저 해시된다.
- 태그 비교는 상수 시간으로 한다. 첫 불일치에서 멈추는 비교는 맞은 길이만큼 시간이 늘어난다.
- HMAC은 바이트에 대한 도장이다. 수신한 원문 바이트로 검증하고, 검증한 뒤에 파싱한다.
- HMAC은 재전송을 막지 않는다. 타임스탬프 창과 요청 ID 중복 제거가 따로 필요하다.

## 관련 주제·근거

- 기초(원본, 읽기만): [foundations/security/hmac.md](../../foundations/security/hmac.md) — §2 정의, §3 이중 해시 이유, §4 대칭 키, §5 상수 시간 비교, §7 서명 범위, §8 재전송 한계
  - 참고: 원본 §1의 "TLS는 이 HTTP 요청의 발신자가 누구인가를 애플리케이션에 증명하지 못한다"는 서버 인증만 하는 일반 TLS에 해당한다. 클라이언트 인증서를 쓰는 mTLS는 연결 상대를 증명한다([network/32](../../network/32-mtls-and-cert-operations/2-summary.md)). 다만 프록시에서 TLS가 끝나면 그 뒤 구간에는 그 증명이 전달되지 않는다는 원본의 지적은 그대로 맞다.
- 선행: [04-hash-functions-and-digests](../04-hash-functions-and-digests/2-summary.md) — Merkle–Damgård, 길이 확장
- 후속(같은 영역 — [영역 표](../README.md))
  - [security/06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md) — 검증자가 위조할 수 없는 서명(부인 방지 뒷받침)
  - [security/10-authentication-basics](../10-authentication-basics/2-summary.md) — HOTP/TOTP = HMAC + 카운터
  - [security/12-tokens-and-jwt](../12-tokens-and-jwt/2-summary.md) — HS256 = HMAC-SHA-256
- 연결
  - [api-design/09-async-apis-and-webhooks](../../api-design/09-async-apis-and-webhooks/2-summary.md) — Standard Webhooks 서명·재전송 창 실험
  - [api-design/26-case-delivery-webhook](../../api-design/26-case-delivery-webhook/2-summary.md) — 파싱 전 서명 검증
  - [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)
  - [03-symmetric-encryption-and-aead](../03-symmetric-encryption-and-aead/2-summary.md) — Encrypt-then-MAC, AEAD
- 1차 출처
  - RFC 2104 HMAC (1997) — §2 정의(B, ipad 0x36, opad 0x5C), §3 키 길이, §5 자르기 <https://www.rfc-editor.org/rfc/rfc2104>
  - RFC 4231 HMAC-SHA-224/256/384/512 테스트 벡터 — §4.2 TC1, §4.3 TC2, §4.7 TC6 <https://www.rfc-editor.org/rfc/rfc4231>
  - NIST FIPS 198-1 HMAC <https://csrc.nist.gov/pubs/fips/198-1/final>
  - Java SE 21 `MessageDigest.isEqual` Implementation Note <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/security/MessageDigest.html>
  - GitHub Docs "Validating webhook deliveries" — `X-Hub-Signature-256`, `sha256=`, `==` 금지, UTF-8 <https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries>
  - RFC 8785 JSON Canonicalization Scheme <https://www.rfc-editor.org/rfc/rfc8785>
  - CWE-208 Observable Timing Discrepancy <https://cwe.mitre.org/data/definitions/208.html> · CWE-345 Insufficient Verification of Data Authenticity <https://cwe.mitre.org/data/definitions/345.html>
- 실험(가짜 키·가짜 비밀만, `--network none`)
  - E5 `Hm.java` — RFC 4231 TC1·TC2·TC6를 JDK `Mac`과 손계산으로. OpenJDK 21.0.12, 2026-10-07. 호스트 `openssl dgst -mac HMAC`(3.0.13)로 TC1·TC2 교차 확인.
  - E5 `Timing.java`·`Timing2.java` — 비교 함수 3종의 첫/마지막 바이트 불일치 시간(중앙값, 3회 + 순서 바꿔 2회). 같은 환경, `--cpus=2`.
  - E5 `canon.py` — 원문 vs 재직렬화 HMAC 검증. Python 3.12.14(python:3.12-slim).
