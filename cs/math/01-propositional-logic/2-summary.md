# math/01-propositional-logic — 명제·술어 논리: 드모르간, 조건문의 부정, 단락 평가 — 정리 (힌트)

## 해결하는 문제

권한 검사·검증 조건은 불리언 식이다. 식을 바꿀 때 뜻이 같은지 확인하는 도구가 없으면, 리팩터링 한 번에 경계 조건이 빠진다.

```text
  원래 규칙:  "회원이면서 인증까지 끝난 사람만 들어온다"
              거부 조건 = !(member && verified)

  리팩터링:   "괄호 풀자"  →  !member && !verified        ← 틀림
              이 식은 "회원도 아니고 인증도 안 된 사람"만 거부한다
              → 회원인데 미인증, 비회원인데 인증 완료 → 둘 다 통과
```

쉬운 예: "비 오고 바람 부는 날이 아니면 산책한다." 비만 오는 날은 산책하나? 한다. "비가 안 오고 바람도 안 부는 날만 산책한다"로 바꿔 말하면 비만 오는 날은 산책하지 않는다. 두 문장은 다르다.

똑같은 구조다.\
`NOT(A AND B)`는 `NOT A OR NOT B`이지 `NOT A AND NOT B`가 아니다. 이 차이는 진리표 4줄이면 보인다.

실무 예:
- `if (!(isOwner && !isLocked)) throw forbidden;`를 읽기 쉽게 바꾸다가 경계 두 줄이 사라져 남의 문서를 수정할 수 있게 된다.
- `user.isAdmin() && user != null`처럼 순서를 바꾸자 `NullPointerException`이 난다.
- "필요한 역할을 전부 가졌나"를 `required.stream().allMatch(...)`로 쓰고, 설정 누락으로 `required`가 비자 누구나 통과한다.

## 동작·원리

### 1. 명제와 연결사 — 진리표가 정의다

```text
  A B | NOT A | A AND B | A OR B | A IMPLIES B | A IFF B
  T T |   F   |    T    |   T    |      T      |    T
  T F |   F   |    F    |   T    |      F      |    F
  F T |   T   |    F    |   T    |      T      |    F
  F F |   T   |    F    |   F    |      T      |    T
```

- *명제(proposition)*: 참이나 거짓 중 하나인 문장. 코드에서는 `boolean` 값을 내는 식이다.
- *연결사(connective)*: 명제를 묶어 새 명제를 만드는 연산. NOT(`!`)·AND(`&&`)·OR(`||`)·IMPLIES(→)·IFF(↔).
- *진리표(truth table)*: 변수의 참·거짓 조합마다 식의 값을 적은 표. 변수가 n개면 2^n줄이다(MCS 3.4.2).
- A IMPLIES B는 "A가 거짓이거나 B가 참"일 때 참이다(MCS 3.1.3). 식으로 `A → B = NOT A OR B`.
  - 흔한 오해: "전제가 거짓이면 조건문은 의미가 없다(거짓이다)." — 수학의 조건문은 전제가 거짓이면 참이다(MCS 3.1.3 "False Hypotheses"). 코드로 옮기면 `!a || b`라서, `a`가 거짓이면 검사를 통과한다.

### 2. 드모르간 법칙과 조건문의 부정

```text
  NOT(A AND B)  =  NOT A  OR  NOT B          (드모르간 — AND)
  NOT(A OR  B)  =  NOT A  AND NOT B          (드모르간 — OR)
  NOT(A → B)    =  A AND NOT B               ("A인데 B가 아닌 경우"가 반례)

  부정을 안쪽으로 밀 때: AND ↔ OR 가 서로 바뀌고, 각 항에 NOT이 붙는다
```

- *드모르간 법칙(De Morgan's laws)*: NOT을 AND·OR 안으로 나눠 넣는 규칙(MCS 3.4, 식 3.14·3.15). 진리표로 확인할 수 있다.
- *동치(equivalent)*: 변수의 어떤 조합에서도 두 식의 값이 같은 것(MCS 3.2.1). 리팩터링 전후 조건식이 동치여야 동작이 보존된다.
- 조건문 `A → B`와 짝들(MCS 3.3.1):
  - *대우(contrapositive)* `NOT B → NOT A`: 원래 조건문과 동치다.
  - *역(converse)* `B → A`: 원래 조건문과 일반적으로 동치가 아니다.
  - "A → B의 부정"을 `NOT A → NOT B`(이(裏), inverse)로 쓰는 것은 틀린 부정이다. 부정은 `A AND NOT B`다.

### 3. 술어와 한정자 — "전부"의 부정은 "하나라도 아님"

```text
  ∀x P(x)  : 어느 x를 골라도 P(x)가 참          Java: stream.allMatch(P)
  ∃x P(x)  : P(x)가 참인 x가 적어도 하나       Java: stream.anyMatch(P)

  NOT ∀x P(x)  =  ∃x NOT P(x)       "전부 만족은 아니다" = "만족 안 하는 게 하나 있다"
  NOT ∃x P(x)  =  ∀x NOT P(x)       "만족하는 게 없다"   = "전부 만족 안 한다"

  빈 집합 위에서:   ∀x P(x) = 참 (반례가 없다)      ∃x P(x) = 거짓 (예가 없다)
```

- *술어(predicate)*: 변수를 받아 명제가 되는 식. `P(x) = "x를 사용자가 가졌다"`.
- *한정자(quantifier)*: 술어를 명제로 만드는 ∀(전칭)·∃(존재). 이 둘 사이의 부정 규칙을 MCS 3.6.5는 "한정자에 대한 드모르간 법칙"이라 부른다(식 3.22).
- *공허한 참(vacuous truth)*: 대상이 하나도 없을 때 전칭 명제가 참이 되는 것. Java `Stream.allMatch` Javadoc이 "스트림이 비면 `true`를 돌려주고 술어를 평가하지 않는다"고 적는다(OpenJDK 21 `Stream.java`).

### 4. 단락 평가 — `&&`·`||`는 오른쪽을 건너뛸 수 있다

```text
  a && b :  a 평가 ─ false → 결과 false (b는 평가 안 함)
                    └ true  → b 평가 → 결과 = b
  a || b :  a 평가 ─ true  → 결과 true  (b는 평가 안 함)
                    └ false → b 평가 → 결과 = b
  a &  b :  a, b 둘 다 평가 (boolean에 쓰는 &, | 는 단락하지 않는다)
```

- *단락 평가(short-circuit evaluation)*: 왼쪽 값만으로 결과가 정해지면 오른쪽을 평가하지 않는 것. JLS 21 §15.23은 `&&`가 "왼쪽 값이 참일 때만 오른쪽을 평가한다", §15.24는 `||`가 "왼쪽 값이 거짓일 때만" 평가한다고 적는다.
- 논리값으로는 `a && b`와 `b && a`가 동치다. 그러나 **프로그램으로는 동치가 아니다.** 오른쪽이 예외를 내거나 부수 효과가 있으면 순서가 결과를 바꾼다.
  - `u != null && u.isAdmin()`은 앞 조건이 뒤 식의 *가드(guard)* 다. 순서를 바꾸면 가드가 사라진다.
- 우선순위: Java 문법에서 `&&`가 `||`보다 먼저 묶인다(JLS §15.24의 문법 `ConditionalOrExpression || ConditionalAndExpression`). `a || b && c`는 `a || (b && c)`다.

### 5. 정규형과 SAT — 식을 기계적으로 다루기

```text
  DNF (OR of ANDs):   (A AND B) OR (NOT A AND C)          "이 조합들 중 하나면 참"
  CNF (AND of ORs):   (A OR B) AND (NOT A OR C)           "이 조건들을 다 지키면 참"
  SAT: 식을 참으로 만드는 대입이 있나?   타당성(valid): 어느 대입에서도 참인가?
       F가 타당  ⇔  NOT F가 충족 불가능
```

- *DNF·CNF*: 식을 AND의 OR(곱의 합) 또는 OR의 AND로 펼친 표준 모양. 어떤 명제식이든 DNF로 바꿀 수 있다(MCS 3.4.1).
- *충족 가능(satisfiable)*: 참이 되는 대입이 하나라도 있는 식. *타당(valid)*: 어느 대입에서도 참인 식(MCS 3.3.2).
- 두 식 F·G가 동치인지는 `F IFF G`가 타당한지와 같다(MCS 3.3.2). 그래서 "리팩터링 전후 조건이 같은가"는 SAT 문제로 바꿀 수 있다: `F XOR G`가 충족 불가능하면 같다.
- 변수가 많으면 진리표는 2^n으로 커진다. 30개면 10억 줄이 넘는다(MCS 3.4.2). SAT를 다항 시간에 푸는 방법은 알려져 있지 않다(MCS 3.5) → [algorithm/40-complexity-p-np](../../algorithm/40-complexity-p-np/2-summary.md).
- 실무 조건식은 변수가 대개 몇 개라 전수 검사로 충분하다(아래 실험).

### 실험: 진리표 전수로 리팩터링 검사, 단락 평가, 공허한 참

코드 핵심(`Logic.java`):

```java
for (int bits = 0; bits < (1 << n); bits++) {           // 2^n 조합 전부 (int 시프트라 n ≤ 30일 때만 — JLS §15.19)
    boolean[] x = new boolean[n];
    for (int i = 0; i < n; i++) x[i] = ((bits >> (n - 1 - i)) & 1) != 0;
    if (f.test(x) != g.test(x)) { diff++; if (first == null) first = Arrays.toString(x); }
}
// f = x -> !(x[0] && (x[1] || x[2])),  g = x -> !x[0] || !x[1] || !x[2]  등
```

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2 --network none`, `java Logic.java`, 2026-10-07)

```text
== 1) 진리표 전수: deny 원본 vs 잘못 옮긴 판 vs 드모르간 판
member verified | orig(!(m&&v)) wrong(!m&&!v) demorgan(!m||!v)
false  false    | true           true            true
false  true     | true           false           true           <- 다름: 거부해야 하는데 허용
true   false    | true           false           true           <- 다름: 거부해야 하는데 허용
true   true     | false          false           false
== 2) 3변수 전수 비교
!(a && (b || c))             vs !a || (!b && !c)         : 0/8행 다름 (동치)
!(a && (b || c))             vs !a || !b || !c           : 2/8행 다름, 첫 반례 [a,b,c]=[true, false, true]
!(a -> b)  (= !( !a || b))   vs a && !b                  : 0/8행 다름 (동치)
!(a -> b)                    vs !a -> !b  (= a || !b)    : 4/8행 다름, 첫 반례 [a,b,c]=[false, false, false]
== 3) 단락 평가
u != null && u.admin()                               -> false
u.admin() && u != null                               -> NullPointerException
u != null &  u.admin()                               -> NullPointerException
u == null || u.admin()                               -> true
!(u != null && u.admin())  ->  u == null || !u.admin() -> true
== 4) 공허한 참(vacuous truth)
required=[] allMatch(has::contains) = true
required=[] anyMatch(has::contains) = false
required=[] !anyMatch(not has)     = true
required=[reader,admin] allMatch = false, !anyMatch(not) = false
```

- 1): 잘못 옮긴 식은 4줄 중 2줄에서 다르다. 다른 두 줄이 바로 "한 조건만 만족한" 경계다.
- 2): 중첩된 괄호의 부정을 "전부 NOT을 붙이고 OR"로 한 번에 펴면 틀린다. 안쪽 `(b || c)`의 부정은 `!b && !c`다. 마지막 행의 `!(a -> b)`와 `!a -> !b`는 c와 무관한 식이라, (a, b) 4조합 중 2조합에서 다르다(8행 중 4행).
- 3): 같은 논리값을 내는 식도 순서·연산자에 따라 예외가 난다. `&`는 단락하지 않아 `u.admin()`까지 평가한다.
- 4): 비어 있는 `required`에 대해 `allMatch`는 `true`다. 드모르간으로 바꾼 `!anyMatch(not)`도 `true`다. 빈 목록을 "검사할 게 없으니 통과"로 둘지 "설정 오류로 거부"로 둘지는 수학이 아니라 정책이 정한다.

### 실험: SQL의 3치 논리 — 드모르간은 남고 배중률은 깨진다

SQL 비교에 NULL이 끼면 결과는 TRUE·FALSE가 아닌 UNKNOWN이다. 자세한 규칙과 `NOT IN` 함정은 [database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md) §4. 여기서는 논리 법칙이 어떻게 되는지만 본다.

(실험, Python 3.12.3 표준 라이브러리 `sqlite3`(SQLite 3.45.1), 호스트, `python3 tvl.py`, 2026-10-07 — 행: (1,'BANNED',1) (2,'ACTIVE',1) (3,NULL,1) (4,'ACTIVE',NULL))

```text
status='BANNED'                  [1]
NOT(status='BANNED')             [2, 4]
status='BANNED' OR NOT(...)      [1, 2, 4]
NOT(status='ACTIVE' AND verified=1)         [1]
status<>'ACTIVE' OR verified<>1 (드모르간)  [1]
(status='ACTIVE' AND verified=1) IS NOT TRUE [1, 3, 4]
```

- `P OR NOT P`가 3번 행을 놓친다. 2치 논리의 *배중률*(P이거나 P가 아니다)이 3치 논리에서는 성립하지 않는다.
- 드모르간으로 바꾼 두 식은 같은 행을 낸다(이 데이터에서). 그러나 둘 다 3·4번(NULL이 낀 행)을 "거부 대상"에서 빠뜨린다. 허용 조건도 UNKNOWN이라 통과하지 못하니, 이 행들은 허용도 거부도 아닌 상태가 된다.
- "허용이 TRUE가 아니면 거부"를 원하면 `IS NOT TRUE`로 UNKNOWN을 거부 쪽에 넣는다.

## 쓰이는 자료구조·알고리즘

- **불리언 대수와 비트 연산** — 권한 플래그를 비트로 두면 AND·OR·NOT이 `&`·`|`·`~`가 된다. "둘 중 하나라도"는 `(perm & (READ|WRITE)) != 0`(∃), "둘 다"는 `(perm & (READ|WRITE)) == (READ|WRITE)`(∀)다. 둘을 섞으면 위 드모르간 실수와 같은 경계 누락이 생긴다 → [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md), [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md).
- **진리표 전수 검사** — 변수 n개의 조건식 두 개를 2^n 조합으로 비교한다. n이 작을 때의 확실한 동치 판정법이다.
- **SAT** — 큰 조건식의 충족 가능성·동치 판정. NP-완전 문제의 원형 → [algorithm/40-complexity-p-np](../../algorithm/40-complexity-p-np/2-summary.md).
- **정책 평가(인가)** — RBAC·ABAC 규칙은 술어 논리식이다. 기본 거부와 규칙 결합 방식 → [security/15-access-control-models](../../security/15-access-control-models/2-summary.md).
- **속성 기반 테스트** — "리팩터링 전후 식이 같다"를 성질로 두고 무작위 입력으로 검사한다 → [testing/14-property-based-testing](../../testing/14-property-based-testing/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 식으로 → 코드로

1. **증상**: "특정 사용자만 막혀야 할 곳을 통과했다" 또는 "어떤 사용자만 NPE".
2. **식으로 어림**: 조건을 기호로 적는다. 예: 거부 = `NOT(owner AND NOT locked)`.
   - 부정은 안쪽으로 민다: `NOT owner OR locked`. 각 항이 "거부되는 이유" 하나씩이다.
   - 조건이 `→`(이면) 모양이면 반례는 `A AND NOT B` 한 가지다. 테스트 케이스를 그 줄에서 만든다.
3. **코드로 확인**: 변수가 몇 개면 진리표 전수 테스트를 둔다. JUnit 5 예:

```java
@ParameterizedTest
@CsvSource({"false,false", "false,true", "true,false", "true,true"})  // 2^2 조합 전부
void refactoredDenyMatchesOriginal(boolean owner, boolean locked) {
    boolean original   = !(owner && !locked);
    boolean refactored = !owner || locked;
    assertEquals(original, refactored);
}
```

### 2. 부정을 쓰지 않는 쪽으로 다시 쓴다

- `if (!(a && b)) deny();` 대신 허용 조건을 이름 붙인 메서드로 뽑는다.

```java
boolean canEdit(User u, Doc d) {
    return u != null              // 가드: 뒤의 u.* 가 안전해진다
        && d.ownerId().equals(u.id())
        && !d.locked();
}
if (!canEdit(user, doc)) throw new AccessDeniedException("edit");
```

- 부정은 맨 바깥에 한 번만 둔다. 안쪽을 드모르간으로 펼 필요가 없어진다.
- 가드가 앞에 와야 하는 식은 한 줄에 쓰고 순서를 바꾸지 말라는 주석을 단다.

### 3. 빈 집합·NULL을 먼저 정한다

- `allMatch`·`containsAll`·SQL `NOT EXISTS`는 대상이 비면 참이다. 빈 목록이 오류인 곳에서는 먼저 막는다.

```java
if (required.isEmpty()) throw new IllegalStateException("required roles not configured");
boolean ok = required.stream().allMatch(user.roles()::contains);
```

- SQL에서 허용 조건이 NULL을 만날 수 있으면 `IS TRUE`·`IS NOT TRUE`·`COALESCE`로 UNKNOWN의 행선지를 정한다.

## 장애 시나리오와 대처

### 1. 드모르간 실수로 권한 검사 우회 (⚠ 커리큘럼)

- **현상**: 잠긴 문서를 소유자가 아닌 사람이 수정했다. 또는 미인증 회원이 유료 기능을 썼다.
- **보이는 형태**: 예외·에러 없음. 감사 로그에 권한 없는 사용자의 성공 요청(200)이 남는다. 리팩터링 커밋 직후부터다.
- **원인**: `!(a && b)`를 `!a && !b`로 바꿨다. 새 식은 "둘 다 아닐 때만" 거부해 "하나만 만족"하는 두 경우를 통과시킨다(실험 1).
- **대처**: 원래 식으로 되돌리고, 진리표 전수 테스트를 회귀 테스트로 둔다. 거부 조건 대신 허용 조건을 양(긍정)의 식으로 쓴다(적용 §2).

### 2. 단락 평가 순서에 기댄 null 검사 붕괴 (⚠ 커리큘럼)

- **현상**: 비로그인 요청에서만 500이 난다.
- **보이는 형태**: 도움말 NPE 메시지(JEP 358). 실행해 보면(OpenJDK 21.0.12, `Npe.java`) `javac -g`로 컴파일한 클래스는 `Cannot invoke "Npe$User.isAdmin()" because "u" is null`, `-g` 없이(또는 `java Npe.java` 소스 실행) 컴파일하면 `... because "<parameter1>" is null`이다. 변수 이름은 디버그 정보가 있을 때만 나온다.
- **원인**: `u != null && u.isAdmin()`을 "가독성"이나 "조건 정렬" 이유로 `u.isAdmin() && u != null`로 바꿨다. 또는 `&&`를 `&`로 바꿨다. 논리값으로는 같지만 평가 순서가 달라 가드가 사라진다(실험 3).
- **대처**: 가드를 맨 앞에 두고 `&&`·`||`만 쓴다. `Objects.requireNonNull`이나 `Optional`로 null 가능성을 타입·입구에서 끊는다. 정적 분석 도구의 null 경고를 켠다.

### 3. 빈 목록이 전부 통과 — 공허한 참

- **현상**: 설정 배포 뒤 누구나 관리 기능에 접근한다.
- **보이는 형태**: 에러 없음. 설정에서 `required-roles` 키가 빠졌거나 오타로 빈 목록이 됐다.
- **원인**: `required.stream().allMatch(has::contains)`는 빈 스트림에서 `true`다(`Stream.allMatch` Javadoc, 실험 4). ∀의 수학 정의대로 동작한 것이다.
- **대처**: 빈 목록을 명시적으로 거부한다(적용 §3). 설정 로딩 시점에 검증해 기동을 실패시킨다.

### 4. NULL이 낀 행이 허용·거부 어디에도 안 잡힌다

- **현상**: "차단 대상이 아닌 사용자" 목록과 "차단 대상" 목록의 합이 전체 사용자 수보다 적다.
- **보이는 형태**: `count(*)`와 두 쿼리 결과 합의 차이. 차이 나는 행은 조건 열이 NULL이다.
- **원인**: SQL은 3치 논리다. `P`와 `NOT P`가 둘 다 UNKNOWN인 행은 WHERE에서 둘 다 빠진다(실험: 3치 논리).
- **대처**: 열에 `NOT NULL` 제약을 건다. 조건에 `IS NOT TRUE`·`COALESCE`를 써서 UNKNOWN의 행선지를 정한다 → [database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md).

### 5. 조건문 부정을 이(裏)로 써서 테스트가 엉뚱한 경우를 본다

- **현상**: "프리미엄이면 할인한다" 규칙을 검증하는 "부정 테스트"가 통과했는데, 프리미엄 고객이 할인을 못 받는 버그가 운영에서 나왔다.
- **보이는 형태**: 테스트 녹색, 고객 문의. 테스트 이름이 "프리미엄이 아니면 할인하지 않는다"이다.
- **원인**: `premium → discount`의 반례는 `premium AND NOT discount`다. "프리미엄이 아니면 할인 안 함"(`NOT premium → NOT discount`)은 원래 규칙과 동치가 아닌 다른 규칙이다(실험 2의 마지막 줄).
- **대처**: 조건문 규칙의 테스트는 "전제가 참인 경우 결론이 참"을 직접 본다. 반대 방향이 필요하면 IFF 규칙인지 요구사항에서 확인한다.

## 핵심 문장

- 리팩터링한 조건식이 원래와 같은지는 진리표로 판정한다. 변수가 몇 개면 2^n 전수 테스트가 가장 싸고 확실하다.
- `NOT(A AND B)`는 `NOT A OR NOT B`다. 부정을 안쪽으로 밀면 AND와 OR가 바뀐다.
- `A → B`의 부정은 `A AND NOT B`이고, `NOT A → NOT B`는 부정이 아니라 다른 규칙이다.
- `&&`·`||`는 논리로는 교환 가능하지만 단락 평가 때문에 코드로는 순서가 의미를 가진다. 가드는 앞에 둔다.
- 빈 집합 위의 "전부"는 참이다. `allMatch`가 빈 목록에서 `true`를 내는 것은 버그가 아니라 정의다.
- SQL은 3치 논리라 `P OR NOT P`가 참이 아닌 행이 있다. UNKNOWN의 행선지를 명시한다.

## 관련 주제·근거

- 후속: [02-induction-and-invariants](../02-induction-and-invariants/2-summary.md)(불변식은 술어다) · [03-sets-relations-orders](../03-sets-relations-orders/2-summary.md)(집합 연산 = 논리 연산) · 나머지 수학 주제 → [math 영역 표](../README.md)
- 연결
  - [database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md) — NULL과 3치 논리, `NOT IN` 함정
  - [security/15-access-control-models](../../security/15-access-control-models/2-summary.md) — 인가 결정 지점, 기본 거부
  - [algorithm/40-complexity-p-np](../../algorithm/40-complexity-p-np/2-summary.md) — SAT·NP-완전
  - [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md) · [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md) — 비트로 하는 불리언 대수
  - [testing/14-property-based-testing](../../testing/14-property-based-testing/2-summary.md) — 동치를 성질로 검사
- 교재
  - Lehman·Leighton·Meyer, *Mathematics for Computer Science*(MCS, 2018-06-06 개정판 PDF <https://courses.csail.mit.edu/6.042/spring18/mcs.pdf>) — 3장 Logical Formulas: 3.1.3 IMPLIES 진리표·거짓 전제, 3.2 프로그램 속 명제 논리(`if (x > 0 || (x <= 0 && y > 100))` 단순화), 3.3.1 대우·역, 3.3.2 타당성·충족 가능성, 3.4 명제 대수(드모르간 식 3.14·3.15, DNF, 2^n 진리표 비용), 3.5 SAT, 3.6.5 한정자의 부정(식 3.22). 판에 따라 장 번호가 다르다 — 위 번호는 이 PDF의 목차 기준.
- 명세·문서
  - JLS SE 21 §15.23 Conditional-And Operator `&&`, §15.24 Conditional-Or Operator `||` <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html>
  - OpenJDK 21 `java/util/stream/Stream.java` — `allMatch`·`noneMatch`의 빈 스트림 `true`, "vacuously satisfied" apiNote (jdk21u 소스)
  - JEP 358 Helpful NullPointerExceptions <https://openjdk.org/jeps/358>
- 실험 목록(이 노트)
  - `Logic.java` — 권한 거부식 진리표 전수, 3변수 동치 판정 4쌍, 단락 평가 5식, `allMatch`/`anyMatch` 빈 목록. OpenJDK 21.0.12 Temurin, docker(`--cpus=2 --network none`), 2026-10-07.
  - `Npe.java` — 순서를 바꾼 가드의 NPE 메시지, `javac -g` 유무 비교. 같은 환경.
  - `tvl.py` — SQLite 3.45.1(Python 3.12.3 `sqlite3`) 3치 논리: `P OR NOT P`, 드모르간 양변, `IS NOT TRUE`. 호스트, 2026-10-07.
