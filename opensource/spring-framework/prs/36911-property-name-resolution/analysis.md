# PR #36911 분석 — Property.resolveName()의 접두사 부분일치

> 기준: 머지 커밋 `f067d40f0a6` (2026-08-20, 마일스톤 7.1.0-M2, main 전용). 인용한
> `Property.java` 좌표는 머지 **후** 코드이며, 수정 전 코드는 diff의 `-` 쪽을 병기한다.
> 근거: 실파일 정독 + `f067d40f0a6` diff + 작업 폴더 `docs/plans/2026-08-14/pr36911-plain-accessor-review/`.
> 같은 폴더의 README(서사)·structure(무대 구조)·tests(테스트별 해설)·gates(이해 게이트)와
> 중복을 피해, 이 문서는 **이름표 사전·단계 추적 표·계약 대조·기각된 대안**을 맡는다.

## 0. 결론

`Property#resolveName()`은 읽기 메서드 이름에서 `get`/`is` 접두사를 `String#indexOf`로
찾아 잘라냈는데, `indexOf`는 접두사를 이름 **어디서든** 찾으므로 접두사 글자를 우연히
품은 무접두사 접근자(`budget()`, `issue()`)가 엉뚱한 위치에서 잘려 빈 문자열이나 틀린
이름이 되고, 그 이름으로 backing field를 찾는 `getField()`가 실패해 필드 애노테이션이
**예외 없이** 탈락했다. 수정은 접두사 판정을 `startsWith`로 좁히고, 같은 이름의 인스턴스
필드를 가진 무인자 비void 메서드(`isPlainAccessor`)이면 접두사를 벗기지 않게 한 것이다.
PR은 머지됐고(7.1.0-M2), 부수적으로 `isUrgent` 필드를 가진 `isUrgent()` getter가
`urgent`가 아니라 `isUrgent`로 해석되는 의도된 동작 변경이 함께 들어갔다.

## 1. 무대

결함이 살던 자리는 `spring-core`의 `Property` 한 클래스이고, 그중에서도 이름 인자를 비운
생성자만 도달하는 `resolveName()`의 read 분기다. 아래 항목은 그 무대의 좌표를 모듈에서
호출처까지 좁혀 간다.

- 모듈: `spring-core`, 패키지 `org.springframework.core.convert`.
- 파일: `spring-core/src/main/java/org/springframework/core/convert/Property.java`
  (`public final class Property`, :51).
- 공개 진입 API: 생성자 둘. `Property(Class, Method, Method)` (:68)과
  `Property(Class, Method, Method, String)` (:72). 둘 다 `public`이고, `Property`는
  `TypeDescriptor(Property)` (`TypeDescriptor.java:111`)·`TypeDescriptor.nested(Property, int)`
  (:725)의 입력이라 프레임워크 외부에서도 만들 수 있는 표면이다.
- 결함 지점: `private String resolveName()` (:135) 의 read 분기.
- 누가 언제 부르나: **이름 인자를 비운 호출만** `resolveName()`을 실행한다(:79의
  `name != null ? name : resolveName()`). 프로덕션 코드의 `new Property(...)` 호출처는
  현재 넷이며(`GenericTypeAwarePropertyDescriptor.java:195`,
  `ReflectivePropertyAccessor.java:152/:196/:254`) **넷 모두 4-인자로 이름을 명시**한다.
  SpEL 세 곳은 커밋 `fd95ab16baa`(gh-37123, 2026-08-10)로 그렇게 바뀐 것이고, 그 이전에는
  3-인자로 불러 이 결함의 실노출 지점이었다. 지금은 사용자·서드파티가 3-인자 생성자를
  직접 부르는 경로가 유일한 진입이다.

## 2. 전체 메서드 그래프

아래 그래프는 3-인자 생성자로 들어온 호출이 이름을 확정하고, 그 이름이 마지막에
`getField()`의 조회 키로 소비되기까지의 전 경로다. 오른쪽 숫자는 `Property.java`의 줄
번호이며, 결함은 `resolveName()`의 `index` 결정 한 칸에 있다.

```
[진입] new Property(objectType, readMethod, null)                 Property.java:68
   |      (3-인자 = name 인자 없음 -> 4-인자에 null 위임)              :69
   v
Property(Class, Method, Method, String name)                          :72
   |
   +-- [a] this.methodParameter = resolveMethodParameter()            :78 -> :182
   |          (타입 결정 — 이름과 무관, 결함의 영향 밖)
   |
   +-- [b] this.name = (name != null ? name : resolveName())          :79
              |
              v
       resolveName()                                                  :135
              |
              +-- readMethod != null ?                                :136
              |     |
              |     +-- String methodName = readMethod.getName()      :137
              |     |
              |     +-- methodName.startsWith("get") ?                :142
              |     |      -> index = isPlainAccessor(readMethod) ? 0 : 3   :143
              |     +-- else methodName.startsWith("is") ?            :145
              |     |      -> index = isPlainAccessor(readMethod) ? 0 : 2   :146
              |     +-- else -> index = 0                             :148-152
              |     |
              |     v
              |   StringUtils.uncapitalize(methodName.substring(index))     :153
              |
              +-- else writeMethod != null ? -> setter 분기            :155-161  (#37139 무대)
              +-- else -> IllegalStateException                        :163
                     |
                     v
              isPlainAccessor(Method method)                    static  :167
                     +-- static | 인자>0 | 반환 void  -> false          :168-171
                     +-- getDeclaringClass().getDeclaredField(name)     :174
                     |      +-- 예외 -> catch -> false                  :177-179
                     +-- return !Modifier.isStatic(field.getModifiers())  :175

[소비] 이름이 확정된 뒤 실제로 쓰이는 곳
   Property.getAnnotations()                                          :125
        -> resolveAnnotations()                                       :215
             +-- addAnnotationsToMap(map, getReadMethod())             :219
             +-- addAnnotationsToMap(map, getWriteMethod())            :220
             +-- addAnnotationsToMap(map, getField())                  :221  <-- 이름 소비
                    -> getField()                                      :238
                         +-- !hasLength(name) -> return null           :240-242  (빈 이름 무음 탈락)
                         +-- ReflectionUtils.findField(declaringClass, name)     :246
                         +-- findField(uncapitalize(name)) / findField(capitalize(name))  :249/:251
                         +-- 전부 실패 -> null                          :255  (틀린 이름 무음 탈락)
   Property.equals / hashCode 도 name을 구성요소로 쓴다                :271-283
   annotationCache 의 키가 Property 자신이므로 이름이 캐시 키에 섞인다  :53, :216
```

데이터 흐름 한 줄 요약: **읽기 메서드 이름(String) -> index(int) -> 프로퍼티 이름(String)
-> Field 조회 키**. 중간의 `index` 하나가 틀리면 마지막 조회가 조용히 빗나간다.

## 2.5 핵심 이름표 사전

이 흐름에서 헷갈리는 것은 "이름"이 세 겹으로 존재한다는 점이다. (1) 메서드의 실제 이름,
(2) 접두사를 벗긴 논리 이름, (3) 필드 조회에 쓰이는 키. 아래 각 항목은 그중 무엇을 들고
있는지를 밝힌다. 예시 값은 결함 케이스 `SampleRecord#issue()`와 정상 케이스
`TestBean#getName()`을 병기한다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 결함과의 관계 |
|---|---|---|---|---|
| `Property(Class, Method, Method)` :68 | 이름 없이 카드를 만드는 3-인자 생성자 | (타입, read, write) -> Property | 사용자·서드파티. 과거에는 SpEL도 | **결함의 유일한 진입** — 이 생성자만 이름 유도를 강제한다 |
| `Property(Class, Method, Method, String)` :72 | 정식 생성자 | 위 + name -> Property | 위 + 프레임워크 내부 4곳 | `name != null`이면 결함 경로를 아예 타지 않는다 |
| `this.name` :61 | 확정된 논리 이름. `final`이라 이후 수정 불가 | — | 생성자 :79에서 1회 확정 | 잘못된 이름이 **그 자리에서 굳는다** |
| `resolveName()` :135 | 접근자 메서드 이름에서 논리 이름 유도 | readMethod/writeMethod -> String | 생성자 :79에서만(private) | 결함이 살던 메서드 |
| `methodName` (지역, :137) | 읽기 메서드의 **실제 이름 원본** | `readMethod.getName()` | resolveName 진입 직후 | 수정 전에는 이 변수 없이 `getName()`을 세 번 호출했다 |
| `index` (지역, :138) | 잘라낼 접두사 길이 (0 / 2 / 3) | 분기 판정 -> int | :143/:146/:151에서 대입 | **결함의 실체** — 수정 전에는 "매칭 위치 + 접두사 길이"였다 |
| `isPlainAccessor(Method)` :167 | "이 메서드는 데이터 클래스의 무접두사 접근자인가" | Method -> boolean | :143·:146에서만(private static) | 수정이 추가한 판별. `issue()`·`getWidget` 컴포넌트를 살린다 |
| `field` (지역, :174) | 메서드와 **같은 이름**의 declared field | `getDeclaredField(method.getName())` | isPlainAccessor 내부 | record backing field가 컴포넌트와 동명이라는 사실이 판별 근거 |
| `Modifier.isStatic(...)` :168/:175 | static 오염 배제 | 수식자 int -> boolean | isPlainAccessor 앞뒤 | 동명 static 상수·static 메서드가 plain으로 오인되는 것을 막는다 |
| `StringUtils.uncapitalize` :153 | 첫 글자 소문자화 | String -> String | substring 직후 항상 | 결함 원인은 아니지만 결과값 계산의 마지막 단계 |
| `readMethod` :57 | 읽기 접근자(@Nullable) | — | 생성자 인자 | null이면 write 분기로 간다(#37139 무대) |
| `writeMethod` :59 | 쓰기 접근자(@Nullable) | — | 생성자 인자 | 이 PR은 손대지 않음(1차 커밋에서 조였다가 원복) |
| `methodParameter` :63 | 타입 정보 담당 | resolveMethodParameter() :182 | 생성자 :78 — **이름보다 먼저** | 이름이 틀려도 **타입은 정상** — 그래서 오류가 조용하다 |
| `resolveAnnotations()` :215 | read/write/field 애노테이션 병합 | — -> Annotation[] | `getAnnotations()` 최초 호출 시 | 이름의 유일한 실소비처 |
| `getField()` :238 | 이름으로 backing field 조회 | name -> Field 또는 null | resolveAnnotations :221 | **무음 실패 지점** — 못 찾으면 null을 돌려주고 끝 |
| `hasLength(name)` 가드 :240 | 빈 이름이면 조회 자체를 생략 | String -> boolean | getField 첫 줄 | `budget()`가 빈 이름이 되는 케이스가 여기서 조용히 끝난다 |
| `ReflectionUtils.findField` :246/:249/:251 | 이름 3변형(원본/uncapitalize/capitalize) 조회 | (Class, String) -> Field | getField 내부 | `sue` 같은 틀린 이름은 세 변형 모두 실패한다 |
| `declaringClass()` :258 | 조회 대상 클래스 결정 | read 우선, 없으면 write | getField :244 | 결함과 무관하나 조회의 다른 축 |
| `annotationCache` :53 | Property -> Annotation[] 캐시 | — | resolveAnnotations :216/:223 | 키가 `Property`이고 `equals`가 `name`을 포함(:275)하므로 잘못된 이름이 캐시 키에도 섞인다 |
| `CachedIntrospectionResults#isPlainAccessor` (spring-beans :345) | 같은 이름 판별식의 원본 | Method -> boolean | `introspectPlainAccessors` :337 | 수정이 **핵심 신호만** 미러한 참조 구현 |

## 3. 결함 경로 단계 추적

수정 전 판별식은 `indexOf("get")` -> (실패 시) `indexOf("is")` -> (실패 시) `index = 0`
3단이었고, 앞 두 단이 매칭에 성공하면 `index = 매칭위치 + 접두사길이`였다(전문은
`structure.md` 2절). 세 입력을 같은 단계표로 통과시키면 갈림이 값으로 드러난다. 정상 케이스는 `TestBean#getName()`,
결함 케이스는 `SampleRecord#budget()`(중간 매칭)과 `SampleRecord#issue()`(시작 매칭)다.

| 단계 | 정상: `getName()` | 결함 A: `budget()` | 결함 B: `issue()` |
|---|---|---|---|
| 진입 | `new Property(TestBean.class, getName, null)` | `new Property(SampleRecord.class, budget, null)` | `new Property(SampleRecord.class, issue, null)` |
| :78 타입 해석 | `MethodParameter(getName, -1)` — 정상 | 정상 | 정상 |
| 수정 전 `indexOf("get")` | 0 | **3** (b-u-d-**g-e-t**) | -1 |
| 수정 전 `indexOf("is")` | (미도달) | (미도달) | **0** (**i-s**-s-u-e) |
| 수정 전 `index` | 0+3 = 3 | 3+3 = **6** | 0+2 = **2** |
| 수정 전 `substring(index)` | `"Name"` | `""` (길이 6 == 6) | `"sue"` |
| 수정 전 최종 이름 | `"name"` | `""` | `"sue"` |
| 수정 후 `startsWith` 판정 | `get` 시작 -> :143 | `get`·`is` 둘 다 아님 -> :151 | `is` 시작 -> :146 |
| 수정 후 `isPlainAccessor` | `TestBean`에 `getName` 필드 없음 -> **false** | (호출 안 됨) | `SampleRecord`에 `issue` 필드 있음(record backing field) -> **true** |
| 수정 후 `index` | 3 | 0 | 0 |
| 수정 후 최종 이름 | `"name"` (불변) | `"budget"` | `"issue"` |
| :221 `getField()` 결과 (수정 전) | `name` 필드 없음 -> null (원래 그렇다) | :240 `hasLength("")` 실패 -> **즉시 null** | `findField("sue")` 3변형 전부 실패 -> **null** |
| :221 `getField()` 결과 (수정 후) | 동일 | `budget` 필드 발견 | `issue` 필드 발견 |
| 관측되는 증상 | 없음 | **컴포넌트 애노테이션 무음 탈락** | 동일 |

두 결함 케이스가 요구하는 수정 축이 서로 다르다는 점이 중요하다. A는 `indexOf ->
startsWith` 전환만으로 고쳐지지만, B는 `issue`가 실제로 `is`로 **시작하므로** 전환만으로는
여전히 `sue`가 된다 — `isPlainAccessor` 판별이 반드시 함께 필요하다. 두 축은 교체 불가능한
한 쌍이다.

## 4. 계약

이 무대가 지키기로 되어 있던 약속과 결함의 관계는 하나씩 대조해 보면 갈린다. 다음 표는
계약별로 출처와 위반 여부를 나란히 놓은 것이다.

| 계약 | 출처 | 결함이 어겼는가 |
|---|---|---|
| `Property`는 `java.beans.PropertyDescriptor` 없이 프로퍼티 하나를 서술한다 | 클래스 javadoc :36-50 | 아니오 (성격 진술) |
| 이름이 주어지면 그대로 쓰고, 없을 때만 유도한다 | :79 | 아니오 — 결함은 유도 경로에만 있다 |
| 읽기 메서드가 있으면 그 이름에서 논리 이름을 유도한다 | :136-153 | 예 — 유도 결과가 빈 문자열/틀린 이름이 될 수 있다 |
| 무접두사 record 스타일 접근자는 이름 전체가 프로퍼티 이름이다 | gh-26029가 추가한 `index = 0` 폴백 + 그 주석 | 예 — 접두사 글자를 품은 이름은 폴백에 도달조차 못 했다 |
| 애노테이션은 read/write/**field** 셋을 병합한 결과다 | :219-221 | 예 — 이름이 틀리면 field 몫이 조용히 빠진다 |
| 조회 실패는 예외가 아니라 `null`이다 | :240-242, :255 | 아니오 — 이것은 결함이 아니라 **전제**다. 이 전제 때문에 결함이 무음이 된다 |
| `name`은 `equals`/`hashCode`의 구성요소다 | :275, :282 | 간접 — 틀린 이름이 캐시 키 동일성까지 오염시킨다 |
| 기존 테스트가 고정하던 것 | 이 PR 이전 `PropertyTests`는 **존재하지 않았다**(파일 신규 생성, diff 기준 208줄 추가) | 그래서 회귀 그물이 없었고 결함이 오래 숨었다 |

새 판별식이 **새로 만든** 계약도 있다. "같은 이름의 인스턴스 필드가 있으면 접두사를 벗기지
않는다"는 규칙은 `java.beans.Introspector`와 갈리는 지점이며(`isUrgent` 필드 +
`isUrgent()` getter -> `isUrgent`), PR 본문 `## Note on impact`에 공개하고
`resolveNameForBooleanGetterBackedByFieldOfSameName` 테스트로 못박았다.

## 5. 수정안

수정은 채택된 한 벌과 검토 끝에 기각된 대안들로 나뉜다. 앞의 5.1은 실제로 머지된 코드와
그 배치 판단이고, 뒤의 5.2는 같은 결함을 다른 자리에서 고치려던 안들과 기각 사유다.

### 5.1 채택된 수정 (머지 커밋 `f067d40f0a6`)

read 분기 교체 — `Property.java:135-153`:

```java
	private String resolveName() {
		if (this.readMethod != null) {
			String methodName = this.readMethod.getName();
			int index;
			// For a get/is-prefixed name, strip the prefix unless the method is a
			// plain accessor for a data class property whose name starts with that
			// prefix, for example, a record component named "issue"
			if (methodName.startsWith("get")) {
				index = (isPlainAccessor(this.readMethod) ? 0 : 3);
			}
			else if (methodName.startsWith("is")) {
				index = (isPlainAccessor(this.readMethod) ? 0 : 2);
			}
			else {
				// Plain accessor method for a data class, for example, a Java record
				// component accessor such as name()
				index = 0;
			}
			return StringUtils.uncapitalize(methodName.substring(index));
		}
```

판별식 신설 — `Property.java:167-180`:

```java
	private static boolean isPlainAccessor(Method method) {
		if (Modifier.isStatic(method.getModifiers()) ||
				method.getParameterCount() > 0 || method.getReturnType() == void.class) {
			return false;
		}
		try {
			// Accessor method referring to instance field of same name?
			Field field = method.getDeclaringClass().getDeclaredField(method.getName());
			return !Modifier.isStatic(field.getModifiers());
		}
		catch (Exception ex) {
			return false;
		}
	}
```

**왜 이 위치인가.** 두 가지 배치 결정이 있다. 첫째, `isPlainAccessor` 호출을 `get`/`is`
분기 **안쪽**에 두었다. 무접두사 이름은 어차피 :151의 폴백에서 이름 전체를 쓰므로 판별
결과가 결과값을 바꾸지 못하고, 바깥에 두면 모든 호출에서 불필요한 리플렉션
(`getDeclaredField`)이 발생한다. 둘째, 판별을 접두사 검사보다 **뒤가 아니라 그 안에서
index 결정 직전**에 둔 것은 `issue`처럼 접두사가 진짜로 맞아떨어지는 이름과 컴포넌트
이름이 문자 그대로 `get`/`is`인 경우를 모두 살리기 위해서다 — 접두사 검사만 통과시키고
plain 판별을 나중에 하면 이미 잘린 뒤라 되돌릴 수 없다.

### 5.2 검토됐다가 기각된 대안

채택된 수정에 이르기까지 네 가지 대안이 검토되고 각각 다른 이유로 빠졌다. 아래는 대안과
기각 사유를 하나씩 정리한 것이다.

- **`isRecordAccessor()` — `Class#isRecord()` + `RecordComponent`로 판별.** 1차 커밋의
  구현이었다. 기각 이유는 리뷰(sbrannen, 2026-08-14)에서 명시됐다. Spring이 지원하려는
  "record 스타일 접근자"는 `java.lang.Record` 전용이 아니라 Kotlin data class와 손으로
  쓴 자바 데이터 클래스까지이며, 그 셋은 바이트코드상 같은 모양(private 필드 + 동명
  무인자 public 메서드)이다. 클래스의 정체가 아니라 **메서드의 모양**을 봐야 한다.
  실행으로 이 기각을 고정하는 테스트가 `resolveNameForGetterDeclaredOnRecord`
  (record 안의 손으로 쓴 `getWidget()`은 여전히 `widget`)와 데이터 클래스 3형제다.
- **`CachedIntrospectionResults#isPlainAccessor`(spring-beans :345-360) 전체 미러.**
  원본은 `Object.class`/`Class.class` 선언 배제와 `isInvalidReadOnlyPropertyType`
  (ClassLoader·ProtectionDomain·AutoCloseable 반환 배제, :362)까지 갖는다. 기각 이유는
  질문이 다르기 때문이다. spring-beans 쪽은 "이 메서드를 프로퍼티로 **승격**할까"를
  묻고(승격하면 introspection 표면이 넓어지므로 위험 타입을 걸러야 한다), spring-core
  쪽은 "이 이름에서 접두사를 **벗길까**"만 묻는다. 위험 타입 배제는 후자의 답을 바꾸지
  않는다. 대신 원본에 없는 **필드의 static 검사**(`return !Modifier.isStatic(...)`)를
  추가했는데, 동명 static 상수가 인스턴스 접근자를 plain으로 오인시키는 경로를 막기
  위해서다(`resolveNameForGetterWithStaticFieldOfSameName`).
- **setter 분기를 같은 커밋에서 함께 조이기.** 1차 커밋에는 들어 있었으나 리뷰 요청으로
  원복했다. 성격이 다르기 때문이다 — read 분기 수정은 "틀린 이름을 옳은 이름으로"이고,
  setter 수정은 "이전에 통과하던 호출이 예외를 던지게" 만드는 동작 강화다. 리뷰·롤백
  단위를 분리하려고 PR #37139로 떼어냈다(그 문서는 `../37139/analysis.md`).
- **SpEL이 이미 아는 이름을 넘기게 하기.** 이 PR의 실노출 경로 자체를 없애는 대안이다.
  기각이 아니라 **분리 처리**됐다 — sbrannen이 gh-37123으로 직접 가져가 커밋
  `fd95ab16baa`로 SpEL 세 호출을 4-인자로 바꿨다. 그럼에도 이 PR이 유효한 이유는
  `Property`의 3-인자 생성자가 `public`이라 외부 호출이 언제든 들어올 수 있어서다.

## 6. 범위 밖과 인접 영향

이 수정이 건드리지 않은 인접 영역과 하위호환의 두 얼굴을 정리하면, 영향 범위가 좁은
구조적 이유가 드러난다. 아래 항목은 같은 패턴의 다른 위치, 하위호환, 범위 밖 순이다.

- **같은 패턴의 다른 위치 — 같은 파일의 write 분기.** `indexOf("set")`가 정확히 같은
  부분일치 결함을 갖고 있었고, PR #37139가 처리했다(머지 커밋 `e8e293a7060`).
- **같은 패턴의 다른 위치 — spring-beans.** `CachedIntrospectionResults`는 접두사를
  문자열로 자르지 않고 `Introspector` 결과 + `introspectPlainAccessors`(:332-343)로
  프로퍼티를 모으므로 이 결함 패턴이 없다. 다만 두 모듈이 같은 자바 코드를 서로 다른
  규칙으로 읽고 있었다는 사실 자체가 이번 수정의 정당성 근거였다.
- **하위호환 — 무해한 쪽.** `getName()`/`isEnabled()`처럼 동명 필드가 없는 JavaBeans
  접근자는 `isPlainAccessor`가 false로 떨어져 전후 결과가 같다. 무접두사 이름
  (`name()`)도 전후 모두 :151 폴백으로 간다.
- **하위호환 — 바뀌는 쪽.** (1) 접두사 글자를 이름 중간에 품은 접근자는 결과가 바뀌지만
  이전 값이 빈 문자열/무의미 문자열이었으므로 실질 회귀 위험이 낮다. (2) `isUrgent` 필드로
  뒷받침되는 `isUrgent()`는 `urgent` -> `isUrgent`로 바뀐다 — `java.beans.Introspector`와
  갈리는 유일한 지점이고, PR 본문에 공개해 메인테이너 판단을 받았다.
- **영향 범위가 좁은 구조적 이유.** 현재 프레임워크 내부의 `new Property(...)` 넷은 모두
  이름을 명시하므로 `resolveName()`에 도달하지 않는다. 즉 이 수정은 공개 API 표면의
  정확성을 고치는 것이지, 내부 동작 경로를 바꾸는 것이 아니다.
- **다루지 않은 것.** `getField()`의 3변형 폴백(:246-253)이 만드는 관대함, `annotationCache`의
  키 설계, `resolveMethodParameter()`의 read/write 타입 선택(:191-197)은 이 PR의 범위 밖이며
  결함과도 무관하다.
