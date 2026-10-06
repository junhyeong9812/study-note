# security/26-security-logging-and-audit — 보안 로그·감사 추적·단계적 강제 — 정리 (힌트)

## 해결하는 문제

보안 사건이 나면 세 가지를 물어야 한다: 무슨 일이 있었나, 누가 했나, 언제부터인가.\
그 답은 **사건 당시에 남겨 둔 기록**에만 있다. 사후에 만들 수 없다.

```text
  정상 운영 ──▶ 침해 ──▶ 탐지(며칠~몇 달 뒤) ──▶ "범위를 산정하라"
                                                    │
                             로그가 없거나 지워졌거나 보존 기한이 지났으면 → 답할 수 없다
                             로그에 토큰·PII가 있으면 → 로그 유출이 2차 유출이 된다
```

- 두 실패가 쌍을 이룬다(OWASP Top 10 2021 A09 Security Logging and Monitoring Failures).
  - **덜 남김**: 로그인·실패·고가 거래 같은 감사 대상 사건을 안 남겨, 침해 범위·경로를 못 밝힌다(CWE-778 Insufficient Logging).
  - **잘못 남김**: 로그에 비밀번호·토큰·PII를 남겨(CWE-532), 또는 로그 주입을 허용해(CWE-117) 로그 자체가 공격면이 된다.
- 또 하나: **이미 도는 시스템에 인가를 새로 켤 때** 그냥 켜면 아직 인증을 안 붙이는 정상 호출이 전부 끊긴다. 관측(audit) 먼저, 강제(enforce) 나중이라는 순서가 필요하다.

쉬운 예: 건물에 CCTV를 다는 일이다.\
사건이 난 **뒤에** "그때 화면 좀 봅시다"는 통하지 않는다. 미리 달려 있고(남김), 저장 기간 안이어야(보존) 하고, 화면에 비밀번호 메모가 찍혀 있으면 안 된다(남기지 말 것). 그리고 출입 통제를 새로 켤 때는 "기록만 하는 기간"을 먼저 둔다.

> 기초는 원본 [`foundations/security/audit-enforce-rollout.md`](../../foundations/security/audit-enforce-rollout.md). audit/enforce 두 모드와 무중단 이관 절차는 그 원고가 정본이다. 이 leaf는 거기 없던 **네 기록 구분·로그 주입·보존·장애·실험·질문**을 채운다.

실무 예:
- 환불 요청을 처리했는데 그게 감사 테이블이 아니라 앱 로그에만 남아, 90일 뒤 분쟁 때 증거가 없다.
- 요청 바디 전체를 INFO로 찍어 카드번호가 로그 수집기와 외부 SaaS로 복제된다(27번).
- 로그인 폼에 넣은 개행 문자가 로그에 "login success admin"이라는 가짜 줄을 심는다.

## 동작·원리

### 1. 네 기록은 목적이 다르다

```text
  앱 로그(debug)   : 개발자가 디버깅. 샘플링·레벨 조정으로 버려질 수 있다. 짧은 보존.
  메트릭          : 수치 집계(초당 401 수). 개별 사건은 모른다.
  트레이스        : 요청 하나의 경로·지연. head 샘플링이면 그 요청이 아예 없을 수 있다.
  감사 로그(audit) : "누가 무엇을 했다"의 법적·보안적 사실. 지우면 안 되고, 보존 기한이 정해진다.
```

- 네 기록의 성질·역할은 [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md)가 정본이다. 핵심 한 줄: **감사 사건을 앱 로그로 대신하지 않는다.** 앱 로그는 레벨·샘플링으로 조용히 사라지도록 설계돼 있다.
- 보안 로그는 감사 로그 쪽에 가깝다. OWASP Logging Cheat Sheet가 "언제·어디서·누가·무엇을"(when, where, who, what)을 필수 속성으로 든다.

### 2. 무엇을 남기고, 무엇은 남기지 않나

```text
  남긴다(OWASP Logging Cheat Sheet)         남기지 않는다("Data to exclude")
  · 인증 성공·실패(크리덴셜 공격 탐지)        · 비밀번호·세션 ID·토큰·암호키
  · 인가 실패                               · 카드번호 등 결제 데이터
  · 입력·검증 실패                           · 보호 대상 개인/건강 정보(법적 허용 없이는)
  · 관리 행위(권한 변경·사용자 관리)
  · 민감 데이터 접근 · 이상 업무 흐름
```

- 남길 것은 **보안 의사결정 지점**이다. "거부했다/허용했다"와 그 주체·대상. 남기지 말 것은 **그 자체가 비밀**인 값이다.
- 식별자는 내부 ID(가명)로 남긴다. 원본 PII는 감사에 꼭 필요한 최소만, 보존 기한과 함께(27번).

### 3. 로그 주입 — 로그가 공격면이 된다 (CWE-117)

```text
  입력 user = "kim\n2026-... INFO login success user=admin role=ADMIN"
  평문 연결: TS + " INFO login failed user=" + user
        → 개행이 그대로 들어가 "가짜 성공 줄"이 로그에 생긴다 (한 입력이 두 줄이 된다)
  방어: 제어 문자 이스케이프, 또는 값을 문자열 리터럴로 인코딩하는 구조화(JSON) 로그
```

(실험, OpenJDK 21.0.12 Temurin, `--network none`, 2026-10-07)

```text
== 평문 연결 (줄 수=2)
  | 2026-10-07T01:00:00Z INFO login failed user=kim
  | 2026-10-07T01:00:00Z INFO login success user=admin role=ADMIN      ← 공격자가 심은 가짜 줄
== 이스케이프 (줄 수=1)
  | 2026-10-07T01:00:00Z INFO login failed user=kim\n2026-10-07T01:00:00Z INFO login success user=admin role=ADMIN
== JSON (줄 수=1)
  | {"ts":"...","level":"INFO","event":"login_failed","user":"kim\n2026-10-07T01:00:00Z INFO login success user=admin role=ADMIN"}
```

- 관찰: 평문 연결은 한 입력이 **두 줄**이 됐다. 뒤 줄은 공격자가 심은 "로그인 성공 admin"이다. 사고 조사자나 로그 파서가 이걸 진짜 사건으로 읽으면 오판한다.
- 이스케이프판·JSON판은 모두 **한 줄**이었다. 개행이 `\n` 리터럴로 들어가 줄을 쪼개지 못했다. 구조화 로그는 값이 필드 안에 갇혀 이 문제를 구조적으로 막는다(reliability/15-logging). 단 이 실험의 JSON판은 값을 직접 JSON 이스케이프해 만든 것이다. 실제 로거에서는 JSON 인코더를 설정해야 같은 결과가 난다(적용 §3).

### 4. 변조 탐지 — 해시 체인과 그 한계

- 감사 로그는 "지운/고친 흔적"이 드러나야 한다. 기록마다 직전 기록의 해시를 넣어 체인을 만든다.
- 중간 하나만 고치면 그 행 해시가 어긋나고, 뒤까지 다시 계산하면 체인은 맞지만 **체인 밖에 둔 고정점(anchor)**과 어긋난다.
- 이 실험과 한계(체인만으로는 전체 재계산을 못 잡고, 고정점을 다른 신뢰 영역에 둬야 함)는 [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) §5가 정본이다. 핵심: **해시 체인은 막지 않고 탐지한다.** 여러 기록을 한 번에 증명하려면 머클 트리로 확장한다([data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md), network/31 CT).

### 5. audit → enforce — 끊지 않고 인가를 켠다

```text
  ① 클라이언트 먼저 배포(모든 호출에 서명) 
  ② 서버 audit: 검사하되 무서명도 통과 + 기록 (보안 경계 아직 안 섬)
     로그에서 "모든 호출이 서명을 붙인다" 확인
  ③ 서버 enforce: 무서명 거절(401). 무서명 경로가 닫힌다 (호출자별 권한 확인은 별도 — 15번)
  고정 규칙: 틀린 서명은 두 모드 다 거절 / 기본값 = enforce(fail-closed) / 키 없으면 audit여도 기동 거부
```

- 두 모드와 순서·위험은 원본이 정본이다. 여기서는 **판정 로직을 실험으로 확인**한다.

(실험, OpenJDK 21.0.12 Temurin, `--network none`, 2026-10-07 — HMAC-SHA256, 테스트 키)

```text
mode     | 유효 서명     | 틀린 서명     | 서명 없음
AUDIT    | PASS_VALID   | REJECT_401   | PASS_UNSIGNED_WARN
ENFORCE  | PASS_VALID   | REJECT_401   | REJECT_401
-- 설정 해석
auth.mode=null   → ENFORCE          (기본값 = 닫힘)
auth.mode=audti  → 알 수 없는 auth.mode=audti → 기동 거부
서명 키 없음 → audit 모드여도 기동 거부
-- audit 관측 집계 (caller: 서명/무서명)
  deploy-agent: 3/0
  nightly-cron: 0/2
enforce 전환 가능? false  ← 무서명 호출자가 남아 있다
```

- 관찰 1: audit가 봐주는 것은 **"서명 없음"뿐**이다. 틀린 서명은 두 모드 다 `REJECT_401`. 원본의 "틀린 서명은 두 모드 다 거절"과 일치.
- 관찰 2: 모드 미설정은 `ENFORCE`(fail-closed), 오타(`audti`)·키 없음은 **기동 거부**. 설정 실수가 조용히 문을 여는 것을 막는 세 장치다.
- 관찰 3: audit 집계가 `nightly-cron: 0/2`(무서명 2건)을 보여 `enforce 전환 가능? false`로 판정했다. **enforce 전환 시점을 감이 아니라 로그로** 정한다는 원본 §4를 그대로 보인 것이다.

## 쓰이는 자료구조·알고리즘

- **해시 체인 / 머클 트리** — 변조 탐지. 체인은 연결 리스트, 다중 증명은 트리. [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) · [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
- **HMAC** — audit/enforce가 판정하는 요청 서명. [security 05-mac-and-hmac](../05-mac-and-hmac/2-summary.md)
- **상수 시간 비교** — 서명 대조는 `MessageDigest.isEqual`로. 타이밍 누출을 줄인다(05번).
- **append-only 저장 + 집합(폐기·허용 목록)** — 감사 테이블은 추가만, 로그 필드 필터는 허용/거부 목록.
- **인가 결정 흐름** — audit/enforce는 "판정하되 막느냐"의 분기. fail-safe 기본값(security/01).

## 적용 — 풀어나가는 법

### 1. 순서

1. **감사 사건과 앱 로그를 분리**한다. 감사는 업무 트랜잭션과 같은 DB 트랜잭션에 추가만 하는 테이블로(reliability/18 §4가 정본).
2. 로그에 넣기 전 **제어 문자를 막고**, 가능하면 구조화(JSON) 로그를 쓴다(§3 실험).
3. **남기지 말 것 목록**(OWASP Data to exclude)을 공용 redaction으로 강제한다(27번).
4. 보안 기능을 켤 때는 **audit → enforce** 순서(원본), 전환은 로그로 판정.
5. 보존 기한을 정하고(27번), 기한 전 파기·기한 후 보관을 둘 다 막는다.

### 2. 감사와 업무를 한 트랜잭션에 (Java, Spring + JDBC)

- 환불과 감사 기록을 같은 트랜잭션에 묶어 "있어야 할 기록이 없거나, 없던 일이 기록되는" 틈을 없애는 코드는 [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) §2가 정본이다(여기서 중복하지 않는다).

### 3. 로그 주입 방어 (Java 21)

```java
// 취약: 사용자 입력을 그대로 이어 붙임
log.info("login failed user=" + user);          // user에 개행이 있으면 줄이 쪼개진다

// 고친 판 1: 구조화 로그 (권장) — 단 출력 인코더가 JSON이어야 값이 필드 안에 갇힌다
log.atInfo().addKeyValue("event", "login_failed").addKeyValue("user", user).log();
// logback.xml: <encoder class="ch.qos.logback.classic.encoder.JsonEncoder"/>  (값을 JSON 이스케이프)
// 기본 패턴의 %kvp는 user="..."로 따옴표만 두르고 개행을 그대로 쓴다 → 이 줄만으로는 못 막는다

// 고친 판 2: 평문이 불가피하면 제어 문자 이스케이프
String safe = user.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n");
log.info("login failed user={}", safe);
```

### 4. audit/enforce 토글 (설정)

```text
# 기본값은 enforce. audit는 이관 중에만 명시적으로.
auth.mode=audit        # 과도기: 무서명도 통과 + 경고 기록
# 로그에서 무서명 경고가 0이 된 뒤
auth.mode=enforce      # 무서명 거절
```

- 키가 없으면 audit여도 기동을 거부하도록 둔다(실험). "관측할 수단(키)이 없으면 뜨지 않는다"가 audit의 정직성을 지킨다(원본 §4).

### 5. 진단

```bash
# 무서명 경고 추이 (enforce 전환 판정)
grep -c 'auth=unsigned' app.log
# 로그에 들어가면 안 되는 값이 새는지 (헤더·토큰·카드 패턴)
grep -E 'password=|authorization: bearer|[0-9]{13,16}' app.log | head
```

## 장애 시나리오와 대처

### 1. 감사 사건을 앱 로그에만 남겨, 보존 기한 뒤 증거가 없다 (⚠ 커리큘럼)

- **현상**: 분쟁·침해 조사 때 "그 처리 기록이 없다".
- **보이는 형태**: 앱 로그 보존(예: 30~90일)이 짧아 해당 시점이 이미 사라짐. 샘플링으로 그 줄이 애초에 안 남음.
- **원인**: 감사 대상 사건을 debug 로그로 취급. 앱 로그는 조용히 버려지도록 설계됨.
- **대처**: 감사 테이블로 분리, 보존 기한을 사건 종류별로. 상세는 reliability/18.

### 2. 로그에 토큰·PII를 남겨 로그 유출이 2차 유출이 된다 (CWE-532)

- **현상**: 로그 저장소·외부 SaaS에서 비밀번호·카드번호·이메일이 발견된다.
- **보이는 형태**: 요청/응답 바디 전체 로깅, 예외 메시지에 PII, `grep`으로 토큰 패턴이 잡힘.
- **원인**: 디버깅 편의로 바디를 통째로 찍음. redaction 미적용.
- **대처**: 남기지 말 것 목록을 공용 필터로 강제. 로그 접근 통제·보존 관리. 상세 27번.

### 3. 로그 주입으로 조사 결과가 오염된다 (CWE-117)

- **현상**: 로그에 일어난 적 없는 "성공" 줄이 있다. 로그 파서·알림이 오작동한다.
- **보이는 형태**: 한 요청이 여러 줄로 쪼개짐(§3 실험). 사용자 값 자리에 타임스탬프·레벨 문자열.
- **원인**: 사용자 입력을 이스케이프 없이 평문 로그에 이어 붙임.
- **대처**: 구조화 로그 또는 제어 문자 이스케이프.

### 4. 감사 로그가 지워졌는데 모른다 (무결성)

- **현상**: 침해자가 흔적을 지웠을 수 있는데 확인할 길이 없다.
- **보이는 형태**: 순번이 비거나, 체인 해시가 어긋나거나(탐지됨), 아무 장치도 없어 알 수 없음(최악).
- **원인**: 변조 탐지 장치 부재, 또는 고정점을 같은 저장소에 둠.
- **대처**: 해시 체인 + **다른 신뢰 영역의 고정점**, WORM 저장소·별도 계정. 관리자 권한자의 변경은 탐지와 저장소 분리로 다룬다(reliability/18 §5).

### 5. enforce로 바로 켜서 정상 호출이 끊긴다

- **현상**: 보안 강제를 켠 직후 구버전 클라이언트·배치의 정상 호출이 전부 401.
- **보이는 형태**: 배포 직후 401 폭증, 특정 호출자(cron·agent)에 집중.
- **원인**: 클라이언트가 아직 서명을 안 붙이는데 서버를 먼저 enforce로 올림.
- **대처**: 원본의 순서(클라이언트 먼저 → audit 관측 → enforce). 문제 시 audit로 되돌리면 무서명이 다시 통과(싼 롤백). 전환은 무서명 경고 0을 로그로 확인한 뒤.

## 핵심 문장

- 보안 질문의 답은 사건 당시 기록에만 있다 — 로그는 사후에 만들 수 없다.
- 로깅 실패는 쌍이다: 덜 남겨 범위를 못 밝히거나(CWE-778), 잘못 남겨 로그가 공격면이 된다(CWE-532·CWE-117).
- 감사 사건을 앱 로그로 대신하지 않는다 — 앱 로그는 샘플링·레벨로 조용히 사라지도록 설계돼 있다.
- 평문 연결 로그는 개행 한 번에 가짜 줄이 생긴다. 구조화 로그는 값을 필드 안에 가둬 이를 막는다(실험).
- audit는 "서명 없음"만 봐준다 — 틀린 서명은 두 모드 다 거절하고, 기본값은 enforce, 키 없으면 기동 거부다(실험).

## 관련 주제·근거

- 기초(정본)
  - [`foundations/security/audit-enforce-rollout.md`](../../foundations/security/audit-enforce-rollout.md) — audit/enforce 두 모드, 무중단 이관, fail-closed
  - [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) — 네 기록 구분, 감사 테이블, 해시 체인, 보존
- 선행·연결
  - [security 01-security-principles](../01-security-principles/2-summary.md) — fail-safe 기본값·완전한 중재
  - [security 05-mac-and-hmac](../05-mac-and-hmac/2-summary.md) — 서명·상수 시간 비교
  - [27-pii-classification-masking-retention](../27-pii-classification-masking-retention/2-summary.md) — redaction·보존·파기
  - [reliability/15-logging](../../reliability/15-logging/2-summary.md) — 구조화 로그·샘플링·레벨
  - [engineering/development-standards/security-standards](../../engineering/development-standards/security-standards/2-summary.md) — 보안 로깅 표준
  - [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) · [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
  - security 29-security-symptom-index · 30-security-incidents
- 1차 출처
  - OWASP Top 10 2021 A09 Security Logging and Monitoring Failures — CWE-778·CWE-117·CWE-223·CWE-532, "Auditable events ... are not logged", "Logs are only stored locally" <https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/> · 2025판 A09 Security Logging and Alerting Failures <https://owasp.org/Top10/2025/>
  - OWASP Logging Cheat Sheet — "when, where, who and what", Data to exclude, 변조 탐지, 보존 <https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html>
- 실험(로컬, `--network none`, OpenJDK 21.0.12 Temurin)
  - 로그 주입: 평문 연결은 2줄(가짜 성공 줄), 이스케이프·JSON은 1줄
  - audit/enforce: audit는 무서명만 통과·틀린 서명 거절, 기본값 enforce, 오타·키 없음 기동 거부, 무서명 집계로 enforce 전환 판정
