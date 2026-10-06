# security/16-identifiers-and-enumeration — 식별자와 열거: 순차 ID vs 랜덤·불투명 식별자 — 정리 (힌트)

## 해결하는 문제

밖에 보이는 식별자는 공격자에게 **지도**가 된다.

```text
  GET /api/customers/5332   → 200 (내 정보)
  GET /api/customers/5333   → 200 ?   ← 번호 하나 올렸을 뿐
  GET /api/customers/5334   → 200 ?
  ...  스크립트 한 줄이면 전체 고객 테이블을 훑는다 (열거)

  인가가 빠져 있으면(15번)  → 대량 유출
  인가가 있어도             → 403/404 차이로 "존재하는 번호" 수집, 최대 번호로 규모 추정
```

- *열거(enumeration)*: 식별자 공간을 차례로 훑어 존재하는 대상을 찾아내는 일.
- 막는 층은 둘이다.
  - 첫째 층(필수): 객체 수준 인가. 번호를 알아도 남의 것은 못 연다(15번).
  - 둘째 층(보강): 밖에 보이는 ID를 추측하기 어렵게 만든다. 인가가 하나 빠졌을 때 피해를 "번호 하나"로 묶는다.
- 랜덤 ID는 둘째 층일 뿐이다. RFC 9562 §8: UUID가 추측하기 어렵다고 가정하면 안 되고(SHOULD NOT), "보유만으로 접근을 주는 보안 수단"으로 쓰면 안 된다(MUST NOT).
- 쉬운 예: 사물함 번호.
  - 번호가 1, 2, 3…이면 옆 칸을 쉽게 짐작한다. 자물쇠(인가)가 없으면 다 열린다.
  - 번호를 무작위 12자리로 바꾸면 옆 칸을 짐작하기 어렵다. 그래도 자물쇠는 달아야 한다.
- 실무 예
  - 호주 통신사 Optus 2022 유출: 호주 통신미디어청(ACMA)은 접근 제어 코드 오류로 인터넷에 노출된 API가 우회됐다고 주장했다(연방법원 소장, 2024). "고객 식별자가 순차여서 스크립트로 훑었다"는 설명은 2차 보도에만 있다 `[?]`.
  - 주문 번호가 1씩 오르면 경쟁사가 하루 두 번 주문해 하루 주문량을 안다.

기초 — 이름(바뀌고 재사용됨)과 불변 ID, 그리고 "누가"(플랫폼 수치 ID)와 "무엇"(내용 주소) 두 축은 원본 [identity-and-ids §1~§3](../../foundations/security/identity-and-ids.md)에 있다. 요약: 검증은 불변 ID로, 표시는 이름으로. 이 노트는 그 ID가 **밖에 보일 때** 생기는 문제를 다룬다.

## 동작·원리

### 1. 식별자에 요구하는 성질 네 가지

```text
                     유일성     불변성     추측 어려움     드러내는 정보
  이름(acme/core)     △          ✗          ✗              사람이 읽는 뜻
  순차 bigint         ✔          ✔          ✗              생성 순서·총량
  UUIDv4              ✔(확률)    ✔          ✔(122비트)      없음
  UUIDv7 / ULID       ✔(확률)    ✔          △(시각은 공개)  생성 시각(밀리초)
  내용 주소(SHA-256)   ✔(충돌저항) ✔         내용을 알면 계산  내용 동일 여부
```

- SHA-256의 ✔는 "같은 해시가 절대 없다"가 아니라 "충돌을 찾기가 계산상 어렵다"(기대 충돌 저항 128비트, NIST SP 800-107 Rev.1 §4.1)는 뜻이다.
- 원본 §1·§2가 다룬 것은 유일성·불변성이다. 열거는 세 번째·네 번째 칸의 문제다.
- 참고: 원본 §2는 commit SHA를 "위조하려면 해시를 깨야 한다"고 적는다. git의 기본 객체 이름은 SHA-1이고, 2017-02-23 SHAttered가 SHA-1 충돌을 실제로 만들었다. git 2.13.0부터 충돌 공격을 탐지하는 강화된 SHA-1 구현을 기본으로 쓴다(git 문서 hash-function-transition). "깨야 한다"는 방향은 맞지만 SHA-1 자체는 약하다고 문서가 적는다.

### 2. 순차 ID가 새는 세 가지

```text
  ① 열거      1, 2, 3, ... n   → 시도 n번이면 전부 적중
  ② 규모 추정  내가 받은 번호 m₁ < m₂ < ... < m_k  → 최대값 m 근처가 전체 수
  ③ 속도 추정  오늘 받은 번호 − 어제 받은 번호 ≈ 하루 생성량(대략)
```

- ③은 근사다. PostgreSQL 시퀀스는 롤백·`ON CONFLICT`로 버려진 번호도 소비해 빈 번호가 생긴다(PostgreSQL 시퀀스 함수 문서). 차이는 실제 건수보다 크거나 같은 추정치다.

- ②는 통계에서 "독일 전차 문제"로 알려진 추정이다. 표본 k개의 최대값 m에서 전체 수를 m + m/k − 1로 추정한다(최소분산 불편 추정량 — 2차 출처 Wikipedia "German tank problem").

### 3. 랜덤 ID — 추측 적중 기대값

```text
  b비트 랜덤 공간 2^b 안에 객체 n개, 공격자가 g번 무작위 추측
  기대 적중 수 ≈ g · n / 2^b

  예) b=64, n=10⁴, g=10⁵  →  10⁹ / 1.8×10¹⁹ ≈ 5.4×10⁻¹¹
```

- 추측 어려움은 비트 수와 **생성기**에 달려 있다. RFC 9562 §6.9는 CSPRNG(암호학적으로 안전한 의사난수 생성기)를 쓰라고 권한다(SHOULD). 예측 가능한 생성기면 비트 수가 커도 소용없다(09번).
  - *CSPRNG*: 출력 일부를 봐도 다음 출력을 예측할 수 없는 난수 생성기. Java는 `SecureRandom`.

### 4. 생일 경계 — 짧은 랜덤 ID는 충돌한다

```text
  N = 2^b 칸에 k개를 무작위로 넣을 때
  충돌 쌍 기대값      ≈ k(k−1) / (2N)
  충돌이 하나라도 날 확률 ≈ 1 − exp(−k² / 2N)
  50%가 되는 k         ≈ √(2N ln 2) ≈ 1.177 √N

  32비트: k ≈ 7.7×10⁴     48비트: 2.0×10⁷     64비트: 5.1×10⁹     122비트(UUIDv4): 2.7×10¹⁸
```

- 직관과 다르게 칸 수의 **제곱근**에서 충돌이 흔해진다. 32비트(약 43억 칸)라도 7만 7천 개쯤이면 반반이다.
  - *생일 경계(birthday bound)*: 무작위 값 k개 중 같은 값이 나올 확률이 √N 근처에서 급격히 커진다는 성질. 23명이면 생일이 겹칠 확률이 50%를 넘는(정확히 계산하면 50.7%) 것과 같은 계산이다.
- RFC 9562 §6.7은 충돌의 영향이 큰 곳(잘못된 대상에 연결되는 경우)이면 충돌 저항을 최대한 확보하라고 적는다.

### 5. UUID·ULID의 비트 배치와 노출

```text
  UUIDv4  [ random_a 48 ][ver 4][ random_b 12 ][var 2][ random_c 62 ]   랜덤 122비트 (RFC 9562 §5.4)
  UUIDv7  [ unix_ts_ms 48 ][ver 4][ rand_a 12 ][var 2][ rand_b 62 ]     앞 48비트 = 밀리초 시각 (§5.7)
  ULID    [ 시각 48비트 ][ 랜덤 80비트 ]  Crockford base32 26자 (ULID 명세)
```

- UUIDv7·ULID는 정렬이 대체로 시간순(밀리초 단위)이라 인덱스에 유리하다. 같은 밀리초 안의 순서는 기본 보장이 아니다 — ULID 명세 "Sorting"은 보장하지 않는다고 적고, RFC 9562 §6.2는 카운터 같은 추가 방식을 둔다([database/28](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md)). 대신 **생성 시각이 문자열에 들어 있다.** 실험이 v7 문자열에서 시각을 다시 꺼냈다.
- RFC 9562 §8: 내장 시각은 "아주 작은 공격 표면"이고 생성 순서를 알려 준다. 보안 동작에 UUID를 쓰면 UUIDv4를 쓰라(SHOULD).
- ULID 명세의 단조(monotonic) 모드는 같은 밀리초 안에서 랜덤 부분을 **1 증가**시킨다. 명세 예: `01BX5ZZKBKACTAV9WEVGEMMVRZ` 다음이 `01BX5ZZKBKACTAV9WEVGEMMVS0`. 한 값을 알면 같은 밀리초의 다음 값을 안다.

### 6. 내부 키와 외부 ID를 나눈다

```text
  DB 내부                               API 밖
  orders.id        bigint 시퀀스  ──X──  (노출 안 함)
  orders.public_id 128비트 랜덤   ─────>  /orders/Vq3x...  (불투명, 추측 어려움)
  + 조회는 그대로  WHERE public_id = ? AND owner_id = ?   (15번 인가)
```

- 내부 PK는 조인·인덱스 효율로 고르고, 외부 ID는 노출 정보로 고른다. 둘의 요구가 다르다([database/28](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md)의 같은 결론).
  - *불투명 식별자(opaque identifier)*: 받는 쪽이 내부 구조·순서·의미를 읽어 낼 수 없는 식별자.

### 실험: 열거 적중, 32비트 생일 충돌, UUIDv7 시각 노출

`IdDemo.java` — 순차 ID 1..10⁴와 64비트 랜덤 ID 10⁴개에 각각 10⁵번 추측, 32비트 랜덤 ID 10만 개를 20번 뽑아 충돌 쌍 수 세기, v4/v7 생성과 v7 시각 복원. 난수는 `SecureRandom`.

```java
for (long g = 1; g <= guesses; g++) if (seq.contains(g)) hitSeq++;            // 1부터 차례로
for (int i = 0; i < guesses; i++) if (r64.contains(rnd.nextLong())) hitR++;   // 64비트 무작위
// 생일: 32비트 값 k개의 충돌 쌍 수 = Σ c(c-1)/2
for (int i = 0; i < k; i++) cnt.merge(rnd.nextInt(), 1, Integer::sum);
// v7 시각 복원
Instant.ofEpochMilli(v7.getMostSignificantBits() >>> 16)
```

(실험, OpenJDK 21.0.12 eclipse-temurin:21-jdk 컨테이너 `--network none`, 2026-10-07, 3회 실행 중 1회차)

```text
enumeration: guesses=100000  sequential hits=10000  random64 hits=0 (expected 5.42e-11)
birthday 32-bit: k=100000 trials=20  colliding pairs avg=1.35 min=0 max=3  expected=1.16
   32 bits: 50% collision at k~7.716e+04   P(collision) for k=1e6: 1.000e+00
   48 bits: 50% collision at k~1.975e+07   P(collision) for k=1e6: 1.775e-03
   64 bits: 50% collision at k~5.057e+09   P(collision) for k=1e6: 2.711e-08
   80 bits: 50% collision at k~1.295e+12   P(collision) for k=1e6: 4.136e-13
  122 bits: 50% collision at k~2.715e+18   P(collision) for k=1e6: 9.404e-26
v4=534ebeca-b97e-4306-845d-24d5d5e7abbc version=4
v7=01a113a8-ec00-7e57-9adf-61b05cb504d8 version=7  decoded time=2026-10-07T00:00:00Z
```

- 관찰
  - 순차 ID는 10⁵번 추측에 10⁴개 전부 적중했다. 64비트 랜덤은 3회 모두 0이었다(기대값 5.4×10⁻¹¹).
  - 32비트 10만 개의 충돌 쌍 평균은 3회 실행에서 1.35·1.30·0.80(각 20회 평균, 회당 최소 0·최대 2~3)이었다. 점검 재실행 3회는 0.80·1.00·1.40(회당 최대 3~4)이었다. 이론값 1.16 근처에서 흔들린다. 10만 개면 충돌이 하나 이상 날 확률이 약 69%(1 − exp(−k²/2N))다. 회당 0쌍인 회차도 있었으니 반드시 나지는 않지만 흔하다.
  - 50% 지점과 k=10⁶에서의 확률 행은 공식 계산값이다(실측이 아님).
  - v7은 시각을 고정(2026-10-07T00:00:00Z)해 만들었고, 문자열 앞 48비트에서 같은 시각이 복원됐다. 실서비스 v7 ID를 받은 사람은 내장 타임스탬프를 밀리초까지 읽는다. 보통 UUID를 만든 시각이라 객체 생성 시각을 짐작할 수 있다(RFC 9562 §6.2는 카운터 넘침 때 타임스탬프를 실제보다 앞당기는 것도 허용(MAY)하므로 정확히 같다는 보장은 없다).

## 쓰이는 자료구조·알고리즘

- **UUIDv4 / UUIDv7 / ULID**: 위 비트 배치. v7·ULID는 "시각 상위 + 랜덤 하위" 비트 필드다. v7 하위 74비트는 RFC 9562 §5.7상 밀리초 미만 시각·카운터를 섞을 수도 있다(MAY)([distributed/13-distributed-id-generation](../../distributed/13-distributed-id-generation/2-summary.md)).
- **생일 경계**: 충돌 확률 1 − exp(−k²/2N). 수학 영역 05 `counting-and-birthday-bound`는 미작성 — [math 영역 표](../../math/README.md).
- **해시 집합**: 실험의 적중 판정·충돌 계수. DB에서는 `UNIQUE` 제약 인덱스가 같은 역할을 하며 충돌을 오류로 드러낸다([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- **Crockford base32·base64url 인코딩**: 비트를 짧은 문자열로. base32는 I·L·O·U를 빼 사람이 옮겨 적을 때 혼동을 줄인다(ULID 명세). base64url은 6비트/자.
- **토큰 버킷**: 열거 속도를 늦추는 주체별 요청 상한([reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 외부 ID 생성 — 취약 예 → 고친 예

```java
// 취약 ①: 내부 시퀀스를 그대로 노출
return "/orders/" + order.getId();                    // 1001, 1002, ...

// 취약 ②: 예측 가능한 생성기 + 짧은 길이
String code = Integer.toString(new java.util.Random().nextInt(1_000_000));   // 20비트 남짓, 비-CSPRNG

// 고친 예: CSPRNG 128비트, URL 안전 문자열 22자
public final class PublicIds {
    private static final java.security.SecureRandom RNG = new java.security.SecureRandom();
    public static String next() {
        byte[] b = new byte[16];
        RNG.nextBytes(b);
        return java.util.Base64.getUrlEncoder().withoutPadding().encodeToString(b);
    }
}
```

- `UUID.randomUUID()`도 된다. Java 21 API 문서: "cryptographically strong pseudo random number generator"로 만든 v4다(실험 출력 `version=4`).

### 2. 스키마 — 내부 PK와 공개 ID를 분리

```sql
CREATE TABLE orders (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- 내부 조인용
  public_id  text   NOT NULL UNIQUE,                            -- 밖에 보이는 값
  owner_id   bigint NOT NULL
);
-- API 조회: 공개 ID + 소유 조건 (인가는 그대로)
SELECT * FROM orders WHERE public_id = ? AND owner_id = ?;
```

- `UNIQUE`가 있으면 짧은 ID의 충돌이 조용한 덮어쓰기가 아니라 오류로 드러난다. 충돌 시 새로 뽑아 재시도한다.

### 3. 사람이 입력하는 짧은 코드는 따로 설계한다

- 초대 코드·쿠폰처럼 짧아야 하는 값은 비트가 적다. 그만큼 다른 방어를 겹친다.
  - 만료 시각·사용 횟수 상한, 주체별·IP별 시도 상한(토큰 버킷), 실패 누적 시 잠금.
  - 생일 경계로 "발급 총량 k에서 충돌 확률"을 미리 계산해 길이를 정한다.

### 4. 시각이 드러나도 되는지 판단한다

- UUIDv7·ULID를 외부에 노출하면 생성 시각(가입 시점, 주문 시각)이 드러난다. 괜찮으면 인덱스 이득을 취하고, 아니면 외부에는 v4·랜덤 공개 ID를 둔다(RFC 9562 §8).

### 5. 진단 — 열거 시도 찾기

```text
  접근 로그에서
  - 한 주체(토큰·IP)가 짧은 시간에 서로 다른 ID를 많이 요청
  - 404·403 비율이 평소보다 높음
  - 요청 ID가 연속(5332, 5333, 5334 ...)
```

- 이 패턴에 알림을 걸고, 응답은 403/404를 섞지 않게 통일한다(15번).

## 장애 시나리오와 대처

### 1. 순차 ID 열거로 대량 수집 (⚠ Optus 2022 `[?]`)

- **현상**: 외부에 고객 데이터 덤프가 올라왔다. 침입 흔적은 없고 API 호출만 있다.
- **보이는 형태**: 접근 로그에 한 출처가 `/customers/{id}`를 연속 번호로 수십만 번 호출, 대부분 200.
- **원인**: 객체 수준 인가가 빠진(또는 한 경로에서 약해진) API + 순차 ID. ACMA는 Optus가 API의 접근 제어를 코드 변경으로 의도치 않게 약화시켰다고 주장했다. 순차 식별자 부분은 2차 보도다.
- **대처**
  - 인가 복구가 먼저다(15번). 그다음 외부 ID를 랜덤 공개 ID로 분리한다.
  - 쓰지 않는(휴면) 엔드포인트를 목록화하고 내린다(iTnews 보도: ACMA는 문제 엔드포인트가 인터넷에 노출된 채 오래 "휴면·미사용" 상태였다고 주장).
  - 주체별 요청 상한, 연속 ID 패턴 알림.
  - 출처 하나 기준의 탐지만 믿지 않는다. 같은 보도에서 Optus는 공격자가 수만 개 IP를 돌려 가며 정상 고객처럼 보였다고 설명했다. 토큰·계정·ID 패턴 기준 탐지를 겹친다.

### 2. 짧은 랜덤 ID 충돌 (⚠ 생일 경계)

- **현상**: 공유 링크를 열었더니 남의 파일이 나왔다. 또는 간헐적 `duplicate key value violates unique constraint` 오류.
- **보이는 형태**: UNIQUE가 없으면 조용히 덮어쓰기·잘못된 연결. 있으면 삽입 실패 로그가 데이터 증가에 따라 늘어난다.
- **원인**: 8자리 16진수(32비트) 같은 짧은 ID. 실험처럼 10만 개만 돼도 충돌이 기대된다.
- **대처**: 122~128비트로 늘린다. UNIQUE 제약 + 충돌 시 재생성. 이미 겹친 행을 찾아 정정한다.

### 3. UUIDv7·ULID가 시각과 다음 값을 흘린다

- **현상**: 공개 프로필 URL의 ID로 가입 시점이 추정됐다. 단조 ULID라면 같은 밀리초에 만든 이웃 ID까지 맞췄다.
- **보이는 형태**: ID 앞 12자리(16진) 또는 10자(base32)가 시간순으로 증가.
- **원인**: 정렬 이득을 위해 고른 시간 기반 ID를 외부에도 그대로 썼다.
- **대처**: 외부에는 v4·랜덤 공개 ID. 내부 PK는 v7 그대로 둬도 된다.

### 4. 이름으로 검증해 재생성된 대상을 믿음 (원본 §1)

- **현상**: 지웠던 저장소 이름을 남이 다시 만들었는데 배포 게이트가 통과시켰다.
- **보이는 형태**: 토큰의 `repository`는 같은데 `repository_id`가 이전 기록과 다르다.
- **원인**: 이름(참조)으로 판정했다.
- **대처**: 불변 수치 ID로 판정하고 이름은 기록용으로 둔다(원본 §1·§3, GitHub OIDC 보안 강화 문서).

## 핵심 문장

- 랜덤 ID는 인가의 대체가 아니라 보강이다. UUID를 "보유만으로 접근을 주는 수단"으로 쓰면 안 된다(RFC 9562 §8).
- 순차 ID는 열거·규모·속도를 흘린다. 내부 PK와 외부 공개 ID를 나눈다.
- 무작위 추측의 적중 기대값은 시도 × 객체 수 / 2^비트다. 이 값이 공격자의 최선이 되려면 ID가 예측 불가(CSPRNG)여야 한다 — 예측 가능하면 공격자는 무작위보다 잘 맞힌다.
- 무작위 ID는 칸 수의 제곱근 근처에서 충돌이 흔해진다. 32비트는 약 7.7만 개에서 50%다.
- UUIDv7·ULID는 생성 시각을 담고, 단조 ULID는 다음 값을 짐작하게 한다. 노출 여부를 따로 판단한다.

## 관련 주제·근거

- 원본(기초): [foundations/security/identity-and-ids.md](../../foundations/security/identity-and-ids.md) — §1 이름 재사용, §2 두 축, §3 검증 행렬, §4 인가 결박
- 선행·후속
  - [15-access-control-models](../15-access-control-models/2-summary.md) — 객체 수준 인가(첫째 층)
  - [security 09 randomness-and-key-management](../09-randomness-and-key-management/2-summary.md)(CSPRNG)
  - [17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md) — 토큰도 추측 불가 값이어야 한다(RFC 6749 §10.4)
  - math 05 `counting-and-birthday-bound` — 미작성, [math 영역 표](../../math/README.md)
- 연결
  - [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md) — 대리키·공개 ID, v4/v7 인덱스 실측
  - [distributed/13-distributed-id-generation](../../distributed/13-distributed-id-generation/2-summary.md) — Snowflake·UUIDv7 생성
  - [api-design/03-status-codes-for-apis](../../api-design/03-status-codes-for-apis/2-summary.md) — 403/404 차이로 존재가 새는 문제
  - [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md)
- 1차 출처
  - RFC 9562 UUIDs(2024-05) — §5.4 v4(122비트), §5.7 v7(48비트 밀리초 + 74비트), §6.7 충돌 저항, §6.9 추측 불가(CSPRNG SHOULD), §8 보안(capability로 쓰지 말 것 MUST NOT, 보안 용도면 v4 SHOULD) <https://www.rfc-editor.org/rfc/rfc9562>
  - ULID 명세 — 48비트 시각 + 80비트 랜덤, Crockford base32 26자, 단조 모드 +1 <https://github.com/ulid/spec>
  - OWASP API Security Top 10 2023 API1 — 랜덤·예측 불가 GUID 권고, 단 인가가 본 대책 <https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/>
  - OWASP Authorization Cheat Sheet — "Ensure Lookup IDs are Not Accessible Even When Guessed or Cannot Be Tampered With" <https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html>
  - Java SE 21 API `java.util.UUID.randomUUID()` — 강한 의사난수 생성기로 만든 v4 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/UUID.html>
  - git 문서 hash-function-transition — SHAttered(2017-02-23), git 2.13.0 강화 SHA-1 <https://git-scm.com/docs/hash-function-transition>
  - Optus 2022: ACMA 연방법원 소송(2024) 보도 — iTnews "Optus breach allegedly enabled by access control coding error" <https://www.itnews.com.au/news/optus-breach-allegedly-enabled-by-access-control-coding-error-608985> (ACMA 원문 페이지는 이 작업에서 열지 못함, 순차 ID 설명은 2차 보도 `[?]`)
  - GitHub Docs — OIDC 보안 강화(이름 대신 수치 ID claim) <https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect>
- 실험: `IdDemo.java`(OpenJDK 21.0.12, 컨테이너 `--network none`, 3회) — 순차 vs 64비트 랜덤 추측 적중, 32비트 10만 개 생일 충돌 20회 × 3, 비트별 50% 지점 계산, v4·v7 생성과 v7 시각 복원
