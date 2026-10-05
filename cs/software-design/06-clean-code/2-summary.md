# software-design/06-clean-code — CLEAN 5속성과 속성 간 긴장: 품질 검사표 — 정리 (힌트)

## 해결하는 문제

코드 리뷰에서 "깔끔하다·지저분하다"는 감각만으로 판정하면 놓치는 것이 생긴다.\
결합과 중복은 diff 한 화면에 드러나지 않기 때문이다.

```text
 감각 리뷰                               검사표 리뷰
 "읽기 좋네요, 승인"                      C 이 클래스는 한 목적인가?
   │                                     L 이걸 바꾸면 무엇이 따라 바뀌나?
   └─ 같은 판단식이 세 번째 파일에도        E 내부 표현이 밖으로 새나?
      있다는 사실은 diff 밖에 있다         A 판단을 객체가 하나, 호출자가 하나?
                                         N 이 지식은 또 어디에 있나?  ← diff 밖을 보게 만든다
```

- *CLEAN*: 좋은 코드가 가져야 할 다섯 성질의 두문자어. **C**ohesive(응집), **L**oosely coupled(느슨한 결합), **E**ncapsulated(캡슐화), **A**ssertive(단정적), **N**onredundant(비중복).
- *품질 검사표*: 결과물이 갖췄는지 하나씩 묻는 질문 목록. SOLID가 "어떻게 만드나(수단)"라면 CLEAN은 "다 만든 것이 어떤 성질인가(상태)"를 묻는다(원본 노트의 구분).

쉬운 예: 공구함 정리 상태를 다섯 항목으로 점검하는 것이다. 서랍마다 한 종류(C), 서랍 하나를 빼도 옆이 안 흔들림(L), 손잡이만 잡으면 씀(E), 같은 공구가 두 서랍에 없음(N).\
똑같은 구조다.\
실무 예: 결제 서비스 PR에서 "카드 사용 가능 조건"을 고칠 때, 그 조건이 승인·환불·포인트 세 서비스에 따로 적혀 있으면 한 곳을 빠뜨린다. 검사표의 N 질문("이 지식은 또 어디 있나?")이 그 세 번째 사본을 찾게 만든다(아래 실험 A).

기초(5속성 정의, 응집·결합 등급 사다리, 나쁜 예·좋은 예 코드, 현장 상황)는 원본 [engineering/clean-code](../../engineering/clean-code/2-summary.md)의 「C」~「N」 절과 「5속성 간의 긴장 관계」에 있다.\
이 노트는 그것을 **리뷰용 검사표**로 다시 묶고, 속성 간 긴장을 같은 변경 요청을 두 설계에 적용하는 실험으로 보인다.\
이름·함수·주석은 [07-naming](../07-naming/2-summary.md)·[08-function-design](../08-function-design/2-summary.md)·[09-comments-and-conventions](../09-comments-and-conventions/2-summary.md)로 나눴다.

## 동작·원리

### 1. 다섯 속성 = 다섯 질문

```text
           ┌───────────────── 한 덩어리 안 ─────────────────┐
           │ C 응집     "이 안의 것들이 한 목적을 향하나?"       │
           │ E 캡슐화   "어떻게 저장했는지 밖에서 몰라도 되나?"   │
           │ A 단정적   "자기 데이터로 하는 판단을 스스로 하나?"  │
           └────────────────────────────────────────────────┘
           ┌───────────────── 덩어리 사이 ──────────────────┐
           │ L 느슨한 결합 "A를 바꿀 때 B도 바꿔야 하나?"        │
           │ N 비중복      "같은 지식이 두 곳에 있나?"           │
           └────────────────────────────────────────────────┘
```

- 위 셋은 클래스 하나를 열어 보면 답할 수 있다.
- 아래 둘은 **그 클래스 밖**을 봐야 답할 수 있다. 리뷰에서 가장 자주 놓치는 쪽이다.
- *응집도(cohesion)*: 한 덩어리 안 요소들이 서로 관련된 정도.
- *결합도(coupling)*: 한쪽을 바꿀 때 다른 쪽도 바꿔야 하는 정도.
- *지식(knowledge)*: 코드가 표현하는 규칙·사실 하나. 예: "쓸 수 있는 카드 = 활성 + 만료 전 + 정지 아님". DRY는 글자가 아니라 이 단위의 중복을 금한다(아래 4절).

### 2. 한 속성이 깨지면 변경 때 무엇이 보이나

| 속성 | 깨진 모양(스멜) | 변경 때 증상 | 더 볼 곳 |
|---|---|---|---|
| C | `CommonUtils`, 필드를 나눠 쓰는 메서드 묶음 | 서로 무관한 변경이 한 파일에 몰린다(Divergent Change) | [10-code-smells](../10-code-smells/2-summary.md) |
| L | 플래그 인자, 큰 객체 통째 전달, 동기 호출 체인 | 한 곳 변경에 여러 파일 수정(Shotgun Surgery) | [02-modularity-coupling-cohesion](../02-modularity-coupling-cohesion/2-summary.md) · [05-connascence](../05-connascence/2-summary.md) |
| E | setter, 가변 컬렉션을 그대로 돌려주는 getter | 불변식이 깨져도 어디서 깨졌는지 모른다 | [20-oop-fundamentals](../20-oop-fundamentals/2-summary.md) · [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md) |
| A | 데이터만 있는 클래스 + 판단은 서비스에 | 같은 조건식이 호출자마다 복사된다 | 원본 「A」, domain-modeling 06 |
| N | 같은 규칙의 사본 여러 개 | 사본 하나를 빠뜨려 화면마다 결과가 다르다 | [11-when-to-abstract](../11-when-to-abstract/2-summary.md) |

- A와 N은 자주 함께 깨진다. 판단이 객체 밖에 있으면, 판단식이 호출자 수만큼 복사되기 때문이다(실험 A).

### 3. 속성 간 긴장

```text
        N 비중복 ───── 당김 ───── L 느슨한 결합
   "한 곳에만 두자"           "공유하면 함께 묶인다"
        │  공유 라이브러리로 합치면 N은 지키고 L은 잃는다
        │  서비스마다 복제하면 L은 지키고 N은 잃는다
        │
        └── 과잉 적용: 글자만 같은 "우연한 중복"까지 합치면
            서로 다른 지식이 한 몸이 된다 → 한쪽 변경이 다른 쪽을 깨뜨린다 (실험 B)

        E 캡슐화 ───── 당김 ───── 편의성(아무 데서나 꺼내 쓰기)
        A 단정적 ───── 당김 ───── 계층 분리(DB가 필요한 판단은 객체 안에 못 넣는다)
        C 응집   ───── 당김 ───── N (함께 변하는 것을 묶으면 다른 곳과 겹칠 수 있다)
```

- 판정 기준은 원본 「5속성 간의 긴장 관계」 표에 있다. 공통 질문은 하나다: **이 둘은 함께 바뀌나?**
- 함께 바뀌면 한 곳에 둔다(N·C 우선). 따로 바뀌면 떨어뜨린다(L 우선). 글자가 같은지는 기준이 아니다.

### 실험 A: 같은 요구를 Ask 설계와 Tell 설계에 적용

요구: "해외 결제가 잠긴 카드는 쓸 수 없다."\
두 설계 모두 승인·환불·포인트 세 서비스가 "쓸 수 있는 카드인가"를 판단한다.

- *Ask(묻기)*: 호출자가 getter로 값을 꺼내 직접 판단한다.
- *Tell(시키기)*: 객체에게 판단을 맡긴다(`card.isUsable(today)`). "Tell, Don't Ask"라는 이름으로 알려진 원칙이다.

```java
// Ask 설계 — 같은 지식이 세 서비스에 있다. PointService만 모양이 다르다
// ApprovalService, RefundService
card.getStatus() == CardStatus.ACTIVE && card.getExpiry().isAfter(today) && !card.isBlocked()
// PointService
boolean usable = CardStatus.ACTIVE.equals(card.getStatus());
usable = usable && !card.isBlocked();
return usable && today.isBefore(card.getExpiry());

// Tell 설계 — 지식은 Card 한 곳에만
public boolean isUsable(LocalDate today) {
    return status == CardStatus.ACTIVE && expiry.isAfter(today) && !blocked;
}
```

변경 절차: Card에 `lockOverseas()`를 더하고 테스트 픽스처가 잠긴 카드를 만든다(두 설계 공통).\
Ask 쪽은 개발자가 `grep`으로 수정 지점을 찾아 조건을 더한다고 가정했다.

(실험, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, 2026-10-02, `scratchpad/sd/06/e06/run.sh`)

```text
[ask] 개발자가 찾은 수정 지점: grep -rl 'getStatus() == CardStatus.ACTIVE' src
    src/ApprovalService.java
    src/RefundService.java
== [ask] git diff --stat
   src/ApprovalService.java | 3 ++-
   src/Card.java            | 3 +++
   src/Fixtures.java        | 4 +++-
   src/RefundService.java   | 3 ++-
   4 files changed, 10 insertions(+), 3 deletions(-)
  approve      = false
  refund       = false
  earnPoints   = true
== [tell] git diff --stat
   src/Card.java     | 5 ++++-
   src/Fixtures.java | 4 +++-
   2 files changed, 7 insertions(+), 2 deletions(-)
  approve      = false
  refund       = false
  earnPoints   = false
```

- 관찰 1 — Ask는 4파일, Tell은 2파일을 고쳤다. 차이는 판단식 사본 수에서 온다.
- 관찰 2 — Ask에서 grep은 사본 셋 중 둘만 찾았다. 모양이 다른 `PointService`가 빠져, 잠긴 카드에 포인트가 쌓인다(`earnPoints = true`). 컴파일 오류도 예외도 없다.
- 해석 — 이 버그는 diff 안에 없다. 리뷰어가 diff만 보면 승인할 변경이다. N 질문이 diff 밖을 보게 한다.

### 실험 B: 반대 방향 — 우연한 중복을 합친 설계

요구: "카드 수수료만 2.5% → 3%. 정산 수수료(가맹점 약관)는 그대로."\
합친 설계는 두 수수료가 상수 `RATE` 하나를 쓴다. 나눈 설계는 `CARD_RATE`·`SETTLEMENT_RATE`가 따로 있다(지금은 값이 같다).

(실험, 같은 환경, `scratchpad/sd/06/e06/run-fee.sh`)

```text
== [merged] git diff --stat
   src/Fees.java | 2 +-
   1 file changed, 1 insertion(+), 1 deletion(-)
  PASS cardFee(1000)       = 30 (기대 30)
  FAIL settlementFee(1000) = 30 (기대 25)
  실패 1건
== [separate] git diff --stat
   src/Fees.java | 2 +-
   1 file changed, 1 insertion(+), 1 deletion(-)
  PASS cardFee(1000)       = 30 (기대 30)
  PASS settlementFee(1000) = 25 (기대 25)
  실패 0건
```

- 관찰 — 두 설계의 diff 크기는 같다(1파일 1줄). 차이는 **영향 범위**다. 합친 설계에서는 바꾸지 않은 정산 수수료가 따라 바뀌었다.
- 해석 — diff 줄 수만으로는 설계 비용을 잴 수 없다. "함께 바뀌는가"가 기준이다. 이 테스트가 없었다면 정산 금액이 조용히 틀렸을 것이다.
- 실험 A와 B는 같은 원칙(지식 단위로 한 곳)의 양면이다. A는 사본을 남겨서, B는 다른 지식을 합쳐서 깨졌다.

### 실험 C: 복붙 탐지기는 글자만 본다

(실험, PMD 7.28.0 CPD, 같은 환경, `scratchpad/sd/06/e06/run-cpd.sh`)

```text
Found a 3 line (27 tokens) duplication in the following files: 
Starting at line 5 of ask/src/ApprovalService.java
Starting at line 5 of ask/src/RefundService.java

        if (card.getStatus() == CardStatus.ACTIVE
                && card.getExpiry().isAfter(today)
                && !card.isBlocked()) {
```

- CPD(copy-paste detector)는 토큰 열이 같은 구간을 찾는다. 실험 A의 사본 셋 중 글자가 같은 둘만 잡았다. 모양이 다른 `PointService`는 보고되지 않았다.
- 실험 B의 나눈 설계(`CARD_RATE`·`SETTLEMENT_RATE`)처럼 글자가 같아도 다른 지식인 경우는 도구가 구별하지 못한다.
- 그래서 N은 도구가 아니라 검사표 질문으로 남는다. 도구는 후보를 줄 뿐이다.

### 4. 출처별로 나눠 보기

- **두문자어 CLEAN**: David Scott Bernstein, 『Beyond Legacy Code』(Pragmatic Bookshelf, 2015-07) Practice 5 「Create CLEAN Code」. 목차에 "Quality Code is Cohesive / Loosely Coupled / Encapsulated / Assertive / Non-Redundant"가 있다(pragprog 목차 확인).
  - 참고: 원본 「[Claude 추가]」의 "제프 랭어(Jeff Langr)의 저술에서 쓰인 것으로 알려져 … (확인 필요)"는 확인되지 않았다. 확인된 출처는 위 Bernstein 2015다. 커리큘럼의 Shalloway–Trott 『Design Patterns Explained』 출처도 확인하지 못했다 [?]. Shalloway 외 『Essential Skills for the Agile Developer』(2011) 부록이 응집·결합·중복·캡슐화를 "코드 품질"로 다룬다는 서평은 있다(i-programmer 서평). Assertive를 처음 넣은 사람은 확인하지 못했다 [?].
- **구성 개념은 더 오래됐다**: 응집·결합 등급은 구조적 설계(Constantine·Yourdon)의 분류다(원본 「[Claude 추가]」, 책 본문 미열람 [?]). 정보 은닉은 Parnas 1972. 비중복은 Hunt–Thomas의 DRY다.
- **DRY 원문**: "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system." 같은 절에 "Not All Code Duplication is Knowledge Duplication"이 있다. 나이와 수량 검증이 같은 코드여도 "That's a coincidence, not a duplication."이라고 쓴다(『The Pragmatic Programmer』 20주년판 Topic 9 발췌 PDF).
- **Tell, Don't Ask에 대한 이견**: Fowler는 bliki "TellDontAsk"(2013-09-05)에서 이 원칙을 소개하면서도 "personally, I don't use tell-dont-ask"라고 쓴다. 대신 데이터와 행동을 함께 두는 것(co-locate)을 본다. A는 "getter를 없애라"가 아니라 "판단을 데이터 곁에 두라"로 읽는 편이 안전하다.

## 쓰이는 자료구조·알고리즘

- **의존 그래프와 도달 가능 집합**: 클래스를 정점, "사용한다"를 간선으로 둔다. 한 정점을 바꿀 때 영향받는 정점 = 역방향 간선으로 도달 가능한 집합. 결합이 강할수록 이 집합이 크다. 실험 A에서 "카드 사용 조건"을 쓰는 정점은 Ask 3개, Tell 1개(Card)였다. 그래프 기초는 [01-complexity](../01-complexity/2-summary.md).
- **응집도 지표 TCC**: 메서드 쌍 중 같은 필드를 쓰는 쌍의 비율. PMD `GodClass` 규칙은 WMC(복잡도 합)·ATFD(외부 데이터 접근)·TCC 세 지표를 조합한다(PMD 문서, Lanza–Marinescu 『Object-Oriented Metrics in Practice』 인용).
- **토큰 열 매칭**: CPD는 소스를 토큰으로 바꾸고 최소 길이(`--minimum-tokens`, 필수 옵션) 이상 같은 구간을 찾는다(PMD CPD 문서). 이름을 무시하는 `--ignore-identifiers` 같은 옵션이 있다. 글자(토큰) 단위라 지식 단위 중복은 못 본다(실험 C).

## 적용 — 풀어나가는 법

### 1. 리뷰 순서

1. diff의 클래스 하나씩 C·E·A를 묻는다. 접속사 없이 "이 클래스는 ○○을 한다"고 말해 보기, 새 setter·가변 컬렉션 반환 찾기.
2. 바뀐 **규칙**마다 N을 묻는다. 그 규칙을 쓰는 곳을 이름이 아닌 **의미**로 찾는다(필드 사용처·호출처 전수).
3. 바뀐 **시그니처**마다 L을 묻는다. 호출처가 몇 곳인가, 무엇을 넘기는가.
4. 합치는 변경(공통 함수·공통 상수 추출)에는 "이 둘은 함께 바뀌나?"를 묻는다. 대답이 "우연히 지금만 같다"면 합치지 않는다.

### 2. 판단을 데이터 곁으로 (Java)

```java
// 전: 세 서비스가 같은 판단을 따로 한다
if (card.getStatus() == CardStatus.ACTIVE && card.getExpiry().isAfter(today) && !card.isBlocked()) { ... }

// 후: 판단은 Card가, 서비스는 시킨다
if (card.isUsable(today)) { ... }
```

- 옮긴 뒤 getter가 남아야 하는지 본다. 화면 표시용이면 남겨도 된다. 판단 재료로만 쓰였다면 지운다.

### 3. 진단 명령

```bash
# 지식의 사용처 — 필드 getter를 쓰는 곳 (글자가 다른 사본까지 잡으려면 getter 단위로 찾는다)
grep -rn "getStatus()\|getExpiry()\|isBlocked()" src | cut -d: -f1 | sort | uniq -c

# 글자 중복 후보 (지식 중복의 일부만 잡는다 — 실험 C)
pmd cpd --minimum-tokens 50 -d src/main/java --language java

# 결합·응집 지표 (PMD 7.x 기본 임계: CouplingBetweenObjects threshold 20)
pmd check -d src/main/java -R category/java/design.xml/GodClass,category/java/design.xml/CouplingBetweenObjects,category/java/design.xml/DataClass
```

- 도구 출력은 검사표의 **후보 목록**이다. 판정은 "함께 바뀌나"로 한다.

## 장애 시나리오와 대처

### 1. 검사표 없이 리뷰 → 지식 사본 하나를 놓침 (⚠ 커리큘럼)

- 현상: "해외 잠금 카드 결제 차단" 배포 뒤에도 잠긴 카드에 포인트가 적립된다.
- 보이는 형태: 에러 로그 없음. 정산·포인트 대사에서 숫자가 어긋나 며칠 뒤 발견. 실험 A의 `earnPoints = true`.
- 원인: 같은 판단식이 서비스 셋에 있었고, 하나는 모양이 달라 grep에 안 걸렸다(A·N 동시 위반).
- 대처: 판단을 객체 하나로 모은다(Tell). 리뷰 검사표에 "이 규칙은 또 어디 있나?"를 넣고, 필드 사용처를 의미로 전수 확인한다.

### 2. Nonredundant만 좇아 우연한 중복까지 합침 → 잘못된 추상화 (⚠ 커리큘럼)

- 현상: 카드 수수료를 올렸더니 정산 금액도 바뀌었다.
- 보이는 형태: 정산 테스트 실패(실험 B `FAIL settlementFee(1000) = 30 (기대 25)`). 테스트가 없으면 가맹점 정산 민원.
- 원인: 값이 같다는 이유로 다른 지식(카드사 계약, 가맹점 약관)을 한 상수로 합쳤다.
- 대처: 다시 나눈다(인라인 후 재추출). 합치기 전 "함께 바뀌나?"를 묻는다. 추상화 시점 판단은 [11-when-to-abstract](../11-when-to-abstract/2-summary.md).

### 3. 결합을 줄이려다 흐름을 잃음 (L 과잉)

- 현상: 직접 호출을 이벤트로 바꾼 뒤, 장애 때 누가 무엇을 불렀는지 추적하는 데 시간이 걸린다.
- 보이는 형태: 스택 트레이스가 이벤트 버스에서 끊긴다. 구현이 하나뿐인 인터페이스가 여럿.
- 원인: 결합을 줄인 대가(가시성 손실)를 따지지 않았다.
- 대처: "무엇을 잃었나"를 함께 적는다(원본 「L」의 판단 기준). 같은 배포 단위 안의 동기 호출은 직접 호출로 두는 쪽을 먼저 검토한다.

### 4. 캡슐화 구멍 → 불변식이 밖에서 깨짐 (E)

- 현상: 이체 단계 목록이 비어 이체가 아무 일도 안 하고 끝난다.
- 보이는 형태: 예외 없이 "성공" 로그. 원인 지점이 이체 클래스 밖에 있어 찾기 어렵다.
- 원인: `getSteps()`가 내부 가변 리스트를 그대로 돌려줬고, 호출자가 `clear()`했다(원본 「E」 예시).
- 대처: `List.copyOf`·불변 뷰 반환, setter 제거. 불변 객체는 [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md).

### 5. 공유 라이브러리로 합친 값 객체 → 함께 재배포 (N↔L)

- 현상: 한 서비스의 반올림 규칙 변경이 다른 서비스들의 재배포를 부른다.
- 보이는 형태: 공통 라이브러리 버전 올림 PR이 서비스 수만큼 생긴다.
- 원인: 서비스 경계를 넘어 N을 우선했다.
- 대처: 경계 안에서는 N, 경계를 넘으면 L 쪽으로 기운다(원본 긴장 표). 결정과 대가를 ADR로 남긴다([47-architecture-decision-records](../47-architecture-decision-records/2-summary.md)).

## 핵심 문장

- CLEAN은 결과물의 성질을 묻는 다섯 질문이다. C·E·A는 클래스 안을, L·N은 클래스 밖을 봐야 답할 수 있다.
- 실험에서 같은 요구 변경이 Ask 설계는 4파일, Tell 설계는 2파일을 바꿨다. Ask 쪽은 grep이 사본 셋 중 둘만 찾아 조용한 버그가 남았다.
- 비중복의 단위는 글자가 아니라 지식이다. 값이 같다고 합친 수수료 상수는 한쪽 변경에 다른 쪽까지 바꿨다.
- 복붙 탐지기(CPD)는 글자가 같은 사본만 찾는다. 모양이 다른 사본과 글자만 같은 다른 지식은 사람이 "함께 바뀌나?"로 판정한다.
- 속성들은 서로 당긴다. 공통 판정 질문은 "이 둘은 함께 바뀌나?"다.

## 관련 주제·근거

- 원본
  - [engineering/clean-code](../../engineering/clean-code/2-summary.md) — 5속성 정의, 응집·결합 등급, 긴장 표, 현장 상황
- 선행
  - [02-modularity-coupling-cohesion](../02-modularity-coupling-cohesion/2-summary.md) — 정보 은닉·결합·응집
- 후속·연결
  - [07-naming](../07-naming/2-summary.md) · [08-function-design](../08-function-design/2-summary.md) · [09-comments-and-conventions](../09-comments-and-conventions/2-summary.md) — 06에서 나눈 가독성 주제
  - [10-code-smells](../10-code-smells/2-summary.md) — 속성이 깨진 모양의 카탈로그
  - E ↔ [20-oop-fundamentals](../20-oop-fundamentals/2-summary.md)(원고: [foundations/oop-basics](../../foundations/oop-basics/README.md)), N ↔ [11-when-to-abstract](../11-when-to-abstract/2-summary.md)
  - A ↔ [domain-modeling/06-anemic-vs-rich-model](../../domain-modeling/06-anemic-vs-rich-model/2-summary.md), [domain-modeling/domain-vs-application-logic](../../domain-modeling/domain-vs-application-logic/)
  - [engineering/solid-principles](../../engineering/solid-principles/2-summary.md) — 수단(SOLID) 쪽
- 글·문서
  - David Scott Bernstein, 『Beyond Legacy Code』(Pragmatic Bookshelf, 2015) Practice 5 「Create CLEAN Code」 — 목차만 확인 <https://pragprog.com/titles/dblegacy/beyond-legacy-code/>
  - Andrew Hunt·David Thomas, 『The Pragmatic Programmer』 20주년판 Topic 9 「DRY—The Evils of Duplication」 발췌 <https://media.pragprog.com/titles/tpp20/dry.pdf>
  - Martin Fowler, "TellDontAsk"(2013-09-05) <https://martinfowler.com/bliki/TellDontAsk.html> · "AnemicDomainModel"(2003-11-25) <https://martinfowler.com/bliki/AnemicDomainModel.html>
  - PMD 7.28.0 design 규칙(GodClass·DataClass·CouplingBetweenObjects 기본 threshold 20) <https://docs.pmd-code.org/pmd-doc-7.28.0/pmd_rules_java_design.html> · CPD <https://docs.pmd-code.org/pmd-doc-7.28.0/pmd_userdocs_cpd.html>
  - Shalloway·Bain·Pugh·Kolsky 『Essential Skills for the Agile Developer』(2011) 서평 — 부록 "Code Qualities" <https://www.i-programmer.info/bookreviews/4-methodology/4914-essential-skills-for-the-agile-developer.html>
- 실험 목록 (코드: scratchpad `sd/06/e06/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, git 2.43.0, PMD 7.28.0 배포판)
  - A Ask vs Tell 같은 요구 변경 — `run.sh` (diff --stat, grep 수정 지점, 실행 결과)
  - B 우연한 중복 합침 vs 나눔 — `run-fee.sh` (diff --stat, 테스트 PASS/FAIL)
  - C CPD가 잡는 중복 — `run-cpd.sh` (`--minimum-tokens 15`)
