# domain-modeling/20-event-storming — 이벤트 스토밍: 이벤트 중심 협업 모델링 — 정리 (힌트)

## 해결하는 문제

개발자끼리 회의실에서 주문 시스템을 설계한다.

```text
  개발자가 그린 흐름                     업무 담당자가 아는 흐름
  주문 접수 → 결제 → 배송               주문 접수 → 결제 승인 → 재고 확보
                                                         └ 재고 없음 → 주문 취소 → 환불
                                        (부분 배송은? 새벽 주문 결제는? ...)
```

- 개발자는 데이터 모델(테이블·클래스)부터 그리기 쉽다. 업무의 예외 경로(재고 없음·환불·부분 배송)는 현장 사람 머릿속에 있다.
- 그 지식이 설계에 안 들어오면 출시 뒤 "이 경우는 어떻게 하죠?" 티켓으로 하나씩 돌아온다(⚠ 커리큘럼: 개발자만 모델링 → 도메인 전문가 지식 누락).

쉬운 예: 가족 여행 계획.
- 한 사람이 일정표 칸(날짜·장소)부터 채우면 빠진 것이 안 보인다.
- 대신 모두가 "일어날 일"을 포스트잇에 써서 벽에 시간 순서로 붙인다. "공항 도착함", "렌터카 받음", "숙소 체크인함".
- 붙이다 보면 "렌터카 받기 전에 면허증 국제판 받아야 함" 같은 빠진 일이 저절로 드러난다. 누군가 "그 날 공휴일이라 렌터카 사무실 닫음"을 붙인다.

똑같은 구조다.\
**업무에서 일어나는 일(도메인 이벤트)을 여러 사람이 함께 벽에 시간 순서로 붙이고, 빈틈과 충돌을 찾는다.** 이것이 이벤트 스토밍이다.

- *이벤트 스토밍(EventStorming)*: 복잡한 업무 도메인을 협업으로 탐색하는 유연한 워크숍 형식(eventstorming.com). Alberto Brandolini가 2013년 블로그 글 "Introducing Event Storming"(2013-11-18)으로 소개했다. 같은 글에 따르면 전신은 2012년 Italian Agile Day에서 발표한 "Event-Based modelling workshop"이고, 2013년 여름 직전에 지금 이름을 붙였다.
- *도메인 이벤트*: 도메인에서 일어난 의미 있는 일(Brandolini 2013). 도메인 전문가에게 의미가 있어야 한다. 과거형 동사로 쓴다(DDD Crew 용어집, 예: "Order Placed"). 코드에서의 도메인 이벤트는 [09-domain-events](../09-domain-events/2-summary.md).

실무 예:
- 새 서비스 착수 전, 업무 담당자·개발자·기획자가 반나절 모여 큰 흐름을 붙이고 바운디드 컨텍스트 후보를 찾는다(16번).
- 장애가 잦은 기존 프로세스(정산·환불)를 붙여 보고, 담당 부서끼리 서로 다르게 이해하던 지점(핫스폿)을 찾는다.

## 동작·원리

### 1. 보드 — 시간축 위의 색깔 포스트잇

```text
  시간 ───────────────────────────────────────────────────────────────────►

  [고객]        [주문하기]      (주문 접수됨)   [정책: 접수되면 결제 요청]  [결제 요청]  (결제 승인됨)
  작은 노랑      파랑            주황           라일락                      파랑         주황
   행위자        명령            이벤트          정책                        명령          이벤트
                   │                                                         │
                   ▼                                                         ▼
               [Order]                                                  [PG(외부)]
               큰 노랑(애그리거트/제약)                                   넓은 분홍(외부 시스템)

  [재고 화면] 초록 = 결정에 필요한 정보(읽기 모델)     [!부분 배송은?] 형광 분홍 = 핫스폿(미해결 질문·충돌)
```

DDD Crew 용어집의 색 관례:

| 포스트잇 | 색 | 뜻 |
|---|---|---|
| 도메인 이벤트 | 주황 | 도메인 전문가에게 의미 있는 일. 과거형 |
| 명령(Command/Action) | 파랑 | 행위자나 자동 처리가 내린 결정·의도 |
| 행위자(Actor) | 작은 노랑 | 이벤트 주변에 관여한 사람·부서·팀 |
| 시스템 | 넓은 분홍 | 배포 가능한 IT 시스템(외부 포함) |
| 정책(Policy) | 큰 라일락 | "X가 일어나면 Y를 한다" — 이벤트와 명령 사이 반응 |
| 읽기 모델 | 초록 | 행위자가 결정하는 데 필요한 정보 |
| 핫스폿 | 형광 분홍 | 충돌·질문·이견·불일치 |
| 제약/애그리거트 | 큰 노랑 | 명령을 수행하려 할 때 지켜야 할 제약 |

- 색은 관례다. 2013년 원글은 이벤트를 모두 주황으로 붙이고, 그 원인을 따로 표시했다. 사용자 행동이 원인이면 명령(파랑), 외부 시스템이나 시간 경과가 원인이면 보라다("Explore the origin of Domain Events" 단계). 지금 흔히 쓰는 색표(위 표)와 다른 곳이 있다. 워크숍마다 범례를 벽에 붙인다.
- *애그리거트*: Brandolini 2013은 "명령을 받아 실행할지 결정하고, 그 결과로 도메인 이벤트를 내는 시스템 부분"이라고 적는다. 지금의 DDD Crew 용어집은 큰 노랑을 "제약(Constraint)"으로 부르고, aggregate는 업무 담당자 앞에서 쓰지 않으려고 "레거시 용어"로 돌렸다고 적는다. 전술 설계의 애그리거트는 [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md).

### 2. 왜 이벤트부터인가

- 이벤트는 업무 담당자가 이미 쓰는 말이다. "주문 접수됨", "환불 완료됨". 테이블·클래스는 개발자의 말이다.
- 시간 순서로 늘어놓으면 빠진 단계·중복·순서 충돌이 눈에 보인다.
- Brandolini 2013: 결과 모델은 완전히 행동 중심이며, 구현을 제약하는 밑바탕 데이터 모델이 없다.
- 같은 글은 "완전한 업무 흐름의 포괄적 모델을 몇 주가 아니라 몇 시간에" 만들었다고 적는다. 이는 저자와 실무자의 경험 주장이다. 통제된 측정 결과가 아니다.

### 3. 세 수준

```text
  Big Picture ──────────> Process Modeling ──────────> Software Design
  (사업 전체 흐름)          (한 프로세스의 규칙)          (구현 가능한 설계)
  이벤트 + 핫스폿 +          이벤트·명령·정책·            + 애그리거트·컨텍스트 경계
  행위자·시스템              읽기 모델의 문법              → 코드 구조로
```

| 수준 | 목적(DDD Crew 용어집) | 참여 |
|---|---|---|
| Big Picture | 사업 라인 건강 진단, 공유된 큰 그림 | 10~30명+ 한 종이 롤에(용어집) |
| Process Modeling | 현재 프로세스 건강 진단, 병목·분리 기회 찾기 | 수치 언급 없음 |
| Software Design | 바운디드 컨텍스트 안에서 공유 언어로 이벤트 기반 소프트웨어 설계 | 수치 언급 없음 |

- 2013년 원글은 "6..8명이 들어가는 큰 회의실"을 권했다. 이후 Big Picture 형식에서는 용어집이 "10~30명+"를 적는다. 형식이 발전하며 규모가 달라졌다.
- Big Picture 진행 단계(용어집): ①혼돈의 탐색(각자 이벤트를 쓴다) → ②타임라인 강제(중복 제거·순서 정리) → ③핫스폿 표시 → ④필요한 개념 추가.
- *핵심 이벤트(pivotal event)*: 흐름에서 가장 중요한 몇 개의 이벤트. 관심 있는 사람이 가장 많은 이벤트(예: 주문 접수됨, 주문 발송됨). 흐름을 구간으로 나누는 기준이 되고, 구간 경계가 컨텍스트 경계 후보가 된다.
- Brandolini의 책 『Introducing EventStorming』(Leanpub)은 집필 중인 책이다. Leanpub 페이지 기준 70% 완성, 마지막 갱신 2021-08-26이다. 목차에 "Discovering Bounded Contexts with EventStorming", "Process Modeling Building Blocks", "Running a Design-Level EventStorming" 장이 있다.

### 4. Process Modeling의 문법 — 보드가 코드가 되는 길

```text
  행위자 ──> 명령 ──> 애그리거트/시스템 ──> 이벤트 ──> 정책 ──> 명령 ──> ...
               ▲                                           │
           읽기 모델(결정에 필요한 정보)                       └ "X가 일어나면 Y를 한다"
```

| 포스트잇 | 코드로 가면 |
|---|---|
| 명령 | 애플리케이션 서비스 메서드 / 명령 핸들러 |
| 애그리거트 | 명령을 받아 불변식을 검사하고 이벤트를 내는 엔티티 |
| 이벤트 | 도메인 이벤트 클래스(과거형 이름) |
| 정책 | 이벤트 구독자(이벤트 → 다음 명령) |
| 읽기 모델 | 조회 전용 모델·화면(CQRS의 조회 쪽, [21-cqrs](../21-cqrs/2-summary.md)) |
| 외부 시스템 | 포트 + ACL(19번) |

- 이 대응은 흔히 쓰는 번역 관례다. 한 포스트잇이 반드시 한 클래스가 되지는 않는다.

### 실험: 보드를 데이터로 옮겨 빈틈을 기계로 찾는다

보드를 데이터로 적고, Process Modeling 문법에 맞지 않는 곳을 찾는 검사기를 돌렸다. 두 보드는 시나리오(예시)다. 하나는 개발자만 그린 것, 하나는 업무 전문가와 함께 고친 것이라는 설정이다.

검사 규칙(이 실험에서 정한 것):
- 타임라인의 이벤트마다 그것을 내는 명령(또는 외부 이벤트)이 있어야 한다.
- 정책이 가리키는 이벤트·명령이 보드에 있어야 한다.
- 마지막 이벤트가 아닌데 아무 정책도 반응하지 않으면 "다음은 누가 하나?"로 표시한다.
- 핫스폿은 미해결로 나열한다.

```java
record Cmd(String name, String issuedBy, String handledBy, List<String> emits) {}
record Policy(String whenEvent, String thenCommand) {}
for (String e: b.timeline()) if(!emitted.contains(e)) out.add("트리거 없는 이벤트: "+e);
for (Policy p: b.policies()) if(!cmdNames.contains(p.thenCommand())) out.add("정책이 내리는 명령이 없음: "+p+" ");
for (String e: b.timeline()) if(!reacted.contains(e) && !e.equals(last)) out.add("반응(정책) 없는 이벤트: "+e+"  ← 다음은 누가 하나?");
```

(실험, JDK 21.0.12 temurin `--cpus=2`, 2026-10-03 — `Board.java`)

```text
== 개발자만 그린 보드(예시)  (이벤트 3, 명령 2, 정책 1)
  - 트리거 없는 이벤트: 결제 승인됨
  - 정책이 내리는 명령이 없음: Policy[whenEvent=주문 접수됨, thenCommand=결제 요청] 
  - 반응(정책) 없는 이벤트: 결제 승인됨  ← 다음은 누가 하나?
  처리자(애그리거트·시스템 후보)별 명령: {Order=[주문하기], Shipment=[배송 시작]}
== 업무 전문가와 함께 고친 보드(예시)  (이벤트 7, 명령 6, 정책 5)
  - 반응(정책) 없는 이벤트: 환불 완료됨  ← 다음은 누가 하나?
  - 핫스폿(미해결 질문): 일부 품목만 재고가 있으면 부분 배송인가 전체 취소인가?
  처리자(애그리거트·시스템 후보)별 명령: {Inventory=[재고 확보], Order=[주문하기, 주문 취소], PG(외부)=[결제 요청, 환불], Shipment=[배송 시작]}
```

관찰:
1. 첫 보드에서 "결제 승인됨"은 누가 내는지 없다. 정책은 "결제 요청" 명령을 가리키는데 그 명령 포스트잇이 없다. 결제 승인 뒤 무엇을 하는지도 없다. 개발자가 머릿속으로 이어 붙인 곳이 문법 검사에서 구멍으로 나왔다.
2. 고친 보드는 재고 실패 → 취소 → 환불 분기가 들어갔다. 처리자별로 명령을 모으니 애그리거트·시스템 후보 4개(Inventory, Order, PG(외부), Shipment)가 나왔다. 외부 PG는 ACL 후보다(19번).
3. 고친 보드에도 "환불 완료됨 ← 다음은 누가 하나?"가 남았다. 환불 완료는 분기의 끝이라 정상일 수 있다. 검사기는 "끝 이벤트"와 "빠뜨린 반응"을 구분하지 못한다. 그래서 보드에 끝 이벤트를 표시하는 규칙이 필요하다. 기계 검사는 질문을 만들 뿐, 답은 사람이 한다.
4. 핫스폿은 보드에서 풀리지 않은 질문으로 남는다. 이것을 그냥 두고 구현에 들어가면 그 질문이 출시 뒤 장애·티켓으로 돌아온다.

해석: 이 실험은 "워크숍이 지식 누락을 줄인다"를 측정한 것이 아니다. 그 주장은 Brandolini·실무자의 경험 주장이다. 실험이 보이는 것은 보드가 **검사 가능한 산출물**이 될 수 있다는 점이다. 이벤트·명령·정책의 문법을 지키면 빠진 연결을 기계적으로 찾을 수 있다.

## 쓰이는 자료구조·알고리즘

- **타임라인(순서 있는 리스트)** — 🔧 커리큘럼의 "타임라인". 보드의 주축이다. 실험의 `timeline`.
- **유향 그래프(이벤트 → 정책 → 명령 → 이벤트)** — Process Modeling 문법은 그래프다. 검사는 "들어오는 간선 없는 이벤트(트리거 없음)", "나가는 간선 없는 비종료 이벤트(반응 없음)", "끝점 없는 간선(없는 명령을 가리키는 정책)" 찾기다. 각각 집합 포함 검사라 O(V+E).
- **그룹화(처리자별 명령 묶기)** — `Map<처리자, List<명령>>`. 애그리거트 후보를 고르는 첫 단계. 실험의 `TreeMap` 출력.
- **구간 나누기(핵심 이벤트 기준)** — 타임라인을 핵심 이벤트로 자르면 구간이 생기고, 구간 경계가 컨텍스트 경계 후보다(16번).
- **상태 기계** — 한 애그리거트에 붙은 이벤트들을 모으면 그 애그리거트의 상태 전이 후보가 된다([11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md), 연습: [basic/09-order-state](../basic/09-order-state/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서 (Big Picture → Process → Design)

1. **사람을 부른다.** 질문할 줄 아는 사람(개발자·기획자)과 답을 아는 사람(업무 담당자)을 섞는다(Brandolini 2013).
2. **공간을 넓힌다.** 긴 종이 롤을 벽에 붙인다. 공간 제약이 생각을 막지 않게 한다(원글: "Ikea paper roll").
3. **혼돈의 탐색**: 각자 주황 포스트잇에 과거형 이벤트를 쓴다. 이때는 순서·중복을 따지지 않는다.
4. **타임라인 강제**: 중복을 합치고 시간 순서로 정렬한다. 핵심 이벤트를 고른다.
5. **핫스폿 표시**: 이견·질문을 형광 분홍으로 붙인다. 그 자리에서 다 풀려 하지 않는다.
6. **Process Modeling**: 한 구간을 골라 명령·정책·읽기 모델·외부 시스템을 채운다. 문법(명령 → 이벤트 → 정책 → 명령)을 지킨다.
7. **Software Design**: 명령을 처리자별로 묶어 애그리거트 후보를 찾고, 구간 경계로 컨텍스트 후보를 긋는다.
8. **보드를 기록한다.** 사진만 두지 말고 이벤트·명령·정책 목록으로 옮긴다(실험처럼 검사 가능한 형태).

### 2. 코드 — 보드의 한 줄을 Java로 (Process Modeling → 코드)

```java
// [결제 승인됨] → (정책: 결제 승인되면 재고 확보) → [재고 확보] → Inventory → [재고 확보됨 | 재고 확보 실패됨]
public record PaymentApproved(OrderId orderId, Money amount, Instant at) {}        // 이벤트: 과거형

@Component
class ReserveStockWhenPaymentApproved {                                           // 정책: "X가 일어나면 Y를 한다"
    private final ReserveStockHandler reserve;
    @EventListener void on(PaymentApproved e) { reserve.handle(new ReserveStock(e.orderId())); }
}

record ReserveStock(OrderId orderId) {}                                            // 명령
class ReserveStockHandler {                                                        // 명령 처리 = 애그리거트 호출
    void handle(ReserveStock cmd) {
        Inventory inv = repo.forOrder(cmd.orderId());
        DomainEvent result = inv.reserve(cmd.orderId());   // StockReserved 또는 StockReservationFailed
        events.publish(result);
    }
}
```

- 이름을 보드의 말 그대로 쓴다. 보드의 "결제 승인됨"이 코드의 `PaymentApproved`가 되도록 용어집을 함께 둔다([03번 유비쿼터스 언어](../03-ubiquitous-language/2-summary.md)).
- Spring 문서(Framework 7.0 "Standard and Custom Events" — 6.2판 문서도 같은 문장)에 따르면 이벤트 리스너는 기본적으로 동기로 이벤트를 받는다. `publishEvent()`는 모든 리스너가 끝날 때까지 막히고, 트랜잭션이 있으면 리스너는 발행자의 트랜잭션 안에서 돈다. 커밋 뒤 처리·유실 없는 전달이 필요하면 09번(도메인 이벤트)과 outbox([distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md))를 따른다.

### 3. 진단 — 보드와 코드가 어긋났나

```bash
# 보드에서 옮긴 이벤트 목록(events.txt, 한 줄에 하나: PaymentApproved 등)이 코드에 다 있나
while read e; do grep -rq "record $e\b\|class $e\b" src/ || echo "코드에 없음: $e"; done < events.txt
```

- 코드에만 있고 보드에 없는 이벤트, 보드에만 있고 코드에 없는 이벤트가 둘 다 신호다. 보드를 다시 보거나 코드 이름을 보드 말로 맞춘다.

## 장애 시나리오와 대처

### 1. 개발자만 모델링 → 도메인 전문가 지식 누락 (⚠ 커리큘럼)

- 현상: 출시 뒤 "재고 없으면 어떻게 하죠?", "부분 환불은요?" 같은 예외 경로 문의가 쏟아진다.
- 보이는 형태: 상태 값에 없는 경우가 수작업으로 처리된다. 운영자가 DB를 직접 고친다. 같은 주제의 버그 티켓이 반복된다.
- 원인: 업무 흐름의 예외 경로가 현장 사람 머릿속에만 있었다. 설계는 개발자가 아는 정상 경로만 담았다(실험 첫 보드: 트리거 없는 이벤트·없는 명령·반응 없는 이벤트).
- 대처: 업무 담당자를 포함한 Big Picture → Process Modeling 워크숍을 연다. 핫스폿을 목록으로 관리하고, 구현 전에 각 핫스폿의 결정을 받는다.

### 2. 워크숍은 했는데 보드가 사진으로만 남았다

- 현상: 몇 달 뒤 아무도 보드 내용을 기억하지 못한다. 코드 이름은 보드와 다르다.
- 보이는 형태: 회의에서 "그때 정한 거 어디 있죠?" 질문. 이벤트 이름이 팀마다 다르다(`OrderCompleted` vs `OrderFinished`).
- 원인: 보드를 검사·추적 가능한 산출물로 옮기지 않았다.
- 대처: 보드를 이벤트·명령·정책 목록으로 옮겨 저장소에 둔다. 코드와 대조하는 검사를 둔다(적용 §3). 용어집과 함께 유지한다.

### 3. 핫스폿을 덮고 구현에 들어갔다

- 현상: 출시 직전에 "부분 배송인가 전체 취소인가"가 아직 정해지지 않았음이 드러난다.
- 보이는 형태: 개발자가 임의로 정한 동작이 운영 정책과 다르다. 고객 응대 스크립트와 시스템 동작이 어긋난다.
- 원인: 핫스폿을 "나중에" 칸에 두고 아무도 담당하지 않았다(실험 고친 보드에도 핫스폿 1개가 남아 있다).
- 대처: 핫스폿마다 담당자·결정 기한을 붙인다. 결정되지 않은 핫스폿이 걸린 기능은 범위에서 빼거나 명시적 기본 동작을 합의한다.

### 4. 이벤트 대신 데이터 모델을 붙인다

- 현상: 포스트잇에 "주문 테이블", "회원 정보" 같은 명사가 붙는다.
- 보이는 형태: 타임라인이 안 생긴다. 토론이 필드 목록으로 흐른다.
- 원인: 이벤트(과거형 일)가 아니라 데이터(명사)부터 그렸다. Brandolini가 피하려던 "구현을 제약하는 데이터 모델"이 처음부터 들어왔다.
- 대처: 진행자가 "그래서 무슨 일이 일어났나요?"로 과거형 문장을 요구한다. 명사 포스트잇은 읽기 모델(초록)이나 나중 단계로 미룬다.

## 핵심 문장

1. 이벤트 스토밍은 업무에서 일어난 일(과거형 도메인 이벤트)을 여러 사람이 시간 순서로 벽에 붙여 도메인을 함께 탐색하는 워크숍이다.
2. 이벤트부터 시작하는 이유는, 그것이 업무 담당자의 말이고 시간 순서로 늘어놓으면 빠진 단계와 충돌이 보이기 때문이다.
3. 수준은 Big Picture(사업 전체) → Process Modeling(이벤트·명령·정책 문법) → Software Design(애그리거트·컨텍스트 경계)으로 내려간다.
4. 문법을 지킨 보드는 검사 가능한 산출물이다 — 트리거 없는 이벤트, 없는 명령을 가리키는 정책을 기계로 찾을 수 있다(실험).
5. "몇 주가 아니라 몇 시간"은 저자·실무자의 경험 주장이다. 효과는 업무 담당자가 실제로 참여하고 핫스폿이 결정으로 이어질 때 나온다.

## 관련 주제·근거

- 선행
  - [16-bounded-contexts](../16-bounded-contexts/2-summary.md) — 워크숍이 찾는 경계
- 후속·연결
  - [17-subdomains](../17-subdomains/2-summary.md) — Big Picture에서 서브도메인 찾기
  - [18-context-mapping](../18-context-mapping/2-summary.md) — 찾은 컨텍스트 사이 관계
  - [19-anti-corruption-layer](../19-anti-corruption-layer/2-summary.md) — 보드의 외부 시스템(분홍) 감싸기
  - [09-domain-events](../09-domain-events/2-summary.md) — 보드의 이벤트를 코드로
  - [03-ubiquitous-language](../03-ubiquitous-language/2-summary.md) — 보드의 말을 코드 이름으로
  - [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md) · [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md) · [21-cqrs](../21-cqrs/2-summary.md) — 애그리거트, 상태 전이, 읽기 모델
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) — 정책 실행의 전달 보장
  - [distributed/23-orchestration-vs-choreography](../../distributed/23-orchestration-vs-choreography/2-summary.md) — 정책 사슬 = 코레오그래피
  - [basic/09-order-state](../basic/09-order-state/2-summary.md) — 주문 상태 연습
- 글·문서
  - Alberto Brandolini, "Introducing Event Storming", 2013-11-18 <https://ziobrando.blogspot.com/2013/11/introducing-event-storming.html>
  - Alberto Brandolini, 『Introducing EventStorming』(Leanpub, 집필 중 — 70%, 2021-08-26 갱신 기준 목차) <https://leanpub.com/introducing_eventstorming>
  - EventStorming 공식 사이트 <https://www.eventstorming.com/>
  - Spring Framework 레퍼런스 "ApplicationContext — Standard and Custom Events"(7.0) — 리스너 기본 동기·발행자 트랜잭션 <https://docs.spring.io/spring-framework/reference/core/beans/context-introduction.html>
  - DDD Crew, "EventStorming Glossary & Cheat Sheet"(README는 CC BY 4.0, 저장소 `LICENSE` 파일은 CC BY-SA 4.0 — 2026-10-03 확인) — 색 관례·세 수준·Big Picture 단계·핵심 이벤트 <https://github.com/ddd-crew/eventstorming-glossary-cheat-sheet>
- 실험 목록
  - 보드(예시 2개)를 데이터로 옮겨 Process Modeling 문법 빈틈 검사·처리자별 명령 묶기 — `scratchpad/dm/16/e20/Board.java`, JDK 21.0.12 temurin `--cpus=2 --network none`
