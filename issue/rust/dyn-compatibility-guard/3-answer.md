# issue/rust/dyn-compatibility-guard — 정답

태그: `contract-drift`

## 정답
<!-- 질문 1:1 대응 -->

1. **trait 정의 파일은 조용히 컴파일되고, 에러는 `dyn Store`를 쓰는 곳에서 E0038 "the trait `Store` is not dyn compatible"로 난다.**\
   trait에 제네릭 메서드를 넣는 것 자체는 합법이다 — 그 trait를 제네릭 바운드(`T: Store`)로만 쓰면 아무 문제가 없다.\
   문제는 `dyn Store` 타입을 만드는 순간에만 검사된다. 그래서 에러 위치는 변경한 trait가 아니라 `Box<dyn Store>`를 쓰는 다른 모듈의 줄이다(note가 원인 메서드를 가리키긴 한다).
   > **dyn 호환성(dyn compatibility)** — trait를 `dyn Trait` 타입(trait 객체)으로 쓸 수 있는 조건. 예전 이름은 object safety이고, 현재 Rust 레퍼런스와 컴파일러 메시지는 "dyn compatible"을 쓴다.

2. **vtable은 메서드마다 함수 포인터 한 칸인데, 제네릭 메서드는 함수 하나가 아니라 타입 인자마다 따로 만들어지는 함수 족이기 때문이다.**\
   `dyn Store`의 메서드 호출은 vtable에서 함수 포인터를 꺼내 부르는 동적 디스패치다. vtable은 구현 타입이 정해질 때 한 번 만들어지므로, 그때 모든 메서드의 기계어가 확정돼 있어야 한다.\
   `visit<F>`는 호출하는 쪽이 넘기는 `F`마다 단형화되므로, vtable을 만드는 시점에는 어떤 `F`들이 필요할지 알 수 없다 — 한 칸에 담을 수 없다.\
   레퍼런스가 나열하는 다른 모양으로는 `Self`를 값으로 받거나 돌려주는 메서드(`fn clone_me(&self) -> Self`), 수신자가 없는 연관 함수, 연관 상수, `Sized`를 상위 trait로 요구하는 trait 등이 있다(각각 `where Self: Sized`로 dyn에서 빼는 예외가 있다).
   > **단형화(monomorphization)** — 제네릭 함수를 실제로 쓰인 타입 인자마다 별도 함수로 복사해 컴파일하는 방식. 정적 디스패치의 기반이다.

3. **`dyn Store`를 쓰는 코드가 컴파일될 때 비로소 발견된다 — 그런 코드가 없으면 발견되지 않는다.**\
   제네릭 사용처만 있으면 모든 것이 컴파일되고 테스트도 통과한다(rustc 1.92에서 확인).\
   dyn 사용처가 다른 크레이트에 있으면 그 크레이트를 빌드할 때, 아직 작성되지 않았으면 그것을 작성하는 날에 터진다 — 변경한 사람과 시점에서 멀어질수록 "왜 깨졌나"를 찾는 비용이 커진다.\
   이 사례의 trait는 다음 단계에서 구현들을 `Box<dyn …>`로 바꿔 끼우는 용도였다 — dyn으로 쓰일 수 있다는 것은 문서 주석이 아니라 실제 계약이었다.

4. **값은 `None`이라 아무것도 만들지 않지만, 타입 `&dyn Store`를 적는 것만으로 dyn 호환성 검사가 일어나기 때문이다.**\
   `const _`는 이름 없는 상수 항목이다 — 컴파일 때 평가되고, 아무도 참조하지 않으므로 바이너리에 코드를 남기지 않는다.\
   `Option<&dyn Store>`라는 타입이 성립하려면 `dyn Store`가 유효한 타입이어야 하고, 이는 곧 `Store`가 dyn 호환이어야 한다는 뜻이다.\
   값으로 `None`을 쓰므로 `Store`의 구현체가 하나도 없어도 된다 — trait 정의 바로 옆, 같은 모듈에 둘 수 있다.\
   결과적으로 "이 trait는 dyn으로 쓰인다"는 암묵적 계약이 정의 옆의 컴파일 타임 단언이 된다. 깨지면 에러가 이 줄을 가리킨다.
   > **정적 단언(static assertion)** — 조건을 컴파일 타임에 검사해 어기면 빌드를 실패시키는 코드. 실행 경로가 없어도 매 빌드마다 검사된다.

5. **일부러 깨뜨려 본다 — trait에 제네릭 메서드를 넣는 변이를 가하고, 가드 줄에서 E0038이 나는지 본 뒤 원복한다.**\
   "가드가 있고 컴파일이 통과한다"는 계약이 지켜지고 있다는 뜻일 수도, 가드가 아무것도 검사하지 않는다는 뜻일 수도 있다 — 둘을 가르는 것은 실패하는 입력이다.\
   이 사례는 변이로 E0038 "not dyn compatible"이 나는 것을 확인했다.\
   변이 뒤에는 원본으로 되돌아왔는지도 확인해야 한다 — 이 사례에서도 원복 명령이 실패해 변이가 남은 것을 재확인 단계에서 발견해 지웠다.

6. **할 수 있다 — 무엇을 포기할지 고른다.**
   - **`where Self: Sized`** — `fn visit<F: Fn(u64)>(&self, f: F) where Self: Sized;`. 이 메서드는 vtable에서 빠지므로 trait는 dyn 호환으로 남는다(가드 통과 — rustc 1.92에서 확인). 대신 `dyn Store`로는 이 메서드를 부를 수 없다 — 구체 타입·제네릭에서만 쓴다.
   - **확장 trait로 분리** — 컴파일러도 "consider moving `visit` to another trait"를 제안한다. 핵심 trait는 dyn 호환으로 두고, 제네릭 메서드는 `trait StoreExt: Store`에 블랭킷 구현으로 둔다. 핵심 계약이 깨끗해지는 대신 trait가 둘이 된다.
   - **제네릭 대신 trait 객체 인자** — `fn visit(&self, f: &dyn Fn(u64))`로 바꾸면 메서드 자체가 dyn 호환이 된다. 호출마다 동적 디스패치 비용이 든다.

## 문제 구조 (추상화 코드)

### 변형 A — trait 변경이 먼 곳의 dyn 사용처에서야 깨짐
① 문제 코드
```rust
// store 모듈
pub trait Store {
    fn insert(&mut self, key: u64, value: u64) -> Option<u64>;
    fn get(&self, key: u64) -> Option<u64>;
    fn visit<F: Fn(u64)>(&self, f: F);          // 나중에 추가 — 여기선 컴파일 ✅
}

// 다른 모듈(또는 다음 단계에 작성될 러너)
fn pick(kind: Kind) -> Box<dyn Store> { /* ... */ }   // 여기서 처음 E0038 💥
```
② 고친 코드
```rust
// store 모듈
pub trait Store {
    fn insert(&mut self, key: u64, value: u64) -> Option<u64>;
    fn get(&self, key: u64) -> Option<u64>;
}

// 구현들을 Box<dyn Store> 로 바꿔 끼운다 — dyn 으로 못 쓰이게 바뀌면 여기서 컴파일이 깨진다.
const _: Option<&dyn Store> = None;
```
무엇이 깨졌나: "dyn으로 쓰인다"는 계약이 trait 선언 어디에도 적혀 있지 않아, 계약을 깨는 변경이 정의 쪽에서 조용히 통과했다.

검증: 변이(제네릭 메서드 추가) → 가드 줄에서 E0038 → 원복 후 원본과 동일함 재확인.

## 검증 기록
- 2026-11-12: 사건 기록 대조·추상화(Claude 초안) — 가드 없는 경우 제네릭 사용처만으로는 통과·dyn 사용처에서 E0038, 가드 줄의 E0038, `where Self: Sized`로 가드 통과를 rustc 1.92.0에서 확인. dyn 호환성 규칙 목록은 Rust 레퍼런스 기준.

## 참고
- Rust Reference — Dyn compatibility: https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility
- Rust 에러 색인 E0038: https://doc.rust-lang.org/error_codes/E0038.html

## 관련 카드
- [registration-mismatch-runtime-failure](../tauri/registration-mismatch-runtime-failure/) — 같은 "선언과 사용의 불일치" 축이지만, 그쪽은 컴파일러가 아예 못 잡아 런타임에 throw하는 경우다. 이 카드는 컴파일러가 잡지만 먼 곳에서 잡는 경우를 정의 옆으로 당긴다.
- [green-masking](../../cross-cutting/testing/green-masking/) — 가드도 실패할 수 있었을 때만 증거다 — 변이로 이빨을 확인하는 같은 원리.
