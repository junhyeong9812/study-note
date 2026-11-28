# java/java-spring/07 — 요청 파라미터 바인딩 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 경로 변수 두 개를 다른 이름으로 받으면 (예측)

```java
// 질문용 발췌 — 클래스에 @RequestMapping("/api/v1")
@GetMapping("/users/{userId}/orders/{orderId}")
public ResponseEntity<OrderResponse> getOrder(
        @PathVariable Long userId,
        @PathVariable("orderId") Long id) { ... }
```

- `GET /api/v1/users/123/orders/456` 을 보내면 `userId` 와 `id` 에는 각각 무엇이 들어가나?

### 2. 쿼리에 `category` 하나만 보내면 (예측)

```java
// 질문용 발췌
@GetMapping("/products")
public ResponseEntity<List<ProductResponse>> searchProducts(
        @RequestParam String category,
        @RequestParam(required = false, defaultValue = "0") int minPrice,
        @RequestParam(required = false, defaultValue = "999999") int maxPrice,
        @RequestParam(defaultValue = "name,asc") String sort) { ... }
```

- `GET /api/v1/products?category=electronics` 를 보내면 네 매개변수의 값은 각각 무엇인가?

### 3. 같은 메서드에 `category` 없이 요청하면 (예측)

- 2번의 `searchProducts` 에 `GET /api/v1/products?minPrice=1000` 을 보내면 메서드 본문까지 갈 수 있나?

### 4. 경로 변수 이름을 괄호 안에 적어야 하는 때가 있는 까닭 (왜)

- `@PathVariable Long userId` 는 이름을 생략하는데, `@PathVariable("orderId") Long id` 는 왜 이름을 적었나?

### 5. GET 요청에 `@RequestBody` 를 쓰지 않는 까닭 (왜)

- 검색 조건을 GET 으로 받을 때 왜 `@RequestBody` 대신 다른 어노테이션을 쓰나?

### 6. 쿠키가 하나도 없는 요청 (경계)

- `@CookieValue(value = "theme", defaultValue = "light")` 와 `@CookieValue(value = "sessionId", required = false)` 는 쿠키가 없을 때 어떻게 다르게 채워지나?

### 7. 쿼리 일부만 보낸 `@ModelAttribute` (예측)

```java
// 질문용 발췌 — MemberSearchCondition 에는 name, age(Integer), city 필드와 getter/setter 가 있다
@GetMapping("/members")
public ResponseEntity<List<MemberResponse>> searchMembers(
        @ModelAttribute MemberSearchCondition condition) { ... }
```

- `GET /api/v1/members?name=Kim&age=25` 를 보내면 `condition` 의 세 필드는 각각 무엇인가?

### 8. 쿼리 파라미터를 받는 세 가지 꼴 (연결)

- 같은 쿼리 문자열을 `@RequestParam` 낱개 · `@RequestParam List`/`Map` · `@ModelAttribute` 객체로 받는 방법은 각각 어떤 상황에 맞나?

### 9. 헤더 · 쿠키 바인딩과 쿼리 바인딩의 닮은 점 (연결)

- `@RequestHeader` 와 `@CookieValue` 의 속성 쓰임새는 `@RequestParam` 의 어떤 속성과 같은 구조인가?

## 실습

### 실습 1. 여섯 가지 바인딩을 모은 컨트롤러 만들기

**만들 것** — `/api/v1` 아래에 경로 · 쿼리 · 본문 · 헤더 · 쿠키 · 조건 객체로 요청 데이터를 받는 Spring 컨트롤러와 검색 조건 객체를 만든다.

**준비물** — Spring Web(`spring-boot-starter-web`)이 필요하다.
`@Valid` 를 쓰려면 Bean Validation 의존성과 `jakarta.validation.Valid` 임포트가 필요하다.
정답 코드는 서비스 필드(`orderService` 등)와 DTO(`OrderResponse` · `CreateOrderRequest` · `ProductResponse` · `SearchResult` · `UserProfile` · `Preferences` · `MemberResponse`)가 이미 있다고 가정한다 — 돌려 보려면 빈 스텁을 직접 만든다.

**요구 조건**

1단계 — 컨트롤러 뼈대
1. `ParameterBindingController` 를 JSON 응답 컨트롤러로 만들고, 모든 경로 앞에 `/api/v1` 이 붙게 한다.

2단계 — 경로 변수
2. `GET /users/{userId}/orders/{orderId}` 를 `getOrder` 에 잇는다.
3. `userId` 는 같은 이름의 매개변수로, `orderId` 는 이름이 다른 매개변수 `id` 로 받아 `orderService.getOrder(userId, id)` 결과를 200 으로 돌려준다.

3단계 — 쿼리 파라미터
4. `GET /products` 의 `searchProducts` 는 `category` 를 필수로 받는다.
5. `minPrice` · `maxPrice` 는 선택이며, 없으면 각각 `0` · `999999` 가 된다.
6. `sort` 는 없으면 `"name,asc"` 가 된다.
7. `GET /products/filter` 의 `filterByIds` 는 `?ids=1&ids=2&ids=3` 처럼 반복된 값을 `List<Long>` 으로 받는다.
8. `GET /search` 의 `search` 는 모든 쿼리 파라미터를 `Map<String, String>` 으로 받는다.

4단계 — 본문
9. `POST /orders` 의 `createOrder` 는 JSON 본문을 `CreateOrderRequest` 로 받고, 검증을 실행한 뒤 `orderService.create(request)` 결과를 돌려준다.

5단계 — 헤더 · 쿠키
10. `GET /profile` 의 `getProfile` 은 `Authorization` 헤더를 필수로, `Accept-Language` 헤더를 기본값 `"ko"` 로, 그리고 모든 헤더를 `Map` 으로 받는다.
11. `Authorization` 값에서 `"Bearer "` 를 지운 토큰과 언어를 `userService.getProfile` 에 넘긴다.
12. `GET /preferences` 의 `getPreferences` 는 `theme` 쿠키를 기본값 `"light"` 로, `sessionId` 쿠키를 선택으로 받아 `new Preferences(theme, sessionId)` 를 돌려준다.

6단계 — 조건 객체
13. `GET /members` 의 `searchMembers` 는 `name` · `age` · `city` 쿼리 파라미터를 `MemberSearchCondition` 객체 하나로 받는다.
14. `MemberSearchCondition` 에 `String name` · `Integer age` · `String city` 필드와 각각의 getter · setter 를 둔다.

**시작 코드**

```java
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;

import java.util.List;
import java.util.Map;

// TODO: JSON 응답 컨트롤러 표시
// TODO: 공통 경로 /api/v1
public class ParameterBindingController {

    // TODO: GET /users/{userId}/orders/{orderId} 매핑
    public ResponseEntity<OrderResponse> getOrder(
            /* TODO: userId 경로 변수 */ Long userId,
            /* TODO: orderId 경로 변수를 id 로 */ Long id) {
        return ResponseEntity.ok(orderService.getOrder(userId, id));
    }

    // TODO: GET /products 매핑
    public ResponseEntity<List<ProductResponse>> searchProducts(
            /* TODO: 필수 */ String category,
            /* TODO: 선택, 기본 0 */ int minPrice,
            /* TODO: 선택, 기본 999999 */ int maxPrice,
            /* TODO: 기본 name,asc */ String sort) {
        return ResponseEntity.ok(
            productService.search(category, minPrice, maxPrice, sort));
    }

    // TODO: GET /products/filter 매핑
    public ResponseEntity<List<ProductResponse>> filterByIds(
            /* TODO: 반복된 ids */ List<Long> ids) {
        return ResponseEntity.ok(productService.findByIds(ids));
    }

    // TODO: GET /search 매핑
    public ResponseEntity<SearchResult> search(
            /* TODO: 모든 쿼리 파라미터 */ Map<String, String> allParams) {
        return ResponseEntity.ok(searchService.search(allParams));
    }

    // TODO: POST /orders 매핑
    public ResponseEntity<OrderResponse> createOrder(
            /* TODO: 검증 + JSON 본문 */ CreateOrderRequest request) {
        return ResponseEntity.ok(orderService.create(request));
    }

    // TODO: GET /profile 매핑
    public ResponseEntity<UserProfile> getProfile(
            /* TODO: Authorization 헤더 */ String authHeader,
            /* TODO: Accept-Language 헤더, 기본 ko */ String lang,
            /* TODO: 모든 헤더 */ Map<String, String> allHeaders) {
        String token = /* TODO: Bearer 접두사 제거 */ null;
        return ResponseEntity.ok(userService.getProfile(token, lang));
    }

    // TODO: GET /preferences 매핑
    public ResponseEntity<Preferences> getPreferences(
            /* TODO: theme 쿠키, 기본 light */ String theme,
            /* TODO: sessionId 쿠키, 선택 */ String sessionId) {
        return ResponseEntity.ok(new Preferences(theme, sessionId));
    }

    // TODO: GET /members 매핑
    public ResponseEntity<List<MemberResponse>> searchMembers(
            /* TODO: 쿼리 파라미터를 객체로 */ MemberSearchCondition condition) {
        return ResponseEntity.ok(memberService.search(condition));
    }
}

public class MemberSearchCondition {
    // TODO: name, age(Integer), city 필드
    // TODO: 각 필드의 getter, setter
}
```

**확인 방법** — 두 클래스를 각자 파일로 나누고 스텁을 채워 Spring Boot 앱으로 띄운 뒤, 요청을 보내 서비스에 넘어간 값을 로그나 디버거로 본다.

```bash
curl "http://localhost:8080/api/v1/users/123/orders/456"
curl "http://localhost:8080/api/v1/products?category=electronics"
curl "http://localhost:8080/api/v1/products/filter?ids=1&ids=2&ids=3"
curl -H "Authorization: Bearer abc123" "http://localhost:8080/api/v1/profile"
curl "http://localhost:8080/api/v1/preferences"
curl "http://localhost:8080/api/v1/members?name=Kim&age=25&city=Seoul"
curl -X POST -H "Content-Type: application/json" -d "{}" "http://localhost:8080/api/v1/orders"
```

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
