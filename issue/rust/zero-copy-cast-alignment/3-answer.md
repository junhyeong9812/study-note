# issue/rust/zero-copy-cast-alignment — 정답

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **오프셋 0과 8은 성공하고, 오프셋 1만 실패한다 — `try_` 계열은 `Err(TargetAlignmentGreaterAndInputNotAligned)`를 돌려주고, 그냥 캐스트 함수는 같은 조건에서 패닉한다.**\
   정렬 속성을 뺀(정렬 1) 페이지 타입을 버퍼 안의 세 오프셋에 두고 `[u64; 2048]`로 캐스트해 실측한 결과다.\
   대상 타입 `u64`의 정렬은 8이므로, 시작 주소가 8의 배수인지만이 성패를 가른다.
   > **제로 카피 캐스트(zero-copy cast)** — 바이트를 복사하지 않고 같은 메모리를 다른 타입의 참조로 다시 보는 것. 디스크 페이지를 노드 구조체로 바로 읽는 데 쓴다.
   > **정렬(alignment)** — 타입의 값이 놓일 수 있는 주소의 배수 조건. `u64`는 보통 8, `u8`은 1.

2. **Rust에서 정렬이 어긋난 참조는 존재하는 것만으로 정의되지 않은 동작이라, 안전한 캐스트 API는 주소를 검사해 그 경우를 거절해야 하기 때문이다.**\
   정렬 1인 타입은 "아무 주소나 된다"는 보장뿐이다. 실제 주소가 8의 배수일지는 그 버퍼가 어디에 놓였는지(할당 위치·다른 구조체 안의 오프셋)에 달려 있다.\
   우연히 8의 배수인 주소에 놓이는 동안 캐스트는 계속 성공하므로, 결함이 "가끔·어떤 환경에서만" 터지는 모습이 된다 — 항상 터지는 결함보다 찾기 어렵다.

3. **타입에 정렬을 박으면 비용 없이 모든 값이 정렬되지만 그 타입의 정렬 요구가 커진다. 정렬 무관 읽기는 어떤 바이트 위치에서도 동작하지만 매번 사본을 만든다.**\
   `#[repr(C, align(8))]`을 준 버퍼 타입은 컴파일러가 모든 값(스택·힙·다른 구조체의 필드)을 8의 배수 주소에 둔다 — 캐스트의 정렬 조건이 타입 수준에서 항상 참이 된다.\
   `pod_read_unaligned`는 바이트를 정렬된 새 값으로 복사한다. 16KB 페이지를 매번 복사하면 제로 카피의 이점이 사라지고, 사본을 고쳐도 원래 버퍼에 반영되지 않는다(쓰기 경로가 따로 필요).\
   페이지처럼 크고 자주 읽고 쓰는 버퍼라면 타입 정렬 쪽이 맞다.

4. **derive(Pod)는 패딩과 Pod가 아닌 필드를 컴파일 타임에 거부한다. 구조체가 정확히 한 페이지 크기인지는 derive가 모르므로 `const` 단언으로 따로 막는다.**\
   헤더 필드 하나를 `u64 → u32`로 바꾸면 뒤 필드 정렬 때문에 4바이트 패딩이 생기고, derive가 `derive(Pod) was applied to a type with padding`으로 빌드를 멈춘다(변이로 확인).\
   배열 길이를 한 칸 줄이면 구조체는 여전히 Pod이지만 페이지보다 작아진다 — `const _: () = assert!(size_of::<Node>() == PAGE_SIZE);`가 이것을 컴파일 오류로 바꾼다(변이로 확인).\
   주소 정렬은 값이 어디 놓이느냐의 문제라 이 둘 어느 쪽으로도 잡히지 않는다 — 그래서 질문 3의 타입 정렬이 필요하다.
   > **Pod(plain old data)** — 패딩이 없고 모든 비트 패턴이 유효해 바이트와 자유롭게 오갈 수 있는 타입.

5. **캐스트 라이브러리의 기본 설정은 배열 impl을 정해진 길이 목록(0..=32, 48, 64, 96, 128, 256, 512, 1024, 2048, 4096)에만 제공하기 때문이다.**\
   4096은 목록에 있고 16384는 없다. 임의 길이 `[T; N]` impl은 const generics 기능 플래그(`min_const_generics`)를 켜야 생긴다.\
   빌드 실패라 위험은 없지만, "임의 길이 배열이면 당연히 된다"는 가정이 첫 빌드에서 깨지는 지점이다 — 기능 플래그를 의존성 선언에 적어 두면 해소된다.

6. **정렬 결함은 주소에 달려 있어서, 테스트가 쓰는 버퍼가 우연히 정렬돼 있으면 같은 코드가 계속 초록이기 때문이다.**\
   결정적으로 재현하려면 주소를 운에 맡기지 않는다 — 넉넉한 바이트 버퍼 안에서 시작 오프셋을 직접 0·1·8로 밀며 같은 캐스트를 시도해, 오프셋 1에서만 실패하는 것을 본다.\
   고친 뒤에는 정렬을 타입이 보장하므로 이런 테스트 대신 "정렬 속성이 있다"는 사실 자체가 가드다(`align_of::<Page>() >= 8` 단언도 가능).

## 문제 구조 (추상화 코드)

### 변형 A — 정렬 1인 버퍼를 넓은 정렬의 구조체로 캐스트
① 문제 코드
```rust
#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable)]
struct Page([u8; PAGE_SIZE]);            // 정렬 1 — 주소는 1의 배수만 보장

#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable)]
struct Node { count: u64, next: u64, keys: [u64; N], values: [u64; N] }  // 정렬 8

let node: &Node = bytemuck::cast_ref(&page);   // page 주소가 8의 배수가 아니면 패닉
```
② 고친 코드
```rust
#[repr(C, align(8))]                     // 모든 Page 값의 주소를 8의 배수로
#[derive(Clone, Copy, Pod, Zeroable)]
struct Page([u8; PAGE_SIZE]);

const _: () = assert!(size_of::<Node>() == PAGE_SIZE);   // 크기는 derive가 모름 — 직접 단언
let node: &Node = bytemuck::cast_ref(&page);             // 정렬·크기 조건이 타입 수준에서 참
```
무엇이 깨졌나: 재해석의 네 조건 중 주소 정렬만 런타임 운에 맡겨져, 주소가 어긋난 경우에만 실패했다.

### 변형 B — 임의 길이 배열의 Pod·Zeroable impl 부재
① 문제 코드
```toml
bytemuck = { version = "1", features = ["derive"] }
# [u8; 16384]: Zeroable 미구현 → E0277 (기본 impl은 정해진 길이 목록뿐)
```
② 고친 코드
```toml
bytemuck = { version = "1", features = ["derive", "min_const_generics"] }   # 임의 길이 [T; N]
```
무엇이 깨졌나: "배열이면 길이와 무관하게 impl이 있다"는 가정이 라이브러리 기본 설정과 달랐다.

## 검증 기록
- 2026-11-17: 사건 기록 대조·추상화(Claude 초안) — 정렬 속성을 뺀 페이지 타입으로 오프셋 0·1·8 캐스트를 실측(1에서만 `TargetAlignmentGreaterAndInputNotAligned`), 패딩·크기 변이가 컴파일 오류로 잡힘을 확인. 기본 배열 impl 길이 목록과 `min_const_generics` 조건, 정렬·크기 검사 순서는 bytemuck 1.25.2 소스에서 확인.

## 참고
- bytemuck `try_cast_ref` · `PodCastError`: https://docs.rs/bytemuck/latest/bytemuck/fn.try_cast_ref.html
- bytemuck `pod_read_unaligned`: https://docs.rs/bytemuck/latest/bytemuck/fn.pod_read_unaligned.html
- Rust Reference — 타입 레이아웃과 `align` 수정자: https://doc.rust-lang.org/reference/type-layout.html

## 관련 카드
- [language-semantics-traps](../language-semantics-traps/) — Rust 표준 동작이 직관과 다른 지점들. 이 카드는 그중 메모리 레이아웃(정렬) 축이다.
- [byte-stream-framing](../../cross-cutting/data/byte-stream-framing/) — 바이트 경계와 의미 경계의 불일치라는 같은 계열. 저쪽은 읽기 경계, 이쪽은 주소 경계다.
