# cs/issue/rust/cargo/crate-module-boundary-rules — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[경계 1] 크레이트 = 링크 단위
   app 크레이트 ──의존──▶ GUI 프레임워크 ──링크──▶ 시스템 GUI 라이브러리
      └ list_dir() 테스트도 이 링크를 요구 💥 헤드리스 CI 에서 빌드 불가
   교정: workspace = [core(순수, serde 만), app(얇은 래퍼)]
         app::read_dir = core::list_dir(..).map_err(..)

[경계 2] 모듈 = privacy 단위
   parent ──▶ child::private_helper()   💥 부모는 자식 private 에 접근 불가
   child  ──▶ parent::private_item      ✓ 자식은 조상 private 에 접근 가능
   sibling_a ──▶ sibling_b::Struct{..}  💥 형제의 private 필드 struct 생성 불가
   교정: 원래 파일을 모듈 루트로 두고  mod sub; pub use sub::*;   (외부 경로 보존)
         부모가 부르는 헬퍼만 pub(super) · 형제 공유 타입은 공통 조상(루트)에

[경계 3] 크레이트 이름 = extern prelude 이름
   로컬 크레이트 "core"  ──가림──▶ 표준 ::core
      use core::...                  💥 어느 core 인가
      derive 매크로가 만든 ::core::marker::... 💥 로컬 core 로 해석
   교정: [lib] name = "core_lib"             (타깃 이름 자체를 바꿈 — 자기 bin 포함)
         또는 core_lib = { package = "core" } (의존하는 쪽에서 별칭)
```

## 핵심 문장

- 크레이트는 **링크 단위**다 — GUI·시스템 라이브러리에 링크되는 크레이트의 테스트는 그 라이브러리를 요구하므로, 테스트할 순수 로직은 **의존 없는 크레이트**로 뺀다.
- 모듈 privacy는 **자식→조상은 열리고, 조상→자식·형제↔형제는 닫힌다** — 공유 타입은 공통 조상에, 재노출은 `pub use`로.
- 순수 이동 리팩토링의 증거는 **공개 항목 집합 diff 0 + 테스트 개수 패리티 + 전 경로 참조 컴파일**이다.
- `core`·`std`·`alloc`은 extern prelude 이름이다 — 같은 이름의 로컬 크레이트는 **매크로가 생성한 `::core::` 경로까지** 가린다.
- 이름 충돌은 타깃 이름 변경(`[lib] name`) 또는 의존 별칭(`package = "core"`)으로 피한다.
