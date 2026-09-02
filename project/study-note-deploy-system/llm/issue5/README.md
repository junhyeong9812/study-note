# issue5 — /digest 예약 계약 제거: 안 쓰면 지운다

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-llm
- 이슈 #10 · PR: https://github.com/junhyeong9812/study-note-deploy-system-llm/pull/11

---

## 1. 무엇이 문제였나 — 예약석이 정말 필요한가

issue1에서 /digest(검색 결과 조각들을 모델이 한국어로 요약해주는 API)를 "계약만 예약"
상태로 남겨뒀다 — 구현은 없고 호출하면 501만 주는 자리. "나중에 backend 수정 없이 켠다"가
명분이었다. 다시 따져보니 그 '나중'의 소비자 둘 다 이 기능을 원하지 않았다.

```
사람용 검색:
    이 시스템의 목적은 인출 학습(기억에서 꺼내는 훈련)이다
    → 기본 동작은 링크 목록이어야 한다. 요약 자동 노출은 목적과 정면 충돌

MCP 확장 (코딩 중 Claude가 질의):
    소비자가 이미 강한 모델(Claude)이다
    → 문서 조각 원문을 직접 읽는 쪽이 항상 낫다
    → 8B가 미리 요약하면 오히려 정보를 깎아서 전달하는 꼴
```

즉 현재 수요 0, 미래 수요도 불분명하다.

> 용어 — MCP(Model Context Protocol): 외부 도구(여기선 이 검색 시스템)를 Claude 같은
> 모델에 연결하는 표준. Claude가 코딩 중 이 검색을 "도구"로 호출하는 경로를 가리킨다.

---

## 2. 무엇을 고민했나

### 갈래 A — 예약석 유지 (탈락)

"나중에 backend 수정 없이 켠다"가 명분이었지만, 그 '나중'의 소비자(MCP)가 이 기능을
원하지 않는다는 결론이 나면서 명분이 소멸했다. → 탈락.

### 갈래 B — 완전 제거 (선택)

예약석의 유지 비용이 "0에 가깝다"고 해도 0은 아니다: 설계 문서·README·테스트가 계속 이
계약을 설명해야 하고, 읽는 사람(미래의 나)이 "이건 뭐지"를 반복해서 묻게 된다. 필요해지면
**그때의 요구로 다시 설계**하는 게 낫다 — 지금 기록해둔 입출력 모양이 그때도 맞으리란 보장이
없고, 틀린 예약석은 없느니만 못하다. → B 채택.

> 용어 — **YAGNI**(You Aren't Gonna Need It): "어차피 안 쓸걸?" — 미래를 위해 미리
> 만들어두는 걸 경계하는 원칙. 예측으로 만든 것은 대개 틀린 모양으로 만들어진다.

---

## 3. 그래서 이렇게 — 기존 ↔ 변경

```
[기존]  POST /digest ──▶ 501 {"success":false,"error":{"code":"not_implemented"}}
        (설계 D2에 입출력 계약, domain에 모델 3형, 테스트 2건)

[변경]  POST /digest ──▶ 404 (그런 경로 없음 — FastAPI 기본)
        설계 D5에 "왜 지웠나"만 남김 (결정의 흔적은 지우지 않는다)
```

---

## 4. 코드 — 실제 커밋에서 (`chore 6486b34`)

**핸들러 삭제** (`wrapper/src/app/api.py`):

```diff
-@router.post("/digest")
-async def post_digest(body: DigestIn):
-    # 계약(DigestIn·DigestResult)만 예약, 구현은 2차 (design D5)
-    await log(body.request_id, "digest not implemented", "warning")
-    return JSONResponse(fail("not_implemented"), status_code=501)
```

**도메인 모델 3형 삭제** (`wrapper/src/app/domain/prompt.py`):

```diff
-class DigestChunk(BaseModel):
-    path: str
-    heading: str
-    content: str
-
-class DigestIn(BaseModel):
-    """/digest 입력 계약 — 2차 구현 예약. (design D2·D5)"""
-    model_config = ConfigDict(extra="forbid")
-    request_id: str = Field(min_length=1, max_length=64)
-    query: str = Field(min_length=1, max_length=300)
-    chunks: list[DigestChunk] = Field(max_length=20)
-
-class DigestResult(BaseModel):
-    """/digest 출력 계약 — 2차 구현 예약."""
-    summary: str
-    source_paths: list[str]
```

**error code 목록에서 not_implemented 삭제** (`wrapper/src/app/domain/envelope.py`):

```diff
 class ErrorBody(BaseModel):
-    code: str                      # busy | upstream | upstream_timeout | schema_violation
-    detail: str | None = None      # | invalid_request | not_implemented
+    code: str                      # busy | upstream | upstream_timeout
+    detail: str | None = None      # | schema_violation | invalid_request
```

설계 D2/D9·README에서도 계약을 지우되, **D5에는 제거 사유를 기록으로 남겼다**(결정의
흔적까지 지우지는 않는다). 테스트는 27건으로 줄어 green.

---

## 5. 구현 중 마주친 문제

없음 — 예약석이 로직 없는 계약뿐이라 제거가 곧 끝이었다. 역설적으로 "지우기 쉬웠다"는
사실 자체가 예약석의 비용이 정말 낮았다는 증거이기도 하다. 그래도 지운 이유는 2절 —
낮은 비용이 0은 아니고, 틀린 예약석은 없느니만 못하다.

---

## 6. 결론

기능 표면 = 실제로 쓰는 것(/rewrite·/health)만. 요약이 필요해지는 날이 오면 그날의
요구사항으로 새 이슈에서 설계한다. PR: #11.
