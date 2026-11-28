# rust/rust-practical/08 — SQLx 데이터베이스 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. Diana 는 id 4 · 활성, Bob 은 비활성으로 바뀐 복제본

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
User { id: 4, name: "Diana", email: "diana@example.com", active: true }
User { id: 2, name: "Bob", email: "bob@example.com", active: false }
```

**왜 그런가**
`create_user` 는 `next_user_id`(4)를 새 `id` 로 쓰고 `active` 를 `true` 로 둔 뒤 id 를 5 로 늘린다.
`update_user_status(2, false)` 는 `iter_mut().find` 로 Bob 을 찾아 `active` 를 `false` 로 바꾸고 그 복제본을 `Ok` 로 돌려준다.
`{:?}` 는 derive 한 `Debug` 꼴로 필드를 차례대로 찍는다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 네 줄 — 주문 없는 유저도 0건으로 나온다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
    Alice: 2건, 1550000원
    Bob: 1건, 150000원
    Charlie: 0건, 0원
    Diana: 0건, 0원
```

**왜 그런가**
`user_order_summary` 는 **유저 목록에서 출발해** 유저마다 한 줄을 만든다 — `LEFT JOIN` 흉내라서 주문이 없는 Charlie · Diana 도 빠지지 않는다.
Alice 의 합은 1500000 + 50000 = 1550000 이고, `{:.0}` 이 소수점 아래를 찍지 않는다.
주문 없는 유저는 빈 목록의 합이다. Rust 버전에 따라 이 합이 `-0.0` 이 되어 `-0원` 으로 찍힐 수 있다는 점은 2-summary 「더 들어가면」에 따로 적었다 (확인 필요).
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 8」.

### 3. 5 → 4 → 5, `[TX]` 줄은 넷

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [TX] BEGIN
  [TX] COMMIT
  유저 수: 5
  [TX] BEGIN
  삭제 후 유저 수: 4
  [TX] ROLLBACK
  롤백 후 유저 수: 5
```

**왜 그런가**
첫 트랜잭션에서 Eve 가 들어가 4명이 5명이 되고, `commit` 은 스냅샷을 버릴 뿐이라 5명이 남는다.
둘째 `begin_transaction` 은 5명짜리 `users` 를 복제해 둔다.
`delete_user(1)` 로 4명이 되지만, `rollback` 이 스냅샷의 5명을 다시 덮어쓴다.
`begin` · `commit` · `rollback` 이 각자 `[TX]` 줄을 하나씩 찍으므로 넷이다.
근거: 2-summary 「동작 방식 (4)」.

### 4. SQL 문법과 타입 오류를 빌드 때 잡는다

`query_as!` · `query!` 는 컴파일 타임에 SQL 문법과 타입을 검증한다.
그래서 SQL 오타나 열 타입과 구조체 필드의 불일치가 프로그램을 돌려 보기 전에 컴파일 에러로 드러난다.
일반 함수에 문자열을 넘기면 그 문자열은 실행할 때 DB 에 닿아서야 틀렸음이 드러난다(원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (6)」 · 「문법 — 형태와 규칙」.

### 5. 연결을 매번 새로 열지 않고 미리 열어 둔 것을 빌려 쓰려고

풀은 미리 열어 둔 연결 묶음이고, 여러 작업이 거기서 연결을 빌려 쓰고 돌려준다.
요청마다 풀을 새로 만들면 매번 연결을 새로 여는 셈이라 풀을 둔 의미가 없어진다.
그래서 원본 팁은 「시작 시 한 번 생성하고 공유한다」고 한다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 2」.

### 6. 같지 않다 — `next_user_id` 는 스냅샷 밖이다

`begin_transaction` 이 저장하는 스냅샷은 `users` 와 `orders` 두 벡터뿐이다.
트랜잭션 안의 `create_user` 가 `next_user_id` 를 1 늘린 것은 롤백으로 돌아가지 않는다.
그래서 롤백 뒤에 만든 유저는 롤백 전 유저보다 하나 큰 `id` 를 받는다 — 롤백 전 `id` 는 건너뛴 번호가 된다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 7. `Err("User 99 not found")` — 길이가 줄지 않아서

`delete_user` 는 `retain` 전의 길이를 기억해 두고, `retain` 뒤 길이와 비교한다.
id 99 가 없으면 아무것도 지워지지 않아 길이가 같고, 「영향받은 행 0」으로 보고 `Err` 를 돌려준다.
SQL 의 `DELETE` 는 맞는 행이 없어도 실패하지 않으므로, 영향받은 행 수를 확인하는 이 방식이 「없는 id」를 드러내는 방법이다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 8. 잡지 못한다 — 주석은 실행되지 않는 설명이다

이 예제는 sqlx 를 부르지 않고 `Vec` 을 뒤질 뿐이다.
메서드 위의 SQL 은 주석이라 컴파일러가 읽지 않는다.
컴파일 타임 검증은 실제 `query!` · `query_as!` 매크로에 SQL 을 넘길 때만 일어난다.
근거: 2-summary 「한눈에」 · 「어디서 틀리나 1」.

### 9. `repo` 가 `db` 를 가변으로 빌리고 있어서

`UserRepository::new(&mut db)` 는 `db` 의 `&mut` 빌림을 `repo` 안에 넣는다.
Rust 의 빌림 규칙상 가변 빌림이 살아 있는 동안 같은 값을 다른 경로로 읽거나 쓸 수 없다.
그래서 `repo` 를 아직 쓰는 동안 `db.users.len()` 을 직접 부르면 빌림 검사기에 걸린다.
라이프타임 `'a` 는 `repo` 가 빌린 `db` 보다 오래 살 수 없다는 점을 적어 둔 것이다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

## 실습 정답

### 실습 1. 인메모리 DB 로 sqlx 패턴 흉내 내기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 모델 세 개 | `struct User` · `struct CreateUserDto` · `struct Order` + `#[derive(Debug, Clone)]` |
| 2. 가상 DB 필드 | `struct Database { users, orders, next_user_id, next_order_id, in_transaction, savepoint }` |
| 3. 시드 초기화 | `Database::new` |
| 4. id 로 찾기 | `find_user_by_id` — `iter().find` |
| 5. 상태로 찾기 | `find_users_by_status` — `filter(...).collect()` |
| 6. 생성 | `create_user` — `next_user_id` 사용 · `+= 1` · `push(user.clone())` |
| 7. 상태 수정 | `update_user_status` — `iter_mut().find` · `Err(format!("User {} not found", id))` |
| 8. 삭제 | `delete_user` — `retain` 후 `len` 비교 |
| 9. 조인 | `find_user_orders` — `filter` + `filter_map` |
| 10. 집계 | `user_order_summary` — 유저마다 `len()` · `sum()` |
| 11. 시작 | `begin_transaction` — `savepoint = Some((users.clone(), orders.clone()))` |
| 12. 확정 | `commit` — `savepoint = None` |
| 13. 되돌리기 | `rollback` — `savepoint.take()` 로 복원 |
| 14. Repository | `struct UserRepository<'a> { db: &'a mut Database }` 와 `impl` 다섯 메서드 |
| 15. CRUD 시연 | `main` 의 `--- 1. 기본 CRUD ---` 구간 |
| 16. 조인·집계 시연 | `main` 의 `--- 2. 조인 + 집계 ---` 구간, `{:.0}` 형식 |
| 17. 트랜잭션 시연 | `main` 의 `--- 3. 트랜잭션 ---` 구간 |
| 18. Repository 시연 | `main` 의 `--- 4. Repository 패턴 ---` 구간 |
| 19. 실제 sqlx 패턴 | 마지막 `println!(r#"..."#)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-practical/reference/database-sqlx.rs`

```rust
// [실전 Rust] SQLx 데이터베이스
// 설명: sqlx로 비동기 DB 접근. 쿼리 매크로, 타입 안전 쿼리, 트랜잭션 패턴
// 팁: sqlx의 query_as!와 query! 매크로는 컴파일 타임에 SQL 문법과 타입을 검증한다. 커넥션 풀(PgPool)은 애플리케이션 시작 시 한 번 생성하고 공유한다. 트랜잭션은 pool.begin()으로 시작하고 tx.commit()으로 확정한다. 마이그레이션은 sqlx-cli로 관리한다.

// === SQLx 패턴 시뮬레이션 ===
// Cargo.toml:
//   sqlx = { version = "0.7", features = ["runtime-tokio-native-tls", "postgres"] }
//   tokio = { version = "1", features = ["full"] }

// 컬렉션 사용 (이 예제에선 미사용이나 import 유지)
use std::collections::HashMap;

// ===== 1. 모델 정의 (FromRow 패턴) =====

// 유저 행 매핑 - 실제 sqlx에서는 #[derive(FromRow)]
#[derive(Debug, Clone)]
struct User {
    id: i64,
    name: String,
    email: String,
    active: bool,
}

// 생성용 DTO - DB가 할당하는 id를 제외한 입력 필드
#[derive(Debug, Clone)]
struct CreateUserDto {
    name: String,
    email: String,
}

// 주문 행 매핑
#[derive(Debug, Clone)]
struct Order {
    id: i64,
    user_id: i64,
    product: String,
    amount: f64,
    status: String,
}

// ===== 2. 인메모리 DB 시뮬레이션 =====

// 가상 DB - PgPool/Connection 역할
struct Database {
    users: Vec<User>,
    orders: Vec<Order>,
    // auto-increment 시뮬레이션
    next_user_id: i64,
    next_order_id: i64,
    // 트랜잭션 상태
    in_transaction: bool,
    // 트랜잭션 시작 시점의 스냅샷 (롤백용)
    savepoint: Option<(Vec<User>, Vec<Order>)>,
}

impl Database {
    // 시드 데이터로 초기화
    fn new() -> Self {
        Database {
            users: vec![
                User { id: 1, name: "Alice".into(), email: "alice@example.com".into(), active: true },
                User { id: 2, name: "Bob".into(), email: "bob@example.com".into(), active: true },
                User { id: 3, name: "Charlie".into(), email: "charlie@example.com".into(), active: false },
            ],
            orders: vec![
                Order { id: 1, user_id: 1, product: "노트북".into(), amount: 1500000.0, status: "completed".into() },
                Order { id: 2, user_id: 1, product: "마우스".into(), amount: 50000.0, status: "pending".into() },
                Order { id: 3, user_id: 2, product: "키보드".into(), amount: 150000.0, status: "completed".into() },
            ],
            next_user_id: 4,
            next_order_id: 4,
            in_transaction: false,
            savepoint: None,
        }
    }

    // === 기본 CRUD ===

    // SELECT * FROM users WHERE id = $1 (sqlx::query_as!의 시뮬레이션)
    fn find_user_by_id(&self, id: i64) -> Option<&User> {
        self.users.iter().find(|u| u.id == id)
    }

    // SELECT * FROM users WHERE active = $1
    fn find_users_by_status(&self, active: bool) -> Vec<&User> {
        self.users.iter().filter(|u| u.active == active).collect()
    }

    // INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *
    fn create_user(&mut self, dto: CreateUserDto) -> User {
        // DB가 ID를 발급하는 패턴
        let user = User {
            id: self.next_user_id,
            name: dto.name,
            email: dto.email,
            active: true,
        };
        self.next_user_id += 1;
        self.users.push(user.clone());
        user
    }

    // UPDATE users SET active = $1 WHERE id = $2
    fn update_user_status(&mut self, id: i64, active: bool) -> Result<User, String> {
        // iter_mut으로 가변 참조 획득 후 수정
        match self.users.iter_mut().find(|u| u.id == id) {
            Some(user) => {
                user.active = active;
                Ok(user.clone())
            }
            None => Err(format!("User {} not found", id)),
        }
    }

    // DELETE FROM users WHERE id = $1 - 영향받은 행이 없으면 에러
    fn delete_user(&mut self, id: i64) -> Result<(), String> {
        let len = self.users.len();
        self.users.retain(|u| u.id != id);
        if self.users.len() < len {
            Ok(())
        } else {
            Err(format!("User {} not found", id))
        }
    }

    // === 조인 쿼리 시뮬레이션 ===

    // SELECT u.name, o.product, o.amount
    // FROM orders o JOIN users u ON o.user_id = u.id
    // WHERE u.id = $1
    fn find_user_orders(&self, user_id: i64) -> Vec<(String, String, f64)> {
        self.orders.iter()
            // 해당 유저의 주문만
            .filter(|o| o.user_id == user_id)
            // 유저 정보를 결합 (JOIN 시뮬레이션)
            .filter_map(|o| {
                self.users.iter()
                    .find(|u| u.id == o.user_id)
                    .map(|u| (u.name.clone(), o.product.clone(), o.amount))
            })
            .collect()
    }

    // === 집계 쿼리 ===

    // SELECT u.name, COUNT(o.id), SUM(o.amount)
    // FROM users u LEFT JOIN orders o ON u.id = o.user_id
    // GROUP BY u.id
    fn user_order_summary(&self) -> Vec<(String, usize, f64)> {
        self.users.iter()
            .map(|u| {
                // 각 유저의 주문 모음
                let user_orders: Vec<&Order> = self.orders.iter()
                    .filter(|o| o.user_id == u.id)
                    .collect();
                let count = user_orders.len();
                // SUM 시뮬레이션
                let total: f64 = user_orders.iter().map(|o| o.amount).sum();
                (u.name.clone(), count, total)
            })
            .collect()
    }

    // === 트랜잭션 시뮬레이션 ===

    // BEGIN - 현재 상태를 저장하여 롤백 가능 상태로 진입
    fn begin_transaction(&mut self) {
        println!("  [TX] BEGIN");
        self.in_transaction = true;
        self.savepoint = Some((self.users.clone(), self.orders.clone()));
    }

    // COMMIT - 변경사항 확정
    fn commit(&mut self) {
        println!("  [TX] COMMIT");
        self.in_transaction = false;
        self.savepoint = None;
    }

    // ROLLBACK - 저장된 스냅샷으로 복원
    fn rollback(&mut self) {
        println!("  [TX] ROLLBACK");
        if let Some((users, orders)) = self.savepoint.take() {
            self.users = users;
            self.orders = orders;
        }
        self.in_transaction = false;
    }
}

// ===== 3. Repository 패턴 =====

// 라이프타임으로 DB 참조를 보유하는 Repository
struct UserRepository<'a> {
    db: &'a mut Database,
}

impl<'a> UserRepository<'a> {
    // DB를 주입받음
    fn new(db: &'a mut Database) -> Self {
        UserRepository { db }
    }

    // 전체 슬라이스 반환 (read-only)
    fn find_all(&self) -> &[User] {
        &self.db.users
    }

    // ID 조회 위임
    fn find_by_id(&self, id: i64) -> Option<&User> {
        self.db.find_user_by_id(id)
    }

    // 생성 - DTO 변환 후 DB에 위임
    fn create(&mut self, name: &str, email: &str) -> User {
        self.db.create_user(CreateUserDto {
            name: name.to_string(),
            email: email.to_string(),
        })
    }

    // 비활성화 - active=false로 업데이트
    fn deactivate(&mut self, id: i64) -> Result<User, String> {
        self.db.update_user_status(id, false)
    }
}

fn main() {
    println!("=== SQLx 패턴 시뮬레이션 ===");
    let mut db = Database::new();

    println!("\n--- 1. 기본 CRUD ---");
    // SELECT 전체
    println!("  모든 유저: {:?}", db.users.iter().map(|u| &u.name).collect::<Vec<_>>());

    // SELECT WHERE 조건
    let active_users = db.find_users_by_status(true);
    println!("  활성 유저: {:?}", active_users.iter().map(|u| &u.name).collect::<Vec<_>>());

    // INSERT
    let new_user = db.create_user(CreateUserDto {
        name: "Diana".into(),
        email: "diana@example.com".into(),
    });
    println!("  생성됨: {:?}", new_user);

    // UPDATE
    let updated = db.update_user_status(2, false).unwrap();
    println!("  비활성화: {:?}", updated);

    println!("\n--- 2. 조인 + 집계 ---");
    // Alice(id=1)의 주문 목록
    let alice_orders = db.find_user_orders(1);
    for (name, product, amount) in &alice_orders {
        println!("  {} -> {} ({:.0}원)", name, product, amount);
    }

    println!("\n  유저별 주문 요약:");
    // GROUP BY 결과
    let summary = db.user_order_summary();
    for (name, count, total) in &summary {
        println!("    {}: {}건, {:.0}원", name, count, total);
    }

    println!("\n--- 3. 트랜잭션 ---");
    // 성공 트랜잭션 - BEGIN -> INSERT -> COMMIT
    db.begin_transaction();
    let user = db.create_user(CreateUserDto {
        name: "Eve".into(),
        email: "eve@example.com".into(),
    });
    println!("  생성: {:?}", user);
    db.commit();
    println!("  유저 수: {}", db.users.len());

    // 롤백 트랜잭션 - BEGIN -> DELETE -> ROLLBACK -> 원상복구
    db.begin_transaction();
    db.delete_user(1).unwrap();
    println!("  삭제 후 유저 수: {}", db.users.len());
    db.rollback();
    println!("  롤백 후 유저 수: {}", db.users.len());

    println!("\n--- 4. Repository 패턴 ---");
    // DB를 Repository로 한 번 감싸서 도메인 어휘로 접근
    let mut repo = UserRepository::new(&mut db);
    println!("  전체: {:?}", repo.find_all().iter().map(|u| &u.name).collect::<Vec<_>>());
    let new = repo.create("Frank", "frank@example.com");
    println!("  생성: {:?}", new);

    // 실제 sqlx 사용 코드
    println!("\n=== 실제 sqlx 코드 패턴 ===");
    println!(r#"
// // 컴파일 타임 쿼리 검증
// let user = sqlx::query_as!(User,
//     "SELECT * FROM users WHERE id = $1", user_id
// ).fetch_one(&pool).await?;
//
// // 트랜잭션
// let mut tx = pool.begin().await?;
// sqlx::query!("INSERT INTO users (name) VALUES ($1)", name)
//     .execute(&mut *tx).await?;
// tx.commit().await?;
//
// // 마이그레이션
// sqlx::migrate!("./migrations").run(&pool).await?;
"#);
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 메서드 하나가 SQL 한 줄을 맡는다 — 주석의 SQL 과 반환 타입(`Option` · `Vec` · `Result`)을 짝지어 읽으면 구조가 보인다.
- `delete_user` 는 「영향받은 행 수」를 길이 비교로 흉내 내 없는 id 를 에러로 만든다.
- 집계는 유저에서 출발하므로 주문 없는 유저도 한 줄 나온다 — `LEFT JOIN` 의 뜻과 같다.
- 트랜잭션은 시작 때 복제한 스냅샷으로 되돌리며, 스냅샷에 없는 `next_user_id` 는 돌아가지 않는다.
- Repository 는 `&'a mut` 로 DB 를 빌리므로 `main` 은 그 단계를 맨 끝에 두어 빌림 충돌을 피한다.
- 실제 sqlx 의 컴파일 타임 검증 · `begin`/`commit` · `migrate!` 는 끝의 문자열에만 있고, 시뮬레이션 자체는 그것을 하지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
