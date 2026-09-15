# domain-modeling/basic/09-order-state — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 서머리(Claude 작성) — 원본 myway 코드·문서 기준.

## 한눈에 — 쉽게 말하면

**주문 상태 전이 = 보드게임의 말판.**

- 주문은 말판 위의 말이다.\
  "결제완료" 칸에서 "준비중" 칸으로는 갈 수 있지만, "결제완료"에서 "배송완료"로 **건너뛸 수는 없다.**\
  갈 수 있는 길은 규칙표가 정한다.
- 그림으로 화살표 9개를 그리면 다 그린 것 같다.\
  그런데 표로 그리면 8×8 = 64칸이고 **55칸이 비어 있다.**\
  그 빈칸이 "안 된다"인지 "아직 안 그렸다"인지 — 그게 이 챕터의 주제다.
- 그리고 핵심 질문 하나: "결제완료 이벤트가 **두 번** 오면?"\
  두 번째는 성공도 실패도 아닌 제3의 것(무시)이다.\
  **참/거짓 하나로는 못 담는다.**
- 실무 예: 쇼핑몰 주문 상태, 결제 상태(10번), 티켓 워크플로우, 배포 파이프라인 상태.

```text
  주문됨 → 결제완료 → 준비중 → 배송중 → 배송완료 → 반품요청 → 환불됨
    |         |         |
    +---------+---------+──→ 취소됨        ← 배송중부터는 취소 불가

  화살표 9개 / 가능한 칸 64개 = 14%.  나머지 86%는 전부 "거부"다.
```

## 문제 — 이 챕터가 시키는 것

원본 README가 준 것은 그림 한 장과 한 문장이다.

```text
  결제완료 -> 준비중 -> 배송중 -> 배송완료 -> 반품요청 -> 환불됨
     |         |
     +---------+---> 취소됨
```

> **그림으로 그리면 화살표가 9개라 다 그린 것 같다.**
> 표로 그리면 8×8 = 64칸이고, **55칸이 비어 있다.**
> 그 빈칸이 "안 된다"인지 "아직 안 그렸다"인지가 이 박스의 주제다.

세 결과를 구별하라는 것도 문제가 못 박은 계약이다.

```text
  APPLIED   상태가 바뀌었다        changed=true   isError=false
  IGNORED   이미 그 상태다         changed=false  isError=false
  REJECTED  허용되지 않는 전이다    changed=false  isError=true
```

**불리언 하나로는 이 셋을 표현할 수 없다.**\
IGNORED를 APPLIED로 뭉개면 중복 이벤트가 후처리를 두 번 돌리고, REJECTED로 뭉개면 재시도가 실패로 보고되어 경보가 울린다.

채울 것: `src/main/java/com/domain/order/OrderStateMachine.java` 의 TODO 1~4.\
`OrderState`(8개 상태 enum)와 `TransitionResult`(결과 레코드)는 계약이라 다 주어져 있다.

| TODO | 메서드 | 시키는 일 |
|---|---|---|
| 1 | `standard(sameStateIsIdempotent)` | 흔한 쇼핑몰 규칙의 전이 표를 만든다. 배송 시작 후엔 취소 불가 |
| 2 | `apply(from, to)` | 전이 시도. **순서가 계약** — 같은 상태인지를 **표보다 먼저** 본다 |
| 3 | `applyAll(start, events)` | 이벤트를 순서대로. 거부해도 **멈추지 않고**, 결과는 **조건 없이 대입** |
| 4 | `reachableFrom(start)` | 닿을 수 있는 상태들 — 11번 BFS를 그대로. 표가 곧 그래프다 |

테스트가 못 박은 계약(`OrderStateTest`):

- 정상 경로는 한 칸씩 APPLIED.
- PREPARING에서는 취소 가능, SHIPPED·DELIVERED에서는 불가.
- CANCELLED·REFUNDED는 terminal(표가 정한다).
- 되돌아가기(PAID→PLACED)는 REJECTED.
- 멱등 켜면 중복이 IGNORED(changed·isError 둘 다 false), 끄면 REJECTED.
- 자기 전이가 있는 표에서 멱등 켜면 IGNORED·끄면 APPLIED.
- PLACED에서 [SHIPPED, PAID] → 첫째 REJECTED이면서 state는 PLACED, 둘째 APPLIED.
- 표준 표에서 PLACED는 8개 전부에 닿고, 끊긴 표에서는 6개만 닿는다.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

## 전체 흐름

```text
요구사항 문장                            코드로의 번역
──────────────────────────────────────────────────────────────
"주문 상태들"                  →  OrderState enum 8개
"갈 수 있는 길"                →  Map<OrderState, Set<OrderState>> 전이 표
                                   standard(): 흔한 쇼핑몰 규칙 9개 화살표
"전이 결과"                    →  TransitionResult(상태, 종류)
                                   APPLIED / IGNORED / REJECTED 3갈래
"중복 이벤트를 어떻게 보나"    →  sameStateIsIdempotent (boolean 정책)
"이벤트 여러 개 순서대로"      →  applyAll — 거부돼도 멈추지 않고 계속
"끝난 상태"                    →  isTerminalIn(machine) — 필드가 아니라 표가 말한다
"표가 제대로 이어졌나"         →  reachableFrom — BFS (11번 그대로)
```

> **상태 머신(state machine)** — 상태들과 그 사이의 허용된 전이(화살표)를 표로 들고 있는 것.\
> 예: 표에 PLACED→PAID 가 있으면 그 이동은 되고, 표에 없는 PLACED→SHIPPED 는 전부 거부다.

> **멱등(idempotent)** — 같은 요청을 두 번 해도 결과가 한 번 한 것과 같은 성질.\
> 예: 결제완료 이벤트가 재전송으로 두 번 와도 주문은 결제완료 상태 하나로 끝난다.

## 규칙 1 — 결과는 둘이 아니라 셋이다 (이 챕터의 핵심)

**어떤 요구사항인가**: "전이를 시도하면 성공 또는 실패" — 라고 쓰고 싶지만, 셋이 필요하다.

```text
  APPLIED   상태가 바뀌었다         changed=true   isError=false
  IGNORED   이미 그 상태다          changed=false  isError=false   ← 제3의 값
  REJECTED  허용되지 않는 전이다    changed=false  isError=true
```

**왜 불리언 하나로 안 되나**: 결과가 답해야 할 질문이 **둘**이기 때문이다 — ① 상태가 바뀌었나(`changed`) → 후처리를 돌릴지 정한다 ② 잘못된 요청인가(`isError`) → 경보를 울릴지 정한다.

IGNORED는 (false, false)라서 둘 중 어느 쪽으로 뭉개도 사고가 난다:

- IGNORED를 APPLIED로 뭉개면 → 중복 결제 이벤트에 포인트 적립·알림이 **두 번** 돈다.
- IGNORED를 REJECTED로 뭉개면 → 네트워크 재시도가 실패로 보고되어 **경보가 울린다.**

**예시 입력**: PLACED에서 [PAID, PAID]를 받으면 → APPLIED(PAID가 됨), IGNORED(이미 PAID).\
멱등을 끄면(strict) 두 번째가 REJECTED.

## 규칙 2 — 같은 상태인지를 표보다 먼저 본다 (순서가 계약)

**`apply`의 판정 순서**: ① from == to 인가 → 멱등이면 IGNORED ② 표에 있나 → APPLIED ③ 없으면 REJECTED.

**함정**: 표준 표에는 자기 전이(자기 자신으로 가는 화살표)가 없어서, 어느 것을 먼저 보든 답이 같다 — **표준 표만 시험하면 이 순서가 아무 의미도 없어 보인다.**\
순서가 갈리는 것은 표에 자기 전이가 있을 때다:

> **자기 전이(self-transition)** — 어떤 상태에서 자기 자신으로 가는 화살표.\
> 예: "배송 중 위치 갱신"처럼 SHIPPED 에서 다시 SHIPPED 로 오는 이벤트가 의미를 갖는 표.

```text
  "배송 중 위치 갱신"처럼 SHIPPED → SHIPPED 가 의미 있는 표라면

    같은 상태를 먼저 본다  →  IGNORED   (중복 이벤트로 본다)
    표를 먼저 본다         →  APPLIED   (갱신으로 본다)

  impl은 같은 상태 먼저 + 멱등 off 스위치로 둘 다 표현한다.
```

## 규칙 3 — 거부는 멈추지 않고, 원래 상태를 담아 돌려준다

**예시 입력**: PLACED에서 이벤트 [SHIPPED, PAID]:

```text
  SHIPPED  →  REJECTED, 상태는 여전히 PLACED   (결제 없이 배송 불가)
  PAID     →  APPLIED,  PLACED → PAID          (뒤의 이벤트는 유효했다)
```

**왜 이렇게 모델링했나**:

- **거부해도 멈추지 않는다** — 뒤의 이벤트가 유효할 수 있다.\
  멈출지 계속할지도 "정해야 하는 규칙"이고, 여기서는 계속으로 정했다.
- **거부·무시는 원래 상태를 그대로 담아 돌려준다.**\
  그래서 `applyAll`은 결과의 상태를 **조건 없이 대입**한다(`current = result.state()`).
- 변종 검증에서 고친 것: 원래는 `changed()`를 확인하고 대입했는데, 거부·무시가 원래 상태를 담고 있으니 **그 조건이 아무 일도 안 하고 있었다.**\
  조건을 지우고, "거부는 원래 상태를 준다"는 불변식을 계약 테스트로 옮겼다 — 거부가 시도한 상태를 담게 바꾸는 변종은 테스트 3개가 잡는다.

> **변종 검증(mutation testing)** — 코드를 일부러 조금 틀리게 바꿔보고 테스트가 그걸 잡는지 확인하는 방법.\
> 예: 거부가 원래 상태 대신 시도한 상태를 담게 바꿨더니 테스트 3개가 깨졌다면, 그 약속은 실제로 지켜지고 있는 것이다.

## 규칙 4 — "끝났다"는 필드가 아니라 표가 말한다

**어떤 요구사항인가**: CANCELLED와 REFUNDED는 종점이다.

**코드로의 번역**: `isTerminalIn(machine)` = "나가는 화살표가 0개인가"(`allowedFrom(state).isEmpty()`).

**왜 이렇게 모델링했나**: `boolean terminal` 필드를 따로 두면 표와 어긋날 수 있고, **어긋나도 아무도 모른다.**\
같은 사실의 출처를 하나(표)로 두면 어긋남 자체가 불가능하다. (06번의 "같은 것을 두 곳에서 지키지 마라"와 같은 원리.)

## 규칙 5 — 표가 곧 그래프다: BFS로 표를 검사한다

**어떤 요구사항인가**: 표를 손으로 채우면 아무도 못 가는 상태가 생길 수 있다.

**예시**: DELIVERED → RETURN_REQUESTED 화살표를 빠뜨리면:

```text
  PLACED에서 BFS  →  닿는 상태 6개 (8개여야 정상)
  RETURN_REQUESTED, REFUNDED 에 아무도 못 간다 = 죽은 상태

  그런데 그 두 상태는 enum에도 switch에도 남아 있어서 아무도 안 지운다.
```

> **BFS(너비 우선 탐색)** — 시작점에서 가까운 곳부터 큐로 차례차례 훑는 그래프 탐색.\
> 예: 전이 표를 그래프로 보고 PLACED 에서 훑으면, 한 걸음 거리인 PAID·CANCELLED 부터 차례로 나온다.

**계산 방법**: `reachableFrom`은 11번 BFS를 그대로 쓴다 — 표가 곧 그래프다.\
시작점을 먼저 방문 처리하므로 끝난 상태도 자기 자신에는 닿는다(0개가 아니라 1개).

## 측정이 알려준 것

- **표의 86%가 빈칸이다**: 상태 8개, 칸 64개, 표에 있는 전이 9개(14%).\
  취소 가능한 상태는 3/8.
- **무작위 이벤트의 73%가 거부된다**: 적용 1,458(15%) / 무시 1,281(13%) / 거부 7,261(73%).\
  **거부를 예외로 던지면 예외가 정상 흐름이 된다** — 외부 이벤트를 받는 자리에서는 특히.\
  그래서 REJECTED는 예외가 아니라 반환값이다.
- **멱등이냐로 730/1,000이 갈리는데 최종 상태는 1,000/1,000이 같다**: 갈리는 것은 상태가 아니라 **"무엇을 오류로 볼 것인가"** 이고, 그 판단이 경보와 재시도를 정한다.
- **어디서 길이 좁아지나** — 닿을 수 있는 상태 수:

| 상태 | 닿을 수 있는 상태 수 |
|---|---|
| PLACED | 8 |
| PAID | 7 |
| PREPARING | 6 |
| SHIPPED | **4** |
| DELIVERED | 3 |
| CANCELLED / REFUNDED | 1 |

`PREPARING → SHIPPED` 한 걸음에 취소와 그 뒤가 통째로 사라진다(6→4).\
표를 눈으로 읽는 대신 이 수를 보면 어디가 "돌이킬 수 없는 경계"인지 보인다.

## 경계·모서리 케이스

| 함정 | 올바른 처리 |
|---|---|
| PLACED → SHIPPED 건너뛰기 | REJECTED — 결제 없이 배송할 수 없다 |
| SHIPPED에서 취소 | REJECTED — "배송이 시작되면 취소 불가"는 규칙이지 자연법칙이 아니다(다르게 정하는 회사도 있다) |
| DELIVERED에서 취소 | 취소가 아니라 반품(RETURN_REQUESTED)으로 간다 |
| SHIPPED → PREPARING 되돌아가기 | REJECTED — 되돌리기가 필요하면 별도 상태(반품·환불)다. 되돌아가면 이력이 사라진다 |
| 끝난 상태(CANCELLED)에서 전이 | 전부 REJECTED — 나가는 화살표가 없다 |
| 중복 이벤트(PAID → PAID) | 멱등이면 IGNORED — 오류가 아니다. strict면 REJECTED |
| 표준 표만으로 시험 | 자기 전이가 없어 판정 순서 결함이 안 드러난다 — 자기 전이 있는 표를 따로 시험 |
| `changed()` 확인 후 대입 | 죽은 조건이었다 — 결과가 항상 그 시점 상태를 담으므로 무조건 대입 |

## 핵심 문장

- 그림의 화살표 9개보다 중요한 것은 **표의 빈칸 55개**다 — 빈칸이 "안 된다"인지 "아직 안 그렸다"인지를 정하는 것이 상태 모델링이다.
- 전이 결과는 셋(APPLIED/IGNORED/REJECTED)이다 — 결과가 답할 질문이 둘(바뀌었나, 오류인가)이라서 **불리언 하나로는 표현이 안 된다.**
- 중복 이벤트는 반드시 온다(네트워크 재전송) — 무시를 성공으로 뭉개면 후처리가 두 번 돌고, 실패로 뭉개면 경보가 울린다.
- 무작위 이벤트의 73%가 거부다 — **거부는 예외가 아니라 정상 흐름의 반환값**이어야 한다.
- "끝났다" 같은 파생 사실은 필드로 두지 말고 표가 말하게 하라 — 출처가 하나면 어긋날 수가 없다.
- 표는 그래프다 — BFS로 닿을 수 없는 상태(죽은 코드)를 찾고, 닿는 상태 수로 "돌이킬 수 없는 경계"를 읽는다.

## 관련 자료

- 챕터 안내: `/home/jun/project/myway/domain-modeling-basic/09-order-state/README.md`
- 내 구현(TODO 껍데기): `/home/jun/project/myway/domain-modeling-basic/09-order-state/src/main/java/com/domain/order/OrderStateMachine.java`
- 계약(전부 주어짐): `.../src/main/java/com/domain/order/OrderState.java`, `TransitionResult.java`
- 정답 기준 소스: `/home/jun/project/myway/domain-modeling-basic/09-order-state/impl/com/domain/order/OrderStateMachine.java`
- 테스트: `.../src/test/java/com/domain/order/OrderStateTest.java`(정상 경로·취소 경계·멱등·자기 전이·도달성), `MeasurementTest.java`(86%·73%·730/1,000·닿는 상태 수)
- 이웃 챕터: 11번 BFS(reachableFrom이 그대로 씀), 10번 결제(같은 상태 머신 사고의 돈 버전)

## 용어 풀이

- **상태 머신(state machine)**: 상태 목록 + 허용된 전이 표. 표에 없는 이동은 거부한다.
- **전이(transition)**: 한 상태에서 다른 상태로의 이동. 표의 화살표 하나.
- **전이 표(transition table)**: 상태별로 "갈 수 있는 곳"의 집합을 담은 지도. `Map<OrderState, Set<OrderState>>`.
- **멱등(idempotent)**: 같은 요청을 두 번 해도 한 번과 같은 성질. 중복 이벤트를 IGNORED로 넘기는 근거.
- **APPLIED / IGNORED / REJECTED**: 바뀜 / 이미 그 상태(오류 아님) / 허용 안 됨(오류). 전이 결과의 3갈래.
- **자기 전이(self-transition)**: 자기 자신으로 가는 화살표(SHIPPED→SHIPPED). 판정 순서를 드러내는 시금석.
- **종점 상태(terminal state)**: 나가는 화살표가 0개인 상태. 필드가 아니라 표에서 파생한다.
- **도달성(reachability)**: 시작 상태에서 화살표를 따라 닿을 수 있는가. BFS로 센다.
- **BFS(너비 우선 탐색)**: 가까운 곳부터 큐로 훑는 그래프 탐색. 여기서는 표 검사기다.
- **enum(열거형)**: 값의 목록을 타입으로 선언한 것. 상태 8개, 결과 종류 3개가 enum이다.
- **EnumMap / EnumSet**: enum 전용 Map/Set. 칸이 고정이라 빠르고, 상태 추가를 빠뜨리면 드러난다.
