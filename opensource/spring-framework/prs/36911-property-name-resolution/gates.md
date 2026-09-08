# PR #36911 — 이해 게이트 기록

> 출처: 세션 07fec95c (2026-08-14~17), 작업 폴더 `docs/plans/2026-08-14/pr36911-plain-accessor-review/`.
> 답변은 원문 그대로(오타 포함), 판정·정답은 대화에 기록된 것만 옮긴다.
> lazy 모드 규칙: 게이트마다 최대 2회 시도, 2회차도 fail이면 워커가 틀린 부분을 지적하고 통과 처리한다.

## 게이트 목록

이 PR에서는 게이트가 다섯 번 열렸고 그중 pass는 G4 한 건이다. 다음 표는 게이트별 대상과
시도 횟수, 최종 판정이다.

| 번호 | 대상 | 시도 | 최종 판정 |
|------|------|------|-----------|
| G1 | 계획 게이트 (판별 근거 + 검사 순서) | 2 | 2회차 fail, 규칙에 따라 통과 처리 |
| G2 | diff A — `Property.java` (판별 메서드 교체 + setter 원복) | 2 | 2회차 fail, 규칙에 따라 통과 처리 |
| G3 | diff B — `PropertyTests.java` (데이터 클래스 픽스처 + 테스트 4건) | 2 | 2회차 fail, 규칙에 따라 통과 처리 |
| G4 | diff C — `Property.java` 리뷰 반영 (R2/R3/R6) | 1 | pass |
| G5 | diff D — 테스트 5건 추가 (R1/R3/R4/R7) | 2 | 2회차 fail, 규칙에 따라 통과 처리 |

## G1 — 계획 게이트 (판별 근거 + 검사 순서)

**질문** (원문)

> 이번 수정에서 `isPlainAccessor()`가 **무엇을 근거로** plain accessor를 판별하게 바뀌는지, 그리고 그 판별을 get/is prefix 검사보다 **먼저** 해야 하는 이유는 무엇인가요?

**시도 1 — 답변**

> 기존에는 레코드 타입을 기반으로 해당 내용을 처리했었고, 그렇게 해서 검사를 했었는데 그게 아닌 데이터 클래스를 쓰면 코틀린과 자바 둘다 활용가능하다보니 그렇게 클래스 객체 활용명명을 바꾸고, 맞네 앞부분에 get과 몇개의 메서드가 맨 앞에 있어야 그 메서드로 판별할 수 있을텐데 그게 아니라 지금은 중간에 get이나 is가 들어가도 그걸 그대로 판별해버리는 문제가 발생해서 이부분을 수정하는거였는데 이걸 레코드가 아닌 데이터 클래스 자체로 처리할 수 있게 하라는게 이번 취지아니야?

**판정 1** — fail (1/2). 부족점:

1. 판별 근거: "record 대신 데이터 클래스로"는 목표이지 판별 방법이 아니다. `isPlainAccessor()`가 "이 클래스가 record인가"를 물어볼 수 없게 되면 메서드의 무엇을 보고 판별하는지(메서드 시그니처 조건 + 선언 클래스에서 무엇을 조회하는지)가 빠졌다.
2. 순서 이유: "이름 중간에 get/is가 들어가는 문제"는 이미 1차 커밋의 startsWith 전환으로 해결된 과거 버그다. startsWith로 바뀐 지금도 plain accessor 체크를 먼저 안 하면 여전히 잘못 잘리는 접근자 이름은 어떤 형태인가.

**시도 2 — 답변**

> 해당 데이터가 불변 객체인지를 보려는거 아니야?

**판정 2** — fail (2/2), 규칙에 따라 통과 처리.

**정답 정리** (판정 워커가 제시한 지적 원문 기준)

1. 판별 근거는 불변성(final 필드 여부)이 아니다. `isPlainAccessor()`가 확인하는 신호는 세 가지다.
   - 파라미터 0개
   - 반환 타입이 void가 아님
   - 선언 클래스에 그 메서드와 같은 이름의 declared field가 존재
   `name()` 메서드가 있고 `name` 필드가 있으면 plain accessor로 본다. 필드의 final 여부나 클래스가 record인지는 조건에 들어가지 않으며, 그래서 Java record뿐 아니라 Kotlin data class, record처럼 생긴 커스텀 Java 클래스까지 같은 규칙으로 커버된다. `isRecord()` / `RecordComponent` 의존을 걷어내는 것이 이번 리뷰 반영의 핵심이다.
2. 순서 이유는 두 가지다.
   - `issue()`처럼 접근자 이름이 실제로 "is"로 시작하는 경우, startsWith 기반 prefix strip이 여전히 "sue"로 잘라버린다. 중간의 get/is를 매칭하던 옛 indexOf 버그는 이미 1차 커밋에서 해결됐고, 지금 문제는 접두사가 진짜로 맞아떨어지는 경우다.
   - 컴포넌트 이름이 문자 그대로 `get` 또는 `is`인 경우 prefix strip이 빈 문자열을 만든다.
   plain accessor로 먼저 판정되면 메서드 이름 전체를 프로퍼티 이름으로 쓰므로 두 경우 모두 회피된다.

## G2 — diff A: `Property.java` (판별 메서드 교체 + setter 원복)

Claude가 먼저 설명한 변경 3덩어리: (1) `isRecordAccessor()`를 `isPlainAccessor()`로 교체하고 record API 대신 파라미터 0개 / 비void 반환 / `getDeclaredField(메서드이름)` 성공으로 판정, (2) read 분기를 `isPlainAccessor()` 호출로 교체(검사 순서는 그대로 prefix보다 먼저), (3) setter 분기를 upstream/main 원본 `indexOf("set")`로 원복.

**질문** (원문, 2문)

> 1. **setter 분기를 왜 원복하나요?** — 원복하면 이 PR의 동작 관점에서 무엇이 달라지나요(무엇을 포기하나요)?
> 2. **`isPlainAccessor()`에서 `getDeclaredField` 호출이 예외를 던지는 상황은 무엇을 의미하며, 그때 왜 false(= prefix strip 경로로 진행)가 올바른가요?**

**시도 1 — 답변**

> 1번 해당 부분은 실제 판별 조건을 수정하는 것만 되고, 완결이 아닌 별도 PR로 setter를 검사하도록 수정하는게 맞다고 생각해. 2번에서 해당 호출이 예외를 던지게 된다면 메서드 이름과 동일한 필드가 없기 떄문에 이건 레코드나 테이터 클래스가 아니라 볼 수 있으니, 이건 프로퍼티가 아니라고 명시하는거 아니야? 그렇게 접근자를 생성하지 않도록 하기 위함 아니야?

**판정 1** — fail (1/2). 부족점:

- 질문 1: "별도 PR로 분리한다"는 결론만 있고, 원복으로 이 PR이 포기하는 동작 변화가 무엇인지(원복 전후로 어떤 입력 메서드의 처리 결과가 달라지는지)를 짚지 않았다.
- 질문 2: 예외의 의미(같은 이름 필드 없음)는 맞지만, false의 효과를 "프로퍼티가 아님 / 접근자 생성 안 함"으로 봤다. false 이후 `resolveName()`이 실제로 무엇을 하는지 다시 확인해야 한다. 거부가 아니다.

**시도 2 — 답변**

> 1번 setter를 저렇게 바꾼 이유는 중간에 set이라는게 있으면 absetb라는 변수도 indexOf인 경우 setter로 인식해버리는걸 고친게 startsWith인데 이게 다시 복구 되게 되겠지.
> 2번에 대해서는 아 없으면 해당 메서드로 생성자 메서드를 생성하는구나?

**판정 2** — fail (2/2), 규칙에 따라 통과 처리.

**정답 정리**

1. 방향은 맞지만 예시가 뒤집혔다. `absetb` 같은 이름은 원복 전(startsWith)에는 "set"으로 시작하지 않으므로 `IllegalArgumentException`이 나고, 원복 후(indexOf)에는 예외 없이 통과해 index+3부터 잘라 "b"라는 엉뚱한 프로퍼티 이름이 나온다. 즉 startsWith 쪽이 더 엄격해서 이전에 조용히 통과하던 비-setter write 메서드를 예외로 거부하게 만드는 behavior change였고, 원복은 그 강화를 이 PR에서 포기한다는 뜻이다. 결과적으로 이 PR은 read 경로(이름 해석)만 다루고, setter 판정 강화는 별도 PR(#37139)로 간다. 리뷰어가 요청한 스코프 분리다.
2. "생성자 메서드를 생성한다"는 맞지 않다. `getDeclaredField`가 던지는 `NoSuchFieldException`은 "메서드 이름과 같은 이름의 declared field가 없다" = plain accessor로 볼 근거가 없다는 뜻일 뿐이다. false를 반환해도 프로퍼티가 거부되는 게 아니라 `resolveName()`이 기존 JavaBeans 경로로 폴백한다. 이름이 "get" / "is"로 시작하면 그 접두사를 잘라낸 나머지를(`getName()` -> `name`), 아니면 이름 전체를 프로퍼티 이름으로 쓴다. 필드 뒷받침이 없는 메서드는 전통 JavaBeans 규약대로 해석하는 것이 맞기 때문에 false가 올바르고, 이 폴백 덕분에 일반 getter의 기존 동작이 그대로 보존된다.

**게이트 중 되묻기와 그에 대한 설명** (G3 진행 중 사용자가 G2 내용을 다시 물어 Claude가 답한 부분)

> 그럼 1번은 indexOf로 인해 set이 중간에 있어도 뒤에 있는 데이터만 잘라서 set 위치 3부터 자른다는 논리에 대해 다시 설명부탁해 그리고 2번 내용 디테일하게 어떻게 동작하는지한번 설명좀 해줄래?

원복된 write 분기:

```java
int index = this.writeMethod.getName().indexOf("set");   // 이름 어디서든 "set"의 첫 위치
if (index == -1) {
    throw new IllegalArgumentException("Not a setter method");
}
index += 3;                                              // "set" 세 글자 건너뛰기
return StringUtils.uncapitalize(this.writeMethod.getName().substring(index));
```

- `setName`: indexOf = 0 -> +3 = 3 -> `substring(3)` = "Name" -> uncapitalize -> `name`
- `absetb`: a(0) b(1) s(2) e(3) t(4) b(5) -> indexOf = 2 -> +3 = 5 -> `substring(5)` = "b"

read 분기의 폴백 구조:

```java
String methodName = this.readMethod.getName();
int index;
if (isPlainAccessor(this.readMethod)) {      // (1) 같은 이름 필드가 있는 무인자·비void 메서드
    index = 0;                               //     이름 전체 사용
}
else if (methodName.startsWith("get")) {     // (2) JavaBeans getter 규약
    index = 3;
}
else if (methodName.startsWith("is")) {      // (3) boolean getter 규약
    index = 2;
}
else {
    index = 0;                               // (4) 아무 규약도 아님, 이름 전체
}
return StringUtils.uncapitalize(methodName.substring(index));
```

- `getName()` (같은 이름 필드 없음): (1) false -> (2) index=3 -> `name`
- `budget()` (필드 `budget` 존재): (1) true -> index=0 -> `budget`
- `issue()` (필드 `issue` 존재): (1) true -> `issue`. (1)이 먼저 없으면 (3)에 걸려 "sue"가 된다

## G3 — diff B: `PropertyTests.java` (데이터 클래스 픽스처 + 테스트 4건)

픽스처 `SampleDataClass`는 record가 아닌 손으로 쓴 클래스로, private 필드 `name` / `budget` / `issue`와 같은 이름의 무인자 접근자를 가진다. 여기에 backing field가 없는 JavaBeans getter `getWidget()`이 함께 있다.

**질문** (원문)

> `SampleDataClass`의 `getWidget()` 테스트는 왜 결과가 `getWidget`이 아니라 `widget`이어야 하나요? — 즉, 같은 클래스의 `budget()`은 이름 전체가 보존되는데 `getWidget()`은 잘리는 이유를, `isPlainAccessor()`의 판별 조건으로 설명해 주세요.

**시도 1 — 답변**

> 1. startWiths를 통해 맨 앞에서부터 get이 있는지만 검사하기 때문이다

**판정 1** — fail (1/2). 부족점:

- startsWith 설명은 `getWidget()`이 잘리는 뒷단계만 말한 것이다. 그 전에 두 메서드가 `isPlainAccessor()`에서 서로 다른 결과를 내기 때문에 한쪽만 폴백 경로로 가는데, 그 갈림의 근거를 짚지 않았다.
- `budget()`도 이름 전체를 보면 조건 비교가 가능한 형태인데 왜 잘리지 않는지, `SampleDataClass`의 필드 목록(`name`, `budget`, `issue`)과 각 메서드 이름을 대조해서 설명해야 한다.

**시도 2 — 답변**

> 아 메서드 파라미터와 메서드명이 일치하지 않기 때문에 getWidget는 false이기 때문이야.

**판정 2** — fail (2/2), 규칙에 따라 통과 처리.

**정답 정리**

인정된 부분: 갈림의 축이 "이름이 일치하는 무언가가 있느냐"이고 `getWidget()`이 그 때문에 false가 된다는 구조는 맞다.

틀린 부분은 비교 대상 개체다. "메서드 파라미터"가 아니라 선언 클래스의 declared field다. `isPlainAccessor()`는 파라미터를 개수로만 본다(0개여야 하고 이름은 보지 않는다). 실제 이름 대조는 `method.getDeclaringClass().getDeclaredField(method.getName())`, 즉 메서드 이름과 같은 이름의 필드가 그 클래스에 선언되어 있는지다.

- `budget()` — 파라미터 0개, 반환 비void, `getDeclaredField("budget")`가 private 필드 `budget`을 찾아 성공 -> true -> index=0 -> 이름 전체 `budget` 보존
- `getWidget()` — 파라미터 0개, 비void는 통과하지만 `getDeclaredField("getWidget")`가 `NoSuchFieldException`(클래스의 필드는 `name` / `budget` / `issue`뿐) -> false -> JavaBeans 폴백에서 `startsWith("get")` -> index=3 -> "Widget" -> uncapitalize -> `widget`

즉 startsWith 절단은 `isPlainAccessor()`가 false를 낸 뒤에야 적용되는 2단계이고, `budget()`은 애초에 그 단계에 도달하지 않는다.

## G4 — diff C: `Property.java` 리뷰 반영 (R2 / R3 / R6)

변경 3가지: (1) R2 — `isPlainAccessor()` 호출을 get/is 분기 안으로 이동, (2) R3 — static 메서드이거나 찾은 동명 필드가 static이면 plain accessor로 인정하지 않음, (3) R6 — 부정확한 Kotlin 예시 주석 제거.

**질문** (원문)

> 변경 1(plain 체크를 프리픽스 분기 안으로 이동)이 **동작을 바꾸지 않는 이유**를 설명해 주세요. 힌트: 프리픽스 없는 이름(`budget()`)이 plain 체크를 안 거치게 되는데, 왜 결과가 그대로일까요?

**시도 1 — 답변**

> 어차피 위 get와 is를 검증할떄 실제 변경 전에 실제 필드와 메서드명을 검사하기 때문에 문제없고, 애초에 get이 없으면 그대로 흘러가서 인덱스 0이 되며, 만약 인덱스가 달라야한면 isPlainAccessor()에서 index레벨이 수정되고 else로 안넘어가기 때문아니야?

**판정 1** — pass.

**정답 정리** (판정 워커 보강)

핵심 두 축을 모두 짚었다. (a) 프리픽스 없는 이름은 get/is 분기에 걸리지 않아 그대로 else로 흘러 index=0이 되므로 plain 체크를 건너뛰어도 결과가 같고, (b) 결과가 실제로 갈리는 프리픽스 있는 이름에서는 여전히 분기 안에서 `isPlainAccessor()`가 0이냐 3(또는 2)이냐를 결정한다. 보강: 변경 전에도 `budget()`은 plain=true면 0, false여도 else의 0이라 어느 쪽이든 0이었으므로 그 구간의 리플렉션은 결과에 영향 없는 순수 비용이었고, 이번 이동은 그 비용만 제거한다.

## G5 — diff D: 테스트 5건 추가 (R1 / R3 / R4 / R7)

테스트 구성: (1) `isTarget()` -> `target` (핵심 수정의 회귀 가드), (2) `isUrgent` 필드 + `isUrgent()` -> `isUrgent` (필드 우선 정책 고정), (3) 컴포넌트가 문자 그대로 `getWidget`인 record -> `getWidget`, (4) static 필드 동명 + 인스턴스 `getCount()` -> `count`, (5) static 메서드 `getLabel()` + 인스턴스 필드 동명 -> `label`.

**질문** (원문)

> 테스트 1의 `isTarget()`은 **옛 코드(indexOf 기반 main)** 에서 어떤 과정을 거쳐 **빈 문자열**이 됐을까요? (`isTarget`이라는 글자에서 무엇이 어디에 매칭됐는지로 설명해 주세요)

**시도 1 — 답변**

> 1번에 대해서 isTarget에서 is를 분리함녀 Target인데 이때 target와 isTarget 자체가 boolean필드이기 때문에 아 isTarget메서드랑 필드가 isTarget일 때 target으로 바꿔서 indexOf는 getIsTaget이 되어야 하는데 getTarget이 되는건가?

**판정 1** — fail (1/2). 부족점:

- 옛 코드는 "is"를 먼저 보지 않는다. 어느 접두사를 어떤 방식으로 먼저 찾는지, 그 탐색이 성공하면 나머지 분기가 어떻게 되는지 순서를 다시 확인해야 한다.
- `getIsTarget` / `getTarget` 같은 이름 변환은 코드에 없다. `isTarget` 8글자를 그대로 놓고, 옛 코드가 찾는 문자열이 몇 번 인덱스에 매칭되는지, 거기에 +3한 뒤 substring이 무엇을 남기는지 글자 단위로 짚어야 한다.

**시도 2 — 답변**

> Target으로 남으면 이거랑 일치하는 필드가 없다?

**판정 2** — fail (2/2), 규칙에 따라 통과 처리.

**정답 정리**

옛 코드에는 필드 대조가 아예 없다. 필드 존재 검사(`getDeclaredField`)는 이번 PR이 새로 도입한 것이고, main의 옛 코드는 순수하게 문자열 인덱스 계산만 한다. 또 옛 코드는 "is"를 먼저 보지 않는다. `indexOf("get")`을 먼저 시도하고, 그것이 -1일 때만 "is" 분기로 간다.

```
인덱스:  0  1  2  3  4  5  6  7
문자  :  i  s  T  a  r  g  e  t
                        g  e  t   <- indexOf("get")가 여기 매칭
```

- `"isTarget".indexOf("get")` -> 5번 인덱스에서 g-e-t를 찾아 5를 반환. -1이 아니므로 "is" 분기는 실행되지 않는다.
- `index += 3` -> 5 + 3 = 8
- `"isTarget".substring(8)` -> 문자열 길이가 정확히 8이므로 빈 문자열 `""`
- `uncapitalize("")` -> 여전히 `""`. 프로퍼티 이름이 빈 문자열이 되는 것이 이 버그다.

핵심은 indexOf가 접두사가 아니라 이름 어디에 있든 "get"을 찾는다는 점이다. `budget()`도 같은 이유로 깨진다(b-u-d-g-e-t, indexOf=3 -> 3+3=6 -> `substring(6)` = `""`).

새 코드에서는 `startsWith("get")`이 false, `startsWith("is")`가 true이고, `isPlainAccessor`는 `isTarget`이라는 이름의 필드가 없어 false이므로 index=2 -> `substring(2)` = "Target" -> uncapitalize -> `target`이 된다.

## 반복된 오해 패턴

다섯 게이트의 오답을 겹쳐 보면 같은 착오가 네 가지 모양으로 되풀이된다. 아래는 그 네
패턴을 빈도순이 아니라 게이트 순서로 정리한 것이다.

1. **판별 대상 개체를 잘못 잡음.** G1에서 "불변 객체인지", G3에서 "메서드 파라미터와 이름 일치"로 답했다. 실제 비교 대상은 선언 클래스의 declared field 하나뿐이고, 파라미터는 개수(0개)로만 쓰인다. 판정 워커가 G3에서 "계획 게이트에서도 같은 혼동이 나왔으니 여기서 확정해 두라"고 명시적으로 짚었다.
2. **false를 거부로 해석.** G2에서 `isPlainAccessor()`의 false를 "프로퍼티가 아니라고 명시", "생성자 메서드를 생성"으로 읽었다. 실제로는 기존 JavaBeans 폴백 경로로 계속 진행한다는 뜻이다. 분기의 값이 아니라 그 뒤에 무엇이 실행되는지를 따라가야 한다.
3. **옛 코드와 새 코드의 기능을 섞음.** G5에서 옛 코드(main)에 없는 필드 대조를 옛 코드 동작으로 설명했다. before / after를 나눠 각각 어떤 코드가 실제로 존재했는지 확인해야 한다.
4. **결론만 말하고 메커니즘을 건너뜀.** G1의 "데이터 클래스로 바꾼다", G2의 "별도 PR로 분리한다"는 목표 서술이지 판별 방법이나 동작 차이가 아니다. 판정 워커의 루브릭은 메커니즘, 이유, 효과를 짚어야 pass다.

## 교훈

이 기록에서 다음 게이트에 가져갈 것은 세 가지다. 손으로 계산해 보기, 분기의 양쪽 경로를
모두 따라가기, 그리고 경우를 나눠 서술하기다.

- 글자 단위 인덱스 추적(`indexOf`가 몇을 반환하고 +3 하면 어디이고 substring이 무엇을 남기는지)을 손으로 해보면 G5 같은 질문은 한 번에 풀린다. 이름 변환이 아니라 문자 매칭이라는 점이 요지다.
- 분기 조건을 읽을 때는 "true면 무엇, false면 무엇"의 양쪽 경로를 다 확인한다. 이 PR의 오해 대부분이 false 경로를 안 따라간 데서 나왔다.
- pass가 나온 유일한 게이트(G4)는 답변이 두 갈래 경우(프리픽스 없는 이름 / 있는 이름)를 나눠 각각의 결과를 대조한 형태였다. 경우를 나누는 서술이 판정 통과의 실질 기준이었다.
