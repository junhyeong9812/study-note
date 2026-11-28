# java/java-project-structures/02 — REST API 전체 구조 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 400 실패 응답이고, 이름 쪽 메시지 하나만 실린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
{success=false, status=400, message='상품명은 필수입니다', data=null}
```

메시지는 하나만 실린다.

**왜 그런가**

- `service.create` 가 맨 먼저 `request.validate()` 를 부른다.
- 이름 `""` 은 `isBlank()` 가 참이므로 첫 검사에서 `BusinessException("상품명은 필수입니다", 400)` 이 던져진다.
- 첫 검사에서 이미 던졌으므로 가격 검사는 실행되지 않는다.
- Controller 의 `catch` 가 `ApiResponse.error(e.getMessage(), e.getStatus())` 를 만든다.
- `error` 는 `data` 에 `null` 을 넣고, `%s` 는 `null` 을 `null` 이라는 글자로 찍는다.
- 근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (2)」 · 「어디서 틀리나 4」.

### 2. `id` 는 1 — 실패한 요청은 번호를 쓰지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
{success=true, status=201, message='생성 완료', data=Product{id=1, name='키보드', price=50000}}
```

**왜 그런가**

- `create` 안에서 `request.validate()` 가 `++sequence` 보다 먼저 실행된다.
- 첫 요청은 검증에서 던져졌으므로 `++sequence` 에 닿지 못했고, `sequence` 는 0 그대로다.
- 둘째 요청에서 `++sequence` 가 1 을 만들고, 그 값이 `id` 가 된다.
- 성공한 생성은 `ApiResponse.created` 로 감싸지므로 201 · "생성 완료" 다.
- 근거: 2-summary 「동작 방식 (5)」.

### 3. 「삭제 완료」는 `data` 칸에 들어가고, 목록에는 마우스만 남는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
{success=true, status=200, message='성공', data=삭제 완료}
{success=true, status=200, message='성공', data=[Product{id=2, name='마우스', price=35000}]}
```

**왜 그런가**

- `deleteProduct` 는 `ApiResponse.ok("삭제 완료")` 를 돌려준다.
- `ok` 는 `message` 를 "성공" 으로 정하고, 받은 값 "삭제 완료" 를 `data` 에 넣는다.
- `store.remove(1L)` 뒤에 남은 값은 id=2 인 마우스뿐이다.
- `findAll` 은 남은 값을 `ArrayList` 에 담아 돌려주고, 리스트의 `toString` 이 `[…]` 꼴로 찍힌다.
- 근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 6」.

### 4. 앞뒤가 안 맞는 응답 조합을 바깥에서 만들 수 없게 한다

바깥 코드는 세 정적 메서드로만 응답을 만들 수 있다.
그래서 「`success=true` 인데 `status=404`」나 「실패인데 `data` 가 있음」 같은 조합이 생기지 않는다.
메서드 이름(`ok` · `created` · `error`)이 응답의 뜻을 드러내고, `timestamp` 도 생성자 한 곳에서만 채워진다.
근거: 2-summary 「동작 방식 (2)」.

### 5. `catch` 하나로 모든 비즈니스 실패를 같은 꼴로 바꾸고, 계층마다 `throws` 를 적지 않아도 된다

예외가 상태 코드를 품고 있으므로 Controller 는 예외의 종류를 가려 분기할 필요가 없다.
`catch (BusinessException e)` 하나에서 `error(e.getMessage(), e.getStatus())` 만 부르면 400 · 404 · 409 가 저절로 맞게 나간다.
새 하위 예외를 더해도 Controller 는 고칠 필요가 없다.
`RuntimeException` 을 상속한 unchecked 예외이므로, `validate` · `findById` · `delete` 를 거쳐 올라오는 동안 메서드마다 `throws` 를 선언하지 않아도 된다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」.

### 6. 아무도 잡지 않아 `ApiResponse` 가 아닌 실패로 새어 나간다

Controller 는 `BusinessException` 계열만 잡는다.
`createProduct(null)` 이면 `null.validate()` 에서 `NullPointerException` 이 나고, 이 예외는 `catch` 에 걸리지 않는다.
예외는 핸들러 밖으로 퍼지고, 클라이언트는 표준 응답 모양을 받지 못한다.
비즈니스 예외와 시스템 예외를 나누면, 시스템 예외는 따로 다룰 자리가 필요하다는 것이 드러난다.
근거: 2-summary 「어디서 틀리나 3」 · 「동작 방식 (6)」.

### 7. 달라지지 않는다 — 같은 키에 같은 객체를 다시 넣을 뿐이다

첫 줄의 삼항 연산자는 조건이 참이어도 거짓이어도 `sequence` 를 고른다.
그래서 두 `put` 은 모두 `store.put(sequence, product)` 와 같다.
`HashMap` 에 같은 키로 다시 넣으면 값이 덮어써지는데, 이번에는 같은 값이라 결과가 바뀌지 않는다.
첫 줄을 지우면 쓸데없는 `toString` · `hashCode` 계산만 사라진다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 8. 요청 DTO 는 들어오는 입력과 그 검증을, 응답 DTO 는 서버가 만든 결과를 싣는다

`ProductRequest` 에는 클라이언트가 보낸 이름과 가격, 그리고 그 입력이 올바른지 아는 `validate()` 가 있다.
`ProductDto` 에는 서버가 발급한 `id` 가 더해진, 바깥에 내보낼 수 있는 결과가 있다.
합치면 클라이언트가 보내면 안 되는 `id` 가 입력에 섞이고, 검증 규칙과 노출 형태가 한 클래스에 엉킨다.
응답 DTO 는 다시 `ApiResponse` 의 `data` 칸에 담겨 나간다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」 · 「동작 방식 (2)」. 「합치면 생기는 문제」는 (원본에 근거 없음 — 추론).

### 9. 같은 패턴을 한 곳으로 모은 것이 `@ControllerAdvice` 다

이 데모는 핸들러마다 「`BusinessException` 을 잡아 `ApiResponse.error` 로 바꾼다」를 되풀이한다.
팁에 따르면 Spring 에서는 이 일을 `@ControllerAdvice` 로 한 곳에서 처리한다.
그러면 핸들러에서 try-catch 가 사라지고, 예외를 응답으로 바꾸는 규칙이 한 군데에만 남는다.
데모는 그 패턴을 눈에 보이게 하려고 일부러 Controller 안에 직접 썼다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. 상품 REST API 의 전체 구조 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `private` 생성자 · timestamp | `private ApiResponse(boolean success, T data, String message, int status)` · `LocalDateTime.now().toString()` |
| 2. 200 성공 응답 | `ApiResponse.ok(T data)` |
| 3. 201 생성 응답 | `ApiResponse.created(T data)` |
| 4. 실패 응답 | `ApiResponse.error(String message, int status)` — `data` 에 `null` |
| 5. 상태 코드를 품은 예외 | `class BusinessException extends RuntimeException` · `super(message)` · `getStatus()` |
| 6. 404 예외 | `class NotFoundException` |
| 7. 409 예외 | `class DuplicateException` |
| 8. 이름 검사 | `ProductRequest.validate()` 첫 `if` — `name == null \|\| name.isBlank()` |
| 9. 가격 검사 | `ProductRequest.validate()` 둘째 `if` — `price < 0` |
| 10. 검증 → id 발급 → 저장 | `ProductService.create` — `request.validate()` · `++sequence` · `store.put(sequence, product)` (원본의 중복 `put` 포함) |
| 11. 없으면 404 | `ProductService.findById` — `store.get(id)` 가 `null` 이면 `NotFoundException` |
| 12. 복사본 목록 | `ProductService.findAll` — `new ArrayList<>(store.values())` |
| 13. 삭제 | `ProductService.delete` — `containsKey` 검사 · `store.remove(id)` |
| 14. 생성 핸들러 | `ProductController.createProduct` — `ApiResponse.created` / `catch (BusinessException e)` |
| 15. 단건 조회 핸들러 | `ProductController.getProduct` — `ApiResponse.ok` / `catch` |
| 16. 목록 핸들러 | `ProductController.getAllProducts` — try-catch 없이 `ApiResponse.ok` |
| 17. 삭제 핸들러 | `ProductController.deleteProduct` — `ApiResponse.ok("삭제 완료")` / `catch` |
| 18. 시나리오 | `RestControllerDemo.main` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-project-structures/reference/rest-controller-full.java`

```java
// [실무 프로젝트 구조] REST API 전체 구조
// 설명: Controller → Service → Response 래핑 → 에러 처리까지 REST API의 전체 구조를 구현
// 팁: ApiResponse로 응답을 표준화하면 프론트엔드에서 일관된 처리가 가능하다. 예외 계층을 만들어 비즈니스 예외와 시스템 예외를 분리한다. Spring에서는 @ControllerAdvice로 예외를 한 곳에서 처리하지만, 여기서는 Controller에서 직접 try-catch로 같은 패턴을 보여준다.

// === REST API 전체 구조 ===
// Controller → Service → Response 래핑 → 에러 처리
// 구조 의도: 모든 응답을 ApiResponse로 표준화 → 클라이언트의 응답 처리 일관성 확보.
// 트레이드오프: 단순 응답에도 래핑이 들어가 페이로드가 커진다. 마이크로 응답이 많은 API에서는 오버헤드.

import java.util.*;
// 응답 timestamp
import java.time.LocalDateTime;

// === 표준 API 응답 래퍼 ===
// 성공/실패 모두 동일한 구조 → 프론트엔드 코드 단순화
class ApiResponse<T> {
    private final boolean success;
    private final T data;
    private final String message;
    private final int status;
    private final String timestamp;

    private ApiResponse(boolean success, T data, String message, int status) {
        this.success = success;
        this.data = data;
        this.message = message;
        this.status = status;
        this.timestamp = LocalDateTime.now().toString();
    }

    // 200 OK 응답
    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(true, data, "성공", 200);
    }

    // 201 Created 응답
    public static <T> ApiResponse<T> created(T data) {
        return new ApiResponse<>(true, data, "생성 완료", 201);
    }

    // 에러 응답 (4xx/5xx)
    public static <T> ApiResponse<T> error(String message, int status) {
        return new ApiResponse<>(false, null, message, status);
    }

    @Override
    public String toString() {
        return String.format("{success=%s, status=%d, message='%s', data=%s}",
            success, status, message, data);
    }
}

// === 커스텀 예외 계층 ===
// 비즈니스 예외 베이스: HTTP 상태 코드를 함께 보유 → 응답 매핑이 쉬워진다
class BusinessException extends RuntimeException {
    private final int status;
    public BusinessException(String message, int status) {
        super(message);
        this.status = status;
    }
    public int getStatus() { return status; }
}

// 자원 없음 → 404
class NotFoundException extends BusinessException {
    public NotFoundException(String resource, Long id) {
        super(resource + "을(를) 찾을 수 없습니다: id=" + id, 404);
    }
}

// 중복 → 409 Conflict
class DuplicateException extends BusinessException {
    public DuplicateException(String field, String value) {
        super(field + " 중복: " + value, 409);
    }
}

// === DTO ===
// 요청 DTO: 검증 메서드도 함께 (검증 실패는 BusinessException으로 통일)
class ProductRequest {
    private final String name;
    private final int price;

    public ProductRequest(String name, int price) {
        this.name = name;
        this.price = price;
    }

    public String getName() { return name; }
    public int getPrice() { return price; }

    // 자기 검증: DTO 자신이 유효한지 알고 있다
    public void validate() {
        if (name == null || name.isBlank()) throw new BusinessException("상품명은 필수입니다", 400);
        if (price < 0) throw new BusinessException("가격은 0 이상이어야 합니다", 400);
    }
}

// 응답 DTO: 외부 노출 가능한 형태
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

// === Service ===
// 비즈니스 로직: 검증 → 저장 → 응답
class ProductService {
    private final Map<Long, ProductDto> store = new HashMap<>();
    // PK 자동 증가
    private long sequence = 0L;

    public ProductDto create(ProductRequest request) {
        // 입력 검증 (DTO에 위임)
        request.validate();
        ProductDto product = new ProductDto(++sequence, request.getName(), request.getPrice());
        // (참고: 아래 두 put은 동일 키에 두 번 저장하는 코드 - 원본 보존)
        store.put(product.toString().hashCode() != 0 ? sequence : sequence, product);
        store.put(sequence, product);
        return product;
    }

    public ProductDto findById(Long id) {
        ProductDto product = store.get(id);
        if (product == null) throw new NotFoundException("상품", id);
        return product;
    }

    public List<ProductDto> findAll() {
        return new ArrayList<>(store.values());
    }

    public void delete(Long id) {
        if (!store.containsKey(id)) throw new NotFoundException("상품", id);
        store.remove(id);
    }
}

// === Controller (REST 엔드포인트 시뮬레이션) ===
// 각 핸들러는 try-catch로 BusinessException을 ApiResponse.error로 매핑
// (실무에선 @ControllerAdvice로 분리하지만 여기선 패턴을 명시적으로 보여줌)
class ProductController {
    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    // POST /api/products: 생성 → 201
    public ApiResponse<?> createProduct(ProductRequest request) {
        try {
            ProductDto product = service.create(request);
            return ApiResponse.created(product);
        } catch (BusinessException e) {
            return ApiResponse.error(e.getMessage(), e.getStatus());
        }
    }

    // GET /api/products/{id}: 단건 조회 → 200 또는 404
    public ApiResponse<?> getProduct(Long id) {
        try {
            return ApiResponse.ok(service.findById(id));
        } catch (BusinessException e) {
            return ApiResponse.error(e.getMessage(), e.getStatus());
        }
    }

    // GET /api/products: 목록 → 200
    public ApiResponse<?> getAllProducts() {
        return ApiResponse.ok(service.findAll());
    }

    // DELETE /api/products/{id}: 삭제 → 200 또는 404
    public ApiResponse<?> deleteProduct(Long id) {
        try {
            service.delete(id);
            return ApiResponse.ok("삭제 완료");
        } catch (BusinessException e) {
            return ApiResponse.error(e.getMessage(), e.getStatus());
        }
    }
}

public class RestControllerDemo {
    public static void main(String[] args) {
        ProductController controller = new ProductController(new ProductService());

        // POST - 생성
        System.out.println("=== 상품 생성 ===");
        System.out.println(controller.createProduct(new ProductRequest("노트북", 1500000)));
        System.out.println(controller.createProduct(new ProductRequest("마우스", 35000)));

        // POST - 유효성 실패 (400)
        System.out.println("\n=== 유효성 검증 실패 ===");
        System.out.println(controller.createProduct(new ProductRequest("", -1000)));

        // GET - 조회
        System.out.println("\n=== 상품 조회 ===");
        System.out.println(controller.getProduct(1L));
        System.out.println(controller.getAllProducts());

        // GET - 없는 상품 (404)
        System.out.println("\n=== 없는 상품 조회 ===");
        System.out.println(controller.getProduct(99L));

        // DELETE
        System.out.println("\n=== 상품 삭제 ===");
        System.out.println(controller.deleteProduct(1L));
        System.out.println(controller.getAllProducts());
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 정적 제네릭 메서드는 `public static <T> ApiResponse<T> …` 처럼 반환형 앞에 `<T>` 를 다시 선언해야 한다.
- 예외 메시지는 `super(message)` 로 넘겨야 Controller 가 `e.getMessage()` 로 꺼낼 수 있다.
- `create` 안에서 `validate()` 를 `++sequence` 보다 먼저 불러야, 실패한 요청이 id 를 쓰지 않는다.
- 정답 코드의 `store.put` 두 줄은 같은 키에 같은 객체를 넣는다. 원본을 보존한 것이며 `store.put(sequence, product)` 한 줄로도 동작은 같다.
- Controller 의 `catch` 는 `BusinessException` 하나만 잡아도 404 · 409 하위 예외까지 모두 처리한다.
- `getAllProducts` 만 try-catch 가 없는 까닭은 `findAll` 이 비즈니스 예외를 던지지 않기 때문이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
