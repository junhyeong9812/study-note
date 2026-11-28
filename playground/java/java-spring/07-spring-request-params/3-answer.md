# java/java-spring/07 — 요청 파라미터 바인딩 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `userId` = 123, `id` = 456

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`userId` 에는 `123L`, `id` 에는 `456L` 이 들어간다.

**왜 그런가**
클래스의 `/api/v1` 과 메서드의 `/users/{userId}/orders/{orderId}` 가 이어져 요청 경로와 맞물린다.
`{userId}` 자리의 `"123"` 은 같은 이름의 매개변수 `userId` 로 간다.
`{orderId}` 자리의 `"456"` 은 `@PathVariable("orderId")` 가 가리키는 매개변수 `id` 로 간다.
두 문자열은 매개변수 타입 `Long` 으로 바뀐다.
근거: 2-summary 「동작 방식 (1)」.

### 2. `category`="electronics", `minPrice`=0, `maxPrice`=999999, `sort`="name,asc"

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `category` → `"electronics"`
- `minPrice` → `0`
- `maxPrice` → `999999`
- `sort` → `"name,asc"`

**왜 그런가**
요청에 실린 값은 `category` 하나뿐이다.
나머지 셋은 요청에 없으므로 각자의 `defaultValue` 문자열이 들어가고, `int` 인 둘은 정수로 바뀐다.
근거: 2-summary 「동작 방식 (2)」.

### 3. 갈 수 없다 — `category` 가 필수라서 바인딩이 실패한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`@RequestParam String category` 에는 `required` 를 적지 않았으므로 기본값 `true` 로 필수다.
요청에 `category` 가 없으므로 바인딩이 실패하고 메서드 본문은 실행되지 않는다.
응답이 400 인지는 정리 본문 밖의 세부다(확인 필요).

**왜 그런가**
`@RequestParam` 의 `required` 기본값이 `true` 이기 때문이다 — 원본 팁이 바로 이 점을 짚는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 4. 매개변수 이름(`id`)이 경로 변수 이름(`orderId`)과 달라서다

`@PathVariable` 은 이름을 생략하면 매개변수 이름과 같은 경로 변수를 찾는다.
`userId` 는 두 이름이 같으니 생략해도 된다.
`id` 는 경로의 `{orderId}` 와 이름이 다르므로, 어노테이션에 `"orderId"` 를 적어 둘을 잇는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 4」.

### 5. 본문은 POST · PUT 의 몫이고, GET 의 조건은 경로와 쿼리로 오기 때문이다

원본 팁은 `@RequestBody` 를 POST · PUT 의 JSON 바디에 쓰고 GET 에는 쓰지 않는다고 한다.
GET 은 조건을 URL 에 실어 보내므로 `@PathVariable` · `@RequestParam` 으로 받는다.
조건이 많으면 `@ModelAttribute` 로 객체 하나에 받는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」 · 「언제 쓰고 언제 안 쓰나」.

### 6. `theme` 은 `"light"`, `sessionId` 는 `null`

`theme` 은 `defaultValue = "light"` 가 있으므로 쿠키가 없으면 `"light"` 가 들어간다.
`sessionId` 는 `required = false` 만 있고 기본값이 없으므로 `null` 이 들어간다.
둘 다 쿠키가 없어도 요청은 실패하지 않는다.
근거: 2-summary 「동작 방식 (5)」.

### 7. `name`="Kim", `age`=25, `city`=null

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `name` → `"Kim"`
- `age` → `25` (`Integer`)
- `city` → `null`

**왜 그런가**
`@ModelAttribute` 는 파라미터 이름과 맞는 필드를 setter 로 채운다.
`city` 는 요청에 없으므로 setter 가 불리지 않고, 참조 타입의 처음 값 `null` 로 남는다.
`age` 의 `"25"` 는 `Integer` 로 바뀐다.
근거: 2-summary 「동작 방식 (6)」.

### 8. 개수와 구조에 따라 고른다

- `@RequestParam` 낱개 — 몇 개 안 되는 검색 · 정렬 값을 이름마다 필수 · 기본값을 정해 받을 때.
- `@RequestParam List<T>` — 같은 이름이 여러 번 올 때(`?ids=1&ids=2&ids=3`).
- `@RequestParam Map<String,String>` — 어떤 이름이 올지 정해 두지 않고 전부 받을 때.
- `@ModelAttribute` 객체 — 조건이 많아 메서드 서명이 길어질 때, 필드로 묶어 받는다.

근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (6)」 · 「언제 쓰고 언제 안 쓰나」.

### 9. `value` 로 이름, `defaultValue` 로 기본값, `required` 로 선택 여부를 정하는 구조가 같다

`@RequestHeader(value = "Accept-Language", defaultValue = "ko")` 는 `@RequestParam(required = false, defaultValue = "0")` 과 같은 꼴로 「없을 때의 값」을 정한다.
`@CookieValue(value = "sessionId", required = false)` 도 `required` 로 선택을 표시한다.
`@RequestHeader Map<String,String>` 은 `@RequestParam Map` 처럼 전부를 모은다.
꺼내는 곳(쿼리 · 헤더 · 쿠키)만 다르고 속성의 쓰임새는 같다.
근거: 2-summary 「동작 방식 (2)」 · 「(4)」 · 「(5)」 · 「문법 — 형태와 규칙」 표.

## 실습 정답

### 실습 1. 여섯 가지 바인딩을 모은 컨트롤러 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. JSON 응답 컨트롤러 · `/api/v1` 접두 | `@RestController` · `@RequestMapping("/api/v1")` |
| 2. `getOrder` 경로 매핑 | `@GetMapping("/users/{userId}/orders/{orderId}")` |
| 3. 같은 이름 · 다른 이름 경로 변수 | `@PathVariable Long userId` · `@PathVariable("orderId") Long id` |
| 4. `category` 필수 | `@RequestParam String category` |
| 5. `minPrice` · `maxPrice` 선택 + 기본값 | `@RequestParam(required = false, defaultValue = "0")` · `defaultValue = "999999"` |
| 6. `sort` 기본값 | `@RequestParam(defaultValue = "name,asc") String sort` |
| 7. 반복 값을 리스트로 | `filterByIds` 의 `@RequestParam List<Long> ids` |
| 8. 모든 쿼리를 맵으로 | `search` 의 `@RequestParam Map<String, String> allParams` |
| 9. JSON 본문 + 검증 | `@PostMapping("/orders")` · `@Valid @RequestBody CreateOrderRequest request` |
| 10. 헤더 필수 · 기본값 · 전부 | `@RequestHeader("Authorization")` · `@RequestHeader(value = "Accept-Language", defaultValue = "ko")` · `@RequestHeader Map<String, String> allHeaders` |
| 11. 토큰 꺼내 넘기기 | `authHeader.replace("Bearer ", "")` · `userService.getProfile(token, lang)` |
| 12. 쿠키 기본값 · 선택 | `@CookieValue(value = "theme", defaultValue = "light")` · `@CookieValue(value = "sessionId", required = false)` |
| 13. 조건 객체로 받기 | `@GetMapping("/members")` · `@ModelAttribute MemberSearchCondition condition` |
| 14. 필드 · getter · setter | `MemberSearchCondition` 의 `name` · `age` · `city` 와 `getXxx` · `setXxx` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-spring/reference/spring-request-params.java`

```java
// [Spring 핵심] 요청 파라미터 바인딩
// 설명: @PathVariable, @RequestParam, @RequestBody, @RequestHeader 등을 사용한 HTTP 요청 데이터 바인딩
// 팁: @RequestParam의 required 기본값은 true이므로, 선택적 파라미터는 required = false를 명시한다. @ModelAttribute는 쿼리 파라미터가 많을 때 객체로 깔끔하게 받을 수 있다. @RequestBody는 POST/PUT의 JSON 바디에 사용하고, GET 요청에는 사용하지 않는다.

// 웹 바인딩 어노테이션 일괄 임포트 (@RestController, @PathVariable 등)
import org.springframework.web.bind.annotation.*;
// ResponseEntity: HTTP 응답 표현
import org.springframework.http.ResponseEntity;

// 리스트 컬렉션
import java.util.List;
// 키-값 자료구조
import java.util.Map;

// @RestController: 컨트롤러 + JSON 응답 자동 변환
@RestController
// @RequestMapping("/api/v1"): 클래스 레벨 공통 경로 prefix
@RequestMapping("/api/v1")
public class ParameterBindingController {

    // === 1. @PathVariable - URL 경로의 변수 ===
    // GET /api/v1/users/123/orders/456
    // @GetMapping: GET 요청 매핑 + 경로의 {} 변수
    @GetMapping("/users/{userId}/orders/{orderId}")
    public ResponseEntity<OrderResponse> getOrder(
            // @PathVariable: URL 경로 변수 바인딩 (이름 동일하면 생략 가능)
            @PathVariable Long userId,
            // 변수명을 명시적으로 매핑 (path의 orderId → 파라미터 id)
            @PathVariable("orderId") Long id) {  // 변수명이 다를 때 명시
        // 서비스 호출 후 200 OK
        return ResponseEntity.ok(orderService.getOrder(userId, id));
    }

    // === 2. @RequestParam - 쿼리 파라미터 ===
    // GET /api/v1/products?category=electronics&minPrice=1000&sort=price,desc
    @GetMapping("/products")
    public ResponseEntity<List<ProductResponse>> searchProducts(
            // @RequestParam: 쿼리 파라미터 바인딩 (기본 required=true)
            @RequestParam String category,
            // required=false + 기본값 지정 (선택 파라미터)
            @RequestParam(required = false, defaultValue = "0") int minPrice,
            // 최대값 기본값 999999
            @RequestParam(required = false, defaultValue = "999999") int maxPrice,
            // 정렬 옵션, 기본 name,asc
            @RequestParam(defaultValue = "name,asc") String sort) {
        // 검색 결과 응답
        return ResponseEntity.ok(
            productService.search(category, minPrice, maxPrice, sort));
    }

    // 여러 값 받기: GET /api/v1/products/filter?ids=1&ids=2&ids=3
    @GetMapping("/products/filter")
    public ResponseEntity<List<ProductResponse>> filterByIds(
            // List로 받으면 같은 이름의 파라미터 여러 값을 모음
            @RequestParam List<Long> ids) {
        return ResponseEntity.ok(productService.findByIds(ids));
    }

    // Map으로 모든 파라미터 받기
    @GetMapping("/search")
    public ResponseEntity<SearchResult> search(
            // Map<String,String>: 모든 쿼리 파라미터 키-값으로 수집
            @RequestParam Map<String, String> allParams) {
        return ResponseEntity.ok(searchService.search(allParams));
    }

    // === 3. @RequestBody - JSON 요청 본문 ===
    // POST /api/v1/orders
    @PostMapping("/orders")
    public ResponseEntity<OrderResponse> createOrder(
            // @Valid: 검증 트리거, @RequestBody: JSON 본문을 객체로 역직렬화
            @Valid @RequestBody CreateOrderRequest request) {
        return ResponseEntity.ok(orderService.create(request));
    }

    // === 4. @RequestHeader - HTTP 헤더 ===
    @GetMapping("/profile")
    public ResponseEntity<UserProfile> getProfile(
            // @RequestHeader("Authorization"): 특정 헤더 값 추출
            @RequestHeader("Authorization") String authHeader,
            // 헤더 + 기본값 지정
            @RequestHeader(value = "Accept-Language", defaultValue = "ko") String lang,
            // 모든 헤더를 Map으로 받기
            @RequestHeader Map<String, String> allHeaders) {
        // Bearer 접두사 제거
        String token = authHeader.replace("Bearer ", "");
        return ResponseEntity.ok(userService.getProfile(token, lang));
    }

    // === 5. @CookieValue - 쿠키 값 ===
    @GetMapping("/preferences")
    public ResponseEntity<Preferences> getPreferences(
            // @CookieValue: 쿠키 값 추출 + 기본값
            @CookieValue(value = "theme", defaultValue = "light") String theme,
            // 선택 쿠키
            @CookieValue(value = "sessionId", required = false) String sessionId) {
        return ResponseEntity.ok(new Preferences(theme, sessionId));
    }

    // === 6. @ModelAttribute - 폼 데이터 또는 쿼리 파라미터를 객체로 바인딩 ===
    // GET /api/v1/members?name=Kim&age=25&city=Seoul
    @GetMapping("/members")
    public ResponseEntity<List<MemberResponse>> searchMembers(
            // @ModelAttribute: 쿼리 파라미터들을 객체 필드에 setter로 바인딩
            @ModelAttribute MemberSearchCondition condition) {
        // MemberSearchCondition의 필드(name, age, city)에 자동 바인딩
        // 검색 실행
        return ResponseEntity.ok(memberService.search(condition));
    }
}

// @ModelAttribute용 조건 객체
// 폼/쿼리 파라미터 바인딩 대상 객체 (setter 필요)
public class MemberSearchCondition {
    // 검색 필드들
    private String name;
    private Integer age;
    private String city;

    // getter, setter 필요 (또는 Lombok @Data)
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Integer getAge() { return age; }
    public void setAge(Integer age) { this.age = age; }
    public String getCity() { return city; }
    public void setCity(String city) { this.city = city; }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 요청의 어느 부분에서 꺼내느냐에 따라 어노테이션 하나를 고른다 — 경로 · 쿼리 · 본문 · 헤더 · 쿠키 · 조건 객체.
- `@RequestParam` 은 기본이 필수라서, 선택 값에는 `required = false` 와 `defaultValue` 를 붙인다.
- 경로 변수와 매개변수 이름이 다를 때만 `@PathVariable("orderId")` 처럼 이름을 적는다.
- `@ModelAttribute` 조건 객체는 setter 가 있어야 원본 주석대로 채워진다.
- 정답 코드는 `@Valid` 임포트 · 서비스 필드 · DTO 가 빠져 있고 `public` 클래스 둘이 한 파일에 있으므로, 돌리려면 파일을 나누고 스텁을 보태야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
