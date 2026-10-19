# PR #37351 - 무대의 실구조와 워크플로우

## 1. 무대 - 실구조

이 결함의 무대는 **하나의 Map 계약을 두 개의 내부 맵으로 구현하는 위임 클래스**다.\
공개 메서드마다 "두 맵 중 어느 쪽을 읽고, 어느 쪽에 어떤 순서로 쓰는가"가 다르고, 그 차이가 결함의 발화 조건이다.

> **위임(delegation)** — 상속 대신 내부에 다른 객체를 들고, 호출을 그 객체에 넘겨 처리하는 구조.\
> 예: 이 클래스는 `LinkedHashMap`을 상속하지 않고 필드로 들고 있다가 `size()` 같은 호출을 넘긴다.

계층을 위에서 아래로 그리면 이렇다.

```text
+------------------------------------------------------------------------------+
| 공개 API             spring-core/util/LinkedCaseInsensitiveMap.java           |
|   containsKey(Object)   색인만 본다                                 :157-160  |
|   get(Object)           색인 -> 원래 키 -> 저장소                    :167-176  |
|   getOrDefault          get 과 같다. 색인에 있으면 기본값을 안 쓴다    :178-187  |
|   put(String, V)        색인 먼저 갱신 -> 저장소 쓰기                 :189-198  |
|   putIfAbsent           색인 선등록 -> 저장소 putIfAbsent             :208-221  |
|   computeIfAbsent       이 PR 의 대상                                :223-241  |
|   remove(Object)        색인에서 제거 -> 저장소에서 제거              :243-252  |
|   size() / isEmpty()    저장소만 본다                          :147-150, :152-155 |
+------------------------------------------------------------------------------+
                 |                                    |
       읽기·쓰기 v                          읽기·쓰기   v
+---------------------------------+  +----------------------------------------+
| caseInsensitiveKeys      :59    |  | targetMap                       :57    |
|   HashMap<String, String>       |  |   LinkedHashMap<String, V>             |
|   "key" -> "Key"                |  |   "Key" -> value  (삽입 순서 보존)      |
|   convertKey = toLowerCase      |  |                                        |
|   (locale)              :337-339|  |   익명 서브클래스로 생성       :115-129 |
+---------------------------------+  |   containsKey -> 바깥 containsKey 위임  |
                                     |                               :117-120 |
                                     |   removeEldestEntry -> 바깥 훅 호출,    |
                                     |   true 면 색인에서도 제거      :121-128 |
                                     +----------------------------------------+
                                                       |
                                                       v
+------------------------------------------------------------------------------+
| 확장점 (protected)                                                            |
|   convertKey(String)            기본: key.toLowerCase(getLocale())   :337-339 |
|   removeEldestEntry(Map.Entry)  기본: false                         :347-349 |
|     <- 서브클래스가 true 를 돌려주면 targetMap 의 삽입 직후 축출이 일어난다      |
+------------------------------------------------------------------------------+
```

이 그림에서 읽어야 할 사실은 셋이다.\
첫째, **`containsKey`와 `size`가 서로 다른 맵을 본다.**\
그래서 두 맵이 어긋나면 공개 API끼리 모순된 답을 한다.\
둘째, **저장소 `targetMap`은 평범한 `LinkedHashMap`이 아니다.**\
`containsKey`와 `removeEldestEntry` 두 메서드가 오버라이드돼 바깥 클래스와 색인으로 되돌아간다.\
셋째, **축출 훅은 JDK가 부른다.**\
이 클래스의 코드가 아니라 `HashMap.computeIfAbsent`/`put` 내부의 `afterNodeInsertion`이 부르므로, 호출 시점을 이 클래스가 정하지 못한다.

`targetMap`의 두 오버라이드가 무엇을 되돌려 보내는지만 떼면 이렇다.

```text
        targetMap 안에서 일어나는 일               실제로 닿는 곳
+-----------------------------------+     +-----------------------------------+
| targetMap.containsKey(k)          | --> | LinkedCaseInsensitiveMap          |
|   (이름은 저장소에 묻는 것 같다)  |     |   .containsKey(k)                 |
|                                   |     |   = 색인 caseInsensitiveKeys 조회  |
+-----------------------------------+     +-----------------------------------+
| targetMap.removeEldestEntry(e)    | --> | LinkedCaseInsensitiveMap          |
|   (JDK 가 삽입 직후 부른다)       |     |   .removeEldestEntry(e)  확장점   |
|                                   |     |   true 면 removeCaseInsensitiveKey |
|                                   |     |   (색인에서 e 의 키 제거)          |
+-----------------------------------+     +-----------------------------------+
```

-> 위 칸 때문에 "저장소에 실제로 들어 있나"를 `targetMap.containsKey`로 확인할 수 없고, 아래 칸 때문에 색인 등록 시점이 JDK의 삽입 순서에 묶인다.

## 2. 쓰기 경로 넷 - 색인과 저장소에 쓰는 순서

이 클래스에서 두 맵에 쓰는 경로는 넷이다.\
고정 축으로 비교하면 `computeIfAbsent`만 다른 성질을 가진 이유가 드러난다.

| 경로 | 색인 쓰기 | 저장소 쓰기 | 실패할 수 있는 단계가 있나 | 축출 훅 |
|---|---|---|---|---|
| `put` (:189-198) | 먼저 `put` | 그 다음 `put` (표기가 바뀌면 옛 키 제거 후) | 없음 | 저장소 `put` 안에서 불림 -> 색인이 이미 있으니 함께 제거 |
| `putIfAbsent` (:208-221) | 먼저 `putIfAbsent` | 그 다음 `putIfAbsent` | 없음(값이 이미 주어짐) | 같음 |
| `remove` (:243-252) | 먼저 제거 | 그 다음 제거 | 없음 | 해당 없음 |
| `computeIfAbsent` 수정 전 (:224-236) | 먼저 `putIfAbsent` | 함수가 non-null일 때만 | **매핑 함수(null·예외)** | 색인이 이미 있으니 함께 제거 |
| `computeIfAbsent` 최종 (:223-241) | 함수가 non-null일 때 람다 안에서 | 그 직후 HashMap이 삽입 | 매핑 함수 | 색인이 이미 있으니 함께 제거 |

**`put`과 `putIfAbsent`는 선등록을 해도 괜찮다.**\
값이 이미 손에 있어서 저장소 쓰기가 실패할 수 없기 때문이다.\
1회차 Opus 리뷰가 이 점을 확인했다 - "`putIfAbsent` (:210) still registers first, but it always inserts, so it cannot leave a phantom."\
`computeIfAbsent`만 **두 쓰기 사이에 실패할 수 있는 사용자 코드가 끼어 있다.**\
그래서 형제 메서드의 "색인 먼저" 관용구를 그대로 쓰면 이 메서드만 깨진다.

> **관용구(idiom)** — 같은 코드베이스 안에서 같은 문제를 푸는 반복된 코드 모양.\
> 예: 이 클래스의 쓰기 메서드는 "색인을 먼저 쓰고 저장소를 쓴다"는 모양을 공유한다.

네 경로를 "실패 가능한 단계가 어디 있나"로 세로로 놓으면 이렇다.

```text
  put / putIfAbsent               computeIfAbsent (수정 전)
  +-------------------+           +-------------------------------+
  | 색인 쓰기         |           | 색인 쓰기                     |
  +-------------------+           +-------------------------------+
           |                                    |
           v                                    v
  +-------------------+           +-------------------------------+
  | 저장소 쓰기       |           | 매핑 함수   <- 실패할 수 있다 |
  | (값이 이미 있다)  |           +-------------------------------+
  +-------------------+                         |
                                                v
  실패할 단계 없음                 +-------------------------------+
  -> 선등록 무해                   | 저장소 쓰기 (non-null 일 때)  |
                                   +-------------------------------+
                                   실패하면 색인만 남는다 -> 팬텀
```

## 3. 한 번의 `computeIfAbsent` 안에서 JDK가 하는 일

결함과 수정 둘 다 **JDK `HashMap.computeIfAbsent` 한 번의 호출 안의 순서**에 걸려 있다.\
JDK 25.0.1 소스(`java/util/HashMap.java:1196-1250`)를 직접 읽어 확인한 흐름이다.

```text
targetMap.computeIfAbsent(key, f)
  |
  +-- 버킷에서 key 노드(old) 탐색
  |     old 가 있고 old.value != null  -> afterNodeAccess(old), old.value 반환   (f 미호출)
  |
  +-- mc = modCount
  +-- v = f.apply(key)                                   <- (1) 사용자 함수
  +-- mc != modCount 이면 ConcurrentModificationException  <- 재진입 감지
  |
  +-- v == null                -> return null            (아무것도 안 함, old 도 안 지움)
  +-- old != null (값이 null)  -> old.value = v
  |                               afterNodeAccess(old)   (삽입 아님 -> 축출 훅 안 불림)
  |                               return v
  +-- 그 외                    -> 새 노드 삽입            <- (2)
                                  modCount++, size++
                                  afterNodeInsertion(true) <- (3)
                                    LinkedHashMap: removeEldestEntry(head) 가 true 면
                                    removeNode(head)
                                  return v
```

`LinkedHashMap.afterNodeInsertion`(`LinkedHashMap.java:321-327`)이 `removeEldestEntry`를 부르고, true면 가장 오래된 노드를 지운다.\
`LinkedHashMap.removeEldestEntry`의 javadoc은 "invoked by put and putAll after inserting a new entry"라고만 적지만, `computeIfAbsent`의 새 노드 삽입도 같은 `afterNodeInsertion` 경로를 탄다.\
작업 중에 스크래치 `Evict2.java`로 "hook 호출·eldest=방금 삽입 키"를 실측했고(명세 §10), 문서화 단계의 `JdkOrder.java`가 "apply -> 삽입 -> removeEldestEntry" 순서를 다시 확인했다.

> **afterNodeInsertion** — `HashMap`이 새 노드를 넣은 직후 부르는 내부 훅으로, `LinkedHashMap`은 여기서 축출 여부를 묻는다.\
> 예: `removeEldestEntry`를 true로 오버라이드하면, 삽입이 끝나자마자 가장 오래된 노드가 제거된다.

이 흐름에서 이 PR에 쓰이는 사실은 넷이다.

| 사실 | 위치 | 이 PR에서의 쓰임 |
|---|---|---|
| null이면 아무것도 안 한다 | `if (v == null) return null` | A: 저장소에 아무것도 없는데 색인만 남는다 / D: 기존 null 노드도 안 지운다 |
| 예외는 apply에서 전파 | `f.apply(key)` | C: 그 아래 단계가 실행되지 않는다 |
| 새 노드는 삽입 **후** 축출 훅 | `afterNodeInsertion(true)` | F1: 호출이 끝난 뒤 등록하면 훅보다 늦다 |
| 기존 null 노드는 값만 갱신 | `old.value = v; afterNodeAccess(old)` | 리뷰 Q4: 기존 키 경로에는 축출이 없다 |
| apply 전후 `modCount` 비교 | `mc != modCount` | F3: 재진입 수정이면 CME, 그러나 람다 안 등록은 이미 끝난 뒤 |

색인 `caseInsensitiveKeys`는 `targetMap`과 별개의 `HashMap`이므로, 감싼 람다 안에서 색인에 쓰는 것은 `targetMap`의 `modCount`를 바꾸지 않는다.\
그래서 래핑 자체는 CME 검사에 걸리지 않는다.

## 4. 등록 시점 셋과 그 결과

같은 타임라인 위에 등록 시점 셋을 올리고, 함수 결과 셋과 축출 여부를 교차시키면 이 PR 전체가 한 표에 들어간다.

| 등록 시점 | 함수 non-null, 축출 없음 | 함수 non-null, 즉시 축출 | 함수 null | 함수 예외 |
|---|---|---|---|---|
| 수정 전: (1) 앞(선등록) | 일치 | 일치 (훅이 지움) | **팬텀 A** | **팬텀 C** |
| B안: (3) 뒤(호출 후) | 일치 | **팬텀 F1** | 일치 | 일치 |
| 최종: (1)과 (2) 사이(람다 안) | 일치 | 일치 (훅이 지움) | 일치 | 일치 |

**수정 전과 B안은 서로의 거울상이다.**\
수정 전은 "등록이 너무 일러서" 실패 경로에서 흔적이 남고, B안은 "등록이 너무 늦어서" 축출 경로에서 흔적이 남는다.\
유일하게 모든 칸이 "일치"인 것은 성공이 확정된 직후이면서 삽입보다 앞인 자리다.

같은 표를 즉시 축출 서브클래스 하나로 세로로 펼치면 이렇다.

```text
  시각      수정 전 (선등록)        B 안 (호출 후)           최종 (람다 안)
  ------    ---------------------   ----------------------   ----------------------
  진입      색인 += key->Key        -                        -
  (1) f     "value"                 "value"                  "value"
            -                       -                        색인 += key->Key
  (2) 삽입  저장소 += Key           저장소 += Key            저장소 += Key
  (3) 훅    색인 -= key             색인 -= key (없음)       색인 -= key
            저장소 -= Key           저장소 -= Key            저장소 -= Key
  반환 후   -                       색인 += key->Key         -
  ------    ---------------------   ----------------------   ----------------------
  최종      색인 {}  저장소 {}      색인 {key->Key}          색인 {}  저장소 {}
                                    저장소 {}  <- 팬텀
```

## 5. 재진입 - 계약 밖에서 생기는 두 갈래

`Map#computeIfAbsent` 계약은 매핑 함수가 맵을 수정하지 말라고 한다.\
JDK는 그것을 `modCount` 비교로 감지해 CME를 던지지만, **감지는 함수가 끝난 뒤**이므로 그 사이에 일어난 일은 되돌리지 않는다.\
리뷰 2회차와 문서화 단계에서 두 갈래가 확인됐다.

> **modCount** — 컬렉션이 구조적으로 바뀔 때마다 1씩 오르는 내부 카운터로, 동시 수정 감지에 쓰인다.\
> 예: 함수 실행 전후의 값이 다르면 함수가 맵을 고쳤다는 뜻이다.

**갈래 1 - 같은 키(다른 표기)를 쓴다: `map.computeIfAbsent("Key", k -> { map.put("KEY", "x"); return "v"; })`**

| 단계 | 람다 안 등록 = `put` | 람다 안 등록 = `putIfAbsent` (최종) | 수정 전(선등록) |
|---|---|---|---|
| 진입 | 색인 `{}` | 색인 `{}` | 색인 `{key->Key}` |
| 함수 안 `put("KEY","x")` | 색인 `{key->KEY}`, 저장소 `{KEY=x}` | 같음 | 색인 `{key->KEY}`(덮음), 저장소 `{KEY=x}` |
| 람다 안 등록 | 색인 `{key->Key}` **덮음** | 색인 `{key->KEY}` 그대로 | - |
| CME | 저장소 `{KEY=x}` | 저장소 `{KEY=x}` | 저장소 `{KEY=x}` |
| 결과 | `get("key")`=null, `remove` 후 `KEY=x` 고아 | 일치 | 일치 |

리뷰 F3가 이 갈래를 짚었고, `put` -> `putIfAbsent`로 해결했다.\
수정 전 코드는 이 경우 일관됐으므로 `put`을 그대로 두었다면 **좁지만 새로운 불일치**였다.

**갈래 2 - 다른 키를 쓴다: `map.computeIfAbsent("Key", k -> { map.put("Other", "x"); return "v"; })`**

함수가 non-null을 돌려주므로 람다 안 등록이 `"key" -> "Key"`를 쓰고, 그 다음 HashMap이 `modCount` 변화를 보고 CME를 던져 `"Key"`는 삽입되지 않는다.\
최종 코드에서도 팬텀이 남는다.\
리뷰 2회차 Opus가 "The phantom stays, the same as before the change, so this is not a regression"이라고 판정했고, 문서화 단계의 `Reentrant2.java`가 "orig does the same, B does not"을 확인했다.\
수정 전과 같은 결과이고 계약 위반 경로라 기록만 남겼다.\
이 갈래 때문에 명세 §2의 "예외면 매핑을 기록하지 않음"은 정확히는 **함수 자신이 던진 예외**에 대해서만 성립한다.

두 갈래를 한 장에 놓으면 이렇다.

```text
                  매핑 함수가 같은 맵에 쓴다 (계약 위반)
                               |
              +----------------+----------------+
              |                                 |
              v                                 v
      같은 키, 다른 표기 ("KEY")          다른 키 ("Other")
              |                                 |
              v                                 v
   람다 안 put        -> 색인 덮음      람다 안 등록 -> CME
   람다 안 putIfAbsent -> 그대로        "Key" 미삽입 -> 팬텀
              |                                 |
              v                                 v
   최종: 일치 (F3 로 해결)              최종: 팬텀 (수정 전과 동일, 기록만)
```

## 6. 이력 - 선등록 구조는 어디서 왔나

`git log`로 확인한 관련 커밋은 이렇다.

| 커밋 | 날짜 | 내용 | 이 PR과의 관계 |
|---|---|---|---|
| `8147c112f54` | 2016-12-23 | "LinkedCaseInsensitiveMap delegates to LinkedHashMap instead of extending it" | 상속에서 위임으로 - `targetMap`과 축출 훅 오버라이드의 출발점 |
| `50e5a65b2d7` | 2017-01-12 | "LinkedCaseInsensitiveMap provides case-insensitive keySet again" | `targetMap.containsKey`를 색인에 위임하는 오버라이드 - 사후 확인을 불가능하게 만든 자리 |
| `b790bd1fd68` | 2018-06-11 | "LinkedCaseInsensitiveMap explicitly implements put/computeIfAbsent" | `computeIfAbsent` 명시 구현 도입 - 이때부터 선등록 구조 |
| `b18cf3c873b` | 2021-04-30 | "Follow contract of computeIfAbsent LinkedCaseInsensitiveMap"(gh-26868, Arjen Poutsma) | 기존 null 값이면 `key = oldKey`로 재계산 - 팬텀이 있으면 이 분기가 표기를 누출(B) |
| `1b4955e49f0` | 2026-09-30 | 이 PR | 선등록 제거, 람다 안 등록 |

선등록 자체를 겨냥한 수정 이력은 없었다(명세 §10).\
gh-26868은 "기존 키가 null에 매핑된 경우"라는 정당한 결함을 고쳤지만, 그 분기는 색인이 언제나 정직하다는 전제 위에 서 있었다.\
선등록이 그 전제를 깨는 순간, 2021년의 수정이 2018년의 결함을 표기 누출로 증폭시키는 구조가 됐다.

머지 이후 같은 파일에 `2b216a4b36a`(2026-10-09, Yanming Zhou, "Fix nullability in LinkedCaseInsensitiveMap", gh-37432)가 들어왔다.\
`containsValue` 파라미터와 `EntryIterator` 타입 파라미터의 nullability 표기 수정으로, 이 PR의 `computeIfAbsent`와는 무관하다.

## 7. 스프링 전역에서의 자리

`LinkedCaseInsensitiveMap`은 조회는 대소문자를 가리지 않되 출력은 원래 표기대로 해야 하는 자리 - HTTP 헤더 이름, JDBC 컬럼명 - 에 쓰인다.\
머지 커밋 기준으로 이 클래스를 언급하는 main 소스는 클래스 자신을 포함해 22개 파일이다(spring-web 11, spring-core 3, spring-jdbc·spring-r2dbc·spring-test·spring-websocket 각 2).\
작업 명세는 "production 25개 파일", 문서화 워커는 "23 main-source files"로 셌는데, 세는 범위가 달라 숫자가 엇갈린다.

> **blast radius** — 한 곳이 잘못됐을 때 영향이 퍼지는 범위.\
> 예: 공용 유틸 클래스는 사용처가 많아, 메서드 하나의 변경도 여러 모듈에 닿을 수 있다.

그중 `computeIfAbsent`를 실제로 부르는 내부 경로는 둘이다.

```text
[프레임워크 안에서 LinkedCaseInsensitiveMap.computeIfAbsent 에 닿는 경로]

spring-web   HttpHeaders()
               new LinkedCaseInsensitiveMap<>(8, Locale.ROOT)         HttpHeaders.java:445
               -> CollectionUtils.toMultiValueMap(...)
               -> MultiValueMapAdapter.add      computeIfAbsent(key, k -> new ArrayList<>(1))     :66
                  MultiValueMapAdapter.addAll   computeIfAbsent(key, k -> new ArrayList<>(values.size()))  :72

spring-test  MockHttpServletResponse
               headers = new LinkedCaseInsensitiveMap<>()             :121
               doAddHeaderValue   computeIfAbsent(name, key -> new HeaderValueHolder())   :788

   두 경로 모두 매핑 함수가 non-null 을 만든다.
   -> 프레임워크 내부 사용만으로는 팬텀이 생기지 않는다.
```

작업 명세와 PR 본문은 이 목록을 `StompHeaders`, `NativeMessageHeaderAccessor`, `MockHttpServletResponse`로 적었다.\
앞의 둘은 `LinkedMultiValueMap`을 쓰므로(`StompHeaders`의 `new LinkedMultiValueMap<>(3)`, StompHeaders.java:116) 이 클래스와 무관하다.\
`computeIfAbsent` 호출을 문자열로만 찾고 수신 객체의 타입을 확인하지 않은 결과다.\
PR 게시 뒤 문서화 워커가 짚었고 메인이 확인해 정정했지만, 게시된 PR 본문은 정정 전 문구로 남아 있다.

발화 조건을 순서대로 통과해야 증상이 보인다.

```text
이 클래스를 직접 쓰나?                 -- 아니오 -->  증상 없음 (HttpHeaders 등 내부 경로)
        |
       예
        v
computeIfAbsent 를 부르나?             -- 아니오 -->  증상 없음
        |
       예
        v
매핑 함수가 null 이나 예외를 내나?     -- 아니오 -->  증상 없음
        |                                   (단, removeEldestEntry 즉시 축출 서브클래스는
       예                                    B 안이었다면 여기서도 팬텀)
        v
  발화 - 색인에 키가 남고, 다음 삽입이 그 표기를 쓴다
```

## 8. 관련 개념

이 무대의 원리는 study-note의 이슈 카드 하나로 정리돼 있다.\
작업 마감 때 아카이브 워커가 판정한 결과다.

- **이슈 1(선등록 -> 실패 흔적)**: 기존 카드 `issue/cross-cutting/reliability/non-transactional-multi-step/`과 원리도 해결도 같아 무변경.\
  카드의 원칙 - "두 저장소에 걸친 변경은 실패 가능한 쪽을 먼저 하고, 그 성공 여부로 다른 쪽을 게이트한다".
- **이슈 2(삽입 도중 훅 -> 확정 시점)**: 같은 원리지만 해결이 다르다 - 순서가 아니라 **확정 시점**의 문제.\
  같은 카드의 `3-answer.md`에 "방안 비교 — 삽입 도중 훅이 두 번째 저장소를 건드릴 때의 확정 시점" 섹션으로 append했다.

다만 이 append는 당시 임시 worktree(브랜치 `docs/spring-37351-lcim`)에서만 이루어졌다.\
그 브랜치에는 main 대비 커밋이 없고, 이 문서 작성 시점의 study-note 작업 트리의 해당 카드에도 "확정 시점" 섹션은 없다.\
즉 이슈 2의 방안 비교 섹션은 커밋되지 않은 채 worktree와 함께 사라진 상태다.

## 출처

기준: upstream 머지 커밋 `1b4955e49f0`(7.0.x, main에 merge-forward). 본문의 LinkedCaseInsensitiveMap.java
file:line은 이 커밋의 "수정 후" 좌표이고, "수정 전"이라고 적은 좌표는 그 부모 `06c597ed6fa` 기준이다.
JDK 좌표는 로컬 Temurin 25.0.1의 `lib/src.zip`이다. 작업 브랜치 커밋은 `95a1db98006`(base
`ebef12d92cd`)이다. 메인테이너가 커밋 메시지에 `Closes gh-37351`을 더하고 7.0.x 위에 올려 머지하면서
`1b4955e49f0`이 됐으며, 두 커밋의 코드 diff는 동일하다(로컬 대조).
