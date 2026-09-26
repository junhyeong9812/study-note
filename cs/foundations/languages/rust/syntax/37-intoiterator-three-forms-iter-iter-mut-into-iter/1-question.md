# rust/syntax/37 — `IntoIterator` 세 형태 — `iter`/`iter_mut`/`into_iter` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`(에디션 격자는 스크립트가 네 에디션을 돈다). **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **`for` 를 보면 먼저 물어라** — 「**`in` 뒤에 놓인 것의 타입이 무엇인가**」. 값인가, `&` 인가, `&mut` 인가.
> ★ **문항 10개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 여섯 형태를 한 표로 (예측)

```bash
# r37_grid.sh
# 여섯 형태 × (x 의 타입 · 순회 뒤 v.len()) — 형태마다 소스 두 벌을 만들어 던진다
forms=(
  'for x in v'
  'for x in &v'
  'for x in &mut v'
  'for x in v.iter()'
  'for x in v.iter_mut()'
  'for x in v.into_iter()'
)
printf '%-24s | %-28s | %s\n' form 'type of x' 'v.len() after the loop'
bad=0
for f in "${forms[@]}"; do
  body="    let mut v = vec![String::from(\"a\")];
    let mut t = \"\";
    $f { t = std::any::type_name_of_val(&x); }
    println!(\"{t}\");"
  printf 'fn main() {\n%s\n}\n' "$body" > g.rs
  rustc --edition 2021 -A unused -o g g.rs 2>/dev/null
  ty=$(./g)
  printf 'fn main() {\n%s\n    println!("{}", v.len());\n}\n' "$body" > h.rs
  if out=$(rustc --edition 2021 -A unused -o h h.rs 2>&1); then
    cell=ok
  else
    cell=$(printf '%s\n' "$out" | grep -o 'error\[E[0-9]*\]' | head -1)
    bad=$((bad+1))
  fi
  printf '%-24s | %-28s | %s\n' "$f" "$ty" "$cell"
done
echo "cells where v cannot be used after the loop: $bad / ${#forms[@]}"
```

- ★★★ 표의 여섯 줄 — `type of x` 칸과 `v.len() after the loop` 칸(`ok` 또는 에러 번호)을 채워라. 마지막 줄의 `N / 6` 은?
- ★★ 여섯 줄 중 **서로 한 글자도 같은 줄**끼리 짝을 지으면?

### 2. ★★ 같은 소스, 네 에디션 (예측)

```bash
# r37_ed_grid.sh
# 같은 소스를 네 에디션으로 — 원본 둘(배열 · Box<[i32]>) × 부르는 꼴 셋
exprs=(
  'a.into_iter()'
  'IntoIterator::into_iter(a)'
  'for-in a'
)
srcs=('[1, 2, 3]' 'vec![1, 2, 3].into_boxed_slice()')
names=('array' 'Box<[i32]>')
printf '%-12s %-28s | %-6s | %-6s | %-6s | %s\n' source call 2015 2018 2021 2024
changed=0; total=0
for i in 0 1; do
  for e in "${exprs[@]}"; do
    if [ "$e" = 'for-in a' ]; then
      line="    let mut t = \"\"; for x in a { t = std::any::type_name_of_val(&x); } println!(\"{t}\");"
    else
      line="    let it = $e; let mut t = \"\"; for x in it { t = std::any::type_name_of_val(&x); } println!(\"{t}\");"
    fi
    printf 'fn main() {\n    let a = %s;\n%s\n}\n' "${srcs[$i]}" "$line" > e.rs
    row=()
    for ed in 2015 2018 2021 2024; do
      rustc --edition $ed -A warnings -o e e.rs 2>/dev/null
      row+=("$(./e)")
    done
    total=$((total+1))
    [ "${row[1]}" != "${row[2]}" ] || [ "${row[2]}" != "${row[3]}" ] && changed=$((changed+1))
    printf '%-12s %-28s | %-6s | %-6s | %-6s | %s\n' "${names[$i]}" "$e" "${row[@]}"
  done
done
echo "rows whose item type changes across editions: $changed / $total"
```

- ★★★ 여섯 줄 × 네 에디션 칸을 채워라(`&i32` 또는 `i32`). 마지막 줄의 수는?
- ★★ 뜻이 바뀌는 줄이 있다면 **어느 에디션 경계**에서 바뀌나 — 배열과 `Box<[i32]>` 가 같은 경계인가?

### 3. ★ 원소가 `i32` 일 때 (예측)

```rust
// r37_copy.rs
// 원소가 Copy 인 i32 일 때
fn main() {
    let v = vec![1, 2];
    for x in v {
        let _ = x;
    }
    println!("{}", v.len());
}
```

- 컴파일되는가? 에러라면 번호와, 진단이 말하는 **`Copy` 가 아닌 타입**은 무엇인가?

### 4. ★★ `&mut v` 로 돌며 고치기 (예측)

```rust
// r37_mut.rs
fn main() {
    let mut v = vec![1, 2, 3];
    for x in &mut v {
        x *= 10;
    }
    println!("{v:?}");
}
```

- 컴파일되는가? 에러라면 번호는? `help:` 가 있다면 그대로 따르면 출력은?

### 5. ★★ 짝으로 나오는 항목 (예측)

```rust
// r37_pairs.rs
use std::any::type_name_of_val;
use std::collections::HashMap;

fn main() {
    let v = vec!['a', 'b'];
    for (i, x) in v.iter().enumerate() {
        println!("[1] {i} {x} : {} , {}", type_name_of_val(&i), type_name_of_val(&x));
    }

    let mut m = HashMap::new();
    m.insert(String::from("k"), 1);
    for (k, n) in &m {
        println!("[2] {k} {n} : {} , {}", type_name_of_val(&k), type_name_of_val(&n));
    }
    for (k, n) in &mut m {
        *n += 1;
        println!("[3] {k} {n} : {} , {}", type_name_of_val(&k), type_name_of_val(&n));
    }
    for (k, n) in m {
        println!("[4] {k} {n} : {} , {}", type_name_of_val(&k), type_name_of_val(&n));
    }
}
```

- `[1]`·`[2]`·`[3]`·`[4]` 네 줄의 두 타입은 각각?
- ★ `[3]` 에서 키 쪽은 왜 그 타입인가?

### 6. ★★ 값 구현 하나뿐인 타입을 `&` 로 (예측)

```rust
// r37_own_missing.rs
// 값 구현 하나만 — & 구현은 안 했다
struct Shelf {
    books: Vec<String>,
}

impl IntoIterator for Shelf {
    type Item = String;
    type IntoIter = std::vec::IntoIter<String>;
    fn into_iter(self) -> Self::IntoIter {
        self.books.into_iter()
    }
}

fn main() {
    let s = Shelf { books: vec![String::from("dune")] };
    for b in &s {
        println!("{b}");
    }
}
```

- 컴파일되는가? 에러라면 번호와 제목은?
- ★★ `help:` 가 있다면 그대로 따르면 **통과하나**? 통과한다면 그 처방은 이 자리의 뜻에 맞는가?

### 7. ★★★ `for x in &v` 가 되는 이유 (왜)

- `for x in &v` 가 `&T` 를 내놓는 것은 **문법 규칙**인가, 어딘가에 **적힌 코드**인가? 적힌 코드라면 무엇이 몇 개이고, `&Vec` 쪽 `into_iter` 의 몸통은 무엇인가?

### 8. ★★ 구현은 하나인데 에디션이 가른다 (왜)

- 배열의 `IntoIterator` 구현은 1.53.0 에 **모든 에디션에** 들어갔다. 그런데도 에디션에 따라 결과가 갈리는 자리가 있다면, 그 차이는 **구현이 아니라 어디에** 사는가? **구현을 에디션마다 따로 두지 못한 이유**는?

### 9. ★ `into_iter()` 뒤 원본 — `help:` 의 `clone()` (경계)

- `let it = v.into_iter(); … v.len()` 의 에러 번호는? `help:` 의 `v.clone().into_iter()` 로 고치면 통과하는가 — 그런데 **원본을 남기고 읽기만** 하려는 뜻이면 맞는 처방은?

### 10. ★★ 에디션 경계를 가로질러 (연결)

- 2번에서 찾은 경계를 [34번 주제](../34-closures-fn-fnmut-fnonce-and-move/) (6)의 클로저 포착 변화와 견주면 **겹치는 경계**가 있나? 이런 에디션 차이들의 **공통점**은(컴파일 여부로)?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
