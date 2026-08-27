# issue4 — 응답 정규화: success/error 봉투(envelope)

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-llm
- 이슈 #7 · PR: https://github.com/junhyeong9812/study-note-deploy-system-llm/pull/8

> **용어 — 봉투(envelope) vs 래퍼(wrapper)**: 둘 다 "감싼다"지만, 관례상
> **래퍼 = 기능/코드를 감싸는 것**(이 리포에선 Ollama를 감싸는 서버),
> **봉투 = 데이터를 담는 규격 통**(모든 응답이 같은 겉모양, 내용물만 교체 —
> SOAP의 Envelope, JSON:API가 이 계보). 응답 쪽을 봉투라 부르는 이유는
> "wrapper"가 이미 서버 이름으로 쓰이고 있어서다.

## 1. 배경 (요구사항)

정규화 전엔 성공이면 결과 JSON을 그대로, 실패면 `{"error": "..."}`를 줬다.
그러면 backend는 **상태코드별·경우별 본문 모양을 전부 외워야** 분기할 수 있다.
호출하는 쪽(backend)이 빠르게 갈라치려면 깃발 하나면 충분하다:

```
success == true  → data 꺼내 쓰면 됨
success == false → error.code 보고 폴백/재시도 결정
```

## 2. 검토한 방식들

### 선택 — 응답 봉투 (success 플래그 + data/error 이형)

```jsonc
{ "success": true,  "data":  { ...결과... } }
{ "success": false, "error": { "code": "busy", "retry_after": 2 } }
```
- code 목록을 계약으로 고정: busy · upstream · upstream_timeout ·
  schema_violation · invalid_request · not_implemented.
- HTTP 상태코드(200/503/422/501)는 그대로 유지 — 상태코드는 인프라(프록시,
  모니터링)가 읽고, 봉투는 애플리케이션(backend)이 읽는다. 역할이 다르다.

### 대안 — HTTP 상태코드만으로 분기 (탈락)

- 503 하나에 "바쁨/모델 죽음/타임아웃" 세 상황이 겹친다. backend가 재시도 판단을
  하려면 결국 본문을 봐야 하고, 그 본문 모양이 제각각이면 원점. → 탈락.

### 대안 — 응답 헤더에 플래그 (탈락)

- 헤더는 로그·디버깅에서 본문과 따로 놀아 추적이 불편하고, 구조화된 부가정보
  (retry_after 등)를 담기 옹색하다. → 탈락.

## 3. 구현 워크플로우 (기존 → 변경)

```
[기존] api.py가 경우마다 다른 모양을 손으로 조립
  성공        → {...RewriteResult...}                (플래그 없음)
  거절        → {"error": "busy", "retry_after": 2}
  입력 오류    → FastAPI 기본 {"detail": [...]}       (모양 또 다름!)

[변경] 모든 업무 응답이 봉투 공장(domain/envelope.py)을 통과
  api.py ──ok(data)──▶   {"success": true,  "data": {...}}
         ──fail(code)──▶ {"success": false, "error": {code, detail?, retry_after?}}
  입력 오류 → app.py의 예외 핸들러가 가로채 같은 봉투로 (code=invalid_request)
  예외: /health — docker healthcheck(인프라 계약)라 봉투 없이 유지
```

## 4. 코드 변경 (diff와 맥락)

```python
# domain/envelope.py — 봉투 공장. 이 두 함수 밖에서 응답 모양을 만들지 않는다
def ok(data): return {"success": True, "data": data}
def fail(code, *, detail=None, retry_after=None):
    return {"success": False, "error": {...없는 필드는 뺌...}}
```

```diff
# api.py — 모든 return이 공장을 거치도록
-        return result
+        return ok(result.model_dump())
-        return JSONResponse({"error": "busy", "retry_after": 2}, status_code=503, ...)
+        return JSONResponse(fail("busy", retry_after=2), status_code=503, ...)
```

```python
# app.py — FastAPI가 몰래 자기 모양으로 내보내던 입력검증 422도 봉투로 통일
@app.exception_handler(RequestValidationError)
async def validation_envelope(request, error):
    return JSONResponse(fail("invalid_request", detail=...), status_code=422)
```

## 5. 구현 중 마주친 문제

### 문제 — "입력 검증 실패"만 봉투 밖으로 새는 구멍

**증상**: 봉투를 다 씌웠다고 생각하고 필수 필드를 빼먹은 요청을 던져보니:

```
$ curl -X POST .../rewrite -d '{"query": "no id"}'          # request_id 누락
{"detail":[{"type":"missing","loc":["body","request_id"],"msg":"Field required",...}]}
```

`success` 필드가 없는 **FastAPI 기본 모양**이 나온다. 봉투 규약을 아는 backend가 이걸
받으면 `body["success"]`에서 KeyError.

**원인**: pydantic 검증 실패는 라우터 함수에 **진입하기 전에** FastAPI가 가로채 자기
형식(`RequestValidationError` → `{"detail": [...]}`)으로 응답한다. 내 핸들러 코드는
한 줄도 실행되지 않는다.

**수정** (app.py — 전역 예외 핸들러로 그 경로를 다시 가로챔):

```python
@app.exception_handler(RequestValidationError)
async def validation_envelope(request, error):
    return JSONResponse(fail("invalid_request", detail=str(error.errors()[:3])[:300]),
                        status_code=422)
```

수정 후:

```
{"success":false,"error":{"code":"invalid_request","detail":"[{'type': 'missing', 'loc': ('body', 'request_id'), ...}]"}}
```

**배경**: 정규화의 값어치는 "예외 없이 전부"에서 나온다 — 한 경로라도 다른 모양이 남으면
소비자는 결국 두 모양을 다 처리해야 해서 도입 의미가 반감된다. 프레임워크가 **내 코드
바깥에서** 만들어주는 응답(검증 실패·404·500 기본 페이지)이 늘 그 구멍이다.

## 6. 결론

업무 응답 전부가 `success` 깃발 하나로 갈라진다(테스트 28건, 실기동으로 성공·
입력오류 봉투 확인). /health만 인프라 계약으로 예외임을 설계 문서에 명시.
backend 구현 때 이 code 목록이 폴백 분기표가 된다. PR: #8
