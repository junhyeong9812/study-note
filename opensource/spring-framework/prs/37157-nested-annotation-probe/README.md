# PR #37157 — Extend TypeNotPresentException probing to nested annotations

## 0. 정향

이 문서는 PR #37153(enum 배열 probe)의 리뷰에서 발견된 후속 결함 — nested
annotation 안의 지연 실패를 probe가 못 본다 — 를 고친 PR의 해설이다. #37153의
해설(`../37153/README.md`)을 먼저 읽는 것이 좋다: 이 PR은 같은 방어망의 다음
구멍을 메우되, **1줄로는 안 되는** 이유가 핵심이기 때문이다. 다 읽으면 "플래그만
추가하면 왜 안 잡히는가"와 "재귀가 왜 안전한가(종료·예외 전파)"를 설명할 수
있어야 한다.

같은 폴더: [테스트 해설](tests.md). 개념 문서(오늘 작업에서 파생):
[JLS annotation 규칙](../../concepts/jls-annotation-rules/jls-annotation-rules.md) ·
[Mockito stubbing 메커니즘](../../concepts/mockito-stubbing-mechanics/mockito-stubbing-mechanics.md) ·
[all-or-nothing 계약](../../concepts/annotation-all-or-nothing-contract/annotation-all-or-nothing-contract.md)

## 1. 배경 — 발견 경로가 특이한 PR

이 결함은 코드 정독이 아니라 **직전 PR의 리뷰 논리에서** 나왔다. #37153이 "단일
enum은 다루는데 enum[]이 빠졌다"를 고치자, 리뷰어가 같은 계산식에 그 논리를
재적용했다: annotation 타입 속성(`type.isAnnotation()` 계열)도 probe 목록에 없지
않은가? 스모크(v1/v2 enum 2단 컴파일 + nested annotation)로 확인하니 실제로
재현됐고 — 단, 예상과 다른 지점이 하나 있었다.

## 2. 수정 전 동작 — 플래그 추가만으로는 안 되는 이유

probe는 "속성을 한 번 실호출해 보고 예외를 관측"하는 장치다. 그런데 nested
annotation 속성은 **invoke가 성공한다**: JDK는 nested annotation 프록시를 정상
반환하고, 폭탄은 그 프록시 **안**(nested의 자기 속성)에 있어서 한 겹 호출로는
예외가 나오지 않는다.

```
프레임 1: outer.value() 호출  → Inner 프록시 반환 (성공!)
프레임 2: inner.color() 호출  → EnumConstantNotPresentException (여기가 폭탄)
```

그래서 #37153식 1줄 확장(플래그에 annotation 추가)만으로는 아무것도 잡지 못한다.
probe가 반환값을 받아 **그 안으로 들어가야**(재귀) 한다.

## 3. 무엇이 문제였나 (실측)

수정 전, nested 멤버가 오염된 annotation은 스캔을 통과해(`isPresent=true`):
`asMap()`이 오염된 nested 프록시를 값으로 실어 나르고(silent corruption),
`synthesize().value().color()`는 raw `EnumConstantNotPresentException`을 사용자
코드에 누출했다. 같은 오염이 직접 속성에 있으면 필터링되는 것과 비대칭.

## 4. 수정 해설

세 조각이다:

1. **플래그 확장**: 계산식에 annotation/annotation[] 추가. 바로 윗줄
   `hasNestedAnnotation` 검사와 동일 표현식이라 지역 변수로 1회 계산해 공유
   (리뷰 F4 반영).
2. **재귀 probe**: `canLoad`/`validate`가 invoke 반환값을 캡처, `Annotation`/
   `Annotation[]`이면 `forAnnotationType(...)`로 재귀. canLoad는 boolean false가
   위로 전파되고, validate는 안쪽 프레임이 만든 `IllegalStateException`이
   `catch (ISE) { throw ex; }`를 통해 **재래핑 없이** 그대로 올라간다 — 그래서
   예외/로그가 실제로 깨진 가장 안쪽 annotation을 지목한다(진단 품질).
3. **종료 보장**: 재귀에 visited 집합이 없어도 안전하다 — JLS §9.6.1이 annotation
   멤버 타입의 순환을 컴파일 에러로 금지하므로 값 트리는 항상 유한하다. (메타-
   annotation 그래프는 순환 가능하지만 이 재귀는 그 축이 아니다 —
   [jls-annotation-rules.md](../../concepts/jls-annotation-rules/jls-annotation-rules.md).)

**의도된 blast radius**: nested 멤버 1개의 결함이 바깥 annotation 전체를 스캔에서
숨긴다. 속성 단위 부분 숨김은 annotation 타입 계약상 표현 불가능하다(던짐=원점
회귀/null=계약 위반/기본값=조작 — [all-or-nothing 계약](../../concepts/annotation-all-or-nothing-contract/annotation-all-or-nothing-contract.md)).
`canLoad` javadoc의 "true if all values are present"가 원래 이 의미론이다.

**범위 밖(Case A)**: nested annotation **타입 자체**가 classpath에 없으면
`getDeclaredAnnotations()` 파싱 단계에서 `NoClassDefFoundError`가 나 probe에
도달조차 못 한다 — probe로는 원리적으로 방어 불가, PR 본문에 한계로 명시.

## 5. 검증 — 이번엔 측정까지

검증은 단위 테스트와 실물 스모크에 더해 이번에는 성능 측정까지 세 층으로 쌓았다.

- test-first: 6 red -> fix -> 리뷰 반영 후 27/27 green + 패키지 스위트.
- 실물 스모크: 수정 후 `isPresent=false` + warn 로그가 `@Inner`(실제 문제
  annotation)를 지목, `asMap()={}`. Case A는 불변(한계 확인).
- **마이크로벤치**(사용자 요청 — "측정 없이 정당화 안 되면 측정하면 되잖아"):
  before/after jar로 canLoad 직접 호출. 기존 probe 무회귀(enum 25->25ns), nested
  속성당 +50~70ns(추가된 리플렉션 읽기가 지배 항), 스캐너의 element 캐시가 반복
  제한. 이 수치가 "사전 게이트 최적화는 복잡도 대비 실익 약함" 판단의 근거이자
  PR 본문의 성능 서술이 됐다.

## 6. 교훈

이 PR이 남긴 것은 결함을 찾는 법, fix 모양의 다양성, 논쟁을 끝내는 측정, red 단계의 자기검증 넷이다.

1. **리뷰의 논리를 diff 밖으로 재적용하면 다음 버그가 나온다.** "빠진 대칭"을
   찾은 논리는 같은 식의 다른 계열에도 물어볼 가치가 있다.
2. **같은 모양의 구멍이라도 fix의 모양은 다를 수 있다.** enum[]은 1줄, nested는
   재귀 — invoke가 성공하는지(폭탄의 위치가 어느 겹인지)가 갈랐다.
3. **"측정 없이 정당화 불가"는 측정하라는 뜻.** 추정 공방 대신 20분짜리 벤치가
   성능 논쟁을 종결하고 PR 본문의 방어 논리까지 만들어 줬다.
4. **테스트가 실패하는 이유가 의도한 이유인지 red 단계에서 확인하라.** Mockito
   중첩 stubbing 버그로 red 6 예측이 8 실패로 나왔다 — 실패 개수만 보고 넘어갔으면
   엉뚱한 테스트를 신뢰할 뻔했다.
