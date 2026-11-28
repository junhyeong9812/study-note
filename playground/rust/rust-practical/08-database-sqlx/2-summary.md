# rust/rust-practical/08 — SQLx 데이터베이스 — 정리 (힌트)

> 출처 — study-site 항목 `rust/database-sqlx`(항목 데이터 `data/rust/practical.json`) · 정답 코드 study-practice `rust/rust-practical/reference/database-sqlx.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**sqlx 로 데이터베이스를 쓰는 일은 「은행 창구에서 서류를 내고 거래하는 일」이다.**
은행은 손님이 올 때마다 직원을 새로 뽑지 않는다.
창구 직원 몇 명을 미리 앉혀 두고 손님이 오면 빈 창구로 보낸다.
서류는 접수 전에 양식 검사를 받는다.
양식이 틀린 서류는 창구에 닿기도 전에 돌려받는다.
여러 장짜리 거래(이체 = 출금 + 입금)는 한 묶음으로 처리한다.
다 되면 도장을 찍어 확정하고, 중간에 문제가 생기면 묶음 전체를 없던 일로 돌린다.
sqlx 로 PostgreSQL 을 쓰는 코드도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 미리 앉혀 둔 창구 직원들 | 커넥션 풀 `PgPool` |
| 접수 전 양식 검사 | `query!` · `query_as!` 매크로의 컴파일 타임 검증 |
| 서류 한 장 | SQL 쿼리 한 개 |
| 여러 장짜리 거래 묶음 | 트랜잭션(`pool.begin()`) |
| 확정 도장 | `tx.commit()` |
| 없던 일로 돌리기 | 롤백 |
| 서류 양식 개정 이력 | 마이그레이션(`sqlx-cli`) |

```text
 앱 시작 ──► PgPool 한 번 생성 ──► 여러 곳에서 공유
                     │
   query_as!(...) ───┤  (컴파일 때 SQL·타입 검사)
                     ▼
              PostgreSQL ◄── begin → 쿼리들 → commit / rollback
```

> **sqlx** — Rust 에서 SQL 데이터베이스에 비동기로 접근하는 라이브러리다.\
> 예: `sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", user_id)`.

이 항목의 예제는 sqlx 를 직접 부르지 않는다.
`Vec` 두 개로 만든 인메모리 DB 로 sqlx 를 쓸 때의 **패턴**(행 매핑 · CRUD · 조인 · 집계 · 트랜잭션 · Repository)을 흉내 낸다.
실제 sqlx 코드는 맨 끝에 문자열로 찍어 보여 줄 뿐이다.

## 이 주제가 답하려는 질문

1. DB 의 한 행을 Rust 의 무엇으로 받고, SQL 한 줄은 코드의 무엇에 대응하나?
2. 여러 쿼리를 「전부 되거나 전부 안 되거나」로 묶으려면 무엇을 저장했다가 무엇을 되돌려야 하나?
3. DB 접근 코드를 도메인 어휘(`create` · `deactivate`)로 감싸면 Rust 의 빌림 규칙과 어떻게 엮이나?
4. 실제 sqlx 는 SQL 오타 · 타입 불일치를 언제 잡고, 커넥션 · 트랜잭션 · 마이그레이션을 어떻게 다루나?

## 동작 방식

### (1) 행을 구조체로 — 모델과 DTO

**언제 쓰나** — 쿼리 결과의 한 행을 이름 붙은 필드로 받고 싶을 때 쓴다.
넣을 때와 읽을 때 필요한 필드가 다르면 입력용 구조체를 따로 둔다.

```text
users 테이블의 한 행           Rust 값
┌────┬───────┬──────────────┬────────┐
│ id │ name  │ email        │ active │ ──►  User { id, name, email, active }
└────┴───────┴──────────────┴────────┘
INSERT 에 넣을 값 (id 없음)          ──►  CreateUserDto { name, email }
```

- 테이블의 열 하나가 구조체의 필드 하나에 대응한다.
- 실제 sqlx 에서는 `#[derive(FromRow)]` 를 붙여 행 → 구조체 변환을 자동으로 만든다(원본 주석).
- 예제는 sqlx 가 없으니 `#[derive(Debug, Clone)]` 만 붙인다.
- `CreateUserDto` 에는 `id` 가 없다 — `id` 는 DB 가 할당하는 값이기 때문이다.

> **FromRow** — sqlx 에서 DB 행을 구조체로 바꾸는 방법을 정하는 derive 다.\
> 예: `#[derive(FromRow)] struct User { … }`.

> **DTO** — 계층 사이에 데이터를 옮기려고 만든, 필요한 필드만 담은 구조체다.\
> 예: 생성 요청의 `name` · `email` 만 담은 `CreateUserDto`.

### (2) SQL 한 줄 = 메서드 하나 — CRUD

**언제 쓰나** — 조회 · 생성 · 수정 · 삭제를 각각 이름 붙은 함수로 감쌀 때 쓴다.
예제는 메서드마다 위에 그 메서드가 흉내 내는 SQL 을 주석으로 적어 둔다.

```text
SQL                                         메서드                         돌려주는 것
SELECT * FROM users WHERE id = $1        →  find_user_by_id(id)         →  Option<&User>
SELECT * FROM users WHERE active = $1    →  find_users_by_status(b)     →  Vec<&User>
INSERT … VALUES ($1,$2) RETURNING *      →  create_user(dto)            →  User
UPDATE users SET active=$1 WHERE id=$2   →  update_user_status(id, b)   →  Result<User, String>
DELETE FROM users WHERE id = $1          →  delete_user(id)             →  Result<(), String>
```

- `find_user_by_id` 는 `iter().find` 로 첫 일치를 찾는다. 없으면 `None` 이다.
- `find_users_by_status` 는 `filter` 로 조건에 맞는 행을 모두 모은다.
- `create_user` 는 `next_user_id` 를 새 `id` 로 쓰고 1 늘린다(auto-increment 흉내), `active` 는 `true` 로 둔다, 복제본을 `users` 에 넣고 원본을 돌려준다(`RETURNING *` 흉내).
- `update_user_status` 는 `iter_mut().find` 로 가변 참조를 얻어 고친다. 못 찾으면 `Err("User {id} not found")` 다.
- `delete_user` 는 `retain` 으로 지운 뒤 길이를 전과 비교한다. 줄지 않았으면(영향받은 행이 0) `Err` 다.

> **CRUD** — Create · Read · Update · Delete, 데이터를 다루는 네 가지 기본 동작이다.\
> 예: `INSERT` · `SELECT` · `UPDATE` · `DELETE`.

> **`$1` 자리표시자** — SQL 안에 값을 직접 붙이지 않고 따로 넘기는 자리다.\
> 예: `"SELECT * FROM users WHERE id = $1", user_id` 에서 `user_id` 가 `$1` 에 들어간다.

### (3) 조인과 집계

**언제 쓰나** — 두 테이블을 이어 붙이거나(조인), 행을 묶어 개수 · 합을 낼 때(집계) 쓴다.

```text
find_user_orders(1)
orders ──filter(user_id==1)──► [노트북, 마우스]
         ──filter_map(users 에서 id 찾아 이름 붙이기)──► [("Alice","노트북",1500000), ("Alice","마우스",50000)]

user_order_summary()
users 하나마다 ──► 그 유저의 orders 모으기 ──► (이름, 개수, 금액 합)
Alice → 2건 · Bob → 1건 · Charlie → 0건(주문 없음도 한 줄)
```

- `find_user_orders` 는 `JOIN … WHERE u.id = $1` 을 흉내 낸다.
- 주문을 먼저 거르고, 주문마다 유저를 찾아 `(이름, 상품, 금액)` 튜플로 만든다.
- 유저를 못 찾은 주문은 `filter_map` 이 버린다 — 내부 조인처럼 짝이 없는 행이 빠진다.
- `user_order_summary` 는 `LEFT JOIN … GROUP BY u.id` 를 흉내 낸다.
- **유저 쪽에서 출발하므로** 주문이 없는 유저도 `0` 건으로 한 줄을 차지한다 — 이것이 `LEFT JOIN` 의 뜻이다.
- 개수는 `len()`, 합은 `map(|o| o.amount).sum()` 이 `COUNT` · `SUM` 역할을 한다.

> **LEFT JOIN** — 왼쪽 테이블의 행을 모두 남기고, 오른쪽에 짝이 없으면 비어 있는 채로 붙이는 조인이다.\
> 예: 주문이 없는 유저도 결과에 나온다.

### (4) 트랜잭션 — 스냅샷을 찍고, 확정하거나 되돌린다

**언제 쓰나** — 여러 쿼리가 모두 성공해야만 의미가 있을 때 쓴다.
하나라도 실패하면 앞서 한 변경까지 없던 일로 돌려야 한다.

```text
begin_transaction()  : savepoint = Some((users 복제, orders 복제)) · in_transaction = true · "[TX] BEGIN"
        │
   create / delete …  (users · orders 를 바로 고친다)
        │
   ┌────┴─────────────────────────┐
commit()                      rollback()
savepoint = None              savepoint.take() 로 꺼내 users · orders 에 덮어쓴다
"[TX] COMMIT"                 "[TX] ROLLBACK"
변경이 그대로 남는다           begin 시점의 users · orders 로 돌아간다
```

- `begin_transaction` 은 그 시점의 `users` 와 `orders` 를 통째로 복제해 `savepoint` 에 둔다.
- 그 사이의 변경은 `users` · `orders` 에 바로 적용된다.
- `commit` 은 스냅샷을 버린다 — 이미 적용된 변경이 확정된다.
- `rollback` 은 `take()` 로 스냅샷을 꺼내(`savepoint` 는 `None` 이 된다) 현재 값에 덮어쓴다.
- **스냅샷에 들어가는 것은 `users` 와 `orders` 둘뿐이다.**
  `next_user_id` · `next_order_id` 는 스냅샷에 없어서 롤백해도 돌아가지 않는다.
- `in_transaction` 깃발은 세우고 내리기만 하고, 어느 메서드도 읽지 않는다.

> **트랜잭션** — 여러 쿼리를 「전부 반영 아니면 전부 취소」로 묶는 단위다.\
> 예: `BEGIN` → `DELETE` → `ROLLBACK` 이면 삭제가 취소된다.

> **커밋 / 롤백** — 커밋은 트랜잭션의 변경을 확정하고, 롤백은 시작 시점으로 되돌린다.\
> 예: `tx.commit()` · 예제의 `db.rollback()`.

### (5) Repository — 빌린 DB 를 도메인 어휘로 감싸기

**언제 쓰나** — 호출하는 쪽이 SQL 이나 DTO 를 몰라도 `create(name, email)` 처럼 쓸 수 있게 할 때 쓴다.

```text
main 의 db ──&mut 빌려 줌──► UserRepository<'a> { db: &'a mut Database }
                                  find_all()    → &self.db.users
                                  find_by_id(id)→ db.find_user_by_id
                                  create(n, e)  → CreateUserDto 만들어 db.create_user
                                  deactivate(id)→ db.update_user_status(id, false)
```

- `UserRepository<'a>` 는 DB 를 소유하지 않고 `&'a mut Database` 로 빌려 쥔다.
- 라이프타임 `'a` 는 「repo 가 빌린 DB 보다 오래 살 수 없다」를 컴파일러에 알린다.
- `&mut` 빌림이므로 repo 가 쓰이는 동안 `main` 은 `db` 를 직접 쓸 수 없다.
- `create` 는 `&str` 두 개를 받아 `to_string()` 으로 DTO 를 만들어 DB 에 넘긴다.
- `deactivate` 는 `update_user_status(id, false)` 에 위임한다.

> **Repository 패턴** — 데이터 저장소 접근을 한 타입에 모아 도메인 어휘의 메서드로 내놓는 설계다.\
> 예: `repo.deactivate(id)`.

> **라이프타임** — 참조가 유효한 범위에 붙이는 이름이다.\
> 예: `struct UserRepository<'a> { db: &'a mut Database }`.

### (6) 실제 sqlx — 매크로 · 풀 · 트랜잭션 · 마이그레이션

**언제 쓰나** — 위 패턴을 진짜 PostgreSQL 에 대고 할 때 쓴다.

```text
cargo build ──► query_as!(User, "SELECT …", id) ──► SQL 문법 · 열 타입 ↔ User 필드 검사
                                                  틀리면 컴파일 에러
실행        ──► .fetch_one(&pool).await?            ──► 풀에서 커넥션 하나 빌려 실행
            ──► pool.begin().await? → tx
                query!(…).execute(&mut *tx).await?
                tx.commit().await?
            ──► sqlx::migrate!("./migrations").run(&pool).await?
```

- `query_as!` · `query!` 는 **컴파일 타임에** SQL 문법과 타입을 검증한다(원본 팁).
- `query_as!(User, …)` 는 결과를 `User` 로 받는다. `fetch_one` 은 한 행을 가져온다.
- 쿼리는 비동기라 `.await` 로 기다리고, 실패는 `?` 로 올려 보낸다.
- 커넥션 풀 `PgPool` 은 애플리케이션 시작 시 **한 번** 만들고 공유한다(원본 팁).
- 트랜잭션은 `pool.begin()` 으로 시작하고 `tx.commit()` 으로 확정한다(원본 팁).
- 트랜잭션 안의 쿼리는 풀이 아니라 `&mut *tx` 에 대고 실행한다.
- 마이그레이션은 `sqlx-cli` 로 관리하고, 코드에서는 `sqlx::migrate!("./migrations").run(&pool)` 로 적용한다.

> **커넥션 풀** — 미리 열어 둔 DB 연결 묶음을 여러 작업이 빌려 쓰고 돌려주는 구조다.\
> 예: `PgPool`.

> **마이그레이션** — 테이블 구조 변경을 번호 붙은 SQL 파일로 쌓아 차례대로 적용하는 방식이다.\
> 예: `./migrations` 폴더의 파일들을 `migrate!` 로 적용한다.

## 문법 — 형태와 규칙

원본의 Cargo.toml 의존성은 다음과 같다.

```text
sqlx  = { version = "0.7", features = ["runtime-tokio-native-tls", "postgres"] }
tokio = { version = "1", features = ["full"] }
```

실제 sqlx 의 꼴을 최소 예제로 모으면 이렇다(원본이 문자열로 보여 준 패턴을 함수로 묶은 것이다).

```rust
// 최소 예제 — 원본의 sqlx 패턴을 한 함수로 모은 것
async fn add_after_lookup(pool: &sqlx::PgPool, user_id: i64, name: &str) -> Result<(), sqlx::Error> {
    let user = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", user_id)
        .fetch_one(pool).await?;          // 한 행 → User
    println!("{:?}", user);

    let mut tx = pool.begin().await?;     // 트랜잭션 시작
    sqlx::query!("INSERT INTO users (name) VALUES ($1)", name)
        .execute(&mut *tx).await?;        // 풀이 아니라 tx 에 대고 실행
    tx.commit().await?;                   // 확정
    Ok(())
}
```

- `query_as!(타입, "SQL", 인자…)` — 결과 행을 그 타입으로 받는다.
- `query!("SQL", 인자…)` — 결과 타입을 따로 정하지 않는 쿼리(INSERT 등)에 쓴다.
- 두 매크로 모두 SQL 과 타입을 컴파일 타임에 검증한다.
- 인자는 `$1`, `$2` … 차례로 들어간다.
- `.fetch_one(...)` 은 행을 가져오고, `.execute(...)` 는 실행만 한다.
- 모든 호출은 비동기다 — `async fn` 안에서 `.await` 한다.
- 트랜잭션은 `pool.begin()` → 쿼리들 → `tx.commit()` 순서다.
- 풀은 시작 때 한 번 만들고, 함수에는 `&PgPool` 로 넘겨 공유한다.
- 마이그레이션 적용: `sqlx::migrate!("./migrations").run(&pool).await?`.

## 어디서 틀리나

### 1. 시뮬레이션은 SQL 을 검증하지 않는다

예제의 메서드 위 주석(`SELECT * FROM users WHERE id = $1 (sqlx::query_as!의 시뮬레이션)`)은 설명일 뿐이다.
메서드는 `Vec` 을 뒤질 뿐이라 주석의 SQL 에 오타가 있어도 아무것도 잡히지 않는다.
컴파일 타임 검증은 실제 `query!` · `query_as!` 매크로를 쓸 때의 이야기다.

### 2. 커넥션 풀을 요청마다 만든다

원본 팁은 「`PgPool` 은 시작 시 한 번 만들고 공유한다」다.
요청마다 풀을 새로 만들면 매번 연결을 새로 여는 셈이라 풀을 둔 의미가 없어진다.
예제의 `Database` 도 `main` 에서 한 번 만들고 끝까지 같은 값을 쓴다.

### 3. `commit` 을 빠뜨린다

트랜잭션은 `pool.begin()` 으로 시작하고 `tx.commit()` 으로 **확정해야** 끝난다(원본 팁).
확정하지 않은 트랜잭션의 변경을 반영된 것으로 믿으면 안 된다.

### 4. 롤백이 모든 것을 되돌린다고 믿는다

예제의 `rollback` 은 스냅샷에 든 `users` · `orders` 만 되돌린다.
`next_user_id` 는 스냅샷 밖이라, 트랜잭션 안에서 만든 유저를 롤백해도 다음 `id` 는 이미 늘어난 값이다.
「무엇을 저장해 두었나」가 「무엇이 되돌아가나」를 정한다.

### 5. 「지울 행이 없음」을 성공으로 넘긴다

`DELETE` 는 맞는 행이 없어도 SQL 자체는 실패하지 않는다.
예제의 `delete_user` 는 지우기 전후 길이를 비교해, 영향받은 행이 0 이면 `Err("User {id} not found")` 로 돌려준다.
「영향받은 행 수」를 확인하지 않으면 없는 id 삭제가 조용히 성공처럼 보인다.

### 6. Repository 를 만든 뒤 `db` 를 직접 쓴다

`UserRepository::new(&mut db)` 는 `db` 를 가변으로 빌린다.
`repo` 를 아직 쓰는 동안 `db.users` 를 직접 읽거나 `db.create_user` 를 부르면 빌림 규칙에 걸린다.
예제의 `main` 은 Repository 단계를 맨 끝에 두어 이 충돌을 피한다.

### 7. 원본 주석과 코드가 어긋나는 곳

- 원본 주석은 `Database` 를 「PgPool/Connection 역할」이라 한다 → 실제 풀은 여러 연결을 동시에 빌려주지만 이 구조체는 `&mut` 하나로만 고칠 수 있어 동시 접근이 없다. 비유로만 받아들인다.
- `in_transaction` 은 세우고 내리기만 하고 읽는 곳이 없다 → 「트랜잭션 상태」를 관리한다는 주석과 달리 동작에 영향이 없다. `commit` 은 `begin` 없이 불러도 막지 않는다.
- `use std::collections::HashMap;` 은 원본 주석대로 「미사용이나 유지」다 → 쓰이지 않는 import 라 컴파일러 경고 대상이다(원본에 근거 없음 — 추론).
- `next_order_id` · `status` 필드와 `find_by_id` · `deactivate` 메서드도 `main` 에서 쓰이지 않는다.

### 8. 집계에서 주문 없는 유저가 빠진다고 생각한다

`user_order_summary` 는 유저 목록에서 출발하므로 주문이 없는 유저도 한 줄 나온다.
주문에서 출발하는 `find_user_orders` 와 출발점이 다르다는 점을 헷갈리기 쉽다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `query!` · `query_as!` 가 컴파일 타임에 SQL 과 타입을 검증한다 | sqlx 라이브러리(매크로)의 동작 — Rust 언어가 SQL 을 아는 것은 아니다 |
| 인자가 `$1`, `$2` 자리에 들어간다 | PostgreSQL 의 자리표시자 문법 — DB 마다 다를 수 있다 (확인 필요) |
| 풀을 한 번 만들고 공유한다 | 원본 팁의 권장 설계 — 언어가 강제하지 않는다 |
| `retain` 이 조건에 맞는 원소만 남긴다 · `iter().find` 가 첫 일치를 돌려준다 | Rust 표준 라이브러리 |
| `repo` 가 살아 있는 동안 `db` 를 직접 못 쓴다 | Rust 언어(빌림 검사기) |
| 롤백이 `users` · `orders` 만 되돌린다 | 이 예제의 구현 — 실제 DB 트랜잭션의 동작과 같다는 보장은 없다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 쿼리 결과를 구조체로 받기 | `query_as!(User, …)` + `FromRow` | 열을 인덱스로 하나씩 꺼내기 |
| SQL 오타를 빌드 때 잡고 싶다 | `query!` · `query_as!` 매크로 | 문자열을 그대로 실행하고 실행 때 알기 |
| 여러 요청이 DB 를 쓴다 | 시작 때 만든 `PgPool` 공유 | 요청마다 풀 · 연결 새로 만들기 |
| 여러 쿼리가 함께 성공해야 한다 | `pool.begin()` → … → `tx.commit()` | 쿼리를 따로따로 실행하고 실패 시 손으로 되돌리기 |
| 테이블 구조를 바꾼다 | `sqlx-cli` 마이그레이션 | 운영 DB 에 손으로 `ALTER` 하기 |
| 호출부가 SQL 을 몰라도 되게 | Repository 로 감싸기 | 모든 곳에 SQL 문자열 흩뿌리기 |

## 핵심 문장

1. **SQL 한 줄은 메서드 하나, 행 하나는 구조체 하나에 대응한다** — 입력용 DTO 는 DB 가 정하는 `id` 를 뺀다.
2. **sqlx 의 `query!` · `query_as!` 는 SQL 과 타입을 컴파일 타임에 검증한다** — 예제의 시뮬레이션은 이 검증을 하지 않는다.
3. **`PgPool` 은 시작 때 한 번 만들고 공유한다.**
4. **트랜잭션은 `begin` 에서 시작해 `commit` 으로 확정하거나 롤백으로 되돌린다** — 예제에서 되돌아가는 것은 스냅샷에 저장한 것뿐이다.
5. **Repository 는 DB 를 `&'a mut` 로 빌려 감싸고, 그동안 원래 `db` 는 직접 쓸 수 없다.**

## 관련 자료

- `web-actix` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `web-axum` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `serde-json` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/practical.json` 의 `database-sqlx`

## 용어 풀이

- **sqlx** — Rust 의 비동기 SQL 데이터베이스 접근 라이브러리.
- **쿼리 매크로** — `query!` · `query_as!` 처럼 SQL 을 받아 컴파일 타임에 검증하는 매크로.
- **FromRow** — DB 행을 구조체로 바꾸는 sqlx derive.
- **DTO** — 계층 사이에 옮길 필드만 담은 구조체.
- **CRUD** — 생성 · 조회 · 수정 · 삭제.
- **`$1` 자리표시자** — SQL 에 값을 따로 넘기는 자리.
- **auto-increment** — DB 가 새 행의 `id` 를 차례로 매기는 방식.
- **RETURNING \*** — INSERT 한 행을 결과로 돌려받는 SQL 꼴.
- **조인 / LEFT JOIN** — 두 테이블을 이어 붙이기 / 왼쪽 행을 모두 남기는 조인.
- **집계 (`COUNT` · `SUM` · `GROUP BY`)** — 행을 묶어 개수 · 합을 내는 쿼리.
- **트랜잭션** — 「전부 반영 아니면 전부 취소」로 묶인 쿼리 단위.
- **커밋 / 롤백** — 트랜잭션 확정 / 시작 시점으로 되돌리기.
- **스냅샷(savepoint)** — 예제에서 롤백용으로 복제해 둔 `users` · `orders`.
- **커넥션 풀 (`PgPool`)** — 미리 열어 둔 DB 연결 묶음.
- **마이그레이션** — 스키마 변경을 파일로 쌓아 차례로 적용하는 방식.
- **sqlx-cli** — sqlx 의 명령줄 도구, 마이그레이션 관리에 쓴다.
- **Repository 패턴** — 저장소 접근을 도메인 어휘의 메서드로 감싸는 설계.
- **라이프타임** — 참조가 유효한 범위의 이름(`'a`).

## 더 들어가면

- `query!` 류 매크로가 컴파일 타임에 검증하려면 빌드할 때 DB 에 접속할 수 있어야 한다(`DATABASE_URL` 환경 변수). DB 없이 빌드하려면 `cargo sqlx prepare` 로 쿼리 메타데이터를 미리 저장해 두는 오프라인 모드를 쓴다 (확인 필요).
- 실제 sqlx 의 `Transaction` 은 `commit` 없이 버려지면(drop) 롤백된다 (확인 필요).
- PostgreSQL 의 시퀀스(auto-increment) 값은 트랜잭션을 롤백해도 되돌아가지 않는다고 알려져 있다 — 예제에서 `next_user_id` 가 롤백되지 않는 것과 우연히 닮았다 (확인 필요).
- 빈 이터레이터의 `f64` 합(`sum`)의 부호가 Rust 버전에 따라 `0.0` 이 아니라 `-0.0` 일 수 있고, 그러면 `{:.0}` 이 `-0` 을 찍는다 (확인 필요).
- 실제 DB 트랜잭션은 다른 연결과의 격리(isolation)까지 다룬다. 예제의 통째 복제 스냅샷은 그 부분을 흉내 내지 않는다 (확인 필요).
- `sqlx::query_as::<_, User>("…")` 같은 매크로 아닌 함수형 API 는 실행 때 검사한다 (확인 필요).
