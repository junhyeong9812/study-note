# PR #36965 — 테스트 해설 (테스트 하나하나)

> PR #36965 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR이 추가한 테스트는 `ValueCodeGeneratorTests.PrimitiveTests`의 여섯 건이고, 여섯 건 전부 수정 전에 실패하는 red 테스트다.\
가드 역할은 새로 추가된 것이 아니라 같은 중첩 클래스에 이미 있던 `generateWhenFloat`·`generateWhenDouble` 두 건이 맡는다.\
`Float`와 `Double` 각각에 대해 NaN, 양의 무한대, 음의 무한대 세 값을 곱집합으로 덮은 구조이므로, 여섯 테스트는 사실상 같은 주장의 여섯 좌표다.

> **red 테스트** — 수정을 적용하기 전에는 반드시 실패해야 하는 테스트.\
> 예: `generateWhenFloatNaN`은 수정 전이면 `NaNF`가 나와 단언이 깨지고, 수정 후에야 초록이 된다.

> **가드 테스트(guard test)** — 고치는 과정에서 멀쩡하던 동작이 망가지지 않았는지 지키는 테스트.\
> 예: 여기서는 `generateWhenFloat`(`0.1F`)와 `generateWhenDouble`(`(double) 0.2`) 두 건이 유한 값 경로를 지킨다.

## 0. 커버리지 한눈에 — 무엇을 덮고 무엇을 못 덮나

축 둘을 잡으면 이 PR의 테스트 배치가 2x2로 정리된다.\
세로축은 값의 타입(`Float` / `Double`), 가로축은 값의 종류(비유한 값 / 유한 값)다.

```text
                비유한 값 (NaN, +Infinity, -Infinity)    유한 값
             +--------------------------------------+------------------------------+
             | generateWhenFloatNaN                 | generateWhenFloat            |
   Float     | generateWhenFloatPositiveInfinity    |   0.1F -> "0.1F"             |
             | generateWhenFloatNegativeInfinity    |                              |
             |   새 테스트 3건 (fix 전 red)          |   기존 테스트 1건 (내내 green) |
             +--------------------------------------+------------------------------+
             | generateWhenDoubleNaN                | generateWhenDouble           |
   Double    | generateWhenDoublePositiveInfinity   |   0.2 -> "(double) 0.2"      |
             | generateWhenDoubleNegativeInfinity   |                              |
             |   새 테스트 3건 (fix 전 red)          |   기존 테스트 1건 (내내 green) |
             +--------------------------------------+------------------------------+

             네 칸의 검증 수단은 전부 hasToString 문자열 비교 하나뿐이다
             +-----------------------------------------------------------+
             | 생성된 소스를 실제 javac 로 컴파일해 보기                    |
             |   -> 네 칸 어디에도 없다. 이 PR 의 테스트가 못 덮는 칸이다   |
             +-----------------------------------------------------------+
```

왼쪽 두 칸이 이 PR이 새로 채운 자리이고, 오른쪽 두 칸은 기존 테스트가 이미 지키던 자리이며, 아래 띠가 어느 칸에도 들어가지 못한 검증이다.

## 1. Float.NaN — red

첫 번째 테스트는 `Float`의 NaN 한 값을 겨눈다.

```java
@Test
void generateWhenFloatNaN() {
	assertThat(generateCode(Float.NaN)).hasToString("java.lang.Float.NaN");
}
```

- **주장**: `Float.NaN`이라는 값을 소스로 번역하면 `NaN`이라는 리터럴이 아니라 `java.lang.Float.NaN`이라는 상수 필드 참조가 나와야 한다.
- **fix 전 결과와 이유**: red.\
  `PrimitiveDelegate`가 `CodeBlock.of("$LF", value)`만 타므로 `$L`이 값의 `toString()`인 `"NaN"`을 그대로 뱉고 접미사 `F`가 붙어 `NaNF`가 나온다.\
  기대 문자열과 다르므로 단언 실패다.\
  여기서 중요한 것은 **생성 단계 자체는 예외 없이 성공한다**는 점이다.\
  결함이 조용하기 때문에 단언 없이는 관측되지 않는다.
- **fix 후**: `Float.isNaN(floatValue)` 분기가 `CodeBlock.of("$T.NaN", Float.class)`를 반환해 기대와 일치한다.\
  NaN만 `==` 비교가 아니라 `isNaN()`으로 판별하는데, `NaN == NaN`이 언제나 false라 등호 비교로는 절대 걸리지 않기 때문이다.\
  이 테스트가 그 판별 방식의 선택까지 간접적으로 고정한다.

> **NaN의 비교 규칙** — IEEE 754에서 NaN은 자기 자신과도 같지 않다.\
> 예: `Float.NaN == Float.NaN`이 `false`이므로 `floatValue == Float.NaN` 같은 분기는 절대 참이 되지 않고, `Float.isNaN(floatValue)`를 써야 한다.

## 2. Float.POSITIVE_INFINITY — red

두 번째 테스트는 같은 질문을 `Float`의 양의 무한대에 던진다.

```java
@Test
void generateWhenFloatPositiveInfinity() {
	assertThat(generateCode(Float.POSITIVE_INFINITY)).hasToString("java.lang.Float.POSITIVE_INFINITY");
}
```

- **주장**: 양의 무한대는 `java.lang.Float.POSITIVE_INFINITY` 상수 참조로 번역된다.
- **fix 전 결과와 이유**: red.\
  같은 `$LF` 경로를 타서 `Float.POSITIVE_INFINITY.toString()`인 `"Infinity"`에 접미사가 붙어 `InfinityF`가 나온다.\
  `Infinity`는 Java 언어에 존재하지 않는 식별자이므로 생성물이 컴파일 불가라는 사실을, 문자열 비교로 대신 잡아낸다.
- **fix 후**: `floatValue == Float.POSITIVE_INFINITY` 분기가 상수 참조를 반환한다.

## 3. Float.NEGATIVE_INFINITY — red

세 번째 테스트는 부호가 반대인 무한대를 별도 좌표로 고정한다.

```java
@Test
void generateWhenFloatNegativeInfinity() {
	assertThat(generateCode(Float.NEGATIVE_INFINITY)).hasToString("java.lang.Float.NEGATIVE_INFINITY");
}
```

- **주장**: 음의 무한대도 대응하는 상수 참조로 번역된다.
- **fix 전 결과와 이유**: red.\
  `-InfinityF`가 나온다.\
  양의 무한대와 따로 테스트하는 이유는 부호가 다른 두 값이 **서로 다른 상수 필드**로 매핑되어야 하고, 한쪽 분기만 넣는 실수가 실제로 가능하기 때문이다.\
  두 분기를 각각 고정하지 않으면 부호를 잘못 매핑하는 회귀가 침묵한다.
- **fix 후**: `floatValue == Float.NEGATIVE_INFINITY` 분기가 처리한다.

> **회귀가 침묵한다** — 잘못된 변경이 들어와도 테스트가 빨간불을 내지 않아 아무도 모르는 상태.\
> 예: `POSITIVE_INFINITY` 테스트 하나만 두면, 음의 무한대를 양의 상수로 매핑하는 오타가 그대로 통과한다.

## 4. Double.NaN — red

네 번째 테스트부터는 `Double` 쪽 세 좌표로 넘어간다.

```java
@Test
void generateWhenDoubleNaN() {
	assertThat(generateCode(Double.NaN)).hasToString("java.lang.Double.NaN");
}
```

- **주장**: `Double`도 `Float`과 같은 규칙을 따른다.
- **fix 전 결과와 이유**: red.\
  `Double` 경로는 접미사가 아니라 캐스트를 쓰는 `CodeBlock.of("(double) $L", value)`이므로 `(double) NaN`이 나온다.\
  실패 문자열의 모양이 `Float` 쪽과 다르다는 것이 두 타입을 따로 테스트해야 하는 이유다.\
  두 경로는 코드 생성 방식이 애초에 달라, 한쪽을 고쳐도 다른 쪽은 그대로 남을 수 있다.
- **fix 후**: `Double.isNaN(doubleValue)` 분기가 `$T.NaN`을 `Double.class`로 반환한다.

## 5. Double.POSITIVE_INFINITY — red

다섯 번째 테스트는 `Double`의 양의 무한대를 고정한다.

```java
@Test
void generateWhenDoublePositiveInfinity() {
	assertThat(generateCode(Double.POSITIVE_INFINITY)).hasToString("java.lang.Double.POSITIVE_INFINITY");
}
```

- **주장**: `Double`의 양의 무한대는 `java.lang.Double.POSITIVE_INFINITY`로 번역된다.
- **fix 전 결과와 이유**: red. `(double) Infinity`가 나온다.
- **fix 후**: `doubleValue == Double.POSITIVE_INFINITY` 분기가 처리한다.

## 6. Double.NEGATIVE_INFINITY — red

여섯 번째 테스트가 마지막 좌표인 `Double`의 음의 무한대를 덮는다.

```java
@Test
void generateWhenDoubleNegativeInfinity() {
	assertThat(generateCode(Double.NEGATIVE_INFINITY)).hasToString("java.lang.Double.NEGATIVE_INFINITY");
}
```

- **주장**: `Double`의 음의 무한대는 `java.lang.Double.NEGATIVE_INFINITY`로 번역된다.
- **fix 전 결과와 이유**: red. `(double) -Infinity`가 나온다.
- **fix 후**: `doubleValue == Double.NEGATIVE_INFINITY` 분기가 처리한다.

## 기대 문자열이 왜 완전 수식 이름인가

여섯 테스트 모두 기대값이 `Float.NaN`이 아니라 `java.lang.Float.NaN`인데, 이는 헬퍼가 만드는 관측 지점 때문이다.

> **완전 수식 이름(fully qualified name)** — 패키지까지 전부 붙인 타입 이름.\
> 예: `Float`가 단순 이름이고 `java.lang.Float`가 완전 수식 이름이다.

```java
private static CodeBlock generateCode(@Nullable Object value) {
	return ValueCodeGenerator.withDefaults().generateCode(value);
}
```

이 헬퍼는 `CodeBlock`을 만들어 그대로 돌려주고, 단언은 `hasToString`으로 그 `CodeBlock`을 바로 문자열화한다.\
JavaPoet에서 `$T` 자리표시자의 import 축약은 `CodeBlock`이 `JavaFile` 안에 배치될 때 일어나므로, 파일 문맥 없이 찍으면 정규화된 이름이 나온다.

> **`JavaFile`** — JavaPoet에서 `.java` 파일 하나를 나타내는 객체. import 문 목록을 여기서 관리한다.\
> 예: `java.lang.Float.NaN`이라는 조각도 `JavaFile` 안에 들어가면 `Float.NaN`으로 줄어들 수 있다.

같은 파일에서 클래스나 컬렉션을 다루는 테스트들은 `resolve(...)` 헬퍼로 `JavaFile`을 만들어 import까지 확인하는데, 이 여섯 건은 그 경로를 쓰지 않는다.\
따라서 고정되는 계약은 "**어떤 타입의 어떤 상수를 참조하는가**"이지 "짧은 이름으로 찍히는가"가 아니다.

## 가드는 기존 테스트가 맡는다

이 PR은 가드 테스트를 새로 추가하지 않았다.\
유한 값 경로가 그대로인지는 같은 중첩 클래스에 이미 있던 두 건이 계속 지킨다.

```java
@Test
void generateWhenFloat() {
	assertThat(generateCode(0.1F)).hasToString("0.1F");
}

@Test
void generateWhenDouble() {
	assertThat(generateCode(0.2)).hasToString("(double) 0.2");
}
```

수정이 `instanceof Float` 분기 안쪽에 조기 반환 세 개를 얹었을 뿐 마지막 `return CodeBlock.of("$LF", value)`를 건드리지 않았으므로, 이 두 건은 수정 전후 모두 green이다.\
"유한 값 처리는 그대로다"라는 주장의 실증이 정확히 여기에 있다.\
새로 넣은 조건이 유한 값까지 가로채는 과잉 분기였다면 이 두 건이 즉시 빨간불이 된다.

기존 두 건이 수정 전후로 무엇을 지키는지를 나란히 놓으면 이렇다.

```text
             수정 전                       수정 후
           +---------------------+       +---------------------+
   0.1F    | "$LF"               |       | 특수값 3검사 통과    |
           |   -> 0.1F           |       | "$LF"               |
           |                     |       |   -> 0.1F           |
           +---------------------+       +---------------------+
   0.2     | "(double) $L"       |       | 특수값 3검사 통과    |
           |   -> (double) 0.2   |       | "(double) $L"       |
           |                     |       |   -> (double) 0.2   |
           +---------------------+       +---------------------+
             -> green                      -> 여전히 green
```

유한 값은 조기 반환 세 개를 모두 빠져나와 옛 폴백으로 떨어지므로 출력 문자열이 한 글자도 달라지지 않는다.

## fixture와 mock

이 PR의 테스트에는 mock도 별도 fixture 클래스도 없다.\
입력값이 `Float.NaN` 같은 JDK 상수 자체이기 때문이다.

> **fixture** — 테스트가 돌기 위해 미리 마련해 두는 고정된 입력·환경.\
> 예: 여기서는 `Float.NaN`이라는 JDK 상수 하나가 fixture 전부다.

> **mock(모의 객체)** — 진짜 협력 객체 대신 끼워 넣는 흉내 객체.\
> 예: 이 테스트들은 `withDefaults()`로 실제 프로덕션 위임자 체인을 그대로 돌리므로 mock이 없다.

다만 그 상수가 무엇을 흉내 내는지는 짚어둘 만하다.\
실제 상황은 "어떤 빈의 프로퍼티 값이나 생성자 인자가 `Double.NaN`을 담고 있고, AOT 빌드가 그 빈 정의를 Java 소스로 다시 써내는" 장면이다.\
그 전체 파이프라인(`BeanDefinitionPropertiesCodeGenerator`에서 `ValueCodeGenerator`를 거쳐 생성 소스 컴파일까지)를 매번 돌리는 대신, 값이 소스 문자열이 되는 마지막 한 단계만 직접 호출해 같은 질문을 던진다.\
`withDefaults()`가 실제 프로덕션 위임자 체인을 그대로 구성하므로 대체물이 아니라 실물이 돈다.

## 실측·한계·역할 요약

여섯 건은 모두 red이고, 실패 문자열은 각각 `NaNF`, `InfinityF`, `-InfinityF`, `(double) NaN`, `(double) Infinity`, `(double) -Infinity`다.\
이 값들은 diff의 `$LF`·`(double) $L` 경로와 각 상수의 `toString()`에서 곧바로 도출되므로 판별에 불확실성이 없다.

한계는 정직하게 남는다.\
이 테스트들은 생성된 문자열을 비교할 뿐 실제로 javac를 돌려 컴파일 가능성을 확인하지 않는다.\
결함의 실제 증상이 "생성 소스가 컴파일되지 않는다"였음을 생각하면 한 칸 앞에서 멈춘 검증이다.\
다만 `java.lang.Float.NaN`이 유효한 상수 참조라는 것은 언어 명세 수준에서 자명하고, 기존 `PrimitiveTests`가 전부 문자열 비교 방식이라 관례를 따른 셈이다.

역할을 한 줄로 정리하면, 여섯 red 테스트는 "비유한 값 여섯 좌표가 각각 올바른 상수 필드로 매핑된다"를 고정하고, 기존 두 테스트는 "유한 값 경로는 그대로다"를 고정한다.
