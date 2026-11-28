# java/java-spring/15 — Spring 테스트 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 서비스 단위 테스트에서 리포지토리가 빈 `Optional` 을 돌려주면 (예측)

```java
// 질문용 발췌
given(userRepository.findById(999L)).willReturn(Optional.empty());

assertThatThrownBy(() -> userService.getUser(999L))
    .isInstanceOf(EntityNotFoundException.class)
    .hasMessageContaining("999");
```

- 이 테스트가 통과하려면 `userService.getUser(999L)` 는 무엇을 해야 하나?

### 2. `@WebMvcTest` 에서 `@MockBean` 줄을 지우면 (예측)

```java
// 질문용 발췌
@WebMvcTest(UserController.class)
class UserControllerTest {
    @Autowired private MockMvc mockMvc;
    // @MockBean private UserService userService;   ← 지웠다
}
```

- `UserController` 가 `UserService` 를 주입받는다면 이 테스트 클래스는 어떻게 되나?

### 3. 준비한 응답의 이름을 바꾸면 (예측)

```java
// 질문용 발췌
UserResponse response = new UserResponse(1L, "Lee", "kim@test.com", LocalDateTime.now());
given(userService.getUser(1L)).willReturn(response);

mockMvc.perform(get("/api/v1/users/{id}", 1L))
    .andExpect(status().isOk())
    .andExpect(jsonPath("$.name").value("Kim"))
    .andExpect(jsonPath("$.email").value("kim@test.com"));
```

- 이 테스트는 통과하나, 실패한다면 어느 검증에서 걸리나?

### 4. 서비스 테스트에서 Spring 을 전혀 쓰지 않는 까닭 (왜)

- `UserServiceTest` 가 `@SpringBootTest` 도 `@MockBean` 도 없이 `mock(...)` 과 `new UserService(...)` 만 쓰는 이유는 무엇인가?

### 5. `persistAndFlush` 다음에 `clear()` 를 부르는 까닭 (왜)

- `UserRepositoryTest` 가 저장 뒤 `findByEmail` 을 부르기 전에 1차 캐시를 비우는 이유는 무엇인가?

### 6. `MockMvc` 와 `TestRestTemplate` 이 닿는 곳 (경계)

- 두 도구는 각각 요청을 어디까지 실제로 보내나?

### 7. 컨트롤러 테스트에서 404 · 400 응답이 기대대로 나오는 조건 (경계)

- `getUser_NotFound` · `createUser_ValidationFail` 이 통과하려면 테스트 코드 바깥에 무엇이 있어야 하나?

### 8. `@MockBean` 과 `mock(...)` 의 쓰임새 (연결)

- 둘 다 가짜를 만드는데, 어떤 테스트에 어느 쪽을 쓰고 차이는 무엇인가?

### 9. 네 테스트를 범위와 속도로 줄 세우기 (연결)

- 단위 · `@WebMvcTest` · `@DataJpaTest` · `@SpringBootTest` 를 띄우는 범위에 따라 어떻게 나누고, 각각 무엇을 검사하는 데 맞나?

## 실습

### 실습 1. 사용자 API 를 네 가지 크기로 테스트하기

**만들 것** — 사용자 조회 · 생성 API 를 단위 · 컨트롤러 슬라이스 · 리포지토리 슬라이스 · 통합의 네 테스트 클래스로 검사한다.

**준비물** — Spring Boot 테스트 스타터(JUnit 5 · Mockito · AssertJ · MockMvc 포함)와 JPA, 그리고 프로젝트 쪽 `UserController` · `UserService` · `UserRepository`(`findById` · `findByEmail`) · `User`(`create` · `getName`) · `UserResponse` · `CreateUserRequest` · `EntityNotFoundException`, 예외를 404 · 400 JSON 응답으로 바꾸는 처리기가 필요하다.
정답 코드는 이 클래스들이 있다고 가정하고 테스트만 담는다.

**요구 조건**

1단계 — 컨트롤러 슬라이스 (`UserControllerTest`)
1. `UserController` 만 로드하는 웹 슬라이스 테스트로 만들고 `test` 프로파일을 켠다.
2. `MockMvc` 와 `ObjectMapper` 를 주입받고, `UserService` 는 컨텍스트 안의 가짜 빈으로 바꾼다.
3. 조회 성공: 서비스가 `1L` 에 이름 `Kim` · 이메일 `kim@test.com` 인 응답을 돌려주게 하고, `GET /api/v1/users/{id}` 가 200 이며 JSON 의 `name` · `email` 이 그 값인지 검증한다.
4. 조회 실패: 서비스가 `999L` 에 `EntityNotFoundException` 을 던지게 하고, 404 이며 `$.code` 가 `ENTITY_NOT_FOUND` 인지 검증한다.
5. 검증 실패: 빈 이름 · 잘못된 이메일 · 짧은 비밀번호로 `POST /api/v1/users` 를 JSON 본문으로 보내고, 400 · `$.code` 가 `VALIDATION_ERROR` · `$.errors` 가 배열인지 검증한다.

2단계 — 통합 (`UserIntegrationTest`)
6. 전체 컨텍스트를 띄우고 실제 서버를 임의 포트로 기동하며 `test` 프로파일을 켠다.
7. `TestRestTemplate` 으로 사용자를 생성(POST)하고 201 과 응답 이름을 검증한다.
8. 응답에서 꺼낸 `id` 로 다시 조회(GET)하고 200 과 이메일을 검증한다.

3단계 — 서비스 단위 (`UserServiceTest`)
9. Spring 없이, 테스트마다 리포지토리 가짜를 만들고 생성자로 서비스에 넣는다.
10. 리포지토리가 사용자를 돌려줄 때 서비스 결과의 이름을 검증한다.
11. 리포지토리가 빈 `Optional` 을 돌려줄 때 `EntityNotFoundException` 이 나고 메시지에 `999` 가 들어 있는지 검증한다.

4단계 — 리포지토리 슬라이스 (`UserRepositoryTest`)
12. JPA 관련 빈만 로드하고 `test` 프로파일을 켠다.
13. `TestEntityManager` 로 사용자를 저장 · 즉시 반영한 뒤 1차 캐시를 비운다.
14. `findByEmail` 결과가 있고 이름이 `Kim` 인지 검증한다.

**시작 코드**

```java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
// TODO: 슬라이스 · 통합 테스트 애너테이션, MockMvc, TestRestTemplate, TestEntityManager import
// TODO: given · status · jsonPath · get · post · assertThat 등 정적 import

// === 1. 컨트롤러 슬라이스 ===
// TODO: UserController 만 로드
@ActiveProfiles("test")
class UserControllerTest {

    // TODO: MockMvc 주입
    // TODO: UserService 를 컨텍스트 안의 가짜로
    // TODO: ObjectMapper 주입

    @Test
    @DisplayName("GET /api/v1/users/{id} - 사용자 조회 성공")
    void getUser_Success() throws Exception {
        // given
        UserResponse response = new UserResponse(1L, "Kim", "kim@test.com",
            LocalDateTime.now());
        // TODO: getUser(1L) 이 response 를 돌려주게

        // when & then
        // TODO: GET 요청 → 200 · $.name · $.email 검증
    }

    @Test
    @DisplayName("GET /api/v1/users/{id} - 존재하지 않는 사용자")
    void getUser_NotFound() throws Exception {
        // TODO: getUser(999L) 이 EntityNotFoundException 을 던지게
        // TODO: GET 요청 → 404 · $.code 검증
    }

    @Test
    @DisplayName("POST /api/v1/users - 유효성 검증 실패")
    void createUser_ValidationFail() throws Exception {
        CreateUserRequest request = new CreateUserRequest("", "invalid-email", "short");
        // TODO: JSON 본문으로 POST → 400 · $.code · $.errors 배열 검증
    }
}

// === 2. 통합 ===
// TODO: 전체 컨텍스트 + 임의 포트 서버
@ActiveProfiles("test")
class UserIntegrationTest {

    // TODO: TestRestTemplate 주입
    @Autowired
    private UserRepository userRepository;

    @Test
    @DisplayName("사용자 생성부터 조회까지 전체 흐름")
    void createAndGetUser() {
        CreateUserRequest request = new CreateUserRequest(
            "TestUser", "test@example.com", "P@ssword123");
        // TODO: POST → 201 · 이름 검증
        // TODO: 응답의 id 꺼내기
        // TODO: GET → 200 · 이메일 검증
    }
}

// === 3. 서비스 단위 (Spring 없이) ===
class UserServiceTest {

    private UserService userService;
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        // TODO: 리포지토리 가짜 만들고 생성자로 서비스에 넣기
    }

    @Test
    @DisplayName("존재하는 사용자 조회")
    void getUser_Success() {
        User user = User.create("Kim", "kim@test.com");
        // TODO: findById(1L) → Optional.of(user)
        // TODO: getUser(1L) 결과 이름 검증
    }

    @Test
    @DisplayName("존재하지 않는 사용자 조회 시 예외")
    void getUser_NotFound() {
        // TODO: findById(999L) → Optional.empty()
        // TODO: 예외 종류 · 메시지 검증
    }
}

// === 4. 리포지토리 슬라이스 ===
// TODO: JPA 관련 빈만 로드
@ActiveProfiles("test")
class UserRepositoryTest {

    @Autowired
    private UserRepository userRepository;
    // TODO: TestEntityManager 주입

    @Test
    @DisplayName("이메일로 사용자 조회")
    void findByEmail() {
        User user = User.create("Kim", "kim@test.com");
        // TODO: 저장 + 즉시 반영, 1차 캐시 비우기
        // TODO: findByEmail 결과 존재 · 이름 검증
    }
}
```

**확인 방법** — 프로젝트에서 `./gradlew test`(또는 `mvn test`)로 테스트를 돌려 네 클래스의 테스트 메서드 여덟 개가 모두 통과하는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
