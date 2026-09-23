# cs/issue/typescript/react/theming-token-reach — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
테마 토글 → :root[data-theme=light] { --bg, --fg, --st-*, ... } 재정의

  CSS 캐스케이드가 닿는 곳                    닿지 않는 곳 (각자 API로 주입)
  ─────────────────────────                  ─────────────────────────────────
  일반 DOM 요소 (color: var(--fg))  ✔         canvas 위젯 (터미널)      → options.theme 갱신 + fit()
  CSS 규칙 안의 SVG stroke          ✔         JS 옵션 테마 (에디터)     → reconfigure (편집 상태 보존)
                                              자체 테마 클래스 서드파티 → theme className 교체
                                              SVG "속성" stroke=var()   → CSS 클래스 규칙으로 이동
                                              네이티브 select 목록(OS)  → 토큰만 쓰는 커스텀 컴포넌트

[실패 지점 1] 비-CSS 표면을 CSS 변수만으로 바꾸려 함 → 그 표면만 어둡게 남음
[실패 지점 2] 설정 변경마다 위젯 재생성 → 색은 맞지만 편집 내용·세션 상태 소실
[실패 지점 3] 한 시각 단위의 색 일부만 토큰
                 color:      var(--st-danger)        ← 테마 추종
                 background: rgba(R,G,B,.15)     ← 고정 → 라이트에서 off-palette
[교정]       background: color-mix(in srgb, var(--st-danger) 15%, transparent)
             같은 값·다른 의미 → 다른 토큰 (독립 조정 가능)
             검증 grep은 fallback 제외, bare 리터럴만
```

## 핵심 문장

- CSS 커스텀 프로퍼티는 **우리 DOM의 CSS 캐스케이드**에만 닿는다 — canvas·JS 옵션·서드파티 테마 클래스·OS 네이티브 위젯은 각자의 API로 주입해야 한다.
- 출처(토큰)는 하나, 전달 경로는 표면마다 — 테마 스토어를 구독해 각 API로 밀어 넣는다.
- 가능하면 위젯을 재생성하지 말고 **라이브 재구성**한다 — 재생성은 내부 상태(편집·세션)를 버린다.
- 한 시각 단위(텍스트+배경+테두리)의 모든 색은 **같은 토큰에서 파생**돼야 테마 전환이 일관된다(`color-mix`).
- 값이 같아도 의미가 다르면 토큰을 나눈다 — 합치면 한쪽을 조정할 때 다른 쪽 의도가 깨진다.
