# rust/rust-testing-security/11 — 대칭 암호화 — 정리 (힌트)

> 출처 — study-site 항목 `rust/encryption`(항목 데이터 `data/rust/testing-security.json`) · 정답 코드 study-practice `rust/rust-testing-security/reference/encryption.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**대칭 암호화는 「같은 열쇠로 잠그고 같은 열쇠로 여는 자물쇠 상자」다.**
보내는 쪽과 받는 쪽이 똑같은 열쇠(키)를 나눠 갖는다.
상자를 잠글 때마다 상자에 일회용 일련번호 스티커(nonce)를 붙인다.
같은 열쇠라도 스티커 번호가 다르면 잠긴 모양이 달라진다.
스티커는 비밀이 아니라서 상자 겉에 그대로 붙어 간다.
대칭 암호화도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 열쇠 | 비밀 키 (`key: Vec<u8>`) |
| 일회용 일련번호 스티커 | nonce (12바이트) |
| 상자에 넣는 편지 | 평문 (`plaintext`) |
| 잠긴 상자 | 암호문 (`ciphertext`) |
| 상자 겉에 붙은 스티커 | 암호문 앞에 붙인 nonce |
| 상자가 뜯겼는지 알려 주는 봉인 | GCM 의 인증 태그 (변조 감지) |

```text
  키 ──┐                          ┌── 키 (같은 것)
       ▼                          ▼
평문 ─▶ [암호화] ─▶ nonce|암호문 ─▶ [복호화] ─▶ 평문
       ▲               │
 nonce ┘               └─ nonce 는 비밀이 아니라 함께 보낸다
```

## 이 주제가 답하려는 질문

1. 키 하나로 어떻게 잠그고 다시 열 수 있나?
2. nonce 는 왜 필요하고, 왜 같은 키에서 두 번 쓰면 안 되나?
3. 암호문을 저장 · 전송할 때 nonce 와 암호문을 어떻게 한 덩어리로 묶나?
4. 이 예제의 장난감 암호와 실제로 써야 할 AES-256-GCM 은 무엇이 다른가?

## 동작 방식

이 항목의 예제는 실제 AES 를 쓰지 않는다.
XOR 과 간단한 의사난수 생성기로 대칭 암호화의 **흐름(패턴)**만 흉내 낸다.
원본도 「XOR 암호화는 안전하지 않다. 패턴만 참고하라」고 못 박는다.

> **대칭 암호화** — 암호화와 복호화에 같은 키를 쓰는 방식.\
> 예: AES-256-GCM 은 32바이트 키 하나로 잠그고 연다.

### (1) 키스트림 만들기 — `derive_keystream`

**언제 쓰나** — 암호화와 복호화 둘 다, 평문과 XOR 할 바이트 줄(키스트림)이 필요할 때 부른다.

```text
입력: nonce(12바이트), key, len
  state = 0
  nonce 의 각 바이트 b:  state = state*31 + b   (넘치면 감아 돈다)
  key   의 각 바이트 b:  state = state*37 + b
  len 번 반복:
     state = state*6364136223846793005 + 1
     stream 에 (state >> 33) as u8 를 넣는다
결과: len 바이트짜리 키스트림
```

- 상태 `state` 는 0 에서 출발한다.
- nonce 바이트를 차례로 섞고, 이어서 키 바이트를 섞어 시작 상태를 만든다.
- 그다음 선형 합동 생성기(LCG) 식을 `len` 번 돌리며 바이트를 하나씩 뽑는다.
- 원본 주석은 「상위 비트가 더 무작위적이라 33비트 시프트」한다고 적는다.
- 같은 키 + 같은 nonce 면 언제나 같은 키스트림이 나온다(결정적이다).
- 키나 nonce 가 하나라도 다르면 시작 상태가 달라져 키스트림 전체가 달라진다.

> **키스트림** — 평문과 한 바이트씩 XOR 할, 키와 nonce 에서 만들어 낸 바이트 줄.\
> 예: 평문이 23바이트면 키스트림도 23바이트를 만든다.

> **LCG(선형 합동 생성기)** — `상태 = 상태 × a + c` 를 되풀이해 수를 뽑는 단순한 의사난수 생성기.\
> 예: `state.wrapping_mul(6364136223846793005).wrapping_add(1)`.

`wrapping_mul` · `wrapping_add` 는 `u64` 범위를 넘으면 패닉하지 않고 감아 돈다.

### (2) 암호화 — XOR 하고 nonce 를 앞에 붙인다

**언제 쓰나** — 평문을 보내거나 저장하기 전에 `encrypt(plaintext, nonce)` 를 부른다.

```text
plaintext  : 48 65 6C 6C 6F ...   (23바이트)
keystream  : k0 k1 k2 k3 k4 ...   (23바이트)
            XOR 한 바이트씩
ciphertext : c0 c1 c2 c3 c4 ...   (23바이트)

결과 Vec<u8> = [ nonce 12바이트 | ciphertext 23바이트 ]  → 35바이트
```

- `derive_keystream(nonce, plaintext.len())` 로 평문 길이만큼 키스트림을 만든다.
- `zip` 으로 평문과 키스트림을 짝지어 `p ^ k` 로 한 바이트씩 XOR 한다.
- `nonce.to_vec()` 로 시작한 벡터 뒤에 암호문을 `extend_from_slice` 로 붙인다.
- 그래서 결과의 앞 `nonce.len()` 바이트는 nonce 그대로이고, 길이는 `nonce 길이 + 평문 길이` 다.

nonce 를 앞에 붙이는 까닭은 복호화할 때 같은 nonce 가 있어야 같은 키스트림을 다시 만들 수 있기 때문이다.
nonce 는 비밀이 아니므로 드러나도 된다 — 비밀은 키뿐이다.

> **nonce** — 「한 번만 쓰는 수(number used once)」. 같은 키로 암호화할 때마다 새로 쓰는 값.\
> 예: 12바이트 랜덤 값.

### (3) 복호화 — 잘라내고 같은 키스트림으로 다시 XOR

**언제 쓰나** — 받은 `nonce|암호문` 덩어리를 평문으로 되돌릴 때 `decrypt(data, nonce_len)` 을 부른다.

```text
data = [ nonce | ciphertext ]
  data.len() < nonce_len ?  → Err("데이터가 너무 짧습니다")
  nonce      = data[..nonce_len]
  ciphertext = data[nonce_len..]
  keystream  = derive_keystream(nonce, ciphertext.len())   ← 암호화 때와 같은 것
  plaintext  = ciphertext XOR keystream
결과: Ok(plaintext)
```

- 길이를 먼저 검사해 슬라이스 범위가 넘쳐 패닉하는 일을 막는다.
- 앞부분은 nonce, 뒷부분은 암호문으로 나눈다.
- 같은 키 + 같은 nonce 로 같은 키스트림을 다시 만든다.
- XOR 은 같은 값을 두 번 하면 원래대로 돌아온다: `(p ^ k) ^ k = p`.
- 그래서 암호화와 복호화가 사실상 같은 연산이다.

**중요**: 이 `decrypt` 는 길이가 충분하면 **언제나 `Ok`** 를 돌려준다.
키가 틀려도 키스트림이 달라질 뿐이라 오류 없이 깨진 바이트가 나온다.
원본 주석은 「실제 GCM 은 인증 실패로 거부」한다고 적는다 — 이 차이가 인증된 암호화(AEAD)의 존재 이유다.

> **AEAD(인증된 암호화)** — 암호화와 함께 「암호문이 바뀌지 않았나」까지 검사하는 방식.\
> 예: AES-GCM 은 키가 틀리거나 암호문이 변조되면 복호화를 거부한다.

### (4) nonce 만들기와 재사용 금지

**언제 쓰나** — `encrypt` 를 부를 때마다 직전에 새 nonce 를 만든다.

```text
now = UNIX_EPOCH 부터 흐른 나노초 (u128)
nonce[0] = now        & 0xFF
nonce[1] = (now >> 8) & 0xFF
...
nonce[11]= (now >> 88)& 0xFF
결과: [u8; 12]
```

- 현재 시각을 나노초로 읽는다.
- 시계가 `UNIX_EPOCH` 보다 앞서 있어 `duration_since` 가 실패하면 `unwrap_or_default()` 로 0 이 된다.
- 시각의 비트를 바이트 단위로 잘라 12칸에 낮은 자리부터 펼쳐 넣는다.
- 원본 주석은 이것이 **시뮬레이션**이며 실제로는 `OsRng` 같은 CSPRNG 을 써야 한다고 적는다.

같은 키에서 nonce 를 두 번 쓰면 왜 안 되나?
같은 키 + 같은 nonce → 같은 키스트림 `k` 다.
그러면 두 암호문을 XOR 하는 순간 키스트림이 지워진다: `(p1 ^ k) ^ (p2 ^ k) = p1 ^ p2`.
키를 몰라도 두 평문의 관계가 드러난다.

```text
c1 = p1 ^ k
c2 = p2 ^ k      (같은 nonce → 같은 k)
c1 ^ c2 = p1 ^ p2   ← k 가 사라졌다
```

예제의 「Nonce 중요성」 부분은 nonce 두 개를 1ms 쉬었다가 만들어, 같은 평문이 다른 암호문이 되는 것을 보이려 한다.

> **CSPRNG** — 암호용으로 예측할 수 없게 설계된 난수 생성기.\
> 예: `aes_gcm::aead::OsRng`.

### (5) 직렬화 — 길이 헤더를 붙인 바이트열

**언제 쓰나** — nonce 와 암호문을 파일 · 네트워크로 보낼 한 덩어리 바이트로 만들 때.

```text
EncryptedMessage { nonce: 12바이트, ciphertext: 23바이트 }
   to_bytes()
[ 0x0C | nonce 12바이트 | ciphertext 23바이트 ]   (0x0C = 12)
   from_bytes()
  비었나? → Err("빈 데이터")
  nonce_len = data[0]
  data.len() < 1 + nonce_len ? → Err("데이터 부족")
  nonce = data[1..1+nonce_len], ciphertext = data[1+nonce_len..]
```

- 첫 바이트에 nonce 길이를 적어 두면 받는 쪽이 nonce 길이를 미리 몰라도 된다.
- `from_bytes` 는 빈 입력과 「헤더가 가리킨 만큼 데이터가 없는」 입력을 `Err` 로 거른다.
- 예제는 `encrypted[nonce.len()..]` 로 암호문만 떼어 구조체에 넣고, 왕복 뒤 `nonce_len=12, ct_len=23` 이 되는지 찍는다.

> **직렬화** — 구조체를 저장 · 전송할 수 있는 바이트열로 바꾸는 것. 되돌리는 것은 역직렬화.\
> 예: `to_bytes` / `from_bytes`.

### (6) 실제로는 — `aes-gcm` 크레이트

**언제 쓰나** — 진짜 데이터를 암호화할 때는 언제나 이쪽이다.

```text
Cargo.toml: aes-gcm = "0.10"
키 생성 : let key = Aes256Gcm::generate_key(&mut OsRng);
          let cipher = Aes256Gcm::new(&key);
암호화  : let nonce = Aes256Gcm::generate_nonce(&mut OsRng);
          let ciphertext = cipher.encrypt(&nonce, plaintext.as_ref())?;
복호화  : let plaintext = cipher.decrypt(&nonce, ciphertext.as_ref())?;
```

- 키와 nonce 를 모두 `OsRng`(CSPRNG)로 만든다 — 예제의 시각 기반 `generate_nonce` 자리다.
- `encrypt` · `decrypt` 가 `Result` 를 돌려줘 `?` 로 실패를 전한다.
- 복호화가 실패할 수 있다는 점이 장난감 `decrypt`(언제나 `Ok`)와 다르다 — GCM 이 변조를 감지하기 때문이다.
- 예제는 이 코드를 실행하지 않고 `println!` 으로 글자만 찍는다.

## 문법 — 형태와 규칙

XOR 왕복의 최소 예제:

```rust
fn xor(data: &[u8], ks: &[u8]) -> Vec<u8> {
    data.iter().zip(ks.iter()).map(|(d, k)| d ^ k).collect()
}

fn main() {
    let msg = b"hi";              // &[u8; 2]
    let ks = [0x5A, 0xA5];
    let ct = xor(msg, &ks);
    let back = xor(&ct, &ks);
    assert_eq!(msg.to_vec(), back); // XOR 두 번이면 원래대로
}
```

- `b"..."` 는 바이트 문자열 리터럴이다 — 타입은 `&[u8; N]` 이고 `&[u8]` 로 넘길 수 있다.
- `iter().zip(...)` 은 짧은 쪽 길이에서 멈춘다 — 그래서 키스트림을 평문 길이만큼 만든다.
- `a ^ b` 는 비트 단위 XOR 이다.
- `wrapping_mul` · `wrapping_add` 는 넘침을 감아 돌린다(패닉하지 않는다).
- `x as u8` 는 정수의 낮은 8비트만 남긴다(나머지를 잘라 낸다).
- `Vec::with_capacity(len)` 은 미리 공간만 잡고 길이는 0 이다.
- `assert!(조건, "메시지")` 는 조건이 거짓이면 패닉한다 — `SimpleCipher::new` 가 빈 키를 이렇게 거부한다.
- `Result<Vec<u8>, String>` 은 성공 시 바이트, 실패 시 오류 문자열을 돌려주는 꼴이다.
- `String::from_utf8_lossy` 는 UTF-8 이 아닌 바이트를 대체 문자(`�`)로 바꿔 보여 준다 — 깨진 복호문을 찍을 때 쓴다.
- `{:02X?}` 는 디버그 출력에 두 자리 대문자 16진수를 적용한다 — 바이트 슬라이스를 hex 로 볼 때 쓴다.
- `println!` 안의 `{{` · `}}` 는 중괄호 글자 하나를 찍는다 — `use aes_gcm::{{...}}` 줄이 그렇다.
- `20.min(encrypted.len())` 은 길이가 20보다 짧을 때 슬라이스가 넘치지 않게 막는다.

## 어디서 틀리나

### 1. XOR 장난감 암호를 실제로 쓴다

원본은 XOR 암호화가 안전하지 않으며 패턴만 참고하라고 적는다.
키스트림을 LCG 로 만드는 방식은 암호용이 아니다.
대칭 암호화의 표준은 **AES-256-GCM** 이다.

### 2. 암호를 직접 구현한다

원본 팁: 자체 암호화 구현은 절대 하지 말고 검증된 크레이트를 쓴다.
예제의 `SimpleCipher` 자체가 「직접 만들면 이렇게 된다」의 표본이다.

### 3. 같은 키에서 nonce 를 다시 쓴다

원본 팁: nonce 는 같은 키에서 **절대** 재사용하면 안 된다(보통 12바이트 랜덤).
재사용하면 같은 키스트림이 나와 `c1 ^ c2 = p1 ^ p2` 로 평문 관계가 샌다(동작 방식 (4)).

### 4. 시각으로 nonce 를 만든다

`generate_nonce` 는 시뮬레이션이다(원본 주석: 「실제로는 부적합」).
- 시각은 남이 짐작할 수 있다.
- 두 번 부른 사이에 시계 값이 같으면 nonce 가 겹친다 — 예제가 `sleep(1ms)` 을 끼운 까닭이다.
- 시계가 `UNIX_EPOCH` 이전이면 `unwrap_or_default()` 로 언제나 0 → 모든 nonce 가 0바이트 12개로 같아진다.
실제로는 `OsRng` 같은 CSPRNG 을 쓴다.

### 5. 복호화가 `Ok` 면 맞는 평문이라고 믿는다

장난감 `decrypt` 는 키가 틀려도 `Ok(깨진 바이트)` 를 돌려준다.
변조 · 틀린 키를 감지하려면 인증된 암호화(AEAD)가 필요하다 — GCM 이 그 일을 한다(원본 팁).

### 6. 키를 코드에 박아 둔다

원본의 핵심 규칙 3: 키를 코드에 하드코딩하지 않는다.
예제의 `b"my-secret-key-..."` 는 시연용일 뿐이다.

### 7. 원본 주석의 「32바이트 키」

원본의 주장: `let key = b"my-secret-key-32bytes-padding!!";` 위에 「32바이트 키」라고 적혀 있다.
왜 의심스러운가: 글자를 세면 `my-secret-key-`(14) + `32bytes-`(8) + `padding!!`(9) = 31바이트다.
이 장난감 암호는 키 길이를 따지지 않아 동작에는 영향이 없다.
AES-256 은 정확히 32바이트 키를 요구하므로 실제 코드라면 문제가 된다.

### 8. 「다른 암호문」이라며 찍은 앞 8바이트

예제는 `enc1[..8]` · `enc2[..8]` 을 찍어 암호문이 다르다고 보여 주려 한다.
그런데 `encrypt` 결과의 앞 12바이트는 nonce 그대로다.
그러니 찍힌 8바이트는 **nonce 의 일부**이지 XOR 된 암호문이 아니다.
암호문이 정말 다른지 보려면 12번째 바이트 이후를 봐야 한다.
(다만 `enc1 == enc2` 비교는 전체 벡터를 비교한다.)

### 9. nonce 길이를 `u8` 로 적는다

`to_bytes` 는 `self.nonce.len() as u8` 로 길이를 적는다.
`as u8` 는 낮은 8비트만 남기므로 255바이트를 넘는 nonce 면 헤더가 틀린 값이 된다.
12바이트 nonce 에서는 문제가 없다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `wrapping_mul` · `wrapping_add` 는 넘쳐도 감아 돈다 | Rust 표준 라이브러리(정수 메서드의 정의) |
| `x as u8` 는 낮은 8비트만 남긴다 | Rust 언어(정수 캐스트 규칙) |
| `zip` 은 짧은 쪽에서 멈춘다 | Rust 표준 라이브러리(`Iterator::zip`) |
| `from_utf8_lossy` 는 잘못된 바이트를 대체 문자로 바꾼다 | Rust 표준 라이브러리 |
| `unwrap_or_default()` 는 실패 시 0 길이 `Duration` 을 준다 | Rust 표준 라이브러리(`Duration` 의 기본값) |
| 시각이 나노초 단위로 바뀐다 | 운영체제 · 하드웨어 시계 — 실제 해상도는 플랫폼마다 다르다 (확인 필요) |
| `sleep(1ms)` 뒤에 시각 값이 달라진다 | 운영체제 스케줄러 — 언어가 보장하는 것은 「최소 그만큼 잔다」 쪽이다 (확인 필요) |
| GCM 은 변조를 감지한다 | GCM 알고리즘 명세와 `aes-gcm` 크레이트의 구현 |
| AES-256-GCM 이 대칭 암호화의 표준이다 | 업계 관행(원본의 팁) — Rust 와 무관 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 실제 데이터를 암호화 | `aes-gcm` 의 `Aes256Gcm` | `SimpleCipher` 같은 직접 만든 암호 |
| nonce 만들기 | `Aes256Gcm::generate_nonce(&mut OsRng)` | 시각 기반 `generate_nonce`, 고정값 |
| 키 만들기 | `Aes256Gcm::generate_key(&mut OsRng)` | 코드에 박은 문자열 |
| 변조 감지가 필요 | AEAD(GCM) — 복호화 실패를 `Result` 로 받는다 | 인증 없는 XOR · 스트림 암호만 |
| 암호문 저장 · 전송 | nonce 를 앞에 붙이거나 길이 헤더로 묶는다 | nonce 를 버리기(복호화 불가) |
| 대칭 암호화의 흐름을 배울 때 | 이 예제의 XOR 패턴 | — |

## 핵심 문장

1. **대칭 암호화는 같은 키로 잠그고 연다** — 비밀은 키뿐이고 nonce 는 암호문과 함께 보낸다.
2. **같은 키 + 같은 nonce 는 같은 키스트림을 만든다** — 그래서 nonce 를 같은 키에서 두 번 쓰면 평문 관계가 샌다.
3. **XOR 은 두 번 하면 원래대로 돌아온다** — 암호화와 복호화가 같은 키스트림으로 같은 연산을 한다.
4. **인증 없는 복호화는 틀린 키에도 「성공」한다** — GCM(AEAD)은 변조 · 틀린 키를 거부한다.
5. **암호는 직접 만들지 않는다** — `aes-gcm` 같은 검증된 크레이트와 `OsRng` 를 쓴다.

## 관련 자료

- `hashing` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [password-hashing](../10-password-hashing/2-summary.md)
- `jwt-rust` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/testing-security.json` 의 `encryption`

## 용어 풀이

- **대칭 암호화** — 암호화와 복호화에 같은 키를 쓰는 방식.
- **평문(plaintext)** — 암호화하기 전의 원래 데이터.
- **암호문(ciphertext)** — 암호화한 뒤의 데이터.
- **키(key)** — 암호화 · 복호화에 쓰는 비밀 바이트열.
- **nonce** — 같은 키에서 한 번만 쓰는 값. 비밀은 아니다.
- **키스트림** — 평문과 XOR 할, 키와 nonce 에서 만든 바이트 줄.
- **XOR** — 두 비트가 다르면 1, 같으면 0 이 되는 연산. 두 번 하면 원래대로 돌아온다.
- **LCG** — `상태 × a + c` 를 되풀이하는 단순 의사난수 생성기.
- **CSPRNG** — 암호용으로 예측할 수 없게 만든 난수 생성기.
- **AES** — 표준 대칭 블록 암호. AES-256 은 32바이트 키를 쓴다.
- **GCM** — AES 를 인증된 암호화로 쓰게 하는 운용 방식.
- **AEAD** — 암호화와 변조 감지를 함께 하는 인증된 암호화.
- **직렬화 / 역직렬화** — 구조체 ↔ 바이트열 변환.
- **라운드트립** — 암호화한 것을 복호화해 원래 값이 나오는지 왕복으로 확인하는 것.
- **크레이트** — Rust 의 패키지 단위.

## 더 들어가면

- GCM 은 암호문 뒤에 인증 태그(흔히 16바이트)를 덧붙여, 복호화 때 이 태그로 변조를 검사한다 (확인 필요).
- GCM 에서 nonce 가 겹치면 기밀성뿐 아니라 인증까지 무너질 수 있다고 알려져 있다 (확인 필요).
- 랜덤 nonce 대신 「메시지마다 1씩 늘리는 카운터」를 nonce 로 쓰는 방식도 있다 — 카운터 상태를 잃지 않는다는 전제가 필요하다 (확인 필요).
- `aes-gcm` 과 같은 계열(RustCrypto)에 `chacha20poly1305` 도 있으며, AES 하드웨어 가속이 없는 환경에서 대안으로 쓰인다 (확인 필요).
- 메모리에 남은 키를 지우는 데 `zeroize` 크레이트를 쓰기도 한다 (확인 필요).
- 키는 환경 변수 · 비밀 관리 서비스 등 코드 바깥에서 주입하는 것이 일반적이다 (확인 필요).
