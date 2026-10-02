# software-design/10-code-smells — 정답

## 정답

### 1. 스멜이란

- 대개 더 깊은 문제와 대응하는 **표면 신호**. Kent Beck이 Fowler의 『Refactoring』을 도우며 만든 말이다(Fowler bliki "CodeSmell", 2006-02-09).
- 문제 자체가 아니라 지표다. 빨리 눈에 띄지만, 긴 메서드라도 괜찮은 경우가 있다. 들여다보고 판단한다.

### 2. 2판의 24개

- 2판 3장: 24개(Pearson 목차).
- 1판(22개) 대비 추가: Mysterious Name, Global Data, Mutable Data, Loops.
- 빠짐: Parallel Inheritance Hierarchies, Incomplete Library Class.
- 이름 바뀜: Long Method → Long Function, Switch Statements → Repeated Switches, Lazy Class → Lazy Element, Inappropriate Intimacy → Insider Trading.

### 3. 다섯 묶음

- Bloaters: Long Method, Large Class (그 외 Primitive Obsession, Long Parameter List, Data Clumps).
- OO Abusers: Switch Statements, Refused Bequest (그 외 Temporary Field, Alternative Classes with Different Interfaces).
- Change Preventers: Divergent Change, Shotgun Surgery (그 외 Parallel Inheritance Hierarchies).
- Dispensables: Duplicate Code, Speculative Generality (그 외 Lazy Class, Data Class, Dead Code).
- Couplers: Feature Envy, Message Chains (그 외 Inappropriate Intimacy, Middle Man).
- CLEAN 대응: Bloaters·OO Abusers ↔ C, Change Preventers·Couplers ↔ L, Data Class·Insider Trading ↔ E·A, Duplicated Code ↔ N.

### 4. 두 변경 축 스멜

- Divergent Change: **한 클래스**가 여러 종류의 이유로 바뀐다.
- Shotgun Surgery: **한 종류의 변경**이 여러 클래스를 조금씩 바꾼다.
- 목표: 흔한 변경과 클래스가 **일대일**(1판 "a one-to-one link between common changes and classes").

### 5. 이력으로 본 지표

(실험 A, 2026-10-02)

```text
== [smelly]  R1 format: 통화 표기 ₩ -> 4개 파일
        3 src/OrderService.java
== [tidy]    R1 format: 통화 표기 ₩ -> 1개 파일
```

- R1: smelly 4파일, tidy 1파일.
- smelly `OrderService`: 세 요구(통화·세금·메일) 모두에서 바뀌어 이유 3개. tidy는 파일마다 이유 1개.
- 두 설계의 실행 결과는 같았다. 스멜은 실행이 아니라 변경 이력에서 보인다.

### 6. tidy의 비용

- 파일이 3개 많다(src 8 vs 5). 호출이 한 단계 간접적이다.
- `OrderMail`은 한 줄 메서드 하나뿐이라 그 자체가 Lazy Element 후보다.
- 정당한 조건: 그 관심사(메일 문구 등)가 **독립적으로, 실제로 자주** 바뀐다는 근거(이력)가 있을 때. 근거가 없으면 더 단순한 쪽이 낫다(12 simple-design-and-yagni).

### 7. 도구가 잡은 것

(실험 B, PMD 7.28.0 기본 임계)

```text
DataClass ... (WOC=0.000%, NOPA=5, NOAM=5, WMC=5)
MutableStaticState: Do not use non-final non-private static fields
ExcessiveParameterList: Avoid long parameter lists (11 parameters - threshold is 10).
UnusedPrivateMethod: Avoid unused private methods such as 'legacyFee(int)'.
[INFO] Found 4 violations.
```

- 4개: Data Class, Global/Mutable Data, Long Parameter List, Dead Code. 한 파일 안 구조로 판정되는 것들이다.
- 못 잡은 것:
  - Feature Envy: PMD 7.28.0 Java 규칙 이름 목록에 이 스멜을 직접 찾는 규칙이 없다. 판단에 "어느 클래스 데이터를 더 쓰나"가 필요하다.
  - Repeated Switches: 두 switch의 글자가 달라 CPD도 무반응.
  - Message Chains: `LawOfDemeter`를 켰지만 보고 0건. 타입 정보가 없어서다 — 컴파일 클래스를 `--aux-classpath`로 주고 다시 돌리면 이 체인을 보고해 5건이 된다.
  - Speculative Generality: `UnusedFormalParameter`는 기본으로 private 메서드만 본다(`checkAll=true` 필요).
- Shotgun·Divergent는 이력의 성질이라 한 시점 소스 분석의 대상이 아니다.

### 8. Speculative Generality

- Brian Foote가 붙인 이름. "언젠가 필요할 것"이라며 만든 훅·특수 경우.
- 알아보기: 메서드·클래스의 **유일한 사용처가 테스트**인 경우.
- 처방(1판): Collapse Hierarchy(하는 일 적은 추상 클래스), Inline Class(불필요한 위임), Remove Parameter(안 쓰는 매개변수). 이상한 추상 이름은 Rename Method.

### 9. 도구 0건, 변경 비용 높음

- 의심: 변경 축 스멜(Shotgun Surgery·Divergent Change). 정적 분석이 보지 않는 영역이다.
- 확인 명령:
  - 커밋당 바뀐 파일 수: `git log --no-merges --since=6.months --format='@%h %s' --name-only | awk ...` 상위 커밋.
  - 파일별 변경 커밋 수: `git log --no-merges --since=6.months --format='' --name-only | sort | uniq -c | sort -rn | head`.
- 상위 파일·커밋을 열어 변경 이유가 몇 가지인지, 같은 지식이 몇 곳에 있는지 본다(53 code-forensics-hotspots).

### 10. 주석이라는 스멜

- 1판: 주석 자체는 나쁜 냄새가 아니라 좋은 냄새다. 다만 나쁜 코드를 덮는 **탈취제**로 쓰이는 일이 많아 목록에 넣었다. 먼저 리팩터링(Extract Method·Rename Method·Introduce Assertion)으로 주석이 필요 없게 해 본다.
- 좋은 냄새인 경우: 무엇을 해야 할지 모를 때 그 불확실함을 적는 것, **왜** 그렇게 했는지 적는 것("A comment is a good place to say why you did something").
