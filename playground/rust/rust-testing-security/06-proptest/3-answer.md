# rust/rust-testing-security/06 — Property-Based Testing — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 일곱 줄 모두 `OK (100 iterations)` — 일곱 프로퍼티는 생성되는 모든 입력에서 성립한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

예상하는 줄은 다음과 같다.

```text
=== Property-Based Testing ===
  reverse 항등성 ... OK (100 iterations)
  reverse 길이 보존 ... OK (100 iterations)
  sort 정렬 보장 ... OK (100 iterations)
  sort 길이 보존 ... OK (100 iterations)
  sort 원소 보존 ... OK (100 iterations)
  RLE encode/decode 라운드트립 ... OK (100 iterations)
  덧셈 교환법칙 ... OK (100 iterations)
```

**왜 그런가**

- `run` 은 이름을 `print!` 로 찍고 줄을 바꾸지 않으므로 `OK …` 가 같은 줄 뒤에 붙는다.
- 문자 단위로 두 번 뒤집으면 원래 문자열이고, 뒤집어도 바이트 길이는 같다.
- 표준 정렬은 길이와 원소 구성을 바꾸지 않고 결과의 이웃 쌍이 모두 `<=` 다.
- RLE 는 `[개수, 바이트]` 로 정확히 되살리고, 길이 29 이하라 255 에서 끊는 경로에도 닿지 않는다.
- `-1000..=1000` 의 두 정수 합은 `i32` 를 넘지 않으니 교환법칙이 그대로 성립한다.
- 깨질 입력이 없으므로 시드가 무엇이든 `Err` 는 나오지 않는다.
- 근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」 · 「동작 방식 (5)」.

### 2. 정렬 보장은 그대로 OK, 길이 보존 · 원소 보존은 `FAILED` 가 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 프로퍼티 3: `dedup` 뒤에도 결과는 오름차순이라 이웃 쌍은 모두 `<=` 다 → `OK (100 iterations)`.
- 프로퍼티 4: 길이 0~29, 값 -50~50 벡터에 중복이 하나라도 있으면 길이가 줄어 `FAILED (iteration i)` 와 `길이 변경: …` 이 찍힌다.
- 프로퍼티 5: 값이 -10~10 스물한 가지뿐이라 중복이 쉽게 생기고, 다시 정렬해도 개수가 달라 `FAILED (iteration i)` 와 `원소 변경됨: …` 이 찍힌다.
- 반복 번호 `i` 는 난수 수열에 달려 있어 코드를 읽는 것만으로는 정할 수 없다.
- 100 번 안에 중복이 있는 입력이 나오는 것은 거의 확실하다(원본에 근거 없음 — 추론).

**왜 그런가**

- `dedup` 은 이웃한 같은 값을 하나만 남기고, 정렬 뒤라면 모든 중복이 사라진다.
- 정렬 상태라는 성질은 남고 길이와 다중집합이 깨진다 — 프로퍼티 하나만으로는 버그를 못 잡고, 여러 불변량을 함께 세워야 잡힌다.
- 프로퍼티 4 가 일찍 끝나면 난수를 덜 꺼내 쓰므로 프로퍼티 5 가 받는 입력도 원래와 달라진다.
- 근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 4」 · 「어디서 틀리나 7」.

### 3. `//     fn test_reverse(s in "[a-z]{0,100}") {` 로 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
//     fn test_reverse(s in "[a-z]{0,100}") {
```

**왜 그런가**

- `println!` 의 형식 문자열에서 `{{` 는 `{`, `}}` 는 `}` 한 글자로 찍힌다.
- `\"` 는 문자열 안의 큰따옴표 하나다.
- 이 줄은 진짜 `proptest` 코드를 실행하지 않고 글자로만 보여 주는 것이다.
- 근거: 2-summary 「동작 방식 (6)」 · 「문법 — 형태와 규칙」.

### 4. 같은 입력을 재현하려고 고정한다 — 대신 프로퍼티끼리 입력이 얽힌다

- 시드가 고정이면 LCG 가 매번 같은 수열을 내므로, 프로그램을 다시 돌려도 모든 프로퍼티가 같은 입력을 받는다.
- 실패가 났을 때 같은 반례를 다시 만들어 디버깅할 수 있다.
- 대가: 일곱 프로퍼티가 실행기 하나의 수열을 이어 쓰므로, 앞에 프로퍼티를 끼우거나 앞 프로퍼티가 일찍 실패하면 뒤 프로퍼티의 입력이 모두 바뀐다.
- 근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 7」.

### 5. 같은 값이 연달아 나오게 해 RLE 의 압축 경로를 자주 밟게 하려고

- RLE 는 같은 값이 이어져야 개수를 늘리는 경로를 탄다.
- 값이 네 가지뿐이면 이웃한 값이 같을 일이 많아 반복 구간이 자주 생긴다.
- 0~255 를 고르게 뽑으면 이웃이 같을 일이 드물어 거의 모든 그룹이 개수 1 이 되고, 핵심 경로가 제대로 검사되지 않는다.
- 근거: 2-summary 「동작 방식 (4)」.

### 6. 검사 대상과 기준이 같은 코드라 같은 버그를 함께 가질 수 있어서

- 검사 대상 `sort` 의 속은 표준 `v.sort()` 이고, 기준도 표준 `sort()` 로 다시 정렬해 만든다.
- 그 정렬에 버그가 있으면 양쪽이 같은 식으로 틀려 서로 맞아 버릴 수 있다.
- 다만 원소를 빼거나 더하는 버그(`dedup` 등)는 다시 정렬해도 개수가 달라 잡힌다.
- 근거: 2-summary 「어디서 틀리나 4」.

### 7. 검사되지 않는다 — 생성기가 길이 29 까지만 만든다

- `count < 255` 에서 끊는 경로는 같은 값이 255 번 넘게 이어져야 실행된다.
- 데이터 길이가 `next_u64() % 30` 이라 최대 29 이므로 그런 입력은 나오지 않는다.
- 100 번 통과는 「생성기가 만든 범위 안에서 깨지지 않았다」는 뜻일 뿐, 경계 코드의 정확성을 보여 주지 않는다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 3」.

### 8. 둘 다 패닉이 나고, `run` 은 `FAILED` 로 보고하지 못한다

- `next_string(0)` 은 길이를 `next_u64() % 0` 으로 구하므로 0 으로 나눈 나머지가 되어 패닉한다.
- `next_i32(i32::MIN, i32::MAX)` 는 `max - min` 계산부터 `i32` 를 넘고, 넓힌 범위의 `a + b` 도 넘칠 수 있다 — 디버그 빌드에서 정수 넘침은 패닉이다.
- `run` 은 클로저가 돌려준 `Result` 만 보므로 패닉을 잡지 못하고, 프로그램 전체가 멈춰 남은 프로퍼티도 돌지 않는다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」 · 「어디서 틀리나 6」 · 「구현 세부사항 대 언어 보장」.

### 9. 문자열은 `"[a-z]{0,100}"`, 벡터는 `prop::collection::vec(…)` 에 해당한다 — 반례는 줄였느냐가 다르다

- `next_string` 은 영문 소문자 문자열을 만드는 정규식 모양 전략 `"[a-z]{0,100}"` 에 해당한다.
- 길이를 정하고 `next_i32` 로 채운 벡터는 `prop::collection::vec(-100..100i32, 0..50)` 에 해당한다.
- 흉내 실행기는 첫 반례를 그대로 보여 주고 멈춘다.
- `proptest` 는 shrinking 으로 반례를 더 단순하게 줄여 보고한다(원본 예: `vec![99, -50, 77, 3]` → `vec![1, 0]`).
- 근거: 2-summary 「동작 방식 (6)」 · 「문법 — 형태와 규칙」 표 · 「어디서 틀리나 2」.

### 10. 덧셈 교환법칙이 세 꼴 어디에도 들지 않는다 — 수학 법칙이다

- 항등성: 프로퍼티 1(`reverse(reverse(s)) == s`).
- 불변량: 프로퍼티 2 · 3 · 4 · 5(길이 보존 · 정렬 상태 · 원소 구성).
- 라운드트립: 프로퍼티 6(RLE encode/decode).
- 프로퍼티 7(덧셈 교환법칙)은 늘 성립해야 하는 수학 식을 프로퍼티로 세운 것이다.
- 근거: 2-summary 「동작 방식 (4)」 표.

## 실습 정답

### 실습 1. 순수 Rust 로 프로퍼티 테스트 실행기를 만들고 일곱 프로퍼티 검사하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 반복 횟수 · 시드, 시드 12345 고정 | `struct TestRunner { iterations, seed }` · `TestRunner::new` |
| 2. LCG 한 걸음 | `next_u64` 의 `wrapping_mul(…).wrapping_add(…)` |
| 3. `[min, max]` 정수 | `next_i32` 의 `range = (max - min) as u64 + 1` · `% range + min` |
| 4. 길이 0 ~ `max_len - 1` 소문자 문자열 | `next_string` 의 `% max_len` · `% 26 + b'a'` |
| 5. 이름 찍고 반복 호출 | `run` 의 `print!("  {} ... ", name)` · `for i in 0..self.iterations` |
| 6. 실패 시 반복 번호 · 메시지 찍고 끝 | `run` 의 `Err(msg) =>` 갈래 · `return` |
| 7. 모두 통과 시 OK | `run` 끝의 `println!("OK ({} iterations)", …)` |
| 8. 문자 단위 뒤집기 | `reverse` 의 `s.chars().rev().collect()` |
| 9. 정렬해 돌려주기 | `sort` 의 `v.sort(); v` |
| 10. `[개수, 바이트]` 인코딩 · 255 에서 새 그룹 · 두 바이트씩 디코딩 | `rle_encode` 의 `count < 255` · `rle_decode` 의 `chunks(2)` |
| 11. 빈 입력 · 짧은 조각 처리 | `if data.is_empty() { return vec![]; }` · `if chunk.len() == 2` |
| 12. 100 회 실행기 하나로 차례로 | `let mut runner = TestRunner::new(100);` · `runner.run(…)` 일곱 번 |
| 13. 두 번 뒤집기 | `"reverse 항등성"` 클로저 · `next_string(20)` |
| 14. 뒤집어도 길이 같음 | `"reverse 길이 보존"` 클로저 · `next_string(50)` |
| 15. 이웃 쌍 `<=` | `"sort 정렬 보장"` 클로저 · `sorted.windows(2)` |
| 16. 정렬 후 길이 같음 | `"sort 길이 보존"` 클로저 · `% 30` · `next_i32(-50, 50)` |
| 17. 다시 정렬해 비교 | `"sort 원소 보존"` 클로저 · `sorted.sort(); original.sort();` |
| 18. RLE 라운드트립 | `"RLE encode/decode 라운드트립"` 클로저 · `(rng.next_u64() % 4) as u8` |
| 19. 교환법칙 | `"덧셈 교환법칙"` 클로저 · `next_i32(-1000, 1000)` |
| 20. `proptest` 코드 · shrinking 설명 | `main` 끝의 `println!` 묶음 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-testing-security/reference/proptest.rs`

```rust
// [테스팅 & 보안] Property-Based Testing
// 설명: 프로퍼티 기반 테스트, 전략, shrinking, 무작위 입력 검증
// 팁: 프로퍼티 기반 테스트는 '모든 입력에 대해 성립해야 하는 속성'을 검증한다. 라운드트립(encode/decode), 항등성(f(f(x))==x), 불변량(정렬 후 길이 보존) 등이 대표적 프로퍼티다. proptest의 shrinking은 실패시 최소 반례를 자동으로 찾아준다.

// === Property-Based Testing 패턴 ===
// 실제: proptest = "1.0" 크레이트 사용
// 여기서는 개념과 패턴을 순수 Rust로 시뮬레이션합니다.

// fmt는 현재 사용되지 않지만 디스플레이 확장 가능성을 위해 유지
use std::fmt;

// === 간단한 프로퍼티 테스트 프레임워크 ===

// 의사 난수 생성과 프로퍼티 반복 실행을 담당
struct TestRunner {
    // 각 프로퍼티당 실행 반복 횟수
    iterations: usize,
    // LCG 시드 - 결정성 재현 가능
    seed: u64,
}

impl TestRunner {
    // 반복 횟수로 러너 생성 (시드는 고정값)
    fn new(iterations: usize) -> Self {
        TestRunner { iterations, seed: 12345 }
    }

    // 간단한 의사 난수 생성기 (LCG)
    fn next_u64(&mut self) -> u64 {
        // 잘 알려진 LCG 상수
        self.seed = self.seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        self.seed
    }

    // [min, max] 범위의 i32 생성
    fn next_i32(&mut self, min: i32, max: i32) -> i32 {
        let range = (max - min) as u64 + 1;
        (self.next_u64() % range) as i32 + min
    }

    // 0..max_len 길이의 영문 소문자 문자열 생성
    fn next_string(&mut self, max_len: usize) -> String {
        let len = (self.next_u64() % max_len as u64) as usize;
        (0..len).map(|_| {
            // a-z 사이의 ASCII 하나 생성
            let c = (self.next_u64() % 26) as u8 + b'a';
            c as char
        }).collect()
    }

    // 프로퍼티 테스트 실행
    // 클로저 prop을 iterations 번 실행하고 첫 실패에서 중단
    fn run<F>(&mut self, name: &str, mut prop: F)
    where F: FnMut(&mut TestRunner) -> Result<(), String>
    {
        print!("  {} ... ", name);
        for i in 0..self.iterations {
            match prop(self) {
                Ok(()) => {}
                Err(msg) => {
                    // 실패 시 어느 반복에서 무엇이 깨졌는지 출력
                    println!("FAILED (iteration {})", i);
                    println!("    {}", msg);
                    return;
                }
            }
        }
        println!("OK ({} iterations)", self.iterations);
    }
}

// === 테스트 대상 코드 ===

// 문자열을 문자 단위로 뒤집음
fn reverse(s: &str) -> String {
    s.chars().rev().collect()
}

// 벡터를 정렬해서 반환
fn sort(mut v: Vec<i32>) -> Vec<i32> {
    v.sort();
    v
}

// RLE 인코딩 후 디코딩 - 라운드트립 검증용
fn encode_decode(data: &[u8]) -> Vec<u8> {
    // RLE 인코더 - 같은 바이트의 반복을 [count, byte] 쌍으로 압축
    fn rle_encode(data: &[u8]) -> Vec<u8> {
        if data.is_empty() { return vec![]; }
        let mut result = Vec::new();
        // u8 카운터 - 255 초과 시 새 그룹
        let mut count: u8 = 1;
        let mut current = data[0];

        for &byte in &data[1..] {
            // 같은 바이트면 카운트 증가, 다르면 그룹 종료
            if byte == current && count < 255 {
                count += 1;
            } else {
                result.push(count);
                result.push(current);
                current = byte;
                count = 1;
            }
        }
        // 마지막 그룹 푸시
        result.push(count);
        result.push(current);
        result
    }

    // RLE 디코더 - 2바이트씩 [count, byte]로 해석
    fn rle_decode(encoded: &[u8]) -> Vec<u8> {
        let mut result = Vec::new();
        for chunk in encoded.chunks(2) {
            if chunk.len() == 2 {
                for _ in 0..chunk[0] {
                    result.push(chunk[1]);
                }
            }
        }
        result
    }

    let encoded = rle_encode(data);
    rle_decode(&encoded)
}

// 메인: 다양한 프로퍼티(항등성/길이보존/라운드트립 등) 검증
fn main() {
    println!("=== Property-Based Testing ===");
    // 100회 반복 러너
    let mut runner = TestRunner::new(100);

    // === 프로퍼티 1: reverse(reverse(s)) == s ===
    // involution(2회 적용=항등) 프로퍼티
    runner.run("reverse 항등성", |rng| {
        let s = rng.next_string(20);
        let result = reverse(&reverse(&s));
        if result != s {
            Err(format!("입력: '{}', reverse(reverse) = '{}'", s, result))
        } else {
            Ok(())
        }
    });

    // === 프로퍼티 2: reverse 길이 보존 ===
    runner.run("reverse 길이 보존", |rng| {
        let s = rng.next_string(50);
        let reversed = reverse(&s);
        if s.len() != reversed.len() {
            Err(format!("입력 길이: {}, 역순 길이: {}", s.len(), reversed.len()))
        } else {
            Ok(())
        }
    });

    // === 프로퍼티 3: sort 결과는 정렬됨 ===
    // 모든 인접 쌍에 대해 a <= b 검증
    runner.run("sort 정렬 보장", |rng| {
        let len = (rng.next_u64() % 20) as usize;
        let v: Vec<i32> = (0..len).map(|_| rng.next_i32(-100, 100)).collect();
        let sorted = sort(v.clone());

        // windows(2)로 인접 쌍 순회
        for w in sorted.windows(2) {
            if w[0] > w[1] {
                return Err(format!("정렬 안 됨: {:?} -> {:?}", v, sorted));
            }
        }
        Ok(())
    });

    // === 프로퍼티 4: sort 길이 보존 ===
    runner.run("sort 길이 보존", |rng| {
        let len = (rng.next_u64() % 30) as usize;
        let v: Vec<i32> = (0..len).map(|_| rng.next_i32(-50, 50)).collect();
        let sorted = sort(v.clone());
        if v.len() != sorted.len() {
            Err(format!("길이 변경: {} -> {}", v.len(), sorted.len()))
        } else {
            Ok(())
        }
    });

    // === 프로퍼티 5: sort 원소 보존 ===
    // multiset이 같아야 함 - 두 결과 모두 정렬해 비교
    runner.run("sort 원소 보존", |rng| {
        let len = (rng.next_u64() % 20) as usize;
        let v: Vec<i32> = (0..len).map(|_| rng.next_i32(-10, 10)).collect();
        let mut sorted = sort(v.clone());
        let mut original = v.clone();
        sorted.sort();
        original.sort();
        if sorted != original {
            Err(format!("원소 변경됨: {:?}", v))
        } else {
            Ok(())
        }
    });

    // === 프로퍼티 6: encode/decode 라운드트립 ===
    // encode 후 decode가 원본과 같아야 함
    runner.run("RLE encode/decode 라운드트립", |rng| {
        let len = (rng.next_u64() % 30) as usize;
        // 4가지 값만 사용해 반복 패턴이 잘 생기게
        let data: Vec<u8> = (0..len).map(|_| (rng.next_u64() % 4) as u8).collect();
        let result = encode_decode(&data);
        if data != result {
            Err(format!("라운드트립 실패: {:?} -> {:?}", data, result))
        } else {
            Ok(())
        }
    });

    // === 프로퍼티 7: 덧셈 교환법칙 ===
    // 수학적 법칙도 프로퍼티로 검증 가능
    runner.run("덧셈 교환법칙", |rng| {
        let a = rng.next_i32(-1000, 1000);
        let b = rng.next_i32(-1000, 1000);
        if a + b != b + a {
            Err(format!("{} + {} != {} + {}", a, b, b, a))
        } else {
            Ok(())
        }
    });

    // === 실제 proptest 사용법 ===
    println!("\n=== 실제 proptest 코드 ===");
    println!("// Cargo.toml: proptest = \"1.0\"");
    println!("// ");
    println!("// use proptest::prelude::*;");
    println!("// ");
    println!("// proptest! {{");
    println!("//     #[test]");
    println!("//     fn test_reverse(s in \"[a-z]{{0,100}}\") {{");
    println!("//         assert_eq!(reverse(&reverse(&s)), s);");
    println!("//     }}");
    println!("//     ");
    println!("//     #[test]");
    println!("//     fn test_sort(v in prop::collection::vec(-100..100i32, 0..50)) {{");
    println!("//         let sorted = sort(v);");
    println!("//         for w in sorted.windows(2) {{");
    println!("//             assert!(w[0] <= w[1]);");
    println!("//         }}");
    println!("//     }}");
    println!("// }}");

    println!("\n=== Shrinking 개념 ===");
    println!("프로퍼티 테스트가 실패하면, 최소 실패 케이스를 자동으로 찾음");
    println!("예: vec![99, -50, 77, 3] 에서 실패 -> vec![1, 0] 으로 축소");
    println!("이를 통해 디버깅이 훨씬 쉬워짐");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**

- 프로퍼티는 「`&mut TestRunner` 를 받아 `Result<(), String>` 을 돌려주는 클로저」라는 한 가지 꼴로 통일되어 있어, `run` 하나로 일곱 개를 모두 돌린다.
- 입력은 클로저 안에서 `rng` 로 만들고, 깨지면 그 입력을 `Err` 메시지에 담아 반례를 남긴다.
- 시드가 고정이라 다시 돌려도 같은 입력이 나오지만, 일곱 프로퍼티가 수열 하나를 이어 쓰므로 차례가 바뀌면 입력도 바뀐다.
- `sort` 는 정렬 보장 · 길이 보존 · 원소 보존 세 불변량을 함께 세워야 `dedup` 같은 버그가 드러난다.
- RLE 데이터의 `% 4` 는 반복 구간을 자주 만들려는 장치지만, 길이 29 제한 때문에 255 경계는 검사되지 않는다.
- 이 실행기에는 shrinking 이 없다 — 진짜 `proptest` 와 다른 가장 큰 점이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
