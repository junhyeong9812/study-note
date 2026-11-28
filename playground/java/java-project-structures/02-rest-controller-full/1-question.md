# java/java-project-structures/02 — REST API 전체 구조 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 이름도 비고 가격도 음수인 생성 요청 (예측)

```java
// 질문용 발췌
ProductController c = new ProductController(new ProductService());
System.out.println(c.createProduct(new ProductRequest("", -1000)));
```

- 찍히는 한 줄의 `success` · `status` · `message` · `data` 는 각각 무엇인가?
- 메시지가 두 개 실리는가, 하나만 실리는가?

### 2. 실패한 생성 다음의 생성 (예측)

```java
// 질문용 발췌
ProductController c = new ProductController(new ProductService());
c.createProduct(new ProductRequest("", 100));
System.out.println(c.createProduct(new ProductRequest("키보드", 50000)));
```

- 「키보드」가 받는 `id` 는 몇인가?
- 이 줄의 `status` 와 `message` 는 무엇인가?

### 3. 노트북과 마우스를 만든 뒤 1번을 지우면 (예측)

```java
// 질문용 발췌
System.out.println(controller.deleteProduct(1L));
System.out.println(controller.getAllProducts());
```

- 첫 줄의 `message` 칸과 `data` 칸에는 각각 무엇이 들어가는가?
- 둘째 줄의 `data` 에는 무엇이 남는가?

### 4. `ApiResponse` 의 생성자를 막아 두는 까닭 (왜)

- 생성자를 `private` 으로 두고 `ok` · `created` · `error` 로만 응답을 만들게 하면 무엇을 막을 수 있는가?

### 5. 예외가 상태 코드를 들고 다니는 까닭 (왜)

- `BusinessException` 이 `status` 필드를 가지면 Controller 의 `catch` 블록은 어떻게 단순해지는가?
- `RuntimeException` 을 상속하는 것은 계층 사이에서 무엇을 덜어 주는가?

### 6. Controller 의 `catch` 가 놓치는 실패 (경계)

- `createProduct(null)` 처럼 `BusinessException` 이 아닌 예외가 나면 응답은 어떻게 되는가?

### 7. 같은 키로 두 번 `put` 하는 줄 (경계)

- `store.put` 첫 줄을 지우면 프로그램의 동작은 달라지는가?

### 8. 요청 DTO 와 응답 DTO 를 나누는 것 (연결)

- `ProductRequest` 와 `ProductDto` 는 각각 어느 쪽 데이터를 싣고, 왜 둘을 한 클래스로 합치지 않는가?

### 9. 되풀이되는 try-catch 와 `@ControllerAdvice` (연결)

- 이 데모의 try-catch 패턴은 Spring 의 `@ControllerAdvice` 와 어떤 관계인가?

## 실습

### 실습 1. 상품 REST API 의 전체 구조 만들기

**만들 것** — 상품을 생성 · 조회 · 목록 조회 · 삭제하는 REST API 를 Controller → Service → `ApiResponse` 래핑 → 예외 처리 구조로 만든다.
HTTP 서버 없이 `main` 에서 Controller 메서드를 직접 불러 응답을 콘솔에 찍는다.

**준비물** — JDK 만 있으면 된다. 외부 라이브러리는 쓰지 않는다. `ProductController` 는 Spring 의 REST 컨트롤러를 흉내 낸 평범한 클래스다.

**요구 조건**

1단계 — 표준 응답 `ApiResponse<T>`
1. 다섯 `final` 필드(`success` · `data` · `message` · `status` · `timestamp`)를 채우는 `private` 생성자를 만든다. `timestamp` 는 만드는 순간의 `LocalDateTime.now().toString()` 이다.
2. `ok(data)` 는 성공 · "성공" · 200 응답을 돌려준다.
3. `created(data)` 는 성공 · "생성 완료" · 201 응답을 돌려준다.
4. `error(message, status)` 는 실패 응답을 돌려주고 `data` 는 `null` 이다.

2단계 — 예외 계층
5. `BusinessException` 은 `RuntimeException` 을 상속하고, 메시지는 부모에게 넘기며 상태 코드는 자기 필드에 담아 `getStatus()` 로 내준다.
6. `NotFoundException(resource, id)` 는 `<resource>을(를) 찾을 수 없습니다: id=<id>` 메시지와 404 를 쓴다.
7. `DuplicateException(field, value)` 는 `<field> 중복: <value>` 메시지와 409 를 쓴다.

3단계 — 요청 DTO 검증
8. `ProductRequest.validate()` 는 이름이 `null` 이거나 공백뿐이면 "상품명은 필수입니다"(400)를 던진다.
9. 이름이 괜찮을 때 가격이 음수면 "가격은 0 이상이어야 합니다"(400)를 던진다.

4단계 — Service
10. `create` 는 먼저 요청을 검증하고, 계수기를 하나 올려 그 값을 `id` 로 하는 `ProductDto` 를 만들어 `store` 에 그 `id` 로 넣고 돌려준다.
11. `findById` 는 없는 `id` 면 `NotFoundException("상품", id)` 를 던진다.
12. `findAll` 은 저장된 값들을 새 `ArrayList` 에 담아 돌려준다.
13. `delete` 는 없는 `id` 면 `NotFoundException` 을 던지고, 있으면 지운다.

5단계 — Controller
14. `createProduct` 는 성공하면 201 응답을, `BusinessException` 이 나면 그 메시지와 상태 코드로 만든 실패 응답을 돌려준다.
15. `getProduct` 는 성공하면 200 응답을, `BusinessException` 이 나면 실패 응답을 돌려준다.
16. `getAllProducts` 는 목록을 200 응답으로 돌려준다(예외 처리 없음).
17. `deleteProduct` 는 성공하면 `data` 에 "삭제 완료" 를 담은 200 응답을, `BusinessException` 이 나면 실패 응답을 돌려준다.

6단계 — 시나리오
18. `main` 은 생성 두 번 → 검증 실패 → 단건 · 목록 조회 → 없는 상품 조회 → 삭제와 목록 조회를 차례로 부르고 각 응답을 찍는다(시작 코드에 이미 있다).

**시작 코드**

```java
import java.util.*;
import java.time.LocalDateTime;

class ApiResponse<T> {
    private final boolean success;
    private final T data;
    private final String message;
    private final int status;
    private final String timestamp;

    // TODO: 다섯 필드를 채우는 private 생성자 (timestamp 는 지금 시각)

    // TODO: public static <T> ApiResponse<T> ok(T data)
    // TODO: public static <T> ApiResponse<T> created(T data)
    // TODO: public static <T> ApiResponse<T> error(String message, int status)

    @Override
    public String toString() {
        return String.format("{success=%s, status=%d, message='%s', data=%s}",
            success, status, message, data);
    }
}

// TODO: class BusinessException — RuntimeException 상속, status 필드, getStatus()
// TODO: class NotFoundException — 404
// TODO: class DuplicateException — 409

class ProductRequest {
    private final String name;
    private final int price;

    public ProductRequest(String name, int price) {
        this.name = name;
        this.price = price;
    }

    public String getName() { return name; }
    public int getPrice() { return price; }

    public void validate() {
        // TODO: 이름 검사 → 가격 검사 (차례대로)
    }
}

class ProductDto {
    private final Long id;
    private final String name;
    private final int price;

    public ProductDto(Long id, String name, int price) {
        this.id = id;
        this.name = name;
        this.price = price;
    }

    @Override
    public String toString() {
        return String.format("Product{id=%d, name='%s', price=%d}", id, name, price);
    }
}

class ProductService {
    private final Map<Long, ProductDto> store = new HashMap<>();
    private long sequence = 0L;

    public ProductDto create(ProductRequest request) {
        // TODO: 검증 → id 발급 → 저장 → 반환
        return null;
    }

    public ProductDto findById(Long id) {
        // TODO: 없으면 NotFoundException
        return null;
    }

    public List<ProductDto> findAll() {
        // TODO: 복사본 목록
        return null;
    }

    public void delete(Long id) {
        // TODO: 없으면 NotFoundException, 있으면 삭제
    }
}

class ProductController {
    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    // POST /api/products
    public ApiResponse<?> createProduct(ProductRequest request) {
        // TODO: 성공 → 201, BusinessException → error
        return null;
    }

    // GET /api/products/{id}
    public ApiResponse<?> getProduct(Long id) {
        // TODO: 성공 → 200, BusinessException → error
        return null;
    }

    // GET /api/products
    public ApiResponse<?> getAllProducts() {
        // TODO: 목록 → 200
        return null;
    }

    // DELETE /api/products/{id}
    public ApiResponse<?> deleteProduct(Long id) {
        // TODO: 성공 → 200 ("삭제 완료"), BusinessException → error
        return null;
    }
}

public class RestControllerDemo {
    public static void main(String[] args) {
        ProductController controller = new ProductController(new ProductService());

        System.out.println("=== 상품 생성 ===");
        System.out.println(controller.createProduct(new ProductRequest("노트북", 1500000)));
        System.out.println(controller.createProduct(new ProductRequest("마우스", 35000)));

        System.out.println("\n=== 유효성 검증 실패 ===");
        System.out.println(controller.createProduct(new ProductRequest("", -1000)));

        System.out.println("\n=== 상품 조회 ===");
        System.out.println(controller.getProduct(1L));
        System.out.println(controller.getAllProducts());

        System.out.println("\n=== 없는 상품 조회 ===");
        System.out.println(controller.getProduct(99L));

        System.out.println("\n=== 상품 삭제 ===");
        System.out.println(controller.deleteProduct(1L));
        System.out.println(controller.getAllProducts());
    }
}
```

**확인 방법** — `javac RestControllerDemo.java && java RestControllerDemo` 로 돌린다.
각 줄의 `status` 가 차례로 201 · 201 · 400 · 200 · 200 · 404 · 200 · 200 인지 본다.
검증 실패 줄에는 이름 메시지 하나만 있고, 마지막 목록에는 마우스만 남았는지도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
