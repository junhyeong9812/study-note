# PR #37351 - 착수 분석: LinkedCaseInsensitiveMap.computeIfAbsent의 팬텀 키

## 0. 결론 먼저

`computeIfAbsent`가 매핑 함수를 부르기 **전에** 색인(`caseInsensitiveKeys`)에 키를 등록하기 때문에, 함수가 null을 돌려주거나 예외를 던지면 저장소(`targetMap`)에는 아무것도 없는데 색인에만 키가 남는다.\
그 상태에서 `containsKey`는 true, `size()`는 0, `get`은 null을 돌려주고, 다음 삽입은 실패한 호출의 표기로 저장된다.\
예외도 로그도 없다.

> **착수 분석(analysis)** — 코드를 고치기 전에 실파일을 읽어 결함의 위치·경로·영향 범위를 확정해 두는 문서.\
> 예: 여기서 수정 방식 두 안(사후 롤백, 계산 후 등록)을 놓고 하나를 골랐는데, 그 선택이 리뷰에서 한 번 뒤집혔다.

착수 전에 스크래치 스모크(`U2Smoke.java`)로 세 경우를 재현했다.

```text
A  null 반환 후     : size=0  containsKey("key")=true
B  이후 KEY 삽입    : 저장 키 = [Key]
C  예외 후          : size=0  containsKey=true
```

출처는 spring-core 버그헌트 라운드6 findings의 U2이고, 착수 당일(2026-09-30) upstream/main `ebef12d92cd` 기준으로 관련 PR·이슈를 재검색해 0건을 확인했다.\
대상 파일은 fork와 upstream이 바이트 동일했다.

## 1. 무대 - 하나의 Map을 두 맵으로

이 클래스는 대소문자를 무시한 조회와 원래 표기 보존을 동시에 맞추려고 맵을 두 개 든다.\
클래스 javadoc - "Preserves the original order as well as the original casing of keys, while allowing for contains, get and remove calls with any case of key"(L41-42).

> **대소문자 보존(case-preserving)** — 비교는 대소문자를 무시하되, 저장과 출력은 넣은 표기 그대로 하는 것.\
> 예: `put("Content-Type", v)` 후 `keySet()`은 `["Content-Type"]`이다.

두 맵에 쓰는 공개 메서드는 넷이고, 그중 하나만 다른 모양이다.

- **`put`**: 색인을 먼저 `put`으로 갱신하고, 표기가 바뀌었으면 저장소에서 옛 키를 지운 뒤 새 키로 저장한다.
- **`putIfAbsent`**: 색인에 먼저 `putIfAbsent`, 기존 키면 저장된 표기로 저장소에 `putIfAbsent`.
- **`remove`**: 색인에서 지우고 받은 원래 키로 저장소에서 지운다.
- **`computeIfAbsent`**: 색인에 먼저 `putIfAbsent`하고, 저장소에는 **매핑 함수가 non-null을 돌려줄 때만** 쓴다.

네 경로가 어디서 갈라지는지 세로로 보면 이렇다.

```text
   put / putIfAbsent           remove                computeIfAbsent
         |                        |                         |
   색인 쓰기                  색인에서 제거             색인 쓰기 (선등록)
         |                        |                         |
         v                        v                         v
   저장소 쓰기                저장소에서 제거           매핑 함수 실행
   (값이 이미 있다)                                   <- 실패할 수 있다
         |                        |                         |
         v                        v                         v
   두 맵 일치                 두 맵 일치             non-null: 저장소 쓰기 -> 일치
                                                     null / 예외: 저장소 그대로
                                                                  -> 색인만 남는다
```

**`computeIfAbsent`만 두 쓰기 사이에 실패할 수 있는 사용자 코드가 끼어 있다.**\
형제 메서드의 "색인 먼저" 관용구가 그 하나에서만 깨진다.

## 2. 핵심 이름표

이 파일을 처음 읽을 때 헷갈리는 지점은 "키"가 세 종류라는 것이다 - 호출자가 넘긴 키, 소문자로 바꾼 키, 색인에서 꺼낸 원래 키.\
이름표를 먼저 고정해 두면 이후 추적이 단순해진다.

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `targetMap` (`LinkedHashMap`, L57) | 저장소. 원래 표기 키 -> 값 | 함수가 실패하면 비어 있는 쪽 |
| `caseInsensitiveKeys` (`HashMap`, L59) | 색인. 소문자 키 -> 원래 키 | 선등록 때문에 **흔적이 남는 쪽** |
| `convertKey` (L337-339) | `key.toLowerCase(getLocale())` | `protected` 확장점. 서브클래스가 바꿀 수 있다 |
| `containsKey` (L157-160) | **색인만** 본다 | 팬텀을 "있다"고 답하는 표면 |
| `size` / `isEmpty` (L147-155) | **저장소만** 본다 | 팬텀이 있어도 0을 답하는 표면 |
| `get` / `getOrDefault` (L167-187) | 색인에서 원래 키 -> 저장소 조회 | 팬텀이면 null. `getOrDefault`는 기본값도 안 돌려준다 |
| `oldKey` (`computeIfAbsent` 지역) | 색인 조회 결과 = 저장된 원래 키 | 팬텀이 있으면 실패한 호출의 표기 |
| `key = oldKey` 분기 (수정 전 L231-233) | 기존 null 값이면 저장된 표기로 계산(gh-26868) | 팬텀이 있으면 표기 누출(B)의 통로 |
| 저장소의 `removeEldestEntry` 오버라이드 (L121-128) | 축출 시 색인에서도 제거 | 등록 시점이 이 훅보다 늦으면 깨진다(착수 때 못 본 것) |
| 저장소의 `containsKey` 오버라이드 (L117-120) | 색인에 위임 | `targetMap.containsKey`로는 저장 여부를 확인할 수 없다(착수 때 못 본 것) |

마지막 두 줄은 착수 분석에서 **보지 못했던** 것이다.\
둘 다 리뷰 1회차에서 드러났고, 첫째는 채택했던 수정안을 뒤집었고 둘째는 그 수정안을 사후 확인으로 살리는 길을 막았다.

> **확장점(extension point)** — 서브클래스가 오버라이드해 동작을 바꾸도록 일부러 열어 둔 메서드.\
> 예: `convertKey`와 `removeEldestEntry`는 `protected`라서 외부 서브클래스가 바꿀 수 있다.

## 3. 결함 경로 단계 추적

빈 맵에서 A 다음에 B를 부르는 시나리오다.

| 단계 | 동작 | 색인 | 저장소 | 공개 API 관측 |
|---|---|---|---|---|
| 1 | `computeIfAbsent("Key", k -> null)` - 색인 `putIfAbsent("key","Key")` | `{key->Key}` | `{}` | |
| 2 | 저장소 `computeIfAbsent` - 함수 null, 기록 안 함 | `{key->Key}` | `{}` | containsKey=true, size=0, get=null |
| 3 | `computeIfAbsent("KEY", k -> "value")` - 색인 `putIfAbsent("key","KEY")` -> 기존 값 `"Key"` | `{key->Key}` | `{}` | |
| 4 | `oldKey="Key"`, `targetMap.get("Key")` = null -> `key = oldKey` | 그대로 | 그대로 | |
| 5 | 저장소 `computeIfAbsent("Key", ...)` -> `"value"` 저장 | `{key->Key}` | `{Key=value}` | **keySet=[Key]** (호출자는 "KEY") |

계획 이해 게이트 중에 `computeIfAbsent(k -> null)`과 `put("Key", null)`의 차이를 직접 돌려 확인했다.\
이 차이가 이후 T4 테스트와 게이트 G4의 핵심이 된다.

```text
computeIfAbsent(k -> null) 후: {}          size=0  containsKey("Key")=false
put("Key", null) 후:          {Key=null}  size=1  containsKey("Key")=true
```

`put`은 null 값이어도 항목을 만들고, `computeIfAbsent`는 함수가 null이면 항목을 만들지 않는다.

## 4. 계약과 기원

**계약.**\
`Map#computeIfAbsent` javadoc - "If the mapping function returns null, no mapping is recorded. If the mapping function itself throws an (unchecked) exception, the exception is rethrown, and no mapping is recorded."\
저장소는 이 계약을 지킨다.\
깨지는 것은 저장소와 색인 사이의 불변식이다 - "색인의 값 집합 == 저장소의 키 집합".\
이 불변식은 `put`(L190-197), 축출 훅(L121-127), `remove`(L244-252)가 이미 강제하고 있으므로, 새로 세울 규칙이 아니라 한 메서드가 어긴 기존 규칙이다.

> **불변식(invariant)** — 코드가 어떤 경로로 돌든 항상 참이어야 하는 문장.\
> 예: "색인이 있다고 하는 키는 저장소에도 있다"가 이 클래스의 불변식이다.

계약을 지키는 쪽과 어기는 쪽을 나란히 놓으면 이렇다.

```text
      Map#computeIfAbsent 계약                  클래스 내부 불변식
+-----------------------------------+    +-----------------------------------+
| null / 예외 -> 매핑 기록 안 함    |    | 색인 값 집합 == 저장소 키 집합    |
+-----------------------------------+    +-----------------------------------+
| 저장소(targetMap): 지킨다         |    | put / remove / 축출 훅: 지킨다    |
| (JDK HashMap 이 처리)             |    | computeIfAbsent: 어긴다           |
+-----------------------------------+    +-----------------------------------+
         \                                         /
          +------ 선등록이 두 칸 사이를 벌린다 ------+
```

**기원.**\
`git log -L`로 이력을 확인했다.

- `b790bd1fd68`(2018-06-11, "LinkedCaseInsensitiveMap explicitly implements put/computeIfAbsent") - `computeIfAbsent`를 명시 구현으로 도입했고, 이때부터 선등록 구조였다.
- `b18cf3c873b`(2021-04-30, gh-26868, Arjen Poutsma, "Follow contract of computeIfAbsent LinkedCaseInsensitiveMap") - 기존 키가 null에 매핑된 경우 `key = oldKey`로 재계산하도록 고쳤다.\
  이 분기는 팬텀이 있을 때도 타면서, 팬텀이 남긴 표기로 새 값을 저장하게 만든다(스모크 B의 원인).
- 선등록 자체를 겨냥한 수정 이력은 없다.

즉 2018년의 선등록 결함 위에, 2021년의 정당한 수정이 "색인은 정직하다"는 전제로 분기를 하나 더 얹었고, 그 분기가 결함을 표기 누출로 넓혔다.

## 5. 발화 조건 - 왜 아무도 못 봤나

착수 리서치는 `computeIfAbsent` 호출처를 grep으로 넷 찾았다 - `StompHeaders:437·443`, `NativeMessageHeaderAccessor:250`, `MockHttpServletResponse:788`.\
전부 매핑 함수가 non-null(`new ArrayList<>`, `new HeaderValueHolder()`)이라 "실경로에서 팬텀은 사용자 코드의 null 반환·예외에서만 생긴다"고 결론 냈다.

**이 목록은 틀렸다.**\
PR을 연 뒤 문서화 워커가 짚었고 메인이 확인했다 - `StompHeaders`와 `NativeMessageHeaderAccessor`는 `LinkedMultiValueMap`을 쓴다.\
문자열 grep만 하고 수신 객체의 타입을 확인하지 않았다.\
실제 내부 경로는 `HttpHeaders`(`new LinkedCaseInsensitiveMap<>(8, Locale.ROOT)`) -> `MultiValueMapAdapter.add`/`addAll`의 `computeIfAbsent(key, k -> new ArrayList<>(...))`, 그리고 `MockHttpServletResponse:788`이다.\
둘 다 non-null을 만드므로 **결론은 그대로**다 - 프레임워크 내부 경로에서는 팬텀이 생기지 않는다.

> **전수 조사(exhaustive audit)** — 표본을 고르지 않고 해당하는 자리를 하나도 빼지 않고 전부 확인하는 것.\
> 예: 호출 지점을 문자열로 찾은 다음, 각 지점의 수신 객체가 정말 이 클래스인지까지 확인해야 전수다.

팬텀이 생기는 쪽은 이 공개 클래스를 직접 쓰면서 `computeIfAbsent`를 조회 캐시로 쓰는 사용자 코드다 - 못 찾으면 null, 조회 중 실패하면 예외.\
둘 다 `Map` 계약상 정상 결과다.

## 6. 수정안

### 6.1 착수 시점의 두 안

인터뷰에서 두 안을 놓고 사용자가 골랐다.

| 안 | 내용 | 착수 시점 판단 |
|---|---|---|
| A 사후 롤백 | 선등록은 두고, 함수가 null/예외면 try/finally로 색인에서 지운다 | 정리 코드가 늘어난다 |
| **B 계산 후 등록** | 색인은 조회만 하고, 저장소 계산이 non-null을 돌려준 뒤에만 등록 | 정리 코드가 필요 없다 - **채택** |

> **보상(compensation)** — 이미 해 버린 쓰기를 실패 시 거꾸로 되돌리는 처리.\
> 예: 선등록 후 함수가 실패하면 finally에서 색인 항목을 지우는 것이 보상이다.

B안 코드는 이랬다.

```java
String caseInsensitiveKey = convertKey(key);
String oldKey = this.caseInsensitiveKeys.get(caseInsensitiveKey);   // 조회만
if (oldKey != null) {
	V oldKeyValue = this.targetMap.get(oldKey);
	if (oldKeyValue != null) {
		return oldKeyValue;
	}
	else {
		key = oldKey;
	}
}
V value = this.targetMap.computeIfAbsent(key, mappingFunction);
if (oldKey == null && value != null) {
	this.caseInsensitiveKeys.put(caseInsensitiveKey, key);          // 성공했을 때만 등록
}
return value;
```

등록 조건 두 개는 각각 이런 경우를 거른다.

- **`oldKey == null`**: 어떤 대소문자로도 원래 없던 새 키.\
  `oldKey != null`이면 색인이 이미 저장된 키를 올바르게 가리키고 있으므로 다시 등록할 필요가 없다.\
  (B안에서는 그 분기가 `key = oldKey`로 바꿔 두므로 다시 등록해도 같은 값을 쓸 뿐이다 - 계획 게이트에서 판정 워커의 "색인이 새 표기로 덮인다"는 설명을 메인이 이렇게 정정했다.)
- **`value != null`**: 저장소에 매핑이 기록됐다는 신호.\
  null인데도 등록하면 지금 버그와 똑같이 팬텀이 생긴다.

**두 번째 조건의 전제가 틀렸다.**\
명세에는 load-bearing 가정 2로 "신규 키 경로에서 `targetMap.computeIfAbsent` 결과 non-null <=> 매핑 기록됨"이 적혀 있었다.\
리뷰 1회차가 반증했다 - `removeEldestEntry` 오버라이드가 같은 호출 안에서 방금 삽입한 항목을 축출할 수 있다.\
반환값이 non-null이어도 호출이 끝난 시점에는 이미 저장소에 없을 수 있는 것이다.

### 6.2 재합의 - 람다 래핑

리뷰 F1 뒤에 수정 구조를 다시 골랐다(명세 §11 재합의).

| 안 | 내용 | 판단 |
|---|---|---|
| **안1 람다 래핑** | 새 키 경로에서 매핑 함수를 감싸, non-null이면 람다 안에서(삽입 직전) 등록 | **채택** - 스크래치 프로토타입으로 축출·A·B·C·경우1·2 실증 |
| 안2 apply 후 put | 값을 먼저 계산하고 저장은 `put`에 맡김 | `HashMap.computeIfAbsent`의 재진입 감지(CME) 등 의미가 달라짐 |
| 안3 A안으로 회귀 | 선등록 + 롤백 | 롤백 판정에 `targetMap.containsKey`를 쓸 수 없어(색인 위임) `keySet().contains`와 try/finally까지 필요 |

안1의 형태는 "신규 키만 래핑, 기존 키 경로는 원 함수 그대로"로 명세에 고정했다.\
기존 키 경로는 HashMap이 삽입이 아니라 기존 노드 갱신을 하므로 축출 훅이 불리지 않고, 색인도 이미 맞기 때문이다.

```java
return this.targetMap.computeIfAbsent(key, k -> {
	V value = mappingFunction.apply(k);
	if (value != null) {
		this.caseInsensitiveKeys.putIfAbsent(convertedKey, k);   // 최종형 (리뷰 2·3회차 반영 후)
	}
	return value;
});
```

정당화는 세 겹이다.

1. **실패 경로에서 등록이 없다.**\
   null이면 람다의 `if`가 건너뛰고, 예외면 `apply` 줄에서 전파되어 등록 줄에 도달하지 않는다.\
   정리 코드가 필요 없다.
2. **성공 경로에서 등록이 삽입보다 앞이다.**\
   JDK는 `apply` -> 새 노드 삽입 -> `afterNodeInsertion`(축출 훅) 순서로 진행하므로, 람다 안 등록은 훅보다 앞이다.\
   훅이 색인과 저장소를 함께 치울 수 있다 - `put`과 같은 순서다.
3. **색인은 별개의 `HashMap`이다.**\
   람다 안에서 색인에 쓰는 것은 `targetMap`의 `modCount`를 바꾸지 않아 CME 검사에 걸리지 않는다.

같은 정당화를 "등록이 언제 일어나나" 한 축으로 요약하면 이렇다.

```text
  수정 전     등록 -> 함수 -> 삽입 -> 훅          실패 경로에서 흔적
  B 안        함수 -> 삽입 -> 훅 -> 등록          축출 경로에서 흔적
  안1 래핑    함수 -> 등록 -> 삽입 -> 훅          흔적 없음
                      ^
                      값이 확보된 직후, 삽입 직전
```

### 6.3 검토했으나 기각한 대안

**대안 - 저장소 키까지 정규화한다.**\
계획 게이트 중 사용자가 물었다 - "애초에 서로 동일하게 정규화하고 비교한다는 선택지는 없던거야?"\
맵을 하나로 합쳐 `소문자 -> (원래 키, 값)` 구조로 바꾸는 방법도 있지만, 이 클래스의 계약은 원래 표기 보존이다.\
HTTP 헤더 이름이나 JDBC 컬럼명처럼 출력은 원래 표기대로 해야 하는 곳에서 쓰인다.\
저장소 키까지 소문자로 바꾸면 그 계약이 깨지고, 구조를 합치는 것은 클래스를 새로 설계하는 일이라 범위 밖이다.

**대안 - B안에 사후 확인을 붙인다.**\
`if (oldKey == null && value != null && this.targetMap.containsKey(key))`처럼 호출 후 저장 여부를 확인하는 안.\
리뷰어가 제안했다가 스스로 막혔다 - `targetMap.containsKey`는 색인에 위임하도록 오버라이드돼 있어(L117-120) 저장소를 묻지 않는다.

**대안 - 새 키와 기존 null 값 경로를 한 호출로 합친다.**\
리뷰 3회차 Q5 - `targetMap.computeIfAbsent(oldKey != null ? oldKey : key, wrapper)`.\
`putIfAbsent`가 기존 색인 항목에는 no-op이라 동작은 같지만, 명세 §11에서 "기존 키 경로는 원 함수 그대로"를 명시적으로 골랐으므로 기각했다.

세 대안과 채택안이 각각 무엇을 건드리는지 나란히 두면 이렇다.

```text
  채택(안1 래핑)   : 새 키 경로의 등록 시점        -> 원인을 고친다
  저장소 정규화    : 클래스의 저장 구조            -> 표기 보존 계약이 깨진다
  B 안 + 사후 확인 : 호출 후 존재 확인             -> 확인 수단이 색인을 본다
  두 경로 병합     : 기존 키 경로까지 래핑         -> 명세가 고른 형태와 다르다
```

### 6.4 영향 범위와 검증 계획

동작이 바뀌는 경로는 "새 키에서 함수가 null이나 예외를 내는 경우" 하나뿐이고, 그 경우의 기존 동작은 팬텀이다.\
거기에 의존하는 코드는 상정하기 어렵다.\
다만 리뷰 2회차가 관측 하나를 짚었다 - 매핑 함수 **안에서** `containsKey(같은 키)`를 부르면, 수정 전에는 선등록 때문에 true, 수정 후에는 false다.\
`Map` 계약이 정의하지 않는 동작이고 내부 호출처도 없어 PR에 언급하지 않았다(Q3 기각).

검증 계획은 명세 §5로 고정했다.

- red 테스트 - null 반환 팬텀(containsKey·keySet·size), 예외 경로 팬텀, 팬텀 표기 누출 - 수정 전 FAIL 실측 후 수정 후 PASS.
- 기존 동작 가드 - 기존 `computeIfAbsent` 테스트 그대로 green.
- `:spring-core:test --tests LinkedCaseInsensitiveMapTests` + `:spring-core:test` 전체 + checkstyle.
- 스모크 재실행(수정 후 A·B·C 정상).

재합의 뒤 blind 테스트 워커(구현 diff 미열람, 명세만)와 즉시 축출 테스트가 더해졌다.

## 7. 착수 시점의 열린 결정과 그 해소

> **load-bearing 가정** — 그것이 참이어야 계획 전체가 성립하는, 아직 확인되지 않은 전제.\
> 예: "반환값이 non-null이면 저장됐다"가 거짓이면 반환값을 근거로 한 등록이 무너진다.

**가정 1 - 팬텀 키 외에 색인 선등록에 의존하는 동작이 없다.**\
예를 들어 매핑 함수 안에서 같은 맵을 재진입 조회하는 경우 - HashMap은 재진입 수정 시 CME라 계약상 비지원.\
task 1에서 호출처 grep으로 확인했고 재진입하는 호출처는 없었다.\
다만 리뷰 1회차 Opus가 한 가지를 덧붙였다 - "Spec assumption 1 missed this in-class path; the caller grep only covered external callers."\
클래스 **안의** 경로(축출 훅)는 호출처 grep에 걸리지 않는다.\
또 앞서 적은 대로 그 호출처 grep 자체가 수신 타입을 확인하지 않아 목록이 틀려 있었다.

**가정 2 - 신규 키 경로에서 `targetMap.computeIfAbsent` 결과 non-null <=> 매핑 기록됨.**\
**반증됐다(리뷰 F1).**\
서브클래스 `removeEldestEntry`가 방금 삽입한 항목을 같은 호출 안에서 축출할 수 있다.\
또한 `targetMap.containsKey`는 색인 위임 오버라이드(L117-120)라 사후 확인 수단이 아니다.\
명세에는 이 가정을 취소선으로 남기고 반증 사유를 덧붙였다.

두 가정의 운명을 나란히 두면 이렇다.

```text
        가정 1: 선등록에 기대는 다른 동작 없음     가정 2: non-null <=> 기록됨
+-----------------------------------------+   +-----------------------------------+
| 확인 방법: 호출처 grep                  |   | 확인 방법: (착수 시 확인 안 함)   |
+-----------------------------------------+   +-----------------------------------+
| 결과: 외부 호출처에는 없음              |   | 결과: 반증 (리뷰 F1)              |
| 한계: 클래스 안의 축출 훅은 grep 밖     |   | 원인: 축출 훅이 같은 호출 안에서  |
|       호출처 목록 자체도 타입 미확인    |   |       방금 넣은 항목을 지운다     |
+-----------------------------------------+   +-----------------------------------+
```

**stakes.**\
최초 판정은 중간이었다 - HttpHeaders·JDBC 컬럼 맵 등 production 사용처가 많은 공용 유틸(blast radius)이지만, 변경은 메서드 1개로 국소적이고 복구가 쉽다.\
리뷰 중 새 경계(축출 훅)가 나와 높음으로 재합의했다.\
설계 선검증은 생략했다 - 동작 불변식(색인 값 집합 == 저장소 키)을 기존 코드가 이미 강제하고 있었기 때문이다(`put` L190-197, 축출 훅 L121-127, `remove` L244-252).

## 8. 범위 밖

> **범위 밖(out of scope)** — 눈에 띄었지만 이번 변경에서 일부러 손대지 않기로 정한 것.\
> 예: 같은 클래스의 `putIfAbsent`도 선등록을 하지만, 실패 단계가 없어 팬텀을 만들지 않으므로 손대지 않는다.

- **형제 메서드(`put`·`putIfAbsent`·`remove`) 리팩터링** - 명세 §4의 금지영역.\
  `putIfAbsent`는 선등록을 하지만 값이 이미 주어져 저장소 쓰기가 항상 일어나므로 팬텀이 없다.
- **사용처(spring-web 등) 변경** - 금지영역.
- **`computeIfAbsent(key, null)`이 NPE를 던지지 않는 것** - 리뷰 3회차 codex의 계약 밖 관찰.\
  diff 이전부터의 동작이라 범위 밖.
- **다른 키로의 재진입 수정이 남기는 팬텀** - 수정 전과 같은 결과이고 계약 위반 경로라 기록만.
- **PR 대상** - main으로 열었고 백포트는 메인테이너 판단에 맡겼다.\
  결과적으로 메인테이너가 7.0.x에 머지하고 main으로 올렸다(7.0.10).

> **백포트(backport)** — 새 버전에서 고친 것을 옛 버전 브랜치에도 옮겨 넣는 일.\
> 예: main을 대상으로 연 PR을 메인테이너가 유지보수 브랜치 7.0.x에 머지한 뒤 main으로 올렸다.

## 출처

착수 시점(2026-09-30)의 명세(`requirement-spec.md` §0-11)와 작업 log를 학습용으로 다듬은 것이다. 기준
upstream/main `ebef12d92cd`. 본문의 L 좌표는 머지 커밋 `1b4955e49f0` 기준이며, "수정 전"이라고 적은 좌표는
그 부모 `06c597ed6fa` 기준이다(`computeIfAbsent` 수정 전 L224-236). 호출처 정정(5절)은 PR 게시 후
문서화 워커의 지적을 메인이 실파일로 확인한 것이다.
