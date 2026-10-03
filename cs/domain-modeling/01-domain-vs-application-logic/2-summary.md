# domain-modeling/01-domain-vs-application-logic — 도메인 규칙과 애플리케이션 흐름의 경계 — 정리 (힌트)

## 해결하는 문제

규칙이 한곳에 없으면, 규칙을 바꿀 때 사본을 전부 찾아 고쳐야 한다. 하나라도 놓치면 그 경로로 옛 규칙이 계속 돈다.

쉬운 예: 도서관 대출 규칙 "연체 중인 회원은 빌릴 수 없다".

```text
  창구 직원 메모     "연체면 거절"
  무인 대출기 코드   if (연체) 거절
  모바일 앱 코드     if (연체) 거절
        │
        ▼  규칙이 "연체 3일 넘으면 거절"로 바뀜
  창구 메모만 고침 → 무인기·앱은 여전히 "연체 하루만 돼도 거절"
```

- 규칙이 회원(대출 자격) 쪽에 하나만 있으면, 창구·무인기·앱은 "빌려 줘"라고 부탁만 한다. 규칙이 바뀌어도 고칠 곳은 하나다.

똑같은 구조다.\
결제 승인 취소 규칙 "정산된 승인은 취소할 수 없다"가 고객 API, 미배송 자동 취소 배치, 상담원 도구 세 곳에 각자 `if`로 들어 있다. "승인 후 7일이 지나면 취소 불가"가 추가되면 세 곳을 다 고쳐야 한다. 아래 실험에서 한 곳만 고친 상태를 재현하면 세 경로 중 두 경로가 새 규칙을 어긴다.

- *도메인 로직(domain logic)*: 시스템이 없어도 업무에 존재하는 규칙. "무엇이 허용되는가"에 답한다.
- *애플리케이션 로직(application logic)*: 시스템이 있어서 생긴 절차. 입력을 받고, 객체를 불러오고, 트랜잭션을 열고, 저장하고, 알림을 보낸다. "무슨 순서로"에 답한다.
- 이 감별법("시스템을 안 만들어도 업무에 존재하는가")과 회색지대 다섯 가지는 원본 노트 [domain-vs-application-logic](../domain-vs-application-logic/2-summary.md)의 「두 로직의 차이」·「경계의 회색지대」에 있다. 이 노트는 그 위에 출처 대조·실험·장애·진단을 더한다.

## 동작·원리

### 1. 네 계층 — 누가 판단하고 누가 조율하나 (Evans 4장)

```text
  ┌──────────────────────┐
  │ User Interface        │  입력 해석, 결과 표시          ← 형식 검증
  ├──────────────────────┤
  │ Application           │  할 일 정의, 순서 조율          ← "얇게", 업무 규칙 없음
  │  (유스케이스·트랜잭션) │  작업 진행 상태만 가짐
  ├──────────────────────┤
  │ Domain                │  업무 개념·업무 상황·업무 규칙   ← 판단은 여기
  ├──────────────────────┤
  │ Infrastructure        │  저장·메시징·외부 연동
  └──────────────────────┘
```

- Evans 『DDD』 4장 「Layered Architecture」의 정의다(2003 최종 원고 PDF로 대조).
  - Application Layer: "This layer is kept thin. It does not contain business rules or knowledge, but only coordinates tasks and delegates work to collaborations of domain objects".
  - 같은 절: 애플리케이션 계층은 업무 상황을 반영하는 상태는 갖지 않고, 사용자·프로그램의 작업 진행 상태는 가질 수 있다.
  - Domain Layer: 업무 개념·업무 상황 정보·업무 규칙을 표현한다. 저장 기술 세부는 인프라에 맡긴다.
- Fowler "AnemicDomainModel"(2003-11-25)도 이 문단을 인용해 "서비스 계층이 얇아야 한다"의 근거로 쓴다.
- Stafford(PoEAA 「Service Layer」)는 같은 구분을 "domain logic"(순수하게 문제 영역의 일)과 "application logic"(애플리케이션 책임, workflow logic이라고도 함)으로 부른다. 애플리케이션 고유 로직을 도메인 객체에 넣으면 도메인 객체를 다른 애플리케이션에서 재사용하기 어려워진다는 것이 분리 이유다.

### 2. 이체 한 건을 계층에 나눈 모습 (Evans 5장 「Services」)

```text
  Application  Funds Transfer App Service
               ① 입력 해석(XML 요청 등) ② 도메인 서비스에 이행 요청
               ③ 확인 응답 수신        ④ 알림을 보낼지 결정 → 인프라 호출
                         │
  Domain       Funds Transfer Domain Service
               Account·Ledger와 상호작용, 차변·대변 기입, 결과 확인(허용 여부 등)
                         │
  Infrastructure  Send Notification Service (이메일·우편 발송)
```

- Evans가 든 경계선 예.
  - "잔액이 기준 밑으로 떨어지면 이메일" — **알림을 보내라고 지시하는 것**은 애플리케이션, **기준을 넘었는지 판단하는 것**은 도메인(계좌 객체의 책임), 이메일 시스템 인터페이스는 인프라 서비스.
  - "거래 내역을 스프레드시트로 내보내기" — 은행 업무에 "파일 형식"이라는 의미가 없고 업무 규칙도 없으므로 애플리케이션 서비스.
- 4장의 그림 4.2(온라인 뱅킹 이체)에 Evans는 이렇게 적는다: 근본 업무 규칙("모든 대변에는 짝이 되는 차변이 있다")은 애플리케이션 계층이 아니라 도메인 계층의 책임이다.

### 3. 판별 질문 셋

| 질문 | "예"면 |
|---|---|
| 시스템을 안 만들어도 이 규칙이 업무에 있나? | 도메인 |
| 이 규칙이 **모든 진입점**(API·배치·메시지 소비자·관리 도구)에서 똑같이 참이어야 하나? | 도메인 — 진입점 쪽에 두면 진입점 수만큼 사본이 생긴다 |
| 판단에 필요한 정보가 객체 안(또는 인자로 받을 수 있는 값)에 있나? | 엔티티·값 객체 메서드. 여러 애그리거트가 필요하면 도메인 서비스, 저장소 조회가 필요하면 원본 회색지대 2의 세 해법 |

- 두 번째 질문이 이 노트의 중심이다. 진입점은 늘어난다. 규칙을 진입점에 두면 "새 진입점을 만든 사람이 규칙을 기억해야 한다"는 조건이 생긴다.

### 실험: 같은 규칙을 진입점 세 곳에 둘 때 vs 엔티티에 둘 때

- 환경: JDK 21(`eclipse-temurin:21-jdk`, openjdk 21.0.12, `--cpus=2`, 네트워크 없음), 실험용 git 저장소(scratchpad), 2026-10-03.
- 두 변형
  - `scattered/`: `Authorization`은 `getStatus`·`setStatus`만 있다. `CancelApi`·`BatchCancelJob`·`AdminCancelTool`이 각자 "정산이면 거절"을 검사하고 `setStatus(CANCELLED)`를 부른다.
  - `rich/`: `Authorization.cancel(now)` 안에 규칙이 있고, 세 진입점은 `a.cancel(now)`만 부른다.
- 새 규칙 "승인 후 7일이 지나면 취소 불가"를 넣는다. 분산 변형은 1단계에서 API만 고치고(사본 누락 재현), 2단계에서 나머지 둘을 고친다.
- 검사 `PathCheck`: 8일 지난 승인을 세 진입점 각각으로 취소해 본다.

```java
// rich/Authorization.java — 1단계에서 추가된 줄은 첫 번째 if
public void cancel(Instant now) {
    if (now.isAfter(approvedAt.plus(java.time.Duration.ofDays(7)))) throw new IllegalStateException("7일 경과");
    if (status == Status.SETTLED) throw new IllegalStateException("정산된 승인은 취소 불가");
    this.status = Status.CANCELLED;
}
```

(실험, JDK 21 temurin, 2026-10-03) 1단계 `git diff --stat`

```text
 rich/Authorization.java  | 1 +
 scattered/CancelApi.java | 1 +
 2 files changed, 2 insertions(+)
```

(실험, JDK 21 temurin, 2026-10-03) 1단계 뒤 `PathCheck`

```text
[scattered]
  CancelApi        8일 지난 승인 취소 → 거절: 7일 경과
  BatchCancelJob   8일 지난 승인 취소 → 취소됨(규칙 위반)
  AdminCancelTool  8일 지난 승인 취소 → 취소됨(규칙 위반)
  위반 경로 = 2 / 3
[rich]
  CancelApi        8일 지난 승인 취소 → 거절: 7일 경과
  BatchCancelJob   8일 지난 승인 취소 → 거절
  AdminCancelTool  8일 지난 승인 취소 → 거절: 7일 경과
  위반 경로 = 0 / 3
```

(실험, JDK 21 temurin, 2026-10-03) 규칙 변경 전체(base → 분산 2단계까지)와 사본 위치

```text
 scattered/AdminCancelTool.java | 1 +
 scattered/BatchCancelJob.java  | 1 +
 scattered/CancelApi.java       | 1 +
 3 files changed, 3 insertions(+)
 rich/Authorization.java | 1 +
 1 file changed, 1 insertion(+)

== 상태를 직접 바꾸는 호출(setStatus) 위치 수
scattered  3
rich       0
== 규칙 사본(7일 검사) 위치 수
scattered  3
rich       1
```

(실험, JDK 21 temurin, 2026-10-03) 반대 사례 — 흐름 관심사(배치에만 실행 로그 한 줄)

```text
 rich/BatchCancelJob.java      | 1 +
 scattered/BatchCancelJob.java | 1 +
 2 files changed, 2 insertions(+)
```

- 관찰
  - 규칙을 정확히 반영하는 데 고친 파일: 분산 3개, 엔티티 1개. 분산 쪽은 2단계를 빠뜨리면 2/3 경로가 새 규칙을 어긴다.
  - 분산 2단계를 마친 뒤에는 두 변형 모두 0/3이다. 차이는 "고칠 곳 수"와 "빠뜨릴 수 있는가"이지, 완성된 코드의 정답 여부가 아니다.
  - 분산 변형에는 `setStatus`를 부르는 외부 위치가 3곳 남는다. 네 번째 진입점을 만드는 사람도 같은 setter로 규칙 없이 상태를 바꿀 수 있다.
  - 반대 사례: 배치에만 해당하는 흐름 변경은 두 변형 모두 1파일이다. 규칙을 엔티티로 옮겨도 흐름 변경의 비용은 줄지 않는다. 이득은 **여러 진입점이 공유하는 규칙**에서만 난다.
- 한계: 진입점 3개·규칙 1개짜리 축소 모델이다. 위반 경로 수는 "한 곳만 고쳤다"는 조건을 일부러 만든 결과이며, 실제 누락 빈도를 잰 것이 아니다.

## 쓰이는 자료구조·알고리즘

- **가드가 붙은 상태 전이** — `cancel()`은 "현재 상태 + 입력(시각) → 허용/거절 + 다음 상태" 함수다. 전이 표로 키우는 법은 [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md)
- **계층 = 방향 있는 의존 그래프** — 계층 규칙은 "간선이 아래(또는 안쪽)로만 향한다"는 그래프 제약이다. 순환이 생기면 계층이 무너진 것이다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md), [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md)
- **사본 찾기 = 텍스트 검색** — "같은 규칙 N벌"은 우선 `grep`으로 조건식·상수(`ofDays(7)`, `SETTLED`)를 찾아 위치 수를 센다. 큰 코드베이스는 같은 모양의 코드 조각을 해시로 묶는 복제 탐지 도구를 쓴다. [algorithm/27-string-hashing](../../algorithm/27-string-hashing/2-summary.md)
- **단일 출처(single source)** — 규칙 하나 = 메서드 하나. 진입점은 그 메서드의 호출자로만 남는다.

## 적용 — 풀어나가는 법

### 1. 규칙을 문장으로, 진입점을 표로 적는다

```text
  규칙                                   CancelApi  Batch  Admin  메시지 소비자
  R1 정산된 승인은 취소 불가                 ✓         ✓      ✓       ?
  R2 승인 후 7일 지나면 취소 불가             ✓         ✓      ✓       ?
```

- 같은 줄에 ✓가 두 개 이상이면 그 규칙은 도메인으로 옮길 후보다. `?`는 확인이 안 된 경로다.

### 2. 사본을 찾는다 (진단)

```bash
# 상태를 서비스·컨트롤러가 직접 바꾸는 곳
grep -rn "setStatus(" src/main/java --include=*.java | grep -v "/domain/"
# 같은 판단을 밖에서 하는 곳 (값을 꺼내 비교)
grep -rnE "getStatus\(\) *(==|!=)|getStatus\(\)\.equals" src/main/java | grep -v "/domain/"
# 규칙 상수의 사본
grep -rn "ofDays(7)" src/main/java
```

### 3. 판단을 엔티티로 옮기고, 진입점은 "시키기"만 한다

```java
// 도메인 — 판단
public class Authorization {
    private Status status;
    private final Instant approvedAt;

    public void cancel(Instant now) {                  // 시각은 인자로 받는다(원본 「도메인이 인프라를 몰라야 하는 이유」)
        if (now.isAfter(approvedAt.plus(CANCEL_WINDOW))) throw AuthorizationException.windowClosed(id);
        if (status == Status.SETTLED) throw AuthorizationException.alreadySettled(id);
        status = Status.CANCELLED;
    }
    // setStatus 없음
}

// 애플리케이션 — 조율 (Spring 예)
@Service
public class CancelAuthorizationService {
    private final AuthorizationRepository repo;
    private final Clock clock;
    private final CancelNotifier notifier;

    @Transactional
    public void cancel(CancelCommand cmd) {
        Authorization a = repo.findById(cmd.authorizationId()).orElseThrow();   // 불러오기
        a.cancel(clock.instant());                                               // 시키기
        notifier.cancelled(a.id());                                              // 부수 작업(알림 여부는 흐름의 결정)
    }
}
```

- 배치·관리 도구도 같은 `a.cancel(...)`을 부른다. 배치가 "거절된 건은 건너뛴다"를 결정하는 것은 흐름이므로 배치 쪽에 남는다.
- 상담원 예외(예: "관리자는 7일이 지나도 취소 가능")가 업무 규칙이면 도메인 메서드에 명시적 인자로 넣는다(`cancelByAgent(now, AgentOverride)`). 진입점에서 `if`로 우회하지 않는다.

### 4. 모든 진입점을 같은 테스트로 돈다

- 실험의 `PathCheck`처럼 "규칙 위반 입력 1개 × 진입점 N개" 표를 테스트로 만든다. 새 진입점이 생기면 표에 한 줄을 더한다.
- 도메인 메서드 자체는 스프링·DB 없이 `new`로 만들어 테스트한다(02번).

### 5. 경계를 기계로 지킨다

- `domain` 패키지가 `org.springframework`·`jakarta.persistence`를 import하지 않는지, 서비스 밖에서 상태 setter를 부르지 않는지 ArchUnit 같은 아키텍처 테스트로 막는다. 방법은 [software-design/38](../../software-design/38-layered-hexagonal-clean/2-summary.md) 「실험 B」.

## 장애 시나리오와 대처

### 1. 같은 규칙 N벌 중 하나만 수정 (⚠ 커리큘럼)

- **현상**: 규칙 변경을 배포했는데 일부 경로에서 옛 규칙대로 처리된다. "앱에서는 막히는데 배치로는 취소됐다".
- **보이는 형태**: 특정 진입점(배치 잡 이름, 관리 도구 사용자) 로그에만 규칙 위반 처리 기록. CS 문의 "기한 지난 건이 취소됐다". 데이터 감사 쿼리(`approved_at < now() - interval '7 days' and status = 'CANCELLED' and cancelled_by = 'batch'`)에 행이 나온다.
- **원인**: 규칙이 진입점마다 복사돼 있었고, 변경 PR이 그중 일부만 고쳤다. 실험의 1단계 상태(2/3 위반)와 같다.
- **대처**: 사본을 `grep`으로 전수 찾는다. 판단을 엔티티 메서드 하나로 옮기고 setter를 닫는다. 진입점 × 위반 입력 테스트를 추가한다. 이미 잘못 처리된 건은 데이터로 찾아 업무 담당자와 정정한다.

### 2. 컨트롤러에 있는 규칙을 메시지 소비자·배치가 우회

- **현상**: HTTP로는 거절되는 요청이 큐 메시지나 재처리 배치로 들어오면 통과한다.
- **보이는 형태**: 같은 업무 오류가 소비자 로그에는 없는데 결과 데이터에는 있다. `@Valid`·컨트롤러 `if`에만 업무 규칙이 있다.
- **원인**: 업무 불변식을 프레젠테이션 검증으로 처리했다. 원본 회색지대 1의 "입력 형식 검증 / 도메인 불변식 / 컨텍스트 의존 규칙" 3분법에서 둘째를 첫째 자리에 둔 것이다.
- **대처**: 형식 검증(필수값·길이)은 컨트롤러에, 업무 불변식은 엔티티·값 객체 생성자와 메서드에 둔다. 모든 진입점이 같은 도메인 메서드를 지나게 한다.

### 3. 도메인에 흐름이 들어감 — 외부 호출·알림·트랜잭션을 엔티티가 안다

- **현상**: 엔티티 메서드 테스트에 목(mock)이 줄줄이 필요하다. 엔티티 메서드 안에서 HTTP 호출이 실패해 상태가 반쯤 바뀐다.
- **보이는 형태**: `domain` 패키지에 `RestTemplate`·`KafkaTemplate`·`@Transactional` import. 원본 「현장에서 만나는 상황」의 `previousStatus` 같은 롤백용 필드.
- **원인**: "무슨 순서로"(알림 보내기, 외부 승인 받기)를 "무엇이 옳은가"와 같은 곳에 넣었다.
- **대처**: 판단은 엔티티, 외부 호출·알림 여부는 애플리케이션 서비스로 뺀다. 외부 시스템과의 정합성은 outbox·saga로 다룬다([distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md), [distributed/15](../../distributed/15-saga/2-summary.md)). 트랜잭션 안의 원격 호출을 피하는 이유는 [database/24](../../database/24-transaction-boundaries-in-app-code/2-summary.md).

### 4. 도메인 서비스 남용 → 엔티티가 다시 빈 껍데기

- **현상**: `XxxDomainService`가 엔티티 값을 꺼내 판단하고 setter로 결과를 써 넣는다. 이름만 "도메인"이다.
- **보이는 형태**: 엔티티에 getter·setter만 있고 도메인 서비스 클래스가 수백 줄. 한 엔티티만 다루는 도메인 서비스 메서드.
- **원인**: Evans 5장은 서비스를 "엔티티나 값 객체의 자연스러운 책임이 아닌" 중요한 도메인 연산에만 쓰라고 하고, 엔티티·값 객체의 행위를 다 빼앗지 않게 신중히 쓰라고 경고한다. 한 엔티티 안의 정보로 판단할 수 있는 규칙을 서비스로 옮기면 이 경고를 어긴다.
- **대처**: 한 엔티티의 정보만 쓰는 판단은 엔티티로 되돌린다. 두 애그리거트 이상이 필요한 규칙(이체처럼)만 도메인 서비스에 남긴다. 상세는 06번(빈약 vs 풍부)과 08번(도메인 서비스·정책).

## 핵심 문장

- 도메인 로직은 "무엇이 허용되는가", 애플리케이션 로직은 "무슨 순서로"에 답한다. Evans는 애플리케이션 계층을 얇게, 업무 규칙 없이 조율만 하는 층으로 정의한다.
- 규칙을 도메인으로 보낼지 가르는 실무 질문은 "이 규칙이 모든 진입점에서 똑같이 참이어야 하나"다.
- 실험에서 진입점 세 곳에 복사한 규칙을 바꾸려면 3파일을 고쳐야 했고, 한 곳만 고친 상태에서는 3경로 중 2경로가 새 규칙을 어겼다. 엔티티에 둔 규칙은 1파일 변경으로 3경로가 모두 따랐다.
- 흐름에만 관한 변경은 규칙을 어디에 두든 비용이 같다. 이득은 공유 규칙에서만 난다.
- 엔티티에 setter를 열어 두면 규칙을 옮겨도 새 진입점이 규칙을 우회할 길이 남는다.

## 관련 주제·근거

- 원본(이어받음): [domain-modeling/domain-vs-application-logic](../domain-vs-application-logic/2-summary.md) — 감별법, 검증 3분법, 중복 검사 해법 A·B·C, 여러 애그리거트·조회·이벤트 회색지대, 계층별 패키지 배치
  - 참고: 원본 「계층별 배치」의 "의존 방향은 항상 안쪽(도메인)을 향한다"는 헥사고날·DIP 배치 기준이다. Evans 4장의 고전 계층형은 각 계층이 아래 계층(인프라 포함)에 의존하는 구조다. DDD Reference(2015) 「Layered Architecture」는 도메인에서 인프라 의존을 없애라고 적고, 헥사고날 같은 관련 패턴이 그 격리를 같거나 더 잘 해낼 수 있다고 덧붙인다.
  - 참고: 원본 회색지대 3의 "하나의 트랜잭션은 하나의 애그리게이트만 변경"은 Vernon "Effective Aggregate Design" 1부(2011)의 문장이다. Vernon도 이를 "rule of thumb"(경험칙)이라 부르며 대부분의 경우의 목표로 제시한다.
- 선행: [software-design/02-modularity-coupling-cohesion](../../software-design/02-modularity-coupling-cohesion/2-summary.md) — 응집·결합, 변경이 몇 곳에 퍼지나
- 연결
  - [02-pojo-and-persistence-ignorance](../02-pojo-and-persistence-ignorance/2-summary.md) — 도메인 객체가 프레임워크를 모르게
  - [06-anemic-vs-rich-model](../06-anemic-vs-rich-model/2-summary.md) — setter가 열린 모델의 불법 상태
  - [07-domain-logic-patterns-and-service-layer](../07-domain-logic-patterns-and-service-layer/2-summary.md) — Transaction Script·Domain Model 선택, Service Layer의 트랜잭션 경계
  - [08-domain-services-and-policies](../08-domain-services-and-policies/2-summary.md) · [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md)
  - [software-design/06-clean-code](../../software-design/06-clean-code/2-summary.md)(Tell, Don't Ask) · [software-design/26-functional-core-imperative-shell](../../software-design/26-functional-core-imperative-shell/2-summary.md) · [software-design/38-layered-hexagonal-clean](../../software-design/38-layered-hexagonal-clean/2-summary.md)
  - [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md)
- 근거
  - Evans 『Domain-Driven Design』(2003) 4장 Isolating the Domain(Layered Architecture, 그림 4.2 이체 예), 5장 A Model Expressed in Software(Services, "SERVICES and the Isolated Domain Layer", "Partitioning Services into Layers") — 2003-04-15 최종 원고 PDF로 문장 대조, 장 구성은 dddcommunity.org 목차 <https://www.dddcommunity.org/uncategorized/toc/>
  - Evans 『DDD Reference』(2015) 「Layered Architecture」·「Services」 <https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf>
  - Fowler "AnemicDomainModel"(2003-11-25) <https://martinfowler.com/bliki/AnemicDomainModel.html>
  - Fowler 『PoEAA』(2002) 「Service Layer」(Randy Stafford) — domain logic vs application logic, domain facade vs operation script <https://www.informit.com/articles/article.aspx?p=1398617&seqNum=4> · 카탈로그 <https://martinfowler.com/eaaCatalog/serviceLayer.html>
  - Vernon "Effective Aggregate Design" Part I(2011) <https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf>
- 실험 목록
  - 규칙 분산 vs 엔티티 집중: 진입점 3개(`CancelApi`·`BatchCancelJob`·`AdminCancelTool`), 새 규칙 추가 시 `git diff --stat`, 한 곳만 고친 상태의 위반 경로 수(2/3 vs 0/3), setter 호출 위치 수(3 vs 0), 흐름 변경 반대 사례(1파일 vs 1파일) — JDK 21.0.12(temurin), 컨테이너 `--cpus=2`·네트워크 없음
