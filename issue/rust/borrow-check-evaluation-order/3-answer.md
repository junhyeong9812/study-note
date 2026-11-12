# issue/rust/borrow-check-evaluation-order — 정답

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **컴파일되지 않는다 — E0502 "cannot borrow `*self` as immutable because it is also borrowed as mutable".**\
   `&mut self.items[...]`는 `IndexMut::index_mut(&mut self.items, 인덱스)`로 풀린다.\
   수신자 `self.items`의 가변 빌림이 먼저 잡히고, 그 다음 인덱스 식 `self.slots[self.slot(key)]`가 평가된다.\
   `self.slot(key)`는 `&self`를 받으므로 `self` 전체를 불변으로 빌린다 — `self.items`는 `self`의 일부라, 살아 있는 가변 빌림과 겹친다.\
   에러 메시지도 세 위치를 짚는다: 가변 빌림(`self.items`), 불변 빌림(`self` — slot 호출), 가변 빌림의 이후 사용(인덱싱 결과).
   > **E0502** — 같은 값을 가변으로 빌린 동안 불변으로 다시 빌리려 할 때(또는 그 반대) 나는 빌림 충돌 에러.

2. **2단계 빌림은 정해진 경우에만 적용된다.**\
   `v.push(v.len())`에서 `push`의 수신자 `&mut v`는 autoref로 만들어지는 빌림이라, 컴파일러가 이를 "예약(reserve)"만 해 두고 인자 `v.len()`의 불변 빌림을 허용한 뒤 호출 시점에 "활성화"한다.\
   rustc 개발 가이드가 밝힌 적용 대상은 autoref 메서드 수신자, 함수 인자의 가변 재빌림, 오버로드된 복합 대입 연산자의 암묵적 가변 빌림이다.\
   오버로드된 인덱싱(`IndexMut`)은 이 목록에 없다 — 그래서 `v[v.len() - 1] = x`는 `v`의 가변 빌림이 인덱스 식보다 먼저 활성화돼 E0502가 난다(rustc 1.92에서 확인).
   > **2단계 빌림(two-phase borrow)** — 가변 빌림을 "예약"과 "활성화" 두 단계로 나눠, 예약과 활성화 사이에는 같은 값의 공유 읽기를 허용하는 규칙. `vec.push(vec.len())` 같은 중첩 호출을 위해 도입됐다.

3. **필드 읽기는 필드 단위로, 메서드 호출은 시그니처 단위로 빌린다.**\
   `self.slots[k]`는 `self.slots` 자리만 불변으로 빌린다 — `self.items`와 겹치지 않는 자리라서 빌림 검사기가 둘을 분리해(disjoint field borrow) 허용한다.\
   `self.slot(k)`는 본문이 `self.slots`만 읽더라도, 시그니처가 `&self`이므로 `self` 전체를 빌린 것으로 본다.\
   빌림 검사는 함수 단위로 이뤄지고, 호출된 함수의 본문은 들여다보지 않는다 — 시그니처가 계약이다.
   > **필드 단위 빌림 분리(disjoint field borrows)** — 한 함수 본문 안에서 구조체의 서로 다른 필드를 따로 빌리면 동시에 가변·불변으로 빌릴 수 있다. 메서드 경계를 넘으면 이 분리가 사라진다.

4. **둘 다 "겹치는 시간"을 없애지만, 없애는 축이 다르다.**
   - **인덱스를 먼저 계산** — `let id = self.slots[self.slot(key)]; let b = &mut self.items[id];`. 불변 빌림을 첫 문장 안에서 끝내 **시간 축**으로 겹침을 없앤다. 인덱스가 `Copy` 값(usize)이라 빌림이 남지 않는다. 이 사례가 고른 방법이고, 컴파일러의 제안(`try adding a local storing this`)과 같다.
   - **필드만 받는 연관 함수로 쪼개기** — `Self::slot_of(&self.slots, depth, key)`처럼 필요한 필드만 인자로 받게 하면 **자리 축**으로 겹침을 없앤다(`items`를 빌리지 않음). 같은 패턴이 여러 곳에 반복되거나, 인덱스 계산 결과가 참조라 먼저 꺼내 둘 수 없을 때 맞다. 대신 시그니처가 내부 필드 구성을 드러낸다.
   인덱스가 `Copy` 값이고 한두 곳이면 앞의 방법이 가장 작은 변경이다.

5. **이 경우는 같다 — 두 문장 사이에 상태를 바꾸는 코드가 없기 때문이다.**\
   원래 식에서도 인덱스는 `index_mut` 호출 전에 한 번 평가된다. 그 값을 앞 문장으로 올려도 사이에 `self`를 바꾸는 코드가 없으므로 같은 버킷을 가리킨다.\
   의미가 달라지는 경우는 두 문장 사이에 인덱스의 근거가 되는 상태를 바꾸는 코드가 끼는 경우다 — 예: 인덱스를 계산한 뒤 구조를 키우거나(분할) 재배치하면, 미리 계산한 인덱스는 낡은 값이 된다. 같은 함수에서 분할 루프는 매 반복마다 인덱스를 다시 계산한다.

6. **시그니처가 약속하는 것은 "이 함수는 `self` 어디든 읽을 수 있다"이고, 컴파일러는 그 약속만 믿는다.**\
   `slot`의 본문이 지금은 `slots`만 읽지만, 시그니처상 `items`를 읽어도 된다. 그런데 `items`의 한 칸에 대한 `&mut`이 살아 있는 동안 같은 `items`를 읽으면 "가변 참조는 유일하다"는 규칙이 깨진다.\
   본문을 보지 않고 시그니처로만 판단하기 때문에, 함수 본문을 고쳐도 호출처의 빌림 판정이 바뀌지 않는다 — 판정이 지역적이고 안정적이다. 대가는 "실행하면 안전했을 코드"의 일부를 거부하는 보수성이고, 그 비용은 대개 지역 변수 한 줄이다.

## 문제 구조 (추상화 코드)

### 변형 A — `&mut` 인덱싱의 인덱스 식이 `&self` 메서드를 호출
① 문제 코드
```rust
struct Table {
    slots: Vec<usize>,          // 칸 → 버킷 번호
    items: Vec<Bucket>,
    depth: u32,
}

impl Table {
    fn slot(&self, key: u64) -> usize { /* self.depth 비트로 칸 번호 계산 */ }

    fn insert(&mut self, key: u64, value: u64) {
        let b = &mut self.items[self.slots[self.slot(key)]];   // E0502
        //           ^^^^^^^^^^ 가변 빌림 시작   ^^^^ &self — self 전체 불변 빌림
        // ...
    }
}
```
② 고친 코드
```rust
fn insert(&mut self, key: u64, value: u64) {
    let id = self.slots[self.slot(key)];   // 불변 빌림은 이 문장에서 끝남 (usize 는 Copy)
    let b = &mut self.items[id];           // 가변 빌림은 여기서 시작
    // ...
    loop {
        let id = self.slots[self.slot(key)];   // 구조가 바뀌는 루프 안에서는 매번 다시 계산
        // ... 넘치면 분할
    }
}
```
무엇이 깨졌나: "인덱스 식이 먼저 평가되고 그 다음 가변 빌림"이라는 직관과 달리, `IndexMut`는 수신자의 가변 빌림이 먼저 잡히고 2단계 빌림의 대상도 아니다.

### 같은 규칙의 최소 재현
```rust
fn f(v: &mut Vec<u64>) {
    v.push(v.len() as u64);   // ✅ autoref 수신자 — 2단계 빌림
    v[v.len() - 1] = 2;       // 💥 E0502 — IndexMut 은 2단계 빌림 없음
    let n = v.len();
    v[n - 1] = 2;             // ✅ 먼저 계산
}
```

## 검증 기록
- 2026-11-12: 사건 기록 대조·추상화(Claude 초안) — 문제 코드·고친 코드와 위 최소 재현 4줄은 rustc 1.92.0에서 컴파일해 E0502/통과를 확인. 2단계 빌림 적용 대상은 rustc 개발 가이드 기준.

## 참고
- rustc dev guide — Two-phase borrows: https://rustc-dev-guide.rust-lang.org/borrow_check/two_phase_borrows.html
- Rust 에러 색인 E0502: https://doc.rust-lang.org/error_codes/E0502.html

## 관련 카드
- [language-semantics-traps](../language-semantics-traps/) — 같은 "식의 평가·수명 규칙이 직관과 다르다" 축이지만, 그쪽은 컴파일을 통과한 뒤 런타임에 드러나는 함정(임시값 수명의 락 가드 등)이다.
