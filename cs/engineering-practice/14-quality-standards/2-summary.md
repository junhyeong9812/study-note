# engineering-practice/14-quality-standards — 품질 표준: 품질 어휘(ISO/IEC 25010)를 팀의 실행 가능한 코드 품질 기준으로 — 정리 (힌트)

## 해결하는 문제

품질 기준이 없으면 같은 코드가 리뷰어마다 다른 판정을 받는다.

- A 리뷰어는 빈 `catch` 블록을 그냥 통과시킨다. B 리뷰어는 같은 코드를 막는다.
- 작성자는 "누가 리뷰하느냐"를 보고 코드를 고친다. 기준이 사람에게 붙어 있다.
- 리뷰 코멘트의 대부분이 공백·이름·괄호 위치 같은 취향 논쟁으로 채워지고, 정작 설계·동작 결함은 덜 본다.

쉬운 예: 맞춤법이다.

```text
  사전이 없을 때                         사전이 있을 때
  교정자 A: "되요" 통과                    사전: "돼요"가 맞다
  교정자 B: "되요" → "돼요"                 맞춤법 검사기가 먼저 걸러 준다
  교정자 C: "띄어쓰기는 내 스타일대로"        교정자는 문장의 뜻·논리를 본다
```

- 사전(기준)이 있으면 판정이 사람과 무관해진다.
- 검사기(도구)가 기계적인 것을 먼저 거르면, 교정자(리뷰어)는 사람만 할 수 있는 일에 시간을 쓴다.

똑같은 구조다. 코드 품질에서 사전은 **팀 품질 기준 문서**, 검사기는 **포매터·정적 분석·품질 게이트**, 교정자는 **코드 리뷰**다.

실무 예:
- 신규 입사자 PR에 리뷰어 세 명이 서로 다른 스타일을 요구해 같은 PR이 세 번 고쳐진다.
- 레거시 저장소에 정적 분석을 처음 켰더니 위반 수천 건이 나와 CI가 영원히 빨갛다. 결국 누군가 검사를 끈다(장애 2).

기초 — ISO/IEC 25010:2023의 9개 특성과 하위 특성 정의·예시 — 는 원본 [quality-standards](../../engineering/development-standards/quality-standards/2-summary.md) §2~§5에 있다. 이 노트는 그 어휘를 **팀이 매일 쓰는 기준과 자동 검사**로 내리는 법을 다룬다.

## 동작·원리

### 1. 세 층 — 어휘 → 기준 → 강제

```text
  ① 어휘 (표준)          ISO/IEC 25010:2023 — 9특성 × 하위 특성
        │                "이 지적은 analysability 이야기다"처럼 이름을 붙인다
        ▼
  ② 기준 (팀 문서)        스타일 가이드 · 규칙 목록 · 완료 정의(DoD) · 리뷰 체크리스트
        │                "우리 팀은 빈 catch를 허용하지 않는다"처럼 판정 가능한 문장
        ▼
  ③ 강제 (도구·절차)      포매터 → 정적 분석(린터) → 품질 게이트(CI) → 사람 리뷰
                         기계가 판정할 수 있는 것은 기계가, 나머지는 리뷰가
```

- *품질 모델(quality model)*: 품질을 특성과 하위 특성으로 나눈 분류 체계. 25010은 측정값이 아니라 분류 어휘를 준다(원본 §1).
- *품질 기준(quality standard, 팀 수준)*: 이 노트에서는 "팀이 합의한, 판정 가능한 코드 품질 규칙 묶음"을 뜻한다. ISO 같은 공식 표준과 구별한다.
- *정적 분석(static analysis)*: 프로그램을 실행하지 않고 소스·바이트코드를 읽어 규칙 위반을 찾는 것. PMD·Checkstyle·SpotBugs·Error Prone 등이 있다.
- *품질 게이트(quality gate)*: 정해진 조건을 못 넘으면 병합·배포를 막는 자동 관문.

층을 하나 빠뜨리면 어떻게 되나.

| 빠진 층 | 증상 |
|---|---|
| ① 어휘 없음 | "품질이 나쁘다"가 무엇을 뜻하는지 사람마다 달라 논쟁이 사실 대화가 되지 않는다 |
| ② 기준 없음 | 리뷰 판정이 리뷰어에게 달린다(이 노트의 ⚠ 장애) |
| ③ 강제 없음 | 기준 문서는 있지만 위키에만 있다. PR마다 같은 지적을 사람이 반복한다 |

### 2. 무엇을 기계에, 무엇을 사람에

```text
           판정이 결정적인가? (같은 입력 → 누구나 같은 결론)
                 │
        ┌────────┴────────┐
       예                 아니오
        │                   │
  기계로 옮긴다            사람(리뷰)에 남긴다
  · 포맷·들여쓰기          · 설계가 요구에 맞나
  · 빈 catch, == 문자열비교 · 이름이 뜻을 전하나
  · 미사용 변수·메서드      · 이 추상화가 지금 필요한가
  · 복잡도 상한            · 테스트가 의미 있는 것을 단언하나
```

Google eng-practices(공개 코드 리뷰 지침, 회사 관례)가 이 경계를 이렇게 적는다.

- 리뷰의 상위 원칙: CL이 완벽하지 않더라도 **시스템 전체의 코드 건강(code health)을 확실히 개선하는 상태**면 승인 쪽으로 기운다("The Standard of Code Review").
  - *CL(changelist)*: Google 용어로 리뷰 단위 변경. 다른 곳의 PR·MR에 해당한다.
- "기술적 사실과 데이터가 의견과 개인 취향을 이긴다."
- 스타일은 **스타일 가이드가 최종 권한**(원문 "the absolute authority")이다("The Standard of Code Review" Principles 절, "What to look for" Consistency 절에도 같은 말). 가이드에 없는 스타일 제안은 `Nit:`을 붙여 "필수 아님"을 표시하고, 개인 취향만으로 CL을 막지 않는다("What to look for in a code review" Style 절).
- 같은 문서가 리뷰에서 볼 것으로 Design·Functionality·Complexity·Tests·Naming·Comments·Style·Consistency·Documentation·Every Line·Context·Good Things를 든다.
  - 흔한 오해: "정적 분석을 켜면 리뷰가 필요 없다". 위 목록의 Design·Functionality·Tests는 대부분 기계가 판정할 수 없다. 도구는 리뷰 시간을 **그쪽으로 옮겨 줄** 뿐이다.

25010 어휘와 이어 보면 이렇다(해석 — 표준이 이 대응을 정하지는 않는다).

| 25010 하위 특성 | 기계가 잡는 신호(예) | 사람이 보는 것 |
|---|---|---|
| analysability | 순환·인지 복잡도 상한, 메서드 길이 | 이름·구조가 의도를 전하나 |
| modifiability | 중복 코드 비율, 의존 규칙 위반 | 같은 개념이 여러 곳에 흩어졌나 |
| testability | (테스트) 커버리지·변이 점수 | 테스트가 계약을 실제로 단언하나 |
| faultlessness | 빈 catch, `==` 문자열 비교, null 역참조 의심 | 오류 경로가 요구대로 동작하나 |

### 3. 게이트를 어디에, 무엇을 기준으로 — "새 코드" 원칙

레거시 코드에 규칙을 처음 켜면 기존 위반이 쏟아진다. 전체 위반 수를 게이트 조건으로 삼으면 게이트는 빨간 채로 남는다.

```text
  전체 기준 게이트                       새 코드 기준 게이트 (ratchet)
  기존 위반 3,000 ──> 실패                기존 위반 3,000 = 기준선(baseline)으로 동결
  새 PR(위반 0)    ──> 여전히 실패          새 PR이 위반 0건 추가 ──> 통과
  → 아무도 못 고침 → 게이트 끔              새 PR이 위반 1건 추가 ──> 실패
                                         기존 위반을 고치고 그 지문을 기준선 파일에서 지워
                                         커밋하면 기준선이 줄어든다(되돌아가지 않음)
```

- *기준선(baseline)*: 규칙을 켠 시점의 기존 위반 목록. 이 목록에 있는 것은 "이미 알던 빚"으로 통과시킨다.
- *래칫(ratchet)*: 한 방향으로만 도는 톱니. 품질 지표가 나빠지는 쪽으로는 못 가고, 좋아지는 쪽으로만 기준을 옮긴다.
  - 주의: 기준선이 커밋된 지문 목록이면, 고친 지문을 목록에서 지우고 커밋해야 줄어든다. 지우지 않으면 같은 위반이 다시 생겨도 "기존 위반"으로 통과한다.

SonarQube의 기본 게이트 "Sonar way"가 이 방식이다(SonarSource 문서 "Understanding quality gates" — 제품 기본값이지 표준이 아니다).
- 새 코드에 새 이슈 0건
- 새 Security Hotspot 100% 검토
- 새 코드 커버리지 ≥ 80.0%
- 새 코드 중복 ≤ 3.0%
- 새 줄이 20줄 미만이면 중복 조건을, 커버 대상 새 줄이 20줄 미만이면 커버리지 조건을 적용하지 않는다(문서의 "fudge factor", 기본 켜짐).
- 같은 문서(2026-10-05 조회)는 Security Hotspot을 단계적으로 없애는 중이라고 적는다(hotspot을 내던 규칙이 취약점·보안 이슈를 내도록 바뀜). 둘째 조건은 제품 버전에 따라 달라질 수 있다.

여기서 문제는 **"새 위반"을 어떻게 알아보나**다. 다음 실험이 이 키 설계를 보인다.

### 4. 실험: 기준선을 줄 번호로 기억하면, 무관한 변경이 위반 폭탄이 된다

v1(레거시)에서 PMD로 기준선을 만들고, v2에서 파일 위에 주석·import 3줄을 끼우고 새 메서드(위반 2건)를 더했다. "새 위반"을 두 가지 키로 찾는다.

팀 규칙(PMD ruleset, 리뷰에서 반복 지적되던 것만 골랐다는 가정의 예시):

```xml
<ruleset name="team" xmlns="http://pmd.sourceforge.net/ruleset/2.0.0">
  <rule ref="category/java/errorprone.xml/EmptyCatchBlock"/>
  <rule ref="category/java/errorprone.xml/UseEqualsToCompareStrings"/>
  <rule ref="category/java/bestpractices.xml/UnusedLocalVariable"/>
  <rule ref="category/java/bestpractices.xml/UnusedPrivateMethod"/>
</ruleset>
```

v1 `Legacy.java`(요지):

```java
public class Legacy {
    public int parse(String s) {
        int unused = 0;
        try { return Integer.parseInt(s); }
        catch (NumberFormatException e) { }          // EmptyCatchBlock
        return -1;
    }
    public boolean isAdmin(String role) { return role == "ADMIN"; }  // UseEqualsToCompareStrings
    private void helper() { }                        // UnusedPrivateMethod
}
```

v2는 맨 위에 `// 2026-10 결제 환불 기능 추가`·`import java.util.Objects;`·빈 줄을 넣고, 아래 메서드를 더했다.

```java
    public long refund(String amount) {
        int tmp = 0;                                  // UnusedLocalVariable (새 위반)
        try { return Long.parseLong(Objects.requireNonNull(amount)); }
        catch (NumberFormatException e) { }          // EmptyCatchBlock (새 위반)
        return 0L;
    }
```

비교기(핵심 부분) — 키를 바꿔 끼우는 것만 다르다.

```java
// 방식 A: 줄 번호 키 — 위에 줄 하나만 끼워도 옛 위반이 전부 "새 위반"이 된다
static String byLine(V v, List<String> src) { return v.rule() + "@" + v.line(); }
// 방식 B: 지문 키 — 규칙 + 클래스·메서드 + 그 줄의 정규화된 코드 (줄 번호 무시)
static String byPrint(V v, List<String> src) {
    return v.rule() + "|" + v.cls() + "." + v.method() + "|" + src.get(v.line() - 1).strip();
}
// 기준선 키 집합(HashSet)에 없는 것만 "새 위반"
```

(실험, PMD 7.7.0 via maven-pmd-plugin 3.26.0 · Maven 3.9.16 · JDK 21.0.12 temurin, 2026-10-05)

```text
$ mvn pmd:check                     # v1
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-pmd-plugin:3.26.0:check (default-cli) on project shop: PMD 7.7.0 has found 3 violations. ...

$ grep -o 'beginline=…rule=…' target/pmd.xml   # 위반 줄·규칙만 추림
== v1
beginline="8" rule="EmptyCatchBlock"
beginline="14" rule="UseEqualsToCompareStrings"
beginline="17" rule="UnusedPrivateMethod"
== v2
beginline="11" rule="EmptyCatchBlock"
beginline="17" rule="UseEqualsToCompareStrings"
beginline="20" rule="UnusedPrivateMethod"
beginline="23" rule="UnusedLocalVariable"
beginline="26" rule="EmptyCatchBlock"

$ java NewViolations.java
v1 위반 3건, v2 위반 5건
A 줄번호 키 -> 새 위반 5건 [EmptyCatchBlock:11, UseEqualsToCompareStrings:17, UnusedPrivateMethod:20, UnusedLocalVariable:23, EmptyCatchBlock:26]
B 지문 키   -> 새 위반 2건 [UnusedLocalVariable:23, EmptyCatchBlock:26]
```

관찰과 해석.
- 실제로 새로 들어온 위반은 2건이다. 줄 번호 키는 3줄 밀린 옛 위반 3건까지 "새 위반"으로 보고 5건이라 했다(오탐 3건). 이 PR 작성자는 자기와 무관한 레거시 위반을 고치라는 요구를 받는다(장애 3).
- 지문 키는 줄 이동에 강하다. 같은 `catch` 줄 텍스트라도 메서드(`refund`)가 다르면 다른 지문이라 새 위반으로 잡았다.
- 지문 키의 한계(이 실험 밖의 추론): 이 실험은 파일 하나라 키에 파일 경로를 넣지 않았다. 저장소 전체 기준선에서는 다른 패키지의 같은 이름 클래스·메서드가 같은 키를 받을 수 있으므로 파일 경로(또는 패키지)를 키에 넣는다(PMD XML 보고서는 위반마다 파일명과 package·class·method를 따로 적는다). 같은 메서드 안에 같은 텍스트의 위반이 둘이면 하나로 합쳐진다. 줄 내용을 고치기만 해도(예: 들여쓰기 아닌 글자 변경) 옛 위반이 새 위반으로 보인다. 실제 도구들은 주변 줄·AST 위치 등을 섞어 지문을 만든다 — 도구마다 방식이 다르다 `[?]`.
- 덤으로 관찰한 것: v1의 `int unused = 0;`은 걸리지 않고 v2의 `int tmp = 0;`은 걸렸다. PMD 7.7.0 문서의 UnusedLocalVariable 설명에 "이름이 `ignored`나 `unused`로 시작하는 변수는 거른다"고 적혀 있다. 규칙에는 의도된 예외가 있고, 그 예외는 **우회로**로도 쓰일 수 있다(장애 4).

### 5. 기준 문서에 들어갈 것 — 완료 정의(DoD)

자동 검사로 옮길 수 없는 기준은 문서로 남고, 그 문서가 실제로 쓰이는 자리는 "완료"의 정의다.

- Scrum Guide 2020: "완료 정의(Definition of Done)는 Increment가 제품에 요구되는 품질 기준을 충족한 상태에 대한 공식적인 기술"이다. DoD를 충족하지 못한 항목은 릴리스할 수 없고 Sprint Review에 내놓을 수도 없다. 조직 표준에 DoD가 있으면 각 스크럼 팀은 최소한 그것을 따른다.
- 품질 기준을 DoD 항목으로 걸면 "리뷰에서 지적받으면 고친다"가 아니라 "완료 조건"이 된다.

```text
  DoD 예시(팀 예시, 표준 아님)
  [자동] 포매터 적용 · 팀 PMD 규칙 새 위반 0 · 새 코드 분기 커버리지 ≥ 팀 기준
  [자동] 아키텍처 규칙(계층·순환) 위반 0
  [사람] 리뷰어 1인 승인 — 체크리스트: 요구 대응·오류 경로·이름·테스트 단언
  [사람] 공개 API 변경이면 문서·변경 기록 갱신
```

## 쓰이는 자료구조·알고리즘

- **추상 구문 트리(AST)와 방문자(visitor)**: PMD는 소스를 AST로 파싱하고 규칙마다 트리를 순회하며 패턴을 찾는다. PMD 규칙은 Java 클래스(방문자)나 XPath 식으로 쓴다(PMD 문서 "Writing a custom rule" — 규칙 작성 방식은 [software-design/41](../../software-design/41-architecture-fitness-rules/2-summary.md)의 바이트코드 기반 ArchUnit과 대비된다).
- **해시 집합으로 기준선 비교**: 기준선 위반의 지문을 `HashSet`에 넣고, 새 결과의 지문이 집합에 없으면 새 위반이다. 비교는 위반 수 n에 대해 평균 O(n). 핵심 설계는 **키(지문)를 무엇으로 만드나**다(실험 4).
- **래칫 = 단조 감소 카운터**: 규칙별 허용 위반 수를 기록해 두고, 측정값이 그보다 크면 실패, 작으면 기록을 낮춘다.
- **복잡도 지표**: 순환 복잡도(제어 흐름 그래프의 독립 경로 수)·인지 복잡도 — 정의와 한계는 [software-design/52-complexity-metrics](../../software-design/52-complexity-metrics/2-summary.md).
- **커버리지·변이 점수**: 테스트 품질 신호와 그 한계는 [testing/16-coverage-and-its-limits](../../testing/16-coverage-and-its-limits/2-summary.md), [testing/15-mutation-testing](../../testing/15-mutation-testing/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **반복 지적을 모은다.** 최근 리뷰 코멘트를 훑어 같은 지적이 몇 번 나왔는지 센다. 기준 후보는 "자주 나오고, 판정이 결정적인 것"부터다.
2. **결정적인 것은 도구로 옮긴다.** 포맷은 포매터로(논쟁 자체를 없앤다), 결함 패턴은 린터 규칙으로. 규칙은 적게 시작한다 — 켠 규칙마다 이유(어느 25010 특성, 어떤 사고)를 적는다.
3. **기존 위반은 기준선으로 동결**하고 새 코드만 막는다(실험 4의 지문 키). 기준선 파일은 저장소에 커밋한다.
4. **사람 몫은 체크리스트와 DoD로.** 체크리스트 항목은 25010 어휘로 쓴다(예: "오류 경로가 요구대로 동작하나 — faultlessness").
5. **예외 절차를 만든다.** 억제(suppress)는 이유와 함께만 허용하고, 억제 수를 지표로 본다.
6. **주기적으로 규칙을 고친다.** 오탐이 잦은 규칙은 끈다. 사고 회고에서 나온 패턴은 규칙으로 추가한다.

### 2. 빌드에 게이트 걸기 (Maven, maven-pmd-plugin 3.26.0)

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-pmd-plugin</artifactId>
  <version>3.26.0</version>
  <configuration>
    <rulesets><ruleset>config/team-rules.xml</ruleset></rulesets>
    <printFailingErrors>true</printFailingErrors>
  </configuration>
  <executions>
    <execution><goals><goal>check</goal></goals></execution>  <!-- 기본 verify 단계에서 위반이 하나라도 있으면 빌드 실패(기준선 비교 없음) -->
  </executions>
</plugin>
```

- 이 설정만으로는 **기존 위반도 막는다**. 3.26.0 플러그인 설명이 check 골을 "Fails the build if there were any PMD violations"로 적는다(플러그인 jar의 plugin.xml 확인). 새 위반만 막으려면 `failOnViolation=false`로 보고서(`target/pmd.xml`)만 만들고 실험 4 같은 지문 비교기를 CI 단계로 붙인다. 플러그인 자체 기능인 `excludeFromFailureFile`은 클래스·규칙 단위로 제외한다(지문보다 거칠다).
- maven-pmd-plugin 3.26.0은 PMD 7.7.0을 썼다(실험 출력 "PMD 7.7.0 has found 3 violations").
- 플러그인 버전과 PMD 버전은 따로 움직인다. 규칙 이름·기본 동작은 PMD 버전별 문서로 확인한다.

### 3. 억제는 이유와 함께 (Java)

```java
// 이유: 외부 SDK가 던지는 예외를 의도적으로 무시 — 실패해도 재시도 큐가 처리한다(티켓 OPS-123)
@SuppressWarnings("PMD.EmptyCatchBlock")
void warmUpCache() {
    try { sdk.preload(); } catch (SdkTimeoutException e) { }
}
```

- 억제 주석에 이유가 없으면 리뷰에서 막는다(기준 문서에 적어 둔다).

### 4. 진단 — 기준이 작동하는지 보는 신호

- 리뷰 코멘트 중 스타일·포맷 비율이 줄었나(포매터 도입 전후).
- 같은 종류의 지적이 PR마다 반복되나 → 규칙 후보.
- 억제 수가 늘기만 하나 → 규칙이 현실과 맞지 않거나 우회가 퍼지는 중.
- 기준선 크기가 줄고 있나(래칫이 도는가).

## 장애 시나리오와 대처

### 1. 기준 부재 → 리뷰 편차 (⚠ 커리큘럼)

- 현상: 같은 패턴이 어떤 PR에선 통과하고 어떤 PR에선 막힌다. 작성자가 "리뷰어 운"을 말한다.
- 보이는 형태: 리뷰 코멘트에 "제 취향은…", "보통은…"이 많다. 같은 PR에 리뷰어끼리 상충하는 요구가 달린다. 리뷰 왕복 횟수가 리뷰어에 따라 크게 다르다.
- 원인: 판정 기준이 문서·도구가 아니라 사람에게 있다.
- 대처: 반복 지적을 모아 결정적인 것은 포매터·린터로 옮긴다. 나머지는 체크리스트로 명문화한다. 스타일 가이드에 없는 것은 `Nit:`(필수 아님)로 표시하는 관례를 둔다(Google eng-practices).

### 2. 레거시 전체에 게이트를 켰다 → 영원히 빨간 CI → 게이트를 끈다

- 현상: 정적 분석 도입 첫날 위반 수천 건으로 PR이 하나도 통과하지 못한다.
- 보이는 형태: `PMD ... has found N violations`로 빌드 실패. 며칠 뒤 누군가 `-Dpmd.skip=true`를 CI 설정에 넣는다.
- 원인: 기존 위반과 새 위반을 구분하지 않았다.
- 대처: 기존 위반은 기준선으로 동결하고 새 코드만 막는다(래칫). SonarQube "Sonar way"도 새 코드 조건만 건다. 기존 위반은 그 파일을 고칠 때 함께 줄인다.

### 3. 기준선을 줄 번호로 기억 → 무관한 변경이 위반 폭탄

- 현상: 파일 맨 위에 import 한 줄을 넣었을 뿐인데 그 파일의 옛 위반이 전부 "새 위반"으로 보고된다.
- 보이는 형태: 실험 4처럼 실제 새 위반 2건에 대해 5건이 보고된다. 작성자는 레거시를 고치거나 기준선을 통째로 다시 만든다.
- 원인: 기준선 키에 줄 번호가 들어갔다. 줄 번호는 위쪽 편집 한 번에 전부 바뀐다.
- 대처: 규칙·파일 경로·클래스·메서드·정규화된 코드로 지문을 만든다. 도구의 기준선 기능을 쓸 때는 그 지문 방식을 문서에서 확인한다. 기준선을 다시 만드는 것은 리뷰 대상 변경으로 다룬다(조용히 갱신하면 새 위반이 묻힌다).

### 4. 지표를 맞추려는 우회 (굿하트)

- 현상: 위반 수는 줄었는데 코드는 그대로다.
- 보이는 형태: 미사용 변수 이름이 `unused…`로 바뀐다(PMD UnusedLocalVariable이 거르는 이름 — 실험 4). 억제 주석이 이유 없이 늘어난다. 커버리지는 오르는데 단언 없는 테스트가 늘어난다.
- 원인: 수치 자체가 목표가 됐다. 규칙의 의도된 예외가 우회로가 됐다.
- 대처: 억제·예외 사용 수를 따로 보고 리뷰한다. 커버리지 대신 변이 점수 같은 보조 신호를 함께 본다([testing/16](../../testing/16-coverage-and-its-limits/2-summary.md)). 규칙의 목적(어느 특성을 지키나)을 기준 문서에 적어, 형식 준수와 목적 달성을 구분한다.

### 5. 스타일 논쟁이 리뷰를 점령한다

- 현상: 리뷰 시간이 길어지는데 결함 발견은 늘지 않는다.
- 보이는 형태: 코멘트 다수가 줄바꿈·괄호·import 순서 지적이다. 같은 PR에 포맷 변경과 기능 변경이 섞여 diff가 커진다.
- 원인: 포맷이 자동화되지 않았다. 포맷 변경과 기능 변경을 한 PR에 섞었다.
- 대처: 포매터를 커밋 전·CI에 붙여 포맷 논쟁을 없앤다. Google eng-practices도 큰 스타일 변경은 다른 변경과 섞지 말라고 한다(diff 파악·병합·롤백이 어려워진다).

## 핵심 문장

- 25010은 품질의 **어휘**를, 팀 품질 기준은 **판정 가능한 문장**을, 도구는 그 문장의 **강제**를 맡는다 — 세 층 중 하나가 빠지면 리뷰 편차가 생긴다.
- 판정이 결정적인 것은 기계로 옮기고, 사람의 리뷰는 설계·동작·테스트처럼 기계가 판정할 수 없는 것에 쓴다.
- 레거시에 기준을 도입할 때는 기존 위반을 기준선으로 동결하고 **새 코드만** 막는다(래칫).
- 기준선의 "새 위반" 판정은 키 설계에 달렸다 — 줄 번호 키는 위쪽 편집 한 번에 옛 위반을 새 위반으로 바꾼다(실험: 실제 2건 vs 보고 5건).
- 규칙의 예외와 억제는 우회로가 될 수 있으므로 그 수를 따로 본다.

## 관련 주제·근거

- 원본(기초): [engineering/development-standards/quality-standards](../../engineering/development-standards/quality-standards/2-summary.md) — ISO/IEC 25010:2023 9특성·하위 특성·2011→2023 변경. 묶음 개요는 [development-standards/README](../../engineering/development-standards/README.md)
- 선행: [05-code-review](../05-code-review/2-summary.md) — 리뷰의 목적·기준·크기
- 연결(같은 영역): [10-technical-debt](../10-technical-debt/2-summary.md) — 기준선으로 동결한 기존 위반은 가시화된 부채다 · [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md) — 게이트가 놓이는 파이프라인
- 후속·연결
  - [15-security-standards](../15-security-standards/2-summary.md) — 같은 "기준 → 자동 검사" 구조를 보안에 적용
  - [16-operational-standards](../16-operational-standards/2-summary.md) · [17-legal-standards](../17-legal-standards/2-summary.md)
  - [software-design/46-quality-attributes-and-tradeoffs](../../software-design/46-quality-attributes-and-tradeoffs/2-summary.md) — 25010 특성 사이의 맞교환, 품질 속성 시나리오
  - [software-design/52-complexity-metrics](../../software-design/52-complexity-metrics/2-summary.md) — PMD 복잡도 규칙과 지표의 한계
  - [software-design/41-architecture-fitness-rules](../../software-design/41-architecture-fitness-rules/2-summary.md) — 아키텍처 규칙을 테스트로, 기존 위반 동결(baseline)
  - [software-design/10-code-smells](../../software-design/10-code-smells/2-summary.md) · [software-design/06-clean-code](../../software-design/06-clean-code/2-summary.md)
  - [testing/16-coverage-and-its-limits](../../testing/16-coverage-and-its-limits/2-summary.md) · [testing/15-mutation-testing](../../testing/15-mutation-testing/2-summary.md)
- 근거
  - ISO/IEC 25010:2023 <https://www.iso.org/standard/78176.html> (원문 유료 — 특성 목록은 원본 노트와 ISO OBP 열람 범위)
  - Google eng-practices, "The Standard of Code Review" <https://google.github.io/eng-practices/review/reviewer/standard.html> · "What to look for in a code review" <https://google.github.io/eng-practices/review/reviewer/looking-for.html>
  - Scrum Guide 2020, Commitment: Definition of Done <https://scrumguides.org/scrum-guide.html>
  - SonarSource, "Understanding quality gates" — Sonar way 4조건·fudge factor 20줄 <https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates>
  - PMD 7.7.0 규칙 문서 — Best Practices(UnusedLocalVariable의 `ignored`/`unused` 예외, UnusedPrivateMethod), Error Prone(EmptyCatchBlock, UseEqualsToCompareStrings) <https://docs.pmd-code.org/pmd-doc-7.7.0/pmd_rules_java_bestpractices.html>
  - Apache Maven PMD Plugin 3.26.0 <https://maven.apache.org/plugins/maven-pmd-plugin/>
- 실험 목록
  - 기준선 키 비교: maven-pmd-plugin 3.26.0(PMD 7.7.0) · Maven 3.9.16 · eclipse-temurin 21.0.12 컨테이너. v1 위반 3건 → v2 위반 5건, 줄 번호 키 "새 위반" 5건 vs 지문 키 2건. 같은 실행에서 `unused` 이름 변수 미검출·`tmp` 검출 관찰.
