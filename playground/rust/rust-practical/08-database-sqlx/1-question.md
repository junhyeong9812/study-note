# rust/rust-practical/08 — SQLx 데이터베이스 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 시드 DB 에 Diana 를 만들고 Bob 을 비활성화하면 (예측)

```rust
// 질문용 발췌
let mut db = Database::new();   // 유저 id 1~3, next_user_id = 4
let new_user = db.create_user(CreateUserDto { name: "Diana".into(), email: "diana@example.com".into() });
let updated = db.update_user_status(2, false).unwrap();
println!("{:?}", new_user);
println!("{:?}", updated);
```

- 두 `println!` 이 찍는 두 줄은 각각 어떤 모습인가?

### 2. 유저별 주문 요약에서 주문 없는 유저 (예측)

```rust
// 질문용 발췌 — users: Alice(1) · Bob(2) · Charlie(3) · Diana(4)
// orders: (user 1, 1500000) · (user 1, 50000) · (user 2, 150000)
let summary = db.user_order_summary();
for (name, count, total) in &summary {
    println!("    {}: {}건, {:.0}원", name, count, total);
}
```

- 이 반복은 몇 줄을 찍고, Alice 와 Charlie 의 줄은 각각 어떤 모습인가?

### 3. 커밋 한 번, 롤백 한 번 (예측)

```rust
// 질문용 발췌 — 시작 시 유저 4명
db.begin_transaction();
db.create_user(CreateUserDto { name: "Eve".into(), email: "eve@example.com".into() });
db.commit();
println!("  유저 수: {}", db.users.len());
db.begin_transaction();
db.delete_user(1).unwrap();
println!("  삭제 후 유저 수: {}", db.users.len());
db.rollback();
println!("  롤백 후 유저 수: {}", db.users.len());
```

- 세 줄에 찍히는 유저 수는 각각 얼마이고, `[TX]` 로 시작하는 줄은 몇 개 끼어드나?

### 4. sqlx 가 SQL 을 매크로로 받는 까닭 (왜)

- `query_as!` · `query!` 를 매크로로 두면 일반 함수에 SQL 문자열을 넘길 때보다 무엇을 얻나?

### 5. 커넥션 풀을 시작 때 한 번만 만드는 까닭 (왜)

- `PgPool` 을 요청마다 새로 만들지 않고 시작 때 한 번 만들어 공유하는 까닭은 무엇인가?

### 6. 롤백이 되돌리는 범위 (경계)

- 예제의 트랜잭션 안에서 유저를 하나 만들고 롤백한 뒤 다시 유저를 만들면, 새 유저의 `id` 는 롤백 전에 만든 유저의 `id` 와 같은가?

### 7. 없는 id 를 지우려 할 때 (경계)

- `delete_user(99)` 는 무엇을 돌려주고, 그렇게 판단하는 근거는 코드의 무엇인가?

### 8. 시뮬레이션의 SQL 주석과 컴파일 타임 검증 (경계)

- `find_user_by_id` 위 주석의 SQL 에 오타가 있으면 이 예제의 빌드는 그것을 잡아 주나?

### 9. Repository 와 빌림 규칙 (연결)

- `let mut repo = UserRepository::new(&mut db);` 뒤에 `repo` 를 아직 쓰는 동안 `db.users.len()` 을 직접 부르면 왜 문제가 되나?

## 실습

### 실습 1. 인메모리 DB 로 sqlx 패턴 흉내 내기

**만들 것** — `Vec` 으로 만든 가상 DB 위에 CRUD · 조인 · 집계 · 트랜잭션 · Repository 를 구현하고, `main` 에서 네 단계로 시연한 뒤 실제 sqlx 코드 패턴을 문자열로 찍는다.

**준비물** — 표준 라이브러리만으로 돌아간다. sqlx 와 tokio 는 쓰지 않고 그 패턴을 흉내 낸 것이다(Cargo.toml 의존성은 주석으로만 남긴다).

**요구 조건**

1단계 — 모델
1. `User`(`id`, `name`, `email`, `active`) · `CreateUserDto`(`name`, `email`, `id` 없음) · `Order`(`id`, `user_id`, `product`, `amount`, `status`) 에 `Debug` · `Clone` 을 derive 한다.

2단계 — 가상 DB
2. `Database` 는 `users` · `orders` 벡터, 다음 id 두 개, 트랜잭션 깃발, 롤백용 스냅샷 `Option<(Vec<User>, Vec<Order>)>` 을 가진다.
3. `new()` 는 시드 유저 3명 · 주문 3건을 넣고 다음 id 를 4 로, 깃발은 `false`, 스냅샷은 `None` 으로 둔다.

3단계 — CRUD
4. `find_user_by_id` 는 `id` 가 같은 첫 유저를 `Option<&User>` 로 돌려준다.
5. `find_users_by_status` 는 `active` 가 같은 유저를 모두 `Vec<&User>` 로 돌려준다.
6. `create_user` 는 다음 유저 id 를 새 `id` 로 쓰고 `active` 를 `true` 로 두며, 다음 id 를 1 늘리고, 복제본을 저장한 뒤 새 유저를 돌려준다.
7. `update_user_status` 는 찾은 유저의 `active` 를 바꿔 복제본을 `Ok` 로, 못 찾으면 `Err("User {id} not found")` 를 돌려준다.
8. `delete_user` 는 `retain` 으로 지우고, 길이가 줄지 않았으면 `Err("User {id} not found")` 를 돌려준다.

4단계 — 조인 · 집계
9. `find_user_orders(user_id)` 는 그 유저의 주문마다 `(유저 이름, 상품, 금액)` 튜플을 만든다.
10. `user_order_summary` 는 모든 유저마다 `(이름, 주문 수, 금액 합)` 을 만든다 — 주문 없는 유저도 포함한다.

5단계 — 트랜잭션
11. `begin_transaction` 은 `"  [TX] BEGIN"` 을 찍고 깃발을 세우며 `users` · `orders` 복제본을 스냅샷으로 둔다.
12. `commit` 은 `"  [TX] COMMIT"` 을 찍고 깃발을 내리며 스냅샷을 버린다.
13. `rollback` 은 `"  [TX] ROLLBACK"` 을 찍고 스냅샷을 꺼내 `users` · `orders` 를 되돌린 뒤 깃발을 내린다.

6단계 — Repository
14. `UserRepository<'a>` 는 `&'a mut Database` 를 쥐고 `new` · `find_all`(`&[User]`) · `find_by_id` · `create(&str, &str)` · `deactivate(id)` 를 DB 메서드에 위임한다.

7단계 — `main`
15. 「1. 기본 CRUD」: 전체 유저 이름 · 활성 유저 이름을 찍고, Diana 를 만들고, Bob(id 2)을 비활성화해 각각 찍는다.
16. 「2. 조인 + 집계」: Alice(id 1)의 주문을 `이름 -> 상품 (금액원)` 꼴로, 유저별 요약을 `이름: N건, 금액원` 꼴로 찍는다(금액은 소수점 없이).
17. 「3. 트랜잭션」: Eve 를 만드는 트랜잭션을 커밋한 뒤 유저 수를, id 1 을 지우는 트랜잭션에서 삭제 후 · 롤백 후 유저 수를 찍는다.
18. 「4. Repository 패턴」: Repository 로 전체 이름을 찍고 Frank 를 만들어 찍는다.
19. 끝으로 실제 sqlx 코드(`query_as!` 조회 · `begin`/`query!`/`commit` 트랜잭션 · `migrate!`)를 raw 문자열로 찍는다.

**시작 코드**

```rust
// Cargo.toml (흉내만 낸다 — 실제로 추가하지 않는다):
//   sqlx = { version = "0.7", features = ["runtime-tokio-native-tls", "postgres"] }
//   tokio = { version = "1", features = ["full"] }

// TODO: User · CreateUserDto · Order 정의 (Debug, Clone)

struct Database {
    // TODO: users, orders, next_user_id, next_order_id, in_transaction, savepoint
}

impl Database {
    fn new() -> Self {
        // 시드 데이터 (미리 채워 둔 값)
        // users:  (1, "Alice", "alice@example.com", true)
        //         (2, "Bob", "bob@example.com", true)
        //         (3, "Charlie", "charlie@example.com", false)
        // orders: (1, user 1, "노트북", 1500000.0, "completed")
        //         (2, user 1, "마우스", 50000.0, "pending")
        //         (3, user 2, "키보드", 150000.0, "completed")
        todo!()
    }

    fn find_user_by_id(&self, id: i64) -> Option<&User> { todo!() }
    fn find_users_by_status(&self, active: bool) -> Vec<&User> { todo!() }
    fn create_user(&mut self, dto: CreateUserDto) -> User { todo!() }
    fn update_user_status(&mut self, id: i64, active: bool) -> Result<User, String> { todo!() }
    fn delete_user(&mut self, id: i64) -> Result<(), String> { todo!() }

    fn find_user_orders(&self, user_id: i64) -> Vec<(String, String, f64)> { todo!() }
    fn user_order_summary(&self) -> Vec<(String, usize, f64)> { todo!() }

    fn begin_transaction(&mut self) { todo!() }
    fn commit(&mut self) { todo!() }
    fn rollback(&mut self) { todo!() }
}

// TODO: struct UserRepository<'a> 와 impl (new, find_all, find_by_id, create, deactivate)

fn main() {
    println!("=== SQLx 패턴 시뮬레이션 ===");
    // TODO: 1. 기본 CRUD
    // TODO: 2. 조인 + 집계
    // TODO: 3. 트랜잭션 (커밋 한 번, 롤백 한 번)
    // TODO: 4. Repository 패턴
    // TODO: 실제 sqlx 코드 패턴을 r#"..."# 로 출력
}
```

**확인 방법** — `rustc database_sqlx.rs && ./database_sqlx` 로 돌려, 롤백 후 유저 수가 삭제 전 수로 돌아왔는지, 주문 없는 유저가 요약에 `0건` 으로 나오는지, Frank 의 `id` 가 6 인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
