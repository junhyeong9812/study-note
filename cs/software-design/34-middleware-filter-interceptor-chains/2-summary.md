# software-design/34-middleware-filter-interceptor-chains — 미들웨어·필터·인터셉터 체인: 등록 순서가 실행 순서 — 정리 (힌트)

## 해결하는 문제

요청 하나에 붙는 일은 많다. 문자 인코딩, 요청 ID, 인증, 권한, 바디 파싱, 로깅, 압축, 예외 → 응답 변환. 이것을 컨트롤러마다 쓰면 빠뜨리는 곳이 생기고, 순서가 컨트롤러마다 달라진다.

```text
 체인 없이                                   체인으로
 handlerA() { 인증; 파싱; 로깅; 본업 }        요청 ─> [인코딩] ─> [인증] ─> [파싱] ─> [로깅] ─> handlerA
 handlerB() { 파싱; 본업 }  ← 인증 빠뜨림                                               └> handlerB
 handlerC() { 로깅; 인증; 본업 } ← 순서 다름   응답 <─ 같은 고리를 거꾸로 거쳐 나온다
```

- *미들웨어(middleware)*: 요청과 응답 사이에 끼워 넣는 처리 단계. 다음 단계로 넘길지 여기서 끝낼지 스스로 정한다.
- *체인(chain)*: 그런 단계들을 순서대로 이어 붙인 것. 앞 고리가 다음 고리를 부른다.

쉬운 예: 공항 출국 절차다. 탑승권 확인 → 보안 검색 → 출국 심사 순서로 줄을 선다. 보안 검색대가 통과시키지 않으면 뒤 단계로 못 간다. 순서를 바꾸면(심사 먼저) 검색 안 된 사람이 심사대에 선다.\
똑같은 구조다.\
실무 예: Servlet Filter 체인(Spring Security 포함), Spring MVC `HandlerInterceptor`, Express·Koa의 `app.use()`, NestJS의 미들웨어 → 가드 → 인터셉터 → 파이프.

뼈대는 GoF *책임 연쇄(Chain of Responsibility)* 패턴이다. 기초는 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) 「13. Chain of Responsibility」.

## 동작·원리

### 1. 체인의 기본형 — 다음 고리를 부를지 내가 정한다

```text
 고리 1 ──next()──> 고리 2 ──next()──> 고리 3 ──> 핸들러
   │                  │
   │                  └─ next()를 안 부르면 여기서 끝: 직접 응답을 써야 한다
   └─ next() 앞 코드 = 들어갈 때, next() 뒤 코드 = 나올 때
```

- Servlet 명세(Jakarta Servlet 6.0 §6.2.1): 필터는 `FilterChain.doFilter`로 다음 고리를 부른다. 부르지 않으면 요청을 막는 것이고, 응답을 채우는 책임은 그 필터에 있다. 필터와 체인 끝의 대상 서블릿은 같은 호출 스레드에서 실행돼야 한다(§6.2.3).
- Express 문서(「Using middleware」·「Writing middleware」): 미들웨어가 요청·응답 주기를 끝내지 않으면 `next()`를 불러야 한다. 아니면 요청이 "hanging" 상태로 남는다. 먼저 로드한 미들웨어가 먼저 실행된다.

### 2. 양파 — 들어간 역순으로 나온다

```text
          ┌──────────── F1 ────────────┐
          │   ┌──────── F2 ────────┐   │
 요청 ──> │ → │ → ┌── I1·I2 ──┐ →  │   │
          │   │   │ 컨트롤러   │    │   │
 응답 <── │ ← │ ← └───────────┘ ←  │   │
          │   └────────────────────┘   │
          └────────────────────────────┘
 호출 스택이 그대로 양파다: F1이 F2를 부르고, F2가 끝나야 F1의 나머지가 돈다
```

- Koa는 이것을 `async (ctx, next) => { 앞; await next(); 뒤; }`로 드러낸다. `koa-compose` 4.1.0 소스는 `dispatch(i)`가 `i+1`번째를 부르는 재귀이고, 같은 고리에서 `next()`를 두 번 부르면 `next() called multiple times`로 거부한다.

### 3. 자바 웹의 두 층 — 필터와 인터셉터

```text
 Tomcat ── FilterChain [F1 → F2 → F3 ...] ── DispatcherServlet ── HandlerInterceptor [I1 → I2] ── 컨트롤러
           (서블릿 컨테이너 층: web.xml/등록 순서)                    (Spring MVC 층: 등록 순서)
```

- *Servlet Filter*: 서블릿 컨테이너가 관리한다. 요청·응답 객체를 래퍼로 바꿔 넘길 수 있다(§6.2.2). 체인 순서는 `<filter-mapping>` 중 URL 패턴이 맞는 것이 **배포 기술자에 나온 순서대로**, 다음에 서블릿 이름이 맞는 것이 순서대로다(§6.2.4).
  - `@WebFilter`에는 순서 속성이 없다(Tomcat 10.1.46의 `jakarta.servlet.annotation.WebFilter`를 `javap`로 확인 — `urlPatterns`·`servletNames`·`dispatcherTypes` 등만 있다).
  - Spring Boot는 `Filter` 빈을 컨테이너에 등록한다. 순서는 필터 클래스에 `@Order`를 달거나 `Ordered`를 구현해서 준다. **빈 메서드에 붙인 `@Order`로는 필터 순서를 정할 수 없다.** 클래스를 못 고치면 `FilterRegistrationBean.setOrder`, 또는 애너테이션 `@FilterRegistration`의 `order`(Spring Boot 3.5 문서 「Servlets, Filters, and Listeners」).
- *HandlerInterceptor*: Spring MVC 안에서 핸들러(컨트롤러 메서드) 앞뒤에 끼운다. 메서드 셋이다.
  - `preHandle` — 등록 순서대로. `false`를 돌려주면 핸들러를 실행하지 않는다.
  - `postHandle` — 핸들러가 성공한 뒤, 역순으로.
  - `afterCompletion` — 요청이 끝난 뒤, 역순으로. `preHandle`이 **true를 돌려준 인터셉터만** 불린다.
  - spring-webmvc 6.2.11 `HandlerExecutionChain.applyPreHandle` 소스: `preHandle`이 false면 그때까지 통과한 인덱스부터 거꾸로 `afterCompletion`을 부르고 멈춘다.
  - 같은 Javadoc: 인터셉터는 필터와 비슷하지만 요청·응답 객체를 바꿔 넘길 수 없다. 핸들러에 붙는 세밀한 전처리(공통 핸들러 코드, 권한 검사 같은 것)는 인터셉터 후보라고 하면서도, 애너테이션 컨트롤러의 경로 매칭과 어긋날 수 있어 **보안 계층**으로는 적합하지 않고 Spring Security나 서블릿 필터 체인에 통합된 방식을 권한다.

### 실험 A: 필터 2개 + 인터셉터 2개의 실행 순서

임베디드 Tomcat에 필터 F1(인코딩 흉내)·F2(보안 흉내)·F3(`/forgot`에서 `chain.doFilter` 누락)를 등록하고, Spring MVC에 인터셉터 I1·I2(I2는 `/deny`에서 `preHandle=false`)를 등록했다.

```java
static class LogFilter implements Filter {
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain) throws IOException, ServletException {
        System.out.println("  → Filter " + name);
        chain.doFilter(req, res);                       // 다음 고리로
        System.out.println("  ← Filter " + name);
    }
}
public void addInterceptors(InterceptorRegistry r) {
    r.addInterceptor(new LogInterceptor("I1", false));
    r.addInterceptor(new LogInterceptor("I2", true));
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, Tomcat embed 10.1.46 · Spring Framework 6.2.11(webmvc), 2026-10-02 — `scratchpad/sd/30/e34/src/exp34/Main.java`)

```text
== GET /hello
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
  응답 200 body='hello'
== GET /deny
  → Filter F1-encoding
  → Filter F2-security
    → preHandle I1
    → preHandle I2 = false (403)
    ← afterCompletion I1
  ← Filter F2-security
  ← Filter F1-encoding
  응답 403 body='<html…>'
== GET /forgot
  → Filter F1-encoding
  → Filter F2-security
  → ForgetfulFilter: chain.doFilter 호출 안 함
  ← Filter F2-security
  ← Filter F1-encoding
  응답 200 body=''
```

- 등록 순서대로 들어가고 역순으로 나왔다. 필터가 인터셉터를 감쌌다.
- `/deny`: I2가 false를 돌려주자 컨트롤러가 실행되지 않았다. `afterCompletion`은 통과한 I1만 불렸다(I2 자신은 안 불렸다).
- `/forgot`: 필터가 `chain.doFilter`를 빼먹자 컨트롤러가 실행되지 않았는데 **응답은 200, 본문은 빈 문자열**이었다. 에러가 아니라 "성공한 빈 응답"으로 보인다.

### 실험 B: Express — 등록 순서와 `next()` 누락

```js
const mw = {
  log:  (req, res, next) => { console.log(`    [log ] ${req.method} ${req.url} body=${JSON.stringify(req.body)} user=${req.user ?? '-'}`); next(); },
  json: express.json(),
  auth: (req, res, next) => {
    if (req.get('authorization') !== 'Bearer ok') { console.log('    [auth] 401'); return res.status(401).send('unauthorized'); }
    req.user = 'kim'; next();
  },
};
for (const name of order) app.use(mw[name]);
app.use('/stuck', (req, res, next) => { console.log('    [stuck] 아무것도 안 하고 끝남 (next 누락)'); });
```

(실험, Express 5.2.1, Node 18.19.1 호스트, 2026-10-02 — `scratchpad/sd/30/e34js/express-order.js`. ms 값은 실행마다 다르다)

```text
== 등록 순서 log → json → auth
 인증 없는 요청:
    [log ] POST /pay body=undefined user=-
    [auth] 401
  -> 401 unauthorized (245ms)
 인증 있는 요청:
    [log ] POST /pay body=undefined user=-
  -> 200 paid 1000 by kim (21ms)
== 등록 순서 json → auth → log
 인증 없는 요청:
    [auth] 401
  -> 401 unauthorized (31ms)
 인증 있는 요청:
    [log ] POST /pay body={"amount":1000,"card":"4111-1111"} user=kim
  -> 200 paid 1000 by kim (18ms)
== next() 누락 (/stuck), 클라이언트 타임아웃 1500ms
    [stuck] 아무것도 안 하고 끝남 (next 누락)
  -> 클라이언트 TimeoutError (1505ms)
```

- `log → json → auth`: 로깅이 인증보다 먼저라 **인증 안 된 요청도 로그에 남았다.** 바디 파서보다 먼저라 `body=undefined`, 인증 전이라 `user=-`다.
- `json → auth → log`: 인증 실패 요청은 로그에 안 남았고, 통과한 요청은 바디와 사용자가 찍혔다. 대신 **카드 번호가 그대로 로그에 찍혔다** — 바디를 찍는 로거는 마스킹이 필요하다.
- `next()` 누락: 서버는 아무 에러도 내지 않았고 클라이언트가 1.5초 뒤 스스로 타임아웃했다.

### 실험 C: Koa — 양파와 `next()` 누락

(실험, Koa 2.16.4 · koa-compose 4.1.0, Node 18.19.1, 2026-10-02 — `scratchpad/sd/30/e34js/koa-onion.js`, `koa-missing.js`)

```text
  → A timing 들어감
  → B error-handler 들어감
  → C auth 들어감
    * 핸들러
  ← C auth 나옴 (status=200)
  ← B error-handler 나옴 (status=200)
  ← A timing 나옴 (status=200)
  응답 200 ok
  두 번째 next(): next() called multiple times
```

`koa-missing.js`: 앞 미들웨어 하나(`next()` 누락 / `await` 없이 `next()` / 정상) 뒤에, 50ms 기다린 뒤 `ctx.body = 'ok'`를 쓰는 미들웨어를 붙였다(ms 값은 실행마다 다르다).

```text
  next() 누락: 404 Not Found (191ms)
  await 누락: 404 Not Found (24ms)
  정상: 200 ok (61ms)
```

- 양파 순서가 그대로 찍혔다. 맨 바깥(A)이 마지막에 나오므로 전체 시간 측정·에러 처리 미들웨어는 바깥에 둔다.
- Koa에서 `next()`를 빼먹으면 매달리지 않고 **404**가 났다. `await` 없이 `next()`만 부른 경우도 뒤 미들웨어가 본문을 쓰기 전에 응답이 나가 404였다. 같은 실수가 프레임워크마다 다른 증상(Express: 매달림, Koa: 404, Servlet Filter: 빈 200)으로 보인다.

### 4. NestJS의 요청 수명 주기

NestJS 문서(「Request lifecycle」, docs 저장소 master 2026-10-02 열람)의 요약 순서:

```text
 요청 → 미들웨어 → 가드 → 인터셉터(컨트롤러 전) → 파이프 → 컨트롤러 → 서비스
      → 인터셉터(요청 후) → 예외 필터 → 응답
```

- 미들웨어는 바인딩 순서대로 실행된다(Express와 같다). 전역 → 모듈 순.
- 가드는 전역 → 컨트롤러 → 라우트 순.
- 인터셉터는 들어갈 때 전역 → 컨트롤러 → 라우트, 응답 쪽은 라우트 → 컨트롤러 → 전역(선입후출).

## 쓰이는 자료구조·알고리즘

- **연결 리스트·배열 체인 + 인덱스** — 고리 목록과 "다음 위치"만 있으면 된다. Koa는 배열 + `dispatch(i)` 재귀, Spring MVC는 인터셉터 리스트 + `interceptorIndex`, Tomcat 10.1.46 `ApplicationFilterChain`은 필터 배열 `filters`와 위치 `pos`를 두고 `filters[pos++]`로 다음 필터를 꺼낸다(소스).
- **호출 스택 = 역순 복귀** — 각 고리가 다음 고리를 함수 호출로 부르므로, 들어간 역순으로 빠져나온다(LIFO). 스택 자체는 [systems/call-stack](../../systems/call-stack/README.md).
- **책임 연쇄(Chain of Responsibility)** — 각 고리가 처리하거나 넘기거나 막는다. GoF 원형은 "처리할 수 있는 하나가 처리하고 멈춤"에 가깝고, 웹 미들웨어는 "모두가 조금씩 처리하고 넘김"이 기본이다.
- **양방향 순회 기록** — Spring MVC는 `preHandle`을 통과한 마지막 인덱스를 기억해 그 인덱스부터 거꾸로 `afterCompletion`을 부른다. 통과하지 못한 고리의 정리 코드는 실행되지 않는다(실험 A `/deny`).

## 적용 — 풀어나가는 법

### 1. 순서를 정하는 기준

1. **바깥(먼저)**: 요청 ID·추적 컨텍스트 부여, 전체 시간 측정, 최상위 예외 → 응답 변환. 안쪽 실패까지 다 보아야 하므로 바깥이다.
2. **그다음**: 문자 인코딩·요청 래핑(바디를 읽는 필터보다 앞). Spring Boot 문서는 바디를 읽는 필터를 `Ordered.HIGHEST_PRECEDENCE`에 두지 말라고 한다(인코딩 설정과 어긋날 수 있다).
3. **인증 → 인가**: Spring Security 문서는 인증 필터가 인가 필터보다 먼저 실행돼야 한다고 예를 든다.
4. **바디 파싱·검증**: 인증을 통과한 요청만 파싱하면 비용과 공격면이 준다.
5. **감사·접근 로그**: 무엇을 남길지에 따라 위치가 갈린다. 인증 실패를 포함한 시도 전부를 남기려면 인증 앞, "허가된 요청의 내용"을 남기려면 인증 뒤. 바디를 남기면 마스킹.

### 2. 코드 — 순서를 코드로 고정하기

```java
// Spring Boot: 필터 순서는 클래스에 @Order 또는 FilterRegistrationBean
@Bean
FilterRegistrationBean<RequestIdFilter> requestId() {
    var r = new FilterRegistrationBean<>(new RequestIdFilter());
    r.setOrder(Ordered.HIGHEST_PRECEDENCE + 10);   // 바깥
    r.addUrlPatterns("/*");
    return r;
}
```

```js
// Express: 등록 순서가 곧 정책. 한 파일에서 한 번에 보이게 둔다
app.use(requestId);
app.use(accessLog);          // 인증 실패까지 남기는 정책이면 인증 앞
app.use(authenticate);
app.use(express.json({ limit: '1mb' }));
app.use('/api', routes);
app.use(errorHandler);       // 에러 처리 미들웨어(인자 4개)는 맨 끝
```

### 3. 진단

- 순서 확인: Spring Boot는 `logging.level.web=debug`로 기동하면 등록된 필터의 순서와 URL 패턴을 로그에 남긴다(Spring Boot 3.5 문서). Spring Security는 `FilterOrderRegistration` 코드에서 자체 필터 순서를 볼 수 있다(Spring Security 6.5 문서 「Architecture」).
- 매달리는 요청: 서버 쪽 처리 시간 지표가 없고 클라이언트 타임아웃만 늘면 `next()`·`chain.doFilter` 누락을 의심한다. 서버 쪽 요청 타임아웃을 두어 "매달림"을 에러로 바꾼다.
- 계약 테스트: 체인 순서를 출력·검증하는 통합 테스트를 둔다(실험 A의 출력 자체가 기대값이 된다).

## 장애 시나리오와 대처

### 1. 등록 순서가 바뀌어 인증 전에 로깅·바디 파싱 실행 (⚠ 커리큘럼)

- 현상: 인증 실패 요청의 바디가 로그에 쌓인다. 또는 인증 안 된 대용량 업로드를 파싱하느라 CPU·메모리를 쓴다.
- 보이는 형태: 접근 로그에 `user=-`인 요청 본문, 401 응답인데 파싱 시간이 긴 요청(실험 B 첫 순서).
- 원인: `app.use` 순서(또는 필터 order 값)가 바뀌었다. 리팩터링 중 등록 코드를 옮기거나, 라이브러리가 자기 필터를 기본 순서로 끼웠다.
- 대처: 순서를 한 곳에 모아 둔다. 순서를 검증하는 테스트를 둔다. 바디 파서에 크기 제한을 둔다.

### 2. `next()` 누락 → 응답 없이 멈춤, 클라이언트 타임아웃 (⚠ 커리큘럼)

- 현상: 특정 경로만 응답이 오지 않는다.
- 보이는 형태: 서버 에러 로그 없음. 클라이언트 `TimeoutError`(실험 B: 1505ms). 서버 열린 연결 수가 늘어난다.
- 원인: 미들웨어가 응답도 안 쓰고 `next()`도 안 불렀다(조건 분기 한쪽에서 빠짐, 비동기 콜백 안에서 에러를 삼킴).
- 대처: 분기마다 응답을 쓰거나 `next()`/`next(err)`를 부르게 한다. 린트·리뷰 체크리스트에 넣는다. 서버 쪽 요청 타임아웃을 둔다. 프레임워크마다 증상이 다르다는 것을 안다 — Koa는 404(실험 C), Servlet 필터는 빈 200(실험 A).

### 3. 필터가 두 번 실행된다

- 현상: 로그 한 요청에 같은 필터 줄이 두 번. 레이트 리밋 카운트가 두 배로 오른다.
- 보이는 형태: 요청 ID 하나에 같은 필터 로그 2줄, 순서도 예상과 다름.
- 원인: Spring Security 문서 — 필터를 `@Component`나 `@Bean`으로 선언하면 Spring Boot가 컨테이너에 자동 등록하고, 그것을 Security 체인에도 넣으면 컨테이너 한 번·Security 한 번, **다른 순서로** 두 번 불릴 수 있다.
- 대처: `FilterRegistrationBean`을 선언하고 `setEnabled(false)`로 컨테이너 자동 등록을 끈다(같은 문서). Spring의 `OncePerRequestFilter`는 요청 속성 `<필터 이름>.FILTERED`가 이미 있으면 같은 요청의 두 번째 실행을 건너뛴다(spring-web 6.2.11 소스). 이름을 어떻게 얻느냐에 기대므로, 근본 대처는 등록을 하나로 만드는 것이다.

### 4. 인터셉터를 보안 계층으로 씀

- 현상: 인터셉터에서 막는다고 생각한 요청이 컨트롤러에 도달한다.
- 보이는 형태: 인터셉터의 거부 로그 없이 컨트롤러가 실행된 요청이 접근 로그에 있다.
- 원인: Spring MVC `HandlerInterceptor` Javadoc은 인터셉터가 애너테이션 컨트롤러의 경로 매칭과 어긋날 수 있어 보안 계층으로 적합하지 않다고 적는다.
- 대처: 인증·인가는 Spring Security(서블릿 필터 체인에 통합)로, 인터셉터는 핸들러 관련 공통 처리에 쓴다.

### 5. `preHandle=false` 뒤 정리 코드가 안 돎

- 현상: 인터셉터에서 시작한 타이머·MDC 값이 일부 요청에서 정리되지 않는다.
- 보이는 형태: 스레드 풀 재사용 스레드에 이전 요청의 MDC 값이 남는다.
- 원인: `afterCompletion`은 `preHandle`이 true를 돌려준 인터셉터만 불린다. 내가 false를 돌려주면 내 `afterCompletion`은 안 불린다(실험 A `/deny`의 I2).
- 대처: false를 돌려주기 전에 직접 정리하거나, 정리가 필요한 것은 바깥 필터의 `try/finally`에서 한다.

## 핵심 문장

- 미들웨어·필터·인터셉터는 책임 연쇄를 요청 파이프라인으로 쓴 것이다. 각 고리는 다음을 부르거나, 막고 직접 응답한다.
- 등록 순서가 곧 실행 순서이고, 나올 때는 역순이다. 실험에서 F1 → F2 → I1 → I2 → 컨트롤러 → I2 → I1 → F2 → F1로 찍혔다.
- 로깅을 인증 앞에 두면 인증 실패 요청도 남고, 바디 파서 앞이면 바디가 없다. 뒤에 두면 바디가 남으니 마스킹이 필요하다.
- 다음 고리 호출을 빠뜨린 결과는 프레임워크마다 다르다. 실험에서 Express는 매달려 클라이언트 타임아웃, Koa는 404, Servlet 필터는 빈 200이었다.
- Spring MVC 인터셉터의 `afterCompletion`은 `preHandle`을 통과한 것만 역순으로 불린다. 보안은 인터셉터가 아니라 필터 체인 쪽에 둔다.

## 관련 주제·근거

- 선행
  - [32-inversion-of-control-and-framework-flow](../32-inversion-of-control-and-framework-flow/2-summary.md) — 흐름은 프레임워크가 쥐고 체인의 고리를 부른다
  - [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md) · 기존 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) — Chain of Responsibility
- 연결
  - [33-aop-and-proxies](../33-aop-and-proxies/2-summary.md) — 같은 위임 체인을 메서드 단위로
  - [reliability/15-logging](../../reliability/15-logging/2-summary.md) — 로그에 무엇을 남기고 무엇을 가릴지
  - [reliability/05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md) — 매달린 요청을 타임아웃으로 끊기
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 401·403·404 상태 코드의 뜻
- 글·문서
  - Jakarta Servlet 6.0 명세 §6.2(필터 체인, 요청·응답 래핑, 매핑 순서) <https://jakarta.ee/specifications/servlet/6.0/jakarta-servlet-spec-6.0.html>
  - spring-webmvc 6.2.11 소스·Javadoc: `HandlerInterceptor`, `HandlerExecutionChain.applyPreHandle`·`triggerAfterCompletion`
  - Spring Boot 3.5 문서 「Servlets, Filters, and Listeners」(필터 순서, `FilterRegistrationBean`, `logging.level.web=debug`) <https://docs.spring.io/spring-boot/3.5/reference/web/servlet.html>
  - Spring Security 6.5 문서 「Architecture」(필터 순서의 중요성, 빈 필터 이중 등록, `setEnabled(false)`) <https://docs.spring.io/spring-security/reference/6.5/servlet/architecture.html>
  - Express 문서 「Using middleware」·「Writing middleware」(`next()` 누락 시 hanging, 로드 순서) <https://expressjs.com/en/guide/using-middleware.html>
  - Express 문서 「Error handling」(에러 처리 미들웨어는 인자 4개, 다른 `app.use()`·라우트 뒤에 정의) <https://expressjs.com/en/guide/error-handling.html>
  - koa-compose 4.1.0 소스 `index.js`(`dispatch`, `next() called multiple times`)
  - NestJS 문서 「Request lifecycle」 <https://docs.nestjs.com/faq/request-lifecycle> (원문: <https://github.com/nestjs/docs.nestjs.com/blob/master/content/faq/request-lifecycle.md>)
  - GoF 『Design Patterns』(1994) Chain of Responsibility — 책 본문은 열람하지 못했다
- 실험 목록
  - A 필터·인터셉터 순서, `preHandle=false`, `chain.doFilter` 누락 — `scratchpad/sd/30/e34/src/exp34/Main.java` (JDK 21.0.12 temurin `--cpus=2` 일회용 컨테이너, Tomcat embed 10.1.46, Spring Framework 6.2.11)
  - B Express 5.2.1 등록 순서 2가지, `next()` 누락 타임아웃 — `scratchpad/sd/30/e34js/express-order.js` (Node 18.19.1)
  - C Koa 2.16.4 양파 순서, `next()` 두 번, `next()`·`await` 누락 — `scratchpad/sd/30/e34js/koa-onion.js`, `koa-missing.js`
