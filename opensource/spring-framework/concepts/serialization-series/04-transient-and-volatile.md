# 04. `transient`와 `volatile`

> 이번 대화에서 나온 오해: **"`transient`를 붙이면 그 필드는 항상 `null`이 된다"** -> 아니다. 살아 있는 객체에는 아무 영향이 없다.

두 키워드는 나란히 나오지만 **완전히 다른 상대에게 하는 말**이다.

| 키워드 | 누구에게 하는 말인가 | 무엇을 요구하나 |
|---|---|---|
| `transient` | **직렬화기**(`ObjectOutputStream`/`InputStream`) | "이 필드는 스트림에 싣지 마라" |
| `volatile` | **JVM 메모리 모델**(스레드·CPU 캐시) | "이 필드는 항상 메인 메모리에서 읽고 쓰라" |

## 1. `transient`

### 하는 일

`defaultWriteObject()`가 필드를 순회할 때 **건너뛴다.** 그게 전부다.

```java
class Session implements Serializable {
    String userId;                 // 실린다
    transient Socket connection;   // 안 실린다 (Socket 은 직렬화 불가)
}
```

### 살아 있는 객체에는 영향이 없다

대입도 호출도 평소와 똑같이 동작한다.

```java
Session s = new Session();
s.connection = socket;          // 정상 대입
s.connection.getPort();         // 정상 동작 — transient 는 여기 관여하지 않는다
```

값이 비는 시점은 딱 하나, **역직렬화로 새로 만들어진 객체**다. 그 객체는 생성자를 거치지 않고 만들어지는데, 스트림에 값이 없으니 기본값(참조형 `null`)으로 남는다.

```
원본 객체        : connection = Socket@ab3   ← 멀쩡함
      │ 직렬화 (connection 은 스킵)
      ▼
스트림           : { userId: "jun" }
      │ 역직렬화
      ▼
복원된 새 객체    : connection = null         ← 여기서만 null
```

### 그래서 항상 따라붙는 질문

> "그 필드를 어떻게 되살릴 것인가?"

세 가지 선택지가 있다.

1. **그냥 null로 둔다** — 다시 안 쓰는 값이면 그것으로 충분
2. **`readObject`에서 다시 채운다** — C4가 택한 방법
3. **lazy 재계산** — 접근 시점에 null이면 만들어 넣는 방식

### `final`과 함께 쓸 수 없는 이유

`readObject`에서 값을 다시 넣으려면 **대입**을 해야 하는데, `final` 필드는 생성자·초기화식 밖에서 대입할 수 없다. 그래서 C4의 fix는 `final`을 뗐다.

```java
// before
private final AnnotatedElementSupplier annotatedElementSupplier;
// after
private transient AnnotatedElementSupplier annotatedElementSupplier;
```

**주의**: `final`을 뗀 것은 "final이면 직렬화가 안 돼서"가 아니다. 직렬화 실패의 원인은 어디까지나 **람다가 캡처한 값의 타입**이었고, `final` 제거는 `transient`를 붙인 **결과로 필요해진 뒷정리**다.

## 2. `volatile`

### 하는 일

멀티스레드 환경에서 **가시성(visibility)** 과 **재정렬 금지(ordering)** 를 보장한다. 직렬화와는 아무 관계가 없다.

```java
class Flag {
    boolean running = true;              // 다른 스레드의 변경이 안 보일 수 있다
    volatile boolean runningV = true;    // 항상 최신값을 본다
}
```

`volatile` 없이 쓰면 각 스레드가 CPU 캐시에 들고 있는 옛 값을 계속 볼 수 있어, 무한루프에 빠지는 고전적인 버그가 생긴다.

### `volatile`이 보장하지 **않는** 것

원자성(atomicity)은 보장하지 않는다.

```java
volatile int count;
count++;      // 읽기 → 더하기 → 쓰기 3단계. 여전히 경쟁 상태가 생긴다
```

증가 연산이 필요하면 `AtomicInteger`나 `synchronized`를 써야 한다.

### C4에서 `volatile`이 쓰인 이유

문제의 필드는 다음 한 줄이다.

```java
private volatile @Nullable AnnotatedElementAdapter annotatedElement;
```

이 필드는 **lazy 캐시**다. 여러 스레드가 동시에 `getAnnotations()`를 부를 수 있는데,

- A 스레드가 어댑터를 만들어 필드에 넣었을 때, B 스레드가 **그 사실을 즉시 보게** 하려고 `volatile`
- 두 스레드가 동시에 만들어도 결과가 동등한 어댑터라 문제가 없다(**benign race**). 그래서 `synchronized`까지는 안 쓴다.

```java
private AnnotatedElementAdapter getAnnotatedElement() {
    AnnotatedElementAdapter annotatedElement = this.annotatedElement;  // volatile 읽기 1회
    if (annotatedElement == null) {
        annotatedElement = this.annotatedElementSupplier.get();
        this.annotatedElement = annotatedElement;                      // volatile 쓰기
    }
    return annotatedElement;
}
```

필드를 로컬 변수로 한 번만 읽는 것도 의도적이다 — `volatile` 읽기는 일반 읽기보다 비싸고, 중간에 값이 바뀌어도 이 메서드 안에서는 일관된 값을 쓰게 된다.

## 3. 헷갈리기 쉬운 조합 정리

네 조합을 한자리에 놓으면 두 수식자가 서로 무관하다는 것이 드러난다.

```java
private static final int A = 1;      // static: 인스턴스가 아니라 클래스에 속함 → 직렬화 안 됨
private transient int b;             // 직렬화 스킵
private volatile int c;              // 직렬화 됨! volatile 은 직렬화와 무관
private transient volatile int d;    // 둘 다 적용 (직렬화 스킵 + 가시성 보장)
```

수식자별로 정리하면 다음과 같다.

| 수식자 | 직렬화에 실리나 | 스레드 가시성 |
|---|---|---|
| (없음) | 예 | 아니오 |
| `transient` | 아니오 | 아니오 |
| `volatile` | 예 | 예 |
| `static` | 아니오 | 아니오 |

**C4의 두 필드가 정확히 대비되는 예다:**

```java
private transient AnnotatedElementSupplier annotatedElementSupplier;   // 안 실림 (레시피)
private volatile @Nullable AnnotatedElementAdapter annotatedElement;   // 실림   (완성품)
```

## 4. 손으로 확인하기

transient 필드의 값이 어느 객체에서만 비는지를 세 줄의 출력으로 확인할 수 있다.

```java
import java.io.*;

public class TransientDemo {
    static class Holder implements Serializable {
        String kept = "kept";
        transient String dropped = "dropped";

        @Override public String toString() { return kept + " / " + dropped; }
    }

    public static void main(String[] args) throws Exception {
        Holder original = new Holder();
        System.out.println("살아있는 객체       : " + original);   // kept / dropped  ← transient 여도 값 있음

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        new ObjectOutputStream(out).writeObject(original);

        System.out.println("직렬화 후 원본      : " + original);   // kept / dropped  ← 원본은 안 변함

        Holder copy = (Holder) new ObjectInputStream(
                new ByteArrayInputStream(out.toByteArray())).readObject();
        System.out.println("역직렬화된 새 객체  : " + copy);       // kept / null     ← 여기서만 null
    }
}
```

세 줄의 출력 차이가 이 문서의 핵심이다.

## 정리

1. `transient` = 직렬화기에게 하는 말. **살아 있는 객체에는 영향 없음.**
2. 값이 비는 것은 **역직렬화로 만들어진 객체**뿐 -> 되살릴 방법을 함께 설계해야 한다.
3. `final`은 `readObject`에서 대입을 막으므로 함께 쓸 수 없다(직렬화 실패 원인과는 무관).
4. `volatile` = 스레드 가시성. 직렬화와 무관하고, 원자성도 보장하지 않는다.
