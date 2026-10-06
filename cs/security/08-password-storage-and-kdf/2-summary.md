# security/08-password-storage-and-kdf — 비밀번호 저장: salt·느린 KDF(bcrypt·scrypt·Argon2)·pepper — 정리 (힌트)

## 해결하는 문제

서버는 로그인 때 "입력한 비밀번호가 맞나"만 알면 된다.\
그런데 비밀번호를 그대로 저장하면, DB가 한 번 새는 순간 전부 노출된다.

```text
  저장 방식                       DB 유출 시 공격자가 하는 일
  평문                            그대로 읽는다
  암호화(AES, 키는 서버에)          키도 같이 새면 그대로 읽는다 (키를 앱이 들고 있으므로)
  SHA-256(pw)                     흔한 비밀번호 목록을 해시해 대조. 같은 비밀번호 = 같은 해시
  SHA-256(salt‖pw)                사용자마다 따로 대조해야 하지만, SHA-256이 너무 빨라 대량 추측 가능
  느린 KDF(salt, pw, 비용)          추측 한 번이 비싸다 → 같은 시간에 시도 수가 수만 배 줄어든다
```

- 비밀번호는 **암호화하지 않고 해시한다.** 되돌릴 필요가 없다. 로그인 때 같은 계산을 다시 해서 비교한다.
- *오프라인 공격*: 공격자가 유출된 해시를 자기 장비에서 끝없이 추측하는 것. 로그인 시도 제한([security/10-authentication-basics](../10-authentication-basics/2-summary.md))이 통하지 않는다. 남는 방어선은 "추측 한 번의 비용"(느린 KDF), 비밀번호 자체의 추측 난도, DB 밖에 둔 pepper(§5)다. KDF 비용은 추측을 **늦추고 비싸게** 할 뿐, 약한 비밀번호를 지켜 주지는 못한다.
- *KDF(Key Derivation Function, 키 유도 함수)*: 비밀번호 같은 낮은 엔트로피 입력에서 키나 검증값을 만드는 함수. 비밀번호 저장용은 일부러 느리게 만든다.
  - 흔한 오해: "SHA-256은 안전한 해시니까 비밀번호에도 안전하다" — 충돌·역상 저항은 있지만 **빠르다**. 비밀번호 공간이 작아서 빠른 해시는 전수 추측에 진다(OWASP Password Storage Cheat Sheet 첫 문단).

쉬운 예: 금고 다이얼이다.
- 숫자 4자리 금고는 경우의 수가 1만이다. 한 번 돌리는 데 0.1초면 금방 연다.
- 한 번 돌릴 때마다 10초가 걸리는 다이얼이면 같은 1만 번에 하루가 넘는다.
- 금고마다 다이얼 배치를 다르게 하면(salt), 한 금고의 답을 다른 금고에 쓸 수 없다.

똑같은 구조다.\
비밀번호의 경우의 수는 못 늘리니, 추측 한 번의 비용과 재사용 가능성을 바꾼다.

실무 예:
- Spring Security의 `PasswordEncoderFactories.createDelegatingPasswordEncoder()`가 `{bcrypt}$2a$10$...` 형식으로 저장한다(7.1.1 소스: 기본 id `bcrypt`, `BCryptPasswordEncoder` 기본 강도 10).
- 2024년 Okta는 AD/LDAP 위임 인증 캐시 키를 `bcrypt(userId + username + password)`로 만들었고, 사용자 이름이 52자 이상이면 비밀번호 없이 캐시로 인증될 수 있었다고 공지했다(아래 장애 시나리오 2).

## 동작·원리

### 1. salt — 같은 비밀번호를 다른 해시로

```text
  salt 없음                               salt 있음 (사용자마다 랜덤 16바이트)
  alice  pw=summer2024 → 9f3a...           alice  salt=a1.. → H(a1..‖summer2024) = 4c..
  bob    pw=summer2024 → 9f3a...  ← 같다    bob    salt=7e.. → H(7e..‖summer2024) = d0..  ← 다르다
  → 미리 계산한 표(레인보우 테이블) 한 장으로   → 사용자마다 따로 계산해야 한다
    전체 사용자를 한 번에 대조
```

- *salt*: 비밀번호마다 붙이는 공개 랜덤 값. 해시와 함께 저장한다. 비밀이 아니다.
- 막는 것: 미리 계산한 표, "같은 해시 = 같은 비밀번호"로 묶어 한 번에 깨기.
- 못 막는 것: 한 사용자를 겨냥한 추측. 그건 §2의 비용이 늦추고 비싸게 만든다(약한 비밀번호까지 지켜 주지는 못한다).
- NIST SP 800-63B-4 §3.1.1.2: salt는 최소 32비트, 충돌이 적게 고른다(SHALL). RFC 9106(Argon2)은 비밀번호 해싱에 16바이트 salt를 권한다(RECOMMENDED).

### 2. 느린 KDF — 추측 한 번의 비용을 올린다

```text
  PBKDF2 : HMAC을 c번 반복                         비용 = CPU 시간 (반복 수)
  bcrypt : Blowfish 키 스케줄을 2^cost번              비용 = CPU 시간 (cost는 로그 단위)
  scrypt : 큰 메모리 배열을 만들고 무작위로 다시 읽음     비용 = CPU 시간 × 메모리 (N, r, p)
  Argon2id: 메모리 블록 행렬을 t번 채우고 섞음            비용 = 메모리(m) × 반복(t), 병렬 레인(p)
```

같은 호스트에서 잰 시간(실험, 2026-10-07, 단일 스레드 · 수치는 이 장비 기준 예시):

```text
(호스트 Python 3.12.3, python3-bcrypt 3.2.2)
cost= 8  ms min=    52.8 max=    53.3
cost=10  ms min=   189.9 max=   206.9
cost=12  ms min=   811.5 max=   819.9
cost=14  ms min=  3135.7 max=  3297.9
sha256 single: 603,421 hashes/s (1 core, python)
scrypt N=2^17 r=8 p=1: 1096ms
pbkdf2-sha256 600k: 570ms

(OpenJDK 21.0.12 + Bouncy Castle 1.81.1, --cpus=2)
argon2id m=19456KiB t=2 p=1 : best 147 ms
argon2id m=47104KiB t=1 p=1 : best 174 ms
argon2id m=65536KiB t=3 p=4 : best 456 ms
PBKDF2-HMAC-SHA256 it=1 : best 0.19 ms
PBKDF2-HMAC-SHA256 it=10,000 : best 43.23 ms
PBKDF2-HMAC-SHA256 it=600,000 : best 587.62 ms
```

읽는 법:

- bcrypt cost가 2 오를 때마다 약 4배(53 → 190 → 812 → 3136ms). cost는 2의 거듭제곱 반복 수의 지수다.
- 단일 SHA-256은 Python에서도 초당 약 60만 번이다(C로 짠 크래킹 도구·GPU는 훨씬 빠르다). bcrypt cost 10 한 번(약 0.19초)과 비교하면 같은 CPU 시간에 추측 수가 10만 배 이상 차이 난다(해석).
- PBKDF2 비용은 반복 수에 거의 비례한다. 호스트 Python `hashlib`로 다시 재면 1만 회 8.8ms → 10만 회 87ms → 60만 회 430ms였다(재실험, 2026-10-07).
  - 위 Java 표의 1만 회(43ms)는 JIT 예열 영향이 섞여 부풀었다. 재실행에서는 86ms로 흔들렸다(해석). 짧은 측정값으로 비례 관계를 읽지 않는다.
- 시간 값은 실행마다 흔들린다. 재실행에서 bcrypt cost 10은 159~208ms, Argon2id m=19456·t=2·p=1은 92ms였다. 경향(cost +2 ≈ 4배)만 읽는다.
- *메모리 하드(memory-hard)*: 계산에 큰 메모리를 쓰게 만들어, 메모리가 작은 코어를 수천 개 묶은 GPU·ASIC의 이점을 줄인다. scrypt·Argon2가 여기에 속하고, PBKDF2·bcrypt는 속하지 않는다.

### 3. 파라미터 기준 — 출처별로 다르다

| 출처 | 권고 | 성격 |
|---|---|---|
| OWASP Password Storage Cheat Sheet (GitHub master, 2026-10-07 열람) | Argon2id 최소 m=19 MiB·t=2·p=1(동등한 다른 조합 표 있음) / scrypt N=2^17·r=8·p=1 / bcrypt는 레거시용, cost 10 이상, 입력 72바이트 제한 / PBKDF2-HMAC-SHA256 60만 회 | 권고(관례) |
| RFC 9106 §4 | 1순위 Argon2id t=1·p=4·m=2 GiB, 메모리가 적으면 2순위 t=3·p=4·m=64 MiB, salt 128비트·태그 256비트 | 표준 권고(RECOMMENDED) |
| NIST SP 800-63B-4 §3.1.1.2 | SP 800-132 등 승인된 해싱 방식 SHOULD, 비용은 성능을 해치지 않는 한 높게·시간이 지나며 올림 SHOULD | 미 연방 지침 |
| Spring Security 7.1.1 `Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8()` | salt 16·해시 32·p=1·m=16384 KiB·t=2 | 라이브러리 기본값 |

- 같은 "Argon2id"라도 RFC 9106의 1순위(2 GiB)와 OWASP 최소값(19 MiB)은 100배 차이가 난다. 로그인 동시 처리량과 서버 메모리로 정한다(아래 장애 시나리오 3).
- 값을 고른 근거와 날짜를 남긴다. 기준은 해마다 오른다.

### 4. bcrypt의 72바이트 — 그 뒤는 무시된다

```text
  입력 바이트:  [ 1 ... 72 ][ 73 ... ]
                └ bcrypt가 쓰는 부분 ┘└ 원조 OpenBSD 방식에서는 조용히 버린다
```

실험(호스트 Python 3.12.3, python3-bcrypt 3.2.2) — `a` 72개로 만든 해시에 다른 입력을 대조했다.

```text
len= 72 checkpw -> True
len= 73 checkpw -> True
len= 97 checkpw -> True                  ← 뒤에 25바이트를 붙여도 통과
len= 71 checkpw -> False
'가'*24 utf8 bytes = 72 | +'나' still matches: True    ← 한글은 UTF-8 3바이트, 24자면 이미 72바이트
```

같은 확인을 Java로(실험, OpenJDK 21.0.12 + Bouncy Castle 1.81.1 `OpenBSDBCrypt`):

```text
BC bcrypt 73 a -> same hash as 72? true
BC checkPassword(73 a, h72) = true
```

- 제한은 **문자가 아니라 바이트**다. 한글 24자, 이모지 18자(4바이트 × 18)면 이미 72바이트다.
- 라이브러리 판마다 다르다.
  - pyca/bcrypt 5.0.0(2025-09-25 PyPI 공개) 변경 기록: "`hashpw`에 72바이트 넘는 비밀번호를 넘기면 이제 `ValueError`. 이전에는 원조 OpenBSD 동작을 따라 조용히 잘랐다."
  - CVE-2025-22228(NVD 게시 2025-03-20, CVSS 3.1 7.4 — CNA VMware 점수): Spring Security `BCryptPasswordEncoder.matches`가 72자 넘는 비밀번호에 대해 앞 72자만 같으면 `true`. 수정판 6.4.4·6.3.8(OSS), 6.2.10·6.1.14·6.0.16·5.8.18·5.7.16(Enterprise Support 전용)(spring.io 공지, 2025-03-19).
  - 수정 방식은 판마다 다르다(소스 대조). 6.4.4의 `BCrypt.hashpw`는 72바이트 초과를 **모든 경로**에서 `IllegalArgumentException("password cannot be more than 72 bytes")`으로 막았다. 6.5.0·7.0.0·7.1.1은 이 검사를 "새 비밀번호에만"(`!for_check`) 적용한다. 그래서 검증 경로는 다시 72바이트 뒤를 버린다.
  - 재실험(Spring Security 7.1.1 `BCrypt.java` 소스를 그대로 컴파일, OpenJDK 21.0.12, 2026-10-07):

```text
hashpw(73 a) -> IllegalArgumentException: password cannot be more than 72 bytes
checkpw(73 a, hash(72 a)) = true
checkpw(72 a + 'XYZ', hash(72 a)) = true
checkpw(71 a, hash(72 a)) = false
```

  - `BCryptPasswordEncoder.matches`는 `BCrypt.checkpw`를 그대로 부른다(7.1.1 소스). 즉 7.1.1에서는 "72바이트 넘는 새 비밀번호는 저장 거부, 검증 입력은 잘라서 비교"다. 길이 검증은 앱이 입력 단계에서 따로 한다.
  - 이 실험의 python3-bcrypt 3.2.2·BC 1.81.1은 둘 다 조용히 잘랐다.
- 고친 예: 입력 길이를 바이트로 제한하거나, HMAC으로 먼저 줄인다(적용 §2).

### 5. pepper — DB 밖에 두는 비밀

```text
  salt  : 사용자마다 다름, DB에 같이 저장 (공개)
  pepper: 전체 공통, DB 밖(시크릿 저장소·HSM)에 저장 (비밀)
          → SQL 인젝션·백업 유출처럼 "DB만" 새면 해시를 추측할 수 없다
```

- NIST SP 800-63B-4: 검증자만 아는 비밀키로 키 있는 해시·암호화를 한 번 더 하라(SHOULD), 그 키는 HSM 같은 하드웨어 보호 영역에 두라(SHOULD).
- OWASP: pepper는 단독으로는 보안 성질을 더하지 않는 심층 방어다. pepper가 새면 바꿔야 하는데, 비밀번호를 모르니 사용자 전원의 재설정이 필요하다.
- 두 방식: 해싱 전에 섞기(pre-hashing), 해싱 결과를 HMAC(pepper)으로 한 번 더(post-hashing).

### 6. 표준 저장 형식 — 알고리즘과 파라미터를 같이 적는다

```text
  $2b$10$<22자 salt><31자 해시>                          bcrypt (60자, 실험의 hash len 60)
  $argon2id$v=19$m=19456,t=2,p=1$<salt b64>$<hash b64>   PHC 문자열 형식
  {bcrypt}$2a$10$...                                     Spring DelegatingPasswordEncoder 접두어
```

- 파라미터가 해시 안에 있으니, 비용을 올려도 옛 해시를 검증할 수 있다. 로그인 성공 때 새 파라미터로 다시 저장하면 점진적으로 올라간다(OWASP "Upgrading the Work Factor").

## 쓰이는 자료구조·알고리즘

- **반복 HMAC(PBKDF2)** — RFC 8018 §5.2. HMAC을 c번 체인. 기초는 [원고 hmac](../../foundations/security/hmac.md).
- **Blowfish 키 스케줄 반복(bcrypt)** — 비싼 키 설정을 2^cost번. 입력이 키 스케줄에 들어가는 구조가 72바이트 한계를 만든다.
- **메모리 하드 함수** — scrypt의 ROMix(큰 배열을 순서대로 채운 뒤 입력 의존 위치로 다시 읽기, RFC 7914), Argon2의 메모리 블록 행렬(1KiB 블록 m개, 레인 p개, 패스 t번, RFC 9106 §3). Argon2id는 첫 패스의 앞 절반에서 Argon2i처럼 입력 독립 접근(부채널 저항), 나머지에서 Argon2d처럼 입력 의존 접근(GPU 저항)을 한다(RFC 9106 §1).
- **테스트 벡터 재현** — scrypt RFC 7914 §12, Argon2id RFC 9106 §5.3을 그대로 재현했다(아래 근거).
- **상수 시간 비교** — 해시 비교에 `MessageDigest.isEqual`(Java) 류. 라이브러리 `matches`는 내부에서 처리한다(Spring `BCrypt.equalsNoEarlyReturn`).

## 적용 — 풀어나가는 법

### 1. 취약 예 → 고친 예 (Java 21, Spring Security)

```java
// 취약: 빠른 해시 + salt 없음
String stored = HexFormat.of().formatHex(
    MessageDigest.getInstance("SHA-256").digest(password.getBytes(UTF_8)));

// 고침: Argon2id, 파라미터는 근거와 함께 고정 (예시: OWASP 최소값 m=19 MiB, t=2, p=1)
PasswordEncoder encoder = new Argon2PasswordEncoder(16, 32, 1, 19456, 2);
String hash = encoder.encode(password);              // $argon2id$v=19$m=19456,t=2,p=1$...
boolean ok = encoder.matches(candidate, hash);

// 여러 방식이 섞인 기존 DB: 접두어로 구분하고 로그인 성공 시 Argon2id로 재해시
// createDelegatingPasswordEncoder()는 encode 기본이 bcrypt이고, 접두어 없는 해시에는 matches가
// IllegalArgumentException을 던진다(7.1.1 소스) → 인코딩 id와 "접두어 없음" 검증기를 직접 지정한다
DelegatingPasswordEncoder delegating = new DelegatingPasswordEncoder("argon2",
    Map.of("argon2", encoder, "bcrypt", new BCryptPasswordEncoder()));
delegating.setDefaultPasswordEncoderForMatches(legacySha256);   // 접두어 없는 옛 SHA-256 전용 검증기(직접 구현, 상수 시간 비교)
if (delegating.matches(candidate, stored) && delegating.upgradeEncoding(stored)) {
    saveNewHash(delegating.encode(candidate));
}
```

- `Argon2PasswordEncoder`의 구현은 Bouncy Castle을 쓴다(7.1.1 소스 주석). 클래스패스에 `bcprov`가 필요하다. 같은 주석은 "BC 구현이 크래커만큼 병렬·최적화를 쓰지 않아 공격자와 방어자 사이에 불필요한 비대칭이 있다"고 적는다.

### 2. bcrypt를 계속 써야 할 때 — 72바이트 문제 막기

```python
# 실험(호스트 Python 3.12.3, bcrypt 3.2.2): HMAC-SHA384(pepper) → base64 → bcrypt
def pre(pw: bytes) -> bytes:
    return base64.b64encode(hmac.new(PEPPER, pw, hashlib.sha384).digest())   # 64바이트 ASCII, NUL 없음
```

```text
prehash len 64
prehash: 72a vs 73a match -> False      ← 73번째 바이트가 이제 결과를 바꾼다
prehash: same 72a -> True
```

- base64로 바꾸는 이유: 원조 bcrypt는 NUL 바이트에서 입력을 끝낸다. 해시 바이트를 그대로 넣으면 첫 바이트가 0일 때 빈 문자열과 같아진다(OWASP "Pre-Hashing Passwords with bcrypt").
- pepper 없는 `bcrypt(base64(sha512(pw)))`는 OWASP가 "password shucking" 위험으로 경고한다. 다른 곳에서 샌 SHA-512 해시를 그대로 대입해 볼 수 있기 때문이다.
- 더 단순한 대안: 입력을 바이트로 재서 72 초과면 거부하고, 이 사실을 가입 화면에 알린다.

### 3. 비용 정하기 — 로그인 처리량으로 역산

```text
  목표: 로그인 1회 해시 ≈ 수백 ms 이하 (예시), 피크 로그인 초당 L건, 코어 C개
  bcrypt cost 10 ≈ 0.19 s/코어 (위 실험 장비) → 코어당 초당 약 5건 → L=100이면 코어 약 20개
  Argon2id m=19 MiB → 동시 로그인 100건이면 해시 메모리만 약 1.9 GiB
```

- 계산 예시는 위 실험 장비 기준이다. 대상 서버에서 직접 잰다(RFC 9106 §4, OWASP 모두 "대상 시스템에서 벤치마크").
- 로그인 엔드포인트에 동시 실행 상한(세마포어)과 속도 제한을 함께 둔다. 비싼 해시는 DoS 표적이 된다([security/28-dos-and-abuse](../28-dos-and-abuse/2-summary.md)).

### 4. 비밀번호 정책 — NIST SP 800-63B-4

- 단일 요소로 쓰는 비밀번호 최소 15자(SHALL), MFA의 일부면 최소 8자(SHALL), 최대 64자 이상 허용(SHOULD).
- 문자 종류 섞기 같은 조합 규칙 강제 금지(SHALL NOT), 주기적 변경 강제 금지(SHALL NOT).
- "최대 64자 이상 허용"과 bcrypt 72**바이트**가 부딪힐 수 있다. 64자 한글은 192바이트다.

## 장애 시나리오와 대처

### 1. 평문·단일 SHA-256 저장 → 유출 시 대량 크래킹 (⚠ 커리큘럼)

- **현상**: DB 덤프가 유출된 뒤, 며칠 안에 상당수 계정의 비밀번호가 공개된다. 다른 사이트에서도 같은 비밀번호로 로그인 시도가 쏟아진다(크리덴셜 스터핑, [security/10-authentication-basics](../10-authentication-basics/2-summary.md)).
- **보이는 형태**: `password` 컬럼이 64자 16진수(SHA-256으로 의심)이거나 32자(MD5로 의심 — 길이만으로 확정하지 말고 코드로 확인). 같은 값이 여러 행에 반복된다(salt 없음의 흔적).
- **원인**: 빠른 해시는 추측 한 번이 싸다(위 실험: Python 단일 코어로도 초당 약 60만 번).
- **대처**
  - 즉시: 영향 계정 비밀번호 재설정 강제, 세션 무효화.
  - 이관: 기존 해시를 입력으로 감싸기 `argon2id(sha256(pw))` → 다음 로그인 때 `argon2id(pw)`로 교체(OWASP Upgrading Legacy Hashes). 오래 로그인 안 한 계정은 해시를 지우고 재설정 요구.

### 2. bcrypt 72바이트 절단 → 다른 입력으로 인증 통과 (⚠ 커리큘럼, Okta 2024)

- **현상**: 긴 입력의 앞부분만 같으면 인증된다. 비밀번호 자체보다 **비밀번호 앞에 다른 값을 이어 붙인 설계**에서 크게 터진다.
- **보이는 형태**(Okta 공지, 2024): 캐시 키 = `bcrypt(userId + username + password)`. 사용자 이름이 52자 이상이면 비밀번호가 72바이트 밖으로 밀려나, 이전에 성공한 캐시 항목이 있을 때 비밀번호 없이 인증될 수 있었다. 2024-07-23 릴리스로 들어갔고 2024-10-30에 발견해 PBKDF2로 바꿨다. 조건: AD/LDAP 위임 인증, MFA 없음, 캐시 사용(에이전트 장애 등).
- **원인**: bcrypt는 72바이트 뒤를 조용히 버린다(위 실험, python-bcrypt 3.2.2·BC 1.81.1). 문자 수가 아니라 바이트라 UTF-8 다국어 입력에서 더 빨리 닿는다.
- **대처**
  - bcrypt 입력은 비밀번호 하나만. 다른 값과 이어 붙이지 않는다. 캐시 키·토큰 같은 용도에는 HMAC을 쓴다.
  - 72바이트 초과 거부 또는 HMAC 선해시(적용 §2). 라이브러리를 초과 시 예외를 내는 판으로 올린다(pyca 5.0.0의 `hashpw`, Spring의 CVE-2025-22228 수정판). 단 Spring 6.5.0 이후 판은 저장 때만 막고 검증 입력은 자른다(위 §4 재실험) — 앱이 로그인 입력 길이도 바이트로 검사한다.
  - 음성 테스트: "앞 72바이트가 같고 뒤가 다른 입력은 실패해야 한다".

### 3. 비용을 너무 높임 → 로그인 지연·메모리 부족

- **현상**: 배포 직후 로그인 p99가 수 초로 튀고, 피크 때 파드가 OOMKilled 된다.
- **보이는 형태**: 로그인 API만 느리고 CPU가 포화. Argon2 메모리를 크게 잡았다면 `java.lang.OutOfMemoryError` 또는 컨테이너 `OOMKilled`. 비싼 해시를 노린 로그인 요청 폭주에 더 쉽게 무너진다.
- **원인**: 비용 = 요청 1건의 CPU·메모리다. 동시 로그인 수 × 해시 메모리를 계산하지 않았다(적용 §3).
- **대처**: 대상 서버에서 측정해 목표 시간 안의 최대치로 정한다. 로그인 동시 실행 상한, IP·계정별 속도 제한. 비용은 한 번에 크게 올리지 않고 단계적으로.

### 4. pepper 분실·유출 → 전원 로그인 불가 또는 보호 상실

- **현상**: 시크릿 저장소 이전 중 pepper 값이 바뀌어 아무도 로그인하지 못한다. 또는 pepper가 코드 저장소에 들어가 DB 유출만으로도 다시 추측이 가능해진다.
- **보이는 형태**: 배포 직후 로그인 성공률 0%, 해시 형식은 정상.
- **원인**: pepper는 비밀번호를 모르면 교체할 수 없다(OWASP). 버전 없이 값 하나로 운영했다.
- **대처**: pepper에 버전 id를 붙여 해시 옆에 저장(`pepper_v=2`), 새 버전은 로그인 성공 시 점진 교체. 저장 위치·회전은 [09](../09-randomness-and-key-management/2-summary.md).

## 핵심 문장

- 비밀번호는 암호화하지 않고, salt를 붙여 일부러 느린 KDF로 해시한다.
- salt는 사용자마다 다른 공개 값으로 미리 계산한 표와 일괄 깨기를 막고, 한 사람을 겨냥한 추측은 KDF의 비용이 늦추고 비싸게 만든다.
- Argon2id·scrypt는 메모리까지 비싸게 만들어 GPU·ASIC의 이점을 줄인다. 파라미터 권고는 출처마다 다르니 대상 서버에서 재고 근거를 남긴다.
- bcrypt는 72바이트 뒤를 버리는 구현이 있다. 문자가 아니라 바이트이고, 앞에 다른 값을 이어 붙이면 비밀번호가 밖으로 밀려난다(Okta 2024).
- pepper는 DB만 새는 경우를 막는 심층 방어이며, 분실·유출 대비 버전 관리가 필요하다.

## 관련 주제·근거

- 선행
  - [security/04-hash-functions-and-digests](../04-hash-functions-and-digests/2-summary.md) — 해시 3성질과 "빠른 해시"(기초: [원고 sha256-and-digest](../../foundations/security/sha256-and-digest.md)) · [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
- 후속·연결
  - [security/10-authentication-basics](../10-authentication-basics/2-summary.md) — 크리덴셜 스터핑·MFA
  - [09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md) — salt 난수, pepper 보관·회전
  - [security/28-dos-and-abuse](../28-dos-and-abuse/2-summary.md) — 비싼 해시 엔드포인트의 남용 제한
- 1차 출처
  - RFC 9106 Argon2 — §3 파라미터(salt 16바이트 RECOMMENDED), §4 파라미터 선택 절차(1순위 2 GiB·2순위 64 MiB), §5.3 Argon2id 테스트 벡터 <https://www.rfc-editor.org/rfc/rfc9106>
  - RFC 7914 scrypt — §12 테스트 벡터 <https://www.rfc-editor.org/rfc/rfc7914>
  - RFC 8018 PKCS #5 v2.1 — §5.2 PBKDF2 <https://www.rfc-editor.org/rfc/rfc8018>
  - OWASP Password Storage Cheat Sheet(GitHub master, 2026-10-07 열람) <https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html>
  - NIST SP 800-63B-4 §3.1.1.2 — 길이(15·8·64), 조합·주기 변경 금지, salt 32비트, 비용, 키 있는 해시 <https://pages.nist.gov/800-63-4/sp800-63b.html>
  - Okta 보안 공지 "AD/LDAP Delegated Authentication — Username" <https://trust.okta.com/security-advisories/okta-ad-ldap-delegated-authentication-username/>
  - NVD CVE-2025-22228 <https://nvd.nist.gov/vuln/detail/CVE-2025-22228> · spring.io 공지 <https://spring.io/security/cve-2025-22228>
  - pyca/bcrypt 5.0.0 변경 기록(PyPI) <https://pypi.org/project/bcrypt/5.0.0/>
  - Spring Security 7.1.1 소스 — `BCrypt.hashpw`(72바이트 검사), `BCryptPasswordEncoder`(기본 강도 10), `Argon2PasswordEncoder`(v5_8 기본값), `PasswordEncoderFactories` <https://github.com/spring-projects/spring-security/tree/7.1.1/crypto>
- 실험(2026-10-07)
  - 호스트 Python 3.12.3 + python3-bcrypt 3.2.2 `bc72.py`: 72바이트 절단(73·97바이트·한글 24자 통과), cost 8~14 시간, 단일 SHA-256 속도, scrypt RFC 7914 벡터(`fdbabe1c…cc0640` 일치)·N=2^17 시간, PBKDF2 60만 회 시간 / `fix.py`: HMAC-SHA384 선해시 후 73번째 바이트 반영
  - OpenJDK 21.0.12 + Bouncy Castle 1.81.1(eclipse-temurin:21-jdk, `--network none`, `--cpus=2`) `Kdf.java`: Argon2id RFC 9106 §5.3 태그 `0d640df5…6b01e659` 일치, Argon2id 3개 파라미터 시간, BC bcrypt 72바이트 절단, PBKDF2 반복 수별 시간
  - 재실험(OpenJDK 21.0.12): Spring Security 7.1.1 `BCrypt.java` 소스 단독 컴파일 — `hashpw(73바이트)` 예외, `checkpw(73바이트, 72바이트 해시)` = true / 호스트 Python `hashlib.pbkdf2_hmac` 1만·10만·60만 회 시간
