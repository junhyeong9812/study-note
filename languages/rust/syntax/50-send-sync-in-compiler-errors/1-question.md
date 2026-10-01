# rust/syntax/50 — `Send`/`Sync` 가 코드에 나타나는 방식 — 질문

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 열 가지 타입, 두 가지 길 (예측)

```bash
# r50_grid.sh
# 타입마다 두 가지 프로그램을 만들어 던진다
#   send — 값을 move 로 다른 스레드에 넘긴다
#   sync — 값은 main 에 두고 두 스레드가 & 로 함께 본다
S=$'\x1f'
types=(
  "Rc<i32>${S}Rc::new(1)"
  "Arc<i32>${S}Arc::new(1)"
  "Cell<i32>${S}Cell::new(1)"
  "RefCell<i32>${S}RefCell::new(1)"
  "Mutex<i32>${S}Mutex::new(1)"
  "RwLock<i32>${S}RwLock::new(1)"
  "Arc<RefCell<i32>>${S}Arc::new(RefCell::new(1))"
  "Arc<Mutex<i32>>${S}Arc::new(Mutex::new(1))"
  "*const i32${S}&1 as *const i32"
  "MutexGuard<'_, i32>${S}M.lock().unwrap()"
)
hdr='use std::cell::{Cell, RefCell};\nuse std::hint::black_box;\nuse std::rc::Rc;\nuse std::sync::{Arc, Mutex, RwLock};\nuse std::thread;\nstatic M: Mutex<i32> = Mutex::new(0);\nfn main() {\n    let x = %s;\n'
first_error() { grep -m1 '^error' cc.txt; }
printf 'type\tsend\tsync\n'
ok=0; m=0
for spec in "${types[@]}"; do
  ty=${spec%%"$S"*}
  make=${spec#*"$S"}
  { printf "$hdr" "$make"; printf '    thread::scope(|s| {\n        s.spawn(move || { black_box(&x); });\n    });\n}\n'; } > send.rs
  { printf "$hdr" "$make"; printf '    thread::scope(|s| {\n        s.spawn(|| { black_box(&x); });\n        s.spawn(|| { black_box(&x); });\n    });\n}\n'; } > sync.rs
  res=()
  for k in send sync; do
    if rustc --edition 2021 -A unused -o "$k" "$k.rs" 2>cc.txt; then
      res+=(pass); ok=$((ok+1))
    else
      res+=("$(first_error)")
    fi
    m=$((m+1))
  done
  row="$ty${S}${res[0]}${S}${res[1]}"
  cols=$(printf '%s' "$row" | awk -F"$S" '{print NF}')
  [ "$cols" = 3 ] || { echo "column count $cols != 3"; exit 1; }
  printf '%s\n' "$row" | tr "$S" '\t'
done
echo "compiling cells: $ok / $m"
```

- 열 행의 `send`·`sync` 칸을 채워라(`pass` 또는 에러의 첫 줄). 막힌 칸의 문구는 두 열에서 각각 어떻게 다른가? 마지막 줄의 `N / 20` 은?

### 2. ★★★ 구조체 두 겹 안의 필드 (예측)

```rust
// r50_chain.rs
use std::rc::Rc;
use std::thread;

struct Cache {
    hits: u32,
    last: Rc<String>,
}

struct Session {
    user: String,
    cache: Cache,
}

fn total(s: Session) -> usize {
    s.user.len() + s.cache.hits as usize + s.cache.last.len()
}

fn main() {
    let s = Session {
        user: String::from("kim"),
        cache: Cache { hits: 0, last: Rc::new(String::new()) },
    };
    let h = thread::spawn(move || total(s));
    println!("{}", h.join().unwrap());
}
```

- 컴파일되는가? 에러라면 첫 줄이 이름을 대는 타입은 무엇이고, `note:` 줄들은 **어떤 순서로** 어떤 타입·자리를 가리키나? 고칠 자리는 어느 필드인가?

### 3. ★★★ 필드를 하나씩 쓰는 클로저 (예측)

```rust
// r50_chain_fields.rs
use std::rc::Rc;
use std::thread;

struct Cache {
    hits: u32,
    last: Rc<String>,
}

struct Session {
    user: String,
    cache: Cache,
}

fn main() {
    let s = Session {
        user: String::from("kim"),
        cache: Cache { hits: 0, last: Rc::new(String::new()) },
    };
    let h = thread::spawn(move || s.user.len() + s.cache.hits as usize + s.cache.last.len());
    println!("{}", h.join().unwrap());
}
```

```bash
# r50_chain_fields_ed.sh
# 필드를 하나씩 쓰는 클로저 — 에디션마다 「appears within the type」 줄이 몇 개 나오나
for e in 2018 2021; do
  rustc --edition "$e" -o cf r50_chain_fields.rs 2>cc.txt
  rc=$?
  echo "edition $e: rustc exit $rc, first line: $(grep -m1 '^error' cc.txt)"
  echo "edition $e: 'appears within the type' lines: $(grep -c 'appears within the type' cc.txt)"
done
```

- 앞 소스를 2021 로 던지면 에러의 첫 줄은 2번과 같은가? `appears within the type` 줄은 몇 개인가? 뒤 스크립트의 네 줄 출력은?

### 4. ★★ 크기 0 인 필드 하나 (예측)

```rust
// r50_phantom.rs
use std::marker::PhantomData;

fn assert_send<T: Send>() {}
fn assert_sync<T: Sync>() {}

struct Handle {
    id: u64,
    _marker: PhantomData<*const ()>,
}

fn main() {
    assert_send::<Handle>();
    assert_sync::<Handle>();
}
```

- 컴파일되는가? 에러라면 몇 개이고, 첫 줄의 범인 타입과 `note:` 사슬은 무엇인가?

### 5. ★★ 직접 「아니다」라고 쓰기 (예측)

```rust
// r50_negative.rs
struct Handle {
    id: u64,
}

impl !Send for Handle {}

fn main() {
    let h = Handle { id: 1 };
    println!("{}", h.id);
}
```

- 컴파일되는가? 에러라면 번호와, 컴파일러가 대신 쓰라고 권하는 것은?

### 6. ★★ 락 가드를 넘기기 (예측)

```rust
// r50_guard.rs
use std::sync::Mutex;
use std::thread;

static M: Mutex<Vec<i32>> = Mutex::new(Vec::new());

fn main() {
    let g = M.lock().unwrap();
    let h = thread::spawn(move || g.len());
    println!("{}", h.join().unwrap());
}
```

- 컴파일되는가? 에러라면 번호와 첫 줄은? 이 뮤텍스는 `static` 인데, 그 사실이 에러와 어떤 관계인가?

### 7. ★★★ `Arc<RefCell<i32>>` 를 보내는 칸의 문구 (왜)

- 1번에서 `Arc<RefCell<i32>>` 를 **`move` 로 넘기는** 칸이 왜 `sent` 가 아니라 `shared` 문구로 막히나? std 의 「`T` 가 `Sync` 인 것은 무엇과 필요충분인가」와 `Arc` 가 넘긴 뒤에도 남기는 것으로 설명하라.

### 8. ★★ `Cell` 과 `MutexGuard` 의 두 칸 (왜)

- 1번에서 `Cell<i32>` 행과 `MutexGuard` 행의 `send`·`sync` 두 칸은 각각 무엇이고, **왜 그런가**? 「`Send` 가 아니면 `Sync` 도 아니다」는 맞는 말인가 — 이 두 행으로 말하라.

### 9. ★★ 컴파일러가 믿어 주는 선언 (경계)

- `*const u8` 필드를 가진 구조체에 `unsafe impl Send for Wrapper {}` 를 붙이면 컴파일되는가? 되면 **누가 무엇을 보증한 것**인가 — 컴파일러가 확인한 것과 안 한 것을 가르라.

### 10. ★★ 자동 구현의 조건과 원리의 자리 (연결)

- 필드가 `u64`·`String`·`Vec<String>`·`HashMap`·`Arc<Mutex<_>>` 인 구조체는 `impl` 없이 `Send + Sync` 인가? 그 규칙의 이름은? 그리고 두 마커가 **데이터 레이스를 왜 타입 오류로 만드는지**의 원리는 어느 문서가 정본인가 — [41번](../41-rc-arc-shared-ownership-and-weak-cycles/)·[42번](../42-refcell-cell-interior-mutability/)에서 `Rc`·`RefCell` 이 스레드를 넘으려면 각각 무엇으로 바꿨나?

## 실행 환경

★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. 격자는 `bash <파일>.sh`. **외부 크레이트를 하나도 쓰지 않는다.**
★★★ **E0277 을 보면 먼저 물어라** — 「**빠진 것은 `Send` 인가 `Sync` 인가, 그리고 사슬의 가장 안쪽 타입은 어느 필드인가**」.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
