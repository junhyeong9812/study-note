# software-design/34-middleware-filter-interceptor-chains — 정답

## 정답

### 1. 흩어진 요청 처리와 체인

- 컨트롤러마다 쓰면 어떤 곳은 인증을 빠뜨리고, 어떤 곳은 순서가 다르다. 정책이 바뀌면 N곳을 고친다.
- 체인으로 모으면 **한 곳에서 순서가 정해진다.** 등록 순서가 곧 실행 순서다.
- 뼈대: GoF 책임 연쇄(Chain of Responsibility). 각 고리가 처리하고 넘기거나, 막고 직접 응답한다.

### 2. 필터·인터셉터 실행 순서

(실험 A, Tomcat embed 10.1.46 · Spring Framework 6.2.11)

```text
  → Filter F1-encoding
  → Filter F2-security
    → preHandle I1
    → preHandle I2
      * 컨트롤러 hello
    ← postHandle I2
    ← postHandle I1
    ← afterCompletion I2
    ← afterCompletion I1
  ← Filter F2-security
  ← Filter F1-encoding
```

- 들어갈 때 등록 순서, 나올 때 역순. 필터(서블릿 컨테이너 층)가 인터셉터(Spring MVC 층)를 감싼다.

### 3. `preHandle=false`

(실험 A `/deny`)

```text
    → preHandle I1
    → preHandle I2 = false (403)
    ← afterCompletion I1
```

- 컨트롤러·`postHandle`은 불리지 않는다.
- `afterCompletion`은 `preHandle`이 true를 돌려준 인터셉터만, 역순으로 불린다 → I1만. I2 자신의 `afterCompletion`은 불리지 않는다(spring-webmvc 6.2.11 `HandlerExecutionChain.applyPreHandle`).

### 4. Express 등록 순서

(실험 B, Express 5.2.1)

- `log → json → auth`
  - 인증 없는 요청도 로그에 남는다(`[log] ... body=undefined user=-` 뒤 `[auth] 401`).
  - 바디 파서 전이라 `body=undefined`, 인증 전이라 `user=-`.
- `json → auth → log`
  - 인증 없는 요청은 로그에 안 남는다(`[auth] 401`만).
  - 인증된 요청은 바디와 사용자가 찍힌다: `body={"amount":1000,"card":"4111-1111"} user=kim`.
- 두 번째 순서의 위험: 카드 번호 같은 민감 정보가 로그에 그대로 남는다. 바디를 찍는 로거에는 마스킹이 필요하다. 첫 번째 순서는 인증 실패 시도를 남기는 장점이 있지만, 인증 안 된 요청의 처리 비용이 앞쪽 고리에서 생긴다.

### 5. 다음 고리 호출 누락

(실험 A·B·C)

- Express: 응답 없이 매달린다. 클라이언트가 스스로 타임아웃 → `TimeoutError (1505ms)`. 문서도 "the request will be left hanging"이라고 적는다.
- Koa 2.16.4: `next()` 누락이면 `404 Not Found`. `await` 없이 `next()`만 불러도 뒤 미들웨어가 본문을 쓰기 전에 응답이 나가 404였다.
- Servlet Filter(Tomcat 10.1.46): `chain.doFilter`를 안 부르면 컨트롤러가 실행되지 않고 **200 + 빈 본문**이 갔다. 명세상 필터가 체인을 막으면 응답을 채울 책임이 그 필터에 있다.

### 6. 필터 순서를 정하는 것

- Servlet 6.0 §6.2.4: URL 패턴이 맞는 `<filter-mapping>`이 배포 기술자에 나온 순서대로, 다음으로 서블릿 이름이 맞는 매핑이 나온 순서대로.
- `@WebFilter`에는 순서 속성이 없다(Tomcat 10.1.46 API를 `javap`로 확인).
- Spring Boot 3.5 문서
  - 줄 수 있는 방법: 필터 **클래스**에 `@Order` 또는 `Ordered` 구현, `FilterRegistrationBean.setOrder`, `@FilterRegistration`의 `order`.
  - 줄 수 없는 방법: 필터를 만드는 **빈 메서드**에 `@Order`를 붙이는 것.

### 7. 인터셉터 vs 필터, NestJS 순서

- 필터: 서블릿 컨테이너 층. 요청·응답 객체를 래퍼로 바꿔 넘길 수 있다. 특정 콘텐츠 유형이나 요청 전체에 매핑하기 좋다(Javadoc의 지침: multipart·GZIP 같은 요청·응답 내용 처리).
- 인터셉터: Spring MVC 층. 핸들러 앞뒤 처리와 핸들러 실행 금지만 할 수 있고 요청·응답 객체를 바꿔 넘기지 못한다(Javadoc).
- Spring은 `HandlerInterceptor` Javadoc에서 인터셉터가 애너테이션 컨트롤러 경로 매칭과 어긋날 수 있어 보안 계층으로 적합하지 않다고 하고, Spring Security 또는 서블릿 필터 체인에 통합된 방식을 권한다.
- NestJS 「Request lifecycle」 요약: 미들웨어 → 가드 → 인터셉터(컨트롤러 전) → 파이프 → 컨트롤러 → 서비스 → 인터셉터(요청 후) → 예외 필터. 인터셉터는 들어갈 때 전역 → 컨트롤러 → 라우트, 나올 때 역순.

### 8. 필터가 두 번 실행된다

- 원인 후보
  - 필터를 `@Component`/`@Bean`으로 선언해 Spring Boot가 서블릿 컨테이너에 자동 등록했고, 같은 필터를 Spring Security 체인에도 넣었다. Spring Security 문서는 이 경우 컨테이너에서 한 번, Security에서 한 번, 다른 순서로 불릴 수 있다고 적는다.
  - 같은 필터를 다른 이름으로 두 번 등록했다(`FilterRegistrationBean` 둘).
- 대처
  - `FilterRegistrationBean`을 선언하고 `setEnabled(false)`로 컨테이너 자동 등록을 끈다(Spring Security 문서).
  - `logging.level.web=debug`로 기동해 등록된 필터 목록·순서를 확인한다(Spring Boot 문서).
  - `OncePerRequestFilter`는 요청 속성 `<필터 이름>.FILTERED`로 같은 요청의 재실행을 건너뛰지만, 등록을 하나로 만드는 것이 근본 대처다.
