# 개념: Mockito stubbing은 어떻게 기록되나 — UnfinishedStubbingException의 원리

> F1(nested annotation probe) 테스트 작성 중 실제로 밟은 함정의 배경 문서. 핵심
> 주장: `given(...)`은 마법 문법이 아니라 일반 Java 코드이고, stubbing 기록은
> 스레드당 1칸짜리 "열림/닫힘" 상태 기계다.

## given()은 문법이 아니다

```java
given(mock.value()).willReturn(x);
```

Java 입장에서 이 줄은 특별할 게 없다 — `given()`을 호출하기 전에 인자
`mock.value()`가 **실제로 호출**된다. Mockito는 "지금 given 안이다"를 알 수 없다.
그래서 다른 방식으로 동작한다:

1. mock의 메서드가 호출되면, Mockito가 스레드 로컬의 **"진행 중(ongoing) stubbing"
   슬롯**에 그 호출을 기록하고(= stubbing이 **열림**) 더미 값을 반환한다.
2. `willReturn(...)`/`willThrow(...)`가 그 슬롯을 읽어 stubbing을 **완결**하고
   슬롯을 비운다(= **닫힘**).

즉 stubbing은 "mock 호출로 열고 -> willReturn류로 닫는" 한 쌍이고, 슬롯이 하나라
**열린 상태에서 다른 mock 상호작용이 끼어들면 상태 기계가 깨진다**. 그때 던지는
것이 `UnfinishedStubbingException`이다.

## 실제로 밟은 함정 (F1 테스트, 2026-08-19)

```java
given(outer.value()).willReturn(mockBrokenInner());   // 실패
```

실행 순서를 따라가면:

1. `outer.value()` 호출 -> stubbing #1 열림
2. `willReturn`의 **인자 평가** -> `mockBrokenInner()` 실행
3. 그 안의 `given(inner.value()).willThrow(...)` -> `inner.value()` 호출이
   stubbing #2를 열려고 함
4. #1이 아직 안 닫힌 상태 -> `UnfinishedStubbingException`

수정은 안쪽 mock을 변수로 선행 생성하는 것:

```java
EnumValueInner inner = mockBrokenInner();   // #2가 열리고-닫혀 완결
given(outer.value()).willReturn(inner);     // #1이 열리고, 인자는 변수라 mock을 안 건드림 → 즉시 닫힘
```

열기-닫기 쌍이 시간축에서 절대 겹치지 않게 하는 것이 규칙의 전부다.

## 흔한 오해 정정

- "프록시가 단일이라 다중 주입이 안 된다" — 아니다. mock 프록시는 몇 개든 만들 수
  있다. 제약은 프록시 개수가 아니라 **진행 중 stubbing 슬롯이 스레드당 1칸**이라는
  기록 방식에 있다.
- 이 함정은 `willReturn` 인자에서 **mock을 만들기만** 하는 것(mock() 호출 자체)이
  아니라, 만들면서 **그 mock을 stubbing까지** 할 때 터진다 — 새 stubbing이 열리는
  행위가 문제의 본질이다.
- 같은 이유로, stubbing 도중 다른 mock의 메서드를 검증(verify)하거나 호출하는
  것도 금지다.

## 이 원리가 주는 일반 규칙

헬퍼 메서드가 "mock 생성 + stubbing"을 함께 하는 패턴은 유용하지만, **그 헬퍼를
다른 stubbing의 인자 위치에서 호출하면 안 된다**. 헬퍼 반환값을 변수로 받은 뒤
다음 줄에서 주입하라. 실측: 이 함정 하나로 red 예측 6건이 8건 실패(엉뚱한 예외
2건 포함)로 나와 원인 분석이 한 라운드 추가됐다 — "테스트가 실패하는 이유가
의도한 이유인가"를 red 단계에서 반드시 확인해야 하는 근거 사례.
