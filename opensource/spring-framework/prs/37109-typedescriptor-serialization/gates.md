# PR #37109 — 이해 게이트 기록

> 출처: 세션 a089ec61 (2026-08-05 회수, 게이트 대화는 2026-08-04), 작업 폴더 `docs/plans/2026-08-04/c4-typedescriptor-serialization`.
> 답변은 사용자 원문 그대로(오타 포함). 판정과 정답은 대화에 기록된 것(판정 워커 verdict, 워커 정정 원문)만 옮겼다.
> 모드는 lazy — 매 diff마다 주관식 이해 게이트, 판정은 독립 워커, 최대 2회. 2회째도 fail이면 워커가 틀린 부분을 짚고 통과 처리한다.

## 게이트 목록

이 작업에서 거친 게이트는 계획 하나와 diff 둘, 모두 세 건이다.

| 번호 | 대상 | 시도 | 최종 판정 |
|---|---|---|---|
| G1 | 계획 게이트 (task 01 RED + task 02 fix 방향) | 2 | fail 2회, 규칙상 통과 처리 |
| G2 | diff 게이트 — task 01 RED 테스트 (`TypeDescriptorTests.java`) | 2 | pass (2회차) |
| G3 | diff 게이트 — task 02 fix (`TypeDescriptor.java`) | 2 | fail 2회, 규칙상 통과 처리 |

세 게이트 모두 같은 판정 워커(task-id `aa8d9efb66f00f82e`)가 담당했고, 패킷에는 메인의 해설이 아니라 `TypeDescriptor.java`·`AnnotatedElementAdapter.java`·`TypeDescriptorTests.java` 실파일이 그라운드 트루스로 들어갔다.

---

## G1 — 계획 게이트 (task 01 RED + task 02 fix 방향)

**질문** (원문, 1/2회차 최초 제시)

> 여기서 lazy 모드 계획 이해 게이트입니다. 아래 두 가지를 **본인 말로** 설명해주세요 (1/2회차):
>
> 1. `annotatedElementSupplier`를 `transient`로 바꾸는 것만으로는 왜 부족하고, `writeObject`에서 굳이 `getAnnotatedElement()`를 먼저 호출해야 하나요?
> 2. `readObject`에서 캐시를 그대로 두지 않고 `AnnotatedElementAdapter.from(...)`으로 다시 만드는 이유는 무엇인가요?

**되묻기** (판정에 제출되지 않음 — 메인이 답변 후 같은 1/2회차를 유지)

> 우선 transient 이게 어떤건지 알고 싶어. 그리고, getAnnotatedElement()l를 통해서 각 어노테이션 객체의 요소값을 가져오는데 이걸 저장해서 포인터를 연결해야 값이 사는게 아닌가? 그냥 호출만 해도 된다고? 그럼 해당 메서드는 별도 전역객체에 포인터를 연결한다고 볼 수 있는데 지금 너의 코드스니펫에선 알 수 없는데? 그리고 readObject메서드에 대해서도 바꾼게 있다면 비포 에프터가 있어야되는 거 아니야?굳이따지면 어뎁터로 해당 객체를 며 ㅇ시할 생각인 거 같은데 결국 어뎁터가 메서드를 만드는 요소들의 집합같아보이긴하는데,

되묻기에 대한 답변(transient 정의, `getAnnotatedElement()`의 부작용, `readObject`는 before가 없는 신규 메서드, 어댑터는 `Annotation[]` 래퍼) 뒤에 질문이 아래와 같이 재정리되어 제시되었다.

> 1. `transient`를 붙였을 때 **역직렬화된 객체에서 무엇이 비어 있게 되고**, 그 구멍을 무엇으로 메우나요?
> 2. `writeObject`에서 `getAnnotatedElement()`를 먼저 부르지 않고 그냥 `defaultWriteObject()`만 하면 어떤 일이 벌어지나요?

**시도 1 — 답변** (사용자 원문)

> 그러니깐 너말을 정리하면,
> private final AnnotatedElementSupplier annotatedElementSupplier; 이거 자체가 참조형이기 때문에,
> 이걸 final로 하면 class객체로 바라보고 객체 상태가 아니라 직렬화에서 문제가 된다. 즉 serializable이 있으면 이걸 직렬화할때
> 객체화해도 된다라는 허용인데 없으면 클래스 객체라 직렬화에서 문제가 발생한다. 그래서 null로 예외가 발생하지않도록 해야된다. 이거지?
> 아 final이 있으면 처음 불변 선언이 되서 나중에 주입이 안되기에 빼야된다는거구나.
> 그리고 getAnnotatedElement()를 통해 annotatedElementSupplier를 주입해야된다는거네, 어뎁터레벨에서,
> 2번도 똑같이 캐시를 하면 기존에 null이라 실 객체로 주입하려는 의도 아니야?
>
> 너의 질문
> 1번에 대해서 transient가 되면 annotatedElementSupplier객체가 null이 되고, 그걸 readObject를 통해 직렬화 객체를 통해
> 해당 클래스를 객체화해서 가져온다. 이거고,
> 2번에서 그냥 바로 부르면 해당 annotatedElementSupplier객체가 프록시 배열에서 null로 있겠지?

**판정 1 — fail**

워커 부족점 (원문): `getAnnotatedElement()`의 채움 방향(무엇이 무엇을 채우는지)이 답변에서 반대로 되어 있고, 직렬화 실패 원인을 `final`/`Serializable` 미부착 탓으로 보고 있음. 두 필드(L76·L78) 중 어느 쪽이 스트림에 실리는지, 그리고 supplier 인터페이스 선언(L730)을 다시 확인할 것. Q2는 supplier가 아니라 다른 필드의 write 시점 값이 쟁점.

근거로 제시된 위치: `TypeDescriptor.java:76-78`, `:256-263`, `:730`.

**재질문 (2/2회차)**

> 1. L76과 L78, **두 필드 중 이번 수정에서 `transient`가 붙는 쪽은 어디**이고, 붙지 않는 쪽은 직렬화될 때 어떻게 되나요?
> 2. `getAnnotatedElement()`가 한 번 실행되고 나면 **L76·L78 중 어느 필드의 값이 달라지나요?**
> 3. `writeObject`에서 그 호출을 생략하면, 스트림에는 그 필드가 어떤 값으로 실리고 역직렬화된 객체는 무엇을 잃게 되나요?

**시도 2 — 답변** (사용자 원문)

> 1번,annotatedElementSupplier 여기에 붙고, 붙지 않는 곳들은 직렬화할때 객체로 주입되서 직렬화 되지않아?
> 2번에서 해당 메서드가 실행되면 76라인이 기존에 직렬화 시 null인데 저걸 통해 실제 객체를 만들어서 주입하는 거 아니야?
> 730줄을 보면 AnnotatedElementAdapter의 부모를 같이 상속받고, 시리얼라이즈를 받는데, 이때 서로 다른 객체를 주입하는게 writeObject인거 아니야? 그래서 역직렬화할때 각 객체들의 구조가 null이 아닌 실제 객체 바이트로 되도록 한다는 거 아니야?

**판정 2 — fail (2회차이므로 통과 처리)**

**정답 정리** (워커 정정 원문 4항목)

1. transient 대상과 non-transient 필드
   - `transient`가 붙는 쪽은 L76 `annotatedElementSupplier`가 맞다. `final`을 같이 제거하는 이유는 "final이면 직렬화가 안 돼서"가 아니라 `readObject`에서 그 필드를 다시 대입해야 하기 때문이다.
   - 붙지 않는 L78 `annotatedElement`(타입 `AnnotatedElementAdapter`)는 "직렬화되지 않는" 게 아니라 정상적으로 직렬화되어 스트림에 실린다(`AnnotatedElementAdapter.java:38`이 `Serializable`, 내부에 `Annotation[]`만 보유). 이번 수정의 전제가 "L78이 어노테이션을 실어 나르는 유일한 통로가 된다"는 것.
2. `getAnnotatedElement()`의 방향이 반대다. `TypeDescriptor.java:256-263`은 L76(supplier)을 읽어 `.get()`을 호출하고 그 결과를 L78(캐시)에 쓴다. 실행 후 값이 달라지는 쪽은 L78이다. L76은 생성자(L90/L102/L115/L131)에서 항상 람다로 채워져 있고, 오히려 lazy라서 null인 쪽이 L78이다.
3. `TypeDescriptor.java:730`의 `private interface AnnotatedElementSupplier extends Supplier<AnnotatedElementAdapter>, Serializable {}`은 `AnnotatedElementAdapter`의 부모를 상속하는 것이 아니라 `Supplier`와 `Serializable`을 상속한 함수형 인터페이스이고, `AnnotatedElementAdapter`는 `get()`의 반환 타입일 뿐이다. 여기에 `Serializable`을 붙였다는 것이 문제의 핵심 원인 — 이 타입의 람다는 직렬화 대상이 되고 캡처값(`Field`·`MethodParameter`·`Property`)까지 함께 직렬화하려 든다. 실패 원인은 `final`도, "Serializable이 없어서"도 아니라 람다가 캡처한 값의 타입이다.
4. `writeObject`에서 호출을 생략하면 — `writeObject`는 "서로 다른 객체를 주입"하는 훅이 아니라 직렬화 시점에 어떤 상태를 내보낼지 결정하는 훅이다. 한 번도 어노테이션을 조회하지 않은 디스크립터는 L78이 null이라 스트림에 `annotatedElement = null`이 실리고, 역직렬화하면 L76은 transient라 null, L78도 null이라 어노테이션이 영구 소실되며 이후 접근 시 NPE가 난다.

메인이 덧붙인 한 줄 요약: L76은 "만드는 방법"(못 싣는 것), L78은 "만들어진 결과"(실을 수 있는 것) — 수정의 본질은 스트림에 나가는 통로를 전자에서 후자로 바꾸는 것.

---

## G2 — diff 게이트: task 01 RED 테스트 (`TypeDescriptorTests.java`)

**질문** (원문, 1/2회차 — 제시된 diff는 라운드트립 헬퍼 1개 + 생성자별 테스트 4개, RED 결과 3 FAIL)

> **diff 게이트 (1/2)** — 위 "설계에서 의도한 두 가지"에 대해 답해주세요.
>
> 1. 헬퍼가 원본의 `getAnnotations()`를 미리 부르지 않고, 기대값을 `field`에서 직접 뽑는 이유는 무엇일까요? (미리 불렀다면 어떤 문제가 생길까요?)
> 2. 지금도 통과하는 네 번째 테스트를 굳이 추가한 이유는 무엇일까요?

**시도 1 — 답변** (사용자 원문)

> 어차피 어뎁터 실 결과값만 있으면 되니깐. 이걸 그대로 사용한다는거고 그럼 이 기능 자체가 서로 다른 서버끼리의 통신에서 해당
> 객체를 그대로 쓸 일이 있어? 아니면 이건 각 통신 객체 즉 어뎁터가 통신에 필요한 결과 산물이라 그대로 쓰는거고, 조립법은 필요없지만 디코딩할때 값을 꺼내야되니 위 문제를 통해 null로 제대로 생성만 되게 하면 되서 저렇게 한거야?
>
> 1번에서 field를 가지고 왔으면, field객체들과 만나는데 이때 serializerble이 없어서 직렬화가 불가능한 필드라 이식해서 예외를 발생시키고, 4번째 테스트는 확인테스트지. 기존에는 이 어노테이션배열로 그대로 생성되었기때문에 눈치채지 못했다는걸 명시하는 거 아니야?

**판정 1 — fail** (Q2는 정답 처리, Q1만 미달)

워커 부족점 (원문): Q2(네 번째 테스트 = 기존 `serializable()`이 `Annotation[]` 경로만 덮어서 놓쳤던 지점을 명시적으로 고정)는 맞다. Q1이 "왜 `NotSerializableException`이 나는가"에 대한 설명일 뿐, "왜 헬퍼가 굳이 미리 해석하지 않는 순서를 강제하는가"에 답하지 못했다. 헬퍼 주석의 "without resolving its annotations first"(`TypeDescriptorTests.java:775-778`)와 L78의 lazy 상태를 연결해서, `writeObject`의 강제 실체화 한 단계만 빠뜨린 반쪽 구현에 이 테스트를 돌리면 어떤 결과가 나올지를 기준으로 다시 생각할 것.

**재질문 (2/2회차)**

> fix를 하다가 세 단계 중 하나를 빠뜨렸다고 가정합시다.
>
> ```
> (1) L76에 transient + final 제거          <- 했음
> (2) readObject에서 L76 재구성              <- 했음
> (3) writeObject에서 강제 실체화            <- 빠뜨림 (writeObject 자체를 안 만듦)
> ```
>
> 이 **반쪽짜리 fix** 상태에서 다음 두 버전의 테스트를 각각 돌리면 어떤 결과가 나올까요?
>
> - **(a)** 헬퍼가 직렬화 **전에** `typeDescriptor.getAnnotations()`를 한 번 부르는 버전
> - **(b)** 지금처럼 **안 부르는** 버전

**시도 2 — 답변** (사용자 원문)

> 이거 내용 왜이렇게 어렵지. 내가 스프링을 이렇게 몰랐구나.
> Q2에 대해서 자세히 알아야될 꺼 같긴해. 저건 약간 찍은 느낌이라, Annotation[]에 대해서 서버 구동 시 해당 서버가 가진 어노테이션 배열을 덮어씌워서 문제없었다는거야? 그리고 Q1에서 직렬화 하는 과정에서 현재는 결과물은 L78객체가 직렬화 시 null이기 때문에, 이걸 채워줘야한다
> a라면 해당 어노테이션을 가져오는 과정에서 람다를 통해 78객체가 채워져 문제가 없지만 지금처럼 안부르면 null객체가 되기 때문이다. 이거같은데,

**판정 2 — pass**

워커 코멘트 (원문): (a)와 (b)가 갈리는 지점을 정확히 짚었다. (a)는 직렬화 전에 `getAnnotations()`가 supplier 람다를 실행해 L78을 채워 놓기 때문에 `writeObject`가 없어도 그 값이 그대로 스트림에 실려 통과하고, (b)는 L78이 null인 채로 실려 어노테이션이 소실된다. 보강 한 줄: (a)의 통과는 "문제가 없는" 것이 아니라 **가짜 green**이라는 점 — 테스트가 (3) 누락을 못 잡아 주므로, 헬퍼가 미리 해석하지 않는 것은 그 반쪽 fix를 red로 붙잡아 두기 위한 설계다.

**정답 정리 (Q2 — 대화에서 별도로 제시된 해설)**

네 번째 테스트를 넣은 이유는 "서버가 가진 어노테이션 배열을 덮어씌운다"가 아니다(그런 메커니즘은 없다). 4번 생성자만 캡처값이 `Annotation[]`이고 JDK annotation 프록시가 `Serializable`이라 이 경로만 통과하는데, 기존 `serializable()` 테스트가 `TypeDescriptor.forObject("")`에서 `valueOf(String.class)`를 거쳐 4번 생성자(`annotations = null`)로 하필 그 경로만 밟고 있었다. 그래서 2025-02 회귀 커밋이 CI를 통과했다. 네 번째 테스트의 목적은 "지금 되는 걸 확인"이 아니라, 4개 경로를 전부 지나가는 이번 fix가 지금 멀쩡한 이 경로까지 망가뜨리면 즉시 red가 뜨게 하는 회귀 앵커다. 덧붙여 annotation의 역직렬화는 배열을 덮어쓰는 것이 아니라 annotation 타입 이름과 멤버 값이 실리고 받는 쪽 JVM이 프록시를 새로 만드는 방식이다.

---

## G3 — diff 게이트: task 02 fix (`TypeDescriptor.java`)

**질문** (원문, 1/2회차 — 제시된 diff는 import 3줄, 필드 수식어 `final` -> `transient`, 직렬화 훅 2개 신규)

> **diff 게이트 (1/2)** — 두 가지 답해주세요.
>
> 1. `readObject`에서 `this.annotatedElement`를 그대로 두지 않고 `AnnotatedElementAdapter.from(...)`을 한 번 통과시키는 이유는? (앞서 EMPTY 얘기를 했었습니다)
> 2. `readObject`의 `this.annotatedElementSupplier = () -> annotatedElement;` 이 람다는 원래 생성자의 람다와 무엇이 다르고, 이 람다는 왜 직렬화 문제를 일으키지 않을까요?

**시도 1 — 답변** (사용자 원문)

> 1. 객체를 읽어들일 때 annotatedElement를 그대로 넣는 게 아니라, 어뎁터를 통해 78라인의 값이 비였는 지 실존하는 지 확인하고 비여있으면 EMPTY를 통해 중간 과정을 생략하고, 있으면 그대로 주입한다.
> 2번에 대해서는 기존에는 실제 람다 함수까지 가져와야됬지만 그 과정에서 write단계에서 문제가 발생하니 우리는 해당 객체에 대해 역직렬화시 넣지않고 그냥 바로 annotatedElement를 반환하는 방식으로 설정함으로 써 직렬화문제를 해결하고 역직렬화 시 해당 메서드가 필요 없으니 위와 같이 바로 뱉도록 설계한 것.

**판정 1 — fail** (Q2는 방향 정답, Q1 미달)

워커 코멘트 (원문): Q2는 방향이 맞다 — 새 람다는 재료(원본 리플렉션 객체) 없이 이미 복원된 어댑터 결과만 돌려주므로 캡처 문제가 사라진다는 인과를 짚었다. 보강: 원래 람다가 못 실린 이유는 "람다 함수 자체"가 아니라 그것이 캡처한 `Field`/`MethodParameter`/`Property` 값이고, 새 필드는 `transient`라 애초에 다시 직렬화될 일도 없다. Q1이 부족하다 — `from(...)`을 "비었는지 확인하는 가드"로만 읽었는데, 그렇다면 "역직렬화된 빈 어댑터를 그냥 두면 왜 안 되나"가 설명되지 않는다. `AnnotatedElementAdapter.isEmpty()`가 무엇을 무엇과 비교하는지, 그 클래스에 `readResolve()`가 있는지 없는지를 보고 다시 따져 볼 것.

**재질문 (2/2회차)**

> 어노테이션이 하나도 없는 `TypeDescriptor`를 직렬화했다가 되살렸습니다. 스트림에서 복원된 어댑터는 내부 배열 길이가 0인 빈 어댑터입니다.
>
> 1. 그 복원된 어댑터에 `isEmpty()`를 호출하면 **`true`인가요 `false`인가요?** 왜 그렇죠?
> 2. 그 결과가 `TypeDescriptor.hasAnnotation(...)`의 동작에 어떤 차이를 만들까요?

**되묻기** (판정 제출 전 — 메인이 `from()` 전문을 보여준 뒤 같은 2/2회차 질문을 재제시)

> 우선 Q2를 정리하면 람다 함수를 기존에 캡처한 내부 필드,메서드파라미터,프롬퍼티를 직렬화가 불가능해서 이걸 하지않도록, 한거고 나중에 읽을때도 이걸 null처리하도록, transient를 통해 직렬화할 필요도 없게 만든거다. 그리고
> Q1에서 일거들일 때 from 메서드가 어떤 메서드인지 먼저 알려주면 안될까? 난 저 메서드를 몰라.

**시도 2 — 답변** (사용자 원문)

> 그럼 1번 어차피 항상 true인데?
> 2번 빈 값이라 그대로 78라인 객체를 그대로 넣게 되겠지?

**판정 2 — fail (2회차이므로 통과 처리)**

**정답 정리** (워커 정정 원문)

1. `isEmpty()`는 **false**다. `isEmpty()`는 배열 길이를 보는 게 아니라 `this == EMPTY`, 즉 싱글턴 인스턴스와의 동일성 비교다(`AnnotatedElementAdapter.java:110-112`). 자바 역직렬화는 `from()`도 생성자도 거치지 않고 객체를 새로 만들어 필드를 채워 넣으므로, 스트림에서 복원된 어댑터는 배열 길이가 0이어도 `EMPTY`와 다른 인스턴스이고 `readResolve()`도 없어 싱글턴으로 되접히지 않는다. "빈 값이면 항상 true"라고 본 지점이 여기서 어긋난다.
2. `hasAnnotation`/`getAnnotation`의 shortcut이 죽는다. 두 메서드는 `isEmpty()`가 true일 때 즉시 `false`/`null`을 반환하는데(`TypeDescriptor.java:283-307`), false가 되니 어노테이션이 하나도 없는데도 매번 `AnnotatedElementUtils.isAnnotated(...)` / `getMergedAnnotation(...)`을 타게 된다. 반환값은 여전히 맞지만 불필요한 비용이 붙고, `getAnnotations()`도 EMPTY 분기를 못 타서 빈 배열을 매번 `clone()`한다(`AnnotatedElementAdapter.java:93`).
3. 그래서 `readObject`의 `AnnotatedElementAdapter.from(...)` 한 줄은 "null 가드"가 아니라 **싱글턴 정규화(canonicalization)** 다. 길이 0이면 `from()`이 `EMPTY`를 돌려주므로 역직렬화로 깨진 동일성이 복원되고 shortcut이 살아난다.

이 정규화는 이후 리뷰 단계에서 `serializableWithoutAnnotations()` 테스트(`getAnnotations()`를 두 번 불러 `isSameAs`로 방어 복사 여부를 관측)로 고정되었다.

---

## 반복된 오해 패턴

세 게이트에 걸쳐 되풀이된 오해는 여섯 갈래이고, 대부분 직렬화의 시점과 방향을 뒤집어 읽은 데서 나왔다.

1. **필드 방향 혼동 (G1 시도 1·2 연속)** — `getAnnotatedElement()`가 L78(캐시)을 읽어 L76(supplier)을 채운다고 반대로 이해했다. 실제는 L76을 읽어 L78에 쓴다. 두 번의 시도에서 같은 방향 오류가 반복됐다.
2. **실패 원인을 키워드에 귀속 (G1)** — `final` 때문에, 혹은 `Serializable`이 안 붙어서 직렬화가 실패한다고 봤다. 실제 원인은 `Serializable`이 붙은 함수형 인터페이스의 람다가 **캡처한 값의 타입**(`Field`·`MethodParameter`·`Property`)이다. `final` 제거는 원인이 아니라 `readObject` 재대입을 위한 뒤처리다.
3. **컴파일 시점 대 런타임 시점 혼동 (G1 이후 정정 라운드)** — "transient가 없으면 컴파일 오류가 난다"는 이해. javac는 직렬화 가능 여부를 검사하지 않고, 실패는 `ObjectOutputStream.writeObject()` 호출 시점에만 난다.
4. **직렬화와 역직렬화의 방향·순서 혼동 (G1 이후 정정 라운드, G3 시도 1)** — "객체를 힙에 올리는 순간 직렬화가 일어난다", "역직렬화하는 과정에서 writeObject로 직렬화한다"는 이해. 실제로는 직렬화가 명시적 호출로만 시작되고, 이번 버그는 쓰기 단계에서 터져 역직렬화는 실행조차 되지 않는다.
5. **동일성 기반 API를 값 기반으로 읽음 (G3 시도 2)** — `isEmpty()`가 배열 길이를 본다고 가정해 "빈 값이면 항상 true"라고 답했다. 실제는 `this == EMPTY` 동일성 비교이고, 역직렬화가 생성자와 정적 팩토리를 우회한다는 사실과 맞물려 false가 된다.
6. **테스트 설계 의도를 결함 설명으로 대체 (G2 시도 1)** — "왜 이 순서를 강제하나"라는 질문에 "왜 예외가 나는가"로 답했다. 테스트의 존재 이유(반쪽 fix를 red로 붙잡는 것)와 결함의 메커니즘을 구분하지 못한 사례.

## 교훈

이 게이트 기록에서 남길 만한 것은 네 가지다.

- 세 게이트 모두 1회차 fail이었고, 통과한 것은 G2 한 건뿐이다. 통과한 게이트의 공통점은 질문이 **구체적인 반사실 시나리오**("(3)만 빠뜨린 반쪽 fix에 (a)/(b) 테스트를 돌리면")로 좁혀졌을 때였다. 개념을 열어놓고 묻는 형태(G1 1회차, G3 1회차)에서는 답이 표면 복창으로 흘렀다.
- 워커가 1회차에 정답을 노출하지 않고 "다시 볼 파일과 줄 번호"만 제시하는 형식이 유지됐다(`TypeDescriptor.java:76-78`, `:256-263`, `:730` 등). 2회차 fail 시에는 규칙대로 정정 항목을 전부 열거하고 통과 처리했다.
- 되묻기가 두 번 있었고(G1의 transient 정의 요청, G3의 `from()` 정의 요청), 둘 다 시도 횟수를 소모하지 않고 메인이 먼저 답한 뒤 같은 회차의 질문을 재제시했다. 특히 G3의 "난 저 메서드를 몰라"는 판정 이전에 전제 지식 결손을 드러낸 사례로, 이후 정답 도달의 직접 조건이 됐다.
- 게이트에서 반복 노출된 개념 다섯 가지(직렬화 시점, transient의 적용 범위, 람다 캡처, 역직렬화가 생성자를 우회한다는 점, 동일성 기반 싱글턴)는 이후 `docs/plans/2026-08-04/c4-typedescriptor-serialization/`의 학습 문서 00~11로 정리되었고, 10번 문서가 이 오해들을 문답 형태로 모았다.
