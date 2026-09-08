# PR #36912 — 테스트 해설 (테스트 하나하나)

> PR #36912 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR이 추가한 테스트는 `GeneratedClassTests`에 한 건이다. 프로덕션 diff가 한 글자
(`reservedMethodNames` -> `reservedMethodName`)인 만큼 테스트도 한 건인데, 그 한 건이
4년 가까이 아무도 실행한 적 없던 경로 — 이름을 둘 이상 넘기는 varargs 경로 — 를
처음으로 밟는다.

## 1. 여러 이름 예약 — red

유일한 새 테스트는 이름 둘을 한 번에 예약한 뒤, 그 뒤의 발급 이름이 각각 번호를 달고
나오는지 본다.

```java
@Test
void reserveMethodNamesWhenMultipleNamesReservesEachName() {
	GeneratedClass generatedClass = createGeneratedClass(TEST_CLASS_NAME);
	generatedClass.reserveMethodNames("apply", "test");
	assertThat(generatedClass.getMethods().add("apply", emptyMethodCustomizer).getName()).isEqualTo("apply1");
	assertThat(generatedClass.getMethods().add("test", emptyMethodCustomizer).getName()).isEqualTo("test1");
}
```

- **주장**: 두 가지다. 첫째, 이름을 둘 넘긴 `reserveMethodNames` 호출이 예외 없이
  끝난다. 둘째, 예약 효과가 이름마다 **개별로** 걸려 이후 발급이 `apply1`과 `test1`이
  된다.
- **fix 전**: 둘째 줄에서 이미 터진다. 루프 첫 반복이 `MethodName.of("apply", "test")`를
  만들어 `applyTest`를 발급받고, 검증문 `Assert.state("applyTest".equals("apply"))`가
  거짓이 되어 `IllegalStateException: Unable to reserve method name 'apply'`가 던져진다.
  단언 두 줄에는 도달조차 하지 않는다. 명백한 red다.
- **fix 후**: 반복마다 자기 이름으로 시퀀스를 한 번씩 소모하므로, 이후 `add("apply")`와
  `add("test")`가 각각 시퀀스 1을 받아 `apply1`, `test1`이 된다.

이 테스트에서 눈여겨볼 설계 판단은 **무엇으로 예약을 관측하는가**다. `GeneratedClass`는
"이 이름이 예약되었나"를 묻는 공개 API가 없고, 예약은 `methodNameSequenceGenerator`라는
private 맵의 카운터 상태로만 존재한다. 리플렉션으로 그 맵을 들여다볼 수도 있었지만
테스트는 그러지 않고, **관측 가능한 바깥 계약**인 "다음 발급 이름"으로 확인한다.
`apply1`이라는 값은 `apply`의 시퀀스가 이미 한 번 소모됐을 때만 나오는 값이므로,
내부 상태를 직접 읽지 않고도 예약 사실을 값으로 증명한다.

두 개의 단언을 모두 두는 이유도 여기 있다. 한 줄만 두면 "첫 이름만 예약되고 둘째는
누락"되는 절반 수정이 통과한다. 두 이름 각각에 대해 번호가 붙는다는 사실이 곧 루프가
per-element로 돌았다는 증거다.

## 2. 이 PR이 추가하지 않은 것 — 기존 테스트 두 건의 역할

이 PR은 기존 테스트를 손대지 않았다. 그런데 그 두 건이 새 테스트의 배경 대조군이므로
같이 읽어야 배치가 보인다.

`reserveMethodNamesReservesNames`는 이름 **하나**를 예약하고 다음 발급이 `apply1`임을
고정한다. 이 테스트가 fix 전에도 green이었다는 사실이 버그가 오래 숨은 이유를 그대로
설명한다. 한 원소 배열은 `MethodName.of(배열)`과 `MethodName.of(원소)`가 같은 값을
만들기 때문에, 잘못된 인자를 넘기고도 결과가 우연히 맞았다. 이 PR의 관점에서 보면
기존 테스트는 **의도치 않은 양성 가드**다 — 수정 후에도 여전히 green이어야 하며, 실제로
그렇다(한 원소 경로의 동작은 변하지 않는다).

`reserveMethodNamesWhenNameUsedThrowsException`은 이미 사용된 이름은 예약할 수 없고
`IllegalStateException`이 나야 함을 고정한다. 이 PR이 `Assert.state`를 건드리지 않았음을
보증하는 자리다. 새 테스트가 "예외가 나지 않아야 한다"를 요구하므로, 자칫 검증문 자체를
지워 버리는 잘못된 수정이 나올 수 있는데 이 기존 테스트가 그것을 막는다. 즉 두 테스트는
"예약 성공은 조용히, 예약 실패는 시끄럽게"라는 계약의 양쪽 끝을 각각 잡고 있다.

## fixture

이 테스트는 새 fixture를 만들지 않고 클래스의 기존 헬퍼 두 개를 그대로 쓴다.

```java
createGeneratedClass(TEST_CLASS_NAME)   // 빈 GeneratedClass 하나
emptyMethodCustomizer                    // 메서드 본문을 채우지 않는 no-op 커스터마이저
```

`emptyMethodCustomizer`가 흉내 내는 것은 실제 AOT 코드 생성기가 넘기는 메서드 본문
빌더다. 이번 검증 대상은 **생성될 메서드의 이름 발급**뿐이고 본문의 내용은 무관하므로,
본문을 비워 관심사를 이름 하나로 좁혔다. mock 라이브러리는 쓰지 않는다 —
`GeneratedClass`의 카운터는 외부 협력자 없이 자기 안에서 완결되는 순수 상태라, 흉내 낼
협력자가 애초에 없다.

`"apply"`와 `"test"`라는 이름 선택에도 의미가 있다. 둘 다 함수형 인터페이스
(`Function#apply`, `Predicate#test`)의 메서드 이름이라, "생성 클래스가 특정 인터페이스를
구현하면서 손으로 쓴 메서드 이름을 미리 잡아 둔다"는 이 API의 실제 사용 시나리오와
겹친다. 게다가 두 이름을 합치면 `applyTest`라는, 어느 쪽과도 같지 않은 제3의 이름이
나오므로 버그의 증상이 값으로 선명하게 드러난다.

## 실측·역할 요약

수정 전후로 실제 실행한 결과를 건수·실패 지점·통과 값으로 정리하면 다음과 같다.

- 추가된 테스트: 1건. 분류: red 1건, 가드 0건.
- fix 전 결과: 두 번째 줄에서 `IllegalStateException`으로 실패(단언 도달 전).
- fix 후 결과: `apply1`, `test1`로 통과.

역할은 하나로 요약된다. 이 테스트는 **public varargs API의 "2개 이상" 경로**를 처음으로
고정한다. 기존 테스트는 "1개" 경로만 덮고 있었고, 그 경로에서는 버그가 결과에 나타나지
않았다. varargs·컬렉션 파라미터를 "0개, 1개, 2개 이상"의 서로 다른 경로로 보고 테스트를
갖추라는 README의 교훈이, 정확히 이 한 건의 존재 이유다.
