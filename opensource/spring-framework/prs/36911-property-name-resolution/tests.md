# PR #36911 — 테스트 해설 (테스트 하나하나)

> PR #36911 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR은 `PropertyTests`를 **새 파일로** 만들어 18건을 넣었다.\
판별 기준은 수정 전 `resolveName()`의 `indexOf` 기반 코드다.

```java
int index = name.indexOf("get");
if (index != -1) { index += 3; }
else { index = name.indexOf("is"); if (index != -1) { index += 2; } else { index = 0; } }
return StringUtils.uncapitalize(name.substring(index));
```

각 테스트의 메서드 이름을 이 식에 넣어 값을 직접 계산하면 red인지 가드인지 diff만으로 판별할 수 있다.\
결과는 red 9건, 가드 9건이다.

> **red / green** — 수정 **전** 코드에서 실패하는 테스트가 red, 통과하는 테스트가 green이다.\
> 예: `isTarget` 테스트는 수정 전에 빈 문자열이 나와 실패하므로 red다.

> **가드(guard) 테스트** — 결함을 재현하려는 게 아니라 "여기는 바뀌면 안 된다"를 붙들어 두는 테스트.\
> 예: `getName()` -> `name`은 수정 전후 모두 같아야 하므로 가드다.

18건이 어떤 축으로 나뉘는지를 먼저 그림으로 두면 아래 해설을 따라가기 쉽다.

```text
PropertyTests 18건
        |
        +-- JavaBeans 보존      getName, isEnabled, isTarget, setName        (1~4)
        |
        +-- record 시나리오     budget, issue, name, getWidget, get/is/getWidget 컴포넌트
        |                                                                   (5~11)
        +-- 데이터 클래스       budget, issue, name, getWidget, isUrgent     (12~16)
        |
        +-- static 엣지         getCount(동명 static 필드), getLabel(static 메서드)
                                                                            (17,18)
```

## 1. 표준 getter — 항상 green (양성 가드)

첫 테스트는 손대지 않아야 할 기본 동작, 즉 평범한 JavaBeans getter에서 접두사가 그대로 벗겨지는지를 고정한다.

```java
@Test
void resolveNameForStandardGetter() throws Exception {
	assertThat(readProperty(TestBean.class, "getName").getName()).isEqualTo("name");
}
```

- **주장**: 평범한 JavaBeans getter `getName()`은 `name`으로 해석된다.
- **fix 전 green인 이유**: `indexOf("get")`이 0을 돌려주므로 `startsWith`와 결과가 같다. 이 형태에서는 두 구현이 구분되지 않는다.
- **역할**: 이 PR의 무회귀 축 중 가장 기본.\
  `startsWith` 전환과 `isPlainAccessor` 도입이 표준 getter의 접두사 제거를 건드리지 않았음을 고정한다.\
  `TestBean`에는 `name` 필드가 없으므로 plain accessor 판정도 false로 떨어져 그대로 벗겨진다.

> **양성 가드 / 음성 가드** — 양성 가드는 "이 동작은 계속 일어나야 한다"를, 음성 가드는 "이 변경은 여기까지 번지면 안 된다"를 고정한다.\
> 예: `getName -> name`은 양성 가드, "setter 경로는 손대지 않았다"는 음성 가드다.

## 2. boolean getter — 항상 green (양성 가드)

두 번째 테스트는 `is` 접두사 쪽에서 같은 보존 동작을 맡는다.

```java
@Test
void resolveNameForBooleanGetter() throws Exception {
	assertThat(readProperty(TestBean.class, "isEnabled").getName()).isEqualTo("enabled");
}
```

- **주장**: `isEnabled()`는 `enabled`로 해석된다(`is` 접두사 제거).
- **fix 전 green인 이유**: `isEnabled`에는 `get`이 없고 `is`가 0번에 있어 `indexOf`와 `startsWith`가 같은 답을 낸다.
- **역할**: `is` 분기의 보존 동작 고정.\
  뒤의 16번(`isUrgent`)과 짝을 이루는 대조군으로, 같은 `is` 접두사라도 **같은 이름의 필드가 없으면** 여전히 벗겨진다는 것을 보인다.

## 3. 이름 중간에 get이 박힌 getter — red

세 번째 테스트가 이 PR의 핵심 수정을 정면으로 겨눈다.\
record 없이 평범한 JavaBeans 클래스만으로 결함을 재현하는 유일한 건이다.

```java
@Test  // regression guard for the indexOf -> startsWith fix: "get" embedded mid-name
void resolveNameForGetterEmbeddingGetInName() throws Exception {
	// with the former indexOf-based resolution this resolved to "" (matched "get" in "isTarget")
	assertThat(readProperty(TestBean.class, "isTarget").getName()).isEqualTo("target");
}
```

- **주장**: `isTarget()`은 `target`이다.
- **fix 전**: `"isTarget".indexOf("get")`은 5(문자 g, e, t가 5~7번에 연속)라서 index가 8이 되고 `substring(8)`은 빈 문자열이다. 기대값 `target`과 달라 red.
- **역할**: 핵심 수정(`indexOf` -> `startsWith`) 자체를 정면으로 겨누는 유일한 테스트다.\
  이 PR의 다른 red들은 record·데이터 클래스 fixture에 의존하지만, 이 건은 평범한 JavaBeans 클래스만으로 재현된다 — 즉 "record 없이도 이미 버그였다"의 증거다.

> **fixture(픽스처)** — 테스트가 관찰할 상황을 만들기 위해 테스트 파일 안에 미리 준비해 두는 클래스·데이터.\
> 예: `SampleRecord`, `EdgeRecord` 같은 테스트 전용 클래스들이 이 PR의 fixture다.

## 4. setter 경로 — 항상 green (음성 가드)

네 번째 테스트는 이 PR이 손대지 않기로 한 setter 경로를 그대로 묶어 둔다.

```java
@Test
void resolveNameForSetter() throws Exception {
	Method setter = TestBean.class.getMethod("setName", String.class);
	assertThat(new Property(TestBean.class, null, setter).getName()).isEqualTo("name");
}
```

- **주장**: 읽기 메서드가 없고 쓰기 메서드만 있는 `Property`는 `setName`에서 `name`을 얻는다.
- **fix 전 green인 이유**: 이 PR은 `writeMethod` 분기를 전혀 손대지 않았다(1차 커밋에서 조였다가 리뷰 요청으로 원복, 별도 PR #37139로 분리). 그러므로 수정 전후 결과가 같다.
- **역할**: 변경 범위가 read 분기에 갇혀 있음을 코드로 못박는 음성 가드.\
  "왜 setter는 안 고쳤나"라는 리뷰 질문에 대해 "이 PR에서는 동작이 그대로다"를 실행으로 답한다.

## 5. record 접근자 budget — red

다섯 번째 테스트부터 record 시나리오가 시작된다.\
첫 건은 이름 중간에 `get`을 품은 컴포넌트다.

```java
@Test  // record component accessor whose name embeds the "get" prefix
void resolveNameForRecordAccessorEmbeddingGetPrefix() throws Exception {
	assertThat(readProperty(SampleRecord.class, "budget").getName()).isEqualTo("budget");
}
```

- **주장**: record 컴포넌트 접근자 `budget()`은 이름 그대로 `budget`이다.
- **fix 전**: `"budget".indexOf("get")`이 3이라 index 6, `substring(6)`은 빈 문자열 -> red.\
  PR 본문 표의 첫 줄(`budget()` -> `""`)을 그대로 실행한 것이다.
- **fixture가 흉내 내는 것**: `SampleRecord`는 실제 애플리케이션의 record DTO를 대신한다.\
  `budget`은 인위적인 이름이 아니라 `widget`, `gadget`처럼 `get`을 품은 평범한 명사 집합의 대표다.
- **fix 후**: `startsWith("get")` 진입 후 `isPlainAccessor`가 true(같은 이름의 인스턴스 필드가 record의 backing field로 존재) -> index 0 -> `budget`.

## 6. record 접근자 issue — red

여섯 번째 테스트는 이름이 실제로 `is`로 시작하는 컴포넌트를 다루며, 5번과 달리 `startsWith` 전환만으로는 고쳐지지 않는다.

```java
@Test  // record component accessor whose name starts with the "is" prefix
void resolveNameForRecordAccessorStartingWithIsPrefix() throws Exception {
	assertThat(readProperty(SampleRecord.class, "issue").getName()).isEqualTo("issue");
}
```

- **주장**: `issue()`는 `issue`다.
- **fix 전**: `get`은 없고 `is`가 0번에 있어 index 2 -> `sue` -> red.\
  이 경우는 5번과 달리 `startsWith`로 바꾸는 것만으로는 고쳐지지 않는다 — `issue`는 실제로 `is`로 **시작하기** 때문이다. 그래서 `isPlainAccessor` 판별이 반드시 필요하다.
- **역할**: 수정의 두 축(`startsWith` 전환 / plain accessor 판별) 중 후자를 단독으로 요구하는 red.\
  5번이 전자를 요구하는 red이므로 둘은 교체 불가능한 한 쌍이다.

5번과 6번이 서로 다른 축을 요구한다는 것을 값으로 보면 이렇다.

```text
5번 budget()                          6번 issue()
+----------------------------+        +----------------------------+
| get 을 이름 중간에 품음    |        | is 로 실제로 시작함        |
| fix 전: substring(6) = ""  |        | fix 전: substring(2)="sue" |
| 요구하는 축:               |        | 요구하는 축:               |
|   indexOf -> startsWith    |        |   isPlainAccessor 판별     |
+----------------------------+        +----------------------------+
  -> 두 red 는 교체 불가능한 한 쌍이다
```

## 7. 접두사 충돌 없는 record 접근자 — 항상 green (양성 가드)

일곱 번째 테스트는 접두사와 충돌하지 않는 평범한 컴포넌트가 기존 동작 그대로 남는지 확인한다.

```java
@Test  // plain record component accessor with no prefix collision (regression guard)
void resolveNameForPlainRecordAccessor() throws Exception {
	assertThat(readProperty(SampleRecord.class, "name").getName()).isEqualTo("name");
}
```

- **주장**: `name()`은 `name`이다.
- **fix 전 green인 이유**: `name`에는 `get`도 `is`도 없어 폴백 `index = 0`으로 떨어졌고, 수정 후에도 접두사 없는 이름은 같은 else 가지로 간다.
- **역할**: gh-26029가 추가한 record 지원의 원래 동작이 이번 수정으로 깨지지 않았음을 고정한다.\
  접두사 판별을 세 갈래로 다시 쓰면서 "접두사 없는 이름"을 잃어버리는 실수를 잡는 자리.

## 8. record 위에 손으로 쓴 getter — 항상 green (음성 가드)

여덟 번째 테스트는 record 안에 사람이 직접 쓴 JavaBeans getter를 대조군으로 세운다.

```java
@Test  // a JavaBeans-style getter declared on a record must still be stripped
void resolveNameForGetterDeclaredOnRecord() throws Exception {
	assertThat(readProperty(SampleRecord.class, "getWidget").getName()).isEqualTo("widget");
}
```

- **주장**: record 안에 사람이 직접 쓴 `getWidget()`은 컴포넌트가 아니므로 여전히 `widget`으로 벗겨진다.
- **fix 전 green인 이유**: `indexOf("get")`이 0이라 결과가 같다.
- **역할**: 1차 커밋이 썼던 "선언 클래스가 record면 벗기지 않는다"는 판별식이었다면 이 테스트는 실패했을 것이다.\
  최종 판별식이 **클래스의 정체가 아니라 메서드의 모양**을 본다는 것을 고정하는 음성 가드다.\
  `SampleRecord`에 `getWidget` 필드는 없으므로 `isPlainAccessor`가 false로 떨어져 접두사가 제거된다.

## 9~11. 이름이 접두사 그 자체인 컴포넌트 — 모두 red

9~11번은 컴포넌트 이름이 접두사 글자 그 자체인 극단을 세 건으로 나눠 고정한다.

```java
@Test  // component literally named "get": proves plain accessor detection must precede startsWith
void resolveNameForRecordAccessorNamedGet() throws Exception {
	assertThat(readProperty(EdgeRecord.class, "get").getName()).isEqualTo("get");
}

@Test  // component literally named "is": proves plain accessor detection must precede startsWith
void resolveNameForRecordAccessorNamedIs() throws Exception {
	assertThat(readProperty(EdgeRecord.class, "is").getName()).isEqualTo("is");
}

@Test  // component literally named "getWidget": plain accessor detection must beat prefix stripping
void resolveNameForRecordAccessorNamedGetWidget() throws Exception {
	assertThat(readProperty(EdgeRecord.class, "getWidget").getName()).isEqualTo("getWidget");
}
```

- **주장**: 컴포넌트 이름이 문자 그대로 `get`, `is`, `getWidget`이어도 이름이 보존된다.
- **fix 전**: 각각 `substring(3)` = 빈 문자열, `substring(2)` = 빈 문자열, `substring(3)` = `widget`. 셋 다 기대값과 달라 red.
- **fixture가 흉내 내는 것**: `EdgeRecord(String get, String is, String getWidget)`은 현실에서 흔치는 않지만 **문법적으로 완전히 합법인** 컴포넌트 이름의 극단이다.\
  자바가 금지하지 않는 입력은 언젠가 들어온다는 전제 아래 경계를 못박는다.
- **역할**: 세 건이 공통으로 증명하는 것은 판별 순서다.\
  `startsWith` 검사와 `isPlainAccessor` 검사 중 **후자가 결과를 결정**해야 한다는 것 — 특히 11번은 8번과 정확히 대칭이다.\
  같은 메서드 이름 `getWidget`인데 8번(backing field 없음)은 벗기고, 11번(같은 이름의 backing field 있음)은 보존한다.\
  두 건을 나란히 두면 판별 기준이 이름이 아니라 필드의 존재라는 점이 값으로 드러난다.

8번과 11번의 대칭은 이렇게 생겼다.

```text
8번 SampleRecord.getWidget()          11번 EdgeRecord 컴포넌트 getWidget()
+----------------------------+        +----------------------------+
| 동명 필드 없음             |        | 동명 필드 있음             |
| isPlainAccessor -> false   |        | isPlainAccessor -> true    |
| 접두사 제거                |        | 이름 보존                  |
| -> widget                  |        | -> getWidget               |
+----------------------------+        +----------------------------+
  -> 판정 단위는 클래스가 아니라 메서드다
```

## 12~14. 손으로 쓴 데이터 클래스 3형제 — red 2건 + 가드 1건

12~14번은 앞의 record 시나리오 세 건을 record가 아닌 손으로 쓴 데이터 클래스에서 그대로 반복한다.

```java
@Test  // data class accessor whose name embeds the "get" prefix
void resolveNameForDataClassAccessorEmbeddingGetPrefix() throws Exception {
	assertThat(readProperty(SampleDataClass.class, "budget").getName()).isEqualTo("budget");
}

@Test  // data class accessor whose name starts with the "is" prefix
void resolveNameForDataClassAccessorStartingWithIsPrefix() throws Exception {
	assertThat(readProperty(SampleDataClass.class, "issue").getName()).isEqualTo("issue");
}

@Test  // plain data class accessor with no prefix collision (regression guard)
void resolveNameForPlainDataClassAccessor() throws Exception {
	assertThat(readProperty(SampleDataClass.class, "name").getName()).isEqualTo("name");
}
```

- **주장**: 5·6·7번과 같은 세 시나리오가 record가 아닌 일반 클래스에서도 동일하게 동작한다.
- **fix 전**: `budget`은 빈 문자열, `issue`는 `sue`로 red. `name`은 폴백을 타 green.
- **fixture가 흉내 내는 것**: `SampleDataClass`는 **Kotlin data class와 손으로 쓴 자바 데이터 클래스**를 대신한다.\
  Kotlin `val issue`가 만들어 내는 바이트코드 모양이 "private final 필드 + 같은 이름의 무인자 public 접근자"인데, 자바 테스트에서 Kotlin을 컴파일할 수 없으니 같은 모양을 자바로 직접 써서 흉내 낸 것이다.
- **역할**: 리뷰어(sbrannen)가 요구한 범위 확장 — "record 전용이 아니라 데이터 클래스 전반"을 실행으로 증명하는 블록이다.\
  5~7번과 결과가 완전히 같다는 사실 자체가 `isPlainAccessor`가 `java.lang.Record`나 `RecordComponent`에 의존하지 않는다는 증거다.

## 15. 데이터 클래스 위의 JavaBeans getter — 항상 green (음성 가드)

15번은 데이터 클래스 쪽에서 8번과 같은 대조군 역할을 한다.

```java
@Test  // a JavaBeans-style getter without a backing field must still be stripped
void resolveNameForGetterDeclaredOnDataClass() throws Exception {
	assertThat(readProperty(SampleDataClass.class, "getWidget").getName()).isEqualTo("widget");
}
```

- **주장**: `SampleDataClass.getWidget()`은 `getWidget` 필드가 없으므로 `widget`으로 벗겨진다.
- **fix 전 green인 이유**: `indexOf("get")`이 0이라 동일한 결과.
- **역할**: 8번의 데이터 클래스 판이다.\
  "데이터 클래스 안에 있다"는 사실만으로 전부 plain accessor로 취급되지 않음을 고정한다 — 판정 단위는 클래스가 아니라 메서드다.

## 16. 같은 이름 필드로 뒷받침되는 boolean getter — red (의도된 동작 변경 고정)

16번은 결함 재현이 아니라 이 PR이 의도적으로 바꾼 동작을 고정하는 자리다.

```java
@Test  // a boolean getter backed by a field of the exact same name resolves to the field name
void resolveNameForBooleanGetterBackedByFieldOfSameName() throws Exception {
	assertThat(readProperty(SampleDataClass.class, "isUrgent").getName()).isEqualTo("isUrgent");
}
```

- **주장**: `private final boolean isUrgent` + `public boolean isUrgent()` 조합은 `urgent`가 아니라 필드명 `isUrgent`로 해석된다.
- **fix 전**: `isUrgent`에 `get`은 없고(`g`,`e`,`n`이라 `get`이 아니다) `is`가 0번이라 index 2 -> `urgent`. 기대값 `isUrgent`와 달라 red.
- **다른 red들과 성격이 다르다**: 이 건은 결함 재현이 아니라 **의도된 동작 변경의 고정**이다.\
  `java.beans.Introspector`는 이 모양을 `urgent`로 읽으므로, 이 테스트가 green이 되는 순간 Spring은 그 지점에서 JDK와 갈라진다.\
  record 컴포넌트 `isUrgent`가 만들어 내는 바이트코드와 이 손으로 쓴 클래스가 **리플렉션으로 구분 불가능**하기 때문에 둘 중 하나를 고를 수밖에 없고, PR은 "필드명이 곧 저자의 의도"를 택했다.
- **역할**: PR 본문 `## Note on impact`에 공개된 트레이드오프를 코드로 못박아, 메인테이너가 다른 결정을 내리면 이 테스트가 먼저 깨지도록 만든 자리다.\
  문서가 아니라 테스트가 정책의 정본이 되게 하는 배치다.

## 17~18. static 엣지 — 모두 항상 green (음성 가드)

17~18번은 `isPlainAccessor`가 새로 도입한 두 static 배제 조건을 각각 겨눈다.

```java
@Test  // a static field of the same name must not make an instance getter a plain accessor
void resolveNameForGetterWithStaticFieldOfSameName() throws Exception {
	assertThat(readProperty(StaticEdgeBean.class, "getCount").getName()).isEqualTo("count");
}

@Test  // a static method must not be treated as a plain accessor
void resolveNameForStaticGetterWithInstanceFieldOfSameName() throws Exception {
	assertThat(readProperty(StaticEdgeBean.class, "getLabel").getName()).isEqualTo("label");
}
```

- **주장**: 두 경우 모두 접두사가 정상적으로 제거된다(`count`, `label`).
- **fix 전 green인 이유**: 수정 전에는 static 여부를 아예 보지 않고 `indexOf("get")=0`으로 벗겼다. 즉 결과값이 우연히 같다.
- **존재 이유는 fix 후**: `isPlainAccessor`가 도입한 두 개의 배제 조건을 각각 겨눈다.\
  17번은 **필드 쪽 static 검사**(`return !Modifier.isStatic(field.getModifiers())`)를, 18번은 **메서드 쪽 static 검사**(첫 줄의 `Modifier.isStatic(method.getModifiers())`)를 지운 미래의 수정에서만 실패한다.
- **fixture가 흉내 내는 것**: `StaticEdgeBean`은 "같은 이름의 필드가 있긴 한데 소유 관계가 인스턴스가 아닌" 상황을 만든다.\
  정적 상수와 인스턴스 접근자가 우연히 이름을 공유하는 실제 코드가 plain accessor로 오인되지 않아야 한다는 뜻이다.
- **판별 근거**: 두 건 모두 fix 전후 기대값이 같으므로 red가 아니라는 판정은 diff만으로 확정된다.

## fixture

테스트 클래스가 새로 만든 fixture는 헬퍼 하나와 클래스 넷이다.

```java
private static Property readProperty(Class<?> objectType, String readMethodName) throws Exception {
	Method readMethod = objectType.getMethod(readMethodName);
	return new Property(objectType, readMethod, null);
}
```

`readProperty`는 **이름 인자를 비운 채** `Property`를 만든다.\
이것이 이 테스트 전체의 전제다.\
`Property`는 이름이 주어지면 그대로 쓰고 없을 때만 `resolveName()`을 부르므로, 이름을 비워야 유도 경로가 실제로 실행된다.\
실제 노출 지점도 같은 모양이다 — SpEL의 `ReflectivePropertyAccessor`가 접근자 메서드만 들고 카드를 만들 때 이 경로를 탄다.

```java
static class TestBean { getName(), isEnabled(), isTarget(), setName(String) }

record SampleRecord(String name, String budget, String issue) { getWidget() }

record EdgeRecord(String get, String is, String getWidget) {}

static class SampleDataClass { 필드 name/budget/issue/isUrgent + 동명 접근자 4개 + getWidget() }

static class StaticEdgeBean { static 필드 getCount + 인스턴스 getCount(),
                              인스턴스 필드 getLabel + static getLabel() }
```

네 클래스는 각각 하나의 세계를 대표한다.\
`TestBean`은 순수 JavaBeans, `SampleRecord`는 정상적인 record, `EdgeRecord`는 합법이지만 극단적인 컴포넌트 이름, `SampleDataClass`는 Kotlin data class를 포함한 넓은 의미의 데이터 클래스, `StaticEdgeBean`은 static 오염이다.\
mock 라이브러리는 하나도 쓰지 않는데, 검증 대상이 **리플렉션으로 읽는 실제 클래스 구조** 자체이기 때문이다.\
Mockito로 만든 프록시는 필드 선언을 흉내 낼 수 없으므로 여기서는 실물 클래스가 유일한 재현 수단이다.

> **mock(목) / 프록시(proxy)** — 진짜 객체 대신 테스트용으로 만들어 끼우는 가짜 객체.\
> 예: Mockito가 만드는 가짜 객체는 메서드 호출은 흉내 내지만 `private final String issue` 같은 필드 선언까지 만들어 내지는 못한다.

## 실측·역할 요약

fix 전 실행 결과를 위 계산대로 정리하면 다음과 같다.

| 분류 | 건수 | 해당 테스트 |
|---|---|---|
| red (결함 재현) | 8 | 3, 5, 6, 9, 10, 11, 12, 13 |
| red (의도된 동작 변경) | 1 | 16 |
| 양성 가드 | 4 | 1, 2, 7, 14 |
| 음성 가드 | 5 | 4, 8, 15, 17, 18 |

역할 요약은 세 겹이다.\
red 8건이 "이름 유도가 실제로 망가져 있었다"를 증명하고, 가드 9건이 "JavaBeans·setter·static 경로는 그대로다"를 보증하며, 16번 한 건이 합의된 정책을 문서가 아닌 실행으로 고정한다.\
특히 8번과 11번의 대칭, 2번과 16번의 대칭은 새 판별식의 기준선이 정확히 어디인지를 값의 차이로 보여 주는 배치다.
