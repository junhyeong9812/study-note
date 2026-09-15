# PR #37157 — Extend TypeNotPresentException probing to nested annotations

## 0. 정향

이 문서는 PR #37153(enum 배열 probe)의 리뷰에서 발견된 후속 결함 — nested annotation 안의 지연 실패를 probe가 못 본다 — 를 고친 PR의 해설이다.\
#37153의 해설(`../37153/README.md`)을 먼저 읽는 것이 좋다.\
이 PR은 같은 방어망의 다음 구멍을 메우되, **1줄로는 안 되는** 이유가 핵심이기 때문이다.\
다 읽으면 "플래그만 추가하면 왜 안 잡히는가"와 "재귀가 왜 안전한가(종료·예외 전파)"를 설명할 수 있어야 한다.

> **nested annotation(중첩 annotation)** — annotation의 속성 값 자리에 또 다른 annotation이 들어간 것.\
> 예: `@ComponentScan(includeFilters = @Filter(...))`에서 `@Filter`가 nested annotation이다.

> **probe(사전 시험 호출)** — 진짜로 쓰기 전에 속성을 한 번 불러 보고 "터지나"만 확인하는 검사.\
> 예: `canLoad()`가 `value()`를 호출해 놓고 반환값은 받지 않는다.

> **지연 실패(lazy failure)** — 값을 저장할 때가 아니라 읽는 순간에야 터지는 실패.\
> 예: 클래스 파일에는 `"BLUE"`라는 이름만 있고, 그 이름을 enum 상수로 바꾸다 실패하는 건 `value()` 호출 시점이다.

같은 폴더: [테스트 해설](tests.md).\
개념 문서(오늘 작업에서 파생): [JLS annotation 규칙](../../concepts/jls-annotation-rules/jls-annotation-rules.md) · [Mockito stubbing 메커니즘](../../concepts/mockito-stubbing-mechanics/mockito-stubbing-mechanics.md) · [all-or-nothing 계약](../../concepts/annotation-all-or-nothing-contract/annotation-all-or-nothing-contract.md)

## 1. 배경 — 발견 경로가 특이한 PR

이 결함은 코드 정독이 아니라 **직전 PR의 리뷰 논리에서** 나왔다.\
#37153이 "단일 enum은 다루는데 enum[]이 빠졌다"를 고치자, 리뷰어가 같은 계산식에 그 논리를 재적용했다: annotation 타입 속성(`type.isAnnotation()` 계열)도 probe 목록에 없지 않은가?\
스모크(v1/v2 enum 2단 컴파일 + nested annotation)로 확인하니 실제로 재현됐고 — 단, 예상과 다른 지점이 하나 있었다.

> **스모크(smoke test)** — 고치기 전에 "정말 그 현상이 일어나나"를 최소 재현으로 직접 돌려 보는 확인.\
> 예: enum v1으로 컴파일한 annotation을 enum v2와 함께 실행해 실제 누출을 눈으로 본다.

## 2. 수정 전 동작 — 플래그 추가만으로는 안 되는 이유

probe는 "속성을 한 번 실호출해 보고 예외를 관측"하는 장치다.\
그런데 nested annotation 속성은 **invoke가 성공한다**.\
JDK는 nested annotation 프록시를 정상 반환하고, 폭탄은 그 프록시 **안**(nested의 자기 속성)에 있어서 한 겹 호출로는 예외가 나오지 않는다.

> **프록시(proxy)** — 실제 객체 대신 앞에 세워져 호출을 받아 넘기는 대리 객체.\
> 예: `@Inner`를 읽으면 JDK가 `Inner` 인터페이스의 동적 프록시를 만들어 주고, `color()` 호출은 그 프록시 안에서 처리된다.

스캔이 시작해서 어디서 멈추는지를 세로로 따라가면 이렇다.

```text
AnnotationsScanner.getDeclaredAnnotations(source)
        |
        v
AttributeMethods.forAnnotationType(@Outer).canLoad(outer, source)
        |
        +-- 플래그 게이트 : @Outer 의 속성 타입은 @Inner (annotation)
        |      |
        |      +-- 수정 전 판정식에 annotation 계열이 없다 -> 플래그 false
        |              -> 실호출 자체를 건너뜀 -> 관측 기회 0
        |
        +-- [만약 플래그만 추가했다면]
               |
               v
        프레임 1 : invoke(outer.value())
               |
               +-- @Inner 프록시 반환 (성공) -> 반환값은 받지 않고 버림
               |
               v
        프레임 2 : inner.color()  <- 폭탄은 여기 있다
               |
               +-- 아무도 호출하지 않는다 -> 예외 없음
        |
        v
canLoad == true -> 스캔 통과 -> isPresent() == true
```

```text
프레임 1: outer.value() 호출  → Inner 프록시 반환 (성공!)
프레임 2: inner.color() 호출  → EnumConstantNotPresentException (여기가 폭탄)
```

그래서 #37153식 1줄 확장(플래그에 annotation 추가)만으로는 아무것도 잡지 못한다.\
probe가 반환값을 받아 **그 안으로 들어가야**(재귀) 한다.

> **재귀(recursion)** — 같은 검사를 한 단계 안쪽 대상에 대해 자기 자신을 다시 부르는 방식.\
> 예: `@Outer`를 검사하다 안쪽 `@Inner`를 만나면, `@Inner`에 대해 똑같은 `canLoad`를 다시 돌린다.

## 3. 무엇이 문제였나 (실측)

수정 전, nested 멤버가 오염된 annotation은 스캔을 통과해(`isPresent=true`) 이렇게 됐다.\
`asMap()`이 오염된 nested 프록시를 값으로 실어 나르고(silent corruption), `synthesize().value().color()`는 raw `EnumConstantNotPresentException`을 사용자 코드에 누출했다.\
같은 오염이 직접 속성에 있으면 필터링되는 것과 비대칭.

같은 폭탄을 두 위치에 놓고 나란히 보면 비대칭이 선명해진다.

```text
같은 폭탄: 런타임에 없는 enum 상수를 가리키는 값

  오염이 직접 속성에 있을 때              오염이 한 겹 안에 있을 때 (수정 전)
  ExampleEnum value()                     @Inner value(), @Inner 안에 폭탄
  +-------------------------------+        +------------------------------+
  | invoke -> 즉시 예외           |        | invoke -> 프록시 반환 (성공)  |
  | 예외 관측 : 있음              |        | 예외 관측 : 없음             |
  | isPresent() = false           |        | isPresent() = true           |
  | asMap()     = {}              |        | asMap() = {value=오염 프록시} |
  | typed 접근  = missing 계약    |        | typed 접근 = 예외 누출       |
  +-------------------------------+        +------------------------------+
    -> 방어망이 작동한다                     -> 한 겹 들어가자 방어망이 사라진다
```

폭탄의 종류는 같은데 **폭탄이 몇 번째 겹에 있느냐**만 다르다.

> **silent corruption(무음 오염)** — 에러 없이 잘못된 값이 그대로 다음 단계로 흘러가는 실패.\
> 예: `asMap()`이 정상처럼 보이는 맵을 돌려주는데 그 안의 값이 터지는 프록시다.

## 4. 수정 해설

세 조각이다.

1. **플래그 확장**: 계산식에 annotation/annotation[] 추가.\
   바로 윗줄 `hasNestedAnnotation` 검사와 동일 표현식이라 지역 변수로 1회 계산해 공유(리뷰 F4 반영).
2. **재귀 probe**: `canLoad`/`validate`가 invoke 반환값을 캡처, `Annotation`/`Annotation[]`이면 `forAnnotationType(...)`로 재귀.\
   canLoad는 boolean false가 위로 전파되고, validate는 안쪽 프레임이 만든 `IllegalStateException`이 `catch (ISE) { throw ex; }`를 통해 **재래핑 없이** 그대로 올라간다.\
   그래서 예외/로그가 실제로 깨진 가장 안쪽 annotation을 지목한다(진단 품질).
3. **종료 보장**: 재귀에 visited 집합이 없어도 안전하다 — JLS §9.6.1이 annotation 멤버 타입의 순환을 컴파일 에러로 금지하므로 값 트리는 항상 유한하다.\
   (메타-annotation 그래프는 순환 가능하지만 이 재귀는 그 축이 아니다 — [jls-annotation-rules.md](../../concepts/jls-annotation-rules/jls-annotation-rules.md).)

> **JLS(Java Language Specification)** — 자바 언어가 무엇을 허용하고 무엇을 컴파일 에러로 막는지 정한 공식 명세.\
> 예: §9.6.1이 "annotation 멤버 타입은 자기 자신을 순환 참조할 수 없다"를 컴파일 단계에서 막는다.

> **값 트리(value tree)** — annotation 인스턴스가 속성 호출로 이어져 만드는 트리. 노드는 프록시, 간선은 속성 호출 1회.\
> 예: `@Deep -> @Nested -> @Inner -> enum 상수`가 깊이 3짜리 값 트리다.

같은 입력이 수정 전후에 어떻게 갈리는지를 나란히 놓으면 이렇다.

```text
입력: @Outer -> @Inner -> (없는 enum 상수)

  수정 전                                  수정 후
  +---------------------------------+        +------------------------------+
  | 플래그(@Inner 속성) : false     |        | 플래그(@Inner 속성) : true    |
  | invoke 호출        : 0 회       |        | invoke 호출        : 1 회     |
  | 반환값             : 버림       |        | 반환값             : value 로 |
  | 재귀               : 없음       |        | 재귀 -> @Inner 에 canLoad     |
  | 예외 관측          : 없음       |        | 예외 관측 : 안쪽 프레임에서   |
  | 보고               : true     |        | 보고 : warn(@Inner) + false   |
  | isPresent()        : true       |        | isPresent()        : false    |
  | asMap()            : 오염 프록시|       | asMap()            : {}       |
  +---------------------------------+        +------------------------------+
    -> 검사가 첫 겹에서 멈춘다               -> 검사가 값 트리 끝까지 내려간다
```

바뀐 것은 판정 하나가 아니라 **검사가 도달하는 범위**다.

**의도된 blast radius**: nested 멤버 1개의 결함이 바깥 annotation 전체를 스캔에서 숨긴다.\
속성 단위 부분 숨김은 annotation 타입 계약상 표현 불가능하다(던짐=원점 회귀/null=계약 위반/기본값=조작 — [all-or-nothing 계약](../../concepts/annotation-all-or-nothing-contract/annotation-all-or-nothing-contract.md)).\
`canLoad` javadoc의 "true if all values are present"가 원래 이 의미론이다.

> **blast radius(영향 반경)** — 문제 하나가 생겼을 때 함께 영향을 받는 범위.\
> 예: 안쪽 `@Filter` 하나가 깨지면 바깥 `@ComponentScan` 전체가 스캔에서 사라진다.

**범위 밖(Case A)**: nested annotation **타입 자체**가 classpath에 없으면 `getDeclaredAnnotations()` 파싱 단계에서 `NoClassDefFoundError`가 나 probe에 도달조차 못 한다.\
probe로는 원리적으로 방어 불가, PR 본문에 한계로 명시.

## 5. 검증 — 이번엔 측정까지

검증은 단위 테스트와 실물 스모크에 더해 이번에는 성능 측정까지 세 층으로 쌓았다.

- test-first: 6 red -> fix -> 리뷰 반영 후 27/27 green + 패키지 스위트.
- 실물 스모크: 수정 후 `isPresent=false` + warn 로그가 `@Inner`(실제 문제 annotation)를 지목, `asMap()={}`.\
  Case A는 불변(한계 확인).
- **마이크로벤치**(사용자 요청 — "측정 없이 정당화 안 되면 측정하면 되잖아"): before/after jar로 canLoad 직접 호출.\
  기존 probe 무회귀(enum 25->25ns), nested 속성당 +50~70ns(추가된 리플렉션 읽기가 지배 항), 스캐너의 element 캐시가 반복 제한.\
  이 수치가 "사전 게이트 최적화는 복잡도 대비 실익 약함" 판단의 근거이자 PR 본문의 성능 서술이 됐다.

> **마이크로벤치(microbenchmark)** — 아주 작은 코드 조각 하나의 실행 시간만 반복 측정하는 성능 실험.\
> 예: `canLoad` 한 번에 25 ns가 걸린다는 식으로 나노초 단위 수치를 뽑는다.

## 6. 교훈

이 PR이 남긴 것은 결함을 찾는 법, fix 모양의 다양성, 논쟁을 끝내는 측정, red 단계의 자기검증 넷이다.

1. **리뷰의 논리를 diff 밖으로 재적용하면 다음 버그가 나온다.**\
   "빠진 대칭"을 찾은 논리는 같은 식의 다른 계열에도 물어볼 가치가 있다.
2. **같은 모양의 구멍이라도 fix의 모양은 다를 수 있다.**\
   enum[]은 1줄, nested는 재귀 — invoke가 성공하는지(폭탄의 위치가 어느 겹인지)가 갈랐다.
3. **"측정 없이 정당화 불가"는 측정하라는 뜻.**\
   추정 공방 대신 20분짜리 벤치가 성능 논쟁을 종결하고 PR 본문의 방어 논리까지 만들어 줬다.
4. **테스트가 실패하는 이유가 의도한 이유인지 red 단계에서 확인하라.**\
   Mockito 중첩 stubbing 버그로 red 6 예측이 8 실패로 나왔다 — 실패 개수만 보고 넘어갔으면 엉뚱한 테스트를 신뢰할 뻔했다.
