# PR #36912 분석 — reserveMethodNames가 varargs 배열 전체를 하나의 이름으로 합친 결함

> 기준: PR 머지베이스 `0c60266986197a191ff33eb498ebc8bac3dc933f` 대비 `refs/pr/36912`.
> 이 문서는 결함의 경로 추적과 계약 분석에 집중한다. 배경 서술은 README.md, 무대의
> 소유 관계도는 structure.md, 테스트 한 건의 해설은 tests.md가 각각 맡는다.

## 0. 결론

`GeneratedClass.reserveMethodNames(String...)`는 루프를 돌며 이름을 하나씩 예약하도록
쓰여 있으면서, 정작 루프 안에서 `MethodName.of()`에 루프 변수가 아니라 **varargs 배열
전체**를 넘긴다. 그래서 이름을 둘 이상 넘기면 첫 반복부터 합쳐진 제3의 이름
(`"apply"`, `"test"` -> `applyTest`)을 발급받고, 그 값이 루프 변수와 다르므로
`Assert.state`가 `IllegalStateException`을 던져 **예약이 한 건도 이뤄지지 않는다**.

수정은 `GeneratedClass.java:84`의 인자를 복수형 `reservedMethodNames`에서 단수형
`reservedMethodName`으로 바꾸는 한 글자다.

PR 상태는 2026-08-25 확인 기준 OPEN이며 라벨은 `status: waiting-for-triage` 하나,
리뷰 코멘트는 0건이다. 생성일은 2026-06-13이다.

## 1. 무대

결함은 AOT 코드 생성기가 쓰는 `GeneratedClass` 한 클래스, 그중 예약 API 한 메서드 안에
갇혀 있다. 아래 항목은 모듈에서 협력 클래스까지 그 좌표를 좁혀 간다.

- 모듈: `spring-core`, 패키지 `org.springframework.aot.generate`.
- 결함 클래스: `spring-core/src/main/java/org/springframework/aot/generate/GeneratedClass.java`
  (`public final class GeneratedClass`, :39).
- 공개 진입 API: `public void reserveMethodNames(String... reservedMethodNames)` (:82).
  같은 클래스의 `getMethods()`(:117)가 돌려주는 `GeneratedMethods`가 실제 이름 발급의
  소비자이고, 둘은 `methodNameSequenceGenerator`(:51) 맵 하나를 공유한다.
- 협력 클래스: `MethodName`(패키지 프라이빗 값 객체, `MethodName.java:33`),
  `GeneratedMethods`(`GeneratedMethods.java:38`), `GeneratedClasses`(생성 팩터리).

누가 언제 부르는가. 이 API는 **AOT 빌드 시점**에만 실행되며, 런타임 요청 경로에는
없다. 트리 안의 프로덕션 호출처는 grep 기준 단 하나다.

```
spring-context/src/main/java/org/springframework/context/aot/
        ApplicationContextInitializationCodeGenerator.java:75
                this.generatedClass.reserveMethodNames(INITIALIZE_METHOD);
```

`INITIALIZE_METHOD`는 `"initialize"` 상수 하나(:60)다. 즉 in-tree 호출은 항상 인자가
**한 개**다. `reserveMethodNames`가 public varargs API이므로 트리 밖 코드 생성기가 여러
이름을 넘길 수 있지만, 실제 그런 호출자가 존재하는지는 미확인이다.

예약이 지키는 것은 런타임 정합성이 아니라 **생성된 소스의 컴파일 가능성**이다.
`ApplicationContextInitializationCodeGenerator`는 `initialize` 메서드를
`MethodSpec.methodBuilder(INITIALIZE_METHOD)`(:90)로 손수 써 넣는데, 자동 생성 메서드가
같은 이름을 발급받으면 한 클래스 안에 같은 시그니처가 둘이 되어 javac가 거부한다.

## 2. 전체 메서드 그래프

진입점부터 결함 지점까지, 그리고 예약이 실제로 효력을 내는 소비 지점까지의 호출
관계다. 괄호 안은 파일:줄이다.

```
[AOT 빌드 태스크]
  -> ContextAotProcessor.performAotProcessing(ctx)          ContextAotProcessor.java:102
  -> ApplicationContextAotGenerator.processAheadOfTime(...)  ApplicationContextAotGenerator.java:51
       |
       +-- new ApplicationContextInitializationCodeGenerator(ctx, generationContext)      :57 / 생성자 :71
       |     +-- getGeneratedClasses().addForFeature("ApplicationContextInitializer", ...)  :73
       |     |     -> new GeneratedClass(name, type)                     GeneratedClass.java:61
       |     |          methods = new GeneratedMethods(name, this::generateSequencedMethodName)  :70
       |     |          methodNameSequenceGenerator = new ConcurrentHashMap<>()                  :72
       |     |
       |     +-- generatedClass.reserveMethodNames(INITIALIZE_METHOD)                            :75
       |           |
       |           v  GeneratedClass.reserveMethodNames(String... reservedMethodNames)           :82
       |           +-- for (String reservedMethodName : reservedMethodNames)                     :83
       |                 +-- MethodName.of( ??? )   <== 결함 지점                MethodName.java:56
       |                 |     of(String... parts) -> new MethodName(join(parts))
       |                 |     join: 조각별 clean+capitalize 를 이어붙인 뒤 uncapitalize        :110
       |                 +-- generateSequencedMethodName(methodName)          GeneratedClass.java:90
       |                 |     map.computeIfAbsent(name, AtomicInteger::new).getAndIncrement()
       |                 |     return (sequence > 0 ? name + sequence : name)
       |                 +-- Assert.state(generatedName.equals(reservedMethodName), ...)          :85
       |                       실패 시 IllegalStateException("Unable to reserve method name '%s'")
       |
       +-- new BeanFactoryInitializationAotContributions(beanFactory).applyTo(...)                :59
             +-- 각 기여자: codeGenerator.getMethods().add(suggestedName, method)
                   -> GeneratedMethods.add(String, Consumer)            GeneratedMethods.java:87
                   -> add(new String[]{suggestedName}, method) -> prefix.and(parts)  :89, :111
                   -> methodNameGenerator.apply(name) == GeneratedClass::generateSequencedMethodName
                        같은 맵을 읽으므로 예약된 이름은 sequence>=1 -> "initialize1"
```

데이터 흐름의 요점은 하나다. **예약을 담는 별도 자료구조가 없다.** 예약은
`methodNameSequenceGenerator` 맵의 카운터를 한 번 미리 소비하는 부작용으로만 존재하고,
그 맵을 `reserveMethodNames`와 `GeneratedMethods.add`가 공유한다. 따라서 잘못된 키로
카운터를 올리면 (1) 의도한 이름은 여전히 sequence 0이라 다음 발급이 맨 이름을 받고
(2) 아무도 쓰지 않을 합성 키가 맵에 남는다.

## 2.5 핵심 이름표 사전

이 흐름에는 이름이 `s` 하나로만 갈리는 쌍(`reservedMethodNames` / `reservedMethodName`)이
있고, "이름"이 문자열·값 객체·맵 키 세 가지 층위로 돌아다닌다. 아래는 등장하는 식별자
전부에 대해 역할, 입출력, 호출 시점, 이 결함과의 관계를 적은 것이다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `reserveMethodNames(String...)` (GeneratedClass.java:82) | 공개 예약 API | `String[]` -> void (실패 시 예외) | AOT 코드 생성기가 생성 클래스를 만든 직후 1회 | 결함이 있는 메서드 본체 |
| `reservedMethodNames` (:82 파라미터) | varargs 배열 전체 | -- | 위 호출 시 바인딩 | :84에 잘못 전달된 값. 원소가 2개 이상이면 결함 발동 |
| `reservedMethodName` (:83 루프 변수) | 이번 반복이 예약할 이름 하나 | -- | 반복마다 | :85 검증과 :86 메시지는 이 값을 쓰는데 :84만 쓰지 않는다 |
| `generatedName` (:84 지역변수) | 발급받은 실제 이름 | `MethodName` -> `String` | 반복마다 | 결함 시 `applyTest` 같은 제3의 값이 들어온다 |
| `MethodName.of(String...)` (MethodName.java:56) | 조각들을 camel-case 이름 하나로 **합치는** 팩터리 | `String[]` -> `MethodName` | `reserveMethodNames`, `MethodName.and` | 여러 조각을 합치는 것이 정상 계약. 결함은 이 API를 "이름 하나씩" 루프 안에서 쓴 데 있다 |
| `MethodName.join(String[])` (:110) | 실제 합성 로직 | `["apply","test"]` -> `"applyTest"` | `of`, `and` 내부 | 결함의 관측 가능한 증상을 만드는 함수 |
| `MethodName.clean(String)` (:115) | 글자만 남기고 `.` 뒤를 대문자화 | `"get.bean"` -> `"getBean"` | `join` 내부 | 결함과 직접 관계 없음. 이름 정규화 규칙의 일부 |
| `MethodName.value` (:42) | 합성된 문자열 본체 | -- | `equals`/`hashCode`/`toString` | 맵 키의 동일성이 이 값 하나로 결정된다(:96, :101) |
| `MethodName.NONE` (:40) | 빈 이름 상수 `of()` | -- | `GeneratedMethods` 생성자의 초기 prefix(:59) | 무관 |
| `MethodName.PREFIXES` (:35) | `get`/`set`/`is` 접두사 목록 | -- | `getPrefix`(:84) | 무관 |
| `MethodName.and(String...)` (:76) | prefix에 조각을 붙여 새 이름 | `["instance"]` -> `myBeanInstance` | `GeneratedMethods.add`(:111), `withPrefix`(:127) | `of(String...)`의 합성 성질을 **정상적으로** 쓰는 자리. 대조군 |
| `methodNameSequenceGenerator` (GeneratedClass.java:51) | 이름별 발급 카운터. 예약 상태의 유일한 저장소 | `Map<MethodName, AtomicInteger>` | `generateSequencedMethodName`만 | 결함 시 합성 키 항목이 오염되어 남는다 |
| `generateSequencedMethodName(MethodName)` (:90) | 이름 발급. 조회가 아니라 **소비** | `MethodName` -> `String` | `reserveMethodNames`(:84), `GeneratedMethods`의 함수 참조(:70) | 예약과 발급이 같은 함수를 공유하므로, 키가 틀리면 두 쪽이 어긋난다 |
| `sequence` (:91 지역변수) | 이번 발급 전의 카운터 값 | -> `int` | 발급마다 | 0이면 맨 이름, 1 이상이면 숫자 접미사 |
| `Assert.state(...)` (:85) | 발급 결과가 요청과 같은지 검증 | `boolean`, 메시지 supplier -> void/예외 | 반복마다 | 결함을 **드러내는** 장치. 이것이 없었다면 조용한 실패였다 |
| `methods` / `getMethods()` (:45, :117) | 생성될 메서드 모음 | -> `GeneratedMethods` | 기여자들이 메서드를 추가할 때 | 예약의 효과가 관측되는 표면 |
| `GeneratedMethods.methodNameGenerator` (GeneratedMethods.java:42) | 이름 발급 함수 참조 | `MethodName` -> `String` | `add`(:111) | `GeneratedClass::generateSequencedMethodName`이 주입된다(:70). 같은 맵을 공유하는 근거 |
| `GeneratedMethods.prefix` (:44) | 제안 이름에 붙는 접두사 | -- | `add`, `withPrefix` | 예약은 prefix를 거치지 않는다. 예약 키와 발급 키가 어긋날 수 있는 별개 경로 |
| `GeneratedMethods.add(String, Consumer)` (:87) | 메서드 추가 진입점 | 제안 이름 -> `GeneratedMethod` | 각 AOT 기여자 | 예약이 효력을 내는 소비 지점 |
| `INITIALIZE_METHOD` (ApplicationContextInitializationCodeGenerator.java:60) | 손코드 메서드 이름 `"initialize"` | -- | 생성자(:75)와 `generateInitializeMethod`(:90) | in-tree 유일 호출의 인자. 원소 1개라 결함이 드러나지 않았다 |

## 3. 결함 경로 단계 추적

두 케이스를 같은 축으로 비교한다. 왼쪽은 in-tree 유일 호출이 타는 단일 이름 경로,
오른쪽은 이름을 둘 넘겼을 때다. 각 단계의 변수 값을 그대로 적었다.

| 단계 | 정상 케이스 `reserveMethodNames("initialize")` | 결함 케이스 `reserveMethodNames("apply", "test")` |
|---|---|---|
| 진입 (:82) | `reservedMethodNames = ["initialize"]` | `reservedMethodNames = ["apply", "test"]` |
| 반복 1 루프 변수 (:83) | `reservedMethodName = "initialize"` | `reservedMethodName = "apply"` |
| 합성 (:84 -> MethodName.java:110) | `join(["initialize"]) = "initialize"` | `join(["apply","test"]) = "applyTest"` |
| 발급 전 맵 (:91) | `{}` | `{}` |
| 발급 (:92) | 키 `initialize` 생성, `sequence = 0` | 키 `applyTest` 생성, `sequence = 0` |
| 발급 결과 (:93) | `generatedName = "initialize"` | `generatedName = "applyTest"` |
| 검증 (:85) | `"initialize".equals("initialize")` = true, 통과 | `"applyTest".equals("apply")` = false, `IllegalStateException` |
| 반복 2 | 없음 | **실행되지 않음** (예외로 루프 중단) |
| 종료 후 맵 | `{initialize -> 1}` | `{applyTest -> 1}` |
| 이후 `getMethods().add("apply", ...)` | 해당 없음 | 키 `apply`는 맵에 없다 -> `sequence = 0` -> 이름 `"apply"` |
| 이후 `getMethods().add("initialize", ...)` | 키 `initialize`가 1 -> `sequence = 1` -> `"initialize1"` | 해당 없음 |

결함 케이스의 마지막 두 행이 피해의 실체다. 예약을 요청한 `apply`와 `test`는 카운터가
0인 채로 남아 있으므로, 이후 자동 생성 메서드가 **번호 없는 맨 이름을 그대로 받는다.**
호출자가 예외를 잡고 진행하면 손코드 메서드와 시그니처가 겹쳐 생성 소스가 컴파일되지
않는다. 예외를 잡지 않으면 AOT 처리 자체가 중단된다. 어느 쪽이든 예약은 실패다.

원소 3개 이상이어도 결과는 같다. 첫 반복에서 이미 예외가 나므로 뒤 원소는 관측되지
않는다. 원소 0개(`reserveMethodNames()`)는 루프가 0회전이라 아무 일도 없고 예외도 없다.

## 4. 계약

이 코드가 고정하고 있는 계약은 네 곳에서 읽힌다.

**javadoc (GeneratedClass.java:76-81)** — "Update this instance with **a set of reserved
method names**"이고 `@param reservedMethodNames the reserved method names`다. 복수의
집합을 받아 각각을 예약한다는 진술이며, "합쳐서 하나로 예약한다"는 서술은 없다.

**코드 자체의 구조** — 루프(:83)가 있고, 검증(:85)이 **루프 변수 하나**와 비교하며,
실패 메시지(:86)가 `'%s'` 자리에 이름 하나만 인용한다. 합친 이름 하나를 예약할
의도였다면 루프도, per-element 검증도, 단수형 메시지도 필요 없다. 세 신호가 모두 "각각
예약"을 가리킨다.

**기존 테스트 두 건** — `reserveMethodNamesReservesNames`
(`GeneratedClassTests.java:74-79`)가 이름 하나를 예약하면 다음 발급이 `apply1`임을
고정하고, `reserveMethodNamesWhenNameUsedThrowsException`(:66-71)이 이미 사용된 이름은
예약할 수 없고 `IllegalStateException`이 나야 함을 고정한다. 두 건이 각각 "예약 성공은
조용히", "예약 실패는 시끄럽게"라는 계약의 양쪽 끝이다.

**부작용 기반 예약의 불변식** — 예약 직후 그 이름의 카운터가 1 이상이어야 하고, 이후
같은 이름의 발급은 숫자 접미사를 받아야 한다. 이 불변식은 공개 조회 API가 없으므로
"다음 발급 이름"으로만 관측된다.

결함이 어기는 계약은 첫째와 넷째다. 이름을 둘 이상 주면 javadoc이 약속한 집합 예약이
일어나지 않고, 요청한 어느 이름의 카운터도 올라가지 않는다. 둘째·셋째 계약은 어기지
않는다 — 오히려 셋째의 검증문이 결함을 예외로 드러내 준 셈이다. 다만 그 대가로
**같은 예외 메시지가 두 가지 다른 사유를 덮는다.** "이미 사용된 이름이라 예약 불가"와
"합성 결과가 요청과 달라서 불일치"가 구분되지 않는다.

## 5. 수정안

변경 지점은 `GeneratedClass.java:84` 한 줄이다.

before (머지베이스 기준 `GeneratedClass.java:82-88`):

```java
	public void reserveMethodNames(String... reservedMethodNames) {
		for (String reservedMethodName : reservedMethodNames) {
			String generatedName = generateSequencedMethodName(MethodName.of(reservedMethodNames));
			Assert.state(generatedName.equals(reservedMethodName),
					() -> String.format("Unable to reserve method name '%s'", reservedMethodName));
		}
	}
```

after (`refs/pr/36912`의 같은 줄):

```java
			String generatedName = generateSequencedMethodName(MethodName.of(reservedMethodName));
```

왜 이 위치인가. 결함은 발급 함수에도, 검증문에도, `MethodName.of`의 합성 규칙에도 없다.
`MethodName.of(String...)`가 여러 조각을 하나로 합치는 것은 `MethodName.and`(:76)가
의존하는 정상 계약이고, `Assert.state`가 루프 변수와 비교하는 것도 per-element 예약
의도에 맞다. 어긋난 것은 **그 사이에 흘러 들어간 인자 하나**뿐이므로, 다른 어떤 곳을
고쳐도 세 요소 중 하나의 정상 계약을 깨게 된다.

검토된 대안과 기각 이유는 셋이다.

첫째, "합친 이름 하나를 예약하는 것이 원래 의도"라고 보고 루프와 검증문을 걷어내는
방향. §4의 세 신호(javadoc의 복수형, per-element 검증, 단수형 메시지)가 모두 반대
방향을 가리키므로 기각한다. 다만 이 판단은 코드에서 읽어낸 추론이므로, PR 본문은
"반대 의도였다면 다른 수정이 맞다"를 명시해 열어 두었다.

둘째, `Assert.state` 검증문을 제거해 예외를 없애는 방향. 예외가 사라져도 요청한 이름의
카운터는 여전히 올라가지 않으므로 결함이 **조용한 실패로 바뀔 뿐**이다. 게다가 기존
테스트 `reserveMethodNamesWhenNameUsedThrowsException`이 고정한 계약을 깬다.

셋째, `MethodName.of`에 단일 인자 오버로드를 추가하거나 시그니처를 바꿔 오용 자체를
막는 방향. 패키지 프라이빗 값 객체의 API 표면을 넓히는 변경이고, `and(String...)`가
가변 조각 합성을 실제로 쓰고 있어 시그니처 축소도 불가능하다. 결함 하나를 고치는 데
필요한 최소 변경보다 크다.

테스트는 `GeneratedClassTests`에 한 건이 추가되었다(`:81-87`). 예약 호출이 예외 없이
끝나는지와, 이후 발급이 `apply1`·`test1`인지를 각각 단언해 **per-element로 카운터가
소비되었음**을 값으로 증명한다. 내부 맵을 리플렉션으로 들여다보지 않고 관측 가능한
후속 동작으로 확인하는 방식이며, 단언을 두 줄 두는 것이 "첫 이름만 예약되는 절반
수정"을 걸러낸다.

## 6. 범위 밖과 인접 영향

**같은 패턴의 다른 위치.** `reservedMethodNames`처럼 varargs 배열을 루프 안에서 통째로
넘기는 자리를 찾았으나, `reserveMethodNames`는 트리 전체에서 선언 1곳·프로덕션 호출
1곳·테스트 3곳뿐이고 다른 위치에 같은 오용은 없다. `MethodName.of(String...)`의 다른
호출처는 `MethodName.and`(:81) 하나이며, 그곳은 합성이 의도된 정상 사용이다.

**하위 호환.** 원소 0개와 1개 경로의 동작은 문자 하나 달라지지 않는다. 1개 배열은
`join(["x"]) == "x"`이므로 `MethodName.of(배열)`과 `MethodName.of(원소)`가 같은 값을
만들기 때문이다. 따라서 in-tree 유일 호출처인 `ApplicationContextInitializer` 생성
경로는 수정 전후가 동일하다. 원소 2개 이상 경로는 수정 전에 **항상 예외로 끝났으므로**
성공 동작이 존재한 적이 없다. 즉 이 변경은 기존 성공 동작을 바꾸는 것이 아니라 늘
실패하던 경로를 성공시키는 쪽이고, 그 방향에서 호환성 위험은 없다.

**인접하지만 이번에 건드리지 않은 것.** (1) 검증문이 "이미 사용된 이름"과 "합성 불일치"를
같은 메시지로 덮는 문제 — 수정 후에는 후자가 발생할 수 없으므로 실질적 모호성이
사라진다. 메시지 자체는 손대지 않았다. (2) 예약 여부를 조회하는 공개 API가 없다는 점 —
테스트가 후속 발급 이름으로 우회하고 있으며, API 추가는 별건이다. (3) `GeneratedMethods`의
prefix 경로(:111)는 예약을 거치지 않으므로 prefix가 붙은 이름은 예약 대상이 될 수 없다.
현재 계약상 문제로 보이지 않으나, 예약 API를 확장할 때 다시 볼 지점이다.
