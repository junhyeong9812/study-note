# security/09-randomness-and-key-management — 정답

## 정답

### 1. 왜 키와 난수인가

- 알고리즘은 공개돼 수십 년 분석을 받는다. 반면 키를 어디 두고, 어떻게 만들고, 언제 바꾸는지는 시스템마다 새로 짜는 부분이라 실수가 몰린다.
- 하드코딩 시크릿: 키가 코드·설정에 있으면 저장소에 닿는 누구나 쓴다. Uber 2016은 엔지니어가 코드 공유 사이트에 올린 접근 키로 클라우드 데이터가 유출됐다(FTC 2018-04).
- 회전 절차 부재: 유출을 알아도 키를 못 바꾸거나, 바꾸면 복호·검증이 깨져 서비스가 멈춘다. 그래서 유출 상태가 길어진다.

### 2. 시각 시드 토큰

- 1분 = 60,000ms → 후보 6만 개. 시드를 알면 `nextLong()`을 그대로 재현한다.
- 실험(OpenJDK 21.0.12): `seed found=true after 124 candidates in 0.3 ms`. 최악 6만 번도 수십 ms 수준이다(해석).
- 고침

```java
private static final SecureRandom RNG = new SecureRandom();
byte[] b = new byte[32]; RNG.nextBytes(b);
String token = Base64.getUrlEncoder().withoutPadding().encodeToString(b);
```

### 3. `setSeed` 두 갈래

- 기본 `new SecureRandom()`(실험에서 `NativePRNG`): 다르다. 두 실행 모두 `equal = false`.
- `SHA1PRNG` + 첫 사용 전 `setSeed(42)`: 같다. 두 번 실행 모두 `d50ac288b90ede2e`.
- Javadoc
  - "The seed supplements, rather than replaces, the existing seed." — 기본 구현은 OS 원천 위에 보충만 한다.
  - "A PRNG SecureRandom will not seed itself automatically if setSeed is called before any nextBytes or reseed calls." — SHA1PRNG는 준 시드만으로 결정적이 된다.

### 4. Linux 난수 원천

- `random(7)` "Choice of random source": 장기 키 생성이라도(아마 그때조차) `/dev/random`·`GRND_RANDOM`보다 `/dev/urandom` 또는 플래그 없는 `getrandom(2)`를 쓰라. `/dev/random`은 무기한 막힐 수 있고 부분 읽기 처리가 코드를 복잡하게 한다.
- 부팅 초기 풀이 준비되지 않은 경우: 같은 문서의 비교 표가 다룬다. `getrandom(2)`(플래그 없음)는 풀이 초기화될 때까지 기다린다.

### 5. 봉투 암호화와 KEK 회전

```text
  KMS 키 ─> KEK v1/v2 ─(wrap)─> [포장된 DEK + kek_version] ─(AES-GCM)─> 데이터 암호문
```

- 다시 하는 일: 포장된 DEK를 옛 KEK로 풀고 새 KEK로 다시 포장, `kek_version` 갱신.
- 하지 않는 일: 데이터 재암호화. 실험: `after KEK rotation: data ct untouched, decrypt via kek-v2 = ...`.
- 주의: 옛 KEK로 포장된 DEK를 새 KEK로 풀면 실패한다(`InvalidKeyException`). 버전을 같이 저장해야 하는 이유다.

### 6. KMS 회전과 데이터 키 유출

- 도움이 안 된다. AWS KMS 문서: 회전은 KMS 키의 현재 재료만 바꾸며, "KMS 키가 만든 데이터 키를 회전하거나 데이터를 다시 암호화하지 않는다. 유출된 데이터 키의 영향을 줄이지 못한다."
- 할 일: 유출된 DEK로 암호화된 데이터를 새 DEK로 다시 암호화하고, 옛 DEK의 포장본을 폐기한다. 유출 경로(로그 등)도 막는다.

### 7. OUP와 받는 쪽 기간

- SP 800-57 표 1: 대칭 데이터 암호화 키 OUP 2년 미만, 받는 쪽 OUP + 3년 미만.
- 이유: 2년간 암호화한 데이터를 그 뒤에도 읽어야(복호) 하기 때문이다.
- 회전 설계 요구: 새 키로 쓰기와 옛 키로 읽기를 동시에 지원(키 버전 기록), 옛 키는 읽기 전용으로 남겼다가 참조가 사라지면 폐기.

### 8. 지운 커밋의 키

- 안전하지 않다. 이력에 남는다.
  - 실험(git 2.43.0): `git grep AKIA HEAD`는 없음, `git log -S` 와 전 이력 스캔은 첫 커밋에서 발견.
- 대응 순서
  1. 키 폐기·회전(가장 먼저 — GitHub 문서도 "먼저 폐기·회전").
  2. 클라우드 감사 로그에서 그 키의 사용 이력 확인.
  3. 영향 범위 산정.
  4. 필요하면 이력 재작성(git-filter-repo) — 포크·클론에는 남는다는 한계.
  5. 시크릿 저장소·주입 방식, 커밋 전 스캔, 짧은 수명 자격 증명.

### 9. 키 교체 배포 후 복호·검증 실패

- 빠진 것: 키 버전. 새 키 하나로 바꿔 끼우니, 옛 키로 암호화된 데이터(`AEADBadTagException`)와 옛 키로 서명된 토큰(`401`)을 읽을 방법이 사라졌다.
- 고침
  - 데이터·토큰에 키 버전(`kek_version`, `kid`)을 기록한다.
  - 읽기·검증 경로는 여러 버전을 받는다. 쓰기·서명만 새 버전.
  - 순서: 새 키 배포(읽기 가능) → 쓰기 전환 → 옛 참조 소진(재포장·토큰 만료) → 옛 키 비활성.
  - 회전을 정기적으로 실행해 절차를 검증해 둔다. 서명 키 쪽 세부는 [security/13-jwks-and-key-rotation](../13-jwks-and-key-rotation/2-summary.md).
