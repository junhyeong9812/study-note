# PR #37082 — 테스트 해설 (테스트 하나하나)

> PR #37082 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

`GenericTypeResolverTests`에 세 건이 추가됐다. 결론부터 말하면 **red 2건, 항상 green인
가드 1건**이다. red 두 건은 이름 폴백이 만들어 내던 두 종류의 오답(형제 인터페이스 매칭,
메서드 레벨 변수 shadowing)을 하나씩 재현하고, 가드 한 건은 그 폴백이 정당하게 필요한
유일한 경우(subtype narrowing)가 살아남았음을 고정한다. 이 PR에서는 테스트 코드만큼
**픽스처를 어디에 선언했는지**가 중요하므로 마지막 fixture 절을 함께 읽어야 한다.
red/green 판별은 실행 결과가 아니라 diff 논리 — 수정 전 이름 폴백에 아무 조건이
없었다는 사실 — 에서 유도했다.

## 1. 최상위 형제 인터페이스 — red

첫 테스트는 하나의 컨트롤러가 동명 타입 변수를 쓰는 인터페이스 둘을 구현하는 구조를 최상위 선언으로 재현한다.

```java
@Test  // gh-36890
void resolveTypeAgainstSameNamedVariablesInTopLevelDeclarations() {
	Type resolvedType = resolveType(
			method(TopCreate.class, "create", Object.class).getGenericParameterTypes()[0], TopController.class);
	assertThat(resolvedType).isEqualTo(Long.class);
}
```

- **주장**: `TopCreate`의 파라미터 타입 변수 `I`를 `TopController` 문맥에서 해석하면
  `TopCreate<Long, Long>`의 첫 인자인 `Long`이어야 한다.
- **픽스처가 흉내 내는 것**: `TopSearch`/`TopCreate`/`TopController`는 gh-36890에
  보고된 REST 컨트롤러 구조의 최소형이다. 하나의 컨트롤러가 제네릭 인터페이스 둘을
  구현하고, 그 둘이 우연히 같은 이름의 타입 변수(`I`, `O`)를 쓰는 형태다. 실무에서는
  `@RequestBody` 파라미터 타입 결정이 `AbstractJackson2HttpMessageConverter#getJavaType`을
  거쳐 이 해석에 의존하므로, 오답은 곧 역직렬화 실패로 나타난다.
- **fix 전 결과와 이유**: red다. `GenericTypeResolver.resolveType`이 구현 인터페이스를
  순서대로 훑는데, 첫 후보인 `TopSearch<String, Long>`에서 동일성 비교는 실패하고
  (선언이 `TopSearch`와 `TopCreate`로 다르다), `TopSearch`는 최상위라
  `getOwnerType()`이 `null`이라 owner 재귀도 건너뛴다. 그래서 조건 없는 이름 폴백까지
  흘러가 `"I"` 이름이 일치하는 자리의 실인자 `String`을 반환한다. 루프는 `TopCreate`에
  닿지 못하고 끝나므로 결과는 `String`, 기대값 `Long`과 달라 단언 실패다.
- **fix 후**: `TopSearch.isAssignableFrom(TopCreate)`가 거짓이라 폴백이 건너뛰어지고
  `null`이 반환된다. `null`은 "여기서는 못 찾았다"는 뜻이므로 루프가 다음 후보인
  `TopCreate<Long, Long>`으로 넘어가 동일성 매칭에 성공하고 `Long`이 나온다.
- **역할**: 이 PR의 주된 재현. 기존 회귀 테스트 `resolveTypeAgainstSameNamedVariables()`와
  구조는 같지만 픽스처가 최상위라는 점만 다르고, 그 한 가지 차이가 문제의 코드 경로를
  실제로 밟게 만든다. 자세한 이유는 fixture 절에 적었다.

## 2. 메서드 레벨 변수 shadowing — red

둘째 테스트는 메서드가 선언한 타입 변수가 클래스 변수를 가리는 구조에서, 해석이 일어나지 않아야 함을 고정한다.

```java
@Test  // gh-36890
void resolveMethodLevelTypeVariableIsNotShadowedByClassVariable() {
	Type resolvedType = resolveType(
			method(TopRepo.class, "convert", Object.class).getGenericReturnType(), TopStringRepo.class);
	assertThat(resolvedType).isInstanceOf(TypeVariable.class);
}
```

- **주장**: 메서드가 선언한 `<T>`는 클래스의 `T`와 별개이므로, 클래스 문맥만으로는
  해석될 수 없고 `TypeVariable`인 채로 남아야 한다.
- **픽스처가 흉내 내는 것**: `TopRepo<T>` 안의 `<T> T convert(Object o)`는 자바에서
  흔한 shadowing 형태다. 제네릭 리포지토리나 매퍼가 클래스 타입 파라미터와 같은 글자를
  메서드에서 다시 쓰는 코드가 그대로 이 모양이 된다. `TopStringRepo extends TopRepo<String>`은
  그 클래스 변수에 실인자를 채워 넣은 하위 타입이다.
- **fix 전 결과와 이유**: red다. 상위 타입 `TopRepo<String>`에 대고 메서드의 `T`를
  물으면 동일성 비교는 실패하고(선언이 `Method`와 `Class`로 다르다), `TopRepo`가
  최상위라 owner도 `null`이다. 이름 폴백이 `"T"` 일치를 찾아 `String`을 돌려주므로
  결과는 `String.class`이고, `isInstanceOf(TypeVariable.class)` 단언이 깨진다.
  클래스 레벨 인자가 메서드 레벨 변수로 새어 들어간 것이다.
- **fix 후**: `variableToCompare.getGenericDeclaration()`이 `Method`이므로
  `instanceof Class<?>` 검사에서 걸러져 폴백이 실행되지 않는다. 어느 후보도 답을 주지
  못하고, bound 폴백도 `Object`뿐이라 `NONE`을 돌려주므로 원래의 `TypeVariable`이
  그대로 반환된다.
- **단언의 형태가 값이 아닌 이유**: "무엇으로 해석되어야 한다"가 아니라 "해석되지 않은
  채여야 한다"가 계약이다. 메서드 타입 변수는 호출 시점에야 정해지므로 클래스 문맥만
  보고 답을 만들어 내는 것 자체가 오답이다. `isInstanceOf(TypeVariable.class)`는
  **틀린 값 대신 모름을 반환하는 것이 의도된 동작**임을 코드로 못박는다.
- **1번과 별도 테스트인 이유**: 두 red는 fix에서 추가된 조건 두 개와 일대일로 대응한다.
  1번은 `resolved.isAssignableFrom(declaringClass)`가, 2번은
  `getGenericDeclaration() instanceof Class<?>`가 없으면 실패한다. 조건 하나만 넣은
  불완전한 수정을 각각 잡아낸다.

## 3. subtype narrowing 보존 — 항상 green (양성 가드)

셋째 테스트는 방향이 반대로, 이름 폴백이 정당하게 필요한 유일한 경우가 살아남았는지를 본다.

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

- **주장**: raw `Box`를 `Container<String>`을 owner로 감싸면 `Box`의 `E`가 `String`으로
  풀려야 한다. `Box<E>`와 `Container<E>`는 서로 다른 선언이므로 이 매칭은 오직 이름
  폴백으로만 성립한다.
- **픽스처가 흉내 내는 것**: `Container`/`Box`는 JDK의 `List`/`ArrayList` 관계를
  최소 형태로 옮긴 것이다. 실전 타입 대신 두 줄짜리 픽스처를 쓴 덕분에 "상속을 통한
  이름 승계"라는 성질만 남고 컬렉션 API의 잡음이 사라진다.
- **fix 전 green인 이유**: 폴백에 조건이 없으니 이름만 같으면 통과했다. 즉 수정 전에도
  이 테스트는 통과한다.
- **존재 이유는 fix 후에 있다**: 앞의 두 red만 있으면 "이름 폴백을 통째로 삭제"라는
  오답도 전부 통과한다. 이 테스트가 정당한 폴백 경로가 살아 있음을 고정해, 이 PR이
  폴백 **제거**가 아니라 폴백 **제한**임을 코드로 못박는다. 새 조건에 대입하면
  `Box`의 `E`는 선언이 `Class`인 `Box`이고 `Container.isAssignableFrom(Box)`가 참이므로
  폴백이 허용된다 — 그 두 조건이 정확히 이 경우만 통과시키도록 골라졌음을 이 테스트가
  증명한다.
- **분류**: ../37153/guard-tests.md의 용어로는 양성 가드다. 넓은 로직을 좁힐 때 좁힌
  뒤에도 남아야 할 동작을 함께 고정해, 다음 사람이 다시 넓히거나 지우지 않게 만든다.
- **기존 자산과의 관계**: `ResolvableTypeTests.narrow()`가 같은 성질을 JDK 타입
  (`ArrayList`/`List`)으로 이미 검증한다. 이 테스트는 그 성질을 이 PR의 문맥에서
  최소 픽스처로 다시 세운 것이며, 실전 타입과 최소 픽스처 양쪽에서 회귀가 잡히도록
  이중으로 배치한 셈이다.

## fixture

이 PR에서 픽스처의 **배치 자체가 검증 조건**이다. 여섯 개 타입이 모두
`GenericTypeResolverTests.java` 파일의 **최상위**에, 테스트 클래스 바깥에 선언됐다.

```java
interface TopSearch<I, O> {
}

interface TopCreate<I, O> {

	default O create(I body) {
		return null;
	}
}

class TopController implements TopSearch<String, Long>, TopCreate<Long, Long> {
}

class TopRepo<T> {

	<T> T convert(Object o) {
		return null;
	}
}

class TopStringRepo extends TopRepo<String> {
}

interface Container<E> {
}

class Box<E> implements Container<E> {
}
```

기존 회귀 테스트가 쓰는 `Search`/`Create`/`Controller`는 테스트 클래스 **안의 중첩
타입**이다. 중첩 타입의 `ParameterizedType`은 `getOwnerType()`이 바깥 클래스를 돌려주므로
`null`이 아니고, 그러면 `resolveVariable`이 owner 분기에서 즉시 반환해 이름 폴백에
아예 도달하지 못한다. 그래서 gh-36890의 회귀 테스트는 통과했지만 그 통과의 이유가
"폴백이 고쳐져서"가 아니라 "폴백을 실행하지 않아서"였다. `Top` 접두사를 단 최상위 쌍을
새로 만든 것은 이름 충돌을 피하기 위해서만이 아니라, owner가 `null`인 경로를 강제로
밟게 하기 위해서다. 중첩으로 옮기는 순간 1·2번은 red를 잃고 무의미해진다.

`TopCreate.create`가 `default` 메서드인 것은 인터페이스에 본문을 두어야 하기 때문이고,
`TopRepo.convert`가 `null`을 반환하는 것도 마찬가지로 구현 내용이 무의미하기 때문이다.
세 테스트 모두 리플렉션으로 시그니처만 읽으므로 본문은 실행되지 않는다.

헬퍼 두 개는 기존 것을 그대로 쓴다.

```java
private static Method method(Class<?> target, String methodName, Class<?>... parameterTypes) {
	Method method = findMethod(target, methodName, parameterTypes);
	assertThat(method).describedAs(target.getName() + "#" + methodName).isNotNull();
	return method;
}
```

`method(...)`는 리플렉션 조회 실패를 조용한 `null`이 아니라 즉시 단언 실패로 만들고,
`resolveType(...)`은 `GenericTypeResolver.resolveType`의 정적 임포트다. 두 헬퍼 덕분에
각 테스트 본문이 "어떤 타입을 어떤 문맥에서 해석하나" 한 줄로 압축된다.

## 분류와 역할 요약

세 테스트를 fix 전 결과와 대응하는 fix 조건으로 정리하면 다음과 같다. 판별 근거는
diff 논리이며 실행으로 측정한 값이 아니다.

| 테스트 | fix 전 | 이 테스트를 깨뜨리는 잘못된 수정 |
|---|---|---|
| `resolveTypeAgainstSameNamedVariablesInTopLevelDeclarations` | red | `isAssignableFrom` 조건 누락 |
| `resolveMethodLevelTypeVariableIsNotShadowedByClassVariable` | red | `instanceof Class<?>` 조건 누락 |
| `resolveTypeVariableByNameWhenNarrowingParameterizedSupertype` | green | 이름 폴백 통째 삭제 |

세 테스트가 함께 있어야 fix의 술어가 유일하게 고정된다. red 둘은 술어가 **충분히
좁은지**를, 가드 하나는 술어가 **지나치게 좁지 않은지**를 각각 묻는다. 폴백처럼
"부당한 사용처와 정당한 사용처가 섞인 로직"을 다룰 때는 이 양방향 배치가 없으면
수정이 어느 방향으로 틀어져도 침묵으로 통과한다.

여기에 더해 이 PR은 픽스처 배치라는 축을 하나 더 보여 준다. 선행 수정 gh-36890은
코드를 옳게 고쳤지만 회귀 테스트를 중첩 타입으로 짠 탓에 대상 경로를 밟지 못했다.
테스트가 초록이라는 사실과 그 테스트가 문제의 코드 줄을 실행했다는 사실은 별개이며,
방어선이 되어야 할 테스트일수록 "이 테스트를 실패시키려면 어떤 코드를 되돌려야 하나"를
되물어 확인할 값어치가 있다.
