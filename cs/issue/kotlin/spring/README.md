# kotlin/spring — Spring·Jackson·아키텍처

Spring·Jackson과 모듈 구조에서 나오는 패턴이다.\
공통 원리: **내부 표현이 외부 계약으로 새지 않게 경계를 명시한다** — 직렬화 이름, 의존 방향, 입력 경로, 보조 기능 장애 모두 경계 밖으로 번지지 않게 막는다.

## 공통 원리

```
  외부 요청 ──▶ [경계] ──▶ 도메인 ──▶ [포트] ──▶ 인프라
                  │                     │
                  ├─ 경로 입력 → canonical 검증
                  ├─ 직렬화 이름 → 명시 매핑
                  └─ 보조 기능 장애 → 격리·강등 (핵심 경로 보호)
```

## 패턴 카드

- [dip-port-ownership](dip-port-ownership/) — 도메인이 포트를 소유하고(DIP) 모듈 의존 방향을 지키며, 리팩토링은 특성 테스트 안전망 위에서 한다.
- [graceful-degradation-fault-isolation](graceful-degradation-fault-isolation/) — 보조 기능(헬스 집계·통계·네이티브 라이브러리)의 장애가 핵심 경로를 인질로 잡지 못하게 격리·강등한다.
- [path-traversal-and-data-reality](path-traversal-and-data-reality/) — 외부 입력을 경로로 결합하면 트래버설로 경계를 벗어난다(검증은 canonical 경로·단일 검증 함수로) — 그리고 버그의 절반은 코드가 아니라 데이터 실태다.
- [serialization-contract-leak](serialization-contract-leak/) — 내부 필드명·네이밍 전략·디버그 표현이 직렬화를 통해 외부 계약이 된다 — 와이어 이름을 명시 매핑하고 양쪽 실제 직렬화 결과로 교차 검증한다.

> 이 폴더의 메타 태그: `least-privilege`(1) · `contract-drift`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
