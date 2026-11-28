# java/java-project-structures/02 — REST API 전체 구조 — 정리 (힌트)

> 출처 — study-site 항목 `java/rest-controller-full`(항목 데이터 `data/java/project-structures.json`) · 정답 코드 study-practice `java/java-project-structures/reference/rest-controller-full.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**REST API 의 전체 구조는 「식당의 주문 창구」와 같다.**
손님은 창구 직원에게만 주문하고, 창구 직원은 주방에 일을 넘긴다.
요리가 나오든 재료가 떨어졌든, 손님에게는 늘 같은 모양의 쟁반이 나간다.
쟁반에는 「잘 됐나 · 상태 번호 · 한마디 · 음식」 칸이 정해져 있다.
재료가 없으면 주방은 「품절 — 번호 404」 쪽지를 올려 보내고, 창구 직원은 그 쪽지를 같은 쟁반에 얹어 내보낸다.
REST API 도 이와 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 손님 | 클라이언트(프론트엔드) |
| 주문서 | 요청 DTO `ProductRequest` |
| 창구 직원 | `ProductController` |
| 주방 | `ProductService` |
| 냉장고 | `store` (`HashMap<Long, ProductDto>`) |
| 요리 | 응답 DTO `ProductDto` |
| 정해진 모양의 쟁반 | `ApiResponse<T>` |
| 번호가 적힌 「품절」 쪽지 | `BusinessException` 과 그 하위 예외 |

```text
클라이언트
   │  요청 (ProductRequest 또는 id)
   ▼
Controller ──호출──▶ Service ──▶ store
   ▲                   │
   ├── ProductDto ─────┤  (성공)
   └── BusinessException┘ (실패: 상태 코드를 품고 온다)
   │
   ▼
ApiResponse { success, status, message, data, timestamp }
   │
   ▼
클라이언트
```

## 이 주제가 답하려는 질문

1. 요청 하나는 어떤 계층을 거쳐 응답이 되는가?
2. 성공 응답과 실패 응답을 왜 같은 모양으로 맞추는가?
3. 서비스 안에서 난 예외는 어떻게 HTTP 상태 코드가 붙은 응답으로 바뀌는가?
4. 입력 검증은 누가 맡는가?

## 동작 방식

### (1) 요청 하나가 지나가는 길 — 계층

**언제 쓰나** — 요청을 받는 일, 규칙을 지키는 일, 데이터를 보관하는 일을 서로 다른 클래스에 나눠 맡길 때 쓴다.

```text
createProduct(new ProductRequest("노트북", 1500000))
   │
   ▼  Controller: try 블록 안에서 service.create(request) 호출
   ▼  Service: request.validate() → ++sequence 로 id 발급 → ProductDto 생성 → store.put
   ▼  Service 가 ProductDto 를 돌려준다
   ▼  Controller: ApiResponse.created(product) 로 감싼다
   ▼
{success=true, status=201, message='생성 완료', data=Product{id=1, ...}}
```

- Controller 는 요청을 받아 서비스에 넘기고, 돌아온 결과를 응답 모양으로 감싼다.
- Service 는 검증 · id 발급 · 저장 같은 비즈니스 로직을 맡는다.
- 저장소는 `HashMap` 하나로 흉내 냈다.
- Controller 는 HTTP 를 직접 다루지 않는다. 주석의 `POST /api/products` 같은 경로는 「이 메서드가 이 엔드포인트를 맡는다」는 표시일 뿐이다.

> **엔드포인트** — 클라이언트가 부르는 「HTTP 메서드 + 경로」 한 쌍이다.\
> 예: `GET /api/products/{id}` 는 상품 한 개를 조회하는 엔드포인트다.

| HTTP 메서드 · 경로 | 핸들러 | 성공 | 실패 |
|---|---|---|---|
| `POST /api/products` | `createProduct` | 201 | 400 (검증 실패) |
| `GET /api/products/{id}` | `getProduct` | 200 | 404 |
| `GET /api/products` | `getAllProducts` | 200 | — (try-catch 없음) |
| `DELETE /api/products/{id}` | `deleteProduct` | 200 | 404 |

### (2) 표준 응답 래퍼 — `ApiResponse<T>`

**언제 쓰나** — 성공이든 실패든 클라이언트가 늘 같은 칸을 읽게 하고 싶을 때 쓴다.

> **래퍼(wrapper)** — 진짜 내용물을 한 겹 감싸 정해진 모양을 입히는 객체다.\
> 예: `ProductDto` 를 `ApiResponse` 의 `data` 칸에 넣어 내보낸다.

```text
ApiResponse.ok(dto)            → success=true , status=200, message="성공",     data=dto
ApiResponse.created(dto)       → success=true , status=201, message="생성 완료", data=dto
ApiResponse.error("…", 404)    → success=false, status=404, message="…",        data=null
            │
            └ 세 메서드 모두 private 생성자 하나를 거친다 → timestamp = LocalDateTime.now().toString()
```

- 필드 다섯 개(`success` · `data` · `message` · `status` · `timestamp`)가 모두 `final` 이라 만든 뒤에는 바뀌지 않는다.
- 생성자가 `private` 이므로 바깥에서는 `ok` · `created` · `error` 세 정적 메서드로만 응답을 만들 수 있다.
- 그래서 「성공인데 상태가 404」처럼 앞뒤가 안 맞는 조합이 바깥에서 생기지 않는다.
- `error` 는 `data` 칸에 `null` 을 넣는다.
- `toString` 은 `success` · `status` · `message` · `data` 만 찍고 `timestamp` 는 찍지 않는다.
- `data` 가 `null` 이면 `%s` 자리에 `null` 이라는 글자가 들어간다.

> **정적 팩토리 메서드** — `new` 대신 객체를 만들어 돌려주는 `static` 메서드다.\
> 예: `ApiResponse.created(product)` 는 201 응답 객체를 만든다.

### (3) 예외 계층 — 상태 코드를 품은 예외

**언제 쓰나** — 「사용자가 뭔가 잘못 보냈다 · 없는 것을 찾았다」 같은 예상 가능한 실패를 응답 코드와 함께 위로 올려 보낼 때 쓴다.

```text
RuntimeException
   └─ BusinessException (message, status)        ← 검증 실패에 직접 쓴다: 400
        ├─ NotFoundException(resource, id)       ← "상품을(를) 찾을 수 없습니다: id=99", 404
        └─ DuplicateException(field, value)      ← "<필드> 중복: <값>", 409
```

- `BusinessException` 은 메시지를 `super(message)` 로 부모에게 넘기고, 상태 코드는 자기 필드 `status` 에 담는다.
- 하위 예외는 생성자 안에서 메시지 문장과 상태 코드를 정해 부모 생성자를 부른다. 그래서 던지는 쪽은 `new NotFoundException("상품", id)` 만 쓰면 된다.
- `RuntimeException` 을 상속하므로 unchecked 예외다. 서비스 · DTO 메서드에 `throws` 선언이 없어도 된다.
- 예외가 상태 코드를 들고 다니므로, Controller 는 `catch (BusinessException e)` 하나로 모든 하위 예외를 `error(e.getMessage(), e.getStatus())` 에 꽂을 수 있다.
- 팁의 말대로, 이렇게 예외 계층을 따로 두면 **비즈니스 예외**(예상한 실패)와 **시스템 예외**(버그 · 예상 못 한 실패)를 나눌 수 있다.
- `DuplicateException` 은 정의만 있고 이 데모 안에서는 아무도 던지지 않는다.

> **unchecked 예외** — `RuntimeException` 의 하위 예외로, 컴파일러가 `throws` 선언이나 `catch` 를 강요하지 않는다.\
> 예: `BusinessException` 은 `validate()` 에 `throws` 없이 던져진다.

> **HTTP 상태 코드** — 응답이 어떻게 끝났는지 나타내는 세 자리 숫자다.\
> 예: 200 성공, 201 생성됨, 400 잘못된 요청, 404 없음, 409 충돌.

### (4) 요청 DTO 의 자기 검증 — `validate()`

**언제 쓰나** — 입력이 올바른지 판단하는 규칙을 입력 데이터 곁에 두고 싶을 때 쓴다.

> **DTO** — 계층 사이나 바깥으로 데이터를 실어 나르는 데만 쓰는 객체다.\
> 예: `ProductRequest` 는 들어오는 입력을, `ProductDto` 는 나가는 결과를 싣는다.

```text
new ProductRequest("", -1000).validate()
   │
   ├─ name 이 null 이거나 비었거나 공백뿐인가? → 그렇다 → BusinessException("상품명은 필수입니다", 400) 을 던지고 끝
   │
   └─ (이름이 멀쩡할 때만 여기까지 온다) price < 0 인가? → BusinessException("가격은 0 이상이어야 합니다", 400)
```

- 두 검사는 차례대로 돈다. 첫 검사에서 던지면 두 번째 검사는 실행되지 않는다.
- 그래서 이름과 가격이 둘 다 틀려도 응답에는 이름 쪽 메시지 하나만 실린다.
- `isBlank()` 는 빈 문자열과 공백만 있는 문자열을 모두 「비었다」로 본다.
- 검증 실패도 `BusinessException` 으로 통일하므로 Controller 가 따로 다룰 필요가 없다.
- 요청 DTO 는 입력만 실어 온다. 응답 DTO `ProductDto` 에는 서버가 발급한 `id` 가 더해진다.

### (5) Service — 저장 · 조회 · 삭제

**언제 쓰나** — 저장소를 직접 만지는 일과 「없으면 404」 같은 규칙을 한 곳에 모을 때 쓴다.

```text
create(request)
   request.validate()          ← 실패하면 여기서 예외, 아래 줄은 실행되지 않는다
   ++sequence                  ← 성공한 요청만 id 를 받는다
   new ProductDto(sequence, name, price)
   store.put(sequence, product)
   return product

findById(id)  : store.get(id) 가 null → NotFoundException("상품", id)
findAll()     : new ArrayList<>(store.values())  ← 복사본 목록
delete(id)    : !store.containsKey(id) → NotFoundException, 아니면 store.remove(id)
```

- `sequence` 는 PK 를 자동으로 늘려 주는 계수기다. `++sequence` 는 먼저 1 을 더한 뒤 그 값을 쓴다. 그래서 첫 상품의 id 는 1 이다.
- 검증이 `++sequence` 보다 앞에 있다. 그래서 검증에 실패한 요청은 번호를 쓰지 않는다.
- 원본에는 `store.put` 이 두 줄 있다. 첫 줄의 삼항 연산자는 참이든 거짓이든 `sequence` 를 고른다. 그래서 두 줄은 같은 키에 같은 객체를 두 번 넣는 셈이다. 정답 코드 주석에도 「원본 보존」이라고 적혀 있다.
- `findAll` 은 `values()` 를 새 `ArrayList` 에 옮겨 돌려준다. 받는 쪽이 목록을 고쳐도 `store` 는 바뀌지 않는다.

> **PK(기본 키)** — 레코드 하나를 다른 레코드와 구별하는 유일한 값이다.\
> 예: `ProductDto` 의 `id`.

### (6) Controller — 예외를 응답으로 바꾸기

**언제 쓰나** — 서비스가 던진 비즈니스 예외를 클라이언트가 읽을 수 있는 실패 응답으로 바꿀 때 쓴다.

```text
getProduct(99L)
   try {
      service.findById(99L)  ──▶ NotFoundException("상품을(를) 찾을 수 없습니다: id=99", 404) 발생
   } catch (BusinessException e)   ← 하위 예외도 여기서 잡힌다
      return ApiResponse.error(e.getMessage(), e.getStatus())
   ▼
{success=false, status=404, message='상품을(를) 찾을 수 없습니다: id=99', data=null}
```

- `createProduct` · `getProduct` · `deleteProduct` 세 핸들러는 같은 꼴의 try-catch 를 되풀이한다.
- `getAllProducts` 에는 try-catch 가 없다. `findAll` 은 `BusinessException` 을 던지지 않기 때문이다.
- `deleteProduct` 는 성공하면 `ApiResponse.ok("삭제 완료")` 를 돌려준다. `ok` 가 `message` 를 "성공" 으로 정하므로, 「삭제 완료」라는 글은 `message` 가 아니라 `data` 칸에 들어간다.
- 반환형 `ApiResponse<?>` 는 「어떤 `T` 든 상관없다」는 뜻이다. 그래서 `ProductDto` · `List<ProductDto>` · `String` 을 담은 응답을 모두 돌려줄 수 있다.
- 잡는 것은 `BusinessException` 계열뿐이다. 다른 예외(예: `null` 요청이 일으키는 `NullPointerException`)는 잡히지 않고 핸들러 밖으로 퍼진다.
- 팁에 따르면 Spring 에서는 `@ControllerAdvice` 로 이 예외 처리를 한 곳에 모은다. 이 데모는 같은 패턴을 Controller 의 try-catch 로 직접 보여 준다.

`main` 이 차례로 만드는 응답의 상태 코드는 다음과 같다(코드를 읽어 추론한 것 — 실행 결과 아님).

| 호출 | 상태 | 까닭 |
|---|---|---|
| 「노트북」 생성 | 201 | id=1 발급 |
| 「마우스」 생성 | 201 | id=2 발급 |
| `("", -1000)` 생성 | 400 | 이름 검사에서 멈춤 |
| `getProduct(1L)` | 200 | 노트북 |
| `getAllProducts()` | 200 | 두 개 |
| `getProduct(99L)` | 404 | 없음 |
| `deleteProduct(1L)` | 200 | `data` 칸에 "삭제 완료" |
| `getAllProducts()` | 200 | 마우스 하나 |

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

```java
class Result<T> {
    private final boolean ok;
    private final T data;
    private final int status;

    private Result(boolean ok, T data, int status) {
        this.ok = ok; this.data = data; this.status = status;
    }
    public static <T> Result<T> ok(T data)     { return new Result<>(true, data, 200); }
    public static <T> Result<T> fail(int status) { return new Result<>(false, null, status); }
}

class AppException extends RuntimeException {
    private final int status;
    AppException(String msg, int status) { super(msg); this.status = status; }
    int getStatus() { return status; }
}
```

- 정적 제네릭 메서드는 반환형 앞에 `<T>` 를 따로 선언한다: `public static <T> ApiResponse<T> ok(T data)`.
- 클래스의 `T` 는 인스턴스에 묶인다. 그래서 `static` 메서드는 자기 `<T>` 가 필요하다.
- `new ApiResponse<>(…)` 의 `<>` 는 타입 인자를 반환형에서 추론하게 한다.
- 받는 쪽이 `T` 를 몰라도 될 때는 `ApiResponse<?>` 로 받는다.
- 예외 메시지는 `super(message)` 로 넘겨야 `e.getMessage()` 로 다시 꺼낼 수 있다.
- 상태 코드 같은 추가 정보는 예외 클래스의 `final` 필드와 getter 로 싣는다.
- `catch (부모예외 e)` 는 그 하위 예외도 모두 잡는다.
- `String.format` 의 `%s` 는 `boolean` · 객체 · `null` 을 글자로 바꾸고, `%d` 는 `int` · `Long` 같은 정수를 받는다.

| 정적 메서드 | success | status | message | data |
|---|---|---|---|---|
| `ok(data)` | true | 200 | "성공" | 받은 값 |
| `created(data)` | true | 201 | "생성 완료" | 받은 값 |
| `error(message, status)` | false | 받은 값 | 받은 값 | `null` |

| 예외 | 상태 | 메시지 꼴 |
|---|---|---|
| `BusinessException` (검증) | 400 | 호출자가 준 문장 |
| `NotFoundException` | 404 | `<자원>을(를) 찾을 수 없습니다: id=<id>` |
| `DuplicateException` | 409 | `<필드> 중복: <값>` |

## 어디서 틀리나

### 1. 모든 응답을 감싸면 응답이 커진다

정답 코드의 주석이 밝힌 트레이드오프다.
래퍼 덕분에 클라이언트의 처리는 일관되지만, 값 하나만 돌려주는 응답에도 `success` · `status` · `message` · `timestamp` 가 따라붙는다.
작은 응답을 아주 많이 주고받는 API 에서는 이 덧붙은 페이로드가 오버헤드가 된다.

> **페이로드** — 응답이나 요청에 실려 오가는 데이터 본문이다.\
> 예: `ApiResponse` 전체가 응답 페이로드다.

### 2. 같은 try-catch 를 핸들러마다 되풀이한다

`createProduct` · `getProduct` · `deleteProduct` 가 똑같은 `catch` 블록을 가진다.
핸들러가 늘면 이 반복도 함께 는다.
팁대로 Spring 에서는 `@ControllerAdvice` 로 한 곳에서 처리한다. 이 데모는 패턴을 눈에 보이게 하려고 일부러 직접 썼다.

### 3. `BusinessException` 밖의 예외는 그대로 새어 나간다

Controller 는 `BusinessException` 계열만 잡는다.
`createProduct(null)` 처럼 `null` 요청이 오면 `request.validate()` 에서 `NullPointerException` 이 나고, 이 예외는 어느 `catch` 에도 걸리지 않는다.
이때 클라이언트는 `ApiResponse` 모양이 아닌 실패를 받게 된다.
비즈니스 예외와 시스템 예외를 나눈다는 것은 「이쪽은 내가 의미를 아는 실패」라는 선을 긋는 것이다. 선 밖의 실패를 어떻게 다룰지는 따로 정해야 한다.

### 4. 검증은 첫 실패에서 멈춘다

`validate()` 는 이름을 먼저 검사하고, 틀리면 곧바로 던진다.
`("", -1000)` 처럼 둘 다 틀려도 응답에는 「상품명은 필수입니다」 하나만 실린다.
틀린 곳을 한 번에 모두 알려 주려면 오류를 모아 두었다가 던지도록 바꿔야 한다.

### 5. 같은 키로 두 번 저장하는 줄

`store.put(product.toString().hashCode() != 0 ? sequence : sequence, product);` 는 조건이 무엇이든 키가 `sequence` 다.
바로 다음 줄도 같은 키에 같은 객체를 넣는다.
결과는 한 번 넣은 것과 같다. 첫 줄은 `toString` 과 `hashCode` 를 쓸데없이 계산할 뿐이다.
정답 코드는 원본을 보존하려고 이 줄을 남겨 두었다.

### 6. 「삭제 완료」는 `message` 가 아니다

`ApiResponse.ok("삭제 완료")` 는 `data` 에 "삭제 완료" 를 넣고, `message` 는 "성공" 으로 둔다.
메시지 칸을 읽는 클라이언트는 「삭제 완료」를 보지 못한다.

### 7. `HashMap` 은 순서를 약속하지 않는다

`findAll` 은 `store.values()` 의 순회 순서를 그대로 따른다.
`HashMap` 은 순회 순서를 보장하지 않으므로, 목록이 id 순으로 나온다고 기대하면 안 된다.
순서가 필요하면 순서를 지키는 맵을 쓰거나 정렬해서 돌려줘야 한다.

### 8. `timestamp` 는 있지만 찍히지 않는다

`ApiResponse` 는 만들어질 때 시각을 기록한다.
그런데 `toString` 형식에 `timestamp` 가 빠져 있어, 데모의 콘솔 줄에서는 보이지 않는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `RuntimeException` 하위 예외는 `throws` 선언 없이 던질 수 있다 | Java 언어 명세 (unchecked 예외 규칙) |
| `catch (BusinessException e)` 가 하위 예외도 잡는다 | Java 언어 명세 |
| `String.format` 의 `%s` 가 `null` 을 `null` 이라는 글자로 바꾼다 | Java 표준 라이브러리 (`Formatter`) 명세 |
| `HashMap` 의 순회 순서 | 보장 없음 — 작은 `Long` 키에서 id 순처럼 보일 수 있는 것은 구현의 동작이다 (확인 필요) |
| 200 · 201 · 400 · 404 · 409 의 뜻 | HTTP 규약 — 이 코드는 숫자를 필드에 넣을 뿐이고, 실제 HTTP 응답 코드로 내보내는 일은 웹 프레임워크가 맡는다 |
| `@ControllerAdvice` 로 예외를 한 곳에서 처리한다 | Spring 프레임워크의 기능 — Java 언어 기능이 아니다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 여러 클라이언트가 같은 방식으로 응답을 읽어야 할 때 | `ApiResponse` 같은 표준 래퍼 | 엔드포인트마다 제각각인 응답 모양 |
| 값 하나만 아주 자주 오가는 가벼운 API | 래핑을 줄인 응답 | 모든 응답에 필드 넷을 덧붙이는 래핑 |
| 예상 가능한 실패(검증 · 없음 · 중복) | 상태 코드를 품은 `BusinessException` 계열 | 의미 없는 `RuntimeException` 을 그대로 던지기 |
| 핸들러가 많은 실무 Spring 프로젝트 | `@ControllerAdvice` 한 곳에서 처리 | 핸들러마다 같은 try-catch 를 복사 |
| 입력 규칙이 그 입력에만 묶일 때 | 요청 DTO 의 `validate()` | Controller 곳곳에 흩어진 `if` 검사 |
| 목록 순서가 중요할 때 | 순서를 지키는 자료구조나 정렬 | `HashMap.values()` 순서에 기대기 |

## 핵심 문장

1. **요청은 Controller → Service → 저장소를 거쳐 내려가고, 결과나 예외가 올라와 `ApiResponse` 로 감싸진다.**
2. **`ApiResponse` 는 `private` 생성자와 `ok` · `created` · `error` 정적 메서드로 성공과 실패를 같은 모양에 담는다.**
3. **예외가 상태 코드를 품고 다니므로 `catch (BusinessException e)` 하나가 모든 비즈니스 실패를 응답으로 바꾼다.**
4. **검증은 요청 DTO 가 스스로 하고, 실패도 같은 예외 계층으로 통일한다.**
5. **표준화의 값은 일관성이고, 대가는 덧붙는 페이로드와 반복되는 try-catch 다(Spring 은 후자를 `@ControllerAdvice` 로 모은다).**

## 관련 자료

- `crud-service` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [error-handling-global](../12-error-handling-global/2-summary.md)
- `pagination-api` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/project-structures.json` 의 `rest-controller-full`

## 용어 풀이

- **REST API** — HTTP 메서드와 자원 경로로 기능을 나눠 내놓는 웹 API 설계 방식이다.
- **엔드포인트** — HTTP 메서드와 경로 한 쌍으로 정해지는 API 의 입구 하나다.
- **Controller** — 요청을 받아 서비스에 넘기고 결과를 응답 모양으로 만드는 계층이다.
- **Service** — 검증 · 저장 · 조회 같은 비즈니스 로직을 맡는 계층이다.
- **DTO** — 계층 사이나 바깥으로 데이터만 실어 나르는 객체다.
- **요청 DTO / 응답 DTO** — 들어오는 입력을 싣는 객체 / 바깥에 내보낼 결과를 싣는 객체다.
- **래퍼** — 내용물을 감싸 정해진 모양을 입히는 객체다.
- **정적 팩토리 메서드** — `new` 대신 객체를 만들어 주는 `static` 메서드다.
- **제네릭 `<T>`** — 타입을 매개변수로 받아 여러 타입에 같은 코드를 쓰게 하는 문법이다.
- **와일드카드 `<?>`** — 「어떤 타입 인자든 상관없다」를 뜻하는 표기다.
- **비즈니스 예외** — 규칙 위반처럼 미리 예상한 실패를 나타내는 예외다.
- **시스템 예외** — 버그나 환경 문제처럼 예상하지 못한 실패를 나타내는 예외다.
- **unchecked 예외** — `RuntimeException` 계열이라 `throws` · `catch` 를 강요받지 않는 예외다.
- **HTTP 상태 코드** — 응답의 결과를 나타내는 세 자리 숫자다.
- **PK** — 레코드를 유일하게 구별하는 키다.
- **시퀀스** — PK 를 하나씩 늘려 발급하는 계수기다.
- **페이로드** — 요청이나 응답에 실리는 데이터 본문이다.
- **`@ControllerAdvice`** — Spring 에서 여러 Controller 의 예외 처리를 한 곳에 모으는 어노테이션이다.

## 더 들어가면

- Spring 에서는 `@ControllerAdvice` 클래스 안에 `@ExceptionHandler(BusinessException.class)` 메서드를 두어 예외를 응답으로 바꾼다. `@RestControllerAdvice` 라는 변형도 있다 (확인 필요).
- 실제 HTTP 상태 코드를 내보내려면 Spring 에서는 `ResponseEntity` 로 상태와 본문을 함께 돌려준다. 본문 안의 `status` 필드와 실제 HTTP 상태가 어긋나지 않게 맞추는 것이 흔한 관례다 (확인 필요).
- 시스템 예외는 보통 최상위 핸들러에서 500 응답으로 바꾸고, 내부 메시지는 감춘 채 로그로만 남긴다 (확인 필요).
- 입력 검증은 Bean Validation(`@Valid` · `@NotBlank` · `@Min` 등)으로 선언할 수도 있다. 이 방식은 실패한 필드를 모아 한 번에 알려 줄 수 있다 (확인 필요).
- `String.isBlank()` 는 Java 11 에 추가된 메서드로 알려져 있다 (확인 필요).
- `HashMap` 과 `long` 계수기는 여러 스레드가 동시에 쓰면 안전하지 않다. 실제 서버라면 `ConcurrentHashMap` 과 `AtomicLong` 이나 데이터베이스의 키 생성을 쓴다 (확인 필요).
- 불변 DTO 는 최근 Java 의 `record` 로 더 짧게 쓸 수 있다 (확인 필요).
