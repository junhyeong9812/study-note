# PR #37139 — 테스트 해설 (테스트 하나하나)

> PR #37139 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR은 `PropertyTests`라는 **새 테스트 파일**을 만들고 네 건을 담았다. 결론부터 말하면
**red 2건, 항상 green인 가드 2건**이며, 네 건이 README 3절 표의 네 행과 정확히 하나씩
대응한다. red 둘은 이 PR이 새로 거부하게 만든 이름 모양을, 가드 둘은 전후가 같아야 하는
두 극단(정상 setter와 원래도 거부되던 이름)을 맡는다. 동작 강화(behavior change) PR이라
가드의 비중이 절반인 것이 이 배치의 특징이다. red/green 판별은 실행 결과가 아니라 diff
논리 — 수정 전 판별이 `indexOf("set")`였다는 사실 — 에서 유도했다.

## 0. 네 테스트가 공유하는 진입점

네 테스트 모두 `Property` 생성자 하나만 호출한다. 판별이 일어나는 시점이 생성 시점이기
때문이다.

```java
public Property(
		Class<?> objectType, @Nullable Method readMethod, @Nullable Method writeMethod, @Nullable String name) {

	this.objectType = objectType;
	this.readMethod = readMethod;
	this.writeMethod = writeMethod;
	this.methodParameter = resolveMethodParameter();
	this.name = (name != null ? name : resolveName());
}
```

이름을 넘기지 않으면 생성자 마지막 줄에서 `resolveName()`이 즉시 불린다. 그래서 잘못된
이름 모양은 지연된 조회가 아니라 **생성 실패**로 나타나고, 테스트도
`assertThatIllegalArgumentException().isThrownBy(() -> writeProperty(...))` 형태로
생성 자체를 감싼다. 읽기 메서드를 `null`로 넘기는 것은 write 분기를 강제로 타게 하기
위한 배치다 — 읽기 메서드가 있으면 그쪽 분기가 먼저 답을 내 write 분기가 실행되지
않는다.

## 1. 정상 setter — 항상 green (양성 가드)

첫 테스트는 규약을 지키는 setter가 강화 이후에도 그대로 통과하는지를 붙잡는다.

```java
@Test
void resolveNameForSetter() throws Exception {
	assertThat(writeProperty("setName").getName()).isEqualTo("name");
}
```

- **주장**: `setName(String)`은 여전히 프로퍼티 이름 `name`으로 풀린다.
- **fix 전 green인 이유**: `indexOf("set")`가 0을 돌려주고 `index += 3`, `substring(3)`
  = `"Name"`, `uncapitalize`로 `"name"`. 수정 전에도 통과한다.
- **존재 이유는 fix 후에 있다**: 이 PR은 판별을 엄격하게 만드는 변경이므로, 엄격화가
  정상 경로까지 잘라내지 않았음을 보증할 축이 필요하다. 특히 `indexOf` 결과에
  `+3`을 더하던 계산을 `substring(3)` 고정으로 바꾸는 과정에서 오프셋을 틀리기 쉬운데
  (예: `substring(4)`로 잘못 쓰면 `"ame"`), 이 테스트가 그 실수를 잡는다.
- **분류**: ../37153/guard-tests.md의 용어로 양성 가드다. "거부해야 할 것을 거부한다"의
  반대 방향, 즉 "받아야 할 것을 여전히 받는다"를 고정한다.

## 2. set 토큰이 아예 없는 이름 — 항상 green (음성 가드)

두 번째 테스트는 수정 전에도 이미 거부되던 유일한 경우가 여전히 같은 예외로 거부되는지를
확인한다.

```java
@Test  // no "set" token at all: rejected before and after this change
void rejectNonSetterWriteMethod() {
	assertThatIllegalArgumentException()
			.isThrownBy(() -> writeProperty("updateName"))
			.withMessage("Not a setter method");
}
```

- **주장**: `updateName(String)`처럼 `set`이 한 글자도 없는 이름은 전후 모두
  `IllegalArgumentException("Not a setter method")`로 거부된다.
- **fix 전 green인 이유**: `indexOf("set")`가 `-1`이라 이미 예외를 던지던 유일한
  경우다. 테스트 위 주석이 "rejected before and after this change"라고 그 사실을 직접
  밝힌다.
- **존재 이유는 fix 후에 있다**: 원래 있던 거부 동작의 회귀 가드다. 판별식을 통째로
  갈아 끼우는 변경이므로, 기존 거부가 사라지지 않았는지를 따로 확인할 값어치가 있다.
  예외 메시지까지 단언하는 것은 거부의 **경로**까지 같음을 요구하는 것이다 — 다른
  예외나 다른 메시지로 실패하면 사용자가 보는 진단이 달라진다.
- **1번과의 관계**: 두 가드가 표의 양 극단을 하나씩 붙잡는다. 1번은 통과해야 할 것,
  2번은 원래도 막혔던 것이다. 이 PR이 바꾸는 집합은 정확히 그 사이 — `set`을 품되
  `set`으로 시작하지 않는 이름 — 이며, 3·4번이 그 사이를 맡는다.

## 3. set을 중간에 품은 이름 — red

세 번째 테스트부터가 이 PR이 새로 막는 영역이다. 이름 중간에 `set`이 박힌 메서드를
거부하라고 요구한다.

```java
@Test  // "set" embedded mid-name: formerly accepted and resolved to "x"
void rejectWriteMethodEmbeddingSetInName() {
	assertThatIllegalArgumentException()
			.isThrownBy(() -> writeProperty("offsetX"))
			.withMessage("Not a setter method");
}
```

- **주장**: `offsetX(String)`은 setter가 아니므로 거부되어야 한다.
- **fixture가 흉내 내는 것**: `offsetX`는 `set`이라는 글자를 우연히 품은 평범한 메서드
  이름이다. `offset`, `reset`, `asset`, `subset` 같은 단어가 들어간 메서드는 실무에서
  흔하고, 그중 인자 하나짜리 void 메서드가 `Property`의 write 메서드로 넘어가면 곧바로
  이 경로를 밟는다.
- **fix 전 결과와 이유**: red다. o-f-f-**s-e-t**-X에서 `indexOf("set")`가 3을 돌려주고
  `+3`이면 6, `substring(6)` = `"X"`, `uncapitalize`로 `"x"`가 된다. 예외 없이 조용히
  성공하므로 "예외가 던져져야 한다"는 단언이 실패한다. 예외가 잘못된 종류로
  던져져서가 아니라 **아무것도 던져지지 않아서** 실패한다.
- **fix 후**: `startsWith("set")`가 거짓이라 즉시 `IllegalArgumentException`.
- **주석의 역할**: `// "set" embedded mid-name: formerly accepted and resolved to "x"`가
  fix 전 실제 결과값을 테스트 옆에 남긴다. 이 테스트가 잡아내는 것이 "잘못된 예외"가
  아니라 "무음 통과"임을 코드만 읽고도 알 수 있게 하는 장치다.

## 4. set으로 끝나는 이름 — red

네 번째 테스트는 같은 결함의 경계 쪽 산출물, 즉 이름이 빈 문자열이 되는 경우를 맡는다.

```java
@Test  // "set" at the end of the name: formerly accepted and resolved to ""
void rejectWriteMethodEndingWithSetToken() {
	assertThatIllegalArgumentException()
			.isThrownBy(() -> writeProperty("upset"))
			.withMessage("Not a setter method");
}
```

- **주장**: `upset(String)`도 setter가 아니므로 거부되어야 한다.
- **fix 전 결과와 이유**: red다. u-p-**s-e-t**에서 `indexOf("set")`가 2, `+3`이면 5인데
  문자열 길이도 5이므로 `substring(5)`는 빈 문자열이고 `uncapitalize("")`도 빈 문자열이다.
  예외 없이 **이름이 빈 문자열인 프로퍼티**가 만들어진다. 3번과 마찬가지로 아무것도
  던져지지 않아 단언이 실패한다.
- **3번과 별도인 이유**: 같은 `indexOf` 결함이지만 산출물의 성질이 다르다. 3번은
  "엉뚱하지만 그럴듯한 이름"이 나오고, 4번은 "빈 이름"이 나온다. 빈 이름은
  `getField()`나 `getName()` 비교를 쓰는 소비자 쪽에서 전혀 다른 방식으로 오동작하므로,
  두 형태를 각각 고정해 둘 값어치가 있다. 또한 4번은 경계 조건 테스트이기도 하다 —
  `indexOf` 결과 + 3이 문자열 길이와 정확히 같아지는 자리라, `substring`이
  `StringIndexOutOfBoundsException` 대신 빈 문자열을 돌려주는 경계다.

## fixture

이 PR은 테스트 파일 자체가 새 것이므로 픽스처도 함께 만들었다. 헬퍼 하나와 대상 빈
하나다.

```java
private static Property writeProperty(String writeMethodName) throws Exception {
	Method writeMethod = TestBean.class.getMethod(writeMethodName, String.class);
	return new Property(TestBean.class, null, writeMethod);
}


@SuppressWarnings("unused")
static class TestBean {

	public void setName(String name) {
	}

	public void updateName(String name) {
	}

	public void offsetX(String value) {
	}

	public void upset(String value) {
	}
}
```

`writeProperty(String)`는 메서드 이름 한 개만 받아 `Property`를 만든다. 두 번째 인자를
`null`로 고정해 읽기 메서드를 없앤 것이 핵심이다 — 앞서 말했듯 read 분기에는 "규약 밖
이름은 이름 전체를 쓴다"는 폴백이 있어서, 읽기 메서드가 있으면 write 분기의 엄격한
거부가 실행되지 않는다. 헬퍼가 그 조건을 네 테스트 전부에 강제한다.

`TestBean`의 네 메서드는 그 자체가 테스트 데이터다. 각각 정상 setter, `set` 없음,
`set` 중간, `set` 끝이라는 네 가지 이름 모양을 대표하며, 시그니처는 전부
`void m(String)`으로 통일했다. 이름 모양만이 유일한 변수이도록 나머지를 고정한 것이다.
`@SuppressWarnings("unused")`는 이 메서드들이 호출되지 않고 리플렉션으로 이름만 읽히기
때문에 붙었다. 실제로 네 테스트 중 어느 것도 메서드 본문을 실행하지 않는다.

`offsetX`와 `upset`의 파라미터 이름만 `value`인 것은 이들이 `name`이라는 프로퍼티와
무관한, 그냥 이름이 그렇게 생긴 메서드임을 드러내는 사소한 표시다.

파일 헤더에는 `@author Junhyeong Kim`과 클래스 Javadoc
`Tests for {@link Property} setter name resolution.`이 붙었다. 새 테스트 클래스의 범위를
"setter 이름 해석"으로 좁게 선언한 것이며, `Property`의 다른 측면(타입 해석, 애너테이션
병합 등)은 이 파일의 대상이 아니라는 뜻이다.

## 분류와 역할 요약

네 테스트를 fix 전 결과와 이름 모양으로 정리하면 다음과 같다. 판별 근거는 diff
논리이며 실행으로 측정한 값이 아니다.

| 테스트 | write 메서드 | fix 전 결과 | 분류 |
|---|---|---|---|
| `resolveNameForSetter` | `setName` | `"name"` 반환 | green (양성 가드) |
| `rejectNonSetterWriteMethod` | `updateName` | 예외 | green (음성 가드) |
| `rejectWriteMethodEmbeddingSetInName` | `offsetX` | `"x"` 반환 | red |
| `rejectWriteMethodEndingWithSetToken` | `upset` | `""` 반환 | red |

이 배치의 성격은 PR의 성격에서 나온다. 이 PR은 결함을 고쳐 "옳은 값"을 돌려주게 만드는
변경이 아니라, 이전에 통과하던 호출이 예외를 던지게 만드는 **동작 강화**다. 그래서
"새로 막는 것"만 단언하면 위험하다 — 막는 조건을 지나치게 넓게 잡아도(예: `startsWith`
대신 정규식 오작성) 그 단언들은 전부 통과하기 때문이다. 강화의 경계 양쪽에 가드를
하나씩 세워 통과해야 할 것과 원래도 막히던 것을 함께 고정해야 경계가 유일하게 결정된다.
red 2 + 가드 2라는 절반의 비율은 그 요구에서 나온 것이다.

한편 이 네 건으로도 덮이지 않는 공백이 하나 남아 있고, PR 본문이 그것을 명시한다.
`settle(String)`처럼 `set` 뒤에 소문자가 오는 이름은 전후 모두 `"tle"`로 해석된다 —
접두사 매칭만으로는 setter와 구분할 수 없기 때문이다. 테스트에 그 케이스가 없는 것은
누락이 아니라, 이 PR이 고치지 않기로 한 범위를 테스트로 고정하지 않은 것이다. 고치지
않은 동작을 테스트로 못박으면 나중에 그 동작을 개선할 때 테스트부터 지워야 한다.
