# rust/rust-patterns/02 — Newtype 패턴 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 2 는 2번 자리에 들어가고, 길이 7 · 첫 원소 1 · 7 은 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
2 삽입 후:   [1, 1, 2, 3, 4, 5, 9]
길이: 7, 첫 번째: 1
contains 7: false
```

**왜 그런가**
- `new` 가 `[3, 1, 4, 1, 5, 9]` 를 정렬해 `[1, 1, 3, 4, 5, 9]` 로 감싼다.
- `binary_search(&2)` 는 2 를 못 찾으므로, 넣으면 정렬이 유지되는 자리 `Err(2)` 를 돌려준다 — `1, 1` 뒤, `3` 앞이다.
- `unwrap_or_else(|p| p)` 가 그 `2` 를 꺼내고, `self.0.insert(2, 2)` 로 끼운다.
- `&*sorted` 는 `deref` 를 거친 `&[T]` 라 슬라이스 꼴로 찍힌다.
- `len` · `[0]` · `contains` 는 `SortedVec` 에 없어서 자동 역참조로 슬라이스의 것이 불린다.
- 근거: 2-summary 「동작 방식 (5)」.

### 2. `Err` 갈래로 오류 문장이 찍히고, 공백만 넣어도 거절된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
에러: 유효하지 않은 이메일: invalid
빈 문자열: Err("빈 문자열은 허용되지 않습니다")
true
```

**왜 그런가**
- `"invalid"` 에는 `'@'` 가 없어 `Err(format!("유효하지 않은 이메일: {}", value))` 가 오고, `match` 의 `Err(e)` 갈래가 `에러: ` 를 앞에 붙여 찍는다.
- `Result` 를 `{:?}` 로 찍으면 `Err(...)` 로 감싸이고, 안의 `String` 은 `Debug` 꼴이라 큰따옴표가 붙는다.
- `"   "` 은 `trim()` 하면 빈 문자열이 되므로 `Err` — `is_err()` 는 `true` 다.
- 근거: 2-summary 「동작 방식 (4)」.

### 3. 두 줄이 찍히고, ID 에는 타입 이름이 붙는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
주문 OrderId(1001): 29900원
주문 OrderId(1002): 15000원
```

**왜 그런가**
- `find_orders_by_user` 는 주문 두 개를 담은 `Vec` 을 돌려주므로 두 줄이다.
- `derive(Debug)` 는 튜플 구조체를 `타입이름(값)` 꼴로 찍는다 — 숫자만 나오지 않는다.
- `{:.0}` 은 소수 자리를 없애 `29900.0` 을 `29900` 꼴로 만든다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 8」.

### 4. 컴파일러는 안의 값이 아니라 구조체 이름으로 타입을 가르기 때문이다

- `Meters` 와 `Kilometers` 는 이름이 다른 두 구조체라 서로 다른 타입이다. 안에 든 것이 둘 다 `f64` 라는 사실은 타입을 같게 만들지 않는다.
- 그래서 `Meters` 를 기대하는 자리에 `Kilometers` 값을 두면 타입 불일치로 거절된다.
- 이 막힘은 **만들 때(컴파일 때)** 일어난다 — 잘못된 프로그램은 실행 파일이 되지 않는다.
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (6)」.

### 5. 「`Email` 이면 이미 검사를 통과했다」고 타입이 말해 주기 때문이다

- 검사를 `new` 한 곳에 두고 그 길로만 만들게 하면, `Email` 타입의 값은 모두 그 검사를 통과한 것이다 — 이것이 불변 조건이다.
- 그러니 `Email` 을 받는 함수는 다시 검사할 필요가 없다.
- `Result<Self, String>` 을 돌려주는 까닭은 검사가 **실패할 수 있음**을 타입에 드러내고, 실패하면 값 대신 이유(오류 문자열)를 주기 위해서다. 부르는 쪽은 `match` 나 `unwrap` 으로 실패를 다뤄야 한다.
- 근거: 2-summary 「동작 방식 (4)」.

### 6. 같은 모듈이면 컴파일된다 — 모듈로 떼고 필드를 닫아야 한다

- Rust 의 비공개는 모듈 단위다. 예제는 모든 코드가 한 모듈에 있으므로 `main` 에서 `Email("bad".to_string())` 을 바로 써도 컴파일된다 — 검사를 건너뛴 `Email` 이 생긴다.
- 원본 주석의 「생성자에서만 만들 수 있게 → 불변 조건 강제」는 이 예제 구조에서는 성립하지 않는다.
- 지키려면 `Email` 을 따로 모듈에 두고, 구조체는 `pub struct Email(String);` 처럼 열되 필드는 비공개로 남긴다. 그러면 모듈 바깥에서는 `Email::new` 말고 만들 길이 없다.
- 근거: 2-summary 「어디서 틀리나 3」 · 「구현 세부사항 대 언어 보장」.

### 7. 읽기 메서드만 자동 역참조로 열리고, 가변 조작은 열리지 않는다

- `sorted.len()` 을 부르면 컴파일러는 `SortedVec` 의 메서드를 먼저 찾고, 없으므로 `Deref` 의 `Target` 인 `[T]` 에서 `len` 을 찾아 부른다.
- `deref` 는 `&[T]`(읽기 참조)만 돌려주고 `DerefMut` 는 구현하지 않았으므로 `sort` 같은 가변 메서드는 이 길로 닿지 않는다. `push` 는 `Vec` 의 메서드라 `[T]` 로 풀리는 길로는 찾을 수 없다.
- 그래서 원소는 `SortedVec::insert` 로만 들어가고 정렬 상태가 유지된다.
- 남용을 경계하는 까닭: 메서드가 어디서 왔는지 읽기 어렵고, `Target` · `DerefMut` 선택에 따라 막고 싶던 조작까지 열려 불변 조건이 깨질 수 있다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 8. `Copy` 를 빼면 둘째 호출이 컴파일 에러가 된다

- `to_meters(self)` 는 `self` 를 값으로 받는다. `Copy` 가 있으면 복사되어 `distance` 가 남지만, 없으면 `distance` 가 이동해 버린다.
- 그래서 다음 줄의 `distance.to_miles()` 는 이미 이동한 값을 쓰려는 것이 되어 컴파일되지 않는다.
- `Email` 은 `String` 을 감쌌고, `Copy` 는 안의 필드가 모두 `Copy` 여야 달 수 있는데 `String` 은 `Copy` 가 아니다.
- 근거: 2-summary 「동작 방식 (2)」 · 「문법 — 형태와 규칙」 · 「어디서 틀리나 7」.

### 9. 타입 별칭은 섞임을 막지 못한다 — 이름만 하나 더 붙기 때문이다

- `type Meters = f64;` 와 `type Kilometers = f64;` 는 둘 다 `f64` 그 자체라 서로 자유롭게 섞인다. 새 타입이 생기지 않는다.
- 섞임을 막으려면 `struct Meters(f64);` 처럼 새 구조체로 감싸는 newtype 이어야 한다.
- 뜻이 다른 값을 가르거나 불변 조건을 지키려면 newtype, 긴 타입 이름을 줄이는 것뿐이면 타입 별칭을 고른다.
- 근거: 2-summary 「어디서 틀리나 2」 · 「언제 쓰고 언제 안 쓰나」.

### 10. 타입을 가르는 일이 컴파일 때 끝나기 때문이다 — 검증 비용은 따로다

- 타입이 맞는지 따지는 일은 컴파일 단계에서 끝나므로 실행 때 「이 값이 `Meters` 인가」를 확인하는 일이 없다. 필드가 하나뿐이라 실행 때 다룰 것은 안의 값뿐이다 — 원본 팁이 zero-cost 라 부르는 까닭이다.
- 다만 메모리 배치가 안쪽 타입과 같다는 것을 언어가 약속하는 것은 `#[repr(transparent)]` 를 달 때이고, 그 밖의 실행 성능은 컴파일러 최적화가 만든다 (확인 필요).
- `Email::new` 의 `contains` 검사는 newtype 자체의 비용이 아니라 내가 넣은 검증 코드의 비용이다 — 만들 때 한 번 치른다.
- 근거: 2-summary 「동작 방식 (6)」 · 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. 단위 · ID · 검증 · 정렬 벡터를 newtype 으로 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 단위 타입 셋 + 파생 | `#[derive(Debug, Clone, Copy, PartialEq)] struct Meters(f64);` · `Kilometers` · `Miles` |
| 2. 미터 → 킬로미터 | `Meters::to_kilometers` 의 `Kilometers(self.0 / 1000.0)` |
| 3. 킬로미터 → 미터 · 마일 | `Kilometers::to_meters` 의 `Meters(self.0 * 1000.0)` · `to_miles` 의 `Miles(self.0 * 0.621371)` |
| 4. 단위별 찍는 꼴 | `impl fmt::Display for Meters/Kilometers/Miles` 의 `write!(f, "{:.1}m" / "{:.2}km" / "{:.2}mi", self.0)` |
| 5. ID 타입 둘 + 파생 | `#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)] struct UserId(u64);` · `OrderId(u64)` |
| 6. 사용자의 주문 두 개 | `find_orders_by_user` 의 `vec![Order::new(OrderId(1001), user_id, 29900.0), Order::new(OrderId(1002), user_id, 15000.0)]` |
| 7. 이메일 검사 생성자 | `Email::new` 의 `value.contains('@') && value.contains('.')` → `Ok(Email(...))` / `Err(format!(...))` |
| 8. 이메일 읽기 · 찍기 | `Email::as_str` 의 `&self.0` · `impl fmt::Display for Email` |
| 9. 빈 문자열 거절 | `NonEmptyString::new` 의 `value.trim().is_empty()` 와 `Ok(NonEmptyString(value.to_string()))` · `as_str` |
| 10. 만들 때 정렬 | `SortedVec::new` 의 `items.sort(); SortedVec(items)` |
| 11. 정렬 유지 삽입 | `SortedVec::insert` 의 `binary_search(&item).unwrap_or_else(\|p\| p)` 와 `self.0.insert(pos, item)` |
| 12. 슬라이스로 역참조 | `impl<T: Ord> Deref for SortedVec<T>` 의 `type Target = [T];` · `fn deref(&self) -> &[T] { &self.0 }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-patterns/reference/newtype-pattern.rs`

```rust
// [패턴 & 관용구] Newtype 패턴
// 설명: 뉴타입 패턴으로 기존 타입을 래핑하여 타입 안전성 확보. 단위 혼동 방지, 의미 부여
// 팁: Newtype은 런타임 비용이 없다(zero-cost). 같은 원시 타입을 여러 의미로 쓸 때 반드시 사용하자. Deref를 구현하면 내부 타입의 메서드를 투명하게 사용할 수 있지만, 남용하면 혼란을 줄 수 있다. 유효성 검사를 생성자에 넣으면 불변 조건을 보장할 수 있다.

// === Newtype 패턴: 타입으로 의미와 안전성 부여 ===
// Display 포매팅
use std::fmt;

// 1. 기본 Newtype: 같은 타입이지만 다른 의미
// 미터 단위
#[derive(Debug, Clone, Copy, PartialEq)]
struct Meters(f64);

// 킬로미터 단위
#[derive(Debug, Clone, Copy, PartialEq)]
struct Kilometers(f64);

// 마일 단위
#[derive(Debug, Clone, Copy, PartialEq)]
struct Miles(f64);

// 단위 변환 구현
impl Meters {
    fn to_kilometers(self) -> Kilometers {
        // 1km = 1000m
        Kilometers(self.0 / 1000.0)
    }
}

impl Kilometers {
    fn to_meters(self) -> Meters {
        Meters(self.0 * 1000.0)
    }

    fn to_miles(self) -> Miles {
        // 1km = 0.621371mi
        Miles(self.0 * 0.621371)
    }
}

// Meters용 Display
impl fmt::Display for Meters {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:.1}m", self.0)
    }
}

// Kilometers용 Display
impl fmt::Display for Kilometers {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:.2}km", self.0)
    }
}

// Miles용 Display
impl fmt::Display for Miles {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:.2}mi", self.0)
    }
}

// 2. ID 타입 구분: UserId와 OrderId를 혼동 방지
// 사용자 ID
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct UserId(u64);

// 주문 ID (같은 u64이지만 다른 타입 -> 컴파일러가 혼용 차단)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct OrderId(u64);

// 주문 정보
#[derive(Debug)]
struct Order {
    id: OrderId,
    user_id: UserId,
    amount: f64,
}

impl Order {
    fn new(id: OrderId, user_id: UserId, amount: f64) -> Self {
        Order { id, user_id, amount }
    }
}

// 함수 시그니처에서 타입이 의미를 전달
// (UserId 자리에 OrderId를 넣으면 컴파일 에러)
fn find_orders_by_user(user_id: UserId) -> Vec<Order> {
    // 실제로는 DB 조회
    vec![
        Order::new(OrderId(1001), user_id, 29900.0),
        Order::new(OrderId(1002), user_id, 15000.0),
    ]
}

// 3. 유효성 검사가 포함된 Newtype
// 이메일: 생성 시 검증 -> 이후로는 항상 유효 보장
#[derive(Debug, Clone, PartialEq)]
struct Email(String);

impl Email {
    // 생성자에서만 만들 수 있게 -> 불변 조건 강제
    fn new(value: &str) -> Result<Self, String> {
        // 매우 단순한 검증 (실무는 더 정교)
        if value.contains('@') && value.contains('.') {
            Ok(Email(value.to_string()))
        } else {
            Err(format!("유효하지 않은 이메일: {}", value))
        }
    }

    // 내부 문자열 접근 (읽기 전용)
    fn as_str(&self) -> &str {
        &self.0
    }
}

// 이메일 출력
impl fmt::Display for Email {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

// 비어있지 않은 문자열 보장 타입
#[derive(Debug, Clone, PartialEq)]
struct NonEmptyString(String);

impl NonEmptyString {
    fn new(value: &str) -> Result<Self, String> {
        // 공백 trim 후 비어 있으면 실패
        if value.trim().is_empty() {
            Err("빈 문자열은 허용되지 않습니다".to_string())
        } else {
            Ok(NonEmptyString(value.to_string()))
        }
    }

    fn as_str(&self) -> &str {
        &self.0
    }
}

// 4. Deref를 활용한 투명한 래핑
// Deref 트레이트 - 자동 역참조용
use std::ops::Deref;

// 항상 정렬되어 있는 벡터 (불변 조건: 정렬 상태 유지)
#[derive(Debug)]
struct SortedVec<T: Ord>(Vec<T>);

impl<T: Ord> SortedVec<T> {
    fn new(mut items: Vec<T>) -> Self {
        // 생성 시 정렬
        items.sort();
        SortedVec(items)
    }

    // 정렬을 유지하며 삽입 (binary_search로 위치 찾음)
    fn insert(&mut self, item: T) {
        let pos = self.0.binary_search(&item).unwrap_or_else(|p| p);
        self.0.insert(pos, item);
    }
}

// Deref 구현: SortedVec를 슬라이스처럼 다룰 수 있음
impl<T: Ord> Deref for SortedVec<T> {
    type Target = [T];
    fn deref(&self) -> &[T] {
        &self.0
    }
}

fn main() {
    println!("=== 1. 단위 구분 ===");
    // 마라톤 거리를 km로 표현
    let distance = Kilometers(42.195);
    println!("마라톤: {}", distance);
    println!("미터:   {}", distance.to_meters());
    println!("마일:   {}", distance.to_miles());

    // 컴파일 에러: Meters와 Kilometers를 혼동할 수 없음
    // let wrong: Meters = Kilometers(5.0); // 타입 불일치!

    println!("\n=== 2. ID 타입 구분 ===");
    // UserId 만들고 조회
    let user = UserId(42);
    let orders = find_orders_by_user(user);
    for order in &orders {
        println!("주문 {:?}: {:.0}원", order.id, order.amount);
    }
    // 컴파일 에러: OrderId를 UserId 자리에 넣을 수 없음
    // find_orders_by_user(OrderId(1)); // 타입 불일치!

    println!("\n=== 3. 유효성 검사 Newtype ===");
    // 유효한 이메일은 Ok
    match Email::new("user@example.com") {
        Ok(email) => println!("유효한 이메일: {}", email),
        Err(e) => println!("에러: {}", e),
    }
    // 유효하지 않으면 Err
    match Email::new("invalid") {
        Ok(email) => println!("유효한 이메일: {}", email),
        Err(e) => println!("에러: {}", e),
    }

    // NonEmptyString 사용
    let name = NonEmptyString::new("Alice").unwrap();
    println!("이름: {}", name.as_str());
    println!("빈 문자열: {:?}", NonEmptyString::new(""));

    println!("\n=== 4. Deref를 통한 투명 래핑 ===");
    // 무순서 입력 -> 자동 정렬
    let mut sorted = SortedVec::new(vec![3, 1, 4, 1, 5, 9]);
    println!("정렬된 벡터: {:?}", &*sorted);
    // 정렬을 유지하며 삽입
    sorted.insert(2);
    println!("2 삽입 후:   {:?}", &*sorted);
    // Deref 덕분에 슬라이스 메서드 사용 가능
    println!("길이: {}, 첫 번째: {}", sorted.len(), sorted[0]);
    println!("contains 7: {}", sorted.contains(&7));
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 단위 · ID 는 감싸기만 해도 타입이 갈린다 — `main` 의 주석 두 줄을 풀면 컴파일러가 거절하는 것이 이 패턴의 핵심 효과다.
- 변환 메서드가 `self` 를 값으로 받으므로 `Copy` 파생이 있어야 `distance` 를 여러 번 쓸 수 있다.
- 검증 newtype 은 `Result` 를 돌려주는 `new` 와 읽기 전용 `as_str` 의 짝이다. 한 모듈 안에서는 `Email(...)` 직접 생성을 막지 못한다는 점을 기억한다.
- `NonEmptyString` 은 `trim` 으로 검사만 하고 원래 입력을 저장한다.
- `binary_search` 의 `Ok` · `Err` 어느 쪽이든 위치 하나를 꺼내 쓰는 것이 `unwrap_or_else(|p| p)` 의 일이다.
- `Deref` 의 `Target` 을 `[T]` 로 두고 `DerefMut` 를 빼서, 읽기 메서드만 열고 정렬을 깨는 조작은 닫았다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
