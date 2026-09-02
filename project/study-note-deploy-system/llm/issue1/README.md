# issue1 — Ollama 앞에 문지기를 세우다: /rewrite·/health

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-llm
- 이슈 #1 · PR: https://github.com/junhyeong9812/study-note-deploy-system-llm/pull/4

---

## 1. 무엇이 문제였나 — Ollama를 그냥 열면 안 되는 이유

study-note 검색 시스템에서 로컬 LLM(qwen3:8b)이 맡는 일은 "답을 만드는 것"이 아니라
**사용자가 친 검색어를 검색엔진이 잘 찾도록 다듬는 것**이다. 그러면 Ollama를 backend에
바로 붙이면 될 것 같지만, 그렇게 하면 세 가지가 한꺼번에 무너진다.

> 용어 — Ollama: 모델(qwen3:8b 같은)을 GPU에 올려두고 HTTP로 "질문 주면 답을 주는"
> 형태로 서빙해주는 프로그램. `http://호스트:11434/api/chat` 식으로 호출한다.

```
[Ollama를 backend에 직접 노출하면]
  ① 프롬프트(모델에게 주는 지시문)가 backend 코드 여기저기에 흩어진다
       → 프롬프트 한 줄 고치는 데 backend 전체를 배포해야 한다
  ② backend가 요청마다 아무 모델이나 지정해 부를 수 있다
       → 모델 교체가 "backend 전 서버 수정"이 된다
  ③ GPU는 1장인데 요청이 몰리면
       → 전부 조금씩 느려지다 다 같이 죽는다 (아무도 거절당하지 않아서)
```

그래서 Ollama 앞에 **얇은 서버(래퍼)를 하나** 세우기로 했다. 이 서버가
"프롬프트·모델 선택·동시 수용량"을 혼자 소유하면, backend는 그냥 검색어만 던지면 된다.

---

## 2. 무엇을 고민했나 — 네 갈래를 놓고 따졌다

### 갈래 A — backend가 Ollama를 직접 호출 (탈락)

```
backend ──프롬프트 직접 조립──▶ ollama :11434
```
위 ①②가 그대로 발생. 검색 오케스트레이션(ES·임베딩·LLM 조율)과 모델 제어가 한 코드에
섞여 나중에 뜯어내기 어렵다. → 탈락.

### 갈래 B — vLLM 같은 고성능 서빙 런타임 (탈락)

동시 처리량은 압도적이지만 **사용자 1명짜리 시스템엔 과잉**이다. 8GB GPU에선 4bit 양자화가
사실상 강제라 품질 이점도 사라지고, 모델을 GPU에 상주 선점(유휴 시 언로드 없음)해 버린다.
→ 탈락. 단, 나중에 LoRA(모델 일부만 미세튜닝) 서빙이 필요해지면 **런타임만 갈아끼우면**
되도록, backend에는 HTTP 계약만 노출한다 — 이 교체 여지가 래퍼 구조의 실익이다.

### 갈래 C — 래퍼가 자체 대기열(큐)을 운영 (탈락)

```
요청 ──▶ [래퍼의 큐에 줄 세움] ──▶ ollama (하나씩 처리)
```
Ollama가 이미 내부적으로 요청을 직렬화(하나씩)한다. 래퍼가 또 큐를 두면 같은 일을 두 겹으로
하는 셈이고, 줄이 길어지면 사용자 검색이 LLM 대기줄에 인질로 잡힌다. → "넘치면 즉시 거절"로.

### 갈래 D — FastAPI 얇은 래핑 + Ollama를 compose로 한 쌍 (선택)

- 이 서버의 핵심 임무는 **"모델이 뱉은 출력이 약속한 JSON 모양인지 검증"**인데, FastAPI가
  쓰는 pydantic(파이썬 데이터 검증 라이브러리)은 **모델 정의 하나가 곧 ①검증기 ②Ollama에
  보낼 JSON 스키마 ③문서**가 된다 — 한 라이브러리로 세 가지를 해결.
- 동시성이 설계상 2로 고정(GPU 1장)이라 무거운 프레임워크가 필요 없다.

→ D 채택.

---

## 3. 그래서 이렇게 — 토폴로지와 한 요청의 흐름

```
                    [토폴로지 — LAN에 열리는 포트는 :8000 하나뿐]
backend ──HTTP──▶ wrapper :8000
                     │ compose 내부 네트워크 (ollama 포트는 호스트에 안 열림)
                     ▼
                  ollama :11434  (GPU, OLLAMA_NUM_PARALLEL=1)

  · Ollama 포트를 호스트에 안 여는 이유 = backend가 래퍼를 우회해 프롬프트를
    직접 치는 경로를 구조적으로 차단하려고
  · 모델은 env MODEL로 고정 → 요청이 모델을 지정할 수 없다
```

```
                    [POST /rewrite 한 건의 흐름]
요청 {query}
  ▼
api.py (라우터 — HTTP만 담당)
  ▼
usecase/rewrite.py
  ├─① 문지기: 세마포어(동시 2명까지 세는 카운터)가 꽉 찼나?
  │        └─ 찼으면 기다리지 않고 즉시 503 {"error":"busy"}
  ├─② 총예산 5초 타이머 시작 (재시도까지 전부 합쳐 5초 안)
  ├─③ domain/prompt.py 가 프롬프트 조립 → ollama /api/chat 호출
  │        (format=JSON스키마 → 모델이 스키마 밖 출력을 못 하게 강제: 1단 방어)
  ├─④ validate.py: pydantic 파싱 (2단 방어)
  │        └─ 실패하면 "네 출력이 이렇게 틀렸다"를 붙여 딱 1회 재요청 (3단 방어)
  │             └─ 또 실패하면 422 {"error":"schema_violation"}
  ▼
성공 → 구조화된 검색 재료 반환
```

> 용어 — 세마포어(semaphore): "동시에 몇 명까지 들여보낼지"를 세는 카운터. 값이 2면
> 두 명이 안에 있는 동안 세 번째는 문 앞에서 기다린다. 우리는 기다리게 하지 않고
> 즉시 돌려보낸다(`sem.locked()`로 "지금 꽉 찼나"만 확인).

**/rewrite가 실제로 하는 일:** 사용자 검색어("낙관적 락이랑 비관적 락 차이")를 받아
검색엔진(ES)이 잘 찾도록 **검색 준비물**로 바꾼다 — 핵심 키워드 목록, 영어↔한국어
대응어("optimistic locking"), 어느 주제 폴더·어느 문서 종류를 뒤질지. **답을 만드는 게
아니다.** 답 찾기는 검색엔진, 최종 합성은 상위 모델의 몫이다.

**/health:** Ollama에 닿는지 + 모델이 실제로 설치돼 있는지 확인. 모델이 없으면 503을 줘서
배포 시스템이 "정상인 척"하지 못하게 한다.

---

## 4. 코드 — 실제 커밋에서 (초기 구현: `feat b25d168`)

**문지기 — 줄 세우지 않고 즉시 거절** (`wrapper/usecase/rewrite.py`):

```python
async def run(query, topics, *, client, sem, model, timeout):
    if sem.locked():                      # 자리 있는지만 보고 (기다리지 않음)
        raise Busy()                      # → api 계층이 503 + Retry-After: 2 로 번역
    async with sem:                       # 입장. 예외가 나도 자동 퇴장(자리 반납)
        ...
```

**3단 검증 — 터진 JSON을 밖으로 내보내지 않는다** (`wrapper/validate.py`):

```python
async def parse_with_retry(schema, raw, retry):
    try:
        return schema.model_validate_json(raw)          # 2단: pydantic 파싱
    except ValidationError as first:
        raw2 = await retry(                              # 3단: 오류를 피드백해 딱 1회 재요청
            f"이전 출력이 스키마를 위반했다: {first.errors()[:3]}\n"
            f"스키마에 맞는 JSON만 다시 출력하라."
        )
        try:
            return schema.model_validate_json(raw2)
        except ValidationError as second:
            raise SchemaViolation(str(second.errors()[:3])) from second
```

(1단은 Ollama 호출 시 `"format": schema`를 넘겨 모델이 스키마 밖을 못 뱉게 강제하는 것.)

---

## 5. 구현 중 마주친 문제

### 문제 1 — 설계 문서와 코드의 응답 모양이 어긋났다 (듀얼 리뷰가 잡음)

- **무엇이 문제였나**: 설계는 `filters{topic, doc_kind}`로 되어 있는데 구현하다 무심코
  입력을 `topics[]`로 바꿔 놓았다. 테스트마저 틀린 모양을 고정해버려 회귀를 못 잡았다.
- **왜 위험한가**: 문서와 코드가 서로 다른 이름을 말하면, 이 서버를 부르는 backend는
  어느 쪽을 믿어야 할지 모른다. "설계 문서가 계약의 정본"이 무너진다.
- **그래서 이렇게** (`wrapper/api.py`, `fix f9c613c` — 다른 모델 codex로 교차 리뷰해 발견):

```diff
 class RewriteIn(BaseModel):
-    query: str
-    topics: list[str] | None = None
+    model_config = ConfigDict(extra="forbid")   # 계약 밖 필드는 아예 거부
+    query: str = Field(min_length=1, max_length=300)
```

같은 리뷰에서 **총예산 타임아웃 결함**도 같이 고쳤다 — 호출마다 5초를 걸면 재시도까지
하면 최대 10초가 된다:

```diff
# wrapper/usecase/rewrite.py
-    raw_output = await _chat(..., timeout)              # 호출마다 5초 → 재시도 시 최대 10초
+    async with asyncio.timeout(timeout):                # 요청 전체가 5초 안 (재시도 포함)
+        raw_output = await _chat(...)
```

### 문제 2 — 모델이 없어도 "health"로 보였다

- **무엇이 문제였나**: 모델 미설치 상태에서 `/health`가 몸통엔 "model_missing"이라 쓰면서
  **상태코드는 200**을 줬다. docker healthcheck는 상태코드만 보므로 "healthy"로 판정한다.
- **그래서 이렇게** (`wrapper/api.py`, `fix f9c613c`): 모델 부재·응답 이상은 503으로.

```diff
-        return {"status": "ok" if model_present else "model_missing", "model": ...}
+        if not model_present:
+            return JSONResponse({"status": "model_missing", "model": state.model},
+                                status_code=503)
+        return {"status": "ok", "model": state.model}
```

"에러 없이 돌았다 ≠ 정상"의 전형이다. 실제로 `ollama pull`을 깜빡한 상태가 정확히 이
시나리오였고, .164 스모크에서 503이 뜨는 걸 확인했다.

### 문제 3 — qwen3 thinking 폭주로 모든 요청이 5초에 타임아웃 (실기동에서만 드러남)

**증상**: 모델 pull 완료·GPU 로드 확인 후에도 /rewrite가 매번 **정확히 5초**에서 죽었다.

```
$ time curl -X POST .../rewrite -d '{"query":"낙관적 락이랑 비관적 락 차이"}'
{"error":"upstream_timeout"}
real    0m5.006s        ← 총예산 5s가 정확히 발동 (계약은 정상, 추론이 문제)
```

**진단 순서**:
```
① ollama ps       → 모델은 100% GPU 로드, 정상
② 같은 요청을 Ollama에 직접 던짐 → 8분 넘게 안 끝남
③ nvidia-smi      → 98%, 5470MiB / 8192MiB  (GPU 풀가동 중)
④ docker logs llm-ollama | tail
     slot print_timing: ... n_gen = 31325, tg = 63.94 t/s
     slot context shift, n_keep = 4, n_left = 4091, n_discard = 2045
```

초당 64토큰으로 **멀쩡히** 생성 중인데 이미 **31,000토큰 이상** — 답이 안 끝나는 게 아니라
**끝낼 생각이 없는** 상태다(4096 컨텍스트를 넘겨 context shift까지 발생). 프롬프트에 넣어둔
`/no_think`(Qwen 모델 카드에 나오는 "생각 끄기" 문자열 스위치)를 Ollama의 qwen3 챗
템플릿이 특별 취급하지 않고 그냥 일반 텍스트로 흘려보낸 것이다. thinking이 켜진 채
JSON 스키마 강제(`format`)와 얽혀 종결 조건에 도달하지 못했다. 게다가 wrapper가 5초에
연결을 끊어도 **Ollama는 서버쪽 생성을 계속했다** — 그래서 후속 요청까지 GPU를 못 잡고
연쇄로 타임아웃.

**그래서 이렇게** (`wrapper/src/app/usecase/rewrite.py`, `fix 63ed56b`):

```diff
             "stream": False,
+            "think": False,            # qwen3 thinking 비활성 — 프롬프트 소프트 스위치는
+                                       # ollama 템플릿에서 무시됨 (.164 실측: 폭주 생성)
             "format": schema,          # 1단: Ollama 구조화 출력 강제
-            "options": {"temperature": 0},
+            # num_predict 상한 — 폭주 가드레일. 클라이언트가 타임아웃으로 끊어도
+            # ollama는 서버측 생성을 계속하므로(실측 31k 토큰) 상한이 유일한 방어선
+            "options": {"temperature": 0, "num_predict": 512},
```

프롬프트의 `/no_think` 문자열은 삭제했다(효과 없는 주술):

```diff
# wrapper/src/app/domain/prompt.py
-    "너는 개발 공부 노트 검색 시스템의 질의 분석기다. /no_think\n"
+    "너는 개발 공부 노트 검색 시스템의 질의 분석기다.\n"
```

**결과**: 콜드 3.56s → 웜 **1.33s**, 출력 정상.

**여기서 얻은 세 가지**:
1. 모델 카드의 프롬프트 문법이 서빙 런타임에서도 통한다고 가정하지 말 것 — 모델 제어는
   그 런타임의 공식 API(`think:false`)로 한다.
2. **클라이언트 타임아웃은 서버 자원을 보호하지 않는다** — 서버측 생성 상한(`num_predict`)이
   유일한 방어선이다(31k 토큰이 그 증거).
3. 이건 mock 테스트로는 절대 못 잡는 유형 — 실기동 스모크를 머지 조건에 넣은 게 유효했다.

---

## 6. 결론

Ollama 앞에 "프롬프트를 소유하는 게이트웨이"를 세웠다. 동시 2건 초과는 기다림 없이 즉시
거절하고, 모델 출력은 3단(스키마 강제 → 검증 → 피드백 재시도 1회)으로 방어하며, 요청
전체가 5초 예산을 넘지 않는다. 수치들(세마포어 2, 5초, 재시도 1회, num_predict 512)은
전부 "일단 이 값으로 두고 로그로 실측한 뒤 조정" 항목으로 `implementation-verification.md`에
등재해놓았다. PR: #4 (테스트 12건 + 실기동 스모크).
