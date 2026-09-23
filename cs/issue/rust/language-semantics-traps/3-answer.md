# cs/issue/rust/language-semantics-traps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **자기 교착한다.** `for`의 head 식 `self.registry().ids()`가 만든 임시값(`MutexGuard`)은 문장 끝이 아니라 **루프 전체가 끝날 때** drop된다. 그래서 본문의 `kill()`이 같은 비재진입 락을 다시 잠그려 하면, 자기가 쥔 락을 기다리는 교착이 된다(std `Mutex`는 같은 스레드의 재잠금 동작을 규정하지 않는다 — 문서상 교착 또는 panic이며, 이 사례는 교착). 실측 증상은 e2e 테스트에서 전 스레드가 futex 대기에 멈춘 것이었다. `match` scrutinee도 같은 규칙이다. `match reg.lock().reserve(id) { ... sleep ... }`로 썼다면 sleep하는 동안 락을 쥐고 있어, 그 락을 기다리는 상대 스레드가 영영 진행하지 못한다. 대기 루프를 작성하던 중 이 동형 패턴을 미리 피했다.
   > **임시값 스코프(temporary scope)** — 임시값은 그것을 둘러싼 문장(식)이 끝날 때 drop되는데, `for`·`match`의 head 식은 루프·match 식 전체가 하나의 식이라 그 블록이 끝날 때까지 산다(본문이 head의 참조를 쓸 수 있기 때문). `let x = &temp();`의 "임시값 수명 연장(lifetime extension)"과는 다른 규칙이다. `if let`은 Rust 2024 에디션부터 else 블록 전에 drop되도록 바뀌었다.

2. 두 처방 모두 "가드의 수명을 문장 하나로 끊는다".
   - **(a) 이름 있는 변수로 묶기** — `let ids = self.registry().ids();` 다음 `for id in ids {...}`. `ids()`가 소유된 값(Vec 등)을 돌려주면 가드는 첫 문장이 끝날 때 drop되고, 루프는 락 없이 돈다. 결과가 가드를 빌리는 타입이면 임시 가드가 문장 끝에 drop되므로 컴파일 에러가 나고, 그렇다고 가드를 이름 있는 변수로 묶으면 그 변수의 스코프 내내 락이 이어진다 — 반환 타입이 소유된 값인지 확인해야 한다.
   - **(b) 락 안에서 필요한 것만 꺼내기** — `let links: Vec<Arc<Link>> = self.links.lock().unwrap_or_else(|p| p.into_inner()).values().map(Arc::clone).collect();` 후 `links.iter()...`. 락은 **복제에 걸리는 시간만큼만** 쥐고, 느린 작업(스냅샷·kill)은 락 밖에서 한다.
   수정 뒤 리뷰가 "동형 패턴 잔존 없음"을 확인했다.

3. **표준 해셔는 영속 식별자용으로 설계되지 않았다.** `HashMap`의 기본 해셔 빌더 `RandomState`는 공격자가 충돌을 일부러 만들어 해시 테이블을 느리게 하는 **해시 DoS**를 막으려고 무작위 키를 쓴다(프로세스·인스턴스마다 다름) — 그래서 같은 경로라도 실행마다 해시값이 달라져, 영속 폴더 키로 쓰면 재시작마다 새 폴더를 만든다. `DefaultHasher::new()`를 직접 만들면 키는 고정이지만, 표준 문서가 **알고리즘이 명세되지 않아 릴리스 간에 해시값을 신뢰하면 안 된다**고 밝힌다 — 툴체인을 올리는 순간 폴더 키가 바뀔 수 있다. 영속 식별자에는 **결정론적 해시**가 필요하다 — basename과 전체 경로의 `fnv1a` 해시를 이어 `"{base}-{:016x}"`로 만들어, 사람이 읽을 수 있으면서 같은 basename의 다른 경로도 구분한다.
   > **해시 DoS** — 같은 버킷에 떨어지는 키를 대량으로 넣어 해시 테이블 연산을 O(n)으로 떨어뜨리는 공격. 무작위 시드는 공격자가 충돌 키를 미리 계산하지 못하게 한다.

4. **(기본 설정에서) debug는 panic, release는 조용히 wrap한다.** Rust의 기본 정수 연산은 기본 설정에서 debug 빌드는 오버플로를 검사해 panic하고, release 빌드는(프로필 기본값 `overflow-checks = false`) 검사를 빼고 2의 보수로 감싼다(`u64::MAX + 1 == 0`). 같은 코드가 빌드 모드에 따라 "크래시"와 "틀린 값"으로 다르게 실패하는 셈이다. 외부 입력을 누적할 때는 **오버플로 정책을 코드로 명시**한다 — 상한에서 멈출 거면 `saturating_add`, 오류로 처리할 거면 `checked_add`. 이 사례는 `saturating_add`로 고쳤다.
   > **wrapping 산술** — 표현 범위를 넘으면 최솟값 쪽으로 돌아가는 모듈러 산술. 조용히 틀린 값을 만든다.

5. **일어난다.** `a.or(b)`는 메서드 호출이라 인자 `b`가 **호출 전에 평가**된다. 그래서 `password`가 이미 있거나 에이전트 인증이어도 키체인 조회가 먼저 실행되고, 사용자는 **불필요한 OS 키체인 잠금 해제 프롬프트와 지연**을 겪는다. `or_else(|| ...)`는 클로저를 받아 **필요할 때만** 호출한다. 교정: 인증 방식이 password인 분기 안에서 `password.or_else(|| id.as_deref().and_then(get_secret))`로 지연 조회.
   > **eager vs lazy 대체값** — `or`/`unwrap_or`/`map_or`는 대체값을 미리 계산하고, `or_else`/`unwrap_or_else`/`map_or_else`는 필요할 때 계산한다. 대체값에 비용·부작용이 있으면 후자를 쓴다.

6. **"take"는 소유권을 한 번만 넘긴다는 계약이다.** `take_writer()`는 내부에 보관한 writer를 꺼내 호출자에게 **이동**시키므로, 두 번째 호출에는 넘길 것이 없어 거부된다. 그래서 연결마다 호출하면 첫 연결만 쓰기 권한을 얻는다. 여러 소비자가 필요하면 **생성 시 한 번 취득해 공유 핸들로 보관**하고 배분한다. 이 사례는 처음에 공유 핸들로 고쳤고, 이후 리뷰에서 큐 + 전용 writer 스레드 구조로 다시 정리했다(쓰기 경로를 한 스레드가 소유).
   > **소유권 이전형 API** — 호출자에게 값을 move하고 원래 자리를 비우는 API(`Option::take`, `take_*`). 다시 부르면 빈 값이거나 에러다.

7. 컴파일러가 잡지 않으므로 **리뷰 체크 포인트**와 **실행 테스트**로 잡는다.
   - **임시값 수명** — `for`/`match`/`if let`의 head에 `lock()`·`borrow_mut()`이 있고 본문에서 같은 자원을 다시 잡는지 본다. 테스트는 동시 호출 e2e(교착은 futex 대기로 드러남).
   - **해셔 시드** — 해시값이 디스크·네트워크로 나가는지 본다. 테스트는 같은 입력의 해시를 **고정 기대값(골든 값)**과 비교(두 프로세스 비교만으로는 `DefaultHasher::new()`의 릴리스 간 불안정을 못 잡는다).
   - **오버플로** — 외부 입력이 `+`·`*`로 누적되는지 본다. 테스트는 `MAX` 근처 값을 **release 빌드**에서도.
   - **즉시 평가** — `or(`/`unwrap_or(` 인자에 함수 호출이 있는지 본다.
   - **1회 취득** — `take_*` 호출이 반복 경로(연결마다·요청마다)에 있는지 본다. 테스트는 두 번째 연결의 동작.

## 문제 구조 (추상화 코드)

### 변형 A — `for`/`match` head의 락 가드가 본문 내내 살아 자기 교착
① 문제 코드
```rust
impl Shared {
    fn registry(&self) -> MutexGuard<'_, Registry> { self.reg.lock().unwrap() }

    fn kill_all(&self) {
        for id in self.registry().ids() {     // 가드 임시값 — 루프 끝까지 생존
            self.kill_session(id);             // registry() 재잠금 → 자기 교착
        }
    }
}
// 동형: match self.registry().reserve(id) { Busy => sleep(..), ... }   // sleep 동안 락 보유
```
② 고친 코드
```rust
fn kill_all(&self) {
    let ids: Vec<Id> = self.registry().ids();  // (a) 문장 끝에서 가드 drop
    for id in ids {
        self.kill_session(id);
    }
}
// (b) 필요한 것만 복제해 꺼내고 락 없이 순회
let links: Vec<Arc<Link>> = self.links.lock().unwrap_or_else(|p| p.into_inner())
    .values().map(Arc::clone).collect();
links.iter().map(|l| l.snapshot()).collect()
// 대기 루프: let attempt = reg.reserve(id); 후 match attempt { ... }
```
무엇이 깨졌나: "임시값은 문장 끝에서 사라진다"는 직관이 head 식에서는 틀렸다.\
같은 구조: 같은 교착이 여러 기록에 반복 인용됨 — 해결은 위 두 처방으로 정리.

### 변형 B — 랜덤 시드 해셔를 영속 키에 사용
① 문제 코드
```rust
let mut h = DefaultHasher::new();              // 알고리즘 비명세 — 릴리스 간 값 보장 없음 (HashMap 의 RandomState 는 실행마다 시드가 다름)
project_path.hash(&mut h);
let dir = format!("{base}-{:016x}", h.finish());   // 재시작마다 다른 폴더
```
② 고친 코드
```rust
fn fnv1a(bytes: &[u8]) -> u64 {                // 결정론 해시(직접 구현)
    let mut h: u64 = 0xcbf29ce484222325;
    for b in bytes { h ^= *b as u64; h = h.wrapping_mul(0x100000001b3); }
    h
}
let dir = format!("{base}-{:016x}", fnv1a(project_path.as_bytes()));
```
무엇이 깨졌나: 메모리 안 해시 테이블용 도구(값의 안정성을 보장하지 않음)를 영속 식별자에 썼다. (예방 설계로 기록 — 실제 사고 여부는 원문에 없음)

### 변형 C — 외부 입력 누적의 암묵적 오버플로 정책
① 문제 코드
```rust
impl Usage {
    fn add(&mut self, o: &Usage) {
        self.tokens += o.tokens;               // debug: panic / release: wrap
    }
}
```
② 고친 코드
```rust
self.tokens = self.tokens.saturating_add(o.tokens);   // 상한에서 멈춤 — 정책을 코드로
```
무엇이 깨졌나: 빌드 모드마다 다른 기본 동작에 정책을 맡겼다.

### 변형 D — `or`의 즉시 평가가 부작용을 일으킴
① 문제 코드
```rust
let stored = id.as_deref().and_then(get_secret);        // 항상 키체인 조회
let auth = match method {
    "password" => Auth::Password(password.or(stored).unwrap_or_default()),
    _ => Auth::Agent,                                    // agent 인증에서도 이미 조회됨
};
```
② 고친 코드
```rust
let auth = match method {
    "password" => Auth::Password(
        password.or_else(|| id.as_deref().and_then(get_secret)).unwrap_or_default()),
    _ => Auth::Agent,
};
```
무엇이 깨졌나: 대체값 계산에 부작용(OS 프롬프트)이 있는데 즉시 평가 API를 썼다.

### 변형 E — 1회 취득 API를 반복 경로에서 호출
① 문제 코드
```rust
fn attach(&self, pty: &Pty) -> Result<Writer> {
    pty.take_writer()                          // 두 번째 attach 부터 거부
}
```
② 고친 코드
```rust
fn spawn(pty: Pty) -> Result<Handles> {
    let writer = pty.take_writer()?;           // 생성 시 1회 취득
    Ok(Handles { writer: Arc::new(Mutex::new(writer)), /* ... */ })   // 공유 배분
}
// 이후: 쓰기 요청을 큐로 모으고 전용 writer 스레드가 단독 소유하는 구조로 재정리
```
무엇이 깨졌나: "take"의 소유권 이전 계약을 "매번 새 핸들을 얻는다"로 읽었다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
