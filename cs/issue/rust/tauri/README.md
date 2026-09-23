# rust/tauri — 커맨드 경계·등록

Tauri 커맨드 경계와 선언형 등록(capability·상태 주입)에서 나오는 패턴이다.\
공통 원리: **커맨드가 어느 스레드에서 도는지, 선언과 사용이 일치하는지는 컴파일러가 확인하지 않는다.**

## 공통 원리

```
  프런트 invoke ──▶ 커맨드 경계 ──▶ Rust 핸들러
                       │               │
                       │               ├─ 동기 커맨드 = UI 스레드 → 창 멈춤
                       │               └─ panic → 구조화 에러 아님
                       └─ capability·주입 등록 누락 → 런타임에만 throw
```

## 패턴 카드

- [command-boundary-execution-model](command-boundary-execution-model/) — Tauri 동기 커맨드는 메인(UI) 스레드에서 실행되고 커맨드 경계의 panic은 구조화된 에러가 되지 않는다 — 블로킹은 async·별도 스레드로, 실패는 Result로 전파한다.
- [registration-mismatch-runtime-failure](registration-mismatch-runtime-failure/) — 정적 capability ACL·TypeId 키 DI처럼 "선언과 사용의 불일치"는 컴파일·테스트를 통과하고 런타임에만 조용히 throw한다 — 선언을 사용처와 함께 검증한다.

> 이 폴더의 메타 태그: `silent-failure`(1) · `resource-bounding`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
