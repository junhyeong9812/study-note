# software-design/28-taming-conditionals — 정답

## 정답

### 1. 진짜 문제

- 분기가 한 메서드에 얽히는 것(조건 조합이 중첩)과, 같은 분기가 여러 곳에 복제되는 것.
- 스멜 이름: **Repeated Switches**(『Refactoring』 2판 3장, 79쪽).

### 2. 도구 사다리

```text
 5 규칙 엔진     ↑ 바꾸기 쉬움·비개발자 변경 가능
 4 다형성        │
 3 테이블(맵)    │
 2 분해          │
 1 가드 절       ↓ 흐름을 한눈에 따라가기 쉬움
```

- 위로 갈수록 변형 추가가 쉬워지고 분기가 코드에서 사라지지만, 실행 흐름이 데이터·다른 클래스·외부 규칙으로 흩어져 추적이 어려워진다.

### 3. 값 vs 행동

- 값(요율·라벨·한도)이고 이산 조합이면 테이블(Map·EnumMap).
- 행동이고 같은 타입 분기가 여러 곳이면 다형성(enum 상수 메서드·Strategy·State) 또는 빠짐없는 `switch` 식.
- 분기 2~3개가 한 곳에만 있으면 그대로 둔다.

### 4. 복잡도

(실험 A, PMD 7.17.0, 2026-10-02)

```text
IfLadder.java:3:	CognitiveComplexity:	… cognitive complexity of 31 …
IfLadder.java:3:	CyclomaticComplexity:	… cyclomatic complexity of 11.
Table.java:14:	CognitiveComplexity:	… cognitive complexity of 1 …
Table.java:14:	CyclomaticComplexity:	… cyclomatic complexity of 3.
```

- 순환 11 → 3, 인지 31 → 1. `Table`의 3은 1 + `if` 1 + `throw` 1이다(PMD 7.17.0은 `throw`도 +1로 센다 — `CycloVisitor` 소스). 예외로 드러내는 설계가 점수를 1 올린 셈이다. 기본 임계(순환 10, 인지 15)로는 `IfLadder`만 보고됐다. 두 구현은 16 조합에서 같은 값을 냈다.

### 5. PLATINUM

```text
IfLadder PLATINUM → 250 (예외 없음, 마지막 else로 처리)
Table PLATINUM → java.lang.IllegalArgumentException: 규칙 없음: PLATINUM/DOMESTIC/false
```

- `if` 사다리는 마지막 `else`가 조용히 BASIC 요율을 매겼다. 테이블은 표에 없는 키를 예외로 드러냈다.

### 6. GIFT 추가

- v1: 컴파일·실행 성공. `GIFT … label=기타`, 적립은 `default`의 0. 에러 없이 틀린 값이 나간다.
- v2: 컴파일 실패 — `error: the switch expression does not cover all possible input values`(`Points`).

### 7. 식과 문

- JEP 361: `switch` **식**은 빠짐없어야 한다. enum의 모든 상수를 다룬 `switch` 식에는 컴파일러가 암묵 `default`(컴파일 후 enum이 바뀌었을 때용)를 넣는다. `switch` **문**은 빠짐없을 필요가 없다. (Java 21의 JEP 441은 패턴 `switch` 문에는 빠짐없음을 요구한다.)
- `default`를 직접 쓰면 그 `switch`는 늘 빠짐없는 것이 되어, 새 상수를 추가해도 컴파일러가 누락을 알려 주지 않는다.

### 8. 한 번에 한 곳

- 이 실험의 javac(JDK 21.0.12)는 한 번에 한 곳(`Points`)만 보고했다. `Points`를 고치고 다시 컴파일하자 `Label`이 나왔다. 파일을 나눠도 같았고, 비공개 옵션 `-XDshould-stop.ifError=GENERATE`를 주자 둘이 함께 나왔다.
- 실무: 누락이 여러 곳이면 컴파일 → 수정을 여러 번 반복해야 한다. 첫 오류를 고쳤다고 끝났다고 판단하지 않는다. 더 근본적으로는 타입별 지식을 enum 상수 한 곳에 모으면(v3) 누락할 곳 자체가 없어진다.

### 9. 플래그 조합 폭발

- 원인: 플래그마다 `if`가 곳곳에 흩어져 경로가 2⁵ = 32개가 됐고, 테스트가 일부 조합만 덮었다.
- 대처: 허용 조합을 결정 테이블이나 enum 프로필로 명시하고 그 밖은 기동 거부. 다 쓴 플래그 분기는 걷어낸다.

### 10. 과설계 되돌리기

- 잘못: 축이 없는 단순 분기(3개, 한 곳, 결과가 값)에 다형성을 넣어 파일과 호출 단계만 늘었다. 27의 실험 A처럼 축이 다르게 오면 여러 층을 고치게 된다.
- 되돌리기: 구현을 호출부로 인라인해 `switch` 식(빠짐없음, `default` 없음)으로 바꾸고, 인터페이스·팩토리를 지운다(29의 "패턴에서 멀어지기").
