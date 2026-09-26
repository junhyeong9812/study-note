# rust/syntax/43 — `Deref` 강제와 스마트 포인터를 쓰는 감각 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. 격자는 `bash <파일>.sh`(칸마다 `--emit=metadata` 로 컴파일만 한다). **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **`&` 를 넘기는 자리를 보면 먼저 물어라** — 「**받는 쪽 타입이 적혀 있나, 추론되나**」와 「**이것은 함수 인자인가 메서드 수신자인가**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 받는 자리 셋 × 넘기는 것 열 (예측)

```bash
# r43_grid.sh
# 받는 자리 셋 × 넘기는 것 열 — 칸마다 소스를 만들어 컴파일만 한다
T=$'\t'
slots=(
  'fn f(_x: &str) {}'
  'fn f(_x: &[i32]) {}'
  'fn f(_x: &String) {}'
)
slotname=('&str' '&[i32]' '&String')
args=(
  '&String|let v = String::from("a"); f(&v);'
  '&Box<String>|let v = Box::new(String::from("a")); f(&v);'
  '&Rc<String>|let v = std::rc::Rc::new(String::from("a")); f(&v);'
  '&&String|let s = String::from("a"); let v = &s; f(&v);'
  '&mut String|let mut v = String::from("a"); f(&mut v);'
  'String (no &)|let v = String::from("a"); f(v);'
  '&Vec<i32>|let v = vec![1, 2]; f(&v);'
  '&Box<Vec<i32>>|let v = Box::new(vec![1, 2]); f(&v);'
  '&[i32; 2]|let v = [1, 2]; f(&v);'
  '&mut Vec<i32>|let mut v = vec![1, 2]; f(&mut v);'
)
hdr="passed"
for s in "${slotname[@]}"; do hdr="$hdr${T}$s"; done
printf '%s\n' "$hdr"
ok=0; total=0
for a in "${args[@]}"; do
  label=${a%%|*}
  body=${a#*|}
  row="$label"
  for i in 0 1 2; do
    printf '%s\nfn main() {\n    %s\n}\n' "${slots[$i]}" "$body" > g.rs
    if rustc --edition 2021 -A unused --emit=metadata -o g.rmeta g.rs 2>err.txt; then
      cell=ok; ok=$((ok+1))
    else
      cell=$(grep -o '^error\[E[0-9]*\]' err.txt | head -1 | sed 's/^error\[\(.*\)\]/\1/')
    fi
    row="$row${T}$cell"
    total=$((total+1))
  done
  cols=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
  [ "$cols" = 4 ] || { echo "column count $cols != 4"; exit 1; }
  printf '%s\n' "$row"
done
echo "cells that compile: $ok / $total"
```

- 열 행 × 세 칸을 `ok` 또는 에러 번호로 채워라. 마지막 줄의 `N / 30` 은?

### 2. ★★★ 같은 `&b` 를 두 함수에 (예측)

```rust
// r43_generic.rs
use std::any::type_name;

fn concrete(_x: &str) -> &'static str {
    type_name::<str>()
}

fn generic<T: ?Sized>(_x: &T) -> &'static str {
    type_name::<T>()
}

fn main() {
    let b = Box::new(String::from("a"));
    println!("concrete(&b)  T = {}", concrete(&b));
    println!("generic(&b)   T = {}", generic(&b));
    println!("generic(&*b)  T = {}", generic(&*b));
    println!("generic(&**b) T = {}", generic(&**b));
}
```

- 네 줄의 `T =` 뒤는 각각 무엇인가?

### 3. ★★ `str` 에만 구현한 트레이트 (예측)

```rust
// r43_bound.rs
trait Shout {
    fn shout(&self) -> String;
}

impl Shout for str {
    fn shout(&self) -> String {
        self.to_uppercase()
    }
}

fn loud<T: Shout + ?Sized>(x: &T) -> String {
    x.shout()
}

fn main() {
    let s = String::from("hi");
    println!("{}", s.shout());
    println!("{}", loud(&s));
}
```

```rust
// r43_ufcs.rs
trait Shout {
    fn shout(&self) -> String;
}

impl Shout for str {
    fn shout(&self) -> String {
        self.to_uppercase()
    }
}

fn main() {
    let s = String::from("hi");
    println!("{}", s.shout());
    println!("{}", Shout::shout(&s));
}
```

- 두 소스는 각각 컴파일되는가? 에러라면 **몇 행**에서 몇 번이고, 에러가 **안 난 행**은 어디인가?

### 4. ★★ 문자열 리터럴 패턴 (예측)

```rust
// r43_match.rs
fn main() {
    let s = String::from("on");
    let n = match &s {
        "on" => 1,
        _ => 0,
    };
    println!("{n}");
}
```

- 컴파일되는가? 에러라면 번호와 「expected / found」는? 통과시키려면 조사 대상을 어떻게 바꾸나(두 가지)?

### 5. ★★ 겹친 포인터에서 메서드와 인자 (예측)

```rust
// r43_method.rs
use std::rc::Rc;

fn takes(s: &str) -> usize {
    s.len()
}

fn main() {
    let b: Box<Rc<String>> = Box::new(Rc::new(String::from("abc")));
    println!("b.len()          {}", b.len());
    println!("b.is_empty()     {}", b.is_empty());
    println!("takes(&b)        {}", takes(&b));
    println!("(**b).len()      {}", (**b).len());
}
```

```rust
// r43_value_arg.rs
fn takes(s: &str) -> usize {
    s.len()
}

fn main() {
    let b = Box::new(String::from("abc"));
    println!("{}", b.len());
    println!("{}", takes(b));
}
```

- 앞 소스의 네 줄 출력은? 뒤 소스는 컴파일되는가 — 된다면 출력, 안 된다면 **어느 행**이 에러이고 `help:` 는?

### 6. ★★ `Deref` 만 단 감싸개로 고치기 (예측)

```rust
// r43_newtype_nomut.rs
use std::ops::Deref;

struct Name(String);

impl Deref for Name {
    type Target = String;
    fn deref(&self) -> &String {
        &self.0
    }
}

fn main() {
    let mut n = Name(String::from("kim"));
    n.push_str("-lee");
    println!("{}", n.0);
}
```

- 컴파일되는가? 에러라면 번호와 `= help:` 는? **에러 말고 무엇이 더** 나오나?

### 7. ★★★ 제네릭 자리에서 안 벗기는 이유 (왜)

- 2번에서 `concrete` 와 `generic` 이 갈리는 이유를 Reference 의 「강제 지점」 정의로 설명하라 — 정의의 어느 구절이 `&T` 를 제외하나?

### 8. ★★ `ok` 이지만 `Deref` 가 아닌 칸 (경계)

- 1번에서 `&[i32; 2]` → `&[i32]` 와 `&mut String` → `&str` 는 통과한다. 각각 Reference 의 **어느 강제**인가? `String`(`&` 없음)은 왜 세 칸 모두 막히나?

### 9. ★★ 강제가 안 도는 자리 목록 (연결)

- [14번 주제](../14-string-vs-str/) (4)는 「안 도는 자리」로 둘을 들었다. 이 편이 더한 자리들은 무엇이고, 이들을 한 문장으로 묶으면?

### 10. ★★ 내 타입에 `Deref` 를 다는 기준 (경계)

- std `Deref` 문서의 「When to implement」는 달아도 되는 조건과 달지 말 조건을 각각 무엇이라고 하나? API Guidelines 의 C-DEREF 는? [30번 주제](../30-operator-overloading-std-ops-index-and-deref/) (8)의 「상속 흉내」가 그 권고의 어느 조건에 걸리나?

### 11. ★ 에러와 함께 나온 경고 (왜)

- 6번에서 에러와 함께 나온 경고의 `help:` 를 따르면 무엇이 되나? 왜 컴파일러는 그 `mut` 가 필요 없다고 보나 — 진짜 처방은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
