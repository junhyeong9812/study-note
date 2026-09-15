# PR #37153 — Include enum array attributes in TypeNotPresentException probing

## 0. 정향

이 문서는 `spring-core` annotation 처리의 `AttributeMethods` 수정 PR을 처음부터 이해하기 위한 해설이다.\
"annotation이 참조하는 enum 상수가 런타임에 없을 수 있다"는 전제가 낯설다면 [enum 상수의 이름 저장과 지연 해석](enum-annotation-name-resolution.md)과 [classpath 버전 스큐](classpath-version-skew.md)를 먼저 읽는 것이 좋다.\
다 읽으면 "왜 단일 enum 속성과 enum 배열 속성이 같은 오염에 다르게 반응했는가"와 "1줄 fix가 어떤 경로로 그 비대칭을 없애는가"를 설명할 수 있어야 한다.

> **annotation 속성(attribute)** — annotation에 붙은 괄호 안의 값 하나하나. 문법상으로는 파라미터 없는 메서드로 선언된다.\
> 예: `@RequestMapping(method = GET)`에서 `method`가 속성이고, 선언은 `RequestMethod[] method();`다.

> **오염된 annotation** — 컴파일 시점에는 존재했지만 지금 실행 중인 classpath에는 없는 값을 가리키는 annotation.\
> 예: `@Foo(BLUE)`로 컴파일했는데 실행 시점의 enum에서 `BLUE`가 삭제돼 있는 경우.

같은 폴더의 심화 문서: [probe 패턴](probe-pattern.md) · [테스트 해설](tests.md) · [리뷰 과정](review.md)

## 1. 배경 — AttributeMethods는 왜 존재하나

Spring의 annotation 처리(`MergedAnnotations`, `AnnotatedElementUtils` 등)는 클래스에 붙은 annotation을 대량으로 훑는다.\
그런데 JDK의 annotation 값 해석은 지연(lazy)이다.\
`Class` 속성이 가리키는 타입이 classpath에 없거나, enum 속성이 가리키는 상수가 로드된 enum에 없으면, annotation 객체 생성 시점이 아니라 **속성을 읽는 순간에** `TypeNotPresentException`/`EnumConstantNotPresentException`이 터진다.

> **지연 해석(lazy resolution)** — 값을 저장해 둘 때가 아니라 꺼내 쓸 때 비로소 실제 대상으로 바꿔 보는 방식.\
> 예: 클래스 파일에는 `"BLUE"`라는 **이름**만 적혀 있고, 그 이름을 실제 enum 상수로 바꾸는 일은 `value()`를 부르는 순간에 일어난다.

> **TypeNotPresentException** — annotation의 `Class` 속성이 가리키는 타입을 classpath에서 못 찾았을 때 읽는 순간 터지는 예외.\
> 예: `@Foo(Gone.class)`인데 `Gone` 클래스가 배포본에서 빠졌다면 `foo.value()`를 부를 때 터진다.

> **EnumConstantNotPresentException** — 같은 일이 enum 상수에 일어났을 때 터지는 예외.\
> 예: `@Foo(BLUE)`인데 로드된 enum에 `BLUE`가 없으면 `foo.value()`를 부를 때 터진다.

`AttributeMethods`는 이 시한폭탄에 대한 방어 장치다.\
annotation 타입별로 속성 메서드를 정리하면서, "늦게 터질 수 있는 타입"(`Class`, `Class[]`, enum)의 속성에 `canThrowTypeNotPresentException` 플래그를 세운다.\
스캔 경로(`AnnotationsScanner.getDeclaredAnnotations`)는 `canLoad()`로 플래그 선 속성을 **미리 한 번 실호출(probe)** 해 보고, 예외가 나면 그 annotation을 스캔 결과에서 통째로 제외한다(warn 로그).\
원조 동기는 javadoc에 남아 있는 Google App Engine의 지연 `Class` 실패였다.

> **probe(사전 시험 호출)** — 진짜로 쓰기 전에 "부르면 터지나" 한 번 불러 보고 결과값은 버리는 검사.\
> 예: `canLoad()`가 `value()`를 호출해 놓고 반환값을 받지 않는다 — 예외가 나는지만 보려는 것이다.

> **스캔(scan)** — 클래스·메서드·필드에 선언된 annotation을 차례로 읽어 모으는 작업.\
> 예: 컴포넌트 스캔이 패키지 밑 클래스를 훑으며 `@Component`가 붙었는지 확인하는 과정.

## 2. 수정 전 동작 — enum만 배열이 빠진 비대칭

플래그 계산식은 이랬다.

```java
this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class || type.isEnum());
```

`Class`는 스칼라·배열을 모두 다루는데 enum은 `type.isEnum()`(스칼라)뿐이다.\
공교롭게도 바로 윗줄의 nested annotation 검사는 `type.isAnnotation() || (type.isArray() && type.componentType().isAnnotation())`로 배열까지 다루고 있어, 같은 생성자 안에서도 enum만 배열이 빠진 비대칭이었다.

> **스칼라(scalar)** — 배열이 아닌 값 하나.\
> 예: `Class value()`는 스칼라, `Class[] value()`는 배열이다.

> **nested annotation(중첩 annotation)** — annotation의 속성 값으로 또 다른 annotation이 들어간 것.\
> 예: `@ComponentScan(filters = @Filter(type = ASSIGNABLE_TYPE))`의 `@Filter`.

같은 클래스 안에서 네 종류의 속성이 이 판정식을 지나는데, 세 갈래는 probe로 넘어가고 한 갈래만 검사 없이 빠져나간다.

```text
@Foo 가 붙은 element 를 스캔한다
        |
        v
AnnotationsScanner.getDeclaredAnnotations(source)
        |
        v
AttributeMethods.forAnnotationType(Foo.class)    (타입당 1회, 캐시)
        |
        v
생성자 루프 :84 — 속성마다 "읽는 순간 터질 수 있나?" 판정
        |
        +-- Class value()          -> 플래그 true   -> probe 대상
        +-- Class[] value()        -> 플래그 true   -> probe 대상
        +-- ExampleEnum value()    -> 플래그 true   -> probe 대상
        +-- ExampleEnum[] value()  -> 플래그 false  -> probe 제외   <== 버그 분기
        |
        v
canLoad(annotation, source) :102       (인스턴스를 만날 때마다)
        |
        +-- 플래그 true 인 속성 -> 실호출
        |       |
        |       +-- 예외 발생 -> warn 로그 -> return false -> 스캐너가 그 자리를 null 로 비움
        |       +-- 정상 반환 -> 다음 속성으로
        |
        +-- 플래그 false 인 속성 -> 건너뜀 -> 예외를 볼 기회가 없다 -> return true
```

네 갈래가 같은 기계장치를 지나는데 갈림은 `:84` 판정 하나에서만 생긴다.\
enum 배열은 실호출이 없으므로 "예외가 안 났다"가 아니라 **예외가 날 기회가 없었다**.

결과: enum **배열** 속성은 probe 대상이 아니므로, 오염된 annotation(런타임 enum에 없는 상수를 참조)이 `canLoad()`를 — 검사 없이 — 통과한다.

## 3. 무엇이 문제였나 — 세 갈래 누출 (실측)

v1 enum(BLUE 있음)으로 컴파일한 annotation을 v2 enum(BLUE 제거)으로 실행하는 재현에서, 단일 enum 속성과 enum 배열 속성이 이렇게 갈렸다.

| | 단일 enum 속성 | enum 배열 속성 (수정 전) |
|---|---|---|
| `isPresent()` | false + warn 로그 (필터링, 설계 의도) | **true** — 오염된 annotation이 정상 행세 |
| `asMap()` | 빈 맵 (missing) | **`{value=EnumConstantNotPresentException 객체}`** — 예외 객체가 값으로 들어간 맵 |
| `getEnumArray`/`synthesize().value()` | `NoSuchElementException` (missing 계약) | **raw `EnumConstantNotPresentException`** 누출 |

같은 오염을 두 형태의 속성에 나란히 걸면 이렇게 보인다.

```text
같은 입력: BLUE 를 가리키는 annotation, 런타임 enum 에는 BLUE 가 없다

  ExampleEnum value()  (단일 enum)          ExampleEnum[] value()  (enum 배열, 수정 전)
  +-------------------------------+          +-------------------------------+
  | probe 실행 -> 예외 관측       |          | probe 없음 -> 예외 못 봄      |
  | isPresent() = false           |          | isPresent() = true            |
  | asMap()     = {}              |          | asMap() = {value=예외 객체}   |
  | value()     = NoSuchElement   |          | value() = 예외 그대로 누출    |
  +-------------------------------+          +-------------------------------+
    -> "없는 것"으로 격리(설계대로)             -> 오염된 값이 조용히 하류로 간다
```

왼쪽은 실패를 관측해서 격리한 것이고, 오른쪽은 실패를 관측하지 못해 통과시킨 것이다.

특히 `asMap()` 행이 가장 나쁘다.\
예외가 나는 것이 아니라 **오염된 값이 조용히 하류로 흘러가는** silent corruption이라, `AnnotationAttributes` 기반 소비자(빈 이름 결정, `@Qualifier` 매칭 등)는 엉뚱한 곳에서 `ClassCastException`으로 죽는다.\
JDK 자체는 단일/배열을 똑같이 취급하므로(둘 다 읽는 순간 예외), 이 비대칭은 Spring이 만든 것이었다.

> **silent corruption(무음 오염)** — 에러가 나지 않은 채 잘못된 값이 그대로 다음 단계로 흘러가는 실패.\
> 예: 맵에 enum 배열 대신 예외 객체가 들어 있는데 호출자는 그걸 모른 채 캐스팅하다 한참 뒤에 죽는다.

## 4. 수정 해설 — 1줄, 그리고 왜 그 1줄이면 충분한가

수정은 판정식에 배열 가지 하나를 더하는 것이 전부다.

```java
this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class ||
		type.isEnum() || (type.isArray() && type.componentType().isEnum()));
```

판정식이 무엇을 받아들이는지가 이렇게 달라진다.

```text
수정 전 판정식 :84                          수정 후 판정식 :84-85
+----------------------------+             +----------------------------+
| Class          -> true     |             | Class          -> true     |
| Class[]        -> true     |             | Class[]        -> true     |
| ExampleEnum    -> true     |             | ExampleEnum    -> true     |
| ExampleEnum[]  -> false    |             | ExampleEnum[]  -> true     | <- 추가된 가지
| String[]       -> false    |             | String[]       -> false    |
+----------------------------+             +----------------------------+
  -> Class 는 배열까지 보는데                  -> Class 와 같은 모양으로 맞춰졌고
     enum 만 스칼라에서 끊긴다                    enum 아닌 배열은 그대로 제외된다
```

바로 윗줄 nested annotation 관용구를 그대로 재사용했다.\
이 플래그의 소비처는 `canLoad()`/`validate()`(같은 클래스)와 `AnnotationsScanner`(canLoad 호출) 셋뿐이고, 셋 모두 "플래그가 서 있으면 probe한다"는 게이트로만 쓰므로, 변경 효과는 "probe 대상 확대" 하나로 국한된다.\
annotation 멤버는 다차원 배열이 문법상 불가능하므로 `componentType()` 1단계 검사로 완결이다.

> **게이트(gate)** — 뒤 단계를 실행할지 말지만 정하는 조건 검사. 값을 바꾸지 않는다.\
> 예: `if (플래그) invoke(...)`에서 플래그는 호출 여부만 정하고 호출 결과에는 관여하지 않는다.

> **componentType()** — 배열 클래스에게 "원소의 타입은 무엇이냐"를 묻는 리플렉션 메서드.\
> 예: `ExampleEnum[].class.componentType()`은 `ExampleEnum.class`다.

수정 후 enum 배열도 단일 enum과 동일하게 정리된다.\
스캔 단계에서 probe -> 예외 관측 -> warn 로그 + 필터링 -> `isPresent()==false`, `asMap()=={}`, typed 접근은 missing-annotation 계약(`NoSuchElementException`)이다.

비용: probe 플래그 계산은 annotation 타입당 1회.\
실호출 비용은 기존 `Class[]` probe와 같은 종류이며 enum 배열 속성에만 추가된다(스캐너의 `declaredAnnotationCache`가 반복 빈도를 제한하지만, 비용을 없애는 것은 아니다 — 캐시 미스마다 발생).

## 5. 검증

검증은 단위 테스트, 패키지 전체 스위트, 실물 재현 세 층으로 쌓았다.

- test-first: 테스트 5건을 먼저 넣어 3건 red(플래그·canLoad 실패·validate 실패) 확인 -> fix 1줄로 21/21 green.\
  상세는 [tests.md](tests.md).
- annotation 패키지 전체 스위트 733 tests, 0 failures.
- 실물 스모크: v1/v2 enum 2단 컴파일 데모로 수정 전 3갈래 누출과 수정 후 필터링을 모두 실측(§3 표).

> **test-first(red/green)** — 고치기 전에 먼저 테스트를 넣어 실패(red)를 눈으로 본 뒤 고쳐서 통과(green)시키는 순서.\
> 예: fix 없이 돌려 3건이 실패하는 것을 확인했기에, 그 3건이 진짜로 이 결함을 잡고 있다는 근거가 된다.

## 6. 교훈

이 한 줄짜리 수정이 남긴 것은 결함을 찾는 법, 정상 판정의 기준, 그리고 fix의 성격 셋이다.

1. **대칭 결함은 같은 식 안에서 찾아라.**\
   "단일 X는 다루는데 X[]가 빠졌다"는 패턴은 바로 윗줄(nested annotation)이 정답 관용구를 이미 들고 있었다.\
   리뷰에서도 같은 질문이 나왔다: 이 식에 아직 빠진 계열은 없나?\
   (nested annotation 자체의 probe 누락 가능성 — 후속 조사로 분리, [review.md](review.md) 참조.)
2. **"에러 없이 돈다" ≠ 정상.**\
   수정 전 `asMap()`은 예외 없이 오염된 맵을 돌려줬다.\
   예외보다 silent corruption이 더 나쁘다.
3. **필터링의 의미론.**\
   Spring은 로드 불가 annotation을 "없는 것"으로 취급하기로 설계했다.\
   fix는 새 동작을 만든 게 아니라 기존 의미론을 배열까지 확장한 것이다.
