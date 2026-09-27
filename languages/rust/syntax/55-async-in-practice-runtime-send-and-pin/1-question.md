# rust/syntax/55 — async 실전: 런타임 선택 · `Send` 경계 · `Pin` 맛보기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. `Box::pin` 문항은 같은 디렉토리에 [54번 주제](../54-async-await-and-future-state-machines/)의 `r54_exec.rs` 를 둔다. tokio 문항은 `cargo … --offline`(로컬 캐시의 tokio 1.52.3).
> ★★★ **future 를 `spawn` 에 넘기기 전에 물어라** — 「**await 를 가로질러 무엇을 쥐고 있나**」와 「**그것은 다른 스레드로 넘겨도 되나**」.
> ★ **문항 12개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 보통 `main` 에서 기다리기 (예측)

```rust
// r55_await_in_main.rs
async fn f() -> u32 {
    7
}

fn main() {
    let v = f().await;
    println!("{v}");
}
```

- 컴파일되는가? 안 된다면 에러 번호와 표지가 짚는 **두 자리**는?

### 2. ★★★ `main` 에 `async` 를 붙이면 (예측)

```rust
// r55_async_main.rs
async fn f() -> u32 {
    7
}

async fn main() {
    let v = f().await;
    println!("{v}");
}
```

- 컴파일되는가? 안 된다면 에러 번호는? 1번과 같은 번호인가?

### 3. ★★★ `Rc` 를 쥔 채 await 하는 future 를 `Send` 자리에 (예측)

```rust
// r55_send_rc.rs
use std::future::Future;
use std::rc::Rc;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn keeps_rc() {
    let r = Rc::new(5);
    tick().await;
    println!("{r}");
}

fn main() {
    need_send(keeps_rc());
}
```

- 컴파일되는가? 에러라면 **에러 번호가 붙나**? `note:` 가 짚는 두 줄(행 번호)과 각 표지의 문구는?

### 4. ★★★ 버리는 방법 세 가지 (예측)

```rust
// r55_send_rc_drop.rs
use std::future::Future;
use std::rc::Rc;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn read_then_drop() {
    let r = Rc::new(5);
    let n = *r;
    drop(r);
    tick().await;
    println!("{n}");
}

fn main() {
    need_send(read_then_drop());
}
```

```rust
// r55_send_rc_ok.rs
use std::future::Future;
use std::rc::Rc;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn drop_without_reading() {
    let r = Rc::new(5);
    drop(r);
    tick().await;
}

async fn read_in_inner_block() {
    let n = {
        let r = Rc::new(5);
        *r
    };
    tick().await;
    println!("{n}");
}

fn main() {
    need_send(drop_without_reading());
    need_send(read_in_inner_block());
    eprintln!("[main] reached the end");
}
```

- 두 파일은 각각 컴파일되는가? 에러가 난다면 어느 함수이고, 그 함수의 `drop(r);` 은 왜 소용이 없었나?

### 5. ★★★ `std` 락 가드를 쥔 채 await (예측)

```rust
// r55_send_guard.rs
use std::future::Future;
use std::sync::Mutex;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn guard_across_await(m: &Mutex<u32>) {
    let mut g = m.lock().unwrap();
    *g += 1;
    tick().await;
    *g += 1;
}

fn main() {
    static M: Mutex<u32> = Mutex::new(0);
    need_send(guard_across_await(&M));
}
```

```rust
// r55_send_guard_drop.rs
use std::future::Future;
use std::sync::Mutex;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn guard_dropped(m: &Mutex<u32>) {
    let mut g = m.lock().unwrap();
    *g += 1;
    drop(g);
    tick().await;
}

fn main() {
    static M: Mutex<u32> = Mutex::new(0);
    need_send(guard_dropped(&M));
}
```

```rust
// r55_send_guard_ok.rs
use std::future::Future;
use std::sync::Mutex;

async fn tick() {}

fn need_send<F: Future + Send>(_f: F) {}

async fn guard_in_block(m: &Mutex<u32>) {
    {
        let mut g = m.lock().unwrap();
        *g += 1;
    }
    tick().await;
}

fn main() {
    static M: Mutex<u32> = Mutex::new(0);
    need_send(guard_in_block(&M));
    eprintln!("[main] reached the end");
}
```

- 세 파일 중 컴파일되는 것은? 에러 메시지에 나오는 **가드의 타입 이름**은?

### 6. ★★ `Unpin` 을 요구하는 자리 (예측)

```rust
// r55_unpin.rs
use std::future::Future;

async fn f() -> u32 {
    7
}

fn need_unpin<F: Future + Unpin>(_f: F) {}

fn main() {
    need_unpin(f());
}
```

```rust
// r55_boxpin.rs
mod r54_exec;

use std::future::Future;
use std::pin::Pin;

async fn seven() -> u32 {
    7
}

async fn add(a: u32, b: u32) -> u32 {
    a + b
}

fn need_unpin<F: Future + Unpin>(_f: &F) {}

fn main() {
    // Two different future types in one Vec: box them and pin the boxes.
    let jobs: Vec<Pin<Box<dyn Future<Output = u32>>>> = vec![Box::pin(seven()), Box::pin(add(1, 2))];
    need_unpin(&jobs[0]);
    for job in jobs {
        let v = r54_exec::block_on(job);
        eprintln!("[main] got {v}");
    }
}
```

- 앞 파일은 컴파일되는가? 에러라면 번호와 `= note:` 의 처방 둘은? 뒤 파일은 컴파일되는가 — `need_unpin(&jobs[0])` 줄은 통과하나? 출력은?

### 7. ★★ std 의 `task`·`future` 모듈에 없는 것 (왜)

- 서머리 (1)의 목록에서 **stable 인 것**을 「양식」·「벨」·「작은 future」로 나눠 보라. 실행기를 짓는 데 필요한데 **목록에 없는 것**은 무엇이고, 그것이 1·2번 에러와 어떻게 이어지나?

### 8. ★★ `MutexGuard` 는 왜 `!Send` 인가 (왜)

- std 문서는 어떤 플랫폼 규칙을 이유로 드나? 그 규칙이 「가드를 쥔 future 가 다른 워커 스레드로 옮겨 간다」와 어떻게 부딪히나?

### 9. ★★ `Send` 가 안 걸리는 실행기라면 (경계)

- 단일 스레드 실행기(`Send` 를 안 요구한다)에서 `std::sync::Mutex` 가드를 await 너머로 쥐면 5번의 컴파일 에러는 안 난다. 그래도 남는 문제는 무엇이고, 처방 두 가지는? 이 문서는 그 문제를 재현했나?

### 10. ★★ tokio 의 네 가지 자리 (연결)

- 서머리 (5)의 tokio 블록에서 `current_thread` 와 `multi_thread` 의 스레드 이름 집합은 각각 무엇이었나? `tokio::spawn` 과 `spawn_local` 은 무엇으로 갈리고, `current_thread` 런타임에서도 `tokio::spawn` 이 `Send` 를 요구하나?

### 11. ★★ `poll` 서명의 `Pin` (왜)

- `Future::poll` 은 왜 `&mut Self` 가 아니라 `Pin<&mut Self>` 를 받나? std `pin` 문서가 드는 대표 예는 무엇이고, 그런 값을 옮기면 무엇이 깨지나? `Pin<Box<…>>` 는 왜 옮겨도 되나?

### 12. ★★ 54번 크기 격자와 4번 (연결)

- [54번 주제](../54-async-await-and-future-state-machines/) (4)의 `b_used_before_only` 1032 대 `b2_indexed_before_only` 8 은 4번의 결과와 어떻게 같은 이야기인가? 이 판정은 언어가 보장하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
