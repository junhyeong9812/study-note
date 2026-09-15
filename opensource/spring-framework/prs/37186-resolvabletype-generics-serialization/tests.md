# PR #37186 — 테스트 해설 (테스트 하나하나)

> 신규 14건(ResolvableTypeTests 11 + TypeDescriptorTests 3).\
> 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.\
> 이 테스트들은 **blind 설계** 산출물이다 — 구현 diff를 안 본 별도 워커가 spec에서 설계했고, red 예측 10건이 실측과 정확히 일치했다.

> **blind 설계** — 구현 코드를 보지 않고 명세만 읽고 테스트를 짜는 방식.\
> 예: "구현이 이렇게 생겼으니 이 단언은 통과하겠지"라는 편향 없이, 계약이 요구하는 것만 겨눈다.

배치 전체를 먼저 본다.\
red 10건이 결함 재현, 가드 4건이 보존 동작·경계의 명세다.

| 층 | red | 가드 |
|---|---|---|
| ResolvableType 기본 | T1 평면 제네릭 / T2 중첩 / T3 변수 해석 | T6 0-파라미터 |
| 경계(null) | T4 generics 배열 null / T5 원소 null | — |
| 계약 | T7 hashCode·HashMap 키 | T10 I4(비직렬화 경로 identity) |
| 캐리어·상태 | T8 Serializable 홀더 안 | RF4 파생 후 직렬화(리뷰 추가) |
| 범위 경계 | — | T9 SPR-17070 고정 |
| TypeDescriptor 층 | T11 collection / T12 map / T13 원소 null | — |

같은 배치를 "무엇을 요구하나 × 어느 입력인가"의 격자로 다시 보면 빈칸의 의미가 보인다.

```text
                          | 왕복이     | identity   | hash/계약 | 예외가   |
  입력 / 층               | 되나       | 가 정본    | 이 성립   | 그대로   |
  ------------------------+------------+------------+-----------+----------+
  구체 인자 (평면/중첩)   | T1 red     | T1 T2      |   T7 red  |    -     |
                          | T2 red     | (내부 Type)|           |          |
  ------------------------+------------+------------+-----------+----------+
  변수 해석 동작          | T3 red     |    -       |    -      |    -     |
  ------------------------+------------+------------+-----------+----------+
  null 경계               | T4 red     | T4 T5      |    -      |    -     |
  (배열 null / 원소 null) | T5 red     |            |           |          |
  ------------------------+------------+------------+-----------+----------+
  0-파라미터 클래스       | T6 green   |    -       |    -      |    -     |
  ------------------------+------------+------------+-----------+----------+
  Serializable 홀더 안    | T8 red     |    -       |    -      |    -     |
  ------------------------+------------+------------+-----------+----------+
  파생 후(캐시 채워짐)    | RF4 gr.    |    -       |    -      |    -     |
  ------------------------+------------+------------+-----------+----------+
  비직렬화 경로           |    -       | T10 green  |    -      |    -     |
  ------------------------+------------+------------+-----------+----------+
  SPR-17070 범위 밖       |    -       |    -       |    -      | T9 green |
  ------------------------+------------+------------+-----------+----------+
  공개 팩토리 표면        | T11~13 red |   -        |    -      |    -     |
  (collection/map)        |            |            |           |          |
  ------------------------+------------+------------+-----------+----------+

  red   = fix 전에 실패해야 하는 재현 (10건)
  green = fix 전후 모두 통과해야 하는 가드 (4건)
```

오른쪽 끝 칸(T9)만 "예외가 계속 나야 한다"를 요구한다 — 고치지 않기로 한 경계의 가드다.

## T1~T2. 평면·중첩 제네릭 라운드트립 — red

가장 기본이 되는 두 건은 제네릭 인자가 구체 타입인 객체의 왕복을 요구한다.

```java
ResolvableType type = ResolvableType.forClassWithGenerics(Map.class, String.class, Integer.class);
ResolvableType read = testSerialization(type);   // 기존 헬퍼: equals·getType·resolve 단언 내장
assertThat(read).hasSameHashCodeAs(type);
ParameterizedType readType = (ParameterizedType) read.getType();
assertThat(readType.getActualTypeArguments()[0]).isSameAs(String.class);
```

- fix 전: 직렬화 자체가 `NotSerializableException` -> red.
- **`isSameAs`를 어디에 거는가가 설계 포인트**: `SyntheticParameterizedType` 래퍼는 라운드트립 후 새 인스턴스가 맞다(Spring 객체).\
  identity 단언은 그 **내부의 JDK Type 원소**(rawType·인자)에만 건다 — blind 설계자가 실측으로 찾아낸 fix-agnostic 원칙.\
  T2는 중첩(`Map<String, List<Integer>>`)에서 안쪽 Synthetic의 원소까지 같은 단언을 반복한다.

> **fix-agnostic(구현 비의존) 단언** — 어떤 방식으로 고치든 참이어야 하는 것만 단언하는 원칙.\
> 예: "래퍼 객체가 같은 인스턴스여야 한다"는 구현에 따라 달라지지만, "내부 JDK Type이 정본이어야 한다"는 어느 fix에서도 참이다.

> **라운드트립(round-trip)** — 직렬화했다가 다시 역직렬화해 원래대로 돌아오는지 보는 왕복 검사.\
> 예: `testSerialization(type)`이 써서 읽은 결과를 돌려주고, 그 결과에 단언을 건다.

## T3. 복원 후 변수 해석 — red

세 번째 건은 복원본이 형태만 같은지가 아니라 실제로 일하는지를 묻는다.

```java
ResolvableType read = testSerialization(ResolvableType.forClassWithGenerics(ArrayList.class, String.class));
assertThat(read.as(List.class).getGeneric(0).resolve()).isEqualTo(String.class);
```

복원된 `TypeVariablesVariableResolver`가 실제로 동작하는지 — 즉 variables가 정본 인스턴스로 복원돼 `resolveVariable`의 매칭이 성립하는지를 **행동으로** 검증한다.\
복원 후 `as()`는 "역직렬화된 객체에서 새로 파생"이므로 범위 밖(파생물의 직렬화)과 무관하다는 점이 설계 노트에 명시돼 있다.

## T4~T5. null 경계 — red

다음 두 건은 인자가 비는 두 형태를 각각 맡는다.\
배열 자체가 null인 `forClassWithGenerics(List.class, (ResolvableType[]) null)`(`List<?>`)과 원소가 null인 `(Map, null, null)`(`Map<?, ?>`)이다.\
이때 인자 자리에 **raw TypeVariable이 재주입**되는 것이 두 번째 운반자였으므로, 복원 후 그 자리가 정본 `getTypeParameters()[i]`와 `isSameAs`인지가 핵심 단언이다.

## T6. 0-파라미터 — 가드 (전후 green)

`forClassWithGenerics(String.class, new ResolvableType[0])` — 타입 파라미터가 없는 클래스는 **원래부터 직렬화되던 케이스**다.\
이 가드는 fix가 그 경로를 깨지 않음을 고정하고, 리뷰에서 강화된 "마커 없으면 원본 직렬화" 원칙의 대표 케이스다.\
(`forClassWithGenerics(String.class)`는 오버로드 모호로 컴파일 불가 — 배열 명시가 필요하다는 것도 blind 설계의 실측 발견.)

## T7. hash 정합 — red

일곱 번째 건은 왕복이 성공하는 것을 넘어 해시 계약이 살아남는지를 본다.

```java
assertThat(readStringList).hasSameHashCodeAs(stringList).isNotEqualTo(readIntegerList);
Map<ResolvableType, String> map = new HashMap<>();
map.put(stringList, "string");
assertThat(map.get(readStringList)).isEqualTo("string");
```

`ResolvableType.hash`는 **직렬화되는 캐시 필드**다.\
복원 그래프가 정본 identity로 재구성되어야 저장된 hash와 재계산이 일치하고, 직렬화를 건넌 객체로 HashMap 조회가 성립한다(I3).\
rebuilt(같은 인자로 새로 만든 인스턴스)와의 동등까지 3자 정합을 본다.

> **해시 계약(hash contract)** — equals가 같은 두 객체는 hashCode도 같아야 한다는 자바의 약속.\
> 예: 이 약속이 깨지면 HashMap에 넣은 값을 같은 키로 다시 꺼내지 못한다.

## T8. Serializable 홀더 경유 — red

여덟 번째 건은 `ResolvableType`을 필드로 들고 다니는 실제 캐리어를 모듈 안의 소형 홀더 클래스로 대역해 세운다.\
spring-core 테스트가 spring-beans를 못 보므로(의존 방향) 대역으로 같은 계약을 검증한다 — 크로스모듈 실캐리어 테스트는 PR 파일 확산을 피해 제외하고 본문 서술로.

> **캐리어(carrier)** — 문제의 객체를 필드로 품고 다니면서 함께 직렬화되는 바깥 객체.\
> 예: `TypeDescriptor`나 `NoSuchBeanDefinitionException`이 `ResolvableType`의 캐리어다.

## T9. SPR-17070 경계 고정 — 가드 (전후 예외)

아홉 번째 건은 고치는 쪽이 아니라 고치지 않기로 한 쪽을 못박는 가드다.

```java
assertThatExceptionOfType(NotSerializableException.class).isThrownBy(() -> serialize(asType));
```

getSuperType/getInterfaces/as 파생은 **여전히** 비직렬화여야 한다 — 의도된 계약 축소(SPR-17070)를 이 PR이 우발적으로 넓히지 않았음의 증명.\
설계 노트: "이 테스트가 붉어지면 수정이 SPR-17070 범위까지 번졌다는 scope-creep 경보다."\
예외 메시지(JDK 내부 클래스명)에는 단언하지 않는다 — 이식성 없는 구현 디테일이라서.

> **scope creep(범위 번짐)** — 고치기로 한 범위 밖까지 변경이 슬금슬금 번지는 현상.\
> 예: enum 배열만 고치려다 의도적으로 남겨 둔 as() 파생까지 직렬화 가능해지면 그것이 범위 번짐이다.

## T10. I4 가드 — 비직렬화 경로의 JDK Type identity (전후 green)

직렬화 지원이 일반 경로에 대체물(surrogate)을 끼워 넣지 않았는지 — `getType()`의 rawType·인자가 여전히 raw JDK 객체와 `isSameAs`인지 고정한다.\
"생성 시점 wrapping" 류의 미래 리팩토링이 런타임 경로를 오염시키면 여기서 잡힌다.

> **대체물(surrogate)** — 원본 대신 끼워 넣은 대역 객체.\
> 예: 직렬화를 위해 JDK Type을 프록시로 감싸 두면, 직렬화와 무관한 평소 호출에도 그 프록시가 튀어나온다.

## RF4. 파생 후 직렬화 — 가드 (리뷰 루프 1 추가)

리뷰에서 추가된 이 가드는 파생 호출로 지연 캐시가 채워진 뒤의 직렬화를 요구한다.

```java
type.as(Collection.class); type.getSuperType(); type.getGenerics(); ...
ResolvableType read = testSerialization(type);
```

as() 등 파생을 호출하면 지연 캐시 필드들이 채워진다 — gh-36346이 그 필드들을 transient로 만들어 뒀지만, **그 사실을 고정하는 테스트가 없으면** 캐시가 비-transient로 되돌아가는 회귀를 못 잡는다.\
"직전에 어떤 메서드를 불렀는가에 따라 직렬화 성패가 갈리는" 종류의 재현 어려운 실패를 예방하는 가드.

> **지연 캐시(lazy cache)** — 처음 필요해질 때 계산해서 필드에 담아 두는 캐시.\
> 예: `getSuperType()`을 한 번도 안 부르면 그 필드는 null이고, 한 번 부르면 값이 채워진 채로 남는다.

## T11~T13. TypeDescriptor 층 — red

마지막 세 건은 한 층 위의 공개 팩토리 표면에서 같은 왕복을 요구한다.\
대상은 `TypeDescriptor.collection(List, valueOf(String))`·`map(...)`·`collection(List, null)`로, 사용자가 실제로 만나는 공개 팩토리 표면에서의 라운드트립.\
원소 null(T13)은 `getElementTypeDescriptor()==null` 보존까지 확인한다.

## 실측 요약

실행 결과는 blind 설계가 예측한 red 개수·항목과 정확히 일치했다.

- fix 전: **10건 red — blind 설계 예측과 개수·항목 정확 일치**, 가드 3건 green.
- fix 후(리뷰 반영 포함): 대상 스위트 전체 green, **spring-core 5,173 tests 0 failures**, upstream main 리베이스 후 재확인 green.
- 별도 실물 스모크: 팩토리 4케이스(collection/map/forClassWithGenerics/중첩) FAIL->OK 전환, 범위 밖(as() 파생)·C4(#37109) 소관은 불변.
