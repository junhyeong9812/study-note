# cs/issue/security/searchable-encryption-blind-index — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답
<!-- 질문 1:1 대응 -->

1. **패턴 은닉을 위한 설계다.** 같은 평문이 같은 암호문이 되면, 암호문만 봐도 "이 두 행은 같은 값"이라는 정보가 샌다(빈도 분석).\
   salt·IV를 섞어 매번 다른 암호문을 내면 이 정보가 사라진다 — 대신 암호문끼리 비교하는 능력도 함께 사라진다.
   > **salt / IV** — 암호화마다 섞는 무작위 값. 같은 평문이 같은 출력을 내지 않게 한다.

2. **조회도 중복 판정도 안 된다.** 입력을 다시 암호화해 비교해도 salt가 달라 일치하는 행이 없다 — 이미 가입한 이메일도 "없음"으로 판정된다.\
   부분 검색(LIKE)은 암호문이 평문의 부분 구조를 보존하지 않으므로 더욱 불가능하다.

3. **작은 입력 공간은 사전으로 뒤집힌다.** 이메일은 무작위 값이 아니라 추측 가능한 문자열이다. 평문 SHA-256은 키가 없으므로, 해시 컬럼이 유출되면 후보 이메일 목록을 해시해 대조하는 것만으로 원문을 복원할 수 있다.\
   HMAC은 비밀 키(pepper)를 알아야 같은 값을 만들 수 있으므로, DB만 유출돼서는 사전 대입이 성립하지 않는다. 키는 코드가 아닌 환경변수로 외부화한다.
   > **blind index** — 암호화된 값을 동등 조회하기 위해 별도로 두는 키 기반 결정적 해시 컬럼.
   > **pepper** — DB 밖(설정·비밀 저장소)에 두는 비밀 키. 행마다 다른 salt와 달리 전체에 공통이다.

4. **정규화 차이가 곧 중복 방지 우회다.** 해시 쪽만 소문자로 바꾸고 암호화 쪽은 원문을 쓰거나, 그 반대면 `A@x.com`과 `a@x.com `이 서로 다른 해시가 되어 같은 사람이 두 번 가입된다.\
   암호화·해시 모두 **같은 함수(trim + lower)** 를 거친 뒤 처리한다.

5. **DB 제약이 판정한다.** 두 요청이 모두 "조회 결과 없음"을 본 뒤 INSERT하면, 해시 컬럼 UNIQUE 제약이 하나만 통과시키고 다른 하나는 무결성 위반으로 실패한다.\
   애플리케이션은 이 예외를 잡아 **409(이미 존재)** 로 바꾼다 — 앱 코드의 사전 조회는 경합을 막지 못하므로 최종 판정은 제약에 맡긴다.

6. **암호문 = 복원·표시·발송, HMAC = 조회·유일키.** 원문이 필요한 곳(메일 발송·관리 화면 표시)은 가역 암호문을 복호화하고, 찾기·중복 판정은 HMAC 컬럼만 쓴다.\
   결정적 암호화(AES-SIV 류)는 한 컬럼으로 복원과 동등 조회를 모두 하지만, 같은 평문 = 같은 암호문이라는 동등성 정보를 암호문 자체가 드러낸다 — 기록에는 후속 공부 대상으로만 남아 있다.

## 문제 구조 (추상화 코드)

### 변형 A — 비결정 암호문으로 동등 조회
① 문제 코드
```java
String enc = cipher.encrypt(email);                          // salt 포함 → 매번 다름
boolean exists = repo.existsByEmail(cipher.encrypt(email));  // 항상 false
repo.save(new Subscriber(enc));                              // 중복 가입
```
② 고친 코드
```java
String normalized = email == null ? "" : email.trim().toLowerCase();   // 두 경로 공통 정규화
String enc  = cipher.encrypt(normalized);                              // 복원·표시·발송용
String hash = hmacHex(pepper, normalized);                             // 조회·유일키용 (CHAR(64) UNIQUE)
try {
    repo.save(new Subscriber(enc, hash));
} catch (DataIntegrityViolationException e) {
    throw new Conflict();                                              // 동시 가입 경합 → 409
}

static String hmacHex(byte[] key, String v) {
    Mac mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(key, "HmacSHA256"));
    return HexFormat.of().formatHex(mac.doFinal(v.getBytes(UTF_8)));
}
```
무엇이 깨졌나: 패턴 은닉용 비결정 출력을 동등 비교에 쓰려 했다.\
같은 구조: 부분 검색·중복 판정이 필요한 다른 암호화 컬럼도 설계 단계에서 같은 이유로 결정적 해시 컬럼 분리가 필요하다고 기록됐다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
