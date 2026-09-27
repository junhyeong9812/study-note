# rust/syntax/34 — 클로저 세 종류 `Fn`/`FnMut`/`FnOnce`와 `move` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. **(6)번 문항만 에디션을 바꿔 던진다** — 답할 때 **어느 에디션인지를 먼저** 말하라.
> ★★ **`--edition` 을 빼면 에디션 2015 다.** ★★ **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **클로저를 보면 두 가지를 먼저 물어라** — 「**몸통이 잡은 것을 읽나 · 고치나 · 옮기나**」와 「**이 클로저가 지금 함수보다 오래 사나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 클로저 몸통 × 받는 함수 격자 (예측)

```bash
# r34_grid.sh
# 클로저 몸통 셋 × 받는 함수 셋 — 컴파일러가 칸마다 받나 거절하나
# 두 벌로 던진다: inline = 부르는 자리에 클로저를 바로 쓴다 · let = 변수에 묶었다가 넘긴다
# 칸: 통과면 ok, 에러면 진단 코드
bodies=(
  'read|println!("{}", s.len())'
  'mutate|s.push(1)'
  'give_away|drop(s)'
)
needs=(Fn FnMut FnOnce)
for layout in inline let; do
  rejected=0 total=0
  echo "== $layout"
  printf '%-10s | %-6s | %-6s | %s\n' body Fn FnMut FnOnce
  for b in "${bodies[@]}"; do
    name=${b%%|*} body=${b#*|} line=""
    for t in "${needs[@]}"; do
      if [ $layout = inline ]; then
        call="need(|| $body);"
      else
        call="let c = || $body;
    need(c);"
      fi
      printf 'fn need(f: impl %s()) {\n    let _ = f;\n}\nfn main() {\n    let mut s = vec![0u8];\n    %s\n}\n' "$t" "$call" >g.rs
      if rustc --edition 2021 -A warnings --crate-name g g.rs -o g 2>g.err; then
        c=ok
      else
        c=$(grep -m1 -oE '^error\[E[0-9]+\]' g.err | sed -E 's/error\[(.*)\]/\1/')
        rejected=$((rejected + 1))
      fi
      total=$((total + 1))
      line+=$(printf ' | %-6s' "$c")
    done
    printf '%-10s%s\n' "$name" "$line"
  done
  echo "rejected cells ($layout): $rejected / $total"
done
rm -f g.rs g.err g
```

- ★★★ `inline` 표의 아홉 칸은 각각 `ok` 인가, 무슨 코드인가? 마지막 줄의 수는?
- ★★ `let` 표의 아홉 칸은? `inline` 표와 **무엇이 같고 무엇이 다른가**?
- ★ 표가 **어떤 모양**을 그리는가 — 어느 열이 전부 받고, 어느 열이 가장 적게 받나?

### 2. ★★ 같은 칸의 에러 번호 (예측)

```rust
// r34_let_mut.rs
// 변수에 묶은 클로저를 impl Fn 자리에
fn need_fn(f: impl Fn()) {
    f();
}

fn main() {
    let mut s = vec![0u8];
    let c = || s.push(1);
    need_fn(c);
}
```

```rust
// r34_inline_mut.rs
// 같은 클로저를 부르는 자리에 바로 쓰면
fn need_fn(f: impl Fn()) {
    f();
}

fn main() {
    let mut s = vec![0u8];
    need_fn(|| s.push(1));
}
```

- 두 소스의 에러 번호는 각각? 진단이 **탓하는 자리**(클로저 몸통인가, 받는 함수의 시그니처인가)는 어디인가?
- ★ 두 번호가 다른 이유를 **추론의 순서**로 설명하면?

### 3. ★★★ `move` 로 잡고 읽기만 (예측)

```rust
// r34_move_fn.rs
// move 로 잡았지만 읽기만 하는 클로저
fn need_fn(f: &impl Fn() -> usize) -> usize {
    f() + f()
}

fn main() {
    let s = String::from("abc");
    let c = move || s.len();
    println!("{}", need_fn(&c));
    println!("{}", c());
}
```

```rust
// r34_move_after.rs
// move 로 잡은 뒤 원래 변수를 쓰면
fn main() {
    let s = String::from("abc");
    let c = move || s.len();
    println!("{}", c());
    println!("{}", s);
}
```

- 앞 소스는 컴파일되는가? 출력은? 이 클로저는 세 트레이트 중 **어디까지** 구현하는가?
- 뒤 소스는? 에러면 번호와, **무엇이 옮겨졌다고** 말하는가?
- ★★ 「`move` 를 붙이면 `FnOnce` 가 된다」는 맞는가? Reference 는 이것을 어떻게 적는가?

### 4. ★★ 스레드에 읽기만 하는 클로저 (예측)

```rust
// r34_thread.rs
// 스레드에 클로저를 넘긴다
use std::thread;

fn main() {
    let v = vec![1, 2, 3];
    let h = thread::spawn(|| v.len());
    println!("{}", h.join().unwrap());
}
```

- 컴파일되는가? 에러면 번호와 `note:` 가 말하는 **요구**는?
- ★ `help:` 대로 고치면 통과하는가? 그때 클로저는 여전히 `Fn` 인가?

### 5. ★★ 클로저 하나의 바이트 (예측)

```rust
// r34_size.rs
// 클로저 하나는 몇 바이트인가 — 무엇을 어떻게 잡았나에 따라
use std::mem::size_of_val;

fn main() {
    let n: i32 = 7;
    let m: i32 = 8;
    let s = String::from("abc");
    let none = || 1;
    let by_ref = || n + 1;
    let two_refs = || n + m;
    let by_move = move || n + 1;
    let string_ref = || s.len();
    println!("none        {}", size_of_val(&none));
    println!("by_ref      {}", size_of_val(&by_ref));
    println!("two_refs    {}", size_of_val(&two_refs));
    println!("by_move     {}", size_of_val(&by_move));
    println!("string_ref  {}", size_of_val(&string_ref));
    let string_move = move || s.len();
    println!("string_move {}", size_of_val(&string_move));
    println!("{}", none() + by_ref() + two_refs() + by_move() + string_move() as i32);
}
```

- 여섯 줄 각각 몇인가? 특히 `by_ref` 와 `by_move` 는?
- ★ 이 수치는 언어가 보장하는가?

### 6. ★★★ 필드 하나를 쓰는 클로저 — 에디션을 바꿔 가며 (예측)

```rust
// r34_dj_borrow.rs
// 클로저가 p.name 을 읽는 동안 p.age 를 고친다
struct P {
    name: String,
    age: u32,
}

fn main() {
    let mut p = P { name: String::from("kim"), age: 30 };
    let c = || println!("{}", p.name);
    p.age += 1;
    c();
    println!("{}", p.age);
}
```

```rust
// r34_dj_size.rs
// move 클로저가 p.name 만 쓴다 — 클로저는 몇 바이트인가
struct P {
    name: String,
    age: u32,
}

fn main() {
    let p = P { name: String::from("kim"), age: 30 };
    let c = move || p.name.len();
    println!("P {}, closure {}", std::mem::size_of::<P>(), std::mem::size_of_val(&c));
    println!("{}", c());
}
```

```rust
// r34_dj_after.rs
// move 클로저가 p.name 만 쓴 뒤 p.age 를 읽는다
struct P {
    name: String,
    age: u32,
}

fn main() {
    let p = P { name: String::from("kim"), age: 30 };
    let c = move || p.name.len();
    println!("{} {}", c(), p.age);
}
```

```bash
# r34_ed_grid.sh
# 세 소스를 에디션 넷으로 — 칸: 통과면 실행 출력(한 줄로), 에러면 진단 코드
changed=0
printf '%-16s | %-22s | %-22s | %-22s | %s\n' source 2015 2018 2021 2024
for f in r34_dj_borrow r34_dj_size r34_dj_after; do
  row=()
  for e in 2015 2018 2021 2024; do
    if rustc --edition $e -A warnings $f.rs -o $f.$e 2>$f.err; then
      row+=("$(./$f.$e | paste -sd '/')")
    else
      row+=("$(grep -m1 -oE '^error\[E[0-9]+\]' $f.err | sed -E 's/error\[(.*)\]/\1/')")
    fi
    rm -f $f.$e $f.err
  done
  printf '%-16s | %-22s | %-22s | %-22s | %s\n' $f "${row[@]}"
  [ "${row[1]}" != "${row[2]}" ] && changed=$((changed + 1))
done
echo "sources whose cell changes between 2018 and 2021: $changed / 3"
```

- ★★★ 격자의 열두 칸은 각각 무엇인가(실행 출력이나 에러 코드)? **어느 두 에디션 사이**에서 갈리는가?
- ★★ `r34_dj_size` 의 클로저 크기가 에디션에 따라 달라진다면, 그 두 값은 **각각 무엇의 크기**인가?

### 7. `FnOnce` 를 두 번, `FnMut` 을 `mut` 없이 (경계)

- `let c = move || s; c(); c();` 는 무슨 번호의 에러인가? `note:` 가 말하는 이유는?
- `let c = || n += 1; c();` 는? 무엇을 한 단어 덧붙이면 되는가?

### 8. ★ 받는 쪽 경계는 무엇으로 적나 (왜)

- 콜백을 **한 번만** 부르는 함수는 `Fn`·`FnMut`·`FnOnce` 중 무엇으로 받는 것이 가장 많은 클로저를 받는가? **여러 번** 부르면?
- ★ 부르는 쪽에서 `Fn` 이 `FnMut` 자리에 들어갈 수 있는 이유를 **빌림 규칙**으로 말하면?

### 9. ★★ 루프에서 모은 클로저 — 세 언어 (연결)

- Rust 에서 `for i in 0..3 { fs.push(Box::new(move || i)) }` 를 부르면 무엇이 나오나? `move` 를 빼면?
- ★ 파이썬의 `[lambda: i for …]` 류가 `[2, 2, 2]` 를 내는 이유는? Go 는 1.22 에서 무엇을 바꿨나?

### 10. ★ E0373 의 `move` 는 무엇 때문인가 (왜)

- 스레드에 넘기는 클로저에 `move` 가 필요한 것은 **트레이트** 때문인가 **수명** 때문인가?

### 11. 빌림 규칙과 세 트레이트 (연결)

- [10번 주제](../10-borrowing-and-aliasing-rules/)의 「불변 빌림 여럿 / 가변 빌림 하나」가 `Fn`·`FnMut` 에 각각 어떻게 대응하는가?
- [08번 주제](../08-ownership-and-move/)의 이동은 어느 트레이트인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
