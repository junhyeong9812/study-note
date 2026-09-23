# cs/issue/java/serializable-capture-contract — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: `contract-drift`

## 정답
<!-- 질문 1:1 대응 -->

1. **직렬화 람다가 싣는 것.** 직렬화 가능한 람다는 `SerializedLambda`로 바뀌어 스트림에 실린다 — 람다를 만든 클래스·구현 메서드 정보와 함께 **캡처한 값들(`capturedArgs`)** 이 그대로 들어간다. 캡처값이 `java.lang.reflect.Field`처럼 `Serializable`이 아닌 객체면 `writeObject`가 `NotSerializableException: java.lang.reflect.Field`를 던진다.
   > **SerializedLambda** — 직렬화 가능한 람다의 직렬화 형태. 캡처 인자를 필드로 가진다.

2. **캐시를 채워도 실린다.** supplier 필드가 `final`·non-transient이면 기본 직렬화 대상이므로, 캐시(결과 필드)를 이미 채웠어도 **supplier 자체가 함께 실린다**. 지연 초기화는 "필요할 때만 리플렉션으로 계산"하려는 성능 최적화였는데, 그 수단(리플렉션 객체를 캡처한 람다)이 클래스가 선언한 `Serializable` 계약과 정면으로 충돌했다. 이전 버전에서는 직렬화되던 객체가 이 최적화 이후 직렬화되지 않게 된 **회귀**였고, 이 객체를 non-transient 필드로 들고 있는 예외 타입 등이 있어 실제로 밟히는 경로였다.

3. **우연히 안전한 경로.** 생성자가 여럿이었고, 기존 테스트는 **어노테이션 배열을 캡처하는 생성자만** 사용했다. 어노테이션 인스턴스(프록시)는 `Serializable`이므로 그 경로에선 직렬화가 성공한다. `Field`·메서드 파라미터를 받는 생성자는 테스트가 밟지 않아 회귀가 가려졌다 — 테스트가 계약을 검증하려면 **캡처 대상이 다른 모든 생성 경로**를 밟아야 한다.

4. **transient만으로는 부족.** `transient`로 바꾸면 supplier는 빠지지만, 역직렬화된 객체에는 supplier가 null이고 결과 캐시가 비어 있으면 복원할 방법이 없다. 그래서
   - `writeObject`: 먼저 결과 getter를 호출해 **캐시 필드를 강제로 채운 뒤** `defaultWriteObject` — 계산 결과(직렬화 가능)만 보낸다.
   - `readObject`: `defaultReadObject` 후 캐시 값으로 supplier를 **재구성**하고, 빈 결과를 **싱글턴으로 정규화**한다.\
   역직렬화는 생성자를 거치지 않아 "빈 값이면 EMPTY 싱글턴을 쓴다"는 생성자 보장이 사라진다. `isEmpty()`가 `== EMPTY`로 빠른 판정을 하면 역직렬화된 빈 객체는 그 빠른 경로를 못 탄다 — 그래서 `readObject`에서 팩터리를 통해 다시 정규화한다(`readResolve`는 없었다).\
   supplier를 non-final로 둔 것은 `readObject`에서 재할당하기 위해서다.
   > **transient** — 기본 직렬화에서 제외되는 필드 수식어.

5. **시끄러운 실패가 낫다.** `serialVersionUID`를 고정하면 구 스트림도 읽히지만, 구 스트림의 어노테이션 정보는 **supplier 필드에만** 들어 있고 그 필드는 이제 transient라 읽히지 않으므로 **어노테이션 정보가 조용히 사라진 객체**가 만들어진다. 고정하지 않으면 필드 수식어 변경(`private transient`)으로 기본 UID가 달라져(실측) `InvalidClassException`이 나고, 호환되지 않음이 즉시 드러난다. 조용한 손실은 나중에 원인 추적이 어렵기 때문에 명시적 실패를 택했다.

6. **재조회 좌표를 보낸다.** 인터페이스가 `extends Serializable`을 선언했는데 구현 두 곳이 JDK 내부 `TypeVariable` 구현(비직렬화)을 직접 보유해 선언 계약을 어겼다. 교정은 운반자 클래스에 `writeReplace()`/`readResolve()` 직렬화 프록시를 두는 것:
   - `writeReplace`: `TypeVariable` 객체 대신 **(그 타입 변수를 선언한 클래스, 타입 파라미터 인덱스)** 마커를 보낸다.
   - `readResolve`: 마커로 `declaringClass.getTypeParameters()[index]`를 다시 조회해 **같은 선언의 타입 변수**를 얻는다 → JDK의 타입 변수 equals/hashCode는 선언 요소와 이름으로 판정하므로 보존된다(인스턴스 동일성은 명세상 보장되지 않으므로 `==`에 기대지 않는다). 입력 검증에 실패하면 `InvalidObjectException`. (클래스에 선언된 타입 변수 기준 — 메서드·생성자에 선언된 타입 변수라면 그 실행 요소를 찾을 좌표가 더 필요하다.)\
   enum 직렬화가 상수 객체가 아니라 **이름**을 보내고 복원 시 같은 상수를 찾는 것과 같은 구조다.
   > **직렬화 프록시(writeReplace/readResolve)** — 직렬화 직전 다른 객체로 바꿔 쓰고, 역직렬화 직후 원래 객체로 되돌리는 훅.

7. **비용을 직렬화 경로에만.** "생성 시점에 모든 타입을 직렬화 가능한 래퍼로 감싸기" 후보는 과거에 같은 방식이 되돌려진 이력이 있었고, 실측에서 약 3배 오버헤드가 나와 선택하지 않았다. 또 일부 API 계열의 비직렬화는 문서화된 의도적 트레이드오프라 버그가 아니라고 재분류해 계약 축소 후보도 보류했다.\
   직렬화 프록시는 **직렬화할 때만** 비용을 낸다 — 직렬화하지 않는 대다수 사용 경로의 비용은 0이다. 드물게 쓰이는 계약을 위해 흔한 경로를 느리게 만들지 않는다.

## 문제 구조 (추상화 코드)

### 변형 A — 지연 초기화 람다가 리플렉션 객체를 캡처
① 문제 코드
```java
public class Desc implements Serializable {
    private final ElementSupplier supplier;                  // final · non-transient
    private AnnotatedElement cached;

    public Desc(Field field) {
        this.supplier = () -> resolve(field);               // 직렬화 람다가 Field 캡처
    }
    public Desc(Annotation[] annotations) {
        this.supplier = () -> adapt(annotations);           // 어노테이션 프록시는 직렬화 OK (테스트는 여기만)
    }
}
// writeObject(new Desc(field)) → NotSerializableException: Field
```
② 고친 코드
```java
    private transient ElementSupplier supplier;             // 직렬화 제외, readObject에서 재할당

    private void writeObject(ObjectOutputStream out) throws IOException {
        getAnnotatedElement();                              // 캐시 강제 해석 (부작용 호출)
        out.defaultWriteObject();
    }
    private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
        in.defaultReadObject();
        AnnotatedElement a = ElementAdapter.from(cached != null ? cached.getAnnotations() : null);
        this.cached = a;                                    // 빈 값은 EMPTY 싱글턴으로 정규화 (생성자 우회 대비)
        this.supplier = () -> a;
    }
// serialVersionUID는 고정하지 않음 → 구 스트림은 InvalidClassException (조용한 손실 대신)
```
무엇이 깨졌나: 최적화용 람다가 비직렬화 객체를 캡처해 `Serializable` 선언을 어겼고, 테스트는 안전한 생성 경로만 밟았다.

### 변형 B — 필드가 JDK 내부 비직렬화 타입을 보유
① 문제 코드
```java
interface VariableResolver extends Serializable { Type resolve(TypeVariable<?> v); }

class VariablesResolver implements VariableResolver {
    private final TypeVariable<?>[] variables;              // JDK 내부 구현 — Serializable 아님
    // ...
}
class SyntheticGenericType implements ParameterizedType, Serializable {
    private final Type[] typeArguments;                     // 원소가 TypeVariable일 수 있음
}
// writeObject(holder) → NotSerializableException: TypeVariableImpl
```
② 고친 코드
```java
    private Object writeReplace() {
        return new Marker(encode(variables));               // TypeVariable → (declaringClass, index)
    }
    // Marker
    private Object readResolve() throws ObjectStreamException {
        TypeVariable<?>[] params = declaringClass.getTypeParameters();
        if (index < 0 || index >= params.length) throw new InvalidObjectException("bad index");
        return rebuild(params[index]);                      // 같은 선언의 타입 변수 재조회 → equals 보존
    }
// 비직렬화 경로의 비용 0 (생성 시점 래핑 방식은 ~3배 오버헤드로 선택하지 않음)
```
무엇이 깨졌나: 인터페이스가 선언한 `Serializable` 계약을 구현의 필드 타입이 지키지 못했다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
