# rust/rust-testing-security/06 — Property-Based Testing — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 일곱 프로퍼티를 다 돌리면 (예측)

```rust
// 질문용 발췌 — run 의 찍는 부분, 프로퍼티는 일곱 개를 차례로 돌린다
print!("  {} ... ", name);
for i in 0..self.iterations {
    match prop(self) {
        Ok(()) => {}
        Err(msg) => { println!("FAILED (iteration {})", i); println!("    {}", msg); return; }
    }
}
println!("OK ({} iterations)", self.iterations);
```

- `TestRunner::new(100)` 으로 일곱 프로퍼티를 돌리면 `=== Property-Based Testing ===` 아래에 줄마다 무엇이 찍히나?

### 2. 정렬에 `dedup` 버그를 심으면 (예측)

```rust
// 질문용 발췌 — 버그를 심은 sort
fn sort(mut v: Vec<i32>) -> Vec<i32> {
    v.sort();
    v.dedup();
    v
}
```

- 이 `sort` 로 바꿔 끼우면 프로퍼티 3(정렬 보장) · 4(길이 보존) · 5(원소 보존)의 결과 줄은 각각 어떻게 되나?

### 3. 중괄호를 두 번 쓴 `println!` (예측)

```rust
// 질문용 발췌
println!("//     fn test_reverse(s in \"[a-z]{{0,100}}\") {{");
```

- 이 줄은 화면에 어떤 글자로 찍히나?

### 4. 시드를 12345 로 고정한 까닭 (왜)

- 실행기가 시드를 고정값으로 두는 까닭은 무엇이고, 그 대가로 생기는 얽힘은 무엇인가?

### 5. RLE 데이터를 `% 4` 로 만드는 까닭 (왜)

- 라운드트립 프로퍼티의 데이터를 0~255 가 아니라 0~3 네 값으로만 만드는 까닭은 무엇인가?

### 6. 원소 보존 검사가 같은 정렬을 쓰는 것 (왜)

- 프로퍼티 5 가 검사 대상과 같은 표준 정렬로 비교 기준을 만드는 것은 왜 약점이 되나?

### 7. RLE 의 255 경계 (경계)

- 이 예제의 생성기로 100 번 돌릴 때 인코더의 `count < 255` 에서 끊는 경로는 검사되나?

### 8. `next_string(0)` 과 `i32` 전체 범위 (경계)

- `next_string(0)` 을 부르거나 교환법칙의 범위를 `i32::MIN..=i32::MAX` 로 넓히면 무엇이 깨지고, `run` 은 그것을 `FAILED` 로 보고하나?

### 9. 흉내 생성기와 `proptest` 전략의 짝 (연결)

- 흉내 실행기의 `next_string` · 벡터 만들기는 `proptest` 의 어떤 전략에 해당하고, 실패했을 때 둘이 보고하는 반례는 무엇이 다른가?

### 10. 일곱 프로퍼티와 대표 프로퍼티의 꼴 (연결)

- 원본 팁이 드는 라운드트립 · 항등성 · 불변량에 일곱 프로퍼티를 나누면 어디에도 들지 않는 것은 무엇인가?

## 실습

### 실습 1. 순수 Rust 로 프로퍼티 테스트 실행기를 만들고 일곱 프로퍼티 검사하기

**만들 것** — 고정 시드 LCG 로 무작위 입력을 만드는 작은 실행기 `TestRunner` 를 만든다.
그 실행기로 `reverse` · `sort` · RLE `encode_decode` · 덧셈의 프로퍼티 일곱 개를 100 번씩 검사한다.

**준비물** — 외부 크레이트는 필요 없다.
`proptest` 크레이트는 쓰지 않고 그 개념을 흉내 내며, 진짜 `proptest` 코드는 글자로만 찍는다.

**요구 조건**

1단계 — 실행기

1. `TestRunner` 는 반복 횟수(`iterations`)와 시드(`seed`)를 가지고, `new(iterations)` 는 시드를 12345 로 고정해 만든다.
2. `next_u64` 는 시드에 시작 코드에 적힌 곱셈 상수를 곱하고 덧셈 상수를 더해(둘 다 넘치면 감아 돌게) 새 시드로 바꾸고 그 값을 돌려준다.
3. `next_i32(min, max)` 는 양 끝을 포함한 `[min, max]` 의 정수를 돌려준다.
4. `next_string(max_len)` 는 길이 0 ~ `max_len - 1` 의 영문 소문자 문자열을 돌려준다.
5. `run(name, prop)` 은 `"  이름 ... "` 을 줄바꿈 없이 찍고, 클로저를 반복 횟수만큼 부른다.
6. 클로저가 `Err(msg)` 를 돌려주면 `FAILED (iteration i)` 와 네 칸 들여 쓴 `msg` 를 찍고 그 프로퍼티를 끝낸다.
7. 반복을 모두 통과하면 `OK (반복횟수 iterations)` 를 찍는다.

2단계 — 검사 대상

8. `reverse` 는 문자열을 문자(`char`) 단위로 뒤집는다.
9. `sort` 는 벡터를 받아 정렬해 돌려준다.
10. `encode_decode` 는 안쪽 함수 `rle_encode` 로 같은 바이트의 연속을 `[개수, 바이트]` 쌍으로 줄이고(개수가 255 에 이르면 새 그룹), `rle_decode` 로 두 바이트씩 끊어 되살린 결과를 돌려준다.
11. `rle_encode` 는 빈 입력에 빈 벡터를 돌려주고, `rle_decode` 는 두 바이트가 안 되는 마지막 조각을 건너뛴다.

3단계 — 프로퍼티

12. 반복 100 번짜리 실행기 하나로 아래 일곱 프로퍼티를 차례로 돌리고, 깨지면 입력이 담긴 `Err` 메시지를 돌려준다.
13. `reverse 항등성` — 길이 0~19 문자열에서 두 번 뒤집으면 원래 문자열이다.
14. `reverse 길이 보존` — 길이 0~49 문자열에서 뒤집어도 길이가 같다.
15. `sort 정렬 보장` — 길이 0~19, 값 -100~100 벡터를 정렬하면 모든 이웃 쌍이 `<=` 다(`windows(2)`).
16. `sort 길이 보존` — 길이 0~29, 값 -50~50 벡터를 정렬해도 길이가 같다.
17. `sort 원소 보존` — 길이 0~19, 값 -10~10 벡터에서 정렬 결과와 원본을 둘 다 다시 정렬하면 같다.
18. `RLE encode/decode 라운드트립` — 길이 0~29, 값 0~3 바이트 벡터가 `encode_decode` 뒤에도 같다.
19. `덧셈 교환법칙` — -1000~1000 의 두 정수에서 `a + b == b + a` 다.
20. 끝으로 진짜 `proptest` 코드 모양과 shrinking 설명을 찍는다(시작 코드에 이미 채워 두었다).

**시작 코드**

```rust
// === Property-Based Testing 패턴 (순수 Rust 흉내) ===

use std::fmt;

struct TestRunner {
    iterations: usize,
    seed: u64,
}

impl TestRunner {
    fn new(iterations: usize) -> Self {
        // TODO: 시드는 12345 로 고정
        todo!()
    }

    fn next_u64(&mut self) -> u64 {
        // TODO: LCG 한 걸음 — 곱셈 상수 6364136223846793005, 덧셈 상수 1442695040888963407
        //       넘침은 감아 돌게(wrapping) 하고, 새 시드를 돌려준다
        todo!()
    }

    fn next_i32(&mut self, min: i32, max: i32) -> i32 {
        // TODO: [min, max] 양 끝 포함
        todo!()
    }

    fn next_string(&mut self, max_len: usize) -> String {
        // TODO: 길이 0..max_len, 글자는 'a'..='z'
        todo!()
    }

    fn run<F>(&mut self, name: &str, mut prop: F)
    where F: FnMut(&mut TestRunner) -> Result<(), String>
    {
        print!("  {} ... ", name);
        // TODO: iterations 번 prop(self) 를 부르고, Err(msg) 면
        //       "FAILED (iteration i)" 와 "    msg" 를 찍고 끝낸다
        println!("OK ({} iterations)", self.iterations);
    }
}

fn reverse(s: &str) -> String {
    // TODO: 문자 단위로 뒤집기
    todo!()
}

fn sort(mut v: Vec<i32>) -> Vec<i32> {
    // TODO
    todo!()
}

fn encode_decode(data: &[u8]) -> Vec<u8> {
    fn rle_encode(data: &[u8]) -> Vec<u8> {
        // TODO: [개수, 바이트] 쌍으로 — 빈 입력은 빈 벡터, 개수(u8)가 255 면 새 그룹
        todo!()
    }

    fn rle_decode(encoded: &[u8]) -> Vec<u8> {
        // TODO: chunks(2) 로 끊어 chunk[0] 번 chunk[1] 을 넣는다 — 짧은 조각은 건너뛴다
        todo!()
    }

    let encoded = rle_encode(data);
    rle_decode(&encoded)
}

fn main() {
    println!("=== Property-Based Testing ===");
    let mut runner = TestRunner::new(100);

    runner.run("reverse 항등성", |rng| {
        // TODO: next_string(20) 으로 s 를 만들고 reverse(&reverse(&s)) == s 검사
        todo!()
    });

    runner.run("reverse 길이 보존", |rng| {
        // TODO: next_string(50), 길이 비교
        todo!()
    });

    runner.run("sort 정렬 보장", |rng| {
        // TODO: 길이 next_u64() % 20, 값 next_i32(-100, 100), windows(2) 로 이웃 쌍 검사
        todo!()
    });

    runner.run("sort 길이 보존", |rng| {
        // TODO: 길이 next_u64() % 30, 값 next_i32(-50, 50)
        todo!()
    });

    runner.run("sort 원소 보존", |rng| {
        // TODO: 길이 next_u64() % 20, 값 next_i32(-10, 10), 둘 다 다시 정렬해 비교
        todo!()
    });

    runner.run("RLE encode/decode 라운드트립", |rng| {
        // TODO: 길이 next_u64() % 30, 값 (next_u64() % 4) as u8
        todo!()
    });

    runner.run("덧셈 교환법칙", |rng| {
        // TODO: a, b 를 next_i32(-1000, 1000) 으로
        todo!()
    });

    // --- 아래는 미리 채워 둔 설명 출력 ---
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

**확인 방법** — `rustc proptest.rs && ./proptest` 로 돌려 일곱 줄이 모두 `OK (100 iterations)` 인지 본다.
이어서 `sort` 에 `v.dedup();` 을 잠깐 넣어 길이 보존 · 원소 보존 줄이 `FAILED` 로 바뀌고 반례가 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
