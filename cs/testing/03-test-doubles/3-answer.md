# testing/03-test-doubles — 정답

## 정답

### 1. 더블이 없을 때

- SUT가 DB·결제 API·메일 서버에 기대면, 테스트가 그 부품을 실제로 써야 한다.
  - 느리고, 데이터를 준비해야 하고, 돈이 나가거나 메일이 간다.
  - "결제 실패"처럼 **DOC가 내야 하는 응답**을 테스트가 마음대로 만들 수 없다.
- 더블은 **DOC**를 대신한다. SUT는 진짜로 실행한다(xunitpatterns.com "Test Double": "replace the real DOC (not the SUT!)").

### 2. 간접 입력·간접 출력

```text
   테스트 ──직접 입력──▶ SUT ──직접 출력──▶ 테스트
                         │ ▲
           간접 출력(호출)│ │간접 입력(반환값·예외)
                         ▼ │
                         DOC
```

- Stub: 간접 입력 화살표(DOC → SUT)를 조종한다.
- Spy: 간접 출력(SUT → DOC)을 기록해 두고, 테스트가 나중에 꺼내 단언한다.
- Mock: 간접 출력을 더블 자신이 미리 받은 기대와 대조한다.

### 3. 다섯 더블

| 이름 | 하는 일 |
|---|---|
| Dummy | 인자 자리만 채운다. 실제로 쓰이지 않는다 |
| Fake | 동작하는 가벼운 구현(인메모리 DB·HashMap 저장소). 운영에는 못 쓴다 |
| Stub | 정해 둔 답을 돌려준다 |
| Spy | Stub처럼 답하면서 받은 호출을 기록한다 |
| Mock | 받아야 할 호출에 대한 기대를 미리 프로그램해 두고 대조한다 |

- Mockito `spy(obj)`는 실제 객체의 **복사본**으로 부분 mock을 만든다. stub하지 않은 메서드는 진짜 메서드 코드가 그 복사본 위에서 돈다. 원본에 호출을 넘기지 않으므로, spy를 만든 뒤 원본을 바꿔도 spy는 모른다(Mockito javadoc 13절, 실험: real=1·spied=2). Meszaros의 Spy는 호출을 기록하는 더블일 뿐, 실제 객체를 바탕으로 할 필요가 없다.

### 4. "mock"의 여러 뜻

- Meszaros·Fowler: 다섯 분류 중 하나. 기대를 미리 프로그램해 행위 검증을 하는 더블.
- Khorikov: 크게 둘로 나눈다. mock(mock·spy)은 **나가는** 상호작용(상태를 바꾸는 호출)을 흉내·검사하고, stub(stub·dummy·fake)은 **들어오는** 입력을 흉내 낸다.
- SWE@G 13장: 더블 종류보다 기법으로 나눈다 — faking, stubbing, interaction testing. 실제 구현을 먼저 고려하라("Prefer Realism Over Isolation").
- Mockito: `mock()`이 만든 객체 하나가 `when`으로 stub도 되고 `verify`로 mock도 된다(Mockito의 용어). `verify`는 실행 뒤에 테스트가 기록을 대조하므로, Meszaros 분류로는 Mock Object보다 Test Spy에 가깝다.
- stub 단언 금지 이유: SUT가 stub을 부르는 것은 결과를 얻는 **과정**이지 결과가 아니다("A call from the SUT to a stub is not part of the end result the SUT produces"). 단언하면 구현 세부에 묶여 리팩터링마다 깨진다.

### 5. 같은 시나리오, 더블 세 종류

| 더블 | 결과 |
|---|---|
| Mockito Stub(작성자의 믿음대로 `-1`, 오래된 것 먼저) | 2개 모두 초록 |
| Fake(HashMap, 계약대로 예외·최신 먼저) | `missingAccount` 오류(`NoSuchElementException: account nope`), `lastTransfer` 실패(`expected: 300L but was: 100L`) |
| H2 실제 구현 | Fake와 같은 두 지점에서 같은 오류·실패 |

- Fake와 H2는 같은 계약 테스트 2개를 모두 통과했다. 그래서 Fake의 실패를 실제 구현의 실패로 믿을 수 있다.
- 서비스를 계약대로 고치고 Stub도 계약에 맞게 다시 쓰자 11개 전부 통과했다. Stub은 테스트마다 따로 고쳐야 했다.

### 6. Mockito 기본 응답

- 실험 출력: `count=0 boxed=0 name=null list=[] opt=Optional.empty obj=null`.
  - 원시·래퍼 숫자는 0, 컬렉션은 빈 것, `Optional`은 `Optional.empty()`, 그 밖의 참조는 `null`(Mockito 5.24.0 `ReturnsEmptyValues`).
- 조용한 버그: 없는 계좌의 `findBalance`(원시 `long`)를 stub하지 않으면 0이 온다. 서비스는 `balance=0`을 돌려줬다. 예외도 실패도 없다.

### 7. 계약 테스트와 Fake

- 계약 테스트: 인터페이스의 공개 동작을 시험하는 같은 테스트 묶음을 실제 구현과 Fake 양쪽에 돌린다(SWE@G 13장 "Fakes Should Be Tested").
- 필요한 이유: Fake도 코드라서 실제와 어긋날 수 있다. 양쪽이 같은 테스트를 통과해야 Fake로 얻은 결과를 실제에 대해 믿을 수 있다.
- SWE@G 13장: 실제 구현을 가진 팀이 Fake를 만들고 유지하라고 권한다.

### 8. `UnnecessaryStubbingException`

- `MockitoExtension`의 기본 엄격도 `STRICT_STUBS`에서, 테스트가 stub했지만 SUT가 한 번도 부르지 않은 호출이 있다는 뜻이다.
- 확인할 것
  - 리팩터링으로 SUT의 호출 경로가 바뀌었나? 그렇다면 그 stub은 지운다.
  - `@BeforeEach`에 모아 둔 공용 stub 때문인가? 필요한 테스트로 옮긴다.
  - 처음부터 테스트가 호출 경로를 잘못 알고 있었나? 테스트가 의도한 시나리오를 실제로 타는지 본다.
- 이유를 확인한 뒤에야 `lenient()`를 고려한다.

### 9. 초록인데 운영에서 `NoSuchElementException`

- 원인 후보
  - 저장소를 전부 Mockito stub으로 바꿔 실제 구현이 한 번도 실행되지 않았다.
  - stub이 실제 계약과 다른 답(`-1`·`null`)을 돌려줬다.
  - Fake가 있었지만 실제 구현과 어긋났다(계약 테스트 부재).
- 재발 방지
  - 계약을 인터페이스 주석과 계약 테스트로 고정하고, Fake와 실제 구현 양쪽에 CI로 돌린다.
  - 서비스 테스트는 계약 테스트를 통과한 Fake로 돌린다.
  - 반환 타입으로 "없음"을 드러낸다(`Optional`).
  - 핵심 경로 몇 개는 실제 조립으로 시험한다(통합·인수 테스트).

### 10. 고르는 순서와 "내 타입만 mock"

- 순서
  - 실제 구현이 빠르고 결정적이면 실제 구현(SWE@G "Prefer Realism Over Isolation").
  - 아니면 계약 테스트를 통과한 Fake.
  - 입력만 필요하면 Stub.
  - 앱 밖에서 관찰되는 출력(메일·외부 API·메시지)이면 Mock·Spy로 호출 검증.
  - 앱 전용 DB 같은 관리형 의존은 실제 구현으로 통합 테스트(Khorikov).
- "Only Mock Types That You Own"(GOOS 8장): 라이브러리 타입을 직접 stub하면, 그 라이브러리의 실제 동작을 테스트 작성자가 추측해 적게 된다. 버전이 바뀌어 동작이 달라져도 테스트는 모른다. 내 인터페이스(어댑터)를 두고 그것을 더블로 바꾸며, 어댑터는 실제 라이브러리와 붙여 시험한다.
