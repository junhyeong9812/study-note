# PR #37351 - Avoid phantom keys in LinkedCaseInsensitiveMap.computeIfAbsent

## 0. 정향

이 문서는 `spring-core`의 `LinkedCaseInsensitiveMap.computeIfAbsent`가 **값을 만들지 못했는데도 키를 "있다"고 답하게 되는** 결함의 해설이다.\
결함의 정체는 "두 자료구조에 쓰는 순서" 하나이고, 수정도 그 순서를 옮기는 것이다.\
그런데 순서를 어디로 옮기느냐가 한 번 틀렸다 - 처음 고친 자리는 너무 늦어서, 리뷰가 그 수정 자체가 새 팬텀을 만든다는 것을 찾아냈다.

> **팬텀 키(phantom key)** — 존재 여부를 물으면 "있다"고 답하는데, 실제로 꺼내려 하면 아무것도 없는 키.\
> 예: `containsKey("key")`는 true인데 `size()`는 0이고 `get("key")`는 null이다.

> **색인(index)** — 원본 데이터를 빨리 찾으려고 따로 들고 있는 보조 자료구조.\
> 예: 이 맵은 소문자 키 -> 원래 키의 대응표를 따로 들고, 대소문자를 무시한 조회를 그 표로 처리한다.

다 읽으면 다음 셋을 설명할 수 있어야 한다.

- "왜 값이 없는데 키가 남는가"
- "왜 '계산이 끝난 뒤 등록'은 정답이 아니었는가"
- "왜 '값을 확보한 직후, 삽입 직전'이 유일하게 맞는 등록 시점인가"

상태: **머지 완료**(2026-09-30 18:48 KST 제출, 같은 날 19:47 KST sbrannen 머지 - upstream 커밋 `1b4955e49f0`, 7.0.x+main, 마일스톤 7.0.10).\
PR은 `main`을 대상으로 열었고, 메인테이너가 `7.0.x`에 머지한 뒤 `main`으로 올렸다("This has been merged into `7.0.x` and `main`.").\
감사 답글은 2026-10-08에 게시했다.

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md) - [착수 분석](analysis.md) -
[이해 게이트 기록](gates.md).

## 1. 배경 - 대소문자를 잊기 위해 맵을 두 개 드는 클래스

`LinkedCaseInsensitiveMap`은 키를 대소문자 구분 없이 다루면서도, 넣은 표기 그대로를 보존하는 맵이다.\
클래스 javadoc이 그 계약을 한 줄로 적는다 - "Preserves the original order as well as the original casing of keys, while allowing for contains, get and remove calls with any case of key"(LinkedCaseInsensitiveMap.java:41-42).

> **대소문자 보존(case-preserving)** — 비교는 대소문자를 무시하되, 저장과 출력은 넣은 표기 그대로 하는 것.\
> 예: `put("Content-Type", v)` 후 `get("content-type")`은 v를 돌려주고, `keySet()`은 `["Content-Type"]`을 보여 준다.

두 요구(무시하며 찾기, 보존하며 저장)를 동시에 맞추려고 이 클래스는 맵을 두 개 든다.

| 이름 | 무엇인가 | 누가 읽나 |
|---|---|---|
| `targetMap` (`LinkedHashMap`, :57) | 저장소. **원래 표기의 키** -> 값 | `size()`(:148-150), `isEmpty()`(:153-155), `keySet()`, `get`의 두 번째 단계 |
| `caseInsensitiveKeys` (`HashMap`, :59) | 색인. **소문자 키** -> 저장소의 원래 키 | `containsKey()`(:158-160), `get`의 첫 번째 단계 |

두 맵은 같은 사실을 두 방식으로 적은 것이고, 클래스 전체가 다음 불변식 위에 서 있다.

> **불변식(invariant)** — 코드가 어떤 경로로 돌든 항상 참이어야 하는 문장.\
> 예: "색인의 값 집합 == 저장소의 키 집합"이 이 클래스의 불변식이다.

작업 명세는 이 불변식을 그대로 받아 적었다 - "`caseInsensitiveKeys`의 값 집합 == `targetMap.keySet()` (containsKey/size/keySet 일치)".\
`put`(:190-198), `remove`(:244-252), 그리고 축출 훅(:121-127)이 이미 이 불변식을 지키고 있다.\
즉 새로 만든 규칙이 아니라 **기존 코드가 강제하던 규칙을 `computeIfAbsent` 한 곳이 어기고 있었던** 결함이다.

두 맵이 어디서 갈라지고 누가 무엇을 읽는지 세로로 그리면 이렇다.

```text
              map.xxx("Key", ...)
                      |
          +-----------+-----------+
          |                       |
          v                       v
  caseInsensitiveKeys        targetMap
  (색인)                     (저장소)
  "key" -> "Key"             "Key" -> value
          |                       |
          v                       v
  containsKey() 가 읽는다    size() / isEmpty() / keySet() 가 읽는다
  get() 1 단계               get() 2 단계
          |                       |
          +-----------+-----------+
                      |
                      v
        둘이 맞는지는 각 쓰기 경로가 지켜야 한다
        (put / remove / 축출 훅은 지킨다)
```

**색인이 거짓말을 하면 `containsKey`가 거짓말을 믿는다** - 이 한 줄이 이 결함의 전체 구조다.

## 2. 수정 전 동작 - 등록이 먼저, 계산이 나중

수정 전 `computeIfAbsent`는 이렇게 생겼다.

```java
public @Nullable V computeIfAbsent(String key, Function<? super String, ? extends V> mappingFunction) {
	String oldKey = this.caseInsensitiveKeys.putIfAbsent(convertKey(key), key);   // (1) 색인에 먼저 등록
	if (oldKey != null) {
		V oldKeyValue = this.targetMap.get(oldKey);
		if (oldKeyValue != null) {
			return oldKeyValue;
		}
		else {
			key = oldKey;                                                         // (2) gh-26868 분기
		}
	}
	return this.targetMap.computeIfAbsent(key, mappingFunction);                  // (3) 여기서 함수 실행
}
```
(수정 전 LinkedCaseInsensitiveMap.java:224-236)

(1)은 **함수를 부르기도 전에** 색인에 무조건 쓴다.\
(3)은 저장소에 쓰는데, 그건 함수가 non-null 값을 돌려줄 때만이다.\
`Map#computeIfAbsent`의 계약이 그렇게 정해 두었기 때문이다 - "If the mapping function returns null, no mapping is recorded. If the mapping function itself throws an (unchecked) exception, the exception is rethrown, and no mapping is recorded."

> **매핑 함수(mapping function)** — `computeIfAbsent`가 키가 없을 때만 불러서 저장할 값을 만들게 하는 함수.\
> 예: `computeIfAbsent(key, k -> new ArrayList<>(1))`에서 `k -> new ArrayList<>(1)`이 매핑 함수다.

두 맵에 쓰는 조건을 고정 축으로 나란히 놓으면 비대칭이 바로 보인다.

| | 색인 쓰기 (1) | 저장소 쓰기 (3) |
|---|---|---|
| 언제 | 함수 호출 **전** | 함수 호출 **후** |
| 조건 | 무조건(새 키면) | 함수가 non-null 반환 |
| 함수가 null 반환 | 이미 써졌다 | 안 써진다 |
| 함수가 예외 | 이미 써졌다 | 안 써진다 |

**실패할 수 있는 쪽(함수)을 나중에 하고, 실패할 수 없는 쪽(색인 등록)을 먼저 했다.**\
그래서 함수가 실패하면 성공한 쪽의 흔적만 남는다.

> **선등록(pre-registration)** — 결과가 확정되기 전에 참조나 표식을 먼저 기록해 두는 것.\
> 예: 값을 만들기 전에 색인에 "key -> Key"를 먼저 써 두면, 값 생성이 실패했을 때 색인만 남는다.

(2)의 분기도 기억해 둘 필요가 있다.\
2021년 커밋 `b18cf3c873b`(gh-26868, "Follow contract of computeIfAbsent LinkedCaseInsensitiveMap")가 넣은 것으로, "기존 키가 null 값에 매핑돼 있으면 저장된 표기로 다시 계산한다"는 정당한 동작이다.\
그런데 이 분기는 진짜 기존 키와 팬텀 키를 구분하지 못한다.\
팬텀이 남아 있으면 이 분기를 타서, 실패한 호출이 남긴 표기로 다음 값을 저장한다(3절의 B).

## 3. 문제 - 세 가지 팬텀

### A - null 반환이 남기는 팬텀

빈 맵에서 `map.computeIfAbsent("Key", k -> null)` 한 번을 따라가면 이렇다.

| 단계 | 동작 | 색인 | 저장소 |
|---|---|---|---|
| 0 | 호출 전 | `{}` | `{}` |
| 1 | `caseInsensitiveKeys.putIfAbsent("key", "Key")` -> null 반환 | `{"key" -> "Key"}` | `{}` |
| 2 | `oldKey == null`이라 분기 건너뜀 | 그대로 | 그대로 |
| 3 | `targetMap.computeIfAbsent("Key", k -> null)` -> 함수가 null -> 기록 안 함 | `{"key" -> "Key"}` | **`{}`** |

끝난 상태에서 공개 API가 돌려주는 값은 서로 모순된다.

```text
containsKey("key") = true     <- 색인을 본다
size()             = 0        <- 저장소를 본다
keySet()           = []       <- 저장소를 본다
get("key")         = null     <- 색인에서 "Key" 를 찾고, 저장소에서 "Key" 를 못 찾는다
```

작업 시작 직후 스크래치 스모크(`U2Smoke.java`)가 이 상태를 실측했다 - "A 팬텀(size=0·containsKey=true)".\
문서화 단계의 추가 프로브는 같은 상태에서 `getOrDefault("key", "N")`이 기본값 `"N"`이 아니라 **null**을 돌려준다는 것도 확인했다.\
코드로 보면 당연하다 - `getOrDefault`(:179-187)는 색인에서 `"Key"`를 찾으면 기본값 분기로 가지 않고 `targetMap.get("Key")`의 null을 그대로 반환한다.

### B - 팬텀의 표기가 다음 삽입에 샌다

A 다음에 `map.computeIfAbsent("KEY", k -> "value")`를 부르면 저장은 정상으로 된다.\
문제는 **어떤 표기로** 저장되느냐다.

```text
putIfAbsent("key", "KEY")   -> 이미 "key" 가 있음 -> 기존 값 "Key" 반환
oldKey = "Key"              -> 분기 진입
targetMap.get("Key")        -> null (저장소는 비어 있다)
key = oldKey                -> "KEY" 가 "Key" 로 바뀐다   <- gh-26868 분기
targetMap.computeIfAbsent("Key", k -> "value")
결과: keySet() = ["Key"]    (호출자가 넘긴 것은 "KEY")
```

실패한 첫 호출의 표기가 성공한 두 번째 호출을 오염시킨다.\
스모크 실측 - "B casing 누출("Key")".\
수정 후 코드는 두 번째 호출의 `"KEY"`를 저장한다.

### C - 예외가 남기는 팬텀

매핑 함수가 예외를 던져도 A와 같은 상태가 된다.\
(1)의 등록은 이미 끝났고, 예외는 (3)에서 전파되므로 되돌리는 코드가 없다.\
스모크 실측 - "C 예외 팬텀 재현".

세 경우를 한 장에 놓으면 공통 원인이 드러난다.

```text
              (1) 색인 선등록  -- 항상 실행된다
                     |
                     v
              (3) 매핑 함수 실행
                     |
     +---------------+----------------+
     |               |                |
     v               v                v
  non-null         null             예외
  저장소 기록       기록 안 함        기록 안 함, 전파
     |               |                |
     v               v                v
  두 맵 일치       팬텀 (A)          팬텀 (C)
                     |
                     v
              다음 삽입이 팬텀의 표기를 쓴다 (B)
```

> **무음 실패(silent failure)** — 실패했는데도 예외·로그 같은 신호가 남지 않아 정상처럼 보이는 실패.\
> 예: 팬텀은 아무 예외 없이 남고, 나중에 `containsKey`와 `get`이 엇갈린 답을 할 때 비로소 드러난다.

### 왜 아무도 못 봤나

프레임워크 내부에서 이 메서드에 넘어가는 매핑 함수는 전부 **non-null을 만드는 생성자 람다**다.\
그래서 프레임워크 경로만으로는 null 반환도 예외도 일어나지 않는다.

여기서 기록 하나를 정정해 둔다.\
작업 명세와 PR 본문은 내부 호출처를 `StompHeaders`, `NativeMessageHeaderAccessor`, `MockHttpServletResponse`로 적었다.\
그런데 PR을 연 뒤 문서화 단계에서 확인하니 앞의 둘은 `LinkedCaseInsensitiveMap`이 아니라 `LinkedMultiValueMap`을 쓴다(`StompHeaders`의 `new LinkedMultiValueMap<>(3)`, StompHeaders.java:116).\
`computeIfAbsent` 문자열만으로 grep하고 실제 맵 타입을 확인하지 않은 탓이다.\
실제 내부 경로는 이렇다.

| 경로 | 맵 생성 | `computeIfAbsent` 호출 | 매핑 함수 |
|---|---|---|---|
| `HttpHeaders` | `new LinkedCaseInsensitiveMap<>(8, Locale.ROOT)` (HttpHeaders.java:445) | `MultiValueMapAdapter.add`/`addAll` (MultiValueMapAdapter.java:66, :72) | `k -> new ArrayList<>(1)` 등 |
| `MockHttpServletResponse` | `new LinkedCaseInsensitiveMap<>()` (MockHttpServletResponse.java:121) | `doAddHeaderValue` (:788) | `key -> new HeaderValueHolder()` |

결론("내부 경로에서는 팬텀이 생기지 않는다")은 그대로지만, **`HttpHeaders`라는 훨씬 흔한 경로가 이 메서드를 쓴다**는 점이 빠져 있었다.\
이 정정은 PR 본문 게시 뒤에 나왔고, 게시된 PR 본문의 Problem 마지막 문단은 정정 전 문구 그대로 남아 있다(커밋 메시지에는 호출처 목록이 없다).

팬텀이 실제로 생기는 쪽은 이 공개 클래스를 직접 쓰면서 `computeIfAbsent`를 **조회 캐시**로 쓰는 사용자 코드다.\
게이트 중 설명에 쓴 예시가 그 형태다.

```java
Column col = columnCache.computeIfAbsent(name, k -> lookupColumn(k));   // 못 찾으면 null
```

`lookupColumn`이 못 찾아 null을 주는 것은 정상 결과이고, `Map` 계약상 "기록하지 않음"이 맞다 - 다음에 다시 찾아볼 수 있어야 하기 때문이다.\
DB 조회나 파싱 중 예외가 나는 것도 흔한 일이다.\
그 두 경우에 이 클래스만 흔적을 남겼다.

## 4. 수정 해설 - 람다 안에서 등록한다

최종 코드는 이렇다.

```java
public @Nullable V computeIfAbsent(String key, Function<? super String, ? extends V> mappingFunction) {
	String convertedKey = convertKey(key);
	String oldKey = this.caseInsensitiveKeys.get(convertedKey);        // 조회만 한다
	if (oldKey != null) {                                              // 기존 키 경로
		V oldKeyValue = this.targetMap.get(oldKey);
		if (oldKeyValue != null) {
			return oldKeyValue;
		}
		return this.targetMap.computeIfAbsent(oldKey, mappingFunction);   // 저장된 표기로 계산
	}
	return this.targetMap.computeIfAbsent(key, k -> {                 // 새 키 경로
		V value = mappingFunction.apply(k);
		if (value != null) {
			this.caseInsensitiveKeys.putIfAbsent(convertedKey, k);     // 값을 확보한 직후, 삽입 직전
		}
		return value;
	});
}
```
(LinkedCaseInsensitiveMap.java:223-241, 머지 커밋 `1b4955e49f0` 기준. 주석은 설명용)

바뀐 것은 셋이다.

1. **첫 줄이 `putIfAbsent`에서 `get`으로.**\
   이제 함수를 부르기 전에는 색인에 아무것도 쓰지 않는다.
2. **기존 키 경로는 동작 그대로.**\
   non-null 값이면 그대로 반환하고, null 값이면 저장된 표기 `oldKey`로 계산한다.\
   `key = oldKey` 재대입을 `computeIfAbsent(oldKey, ...)` 직접 호출로 바꿨을 뿐이고, 원래 매핑 함수를 감싸지 않고 넘긴다.
3. **새 키 경로는 매핑 함수를 감싼 람다를 넘긴다.**\
   감싼 람다 안에서 사용자 함수가 non-null을 돌려준 그 순간에 색인에 등록한다.

같은 입력 셋을 수정 전후에 넣으면 이렇다.

```text
                 수정 전                              수정 후
+--------------------------------+   +--------------------------------+
| null 반환                      |   | null 반환                      |
|   색인 {key->Key} / 저장소 {}  |   |   람다 안 if 가 등록을 건너뜀  |
|   -> 팬텀                      |   |   HashMap 도 삽입하지 않음     |
|                                |   |   색인 {} / 저장소 {}          |
+--------------------------------+   +--------------------------------+
| 예외                           |   | 예외                           |
|   색인 {key->Key} / 저장소 {}  |   |   apply 줄에서 전파            |
|   -> 팬텀                      |   |   등록 줄에 도달하지 않음      |
|                                |   |   색인 {} / 저장소 {}          |
+--------------------------------+   +--------------------------------+
| 이후 "KEY" 로 삽입             |   | 이후 "KEY" 로 삽입             |
|   keySet = [Key]  (누출)       |   |   keySet = [KEY]               |
+--------------------------------+   +--------------------------------+
```

### 왜 "계산이 끝난 뒤 등록"이 아닌가

처음 고친 형태(작업 기록의 B안)는 더 단순했다.

```java
V value = this.targetMap.computeIfAbsent(key, mappingFunction);
if (oldKey == null && value != null) {
	this.caseInsensitiveKeys.put(caseInsensitiveKey, key);   // 호출이 끝난 뒤 등록
}
return value;
```

A·B·C는 전부 막는다.\
그런데 리뷰어 둘(Opus 워커와 codex)이 **서로 독립적으로 같은 결함**을 찾았다(6절 F1).\
`removeEldestEntry`를 오버라이드해 방금 넣은 항목을 곧바로 축출하는 서브클래스에서는, 이 수정이 **새 팬텀을 만든다**.

> **축출 훅(eviction hook)** — 삽입 직후 "가장 오래된 항목을 지울까"를 묻는, 서브클래스가 오버라이드하는 자리.\
> 예: `LinkedHashMap.removeEldestEntry`가 true를 돌려주면 삽입 직후에 가장 오래된 항목이 제거된다.

원인은 JDK의 `HashMap.computeIfAbsent`가 **한 번의 호출 안에서** 하는 일의 순서다.\
JDK 25.0.1 소스로 확인한 순서는 이렇다(발췌).

```java
int mc = modCount;
V v = mappingFunction.apply(key);                          // (1) 함수 실행
if (mc != modCount) { throw new ConcurrentModificationException(); }
if (v == null) {
	return null;                                           //     null 이면 아무것도 안 하고 끝
} else if (old != null) {
	old.value = v;                                         //     값이 null 이던 기존 노드는 값만 갱신
	afterNodeAccess(old);
	return v;
}
...
tab[i] = newNode(hash, key, v, first);                     // (2) 새 노드 삽입
...
afterNodeInsertion(true);                                  // (3) removeEldestEntry 호출
return v;
```
(JDK 25.0.1 `java/util/HashMap.java:1228-1249`, `LinkedHashMap.afterNodeInsertion`은 :321-327)

그리고 이 클래스의 저장소는 그 (3)에 훅을 걸어 두었다.

```java
@Override
protected boolean removeEldestEntry(Map.Entry<String, V> eldest) {
	boolean doRemove = LinkedCaseInsensitiveMap.this.removeEldestEntry(eldest);
	if (doRemove) {
		removeCaseInsensitiveKey(eldest.getKey());   // 저장소에서 지울 항목을 색인에서도 지운다
	}
	return doRemove;
}
```
(LinkedCaseInsensitiveMap.java:121-128)

이 훅은 "저장소와 색인을 함께 치운다"고 설계돼 있다.\
문제는 함께 치우려면 **치울 때 색인에 이미 항목이 있어야** 한다는 것이다.\
등록 시점 셋을 같은 타임라인에 올리면 답이 한 칸으로 좁혀진다.

```text
  targetMap.computeIfAbsent(key, f) 한 번의 호출
  +--------------------------------------------------------------+
  |  (1) f 실행        (2) 저장소 삽입        (3) 축출 훅 실행   |
  +--------------------------------------------------------------+

  [수정 전] 선등록 ............ (1) 보다 앞
            -> 훅이 함께 지운다. 단 f 가 null / 예외면 팬텀

  [최종]    람다 안 등록 ....... (1) 과 (2) 사이, f 가 non-null 일 때만
            -> 훅이 함께 지운다. f 가 null / 예외면 등록 자체가 없다

  [B 안]    호출 후 등록 ....... (3) 보다 뒤
            -> 훅이 지울 때 색인이 비어 있었다
            -> 이미 축출된 키를 다시 등록 -> 새 팬텀
```

B안에서 축출 서브클래스를 따라가면 이렇다.

| 순서 | 무슨 일 | 색인 | 저장소 |
|---|---|---|---|
| (1) | 함수 실행 -> "value" | `{}` | `{}` |
| (2) | 삽입 | `{}` | `{"Key"="value"}` |
| (3) | 훅: 색인에서 "key" 지우기 시도 -> **지울 것 없음**, 저장소에서는 제거 | `{}` | `{}` |
| 호출 반환 후 | `value != null`이라 등록 | `{"key" -> "Key"}` | `{}` |

메인이 재현한 결과(`Evict.java`) - "computeIfAbsent size=0·containsKey=true(신규 팬텀), put은 정상".\
수정 전 코드는 오히려 이 경우에 **맞았다** - 선등록이 (1) 앞에 있으니 (3)의 훅이 정상적으로 지웠다.\
즉 B안은 A·B·C를 고치면서 **수정 전에 없던 결함을 만든 회귀**였다.

> **회귀(regression)** — 수정 전에는 맞던 동작이 수정 때문에 틀리게 되는 것.\
> 예: 즉시 축출 서브클래스에서 수정 전 코드는 정상이었는데, 계산 후 등록으로 바꾸자 팬텀이 생겼다.

정답은 그래서 **(1)과 (2) 사이**, 즉 "값을 확보한 직후, 삽입 직전"이다.\
그 자리에 끼어들 수 있는 방법이 매핑 함수를 감싸는 것이다.

- 함수가 null이면 감싼 람다의 `if`가 등록을 건너뛰고, HashMap도 (2)를 하지 않는다.
- 함수가 예외면 `apply` 줄에서 전파되어 등록 줄에 도달하지 않는다.
- 함수가 non-null이면 (2)보다 먼저 등록되므로 (3)의 훅이 함께 지울 수 있다 - `put`이 하는 것과 같은 순서다.

같은 서브클래스를 최종 코드로 따라가면 이렇다.

| 순서 | 무슨 일 | 색인 | 저장소 |
|---|---|---|---|
| (1) 사용자 함수 | -> "value" | `{}` | `{}` |
| (1) 람다 안 등록 | `value != null` | `{"key" -> "Key"}` | `{}` |
| (2) | 삽입 | `{"key" -> "Key"}` | `{"Key"="value"}` |
| (3) | 훅: 색인에서 "key" **지움**, 저장소에서도 제거 | `{}` | `{}` |

색인은 `targetMap`과 별개의 `HashMap`이므로, 람다 안에서 색인에 쓰는 것은 `targetMap`의 `modCount`를 건드리지 않고 CME 검사에 걸리지 않는다(1회차 Opus 리뷰의 설명).

### 왜 사후 확인으로 고칠 수 없었나

B안을 살리는 가장 쉬운 생각은 "호출 후에 저장소에 실제로 들어 있는지 확인하고 등록한다"이다.\
리뷰어도 처음 그렇게 제안했다가 스스로 막혔고, 메인도 같은 함정을 재확인했다.\
저장소 `targetMap`의 `containsKey`는 **색인에 위임하도록 오버라이드**돼 있다.

```java
@Override
public boolean containsKey(Object key) {
	return LinkedCaseInsensitiveMap.this.containsKey(key);   // 저장소가 아니라 색인을 본다
}
```
(LinkedCaseInsensitiveMap.java:117-120)

이 오버라이드는 2017년 커밋 `50e5a65b2d7`("LinkedCaseInsensitiveMap provides case-insensitive keySet again")에서 들어왔다.\
그 결과 `targetMap.containsKey(key)`는 "저장소에 있나"가 아니라 "색인에 있나"를 묻는 질문이 됐다.\
사후 확인 수단으로는 쓸 수 없다.

### 왜 `put`이 아니라 `putIfAbsent`인가

람다 안의 등록은 처음에 `put`이었다가 리뷰 2회차(F3)에서 `putIfAbsent`로 바뀌었다.\
정상 경로에서는 둘이 똑같다 - 새 키 경로에 들어왔다는 것은 메서드 첫머리에서 `oldKey == null`을 확인했다는 뜻이고, 함수가 맵을 건드리지 않는 한 람다에 도착했을 때도 색인에 그 키는 없다.

차이는 **매핑 함수가 같은 맵을 재진입 수정**하는, 계약상 금지된 경우에만 생긴다.

> **재진입(reentrancy)** — 어떤 메서드가 실행 중인 동안 같은 객체의 메서드가 다시 호출되는 것.\
> 예: `map.computeIfAbsent("Key", k -> { map.put("KEY", "x"); return "v"; })`처럼 매핑 함수 안에서 같은 맵을 고치는 것.

| 시점 | 등록이 `put`일 때 색인 | 등록이 `putIfAbsent`일 때 색인 | 저장소 |
|---|---|---|---|
| 람다 안 `map.put("KEY", "x")` 직후 | `{"key" -> "KEY"}` | `{"key" -> "KEY"}` | `{"KEY"="x"}` |
| 람다 안 등록 직후 | `{"key" -> "Key"}` **덮어씀** | `{"key" -> "KEY"}` 그대로 | `{"KEY"="x"}` |
| HashMap이 CME를 던짐 | - | - | `"Key"="v"`는 저장 안 됨 |

`put`이면 색인이 저장소에 없는 `"Key"`를 가리켜 `get("key")`가 null이 되고, `remove` 후에도 `"KEY"=x`가 아무도 가리키지 않는 고아로 남는다.\
`putIfAbsent`면 두 맵이 일치하고, 수정 전 코드와 같은 결과다.\
메인 재현(`Reentrant.java`) - "put 사용: target={KEY=x} get(key)=null remove 후 size=1 / putIfAbsent 사용: target={KEY=x} get(key)=x remove 후 size=0".

> **CME(ConcurrentModificationException)** — 계산이나 순회 도중 컬렉션이 구조적으로 바뀐 것을 감지했을 때 던지는 예외.\
> 예: JDK `HashMap.computeIfAbsent`는 함수 실행 전후의 `modCount`를 비교해 다르면 이 예외를 던진다.

### 기존 키 경로는 왜 감싸지 않았나

기존 키가 null 값을 갖고 있는 경로(:232)는 원래 함수를 그대로 넘긴다.\
이 경로에서는 HashMap이 새 노드를 삽입하지 않고 기존 노드의 값만 바꾸므로(`old.value = v; afterNodeAccess(old)`), 축출 훅이 불리지 않는다.\
함수가 null을 돌려주면 HashMap은 기존 `"Key"=null` 노드를 지우지 않고 그대로 둔다.\
색인도 이미 `oldKey`를 가리키고 있어 등록할 것이 없다.\
리뷰 3회차가 "두 경로를 한 호출로 합칠 수 있다"(Q5)고 했지만, 명세 §11에서 "신규 키만 래핑, 기존 키 경로는 원 함수 그대로"로 명시적으로 고른 형태라 유지했다.

## 5. 검증

테스트를 먼저 쓰고 red를 확인한 뒤 fix했다.\
`LinkedCaseInsensitiveMapTests`에 테스트 5건을 추가하고 기존 테스트 1건에 단언 1줄을 더했다(2파일, +56/-5).

> **red(레드)** — 고치기 전에 새 테스트를 돌려 일부러 실패를 확인하는 단계.\
> 예: 여기서 실패하지 않으면 그 테스트는 이 결함을 겨냥하지 못한 것이다.

| 항목 | 수정 전 | B안 | 최종 |
|---|---|---|---|
| red 3건(A·B·C) | **21 tests, 3 failed** | green | green |
| 즉시 축출 테스트 | green(수정 전은 맞았다) | **red** | green |
| blind 테스트 26건(spec만 보고 설계) | 16 fail | **1 fail**(즉시 축출) | **26/26** |
| `spring-core` 전체 | - | 5260 tests, 0 failures | **5262 tests, 0 failures** |
| 사용처 모듈 | - | - | web 88 · messaging 153 · test 80 · jdbc 1026, 실패 0 |
| checkstyle Main/Test | - | 통과 | 통과 |
| 스모크 재실행 | A·B·C 재현 | A/B/C 정상 | U2Smoke·Evict·Reentrant·Trace 정상 |

**blind 테스트 워커의 결과가 이 검증의 핵심 증거다.**\
구현 diff를 보지 않고 명세(§1-5)와 upstream 원본만 읽은 워커가 26건을 설계했는데, 그중 `computeIfAbsentWhenNewEntryIsImmediatelyEvicted`가 B안에서만 실패했다.\
리뷰어 둘이 코드를 읽고 찾은 F1을, 구현을 전혀 보지 않은 테스트 설계가 독립적으로 다시 찾은 셈이다.

> **blind 테스트(blind test)** — 구현을 보지 않고 명세만으로 설계한 테스트.\
> 예: 구현자가 생각하지 못한 경계를, 구현을 모르는 쪽이 계약만 보고 찾아낼 수 있다.

stakes는 처음 **중간**으로 판정했다(production 사용처가 많은 공용 유틸이지만 변경은 메서드 하나로 국소적이고 복구가 쉽다).\
리뷰 1패스에서 F1(축출 훅이라는 새 경계)이 나오자 "리뷰 중 새 경계"라는 승격 트리거에 걸려 **높음**으로 재합의했다.\
그래서 리뷰가 듀얼 1패스에서 **듀얼 리뷰 루프(최대 3회, 1패스를 1회차로 인정)**로 바뀌었고, blind 테스트 워커가 추가됐다.\
설계 선검증은 생략했다 - 동작 불변식(색인 값 집합 == 저장소 키)을 기존 코드가 이미 강제하고 있었기 때문이다(`put` :190-197, 축출 훅 :121-127, `remove` :244-252).

> **stakes 승격** — 진행 중에 예상보다 위험이 크다는 신호가 나오면 검증 강도를 한 단계 올리는 것.\
> 예: 리뷰에서 처음 보는 경계(축출 훅)가 나오자 리뷰를 1패스에서 최대 3회 루프로 바꿨다.

테스트 자체의 해설은 [tests.md](tests.md), 축출 훅과 재진입의 구조는 [structure.md](structure.md).

## 6. 리뷰 지적에서 수정까지 - 순차 타임라인

이 PR의 리뷰는 앞선 PR들과 성격이 다르다.\
**리뷰가 프로덕션 코드의 설계를 바꿨다.**\
1회차 지적 하나가 "계산 후 등록"이라는 수정 방향을 회귀로 판정했고, 그 뒤로 등록 방식과 이름이 한 번씩 더 다듬어졌다.

**(1) 1회차 발주.**\
기준 `ebef12d92cd`에 대한 diff와 명세, 관련 호출처 grep을 담은 packet을 만들고 Opus 워커와 codex를 병렬 실행했다.\
보안 스캔 매칭은 0건이었다.

**(2) 1회차 - F1(축출 훅 순서), 두 리뷰어 독립 동일.**\
codex가 먼저 finding 1건을 냈고, 메인이 채택 전에 `Evict.java`로 재현했다.\
곧이어 도착한 Opus의 F1이 같은 결함이었다 - "The diff adds a new phantom key when an eviction removes the entry that was just inserted."\
Opus는 두 수정안을 제시했다 - 등록 후 축출됐으면 되돌리기(`keySet().contains` 사용), 또는 매핑 함수 안에서 등록하기.\
같은 회차의 F2는 "기존 null 값 키 + 함수가 null/예외" 분기 테스트가 없다는 지적이었다.

**(3) 재합의.**\
메인이 수정안 셋을 비교해 사용자에게 올렸다.

| 안 | 내용 | 대가 |
|---|---|---|
| 안1 람다 래핑 (Opus 제안) | 등록을 람다 안, (1)과 (2) 사이로 | 새 키마다 람다 객체 하나 |
| 안2 apply 후 put (codex 제안) | 값을 먼저 계산하고 저장은 `put`에 맡김 | `HashMap.computeIfAbsent`가 해 주던 재진입 감지(CME) 등 의미가 조금 달라짐 |
| 안3 선등록 + 롤백으로 회귀 | try/finally로 되돌리기 | `targetMap.containsKey` 위임 함정 때문에 `keySet().contains`까지 써야 해 가장 복잡 |

사용자는 안1과 stakes 높음 승격을 골랐다.\
안1은 스크래치 프로토타입으로 축출·A·B·C·경우1·2를 먼저 실증한 뒤 레포에 적용했다.\
프로토타입 첫 실행이 상대경로 실수로 레포 빌드를 로드해 "여전히 실패"로 보였던 일이 있었고, 절대경로로 다시 돌려 정상임을 확인했다.

**(4) 1회차 반영.**\
F1은 diff 3(래핑)과 diff 4의 즉시 축출 테스트로, F2는 diff 4의 기존 null 값 테스트 1건으로 반영했다.\
codex의 "실행 증거 packet 부재"(Q1)는 리뷰어가 정적 검토 역할이고 실행 결과는 log가 정본이라 범위 밖으로, codex·Opus 공통의 "`size()` 명시 단언"(Q2)은 `isEmpty()`가 같은 검사라 기각했다.

**(5) 2회차 - F3(재진입), F4(표기 단언).**\
codex는 finding 0건, 렌즈 7개 verified.\
Opus가 low 2건을 냈다.

- **F3**: 람다 안의 `put`이 재진입 수정과 만나면 색인을 저장소에 없는 표기로 덮는다.\
  메인이 `Reentrant.java`로 재현했고, 수정 전 코드는 이 경우 일관됐으므로 "계약 위반 경로지만 신규 불일치"로 보고 채택 -> `putIfAbsent`.
- **F4**: 기존 null 값 키에 non-null을 계산하는 경로(:232)의 저장 표기를 단언하는 테스트가 없다 -> 기존 테스트에 `keySet().containsExactly("Key", "null")` 1줄.

2회차의 열린 질문 둘은 기각했다 - 매핑 함수 안에서 `containsKey` 관측이 바뀌는 것(Q3, Map 계약 미정의·내부 호출처 없음), 기존 null 값 경로의 축출(Q4, 삽입이 아니라 기존 노드 갱신이라 훅이 불리지 않음).

**(6) 3회차 - F5(네이밍).**\
codex는 finding 0건(계약 밖 관찰 하나 - `computeIfAbsent(key, null)`이 NPE를 던지지 않는 것은 diff 이전부터라 범위 밖).\
Opus가 low 1건을 냈다.\
새 지역 변수 `caseInsensitiveKey`는 **소문자로 변환한 키**를 담는데, 같은 클래스의 `get`(:170), `getOrDefault`(:181), `remove`(:246)에서는 같은 이름이 **색인에서 꺼낸 원래 키**를 담는다.\
약 20줄 거리에서 같은 이름이 반대 의미로 쓰인다.\
채택 -> `convertedKey`로 이름 변경.

**(7) 종료 판정과 user override.**\
3회차에서 신규 채택이 1건 나왔으므로 루프 규칙상 종료 조건(신규 0건)을 채우지 못했다.\
사용자가 "이름 변경 + 타깃 재점검"을 선택했고, 이름 변경 hunk만 codex로 재점검해 "Findings: none"을 받은 뒤 리뷰를 종료했다.\
4회차 전체 리뷰를 생략한 것은 log에 user override로 기록했다.

각 지적이 바꾼 것을 한 표로 모으면 이렇다.

| id | 회차 | 출처 | 무엇을 바꿨나 |
|---|---|---|---|
| F1 | 1 | Opus + codex | 등록 시점: 호출 후 -> 람다 안(diff 3) + 즉시 축출 테스트(diff 4) |
| F2 | 1 | Opus | 기존 null 값 + null 반환 테스트 1건(diff 4) |
| F3 | 2 | Opus | 람다 안 등록 `put` -> `putIfAbsent`(diff 5) |
| F4 | 2 | Opus | `computeIfAbsentWithExistingValue`에 `keySet()` 단언 1줄(diff 5) |
| F5 | 3 | Opus | 지역 변수 `caseInsensitiveKey` -> `convertedKey`(diff 6) |

설계가 어떻게 옮겨 갔는지만 세로로 보면 이렇다.

```text
  수정 전   색인 선등록 -> 함수 실행
              |   null / 예외 -> 팬텀 (A, B, C)
              v
  B 안      함수 실행 -> 호출 끝 -> 등록
              |   A, B, C 해결
              |   축출 훅보다 늦다 -> 새 팬텀 (F1)
              v
  안1 래핑  함수 실행 -> [람다 안 등록] -> 삽입 -> 축출 훅
              |   A, B, C, F1 해결
              |   람다 안 put 이 재진입 수정을 덮는다 (F3)
              v
  최종      람다 안 putIfAbsent + convertedKey
```

여기서 가장 값이 큰 것은 **F1**이다.\
B안은 명세의 테스트 셋(A·B·C)을 전부 통과했고, 그 테스트 셋만 보면 끝난 일이었다.\
그런데 명세의 load-bearing 가정 2("신규 키 경로에서 `targetMap.computeIfAbsent` 결과 non-null <=> 매핑 기록됨")가 축출 훅 앞에서 거짓이었다.\
같은 호출 안에서 기록됐다가 지워질 수 있기 때문이다.\
이 가정은 명세에 취소선과 함께 "반증됨(리뷰 F1)"으로 남겨 두었다.

> **load-bearing 가정** — 그것이 참이어야 계획 전체가 성립하는, 아직 확인되지 않은 전제.\
> 예: "반환값이 non-null이면 저장됐다"가 거짓이면 반환값을 근거로 한 등록이 무너진다.

### PR 게시 후 정정 두 건

PR을 연 뒤 문서화 워커가 사실 두 가지를 짚었고, 메인이 직접 확인해 정정했다.

1. **내부 호출처** - 3절에 적은 대로 `StompHeaders`·`NativeMessageHeaderAccessor`는 이 클래스를 쓰지 않는다.\
   실제 경로는 `HttpHeaders` -> `MultiValueMapAdapter.add`/`addAll`과 `MockHttpServletResponse`다.
2. **변이 실험 보고** - 메인은 F4 단언의 가치를 설명하며 "변이 m1(`oldKey` -> `key`)을 새 단언이 잡는다"고 보고했는데, 실제로 m1을 잡은 것은 **기존 단언 `get("null")`(테스트 :109)**이었다.\
   새 단언 `keySet().containsExactly("Key", "null")`(:110)은 다른 변이 - 기존 null 값 경로를 "apply 후 put"으로 바꾼 m2(`["Key","NULL"]`) - 를 혼자 잡는다.\
   단언의 가치는 있지만 설명이 틀렸다.

또 하나는 기록만 해 두었다 - 매핑 함수 안에서 **다른 키**로 같은 맵에 쓰는 재진입이면, 최종 코드에서도 CME 직전에 등록이 끝나 팬텀이 남는다.\
수정 전 코드도 똑같이 남기므로 회귀가 아니고, 계약상 금지된 사용이다.

## 7. 교훈

이 결함이 남긴 것은 두 저장소 동기화의 규칙, 그 규칙의 "시점" 버전, 사후 확인 수단을 의심하는 습관, grep 결과를 타입으로 확인하는 일, 그리고 재현 환경의 함정 다섯이다.

1. **두 저장소에 걸친 쓰기는 실패할 수 있는 쪽을 먼저 하고, 그 성공으로 다른 쪽을 게이트한다.**\
   수정 전 코드는 실패할 수 없는 색인 등록을 먼저 하고 실패할 수 있는 함수 실행을 나중에 했다.\
   그래서 실패하면 성공한 쪽의 흔적만 남았다.
2. **"성공한 뒤에 등록"도 성공을 판정하는 시점이 늦으면 깨진다.**\
   B안은 순서를 뒤집었지만 등록을 호출이 **끝난 뒤**로 미뤘고, 그 사이에 같은 호출 안의 훅이 이미 반대편을 정리해 버렸다.\
   정답은 "성공 직후, 다음 단계 직전"이었다 - 값을 확보한 직후, 삽입 직전.\
   **반환값이 non-null이라는 것은 "지금 기록돼 있다"가 아니라 "값이 만들어졌다"였다.**
3. **사후 확인 수단이 실제로 무엇을 보는지 확인한다.**\
   `targetMap.containsKey`는 이름만 보면 저장소를 묻지만 실제로는 색인을 묻는다.\
   확인 수단 자체가 확인 대상에 기대고 있으면 확인이 아니다.
4. **grep 결과는 타입으로 검증한다.**\
   `computeIfAbsent` 문자열로 찾은 호출처 넷 중 둘은 다른 맵 클래스였다.\
   결론은 바뀌지 않았지만, 가장 흔한 실제 경로(`HttpHeaders`)를 놓쳤고 그 틀린 목록이 PR 본문에 실렸다.
5. **스크래치 재현은 절대 classpath로.**\
   프로토타입 첫 실행이 상대경로 때문에 레포 빌드를 로드해 "수정안이 안 통한다"로 오판할 뻔했다.
