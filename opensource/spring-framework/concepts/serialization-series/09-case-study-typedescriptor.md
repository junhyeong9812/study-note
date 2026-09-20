# 09. 케이스 스터디 — 개념으로 다시 읽는 C4

> 01~08·11의 개념들이 **하나의 버그에서 어떻게 맞물리는지** 순서대로 따라간다.
> (작업 서사·판단 기록은 [PR #37109 해설](../../prs/37109-typedescriptor-serialization/README.md), 여기서는 **메커니즘**만.)

## 등장 인물

무대에 오르는 것은 `TypeDescriptor`의 네 필드다.

```java
public class TypeDescriptor implements Serializable {          // ← 계약: 직렬화 가능

    private final Class<?> type;                                        // Class → 이름으로 복원 (07)
    private final ResolvableType resolvableType;                        // SerializableTypeWrapper 로 감싸짐 (07)
    private transient AnnotatedElementSupplier annotatedElementSupplier;// 레시피 — 직렬화 제외 (04, 06)
    private volatile @Nullable AnnotatedElementAdapter annotatedElement;// 결과 — 직렬화 대상 (02, 04)
}
```

**한 문장 모델: 76번 줄은 "만드는 방법", 78번 줄은 "만들어진 결과".**

## 1막 — 아무 일도 없다 (컴파일 · 생성)

먼저 평범한 생성 경로를 따라간다.

```java
Field field = MyBean.class.getDeclaredField("name");
TypeDescriptor td = new TypeDescriptor(field);
```

세 시점에 무슨 일이 일어나는지 정리하면 다음과 같다.

| 시점 | 무슨 일이 | 관련 문서 |
|---|---|---|
| javac | 람다 본문이 `lambda$new$1`로 분리, `invokedynamic` 삽입. **직렬화 가능 여부는 검사하지 않음** | [01](01-compile-vs-runtime.md), [06](06-lambda-internals.md) |
| `new` 실행 | 힙에 객체 생성, 생성자가 supplier 필드에 람다 대입. **이때 `field`가 캡처된다** | [02](02-heap-and-object-graph.md), [06](06-lambda-internals.md) |
| 이후 | `annotatedElement`는 `null`. 아무도 안 물어보면 계속 null (lazy) | [02](02-heap-and-object-graph.md) |

여기까지 **아무 문제 없다.** `td.getAnnotations()`도 정상 동작한다. 대다수 애플리케이션이 이 상태로만 산다.

## 2막 — 직렬화 요청 (문제 발생)

누군가 `writeObject(td)`를 호출한다. 실무에서는 세션 복제·분산 캐시·원격 예외 전송 같은 프레임워크 동작이다([03](03-serialization-basics.md)).

```
writeObject(td) — 객체 그래프를 순회 (02)
 ├─ type             : Class            O
 ├─ resolvableType   : ResolvableType   O
 ├─ annotatedElement : null             O
 └─ annotatedElementSupplier : 람다
      └─ writeReplace() → SerializedLambda (06)
           └─ capturedArgs[0] = Field    X Serializable 아님 (07)
                ! NotSerializableException: java.lang.reflect.Field
```

핵심 인과 세 줄:

1. **직렬화는 객체 그래프를 따라간다** — 필드가 가리키는 객체를 계속 파고든다([02](02-heap-and-object-graph.md))
2. **직렬화 가능 람다는 캡처값을 함께 싣는다** — 되살려서 실행하려면 재료가 필요하니까([06](06-lambda-internals.md))
3. **`Field`는 JVM 내부 상태라 실을 수 없다**([07](07-reflection-objects.md))

그리고 이 실패는 **런타임**에만, **쓰기 시점**에만 일어난다([01](01-compile-vs-runtime.md), [03](03-serialization-basics.md)).

## 3막 — 수정 (통로 갈아끼우기)

```java
private transient AnnotatedElementSupplier annotatedElementSupplier;   // (04) 스트림에서 제외
```

이제 그래프 순회가 supplier를 아예 안 본다 -> `Field`를 만날 일이 없다. 하지만 두 구멍이 생긴다.

**구멍 (1) — 결과가 안 실릴 수 있다**

lazy라 `annotatedElement`가 `null`인 채 실릴 수 있다. 그러면 받는 쪽은 레시피도(transient) 결과도(null) 없어 어노테이션을 영구히 잃는다.

```java
private void writeObject(ObjectOutputStream outputStream) throws IOException {
    getAnnotatedElement();          // (05) 부작용으로 78번 필드를 채운다
    outputStream.defaultWriteObject();
}
```

**구멍 (2) — 받는 쪽에 레시피가 없다**

`transient` 필드는 역직렬화된 객체에서 `null`이다([04](04-transient-and-volatile.md)). 그리고 역직렬화는 생성자를 건너뛰므로 다시 채워지지도 않는다([05](05-serialization-hooks.md)).

```java
private void readObject(ObjectInputStream inputStream) throws IOException, ClassNotFoundException {
    inputStream.defaultReadObject();
    AnnotatedElementAdapter annotatedElement = AnnotatedElementAdapter.from(   // (08) 싱글턴 정규화
            this.annotatedElement != null ? this.annotatedElement.getAnnotations() : null);
    this.annotatedElement = annotatedElement;
    this.annotatedElementSupplier = () -> annotatedElement;                    // (06) 재료 없는 새 람다
}
```

- `final`을 뗀 이유는 **여기서 대입해야 하기 때문**이지, final이 직렬화를 막아서가 아니다([04](04-transient-and-volatile.md))
- 새 람다가 캡처하는 것은 `AnnotatedElementAdapter`(Serializable) — **재료가 아니라 결과**([06](06-lambda-internals.md))
- `from(...)`은 빈 어댑터를 `EMPTY` 싱글턴으로 되접는다. 역직렬화가 팩토리를 우회해 동일성이 깨졌기 때문([08](08-identity-and-singleton.md))

## 4막 — 부작용 (수정이 만든 파장)

이 수정은 세 가지 파장을 남겼다.

| 파장 | 내용 | 문서 |
|---|---|---|
| `serialVersionUID` 변경 | private transient는 UID 해시에서 제외 -> 구스트림은 `InvalidClassException` | [11](11-serialversionuid.md) |
| 예외 타입 변화 | 어노테이션 클래스 부재 시 `TypeNotPresentException`(전) `NotSerializableException`(후) | — |
| lazy는 유지 | 해석 강제는 `writeObject` 안에서만 | [02](02-heap-and-object-graph.md) |

## 전체 타임라인 한 장

네 국면을 한 장에 겹쳐 놓으면 다음과 같다.

```
(1) 생성           supplier = 람다(Field 캡처)      annotatedElement = null
                  ─ 컴파일·실행 모두 정상, 문제 없음

(2) 직렬화 (전)     그래프 순회 → 람다 → capturedArgs[Field] → !
   직렬화 (후)     getAnnotatedElement() 로 결과 실체화
                  → defaultWriteObject: 결과 O 실림 / 레시피 X 제외

(3) 역직렬화        생성자 우회, 필드 직접 주입
                  → 결과 복원됨, 레시피는 null
                  → from(...) 로 EMPTY 정규화 + 결과를 돌려주는 새 람다 설치

(4) 이후 사용       겉보기 동작 동일 (getAnnotations / hasAnnotation 정상)
                  단 원본 Field 참조는 영원히 사라짐 (필요 없으므로 무해)
```

## 이 케이스가 가르쳐주는 것

1. **성능 최적화가 계약을 깰 수 있다.** lazy 도입 자체는 옳았지만, 그 수단(직렬화 가능 람다)이 `Serializable` 계약과 충돌했다.
2. **테스트가 커버하는 "경로"를 봐야 한다.** 직렬화 테스트는 있었지만 4개 생성자 중 유일하게 안 깨지는 경로만 밟고 있었다.
3. **불변식은 명시적으로 고정해야 한다.** lazy 유지·EMPTY shortcut처럼 깨져도 조용한 것은 테스트로 못 박지 않으면 다음 사람이 무심코 되돌린다.
4. **필드 수식어 하나가 wire 호환을 바꾼다.** `Serializable` 클래스에서는 `final`·`transient` 한 글자가 공개 계약이다.
