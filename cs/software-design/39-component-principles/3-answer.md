# software-design/39-component-principles — 정답

## 정답

### 1. 컴포넌트 묶음이 나쁠 때

- 따로 빌드·시험·릴리스할 수 없다. 한 컴포넌트를 고치면 순환이나 불필요한 의존으로 묶인 다른 컴포넌트까지 함께 배포해야 한다.
- 응집 3원칙(REP·CCP·CRP): 무엇을 한 배포 단위에 묶을지.
- 결합 3원칙(ADP·SDP·SAP): 배포 단위 사이 의존을 어떻게 둘지.

### 2. 응집 3원칙

- REP: 재사용 단위 = 릴리스 단위. 버전으로 릴리스된 것만 효과적으로 재사용된다.
- CCP: 같은 종류의 변경에 함께 닫힌 클래스끼리 묶는다. 변경은 패키지 안 모든 클래스에 영향을 준다.
- CRP: 함께 재사용되는 클래스끼리 묶는다. 하나를 쓰면 전부를 쓰는 셈이다.
- 긴장 예: CCP만 따라 "환불 관련 전부"를 한 모듈에 넣으면, 그중 날짜 유틸만 쓰는 소비자도 환불 변경마다 끌려 릴리스된다(CRP 위반). 반대로 CRP만 따라 잘게 쪼개면 정책 변경 하나가 여러 모듈 릴리스로 퍼진다(CCP 위반).

### 3. SDP·SAP와 지표

```text
 SDP: 불안정(web) → 중간(usecases) → 안정(entities)   의존은 안정된 쪽으로
 SAP: A ▲  주계열 A + I = 1  — 안정(I 낮음)할수록 추상(A 높음)
```

- Ca: 밖에서 안의 클래스에 의존하는 클래스 수. Ce: 안에서 밖의 클래스에 의존하는 클래스 수.
- I = Ce/(Ca+Ce), A = 추상 클래스 수/전체 클래스 수.
- D = |A+I−1|/√2(0~0.707), Dn = |A+I−1|(0~1). Martin 1994-10-28 논문.

### 4. acyclic판의 I

(실험 A, 2026-10-02)

```text
entities    5   0  0.00  0.50  0.50   []
usecases    2   2  0.50  0.50  0.00   [entities]
db          1   1  0.50  0.00  0.50   [entities, usecases]
web         0   2  1.00  0.00  0.00   [db, entities, usecases]
```

- entities 0.00, usecases 0.50, db 0.50, web 1.00.
- 모든 의존 간선이 I가 같거나 작은 쪽으로 향한다(web 1.00 → 0.50·0.00, db 0.50 → 0.50·0.00, usecases 0.50 → 0.00). SDP와 맞다. db → usecases는 I가 같은 쪽으로의 의존이다.

### 5. import 한 줄로 생긴 순환

```text
  entities 빌드 실패: cyclic/entities/comp/entities/Order.java:2: error: package comp.web does not exist
  usecases 빌드 실패: ... package comp.entities does not exist
SCC: [[usecases, web, entities, db]]
순환 있음 → 위상 순서(빌드 순서) 없음
```

- 첫 컴포넌트 `entities`가 `web`을 요구해 빌드가 막히고, 뒤는 연쇄로 실패했다.
- 컴파일러는 import 줄(`Order.java:2`)에서 멈추지만, 의존의 실체는 8행의 사용(`WebFormat` 생성·호출)이다. ArchUnit은 이 사용 지점을 보고한다.
- SCC가 컴포넌트별 4개에서 하나(4개 전부)로 합쳐졌다.
- 프로그램 출력은 두 판 모두 `o-1 12,000원`. 순환은 실행이 아니라 독립 빌드·릴리스를 깬다.

### 6. SCC 1개 vs 순환 4개

- SCC는 서로 닿는 정점의 최대 묶음이다. ArchUnit은 그 안의 개별 순환 경로(db→entities→web→db, db→usecases→entities→web→db, entities→web→entities 등)를 각각 보고했다(`violated (4 times)`).
- 끊을 곳: 보고된 경로들이 공통으로 지나는 의존을 찾는다. 이 실험에서는 모두 `Order.java:8`(`entities → web`)을 지난다. 그 간선 하나를 끊으면 전부 사라진다(acyclic판은 `순환 없음`).

### 7. cyclic판의 지표 변화

```text
entities    5   1  0.17  0.50  0.33   [web]
web         1   2  0.67  0.00  0.33   [db, entities, usecases]
```

- `entities`의 I: 0.00 → 0.17. `web`의 Ca: 0 → 1.
- 더 안정된 `entities`(0.17)가 덜 안정된 `web`(0.67)에 의존한다. SDP 위반이고, 순환이므로 ADP 위반이기도 하다.

### 8. entities의 Dn = 0.5

- 꼭 나쁘다고 할 수 없다. 엔티티는 `Order`·`Money` 같은 구체 값 객체가 핵심이라 추상도가 낮은 것이 자연스럽다. 이 실험의 추상 클래스 2개는 `MoneyFormat`·`OrderPolicy` 인터페이스다.
- 지표는 판정이 아니라 질문거리다. "이 안정된 구체 클래스를 바꿔야 하면 무엇이 끌려오나?"를 묻고, 그 변경 가능성이 낮으면 그대로 둔다.

### 9. 순환 끊기

- Martin "Granularity" 「Breaking the Cycle」: ① DIP — 필요한 인터페이스를 의존받는 쪽에 두고 반대쪽이 구현해 방향을 뒤집는다. ② 둘이 함께 의존하는 새 패키지를 만들고 공통 클래스를 옮긴다.
- 실험의 acyclic판은 ①이다. `entities`가 `MoneyFormat`을 소유하고 `web`의 `WebFormat`이 구현한다.

### 10. 네 모듈 동시 배포

- 신호: 모듈을 따로 빌드하면 `package ... does not exist`(실험 A), ArchUnit `Cycle detected`(실험 B), Tarjan SCC 크기 2 이상, 안정된 모듈의 I 상승.
- 고치기: 순환 경로의 공통 간선을 찾아 DIP 또는 공통 컴포넌트 추출로 끊는다. `slices().matching("..(*)..").should().beFreeOfCycles()`를 빌드 테스트에 넣어 재발을 막는다.
