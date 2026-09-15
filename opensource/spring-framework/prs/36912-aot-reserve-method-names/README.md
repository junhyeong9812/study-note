# PR #36912 — Fix reserveMethodNames to reserve each supplied name

## 0. 정향

이 문서는 `spring-core`의 `GeneratedClass#reserveMethodNames(String...)` 버그 수정 PR을 처음부터 이해하기 위한 해설이다.\
바뀐 글자는 `reservedMethodNames`에서 `s` 하나를 뺀 것뿐이지만, 그 한 글자가 왜 문제였는지 알려면 AOT 코드 생성기가 메서드 이름을 어떻게 만들고 충돌을 어떻게 피하는지부터 봐야 한다.\
다 읽으면 "이름을 두 개 이상 예약하면 예약이 되기는커녕 예외가 났다"를 남에게 설명할 수 있어야 한다.

## 1. 배경 — AOT 코드 생성에서 메서드 이름 예약이 왜 필요한가

Spring의 AOT 처리는 런타임 리플렉션으로 하던 일을 빌드 시점에 자바 소스로 미리 써 둔다.\
`GeneratedClass`는 그렇게 생성될 클래스 하나를 나타내는 객체다.\
이 객체는 클래스 이름, 중첩 클래스 목록, 그리고 생성될 메서드들의 모음(`GeneratedMethods`)을 들고 있다.

> **AOT(Ahead-Of-Time, 사전 컴파일)** — 프로그램이 실행되기 전(빌드 시점)에 미리 처리해 두는 방식. 실행 중에 알아내던 것을 빌드 때 확정해 파일로 남긴다.\
> 예: 런타임 리플렉션으로 빈을 조립하던 코드를 빌드 시점에 자바 소스로 써 두는 Spring AOT 처리.

> **`GeneratedClass`** — 앞으로 생성될 자바 클래스 하나를 나타내는 객체. 클래스 이름·중첩 클래스·메서드 모음과, 메서드 이름 발급용 카운터를 들고 있다.\
> 예: `ApplicationContextInitializer`를 구현하는 클래스를 만들 때 `GeneratedClasses.addForFeature(...)`가 하나 만들어 준다.

> **`GeneratedMethods`** — 한 `GeneratedClass` 안에 생성될 메서드들의 모음. `add(suggestedName, ...)`로 메서드를 받고, 이름은 자기가 짓지 않고 `GeneratedClass`의 발급 함수에 물어본다.\
> 예: `generatedClass.getMethods().add("apply", ...)`가 돌려주는 메서드의 이름이 `apply1`이 되는 식.

생성되는 메서드 이름은 사람이 짓지 않는다.\
코드 생성기는 "이런 이름이면 좋겠다"는 제안(`suggestedName`)만 주고, 실제 이름은 `GeneratedClass`가 정한다.\
한 클래스 안에서 같은 제안이 여러 번 오면 충돌하므로, `GeneratedClass`는 이름별 카운터를 두고 두 번째부터 숫자를 붙인다.\
이 카운터가 `methodNameSequenceGenerator`이고, 이름을 발급하는 함수가 `generateSequencedMethodName`이다.

> **제안 이름(suggestedName)** — 코드 생성기가 "이 이름이면 좋겠다"고 내는 후보 문자열. 최종 이름은 아니며, 충돌하면 뒤에 번호가 붙는다.\
> 예: `add("apply", ...)`의 `"apply"` — 이미 한 번 쓰였다면 실제 이름은 `apply1`이 된다.

```java
private final Map<MethodName, AtomicInteger> methodNameSequenceGenerator;

private String generateSequencedMethodName(MethodName name) {
	int sequence = this.methodNameSequenceGenerator
			.computeIfAbsent(name, key -> new AtomicInteger()).getAndIncrement();
	return (sequence > 0 ? name.toString() + sequence : name.toString());
}
```

첫 호출은 시퀀스 0이라 이름을 그대로 돌려주고, 두 번째부터 `apply1`, `apply2`처럼 뒤에 번호가 붙는다.\
여기서 핵심은 이 함수가 **조회가 아니라 발급**이라는 점이다.\
호출하는 순간 카운터가 증가한다.\
이 성질이 뒤에서 그대로 "예약" 메커니즘이 된다.

이름을 미리 잡아 둬야 하는 상황은 생성 클래스가 특정 인터페이스를 구현할 때 생긴다.\
생성된 클래스가 손으로 쓴 메서드 하나를 반드시 갖는데, 자동 생성 메서드가 우연히 같은 이름을 받으면 컴파일이 깨진다.\
실제로 in-tree 유일한 호출처가 그 경우다.

> **in-tree 호출처** — 이 저장소(spring-framework 트리) 안에 실제로 존재하는 호출 코드. 트리 밖 사용자 코드와 구분하는 말.\
> 예: `reserveMethodNames`의 in-tree 프로덕션 호출처는 `ApplicationContextInitializationCodeGenerator.java:75` 하나뿐이다.

```java
private static final String INITIALIZE_METHOD = "initialize";
...
this.generatedClass.reserveMethodNames(INITIALIZE_METHOD);
```

`ApplicationContextInitializationCodeGenerator`는 `ApplicationContextInitializer`를 구현하는 클래스를 만들고, 그 안에 `initialize` 메서드를 직접 써 넣는다.\
그래서 생성자에서 `initialize`를 먼저 예약해, 이후 자동 생성 메서드가 그 이름을 못 받게 막는다.

## 2. 수정 전 동작 방식 — 발급을 한 번 소모해서 예약한다

`reserveMethodNames`의 아이디어는 단순하다.\
예약할 이름으로 시퀀스를 한 번 소모해 두면, 같은 이름에 대한 다음 발급은 시퀀스 1이 되어 `apply1`처럼 번호가 붙는다.\
즉 이후 아무도 맨 이름을 받지 못한다.\
수정 전 코드는 이렇다.

```java
/**
 * Update this instance with a set of reserved method names that should not
 * be used for generated methods. Reserved names are often needed when a
 * generated class implements a specific interface.
 * @param reservedMethodNames the reserved method names
 */
public void reserveMethodNames(String... reservedMethodNames) {
	for (String reservedMethodName : reservedMethodNames) {
		String generatedName = generateSequencedMethodName(MethodName.of(reservedMethodNames));
		Assert.state(generatedName.equals(reservedMethodName),
				() -> String.format("Unable to reserve method name '%s'", reservedMethodName));
	}
}
```

in-tree 호출이 실제로 타는 경로를 단계별로 펴 보면 이렇다.\
왼쪽이 단계, 오른쪽이 그 단계가 정하는 값이다.

```text
ApplicationContextInitializationCodeGenerator    "initialize" 를 예약하려 한다
        |
        v
reserveMethodNames("initialize")                 루프 1회전, reservedMethodName = "initialize"
        |
        v
MethodName.of(reservedMethodNames)               배열 전체를 넘긴다  <-- 버그 자리
        |
        v
join(["initialize"]) = "initialize"              원소 1개라 우연히 같은 값이 나온다
        |
        v
generateSequencedMethodName(...)                 카운터 0 -> 1, "initialize" 반환
        |
        v
Assert.state("initialize".equals("initialize"))  통과 -> 증상이 드러나지 않는다
```

원소가 하나뿐이라 잘못된 인자가 결과에 나타나지 않는다는 것이 이 그림의 요점이다.

`Assert.state`는 안전장치다.\
발급받은 이름이 예약하려던 이름과 다르다면, 그 이름은 이미 누가 써 버렸다는 뜻이다.\
이때 예약은 실패해야 하므로 `IllegalStateException`을 던진다.\
기존 테스트 `reserveMethodNamesWhenNameUsedThrowsException`이 이 경로를 고정한다.

> **`Assert.state` / `IllegalStateException`** — 지금 상태가 코드가 기대하는 상태인지 확인하고, 아니면 예외를 던지는 Spring 유틸리티. 상태가 틀렸다는 신고이지 인자 검증이 아니다.\
> 예: 발급 이름이 예약하려던 이름과 다르면 `Unable to reserve method name 'apply'`를 던진다.

문제는 루프 안에서 `MethodName.of`에 넘기는 인자다.\
루프 변수 `reservedMethodName`이 아니라 배열 전체인 `reservedMethodNames`가 들어가 있다.\
오타 한 글자라 눈에 잘 안 띈다.

`MethodName`은 여러 조각을 받아 camel-case 이름 하나로 합치는 값 객체다.\
조각별로 문자만 남기고 첫 글자를 대문자로 만든 뒤 이어 붙이고, 마지막에 첫 글자를 소문자로 되돌린다.

> **`MethodName`** — 메서드 이름 하나를 담는 값 객체. `of(String... parts)`로 만들며, 여러 조각을 camel-case로 **합쳐** 이름 하나를 만든다.\
> 예: `MethodName.of("get", "bean", "factory")` = `getBeanFactory`.

```java
private static String join(String[] parts) {
	return StringUtils.uncapitalize(Arrays.stream(parts).map(MethodName::clean)
			.map(StringUtils::capitalize).collect(Collectors.joining()));
}
```

`MethodNameTests`가 이 합성 규칙을 명시적으로 고정한다.\
예를 들어 `MethodName.of("get", "bean", "factory")`는 `getBeanFactory`다.\
즉 여러 조각을 넘기면 여러 이름이 아니라 **하나의 합쳐진 이름**이 나온다.

## 3. 무엇이 문제였나 — 이름이 두 개 이상이면 예약 자체가 실패한다

이름 하나만 넘기면 버그가 드러나지 않는다.\
한 원소 배열은 합쳐도 자기 자신이라 `MethodName.of(reservedMethodNames)`와 `MethodName.of(reservedMethodName)`이 같은 값이 된다.\
유일한 in-tree 호출처가 이름 하나만 예약하므로, 여러 이름 경로는 한 번도 실행된 적이 없었다.

이름을 둘 이상 넘기면 이야기가 달라진다.\
`reserveMethodNames("apply", "test")`의 첫 반복에서 `MethodName.of("apply", "test")`는 `applyTest`가 되고, 발급 결과도 `applyTest`다.\
그런데 검증은 루프 변수와 비교한다.\
`"applyTest".equals("apply")`는 거짓이므로 첫 반복에서 바로 `IllegalStateException: Unable to reserve method name 'apply'`가 튀어나온다.

```text
reserveMethodNames("apply", "test")              1회전, reservedMethodName = "apply"
        |
        v
MethodName.of(["apply","test"])                  join -> "applyTest"  <-- 제3의 이름
        |
        v
generateSequencedMethodName("applyTest")         맵에 applyTest 생성, sequence 0 -> "applyTest"
        |
        v
Assert.state("applyTest".equals("apply"))        false -> IllegalStateException
        |
        v
루프 중단                                        2회전("test")은 실행조차 되지 않는다
```

컴파일된 upstream 코드에 직접 붙여 확인한 실행 결과가 이를 뒷받침한다.\
예약 호출은 예외로 끝나고, 이후 `apply`와 `test`는 번호 없는 맨 이름을 그대로 받는다.\
즉 예약은 하나도 이뤄지지 않았다.

```text
THROWN: java.lang.IllegalStateException: Unable to reserve method name 'apply'
apply -> apply
test  -> test
MethodName.of(apply,test) = applyTest
```

실패 양상은 두 겹이다.\
겉으로는 예외라서 시끄럽지만, 예외를 잡아서 넘기는 호출자가 있다면 조용한 실패가 된다.\
예약된 줄 알았던 이름을 자동 생성 메서드가 받아 가고, 손으로 쓴 메서드와 시그니처가 같아지면 생성된 소스가 컴파일되지 않는다.\
게다가 카운터에는 아무도 쓰지 않을 `applyTest` 항목만 하나 남는다.

> **조용한 실패(silent failure, 무음 실패)** — 작업이 실패했는데 아무 신호도 남지 않아 성공한 것처럼 보이는 상태. 로그도 예외도 없어 나중에 다른 증상으로 터진다.\
> 예: 호출자가 `IllegalStateException`을 잡고 넘어가면 "예약했다"고 믿은 채 진행하지만 실제로 예약된 이름은 하나도 없다.

## 4. 수정 해설 — 루프 변수를 넘긴다

수정은 인자를 루프 변수로 바꾸는 것이다.

```java
-			String generatedName = generateSequencedMethodName(MethodName.of(reservedMethodNames));
+			String generatedName = generateSequencedMethodName(MethodName.of(reservedMethodName));
```

같은 입력 `reserveMethodNames("apply", "test")`가 수정 전후로 어떻게 갈라지는지 나란히 놓으면 이렇다.

```text
수정 전 of(reservedMethodNames)          수정 후 of(reservedMethodName)
+------------------------------+         +------------------------------+
| round 1: join(apply,test)    |         | round 1: join(apply)         |
|   = "applyTest"              |         |   = "apply"                  |
| check applyTest vs apply: NO |         | check apply vs apply: OK     |
| round 2: not executed        |         | round 2: "test" -> OK        |
| map { applyTest -> 1 }       |         | map { apply->1, test->1 }    |
+------------------------------+         +------------------------------+
  -> apply, test 는 예약되지 않는다         -> 이후 발급은 apply1, test1
```

같은 루프, 같은 검증문인데 들어가는 값 하나만 달라져 결과가 갈린다.

이 수정에는 의도 판단이 하나 걸려 있다.\
`reserveMethodNames`가 이름을 **각각** 예약하는 것인지, 아니면 합친 이름 하나를 예약하는 것인지다.\
코드 자체가 답을 준다.\
첫째, javadoc이 "a set of reserved method names"라고 복수의 집합으로 말한다.\
둘째, 검증문이 루프 변수와 비교하므로 반복마다 하나씩 예약된다는 전제 위에 서 있다.\
셋째, 실패 메시지가 `'%s'` 하나만 인용한다.\
합친 이름 하나를 예약할 의도였다면 루프도 per-element 검증도 필요 없다.\
그래서 "각각 예약"이 의도이고 인자 전달이 오타라고 읽는 것이 자연스럽다.\
PR 본문도 이 판단을 명시하고, 반대 의도였다면 다른 수정이 맞다고 열어 두었다.

수정 전후를 같은 입력으로 비교하면 차이가 분명하다.\
아래는 컴파일된 upstream 코드와, 같은 파일에 위 한 줄만 적용해 다시 컴파일한 코드를 각각 실행한 결과다.

| 호출 | 수정 전 | 수정 후 |
|------|---------|---------|
| `reserveMethodNames("apply", "test")` | `IllegalStateException` | 정상 종료 |
| 이후 `add("apply", ...)` | `apply` | `apply1` |
| 이후 `add("test", ...)` | `test` | `test1` |

이름 하나만 넘기는 기존 경로의 결과는 달라지지 않는다.\
한 원소 배열은 두 표현이 같은 값을 만들기 때문이다.\
그래서 유일한 in-tree 호출처인 `ApplicationContextInitializer` 생성 경로는 동작이 그대로다.

## 5. 검증 — 테스트가 무엇을 고정하나

회귀 테스트는 지금까지 아무도 밟지 않던 여러 이름 경로를 고정한다.

> **회귀 테스트(regression test)** — 한 번 고친 결함이 다시 살아나면 곧바로 실패하도록 남겨 두는 테스트. 수정 전에는 반드시 실패(red)해야 의미가 있다.\
> 예: `reserveMethodNamesWhenMultipleNamesReservesEachName` — 수정 전에는 두 번째 줄에서 예외로 터진다.

```java
@Test
void reserveMethodNamesWhenMultipleNamesReservesEachName() {
	GeneratedClass generatedClass = createGeneratedClass(TEST_CLASS_NAME);
	generatedClass.reserveMethodNames("apply", "test");
	assertThat(generatedClass.getMethods().add("apply", emptyMethodCustomizer).getName()).isEqualTo("apply1");
	assertThat(generatedClass.getMethods().add("test", emptyMethodCustomizer).getName()).isEqualTo("test1");
}
```

이 테스트가 고정하는 것은 두 가지다.\
첫째, 예약 호출이 예외 없이 끝난다는 것.\
수정 전에는 이 줄에서 바로 터졌다.\
둘째, 예약 효과가 이름마다 개별로 걸린다는 것.\
`apply1`과 `test1`은 각 이름의 시퀀스가 이미 한 번 소모됐을 때만 나오는 값이므로, 두 이름이 각각 예약됐음을 결과값으로 증명한다.

기존 테스트 두 개는 그대로 남아 단일 이름 계약을 지킨다.\
`reserveMethodNamesReservesNames`가 이름 하나를 예약하면 다음 발급이 `apply1`임을 고정하고, `reserveMethodNamesWhenNameUsedThrowsException`이 이미 쓰인 이름은 예약할 수 없음을 고정한다.\
즉 새 테스트는 기존 계약을 바꾸지 않고 빈 칸만 채운다.

## 6. 상태와 교훈

PR은 2026년 6월 13일에 열렸고 현재 `status: waiting-for-triage` 라벨이 붙은 OPEN 상태다.\
리뷰 코멘트는 아직 없다.\
대상 코드는 2022년 6월 커밋 `f2d31b7a20c "Migrate AOT tests to use GeneratedClasses and refine/polish AOT APIs"`에서 지금 형태로 들어왔고, 그 뒤로 이 줄은 손대지 않은 채 유지됐다.

교훈 하나는 varargs 파라미터와 루프 변수의 이름이 단수/복수로만 갈릴 때 오타가 컴파일러를 통과한다는 점이다.\
`MethodName.of`가 `String...`을 받으므로 배열을 넘겨도 타입이 맞는다.\
타입 검사로 못 잡는 자리에서는 이름이 유일한 방어선이라, 이런 쌍은 눈으로 볼 때 특히 느리게 읽어야 한다.

> **varargs(가변 인자, `String...`)** — 인자를 0개, 1개, 여러 개 자유롭게 받는 자바 문법. 메서드 안에서는 배열 한 개로 보이므로, 배열 자체를 다시 varargs에 넘겨도 타입 오류가 나지 않는다.\
> 예: `MethodName.of(String... parts)`에 배열 `reservedMethodNames`를 그대로 넘겨도 컴파일이 통과한다.

다른 하나는 API 표면과 실제 사용 범위의 간극이다.\
`reserveMethodNames`는 public varargs API지만 in-tree 호출처는 이름 하나만 넘긴다.\
테스트도 그 사용 패턴만 따라가서, 4년 가까이 아무도 밟지 않은 경로가 남았다.\
varargs·컬렉션 파라미터는 "0개, 1개, 2개 이상"이 각각 다른 경로라고 보고 테스트를 갖추는 편이 안전하다.

## 7. 머지 — "의도가 아니라 버그"라는 판별이 인정됐다

2026-09-04에 Brian Clozel이 `2b5229ff8fa`로 머지했다.\
커밋은 제출한 것 그대로다.\
author와 authored date(2026-06-13)가 유지됐고, 프로덕션 한 줄과 테스트 8줄의 diff가 제출본과 바이트 단위로 같다.\
7.0.x와 main 양쪽에 들어갔고 마일스톤은 7.0.10, 라벨은 `type: bug`와 `in: core`가 붙었다.

> **마일스톤(milestone) / maintenance release** — 이슈·PR을 어느 릴리스에 실을지 묶어 두는 표식과, 새 기능 없이 결함 수정만 담아 내보내는 정기 릴리스.\
> 예: 이 PR의 마일스톤은 7.0.10이고, 다음 maintenance release에 실린다.

남긴 코멘트는 이렇다.

> You were right on the intent @junhyeong9812, this is now fixed for the next
> maintenance release thanks to you!

"intent"라는 단어가 이 PR의 핵심이었다.\
`reserveMethodNames(String...)`에서 배열을 통째로 넘긴 줄이 의도된 동작(여러 이름을 합쳐 한 이름으로 예약)인지 오타인지가 채택 여부를 갈랐고, 메인테이너가 `type: bug` 라벨과 함께 후자로 판정했다.\
다음 maintenance release에 실린다는 말은 이 결함이 릴리스 노트에 올라가는 실사용 버그로 분류됐다는 뜻이다.

같은 "의도 vs 버그" 질문에서 반대 결말이 난 사례가 [#36917](../36917-classfile-array-attributes/README.md)이다.\
그쪽도 판별 자체는 맞았지만(메인테이너가 같은 결함을 직접 고쳤다) 제출물은 채택되지 않았다.\
두 사례를 나란히 놓으면 갈린 지점이 보인다.\
여기서는 결함이 한 줄에 국소적이고 계약 위반이 자명해서 "고칠 것이 하나"였고, 저기서는 다섯 타입이 동시에 빠진 구조적 증상이라 "채워 넣는 패치"가 아니라 "다시 빠지지 않게 만드는 패치"가 요구됐다.\
판별이 맞았다는 것과 그 판별에 맞는 층위의 수정을 냈다는 것은 별개다.

---

연관 ko-docs (모듈 지도): `spring-core/08-AOT-인프라.md`
