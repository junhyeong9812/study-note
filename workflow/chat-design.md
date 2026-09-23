# chat — 우측 채팅 패널: 현재 문서에 대해 묻는다

> **구현 완료(2026-09-01)**. llm /chat·backend 오케스트레이션·front 패널·PC 브리지 전부 가동.
> 아래는 설계이자 현행 구조. 브리지 보안은 codex 리뷰 F2~F8 반영(인증·동시1·상한·도구차단).

```
[front 우측 패널]  하단 입력 + → 버튼, 스트림 타자 렌더
   │  POST /api/chat {doc_path, question}   ← 문서 "내용"이 아니라 "경로"만 (변조 차단·경량)
   │  쿠키: chat_session (HttpOnly — 값은 세션 id뿐, 대화 내용은 절대 쿠키에 안 담는다)
   ▼
[backend 채팅 오케스트레이션]
   ├─ 세션: 쿠키 없으면 발급(중앙 발급 규약) · 있으면 검증
   ├─ 기록: Redis chat:{sessionId}:{docPath} = messages 배열 (TTL 7일)
   │        첫 대화 판정 = 이 키의 존재 여부
   ├─ 컨텍스트 조립: 첫 대화면 git에서 doc_path 원문 로드 → system 컨텍스트로
   │                이후엔 기록의 최근 N턴 + 새 질문
   └─ llm /chat 호출, SSE로 중계 (MVC ResponseBodyEmitter — webflux 불필요, 비교 문서 참조)
        ▼
[llm wrapper /chat]  Ollama stream:true 청크 중계 (세마포어·타임아웃 규약 동일)

[에스컬레이션 — 방식 ⓑ: PC의 Claude Code headless]
   답변 아래 "더 정확한 답변" 버튼(수동 트리거)
   ├─ + (실험) 모델 자가신고: 스트림 말미에 확신도 토큰을 뱉게 해서
   │   "애매함/모름" 신고 시 버튼을 강조 — 7B 자가평가는 과신 경향이 있어
   │   자동 전환이 아니라 "제안"까지만 ([구현 검증] 등재)
   └─ backend →(X-Bridge-Secret)→ socat(.158) → 역터널 → PC 브리지 → `claude -p --allowedTools ""`
      · 인증(공유 시크릿 상수시간)·동시 1건·출력 20KB 상한·도구 전면 차단(프롬프트 주입 완화)
      · 비스트리밍(단일 응답 — F5 결정): 수십 초 소요, 실패 시 "지금은 로컬 답변만 가능" 안내
      · 제약: PC 온라인 필요. 서브넷 분리라 역터널로 노출(tools/claude-bridge/README)
```

**설계 원칙**
1. 대화 상태의 정본은 서버(Redis) — 쿠키는 열쇠(id)만.
2. 문서의 정본은 git — front가 내용을 실어 나르지 않는다.
3. 폴백 사다리: qwen3(로컬·즉시) → Claude(정확·느림·수동 트리거) — 검색의 폴백 철학과 동일.
