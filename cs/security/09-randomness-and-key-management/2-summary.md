# security/09-randomness-and-key-management — 난수(CSPRNG)와 키 관리: 수명·회전·봉투 암호화·시크릿 관리 — 정리 (힌트)

## 해결하는 문제

암호 알고리즘이 튼튼해도, 그 안에 넣는 **키와 난수**가 약하거나 새면 소용이 없다.

```text
  알고리즘은 공개, 안전은 키에서 나온다 (Kerckhoffs 원칙)

  키·난수가 깨지는 길                          결과
  1. 예측 가능한 난수로 키·토큰·nonce 생성        공격자가 같은 값을 재계산 (Debian 2008)
  2. 키를 코드·설정 파일에 하드코딩 → git        저장소에 접근한 누구나 사용 (Uber 2016)
  3. 키를 바꿀 절차가 없음                      유출돼도 몇 주간 못 바꾸고, 바꾸면 장애
  4. 키 하나를 여러 데이터·여러 용도에 공유       하나가 새면 그 범위 전체
```

- 이 노트는 두 문제를 묶는다.
  - **난수**: 키·세션 ID·리셋 토큰은 예측 불가능해야 한다. salt는 서로 겹치지 않는 것(SP 800-63B-4), AES-GCM nonce는 같은 키에서 다시 쓰지 않는 것(SP 800-38D — 카운터 같은 결정적 구성도 허용)이 핵심이다. 무작위로 뽑는다면 그 난수도 CSPRNG에서 나와야 겹치지 않는다.
  - **키 관리**: 키를 만들고, 보관하고, 쓰고, 바꾸고, 폐기하는 수명 전체.
- *CSPRNG(Cryptographically Secure PRNG)*: 출력 일부를 봐도 다음·이전 출력을 예측할 수 없는 의사난수 생성기. 운영체제 엔트로피로 시드를 받는다.
  - 흔한 오해: "난수면 다 같다" — `java.util.Random`은 48비트 시드의 선형 합동 생성기라고 Javadoc에 적혀 있다. 통계적으로 고르게 보여도 예측 가능하다.

쉬운 예: 아파트 현관 비밀번호다.
- 생일·동 호수로 정하면(예측 가능한 난수) 이웃이 맞힌다.
- 번호를 현관문 옆에 적어 두면(하드코딩) 지나가는 사람이 다 본다.
- 이사 간 사람이 번호를 아는데 바꿀 방법이 없으면(회전 부재) 계속 열린다.

똑같은 구조다.\
값을 만드는 법, 두는 곳, 바꾸는 법이 다 맞아야 한다.

실무 예:
- Uber 2016: FTC 발표(2018-04, 수정 고소장의 주장)에 따르면 침입자가 "Uber 엔지니어가 코드 공유 사이트에 올린 접근 키"로 클라우드 저장소의 비암호화 파일을 내려받았다. 파일에는 "2,500만 건 넘는 이름·이메일, 2,200만 건의 이름·휴대전화 번호, 60만 건의 이름·운전면허 번호"(미국 Uber 운전자·승객)가 들어 있었다.
- Debian 2008(CVE-2008-0166, DSA-1571): Debian 고유 패치 때문에 OpenSSL 난수가 예측 가능해졌다. SSH·OpenVPN·DNSSEC 키, X.509 인증서용 키, TLS 세션 키가 영향을 받았다.

## 동작·원리

### 1. CSPRNG의 구조

```text
  엔트로피 원천 (인터럽트 타이밍, CPU 난수 명령 등)
        │  섞기
        ▼
  커널 풀 ──> 커널 CSPRNG ──> getrandom(2) · /dev/urandom
                                    │ 시드
                                    ▼
                    사용자 공간 DRBG (Java NativePRNG·DRBG, OpenSSL RAND)
                                    │
                                    ▼
                      키 · salt · nonce · 토큰
```

- *엔트로피*: 공격자가 모르는 정도. 비트 수로 센다. 시드의 엔트로피가 작으면 출력이 아무리 길어도 경우의 수는 시드만큼이다.
- *DRBG(Deterministic Random Bit Generator)*: 시드에서 긴 출력을 만드는 결정적 알고리즘. NIST SP 800-90A가 Hash_DRBG·HMAC_DRBG·CTR_DRBG를 정의한다 `[?]`(목록만 확인, 본문 미대조).
- Linux `random(7)`: 장기 키 생성이라도 `/dev/random`이나 `GRND_RANDOM`보다 `/dev/urandom`·플래그 없는 `getrandom(2)`를 쓰라고 적는다. 부팅 초기 풀이 준비되기 전 상황은 `getrandom`이 기다려 준다(같은 문서의 비교 표).

### 2. 예측 가능한 난수가 보이는 모습 (자기 예제)

실험(OpenJDK 21.0.12 temurin, `--network none`, 2회 실행 같은 결과):

```text
Random(42) x2: 431130 392763 211248 | 431130 392763 211248
time-seeded token: seed found=true after 124 candidates in 0.3 ms
```

- 같은 시드 → 같은 수열. 시드를 알면 전부 재현된다.
- 두 번째 줄은 `new Random(발급시각ms).nextLong()`으로 만든 "리셋 토큰"이다. 발급 시각을 1분 범위로만 알아도 후보는 6만 개다. 이 실행에서는 124번째 후보에서 시드를 찾았다(코드에 고정한 예시 발급 시각이 창 시작보다 123ms 뒤라서 124는 매번 같다). 최악 6만 번도 수십 ms 수준이다(해석).
- 고친 예: `SecureRandom`으로 128비트 이상을 뽑는다(적용 §1).

### 3. `SecureRandom`과 `setSeed`의 함정

```text
default SecureRandom algorithm = NativePRNG
new SecureRandom()+setSeed(42) x2 equal = false  (92fe86bd0f138bd6 / 2566d3e707d24a72)
SHA1PRNG setSeed(42) before use x2 equal = true  (d50ac288b90ede2e)
```

(실험, OpenJDK 21.0.12, Linux 컨테이너. 첫 줄의 16진수는 실행마다 달랐고, SHA1PRNG 줄은 2회 모두 `d50ac288b90ede2e`.)

- Linux 기본 `new SecureRandom()`은 `NativePRNG`였다. `setSeed`는 Javadoc대로 기존 시드를 **보충**할 뿐이라 같은 시드를 줘도 출력이 달랐다.
- `SHA1PRNG`에 **첫 사용 전** `setSeed`를 하면 결정적이 된다. Javadoc: "PRNG `SecureRandom`은 `nextBytes`·`reseed` 전에 `setSeed`가 불리면 스스로 시드를 받지 않는다."
  - 취약 패턴: "테스트 재현성"을 위해 `SHA1PRNG` + 고정 시드를 쓴 코드가 운영에 남는다 → 키·토큰이 매번 같다.
- 강한 키(장기 RSA 키 등)는 `SecureRandom.getInstanceStrong()`을 고려한다(Javadoc). 이 실험 환경(OpenJDK 21.0.12 Linux 컨테이너)에서 그 알고리즘은 `NativePRNGBlocking`이었다(`securerandom.strongAlgorithms = NativePRNGBlocking:SUN,DRBG:SUN`).
  - Javadoc은 엔트로피 원천이 `/dev/random`이면 `nextBytes` 등이 막힐 수 있다고 적는다. 그래서 요청 경로에서는 주의한다.

### 4. 키 수명 — cryptoperiod

- *cryptoperiod*: 한 키를 쓰도록 허락된 기간. 길수록 유출·분석 위험이 쌓이고, 짧을수록 교체 비용이 든다.
- NIST SP 800-57 Part 1 Rev.5 표 1(제안값, 발췌):

| 키 종류 | 만드는 쪽 사용 기간(OUP) | 받는 쪽 사용 기간 |
|---|---|---|
| 서명 개인키 | 1~3년 | — |
| 대칭 데이터 암호화 키 | 2년 미만 | OUP + 3년 미만 |
| 대칭 키 포장 키(KEK) | 2년 미만 | OUP + 3년 미만 |
| 대칭 마스터 키·키 유도 키 | 약 1년 | — |
| 임시 키 합의 키 | 키 합의 한 번 | — |

- "받는 쪽 사용 기간"이 더 긴 이유: 2년 동안 암호화한 데이터를 그 뒤에도 **복호**해야 하기 때문이다. 그래서 회전은 "새 키로 쓰기 + 옛 키로 읽기"를 함께 지원해야 한다.

### 5. 봉투 암호화 — 키의 계층

```text
          KMS/HSM 안에서만 존재 (밖으로 안 나옴)
                 ┌────────────┐
                 │  KEK v1/v2 │   키 포장 키 (회전 대상)
                 └─────┬──────┘
          wrap/unwrap  │
       ┌───────────────┼────────────────┐
  [포장된 DEK a]   [포장된 DEK b]   [포장된 DEK c]     ← 데이터 옆에 저장 (포장된 상태)
       │                │                 │
  레코드 a 암호문   레코드 b 암호문     파일 c 암호문      ← DEK로 AES-GCM
```

- *DEK(Data Encryption Key)*: 데이터를 직접 암호화하는 키. 레코드·파일·테넌트 단위로 많다.
- *KEK(Key Encryption Key)*: DEK를 암호화(포장)하는 키. 적고, KMS·HSM 밖으로 나오지 않게 둔다.
- 장점: KEK를 회전할 때 **데이터를 다시 암호화하지 않고** 포장된 DEK만 다시 포장한다.

실험(OpenJDK 21.0.12, `AES/GCM/NoPadding` + `AESWrap`):

```text
data ct 54B, wrapped DEK (AESWrap) 40B under kek-v1
after KEK rotation: data ct untouched, decrypt via kek-v2 = card=4111-1111-1111-1111 (test number)
unwrap v1-wrapped DEK with kek-v2 -> InvalidKeyException
```

- 데이터 암호문(54바이트 = 평문 38 + 태그 16)은 그대로 두고, DEK(32바이트 → 포장 40바이트)만 v2로 다시 포장했다.
- v1로 포장된 DEK를 v2로 풀면 실패한다. 그래서 포장된 DEK 옆에 **KEK 버전**을 같이 저장해야 한다.
- AWS KMS 문서도 같은 구분을 한다: KMS 키 회전은 "현재 키 재료"만 바꾸고, 옛 재료는 남겨 옛 암호문을 자동으로 푼다. 그리고 "회전은 KMS 키가 만든 **데이터 키를 회전하거나 데이터를 다시 암호화하지 않는다**. 유출된 데이터 키의 영향을 줄이지 못한다"고 적는다. 자동 회전 기본 주기는 365일이다.

### 6. 시크릿 관리 — 코드 밖에, 버전과 함께

```text
  나쁨: 소스 코드 / application.yml / Dockerfile ENV / git 이력
  나음: 배포 시점에 주입되는 환경 변수·파일 (권한 제한)
  좋음: 시크릿 저장소(Vault·클라우드 Secrets Manager) + 짧은 수명 자격 증명 + 접근 감사 로그
```

- git에서 지운 시크릿은 이력에 남는다. 실험(git 2.43.0, 로컬 일회용 저장소, AWS 문서의 예시 키 `AKIAIOSFODNN7EXAMPLE`):

```text
== HEAD grep:
(none in HEAD)
== history (git log -S):
1f55754 remove hardcoded key
94cb36a add config
== mini scanner over all revisions:
94cb36a7cfc688744920cc22f1bcdc44fa8e2424:application.properties:1:aws.accessKeyId=AKIAIOSFODNN7EXAMPLE
```

(커밋 해시는 실행마다 다르다.)

- 최신 판(HEAD)에는 없지만, 이력을 훑는 스캐너(정규식 `AKIA[0-9A-Z]{16}`)는 첫 커밋에서 찾았다.
- GitHub 문서 "Removing sensitive data from a repository": 시크릿이면 **먼저 폐기·회전**하라. 무효화되면 그것으로 충분할 수 있고, 이력 재작성은 그다음 문제다. 재작성해도 포크·다른 사람의 클론에는 남는다.

## 쓰이는 자료구조·알고리즘

- **선형 합동 생성기(LCG)** — `java.util.Random`의 48비트 상태. 상태가 작고 갱신이 선형이라 예측 가능하다. [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md), 수학 배경 [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md).
- **DRBG(HMAC_DRBG 등)** — 해시·HMAC·블록 암호로 상태를 갱신하는 결정적 생성기. RFC 6979의 결정적 ECDSA k도 HMAC_DRBG다([06](../06-public-key-and-signatures/2-summary.md)).
- **키 계층 트리(봉투 암호화)** — 루트(KMS 키) → KEK → DEK → 데이터. 회전은 한 층만 다시 포장한다.
- **버전 붙은 키 맵** — `{kid/버전 → 키}`. 쓰기는 현재 버전, 읽기는 저장된 버전으로 찾는다. JWT의 `kid`([security/13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md), 기초 [원고 jwks](../../foundations/security/jwks.md))와 같은 구조다.
- **패턴 매칭 스캐너** — 정규식(접두어 `AKIA` 등) + 엔트로피 휴리스틱으로 이력·변경분을 훑는다.

## 적용 — 풀어나가는 법

### 1. 취약 예 → 고친 예: 토큰·ID 생성 (Java 21)

```java
// 취약: 예측 가능
String token = Long.toHexString(new Random(System.currentTimeMillis()).nextLong());
String token2 = UUID.nameUUIDFromBytes(email.getBytes()).toString();   // 입력에서 결정됨 (난수 아님)

// 고침: CSPRNG에서 128비트 이상
private static final SecureRandom RNG = new SecureRandom();   // 스레드 안전, 재사용
static String newToken() {
    byte[] b = new byte[32];                                   // 256비트
    RNG.nextBytes(b);
    return Base64.getUrlEncoder().withoutPadding().encodeToString(b);
}
// UUID.randomUUID(): Javadoc "cryptographically strong pseudo random number generator"로 생성(버전 4, 랜덤 122비트)
```

- 하지 말 것: `setSeed`로 고정 시드 주기, `SHA1PRNG` + 고정 시드, `Math.random()`·`ThreadLocalRandom`을 보안 값에 쓰기.

### 2. 봉투 암호화 + 회전 데이터 모델

```sql
-- 레코드 옆에 포장된 DEK와 KEK 버전을 같이 둔다
CREATE TABLE secret_blob (
  id           BIGINT PRIMARY KEY,
  kek_version  INT     NOT NULL,      -- 어떤 KEK로 포장했나
  wrapped_dek  BYTEA   NOT NULL,      -- 40바이트(AESWrap, AES-256 DEK) 예시
  nonce        BYTEA   NOT NULL,      -- 12바이트, DEK별로 겹치지 않게
  ciphertext   BYTEA   NOT NULL
);
```

- 회전 절차(예시): 새 KEK 버전 생성 → 쓰기를 새 버전으로 → 배치로 `wrapped_dek`만 다시 포장(작은 크기, 데이터 재암호화 없음) → 옛 버전 참조 0 확인 → 옛 KEK 비활성 → 보관 기한 뒤 폐기.
- 데이터 키 자체가 유출됐다면 KEK 회전으로는 부족하다. 그 DEK로 암호화한 데이터를 새 DEK로 다시 암호화한다(AWS KMS 문서의 주의와 같은 이유).

### 3. 시크릿 주입 (Spring Boot 예)

```yaml
# application.yml — 값이 아니라 참조만 둔다
payment:
  api-key: ${PAYMENT_API_KEY}        # 배포 환경·시크릿 저장소가 주입
```

- 로컬 개발용 값은 `.gitignore`된 파일에. 커밋 전 훅·CI·저장소 플랫폼의 시크릿 스캔을 켠다([engineering-practice/15](../../engineering-practice/15-security-standards/2-summary.md)의 "시크릿 스캔").
- 시크릿에도 소유자·만든 날·만료일·회전 절차를 적어 둔다. "누가 이 키를 쓰는지 모름"이 회전을 막는 가장 흔한 이유다.

### 4. 유출 대응 순서

```text
  1. 폐기·회전 (새 키 발급 → 소비자 교체 → 옛 키 비활성)      ← 가장 먼저
  2. 사용 기록 확인 (클라우드 감사 로그에서 그 키의 호출 이력)
  3. 영향 범위 산정·통지
  4. 이력 정리 (git-filter-repo 등, 포크·클론 한계 인지)
  5. 재발 방지 (스캐너, 짧은 수명 자격 증명)
```

## 장애 시나리오와 대처

### 1. 하드코딩 시크릿이 git으로 유출 (⚠ 커리큘럼, Uber 2016)

- **현상**: 저장소 접근 권한만 있는 사람(또는 저장소를 얻은 침입자)이 운영 클라우드·DB에 접근한다.
- **보이는 형태**: 클라우드 감사 로그에 평소와 다른 IP·시각의 대량 다운로드. 저장소 이력 스캔에서 키 패턴 발견(위 실험 형태). FTC 발표에 따르면 Uber는 2016년 11월에 알았고 2017년 11월까지 공개하지 않았다.
- **원인**: 키가 코드·설정 파일에 있었고, 비공개 저장소라고 안전하다고 봤다. 지워도 이력에 남는다.
- **대처**: 유출 대응 순서(적용 §4) — 회전이 먼저. 이후 시크릿 저장소·주입 방식으로 옮기고, 커밋 전 스캔과 장기 키 대신 짧은 수명 자격 증명을 쓴다.

### 2. 회전 절차 부재 → 유출 후 대응 불가 (⚠ 커리큘럼)

- **현상**: 키가 샌 것을 알았는데 며칠~몇 주 동안 바꾸지 못한다. 또는 급히 바꿨더니 서비스가 멈춘다.
- **보이는 형태**: 키 교체 배포 직후 `javax.crypto.AEADBadTagException`(복호 실패), `401`(서명 검증 실패), 외부 API의 인증 오류 폭증.
- **원인**: 키에 버전이 없어서 "새 키로 쓰기 + 옛 키로 읽기"를 동시에 못 한다. 그 키를 쓰는 소비자 목록이 없다.
- **대처**: 키 버전(`kid`·`kek_version`)을 데이터·토큰에 같이 기록, 읽기 경로는 여러 버전을 받게. 평소에 회전을 정기적으로 실행해 절차를 검증한다(회전을 한 번도 안 해 본 시스템은 비상시에도 못 한다).

### 3. 예측 가능한 난수 → 키·토큰 재계산 (Debian 2008)

- **현상**: 서로 다른 서버에서 같은 키가 생성된다. 리셋 토큰·세션 ID를 공격자가 맞힌다.
- **보이는 형태**: 키 지문(fingerprint) 중복. 공지 DSA-1571: 0.9.8c-1 이후 Debian OpenSSL로 만든 암호 재료를 전부 새로 만들라고 권했고("is recreated from scratch"), 그 시스템에서 **사용된** DSA 키도 손상으로 보라고 했다([06](../06-public-key-and-signatures/2-summary.md) §5).
- **원인**: 시드 엔트로피가 작아졌다(Debian 패치). 앱 수준에서는 `Random`·시각 시드·고정 시드 `SHA1PRNG`가 같은 부류다(위 실험).
- **대처**: OS CSPRNG 기반 `SecureRandom` 기본 생성자만 쓰도록 정적 분석 규칙(FindSecBugs `PREDICTABLE_RANDOM` 규칙). 의심되면 그 기간에 만든 키·토큰을 전부 재발급.

### 4. "KMS 키를 회전했으니 안전하다"는 착각

- **현상**: 데이터 키가 로그·덤프로 샜는데, KMS 키 회전만 하고 종료 처리했다.
- **보이는 형태**: 회전 이벤트(`RotateKey`)는 CloudTrail에 있지만, 샌 데이터 키로 암호화된 데이터는 그대로다.
- **원인**: KMS 회전은 KEK 재료만 바꾼다. 데이터 키를 바꾸거나 데이터를 다시 암호화하지 않는다(AWS KMS 문서).
- **대처**: 무엇이 샜는지에 따라 층을 고른다 — KEK 유출: KEK 회전 + DEK 재포장. 단 그 KEK로 포장된 DEK 사본도 샜을 수 있으면 재포장으로는 부족하다 — 그 DEK를 노출된 것으로 보고 새 DEK로 데이터를 재암호화한다(SP 800-57 Part 1 Rev.5 §5.5.1: 기밀성용 키가 새면 그 키로 암호화한 것 전부가 노출될 수 있다). DEK 유출: 해당 데이터 재암호화. 평문 데이터 유출: 키 회전으로는 되돌릴 수 없다.

## 핵심 문장

- 보안 값(키·salt·nonce·토큰)은 OS 엔트로피로 시드되는 CSPRNG에서 뽑고, `Random`·시각 시드·고정 시드는 예측 가능하다.
- Java `SecureRandom.setSeed`는 보통 시드를 보충하지만, `SHA1PRNG`에 첫 사용 전 시드를 주면 결정적이 된다.
- 키에는 수명(cryptoperiod)이 있고, 회전은 "새 키로 쓰기 + 옛 키로 읽기"를 버전으로 함께 지원해야 한다.
- 봉투 암호화는 DEK로 데이터를, KEK로 DEK를 암호화해 KEK 회전 때 데이터를 다시 암호화하지 않게 한다 — 대신 DEK 유출은 KEK 회전으로 해결되지 않는다.
- 시크릿은 코드와 git 밖에 두고, 유출되면 이력 삭제보다 폐기·회전이 먼저다.

## 관련 주제·근거

- 선행
  - [security/03-symmetric-encryption-and-aead](../03-symmetric-encryption-and-aead/2-summary.md) — DEK가 쓰는 AES-GCM, nonce 재사용 문제
  - [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md) · [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md) — PRNG·시드
- 후속·연결
  - [06-public-key-and-signatures](../06-public-key-and-signatures/2-summary.md) — ECDSA k와 난수 품질
  - [07-key-exchange-forward-secrecy](../07-key-exchange-forward-secrecy/2-summary.md) — 임시 키의 수명
  - [08-password-storage-and-kdf](../08-password-storage-and-kdf/2-summary.md) — salt 난수, pepper 보관
  - [security/13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md) — 서명 키 회전과 `kid`(기초: [원고 jwks](../../foundations/security/jwks.md))
  - [security/27-pii-classification-masking-retention](../27-pii-classification-masking-retention/2-summary.md) — 키 파기로 삭제(crypto-shredding)
  - [engineering-practice/15-security-standards](../../engineering-practice/15-security-standards/2-summary.md) — 시크릿 스캔·정적 분석
  - [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md) — 외부 노출 ID의 무작위성
- 1차 출처
  - NIST SP 800-57 Part 1 Rev.5 — 표 1 cryptoperiod, 표 2 보안 강도 <https://doi.org/10.6028/NIST.SP.800-57pt1r5>
  - NIST SP 800-90A Rev.1 DRBG `[?]`(본문 미대조) <https://csrc.nist.gov/pubs/sp/800/90/a/r1/final>
  - Java SE 21 `SecureRandom` Javadoc — setSeed 보충, 첫 사용 전 setSeed 시 자체 시드 생략, getInstanceStrong <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/security/SecureRandom.html>
  - Java SE 21 `Random` Javadoc — 48비트 시드 선형 합동 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Random.html>
  - Linux man-pages `random(7)` — Choice of random source
  - AWS KMS Developer Guide "Rotate AWS KMS keys" — 현재 키 재료만 교체, 데이터 키 미회전, 기본 365일 <https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html>
  - GitHub Docs "Removing sensitive data from a repository" — 먼저 폐기·회전, git-filter-repo, 포크·클론 한계 <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository>
  - FTC 보도자료 2018-04 "Uber Agrees to Expanded Settlement…" <https://www.ftc.gov/news-events/news/press-releases/2018/04/uber-agrees-expanded-settlement-ftc-related-privacy-security-claims>
  - Debian DSA-1571-1(2008-05-13), NVD CVE-2008-0166 <https://lists.debian.org/debian-security-announce/2008/msg00152.html>
- 실험(2026-10-07)
  - OpenJDK 21.0.12(eclipse-temurin:21-jdk, `--network none`) `Rng.java`(2회 실행): `Random` 시드 재현, 시각 시드 토큰의 시드 탐색, 기본 `SecureRandom`=NativePRNG의 setSeed 비결정 vs `SHA1PRNG` 사전 setSeed 결정, AES-GCM + AESWrap 봉투 암호화와 KEK 회전 / `getInstanceStrong()` 알고리즘 출력(`NativePRNGBlocking`)
  - git 2.43.0 로컬 일회용 저장소: AWS 문서 예시 키를 커밋 후 삭제 → HEAD에는 없음, `git log -S`·전 이력 정규식 스캔에서 발견
