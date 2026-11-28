# java/java-spring/15 — Spring 테스트 — 정리 (힌트)

> 출처 — study-site 항목 `java/spring-test`(항목 데이터 `data/java/spring-essentials.json`) · 정답 코드 study-practice `java/java-spring/reference/spring-test.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**Spring 테스트는 「자동차를 세 가지 크기로 검사하는 일」이다.**
부품 하나는 작업대에 올려 혼자 검사한다.
엔진룸만 볼 때는 엔진룸만 시동 걸고, 연결된 나머지 부품은 모형으로 끼운다.
마지막에는 완성차를 도로에 내보내 처음부터 끝까지 달려 본다.
Spring 테스트도 똑같은 구조다.
`UserService` 하나만 Spring 없이 검사하면 단위 테스트가 된다.
컨트롤러 계층만 띄우고 서비스를 가짜로 끼우면 `@WebMvcTest` 슬라이스 테스트가 된다.
애플리케이션 전체를 띄워 실제 HTTP 로 부르면 `@SpringBootTest` 통합 테스트가 된다.

> **단위 테스트** — 클래스 하나를 그 의존 대상과 떼어 놓고 검사하는 테스트.\
> 예: `UserService` 를 `new` 로 만들고 `UserRepository` 자리에는 가짜를 넣는다.

> **슬라이스 테스트** — 애플리케이션의 한 계층(웹 · JPA 등)에 필요한 빈만 띄우는 테스트.\
> 예: `@WebMvcTest` 는 웹 계층만, `@DataJpaTest` 는 JPA 계층만 띄운다.

> **통합 테스트** — 여러 계층을 실제로 이어 붙여 함께 검사하는 테스트.\
> 예: `@SpringBootTest` 로 서버를 띄우고 POST 다음 GET 을 실제로 보낸다.

| 비유 | 실체 |
|---|---|
| 작업대 위 부품 하나 | Spring 없이 Mockito 만 쓰는 `UserServiceTest` |
| 엔진룸만 시동 · 나머지는 모형 | `@WebMvcTest` + `@MockBean` |
| 연료 계통만 따로 시험 | `@DataJpaTest` (Repository 만) |
| 완성차 도로 주행 | `@SpringBootTest(RANDOM_PORT)` + `TestRestTemplate` |
| 검사 기록지의 「통과 조건」 | `andExpect(...)` · `assertThat(...)` |

```text
  범위 좁음 · 빠름                                      범위 넓음 · 느림
  ─────────────────────────────────────────────────────────────────▶
  [단위]            [슬라이스]                [슬라이스]        [통합]
  Service 하나      Controller + 웹 빈         Repository + JPA   전체 컨텍스트
  Mockito mock()    @WebMvcTest + @MockBean   @DataJpaTest        @SpringBootTest
                    MockMvc                   TestEntityManager   TestRestTemplate
```

## 이 주제가 답하려는 질문

1. 테스트마다 Spring 의 무엇을 띄우고, 무엇을 가짜로 바꾸나?
2. 컨트롤러에 요청을 보내고 응답(상태 코드 · JSON 필드)을 어떻게 검증하나?
3. 단위 · 슬라이스 · 통합 테스트는 속도와 검사 범위가 어떻게 다르고, 언제 무엇을 고르나?
4. Repository 를 검사할 때 「정말 DB 에서 읽어 왔다」를 어떻게 확인하나?

## 동작 방식

### (1) `@WebMvcTest` — 컨트롤러만 띄우고 서비스는 가짜로

**언제 쓰나** — 요청 URL · 상태 코드 · 응답 JSON 꼴 · 입력 검증처럼 웹 계층의 일만 확인할 때 쓴다.
서비스의 실제 로직은 여기서 검사하지 않는다.

```text
@WebMvcTest(UserController.class)
        │
        ▼
 ┌─ 테스트용 Spring 컨텍스트 ───────────────────────────┐
 │  UserController (진짜)                                │
 │  웹 관련 빈 (MockMvc · ObjectMapper 등)               │
 │  UserService ← @MockBean 이 넣은 가짜                 │
 │  (Repository · DB 는 없음)                            │
 └──────────────────────────────────────────────────────┘
        │
 given(userService.getUser(1L)).willReturn(response)   ← 가짜의 대답을 미리 정함
        │
 mockMvc.perform(get("/api/v1/users/{id}", 1L))         ← 서블릿 컨테이너 없이 요청
        │
        ▼
 .andExpect(status().isOk())
 .andExpect(jsonPath("$.name").value("Kim"))            ← 응답을 검사
```

- `@WebMvcTest(UserController.class)` 는 지정한 컨트롤러와 웹 관련 빈만 컨텍스트에 올린다.
- 컨트롤러가 기대는 `UserService` 는 올라오지 않으므로 `@MockBean` 으로 가짜 빈을 넣는다.
- `given(...).willReturn(...)` 은 「이 인자로 부르면 이 값을 돌려줘라」를 가짜에게 미리 적어 두는 것이다.
- `given(...).willThrow(...)` 는 대답 대신 예외를 던지게 한다 — 원본은 `999L` 에 `EntityNotFoundException` 을 던지게 하고 404 와 `"ENTITY_NOT_FOUND"` 코드를 기대한다.
- `MockMvc` 는 실제 서버를 띄우지 않고 컨트롤러로 요청을 흘려보낸다.
- `andExpect` 가 여럿이면 하나라도 맞지 않을 때 테스트가 실패한다.
- `jsonPath("$.name")` 은 응답 JSON 의 최상위 `name` 필드를 가리킨다.
- POST 본문은 `objectMapper.writeValueAsString(request)` 로 객체를 JSON 문자열로 바꿔 `.content(...)` 에 넣고, `.contentType(MediaType.APPLICATION_JSON)` 으로 형식을 알린다.

> **빈(bean)** — Spring 컨텍스트가 만들고 관리하는 객체.\
> 예: `UserController` · `UserService` 가 빈으로 등록된다.

> **컨텍스트** — 빈들을 만들어 서로 이어 주는 Spring 의 컨테이너.\
> 예: `@SpringBootTest` 는 애플리케이션의 컨텍스트 전체를 띄운다.

> **목(mock)** — 진짜 대신 끼우는 가짜 객체로, 미리 정한 대로만 대답한다.\
> 예: `@MockBean private UserService userService;`

> **스텁(stub)** — 가짜에게 「이렇게 부르면 이렇게 대답하라」를 정해 두는 일.\
> 예: `given(userService.getUser(1L)).willReturn(response);`

### (2) `@SpringBootTest(RANDOM_PORT)` — 전체를 띄우고 실제 HTTP 로

**언제 쓰나** — 컨트롤러 → 서비스 → 리포지토리 → DB 가 실제로 맞물려 돌아가는 흐름을 확인할 때 쓴다.

```text
@SpringBootTest(webEnvironment = RANDOM_PORT)
        │
        ▼
 전체 컨텍스트 로드 + 실제 서버를 임의 포트로 기동
        │
 restTemplate.postForEntity("/api/v1/users", request, UserResponse.class)
        │   (TestRestTemplate 이 임의 포트를 자동으로 붙여 실제 HTTP 호출)
        ▼
 201 CREATED · body.name == "TestUser"   → 생성된 id 를 꺼냄
        │
 restTemplate.getForEntity("/api/v1/users/{id}", UserResponse.class, userId)
        ▼
 200 OK · body.email == "test@example.com"
```

- `@SpringBootTest` 는 전체 컨텍스트를 올린다 — 가짜가 없고 서비스 · 리포지토리가 모두 진짜다.
- `RANDOM_PORT` 는 실제 서버를 임의 포트로 띄운다.
- `TestRestTemplate` 은 그 포트를 알아서 붙여 상대 경로(`/api/v1/users`)로 실제 HTTP 요청을 보낸다.
- 첫 요청(POST)의 응답에서 `id` 를 꺼내 두 번째 요청(GET)의 URL 변수 `{id}` 에 넣는다 — 앞 단계의 결과가 다음 단계의 입력이 된다.
- 응답은 `ResponseEntity` 로 받아 `getStatusCode()` 와 `getBody()` 를 따로 검사한다.
- 전체를 띄우므로 슬라이스 · 단위 테스트보다 느리다.

### (3) Spring 없는 서비스 단위 테스트 — Mockito 만

**언제 쓰나** — 서비스의 비즈니스 로직(찾으면 변환, 없으면 예외)을 가장 빠르게 확인할 때 쓴다.

```text
@BeforeEach setUp()
   userRepository = mock(UserRepository.class)      ← Mockito 가 가짜 생성
   userService    = new UserService(userRepository) ← 생성자로 직접 주입
        │
 given(userRepository.findById(999L)).willReturn(Optional.empty())
        │
 userService.getUser(999L)
        ▼
 assertThatThrownBy(...)
   .isInstanceOf(EntityNotFoundException.class)
   .hasMessageContaining("999")
```

- Spring 컨텍스트를 전혀 띄우지 않는다 — `@Autowired` 도 `@MockBean` 도 없다.
- `mock(...)` 으로 가짜를 만들고 `new` 로 서비스에 직접 넣는다.
- 이것이 되는 까닭은 `UserService` 가 생성자로 리포지토리를 받기 때문이다.
- `@BeforeEach` 가 테스트마다 새 가짜와 새 서비스를 만들어, 앞 테스트의 스텁이 다음 테스트로 새지 않는다.
- `findById` 가 `Optional.of(user)` 를 돌려주면 성공 경로, `Optional.empty()` 를 돌려주면 예외 경로를 검사한다.
- `assertThatThrownBy` 는 람다 안에서 예외가 나는지, 그 종류와 메시지까지 검사한다.

### (4) `@DataJpaTest` — Repository 만, 캐시를 비우고 읽기

**언제 쓰나** — `findByEmail` 같은 쿼리 메서드가 DB 에서 제대로 찾아오는지 확인할 때 쓴다.

```text
@DataJpaTest   (JPA 관련 빈만 · 원본 주석: 인메모리 DB + 트랜잭션 자동 롤백)
        │
 entityManager.persistAndFlush(user)   ← 저장하고 즉시 DB 에 반영
 entityManager.clear()                 ← 1차 캐시를 비움
        │
 userRepository.findByEmail("kim@test.com")
        ▼
 found.isPresent() · found.get().getName() == "Kim"
        │
 테스트 끝 → 트랜잭션 롤백 (원본 주석)
```

- `@DataJpaTest` 는 JPA 관련 빈만 올린다 — 컨트롤러 · 서비스는 없다.
- `TestEntityManager` 는 테스트 전용 `EntityManager` 로, 준비 데이터를 넣는 데 쓴다.
- `persistAndFlush` 는 저장(persist)과 DB 반영(flush)을 한 번에 한다.
- `clear()` 는 1차 캐시를 비운다 — 원본 주석은 이것이 「실제 SELECT 실행 보장」이라고 적는다(이 주장의 정확도는 「어디서 틀리나 5」).
- 원본 주석에 따르면 테스트가 끝나면 트랜잭션이 롤백되어, 넣은 데이터가 다음 테스트에 남지 않는다.

> **1차 캐시** — 한 영속성 컨텍스트 안에서 이미 읽거나 저장한 엔티티를 메모리에 들고 있는 저장소.\
> 예: `persist` 한 `user` 는 `clear()` 전까지 메모리에 남아 있다.

### (5) 네 테스트에 공통인 뼈대 — given · when · then 과 프로파일

**언제 쓰나** — 모든 테스트 메서드를 읽기 쉽게 세 칸으로 나눌 때 쓴다.

```text
// given     준비: 입력 DTO · 도메인 객체 · 가짜의 대답
// when      실행: perform(...) · postForEntity(...) · getUser(...)
// then      검증: andExpect(...) · assertThat(...)
```

- 원본의 모든 테스트가 이 세 주석으로 나뉜다.
- MockMvc 는 실행과 검증이 한 사슬로 이어져 `// when & then` 으로 묶는다.
- `BDDMockito.given` 은 이 「given」 칸에 맞춘 이름의 스텁 문법이다.
- `@ActiveProfiles("test")` 는 테스트 동안 `test` 프로파일을 켠다 — 테스트용 설정을 따로 쓰게 하는 스위치다.
- `@DisplayName` 은 테스트 결과에 보일 사람이 읽는 이름을 붙인다.

> **BDD** — 동작을 given · when · then 으로 서술하는 테스트 작성 방식.\
> 예: `given(repo.findById(1L)).willReturn(...)`.

> **프로파일** — 같은 애플리케이션에서 환경마다 다른 설정 묶음을 고르는 이름.\
> 예: `@ActiveProfiles("test")`.

## 문법 — 형태와 규칙

최소 예제(직접 쓴 것):

```java
// 슬라이스: 컨트롤러 + 가짜 서비스
@WebMvcTest(ItemController.class)
class ItemControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean ItemService itemService;

    @Test
    void get() throws Exception {
        given(itemService.find(1L)).willReturn(new ItemResponse(1L, "pen"));
        mockMvc.perform(get("/items/{id}", 1L))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("pen"));
    }
}
```

| 애너테이션 · 도구 | 띄우는 것 | 가짜로 바꾸는 것 | 요청 · 검증 도구 |
|---|---|---|---|
| `@WebMvcTest(X.class)` | 컨트롤러 `X` + 웹 관련 빈 | 필요한 서비스를 `@MockBean` 으로 | `MockMvc` · `status()` · `jsonPath()` |
| `@SpringBootTest(RANDOM_PORT)` | 전체 컨텍스트 + 실제 서버 | 없음 | `TestRestTemplate` · `assertThat` |
| (애너테이션 없음) | Spring 없음 | 의존 대상을 `mock(...)` 으로 | 직접 호출 · `assertThat` · `assertThatThrownBy` |
| `@DataJpaTest` | JPA 관련 빈 | 없음 | `TestEntityManager` · `assertThat` |

- `@MockBean` 은 Spring 컨텍스트 **안의** 빈을 가짜로 바꾼다 — 컨텍스트가 있는 테스트에서 쓴다.
- `mock(...)` 은 Mockito 가 그냥 가짜 객체를 만든다 — 컨텍스트가 없는 단위 테스트에서 쓴다.
- `get(...)` · `post(...)` 는 `MockMvcRequestBuilders`, `status()` · `jsonPath()` 는 `MockMvcResultMatchers` 에서 정적 import 한다.
- URL 의 `{id}` 는 `get("/…/{id}", 1L)` · `getForEntity("/…/{id}", Type.class, userId)` 처럼 뒤 인자로 채운다.
- `perform` 을 쓰는 테스트 메서드는 `throws Exception` 을 단다.
- `@Autowired` 는 테스트 클래스에서도 필드에 빈을 주입한다.
- `@Test` · `@DisplayName` · `@BeforeEach` 는 JUnit 5 의 것이다.

## 어디서 틀리나

### 1. `@WebMvcTest` 에서 서비스 가짜를 빠뜨린다
`@WebMvcTest` 는 컨트롤러만 로드하고 서비스는 올리지 않는다.
컨트롤러가 `UserService` 를 주입받는데 컨텍스트에 그 빈이 없으면 컨텍스트를 만들 수 없다(원본에 근거 없음 — 추론).
그래서 팁대로 서비스는 `@MockBean` 으로 대체한다.

### 2. 모든 테스트를 `@SpringBootTest` 로 쓴다
팁: `@SpringBootTest` 는 전체 컨텍스트를 로드하므로 통합 테스트에 적합하다.
거꾸로 말하면 웹 계층만 보거나 로직만 볼 때 쓰기엔 무겁다.
컨트롤러는 `@WebMvcTest`, 리포지토리는 `@DataJpaTest`, 서비스 로직은 Spring 없는 단위 테스트로 나누는 것이 원본의 구도다.

### 3. 단위 테스트에 `@MockBean` 을 쓴다
팁: 서비스 단위 테스트는 Spring 없이 Mockito 만으로 작성하면 가장 빠르다.
`@MockBean` 은 컨텍스트의 빈을 바꾸는 도구라 컨텍스트 없는 테스트에는 맞지 않는다.
단위 테스트는 `mock(...)` + 생성자 주입이다.

### 4. 404 · 400 응답이 「컨트롤러 테스트가 알아서」 나온다고 여긴다
원본은 서비스가 `EntityNotFoundException` 을 던지면 404 와 `$.code == "ENTITY_NOT_FOUND"` 를 기대한다.
잘못된 입력에는 400 과 `$.code == "VALIDATION_ERROR"`, 배열인 `$.errors` 를 기대한다.
이 상태 코드와 JSON 꼴은 예제에 보이지 않는 프로젝트 쪽 코드(예외를 응답으로 바꾸는 처리기, 요청 DTO 의 검증 설정)가 만든다(원본에 근거 없음 — 추론).
그 코드가 없으면 같은 테스트가 실패한다.

### 5. `clear()` 의 주석을 그대로 믿는다
원본의 주장 → 「1차 캐시 비우기 - 실제 SELECT 실행 보장」.
왜 의심스러운가 → `findByEmail` 같은 쿼리 메서드는 캐시가 있어도 DB 에 SELECT 를 보내는 것으로 알려져 있다(확인 필요).
그렇다면 `clear()` 가 확실히 바꾸는 것은 「SELECT 가 나가느냐」보다 「돌려받는 객체가 메모리에 있던 그 `user` 인가, DB 에서 새로 만든 객체인가」다(확인 필요).
어느 쪽이든 `clear()` 를 두면 결과가 메모리에 남은 객체가 아니라 DB 에서 다시 읽은 값임이 분명해진다.

### 6. 예제를 그대로 복사하면 컴파일되지 않는다
원본의 import 목록에는 `ObjectMapper` · `LocalDateTime` · `ResponseEntity` · `HttpStatus` · `Optional` · `BeforeEach` · `DataJpaTest` · `TestEntityManager` · `mock` · `assertThatThrownBy` 가 없다.
반대로 `Nested` 와 `any` 는 import 했지만 쓰지 않는다.
`UserController` · `UserService` · `User` · `UserResponse` · `CreateUserRequest` · `EntityNotFoundException` 도 예제 밖에 있어야 한다.

### 7. 단위 테스트에서 스텁이 테스트 사이로 샌다고 걱정한다
`@BeforeEach` 가 테스트마다 `mock(...)` 과 `new UserService(...)` 를 다시 하므로 테스트끼리 가짜를 나눠 쓰지 않는다.
이 준비를 필드 선언에서 한 번만 하면 이 보장이 흐려진다(원본에 근거 없음 — 추론).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `@WebMvcTest` 는 컨트롤러와 웹 관련 빈만 로드한다 | Spring Boot 테스트 자동 설정 (Java 언어 아님) |
| `MockMvc` 는 서블릿 컨테이너 없이 컨트롤러를 부른다 | Spring Test 프레임워크 |
| `RANDOM_PORT` 로 실제 서버가 임의 포트에 뜨고 `TestRestTemplate` 이 그 포트를 붙인다 | Spring Boot 테스트 지원 |
| `@DataJpaTest` 가 인메모리 DB 를 쓰고 트랜잭션을 롤백한다 | Spring Boot 테스트 자동 설정 — 인메모리 DB 로 바뀌는 것은 클래스패스에 내장 DB 가 있을 때의 동작으로 알려져 있다(확인 필요) |
| `given(...).willReturn(...)` 대로 가짜가 대답한다 | Mockito 라이브러리 |
| 단위 테스트가 「가장 빠르다」 | 아무도 보장하지 않는다 — 컨텍스트를 띄우지 않아서 대체로 그렇다는 경험칙 |
| 응답 JSON 필드 이름이 `name` · `email` 이다 | 프로젝트의 DTO 와 JSON 변환 설정 |
| 404 · 400 응답의 `code` 값 | 프로젝트의 예외 처리 코드 (예제 밖) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| URL · 상태 코드 · JSON 꼴 · 입력 검증 확인 | `@WebMvcTest` + `@MockBean` + `MockMvc` | `@SpringBootTest` (전체를 띄울 필요 없음) |
| 서비스의 분기 로직 · 예외 확인 | Spring 없이 `mock(...)` + `new` | `@MockBean` · 어떤 Spring 테스트 애너테이션도 |
| 쿼리 메서드가 DB 에서 제대로 찾나 | `@DataJpaTest` + `TestEntityManager` | 리포지토리를 `mock` 으로 바꾼 테스트 (DB 를 안 거침) |
| 생성 → 조회까지 전 계층이 맞물리나 | `@SpringBootTest(RANDOM_PORT)` + `TestRestTemplate` | 가짜를 끼운 슬라이스 테스트 |
| 테스트용 설정을 따로 쓰기 | `@ActiveProfiles("test")` | 운영 설정을 그대로 쓰기 |

## 핵심 문장

1. **테스트의 크기는 「무엇을 띄우고 무엇을 가짜로 바꾸나」로 정해진다** — 단위(Spring 없음) · 슬라이스(한 계층) · 통합(전체).
2. **`@WebMvcTest` 는 컨트롤러만 띄우므로 서비스는 `@MockBean` 으로 채운다** — 검사 대상은 웹 계층의 일이다.
3. **`MockMvc` 는 서버 없이, `TestRestTemplate` 은 임의 포트의 실제 서버로 요청한다.**
4. **서비스 로직은 Spring 없이 `mock(...)` 과 생성자 주입으로 검사하는 것이 가장 빠르다.**
5. **`@DataJpaTest` 는 저장 → flush → clear 뒤에 읽어, 결과가 DB 에서 온 것임을 분명히 한다.**

## 관련 자료

- `spring-rest-controller` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `spring-service-layer` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `spring-validation` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/spring-essentials.json` 의 `spring-test`

## 용어 풀이

- **단위 테스트** — 클래스 하나를 의존 대상과 떼어 검사하는 테스트.
- **슬라이스 테스트** — 한 계층에 필요한 빈만 띄우는 테스트.
- **통합 테스트** — 여러 계층을 실제로 이어 함께 검사하는 테스트.
- **빈(bean)** — Spring 컨텍스트가 만들고 관리하는 객체.
- **컨텍스트** — 빈을 만들어 서로 이어 주는 Spring 의 컨테이너.
- **목(mock)** — 미리 정한 대로만 대답하는 가짜 객체.
- **스텁(stub)** — 가짜의 대답을 미리 정해 두는 일.
- **`@MockBean`** — 컨텍스트 안의 빈을 목으로 바꾸는 애너테이션.
- **`MockMvc`** — 서블릿 컨테이너 없이 컨트롤러에 요청을 보내는 테스트 도구.
- **`TestRestTemplate`** — 통합 테스트에서 실제 HTTP 요청을 보내는 클라이언트.
- **`jsonPath`** — 응답 JSON 안의 위치를 `$.name` 처럼 가리키는 식.
- **`TestEntityManager`** — 테스트 전용 `EntityManager`.
- **1차 캐시** — 영속성 컨텍스트가 메모리에 들고 있는 엔티티 저장소.
- **flush** — 메모리의 변경을 DB 에 반영하는 일.
- **BDD** — given · when · then 으로 동작을 서술하는 방식.
- **프로파일** — 환경마다 다른 설정 묶음을 고르는 이름.
- **`RANDOM_PORT`** — 실제 서버를 임의 포트로 띄우라는 `@SpringBootTest` 설정.

## 더 들어가면

- Spring Boot 3.4 무렵부터 `@MockBean` 이 사용 중단(deprecated) 표시를 받고, Spring Framework 쪽의 `@MockitoBean` 이 대신하는 것으로 알려져 있다 (확인 필요).
- Spring 테스트는 설정이 같은 테스트 클래스끼리 컨텍스트를 캐시해 다시 쓴다고 알려져 있다 — `@MockBean` 조합이 클래스마다 다르면 컨텍스트를 새로 띄워 느려질 수 있다 (확인 필요).
- `RANDOM_PORT` 통합 테스트에 `@Transactional` 을 붙여도 서버 쪽 요청 처리는 다른 스레드의 트랜잭션이라 롤백되지 않는다고 알려져 있다 (확인 필요).
- `@DataJpaTest` 에서 인메모리 DB 대신 설정한 실제 DB 를 쓰려면 `@AutoConfigureTestDatabase(replace = NONE)` 같은 설정이 필요하다고 알려져 있다 (확인 필요).
- JPQL · 쿼리 메서드는 실행 전에 자동 flush 하고 SELECT 를 보내지만, 같은 식별자의 엔티티가 1차 캐시에 있으면 그 인스턴스를 돌려준다고 알려져 있다 (확인 필요).
- JUnit 5 의 `@Nested` 로 성공 · 실패 경우를 안쪽 클래스로 묶을 수 있다 — 원본은 import 만 하고 쓰지 않았다 (확인 필요).
