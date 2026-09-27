# java/spring — Spring·JPA 기본 동작

Spring·JPA가 명시하지 않은 부분을 채우는 기본 동작에서 나오는 패턴이다.\
공통 원리: **프레임워크의 암묵 기본값은 계약이다** — 코드에 드러나지 않는 동작을 명시로 끌어올린다.

## 공통 원리

```
  내 코드 ──▶ 프레임워크 (프록시·자동설정·영속성 컨텍스트)
                 │
                 ├─ 같은 빈 내부 호출 → 프록시 우회
                 ├─ 조건 평가 순서    → 빈 미등록
                 └─ 전체 컬럼 UPDATE  → 의도치 않은 덮어쓰기
```

## 패턴 카드

- [framework-default-contracts](framework-default-contracts/) — Spring·JPA의 기본 동작(프록시 self-invocation·자동설정 back-off·빈 이름 파생·정적 전체 UPDATE·save=merge·필터 자동등록·조건 평가 순서)은 명시하지 않으면 조용히 다르게 동작한다.
