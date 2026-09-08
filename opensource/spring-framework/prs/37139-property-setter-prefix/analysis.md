# PR #37139 분석 — Property.resolveName() write 분기의 set 부분일치

> 기준: 커밋 `e8e293a7060` (author junhyeong9812, committer Sam Brannen, 2026-08-19,
> 마일스톤 7.1.0-M2). PR 자체는 **CLOSED**다 — #36911과 #37139가 각각 `PropertyTests.java`를
> 신규 생성해 충돌했고, 메인테이너가 이 커밋을 **수동 적용**한 뒤(내용 무변경, 저자 크레딧 유지)
> PR을 닫았다. main에서 `f067d40f0a6`(#36911) 바로 뒤에 얹혀 있다.
> 근거: 실파일 정독 + `e8e293a7060` diff + `docs/plans/2026-08-14/property-setter-startswith/`.
> 이 폴더의 README(서사)·structure(무대·워크플로우)·tests(테스트별)·gates(이해 게이트)와
> 중복을 피해, 이 문서는 **이름표 사전·단계 추적 표·계약 대조·기각된 대안**을 맡는다.

## 0. 결론

`Property#resolveName()`의 write 분기는 setter 여부를 `indexOf("set") == -1`로 판정했다.
`indexOf`는 토큰을 이름 어디서든 찾으므로 거부되는 것은 "`set`이 한 글자도 없는 이름"뿐이었고,
`offsetX(String)`·`upset(String)`처럼 `set`을 중간이나 끝에 품은 **비-setter가 조용히 통과해**
각각 `"x"`·`""`라는 무의미한 프로퍼티 이름을 만들었다. 수정은 판정을 `startsWith("set")`로
좁혀, setter가 아닌 write 메서드는 예외 없이 기존 `IllegalArgumentException("Not a setter
method")`로 일관되게 거부하게 한 것이다. #36911에서 리뷰 요청으로 분리된 스코프이며, 성격은
버그 수정이 아니라 **동작 강화(behavior change)** 다.

## 1. 무대

결함이 놓인 자리를 모듈에서 호출자까지 좁혀 가며 짚으면 다음과 같다.

- 모듈: `spring-core`, 패키지 `org.springframework.core.convert`.
- 파일: `spring-core/src/main/java/org/springframework/core/convert/Property.java`.
- 결함 지점: `resolveName()` (:135) 의 **write 분기** (:155-161). read 분기(#36911 무대)와
  같은 메서드 안에 있지만 구조가 다르다 — read에는 "규약 밖 이름이면 이름 전체를 쓴다"는
  폴백(:148-152)이 있고, **write에는 폴백이 없다**. `setXxx` 규약을 못 맞추면 거부가 유일한 답이다.
- 공개 진입 API: `Property(Class, Method, Method)` (:68). write 분기에 도달하려면
  `readMethod == null && writeMethod != null` + 이름 인자 미지정이라는 두 조건이 동시에
  필요하다.
- 누가 언제 부르나: 프로덕션 코드의 `new Property(...)` 넷은 모두 4-인자로 이름을 명시한다
  (`GenericTypeAwarePropertyDescriptor.java:195`,
  `ReflectivePropertyAccessor.java:152/:196/:254`). 특히 write 방향인
  `ReflectivePropertyAccessor.canWrite`(:254)도 gh-37123 이후 이름을 넘긴다. 따라서 **현재
  main에서 write 분기에 도달하는 프레임워크 내부 호출은 없고**, 도달 경로는 사용자·서드파티의
  3-인자 직접 호출과 테스트 코드뿐이다. 이것이 이 동작 강화의 blast radius가 작다고 말할 수
  있는 근거다.

## 2. 전체 메서드 그래프

생성자 진입에서 이름 확정까지, 그리고 확정된 이름이 소비되는 곳까지를 한 그림으로 펼치면
결함이 어느 줄에 있고 그 여파가 어디까지 가는지가 보인다.

```
[진입] new Property(objectType, null, writeMethod)                Property.java:68
   |
   v
Property(Class, Method read, Method write, String name)               :72
   |
   +-- [a] this.methodParameter = resolveMethodParameter()            :78 -> :182
   |          +-- resolveReadMethodParameter()  -> null (read 없음)    :201
   |          +-- resolveWriteMethodParameter() -> MethodParameter(write, 0)  :208
   |          +-- write != null 이므로 write 채택                      :198
   |          (타입은 여기서 정상적으로 확정된다 — 이름 결함과 무관)
   |
   +-- [b] this.name = (name != null ? name : resolveName())          :79
              |
              v
       resolveName()                                                  :135
              +-- readMethod != null ?  -> read 분기 (#36911 무대)     :136-154
              +-- writeMethod != null ?                               :155
              |     |
              |     +-- String methodName = writeMethod.getName()     :156
              |     +-- !methodName.startsWith("set") ?               :157   <-- 수정 지점
              |     |      -> throw IllegalArgumentException          :158
              |     +-- return uncapitalize(methodName.substring(3))  :160
              |
              +-- else -> IllegalStateException                       :163
                    (같은 조건을 :187이 먼저 검사하므로 실제로는 그쪽이 먼저 터진다)

[소비] 확정된 이름이 실제로 쓰이는 곳
   getAnnotations() :125 -> resolveAnnotations() :215
        +-- addAnnotationsToMap(map, getReadMethod())  -> null이라 skip  :219
        +-- addAnnotationsToMap(map, getWriteMethod()) -> setter 애노테이션 :220
        +-- addAnnotationsToMap(map, getField())                        :221  <-- 이름 소비
               -> getField() :238
                    +-- !hasLength(name) -> null            :240-242   ("upset" 케이스)
                    +-- findField(declaringClass, name)     :246       ("offsetX" -> "x" 케이스)
                    +-- uncapitalize/capitalize 폴백        :249/:251
                    +-- 전부 실패 -> null                    :255
   equals :271 / hashCode :280 도 name을 구성요소로 쓴다
   annotationCache :53 의 키가 Property 자신 -> 잘못된 이름이 캐시 키에도 섞인다
```

데이터 흐름: **write 메서드 이름(String) -> 통과/거부 판정(boolean) -> 프로퍼티 이름(String)**.
수정 전에는 판정과 이름 계산이 **같은 `indexOf` 결과 하나**에 묶여 있었다(`index`를 판정에도
쓰고 `+3`해서 substring 오프셋으로도 썼다). 수정은 그 결합을 끊어 판정은 `startsWith`, 오프셋은
상수 3으로 분리한다.

## 2.5 핵심 이름표 사전

위 그래프에 등장한 이름 하나하나가 무엇을 맡고 언제 불리는지를 다음 표에 모았다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `Property(Class, Method, Method)` :68 | 이름 없이 카드를 만드는 3-인자 생성자 | (타입, read, write) -> Property | 사용자·서드파티·테스트 | write 분기에 도달하는 **유일한 입구** |
| `writeMethod` :59 | 쓰기 접근자(@Nullable) | — | 생성자 인자 | 이 분기의 입력. `readMethod`가 null이어야만 여기까지 온다 |
| `readMethod` :57 | 읽기 접근자(@Nullable) | — | 생성자 인자 | **null이 아니면 write 분기가 실행되지 않는다** — 테스트 헬퍼가 null로 고정하는 이유 |
| `resolveName()` :135 | 접근자 이름에서 논리 이름 유도 | read/write -> String | 생성자 :79에서만 | 결함이 살던 메서드 (read/write 두 분기 각각 결함이 있었다) |
| `methodName` (지역, :156) | write 메서드의 실제 이름 원본 | `writeMethod.getName()` | write 분기 진입 직후 | 수정이 도입한 지역변수. 수정 전에는 `getName()`을 두 번 호출했다 |
| `index` (수정 전 지역변수) | `indexOf("set")` 결과이자 substring 오프셋 | String -> int | 수정 전 write 분기 | **결함의 실체** — 판정(`== -1`)과 오프셋(`+3`)을 겸했다 |
| `startsWith("set")` :157 | 접두사 시작 판정 | String -> boolean | 수정 후 write 분기 | 판정만 담당. 거부 집합을 "set으로 시작하지 않는 전부"로 넓힌다 |
| `substring(3)` :160 | 접두사 3글자 제거 | String -> String | 판정 통과 후 | 오프셋이 상수라 계산 실수 여지가 사라진다 |
| `StringUtils.uncapitalize` :160 | 첫 글자 소문자화 | String -> String | substring 직후 항상 | `"Name"` -> `"name"`. 값 계산의 마지막 단계 |
| `IllegalArgumentException("Not a setter method")` :158 | 거부 신호 | — | 판정 실패 시 | **메시지가 전후 동일** — 새 거부가 기존 진단과 같은 얼굴로 나온다 |
| `IllegalStateException("Property is neither readable nor writable")` :163 | read·write 둘 다 없음 | — | 마지막 else | 실제로는 :187의 같은 예외가 먼저 터진다(:78이 :79보다 먼저 실행) |
| `resolveMethodParameter()` :182 | 타입 정보 결정 | read/write -> MethodParameter | 생성자 :78 — **이름보다 먼저** | 이름이 오염돼도 타입은 정상 -> 오류가 조용해지는 구조적 이유 |
| `this.name` :61 | 확정된 논리 이름, `final` | — | 생성자 :79에서 1회 | 잘못된 이름을 나중에 고칠 여지가 없다 -> 판정은 생성 시점에 엄격해야 한다 |
| `getField()` :238 | 이름으로 backing field 조회 | name -> Field 또는 null | resolveAnnotations :221 | 오염된 이름의 실피해 지점. 실패해도 예외 없음 |
| `hasLength(name)` 가드 :240 | 빈 이름이면 조회 생략 | String -> boolean | getField 첫 줄 | `upset` -> `""` 케이스가 여기서 조용히 끝난다 |
| `equals` :271 / `hashCode` :280 | 동일성 판정 | — | `annotationCache` 조회 시 | `name`을 구성요소로 쓰므로(:275, :282) 오염이 캐시 키까지 전파된다 |
| `writeProperty(String)` (테스트 헬퍼) | write 전용 Property 생성 | 메서드 이름 -> Property | `PropertyTests` 4건 | read를 null로 고정해 write 분기를 강제로 태운다 |

## 3. 결함 경로 단계 추적

수정 전 write 분기는 다음 네 줄이었다(diff의 `-` 쪽).

```java
int index = this.writeMethod.getName().indexOf("set");
if (index == -1) {
    throw new IllegalArgumentException("Not a setter method");
}
index += 3;
return StringUtils.uncapitalize(this.writeMethod.getName().substring(index));
```

네 가지 이름 모양을 같은 단계표에 통과시키면 동작이 바뀌는 집합이 정확히 드러난다.

| 단계 | 정상: `setName` | 원래도 거부: `updateName` | 결함 A: `offsetX` | 결함 B: `upset` |
|---|---|---|---|---|
| 진입 | `new Property(TestBean.class, null, m)` | 동일 | 동일 | 동일 |
| :78 타입 해석 | `MethodParameter(m, 0)` — 정상 | 정상 | 정상 | 정상 |
| 수정 전 `indexOf("set")` | 0 | **-1** | **3** (o-f-f-**s-e-t**-X) | **2** (u-p-**s-e-t**) |
| 수정 전 판정 | 통과 | 거부 | **통과** (오탐) | **통과** (오탐) |
| 수정 전 `index += 3` | 3 | (미도달) | 6 | 5 |
| 수정 전 `substring(index)` | `"Name"` | — | `"X"` | `""` (길이 5 == 5, 경계) |
| 수정 전 최종 결과 | 이름 `"name"` | `IllegalArgumentException` | 이름 `"x"` | 이름 `""` |
| 수정 후 `startsWith("set")` | true | false | **false** | **false** |
| 수정 후 최종 결과 | 이름 `"name"` (불변) | 예외 (불변) | **예외** | **예외** |
| 수정 전 `getField()` 결과 | `name` 필드 조회 (원래 동작) | — | `findField("x")` 3변형 전부 실패 -> null (실필드 `offsetX`는 끝내 미발견) | :240 `hasLength("")` 실패 -> **조회 자체 생략**, null |
| 관측되는 증상 | 없음 | 없음 (정상 거부) | **무음 오탐 — 엉뚱한 이름의 카드가 완성됨** | **무음 오탐 — 빈 이름 카드** |

동작이 바뀌는 집합은 정확히 A·B가 속한 "`set`을 포함하되 `set`으로 시작하지 않는 이름"이다.
양 극단(정상 setter, `set`이 아예 없는 이름)은 전후 동일하다. 그리고 A와 B는 같은 결함에서
나오지만 **산출물의 성질이 다르다** — A는 "엉뚱하지만 그럴듯한 이름"이라 소비자가 조회
실패로 겪고, B는 "빈 이름"이라 `hasLength` 가드에 걸려 조회 시도조차 되지 않는다. 그래서
테스트도 둘을 따로 고정한다.

## 4. 계약

이 코드가 지키기로 한 약속을 하나씩 세우고 결함이 그중 무엇을 어겼는지 대조한다. 어긴
것은 거부 계약 하나이고, 나머지는 결함이 조용해진 구조적 전제다.

| 계약 | 출처 | 결함이 어겼는가 |
|---|---|---|
| write 분기는 `setXxx` 규약을 못 맞추는 write 메서드를 **거부한다** | :157-159의 예외 자체 + 메시지 "Not a setter method" | 예 — 거부 집합이 "set 토큰이 전혀 없는 이름"으로 좁혀져 있었다 |
| write 분기에는 read 분기 같은 폴백이 없다 | :155-161에 else 가지가 없음 | 아니오 — 이것은 전제다. 폴백이 없으므로 판정이 유일한 방어선이고, 판정이 느슨하면 곧바로 오염된 이름이 나온다 |
| 유도된 이름은 프로퍼티의 논리 이름이다 | `getName()` javadoc :90-92 ("The name of the property: for example, 'foo'") | 예 — `"x"`·`""`는 어떤 프로퍼티의 이름도 아니다 |
| 이름은 생성자에서 확정되고 `final`이다 | :61, :79 | 아니오 — 전제. 다만 이 전제 때문에 잘못된 이름을 사후 교정할 수 없어 **생성 시점 엄격성**이 요구된다 |
| 이름은 `equals`/`hashCode`의 구성요소다 | :275, :282 | 간접 — 오염이 `annotationCache`(:53) 키까지 전파된다 |
| 예외 메시지 "Not a setter method"는 사용자가 보는 진단이다 | :158 | 아니오 — 수정 전후 동일. 테스트가 메시지까지 단언해 거부 **경로**의 동일성을 요구한다 |
| 기존 테스트가 고정하던 것 | 이 PR 이전 write 분기를 겨눈 테스트는 **없었다**(`PropertyTests`가 신규 파일) | 회귀 그물이 없어 결함이 오래 숨었다 |

## 5. 수정안

### 5.1 채택된 수정 (커밋 `e8e293a7060`)

`Property.java:155-161`:

```java
		else if (this.writeMethod != null) {
			String methodName = this.writeMethod.getName();
			if (!methodName.startsWith("set")) {
				throw new IllegalArgumentException("Not a setter method");
			}
			return StringUtils.uncapitalize(methodName.substring(3));
		}
```

**왜 이 위치인가.** 판정과 오프셋 계산이 `index` 하나에 묶여 있던 것을 끊는 것이 수정의
핵심이다. 수정 전 코드는 `indexOf` 결과를 (1) 거부 판정(`== -1`)과 (2) substring 오프셋
(`+3`) 양쪽에 썼기 때문에, 판정을 고치면 오프셋도 함께 손봐야 했다. `startsWith`로 판정을
분리하면 통과한 이름은 반드시 0번에서 시작하므로 오프셋이 상수 3으로 확정된다 — 계산
실수 여지가 사라지고, 그 실수를 잡는 자리가 `resolveNameForSetter` 가드다.

read 분기(:142-152)와 대칭이 아니라는 점도 의도적이다. read 분기는 `startsWith` 실패 시
폴백(index = 0)으로 흘려보내지만 write 분기는 예외로 끊는다. 프로퍼티의 쓰기 경로에서
"규약 밖 이름"은 유효한 프로퍼티가 아니라 잘못된 인자이기 때문이다.

### 5.2 검토됐다가 기각된 대안

채택안에 이르기까지 네 가지 다른 길을 검토하고 각각 다른 이유로 접었다.

- **`set` + 대문자까지 요구(`settle` 구멍 막기).** `settle(String)`은 전후 모두 `"tle"`로
  해석되는 것이 이 수정의 남는 공백이다. 접두사 뒤 대문자를 강제하면 막을 수 있지만
  기각했다. 이유는 두 가지다. (1) JavaBeans 규약 자체가 `setURL` 같은 연속 대문자와
  단일 소문자 프로퍼티(`setA`)를 허용해 판정이 단순하지 않고, (2) 이 PR이 고치려는 결함은
  "부분일치"이지 "접두사 뒤 글자 종류"가 아니다. 한 PR = 한 논리 변경 원칙에 따라 공백을
  **PR 본문에 명시적으로 공개**하는 쪽을 택했고, 테스트로 못박지도 않았다 — 고치지 않은
  동작을 테스트로 굳히면 나중에 개선할 때 테스트부터 지워야 하기 때문이다.
- **거부 대신 read 분기처럼 이름 전체를 쓰기(관대 폴백).** `offsetX` -> `"offsetX"`.
  기각 이유는 계약이다. write 분기의 기존 계약은 거부이고(예외가 이미 있었다), 관대 폴백은
  "setter가 아닌 메서드도 프로퍼티 쓰기 경로로 인정"하는 훨씬 큰 의미 변경이 된다. 이해
  게이트 G1에서 사용자가 정확히 이 오해(read의 폴백 구조를 write로 전이)를 했고, 판정 기록에
  남아 있다.
- **#36911에 묶어서 함께 머지.** 1차 커밋에는 실제로 묶여 있었고 리뷰(sbrannen)에서
  분리 요청을 받았다. 기각 이유는 리스크 등급이다 — read 분기 수정은 "틀린 이름을 옳은
  이름으로" 바꾸는 것이라 기존 호출이 계속 성공하지만, write 분기 수정은 **이전에 성공하던
  호출이 예외를 던지게** 만든다. 리뷰·롤백 단위를 분리해야 한다.
- **예외 대신 경고 로그 + 기존 동작 유지.** 검토 기록에는 없으나 구조상 가능한 선택지다.
  실제로 채택되지 않은 이유는 `Property`가 로거를 갖지 않는 순수 값 객체이고, 이름이
  `final`로 굳는 설계상 "경고하고 오염된 값을 굳히는" 것은 문제를 지연시킬 뿐이기
  때문이다. (이 항목은 문서화된 기각 기록이 아니라 구조에서 유도한 서술이다.)

## 6. 범위 밖과 인접 영향

이 수정이 건드리지 않은 인접 영역과, 그럼에도 알아 둬야 할 파급을 정리한다. 요지는 실제
영향 집합이 좁고 프레임워크 내부 호출은 전혀 걸리지 않는다는 것이다.

- **같은 패턴의 다른 위치 — 같은 메서드의 read 분기.** `indexOf("get")`/`indexOf("is")`가
  같은 부분일치 결함을 갖고 있었고 PR #36911이 처리했다(`f067d40f0a6`). 이 커밋이 그 바로
  뒤에 얹혀 있어, main에서는 `resolveName()`의 두 분기가 함께 `startsWith` 기반이 됐다.
- **남는 공백(의도적).** `settle(String)` 계열 — `set`으로 시작하지만 뒤가 소문자인 이름은
  전후 모두 `"tle"`로 해석된다. PR 본문에 "A remaining known gap, unchanged by this PR"로
  공개했다.
- **하위호환 — 영향받는 집합.** 정확히 "`set`을 포함하되 `set`으로 시작하지 않는 write
  메서드를 이름 없이 `Property`에 넘기는 호출"뿐이다. 그 호출은 이제 생성 시점에
  `IllegalArgumentException`을 받는다.
- **하위호환 — 프레임워크 내부는 무영향.** spring-beans는 이름을 명시하고, SpEL의 setter
  탐색은 원래 `set`+이름 형태를 찾으며(`ReflectivePropertyAccessor.findSetterForProperty`
  :413), gh-37123 이후 SpEL도 이름을 명시해 넘긴다. PR 본문이 든 유일한 예외 경로는 SpEL의
  Kotlin 지원이 `@JvmName`으로 개명된 setter를 노출하는 경우인데, 그것도 gh-37123으로
  이 코드 경로에서 벗어난다.
- **PR이 CLOSED인 이유는 거절이 아니다.** #36911과 이 PR이 각자 `PropertyTests.java`를
  신규 생성해 파일 충돌이 났고, 메인테이너가 커밋을 수동 적용(author 크레딧 유지)한 뒤
  PR을 닫았다. 코드 내용은 제출본과 무변경이다.
- **다루지 않은 것.** `resolveMethodParameter()`의 read/write 타입 선택(:191-197),
  `getField()`의 3변형 폴백(:246-253), `annotationCache` 키 설계는 이 PR의 범위 밖이며
  결함과도 무관하다.
