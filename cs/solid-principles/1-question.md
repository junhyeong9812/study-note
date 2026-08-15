# SOLID 원칙 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

## 질문

**1. (왜)** SOLID 5가지 원칙 사이의 우선순위는 어떻게 되는가? 어떤 원칙이 어떤 원칙을 싸게 만들어주는가?

**2. (왜 — 원칙 위의 질문)** 이 원칙들보다 우선시되어야 하는 것은 무엇인가? 원칙끼리 부딪힐 때 무엇으로 판정하는가?

**3. (경계)** 단일 책임 원칙의 "단일 책임"은 무엇을 기준으로 판정하는가? 그 기준은 코드만 읽어서 판정할 수 있는가?

**4. (충돌)** 클래스를 잘게 나눌수록 SRP는 지켜진다. 그때 무엇과 부딪히고, 어떻게 푸는가?

**5. (경계)** 의존관계 역전(DIP)과 의존성 주입(DI)의 차이는 무엇인가? 둘은 어떤 관계인가?

**6. (판단)** 아래 코드에서 `instanceof`가 "다형성이 깨진 증거"인 이유는 무엇인가? 좋은 instanceof와 나쁜 instanceof는 어떻게 구별하는가?

```java
public class AreaCalculator {
    public double area(Shape shape) {
        if (shape instanceof Circle c) {
            return Math.PI * c.radius() * c.radius();
        } else if (shape instanceof Rectangle r) {
            return r.width() * r.height();
        }
        throw new IllegalArgumentException("모르는 도형");
    }
}
```

**7. (연결 — db-engine-lab)** 아래 LogManager의 replay는 레코드를 해석하지 않고 핸들러에게 넘기기만 하고, "커밋된 것만 반영한다" 같은 판단은 호출자(Recovery)가 한다. 이 분리는 SOLID 중 어떤 원칙(들)의 사례인가? LogManager가 커밋 판단까지 하면 각 원칙 관점에서 무엇이 나빠지는가?

```kotlin
/** LSN-aware replay — handler receives (lsn, record). */
fun replayWithLsn(handler: (Long, LogRecord) -> Unit) {
    file.seek(0)
    var lsn = 0L
    while (file.filePointer < file.length()) {
        try {
            val len = file.readInt()
            val bytes = ByteArray(len)
            file.readFully(bytes)
            lsn++
            handler(lsn, decode(bytes))
        } catch (_: EOFException) {
            break
        }
    }
    file.seek(file.length())
}
```

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
