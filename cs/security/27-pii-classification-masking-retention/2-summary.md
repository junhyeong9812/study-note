# security/27-pii-classification-masking-retention — 데이터 분류·마스킹·토큰화·보존·파기 — 정리 (힌트)

## 해결하는 문제

개인정보는 "있는 곳"이 아니라 "**복제되는 곳**"에서 샌다.\
한 번 받은 카드번호·이메일·주민번호는 로그, 에러 트래커, 백업, 분석 DW, 스테이징으로 조용히 퍼진다.

```text
  운영 DB(암호화·접근통제 있음)
      │  요청 바디 전체 로깅 ──▶ 로그 수집기 ──▶ 외부 SaaS
      │  예외 메시지에 이메일 ──▶ 에러 트래커(Sentry 등)
      │  야간 덤프 ──▶ 스테이징 DB(통제 약함) ──▶ 여기 유출이 실유출
      └  정기 백업 ──▶ 테이프(탈퇴해도 남음)
  → 보호는 운영 DB 한 곳이 아니라 "퍼진 모든 사본"에 걸려야 한다
```

- *PII(개인식별정보)*: 특정 개인을 알아낼 수 있는 정보. 단독으로(주민번호) 또는 조합으로(생일+우편번호+성별).
- 세 가지를 설계한다.
  - **분류**: 어떤 데이터가 얼마나 민감한가 → 그에 맞는 통제.
  - **변형**: 마스킹·토큰화·가명화로 사본에서 원본을 줄이거나 없앤다.
  - **보존·파기**: 언제까지 두고 언제 지우나. 백업·파생본까지.
- 근거: NIST SP 800-122(2010, PII 기밀성 영향 수준 low/moderate/high로 분류, 최소 수집·비식별화), OWASP Logging Cheat Sheet(남기지 말 것), GDPR 17조(삭제권).

쉬운 예: 민감한 서류를 복사기로 여러 장 떴다.\
원본 금고만 잠가도 소용없다 — 복사본이 책상·휴지통·협력사에 흩어져 있다. 그래서 처음부터 **민감한 칸은 가리고 복사**(마스킹)하거나, **실제 내용 대신 보관증 번호로 복사**(토큰화)하고, 복사본마다 **폐기 날짜**를 적어 둔다.

실무 예:
- 요청 바디 전체를 로깅해 카드번호가 외부 로그 SaaS로 복제된다(26번 CWE-532).
- 예외 메시지에 이메일이 들어가 에러 트래커에 노출된다.
- 탈퇴 회원 데이터가 백업·분석 DW에 영구 잔존한다.
- 운영 DB 덤프로 스테이징을 구성해, 스테이징 유출이 곧 실유출이 된다.

## 동작·원리

### 1. 분류 — 민감도에 통제를 맞춘다

```text
  공개 < 내부 < 기밀(PII) < 민감 PII(주민번호·카드·건강·생체)
   낮은 통제        ───────────────▶        높은 통제(암호화·최소 접근·짧은 보존·감사)
```

- NIST SP 800-122: PII마다 **기밀성 영향 수준**(low/moderate/high)을 정하고 그에 맞춰 보호한다. 수준은 PII가 부적절하게 접근·사용·공개될 때 당사자 개인과(또는) 조직에 생길 수 있는 피해로 판단한다(SP 800-122 §3).
- 분류가 있어야 "이 칸은 로그 금지", "저 칸은 암호화 필수"를 자동 규칙으로 걸 수 있다. 분류 없는 보호는 전부에 같은 통제를 걸거나(비용·불편) 아무 데도 안 건다.

### 2. 마스킹 vs 토큰화 vs 가명화 — 되돌릴 수 있나

```text
  마스킹:   4111 11** **** 1111   보이는 자릿수만 제한 (표시용 — 화면에서 되돌릴 수 없음, 원본 저장은 별개)
  토큰화:   카드번호 → tok_9f3a..  별도 금고(볼트)에 매핑 저장, 토큰만 유통 (볼트로만 가역)
  가명화:   실명 → 가명(HMAC 등)  같은 입력이 같은 가명 (HMAC 자체는 비가역 — 키+후보 대조로 재식별 가능)
  익명화:   되돌릴 수 없게 집계·일반화 (비가역, 재식별 위험 관리)
```

- *마스킹*: 표시할 때 일부만 보인다. PCI DSS v4.0 요건 3.4.1 — 원칙은 표시 시 최대 BIN + 마지막 4자리까지, 더 봐야 하는 역할은 문서화된 업무상 근거가 있을 때만(PCI SSC FAQ 1492). 표시 마스킹은 **저장된** PAN 보호(요건 3.5.1 — 암호화·절단·토큰화·키 해시)와 별개 요건이다(같은 FAQ).
- *토큰화*: 민감 값을 **의미 없는 토큰**으로 바꾸고, 원본은 분리된 볼트에만 둔다. 앱·로그·분석은 토큰만 다룬다. 유출돼도 볼트 없이는 원본을 얻지 못한다. 단 같은 토큰으로 기록을 서로 연결할 수 있고, 결제에 쓰이는 토큰이면 그 자체로 악용될 수 있다 — 영향은 토큰의 용도·권한에 달렸다(PCI SSC Tokenization Guidelines).
- *가명화(pseudonymisation)*: 식별자를 키 기반으로 치환. 같은 입력 → 같은 가명이라 조인·분석은 되지만, 키 없이는 원본 복원이 어렵다. GDPR이 권장 기법으로 든다(하지만 가명정보도 여전히 개인정보다).
- *익명화*: 재식별이 안 되게 만든 것. 성공하면 개인정보가 아니게 된다.

(실험, OpenJDK 21.0.12 Temurin, `--network none`, 2026-10-07 — 테스트 카드번호 4111...·example.com·가짜 값만)

```text
원본   : {... card=4111 1111 1111 1111, cardAlt=4111111111111111, email=kim@example.com, rrn=000000-0000000, memo=연락은 kim at example dot com}
거부목록: {... card=[CARD], cardAlt=4111111111111111, email=[EMAIL], rrn=000000-0000000, memo=연락은 kim at example dot com}
허용목록: {... card=[REDACTED], cardAlt=[REDACTED], email=[REDACTED], rrn=[REDACTED], memo=[REDACTED]}
표시 마스킹: 411111******1111
```

- 관찰: **거부 목록 정규식**은 아는 모양만 지웠다. 공백 없는 `cardAlt`, 거부 목록에 패턴이 아예 없던 `rrn`, "kim at example dot com"으로 흘려 쓴 `memo`는 그대로 샜다.
- **허용 목록**(안전 필드만 남기고 나머지 `[REDACTED]`)은 `orderId·amount·currency`만 남기고 전부 가렸다. 로그·분석에는 허용 목록이 안전하다 — "모르는 것은 가린다".

### 3. 가명화 — 키 없는 해시 vs HMAC

```text
  SHA-256(전화번호): 값 공간이 작으면 후보를 다 돌려(열거) 원본을 되찾는다
  HMAC-key(전화번호): 같은 입력 → 같은 가명(조인 가능), 키 없이는 열거 불가
```

(실험, 같은 환경 — 전화번호 뒤 4자리를 모르는 상황을 가정)

```text
SHA-256(전화) 열거 복원: 010-1234-5678 (약 290 ms, 후보 1만 개)   ← 집필 3회 257~307 ms, 점검 재실행 3회 234~315 ms
HMAC 가명: 287958b90d3b5597 / 다시: 287958b90d3b5597   (같은 입력 → 같은 가명, 키 없이는 열거 불가)
```

- 관찰: 전화번호를 그냥 SHA-256으로 가명화하면, 뒤 4자리 후보 1만 개를 **약 0.3초(234~315 ms)에** 다 돌려 원본을 되찾았다. 이 시간은 JVM 시작 직후 문자열 처리까지 포함한 값이라, 해시 계산만 따지면 더 짧다(해석). 값 공간이 작은 식별자(전화·주민번호·카드)는 "해시했으니 안전"이 거짓이다.
- HMAC(비밀 키)으로 하면 같은 입력이 같은 가명을 내 분석 조인은 되고, 키가 없으면 열거가 막힌다. 단 **키가 새면** 같은 열거를 키로 다시 돌려 전부 재식별할 수 있다(HMAC을 "복호"하는 게 아니라 후보 대조). 그래서 키 관리가 핵심이다(09번).

### 4. crypto-shredding — 키를 지워 데이터를 지운다

```text
  사용자별 키로 암호화 → 백업·DW에 암호문만 남는다
  탈퇴 → 그 사용자 키의 모든 사본(백업·에스크로 포함) 파기 → 흩어진 암호문이 한꺼번에 못 읽는 상태가 된다
```

(실험, 같은 환경 — AES-256-GCM, 사용자별 키)

```text
파기 전 복호: kim@example.com
키 파기 후 : 키 없음 → 백업 암호문 31바이트는 읽을 수 없음
```

- 관찰: 사용자 키를 지우자, 백업에 남아 있는 암호문(31바이트)은 평문으로 되돌릴 수 없게 됐다. **백업 테이프를 일일이 찾아 지우지 않아도** 키 파기로 "읽을 수 없게" 만든다. 단 실험은 암호문 하나로 확인한 것이다. 그 키의 백업·에스크로 사본이나 이미 메모리에 풀린 키가 남아 있으면 다른 곳의 암호문은 여전히 복호된다 — 관련 키 사본을 모두 쓸 수 없게 해야 성립한다(NIST SP 800-88 Cryptographic Erase).
- *crypto-shredding(암호 삭제)*: 데이터가 아니라 **키를 파기**해 실질적 삭제를 이루는 기법. 백업·파생본처럼 선택 삭제가 어려운 곳에서 특히 쓸모 있다([data-engineering/12-data-retention-and-erasure](../../data-engineering/12-data-retention-and-erasure/2-summary.md)).
  - 한계: 암호 자체가 뒤에 깨지면 과거 암호문이 복원될 수 있다. 법·규정이 "물리적 삭제"를 요구하면 이것만으로는 부족할 수 있다(해석).

### 5. 보존과 파기 — 두 방향의 실수

```text
  너무 오래 둔다 ──▶ 유출 시 피해 확대, 삭제권 위반
  너무 일찍 지운다 ──▶ 법정 보존 의무 위반(세금·거래 기록), 분쟁 증거 소멸
  정답: 데이터 종류별 보존 기한 + 기한 후 자동 파기 + 삭제 전파
```

- GDPR 17조(1): 사유가 있으면 "without undue delay" 삭제. (3): 표현의 자유, **법적 의무**·공익 업무, 공공보건, 공익 기록보존·연구·통계, 법적 청구의 제기·행사·방어에 필요한 처리는 예외.
- 그래서 "삭제권이 왔다고 전부 지운다"가 아니다. 법정 보존 의무가 겹치는 데이터는 지우지 못한다 — 보존과 삭제권이 충돌한다.
- 삭제는 **전파**가 핵심이다: 운영 DB뿐 아니라 백업·로그·파생 복제본·검색 인덱스·분석 DW까지. 바로 못 지우는 백업은 쓰지 못하게 묶었다가 주기에 덮어쓰거나, crypto-shredding으로 처리한다(영국 ICO 삭제권 지침의 백업 항목, reliability/18 §6).

## 쓰이는 자료구조·알고리즘

- **형식 보존 토큰** — 토큰이 원본과 같은 형식(16자리)이면 기존 스키마를 안 바꾸고 끼운다(검사 숫자 같은 기존 검증 통과 여부는 따로 확인). 만드는 길은 둘이다: 볼트가 토큰↔원본 매핑을 들고 있는 방식(해시맵/보안 저장소), 그리고 볼트 없이 키로 암호화하는 **FPE(format-preserving encryption, NIST SP 800-38G)** — FPE는 키로 복호되는 암호다.
- **HMAC(키 기반 가명)** — 같은 입력 → 같은 출력(조인 가능), 키 없이 역산 불가. [security 05-mac-and-hmac](../05-mac-and-hmac/2-summary.md)
- **대칭 암호 + 키 계층(봉투 암호화)** — crypto-shredding은 데이터 키를 지워 삭제. [security 03-symmetric-encryption-and-aead](../03-symmetric-encryption-and-aead/2-summary.md) · [09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md)
- **생일 경계** — 짧은 랜덤 ID·작은 값 공간은 충돌·열거가 쉽다(실험의 전화번호 열거). [security 16-identifiers-and-enumeration](../16-identifiers-and-enumeration/2-summary.md)
- **거부 목록 vs 허용 목록(집합 소속)** — redaction은 허용 목록이 안전하다(실험).

## 적용 — 풀어나가는 법

### 1. 순서

1. **분류 태그**를 데이터 모델에 붙인다(필드마다 public/internal/pii/sensitive).
2. 로그·에러·메트릭으로 나가는 경로에 **허용 목록 redaction**을 공용으로 건다(거부 목록은 샌다 — 실험).
3. 민감 값은 **토큰화**해 앱·로그·분석은 토큰만 다룬다. 원본은 분리 볼트.
4. 분석·조인용 식별자는 **키 기반 가명(HMAC)**. 키는 KMS로(09번).
5. **보존 기한 + 자동 파기 + 삭제 전파**를 둔다. 백업은 crypto-shredding 또는 묶음.
6. **운영 데이터를 테스트/스테이징에 복제 금지** — 복제해야 하면 가명·합성 데이터로.

### 2. 로그 redaction — 취약 → 고친 예 (Java 21)

```java
// 취약: 요청 바디·예외를 통째로 (카드·이메일이 그대로)
log.info("checkout request: {}", requestBody);
log.error("failed for user: " + user, ex);

// 고친 판: 허용 목록으로 안전 필드만 (실험의 allowlist)
Set<String> SAFE = Set.of("orderId", "amount", "currency");
String safe = fields.entrySet().stream()
    .map(e -> e.getKey() + "=" + (SAFE.contains(e.getKey()) ? e.getValue() : "[REDACTED]"))
    .collect(Collectors.joining(", ", "{", "}"));
log.info("checkout request: {}", safe);
```

### 3. 표시 마스킹과 토큰화

```java
// 표시 마스킹: 앞 6 + 마지막 4 (PCI DSS v4.0 3.4.1의 원칙 "BIN + 마지막 4" 안쪽). 원본 pan은 그대로 — 저장 보호는 따로
String masked = pan.substring(0, 6) + "*".repeat(pan.length() - 10) + pan.substring(pan.length() - 4);
// 411111******1111  (실험 출력)

// 가명(HMAC) — 같은 입력 같은 가명, 키 없이 역산 불가 (키는 KMS)
Mac mac = Mac.getInstance("HmacSHA256");
mac.init(kms.pseudonymKey());
String pseudo = HexFormat.of().formatHex(mac.doFinal(phone.getBytes())).substring(0, 16);
```

- 전화·주민번호를 **키 없는 SHA-256으로 가명화하지 않는다** — 실험에서 약 0.3초 만에 열거 복원됐다.

### 4. 보존·파기

```sql
-- 보존 기한 지난 레코드 자동 파기 (예시: 90일 로그, 거래는 법정 기한 별도)
DELETE FROM access_log WHERE created_at < now() - interval '90 days';
```

- 삭제권 처리: 운영 저장소는 지우고, 로그·검색 인덱스·DW의 사본도 전파한다. 바로 못 지우는 백업은 crypto-shredding(키 파기) 또는 접근 차단 후 주기 덮어쓰기.

### 5. 진단

```bash
# 로그에 PII 패턴이 새는지 (카드 13~16자리·이메일·토큰)
grep -E '[0-9]{13,16}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+|bearer [A-Za-z0-9._-]+' app.log | head
# 스테이징이 운영 덤프로 구성됐는지 (실제 이메일 도메인 존재)
psql staging -c "select count(*) from users where email not like '%@example.com'"
```

## 장애 시나리오와 대처

### 1. 요청 바디 전체 로깅 → 카드·주민번호가 외부로 복제 (⚠ 커리큘럼)

- **현상**: 로그 수집기·외부 SaaS에서 결제/식별 정보가 발견된다.
- **보이는 형태**: INFO 로그에 바디 원문. `grep`으로 카드·주민번호 패턴.
- **원인**: 디버깅 편의로 바디 통째 로깅, redaction 없음 또는 거부 목록만(새는 칸이 남음).
- **대처**: 허용 목록 redaction을 공용 필터로. 이미 복제된 로그는 보존 정책으로 파기, 외부 SaaS에 삭제 요청. 카드가 샜으면 PCI 절차·토큰화 도입.

### 2. 예외 메시지에 이메일 → 에러 트래커 노출 (⚠ 커리큘럼)

- **현상**: 에러 트래커 이슈 제목·본문에 이메일·이름.
- **보이는 형태**: `UserNotFound: kim@example.com` 같은 메시지가 외부 도구에.
- **원인**: 예외에 식별자를 문자열로 넣음. 에러 리포터가 컨텍스트를 통째 수집.
- **대처**: 예외 메시지엔 내부 ID(가명)만. 에러 리포터에 스크러빙 규칙. 26번 로그 규칙과 같은 목록.

### 3. 탈퇴 회원 데이터가 백업·DW에 영구 잔존 (⚠ 커리큘럼)

- **현상**: 삭제권 처리를 했는데 백업·분석 DW에서 그 사람 데이터가 나온다.
- **보이는 형태**: 운영 DB엔 없고 DW·백업엔 있음. 삭제 전파 로그 부재.
- **원인**: 삭제가 운영 DB에만 적용. 백업·파생본은 손대지 않음.
- **대처**: 삭제 전파 목록(운영·로그·인덱스·DW). 백업은 crypto-shredding 또는 접근 차단 후 주기 덮어쓰기. 단 법정 보존 의무(GDPR 17(3))가 겹치면 그 데이터는 예외로 분리 보관.

### 4. 운영 덤프로 스테이징 구성 → 스테이징 유출이 실유출 (⚠ 커리큘럼)

- **현상**: 통제가 약한 스테이징/테스트가 뚫렸는데 실제 고객 데이터가 들어 있다.
- **보이는 형태**: 스테이징 DB에 실제 이메일 도메인·실명. 접근 권한이 운영보다 넓음.
- **원인**: "데이터가 있어야 테스트가 된다"며 운영 덤프를 복제.
- **대처**: 운영 데이터 복제 금지. 가명화·마스킹한 데이터나 합성 데이터로 테스트 셋 구성. 토큰화돼 있으면 볼트 없는 토큰만 복제.

### 5. 가명화했는데 재식별된다

- **현상**: "가명이라 안전"하다던 데이터에서 개인이 특정된다.
- **보이는 형태**: 작은 값 공간을 키 없이 해시했거나(실험), 준식별자(생일+지역+성별) 조합으로 좁혀짐.
- **원인**: 키 없는 해시(열거 가능), 또는 가명정보도 개인정보라는 점을 간과.
- **대처**: 키 기반 가명(HMAC)+KMS, 준식별자 일반화·k-익명성 검토, 가명정보도 개인정보로 다뤄 접근통제·보존을 유지.

## 핵심 문장

- 개인정보는 복제되는 곳(로그·에러 트래커·백업·DW·스테이징)에서 샌다 — 보호는 운영 DB 한 곳이 아니라 모든 사본에 건다.
- 로그·분석 redaction은 허용 목록으로 한다 — 거부 목록은 모르는 형식(공백 없는 카드·흘려 쓴 이메일)을 흘린다(실험).
- 전화·주민번호를 키 없는 해시로 가명화하면 값 공간이 작아 열거로 복원된다(실험 약 0.3초). 키 기반 HMAC을 쓴다.
- crypto-shredding은 키를 지워 백업·파생본의 데이터를 한꺼번에 못 읽게 한다(실험).
- 보존은 양방향 실수다 — 너무 오래 두면 삭제권 위반·피해 확대, 너무 일찍 지우면 법정 보존 의무 위반.

## 관련 주제·근거

- 선행
  - [26-security-logging-and-audit](../26-security-logging-and-audit/2-summary.md) — 로그에 남기지 말 것, 감사 보존
  - [security 09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md) — 토큰화 볼트·가명 키·crypto-shredding 키 관리
- 연결
  - [security 03-symmetric-encryption-and-aead](../03-symmetric-encryption-and-aead/2-summary.md) · [05-mac-and-hmac](../05-mac-and-hmac/2-summary.md) · [16-identifiers-and-enumeration](../16-identifiers-and-enumeration/2-summary.md)
  - [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) §6 — 로그 PII와 삭제 범위
  - [data-engineering/12-data-retention-and-erasure](../../data-engineering/12-data-retention-and-erasure/2-summary.md) — 보존·삭제 전파·crypto-shredding
  - [engineering-practice/17-legal-standards](../../engineering-practice/17-legal-standards/2-summary.md) — 법적 의무·보존
  - security 29-security-symptom-index · 30-security-incidents
- 1차 출처
  - NIST SP 800-122 Guide to Protecting the Confidentiality of PII(2010-04) — 기밀성 영향 수준 low/moderate/high, 최소 수집·비식별화 <https://csrc.nist.gov/pubs/sp/800/122/final>
  - OWASP Logging Cheat Sheet "Data to exclude" <https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html>
  - GDPR Art. 17 Right to erasure — (1) "without undue delay", (3) 예외(표현의 자유·법적 의무·공공보건·기록보존·법적 청구의 제기·행사·방어) <https://gdpr-info.eu/art-17-gdpr/>
  - PCI DSS v4.0 요건 3.4.1 — 표시 시 BIN + 마지막 4자리 원칙, 업무상 근거 있는 역할 예외, 3.5.1(저장 PAN 보호)과 별개 — PCI SSC FAQ 1492 <https://www.pcisecuritystandards.org/faqs/1492/> (표준 본문 PDF는 원문 대조 못 함)
  - 개인정보보호위원회 「가명정보 처리 가이드라인」(2024-02 개정판) — 가명처리 기준[?] (2025 개정안 의견수렴 중)
- 실험(로컬, `--network none`, OpenJDK 21.0.12 Temurin)
  - redaction: 거부 목록은 공백 없는 카드·흘려 쓴 이메일을 흘림, 허용 목록은 안전 필드만 남김
  - 표시 마스킹 `411111******1111`
  - 가명: SHA-256(전화)는 후보 1만 개를 약 0.3초(234~315 ms)에 열거 복원, HMAC은 같은 가명·키 없이 불가
  - crypto-shredding: 키 파기 후 백업 암호문(31바이트) 복호 불가
