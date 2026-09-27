# java/syntax/34 — `import`·static import·(25) 모듈 import 선언 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력(에러 메시지 포함)을 맞힐 수 있는지**를 묻는다.
> 선행 없음. 이어지는 주제: [58 리플렉션](../58-reflection/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 온디맨드 둘이 겹치면 어디서 터지나 (예측)

```java
import java.util.*;
import java.awt.*;

public class Ex {
    public static void main(String[] args) {
        List x = null;
    }
}
```

- 컴파일되는가? 에러라면 **몇 번째 줄**에서 나는가?
- 에러 메시지의 첫 줄을 적을 수 있는가?
- `List x = null;` 을 지우면 컴파일되는가?

### 2. 단일 타입 import 둘이 겹치면 (예측)

```java
import java.util.List;
import java.awt.List;
```

- 이 두 줄만으로 컴파일 에러가 나는가?
- 1번과 **에러 나는 위치와 문구가 어떻게 다른가**?
- 두 경우를 문구만 보고 구별할 수 있는가?

### 3. 누가 이기나 — 우선순위 (예측)

```java
// 같은 패키지에 이런 클래스가 있다
public class List { public String toString() { return "내가 만든 List"; } }
public class Integer { public String toString() { return "내 Integer"; } }

// Ex.java
import java.util.*;
public class Ex {
    public static void main(String[] args) {
        List x = new List();
        Integer i = new Integer();
        System.out.println(x + " / " + i);
    }
}
```

- 두 변수의 타입은 각각 무엇인가? 출력은 무엇인가?
- `java.lang.Integer` 도 가려지는가?
- 진짜 `java.util.List` 를 쓰려면 어떻게 하는가?
- 우선순위 네 단계를 강한 쪽부터 말할 수 있는가?

### 4. `import` 를 지우고 풀네임으로 바꾸면 클래스 파일이 같은가 (예측)

```java
// A: import 를 쓴 판
import java.util.ArrayList;
import java.util.List;
import static java.lang.Math.max;
// B: 전부 풀네임으로 쓴 판 (import 0줄)
```

- `javap -c -p` 출력이 같은가?
- 클래스 파일 **바이트**도 같은가?
- 다르다면 어느 속성이 다른가, 그것을 무엇으로 확인했는가?
- 여기서 나오는 결론은 "쓰지 않는 `import` 를 지우는 이유"에 대해 무엇을 말하는가?

### 5. `import module java.base;` 를 21 과 25 에서 각각 (예측)

```java
import module java.base;

public class Ex {
    public static void main(String[] args) {
        List<String> names = List.of("a", "b", "c");
        Path p = Path.of("/tmp");
        System.out.println(names + " " + p);
    }
}
```

- JDK 21 에서 컴파일하면 무엇이 나오는가 — 에러 메시지 첫 줄은?
- JDK 25 에서는 `--enable-preview` 가 필요한가?
- 이것이 **정식인가 프리뷰인가**, 그것을 어떻게 확인했는가?
- `java.base` 가 export 하는 패키지는 몇 개인가 — 어떻게 셌는가?

### 6. 모듈 import 두 개를 겹치면 (예측)

```java
import module java.base;
import module java.desktop;
...
List<String> x = List.of("a");
```

- 컴파일되는가? 에러면 메시지는 무엇인가?
- 1번과 같은 종류의 에러인가?
- 해소하는 방법은 무엇인가?

### 7. `import java.util.*;` 로 `ConcurrentHashMap` 이 들어오나 (경계)

- 들어오는가?
- 들어오지 않는다면 그 이유를 한 문장으로 말할 수 있는가?
- 패키지 이름의 점(`.`)은 무엇을 뜻하는가?

### 8. `static import` 의 경계 (경계)

- `static import` 로 들여올 수 있는 것은 메서드뿐인가?
- 인터페이스의 static 메서드(`List.of`)도 되는가?
- 같은 이름의 static 메서드를 두 타입에서 온디맨드로 들여오면 어떻게 되는가?
- 시그니처가 다르면 어떻게 되는가?

### 9. 남용 경계 (왜)

- `static import` 를 쓸 자리와 안 쓸 자리를 가르는 한 줄 기준은 무엇인가?
- 테스트 코드에서 널리 쓰이는 이유는 무엇인가?
- 모듈 import 선언이 권장되는 자리는 어디이고, 권장되지 않는 자리는 어디인가?

### 10. 왜 이런 규칙인가 (왜)

- 온디맨드 충돌을 `import` 줄이 아니라 **쓰는 줄**에서 터뜨리는 설계의 이득은 무엇인가?
- 단일 타입 import 가 온디맨드를 이기게 한 이유는 무엇인가?
- 같은 패키지 타입이 `java.lang` 까지 가리게 한 것의 대가는 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- `import` 와 접근 제어(`private`·package-private)는 각각 무엇을 정하는가?
- `Class.forName("java.util.List")` 는 `import` 의 영향을 받는가?
- `import` 가 통과했는데 실행에서 터질 수 있는가 — 어떤 오류인가?
- 클래스 이름을 `Target`·`Type`·`Field` 로 지으면 무슨 일이 생기는가?

### 12. 중첩 타입과 static 멤버 import (예측)

```java
// (가)
import java.util.*;
...
Entry<String,Integer> e = null;

// (나)
import java.util.Map.Entry;
import static java.util.Map.entry;
...
Entry<String,Integer> e = entry("a", 1);
```

- (가) 는 컴파일되는가? 아니면 에러 메시지는 무엇인가?
- 온디맨드 import 가 중첩 타입을 주지 않는 이유는 무엇인가?
- (나) 의 `entry("a",1)` 이 돌려준 객체의 구현 클래스 이름은 무엇인가 — 그 이름에 기대도 되는가?
- 중첩 타입을 쓰는 다른 방법은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
