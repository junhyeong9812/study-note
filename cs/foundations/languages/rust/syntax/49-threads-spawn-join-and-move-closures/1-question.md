# rust/syntax/49 — 스레드 `spawn`/`join` 과 `move` 클로저 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. 격자·판 수 탐침은 `bash <파일>.sh`. **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **스레드에 클로저를 넘기면 먼저 물어라** — 「**이 클로저가 품은 것 중 main 의 지역 변수를 가리키는 것이 있나, 있다면 누가 그 변수보다 먼저 끝난다고 약속하나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 열세 가지 넘기기 (예측)

```bash
# r49_grid.sh
# 스레드에 넘기는 값마다 프로그램을 하나씩 만들어 던진다 — 컴파일되나, 안 되면 첫 진단 줄은 무엇인가
S=$'\x1f'
cases=(
  "local Vec, no move${S}let v = vec![1, 2, 3]; let h = thread::spawn(|| v.len()); println!(\"{}\", h.join().unwrap());"
  "local Vec, move${S}let v = vec![1, 2, 3]; let h = thread::spawn(move || v.len()); println!(\"{}\", h.join().unwrap());"
  "local Vec, move, then v.len() in main${S}let v = vec![1, 2, 3]; let h = thread::spawn(move || v.len()); println!(\"{} {}\", h.join().unwrap(), v.len());"
  "Arc clone, move${S}let a = Arc::new(vec![1, 2, 3]); let b = Arc::clone(&a); let h = thread::spawn(move || b.len()); println!(\"{} {}\", h.join().unwrap(), a.len());"
  "Arc, no move${S}let a = Arc::new(vec![1, 2, 3]); let h = thread::spawn(|| a.len()); println!(\"{}\", h.join().unwrap());"
  "local of type &'static str, no move${S}let s: &'static str = \"abc\"; let h = thread::spawn(|| s.len()); println!(\"{}\", h.join().unwrap());"
  "string literal inside the closure${S}let h = thread::spawn(|| \"abc\".len()); println!(\"{}\", h.join().unwrap());"
  "static item, no move${S}let h = thread::spawn(|| V.len()); println!(\"{}\", h.join().unwrap());"
  "reference to local Vec, move${S}let v = vec![1, 2, 3]; let r = &v; let h = thread::spawn(move || r.len()); println!(\"{}\", h.join().unwrap());"
  "scope: shared borrow${S}let v = vec![1, 2, 3]; let n = thread::scope(|s| s.spawn(|| v.len()).join().unwrap()); println!(\"{} {}\", n, v.len());"
  "scope: one mutable borrow${S}let mut v = vec![1, 2, 3]; thread::scope(|s| { s.spawn(|| v.push(4)); }); println!(\"{}\", v.len());"
  "scope: two mutable borrows${S}let mut v = vec![1, 2, 3]; thread::scope(|s| { s.spawn(|| v.push(4)); s.spawn(|| v.push(5)); }); println!(\"{}\", v.len());"
  "scope: shared + mutable${S}let mut v = vec![1, 2, 3]; thread::scope(|s| { s.spawn(|| v.len()); s.spawn(|| v.push(5)); }); println!(\"{}\", v.len());"
)
printf 'case\tcompiles\tfirst diagnostic line / stdout\n'
ok=0; m=0
for spec in "${cases[@]}"; do
  label=${spec%%"$S"*}
  body=${spec#*"$S"}
  printf 'use std::sync::Arc;\nuse std::thread;\nstatic V: [i32; 3] = [1, 2, 3];\nfn main() {\n    %s\n}\n' "$body" > g.rs
  if rustc --edition 2021 -A unused -o g g.rs 2>cc.txt; then
    out=$(./g 2>&1 | tr '\n' ' ')
    row="$label${S}yes${S}stdout: ${out% }"
    ok=$((ok+1))
  else
    row="$label${S}no${S}$(grep -m1 '^error' cc.txt)"
  fi
  cols=$(printf '%s' "$row" | awk -F"$S" '{print NF}')
  [ "$cols" = 3 ] || { echo "column count $cols != 3"; exit 1; }
  printf '%s\n' "$row" | tr "$S" '\t'
  m=$((m+1))
done
echo "compiling cells: $ok / $m"
```

- 열세 행의 `compiles` 칸과, 막힌 행의 **에러 번호**를 채워라. 마지막 줄의 `N / 13` 은?
- ★ 2행과 9행은 둘 다 `move` 를 붙였다. 무엇이 다른가?

### 2. ★★ 같은 소스, 세 에디션 (예측)

```rust
// r49_static_str.rs
use std::thread;

fn main() {
    let s: &'static str = "abc";
    let h = thread::spawn(|| s.len());
    println!("{}", h.join().unwrap());
}
```

```bash
# r49_static_str_ed.sh
# 같은 소스를 세 에디션으로 — 컴파일되나
for e in 2018 2021 2024; do
  if rustc --edition "$e" -o s_$e r49_static_str.rs 2>cc.txt; then
    echo "edition $e: compiles, stdout $(./s_$e)"
  else
    echo "edition $e: $(grep -m1 '^error' cc.txt)"
  fi
done
```

- 스크립트의 세 줄 출력은? 에디션마다 갈린다면 클로저가 **무엇을** 잡았기 때문인가?

### 3. ★★ 참조를 옮긴 클로저 (예측)

```rust
// r49_e0597.rs
use std::thread;

fn main() {
    let v = vec![1, 2, 3];
    let r = &v;
    let h = thread::spawn(move || r.len());
    println!("{}", h.join().unwrap());
}
```

- 컴파일되는가? 에러라면 번호와, 진단이 `v` 에 요구하는 **수명**은?

### 4. ★★★ 자식 스레드 셋의 끝 (예측)

```rust
// r49_join.rs
use std::thread;

fn main() {
    let ok = thread::spawn(|| 40 + 2).join();
    println!("[1] join is_ok {}  value {:?}", ok.is_ok(), ok.as_ref().ok());

    let bad = thread::spawn(|| {
        let v: Vec<i32> = Vec::new();
        v[0]
    })
    .join();
    println!("[2] join is_err {}", bad.is_err());
    let p = bad.unwrap_err();
    println!("[3] payload String {}  &str {}  text {:?}", p.is::<String>(), p.is::<&str>(), p.downcast_ref::<String>());

    let lit = thread::spawn(|| -> i32 { panic!("fixed text") }).join();
    let p = lit.unwrap_err();
    println!("[4] payload String {}  &str {}  text {:?}", p.is::<String>(), p.is::<&str>(), p.downcast_ref::<&str>());
    println!("[5] main still running");
}
```

- 표준 출력의 다섯 줄은? 표준 오류에는 무엇이 몇 번 찍히나, 종료 코드는? `[3]` 과 `[4]` 의 패닉 값은 각각 어떤 타입인가?

### 5. ★★ 핸들을 버린 자식 (예측)

```rust
// r49_detach.rs
use std::env;
use std::thread;
use std::time::Duration;

fn main() {
    let wait_ms: u64 = env::args().nth(1).unwrap().parse().unwrap();
    let _ = thread::spawn(|| {
        thread::sleep(Duration::from_millis(50));
        println!("child line");
    });
    thread::sleep(Duration::from_millis(wait_ms));
    println!("main line");
}
```

```bash
# r49_detach.sh
# JoinHandle 을 버린 자식 — main 이 먼저 끝나는 판과 늦게 끝나는 판을 20번씩
rustc --edition 2021 -o r49_detach r49_detach.rs || exit 1
for w in 0 300; do
  child=0; mainl=0
  for i in $(seq 20); do
    out=$(./r49_detach "$w")
    case $out in *"child line"*) child=$((child+1)) ;; esac
    case $out in *"main line"*) mainl=$((mainl+1)) ;; esac
  done
  echo "main waits ${w}ms: runs with child line $child / 20, runs with main line $mainl / 20"
done
```

- 두 줄의 `N / 20` 은 각각 얼마로 예상하나? 이 숫자는 **보장**인가?

### 6. ★★★ 스코프 안의 가변 빌림 (예측)

```rust
// r49_scope.rs
use std::thread;

fn main() {
    let mut v = vec![1, 2, 3];
    let total: i32 = v.iter().sum();
    thread::scope(|s| {
        s.spawn(|| {
            thread::sleep(std::time::Duration::from_millis(100));
            v.push(total);
            eprintln!("[child] pushed");
        });
        eprintln!("[main] end of scope closure");
    });
    eprintln!("[main] after scope, v = {:?}", v);
}
```

- 세 줄은 **어떤 순서로** 찍히나? `v` 의 마지막 값은? 이 스레드는 왜 `move` 없이 `v` 를 고칠 수 있나?

### 7. ★★★ `spawn` 은 왜 `'static` 을 요구하나 (왜)

- `thread::spawn` 의 시그니처는 `F` 와 `T` 에 각각 무엇을 요구하나? std 는 `'static` 의 이유를 무엇이라고 쓰나? `move` 는 그 요구를 **어떻게** 맞추고, 무엇은 못 맞추나?

### 8. ★★★ `thread::scope` 가 푸는 것과 안 푸는 것 (경계)

- 스코프 스레드의 클로저는 `'static` 대신 무엇을 요구하나? 그 대가로 `scope` 는 무엇을 약속하나? 두 스코프 스레드가 같은 `Vec` 을 가변으로 빌리면 어떻게 되나 — 1번 격자의 어느 행인가?

### 9. ★★ 패닉이 가는 곳 — `spawn` 대 `scope` (경계)

- `spawn` 한 스레드의 패닉과 `thread::scope` 안의 스레드의 패닉은 main 에 각각 어떻게 도착하나? `scope` 안에서 패닉을 `Result` 로 받고 싶으면 무엇을 하나?

### 10. ★★ detach 된 스레드의 일은 언제 사라지나 (왜)

- `JoinHandle` 을 버리면 무엇이 되나? main 이 끝날 때 아직 도는 스레드는 어떻게 되나 — std 모듈 문서는 무엇이라고 쓰나? 5번의 판 수 탐침은 무엇을 **못** 보나?

### 11. ★ 스레드 둘이 같은 값을 쓰려면 (연결)

- 1번 3행(E0382)을 고쳐 main 과 스레드가 **둘 다** `v` 를 읽게 하는 방법 둘은? [41번 주제](../41-rc-arc-shared-ownership-and-weak-cycles/)에서 `Rc` 로 같은 일을 하면 무엇이 막았나 — 그 에러는 `spawn` 시그니처의 **어느 경계**에서 오나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
