# rust/rust-testing-security/11 — 대칭 암호화 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 길이는 35 (nonce 12 + 데이터 23), 앞 12바이트는 nonce 그대로다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
암호문 길이: 35 (nonce 12 + 데이터 23)
```

앞 12바이트는 `generate_nonce()` 가 준 nonce 바이트가 XOR 없이 그대로 들어간 것이다.

**왜 그런가**
`b"Hello, encrypted world!"` 는 글자를 세면 23바이트다.
`encrypt` 는 `nonce.to_vec()` 로 결과를 시작하고 그 뒤에 23바이트 암호문을 `extend_from_slice` 로 붙인다.
그래서 길이는 12 + 23 = 35 이고, 앞부분은 nonce 다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 패닉하지 않는다 — `Ok(깨진 바이트)` 를 꺼낸다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`unwrap()` 은 패닉하지 않고 23바이트를 꺼낸다.
그 바이트는 원래 평문과 다르며, `from_utf8_lossy` 를 거치면 알아볼 수 없는 글자와 대체 문자(`�`)가 섞여 찍힐 것으로 본다.
정확한 바이트 값은 손으로 짐작할 수 없다.

**왜 그런가**
장난감 `decrypt` 가 `Err` 를 내는 경우는 데이터가 `nonce_len` 보다 짧을 때뿐이다.
35바이트 ≥ 12 이므로 언제나 `Ok` 다.
키가 다르면 시작 상태가 달라져 키스트림이 통째로 바뀌고, 그 키스트림으로 XOR 한 결과는 원래 평문이 아니다.
인증이 없으니 「틀렸다」는 것을 알릴 길이 없다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 3. 「동일: false」 — 다만 찍힌 8바이트는 nonce 의 일부다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  동일: false
```

`enc1[..8]` · `enc2[..8]` 은 각 결과 벡터의 맨 앞, 곧 `nonce1` · `nonce2` 의 앞 8바이트다.

**왜 그런가**
두 nonce 는 1ms 이상 떨어진 시각에서 만들어져 낮은 자리 바이트가 다를 것으로 본다.
nonce 가 다르면 결과 앞부분부터 다르고, 키스트림도 달라져 뒤의 암호문 23바이트도 달라진다.
그래서 전체 벡터 비교 `enc1 == enc2` 는 `false` 다.
그런데 `encrypt` 결과의 앞 12바이트는 nonce 그대로이므로, 찍힌 앞 8바이트만으로는 암호문이 다르다는 것을 보여 주지 못한다.
근거: 2-summary 「동작 방식 (2)·(4)」 · 「어디서 틀리나 8」.
(시각이 1ms 동안 반드시 바뀐다는 것은 운영체제 시계에 달린 일이다 — 2-summary 「구현 세부사항 대 언어 보장」.)

### 4. XOR 은 같은 값을 두 번 하면 원래대로 돌아오기 때문이다

암호문은 `c = p ^ k` 이다.
같은 키와 같은 nonce 로 `derive_keystream` 을 다시 부르면 같은 `k` 가 나온다(결정적이다).
`c ^ k = (p ^ k) ^ k = p` 이므로 같은 연산으로 평문이 돌아온다.
근거: 2-summary 「동작 방식 (1)·(3)」.

### 5. nonce 는 비밀이 아니고, 복호화에 꼭 필요하기 때문이다

대칭 암호화에서 비밀은 키뿐이다.
nonce 는 「같은 키로도 매번 다른 키스트림을 만들게 하는 값」이라 드러나도 키 없이는 키스트림을 만들 수 없다.
반대로 받는 쪽은 같은 nonce 가 있어야 같은 키스트림을 다시 만들 수 있다.
그래서 nonce 를 암호문 앞에 붙여 함께 보낸다.
근거: 2-summary 「동작 방식 (2)」.

### 6. 두 평문의 XOR(`p1 ^ p2`)이 키 없이 드러난다

같은 키 + 같은 nonce → 같은 키스트림 `k` 다.
`c1 ^ c2 = (p1 ^ k) ^ (p2 ^ k) = p1 ^ p2` 로 `k` 가 지워진다.
한쪽 평문을 알거나 짐작하면 다른 쪽 평문도 풀린다.
원본 팁이 「같은 키에서 절대 재사용하면 안 된다」고 하는 까닭이다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 7. 같은 시각 값을 두 번 읽거나, 시계가 `UNIX_EPOCH` 이전일 때다

- 두 번 부른 사이에 시계 값이 바뀌지 않으면 같은 nonce 가 나온다 — 예제가 `sleep(1ms)` 을 끼운 까닭이다.
- 시계가 `UNIX_EPOCH` 이전이면 `duration_since` 가 실패하고 `unwrap_or_default()` 가 0 을 주어, 매번 0바이트 12개짜리 nonce 가 나온다.
- 겹치지 않더라도 시각은 남이 짐작할 수 있는 값이다.
그래서 원본은 이것을 시뮬레이션이라 하고 실제로는 `OsRng` 같은 CSPRNG 을 쓰라고 한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 8. 255바이트를 넘으면 헤더가 틀린다 — `as u8` 가 잘라 내기 때문이다

`to_bytes` 는 길이를 `self.nonce.len() as u8` 한 바이트로 적는다.
`as u8` 는 낮은 8비트만 남기므로 256 이상이면 실제 길이와 다른 값이 적힌다.
그러면 `from_bytes` 가 nonce 와 암호문의 경계를 잘못 자른다.
12바이트 nonce 에서는 문제가 없다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 9」.

### 9. AES-GCM 이었다면 틀린 키에서 복호화가 실패(`Err`)한다

GCM 은 인증된 암호화(AEAD)라 암호화와 함께 변조 감지까지 한다(원본 팁).
원본 주석도 「실제 GCM 은 인증 실패로 거부」한다고 적는다.
그래서 `aes-gcm` 의 `cipher.decrypt(...)` 는 `Result` 를 돌려주고, 틀린 키 · 변조된 암호문이면 깨진 평문 대신 실패가 돌아온다.
2번처럼 「`Ok` 인데 쓰레기」가 되는 일이 막힌다.
근거: 2-summary 「동작 방식 (3)·(6)」.

### 10. 키 생성 · 암호화기 생성 · nonce 생성 · encrypt · decrypt 가 하나씩 맞물린다

| 예제 | `aes-gcm` |
|---|---|
| 코드에 박은 키 + `SimpleCipher::new(key)` | `Aes256Gcm::generate_key(&mut OsRng)` + `Aes256Gcm::new(&key)` |
| `generate_nonce()` (시각 기반) | `Aes256Gcm::generate_nonce(&mut OsRng)` |
| `cipher.encrypt(plaintext, &nonce)` | `cipher.encrypt(&nonce, plaintext.as_ref())?` |
| `cipher.decrypt(&encrypted, nonce_len)` | `cipher.decrypt(&nonce, ciphertext.as_ref())?` |

차이는 키 · nonce 를 CSPRNG(`OsRng`)으로 만든다는 점과, `encrypt` · `decrypt` 가 `?` 로 실패를 전한다는 점이다.
근거: 2-summary 「동작 방식 (6)」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. XOR 장난감 암호로 대칭 암호화의 흐름 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 키를 담고 빈 키 거부 | `struct SimpleCipher { key }`, `SimpleCipher::new` 의 `assert!(!key.is_empty(), ...)` |
| 2. 키스트림 생성 | `derive_keystream` — `wrapping_mul(31)` · `wrapping_mul(37)` · `wrapping_mul(6364136223846793005).wrapping_add(1)` · `(state >> 33) as u8` |
| 3. XOR 후 nonce 를 앞에 붙임 | `encrypt` — `zip(...).map(\|(p, k)\| p ^ k)`, `nonce.to_vec()` + `extend_from_slice` |
| 4. 길이 검사 후 분리 · 복호화 | `decrypt` — `if data.len() < nonce_len`, `&data[..nonce_len]` · `&data[nonce_len..]`, `c ^ k` |
| 5. 시각 기반 12바이트 nonce | `generate_nonce` — `duration_since(UNIX_EPOCH).unwrap_or_default().as_nanos()`, `(now >> (i * 8)) & 0xFF` |
| 6. `Debug` 파생 구조체 | `#[derive(Debug)] struct EncryptedMessage` |
| 7. 길이 헤더 직렬화 | `to_bytes` — `result.push(self.nonce.len() as u8)` |
| 8. 검증 포함 역직렬화 | `from_bytes` — `Err("빈 데이터")` · `Err("데이터 부족")` · `data[1..1+nonce_len]` |
| 9. 기본 암호화/복호화 시연 | `main` 의 `cipher.encrypt` · `{:02X?}` · `20.min(...)` · `assert_eq!(plaintext.to_vec(), decrypted)` |
| 10. 잘못된 키 시연 | `wrong_cipher.decrypt(...).unwrap()` + `String::from_utf8_lossy` |
| 11. Nonce 중요성 시연 | `nonce1` · `sleep(from_millis(1))` · `nonce2`, `enc1 == enc2` |
| 12. 직렬화 왕복 시연 | `EncryptedMessage { nonce, ciphertext: encrypted[nonce.len()..] }`, `to_bytes` → `from_bytes` |
| 13. aes-gcm 사용법 · 규칙 찍기 | `=== 실제 aes-gcm 코드 ===` · `=== 암호화 핵심 규칙 ===` 의 `println!` 묶음 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-testing-security/reference/encryption.rs`

```rust
// [테스팅 & 보안] 대칭 암호화
// 설명: AES-GCM 패턴, 대칭 암호화, 키 생성, nonce 관리
// 팁: 대칭 암호화는 AES-256-GCM이 표준이다. GCM 모드는 인증된 암호화(AEAD)로 변조 감지까지 포함한다. Nonce는 같은 키에서 절대 재사용하면 안 된다(보통 12바이트 랜덤). 자체 암호화 구현은 절대 하지 말고 검증된 크레이트를 사용하자.

// === 대칭 암호화 패턴 ===
// 실제: aes-gcm = "0.10"
// 여기서는 XOR 기반 간단한 암호화로 패턴을 보여줍니다.

// === 1. 간단한 XOR 암호화 (교육용) ===
// 주의: XOR 암호화는 안전하지 않습니다. 패턴만 참고하세요.

// 키를 보관하는 단순 암호화기 구조체 (실제 사용 금지)
struct SimpleCipher {
    // 비밀 키 바이트 (실제 AES는 16/24/32바이트)
    key: Vec<u8>,
}

impl SimpleCipher {
    // 키 슬라이스로 새로운 암호화기 생성
    fn new(key: &[u8]) -> Self {
        // 빈 키는 절대 안전하지 않으므로 거부
        assert!(!key.is_empty(), "키는 비어있을 수 없습니다");
        SimpleCipher { key: key.to_vec() }
    }

    // 평문을 nonce와 함께 암호화하여 nonce가 prefix된 ciphertext 반환
    fn encrypt(&self, plaintext: &[u8], nonce: &[u8]) -> Vec<u8> {
        // nonce + key로 키스트림 생성 (실제로는 AES-CTR 등 사용)
        let keystream = self.derive_keystream(nonce, plaintext.len());
        // 평문과 키스트림을 XOR하여 암호문 생성
        let ciphertext: Vec<u8> = plaintext.iter()
            .zip(keystream.iter())
            .map(|(p, k)| p ^ k)
            .collect();

        // nonce를 앞에 붙임 (복호화시 필요)
        let mut result = nonce.to_vec();
        result.extend_from_slice(&ciphertext);
        result
    }

    // nonce가 prefix된 데이터를 받아 평문으로 복호화
    fn decrypt(&self, data: &[u8], nonce_len: usize) -> Result<Vec<u8>, String> {
        // 길이 검증으로 패닉 방지
        if data.len() < nonce_len {
            return Err("데이터가 너무 짧습니다".to_string());
        }

        // 앞부분 nonce, 뒷부분 ciphertext로 분리
        let nonce = &data[..nonce_len];
        let ciphertext = &data[nonce_len..];
        // 같은 nonce로 같은 키스트림을 재생성 (XOR의 특성)
        let keystream = self.derive_keystream(nonce, ciphertext.len());

        // 다시 XOR하여 평문 복원
        let plaintext: Vec<u8> = ciphertext.iter()
            .zip(keystream.iter())
            .map(|(c, k)| c ^ k)
            .collect();

        Ok(plaintext)
    }

    // 키와 nonce로부터 결정적 의사난수 키스트림 생성 (LCG)
    fn derive_keystream(&self, nonce: &[u8], len: usize) -> Vec<u8> {
        let mut stream = Vec::with_capacity(len);
        // 초기 상태 - LCG 시드
        let mut state: u64 = 0;

        // nonce와 key를 혼합하여 초기 상태 생성
        for &b in nonce {
            state = state.wrapping_mul(31).wrapping_add(b as u64);
        }
        for &b in &self.key {
            state = state.wrapping_mul(37).wrapping_add(b as u64);
        }

        // LCG 반복으로 바이트씩 키스트림 채움
        for _ in 0..len {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
            // 상위 비트가 더 무작위적이라 33비트 시프트
            stream.push((state >> 33) as u8);
        }

        stream
    }
}

// === 2. Nonce 생성 (시뮬레이션) ===
// 12바이트 nonce를 생성 (실제는 OsRng 같은 CSPRNG 사용)
fn generate_nonce() -> [u8; 12] {
    // 현재 시각 나노초로 시드 (시뮬레이션 - 실제로는 부적합)
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let mut nonce = [0u8; 12];
    // 시간 비트를 바이트별로 펼쳐넣음
    for (i, byte) in nonce.iter_mut().enumerate() {
        *byte = ((now >> (i * 8)) & 0xFF) as u8;
    }
    nonce
}

// === 3. 암호화된 메시지 구조체 ===
// 직렬화 가능한 nonce+ciphertext 묶음
#[derive(Debug)]
struct EncryptedMessage {
    nonce: Vec<u8>,
    ciphertext: Vec<u8>,
}

impl EncryptedMessage {
    // 바이트 형식으로 직렬화 [nonce_len(1)][nonce][ciphertext]
    fn to_bytes(&self) -> Vec<u8> {
        let mut result = Vec::new();
        // 첫 바이트에 nonce 길이 기록
        result.push(self.nonce.len() as u8);
        result.extend_from_slice(&self.nonce);
        result.extend_from_slice(&self.ciphertext);
        result
    }

    // 바이트에서 역직렬화 - 길이 검증 포함
    fn from_bytes(data: &[u8]) -> Result<Self, String> {
        if data.is_empty() {
            return Err("빈 데이터".to_string());
        }
        // 길이 헤더 읽기
        let nonce_len = data[0] as usize;
        // 헤더가 가리키는 만큼 데이터가 있는지 확인
        if data.len() < 1 + nonce_len {
            return Err("데이터 부족".to_string());
        }
        Ok(EncryptedMessage {
            nonce: data[1..1+nonce_len].to_vec(),
            ciphertext: data[1+nonce_len..].to_vec(),
        })
    }
}

// 메인: 암호화/복호화/Nonce 효과/직렬화 시연
fn main() {
    // === 기본 암호화/복호화 ===
    println!("=== 기본 암호화/복호화 ===");
    // 32바이트 키 (시뮬레이션)
    let key = b"my-secret-key-32bytes-padding!!";
    let cipher = SimpleCipher::new(key);

    // 평문과 nonce 준비
    let plaintext = b"Hello, encrypted world!";
    let nonce = generate_nonce();
    let encrypted = cipher.encrypt(plaintext, &nonce);

    println!("평문: {:?}", String::from_utf8_lossy(plaintext));
    // 암호문 앞부분만 hex로 출력
    println!("암호문: {:02X?}", &encrypted[..20.min(encrypted.len())]);
    println!("암호문 길이: {} (nonce {} + 데이터 {})",
        encrypted.len(), nonce.len(), plaintext.len());

    // 복호화 - 같은 키로 라운드트립 검증
    let decrypted = cipher.decrypt(&encrypted, nonce.len()).unwrap();
    println!("복호문: {:?}", String::from_utf8_lossy(&decrypted));
    assert_eq!(plaintext.to_vec(), decrypted);

    // === 다른 키로 복호화 시도 ===
    println!("\n=== 잘못된 키 ===");
    // 잘못된 키는 깨진 데이터를 만든다 (실제 GCM은 인증 실패로 거부)
    let wrong_cipher = SimpleCipher::new(b"wrong-key-wrong-key-wrong-key!!");
    let wrong_result = wrong_cipher.decrypt(&encrypted, nonce.len()).unwrap();
    println!("잘못된 키로: {:?} (깨진 데이터)", String::from_utf8_lossy(&wrong_result));

    // === Nonce 중요성 ===
    println!("\n=== Nonce 중요성 ===");
    // 두 개의 다른 nonce 생성 (시간 차이)
    let nonce1 = generate_nonce();
    std::thread::sleep(std::time::Duration::from_millis(1));
    let nonce2 = generate_nonce();
    let enc1 = cipher.encrypt(plaintext, &nonce1);
    let enc2 = cipher.encrypt(plaintext, &nonce2);
    println!("같은 평문, 다른 nonce -> 다른 암호문");
    println!("  enc1: {:02X?}...", &enc1[..8.min(enc1.len())]);
    println!("  enc2: {:02X?}...", &enc2[..8.min(enc2.len())]);
    println!("  동일: {}", enc1 == enc2);

    // === 메시지 직렬화 ===
    println!("\n=== 메시지 직렬화 ===");
    // 암호문에서 nonce 부분을 분리하여 구조체로 만듦
    let msg = EncryptedMessage {
        nonce: nonce.to_vec(),
        ciphertext: encrypted[nonce.len()..].to_vec(),
    };
    let bytes = msg.to_bytes();
    let restored = EncryptedMessage::from_bytes(&bytes).unwrap();
    println!("직렬화/역직렬화: nonce_len={}, ct_len={}",
        restored.nonce.len(), restored.ciphertext.len());

    // === 실제 aes-gcm 코드 ===
    println!("\n=== 실제 aes-gcm 코드 ===");
    println!("// Cargo.toml: aes-gcm = \"0.10\"");
    println!("// use aes_gcm::{{Aes256Gcm, Key, Nonce, aead::{{Aead, KeyInit}}}};");
    println!("// use aes_gcm::aead::OsRng;");
    println!("// ");
    println!("// 키 생성:");
    println!("// let key = Aes256Gcm::generate_key(&mut OsRng);");
    println!("// let cipher = Aes256Gcm::new(&key);");
    println!("// ");
    println!("// 암호화:");
    println!("// let nonce = Aes256Gcm::generate_nonce(&mut OsRng);");
    println!("// let ciphertext = cipher.encrypt(&nonce, plaintext.as_ref())?;");
    println!("// ");
    println!("// 복호화:");
    println!("// let plaintext = cipher.decrypt(&nonce, ciphertext.as_ref())?;");

    println!("\n=== 암호화 핵심 규칙 ===");
    println!("1. Nonce는 절대 재사용하지 않는다 (같은 키에서)");
    println!("2. 인증된 암호화(AES-GCM) 사용 -> 변조 감지");
    println!("3. 키를 코드에 하드코딩하지 않는다");
    println!("4. 자체 암호화 구현 금지 -> 검증된 라이브러리 사용");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- `encrypt` 와 `decrypt` 의 핵심은 같은 `derive_keystream` 호출과 같은 XOR 이다 — 키와 nonce 가 같으면 키스트림이 같다.
- nonce 는 결과 앞에 붙여 두고, 복호화 때 `nonce_len` 만큼 잘라 다시 쓴다.
- `decrypt` 의 길이 검사는 슬라이스 패닉을 막을 뿐, 틀린 키를 잡아 주지는 않는다 — 그 일은 GCM 같은 AEAD 의 몫이다.
- `generate_nonce` 는 흐름을 보이기 위한 흉내다 — 실제로는 `OsRng` 로 만든다.
- 직렬화는 길이 헤더 한 바이트로 nonce 와 암호문의 경계를 적고, 역직렬화에서 그 헤더를 믿기 전에 데이터 길이를 확인한다.
- 이 코드 전체가 「암호를 직접 만들지 말라」는 규칙의 반면교사다 — 실제로는 `aes-gcm` 을 쓴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
