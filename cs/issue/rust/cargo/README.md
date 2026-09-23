# rust/cargo — 크레이트·모듈 경계

cargo 빌드 단위와 모듈 가시성 규칙에서 나오는 패턴이다.\
공통 원리: **빌드 단위 경계가 코드 구조를 강제한다** — 테스트 가능한 순수 core를 무거운 링크 의존에서 분리한다.

## 공통 원리

```
  app 크레이트 ──링크──▶ GUI/네이티브 의존 (헤드리스 테스트 불가)
       │
       └─ core 크레이트 (순수 로직) ◀── 테스트는 여기서
```

## 패턴 카드

- [crate-module-boundary-rules](crate-module-boundary-rules/) — Rust 빌드 단위 경계(링크 의존 크레이트의 헤드리스 테스트 불가·extern prelude 이름 충돌·module privacy)는 코드 구조를 강제하므로 순수 core 분리·이름 회피로 대응한다.
