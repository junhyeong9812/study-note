# domain-modeling-basic/09-order-state — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다 (`/home/jun/project/myway/domain-modeling-basic/09-order-state/impl/`).

⚠️ 정답은 Claude 초안(2026-09-15) — 원본 impl 코드·README 측정 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. -->

### A. 과제 (OrderStateMachine.java 의 TODO 1~4)

#### 0. 요구사항 — 그림 한 장

- 표로 바꾸면 **8 × 8 = 64칸**, 채워진 칸은 **9개(14%)**, 빈칸 **55개(86%)**.
- 빈칸 55개는 각각 **"안 된다"(의도적 금지)** 이거나 **"아직 안 그렸다"(빠뜨림)** 다.\
  그림은 이 둘을 구별하지 않는다.

> **전이 표(transition table)** — 상태마다 "여기서 갈 수 있는 곳"을 적어둔 표.\
> 예: 8개 상태를 가로·세로에 늘어놓으면 64칸이 되고, 한 칸 한 칸이 "이 이동을 허용하나"라는 질문이 된다.

- 그림이 위험한 이유: **화살표 9개를 그리고 나면 "다 그린 것 같다".**\
  표를 그려야 비로소 55칸을 하나하나 판정하게 된다.
- 배송 중 취소: **규칙**이다.\
  자연법칙이 아니라 회사가 정한 것 — 다르게 정하는 회사도 있다.\
  impl 의 `standard()` javadoc 이 그걸 명시한다.
- 배송 완료 후 취소: 그림은 **답하지 않는다.**\
  표준 표는 DELIVERED → RETURN_REQUESTED 만 두어 "반품으로만 간다"로 답을 정했지만, 그건 그림이 아니라 **표를 만들면서 내린 결정**이다.
- 안 정해준 결정 셋: **① 같은 상태로의 전이를 멱등으로 볼 것인가**(`sameStateIsIdempotent`) **② 거부를 만나면 멈출 것인가 계속할 것인가** **③ "끝났다"를 어떻게 표현할 것인가**(필드 vs 표).

#### 1. TODO 1 — standard

```java
Map<OrderState, Set<OrderState>> table = new EnumMap<>(OrderState.class);
table.put(OrderState.PLACED,           EnumSet.of(OrderState.PAID, OrderState.CANCELLED));
table.put(OrderState.PAID,             EnumSet.of(OrderState.PREPARING, OrderState.CANCELLED));
table.put(OrderState.PREPARING,        EnumSet.of(OrderState.SHIPPED, OrderState.CANCELLED));
table.put(OrderState.SHIPPED,          EnumSet.of(OrderState.DELIVERED));
table.put(OrderState.DELIVERED,        EnumSet.of(OrderState.RETURN_REQUESTED));
table.put(OrderState.RETURN_REQUESTED, EnumSet.of(OrderState.REFUNDED));
table.put(OrderState.CANCELLED,        EnumSet.noneOf(OrderState.class));
table.put(OrderState.REFUNDED,         EnumSet.noneOf(OrderState.class));
return new OrderStateMachine(table, sameStateIsIdempotent);
```

```text
  PLACED ──► PAID ──► PREPARING ──► SHIPPED ──► DELIVERED ──► RETURN_REQUESTED ──► REFUNDED
    │         │           │                                                            (끝)
    └─────────┴───────────┴──► CANCELLED (끝)

  전이 9개:  PLACED→PAID, PLACED→CANCELLED, PAID→PREPARING, PAID→CANCELLED,
            PREPARING→SHIPPED, PREPARING→CANCELLED, SHIPPED→DELIVERED,
            DELIVERED→RETURN_REQUESTED, RETURN_REQUESTED→REFUNDED
```

- 취소 가능한 상태: **3 / 8** — PLACED, PAID, PREPARING.
- CANCELLED·REFUNDED 에는 **빈 집합**을 넣는다.\
  `allowedFrom` 이 `getOrDefault(state, noneOf)` 라 **결과는 같다.**\
  그런데 **명시적으로 넣는 쪽이 낫다** — "여기서 갈 곳이 없다"가 결정이라는 것을 표가 직접 말해주기 때문이다(빠뜨린 것과 구별된다).\
  이것이 바로 이 챕터의 주제인 "빈칸이 금지인가 누락인가"다.
- `EnumMap`·`EnumSet` 을 쓰는 이유: enum 전용 자료구조라 **배열/비트마스크로 구현돼 빠르고 메모리가 작으며**, 순회 순서가 enum 선언 순서로 **결정적**이다.

> **결정적(deterministic)** — 같은 입력을 몇 번 돌려도 순서까지 똑같이 나오는 성질.\
> 예: 일반 `HashMap` 은 순회 순서가 보장되지 않지만 `EnumMap` 은 언제나 enum 선언 순서로 돈다.

- `of(...)` 가 복사하는 이유: 호출자가 넘긴 맵을 **나중에 바꾸면 기계의 규칙이 몰래 바뀐다.**\
  복사해서 들고 있으면 기계가 만들어진 뒤 규칙이 불변이다.\
  게다가 빠진 상태를 빈 집합으로 채워 **모든 상태에 대한 항목이 있다는 것을 보장**한다.

> **방어적 복사(defensive copy)** — 밖에서 받은 자료구조를 그대로 들고 있지 않고, 복사본을 만들어 보관하는 것.\
> 예: 호출자가 넘긴 표에 나중에 `put` 을 하나 더 해도, 복사해 둔 기계의 규칙은 꿈쩍도 안 한다.

#### 2. TODO 2 — apply

```java
if (from == to) {                          // ① 같은 상태를 표보다 먼저 본다
    return sameStateIsIdempotent
            ? TransitionResult.ignored(from)
            : (allowedFrom(from).contains(to)
                    ? TransitionResult.applied(to)
                    : TransitionResult.rejected(from));
}
return allowedFrom(from).contains(to)      // ② 그 다음에 표를 본다
        ? TransitionResult.applied(to)
        : TransitionResult.rejected(from);
```

- 결과가 셋인 이유: 실제로 **질문이 둘**이기 때문이다 — "상태가 바뀌었나(후처리를 돌릴까)"와 "오류인가(경보를 울릴까)".\
  두 개의 예/아니오 조합 중 의미 있는 것이 셋이다.

```text
              changed()   isError()      의미
  APPLIED       true       false      바뀌었다 → 후처리를 돌린다
  IGNORED       false      false      안 바뀌었지만 잘못도 아니다 → 조용히 넘긴다
  REJECTED      false      true       허용되지 않는다 → 경보를 울린다
```

- 뭉갤 때의 두 사고: **IGNORED → APPLIED** 로 뭉개면 중복 이벤트가 **후처리를 두 번 돌린다**(포인트 2번 적립).\
  **IGNORED → REJECTED** 로 뭉개면 정상적인 재시도가 **실패로 보고되어 경보가 울린다.**

> **멱등(idempotent)** — 같은 요청을 두 번 보내도 결과가 한 번 보낸 것과 같은 성질.\
> 예: 결제완료 이벤트가 네트워크 재전송으로 두 번 와도 주문은 결제완료 한 번인 상태로 남는다.

- 순서가 결과를 바꾸는 입력: **표에 자기 전이가 있는 경우**(예: `SHIPPED → SHIPPED` 가 표에 있음) + 같은 상태로의 이벤트.

> **자기 전이(self-transition)** — 어떤 상태에서 자기 자신으로 가는 화살표.\
> 예: 배송 중에 위치가 갱신될 때마다 SHIPPED → SHIPPED 이벤트가 오는 표라면, 그 화살표가 실제로 의미를 갖는다.

```text
  표: SHIPPED → {SHIPPED, DELIVERED},  멱등 켬,  apply(SHIPPED, SHIPPED)

    같은 상태를 먼저 본다  ──►  IGNORED   (중복 이벤트로 본다)
    표를 먼저 본다        ──►  APPLIED   (위치 갱신으로 본다)
```

- 표준 표만으로는 무의미해 보이는 이유: 표준 표에는 **자기 전이가 하나도 없다.**\
  그래서 두 순서가 **항상 같은 답**을 낸다 — 순서를 뒤집는 변종이 테스트를 다 통과한다.
- 현실 사례: **"배송 중 위치 갱신"** — 같은 SHIPPED 상태로 다시 오는 것이 의미 있는 이벤트인 경우.
- 멱등 끄고(strict) 자기 전이가 표에 있으면: **APPLIED**(표를 따른다).
- 멱등 끄고 자기 전이가 표에 없으면: **REJECTED.**
- 거부·무시는 **원래 상태(from)** 를 담아 돌려준다.\
  그래서 부르는 쪽이 결과를 **조건 없이 대입**할 수 있다.

#### 3. TODO 3 — applyAll

```java
List<TransitionResult> results = new ArrayList<>();
OrderState current = start;
for (OrderState event : events) {
    TransitionResult result = apply(current, event);
    results.add(result);
    current = result.state();       // 조건 없이 대입한다
}
return results;
```

- PLACED 에서 [SHIPPED, PAID]:

```text
  ① apply(PLACED, SHIPPED)  →  REJECTED, state = PLACED   (멈추지 않는다)
  ② apply(PLACED, PAID)     →  APPLIED,  state = PAID

  최종 상태 = PAID
```

- 멈추기 vs 계속하기: **옳고 그름이 아니라 정해야 하는 규칙**이다.\
  여기서는 **계속한다** — 뒤의 이벤트가 유효할 수 있기 때문(위 예가 정확히 그 경우).
- 거부를 예외로 던지면: 측정상 무작위 이벤트의 **73%가 거부**다 → **예외가 정상 흐름이 된다.**\
  외부 이벤트를 받는 자리에서는 특히 그렇다 — 스택 트레이스가 로그를 덮고, 경보가 상시 울려 아무도 안 본다.
- `changed()` 를 확인하고 대입하는 코드가 아무 일도 안 하는 이유: **거부와 무시가 `from` 을 담아 돌려주기 때문**이다.\
  `changed()` 가 false 인 결과의 `state()` 는 이미 `current` 와 같다 → 대입해도 값이 안 바뀐다.\
  조건이 **항상 참인 것과 같은 효과.**
- 지우면 좋아지는 것: **죽은 분기가 사라진다.**\
  남겨두면 "이 조건이 뭔가를 막고 있다"는 착각을 주고, 변종 검증에서 그 조건을 지워도 아무 테스트가 안 깨져 **어느 쪽이 진짜 방어인지 알 수 없다**(06·08번과 같은 구조).

> **죽은 분기(dead branch)** — 있어도 실제로는 한 번도 갈라지지 않는 if 문.\
> 예: "바뀐 경우에만 대입한다"는 조건이, 안 바뀐 경우에도 같은 값을 대입하는 상황이면 아무것도 거르지 않는다.

- 불변식: **"거부와 무시는 원래 상태를 그대로 담아 돌려준다."**\
  지키는 것은 **계약 테스트** — 거부가 시도한 상태(`to`)를 담게 바꾸는 변종을 **테스트 3개**가 잡는다.

> **불변식(invariant)** — 프로그램이 도는 동안 언제 확인해도 참이어야 하는 조건.\
> 예: "거부 결과의 state 는 언제나 시도 전 상태다" — 이게 참이라서 대입 조건을 지울 수 있다.

> **변종 검증(mutation testing)** — 코드를 일부러 조금 틀리게 바꿔보고, 테스트가 그걸 잡아내는지 확인하는 방법.\
> 예: 거부가 `from` 대신 `to` 를 담게 바꿔 놓고 테스트를 돌렸더니 3개가 빨갛게 됐다면, 그 불변식은 실제로 지켜지고 있는 것이다.

#### 4. TODO 4 — reachableFrom

```java
Set<OrderState> seen = EnumSet.of(start);
Deque<OrderState> queue = new ArrayDeque<>();
queue.add(start);
while (!queue.isEmpty()) {
    OrderState current = queue.poll();
    for (OrderState next : allowedFrom(current)) {
        if (seen.add(next)) {       // 처음 본 것만 큐에 넣는다
            queue.add(next);
        }
    }
}
return seen;
```

- 그래프 대응: **정점 = 상태**, **간선 = 표의 전이 한 칸.**\
  표가 곧 인접 리스트다.

> **인접 리스트(adjacency list)** — 정점마다 "여기서 바로 갈 수 있는 정점들"을 목록으로 들고 있는 그래프 표현.\
> 예: `Map<OrderState, Set<OrderState>>` 전이 표가 그대로 인접 리스트다 — 따로 그래프를 만들 필요가 없다.

- BFS 절차: **시작 상태를 본 것으로 표시하고 큐에 넣는다 → 큐에서 하나 꺼내 그 상태에서 갈 수 있는 곳을 본다 → 처음 보는 곳이면 표시하고 큐에 넣는다 → 큐가 빌 때까지.**

> **BFS(너비 우선 탐색)** — 시작점에서 가까운 곳부터 큐로 차례차례 훑는 그래프 탐색.\
> 예: PLACED 에서 시작하면 한 걸음 거리인 PAID·CANCELLED 를 먼저 보고, 그 다음에 두 걸음 거리를 본다.

- 시작 상태는 **포함된다**(`EnumSet.of(start)` 로 시작).\
  그래서 terminal 상태의 답이 0이 아니라 1이다.
- CANCELLED 가 1인 이유: 나가는 간선이 없어서 **자기 자신만** 남는다.

> **종점 상태(terminal state)** — 나가는 화살표가 하나도 없는 상태.\
> 예: 취소됨·환불됨에 닿으면 표 위에서 더 갈 곳이 없다 — 그래서 닿을 수 있는 상태 수가 자기 자신뿐인 1이다.

- 잡을 수 있는 결함: **아무도 못 가는 상태**(도달 불가).\
  테스트에서 표를 끊으면 8개 중 6개만 닿고 RETURN_REQUESTED·REFUNDED 가 빠지는 것으로 잡힌다.

> **도달성(reachability)** — 시작 상태에서 화살표만 따라가 그 상태에 이를 수 있는가.\
> 예: DELIVERED → RETURN_REQUESTED 화살표를 빠뜨리면 반품요청·환불됨은 어디서도 못 가는 상태가 된다.

- 방치하면 남는 것: **그 상태를 다루는 코드**(UI 문구, 분기, 배치 처리)가 계속 남는다.\
  아무도 도달 못 하니 버그도 안 나고, 그래서 **아무도 지우지 않는다.**

### B. 개념

#### 5. 측정이 알려준 것

| | |
|---|---|
| 상태 | 8개 |
| 가능한 전이 칸 | 64개 |
| 표에 있는 전이 | **9개 (14%)** |
| 취소 가능한 상태 | 3 / 8 |

  → 빈칸 **86%.**

- 무작위 이벤트 10,000건:

| | 건수 |
|---|---|
| 적용 | 1,458 (15%) |
| 무시 | 1,281 (13%) |
| 거부 | **7,261 (73%)** |

- 설계 결론: **거부를 예외로 던지면 예외가 정상 흐름이 된다.**\
  거부는 **정상 응답**으로 표현해야 한다 — 그래서 `TransitionResult` 가 값(enum Kind)이지 예외가 아니다.
- 멱등 여부로 **730/1,000** 이 갈린다.
- 그런데 최종 상태는 **1,000/1,000** 이 같다.
- 그럼 멱등이 정하는 것: **상태가 아니라 "무엇을 오류로 볼 것인가"** — 그리고 그 판단이 **경보와 재시도**를 정한다.\
  `PLACED` 에서 `[PAID, PAID, PAID]` 를 받으면 멱등은 적용 1·무시 2(경보 0회), 엄격은 적용 1·거부 2(**경보 2회**).\
  상태는 둘 다 PAID.
- 상태별 닿을 수 있는 수:

| 상태 | 닿을 수 있는 상태 수 |
|---|---|
| PLACED | 8 |
| PAID | 7 |
| PREPARING | 6 |
| SHIPPED | **4** |
| DELIVERED | 3 |
| RETURN_REQUESTED | 2 |
| CANCELLED / REFUNDED | 1 |

- `PREPARING → SHIPPED` 한 걸음에 사라지는 것: **취소(CANCELLED)와 그 뒤가 통째로.**\
  6 → 4 로 두 개가 한꺼번에 준다.
- 이 수를 보면 **어디서 길이 좁아지는지**가 보인다 — 표를 눈으로 읽으면 "화살표가 하나 없네" 정도지만, 이 수는 "그 한 칸이 선택지를 둘 날린다"를 보여준다.

#### 6. 변종 검증에서 고친 것

- `applyAll` 에서 **`changed()` 를 확인하고 상태를 대입하던 것**을 **조건 없이 대입**으로 바꿨다.
- 아무 일도 안 하던 이유: 거부·무시가 **원래 상태를 담고 있어** 대입해도 값이 같다.\
  조건이 걸러내는 경우가 **하나도 없었다.**
- 지키는 테스트: **계약 테스트**(거부가 원래 상태를 준다 — `rejectionDoesNotStop` 에서 `results.get(0).state() == PLACED`).

> **계약 테스트(contract test)** — 구현 세부가 아니라 "밖에 약속한 동작"을 못 박는 테스트.\
> 예: "거부는 원래 상태를 담아 돌려준다"를 테스트가 들고 있으면, 나중에 누가 구현을 갈아엎어도 그 약속은 안 깨진다.

- 거부가 시도한 상태를 담게 바꾸는 변종은 **테스트 3개**가 잡는다.
- 08번과 같은 점: **서로를 덮는 중복 방어를 걷어내고, 남긴 하나를 테스트가 실제로 때리게 만든다.**\
  다른 점: 08번은 두 방어가 **서로를 덮어** 어느 쪽을 지워도 통과했고, 09번은 한 조건이 **애초에 아무것도 안 하고 있었다**(불변식 덕분에 항상 참).\
  08은 "둘 중 하나를 골라 지운다", 09는 "이미 죽은 조건을 지운다".

#### 7. 생각해볼 것

> 원본 README가 답을 주지 않고 던진 질문 — (원본에 근거 없음 — 내 추론) 표시.

- 조건부 전이: (내 추론) **표만으로는 표현할 수 없다.**\
  표의 칸은 "된다/안 된다"뿐이라 "금액이 0이면"이라는 술어를 담지 못한다.\
  방법은 둘 — ① 칸의 값을 `Set<State>` 에서 `조건 → State` 목록으로 올린다(표가 복잡해진다) ② 상태를 쪼갠다(`PLACED_FREE` / `PLACED_PAID_REQUIRED`).\
  ②가 표를 단순하게 유지하지만 상태 수가 늘어 64칸이 100칸이 된다.
- 부수 효과(알림·적립)의 자리: (내 추론) **부르는 쪽**이 낫다.\
  표에 붙이면 표가 "무엇이 허용되나"와 "무엇을 하나" 두 가지를 말하게 되어, 규칙을 읽으려면 부수 효과까지 읽어야 한다.\
  `TransitionResult` 가 `changed()` 를 주는 것이 바로 "부르는 쪽이 판단하라"는 설계다.

> **부수 효과(side effect)** — 값을 돌려주는 것 말고, 프로그램 바깥 세상을 바꾸는 일.\
> 예: 상태를 바꾸면서 알림 문자를 보내고 포인트를 적립하는 것 — 되돌리기가 어려워서 "몇 번 돌았나"가 중요해진다.

- 상태 이력: (내 추론) 지금 구조는 **현재 상태만** 들고 있다.\
  이력을 남기려면 `(주문, 이전 상태, 다음 상태, 시각, 사유, 행위자)` 를 append 하는 저장소가 필요하다.\
  지금 상태만으로 못 답하는 질문 — "언제 배송이 시작됐나", "취소 전에 결제까지 갔었나", "누가 바꿨나", "같은 이벤트가 몇 번 왔나".\
  특히 **IGNORED 는 상태를 안 바꾸므로 현재 상태에 흔적이 전혀 없다.**
- 관리자 강제 전이: (내 추론) 문을 만들되 **표를 우회하는 게 아니라 다른 표를 쓰게** 해야 한다 — `OrderStateMachine.of(관리자표, ...)` 처럼.\
  우회 함수(`forceSet`)를 만들면 그 경로를 지나는 전이는 아무 규칙도 안 받고, 결국 표는 "권고"가 된다.\
  대신 강제 전이는 **반드시 이력에 사유와 행위자를 남겨야** 한다.

#### 8. 연결

- "끝났다"를 별도 필드로 두면: 표와 필드가 **어긋나도 아무도 모른다**(표에는 나갈 길이 있는데 필드는 끝났다고 말하는 상태).\
  그래서 `OrderState.isTerminalIn(machine)` 이 **`machine.allowedFrom(this).isEmpty()`** 로 표에게 묻는다 — **단일 출처.**

> **단일 출처(single source of truth)** — 같은 사실을 두 곳에 적어두지 않고 한 곳에서만 관리하는 것.\
> 예: "끝났나"를 표에서 계산하면, 표를 고쳤을 때 따로 고쳐야 할 필드가 없어서 어긋날 자리 자체가 없다.

- **07번 알림과 같은 점**: 둘 다 "순서가 계약"이고, 둘 다 **표준 입력만으로는 그 순서가 무의미해 보인다.**\
  07은 자기 전이 대신 "미뤄진 알림들이 같은 시각이 되는" 경우에만 순서가 드러나고, 09는 "표에 자기 전이가 있는" 경우에만 드러난다.\
  교훈: **순서가 계약인 코드는, 그 순서가 실제로 갈리는 입력을 테스트가 반드시 들고 있어야 한다.**
- **11번 BFS**: 전이 표가 곧 그래프(정점=상태, 간선=전이)이므로 도달 가능성 문제가 그대로 그래프 탐색 문제가 된다 — 알고리즘을 새로 만들 게 아니라 이미 있는 것을 **알아보는 것**이 요점.
- 다른 도메인으로: **"허용 목록을 그림이 아니라 표로 그려라"** — 권한 체계(역할 × 동작), 워크플로 승인 단계, 상품 상태, 배송사 코드 매핑.\
  어디서든 "빈칸이 금지인가 누락인가"를 한 칸씩 판정하게 만드는 것이 표의 힘이다.

## 근거

- 기준 소스: `/home/jun/project/myway/domain-modeling-basic/09-order-state/impl/com/domain/order/OrderStateMachine.java`
- 문제 원문: `src/main/java/com/domain/order/OrderStateMachine.java`(TODO 1~4 javadoc), `OrderState.java`·`TransitionResult.java`(계약), `README.md`(세 결과·함정·측정·변종 검증·생각해볼 것)
- 수치 근거: `README.md` 측정 절 + `src/test/java/com/domain/order/MeasurementTest.java`(8·64·9·14·3 / 1,458·1,281·7,261·10,000·72 / 730·1,000 / 중복 3회 idem 1·0 과 strict 1·2 / 도달 8·7·6·4·3·2·1·1), `OrderStateTest.java`(정상 경로 APPLIED, SHIPPED·DELIVERED 취소 불가, terminal 판정, 되돌아가기 REJECTED, 멱등 IGNORED vs 엄격 REJECTED, 자기 전이 순서, [SHIPPED,PAID] 거부 후 계속, 도달 8개 / 끊긴 표 6개)
