# testing — 초록불의 증거력

테스트와 측정이 결함 유무를 제대로 말해 주는지에 관한 패턴이다.\
공통 원리: **초록불은 그 테스트가 실패할 수 있었을 때만 증거다** — 환경이 실행 환경을 재현하고, 격리돼 있고, 도구 기본값을 이해하고 있어야 한다.

## 공통 원리

```
  코드 결함 있음 ──▶ 테스트 ──▶ 초록?
                       │
                       ├─ 무단언·약한 단언·수집 누락  → 위장 초록
                       ├─ 검증 환경 ≠ 실행 환경       → 무관한 결과
                       ├─ 공유 상태·시드·스케줄링     → 비결정
                       └─ 도구 기본값 오해            → 검사 안 됨
                                  ▼
            "통과" ≠ "검증" — 실패 재현부터 확인
```

## 패턴 카드

- [green-masking](green-masking/) — 초록불은 테스트가 실패할 수 있었을 때만 증거다 — 무단언·약한 단언·수집 누락·캐시된 결과·표현 못 하는 픽스처·버그를 고정한 기대값은 결함을 통과시키므로 뮤테이션·대조군으로 이빨을 확인한다.
- [performance-measurement-validity](performance-measurement-validity/) — 측정값이 유효하려면 생존자 편향·JIT 워밍업·수렴 전 캐시·생성기 자체의 자원 한계·데이터 부재를 배제해야 한다.
- [test-isolation-and-determinism](test-isolation-and-determinism/) — 테스트 결과가 코드가 아니라 환경(공유 상태 디렉토리·재사용 컨테이너·시드 상수·스레드 스케줄링)에 좌우되지 않게 격리하고 happens-before를 보장한다.
- [test-tool-default-semantics](test-tool-default-semantics/) — 테스트 도구의 기본 의미(비선점 타임아웃·중첩 클래스 섀도잉·mock 패치 경로·호이스팅·lifespan 미실행·로거 비활성화)는 직관과 달라 테스트가 소실·무한 대기·무효화된다.
- [verification-environment-parity](verification-environment-parity/) — 검증 환경(헤드리스 모드·jsdom·H2·standalone MockMvc·빌드 스테이지·curl)이 실행 환경을 재현하지 않으면 테스트는 결함 유무와 무관한 결과를 낸다 — 실제 경로·실 DB로 검증한다.

> 이 폴더의 메타 태그: `test-reliability`(5) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
