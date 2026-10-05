# software-design/52-complexity-metrics — 복잡도 지표: 순환·인지·NPath·크기·중첩과 지표의 한계 — 정리 (힌트)

## 해결하는 문제

"이 메서드는 복잡하다"를 리뷰어마다 다르게 느낀다. 숫자가 있으면 어디부터 볼지, 테스트를 몇 개는 짜야 할지, 어떤 코드를 게이트에서 막을지 정할 수 있다.\
다만 숫자는 이해하기 어려움 자체가 아니라 그 그림자다. 무엇을 세는지 모르면 잘못 읽는다.

```text
                  같은 순환 복잡도 4
 sumOfPrimes: 중첩 루프 + 레이블 continue         getWords: switch 하나에 case 셋
   OUT: for (...)          ← 읽기 어렵다           switch (n) {            ← 한눈에 읽힌다
     for (...)                                      case 1: return "one";
       if (...) continue OUT;                       ...
 인지 복잡도 7                                      인지 복잡도 1
```

- *순환 복잡도(cyclomatic complexity)*: 제어 흐름 그래프의 독립 경로 수. McCabe(1976)가 정의했다.
- *인지 복잡도(cognitive complexity)*: 사람이 흐름을 따라 읽는 어려움을 규칙으로 센 값. G. Ann Campbell(SonarSource) 백서가 정의했다.
- *NPath*: 메서드를 처음부터 끝까지 지나는 비순환 경로의 수(PMD 정의).

쉬운 예: 지하철 노선도의 갈림길 수(순환 복잡도)와 "환승할 때 몇 번이나 헷갈리나"(인지 복잡도)는 다르다. 갈림길이 같아도 한 역에 몰려 있으면 더 헷갈린다.\
똑같은 구조다.\
실무 예: PMD·Sonar가 메서드마다 이 숫자를 내고, CI 게이트가 임계를 넘으면 빌드를 막는다.

## 동작·원리

### 1. 순환 복잡도 — 제어 흐름 그래프의 독립 경로 수

```java
static long fee(boolean member, boolean coupon) {   // 실험 d의 메서드 (분기 기록 코드는 생략)
  long base = 3_000;
  if (member) base -= 1_000;
  if (coupon) base -= 1_500;
  return base;
}
```

```text
        [N1: base=3000, member?]
           /              \
   [N2: base-=1000]    [N3: (else)]
           \              /
        [N4: coupon?]
           /              \
   [N5: base-=1500]    [N6: (else)]
           \              /
        [N7: return base]

  노드 N = 7, 간선 E = 8, 연결 요소 P = 1
  V(G) = E − N + 2P = 8 − 7 + 2 = 3      (= 결정 2개 + 1)
```

- *제어 흐름 그래프(CFG)*: 노드 = 순차로 실행되는 코드 덩어리, 간선 = 분기. 입구·출구가 하나씩이다.
- McCabe 1976(IEEE TSE SE-2(4)): 그래프 이론의 순환수 v(G) = e − n + p에서 출발한다. 출구에서 입구로 간선을 하나 더해 강하게 연결된 그래프로 보고, 프로그램에는 v = e − n + 2p를 쓴다.
- 같은 논문의 성질: v(G) ≥ 1, v(G)는 선형 독립 경로의 최대 수(기저 집합의 크기), 기능 문장을 넣고 빼도 v는 그대로, 간선 하나를 더하면 1 늘어난다, v는 결정 구조에만 의존한다.
- 계산 지름길: 구조적 프로그램에서는 조건(predicate) 수 + 1. McCabe는 `IF c1 AND c2`를 2로 센다 — 조건을 세는 편이 편하다고 썼다. PMD도 `&&`·`||`·삼항을 결정점으로 센다(규칙 문서 예제).
- McCabe가 쓴 상한은 10이다: "a reasonable, but not magical, upper limit". 같은 논문에서 이 상한이 불합리해 보인 유일한 경우로 큰 case 문(독립된 case가 많은 선택)을 들었다.

### 2. "독립 경로 수 = 최소 테스트 수"의 정확한 뜻

```text
  fee(member, coupon)      v(G) = 3,  경로 수(NPath) = 4
  분기 커버리지 최소   : (T,F) (F,T)          2개로 4분기 모두 지남
  기저 경로(basis)     : (F,F) (T,F) (F,T)    3개 = v(G)
  모든 경로            : TT TF FT FF          4개 = NPath
```

- v(G)는 **기저 경로 테스트**(독립 경로 집합을 하나씩 실행)에 필요한 수다. McCabe: "v is only the minimal number of independent paths that should be tested. There are often additional paths to test."
- 분기 커버리지는 v(G)보다 적은 테스트로도 채울 수 있다. 모든 경로는 v(G)보다 많을 수 있다(경로는 곱으로 늘고, v는 합으로 는다).
- SonarSource 백서는 순환 복잡도가 "메서드를 완전히 덮는 최소 테스트 수를 정확히 계산한다"고 쓰지만, 여기서 "완전히"는 기저 경로 기준으로 읽어야 한다(아래 실험 d가 차이를 보인다 — 해석).

### 3. NPath — 경로를 곱으로 센다

- PMD 문서: NPath는 비순환 실행 경로 수다. 같은 블록 안의 문장은 경로를 곱한다. 그래서 지수적으로 커진다.
- 독립 `if` k개가 나란히 있으면 순환 복잡도는 k+1, NPath는 2^k다(실험 d: `if` 2개 → 3과 4).
- PMD 7.28.0 `NPathComplexity`의 기본 보고 임계는 200이다(규칙 소스 `defaultValue(200)`, 문서 "A threshold of 200 is generally considered the point...").

### 4. 인지 복잡도 — 흐름이 끊기는 곳과 중첩을 센다

```text
 세 규칙 (백서 v1.7, 2023-08-29)
  1. 여러 문장을 하나로 줄이는 축약은 무시한다       (메서드 자체, ?. 같은 null 병합)
  2. 선형 흐름이 끊길 때마다 +1                      (if, else if, else, 삼항, switch 하나, 반복문, catch,
                                                     논리 연산자 열(같은 종류 연속은 한 번), 재귀, 레이블 점프)
  3. 흐름을 끊는 구조가 중첩되면 중첩 깊이만큼 더 +    (if 안의 for: +1+1, 그 안의 while: +1+2)

  예) try { if (c1) {             +1
            for (...) {           +2 (중첩 1)
              while (c2) {...}    +3 (중첩 2)
      } } catch (E1 | E2 e) {     +1
            if (c2) {...}         +2 (중첩 1)
      }                           합계 9
```

- `switch`는 case 수와 관계없이 +1이다. 순환 복잡도는 case마다 +1이다. 그래서 `getWords`는 순환 4·인지 1이다.
- 같은 종류 논리 연산자의 열(`a && b && c`)은 +1 한 번이다. 종류가 바뀔 때마다(`a || b && c`) 다시 +1.
- 조기 `return`·일반 `break`/`continue`는 더하지 않는다(가드 절이 점수에서 손해 보지 않는다). 레이블로 점프하는 `continue OUT`은 +1.
- 메서드에 진입 비용이 없으므로 클래스·애플리케이션 단위로 더한 값도 의미가 있다고 백서는 주장한다. 백서가 든 순환 복잡도의 문제: 메서드마다 최소 1이라 클래스 합계가 높아도 "크지만 단순한 클래스"인지 "작지만 흐름이 복잡한 클래스"인지 알 수 없고, 애플리케이션 수준 합계는 코드 줄 수와 상관한다고 널리 알려져 있다.

### 5. 크기와 중첩 깊이

- *NCSS(Non-Commenting Source Statements)*: 주석·빈 줄을 빼고 문장 수를 센다(PMD `NcssCount`).
- *중첩 깊이*: `if` 안의 `if`가 몇 단인가. PMD `AvoidDeeplyNestedIfStmts`의 기본 `problemDepth`는 3이다(규칙 소스).
- 크기는 다른 지표와 함께 커진다. McCabe 논문은 물리적 크기 제한(예: 50줄)만으로는 부족하다는 예로, `IF THEN` 25개짜리 50줄 프로그램이 최대 3,350만 경로를 가질 수 있다고 들었다.

### 6. 지표의 한계

```text
 지표가 보는 것          지표가 못 보는 것
 분기 수·중첩·경로 수     이름이 의도를 말하나 / 도메인 규칙이 맞나
 메서드 하나의 모양       흐름이 여러 메서드·파일로 흩어진 비용
 지금 코드               얼마나 자주 바뀌나(핫스팟), 누가 아나
```

- *굿하트의 법칙(Goodhart's law)*: 측정값이 목표가 되면 좋은 측정값이 아니게 된다. 게이트를 맞추려고 메서드를 기계적으로 쪼개면 메서드별 숫자는 내려가도 이해 비용은 남는다(실험 c).
- 맥락이 없다: 큰 `switch`(enum별 매핑)는 순환 복잡도가 높아도 읽기 쉽다. McCabe 자신도 이 경우를 예외로 들었다.
- 도구마다 다르다: PMD는 임계 "이상"(≥)에서 보고하고, Sonar Java 규칙은 "초과"(>)에서 보고한다(「적용」 1단계 참고). 같은 숫자라도 결과가 다를 수 있다.

### 실험 a·b·c·d: PMD로 재고, 테스트로 경로를 확인한다

(실험, PMD 7.28.0, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/11/e52/run.sh`, 2026-10-02 — a·b·c·d는 모든 메서드를 보이려고 임계를 1로 낮춘 규칙 세트 `common/metrics.xml` 사용)

a. 백서의 두 예제를 Java로 옮겼다.

```text
Paper.java:3:	CognitiveComplexity:	The method 'sumOfPrimes(int)' has a cognitive complexity of 7,
Paper.java:3:	CyclomaticComplexity:	The method 'sumOfPrimes(int)' has a cyclomatic complexity of 4.
Paper.java:16:	CognitiveComplexity:	The method 'getWords(int)' has a cognitive complexity of 1,
Paper.java:16:	CyclomaticComplexity:	The method 'getWords(int)' has a cyclomatic complexity of 4.
```

- PMD 결과가 백서의 값(순환 4·4, 인지 7·1)과 같다.

b. 같은 배송비 규칙을 중첩 `if`(4단)와 가드 절로 썼다.

```java
long feeGuarded(Order o) {
  if (o == null) return 0;
  if (o.digital()) return 0;
  if (o.amount() >= 30_000) return 0;
  if (o.remote()) return 6_000;
  return 3_000;
}
```

```text
Shipping.java:3:	CognitiveComplexity:	The method 'feeNested(Order)' has a cognitive complexity of 11,
Shipping.java:3:	CyclomaticComplexity:	The method 'feeNested(Order)' has a cyclomatic complexity of 5.
Shipping.java:19:	CognitiveComplexity:	The method 'feeGuarded(Order)' has a cognitive complexity of 4,
Shipping.java:19:	CyclomaticComplexity:	The method 'feeGuarded(Order)' has a cyclomatic complexity of 5.
### b 중첩 깊이 (AvoidDeeplyNestedIfStmts 기본 problemDepth=3)
Shipping.java:7:	AvoidDeeplyNestedIfStmts:	Deeply nested if..then statements are hard to read
```

- 분기 수가 같아 순환 복잡도는 둘 다 5다. 인지 복잡도는 중첩판 11(if +1·+2·+3·+4, else +1), 가드 절판 4다. 중첩 깊이 규칙은 셋째 단 `if`(7행)를 짚었다.

c. 지표 게이트 게이밍: 승인 규칙 메서드(`if` 8개, `&&` 5개)를 판단 흐름은 그대로 두고 세 도우미로 기계적으로 쪼갰다.

```text
Approval.java:3:	CognitiveComplexity:	The method 'decide(long, int, boolean, boolean, String, int)' has a cognitive complexity of 13,
Approval.java:3:	CyclomaticComplexity:	The method 'decide(long, int, boolean, boolean, String, int)' has a cyclomatic complexity of 14.
ApprovalSplit.java:2:	CyclomaticComplexity:	The class 'ApprovalSplit' has a total cyclomatic complexity of 19 (highest 7).
ApprovalSplit.java:3:	CyclomaticComplexity:	The method 'decide(long, int, boolean, boolean, String, int)' has a cyclomatic complexity of 3.
ApprovalSplit.java:10:	CyclomaticComplexity:	The method 'precheck(long, boolean, int)' has a cyclomatic complexity of 4.
ApprovalSplit.java:16:	CyclomaticComplexity:	The method 'byScore(long, int, boolean)' has a cyclomatic complexity of 7.
ApprovalSplit.java:22:	CyclomaticComplexity:	The method 'byChannel(long, int, String)' has a cyclomatic complexity of 5.
ApprovalSplit.java:3:	CognitiveComplexity:	The method 'decide(long, int, boolean, boolean, String, int)' has a cognitive complexity of 2,
ApprovalSplit.java:10:	CognitiveComplexity:	The method 'precheck(long, boolean, int)' has a cognitive complexity of 3,
ApprovalSplit.java:16:	CognitiveComplexity:	The method 'byScore(long, int, boolean)' has a cognitive complexity of 6,
ApprovalSplit.java:22:	CognitiveComplexity:	The method 'byChannel(long, int, String)' has a cognitive complexity of 4,
### c (PMD 7.28.0 기본 임계)
Approval.java:3:	CyclomaticComplexity:	The method 'decide(long, int, boolean, boolean, String, int)' has a cyclomatic complexity of 14.
```

- 쪼갠 쪽 인지 복잡도는 2·3·6·4로 합 15다. 원본은 13이었다. 순환 복잡도는 원본 14, 쪼갠 쪽은 클래스 합계 19(메서드 최대 7)다.
- 기본 임계로 돌리면 원본만 보고되고 쪼갠 쪽은 통과한다. 메서드별 숫자는 모두 10 아래로 내려갔지만 판단 흐름의 총량은 줄지 않았고, `null`을 돌려 "계속"을 뜻하는 새 규약이 생겼다.
- 원본 인지 복잡도 13은 PMD 기본 임계 15 아래라 보고되지 않았다. 같은 메서드가 순환 복잡도로는 걸리고 인지 복잡도로는 안 걸린다.

d. 기저 경로 vs 커버리지: 위 1절의 `fee`에 명세(하한 1,000원)를 빠뜨린 버그를 넣었다. 회원이면서 쿠폰도 쓰면 500원이 나온다.

```text
Fee.java:4:	CognitiveComplexity:	The method 'fee(boolean, boolean)' has a cognitive complexity of 4,
Fee.java:4:	CyclomaticComplexity:	The method 'fee(boolean, boolean)' has a cyclomatic complexity of 3.
Fee.java:4:	NPathComplexity:	The method 'fee(boolean, boolean)' has an NPath complexity of 4,
### d 실행
분기 커버리지 최소(TF,FT)          테스트 2개, 분기 커버 4/4, 버그 발견 아니오
기저 경로 3개(FF,TF,FT)         테스트 3개, 분기 커버 4/4, 버그 발견 아니오
모든 경로(TT,TF,FT,FF)         테스트 4개, 분기 커버 4/4, 버그 발견 예
```

- 인지 4는 분기 기록용 `else` 두 개(+1씩, 백서의 hybrid 증분)를 포함한 값이다. 1절처럼 `else` 없이 줄인 코드라면 인지 2다. 순환 3·NPath 4는 `else` 유무와 관계없이 같다.
- 분기 4개를 모두 지나는 데 테스트 2개면 충분했다(v(G) = 3보다 적다). 기저 경로 3개도, 분기 커버리지 100%도 버그를 못 잡았다. 버그는 두 결정이 모두 참인 경로(TT)에만 있었다.
- 해석: 순환 복잡도는 "최소 이만큼은 짜라"의 하한이다(McCabe). 결정 사이의 상호작용 버그는 경로 조합을 따로 봐야 한다. 커버리지의 한계는 testing 영역 16 coverage-and-its-limits.
- 이 예는 경로가 4개뿐이라 전부 시험할 수 있었다. NPath가 수백·수천이면 전수는 불가능하다. 그때는 경계값·결정 테이블로 고른다(testing 영역 07).

## 쓰이는 자료구조·알고리즘

- **제어 흐름 그래프와 순환수**: V = E − N + 2P. 그래프를 만들지 않고도 AST를 순회하며 결정점(`if`·`case`·반복문·`catch`·`&&`·`||`·`?:`)을 세어 +1 하면 구조적 코드에서는 같은 값이 나온다.
- **기저 경로 집합(선형대수)**: 경로를 간선 사용 횟수 벡터로 보면, 모든 경로는 v(G)개의 독립 경로 벡터의 선형 결합이다(McCabe의 Theorem 1 응용). 기저 경로 테스트는 기준 경로에서 결정을 하나씩 뒤집어 만든다(실험 d의 FF → TF, FT).
- **NPath 재귀 계산**: 순차 문장은 곱, 분기는 합으로 AST를 재귀 평가한다. `if`가 나란히 k개면 2^k로 커진다.
- **중첩 카운터를 든 AST 순회(인지 복잡도)**: 트리를 내려가며 중첩 깊이를 들고 다니다가, 흐름을 끊는 노드에서 1 + 깊이를 더한다. 람다·중첩 메서드는 깊이만 올린다.
- 경로 조합 테스트 설계는 [testing/07-test-design-techniques](../../testing/07-test-design-techniques/2-summary.md).

## 적용 — 풀어나가는 법

1. **도구로 잰다.** PMD 7.x 규칙 세트에 세 규칙을 넣고 CI에서 돌린다.

```xml
<rule ref="category/java/design.xml/CyclomaticComplexity"/>   <!-- 메서드 ≥10, 클래스 ≥80 (기본) -->
<rule ref="category/java/design.xml/CognitiveComplexity"/>    <!-- 메서드 ≥15 (기본) -->
<rule ref="category/java/design.xml/NPathComplexity"/>        <!-- 메서드 ≥200 (기본) -->
<rule ref="category/java/design.xml/AvoidDeeplyNestedIfStmts"/> <!-- if 깊이 3 (기본) -->
```

```bash
pmd check -d src/main/java -R ruleset.xml -f text      # PMD 7 CLI (위반이 있으면 종료 코드 4)
```

- Sonar Java: 인지 복잡도 S3776 기본 15, 순환 복잡도 S1541 기본 10이다. 둘 다 "max 초과(>)"일 때 보고한다(sonar-java master 소스 `DEFAULT_MAX`, `if (total > max)`·`if (size > max)`, 2026-10-02 조회). PMD는 "≥"다. 같은 15라도 PMD는 15에서, Sonar는 16부터 보고한다.

2. **숫자를 신호로만 쓴다.** 높은 메서드 목록을 뽑고, 변경 빈도와 겹쳐 본다(자주 바뀌고 복잡한 곳 = 핫스팟, [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md)). 거의 안 바뀌는 복잡한 코드는 우선순위가 낮다.
3. **인지 복잡도가 높으면 중첩부터 편다.** 가드 절(실험 b: 11 → 4), 조건 분해(Decompose Conditional), 테이블·다형성([28-taming-conditionals](../28-taming-conditionals/2-summary.md)).
4. **순환 복잡도가 높으면 테스트 수를 점검한다.** 적어도 v(G)개의 독립 경로를 시험했는지 보고, 결정끼리 상호작용하는 조합(실험 d의 TT)은 따로 넣는다.
5. **쪼개기 전에 묻는다.** "이 조각에 도메인 이름을 붙일 수 있나?" 이름이 안 나오면 게이트를 맞추려는 쪼개기다(실험 c). 이름이 붙는 조각만 추출한다.
6. **예외는 명시한다.** enum 매핑용 큰 `switch`처럼 읽기 쉬운데 순환 복잡도만 높은 코드는 억제 주석(`@SuppressWarnings("PMD.CyclomaticComplexity")`)과 이유를 남긴다. 임계를 몰래 올리지 않는다.

## 장애 시나리오와 대처

### 1. 순환 복잡도 40인 메서드에서 분기 누락 버그가 반복된다 (⚠ 커리큘럼)

- 현상: 같은 메서드에서 "이 조합일 때 틀린 값" 버그가 분기마다 돌아가며 나온다.
- 보이는 형태: PMD `cyclomatic complexity of 40`. 버그 리포트가 특정 입력 조합에서만 재현된다. 커버리지는 높게 나온다.
- 원인: 결정이 많아 독립 경로만 40개, 조합 경로는 그보다 훨씬 많다. 분기 커버리지는 조합을 보장하지 않는다(실험 d).
- 대처: 기저 경로부터 테스트를 채우고, 조합은 결정 테이블로 고른다. 결정들을 이름 붙은 규칙 객체·테이블로 나눠 각자 테스트한다.

### 2. 지표 게이트를 맞추려 메서드를 잘게 쪼개 흐름이 5파일로 흩어진다 (⚠ 커리큘럼, 굿하트)

- 현상: 게이트는 통과했는데 한 결정을 따라가려면 파일 다섯 개를 열어야 한다.
- 보이는 형태: 메서드별 숫자는 모두 임계 아래, 클래스 합계는 오히려 증가(실험 c: 14 → 합계 19, 인지 13 → 합 15). `return null`로 "계속"을 알리는 등 새 규약이 생긴다.
- 원인: 숫자가 목표가 됐다. 이름 없는 쪼개기는 복잡도를 옮겼을 뿐이다.
- 대처: 게이트는 경고로 두고 리뷰에서 판단한다. 쪼갠 조각에 도메인 이름이 붙는지 확인한다. 클래스·모듈 합계와 변경 빈도를 함께 본다.

### 3. 중첩 5단 `if` — 리뷰에서 `else` 누락이 통과된다 (⚠ 커리큘럼)

- 현상: 깊은 곳의 한 분기에서 `else`가 빠져 기본값이 그대로 나갔다. 리뷰어 둘이 다 놓쳤다.
- 보이는 형태: 인지 복잡도가 순환 복잡도보다 훨씬 크다(실험 b: 11 vs 5). `AvoidDeeplyNestedIfStmts` 경고.
- 원인: 중첩이 깊으면 읽는 사람이 바깥 조건들을 머리에 쌓고 있어야 한다. 어느 `else`가 어느 `if`의 것인지 놓치기 쉽다.
- 대처: 가드 절로 펴서 각 조건을 "여기서 끝"으로 만든다(실험 b의 가드 절판, 인지 4). 깊이 규칙을 CI에 켠다.

### 4. 지표가 읽기 쉬운 코드를 막는다

- 현상: enum 30개를 문자열로 바꾸는 `switch`가 게이트에 걸린다.
- 보이는 형태: 순환 복잡도 31(예시 — case 30개 + 1), 인지 복잡도 1(`switch`는 +1, 실험 a의 `getWords`와 같은 구조).
- 원인: 순환 복잡도는 case마다 +1이다. McCabe도 큰 case 문을 상한 10의 예외로 들었다.
- 대처: 이런 코드는 인지 복잡도로 판단하거나 억제 주석에 이유를 남긴다. 가능하면 `EnumMap`·enum 필드로 옮겨 분기 자체를 없앤다.

## 핵심 문장

- 순환 복잡도는 제어 흐름 그래프의 독립 경로 수 V = E − N + 2P이고, 구조적 코드에서는 결정 수 + 1이다(McCabe 1976).
- v(G)는 기저 경로 테스트의 수이자 "적어도 이만큼"의 하한이다. 실험에서 분기 커버리지는 2개로 찼고, 기저 경로 3개도 결정이 겹치는 경로의 버그를 못 잡았다.
- 인지 복잡도는 흐름이 끊기는 곳마다 +1, 중첩되면 깊이만큼 더 센다. 분기 수가 같아도 중첩 `if`는 11, 가드 절은 4였다.
- NPath는 경로를 곱으로 세어 독립 `if` k개에서 2^k로 커진다. PMD 기본 임계는 200이다.
- 지표는 신호이지 목표가 아니다. 게이트를 맞추려 쪼갠 코드는 메서드 숫자만 내려가고 총량은 늘었다(굿하트).
- 도구마다 임계 비교가 다르다. PMD는 ≥, Sonar Java는 >다.

## 관련 주제·근거

- 선행
  - [06-clean-code](../06-clean-code/2-summary.md) — 좋은 코드의 속성
  - [testing/07-test-design-techniques](../../testing/07-test-design-techniques/2-summary.md) — 경계값·결정 테이블
- 후속·연결
  - [testing/16-coverage-and-its-limits](../../testing/16-coverage-and-its-limits/2-summary.md) — 분기·조건 커버리지의 한계
  - [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md) — 핫스팟 = 변경 빈도 × 복잡도
  - [28-taming-conditionals](../28-taming-conditionals/2-summary.md) — 조건문을 줄이는 도구
  - [11-when-to-abstract](../11-when-to-abstract/2-summary.md) — 플래그 매개변수가 늘리는 경로
- 논문·문서
  - Thomas J. McCabe, "A Complexity Measure", IEEE Transactions on Software Engineering, SE-2(4), 1976-12 — 정의·성질·상한 10·case 문 예외·테스트 방법론 <http://www.literateprogramming.com/mccabe.pdf>
  - G. Ann Campbell, "Cognitive Complexity — a new way of measuring understandability", SonarSource 백서 v1.7, 2023-08-29 <https://www.sonarsource.com/docs/CognitiveComplexity.pdf>
  - PMD 7.28.0 `category/java/design.xml`(CyclomaticComplexity·CognitiveComplexity·NPathComplexity·NcssCount·AvoidDeeplyNestedIfStmts 설명), 규칙 소스의 기본값 <https://github.com/pmd/pmd/tree/pmd_releases/7.28.0/pmd-java/src/main/java/net/sourceforge/pmd/lang/java/rule/design> · 문서 <https://docs.pmd-code.org/latest/pmd_rules_java_design.html>
  - sonar-java `CognitiveComplexityMethodCheck`(S3776, DEFAULT_MAX 15), `MethodComplexityCheck`(S1541, DEFAULT_MAX 10) — master 브랜치 소스(2026-10-02 조회) <https://github.com/SonarSource/sonar-java/tree/master/java-checks/src/main/java/org/sonar/java/checks>
- 실험 목록 (코드: scratchpad `sd/11/e52/a·b·c·d`, `run.sh`, PMD 7.28.0 바이너리 배포판, JDK 21.0.12 temurin `--cpus=2`)
  - a 백서 예제 재현(순환 4·4, 인지 7·1)
  - b 중첩 vs 가드 절(순환 5·5, 인지 11·4, 중첩 깊이 경고)
  - c 게이트 게이밍(원본 순환 14·인지 13 → 쪼갠 쪽 최대 7·합계 19, 인지 합 15, 기본 임계 결과)
  - d 기저 경로 vs 분기 커버리지 vs 모든 경로(테스트 2·3·4개, 버그는 4개에서만 발견)
