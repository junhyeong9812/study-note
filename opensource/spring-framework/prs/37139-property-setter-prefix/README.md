# PR #37139 — Reject write methods not starting with "set" in Property

## 0. 정향

이 문서는 PR #36911에서 분리된 setter 판별 강화 PR의 해설이다. 분리 자체가
메인테이너(sbrannen)의 요청이었으므로, "왜 같은 메서드의 두 수정이 다른 PR이
되는가"가 이 문서의 또 하나의 주제다. `Property`가 무엇인지는 `../36911/README.md`
1절을 먼저 읽어야 한다.

## 1. 배경 — write 분기의 자리

`Property#resolveName()`은 카드가 이름 없이 만들어졌을 때 접근자 메서드 이름에서
논리 이름을 유도한다. 읽기 메서드가 없고 쓰기 메서드만 있으면 write 분기가
실행된다: setter 이름에서 `set`을 벗겨 프로퍼티 이름을 만든다. 이 유도는 순수
문자열 처리다 — 필드 존재를 확인하지 않고, 유도된 이름과 일치하는 필드가 없어도
프로퍼티는 유효하다.

read 분기와의 구조 차이가 중요하다. read 분기에는 "규약 밖 이름은 이름 전체를
쓴다"는 폴백이 있지만, write 분기에는 폴백이 없다 — setter 규약에 안 맞으면
`IllegalArgumentException("Not a setter method")`로 거부한다. 프로퍼티의 쓰기
경로는 `setXxx` 규약이 전부이기 때문이다.

## 2. 수정 전 동작 방식 — indexOf가 만드는 구멍

수정 전 코드는 거부 판정을 `indexOf`로 했다:

```java
int index = this.writeMethod.getName().indexOf("set");
if (index == -1) {
    throw new IllegalArgumentException("Not a setter method");
}
index += 3;
return StringUtils.uncapitalize(this.writeMethod.getName().substring(index));
```

`indexOf`는 이름 어디서든 `set`을 찾는다. 그래서 거부되는 것은 "`set`이라는 글자가
아예 없는 이름"뿐이고, 중간이나 끝에 `set`을 품은 이름은 통과해서 그 뒤를 이름으로
삼는다.

## 3. 무엇이 문제였나 — 조용히 만들어지는 엉뚱한 이름

값으로 따라가면 구멍이 보인다. 다음 표는 write 메서드별 수정 전 결과다.

| write 메서드 | indexOf 결과 | 수정 전 결과 |
|---|---|---|
| `setName(String)` | 0 | `name` (정상) |
| `updateName(String)` | -1 | 예외 (정상 거부) |
| `offsetX(String)` | 3 | `x` (엉뚱한 이름, 무음 통과) |
| `upset(String)` | 2 | 빈 문자열 (무음 통과) |

`offsetX`의 계산: o-f-f-**s-e-t**-X에서 `set`이 3번 위치, +3이면 6번, `substring(6)`
= "X", uncapitalize로 "x". 예외 없이 조용히 성공하므로, 이 이름을 소비하는 쪽
(`getField()`, `getName()` 비교)이 영문 모를 오동작을 한다. read 분기의 indexOf
버그(#36911)와 같은 뿌리다.

## 4. 수정 해설 — startsWith 한 곳, 그리고 분리의 이유

수정은 판별을 시작 위치로 제한한다:

```java
String methodName = this.writeMethod.getName();
if (!methodName.startsWith("set")) {
    throw new IllegalArgumentException("Not a setter method");
}
return StringUtils.uncapitalize(methodName.substring(3));
```

동작이 바뀌는 집합은 정확히 "`set`을 포함하되 `set`으로 시작하지 않는 이름"이다.
`setName`(정상)과 `updateName`(원래도 거부)은 전후 동일하고, `offsetX`/`upset`은
무음 통과에서 생성 시점 예외로 바뀐다.

이것이 #36911에서 분리된 이유다. read 분기 수정은 "잘못된 이름을 옳은 이름으로"
고치는 것이지만, setter 수정은 "이전에 통과하던 호출이 예외를 던지게 되는" 동작
강화(behavior change)다. 성격이 다른 두 변경을 한 PR에 묶으면 리뷰·롤백 단위가
흐려지므로, 메인테이너가 "1 PR = 1 논리 변경" 원칙대로 분리를 요청했다.

남는 공백도 정직하게 공개했다: `settle(String)`처럼 `set` 뒤에 소문자가 오는
이름은 전후 모두 "tle"로 해석된다 — 접두사 매칭만으로는 setter와 구분할 수 없어
이 PR의 범위 밖이다. 또한 새 예외의 실파급은 작다: 프레임워크 내부에서 이름 없이
카드를 만드는 곳은 SpEL뿐이고, SpEL의 setter 탐색은 원래 `set`+이름 형태를 찾는다
(예외적으로 Kotlin `@JvmName` 개명 setter 경로가 있으나, #37123이 SpEL에 명시
이름을 넘기게 바꾸면 이 경로 자체가 사라진다).

## 5. 검증 — 테스트 4건이 각각 고정하는 것

`PropertyTests` 4건은 표의 네 행을 그대로 고정한다. `setName -> name`은 강화가
정상 경로를 다치게 하지 않았음을(과도한 엄격화·substring 오프셋 실수 방지),
`updateName` 예외는 원래 있던 거부의 회귀 가드를, `offsetX`/`upset` 예외는 이 PR의
행위 변경 자체를 고정하며 예외 메시지까지 단언한다.

참고로 #36911 브랜치에도 별도 `PropertyTests`가 추가돼 있어, 두 PR 중 나중에
머지되는 쪽이 테스트 파일을 합치는 사소한 rebase를 하게 된다.

## 6. 상태와 교훈

2026-08-14 제출, 리뷰 대기 중이다.

교훈 둘. 첫째, 같은 결함(indexOf 부분일치)이라도 고침의 결과가 "옳은 값"인지 "새
예외"인지에 따라 리스크 등급이 다르다 — 후자는 별도 PR, 별도 공개가 맞다. 둘째,
동작 강화 PR의 테스트는 양방향이어야 한다: 거부해야 할 것을 거부하는 단언만 있으면
"여전히 받아야 할 것을 받는다"는 반대 방향 실수를 못 잡는다.

---

연관 ko-docs (모듈 지도): `spring-core/02-타입-변환-conversion.md`
