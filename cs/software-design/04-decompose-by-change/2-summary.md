# software-design/04-decompose-by-change — 분해 기준: 바뀔 결정을 숨긴다 — 정리 (힌트)

## 해결하는 문제

02는 "결정을 숨겨라", 03은 "깊게 숨겨라"였다.\
남은 질문은 **무엇을 기준으로 모듈을 자르나**다.\
가장 흔한 답은 처리 순서다. "입력 → 처리 → 출력"을 그리고 칸마다 모듈을 만든다. Parnas(1972)는 이 방식이 변경 앞에서 약하다는 것을 KWIC 예로 보였다.

```text
 처리 단계로 자르기                        바뀔 결정으로 자르기
 [입력]→[이동]→[정렬]→[출력]                [줄 저장] [순환 이동] [정렬] [출력]
    └──────┴──────┴──────┘                   각자 결정 하나를 숨긴다
     모두 같은 저장 형식을 안다                 저장 형식은 [줄 저장]만 안다
 "저장 형식 변경" → 전부 수정               "저장 형식 변경" → [줄 저장]만 수정
```

- *분해(decomposition)*: 시스템을 모듈로 나누는 일. Parnas는 모듈을 서브프로그램이 아니라 **책임 할당(responsibility assignment)** 으로 보고, 분해에는 독립된 모듈 작업을 시작하기 전에 정해야 하는 설계 결정이 들어 있다고 썼다. 두 분해의 차이도 "작업 할당(work assignment)으로 나누는 방식과 모듈 사이 인터페이스"에 있다고 쓴다.
- *변동성(volatility)*: 무엇이, 어떤 이유로, 얼마나 자주 바뀔 것인가. Löwy는 이것을 분해 기준으로 삼는다("Decompose based on volatility").

쉬운 예: 이사 짐을 "아침에 쓰는 것·저녁에 쓰는 것"(시간 순)으로 싸면, 칫솔을 바꿀 때 아침 상자와 저녁 상자를 다 연다. "욕실 물건·주방 물건"(바뀌는 이유가 같은 것끼리)으로 싸면 욕실 상자 하나만 연다.\
똑같은 구조다.\
실무 예: "결제 수단 추가" 요구 하나에 컨트롤러·서비스·DTO·매퍼·enum 등 파일 여러 개가 바뀐다. 계층별(처리 단계별)로 잘라서, "결제 수단"이라는 바뀌는 결정이 여러 계층에 퍼져 있기 때문이다.

## 동작·원리

### 1. Parnas의 KWIC — 두 분해

KWIC 색인: 줄마다 "첫 단어를 떼어 끝에 붙이는" 순환 이동을 모두 만들고, 그 전부를 알파벳순으로 출력한다.

```text
 분해 1 (흐름도)                                  분해 2 (정보 은닉)
 ┌────────┐                                      ┌──────────────┐  CHAR(r,w,c) WORDS(r)
 │ Input  │──쓴다──┐                              │ Line Storage │  저장 방식을 숨김
 └────────┘        v                              └──────▲───────┘
 ┌────────┐   ┌───────────────┐                   ┌──────┴───────┐  CSCHAR(l,w,c) CSSETUP
 │C. Shift│──>│ 공유 저장 형식 │<─┐                │ Circ. Shifter│  이동을 저장할지 계산할지 숨김
 └────────┘   │ 4글자/워드 압축│  │                └──────▲───────┘
 ┌────────┐   │ 줄 시작 색인    │  │                ┌──────┴───────┐  ALPH, ITH(i)
 │ Alpha. │──>│ 이동 색인 쌍    │  │                │ Alphabetizer │  언제·어떻게 정렬할지 숨김
 └────────┘   └───────────────┘  │                └──────▲───────┘
 ┌────────┐                      │                ┌──────┴───────┐
 │ Output │──────────────────────┘                │   Output     │
 └────────┘                                      └──────────────┘
 인터페이스 = 표 형식·포인터 규약                   인터페이스 = 함수 이름과 인자 수·타입
```

- Parnas 원문(1972): 분해 1의 기준은 "make each major step in the processing a module" — 흐름도를 그리는 것이다.
- 분해 2의 기준은 정보 은닉이다. 각 모듈은 "its knowledge of a design decision which it hides from all others"로 특징지어진다.
- 두 분해는 **같은 실행 코드가 될 수도 있다**. Parnas는 차이가 실행 표현이 아니라 변경·문서화·이해에 쓰는 표현에 있다고 쓴다.

### 2. 다섯 가지 변경 — 어느 분해가 몇 모듈을 고치나

Parnas가 든 "바뀔 가능성이 있는 결정"과 원문의 판정이다.

| # | 바뀔 결정 | 분해 1 | 분해 2 |
|---|---|---|---|
| 1 | 입력 형식 | 한 모듈 | 한 모듈 |
| 2 | 모든 줄을 메모리에 둔다 | **모든 모듈** | Line Storage만 |
| 3 | 4글자를 한 워드에 압축 | **모든 모듈** | Line Storage만 |
| 4 | 이동을 저장하지 않고 색인만 | 이동·정렬·출력 | Circular Shifter만 |
| 5 | 한 번에 다 정렬 | 어렵다(출력이 정렬 완료를 기대) | Alphabetizer만 |

- 원문: 두 번째 변경은 분해 1에서 "changes in every module"을 부르고, 분해 2에서는 저장 방식 지식이 모듈 1을 뺀 모두에게 숨겨져 있어 그 모듈에만 갇힌다.
- Parnas는 자기 분해 2에도 설계 오류가 있었다고 적는다. Circular Shifter 정의가 **이동의 순서**까지 정해 필요 이상으로 드러냈다. 순서를 빼고 "원래 줄을 알아내는 함수"를 두었으면 더 많은 시스템을 정의 변경 없이 만들 수 있었다.

### 3. 변동성 축 찾기

```text
 질문 1  무엇이 바뀌나?        저장 형식 · 결제 수단 · 세율 · 알림 채널 · 외부 API
 질문 2  왜 바뀌나?            규제 · 영업(새 PG 계약) · 성능 · 공급사 교체
 질문 3  얼마나 자주?          분기마다 / 연 1회 / 거의 안 바뀜
 질문 4  누가 바꾸자고 하나?    같은 사람(팀)이 요구하는 것끼리 한 모듈
            │
            v
 결정 하나 = 모듈 하나가 숨긴다. 자주 바뀌는 결정일수록 인터페이스 뒤로
```

- Löwy 『Righting Software』(2020) 2장 "Decomposition"은 "Avoid Functional Decomposition"과 "Volatility-Based Decomposition"·"Identifying Volatility" 절로 이루어진다(InformIT 목차 확인).
- 같은 장 공개 발췌: 기능 분해에서는 변경이 "affects multiple (if not most) of the components"하고, 변동성 기반 분해에서는 변경이 각 모듈 안에 갇힌다. 저자는 기능 분해의 변경을 "swallowing a live hand grenade"에 비유한다. 이것은 저자의 주장이다.
- 주의: 변동성은 **예측**이다. 틀린 예측으로 만든 경계는 추측성 일반화(Speculative Generality)가 된다. 실제로 함께 바뀐 이력(`git log`)으로 예측을 고친다(53).

### 4. 기능 분해의 함정 — 같은 변동을 나눠 가진다

```text
 OrderService            PaymentService           NotificationService
 ├ if (method==CARD)     ├ if (method==CARD)      ├ if (method==CARD)
 ├ if (method==KAKAO)    ├ if (method==KAKAO)     ├ if (method==KAKAO)
 └ ...                   └ ...                    └ ...
        "결제 수단"이라는 하나의 변동이 세 서비스에 흩어져 있다

 결제 수단별 모듈:  CardPayment · KakaoPayment · (새) NaverPayment
        새 수단 = 새 모듈 하나 + 등록 한 줄
```

- 이름이 기능(`OrderService`)이라고 응집이 강한 것은 아니다. 같은 이유로 바뀌는 코드가 여러 기능에 흩어져 있으면, 기능별 분해는 변동을 나눠 가진다.

### 실험: KWIC 두 분해에 같은 변경 적용

Java로 두 분해를 작게 구현했다. 분해 1은 `Core`의 공유 배열(문자 배열 + 줄 시작·끝 색인 + 이동 색인)을 모든 단계가 직접 읽는다. 분해 2는 Parnas처럼 `LineStorage.word(r, w)`·`CircularShifter.word(i, w)`·`Alphabetizer.ith(i)` 인터페이스만 쓴다.

```java
// 분해 1 — 정렬 단계도 저장 형식(문자 배열·오프셋)을 안다 (발췌)
public class Core {
    public static char[] chars;                      // 단어는 공백 하나로 구분해 이어 붙임
    public static int[] lineStart, lineEnd;
    public static int[][] shifts;                    // {줄 번호, 시작 오프셋}
}
// 분해 2 — 저장 형식은 LineStorage만 안다
public class LineStorage {
    private char[] chars; private int[] start, end;
    public int lines() { ... }  public int words(int r) { ... }  public String word(int r, int w) { ... }
}
```

입력 `"Pipes and Filters"`, `"Information Hiding"`, `"Software Design"`. 두 분해의 출력은 처음부터 끝까지 같다.

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, git 2.43, 2026-10-02)

```text
and Filters Pipes
Design Software
Filters Pipes and
Hiding Information
Information Hiding
Pipes and Filters
Software Design
```

**변경 ① 저장 형식 변경**(Parnas의 2·3번과 같은 종류): 문자 배열 압축을 그만두고 `String[][]`(줄 → 단어)로 저장.

```text
## m1 diff
 src/kwic/Alphabetizer.java  | 17 ++---------------
 src/kwic/CircularShift.java |  5 +----
 src/kwic/Core.java          |  7 +++----
 src/kwic/Input.java         |  5 ++---
 src/kwic/Output.java        |  9 +--------
 5 files changed, 9 insertions(+), 34 deletions(-)
## m2 diff
 src/kwic/LineStorage.java | 20 ++++++--------------
 1 file changed, 6 insertions(+), 14 deletions(-)
```

- 분해 1은 공유 형식을 아는 다섯 파일이 모두 바뀌었다. 분해 2는 `LineStorage` 하나였다. 출력은 둘 다 그대로였다.

**변경 ② 반대 상황**: "출력 줄 끝에 원래 줄 번호를 붙인다."

```text
## m1 diff
 src/kwic/Output.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
## m2 diff
 src/kwic/CircularShifter.java | 1 +
 src/kwic/Output.java          | 2 +-
 2 files changed, 2 insertions(+), 1 deletion(-)
## m1 run
and Filters Pipes  (1)
Design Software  (3)
...
```

- 이번에는 분해 1이 쌌다. 공유 이동 색인 `{줄 번호, 시작}`에 원래 줄이 이미 드러나 있었다.
- 분해 2는 `CircularShifter`가 원래 줄을 숨겼으므로 인터페이스에 `originalLine(i)`를 더해야 했다. Parnas가 "원래 줄을 알아내는 함수"를 두라고 한 바로 그 자리다.
- 해석: 정보 은닉은 **숨긴 결정이 바뀔 때** 싸다. 숨긴 정보를 **새로 꺼내 써야 할 때**는 인터페이스 변경이 필요하다. 그래서 무엇을 숨길지는 변동성 예측에 달렸다.

### 실험: 도달 가능 집합은 상한일 뿐이다

jdeps 간선을 뒤집어, 바뀐 모듈에 직·간접으로 의존하는 클래스를 BFS로 셌다(변경 전 코드).

```text
## m1 edges
kwic.Alphabetizer kwic.Core
kwic.CircularShift kwic.Core
kwic.Input kwic.Core
kwic.Main kwic.Alphabetizer
kwic.Main kwic.CircularShift
kwic.Main kwic.Input
kwic.Main kwic.Output
kwic.Output kwic.Core
## m2 edges
kwic.Alphabetizer kwic.CircularShifter
kwic.CircularShifter kwic.LineStorage
kwic.Input kwic.LineStorage
kwic.Main kwic.Alphabetizer
kwic.Main kwic.CircularShifter
kwic.Main kwic.Input
kwic.Main kwic.LineStorage
kwic.Main kwic.Output
kwic.Output kwic.Alphabetizer
kwic.Output kwic.CircularShifter
kwic.Core 에 의존하는 클래스(직·간접): ['kwic.Alphabetizer', 'kwic.CircularShift', 'kwic.Input', 'kwic.Main', 'kwic.Output'] 개수 5
kwic.LineStorage 에 의존하는 클래스(직·간접): ['kwic.Alphabetizer', 'kwic.CircularShifter', 'kwic.Input', 'kwic.Main', 'kwic.Output'] 개수 5
```

- 도달 가능 집합은 둘 다 5개로 같다. 그런데 실제로 바뀐 파일은 5개와 1개였다.
- 도달 가능 집합은 **"바뀔 수도 있는" 최대 범위**다. 변경은 인터페이스가 그대로인 첫 모듈에서 멈춘다. 분해 1의 `Core`는 인터페이스가 곧 저장 형식이라 멈출 곳이 없었다.
- 그래서 영향 분석은 두 단계다. ① 그래프로 후보를 뽑고, ② 바뀌는 결정이 각 후보의 인터페이스에 드러나는지 본다.

## 쓰이는 자료구조·알고리즘

- **의존 그래프 + 역방향 BFS(도달 가능 집합)** — "X를 바꾸면 누가 영향받을 수 있나"의 상한. 실험의 `reach.py`가 이것이다. [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md).
- **위상 정렬** — 의존 그래프에 순환이 없으면 "아래에서 위로" 바꾸는 순서가 나온다. 순환이 있으면 정렬이 안 되고, 묶음(SCC)이 한 덩어리로 바뀐다. [algorithm/18-scc](../../algorithm/18-scc/2-summary.md), [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md).
- **동시 변경 행렬** — 파일 쌍마다 "같은 커밋에서 함께 바뀐 횟수". 변동성 예측을 이력으로 검증한다(53 code-forensics-hotspots).
- **KWIC의 순환 이동·정렬** — 순환 이동은 (줄, 시작 단어) 쌍으로 저장하면 문자열 복사 없이 표현된다. 정렬은 비교 정렬([algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md) — Java의 객체 배열 정렬은 TimSort 계열).
- **전략·플러그인 등록표** — "결제 수단별 모듈"은 수단 → 구현의 맵으로 고른다. 확장점은 36 extension-points-and-plugins.

## 적용 — 풀어나가는 법

### 1. 분해를 정하는 순서

1. 요구 목록 대신 **변경 목록**을 쓴다. "지난 1년간 들어온 변경 요청"이 가장 좋은 재료다.
2. 변경마다 "어떤 결정이 바뀌었나"를 한 단어로 붙인다(저장 형식, 결제 수단, 세율, 알림 채널).
3. 같은 결정에 속하는 코드를 모은다. 결정 하나 = 모듈 하나.
4. 모듈 인터페이스에 그 결정이 드러나지 않는지 본다(02의 누출 점검).
5. 처리 순서(흐름)는 모듈 **안**이나 조정자(Master Control)에 둔다. 경계로 쓰지 않는다.

### 2. 이력으로 변동성 확인

```bash
# 어떤 파일이 함께 바뀌어 왔나 — 커밋별 파일 목록
git log --format='--%h' --name-only -- src/ | head -50
# 특정 요구(예: "결제 수단")가 건드린 파일 수
git log --grep='결제 수단' --format= --name-only | sort -u | wc -l
```

### 3. 코드 (Java) — 결제 수단을 변동 축으로

```java
// 처리 단계(계층)별로 흩어진 결정 (예시)
switch (req.method()) { case CARD -> ...; case KAKAO -> ...; }       // Controller
switch (order.method()) { case CARD -> ...; case KAKAO -> ...; }     // Service
switch (dto.method()) { case CARD -> ...; case KAKAO -> ...; }       // Mapper

// 변동 축으로 모은 결정
interface PaymentMethod { String code(); Receipt pay(Order o); }
final class CardPayment  implements PaymentMethod { ... }
final class KakaoPayment implements PaymentMethod { ... }
Map<String, PaymentMethod> methods;                                  // 새 수단 = 클래스 하나 + 등록
```

## 장애 시나리오와 대처

### 1. 요구 1건에 파일 12개 (⚠ 커리큘럼)

- 현상: "결제 수단 추가" PR이 컨트롤러·서비스·DTO·매퍼·enum 등 여러 파일을 건드린다.
- 보이는 형태: `git show --stat`의 파일 수가 크고, 같은 묶음이 이전 "수단 추가" 커밋에서도 똑같이 바뀌었다. `switch (method)`가 여러 계층에 있다.
- 원인: 계층(처리 단계)으로 잘라서 결제 수단이라는 변동이 여러 계층에 퍼졌다.
- 대처: 결제 수단 결정을 한 인터페이스 뒤로 모은다. 계층은 그 인터페이스만 부른다.

### 2. 저장 포맷 변경이 모든 단계 모듈을 깨뜨림 (⚠ 커리큘럼)

- 현상: 파일·메시지·테이블 형식 하나 바꾸는 데 수집·변환·적재·보고 모듈이 모두 바뀐다.
- 보이는 형태: 실험의 분해 1처럼 5파일 중 5파일 수정. 배포를 모든 모듈이 함께 해야 한다.
- 원인: 단계별 분해가 중간 형식을 공유 인터페이스로 삼았다.
- 대처: 형식을 소유하는 모듈 하나를 두고 나머지는 그 모듈의 연산(읽기·쓰기)만 쓴다. 실험의 분해 2는 1파일.

### 3. 기능별 서비스가 같은 변동을 나눠 가짐 (⚠ 커리큘럼)

- 현상: `OrderService`·`PaymentService`·`NotificationService`를 각각 고쳐야 새 결제 수단이 동작한다. 하나를 빠뜨리면 알림만 안 간다.
- 보이는 형태: 같은 enum 값 분기가 여러 서비스에 반복. 빠뜨린 쪽에서 `default` 분기 로그나 `IllegalArgumentException`.
- 원인: 기능(명사)으로 잘랐지만 변동(결제 수단)은 기능을 가로지른다.
- 대처: 변동을 기준으로 다시 묶는다. 당장 못 바꾸면 enum 분기를 한 곳(등록표)으로 모으는 것부터.

### 4. 예측이 틀린 경계 — 숨긴 것을 꺼내 써야 함

- 현상: "숨겨 둔" 정보를 새 기능이 필요로 해서 인터페이스를 계속 넓힌다.
- 보이는 형태: 실험 변경 ②처럼 은닉한 쪽이 더 많은 파일을 고친다. getter가 하나씩 늘어난다.
- 원인: 변동성 예측이 틀렸거나, 숨긴 정보가 사실은 바깥의 관심사였다.
- 대처: 이력으로 예측을 고치고 경계를 옮긴다. 경계를 옮기는 리팩터링은 13 refactoring·14 tidy-first.

## 핵심 문장

- 모듈을 처리 단계로 자르지 말고, 바뀔 설계 결정마다 하나씩 숨기도록 자른다(Parnas 1972).
- 단계별 분해는 중간 형식을 공유하므로 형식 변경이 그 형식을 아는 단계 전부를 깨뜨린다. 실험에서 저장 형식 변경은 5파일 대 1파일이었다.
- 정보 은닉은 숨긴 결정이 바뀔 때 싸고, 숨긴 정보를 꺼내 써야 할 때 비싸다. 실험의 "원래 줄 번호" 변경은 1파일 대 2파일로 거꾸로 갈렸다.
- 의존 그래프의 도달 가능 집합은 상한이다. 변경은 인터페이스가 그대로인 첫 모듈에서 멈춘다.
- 변동성은 예측이므로 변경 이력으로 확인하고 고친다.

## 관련 주제·근거

- 선행
  - [02-modularity-coupling-cohesion](../02-modularity-coupling-cohesion/2-summary.md) — 정보 은닉·누출
  - [03-deep-modules-and-abstraction](../03-deep-modules-and-abstraction/2-summary.md) — 깊은 인터페이스
- 후속
  - [05-connascence](../05-connascence/2-summary.md) — 함께 바뀌어야 하는 것을 종류별로
  - [36-extension-points-and-plugins](../36-extension-points-and-plugins/2-summary.md) · [40-codebase-structure](../40-codebase-structure/2-summary.md) · [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md) · [13-refactoring](../13-refactoring/2-summary.md) · [14-tidy-first](../14-tidy-first/2-summary.md)
  - [10 code-smells](../10-code-smells/2-summary.md)(Divergent Change·Shotgun Surgery·Speculative Generality)
- 다른 영역
  - [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) · [algorithm/18-scc](../../algorithm/18-scc/2-summary.md) · [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md)
  - [distributed/20-data-ownership-and-cross-service-queries](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md) — 서비스 경계에서 같은 질문(무엇을 누가 소유하나)
- 글·문서
  - D. L. Parnas, "On the Criteria To Be Used in Decomposing Systems into Modules", CACM 15(12):1053–1058, 1972 — 원문 PDF 열람(두 분해, 다섯 변경, "The Criteria", 원래 줄 식별 함수) <https://www.win.tue.nl/~wstomv/edu/2ip30/references/criteria_for_modularization.pdf>
  - Juval Löwy, 『Righting Software』(Addison-Wesley, 2020) 2장 "Decomposition" — InformIT 목차 <https://www.informit.com/store/righting-software-9780136524038>, 공개 발췌 "Software System Decomposition"(2019-12-17) <https://www.informit.com/articles/article.aspx?p=2995357&seqNum=2>. 책 본문의 나머지는 열람하지 못했다.
  - J. Ousterhout, 『A Philosophy of Software Design』 2판 5장 — 시간 순(temporal) 분해를 피하라: 작업 순서가 아니라 작업에 필요한 지식으로 모듈을 정하라(본문 미열람, 독자 노트 Lebrero 2021로 확인한 요지) <https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/>
- 실험 목록 (코드: scratchpad `sd/01/e04/{m1,m2}/src/kwic/*.java`, 각 저장소 커밋 3개(base → 저장 형식 → 줄 번호), 구동 `run.sh`·`jd.sh`, 도달 집합 `reach.py`·`edges-m1.txt`·`edges-m2.txt`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`)
  - 변경 ① 저장 형식: 분해 1 5파일 9/34줄, 분해 2 1파일 6/14줄, 출력 동일
  - 변경 ② 원래 줄 번호: 분해 1 1파일, 분해 2 2파일(인터페이스 `originalLine` 추가)
  - 도달 가능 집합: 둘 다 5개 — 실제 변경 범위와의 차이
