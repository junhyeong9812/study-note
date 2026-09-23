# cs/issue/typescript/next/ssr-hydration-parity — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
서버:  React 트리 ──render──▶ HTML 문자열 ──전송──▶ 브라우저 HTML 파서 ──▶ DOM
클라:  React 트리(첫 렌더) ──hydrate: 기존 DOM과 대조·이벤트 부착──▶ 일치해야 함
                                  │
       불일치 원인 ①  첫 렌더가 브라우저 전용 값에 의존
                      typeof window 분기 / lazy initializer 가 window 읽음
                      서버: 빈 것·0   클라: SiteMap·실제 폭   → mismatch
                      → 첫 렌더는 서버와 같은 값, 브라우저 값은 마운트 후 effect에서
       불일치 원인 ②  서버 HTML 이 파서를 거치며 재구성됨
                      <p><p>..</p></p> → 파서가 앞 <p>를 자동으로 닫음 → DOM ≠ React 트리
                      → 중첩 규칙에 맞는 태그(<div>)
```

## 핵심 문장

- 하이드레이션은 서버가 만든 DOM을 **재사용**한다 — 클라이언트 첫 렌더 결과가 그 DOM과 같아야 한다.
- 브라우저에서만 참인 조건·window 값은 첫 렌더에 쓰지 않는다 — **마운트 후 effect**에서 반영한다.
- lazy initializer도 첫 렌더다 — 클라이언트에서만 실행된다고 서버와 같아지지 않는다.
- 서버 HTML은 브라우저 **HTML 파서를 거친다** — 중첩 규칙 위반은 파서가 고쳐 쓰고, 그 결과는 React 트리와 다르다.
