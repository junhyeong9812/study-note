# software-design/37-architecture-styles — 아키텍처 스타일: 요구(품질 속성)에 맞춰 고르기 — 정리 (힌트)

## 해결하는 문제

시스템의 큰 모양(스타일)은 나중에 바꾸기 비싸다. 그런데 스타일마다 잘 버티는 변경과 품질이 다르다.

```text
 요구: "결제 수단이 매달 는다"            요구: "하류가 죽어도 주문은 받아야 한다"
   계층형     → 공유 switch 여러 곳 수정      동기 호출 사슬 → 하류 다운 = 주문 실패
   마이크로커널 → 플러그인 파일 하나 추가      이벤트 기반   → 주문 수락, 처리는 나중에
       ↑ 같은 기능, 다른 변경 비용               ↑ 같은 기능, 다른 가용성
```

- *아키텍처 스타일(architecture style)*: 시스템 전체 구조의 이름 붙은 골격. 계층형·파이프라인·마이크로커널·서비스 기반·이벤트 기반·공간 기반·마이크로서비스 등.
- *품질 속성(quality attribute, 아키텍처 특성)*: 기능과 별개로 시스템이 갖춰야 할 성질. 가용성·확장성·변경 용이성·성능·시험 용이성 등. Richards–Ford는 "-ilities"라고 부르고 "성공 기준"이라고 쓴다(1장, 무료 공개 장).

쉬운 예: 이삿짐 트럭과 오토바이 배달은 둘 다 "운반"이다. 무엇을 얼마나 자주 나르냐에 따라 맞는 쪽이 갈린다.\
똑같은 구조다. 스타일은 기능이 아니라 **품질 요구**로 고른다.\
실무 예: 정합성이 1순위인 원장을 결과적 일관성 이벤트로 짜면 "승인됐는데 원장엔 없는" 시간이 생긴다. 확장이 1순위인 티켓 오픈을 단일 DB 계층형으로 짜면 DB에서 막힌다.

각 스타일의 모양·강점·약점·토폴로지는 원본 [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) 「1. 모놀리식」「2. 분산형」에 이미 있다. 이 노트는 그 위에 **요구-스타일 불일치를 진단하는 법**과 그것을 보이는 실험 둘을 더한다.

## 동작·원리

### 1. 스타일 지도 — 두 갈림길

```text
                        배포 단위가 하나인가?
              예 ──────────────┴────────────── 아니오
      모놀리식                                    분산
  ┌───────────┬───────────┬─────────┐   ┌──────────┬──────────┬──────────┬──────────┐
  계층형      파이프라인   마이크로커널    서비스기반   이벤트기반   공간기반    마이크로서비스
  기술로 나눔  변환 단계   코어+플러그인   DB 공유     비동기 이벤트 DB를 경로   서비스별 DB
                                                               밖으로
  ─────────── 나누는 축 ───────────
  기술 분할(technical partitioning): 계층형        → "표현·업무·영속"으로
  도메인 분할(domain partitioning): 서비스 기반·마이크로서비스 → "결제·주문·정산"으로
  (마이크로커널은 둘 다 가능: 코어/플러그인 경계는 기술 쪽, 플러그인을 업무 종류로 나누면 도메인 쪽)
```

- 기술 분할·도메인 분할이라는 이름과 정의는 Richards–Ford 8장 「Component-Based Thinking」의 것이다(독자 노트로 장 위치만 확인). 계층형이 기술 분할이라는 것은 같은 책 10장. 마이크로커널이 기술·도메인 분할을 둘 다 제공한다는 평가는 12장의 것으로 독자 노트(bagerbach.com)로 확인했다 — 책 본문은 직접 못 봤다.

- 첫 갈림길(배포 단위 수)과 스타일별 설명: 원본 「전체 흐름」.
- *기술 분할 vs 도메인 분할*: 최상위 단위를 기술 역할로 나누나, 업무 영역으로 나누나. 어느 쪽이 맞는지는 **자주 오는 변경이 어느 축을 따라오나**로 정한다([04-decompose-by-change](../04-decompose-by-change/2-summary.md)).

### 2. 스타일 = 특정 변경·특정 품질에 최적화된 모양

```text
 변경 축                       잘 버티는 스타일              비싸지는 스타일
 ─────────────────────────────────────────────────────────────────────────
 "종류가 는다" (수단·포맷)      마이크로커널: 플러그인 추가      계층형: 공유 switch 여러 곳
 "모든 종류에 필드 추가"         계층형: 층마다 1곳             마이크로커널: 계약 + 모든 플러그인
 "하류 장애에도 접수"            이벤트 기반                    동기 호출 사슬
 "강한 정합성 한 번에"           모놀리식·서비스 기반(로컬 ACID)  마이크로서비스·이벤트(Saga·결과적)
```

- Richards–Ford 1장 「Laws of Software Architecture」: "Everything in software architecture is a tradeoff." 따름정리: 트레이드오프가 없어 보이면 아직 못 찾은 것이다.
- 그러므로 스타일 선택은 "어느 쪽 비용을 감수할지" 고르는 일이다. 실험 A·B가 같은 기능을 두 모양으로 짜서 그 비용을 잰다.

### 실험 A: 같은 결제 기능, 계층형 vs 마이크로커널 — 변경 두 가지

두 저장소를 같은 동작(CARD·KAKAO 수수료·한도)으로 만들고, 같은 요구 두 개를 각각 브랜치로 적용했다.

```text
 계층형                                   마이크로커널
 presentation/PaymentController           core/PaymentPlugin  (계약: type·fee·limit)
 business/PaymentService  (switch 수수료)  core/Kernel         (ServiceLoader로 플러그인 수집)
 business/LimitPolicy     (switch 한도)    plugins/CardPlugin, plugins/KakaoPlugin
 persistence/PaymentRepository            META-INF/services/core.PaymentPlugin (등록)
```

- R1: 새 결제 수단 `POINT`(수수료 0, 한도 30만).
- R2: 모든 결제에 통화(`currency`) 추가, 해외 통화면 수수료 1%p 추가.

계층형 R1의 실제 변경(두 `switch`에 한 줄씩):

```java
            case "KAKAO" -> amount * 1 / 100;
            case "POINT" -> 0;                       // PaymentService
            case "KAKAO" -> 2_000_000;
            case "POINT" -> 300_000;                 // LimitPolicy
```

마이크로커널 R1의 실제 변경(새 파일 + 등록 한 줄):

```java
public class PointPlugin implements core.PaymentPlugin {
    public String type() { return "POINT"; }
    public long fee(long amount) { return 0; }
    public long limit() { return 300_000; }
}
```

(실험, 호스트 git 2.43.0 `git diff --stat`, 각 브랜치를 JDK 21.0.12 temurin `--cpus=2`에서 컴파일·실행해 동작 확인, `scratchpad/sd/35/e37/`, 2026-10-02)

```text
== layered r1-new-method
 src/business/LimitPolicy.java    | 1 +
 src/business/PaymentService.java | 1 +
 2 files changed, 2 insertions(+)
== layered r2-currency
 src/Main.java                           | 2 +-
 src/business/PaymentService.java        | 5 +++--
 src/persistence/PaymentRepository.java  | 2 +-
 src/presentation/PaymentController.java | 2 +-
 4 files changed, 6 insertions(+), 5 deletions(-)
== kernel r1-new-method
 src/META-INF/services/core.PaymentPlugin | 1 +
 src/plugins/PointPlugin.java             | 6 ++++++
 2 files changed, 7 insertions(+)
== kernel r2-currency
 src/Main.java                | 2 +-
 src/core/Kernel.java         | 6 +++---
 src/core/PaymentPlugin.java  | 2 +-
 src/plugins/CardPlugin.java  | 2 +-
 src/plugins/KakaoPlugin.java | 2 +-
 5 files changed, 7 insertions(+), 7 deletions(-)
```

기존 파일 수정 수 / 새 파일 수(`git diff --name-only --diff-filter=M|A`):

```text
layered r1-new-method 기존파일수정=2 새파일=0
layered r2-currency 기존파일수정=4 새파일=0
kernel r1-new-method 기존파일수정=1 새파일=1
kernel r2-currency 기존파일수정=5 새파일=0
```

실행 확인(같은 환경):

```text
== layered r1-new-method: CARD ok fee=200 KAKAO ok fee=100 POINT ok fee=0
== layered r2-currency: CARD ok fee=300 KAKAO ok fee=200
== kernel r1-new-method: CARD ok fee=200 KAKAO ok fee=100 POINT ok fee=0
== kernel r2-currency: CARD ok fee=300 KAKAO ok fee=200
```

- 관찰 1(R1) — 계층형은 **기존 업무 코드 2곳**(같은 `switch`가 둘)을 고쳤다. 마이크로커널은 Java 기존 코드를 고치지 않았다. 수정된 기존 파일 1개는 등록 파일 한 줄이다.
- 관찰 2(R2) — 이번에는 마이크로커널이 계약·커널·**모든 플러그인**을 고쳤다(5개). 계층형은 층마다 한 곳씩 4개였다.
- 해석 — 두 설계 모두 플러그인 2개짜리 장난감이라 파일 수 차이는 작다. 차이는 **무엇에 비례하나**다. 계층형 R1은 "같은 `switch`가 있는 곳의 수"에, 마이크로커널 R2는 "플러그인 수"에 비례한다(구조에서 나온 추론, 플러그인 2개에서만 측정).
- 결론 — "결제 수단이 자주 는다"가 주된 변경이면 마이크로커널이 맞고, "모든 수단에 공통 필드가 자주 붙는다"면 계약이 자주 깨져 손해다(원본 1.3의 "계약을 바꾸면 모든 플러그인이 깨진다").

### 실험 B: 같은 주문 기능, 동기 호출 vs 이벤트 — 하류 장애 중 가용성

논리 시간 모형이다. 1초에 주문 1건, 1000초. 알림 서비스가 300~599초 동안 다운된다.

- 동기 스타일: 주문 처리 안에서 알림을 호출하고, 실패하면 주문도 실패한다.
- 이벤트 스타일: 주문은 수락하고 알림 이벤트를 큐에 넣는다. 알림 소비자는 살아 있을 때 초당 최대 5건 처리한다.

```java
for (int t = 0; t < N; t++) if (notifyUp(t)) okSync++;              // 동기: 알림이 죽으면 주문도 실패
for (int t = 0; t < N + 200; t++) {                                 // 이벤트: 큐에 쌓였다 복구 후 소비
    if (t < N) queue.add(t);
    if (notifyUp(t)) for (int k = 0; k < rate && !queue.isEmpty(); k++) {
        int born = queue.poll(); maxLag = Math.max(maxLag, t - born); delivered++;
    }
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/35/e37/qa/SyncVsEvent.java`, 2026-10-02 — 결정적 모형이라 실행마다 같다)

```text
동기 호출 스타일 : 주문 성공 700/1000 (70.0%)
이벤트 스타일    : 주문 성공 1000/1000 (100.0%), 알림 전달 1000건, 최대 큐 길이 301, 알림 최대 지연 300초
```

- 관찰 — 동기 사슬은 하류 다운 시간만큼 주문을 잃었다(30%). 이벤트는 주문을 모두 받았지만, 알림이 **최대 300초 늦었다**. 큐가 301건까지 쌓였다.
- 해석 — 이벤트 스타일은 가용성을 얻고 **즉시성·일관성**을 내준다. "주문 즉시 알림이 반드시 가야 한다"가 요구라면 이 결과는 품질 미달이다. 모형의 수치는 가정(다운 300초, 처리율 5건/초)에서 나온 것이고, 핵심은 비용이 **어디로 옮겨 가나**다.
- 원본 2.2의 "결과적 일관성을 감수한다는 뜻"(150ms 창)을 장애 시간으로 늘린 판이다.

### 3. 요구 → 스타일 판단 순서

```text
 ① 품질 속성 상위 3개를 고른다 (예: 정합성 > 변경 용이성 > 확장성)
 ② 각 속성을 시나리오로 쓴다   "알림 서비스가 5분 죽어도 주문 접수율 99% 이상"
 ③ 후보 스타일마다 시나리오를 대 본다 (실험 A·B처럼 비용이 어디로 가나)
 ④ 버리는 속성을 적는다      "이벤트 → 알림 최대 지연 = 장애 시간"
 ⑤ ADR로 남긴다 ([47-architecture-decision-records](../47-architecture-decision-records/2-summary.md))
```

- *품질 속성 시나리오*: 품질 요구를 "어떤 자극이 어떤 환경에서 오면 시스템이 어떻게 응답하고 무엇으로 재나"의 시험 가능한 문장으로 쓴 것. 이 기법은 SEI 계열 문헌(Bass·Clements·Kazman 『Software Architecture in Practice』)의 것으로 알려져 있으나 이 노트에서 원문을 확인하지 않았다 [?]. ISO/IEC 25010 품질 모델과 함께 [46-quality-attributes-and-tradeoffs](../46-quality-attributes-and-tradeoffs/2-summary.md)에서 다룬다.
- 시스템 안에서 경로마다 다른 스타일을 섞을 수 있다(원본 「전체 흐름」: 한 마이크로서비스 내부가 헥사고날). 예: 승인은 동기·강한 일관성, 알림·집계는 이벤트.

## 쓰이는 자료구조·알고리즘

- **의존 그래프**: 스타일은 "어떤 모듈이 어떤 모듈에 의존해도 되나"의 규칙이다. 계층형 = 층 사이 단방향 DAG, 마이크로커널 = 플러그인 → 코어 별 모양. 방향 규칙은 [38-layered-hexagonal-clean](../38-layered-hexagonal-clean/2-summary.md), 순환 탐지는 [39-component-principles](../39-component-principles/2-summary.md).
- **디스패치 테이블 vs switch**: 마이크로커널의 플러그인 맵(타입 → 구현)은 계층형의 반복된 `switch`를 테이블 하나로 바꾼 것이다(실험 A R1).
- **큐(FIFO)**: 이벤트 기반의 완충. 실험 B에서 큐 길이가 장애 시간 × 유입률만큼 자랐다. 큐는 [data-structure 영역](../../data-structure/README.md).
- **파이프와 필터**: 파이프라인 스타일 = 함수 합성 + 단계 사이 버퍼.

## 적용 — 풀어나가는 법

1. **요구를 품질 속성 시나리오로 바꾼다.** "빠르게"가 아니라 "p99 300ms", "알림 장애 5분에도 주문 접수".
2. **잦은 변경 축을 데이터로 찾는다.** 지난 변경 이력에서 파일별 변경 횟수를 센다(아래 명령). 이 명령은 빈도만 센다. "함께 바뀌는 묶음"은 커밋별 파일 목록(`git log --name-only`)을 직접 보거나 변경 결합 분석으로 본다.
   ```bash
   git log --since=6.months --name-only --pretty=format: | sort | uniq -c | sort -rn | head
   ```
   같은 `switch`·같은 층 묶음이 매번 함께 바뀌면 그 축이 스타일 경계를 결정한다(실험 A).
3. **후보 스타일을 시나리오로 대 본다.** 작은 스파이크(실험 A처럼 두 모양으로 짜서 diff)나 모형(실험 B)으로 "비용이 어디로 가나"를 본다.
4. **버리는 것을 적는다.** 이벤트를 고르면 지연·순서·중복 처리, 마이크로서비스면 분산 트랜잭션·운영 N배(원본 2.5 「치르는 대가」).
5. **경로별로 섞는다.** 강한 일관성이 필요한 쓰기 경로와 지연을 허용하는 부가 경로를 나눈다.
6. **불일치 신호를 지표로 본다**(아래 장애 시나리오의 "보이는 형태").

## 장애 시나리오와 대처

### 1. 스타일-요구 불일치 → 품질 속성 미달 (⚠ 커리큘럼)

- 현상: 기능은 다 되는데 "자주 하는 변경"이 매번 비싸거나, 핵심 품질 지표가 목표에 못 미친다.
- 보이는 형태: 변경 리드타임 증가, PR마다 같은 파일 묶음 수정(실험 A의 계층형 R1: 같은 `switch` 2곳), 하류 장애 때 주문 성공률 급락(실험 B 70%).
- 원인: 스타일을 기능·유행으로 골랐다. 품질 우선순위와 잦은 변경 축을 확인하지 않았다.
- 대처: 상위 품질 속성 재정의 → 해당 경로만 다른 스타일로(예: 알림만 이벤트로 분리, 결제 수단만 플러그인화). 결정을 ADR로 남긴다.

### 2. 이벤트로 바꿨더니 "됐는데 안 됐다"는 문의가 는다

- 현상: 주문 완료 화면 뒤 알림·포인트가 늦게 온다. 하류 장애 때는 몇 분씩.
- 보이는 형태: 큐 적체(consumer lag) 증가, 주문 시각과 처리 시각의 차이 분포가 장애 시간만큼 늘어남(실험 B 최대 300초).
- 원인: 가용성을 얻는 대신 즉시성을 내줬다. 이 요구가 즉시성을 요구하는 경로였다.
- 대처: 즉시성이 필요한 단계는 동기로 되돌리거나, 화면에 중간 상태("처리 중")를 보인다. 적체 지표에 경보를 둔다([reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)).

### 3. 마이크로커널의 계약이 자주 바뀌어 모든 플러그인이 흔들린다

- 현상: 플러그인 추가보다 계약 변경이 더 잦다. 매번 모든 플러그인을 고친다.
- 보이는 형태: 계약 파일 변경 PR에 플러그인 N개가 함께 묶임(실험 A R2: 계약·커널·플러그인 전부).
- 원인: 변동성이 "종류"가 아니라 "공통 속성"에 있었다. 원본 1.3 "코어 계약을 정확히 그을 수 있을 때만 유효".
- 대처: 계약에 기본 구현(`default` 메서드)·컨텍스트 객체(인자 묶음)를 둬 추가를 비파괴로. 그래도 잦으면 플러그인화를 거둔다.

### 4. 마이크로서비스라 해 놓고 함께 배포한다 (분산 모놀리스)

- 현상: 서비스 하나 배포에 다른 서비스 배포가 줄줄이 필요하다.
- 보이는 형태: 배포 순서표, 공유 DB 스키마 변경 때 여러 서비스 동시 수정.
- 원인과 대처: 원본 「핵심 문장」·2.5 참고. 경계 재설정 또는 서비스 기반·모듈러 모놀리스로 후퇴([45-monolith-vs-microservices](../45-monolith-vs-microservices/2-summary.md)).

### 5. 계층형이 싱크홀이 된다

- 현상: 요청 대부분이 층마다 그대로 넘기기만 한다.
- 보이는 형태: 서비스 메서드가 리포지토리 호출 한 줄인 비율이 높다.
- 원인: 업무 로직이 거의 없는 CRUD에 층을 강제했다.
- 대처: Richards의 80-20 경험칙(요청의 20% 정도가 통과만 하면 정상, 대부분이면 과함)으로 판정하고, 층을 열거나(open layer) 단순 경로를 줄인다. 원본 1.1. 경험칙 출처는 Richards 『Software Architecture Patterns』(O'Reilly, 2015) 1장 Layered Architecture의 「Considerations」 절이다(O'Reilly 공개 발췌: "around 20 percent of the requests as simple pass-through processing"). 비율이 뒤집히면 일부 층을 열라고 하면서, 층 격리가 약해져 변경 통제가 어려워진다는 대가도 함께 적는다.

## 핵심 문장

- 아키텍처 스타일은 기능이 아니라 품질 속성과 잦은 변경 축으로 고른다. Richards–Ford의 첫 법칙대로 모든 선택은 트레이드오프다.
- 실험에서 새 결제 수단 추가는 계층형에서 기존 `switch` 2곳 수정, 마이크로커널에서 새 파일 하나였다. 모든 수단에 통화를 붙이자 반대로 마이크로커널이 계약과 모든 플러그인을 고쳤다.
- 하류 300초 장애 모형에서 동기 사슬은 주문 30%를 잃었고, 이벤트는 모두 받았지만 알림이 최대 300초 늦었다.
- 스타일-요구 불일치는 크래시가 아니라 변경 리드타임·품질 지표 미달로 보인다. 경로별로 다른 스타일을 섞어 맞춘다.

## 관련 주제·근거

- 원본
  - [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) — 스타일별 그림·강점/약점·토폴로지·SOA 교훈·분산 모놀리스
- 선행
  - [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md) — 원본 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md)
- 후속·연결
  - [38-layered-hexagonal-clean](../38-layered-hexagonal-clean/2-summary.md) — 계층형의 의존 방향 문제와 역전
  - [39-component-principles](../39-component-principles/2-summary.md) — 컴포넌트 단위 의존·순환
  - [36-extension-points-and-plugins](../36-extension-points-and-plugins/2-summary.md) — 마이크로커널의 플러그인 연결 방법(`ServiceLoader`)
  - [45-monolith-vs-microservices](../45-monolith-vs-microservices/2-summary.md), [46-quality-attributes-and-tradeoffs](../46-quality-attributes-and-tradeoffs/2-summary.md), [47-architecture-decision-records](../47-architecture-decision-records/2-summary.md)
  - [distributed 영역](../../distributed/README.md) — 결과적 일관성·Saga
- 글·책
  - Mark Richards, Neal Ford, 『Fundamentals of Software Architecture』(O'Reilly, 2020; 2판 2025). 1장(무료 공개 장, Thoughtworks 배포 PDF)에서 "architecture characteristics", "Everything in software architecture is a tradeoff." 확인. 2부 Architecture Styles의 장 구성(9 Foundations, 10 계층형 ~ 16 오케스트레이션 SOA, 이어서 마이크로서비스)은 검색 요약으로만 확인 [?] <https://www.oreilly.com/library/view/fundamentals-of-software/9781492043447/>
  - Mark Richards, 『Software Architecture Patterns』(O'Reilly, 2015) 1장 Layered Architecture 「Considerations」 — architecture sinkhole anti-pattern·80-20 rule(공개 발췌로 원문 확인) <https://www.oreilly.com/content/software-architecture-patterns/>
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-02)
  - A `scratchpad/sd/35/e37/layered`·`e37/kernel`(git 저장소, 브랜치 `r1-new-method`·`r2-currency`), `e37/build.sh`로 브랜치별 컴파일·실행 — `git diff --stat`·`--diff-filter=M|A`
  - B `scratchpad/sd/35/e37/qa/SyncVsEvent.java` — 논리 시간 모형, 동기 vs 이벤트의 주문 성공률·알림 지연
