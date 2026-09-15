# PR #37082 — Restrict type variable name fallback to subtype narrowing

## 0. 정향

이 PR은 `ResolvableType`이 제네릭 타입 변수를 해석할 때 쓰는 "이름 기반 폴백"의 적용 범위를 좁힌다.\
원래 이 폴백은 `ArrayList`가 `List<String>`을 좁히는 상황처럼 선언이 다른 두 변수를 이름으로 이어주기 위한 장치였는데, 아무 조건 없이 동작한 탓에 이름만 우연히 같은 무관한 타입 변수까지 매칭해 버렸다.\
수정은 "resolve된 타입이 변수 선언 클래스의 상위 타입일 때"라는 조건을 걸어, 진짜 subtype narrowing에만 폴백을 허용한다.\
이 문서는 그 코드가 원래 무엇이고 어떻게 동작하는지부터 따라간다.

> **폴백(fallback)** — 앞선 방법들이 전부 실패했을 때 마지막으로 시도하는 예비 경로.\
> 예: 변수 동일성으로 못 찾으면 "이름이라도 같은 것"을 찾아보는 것이 여기서 말하는 이름 폴백이다.

> **subtype narrowing(하위 타입으로 좁히기)** — 넓은 상위 타입의 제네릭 인자를, 그것을 구현·상속한 좁은 하위 타입이 그대로 물려받는 관계.\
> 예: `List<String>`을 `ArrayList`로 좁히면 `ArrayList`의 `E`도 `String`이어야 한다.

---

## 1. 배경 — 타입 변수 해석과 이름 기반 폴백

`ResolvableType`은 Spring이 자바 리플렉션의 `Type` 계층을 다루기 위해 만든 추상화다.\
자바 리플렉션은 `List<String>` 같은 시그니처를 `ParameterizedType`으로, `T`나 `I` 같은 선언을 `TypeVariable`로 돌려준다.\
문제는 `TypeVariable` 자체에는 값이 없다는 것이다.\
`Create<I, O>` 인터페이스의 메서드 `O create(I body)`에서 파라미터 타입을 물으면 리플렉션은 그냥 `I`를 준다.\
이 `I`가 실제로 무엇인지 알려면 그 변수를 바인딩한 문맥, 즉 `Controller implements Create<Long, Long>` 같은 구현 클래스를 함께 봐야 한다.

> **리플렉션(reflection)** — 실행 중에 클래스·메서드·필드의 선언 정보를 프로그램이 스스로 들여다보는 기능.\
> 예: `TopCreate.class.getMethod("create", Object.class).getGenericParameterTypes()`로 파라미터의 제네릭 선언을 읽는다.

> **ParameterizedType(파라미터화 타입)** — `List<String>`처럼 제네릭 인자가 실제로 채워진 타입을 리플렉션이 표현하는 방식.\
> 예: `TopSearch<String, Long>`은 raw 클래스 `TopSearch`와 실인자 배열 `[String, Long]`을 함께 들고 있다.

> **TypeVariable(타입 변수)** — `T`, `I`, `E`처럼 아직 값이 정해지지 않은 제네릭 자리 이름 그 자체.\
> 예: `Create<I, O>`의 `I`는 `Controller implements Create<Long, Long>`이라는 문맥을 봐야 `Long`으로 풀린다.

이 "변수를 문맥에 대고 값으로 바꾸는" 일이 타입 변수 해석이다.\
Spring에서는 두 계층이 나눠 맡는다.\
바깥쪽은 `GenericTypeResolver.resolveType(Type, Class)`로, 제네릭 타입과 문맥 클래스를 받아 최대한 치환한 `Type`을 돌려준다.\
안쪽은 `ResolvableType`의 `VariableResolver` 체인으로, 실제 매칭을 수행한다.

> **VariableResolver(변수 해석기)** — "내가 모르는 타입 변수는 이 사람에게 물어봐"라고 위임할 상대를 나타내는 인터페이스.\
> 예: `ResolvableType.forType(ArrayList.class, listOfString)`은 `listOfString`을 해석기로 붙여, `ArrayList`의 `E`를 `List<String>`에게 되묻게 한다.

실사용처는 얕지 않다.\
이슈 gh-36890이 보고한 경로는 `AbstractJackson2HttpMessageConverter#getJavaType(Type, Class)`다.\
Spring MVC가 `@RequestBody` 파라미터를 어떤 타입으로 역직렬화할지 정할 때 이 메서드를 거치고, 그 안에서 `GenericTypeResolver.resolveType`을 호출한다.\
타입 변수 해석이 틀리면 컨트롤러가 JSON 본문을 엉뚱한 타입으로 읽어 400을 내뱉는다.

> **역직렬화(deserialization)** — 바이트나 텍스트로 온 데이터를 프로그램 안의 객체로 되돌리는 일.\
> 예: HTTP 본문 `{"id":7}`을 `Long`으로 읽을지 `String`으로 읽을지가 여기서 정해진다.

핵심 함수는 `ResolvableType.resolveVariable(TypeVariable<?>)`다.\
이 메서드는 자기 자신이 `ParameterizedType`일 때 그 타입이 들고 있는 실인자 배열과 raw 클래스의 타입 파라미터 배열을 짝지어, 찾는 변수와 일치하는 자리를 골라낸다.\
매칭 방식이 이 PR의 전부다.

> **raw 클래스(raw class)** — 제네릭 인자를 떼어 낸, 타입의 뼈대가 되는 클래스 자체.\
> 예: `TopSearch<String, Long>`의 raw 클래스는 `TopSearch`이고, 여기서 선언된 변수 배열 `[I, O]`를 꺼낸다.

---

## 2. 수정 전 동작 방식

수정 전 `resolveVariable`은 네 단계를 순서대로 시도한다.\
아래는 `spring-core/src/main/java/org/springframework/core/ResolvableType.java`의 실제 코드다.

```java
private @Nullable ResolvableType resolveVariable(TypeVariable<?> variable) {
	TypeVariable<?> variableToCompare = SerializableTypeWrapper.unwrap(variable);
	if (this.type instanceof TypeVariable) {
		return resolveType().resolveVariable(variableToCompare);
	}
	if (this.type instanceof ParameterizedType parameterizedType) {
		Class<?> resolved = resolve();
		if (resolved == null) {
			return null;
		}
		TypeVariable<?>[] variables = resolved.getTypeParameters();
		Type[] typeArguments = parameterizedType.getActualTypeArguments();
		for (int i = 0; i < variables.length; i++) {
			if (ObjectUtils.nullSafeEquals(variables[i], variableToCompare)) {
				return forType(typeArguments[i], this.variableResolver);
			}
		}
		Type ownerType = parameterizedType.getOwnerType();
		if (ownerType != null) {
			return forType(ownerType, this.variableResolver).resolveVariable(variableToCompare);
		}
		// Fallback: comparison by variable name, independent of generic declaration context.
		for (int i = 0; i < variables.length; i++) {
			if (ObjectUtils.nullSafeEquals(variables[i].getName(), variableToCompare.getName())) {
				return forType(typeArguments[i], this.variableResolver);
			}
		}
	}
	...
}
```

`@RequestBody` 한 번이 이 메서드에 닿기까지, 그리고 그 안에서 값이 갈라지는 자리는 다음과 같다.

```text
GenericTypeResolver.resolveType(I, TopController.class)   "이 변수를 이 문맥에서 풀어 줘"
        |
        v
GenericTypeResolver.resolveVariable(I, TopController)     후보를 순서대로 시도
        |   자기 자신 -> superType -> 인터페이스 선언 순서
        v
DefaultVariableResolver.resolveVariable(I)                후보 하나를 통째로 되묻는 어댑터
        |
        v
ResolvableType.resolveVariable(I)          <- 실제 매칭이 일어나는 곳
        |
        +--[1] 동일성 비교  variables[i].equals(I) ?      이름 + 선언 주체를 함께 본다
        |        일치 -> typeArguments[i] 를 답으로 반환   (정상 경로)
        |
        +--[2] ownerType != null ?                       중첩 선언이면 바깥으로 올라가 재귀
        |        있으면 -> 결과가 무엇이든 즉시 return      (여기서 끝나면 [3] 미도달)
        |
        +--[3] 이름만 비교  getName() 이 같은가 ?          선언 문맥을 보지 않는다
                 일치 -> typeArguments[i] 를 답으로 반환   <- 이 PR 이 조건을 거는 자리
```

같은 메서드 안에서 [1]은 선언 주체까지 보고 [3]은 이름만 보며, 그 둘 사이를 가르는 유일한 방벽이 [2]의 `ownerType != null`이라는 우연한 조건이다.

순서를 서사로 풀면 이렇다.\
먼저 변수 **동일성**으로 맞춰 본다.\
`variables[i]`와 `variableToCompare`를 `equals`로 비교하는데, `TypeVariable`의 equality는 이름과 `getGenericDeclaration()`을 함께 본다.\
즉 "같은 선언에서 나온 같은 이름의 변수"만 통과한다.\
이게 정확한 매칭이며 정상 경로다.

> **getGenericDeclaration()** — 이 타입 변수를 선언한 주체를 돌려주는 JDK 메서드로, `Class`·`Method`·`Constructor` 셋 중 하나다.\
> 예: `ArrayList<E>`의 `E`는 `class java.util.ArrayList`를, `<T> T convert(...)`의 `T`는 그 메서드 자체를 돌려준다.

동일성으로 못 찾으면 **owner 타입**으로 재귀한다.\
중첩 타입의 경우 바깥 클래스가 타입 변수를 선언했을 수 있으므로, 바깥으로 한 단계 올라가 다시 물어보는 것이다.\
여기서 중요한 점은 이 분기가 `return`이라는 것이다.\
owner가 있으면 그 결과가 무엇이든 즉시 반환되고, 뒤의 폴백은 아예 도달하지 않는다.

> **owner 타입(owner type)** — 어떤 타입이 다른 타입 안에 중첩 선언돼 있을 때 그 바깥 타입. 최상위 선언이면 `null`이다.\
> 예: `class Tests { interface Search<I,O> {} }`의 `Search`는 owner가 `Tests`지만, 파일 최상위의 `interface TopSearch<I,O>`는 owner가 `null`이다.

owner도 없으면 마지막으로 **이름만** 비교한다.\
선언 문맥을 무시하고 문자열이 같으면 그 자리의 실인자를 답으로 준다.\
주석이 "independent of generic declaration context"라고 스스로 밝히고 있다.

이름 폴백은 실수로 들어간 코드가 아니다.\
존재 이유가 분명한 케이스가 있다.\
`ResolvableTypeTests.narrow()`가 그 케이스다.

```java
ResolvableType type = ResolvableType.forField(Fields.class.getField("stringList"));
ResolvableType narrow = ResolvableType.forType(ArrayList.class, type);
assertThat(narrow.getGeneric().resolve()).isEqualTo(String.class);
```

`List<String>` 필드를 owner로 삼아 raw `ArrayList`를 감싼 뒤, 그 제네릭이 `String`으로 풀리기를 기대한다.\
그런데 `ArrayList`의 `E`와 `List`의 `E`는 자바에서 **서로 다른 `TypeVariable` 인스턴스**다.\
선언이 각각 `ArrayList`와 `List`이기 때문이다.\
동일성 비교로는 절대 매칭되지 않는다.\
그럼에도 답이 `String`이어야 하는 이유는 `ArrayList`가 `List`를 구현하며 `E`를 그대로 물려받기 때문이다.\
이 "상속을 통한 이름 승계"를 건져 내는 장치가 바로 이름 폴백이었다.

참고로 이 폴백 자체는 gh-36890 수정(커밋 `9130ded96f4`, Juergen Hoeller)이 도입했다.\
그 이전에는 첫 번째 루프가 아예 이름 비교였고, 그 커밋이 첫 루프를 동일성 비교로 승격시키면서 `narrow()`가 깨지지 않도록 이름 비교를 뒤쪽 폴백으로 밀어 둔 것이다.

---

## 3. 무엇이 문제였나

이름 폴백에 조건이 없으니, 상속 관계가 전혀 없는 형제 인터페이스끼리도 이름이 같으면 매칭됐다.\
gh-36890의 원 시나리오가 정확히 그 모양이다.

```java
interface TopSearch<I, O> {}
interface TopCreate<I, O> { O create(I body); }
class TopController implements TopSearch<String, Long>, TopCreate<Long, Long> {}
```

`TopCreate`의 `I`를 `TopController` 문맥에 대고 해석하면 답은 `Long`이어야 한다.\
실제로는 `String`이 나온다.\
경로를 따라가 보자.\
`GenericTypeResolver.resolveType`은 문맥 클래스에 제네릭이 없으면 상위 타입과 인터페이스를 순서대로 훑는다.

```java
for (ResolvableType ifc : contextType.getInterfaces()) {
	resolvedType = resolveVariable(typeVariable, ifc);
	if (resolvedType != ResolvableType.NONE) {
		return resolvedType;
	}
}
```

첫 인터페이스는 `TopSearch<String, Long>`이다.\
여기에 `TopCreate`의 `I`를 물어본다.\
동일성 비교는 실패한다.\
선언이 `TopSearch`와 `TopCreate`로 다르기 때문이다.\
다음으로 owner를 보는데, `TopSearch`는 최상위 인터페이스라 `getOwnerType()`이 `null`이다.\
그래서 이름 폴백까지 흘러가고, `TopSearch`의 첫 파라미터 이름이 `"I"`이므로 매칭에 성공해 `String`을 돌려준다.\
루프는 `TopCreate`에 닿지도 못하고 끝난다.

같은 입력이 수정 전후로 어떻게 갈리는지 나란히 놓으면 이렇다.

```text
수정 전 (이름 폴백에 조건 없음)              수정 후 (subtype narrowing 만 허용)
+-----------------------------------+      +-----------------------------------+
| ifc[0] TopSearch<String, Long>    |      | ifc[0] TopSearch<String, Long>    |
|   [1] 동일성 -> 실패              |      |   [1] 동일성 -> 실패              |
|   [2] owner = null -> 통과        |      |   [2] owner = null -> 통과        |
|   [3] 이름 "I" == "I" -> String   |      |   [3] 게이트: TopSearch 는        |
|        (즉시 return)              |      |       TopCreate 의 상위가 아니다  |
|                                   |      |       -> 폴백 건너뜀 -> null      |
+-----------------------------------+      +-----------------------------------+
| ifc[1] TopCreate<Long, Long>      |      | ifc[1] TopCreate<Long, Long>      |
|   도달하지 못함                   |      |   [1] 동일성 -> 성공 -> Long      |
+-----------------------------------+      +-----------------------------------+
  결과: String  (오답)                       결과: Long  (정답)
```

수정은 오답을 옳은 답으로 바꾸는 것이 아니라, 오답 대신 "모름"을 내놓아 상위 루프가 다음 후보까지 가도록 길을 비켜 주는 것이다.

여기서 왜 gh-36890 수정 이후에도 이게 남았는지가 갈린다.\
그 수정이 추가한 회귀 테스트 `resolveTypeAgainstSameNamedVariables()`는 `Search`/`Create`/`Controller`를 `GenericTypeResolverTests` 안의 **중첩 타입**으로 선언했다.\
중첩 타입의 `ParameterizedType`은 owner가 바깥 클래스이므로 `null`이 아니다.\
그래서 owner 분기에서 즉시 반환되고 이름 폴백은 실행되지 않는다.\
반환값이 `null`이라 루프는 다음 인터페이스인 `Create<Long, Long>`으로 넘어가고, 거기서 동일성 매칭이 성공해 `Long`이 나온다.\
테스트는 통과하지만, 통과 이유가 "이름 폴백이 고쳐져서"가 아니라 "이름 폴백에 도달하지 못해서"였던 셈이다.

> **회귀 테스트(regression test)** — 한 번 고친 결함이 다시 살아나지 않는지 지키려고 남겨 두는 테스트.\
> 예: gh-36890이 고쳐진 뒤 같은 증상이 재발하면 `resolveTypeAgainstSameNamedVariables()`가 빨갛게 되도록 심어 뒀다.

중첩이냐 최상위냐 하나로 실행되는 코드 줄이 달라지는 모습을 나란히 두면 이렇다.

```text
중첩 선언 (기존 회귀 테스트)                  최상위 선언 (실제 애플리케이션)
+-----------------------------------+      +-----------------------------------+
| class Tests {                     |      | interface TopSearch<I, O> {}      |
|   interface Search<I, O> {}       |      | interface TopCreate<I, O> {}      |
| }                                 |      |                                   |
| ownerType = class Tests           |      | ownerType = null                  |
+-----------------------------------+      +-----------------------------------+
| [2] owner 분기에서 즉시 return    |      | [2] 분기를 타지 않고 통과         |
| [3] 이름 폴백 -> 실행되지 않음    |      | [3] 이름 폴백 -> 실행된다         |
+-----------------------------------+      +-----------------------------------+
  테스트 초록. 단, 대상 코드 미실행           보고자가 겪은 오답이 그대로 남는다
```

같은 구조인데 선언 위치 하나로 갈라지므로, 픽스처를 중첩으로 둔 순간 회귀 테스트가 지키려던 코드 줄을 밟지 못했다.

리플렉션이 실제로 그렇게 동작하는지 JDK만으로 확인했다.

```text
TOP  TopSearch ownerType=null
TOP  TopCreate ownerType=null
NEST Probe$Search ownerType=class Probe
NEST Probe$Create ownerType=class Probe
```

같은 구조가 중첩이냐 최상위냐에 따라 다른 답을 내는 것이다.\
그리고 실제 애플리케이션의 인터페이스는 보통 각자 파일에 최상위로 선언되므로, 이슈에 보고된 REST 컨트롤러 형태는 여전히 깨진 채였다.

두 번째 증상은 메서드 레벨 타입 변수의 shadowing이다.

```java
class TopRepo<T> {
	<T> T convert(Object o) { return null; }
}
class TopStringRepo extends TopRepo<String> {}
```

> **shadowing(가리기)** — 안쪽 범위에서 같은 이름을 다시 선언해 바깥 범위의 이름을 보이지 않게 하는 것.\
> 예: `class TopRepo<T>` 안의 `<T> T convert(...)`에서 메서드의 `T`는 클래스의 `T`를 가리는 완전히 별개의 변수다.

메서드의 `<T>`는 클래스의 `T`를 가린다.\
자바 언어 규칙상 둘은 완전히 별개이고, 메서드 `T`는 호출 시점에야 정해지므로 클래스 문맥만으로는 해석될 수 없다.\
그런데 이름 폴백은 `TopRepo<String>`에서 `"T"`를 찾아내 `String`을 돌려줬다.\
클래스 레벨 인자가 메서드 레벨 변수로 새어 들어간 것이다.\
이 역시 `TopRepo`가 최상위라 owner가 `null`이기에 도달하는 경로다.

같은 입력에 대해 수정 전후가 내놓는 값은 다음과 같다.

| 해석 대상 | 수정 전 | 수정 후 |
|---|---|---|
| `TopCreate.I` @ `TopController` | `String` | `Long` |
| `TopRepo#convert`의 메서드 `T` @ `TopStringRepo` | `String` | 미해석 (`TypeVariable` 그대로) |
| `ArrayList.E` @ `List<String>` | `String` | `String` |

---

## 4. 수정 해설 — subtype narrowing 제한

수정은 이름 폴백을 없애지 않는다.\
없애면 `narrow()`가 깨진다.\
대신 폴백이 정당한 유일한 조건을 명시적으로 건다.

```java
// Fallback: comparison by variable name, limited to a subtype narrowing the
// resolved supertype (for example, ArrayList narrowing List<String>). A name
// match against an unrelated declaration must not be accepted (gh-36890).
if (variableToCompare.getGenericDeclaration() instanceof Class<?> declaringClass &&
		resolved.isAssignableFrom(declaringClass)) {
	for (int i = 0; i < variables.length; i++) {
		if (ObjectUtils.nullSafeEquals(variables[i].getName(), variableToCompare.getName())) {
			return forType(typeArguments[i], this.variableResolver);
		}
	}
}
```

조건은 두 개이고 각각 앞 절의 증상 하나씩을 막는다.

> **술어(predicate)** — 참/거짓만 답하는 조건식. 여기서는 "이 폴백을 써도 되는가"를 묻는 문지기 역할이다.\
> 예: `resolved.isAssignableFrom(declaringClass)`는 "지금 보는 타입이 변수 선언 클래스의 상위인가"를 묻는 술어다.

첫째, `getGenericDeclaration() instanceof Class<?>`는 찾는 변수가 **클래스나 인터페이스가 선언한 변수**임을 요구한다.\
자바에서 `getGenericDeclaration()`은 `Class`, `Method`, `Constructor` 중 하나를 돌려준다.\
메서드 레벨 변수는 `Method`를 돌려주므로 이 검사에서 걸러진다.\
shadowing 사례가 여기서 차단된다.

둘째, `resolved.isAssignableFrom(declaringClass)`는 지금 보고 있는 파라미터화 타입의 raw 클래스가 **변수 선언 클래스의 상위 타입**임을 요구한다.\
이것이 "subtype narrowing"이라는 표현의 의미다.\
`ArrayList`의 `E`를 `List<String>`에 대고 물을 때 `List.isAssignableFrom(ArrayList)`는 참이므로, 좁히는 쪽이 넓히는 쪽의 인자를 이름으로 물려받는 것이 타당하다.\
반대로 `TopCreate`의 `I`를 `TopSearch<String, Long>`에 물을 때 `TopSearch.isAssignableFrom(TopCreate)`는 거짓이다.\
두 인터페이스는 형제일 뿐 상속 관계가 없으므로 이름이 같다는 사실에 아무 의미가 없다.

> **isAssignableFrom** — `A.isAssignableFrom(B)`는 "B 타입의 값을 A 타입 자리에 넣을 수 있나", 즉 A가 B의 상위 타입인가를 묻는다.\
> 예: `List.isAssignableFrom(ArrayList)`는 참이고, `TopSearch.isAssignableFrom(TopCreate)`는 거짓이다.

세 케이스를 같은 게이트에 통과시켜 보면 통과/차단이 이렇게 갈린다.

```text
                       선언 주체가 Class ?   resolved 가 상위 ?   폴백
  ArrayList.E @ List<String>     예              예                통과 -> String
  TopCreate.I @ TopSearch<..>    예             아니오             차단 -> null
  메서드 T @ TopRepo<String>    아니오(Method)   (검사 안 함)       차단 -> null
```

두 술어를 모두 통과하는 것은 진짜 상속 관계인 첫 줄뿐이고, 나머지 둘은 서로 다른 술어에서 각각 걸린다.

리플렉션 값으로도 확인된다.

```text
ArrayList E decl=class java.util.ArrayList
List assignableFrom ArrayList=true
TopCreate I decl=interface TopCreate
TopSearch assignableFrom TopCreate=false
convert returnType decl=java.lang.Object TopRepo.convert(java.lang.Object)
```

조건이 걸리면 폴백은 그냥 건너뛰어지고 `resolveVariable`은 뒤쪽 분기로 흘러 결국 `null`을 반환한다.\
`null`은 "여기서는 못 찾았다"는 뜻이므로, `GenericTypeResolver`의 인터페이스 루프가 다음 후보인 `TopCreate<Long, Long>`으로 넘어가 동일성 매칭에 성공한다.\
즉 수정은 잘못된 답을 만들어 내는 대신 "모름"을 반환하게 하고, 상위 계층의 탐색이 정답을 찾도록 길을 비켜 준다.

shadowing 사례에서는 어떤 후보도 답을 주지 못하므로 최종적으로 미해석 상태가 된다.\
`GenericTypeResolver.resolveType`은 `ResolvableType.forVariableBounds(typeVariable)`로 bound 폴백을 시도하는데, 메서드 `T`의 bound는 `Object`뿐이고 `resolveBounds`는 `bounds[0] == Object.class`일 때 `null`을 돌려주므로 결과가 `NONE`이다.\
그래서 마지막 줄의 `return genericType`이 실행되어 `TypeVariable`이 그대로 나온다.\
해석 불가를 해석 불가로 정직하게 보고하는 셈이다.

> **bound(상한)** — 타입 변수가 가질 수 있는 타입의 한계를 `extends`로 적어 둔 것.\
> 예: `<T extends Number>`의 bound는 `Number`이고, 아무것도 안 적은 `<T>`의 bound는 `Object`뿐이다.

---

## 5. 검증 — 테스트가 무엇을 고정하나

`spring-core/src/test/java/org/springframework/core/GenericTypeResolverTests.java`에 테스트 세 개가 추가됐다.\
각각이 고정하는 성질이 다르다.

```java
@Test  // gh-36890
void resolveTypeAgainstSameNamedVariablesInTopLevelDeclarations() {
	Type resolvedType = resolveType(
			method(TopCreate.class, "create", Object.class).getGenericParameterTypes()[0], TopController.class);
	assertThat(resolvedType).isEqualTo(Long.class);
}
```

첫째는 형제 인터페이스 케이스를 **최상위 선언**으로 재현한다.\
이 테스트가 기존 `resolveTypeAgainstSameNamedVariables()`와 구조가 같으면서도 새로 필요한 이유가 3절의 owner 분기다.\
그래서 헬퍼 타입 `TopSearch`, `TopCreate`, `TopController`를 테스트 클래스 안이 아니라 **파일 최상위**에 선언한다.\
중첩 타입으로 두면 owner가 붙어 이 회귀를 재현하지 못한다.\
테스트 픽스처의 배치 자체가 검증 조건인 드문 사례다.

> **픽스처(fixture)** — 테스트가 쓰려고 미리 준비해 둔 고정 데이터나 헬퍼 타입.\
> 예: 이 PR의 `TopSearch`/`TopCreate`/`TopController` 세 타입이 그 픽스처이며, 선언 위치까지 의미를 갖는다.

```java
@Test  // gh-36890
void resolveMethodLevelTypeVariableIsNotShadowedByClassVariable() {
	Type resolvedType = resolveType(
			method(TopRepo.class, "convert", Object.class).getGenericReturnType(), TopStringRepo.class);
	assertThat(resolvedType).isInstanceOf(TypeVariable.class);
}
```

둘째는 shadowing 케이스를 고정한다.\
주목할 점은 단언이 "값이 틀렸다"가 아니라 "타입 변수로 남아 있다"라는 것이다.\
잘못된 값 대신 미해석을 반환하는 것이 의도된 동작임을 명시한다.

```java
@Test  // gh-36890
void resolveTypeVariableByNameWhenNarrowingParameterizedSupertype() {
	// A raw subtype narrowing a parameterized supertype must still carry the argument
	// across by variable name, even though Box<E> and Container<E> are distinct declarations.
	ResolvableType containerOfString = ResolvableType.forClassWithGenerics(Container.class, String.class);
	ResolvableType box = ResolvableType.forType(Box.class, containerOfString);
	assertThat(box.getGeneric().resolve()).isEqualTo(String.class);
}
```

셋째는 방향이 반대인 **긍정 테스트**다.\
앞의 두 테스트만 있으면 "이름 폴백을 통째로 삭제"라는 오답도 통과한다.\
이 테스트는 정당한 subtype narrowing 경로가 살아 있음을 고정해, 수정이 폴백 제거가 아니라 폴백 제한임을 코드로 못박는다.\
주석이 `Box<E>`와 `Container<E>`가 서로 다른 선언임을 명시하는 이유도 그것이다.

> **긍정 테스트(positive guard)** — 결함을 재현하는 대신, 수정 뒤에도 **남아 있어야 할** 동작이 남았는지를 지키는 테스트.\
> 예: 이름 폴백을 통째로 지우는 오답을 이 테스트 하나가 잡아낸다.

기존 자산으로는 `ResolvableTypeTests.narrow()`와 gh-34386, gh-36890의 테스트가 그대로 통과한다.\
`narrow()`는 셋째 테스트와 같은 성질을 JDK 타입(`ArrayList`/`List`)으로 검증하므로, 실전 타입과 최소 픽스처 양쪽에서 회귀가 잡힌다.

---

## 6. 상태와 교훈

PR #37082는 2026-08-15 기준 **OPEN**이며 리뷰나 코멘트는 아직 없다.\
선행 수정인 gh-36890(커밋 `9130ded96f4`)은 이미 머지되어 있고, 이 PR은 그 후속으로 같은 이슈 번호를 참조한다.

교훈 하나는 **회귀 테스트의 픽스처 배치가 검증 범위를 결정한다**는 것이다.\
gh-36890 수정은 정확한 성질을 정확한 코드로 고쳤지만, 회귀 테스트를 중첩 타입으로 짠 탓에 문제의 코드 경로를 실행조차 하지 않았다.\
테스트는 초록이었고 이슈는 닫혔으나, 정작 보고자가 겪은 최상위 인터페이스 구성은 그대로였다.\
테스트가 통과했다는 사실과 그 테스트가 대상 경로를 밟았다는 사실은 별개이며, 방어선이 되어야 할 테스트일수록 "이 테스트를 실패시키려면 어떤 코드를 되돌려야 하나"를 되물어 확인할 값어치가 있다.

다른 하나는 **폴백을 다룰 때는 그것이 왜 있는지부터 복원해야 한다**는 것이다.\
이름만 보고 매칭하는 코드는 첫눈에 명백한 버그처럼 보이지만, 삭제하면 `narrow()`가 깨진다.\
폴백이 정당한 케이스(subtype narrowing)와 부당한 케이스(형제 선언, 메서드 레벨 shadowing)를 가르는 술어를 찾아 그것만 통과시키는 것이 옳은 수정이었고, 그 술어를 코드로 고정하는 것이 긍정 테스트의 역할이었다.\
넓은 로직을 좁힐 때는 좁힌 뒤에도 남아야 할 동작을 함께 테스트에 남겨야 다음 사람이 다시 넓히거나 지우지 않는다.

---

연관 ko-docs (모듈 지도): `spring-core/04-타입-리플렉션과-제네릭.md`
