# java/java-spring/07 — 요청 파라미터 바인딩 — 정리 (힌트)

> 출처 — study-site 항목 `java/spring-request-params`(항목 데이터 `data/java/spring-essentials.json`) · 정답 코드 study-practice `java/java-spring/reference/spring-request-params.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**요청 파라미터 바인딩은 「택배 상자에서 물건을 꺼내 칸칸이 나눠 담는 일」이다.**
택배 상자(HTTP 요청)에는 송장 주소(URL 경로), 주소 옆 메모(쿼리 문자열), 상자 속 내용물(본문), 겉면 스티커(헤더), 단골 표시(쿠키)가 함께 붙어 온다.
받는 사람(컨트롤러 메서드)은 「주소의 몇 번째 칸」「메모의 어느 항목」「상자 속 물건」을 집어 오라고 표시만 해 두면 된다.
Spring MVC 도 똑같은 구조다.
메서드 매개변수에 어노테이션을 붙이면, Spring 이 요청에서 해당 조각을 찾아 매개변수 타입으로 바꿔 넣어 준다.

> **바인딩** — 요청의 문자열 데이터를 메서드 매개변수(또는 객체 필드)에 타입을 맞춰 채워 넣는 일.\
> 예: 쿼리 `?minPrice=1000` 을 `int minPrice` 에 `1000` 으로 넣는다.

| 비유 | 실체 |
|---|---|
| 송장 주소의 칸 | URL 경로 변수 → `@PathVariable` |
| 주소 옆 메모 | 쿼리 파라미터 → `@RequestParam` |
| 상자 속 내용물 | JSON 본문 → `@RequestBody` |
| 겉면 스티커 | HTTP 헤더 → `@RequestHeader` |
| 단골 표시 | 쿠키 → `@CookieValue` |
| 메모 여러 줄을 한 봉투에 | 쿼리 파라미터 묶음 → `@ModelAttribute` 객체 |

```text
GET /api/v1/users/123/orders/456?x=1      ← 경로 · 쿼리
Authorization: Bearer abc                 ← 헤더
Cookie: theme=dark                        ← 쿠키
{ ... }                                   ← 본문(POST/PUT)
          │
          ▼  Spring 이 조각마다 꺼내 타입 변환
getOrder(@PathVariable Long userId, ...)
```

## 이 주제가 답하려는 질문

1. 요청의 어느 부분(경로 · 쿼리 · 본문 · 헤더 · 쿠키)을 어떤 어노테이션으로 꺼내나?
2. 값이 없을 때는 어떻게 되며, 선택 값과 기본값은 어떻게 정하나?
3. 같은 이름의 값이 여러 개이거나, 파라미터가 많을 때는 어떻게 받나?
4. 매개변수 이름과 요청 속 이름이 다르면 어떻게 이어 주나?

## 동작 방식

원본 예제는 컨트롤러 하나에 여섯 가지 바인딩을 모아 둔다.
클래스에 `@RestController` 와 `@RequestMapping("/api/v1")` 이 붙어 있다.

> **`@RestController`** — 컨트롤러이면서, 메서드가 돌려준 객체를 JSON 응답으로 바꿔 보내는 클래스 표시.\
> 예: `ResponseEntity.ok(order)` 를 돌려주면 `order` 가 JSON 본문이 된다.

> **`@RequestMapping` (클래스 위)** — 클래스 안 모든 메서드 경로 앞에 붙는 공통 접두 경로.\
> 예: 클래스 `/api/v1` + 메서드 `/products` = `/api/v1/products`.

> **`ResponseEntity`** — 상태 코드 · 헤더 · 본문을 함께 담는 HTTP 응답 표현.\
> 예: `ResponseEntity.ok(x)` 는 200 OK 에 본문 `x`.

### (1) `@PathVariable` — URL 경로의 변수

**언제 쓰나** — 경로 자체가 자원을 가리킬 때(「123번 사용자의 456번 주문」).

```text
매핑:  @GetMapping("/users/{userId}/orders/{orderId}")
요청:  GET /api/v1/users/123/orders/456
        │
        ├─ {userId}  = "123" → @PathVariable Long userId          → 123L
        └─ {orderId} = "456" → @PathVariable("orderId") Long id   → 456L
```

- 매핑 경로의 `{…}` 자리가 경로 변수다.
- 요청 경로에서 그 자리의 글자를 잘라 낸다.
- 매개변수 이름이 `{}` 안 이름과 같으면 어노테이션에 이름을 생략한다(`userId`).
- 이름이 다르면 `@PathVariable("orderId")` 처럼 경로 쪽 이름을 적어 잇는다(매개변수는 `id`).
- 잘라 낸 문자열 `"456"` 은 매개변수 타입 `Long` 으로 바뀐다.

### (2) `@RequestParam` — 쿼리 파라미터

**언제 쓰나** — 검색 조건 · 정렬 · 페이지처럼 「같은 자원을 어떻게 걸러 보나」를 정할 때.

```text
요청: GET /api/v1/products?category=electronics&minPrice=1000&sort=price,desc
        │
        ├─ category=electronics → @RequestParam String category              (필수)
        ├─ minPrice=1000        → @RequestParam(required=false, defaultValue="0") int minPrice
        ├─ (maxPrice 없음)      → defaultValue="999999" 이 들어감
        └─ sort=price,desc      → @RequestParam(defaultValue="name,asc") String sort
```

- `@RequestParam` 의 `required` 기본값은 `true` 다 — 값이 없으면 바인딩이 실패한다.
- 선택 파라미터는 `required = false` 를 적는다.
- `defaultValue` 를 주면 값이 없을 때 그 문자열이 들어가고, 매개변수 타입으로 바뀐다(`"999999"` → `999999`).
- 같은 이름을 여러 번 보내면 `List` 로 모은다: `?ids=1&ids=2&ids=3` → `@RequestParam List<Long> ids` = `[1, 2, 3]`.
- 이름을 정하지 않고 전부 받으려면 `@RequestParam Map<String, String> allParams` 로 키-값을 모은다.

### (3) `@RequestBody` — JSON 요청 본문

**언제 쓰나** — POST · PUT 으로 새 자원이나 수정 내용을 통째로 보낼 때.

```text
요청: POST /api/v1/orders
      Content-Type: application/json
      { ...주문 내용... }
        │
        ├─ 본문 JSON → CreateOrderRequest 객체로 역직렬화   (@RequestBody)
        └─ 객체의 검증 규칙 실행                            (@Valid)
```

- 본문 전체가 매개변수 객체 하나가 된다.
- `@Valid` 를 함께 붙이면 객체가 채워진 뒤 검증이 실행된다.
- 원본 팁: GET 요청에는 쓰지 않는다 — GET 은 조건을 경로와 쿼리로 보내는 요청이고, 본문은 POST · PUT 의 몫이다.

> **역직렬화** — 텍스트(JSON)를 객체로 되돌리는 일.\
> 예: `{"name":"Kim"}` → `name` 필드가 `"Kim"` 인 객체.

### (4) `@RequestHeader` — HTTP 헤더

**언제 쓰나** — 인증 토큰 · 언어 설정처럼 요청 전체에 붙는 부가 정보를 읽을 때.

```text
요청 헤더:
  Authorization: Bearer abc123
  (Accept-Language 없음)
        │
        ├─ @RequestHeader("Authorization") String authHeader  → "Bearer abc123"
        ├─ @RequestHeader(value="Accept-Language", defaultValue="ko") → "ko"
        └─ @RequestHeader Map<String,String> allHeaders       → 헤더 전부
메서드 안: authHeader.replace("Bearer ", "") → "abc123"
```

- 헤더 이름을 적어 값 하나를 꺼낸다.
- `@RequestParam` 과 같은 꼴로 `value` · `defaultValue` 를 준다.
- `Map` 으로 받으면 모든 헤더가 키-값으로 모인다.
- 원본은 꺼낸 값에서 `"Bearer "` 를 지워 토큰만 남긴다.

### (5) `@CookieValue` — 쿠키 값

**언제 쓰나** — 화면 테마 · 세션 식별자처럼 브라우저가 쿠키로 들고 오는 값을 읽을 때.

```text
요청: Cookie: (아무것도 없음)
        │
        ├─ @CookieValue(value="theme", defaultValue="light") String theme → "light"
        └─ @CookieValue(value="sessionId", required=false) String sessionId → null
```

- 쿠키 이름을 `value` 로 적는다.
- 기본값을 주면 쿠키가 없을 때 그 값이 들어간다.
- `required = false` 만 주고 기본값이 없으면, 쿠키가 없을 때 `null` 이 들어간다.

### (6) `@ModelAttribute` — 쿼리 · 폼 데이터를 객체로

**언제 쓰나** — 검색 조건처럼 쿼리 파라미터가 많을 때 하나하나 `@RequestParam` 으로 받지 않고 객체 하나로 받는다.

```text
요청: GET /api/v1/members?name=Kim&age=25&city=Seoul
        │
        ├─ new MemberSearchCondition()
        ├─ name=Kim   → setName("Kim")
        ├─ age=25     → setAge(25)     (String "25" → Integer)
        └─ city=Seoul → setCity("Seoul")
        ▼
searchMembers(MemberSearchCondition condition)
```

- 파라미터 이름이 객체의 필드(프로퍼티) 이름과 맞으면 그 필드에 채운다.
- 원본 코드의 주석대로 setter 로 채우므로, 조건 객체에 getter · setter 가 필요하다(또는 Lombok `@Data`).
- 요청에 없는 필드는 채워지지 않고 처음 값(참조 타입이면 `null`)으로 남는다.
- 원본 예제가 `age` 를 `int` 가 아닌 `Integer` 로 둔 것도 「안 왔음 = `null`」을 담기 위해서로 읽힌다(원본에 근거 없음 — 추론).

## 문법 — 형태와 규칙

```java
@RestController
@RequestMapping("/api/demo")
public class DemoController {
    @GetMapping("/items/{itemId}")
    public String one(@PathVariable("itemId") Long id,
                      @RequestParam(required = false, defaultValue = "1") int page,
                      @RequestHeader(value = "Accept-Language", defaultValue = "ko") String lang,
                      @CookieValue(value = "theme", required = false) String theme) {
        return id + "/" + page + "/" + lang + "/" + theme;
    }

    @PostMapping("/items")
    public String create(@Valid @RequestBody ItemRequest body) {
        return "ok";
    }
}
```

| 어노테이션 | 꺼내는 곳 | 자주 쓰는 속성 | 여러 값 · 전부 |
|---|---|---|---|
| `@PathVariable` | URL 경로의 `{이름}` | 이름 (`"orderId"`) | — |
| `@RequestParam` | 쿼리 문자열 (`?a=1`) | `required`(기본 `true`) · `defaultValue` | `List<T>` · `Map<String,String>` |
| `@RequestBody` | 요청 본문(JSON) | `@Valid` 와 함께 | 본문 전체 = 객체 하나 |
| `@RequestHeader` | HTTP 헤더 | `value` · `defaultValue` | `Map<String,String>` |
| `@CookieValue` | 쿠키 | `value` · `defaultValue` · `required` | — |
| `@ModelAttribute` | 쿼리 · 폼 파라미터 묶음 | — | 객체 필드 여럿 |

- 매개변수 이름과 요청 속 이름이 같으면 어노테이션의 이름을 생략한다.
- 다르면 어노테이션에 요청 쪽 이름을 적는다.
- 요청의 값은 모두 문자열이고, 매개변수 타입(`Long` · `int` · `Integer`)으로 바뀌어 들어간다.
- 한 메서드에 여러 바인딩 어노테이션을 섞어 쓴다.

## 어디서 틀리나

### 1. 선택 파라미터에 `required = false` 를 빼먹는다

`@RequestParam` 의 `required` 기본값은 `true` 다.
그래서 `@RequestParam String category` 처럼 쓴 파라미터를 빼고 요청하면 바인딩이 실패한다.
선택 파라미터라면 `required = false` 를 적고, 필요하면 `defaultValue` 를 함께 준다.

### 2. 파라미터가 많은데 `@RequestParam` 을 줄줄이 단다

검색 조건이 다섯 개, 열 개가 되면 메서드 서명이 길어진다.
원본 팁대로 `@ModelAttribute` 로 조건 객체 하나에 받으면 깔끔하다.
이때 조건 객체에 setter 가 없으면 원본 주석이 말하는 「setter 로 바인딩」이 일어나지 않는다.

### 3. GET 요청에 `@RequestBody` 를 단다

원본 팁: `@RequestBody` 는 POST · PUT 의 JSON 바디에 쓰고, GET 에는 쓰지 않는다.
GET 의 조건은 경로(`@PathVariable`)와 쿼리(`@RequestParam` · `@ModelAttribute`)로 받는다.

### 4. 경로 변수 이름과 매개변수 이름이 어긋난다

`{orderId}` 를 매개변수 `id` 로 받으면서 `@PathVariable Long id` 라고만 쓰면 `id` 라는 경로 변수를 찾는다.
이름이 다르면 `@PathVariable("orderId")` 처럼 경로 쪽 이름을 반드시 적는다.

### 5. `"Bearer "` 지우기를 `replace` 로 한다

원본은 `authHeader.replace("Bearer ", "")` 로 토큰을 꺼낸다.
Java 의 `String.replace` 는 앞부분만이 아니라 문자열 안 **모든** 일치를 바꾼다.
또 `Authorization` 헤더가 `Bearer ` 로 시작하지 않아도 그대로 통과한다.
접두사 검사(`startsWith`) 뒤에 잘라 내는 편이 의도에 맞다(원본에 근거 없음 — 추론).

### 6. 원본 예제는 그대로 컴파일되지 않는다

원본의 주장 → 「완성된 컨트롤러 예제」로 보인다.
왜 의심스러운가 →
- `@Valid` 를 쓰지만 그 임포트가 없다(`org.springframework.web.bind.annotation.*` 에 들어 있지 않다).
- `orderService` · `productService` · `searchService` · `userService` · `memberService` 필드가 선언되지 않았다.
- `OrderResponse` · `CreateOrderRequest` 같은 DTO 가 정의되지 않았다.
- `public` 클래스 두 개(`ParameterBindingController` · `MemberSearchCondition`)가 한 파일에 있다 — Java 는 한 파일에 `public` 최상위 클래스를 하나만 허용하므로 파일을 나눠야 한다.

바인딩 문법을 보이는 발췌로 읽어야 한다.

### 7. 받아 놓고 쓰지 않는 값

`getProfile` 은 `allHeaders` 를 받지만 메서드 안에서 쓰지 않는다.
「모든 헤더를 `Map` 으로 받을 수 있다」를 보이는 시연용이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 어노테이션을 보고 요청에서 값을 꺼내 매개변수에 넣는다 | Spring MVC(프레임워크). Java 언어는 어노테이션을 붙이게만 해 줄 뿐 아무 동작도 하지 않는다 |
| `@RequestParam` 의 `required` 기본값이 `true` | Spring 의 어노테이션 정의(원본 팁) |
| JSON 본문을 객체로 바꾼다 | Spring 의 메시지 변환기와 그 뒤의 JSON 라이브러리(어느 라이브러리인지는 설정에 따름 — 확인 필요) |
| `@Valid` 로 검증이 돌아간다 | Bean Validation 구현체가 클래스패스에 있어야 한다(확인 필요) |
| 이름을 생략하면 매개변수 이름으로 찾는다 | Spring 이 매개변수 이름을 알아낼 수 있어야 한다 — 컴파일 설정에 달렸다(확인 필요) |
| `String.replace` 가 모든 일치를 바꾼다 | Java 표준 라이브러리 |
| 한 파일에 `public` 최상위 클래스는 하나 | Java 언어 규칙 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 특정 자원 하나를 가리킴 (`/users/123`) | `@PathVariable` | 쿼리로 `?id=123` 만 두기 |
| 검색 · 정렬 · 필터 몇 개 | `@RequestParam` (+ `required=false` · `defaultValue`) | `@RequestBody` |
| 검색 조건이 많음 | `@ModelAttribute` 조건 객체 | `@RequestParam` 열 줄 |
| 같은 이름의 값 여럿 (`?ids=1&ids=2`) | `@RequestParam List<Long>` | 쉼표로 직접 쪼개기 |
| 생성 · 수정 데이터 통째로 | `@Valid @RequestBody` | GET 요청 |
| 인증 토큰 · 언어 | `@RequestHeader` | 쿼리에 토큰 싣기 |
| 테마 · 세션 식별자 | `@CookieValue` | — |

## 핵심 문장

1. **어노테이션이 「요청의 어디서 꺼낼지」를 정한다** — 경로 · 쿼리 · 본문 · 헤더 · 쿠키마다 하나씩.
2. **`@RequestParam` 은 기본이 필수다** — 선택이면 `required = false`, 빈자리 값은 `defaultValue`.
3. **이름이 다르면 어노테이션에 요청 쪽 이름을 적는다** — `@PathVariable("orderId") Long id`.
4. **본문은 POST · PUT 의 몫이다** — GET 조건은 경로와 쿼리로, 많으면 `@ModelAttribute` 객체로.
5. **요청 값은 문자열이고, 매개변수 타입으로 바뀌어 들어간다** — 안 온 값은 기본값 또는 `null`.

## 관련 자료

- `spring-rest-controller` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `spring-validation` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `spring-exception-handler` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/spring-essentials.json` 의 `spring-request-params`

## 용어 풀이

- **바인딩** — 요청 데이터를 매개변수나 객체 필드에 타입을 맞춰 채우는 일.
- **경로 변수** — 매핑 경로의 `{이름}` 자리에 들어오는 URL 조각.
- **쿼리 파라미터** — URL 의 `?` 뒤에 `이름=값&…` 꼴로 붙는 값.
- **요청 본문** — 헤더 뒤에 실려 오는 데이터, POST · PUT 의 JSON 이 여기 실린다.
- **헤더** — 요청 전체에 붙는 이름-값 부가 정보(`Authorization` · `Accept-Language` 등).
- **쿠키** — 브라우저가 저장했다가 요청마다 실어 보내는 작은 이름-값.
- **역직렬화** — JSON 같은 텍스트를 객체로 되돌리는 일.
- **`@RestController`** — 반환 객체를 JSON 응답으로 보내는 컨트롤러 표시.
- **`@RequestMapping`** — 경로 매핑, 클래스 위에 두면 공통 접두 경로.
- **`@GetMapping` · `@PostMapping`** — GET · POST 요청에 메서드를 잇는 매핑.
- **`ResponseEntity`** — 상태 코드 · 헤더 · 본문을 담은 응답 객체.
- **`required`** — 값이 꼭 있어야 하는지, `@RequestParam` 에서 기본 `true`.
- **`defaultValue`** — 값이 없을 때 대신 쓸 문자열.
- **`@Valid`** — 바인딩된 객체의 검증을 실행하라는 표시.
- **`@ModelAttribute`** — 쿼리 · 폼 파라미터를 객체 필드에 채우는 표시.
- **setter** — 필드 값을 바꾸는 `setXxx` 메서드.
- **DTO** — 요청 · 응답 데이터를 나르는 용도의 객체(`CreateOrderRequest` 등).

## 더 들어가면

- `defaultValue` 를 주면 `required` 가 사실상 `false` 로 취급된다 — 원본의 `sort` 가 `required = false` 없이 `defaultValue` 만 둔 것도 그래서 동작한다(확인 필요).
- 필수 `@RequestParam` 이 빠지면 보통 400 Bad Request 로 응답한다(확인 필요).
- `@RequestParam Map<String, String>` 은 같은 이름이 여러 번 오면 값 하나만 담는다; 전부 받으려면 `MultiValueMap` 을 쓴다(확인 필요).
- 기본형 `int` 에 `required = false` 만 주고 기본값이 없으면, 값이 없을 때 `null` 을 넣을 수 없어 오류가 난다(확인 필요).
- 어노테이션의 이름 생략은 컴파일 때 매개변수 이름을 남기는 설정(`-parameters`)에 기대며, 최근 Spring 버전에서는 이 설정이 없으면 실패한다(버전 범위 확인 필요).
- `@ModelAttribute` 는 setter 말고 생성자로도 채울 수 있다 — 원본 주석의 「setter 필요」는 기본 생성자 + setter 꼴일 때의 이야기다(확인 필요).
- `@ModelAttribute` 는 단순 타입이 아닌 매개변수에서 생략해도 기본으로 적용된다(확인 필요).
- 헤더 이름은 HTTP 규칙상 대소문자를 가리지 않는다(확인 필요).
- `@Valid` 검증이 실패하면 `MethodArgumentNotValidException` 이 나고 기본 응답은 400 이다(확인 필요).
