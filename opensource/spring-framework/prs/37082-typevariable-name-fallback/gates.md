# PR #37082 — 이해 게이트 기록

> 출처: 세션 b5319e6a (2026-07-22), 작업 폴더 `docs/plans/2026-07-22/c3-resolvabletype-toplevel-name-fallback`. 답변은 원문 그대로(오타 포함), 판정과 정답은 대화에 기록된 것만 옮긴다.
> 모드: lazy (매 diff 이해 게이트, 최대 2회, 판정은 별도 서브에이전트 워커). 게이트 발생은 `gate-guard` 훅이 강제했다 — 08:14 이전 fixture 편집 시도가 `PENDING_GATE=1`로 실제 차단된 기록이 있다.

## 게이트 목록

이 작업에서 열린 게이트는 계획 하나와 diff 다섯, 모두 여섯 건이다.

| 번호 | 대상 | 시도 | 최종 판정 |
|------|------|------|-----------|
| G1 | 계획 (task.md — 버그 메커니즘과 fix 방향) | 2 | pass (메인 통과 처리, 판정 워커 미투입) |
| G2 | diff 1 — `GenericTypeResolverTests` 재현 테스트 2건 | 1 | pass (판정 워커 verdict=pass) |
| G3 | diff 1 — 톱레벨 fixture 5개 | 1 | pass (메인 통과 처리, 동일 구조 중복 판정 생략) |
| G4 | diff 2 — `ResolvableType.resolveVariable` subtype 가드 | 1 | pass (판정 워커 verdict=pass) |
| G5 | diff 4 — 양성 narrowing 테스트 (리뷰 F2 채택분) | 1 | pass (메인 통과 처리, 중복 판정 생략) |
| G6 | diff 4 — `Container`/`Box` fixture | 0 (질문·답변 없음) | pass (메인이 직접 해소) |

- 판정 워커가 실제로 돈 게이트는 G2, G4 두 건이며 둘 다 verdict=pass.
- fail 판정은 한 건도 기록되지 않았다. 다만 G1의 1차 시도는 답변이 아니라 절차 요구여서 게이트 자체가 재구성됐고, G2 진행 중 사용자가 스스로 방향 반전을 교정한 기록이 있다.

---

## G1 — 계획 게이트 (버그 메커니즘과 fix 방향)

**질문** (07:30, 원문)

> lazy 계획 게이트입니다 — 진행 전에 확인 하나 부탁드립니다. **이 버그가 왜 톱레벨에서만 나고 중첩에선 안 나는지, 그리고 fix가 뭘 좁히려는 건지** 본인 말로 설명해주시겠어요? (이해 정렬용 — 판정은 별도 워커가 합니다)

**시도 1 — 답변** (07:35, 07:36, 07:38)

> 있잖아 문서를 /home/jun/project/spring-framework-fork/docs/plans/2026-07-15/c2-twobytematcher-reset 여기에서 계획이나 어떤 문제를 어떻게 할지 문서화를 해줘야 diff로 각각 비포 에프터가 있어야 그에 맞춰서 해주지않을까?

> (계획 원문을 되붙이며) 이걸 내가 너의 계획문서를 보고 판단한느게 맞지않을까?

> 실 코드를 내가 볼 수 없으니깐

**판정 1** — 판정 워커 미투입. 메인이 절차 오류를 인정하고 게이트를 재구성했다: 질문을 말로 던진 것이 잘못이고, lazy 플레이북 3.1대로 before/after 스니펫을 계획 문서에 먼저 박은 뒤 그 문서를 근거로 판단하게 하는 것이 맞다고 판단. 이에 따라 `/tmp` 복사본 계측 실험으로 fix를 실증 확정하고 `task.md`를 작성한 뒤(07:47) 게이트를 다시 열었다.

**시도 2 — 답변** (계획 문서 검토 후, 되묻기 3회에 이은 정리, 07:49 - 07:56)

> 아 결국 오너 타입이 null인 경우에 대해 톱레벨 타입이라면 의존성이 엮인게 아닌 단독클래스는 톱클래스타입일꺼고 여기서 null이면 그냥 스킵되는데 이때 무관한 형제 선언과 이름 매칭이 된다? 그런데 이때 이름이 같은 객체가 생성되면 어차피 java에서 오류를 띄우지않아? (07:49)

> 그럼 이떄  TopSearch<String,Long>의 raw인 TopSearch가 어떤 클래스에도 중첩돼 있지 않으면 owner가 없어 null. 중첩이면 getOwnerType()이 바깥 클래스를 반환해서 owner 재귀가 폴백 이부분이 약간 이해가 안되는데,
> TopSearch에 대해서 raw라는건 해당 TopSearch로 생성한 객체를 이야기하는거야? (07:52)

> raw는 결국 인터페이스 클래스라는건데 그렇다면 너말은 중첩 Search<String,Long>      | interface OwnerProbe$Search   | class OwnerProbe (바깥 클래스) 여기서 search는 OwnerProbe를 상속받고 있어서 getOwnerType()이 OwnerProbe가 나온다는거 맞아? (07:54)

> 아 중첩이라는게 객체 내에 선언해서 중첩된 구조이며, 그뜻이구나. (07:56)

**판정 2** — pass. 메인이 마지막 답변을 "이해하신 그대로"로 인정하되 용어 하나를 정정하고(객체 안이 아니라 타입 선언 안) diff 1 착수로 넘어갔다. 계획 게이트에는 판정 워커를 돌리지 않았다.

**정답 정리** (대화에 제시된 정답)

- "이름이 같은 객체"가 아니라 "이름이 같은 타입변수"다. 서로 다른 인터페이스가 같은 타입변수 문자를 재사용하는 것은 완전히 합법이며 Java가 오류를 내지 않는다. 실제로 fixture를 컴파일해 확인했다.
  - `TopSearch.I`: `getName()="I"`, `getGenericDeclaration()=interface TopSearch`
  - `TopCreate.I`: `getName()="I"`, `getGenericDeclaration()=interface TopCreate`
- identity 루프는 `equals`로 비교하므로 선언이 다르면 매칭하지 않는다(정상). 이름 폴백은 `getName()` 문자열만 비교하므로 `TopSearch.I`를 집어 온다(사고). Java가 막아주는 것이 아니라 Spring 코드가 선언을 무시한 것이다.
- 트리거는 `TopController`의 톱레벨 여부가 아니라 타입변수를 선언한 형제 인터페이스가 톱레벨인지 여부다.
- raw type은 인스턴스가 아니라 `<...>`를 뗀 `Class` 자체다. 실측표:

| | `getRawType()` | `getOwnerType()` |
|---|---|---|
| 중첩 `Search<String,Long>` | `interface OwnerProbe$Search` | `class OwnerProbe` |
| 톱레벨 `TopSearch<String,Long>` | `interface TopSearch` | `null` |

- 코드 근거 (`ResolvableType.resolveVariable`):

```java
Type ownerType = parameterizedType.getOwnerType();
if (ownerType != null) {
    return forType(ownerType, this.variableResolver).resolveVariable(variableToCompare);  // 무조건 return
}
// 이 아래가 이름 폴백
```

  중첩은 owner 재귀가 무조건 return하므로 이름 폴백에 도달하지 못하고, 톱레벨은 `null`이라 그대로 폴백으로 떨어진다.
- 중첩과 상속은 다른 축이다. 중첩은 타입 선언 몸통 안에 다른 타입을 선언한 것으로 `getOwnerType()`이 다루고, 상속은 `getGenericSuperclass()` / `getGenericInterfaces()`가 다룬다. `OwnerProbe$Search`의 `$`는 상속이 아니라 중첩 표시다.

---

## G2 — diff 1: 재현 테스트 2건

**질문** (07:57, 원문)

> lazy 이해 게이트입니다. **이 두 테스트가 각각 무엇을 검증하는지, 그리고 왜 수정 전에는 실패하고 수정 후에는 통과하게 되는지** 본인 말로 설명해주시겠어요? (fixture 5개는 이 이해가 통과되면 바로 이어 추가합니다. 판정은 별도 워커가 합니다.)

**시도 1 — 답변** (되묻기 5회에 이은 최종 정리, 08:01 - 08:13)

> 1번에 대해서 TopCreate.class에 대해서 create 메서드의 파라미터 타입이 0번째와 TopController.class가 2번째인자인데 이건 왜 들어가는거야? 그리고 이렇게 만든 타입이 Long.class여야되는데 지금은String이라 오류라고 증명하는 코드인 거같고,
> 저 메서드라는 함수와 리폴브타입에 대해 알려줄래? 그리고 탑리포랑 비교하는건 2번째인자인 이유가 어떤것이며 저 타입의 객체 타입은 TypeVariable.class인데 이건 어떤 객체타입을 말하는거야? (08:01)

> 그럼 TopController 관점에서 봐야 TopController implements TopCreate<Long,Long> -> I = Long 여기서 TopController 생성 시 파라미터를 <I>로 받아? (08:04)

> 그럼 TopSearch에서는 I에 String인데 이게 TopCreate의 I까지 영향을 줘서 둘다 String이 된다는거야? (08:05)

> 아 그럼 테스트는 결국 해당 데이터를 찾는 과정에서 Long이 되어야 하는데 controller관점에서 그게 아니라 I로만 확인하니 TopSearch타입의 I와 착각해서 String을 가져올꺼고, 그래서 생기는 문제라는거네, 그리고 그 다음 2번쨰 리포에 대해서 그렇다면 ToStringRepo관점에서는 String이고 TypeVariable이 기본적으로 resolvedType도 String이 되서 단언이 꺠지는 거아니야? (08:09)

> 아 그럼 저건 실제 String이여야 하는데 이때 TypeVariable.class가 String으로 컴파일 시점에적용이 되어야 하는데 적용이 되지 않아서 단언이 깨진다는거네 지금은 그러면 TypeVariable.class가 바라보는 객체는 누구야? (08:11)

> 아 애초에 TypeVariable.class라는 객체는 미해결 타입이라는 객체를 나타낼뿐인 제네릭을 나타내는것이며, 그대로 전달해야되는데 리턴타입은 아직 T로 고정되어있어야하는데 그게 아니라 String이 되버려서 터지는게 문제라는거구나 (08:13)

**판정 1** — 판정 워커 verdict = pass. 워커 원문 요지:

> The user correctly grasps both tests' mechanism: Test 1 - the resolver's name-only fallback confuses TopCreate.I with the sibling TopSearch.I because both are named "I", so it wrongly returns String instead of Long (the correct binding from `implements TopCreate<Long,Long>`); they also correctly note bindings are positional from the implements clause and the same-named variables are distinct by declaration, not contaminated. Test 2 - they correctly identify the method-level `<T>` as a distinct shadowing variable that must stay an unresolved TypeVariable, with the bug leaking class T=String via name match and breaking `isInstanceOf(TypeVariable.class)`; they caught and corrected their initial inversion. No material gap.

**정답 정리** (대화에 제시된 정답)

- `method(...)`는 이 테스트 파일의 private 헬퍼(line 269)로 리플렉션 `Method` 객체를 돌려준다.

```java
private static Method method(Class<?> target, String methodName, Class<?>... parameterTypes) {
    Method method = findMethod(target, methodName, parameterTypes);
    ...
    return method;
}
```

- 세 번째 인자 `Object.class`는 type erasure 때문에 필요한 검색 키다. `O create(I body)`의 바이트코드 시그니처는 `create(Object)`이므로 그 키로 찾아야 한다. 해석 대상이 아니다.
- `getGenericParameterTypes()[0]`이 erase되지 않은 타입변수 `I`이며 이것이 해석 대상이다.
- `GenericTypeResolver.resolveType(Type genericType, Class<?> contextClass)`의 두 인자는 각각 해석 대상과 관점 클래스다. 두 번째라서 특별한 것이 아니라 시그니처 순서일 뿐이다.
- `TopController`는 제네릭이 아니다. 바인딩은 `implements TopCreate<Long, Long>` 선언 자체에 박혀 있고 위치 기준 1대1 대응이다. 인스턴스를 만들 필요가 없으며 `TopController.class.getGenericInterfaces()`가 읽는 타입 레벨 정보다.
- 두 선언의 바인딩은 각자 독립적이고 올바르다(`TopSearch.I = String`, `TopCreate.I = Long`). 오염이 아니라 조회 버그다.
  - 틀린 표현: "TopSearch의 I가 TopCreate의 I를 String으로 만든다"
  - 옳은 표현: "`TopCreate.I`를 물었는데 해석기가 이름만 보고 `TopSearch.I`(=String)를 잘못 반환한다"
- 테스트 2에서 메서드 `T`의 정답은 String이 아니라 미해결 상태 유지다. `<T> T convert(Object o)`가 자기 `T`를 새로 선언해 클래스 `T`를 가리므로 `TopStringRepo` 관점만으로는 정해질 수 없다.
  - 수정 후: `resolvedType`이 `TypeVariable`이므로 `isInstanceOf(TypeVariable.class)`가 참, PASS.
  - 수정 전: 이름 폴백이 클래스 `T`(=String)로 채워 `String.class`가 되므로 FAIL.
- `TypeVariable.class`는 특정 변수를 가리키는 것이 아니라 `java.lang.reflect.TypeVariable` 인터페이스의 `Class` 메타객체다. 수정 후 반환되는 실제 인스턴스는 `TopRepo.class.getDeclaredMethod("convert", Object.class).getTypeParameters()[0]`, 즉 `convert`가 선언한 `T`다.
- `java.lang.reflect.Type`의 하위 종류: `Class`, `ParameterizedType`, `TypeVariable`, `WildcardType`, `GenericArrayType`.
- 이것은 컴파일 시점이 아니라 런타임 리플렉션 조회다.

---

## G3 — diff 1: 톱레벨 fixture 5개

**질문** (08:14, 원문)

> 앞서 이 구조들(형제 인터페이스 `TopSearch`/`TopCreate`의 동명 `I`, 클래스 vs 메서드 `T` shadowing, `implements`의 위치 기반 바인딩, 톱레벨의 owner=null)을 이미 상세히 이해하셨으니, 이 fixture diff에 대해 **"왜 이 선언들을 톱레벨에 두었고 각 fixture가 어느 테스트의 무엇을 재현하는지"** 한 줄로 확인해주시면 게이트를 넘기겠습니다.

**시도 1 — 답변** (08:24)

> Top으로설계했을떄는 null이라서 String으로 흘러가서 오너타입일 때
> for (int i = 0; i < variables.length; i++) {
>                 if (ObjectUtils.nullSafeEquals(variables[i].getName(), variableToCompare.getName())) {
>                     return forType(typeArguments[i], this.variableResolver);
>                 }
>             }
> 여기서 이름만 비교하니깐 여기서 문제가 생기니깐, 그걸 확인하기 위함 아니야? 각 메서드들의 상속받았을 때 T가 제대로 처리가 되는지 그래서 여기서 if절로 객체 클래스 타입을 보려고 하는 거 아닌가?

**판정 1** — pass (메인 통과 처리). 판정 워커는 돌리지 않았다. 사유는 이 선언들이 직전 G2에서 판정 워커가 이미 명시적으로 검증한 동일 구조라 중복 판정을 피한 것.

**정답 정리** (대화에 제시된 정정)

- 맞게 본 것: 톱레벨이라 `ownerType == null`이라 name-only 루프로 흘러 String이 샌다는 점, 그 루프가 이름만 비교한다는 점, fixture 두 쌍이 각각 형제 인터페이스 동명 `I`(테스트 1)와 클래스 대 메서드 `T` shadowing(테스트 2)을 재현한다는 점.
- 정정: "오너타입일 때 이 루프"가 아니라 "오너타입이 `null`일 때(톱레벨) 이 루프에 도달"한다. 오너타입이 있으면 위쪽 `if (ownerType != null) return ...`에서 막혀 루프까지 오지 못한다. 용어만 반대로 쓴 것이고 앞 문장의 방향은 맞았다.
- 정정: 마지막의 "if절로 객체 클래스 타입을 보려고 한다"는 fixture가 아니라 다음 단계인 diff 2(fix) 이야기다. 내용 자체는 정확하다.

---

## G4 — diff 2: subtype 가드 (fix)

**질문** (08:29, 원문)

> 앞서 이 가드의 (A)`instanceof Class` / (B)`isAssignableFrom` 판별을 상세히 이해하셨으니, lazy 이해 게이트로 **이 diff가 무엇을 바꾸고 왜 세 케이스(narrow 허용 / C3#1·#2 거부)가 의도대로 갈리는지** 한 번 정리해주시면, 판정 워커 확인 후 전체 스위트 검증(diff 2 acceptance)으로 넘어가겠습니다.

**시도 1 — 답변** (08:31, 08:35, 08:41)

> 진행하자

> 처음 조건을 통해 해당 객체 선언자가 class인지 확인하고 이떄 그리고 resolved의 하위 타입이라는건 결국 객체 내에 이름을 확인한다는거 맞지?

> 아 그럼 기존에는 search와 create를 같이 받고있어서 저 검사를 하면 서로 상속이 아니라서 따로 보겠구나.

**판정 1** — 판정 워커 verdict = pass. 워커 원문:

> Correctly grasps the two-stage guard: the inheritance check (isAssignableFrom) is distinct from the separate name comparison in the loop, and applies it accurately to all three cases (C3#1 sibling rejection to Long, C3#2 Method-declaration rejection, narrow() subtype allowance).

**정답 정리** (대화에 제시된 정답)

- 중간 오해 정정: `resolved.isAssignableFrom(declaringClass)`는 이름과 무관하다. 상속(타입 계층) 관계만 본다. 이름 비교는 그 안쪽 `for` 루프에서 따로 한다.

```java
if ( ... instanceof Class<?> declaringClass          // (1) 선언자가 클래스인가
        && resolved.isAssignableFrom(declaringClass)) // (2) 상속 관계인가, 이름 아님
{
    for (...) {
        if (nullSafeEquals(variables[i].getName(), variableToCompare.getName())) // (3) 이름 같은가
            return ...;
    }
}
```

- 등장 인물: `variableToCompare`는 지금 찾고 있는 타입변수, `resolved`는 지금 스캔 중인 raw 클래스(이름 매칭 후보 `variables[]`를 꺼낸 클래스).
- `getGenericDeclaration()`의 반환은 `Class`, `Method`, `Constructor` 중 하나다. `instanceof Class<?>` 검사는 메서드와 생성자 레벨 변수를 걸러내고, 통과하면 선언 클래스를 확보한다.
- `A.isAssignableFrom(B)`는 "B가 A이거나 A의 하위타입이냐"이므로, 가드는 "찾는 변수의 선언 클래스가 스캔 중인 클래스이거나 그 하위타입이냐"를 묻는다. 이것이 곧 정당한 subtype 좁힘인지의 판별식이다.

| 상황 | `resolved` | `declaringClass` | `isAssignableFrom` | 결과 |
|------|-----------|------------------|--------------------|------|
| narrow (정당) `List<String>` 을 `ArrayList` 로 | `List` | `ArrayList` | true | 폴백 허용, E=String |
| C3 #1 (버그) | `TopSearch` | `TopCreate` | false (형제) | 폴백 거부, 올바른 Long |
| C3 #2 (버그) | `TopRepo` | (Method) | (1)에서 이미 false | 폴백 거부, T 미해결 |

- 실측값(대화 중 직접 출력):

```
narrow: List.isAssignableFrom(ArrayList)      = true
C3#1:   TopSearch.isAssignableFrom(TopCreate) = false
        TopCreate.isAssignableFrom(TopSearch) = false
```

- 핵심 직관: 이름이 같은 두 타입변수를 매칭해도 되는 유일하게 정당한 경우는 supertype을 그 subtype으로 좁힐 때뿐이다.

---

## G5 — diff 4: 양성 narrowing 테스트 (리뷰 F2)

**질문** (08:54, 원문)

> lazy 이해 게이트입니다. **이 테스트가 앞의 두 버그 테스트와 어떻게 다른지(버그 vs 정당), 그리고 왜 가드가 이건 통과시켜야 하는지** 한 줄로 확인해주시면, fixture(`Container`/`Box`) 추가하고 판정 워커로 넘기겠습니다.

**시도 1 — 답변** (08:55)

> 앞에 내용은 박스와 컨테이너에대해서 박스로좁혔을때는 string클래스가제대로 적용되도록 확인하는 테스트이다.

**판정 1** — pass (메인 통과 처리). 판정 워커는 돌리지 않았다. 사유는 이 양성 테스트의 개념(가드 true-branch)이 diff 2에서 이미 판정 워커가 통과시킨 것과 동일하고 답변도 정확하다는 것.

**정답 정리** (대화에 제시된 보충)

- 대상 테스트:

```java
@Test  // gh-36890
void resolveTypeVariableByNameWhenNarrowingParameterizedSupertype() {
    ResolvableType containerOfString = ResolvableType.forClassWithGenerics(Container.class, String.class);
    ResolvableType box = ResolvableType.forType(Box.class, containerOfString);
    assertThat(box.getGeneric().resolve()).isEqualTo(String.class);
}
```

- 갈리는 이유: 버그 테스트 1과 2는 형제 관계 또는 클래스 대 메서드라 상속 관계가 아니므로 가드가 `isAssignableFrom=false`로 거부해야 정상이고, 이 테스트는 `Box implements Container`로 진짜 하위타입이라 `Container.isAssignableFrom(Box)=true`로 허용해야 정상이다.
- 즉 가드의 두 방향을 버그 테스트(거부)와 이 테스트(허용)가 나눠서 잠근다.
- 실증: 가드가 있으면 String, 폴백을 제거하면 null. 이 테스트가 가드의 true-branch를 정확히 탄다. 목적은 나중에 가드를 과하게 조여 정당한 좁힘까지 막으면 이 테스트가 깨져 잡아주는 것.

---

## G6 — diff 4: `Container`/`Box` fixture

**질문 / 답변** — 없음. 08:56에 fixture를 추가하면서 `PENDING_GATE=1`이 재설정됐고, 메인이 "diff 1 fixture 때와 동일하게, 이미 이해된 선언이라 게이트를 내립니다"로 직접 해소했다.

**판정** — pass (메인 통과 처리). 대화에 명시된 정답 없음.

---

## 반복된 오해 패턴

여섯 게이트에 걸쳐 되풀이된 오해는 다섯 갈래이고, 대부분 리플렉션 메타데이터를 실행 시점 개념으로 읽은 데서 나왔다.

1. **타입 레벨과 인스턴스 레벨 혼동** — G1과 G2에서 반복. "이름이 같은 객체가 생성되면", "TopSearch로 생성한 객체", "TopController 생성 시 파라미터를 `<I>`로 받아?", "객체 내에 선언해서". 이 작업은 처음부터 끝까지 `java.lang.reflect` 메타데이터만 다루며 `new`가 등장하지 않는다는 점이 세 번 정정됐다.
2. **중첩과 상속 혼동** — G1에서 `OwnerProbe$Search`의 `$`를 상속으로 읽었다. 중첩은 `getOwnerType()`의 축, 상속은 `getGenericSuperclass()` / `getGenericInterfaces()`의 축이다.
3. **기대값 방향 반전** — G2에서 메서드 레벨 `T`의 정답을 String으로 잡았다. 실제로는 String이 되는 것이 버그이고 미해결 `TypeVariable`로 남는 것이 정답이다. 다음 턴에 스스로 교정했고 판정 워커도 이를 인정했다.
4. **조건 방향 뒤집기** — G3에서 "오너타입일 때 이 루프"라고 썼으나 실제는 오너타입이 null일 때 도달한다. 직전 문장에서는 방향을 맞게 서술해 용어 실수로 판정됐다.
5. **가드 두 단계 뭉개기** — G4에서 `isAssignableFrom`을 이름 확인으로 읽었다. 상속 검사(가드)와 이름 검사(루프 안)는 별개의 단계다.

## 교훈

이 게이트 기록에서 남길 만한 것은 다섯 가지다.

- 되묻기가 곧 게이트 답변으로 기능했다. G1과 G2는 각각 3회와 5회의 되묻기를 거쳐 마지막 한 문장에서 정리에 도달했고, 판정 워커는 그 궤적 전체를 보고 "초기 반전을 스스로 교정했다"를 pass 근거로 삼았다.
- 계획 게이트를 말로 던진 것이 절차 오류였다. 사용자가 "실 코드를 내가 볼 수 없으니깐"이라고 지적한 뒤에야 before/after 스니펫을 담은 계획 문서를 먼저 만들고 그것을 판단 근거로 삼는 흐름으로 교정됐다. lazy 플레이북 3.1의 "before/after 선행 기록"이 형식이 아니라 판단 가능성의 전제였다.
- 훅이 실제로 작동했다. fixture 편집 시도가 `PENDING_GATE=1`로 차단되면서 테스트 메서드와 fixture가 별개의 게이트 단위로 쪼개졌다.
- 동일 구조 반복에는 판정 워커를 생략했다. G3, G5, G6은 직전 게이트에서 워커가 이미 검증한 구조라 메인이 직접 게이트를 내렸다. 워커가 실제로 판정한 것은 G2와 G4 두 건뿐이다.
- 게이트가 리뷰 산출물로도 이어졌다. 듀얼 리뷰에서 채택된 F2(양성 narrowing 테스트)가 새 diff가 되면서 G5라는 추가 게이트를 만들었다.
