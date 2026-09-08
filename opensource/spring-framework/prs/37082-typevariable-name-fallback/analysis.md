# PR #37082 분석 — ResolvableType 타입 변수 이름 폴백의 과잉 매칭

> 작성일: 2026-08-27 · 기준: PR base `1502ab0b20b`, PR head `1633f41727c` (spring-core)
> 목적: 착수 시점 관점의 설명 문서 — 전체 메서드 그래프, 이름표 사전, 결함 경로 단계 추적, 계약, 수정안.
> 같은 폴더: [README](README.md) · [테스트 해설](tests.md) · [실구조](structure.md) · [이해 게이트](gates.md).

## 0. 결론 먼저

`ResolvableType.resolveVariable()`의 마지막 폴백은 타입 변수를 **이름 문자열만으로** 매칭한다(base L966-971). 주석 스스로 "independent of generic declaration context"라고 밝히듯 선언 문맥을 보지 않으므로, 상속 관계가 전혀 없는 형제 인터페이스의 동명 변수나 클래스 변수를 가린 메서드 레벨 변수까지 매칭해 **틀린 타입**을 돌려준다.

수정은 폴백을 제거하지 않고 정당한 유일한 조건 — "찾는 변수를 선언한 것이 클래스이고, 지금 보고 있는 파라미터화 타입이 그 선언 클래스의 상위 타입일 때" — 를 걸어 subtype narrowing에만 허용하는 것이다(head L969-976, 2개 술어).

PR 상태: **OPEN, 리뷰 대기**(2026-07-22 제출, 라벨 `status: waiting-for-triage` / `in: core`, 코멘트·리뷰 없음, 2026-08-27 확인).

## 1. 무대 — 모듈·파일·클래스와 진입 API

무대는 `spring-core`의 `org.springframework.core` 패키지, 두 파일이다. 결함 본체는 `ResolvableType.java`의 `private` 메서드 `resolveVariable(TypeVariable)`(base L945-983)이고, 그 결과를 소비해 계층 전체를 훑는 상위 진입점이 `GenericTypeResolver.java`의 `resolveType(Type, Class)`(L154)와 그 도우미 `resolveVariable(TypeVariable, ResolvableType)`(L210)이다.

공개 진입 API는 `GenericTypeResolver.resolveType(genericType, contextClass)`다. "이 제네릭 타입을 이 문맥 클래스에 대고 최대한 치환해 달라"는 요청이며, 자바 리플렉션이 `TypeVariable`(값 없는 이름)만 돌려주는 자리를 실제 타입으로 바꾸는 것이 목적이다.

누가 어떤 상황에서 부르나. 이슈 gh-36890이 보고한 실사용 경로는 `AbstractJackson2HttpMessageConverter#getJavaType(Type, Class)`다. Spring MVC가 `@RequestBody` 파라미터를 어떤 타입으로 역직렬화할지 정할 때 이 메서드를 거치므로, 해석이 틀리면 컨트롤러가 JSON 본문을 엉뚱한 타입으로 읽는다. 그 밖에도 `ResolvableType`은 `BeanFactory` 타입 매칭, 이벤트 리스너 제네릭 판별, 컨버터 선택 등 프레임워크 전역에서 쓰이지만, 이번 결함이 도달하는 폴백은 뒤에서 볼 조건 때문에 **최상위 선언 + owner 없음** 조합에서만 실행된다.

이 폴백 자체는 결함이 아니라 앞선 수정의 산물이다. gh-36890 수정(커밋 `9130ded96f4`, Juergen Hoeller, 2026-06-22)이 첫 번째 루프를 이름 비교에서 **변수 동일성 비교**로 승격시키면서, 그것만으로는 깨지는 케이스(`ResolvableTypeTests.narrow()`)를 살리려고 이름 비교를 뒤쪽 폴백으로 밀어 둔 것이다. 이 PR은 그 후속으로 폴백의 적용 범위를 좁힌다.

## 2. 전체 메서드 그래프

### 2.1 진입점부터 결함 지점까지

공개 진입점에서 결함이 사는 private 메서드까지는 어댑터 하나를 사이에 둔 네 단계다.

```
 GenericTypeResolver.resolveType(genericType, contextClass)          GenericTypeResolver.java:154
   |-- genericType 이 TypeVariable 이면                                :156
   |     |-- resolveVariable(typeVariable, ResolvableType.forClass(contextClass))   :157
   |     |-- NONE 이면 ResolvableType.forVariableBounds(typeVariable) 로 폴백        :159-161
   |     +-- 그래도 NONE 이면 마지막 줄에서 genericType 을 그대로 반환                :207
   +-- genericType 이 ParameterizedType 이면 미해석 인자마다 같은 처리                :173-205
         |
         v
 GenericTypeResolver.resolveVariable(typeVariable, contextType)      :210
   |-- contextType.hasGenerics() 이면 asVariableResolver() 로 직접 질의   :212-224
   |     +-- 결과가 TypeVariable 이면 resolveType() 으로 계속 푼다        :219-221
   |-- contextType.getSuperType() 으로 재귀 (NONE 아니면 채택)            :226-232
   |-- contextType.getInterfaces() 를 **선언 순서대로** 재귀              :233-238
   +-- 전부 실패하면 ResolvableType.NONE                                 :239
         |
         v  (asVariableResolver -> DefaultVariableResolver -> source.resolveVariable)
 ResolvableType.DefaultVariableResolver.resolveVariable(v)           ResolvableType.java:1599
         |
         v
 ResolvableType.resolveVariable(TypeVariable variable)               :945   <<< 결함이 사는 메서드
   |-- variableToCompare = SerializableTypeWrapper.unwrap(variable)     :946
   |-- (1) this.type 이 TypeVariable      -> resolveType() 후 재귀       :947-949
   |-- (2) this.type 이 ParameterizedType -> 아래 네 단계                :950-972
   |        |-- resolved = resolve()  (null 이면 즉시 null)              :951-954
   |        |-- variables     = resolved.getTypeParameters()             :955
   |        |-- typeArguments = parameterizedType.getActualTypeArguments()  :956
   |        |-- 2a. 변수 **동일성** 비교 -> typeArguments[i]              :957-961
   |        |-- 2b. ownerType != null 이면 owner 로 재귀하고 **즉시 return**  :962-965
   |        +-- 2c. 변수 **이름만** 비교 -> typeArguments[i]              :966-971   <<< 결함
   |-- (3) this.type 이 WildcardType -> 한 단계 풀고 재시도               :973-978
   |-- (4) this.variableResolver 에게 위임                               :979-981
   +-- (5) null                                                         :982
```

### 2.2 데이터 흐름 — 세 배열이 자리로 짝지어진다

매칭은 선언된 변수 배열과 실인자 배열을 같은 인덱스로 짝짓는 작업이고, 판정 기준만 단계마다 다르다.

```
 resolved (Class)  ---getTypeParameters()--->  variables[]     "선언된 변수들"
 parameterizedType ---getActualTypeArguments()->  typeArguments[]  "그 자리에 채워진 실인자들"
                                                     |
 variableToCompare ("찾는 변수") ---- i 번째 자리에서 일치 판정 ----+
                                                     |
                                                     v
                             forType(typeArguments[i], this.variableResolver)  = 답
```

일치 판정이 2a에서는 `variables[i].equals(variableToCompare)`(이름 + `getGenericDeclaration()`), 2c에서는 `variables[i].getName().equals(variableToCompare.getName())`(이름만)이다. **같은 배열, 같은 인덱스, 다른 판정 기준** — 2c가 느슨해서 무관한 자리를 고른다.

### 2.3 결함이 전파되는 길

2c가 답을 만들어 내면 `DefaultVariableResolver`가 non-null을 돌려주고, `GenericTypeResolver.resolveVariable`은 그것을 성공으로 보아 **즉시 반환**한다(L218-223). 인터페이스 루프(L233-238)는 뒤 후보를 시도조차 하지 못한다. 즉 결함의 실질적 피해는 "틀린 답"이 아니라 "**틀린 답이 정답 탐색을 조기 종료시킨다**"는 것이다. 반대로 2c가 null을 돌려주면 루프가 다음 후보로 넘어가 동일성 매칭으로 정답을 찾는다 — 수정이 "답을 고치는" 대신 "모름을 반환하게 하는" 형태인 이유다.

## 2.5 핵심 이름표 사전

이 흐름에서 헷갈리는 것은 "변수"가 세 얼굴로 등장한다는 점이다: 찾고 있는 변수, 지금 보고 있는 타입이 선언한 변수들, 그리고 그 자리에 채워진 실인자들. 아래 표는 각 이름이 그중 무엇인지를 명시한다. (예시 값은 결함 케이스 A = `TopCreate`의 `I`를 `TopSearch<String, Long>`에 대고 물을 때 / 정상 케이스 D = `Box`의 `E`를 `Container<String>`에 대고 물을 때)

| 이름표 | 무엇인가 / 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `resolveVariable(TypeVariable)` (`ResolvableType.java:945`) | **찾는 변수를 이 타입의 문맥에서 실인자로 바꾼다.** `private` | `TypeVariable` -> `ResolvableType` 또는 null | `DefaultVariableResolver`(:1599), 자기 재귀(:948, :964, :974) | 결함 본체 |
| `variable` (파라미터) | 호출자가 찾아 달라고 넘긴 변수. 직렬화 래퍼가 씌워져 있을 수 있다 | | | 원본 |
| `variableToCompare` (`:946`) | `SerializableTypeWrapper.unwrap(variable)` — 래퍼를 벗긴 **진짜 `TypeVariable`**. 이후 모든 비교의 좌변 | `TypeVariable` -> `TypeVariable` | `:946`에서 1회 | 벗겨야 `equals`가 성립한다. gh-36890 수정이 도입 |
| `this.type` (`:106`) | 이 `ResolvableType`이 감싼 원본 `java.lang.reflect.Type` | | 생성 시 고정 | `ParameterizedType`일 때만 결함 경로에 들어간다 |
| `this.variableResolver` (`:121`) | "내가 모르는 변수는 이 사람에게" 위임처 | | 생성 시 고정 | 2c가 null을 주면 (4)에서 이쪽으로 넘어간다 |
| `resolved` (`:951`) | `resolve()` 결과 = 이 파라미터화 타입의 **raw 클래스**. null이면 즉시 포기 | -> `Class<?>` | `resolveVariable` 안 | 수정이 추가한 술어의 좌변. A에서 `TopSearch`, D에서 `Container` |
| `variables` (`:955`) | `resolved.getTypeParameters()` — **지금 보고 있는 타입이 선언한** 변수 배열 | -> `TypeVariable<?>[]` | 같은 메서드 | A에서 `[I, O]` of `TopSearch` (찾는 `I`와 **다른 인스턴스**) |
| `typeArguments` (`:956`) | `getActualTypeArguments()` — 그 자리에 실제로 채워진 타입들 | -> `Type[]` | 같은 메서드 | A에서 `[String, Long]`. 잘못 고르면 `String`이 답이 된다 |
| 2a 동일성 루프 (`:957-961`) | `variables[i].equals(variableToCompare)` — `TypeVariable`의 equality는 **이름 + `getGenericDeclaration()`** | -> 매치 시 답 | 항상 먼저 | 정확한 매칭. A에서 실패(선언이 `TopSearch` vs `TopCreate`) |
| `ownerType` (`:962`) | `parameterizedType.getOwnerType()` — 중첩 타입의 바깥 클래스. 최상위 선언이면 **null** | -> `Type` 또는 null | 2a 실패 후 | **결함 발동 조건.** non-null이면 즉시 return 하므로 2c에 도달하지 않는다 |
| 2c 이름 루프 (`:966-971`) | `variables[i].getName().equals(...)` — 선언 문맥 무시 | -> 매치 시 답 | owner가 null일 때만 | **결함 지점.** A에서 `"I" == "I"` -> `String` |
| `declaringClass` (head `:969`, 신설) | `variableToCompare.getGenericDeclaration()`이 `Class`일 때 그 클래스 | -> `Class<?>` | 수정 후 2c 진입 판정 | 술어 (1). `Method`/`Constructor` 선언은 여기서 탈락 |
| `getGenericDeclaration()` (JDK) | 이 변수를 선언한 주체. `Class` / `Method` / `Constructor` 중 하나 | -> `GenericDeclaration` | 수정이 추가 | 메서드 레벨 shadowing을 가르는 유일한 신호 |
| `isAssignableFrom(declaringClass)` (JDK) | `resolved`가 선언 클래스의 **상위 타입**인가 | -> `boolean` | 수정이 추가 | 술어 (2). D에서 `Container.isAssignableFrom(Box)=true`, A에서 `TopSearch.isAssignableFrom(TopCreate)=false` |
| `resolveType()` (`:920`) | 한 단계만 푼다. `TypeVariable`이면 resolver 질의 후 bounds 폴백 | -> `ResolvableType` | (1)(3), `GenericTypeResolver:220` | 2c가 null을 준 뒤 흐름이 지나가는 경로 |
| `resolveBounds(Type[])` (`:1467`) | bounds 첫 원소를 돌려주되 **`Object.class`면 null** | -> `Type` 또는 null | `forVariableBounds`(:1463), `resolveType`(:940) | 메서드 `T`의 bound가 `Object`뿐이라 최종 미해석이 되는 이유 |
| `forVariableBounds(TypeVariable)` (`:1463`) | 변수의 bound로 만든 `ResolvableType` | -> `ResolvableType` | `GenericTypeResolver:160, :184` | 마지막 그물. bound가 `Object`면 `NONE` |
| `asVariableResolver()` (`:1052`) | 자기 자신을 `VariableResolver`로 감싼 어댑터. `NONE`이면 null | -> `VariableResolver` | `GenericTypeResolver:213`, `forType(Type, ResolvableType)`(:1497) | 상위 계층이 결함 메서드에 닿는 통로 |
| `DefaultVariableResolver` (`:1590`) | `source.resolveVariable(v)`로 통째로 되묻는 어댑터 | | `asVariableResolver`가 생성 | 결함 메서드의 유일한 외부 호출자 |
| `TypeVariablesVariableResolver` (`:1611`) | 미리 짝지어 둔 `variables[]`/`generics[]` 표에서 **동일성만으로** 조회 | | `forClassWithGenerics`(:1191-1192) | 이쪽에는 이름 폴백이 **없다** — 수정 방향이 이 관례와 일치한다는 근거 |
| `SyntheticParameterizedType.getOwnerType()` (`:1665`) | 항상 null을 반환 | -> null | `forClassWithGenerics`가 만든 타입 | `forClassWithGenerics`로 만든 타입은 **반드시 2c에 도달한다** — 정상 케이스 D가 폴백에 의존하는 이유 |
| `forType(Type, ResolvableType owner)` (`:1494`) | owner를 resolver로 삼아 타입을 감싼다 | -> `ResolvableType` | `narrow()` 테스트, `getSuperType`(:520), `getInterfaces`(:549), `getGenerics`(:794) | 계층 탐색이 문맥을 물려주는 방법 |
| `GenericTypeResolver.resolveVariable(v, contextType)` (`:210`) | 문맥 클래스의 자기 자신 -> superType -> **인터페이스 선언 순서**로 후보를 시도 | -> `ResolvableType` 또는 `NONE` | `resolveType`(:157, :182) | 첫 성공을 답으로 삼으므로 2c의 오답이 탐색을 조기 종료시킨다 |
| `getInterfaces()` (`:538`) | 직접 구현 인터페이스를 `implements` 선언 순서대로 | -> `ResolvableType[]` | `GenericTypeResolver:233` | **후보 순서가 답을 바꾼다.** A에서 `TopSearch`가 먼저다 |
| `getSuperType()` (`:508`) | 직접 상위 클래스. 없으면 `NONE` | -> `ResolvableType` | `GenericTypeResolver:226` | shadowing 케이스에서 `TopRepo<String>`이 후보가 되는 경로 |
| `getGenerics()` (`:783`) / `getGeneric(int...)` (`:754`) | 제네릭 인자들. raw `Class`면 타입 파라미터를 자기 자신을 resolver로 감싸 돌려준다(:794) | -> `ResolvableType[]` | 정상 케이스 D의 진입점 | `narrow()`가 폴백에 닿는 경로 |
| `NONE` (`:95`) | "값 없음"을 null 대신 표현하는 싱글턴 | | 전역 | `GenericTypeResolver`는 `NONE`, `ResolvableType`은 `null`로 실패를 표현한다 — 두 층의 표현이 다르다 |

이 표에서 결함이 한 줄로 보인다. **2a는 `variables[i]` 전체를 비교하고 2c는 `getName()`만 비교하는데, 그 사이에 있는 유일한 방벽이 `ownerType != null`이라는 우연한 조건뿐이다.** 수정은 2c에 자기 자신의 정당성 조건을 붙여 그 우연 의존을 없앤다.

## 3. 결함 경로 단계 추적

네 케이스를 같은 형식으로 따라간다. A와 B는 결함, C는 결함이 **드러나지 않았던** 대조군, D는 폴백이 정당한 정상 케이스다. 픽스처는 실제 테스트가 쓰는 것과 같다.

케이스 A — 최상위 형제 인터페이스. `interface TopSearch<I, O> {}`, `interface TopCreate<I, O> { default O create(I body) { return null; } }`, `class TopController implements TopSearch<String, Long>, TopCreate<Long, Long> {}`에서 `TopCreate#create`의 파라미터 타입 `I`를 `TopController` 문맥으로 해석한다. 기대값은 `Long`이다.

| 단계 | 위치 | 수정 전 | 수정 후 |
|---|---|---|---|
| 문맥 진입 | `GenericTypeResolver:157` | `contextType = TopController`, `hasGenerics()=false` | 동일 |
| superType | `:226` | `Object` -> `NONE` | 동일 |
| 인터페이스 후보 1 | `:233` | `ifc = TopSearch<String, Long>` | 동일 |
| 2a 동일성 | `ResolvableType:957` | `TopSearch.I` vs `TopCreate.I` -> **false**(실측: `equals=false`) | 동일 |
| 2b owner | `:962` | `getOwnerType()=null`(실측) -> 통과 | 동일 |
| 2c 진입 판정 | head `:969` | (조건 없음) | `declaringClass=TopCreate`, `TopSearch.isAssignableFrom(TopCreate)=false`(실측) -> **건너뜀** |
| 2c 이름 비교 | `:966-971` | `"I"=="I"` -> `typeArguments[0]=String` | 실행되지 않음 |
| 반환 | | `String` (오답) | `null` -> `NONE` |
| 인터페이스 후보 2 | `:233` | **도달 못 함** | `ifc = TopCreate<Long, Long>` -> 2a 동일성 성공 -> `Long` |
| 최종 | | `String` | `Long` |

케이스 B — 메서드 레벨 변수 shadowing. `class TopRepo<T> { <T> T convert(Object o) {...} }`, `class TopStringRepo extends TopRepo<String> {}`에서 `convert`의 반환 타입(메서드 `T`)을 `TopStringRepo` 문맥으로 해석한다. 메서드 `T`는 호출 시점에야 정해지므로 클래스 문맥만으로는 해석될 수 없다.

| 단계 | 위치 | 수정 전 | 수정 후 |
|---|---|---|---|
| superType 후보 | `GenericTypeResolver:226` | `TopRepo<String>` | 동일 |
| 2a 동일성 | `ResolvableType:957` | 클래스 `T` vs 메서드 `T` -> false (선언이 `class TopRepo` vs `TopRepo.convert`, 실측) | 동일 |
| 2b owner | `:962` | `TopRepo`가 최상위라 null -> 통과 | 동일 |
| 2c 진입 판정 | head `:969` | (조건 없음) | `getGenericDeclaration()`이 `Method`(실측 `isClass=false`) -> **건너뜀** |
| 2c 이름 비교 | `:966-971` | `"T"=="T"` -> `String` | 실행되지 않음 |
| bound 폴백 | `GenericTypeResolver:160` | 도달 안 함 | `forVariableBounds` -> bounds `[Object]`(실측) -> `resolveBounds`가 null -> `NONE` |
| 최종 | `:207` | `String` (클래스 인자가 메서드 변수로 새어 들어감) | `genericType` 그대로 = `TypeVariable` (미해석) |

케이스 C — 대조군. 같은 구조를 **중첩 타입**으로 선언하면(`GenericTypeResolverTests` 안의 `Search`/`Create`/`Controller`) `getOwnerType()`이 `GenericTypeResolverTests.class`로 non-null이다(실측: `NEST Probe$Nested$Search ownerType=class Probe$Nested`). 2b에서 owner로 재귀한 뒤 **즉시 return** 하므로 2c에 도달하지 않고, owner 재귀는 null을 돌려주어 인터페이스 루프가 다음 후보로 넘어가 정답을 찾는다. 기존 회귀 테스트 `resolveTypeAgainstSameNamedVariables()`(base `GenericTypeResolverTests.java:263-267`)가 이 배치였기 때문에, gh-36890 수정 이후에도 초록이었지만 **문제의 코드 경로를 실행조차 하지 않았다.**

케이스 D — 정당한 subtype narrowing. `ResolvableTypeTests.narrow()`(base `ResolvableTypeTests.java:1413-1417`)가 그것이다.

```java
		ResolvableType type = ResolvableType.forField(Fields.class.getField("stringList"));
		ResolvableType narrow = ResolvableType.forType(ArrayList.class, type);
		assertThat(narrow.getGeneric().resolve()).isEqualTo(String.class);
```

`ArrayList`의 `E`를 `List<String>`에 대고 묻는다. 2a는 실패한다 — `ArrayList.E`와 `List.E`는 선언이 달라 서로 다른 `TypeVariable`이다(실측 `ArrayList E decl=class java.util.ArrayList`). `java.util.List`는 최상위라 owner도 null이다. 그러므로 이 케이스는 **오직 2c로만 답을 얻는다.** 수정 후에도 `declaringClass=ArrayList`이고 `List.isAssignableFrom(ArrayList)=true`(실측)이므로 폴백이 허용되어 `String`이 그대로 나온다. PR이 추가한 긍정 테스트 `resolveTypeVariableByNameWhenNarrowingParameterizedSupertype()`은 같은 성질을 최소 픽스처(`Container<E>` / `Box<E>`, 실측 `Container.isAssignableFrom(Box)=true`)로 다시 고정한다. 그 픽스처가 `forClassWithGenerics`로 만들어지는 점도 의도적이다 — `SyntheticParameterizedType.getOwnerType()`이 항상 null이라(`ResolvableType.java:1665-1667`) 반드시 2c에 도달하기 때문이다.

## 4. 계약과 그 위반

이 무대의 계약 여덟 가지 중 결함이 어기는 것은 앞의 셋이고, 나머지는 수정이 기대거나 지켜야 할 제약이다.

| 계약 | 출처 | 위반 여부 |
|---|---|---|
| `TypeVariable`의 동일성은 이름과 선언 주체를 함께 본다 — 이름만 같은 두 변수는 다른 변수다 | JDK `TypeVariable` 규약, gh-36890 수정이 2a를 동일성으로 승격시킨 것(`9130ded96f4`) | 2c가 정면으로 위반 |
| 메서드 레벨 타입 변수는 클래스 레벨 변수를 가리며, 둘은 완전히 별개다 | 자바 언어 규칙 | 2c가 클래스 인자를 메서드 변수에 대입해 위반 |
| 이름 폴백은 subtype narrowing을 살리기 위해 존재한다 | 폴백을 도입한 커밋 `9130ded96f4`와 그것이 지키려 한 `ResolvableTypeTests.narrow()` | 코드가 그 의도보다 넓다 — 조건이 없어 형제 선언까지 통과 |
| `resolveVariable`이 null을 돌려주면 상위 루프가 다음 후보를 시도한다 | `GenericTypeResolver:218-223, :233-238` | 위반 아님 — 이것이 수정이 기대는 성질이다 |
| 해석 불가는 `TypeVariable`을 그대로 돌려주는 것으로 보고한다 | `GenericTypeResolver:207` (마지막 줄 `return genericType`) | 위반 아님. 케이스 B의 수정 후 동작이 이 계약을 따른다 |
| `TypeVariablesVariableResolver`는 동일성만으로 조회한다 (이름 폴백 없음) | `ResolvableType.java:1623-1631` | 위반 아님 — 같은 클래스 안에 이미 "이름만으로는 안 된다"는 선례가 있다 |
| `forClassWithGenerics`로 만든 타입은 owner가 없다 | `SyntheticParameterizedType.getOwnerType()`(:1665-1667) | 위반 아님. 폴백을 완전히 삭제하면 이 경로가 깨진다는 제약 |
| 이름이 바뀐 전이적 변수도 해석되어야 한다 | `GenericTypeResolverTests.resolveVariableNameChange()`(gh-34386, base :192-202) | 위반 아님 — 이 경로는 2a 동일성 + 중첩 owner로 동작하며 2c를 거치지 않는다 |

## 5. 수정안

### 5.1 채택 — 2c에 subtype narrowing 술어를 건다

이름 비교 루프는 그대로 두고, 그 앞에 두 술어로 된 게이트를 세운다.

```java
			// before (ResolvableType.java:966-971, base 1502ab0b20b)
			// Fallback: comparison by variable name, independent of generic declaration context.
			for (int i = 0; i < variables.length; i++) {
				if (ObjectUtils.nullSafeEquals(variables[i].getName(), variableToCompare.getName())) {
					return forType(typeArguments[i], this.variableResolver);
				}
			}
```

```java
			// after (ResolvableType.java:966-976, head 1633f41727c)
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

**왜 이 위치인가.** 조건을 루프 밖에 두면 폴백 전체가 하나의 술어로 켜지고 꺼진다 — "이 폴백이 정당한가"는 자리 `i`마다가 아니라 **찾는 변수와 지금 타입의 관계**에서 한 번에 결정되는 성질이기 때문이다. 루프 안에 넣으면 같은 판정이 반복되고, 상위 계층(`GenericTypeResolver`)에 넣으면 `resolveVariable`을 직접 부르는 다른 경로(재귀 `:948`, `:964`, `:974`와 `DefaultVariableResolver`)가 보호를 받지 못한다.

**두 술어가 각각 하나씩 막는다.** `getGenericDeclaration() instanceof Class<?>`는 케이스 B(메서드 레벨 선언은 `Method`를 돌려준다)를 막고, `resolved.isAssignableFrom(declaringClass)`는 케이스 A(형제 인터페이스는 상속 관계가 없다)를 막는다. 케이스 D는 두 술어를 모두 통과한다.

**폴백이 꺼지면 무슨 일이 일어나나.** 2c를 건너뛰면 `resolveVariable`은 (3)(4)를 지나 결국 null로 끝나고, `GenericTypeResolver`가 그것을 `NONE`으로 받아 다음 후보를 시도한다. 즉 수정은 답을 바로잡는 것이 아니라 **"모름"을 정직하게 반환해 상위 탐색이 정답에 닿도록 길을 비켜 주는 것**이다.

### 5.2 검토된 대안과 기각 이유

같은 증상을 겨냥한 다른 네 접근을 검토했고, 각각 다음 이유로 밀렸다.

- **이름 폴백 전체 삭제.** 가장 단순하지만 `ResolvableTypeTests.narrow()`가 깨진다. 케이스 D는 2a도 2b도 답을 줄 수 없고 오직 2c로만 해석되므로, 삭제는 결함 수정이 아니라 기능 제거다. 이 오답을 막기 위해 PR이 긍정 테스트를 별도로 추가했다.
- **2b의 `return`을 폴백 통과로 완화.** owner 재귀가 null이면 2c를 시도하게 하는 안이다. 케이스 A는 고치지 못하고(A는 애초에 owner가 null이다) 오히려 케이스 C가 결함 경로에 새로 들어오므로, 결함 범위를 넓힌다.
- **`GenericTypeResolver` 쪽에서 후보 순서를 바꾸거나 전 후보를 시도해 유일 해를 요구.** 증상 하나(A)는 완화되지만 원인(느슨한 판정)은 그대로이고, 인터페이스 선언 순서에 의존하던 기존 동작 전반을 흔든다. 결함이 사는 곳이 아닌 곳을 고치는 안이다.
- **술어를 `declaringClass.isAssignableFrom(resolved)`로 뒤집기.** 방향이 반대다. narrowing은 `resolved`(`List`)가 넓고 `declaringClass`(`ArrayList`)가 좁은 관계이므로 `resolved.isAssignableFrom(declaringClass)`가 맞다. 뒤집으면 케이스 D가 깨진다.

## 6. 범위 밖과 인접 영향

이 PR이 손대지 않은 인접 코드와, 수정이 남기는 영향은 다음 다섯 갈래로 정리된다.

- **같은 패턴의 다른 위치는 없다.** 이름 기반 변수 매칭은 이 클래스에서 2c 한 곳뿐이다. `TypeVariablesVariableResolver`(:1623-1631)는 동일성만 쓰고, `GenericTypeResolver.getTypeVariableMap`(:261)이 만드는 맵도 `TypeVariable` 자체를 키로 쓴다. 수정은 클래스 내부의 다수 관례에 맞추는 방향이다.
- **`SerializableTypeWrapper.unwrap`은 건드리지 않았다.** 래퍼를 벗기는 일(:946)과 벗긴 뒤 무엇으로 비교하느냐는 별개 축이며, 전자는 gh-36890 수정에서 이미 정리됐다.
- **하위호환.** 동작이 달라지는 것은 (1) 무관한 선언과 이름만 같은 변수, (2) 메서드 레벨 변수 두 경우뿐이고, 둘 다 수정 전 값이 **틀린 값**이었다. 정당한 narrowing과 동일성 매칭은 그대로다. 공개 API 시그니처 변화 없음. 다만 (2)의 반환 형태가 "구체 클래스"에서 "`TypeVariable` 그대로"로 바뀌므로, 그 우연한 해석에 의존해 `resolve()` 결과가 non-null임을 전제하던 호출자가 있다면 영향을 받는다 — 그런 호출자가 실제로 있는지는 **미확인**이며, 원래 값이 틀렸다는 점에서 의존이 정당화되지는 않는다.
- **검증.** `GenericTypeResolverTests`에 세 건이 추가됐다. A 재현(최상위 픽스처 — 테스트 픽스처의 배치 자체가 검증 조건이다), B 재현(단언이 "값이 틀렸다"가 아니라 "`TypeVariable`로 남아 있다"), D 긍정 가드(폴백 삭제라는 오답을 막는다). 기존 자산으로는 `narrow()`, gh-34386, gh-36890 테스트가 그대로 통과한다. 상세는 [tests.md](tests.md).
- **인접 리포트.** gh-36890 이슈 자체는 선행 커밋 `9130ded96f4`로 이미 닫혔다. 이 PR은 같은 이슈 번호를 참조하는 후속이며, 새 이슈를 열지 않고 "그 수정이 최상위 선언에서는 도달하지 못했다"는 범위 보완으로 제출됐다.
