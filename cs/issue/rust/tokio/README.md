# rust/tokio — 비동기 런타임

tokio 런타임과 `select!` 루프 의미에서 나오는 패턴이다.\
공통 원리: **`select!`는 분기 본문이 도는 동안 다른 분기를 보지 않는다** — 본문은 짧게, 닫힌 채널은 분기에서 제거한다.

## 공통 원리

```
  loop { select! {
     a = rx_a.recv() => { 긴 await ... }   ← 이 동안 b는 poll 안 됨
     b = rx_b.recv() => { ... }            ← 닫힌 채널 = 항상 준비 → busy loop
  } }
```

## 패턴 카드

- [select-loop-semantics](select-loop-semantics/) — tokio `select!`는 분기 본문의 await 동안 다른 분기를 poll하지 않고 닫힌 채널은 영원히 준비 상태이며 런타임 드라이버는 명시적으로 켜야 한다 — 읽기·쓰기를 독립 future로 분리하고 종료 조건을 모든 분기에서 처리한다.

> 이 폴더의 메타 태그: `resource-bounding`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
