# issue/python/fastapi/response-normalization-framework-boundary — 정답

태그: `contract-drift`

## 정답

<!-- 질문 1:1 대응 -->

1. **응답 계약은 "내 코드가 실행되는 범위"까지만 보장되기 때문이다.** 봉투 공장을 라우터의 모든 `return`에 통과시켜도, 그 `return`들은 요청이 라우터 함수 *안까지 들어왔을 때만* 실행된다. 프레임워크는 그 함수에 닿기 전(라우팅·입력 검증)과 후(미처리 예외 → 500)에 **자기 형식으로** 응답을 만들며, 그 응답들은 내 봉투 코드를 한 줄도 거치지 않는다. 그래서 "내 핸들러를 다 고쳤다"는 계약의 완결이 아니라 계약의 *일부*일 뿐이다.
   > **봉투(envelope)** — 모든 응답이 같은 겉모양(`success` 깃발 + `data`/`error`)을 갖고 내용물만 바뀌는 응답 규격. 소비자가 상태코드·본문 모양을 외우지 않고 깃발 하나로 분기하게 해 준다.

2. pydantic 입력 검증 실패의 응답은 **FastAPI가, 라우터 함수에 진입하기 전에** 만든다. FastAPI는 요청 본문을 파라미터 모델(`ItemIn`)로 파싱·검증한 *다음에야* 내 함수를 호출하는데, 검증이 실패하면 `RequestValidationError`를 발생시키고 자기 기본 핸들러가 이를 잡아 `{"detail": [...]}`로 응답한 뒤 끝낸다. 내 라우터 함수는 **호출 자체가 안 된다.** 그래서 함수 몸통 안에 아무리 완벽한 `try/except`를 써도 그 실패는 잡히지 않는다 — 잡으려는 코드가 있는 곳까지 실행이 도달하지 못한다.
   > **RequestValidationError** — 요청이 선언된 스키마(타입·필수 필드·제약)를 어겼을 때 FastAPI가 라우터 진입 전에 던지는 예외. 기본 핸들러가 `{"detail":[...]}`로 응답한다.

3. 소비자는 봉투를 믿고 `body["success"]`를 먼저 읽는데, 검증 실패 응답에는 `success` 키가 없으므로 **KeyError로 터진다.** 즉 "정상/실패" 분기를 하기도 전에 파싱 단계에서 죽는다. 그러면 소비자는 결국 "봉투 모양"과 "FastAPI 기본 모양" 두 가지를 다 처리하는 방어 코드를 넣어야 하고, 그 순간 정규화의 목적(소비자가 한 모양만 알면 됨)이 사라진다. **정규화는 예외가 하나라도 있으면 값어치가 반감된다** — 100%가 아니면 소비자는 여전히 여러 모양을 알아야 하기 때문이다.

4. 처방의 일반형은 **"프레임워크가 내 코드 밖에서 응답을 만드는 지점을, 프레임워크가 제공하는 훅(전역 예외 핸들러)으로 되가로채, 내 규약으로 다시 씌운다"** 이다. FastAPI에선 `@app.exception_handler(RequestValidationError)`로 검증 실패를, `StarletteHTTPException`(또는 상태코드 404) 핸들러로 없는 경로를, `Exception`(또는 500) 핸들러로 미처리 예외를 잡아 전부 `fail(code, ...)` 봉투로 통일한다. 단 Starlette에서 `Exception`/500 핸들러는 가장 바깥의 `ServerErrorMiddleware`에서 실행되므로 사용자 미들웨어 안쪽이 아니다 — 미들웨어가 그 500 응답을 보고 가공한다고 가정하면 안 된다. 핵심은 "내 코드로 커버가 안 되는 경계에는, 그 경계를 관장하는 프레임워크의 확장점으로 개입한다"는 것 — 경계마다 그런 훅이 있다.
   > **전역 예외 핸들러(exception handler)** — 특정 예외 타입이 올라오면 앱 전역에서 가로채 응답을 대신 만드는 프레임워크 확장점. 라우터 밖에서 생기는 응답까지 규약 아래로 끌어오는 통로다.

5. **읽는 주체가 다르기 때문에 둘 다 남긴다.** HTTP 상태코드(200·503·422·501)는 **인프라 계층**(리버스 프록시·로드밸런서·모니터링·재시도 정책)이 본문을 파싱하지 않고 읽는 신호다. 봉투의 `success`/`error.code`는 **애플리케이션 계층**(backend)이 폴백·재시도를 정밀 분기하려고 읽는다. 상태코드 하나로는 부족한데(예: 503 하나에 "바쁨/모델 죽음/타임아웃"이 겹침) 그렇다고 상태코드를 버리면 인프라가 눈이 먼다. 그래서 상태코드는 굵은 신호로, 봉투는 세밀한 신호로 **역할을 나눠** 병존시킨다.

6. **"규약에서 명시적으로 빼는 것"과 "규약이 조용히 새는 것"은 예측 가능성에서 달라진다.** `/health`는 docker healthcheck라는 인프라 계약이 상태코드만 보므로 봉투가 필요 없고, `/chat`은 스트리밍 청크(text/plain) 자체가 계약이라 JSON 봉투를 씌울 수 없다. 이 둘은 **설계 문서에 "봉투 예외"로 적어** 소비자가 미리 알고 그렇게 다룬다 — 예측 가능한 예외다. 반면 검증 실패가 다른 모양으로 새는 것은 소비자가 몰랐던 모양이라 런타임에 터진다. 전자는 계약의 *일부로 문서화된 예외*, 후자는 *문서에 없는 누출*이다.

7. 일반 원리: **횡단 관심사(cross-cutting concern)를 "내 핸들러 코드"에만 심으면, 요청이 내 핸들러를 거치지 않고 응답되는 모든 경로에서 그 관심사가 빠진다.** 봉투 정규화가 검증 실패에서 새듯이 — 로깅을 라우터 안에서만 하면 프레임워크가 조기 거절한 요청(검증 실패·인증 실패·404)은 로그에 안 남고, 인증 검사를 핸들러 본문(데코레이터)에서만 하면 입력 검증 실패 같은 조기 응답이 인증보다 먼저 나가 미인증 요청에도 스키마 오류 세부가 노출되며, 트레이싱을 함수 안에서 시작하면 진입 전 실패한 스팬이 유실된다. 그래서 횡단 관심사는 라우터가 아니라 **프레임워크 경계(미들웨어·예외 핸들러)**에 걸어야 "예외 없이 전부"가 성립한다.
   > **횡단 관심사(cross-cutting concern)** — 개별 기능이 아니라 모든 요청에 공통으로 걸쳐야 하는 관심사(응답 형식·로깅·인증·트레이싱). 핸들러 단위가 아니라 경계 단위로 심어야 새지 않는다.

## 문제 구조 (추상화 코드)

### 변형 A — 라우터 진입 전 입력 검증 실패가 봉투 밖으로 샘
① 문제 코드
```python
class ItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    # ...

@router.post("/items", response_model=SuccessEnvelope)
async def post_item(body: ItemIn):          # 검증 실패 시 여기까지 오지 않음
    try:
        return ok(result)                   # 봉투는 함수 안의 return 만 통과
    except Busy:
        return fail("busy", ...)
# 검증 실패 → 프레임워크 기본 응답 {"detail": [...]} — success 키 없음
```
② 고친 코드
```python
@app.exception_handler(RequestValidationError)      # 라우터 밖 경로를 되가로챔
async def envelope_invalid_request(request, exc):
    return JSONResponse(fail("invalid_request", ...), status_code=422)   # 상태코드는 유지

# 의도적 예외는 설계 문서에 명시:
#   GET /health  → {"status": ...} + 503  (인프라 계약 — 봉투 없음)
#   POST /chat   → text/plain 청크      (스트림 자체가 계약 — 스트림 시작 전 거절만 fail("busy"))
```
무엇이 깨졌나: 봉투 공장은 핸들러 안의 `return`에만 걸려 있었고, 프레임워크가 핸들러 진입 전에 만드는 응답은 그 공장을 거치지 않았다.\
연결: 봉투의 error code 목록은 곧 소비자의 폴백 분기표다 — 쓰이지 않는 code는 계약에서 뺀다([yagni-dead-contract](../yagni-dead-contract/)).

### 변형 B — 하위 레이어가 HTTP 예외를 직접 던져 매핑 분기를 우회
① 문제 코드
```python
def check_limit(total):                     # 도메인 레이어
    if total > LIMIT:
        raise HTTPException(400, "...")             # 도메인이 HTTP를 앎

@app.post("/search")
async def search(req):                              # 엔드포인트마다 같은 try/except 반복
    try:
        # ...
    except DomainValidationError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(500, "internal")        # HTTPException 도 여기로 흡수 → 400이 500으로
```
② 고친 코드
```python
def check_limit(total):
    if total > LIMIT:
        raise DomainValidationError("...")          # 도메인은 도메인 예외만

_STATUS_BY_TYPE = {DomainValidationError: 400, ...}   # 도메인 예외 계층 → 상태코드

@app.exception_handler(AppError)                 # 서브클래스 전체 매칭 — 매핑을 한 곳에
async def domain_error_handler(request, exc):
    status = next((_STATUS_BY_TYPE[t] for t in type(exc).__mro__ if t in _STATUS_BY_TYPE), 500)   # 미등록 서브클래스도 가장 가까운 부모로 — KeyError 금지
    scope = request.url.path.split("/")[1]          # 핸들러에선 엔드포인트 파라미터 접근 불가
    # ...

@app.exception_handler(Exception)                   # 500 로깅 통합 (exc_info=True)
async def unknown_error_handler(request, exc): ...
```
무엇이 깨졌나: 매핑이 "도메인 예외 → 400, 나머지 → 500"인데 하위 레이어가 매핑 대상이 아닌 타입을 던져 일반 예외로 흡수됐다.

### 변형 C — 핸들러가 요청 모델을 직접 생성해 프레임워크의 자동 422를 우회
① 문제 코드
```python
@app.post("/detail")
async def detail(request: Request):
    body = await request.json()                     # JSONDecodeError 도 매핑 없음
    req = DetailIn(**body)                          # 핸들러 안의 pydantic ValidationError → generic 500
```
② 고친 코드 (계획)
```python
@app.exception_handler(RequestValidationError)
@app.exception_handler(pydantic.ValidationError)    # 핸들러 안에서 난 검증 오류도 같은 포맷
async def invalid_request(request, exc):
    return JSONResponse(domain_validation_body(exc), status_code=400)   # 기존 도메인 검증 오류(400) 포맷으로 통일
# JSON 파싱 실패도 400. 재현 케이스 5종(필수 누락·size=0·page=0·타입 오류·빈 이름) 테스트.
# 500 → 4xx 는 public contract 변경이므로 기록.
```
무엇이 깨졌나: 검증을 프레임워크의 요청 검증 단계 밖(핸들러 본문)으로 옮기는 순간, 그 오류는 프레임워크의 422 매핑이 아니라 catch-all 500으로 떨어진다. 모니터링에는 클라이언트 오류가 전부 내부 오류로 집계됐다.\
같은 구조: 리뷰에서 "검증 오류 핸들러 부재로 입력 오류가 전부 500"이 다시 지적됨(해결은 계획 단계).

### 변형 D — 외부 입력 파싱 실패를 도메인 예외로 번역하지 않음 (다른 스택)
① 문제 코드
```java
long[] parseRange(String header) {                  // "bytes=-" · 비숫자
    String[] parts = header.substring(6).split("-");
    long suffix = Long.parseLong(parts[1]);         // AIOOBE / NumberFormatException → catch-all 500
    // ...
}
MediaType type = MediaType.parseMediaType(stored);  // 업로드 때 검증 안 한 값 → 다운로드마다 500
```
② 고친 코드
```java
// RFC 7233(현행 RFC 9110) 준수로 재작성, 만족 불가 범위는 도메인 예외 → 416 핸들러
if (!valid) throw new RangeNotSatisfiableException(size);

MediaType type = safeParse(stored).orElse(MediaType.APPLICATION_OCTET_STREAM);   // 안전 파싱 + 폴백
```
무엇이 깨졌나: 입력 파싱의 런타임 예외가 catch-all 핸들러에서 "서버 오류"로 분류됐고, 저장 시 검증하지 않은 값은 읽을 때마다 폭발했다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(위 변형 A~D)은 "프레임워크 확장점(전역 예외 핸들러)으로 핸들러 밖 응답을 되가로채 한 봉투로 정규화한다"이다. 같은 원리(프레임워크가 핸들러 밖에서 만드는 응답이 계약의 구멍)에 다른 방안이 쓰인 사례:

### 방안 1 — 전역 핸들러 대신 호출 지점에서 예외를 계약된 오류로 변환
```python
# 문제: returncode 만 검사 — timeout 은 반환코드가 아니라 예외
proc = subprocess.run(cmd, capture_output=True, timeout=60)   # 초과 시 TimeoutExpired → 전역 500
if proc.returncode != 0: raise HTTPException(500, "변환에 실패했습니다")

# 고친
try:
    proc = subprocess.run(cmd, capture_output=True, timeout=60)   # 인자는 리스트(shell=False)
except subprocess.TimeoutExpired:
    raise HTTPException(500, "변환 시간이 초과됐습니다")         # 계약된 detail 로 변환
if proc.returncode != 0 or not out.is_file():                  # out = 변환 결과 파일 경로(cmd 에 전달한 것)
    raise HTTPException(500, "변환에 실패했습니다")
```

### 방안 2 — 예외 루트를 하나로 통합하고, 필터 체인은 직접 잡아 같은 봉투로
```java
// 문제 ①: 예외 트리가 둘 — 핸들러는 한쪽 루트만 매칭
class LegacyBusinessException extends RuntimeException {}          // BusinessException 미상속
@ExceptionHandler(BusinessException.class) ...                      // 못 잡음 → catch-all 500, 메시지 유실
// 문제 ②: @ControllerAdvice 는 디스패처가 호출한 핸들러의 예외만 처리
class AuthFilter extends OncePerRequestFilter {
    void doFilterInternal(...) { cache.get(token); /* I/O 예외 → 컨테이너/부트 기본 오류 응답 500(봉투 아님) */ }
}
// 문제 ③: @Transactional + throws Exception, rollbackFor 없음 → 체크 예외에 롤백 안 됨

// 고친
class LegacyBusinessException extends BusinessException {}         // 단일 트리로 재부모화
class AuthFilter extends OncePerRequestFilter {
    void doFilterInternal(...) {
        try { cache.get(token); }
        catch (CacheIoException e) { writeErrorResponse(res, 503, ...); return; }   // 같은 오류 봉투
    }
}
@ExceptionHandler(MultipartException.class) ... 413                // 미등록 프레임워크 예외 등록
@ExceptionHandler(DataIntegrityViolationException.class) ...        // 중복이면 409, FK/not-null 400 (내부 제약명 비노출)
@ExceptionHandler(PessimisticLockingFailureException.class) ... 503 + Retry-After
@Transactional(rollbackFor = Exception.class)
```
같은 구조: 비숫자 헤더를 `Long.valueOf`로 파싱하다 NumberFormatException → 로그인 잠금·감사 로그가 건너뛰어짐.

### 방안 3 — 과광역 catch 대신 구체 예외 타입별 상태코드
```kotlin
// 문제: 봉투 구멍을 막으려 포괄 Exception → 500 을 넣자 클라이언트 입력 오류(size=abc)까지 500으로 회귀
// 문제: 파일 읽기의 모든 예외를 404로 → I/O·권한 장애가 "문서 없음"으로 위장
} catch (_: Exception) { throw NotFound() }

// 고친
@ExceptionHandler(MissingServletRequestParameterException::class, MissingRequestHeaderException::class,
    MethodArgumentTypeMismatchException::class, HttpMessageNotReadableException::class)   // → 4xx
fun badRequest(...) = ...
} catch (_: java.io.FileNotFoundException) { throw NotFound() }   // 부재만 404 — 그 외 I/O 는 전역 500 봉투
// 하위 호출이 "부재"를 FileNotFoundException 으로 번역해 404 계약 유지
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 전역 예외 핸들러로 정규화 | 프레임워크가 해당 경로에 확장점을 제공한다 | 핸들러·매핑표 한 곳 | 매핑표에 없는 타입은 catch-all 로 떨어짐 | 검증 실패·도메인 예외처럼 타입이 명확한 경로 |
| 1. 호출 지점 변환 | 그 예외가 어디서 나는지 안다 | 호출부마다 try/except | 같은 호출이 다른 곳에 생기면 누락 | 특정 외부 호출의 특수 예외(timeout 등) |
| 2. 예외 루트 통합 + 필터 직접 처리 | 핸들러가 닿지 않는 층(필터·컨테이너)이 있다 | 예외 계층 재설계, 필터별 오류 응답 | 새 필터·새 루트가 생기면 재발 | 서블릿 필터·예외 트리가 둘 이상인 스택 |
| 3. 구체 타입별 매핑 + 포괄 catch 는 마지막 5xx 그물 | 4xx/5xx·부재/장애 구분이 소비자에게 의미 있다 | 타입 목록 유지 | 포괄 catch 를 먼저 넣으면 4xx 회귀·장애 위장 | 봉투를 새로 씌우는 중 회귀를 막아야 할 때 |

**결론**: 응답이 만들어지는 층마다 확장점이 있으면 전역 핸들러로 한 곳에서 정규화하는 것이 기본이다.\
전역 핸들러가 닿지 않는 층(필터·컨테이너)이 있으면 그 층에서 직접 같은 봉투를 쓰고, 예외 루트를 하나로 모은다(2).\
특정 외부 호출의 특수 예외는 호출 지점에서 계약된 오류로 바꾸는 편이 의미를 가장 잘 보존한다(1).\
어느 방안이든 포괄 catch는 **마지막 5xx 그물**로만 둔다 — 넓게 잡을수록 "누구 잘못인가·없는 것인가 고장인가"의 구분이 사라진다(3).

## 방안 비교 — 프레임워크의 본문 해석이 인증보다 먼저 돈다: 응답 모양을 고치기 vs 해석 순서를 되찾기

같은 원리(프레임워크가 핸들러 진입 전에 만드는 응답은 핸들러 안의 규칙을 거치지 않는다 — 질문 2·7)가, Kotlin/Spring 서버의 **인증 순서**에서 나온 사례다.\
서버의 두 POST 경로는 공유 비밀 헤더로 인증하고, 계약은 "비밀값이 없거나 틀리면 401, 본문 꼴이 틀리면 422"였다.\
핸들러가 본문을 `@RequestBody` 인자로 받으면, Spring 은 핸들러를 부르기 **전에** 본문을 해석한다 — 비밀값 검사는 핸들러 안에 있으니 해석보다 뒤다.

```
요청 ──▶ [프레임워크: Content-Type 확인 · JSON 해석 → 인자 바인딩] ──▶ 핸들러 { 비밀값 검사 → 처리 }
              │ 실패                                                       ▲
              └─▶ 400(깨진 JSON) · 415(JSON 아닌 Content-Type)              │ 여기까지 오지 않는다
                  비밀값 없는 요청도 받는다 — 인증보다 본문 검증이 먼저 답한다
방안 4  전역 예외 처리로 400·415 를 422 봉투로 바꾼다   → 모양은 맞지만 순서는 그대로(해석이 먼저)
방안 5  인자 바인딩을 빼고 원문을 직접 읽는다          → 비밀값 → Content-Type · 크기 · JSON 꼴 → 422
```

### 방안 4 — 전역 예외 처리로 프레임워크 오류를 계약 모양으로 (선택하지 않은 방법)
```kotlin
@RestControllerAdvice
class ParseErrorAdvice {
    @ExceptionHandler(HttpMessageNotReadableException::class)
    fun unreadable() = ResponseEntity.status(422).body(envelopeError("invalid_request"))
}
```
이 카드의 기본 방안(전역 핸들러로 정규화)과 같은 길이다. 응답 모양은 맞출 수 있지만, 해석이 인증보다 먼저 도는 순서는 바뀌지 않는다 — 비밀값 없는 깨진 요청은 여전히 401 이 아니라 해석 오류를 받는다.\
게다가 같은 서버의 다른 경로(로그 조회 등)는 자기 해석 규칙을 쓰고 있어, 전역 처리가 그 경로들로 번질 수 있었다 — 이것이 선택하지 않은 이유로 기록됐다.

### 방안 5 — 원문을 직접 읽어, 인증 → 본문 검증 순서를 핸들러가 정한다 (이 사례의 선택)
```kotlin
@PostMapping("/attempts")
fun record(request: HttpServletRequest): ResponseEntity<out Any> = guarded(request) { body -> handle(body) }

private fun guarded(request: HttpServletRequest, handle: (Map<String, Any?>) -> ResponseEntity<out Any>): ResponseEntity<out Any> {
    if (!hasValidKey(request)) return status401()                      // 1. 비밀값 먼저(상수 시간 비교)
    val body = try { parseJsonObject(request) } catch (e: BadBody) { return status422(e.detail) }   // 2. 그다음 본문 → 422
    return handle(body)
}

private fun parseJsonObject(request: HttpServletRequest): Map<String, Any?> {
    val type = parseMediaTypeOrNull(request.contentType)
    if (type == null || !(APPLICATION_JSON.isCompatibleWith(type) || type.subtype.endsWith("+json"))) throw BadBody("Content-Type")
    if (request.contentLengthLong > BODY_LIMIT) throw BadBody("too large")
    val bytes = request.inputStream.use { it.readNBytes(BODY_LIMIT + 1) }   // 길이 머리글이 없거나 거짓이어도 상한까지만
    if (bytes.size > BODY_LIMIT || bytes.isEmpty()) throw BadBody("size")
    val node = strictJson.readTree(bytes)                                // 뒤에 남는 토큰도 오류
    if (node == null || !node.isObject) throw BadBody("object required")
    return strictJson.treeToValue(node, Map::class.java) as Map<String, Any?>
}
```
테스트는 해석할 수 없는 본문 11가지 × 두 POST 경로 × (비밀값 없음·틀림 → 401 / 맞음 → 422, 기록 없음)이었고, 고치기 전 구현에서 Spring 기본 400 이 나가는 것을 확인했다.\
변형 실험: 본문 해석을 인증 앞으로 옮기면 실제 HTTP 를 쓰는 테스트가 빨강이 됐다. 배포 뒤 서버에서도 새 경로들이 깨진 본문을 포함해 비밀값 없이 401 이었다.\
인증을 필터·인터셉터로 옮겨 바인딩보다 앞에 두는 방법도 있다 — 이 사례 기록에는 그 비교가 없다.

| 방안 | 응답 모양 | 인증과 해석의 순서 | 영향 범위 | 맞는 조건 |
|------|-----------|--------------------|-----------|-----------|
| 4. 전역 예외 처리 | 계약 모양으로 맞춤 | 해석이 먼저 — 비인증 요청도 본문 검증 결과를 받는다 | 서버 전체 경로 | 순서가 계약이 아니고, 모든 경로가 같은 오류 규약을 쓸 때 |
| 5. 원문 직접 읽기 | 핸들러가 정함 | 인증이 먼저 | 그 경로만 | 인증 전에 아무것도 해석하지 않아야 하는 경로, 다른 경로의 규칙을 건드리면 안 될 때 |

**결론**: 프레임워크의 편의 기능(인자 바인딩)은 핸들러보다 먼저 돈다 — 핸들러 안에 둔 인증은 그보다 늦다.\
응답 **모양**만 문제라면 전역 처리로 충분하지만(4), 인증과 해석의 **순서**가 계약이면 모양을 고쳐서는 풀리지 않는다.\
그때는 그 경로에서 바인딩을 빼고 원문을 직접 읽어 순서를 되찾는다(5). 직접 읽을 때는 프레임워크가 해 주던 것(Content-Type·크기 상한·엄격한 JSON)을 빠짐없이 다시 한다 — 길이 머리글을 믿지 않고 상한까지만 읽는 것까지.

검증 기록: 2026-11-23 — 사건 기록·리뷰 기록·수정 코드 대조·추상화(경로·헤더 이름은 일반화했다). 테스트 구성(11가지 × 2 경로)·변형 실험·서버 확인(비밀값 없는 깨진 본문 401)은 사건 기록의 값이다. 방안 4 의 코드는 선택하지 않은 방법을 보이려고 쓴 일반형이다.
