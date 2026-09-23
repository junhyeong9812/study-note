# rust — Rust 언어·크레이트 생태계

Rust 언어 규칙과 주요 크레이트(cargo·serde·tauri·tokio)에 뿌리내린 패턴이다.\
공통 원리: **컴파일러가 막아 주지 않는 영역(런타임 설정·선언과 사용의 불일치·표준 동작의 기본값)에서 결함이 숨는다.**\
언어 레벨 카드는 이 폴더에, 크레이트별 카드는 하위 폴더에 있다.

## 공통 원리

```
  컴파일 통과 ──▶ 런타임
      │              ├─ 해셔 랜덤 시드     → 영속 키 불안정
      │              ├─ debug panic / release wrap
      │              ├─ 임시값 수명의 락   → 교착
      │              └─ 선언 ↔ 사용 불일치 → 런타임 throw
      ▼
  "타입이 맞다" ≠ "동작이 맞다"
```

## 하위 폴더

| 폴더 | 카드 수 | 무엇 |
|------|---------|------|
| [cargo/](cargo/) | 1 | 크레이트·모듈 경계 |
| [serde/](serde/) | 1 | 데이터 모델 |
| [tauri/](tauri/) | 2 | 커맨드 경계·등록 |
| [tokio/](tokio/) | 1 | 비동기 런타임 |

## 패턴 카드 (이 폴더 직속)

- [language-semantics-traps](language-semantics-traps/) — Rust 표준 동작(랜덤 시드 해셔·debug panic/release wrap·eager `or`·임시값 수명의 MutexGuard·take 1회 취득)이 직관과 달라 영속 키·교착·오버플로를 만든다.

> 이 폴더의 메타 태그: `silent-failure`(1) · `resource-bounding`(2) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../README.md#태그-역인덱스).
