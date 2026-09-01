# issue11 — 우측 채팅 패널: 스트림을 타자로 그리기

- 이슈 #25 · PR: #26

## 1. 배경

빈 우측 공간에 "현재 문서에게 묻는" 채팅 패널(340px). 문서 페이지에서만 뜨고(폴더/트리
화면엔 없음), 답은 ChatGPT처럼 타자 치듯 흐른다.

## 2. 방식 — ReadableStream을 조각조각 렌더

```tsx
const reader = response.body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const token = decoder.decode(value, { stream: true });
  setMessages(prev => { /* 마지막 assistant 메시지에 token 이어붙임 */ });
}
```

**BFF의 핵심은 쿠키 왕복**: 세션은 backend가 발급하므로, front 프록시가
`set-cookie`(상류→브라우저)와 `cookie`(브라우저→상류)를 **양방향으로 전달**해야
세션이 성립한다. 스트림 바디는 `new Response(upstream.body)`로 그대로 흘린다(버퍼링 안 함).

## 3. 페이지별 대화 + 에스컬레이션

- doc_path가 바뀌면 이력 재로드(문서마다 다른 대화) — Redis 키가 path별이라 자연스러움.
- 답변 아래 **"더 정확한 답변 (Claude)" 버튼**(수동 트리거 — 7B 자가판정은 과신이라
  자동 전환 안 함). 누르면 마지막 질문을 escalate로, Claude 답변은 테두리로 구분.
- 브리지 오프라인이면 "지금은 로컬 답변만 가능"으로 우아하게.

## 4. 결론

엣지 최종 E2E: www.junproject.xyz 문서에서 채팅 스트림("블룸 필터는…") + 에스컬레이션
동작. PR #26
