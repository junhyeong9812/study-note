# rust/rust-testing-security/10 — 비밀번호 해싱 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 103 문자 — `$` 셋 + `1000` 넷 + 솔트 32 + 해시 64

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
길이: 103 문자
```

**왜 그런가**

저장 형식은 `$반복횟수$솔트hex$해시hex` 다.
`$` 가 3개, `1000` 이 4글자다.
솔트는 16바이트를 두 글자씩 hex 로 바꿔 32글자, 해시는 32바이트라 64글자다.
3 + 4 + 32 + 64 = 103 이다.
솔트와 해시의 내용은 매번 달라도 길이는 고정이라 이 값은 변하지 않는다.
근거: 2-summary 「동작 방식 (3)」.

### 2. `false` · `true` · `false` · `true`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  동일: false
올바른 비밀번호: true
틀린 비밀번호:   false
올바른(해시2):   true
```

**왜 그런가**

두 번의 `hash_password` 는 각각 새 솔트를 만든다.
솔트가 다르면 솔트 hex 부분도, 그 솔트로 계산한 해시 부분도 달라 두 문자열이 다르다.
다만 솔트가 시각에서 나오므로, 두 호출의 시각 값이 같게 읽히는 드문 경우에는 `true` 가 될 수도 있다 (OS 시계 해상도에 달림 — 확인 필요).
검증은 저장 문자열 안의 솔트와 반복 횟수로 입력을 다시 해싱해 견준다.
올바른 비밀번호는 같은 값이 나와 `true` 다.
`"wrong"` 은 다른 해시가 나와 `false` 다 (이 장난감 해시가 우연히 충돌하지 않는다는 전제 — 원본에 근거 없음 — 추론).
해시2 도 자기 솔트를 품고 있으므로 원래 비밀번호면 통과해 `true` 다.
근거: 2-summary 「동작 방식 (1)」 「(3)」 「(4)」, 「어디서 틀리나 3」.

### 3. `true` — 검증은 저장 문자열의 반복 횟수를 쓴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
true
```

**왜 그런가**

`verify_password` 는 `self.iterations`(10)를 쓰지 않는다.
저장 문자열의 `parts[1]`(1000)을 읽어 `PasswordHasher::new(iterations)` 로 새 해셔를 만들고 그것으로 다시 해싱한다.
그래서 저장할 때와 같은 1000 라운드가 재현되어 같은 해시가 나온다.
근거: 2-summary 「동작 방식 (4)」 2번 해설.

### 4. 솔트의 일은 숨기가 아니라 해시를 서로 다르게 만드는 것이다

검증할 때 같은 솔트로 다시 해싱해야 하므로 솔트는 어딘가에 남아 있어야 한다.
솔트가 하는 일은 같은 비밀번호라도 사용자마다 · 해싱마다 다른 저장값을 만들어, 미리 계산한 레인보우 테이블이 통하지 않게 하는 것이다.
공격자가 솔트를 알아도 그 솔트 하나에 맞춰 후보를 처음부터 다시 해싱해야 하므로 미리 계산의 이득이 사라진다.
근거: 2-summary 「동작 방식 (3)」 5번 해설, 「어디서 틀리나 2」.

### 5. 빠르면 대입 시도를 많이 할 수 있다 — 반복은 시도 하나의 값을 올린다

원본의 팁대로 SHA/MD5 는 너무 빨라서 브루트포스에 취약하다.
원본은 GPU 로 초당 수십억 개를 계산할 수 있다고 적는다 (수치는 원본의 주장 — 확인 필요).
반복 라운드(key stretching)는 해시 한 번에 `iterations` 만큼 계산을 되풀이하게 만든다.
공격자도 후보 하나마다 같은 횟수를 돌려야 하므로 같은 시간에 시도할 수 있는 수가 그만큼 줄어든다.
전용 알고리즘이 「의도적으로 느린」 까닭이 이것이다.
근거: 2-summary 「동작 방식 (2)」 7번 해설, 「어디서 틀리나 1」.

### 6. 0 을 곱해 칸의 정보가 지워지는 일을 막는다

`| 1` 은 맨 아래 비트를 1 로 만들어 곱하는 값이 절대 0 이 되지 않게 한다.
0 을 곱하면 `(자기 + 다음 칸)` 의 정보가 그 라운드에서 통째로 사라진다.
정답 코드의 주석도 「| 1로 0 곱셈 방지」라고 적는다.
근거: 2-summary 「동작 방식 (2)」 4번 해설.

### 7. 중간에 멈추면 걸린 시간으로 「어디까지 맞았나」가 샌다

보통의 비교는 처음 다른 자리에서 멈출 수 있어, 앞부분이 많이 맞을수록 늦게 끝난다.
공격자는 그 시간 차이를 재서 한 글자씩 맞혀 갈 수 있다 — 타이밍 공격이다.
`constant_time_compare` 는 모든 바이트 쌍의 XOR 을 OR 로 누적하고 끝까지 다 돈 뒤에야 0 인지 본다.
그래서 어디서 틀렸든 같은 횟수만큼 돈다.
길이가 다를 때 곧장 `false` 를 내는 것은 해시 hex 길이가 형식상 알려진 값이라 숨길 것이 없기 때문이다.
단, 이 코드가 실제 기계어에서도 시간 차 없이 도는지는 언어가 보장하지 않는다 (확인 필요).
근거: 2-summary 「동작 방식 (5)」, 「구현 세부사항 대 언어 보장」.

### 8. 짧으면 패닉, hex 아닌 글자는 조용히 0

솔트 hex 가 32글자보다 짧으면 `&salt_hex[i*2..i*2+2]` 가 범위를 넘어 **패닉**한다 — `false` 를 돌려주지 않는다.
여러 바이트 글자가 섞여 글자 경계에서 잘려도 패닉할 수 있다.
조각 개수와 반복 횟수는 검사해 `false` 로 막지만 솔트 길이는 검사하지 않기 때문이다.
hex 가 아닌 영문자 두 글자는 `from_str_radix` 가 실패하고 `unwrap_or(0)` 이 0 을 넣어 조용히 진행한다.
그 결과 다른 솔트로 해싱하게 되어 보통 `false` 가 나온다.
근거: 2-summary 「어디서 틀리나 5」, 「동작 방식 (4)」 3·4번 해설.

### 9. 「해싱마다 다르게」는 대체로 채우지만 「예측 불가」는 못 채운다

시각은 계속 바뀌므로 연달아 부른 두 솔트는 보통 다르다 — 같은 비밀번호에 다른 저장값을 만드는 일은 대체로 해낸다.
하지만 시각은 짐작할 수 있고, 상위 바이트는 거의 바뀌지 않거나 늘 0 이다.
시계 해상도에 따라 같은 값이 나올 수도 있다 (확인 필요).
시스템 시각이 기원보다 앞서면 솔트가 전부 0 이 된다.
그래서 원본은 「실제로는 CSPRNG 사용」이라 하고, 실제 코드는 `OsRng` 를 쓴다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 3」.

### 10. 솔트 생성 · 해싱 · 파싱 · 검증이 한 호출씩 짝을 이룬다

- `generate_salt` ↔ `SaltString::generate(&mut OsRng)`
- `PasswordHasher::new(1000)` ↔ `Argon2::default()`
- `hash_password` ↔ `argon2.hash_password(password.as_bytes(), &salt)?` 뒤 `.to_string()`(PHC 형식 문자열)
- `split('$')` 로 반복 횟수 · 솔트를 되살리는 부분 ↔ `PasswordHash::new(&hash_string)?`
- `verify_password` ↔ `Argon2::default().verify_password(password.as_bytes(), &parsed)?`

두 쪽 모두 「솔트와 파라미터를 해시와 함께 한 문자열에 담고, 검증할 때 그것을 읽어 다시 계산한다」는 같은 뼈대다.
근거: 2-summary 「동작 방식 (6)」.

## 실습 정답

### 실습 1. 솔트 · 반복 · 상수 시간 비교를 갖춘 비밀번호 해싱 시뮬레이션 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 구조체와 `new` | `struct PasswordHasher { iterations: u32 }`, `fn new` |
| 2. 시각 기반 16바이트 솔트 | `generate_salt` — `as_nanos()`, `(now >> (i * 8)) & 0xFF` |
| 3. 비밀번호 + 솔트를 XOR 로 접기 | `hash_with_salt` — `combined.extend_from_slice(salt)`, `hash[i % 32] ^= byte` |
| 4. 라운드 섞기(wrapping) | `for round in 0..self.iterations` — `wrapping_add` · `wrapping_mul(hash[(i + 7) % 32] \| 1)` · `round as u8` |
| 5. 32바이트 반환 | `-> [u8; 32]` |
| 6. `$반복$솔트$해시` 문자열 | `hash_password` — `format!("{:02x}", b)`, `format!("${}${}${}", …)` |
| 7. 조각 4개 · 반복 파싱 실패 시 `false` | `verify_password` — `parts.len() != 4`, `match parts[1].parse()` |
| 8. 솔트 복원 · 저장된 반복으로 재해싱 | `u8::from_str_radix(…, 16).unwrap_or(0)`, `PasswordHasher::new(iterations)` |
| 9. 상수 시간 비교로 판정 | `constant_time_compare(&computed_hex, parts[3])` |
| 10. 길이 검사 + XOR · OR 누적 | `fn constant_time_compare` — `fold(0u8, \|acc, (x, y)\| acc \| (x ^ y))` |
| 11. 해싱 · 길이 출력 | `main` 의 `=== 비밀번호 해싱 ===` 절 |
| 12. 두 번째 해시와 비교 | `hashed2`, `hashed == hashed2` |
| 13. 세 가지 검증 | `=== 비밀번호 검증 ===` 절의 `verify_password` 세 줄 |
| 14. 설명 · 알고리즘 · argon2 · 체크리스트 | `main` 의 3 · 4 · 5 절 `println!` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-testing-security/reference/password-hashing.rs`

```rust
// [테스팅 & 보안] 비밀번호 해싱
// 설명: argon2, bcrypt 패턴, 비밀번호 해싱/검증, 솔트
// 팁: 비밀번호에는 반드시 전용 해싱 알고리즘(argon2id 권장)을 사용한다. 매번 랜덤 솔트를 생성하고, 비교는 상수 시간(constant-time)으로 해야 타이밍 공격을 방지한다. SHA/MD5는 비밀번호에 절대 쓰지 않는다 - 너무 빨라서 브루트포스에 취약하다.

// === 비밀번호 해싱 패턴 ===
// 실제: argon2 = "0.5" 또는 bcrypt = "0.15"

// === 간단한 비밀번호 해싱 시뮬레이션 ===
// 주의: 이것은 교육용 시뮬레이션입니다. 실제 사용하면 안 됩니다!

// 비밀번호 해싱 동작을 캡슐화한 struct
struct PasswordHasher {
    // 간단한 PBKDF2-like 반복 해싱
    // key stretching을 위한 반복 횟수
    iterations: u32,
}

impl PasswordHasher {
    // 반복 횟수로 해셔 생성
    fn new(iterations: u32) -> Self {
        PasswordHasher { iterations }
    }

    // 솔트 생성 (실제로는 CSPRNG 사용)
    // 16바이트 솔트를 생성 (시뮬레이션 - 실제는 OsRng)
    fn generate_salt(&self) -> [u8; 16] {
        // 시뮬레이션: 고정 방법 대신 시간 기반
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos();
        let mut salt = [0u8; 16];
        // 시각 비트를 바이트별로 펼침
        for (i, byte) in salt.iter_mut().enumerate() {
            *byte = ((now >> (i * 8)) & 0xFF) as u8;
        }
        salt
    }

    // 비밀번호 + 솔트 해싱
    // 반복 라운드로 의도적으로 느리게 만든 해시
    fn hash_with_salt(&self, password: &str, salt: &[u8; 16]) -> [u8; 32] {
        let mut hash = [0u8; 32];

        // 초기 해시: password + salt 결합
        let mut combined = password.as_bytes().to_vec();
        combined.extend_from_slice(salt);

        // 단순한 XOR 분배로 초기 상태 채움
        for (i, byte) in combined.iter().enumerate() {
            hash[i % 32] ^= byte;
        }

        // 반복 해싱 (key stretching) - 브루트포스 비용 증가
        for round in 0..self.iterations {
            let mut new_hash = [0u8; 32];
            // 각 바이트가 다음 바이트와 7번째 바이트에 의존하게 섞음
            for i in 0..32 {
                new_hash[i] = hash[i]
                    .wrapping_add(hash[(i + 1) % 32])
                    // | 1로 0 곱셈 방지
                    .wrapping_mul(hash[(i + 7) % 32] | 1)
                    .wrapping_add(round as u8);
            }
            hash = new_hash;
        }

        hash
    }

    // 비밀번호 해시 생성 (솔트 포함)
    // PHC 스타일 형식으로 솔트와 해시를 함께 저장
    fn hash_password(&self, password: &str) -> String {
        // 매번 새로운 랜덤 솔트
        let salt = self.generate_salt();
        let hash = self.hash_with_salt(password, &salt);

        // 형식: $iterations$salt_hex$hash_hex
        // 솔트와 해시를 hex 문자열로 변환
        let salt_hex: String = salt.iter().map(|b| format!("{:02x}", b)).collect();
        let hash_hex: String = hash.iter().map(|b| format!("{:02x}", b)).collect();

        format!("${}${}${}", self.iterations, salt_hex, hash_hex)
    }

    // 비밀번호 검증
    // 저장된 해시와 입력 비밀번호 비교
    fn verify_password(&self, password: &str, stored: &str) -> bool {
        // $로 분리 - [empty, iterations, salt, hash]
        let parts: Vec<&str> = stored.split('$').collect();
        if parts.len() != 4 { return false; }

        // 해시 생성 시 사용된 반복 횟수 복원
        let iterations: u32 = match parts[1].parse() {
            Ok(n) => n,
            Err(_) => return false,
        };

        // 솔트 복원 - hex 문자열 -> 바이트
        let salt_hex = parts[2];
        let mut salt = [0u8; 16];
        for i in 0..16 {
            salt[i] = u8::from_str_radix(&salt_hex[i*2..i*2+2], 16).unwrap_or(0);
        }

        // 같은 파라미터로 후보 해시 계산
        let hasher = PasswordHasher::new(iterations);
        let computed = hasher.hash_with_salt(password, &salt);
        let computed_hex: String = computed.iter().map(|b| format!("{:02x}", b)).collect();

        // 타이밍 공격 방지를 위해 상수 시간 비교 사용해야 함
        constant_time_compare(&computed_hex, parts[3])
    }
}

// 타이밍 공격 방지 비교
// 길이가 같으면 모든 바이트를 끝까지 비교 (조기 반환 없음)
fn constant_time_compare(a: &str, b: &str) -> bool {
    if a.len() != b.len() { return false; }
    // XOR 결과를 OR로 누적 - 한 바이트라도 다르면 비트가 남음
    let result: u8 = a.bytes().zip(b.bytes())
        .fold(0u8, |acc, (x, y)| acc | (x ^ y));
    result == 0
}

// 메인: 해싱/검증/같은 비밀번호의 다른 해시(솔트 효과) 시연
fn main() {
    // 1000 라운드의 해셔
    let hasher = PasswordHasher::new(1000);

    // === 1. 비밀번호 해싱 ===
    println!("=== 비밀번호 해싱 ===");
    let password = "MySecureP@ssw0rd";
    let hashed = hasher.hash_password(password);
    println!("비밀번호: {}", password);
    println!("해시: {}", hashed);
    println!("길이: {} 문자", hashed.len());

    // 같은 비밀번호도 매번 다른 해시 (솔트 때문)
    // 솔트 효과: 같은 입력이라도 솔트가 다르면 다른 해시
    let hashed2 = hasher.hash_password(password);
    println!("\n같은 비밀번호, 다른 해시:");
    println!("  해시1: {}", hashed);
    println!("  해시2: {}", hashed2);
    println!("  동일: {}", hashed == hashed2); // false!

    // === 2. 비밀번호 검증 ===
    println!("\n=== 비밀번호 검증 ===");
    // 정상 케이스 - 통과해야 함
    println!("올바른 비밀번호: {}", hasher.verify_password(password, &hashed));
    // 틀린 비밀번호 - 거부되어야 함
    println!("틀린 비밀번호:   {}", hasher.verify_password("wrong", &hashed));
    // 다른 솔트의 해시도 같은 원본 비밀번호면 검증 통과
    println!("올바른(해시2):   {}", hasher.verify_password(password, &hashed2));

    // === 3. 왜 일반 해시를 쓰면 안 되는가 ===
    println!("\n=== 비밀번호에 SHA를 쓰면 안 되는 이유 ===");
    println!("1. SHA는 빠르다 -> 브루트포스 공격에 취약");
    println!("   GPU로 초당 수십억 개 해시 가능");
    println!("2. 솔트 없으면 레인보우 테이블 공격 가능");
    println!("3. 비밀번호 해싱 전용 알고리즘은 의도적으로 느림");

    println!("\n=== 올바른 비밀번호 해싱 알고리즘 ===");
    println!("1. Argon2id (권장) - 메모리 하드, 2015 PHC 우승");
    println!("2. bcrypt          - 오래되었지만 여전히 안전");
    println!("3. scrypt          - 메모리 하드");
    println!("4. PBKDF2          - 가장 오래된 표준, 반복 기반");

    // === 4. 실제 argon2 크레이트 사용법 ===
    println!("\n=== 실제 argon2 코드 ===");
    println!("// Cargo.toml: argon2 = \"0.5\"");
    println!("// use argon2::{{Argon2, PasswordHash, PasswordHasher, PasswordVerifier}};");
    println!("// use argon2::password_hash::SaltString;");
    println!("// use argon2::password_hash::rand_core::OsRng;");
    println!("// ");
    println!("// 해싱:");
    println!("// let salt = SaltString::generate(&mut OsRng);");
    println!("// let argon2 = Argon2::default();");
    println!("// let hash = argon2.hash_password(password.as_bytes(), &salt)?;");
    println!("// let hash_string = hash.to_string();  // PHC 형식");
    println!("// ");
    println!("// 검증:");
    println!("// let parsed = PasswordHash::new(&hash_string)?;");
    println!("// Argon2::default().verify_password(password.as_bytes(), &parsed)?;");

    // === 5. 보안 체크리스트 ===
    println!("\n=== 비밀번호 보안 체크리스트 ===");
    println!("[필수] 전용 해싱 알고리즘 (argon2, bcrypt)");
    println!("[필수] 랜덤 솔트 (사용자마다 다른 솔트)");
    println!("[필수] 상수 시간 비교 (타이밍 공격 방지)");
    println!("[권장] 비밀번호 정책 (최소 길이, 복잡성)");
    println!("[금지] 평문 저장");
    println!("[금지] MD5, SHA 단독 사용");
    println!("[금지] 하드코딩된 솔트");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**

- 해싱과 검증이 **같은 `hash_with_salt`** 를 쓰는 것이 핵심이다 — 같은 입력 · 솔트 · 반복이면 같은 바이트가 나와야 검증이 성립한다.
- 검증은 `self.iterations` 가 아니라 저장 문자열의 반복 횟수로 새 해셔를 만든다.
- `split('$')` 의 첫 조각이 빈 문자열이라 조각 수 검사는 `4` 다.
- 라운드 식은 넘침을 감수하는 섞기라 `wrapping_*` 를 쓰고, `| 1` 로 0 곱셈을 막는다.
- 비교는 `==` 가 아니라 끝까지 도는 XOR · OR 누적이다.
- 이 코드는 교육용이다 — 솔트는 `OsRng`, 해싱은 Argon2id 같은 전용 알고리즘으로 바꿔야 실제로 쓸 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
