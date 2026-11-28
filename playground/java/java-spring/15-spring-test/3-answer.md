# java/java-spring/15 — Spring 테스트 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `EntityNotFoundException` 을 던지고, 메시지에 `999` 가 들어 있어야 한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`getUser(999L)` 는 값을 돌려주지 않고 `EntityNotFoundException` 을 던져야 한다.
그 예외의 메시지에는 문자열 `999` 가 들어 있어야 한다.
둘 중 하나라도 어긋나면(예외가 안 나거나, 종류가 다르거나, 메시지에 `999` 가 없으면) 테스트는 실패한다.

**왜 그런가**
가짜 리포지토리는 `findById(999L)` 에 `Optional.empty()` 를 돌려주도록 스텁되어 있다.
`assertThatThrownBy` 는 람다 안에서 예외가 나는지, `isInstanceOf` 로 종류를, `hasMessageContaining` 으로 메시지를 검사한다.
근거: 2-summary 「동작 방식 (3)」.

### 2. 컨텍스트를 만들지 못해 테스트가 실패한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`UserController` 가 필요로 하는 `UserService` 빈이 컨텍스트에 없으므로 컨텍스트 로드 단계에서 실패하고, 이 클래스의 테스트는 모두 실패한다.

**왜 그런가**
`@WebMvcTest(UserController.class)` 는 컨트롤러와 웹 관련 빈만 로드하고 서비스는 올리지 않는다.
그 빈 자리를 채우던 것이 `@MockBean` 이었다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」 (원본에 근거 없음 — 추론).

### 3. 실패한다 — `$.name` 검증에서 걸린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
가짜 서비스가 이름 `Lee` 인 응답을 돌려주므로 응답 JSON 의 `name` 은 `Lee` 가 된다.
상태 코드 검사(`isOk`)는 통과하지만, `jsonPath("$.name").value("Kim")` 에서 기대와 달라 테스트가 실패한다.

**왜 그런가**
MockMvc 는 가짜가 준 값을 컨트롤러가 그대로 JSON 으로 내보낸 결과를 검사한다.
`andExpect` 가 여럿이면 하나라도 맞지 않을 때 테스트가 실패한다.
근거: 2-summary 「동작 방식 (1)」.

### 4. 컨텍스트를 띄우지 않아 가장 빠르고, 로직만 떼어 볼 수 있기 때문이다

서비스의 분기(찾으면 변환, 없으면 예외)는 Spring 기능 없이도 확인할 수 있다.
그래서 컨텍스트를 띄우는 비용을 없애고, `mock(...)` 으로 리포지토리를 가짜로 만든 뒤 `new UserService(userRepository)` 로 직접 넣는다.
`@MockBean` 은 컨텍스트 안의 빈을 바꾸는 도구라 컨텍스트 없는 테스트에는 맞지 않는다.
근거: 원본 팁 「서비스 단위 테스트는 Spring 없이 Mockito 만으로 작성하면 가장 빠르다」, 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 5. 결과가 메모리에 남은 객체가 아니라 DB 에서 읽어 온 값이게 하려는 것이다

`persist` 한 `user` 는 `clear()` 전까지 1차 캐시에 남아 있다.
캐시를 비우면 `findByEmail` 의 결과가 방금 저장한 그 객체가 아니라 DB 에서 다시 읽은 값임이 분명해진다.
원본 주석은 이를 「실제 SELECT 실행 보장」이라고 적었지만, 쿼리 메서드는 캐시와 상관없이 SELECT 를 보낼 수 있어 이 표현은 정확도가 의심스럽다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 6. `MockMvc` 는 서버 없이 컨트롤러까지, `TestRestTemplate` 은 실제 서버로 HTTP 를 보낸다

`MockMvc` 는 서블릿 컨테이너를 띄우지 않고 요청을 컨트롤러로 흘려보낸다 — 실제 네트워크 요청은 없다.
`TestRestTemplate` 은 `RANDOM_PORT` 로 뜬 실제 서버에 그 포트를 붙여 진짜 HTTP 요청을 보낸다.
그래서 `MockMvc` 는 슬라이스 테스트에, `TestRestTemplate` 은 전체 흐름을 보는 통합 테스트에 쓰인다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 7. 예외를 응답으로 바꾸는 처리기와 요청 DTO 의 검증 설정이 있어야 한다

테스트는 서비스가 `EntityNotFoundException` 을 던지게 할 뿐, 그것을 404 와 `"ENTITY_NOT_FOUND"` 코드로 바꾸는 일은 하지 않는다.
잘못된 입력이 400 · `"VALIDATION_ERROR"` · 배열 `errors` 가 되는 것도 프로젝트의 검증 설정과 예외 처리 코드가 만든다.
그 코드가 없으면 같은 테스트가 실패한다.
근거: 2-summary 「어디서 틀리나 4」 (원본에 근거 없음 — 추론).

### 8. 컨텍스트가 있으면 `@MockBean`, 없으면 `mock(...)` 이다

`@MockBean` 은 Spring 컨텍스트 안의 빈을 가짜로 바꾼다 — 원본에서는 `@WebMvcTest` 의 `UserService` 자리를 채운다.
`mock(...)` 은 Mockito 가 그냥 가짜 객체를 만들고, 주입은 테스트가 생성자로 직접 한다 — 원본의 `UserServiceTest` 가 이 방식이다.
두 경우 모두 대답은 `given(...).willReturn(...)` 같은 스텁으로 정한다.
근거: 2-summary 「문법 — 형태와 규칙」의 규칙 불릿 · 「동작 방식 (1)」 · 「동작 방식 (3)」.

### 9. 단위 < 슬라이스(웹 · JPA) < 통합 순으로 넓어지고 느려진다

- 단위(Spring 없음): 서비스 로직 · 예외 분기.
- `@WebMvcTest`(컨트롤러 + 웹 빈, 서비스는 가짜): URL · 상태 코드 · JSON 꼴 · 입력 검증.
- `@DataJpaTest`(JPA 빈만): 리포지토리의 쿼리 메서드가 DB 에서 제대로 찾는지.
- `@SpringBootTest`(전체 컨텍스트 + 실제 서버): 생성 → 조회처럼 전 계층이 맞물리는 흐름.

웹 슬라이스와 JPA 슬라이스는 서로 다른 계층을 보므로 둘 사이에 크기 차례가 있는 것은 아니다.
근거: 원본 팁 전체, 2-summary 「한눈에」의 그림 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 사용자 API 를 네 가지 크기로 테스트하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 컨트롤러만 로드 · `test` 프로파일 | `@WebMvcTest(UserController.class)` · `@ActiveProfiles("test")` |
| 2. `MockMvc` · `ObjectMapper` 주입, 서비스 가짜 | `@Autowired MockMvc mockMvc` · `@Autowired ObjectMapper objectMapper` · `@MockBean UserService userService` |
| 3. 조회 성공 검증 | `getUser_Success()` 의 `given(...).willReturn(response)` · `status().isOk()` · `jsonPath("$.name")` · `jsonPath("$.email")` |
| 4. 조회 실패 검증 | `getUser_NotFound()` 의 `willThrow(new EntityNotFoundException(...))` · `isNotFound()` · `jsonPath("$.code")` |
| 5. 검증 실패 POST | `createUser_ValidationFail()` 의 `post(...)` · `contentType` · `objectMapper.writeValueAsString` · `isBadRequest()` · `jsonPath("$.errors").isArray()` |
| 6. 전체 컨텍스트 + 임의 포트 | `@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)` |
| 7. 생성 · 201 · 이름 | `restTemplate.postForEntity(...)` · `HttpStatus.CREATED` · `getBody().name()` |
| 8. id 로 조회 · 200 · 이메일 | `getBody().id()` · `restTemplate.getForEntity("/api/v1/users/{id}", ..., userId)` · `HttpStatus.OK` |
| 9. Spring 없이 가짜 + 생성자 주입 | `@BeforeEach setUp()` 의 `mock(UserRepository.class)` · `new UserService(userRepository)` |
| 10. 사용자 있을 때 | `UserServiceTest.getUser_Success()` 의 `Optional.of(user)` · `result.name()` |
| 11. 사용자 없을 때 예외 | `UserServiceTest.getUser_NotFound()` 의 `Optional.empty()` · `assertThatThrownBy(...)` |
| 12. JPA 빈만 · `test` 프로파일 | `@DataJpaTest` · `@ActiveProfiles("test")` |
| 13. 저장 · 반영 · 캐시 비우기 | `entityManager.persistAndFlush(user)` · `entityManager.clear()` |
| 14. `findByEmail` 결과 검증 | `assertThat(found).isPresent()` · `found.get().getName()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-spring/reference/spring-test.java`

```java
// [Spring 핵심] Spring 테스트
// 설명: @SpringBootTest, @WebMvcTest, MockMvc, TestRestTemplate을 사용한 통합 테스트와 슬라이스 테스트
// 팁: @WebMvcTest는 컨트롤러만 로드하므로 빠르고, 서비스는 @MockBean으로 대체한다. @SpringBootTest는 전체 컨텍스트를 로드하므로 통합 테스트에 적합하다. 서비스 단위 테스트는 Spring 없이 Mockito만으로 작성하면 가장 빠르다. @DataJpaTest는 JPA 관련 빈만 로드하여 Repository를 테스트한다.

// @DisplayName: 테스트 표시 이름
import org.junit.jupiter.api.DisplayName;
// @Nested: 내부 테스트 클래스 그룹화
import org.junit.jupiter.api.Nested;
// @Test: JUnit 5 테스트 메서드
import org.junit.jupiter.api.Test;
// @Autowired: 테스트에서도 빈 주입에 사용
import org.springframework.beans.factory.annotation.Autowired;
// @WebMvcTest: 웹 계층 슬라이스 테스트 (컨트롤러만 로드)
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
// @SpringBootTest: 전체 컨텍스트 로드 통합 테스트
import org.springframework.boot.test.context.SpringBootTest;
// @MockBean: Spring 컨텍스트 내 빈을 Mock으로 대체
import org.springframework.boot.test.mock.mockito.MockBean;
// TestRestTemplate: 통합 테스트용 REST 클라이언트
import org.springframework.boot.test.web.client.TestRestTemplate;
// 미디어 타입 (JSON 등)
import org.springframework.http.MediaType;
// @ActiveProfiles: 테스트 시 활성화할 프로파일 지정
import org.springframework.test.context.ActiveProfiles;
// MockMvc: 서블릿 컨테이너 없이 컨트롤러 테스트
import org.springframework.test.web.servlet.MockMvc;

// 인자 매처 (any() 등)
import static org.mockito.ArgumentMatchers.any;
// BDD 스타일 Mockito (given/willReturn)
import static org.mockito.BDDMockito.given;
// MockMvc 요청 빌더 (get, post 등)
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
// MockMvc 결과 매처 (status, jsonPath 등)
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
// AssertJ 어설션
import static org.assertj.core.api.Assertions.assertThat;

// === 1. @WebMvcTest - 컨트롤러 슬라이스 테스트 ===
// @WebMvcTest(UserController.class): 해당 컨트롤러와 웹 관련 빈만 로드 (빠른 슬라이스 테스트)
@WebMvcTest(UserController.class)  // 해당 컨트롤러만 로드
// 테스트 프로파일 활성화
@ActiveProfiles("test")
class UserControllerTest {

    // MockMvc 주입 (자동 설정됨)
    @Autowired
    private MockMvc mockMvc;

    // @MockBean: 컨텍스트의 UserService를 Mock 객체로 대체
    @MockBean  // Service를 Mock으로 대체
    private UserService userService;

    // JSON 직렬화 도구
    @Autowired
    private ObjectMapper objectMapper;

    // 단건 조회 성공 테스트
    @Test
    @DisplayName("GET /api/v1/users/{id} - 사용자 조회 성공")
    void getUser_Success() throws Exception {
        // given
        // 응답 DTO 준비
        UserResponse response = new UserResponse(1L, "Kim", "kim@test.com",
            LocalDateTime.now());
        // BDD: getUser(1L) 호출 시 response 반환하도록 설정
        given(userService.getUser(1L)).willReturn(response);

        // when & then
        // GET 요청 + 검증
        mockMvc.perform(get("/api/v1/users/{id}", 1L)
                .accept(MediaType.APPLICATION_JSON))
            // 200 OK 검증
            .andExpect(status().isOk())
            // JSON path로 필드값 검증
            .andExpect(jsonPath("$.name").value("Kim"))
            .andExpect(jsonPath("$.email").value("kim@test.com"));
    }

    // 404 케이스 테스트
    @Test
    @DisplayName("GET /api/v1/users/{id} - 존재하지 않는 사용자")
    void getUser_NotFound() throws Exception {
        // given
        // 예외를 던지도록 설정
        given(userService.getUser(999L))
            .willThrow(new EntityNotFoundException("User", 999L));

        // when & then
        // 404 + 에러 코드 검증
        mockMvc.perform(get("/api/v1/users/{id}", 999L))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.code").value("ENTITY_NOT_FOUND"));
    }

    // 검증 실패 테스트
    @Test
    @DisplayName("POST /api/v1/users - 유효성 검증 실패")
    void createUser_ValidationFail() throws Exception {
        // given
        // 잘못된 입력값 (빈 이름, 잘못된 이메일, 짧은 비밀번호)
        CreateUserRequest request = new CreateUserRequest("", "invalid-email", "short");

        // when & then
        // POST 요청 후 400 + 검증 에러 응답 확인
        mockMvc.perform(post("/api/v1/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.code").value("VALIDATION_ERROR"))
            .andExpect(jsonPath("$.errors").isArray());
    }
}

// === 2. @SpringBootTest - 전체 통합 테스트 ===
// @SpringBootTest: 전체 컨텍스트 로드. RANDOM_PORT: 임의 포트로 실제 서버 기동
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class UserIntegrationTest {

    // TestRestTemplate: 실제 HTTP 호출 (랜덤 포트 자동 적용)
    @Autowired
    private TestRestTemplate restTemplate;

    // 실제 레포지토리 (DB 검증용)
    @Autowired
    private UserRepository userRepository;

    @Test
    @DisplayName("사용자 생성부터 조회까지 전체 흐름")
    void createAndGetUser() {
        // given
        // 생성 요청 DTO
        CreateUserRequest request = new CreateUserRequest(
            "TestUser", "test@example.com", "P@ssword123");

        // when - 생성
        // POST 요청
        ResponseEntity<UserResponse> createResponse = restTemplate
            .postForEntity("/api/v1/users", request, UserResponse.class);

        // then
        // 201 + 본문 검증
        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(createResponse.getBody().name()).isEqualTo("TestUser");

        // 생성된 ID 추출
        Long userId = createResponse.getBody().id();

        // when - 조회
        // GET 요청 (URL 변수 치환)
        ResponseEntity<UserResponse> getResponse = restTemplate
            .getForEntity("/api/v1/users/{id}", UserResponse.class, userId);

        // then
        // 200 + 이메일 검증
        assertThat(getResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(getResponse.getBody().email()).isEqualTo("test@example.com");
    }
}

// === 3. Service 단위 테스트 (Spring 없이) ===
// Spring 컨텍스트 없는 순수 단위 테스트 (가장 빠름)
class UserServiceTest {

    // 테스트 대상
    private UserService userService;
    // 의존성 (Mock)
    private UserRepository userRepository;

    // 각 테스트 전 셋업
    @BeforeEach
    void setUp() {
        // Mockito mock 객체 생성
        userRepository = mock(UserRepository.class);
        // 직접 객체 생성으로 주입
        userService = new UserService(userRepository);
    }

    @Test
    @DisplayName("존재하는 사용자 조회")
    void getUser_Success() {
        // given
        // 도메인 객체 준비
        User user = User.create("Kim", "kim@test.com");
        // findById 호출 시 Optional 반환 설정
        given(userRepository.findById(1L)).willReturn(Optional.of(user));

        // when
        // 실제 호출
        UserResponse result = userService.getUser(1L);

        // then
        // 결과 검증
        assertThat(result.name()).isEqualTo("Kim");
    }

    @Test
    @DisplayName("존재하지 않는 사용자 조회 시 예외")
    void getUser_NotFound() {
        // given
        // 빈 Optional 반환
        given(userRepository.findById(999L)).willReturn(Optional.empty());

        // when & then
        // 예외 발생 검증
        assertThatThrownBy(() -> userService.getUser(999L))
            .isInstanceOf(EntityNotFoundException.class)
            .hasMessageContaining("999");
    }
}

// === 4. @DataJpaTest - Repository 슬라이스 테스트 ===
// @DataJpaTest: JPA 관련 빈만 로드 (인메모리 DB + 트랜잭션 자동 롤백)
@DataJpaTest
@ActiveProfiles("test")
class UserRepositoryTest {

    // 실제 레포지토리 주입
    @Autowired
    private UserRepository userRepository;

    // TestEntityManager: 테스트 전용 EntityManager (영속화/플러시/클리어)
    @Autowired
    private TestEntityManager entityManager;

    @Test
    @DisplayName("이메일로 사용자 조회")
    void findByEmail() {
        // given
        // 사용자 도메인 생성
        User user = User.create("Kim", "kim@test.com");
        // persist + flush로 DB에 즉시 반영
        entityManager.persistAndFlush(user);
        // 1차 캐시 비우기 - 실제 SELECT 실행 보장
        entityManager.clear();  // 1차 캐시 초기화

        // when
        // 메서드 호출
        Optional<User> found = userRepository.findByEmail("kim@test.com");

        // then
        // 결과 검증
        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo("Kim");
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**

- 네 클래스는 「무엇을 띄우나」만 다르고, 모두 given · when · then 의 같은 뼈대를 쓴다.
- 컨텍스트가 있는 테스트(`@WebMvcTest`)는 `@MockBean`, 없는 테스트(`UserServiceTest`)는 `mock(...)` 으로 가짜를 만든다.
- MockMvc 는 `perform(...)` 뒤에 `andExpect` 를 사슬로 이어 실행과 검증을 한 줄에 둔다.
- 통합 테스트는 POST 응답의 `id` 를 GET 의 URL 변수로 넘겨 두 요청을 잇는다.
- 리포지토리 테스트는 `persistAndFlush` → `clear` → 조회 순서로, 결과가 DB 에서 온 값임을 분명히 한다.
- 정답 코드는 import 가 일부 빠져 있어(2-summary 「어디서 틀리나 6」) 실제 프로젝트에서는 `ObjectMapper` · `Optional` · `BeforeEach` · `DataJpaTest` 등을 보태야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
