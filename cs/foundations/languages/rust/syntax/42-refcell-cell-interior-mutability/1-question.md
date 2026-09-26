# rust/syntax/42 — `RefCell`/`Cell` 내부 가변성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. 격자는 `bash <파일>.sh`(에디션 격자는 스크립트가 2021·2024 를 돈다). **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **`RefCell` 을 보면 먼저 물어라** — 「**지금 살아 있는 가드는 몇 개이고, 각각 언제 `Drop` 되나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 열두 가지 빌림 조합 (예측)

```bash
# r42_grid.sh
# RefCell 빌림 조합마다 프로그램을 하나씩 만들어 던진다 — 통과인가, 패닉이면 문구는 무엇인가
T=$'\t'
cases=(
  'shared + shared (both held)|let a = c.borrow(); let b = c.borrow(); let _ = (a.len(), b.len());'
  'shared held + mut|let a = c.borrow(); let mut b = c.borrow_mut(); b.push(a.len());'
  'mut held + shared|let mut a = c.borrow_mut(); let b = c.borrow(); a.push(b.len());'
  'mut held + mut|let mut a = c.borrow_mut(); let mut b = c.borrow_mut(); a.push(1); b.push(2);'
  'mut in inner block, then mut|{ let mut a = c.borrow_mut(); a.push(1); } let mut b = c.borrow_mut(); b.push(2);'
  'mut, drop(guard), then mut|let mut a = c.borrow_mut(); a.push(1); drop(a); let mut b = c.borrow_mut(); b.push(2);'
  'two statements, temporaries only|c.borrow_mut().push(1); c.borrow_mut().push(2);'
  'one statement: mut receiver + shared argument|c.borrow_mut().push(c.borrow().len());'
  'one statement: value first, then mut|let n = c.borrow().len(); c.borrow_mut().push(n);'
  'match on c.borrow() + mut in arm|match c.borrow().len() { n => c.borrow_mut().push(n) }; println!();'
  'if condition c.borrow() + mut in body|if c.borrow().len() < 9 { c.borrow_mut().push(0); }'
  'mut held, try_borrow_mut|let _a = c.borrow_mut(); let r = c.try_borrow_mut(); println!("try_borrow_mut is_err {}", r.is_err());'
)
printf 'case\tresult\n'
p=0; m=0
for spec in "${cases[@]}"; do
  label=${spec%%|*}
  body=${spec#*|}
  printf 'use std::cell::RefCell;\nfn main() {\n    let c = RefCell::new(vec![1, 2, 3]);\n    %s\n}\n' "$body" > g.rs
  rustc --edition 2021 -A unused -o g g.rs 2>cc.txt || { echo "compile failed: $label"; cat cc.txt; exit 1; }
  if ./g >/dev/null 2>err.txt; then
    res=pass
  else
    res="panic: $(sed -n 3p err.txt)"
    p=$((p+1))
  fi
  row="$label${T}$res"
  cols=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
  [ "$cols" = 2 ] || { echo "column count $cols != 2"; exit 1; }
  printf '%s\n' "$row"
  m=$((m+1))
done
echo "panic cells: $p / $m"
```

- 열두 행의 `result` 칸을 채워라(`pass` 또는 `panic:` 뒤의 문구). 마지막 줄의 `N / 12` 는?
- ★ 7행과 8행, 10행과 11행은 각각 무엇이 다른가?

### 2. ★★ `if let` 두 소스 × 두 에디션 (예측)

```bash
# r42_iflet.sh
# if let 의 조건식 임시값(Ref 가드)은 어느 갈래까지 사는가 — 두 소스 × 두 에디션
cat > then.rs <<'RS'
use std::cell::RefCell;
fn main() {
    let c = RefCell::new(vec![1, 2, 3]);
    if let Some(n) = c.borrow().first().copied() {
        c.borrow_mut().push(n);
    }
    println!("{:?}", c.borrow());
}
RS
cat > else.rs <<'RS'
use std::cell::RefCell;
fn main() {
    let c = RefCell::new(vec![1, 2, 3]);
    if let Some(n) = c.borrow().get(9).copied() {
        println!("{n}");
    } else {
        c.borrow_mut().push(0);
    }
    println!("{:?}", c.borrow());
}
RS
printf 'source\tedition\tresult\n'
p=0; m=0
for src in then else; do
  for ed in 2021 2024; do
    rustc --edition $ed -o "$src$ed" "$src.rs" || exit 1
    if out=$(./"$src$ed" 2>err.txt); then
      res="pass $out"
    else
      res="panic: $(sed -n 3p err.txt)"; p=$((p+1))
    fi
    row=$(printf '%s\t%s\t%s' "$src" "$ed" "$res")
    cols=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
    [ "$cols" = 3 ] || { echo "column count $cols != 3"; exit 1; }
    printf '%s\n' "$row"
    m=$((m+1))
  done
done
echo "panic cells: $p / $m"
```

- 네 행의 `result` 는? 마지막 줄의 `N / 4` 는?

### 3. ★★★ 같은 모양, 두 가지 빌림 (예측)

```rust
// r42_pair_ref.rs
fn main() {
    let mut v = vec![1, 2, 3];
    let a = &v;
    let b = &mut v;
    b.push(a.len());
}
```

```rust
// r42_pair_cell.rs
use std::cell::RefCell;

fn main() {
    let v = RefCell::new(vec![1, 2, 3]);
    let a = v.borrow();
    println!("[1] first borrow taken, len {}", a.len());
    let mut b = v.borrow_mut();
    println!("[2] second borrow taken");
    b.push(a.len());
}
```

- 각각 컴파일되는가? 에러라면 번호는? 실행된다면 **표준 출력과 표준 오류에 각각 무엇이** 나오고 종료 코드는?

### 4. ★★ 물어보고 빌리기 (예측)

```rust
// r42_try.rs
use std::cell::RefCell;

fn main() {
    let c = RefCell::new(String::from("x"));
    let held = c.borrow();
    match c.try_borrow_mut() {
        Ok(_) => println!("[1] Ok"),
        Err(e) => println!("[1] Err  Debug {:?}  Display {}", e, e),
    }
    drop(held);
    match c.try_borrow_mut() {
        Ok(mut g) => {
            g.push('y');
            println!("[2] Ok  now {}", g);
        }
        Err(e) => println!("[2] Err {:?}", e),
    }
    let m = c.borrow_mut();
    println!("[3] try_borrow while mut held  is_err {}", c.try_borrow().is_err());
    drop(m);
}
```

- 세 줄의 출력은? `[1]` 의 `Debug` 와 `Display` 는 각각 무엇인가?

### 5. ★★ 참조를 주지 않는 칸 (예측)

```rust
// r42_cell.rs
use std::cell::Cell;

struct Counter {
    hits: Cell<u32>,
}

impl Counter {
    fn touch(&self) {
        self.hits.set(self.hits.get() + 1);
    }
}

fn main() {
    let k = Counter { hits: Cell::new(0) };
    let r1 = &k;
    let r2 = &k;
    r1.touch();
    r2.touch();
    k.touch();
    println!("hits {}", k.hits.get());

    let name = Cell::new(String::from("a"));
    let old = name.replace(String::from("b"));
    let now = name.take();
    println!("old {old:?}  taken {now:?}  left {:?}", name.into_inner());
}
```

```rust
// r42_cell_get.rs
use std::cell::Cell;

fn main() {
    let name = Cell::new(String::from("a"));
    let s = name.get();
    println!("{s}");
}
```

- 앞 소스의 두 줄 출력은? 뒤 소스는 컴파일되는가 — 안 된다면 에러 번호와 **만족되지 않은 경계**는?

### 6. ★★ 스레드끼리 나눈 `RefCell` (예측)

```rust
// r42_sync.rs
use std::cell::RefCell;
use std::sync::Arc;
use std::thread;

fn main() {
    let shared = Arc::new(RefCell::new(0));
    let s2 = Arc::clone(&shared);
    let h = thread::spawn(move || {
        *s2.borrow_mut() += 1;
    });
    h.join().unwrap();
    println!("{}", shared.borrow());
}
```

- 컴파일되는가? 에러라면 번호와, 컴파일러가 권하는 **대신 쓸 타입**은?

### 7. ★★★ 빌림 검사를 실행 중으로 옮기면 남는 것 (왜)

- 3번의 두 소스는 **같은 규칙**을 어겼다. 무엇이 같고, 무엇이 달라졌나? 「`RefCell` 로 바꾸면 에러가 사라진다」가 왜 해결이 아닌가 — **실행하지 않은 경로**에 대해서는 무엇이 달라지나?

### 8. ★★★ `match` 와 `if` 의 임시값 (왜)

- 1번에서 `match c.borrow().len() { … }` 와 `if c.borrow().len() < 9 { … }` 는 왜 결과가 갈리나? Reference 는 각각의 임시값을 어디까지 살려 두나? 2024 에디션이 `if let` 에서 바꾼 것은 **어느 갈래**인가?

### 9. ★★ 패닉 문구는 누구의 것인가 (경계)

- 1.92 에서 `borrow_mut` 가 실패하면 무슨 문구로 패닉하나? `already borrowed: BorrowMutError` 라는 형식은 어디서 오는 것이고 지금도 나오나? std 소스에 있는 문구 **넷** 중 이 툴체인에서 안 나오는 둘은 무엇이 켜야 나오나 — `-C debug-assertions` 로 되나?

### 10. ★★ `Cell` 과 `RefCell` 중 무엇을 (경계)

- `&self` 메서드에서 호출 횟수를 세는 칸과, 여러 곳이 같은 `Vec` 에 넣는 칸은 각각 어느 것이 알맞나? `Cell<String>` 에서 값을 **꺼내려면** 무엇을 쓰나?

### 11. ★ `Rc<RefCell<T>>` 와 그 스레드 판 (연결)

- [41번 주제](../41-rc-arc-shared-ownership-and-weak-cycles/)의 `Rc` 와 이 편의 `RefCell` 은 각각 무엇을 맡나? 스레드를 넘으면 두 자리가 각각 무엇으로 바뀌나 — 6번의 컴파일러와 std `cell` 모듈 문서는 `RefCell` 의 `Sync` 판을 무엇이라고 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
