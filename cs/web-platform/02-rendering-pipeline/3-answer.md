# web-platform/02-rendering-pipeline — 정답

## 정답

### 1. 단계로 나누는 이유

- 단계마다 결과물(DOM·계산된 스타일·레이아웃 트리·디스플레이 리스트·레이어)을 들고 있으면, 바뀐 것이 닿는 단계부터만 다시 계산하면 된다.

```text
  width      Style → Layout → Paint → Composite   기하가 바뀜
  color      Style →          Paint → Composite   모양만 바뀜
  transform  Style →                  Composite   레이어를 옮기기만(자기 레이어가 있을 때)
```

- 근거: web.dev "Rendering performance"의 세 경로.

### 2. 스크립트·CSS가 막는 것

```text
 파서  ──<head> ── <link css> ── <script> ▒▒▒▒▒▒▒▒▒▒(정지)▒▒▒▒▒▒▒ ── 계속 파싱 ──
 CSS                 └──── 다운로드 ─────┘
 JS                            └ 다운로드 ┘ (CSS 끝나길 기다림) [실행]
 첫 렌더링   ×××××××××××××××××××××××××××××××××××××××××××××  ── 여기서 가능
```

- 동기 `<script>`: 파서를 멈춘다(`document.write`로 문서를 바꿀 수 있으므로). 앞선 스타일시트 중 스크립트를 막는 조건(파서가 넣음·`media` 일치·활성)을 채운 것이 아직 로딩 중이면, 그것이 끝나야 실행된다(HTML "Interactions of styling and scripting").
- CSS: 파서는 계속 가지만, 렌더 차단 조건을 채운 스타일시트(예: `media`가 맞는 `<head>`의 시트)가 준비될 때까지 첫 렌더링이 막힌다(렌더 차단). `media="print"` 시트는 화면 렌더링을 막지 않는다.
- 세부·처방(preload 스캐너, `defer`/`async`)은 13번.

### 3. 강제 동기 레이아웃의 조건

- `el.style.width = …`는 "더러움" 표시만 하고 돌아온다. 계산은 다음 렌더링 업데이트로 미뤄진다.
- `el.offsetWidth`가 부르는 쪽이다. 기하 읽기는 최신 값을 돌려줘야 하므로, 스타일·레이아웃이 더러우면 그 자리에서 계산을 끝낸다.
- 그래서 "쓰기 뒤의 읽기"가 강제 동기 레이아웃이다. 더러운 것이 없으면 읽기만으로는 다시 계산하지 않는다.

### 4. 교차 vs 분리

(실험, headless Chrome 151, CPU 1×·4× 스로틀, 2026-10-04 — 5회 범위)

```text
CPU 1x interleaved N=300  LayoutCount+300  RecalcStyleCount+300  LayoutDuration 136.3~161.3ms  함수 실행 145.7~180.5ms  (5회)
CPU 1x batched     N=300  LayoutCount+1  RecalcStyleCount+1  LayoutDuration 1.1~1.6ms  함수 실행 1.3~2.5ms  (5회)
CPU 4x interleaved N=300  LayoutCount+300  RecalcStyleCount+300  LayoutDuration 503.7~682.9ms  함수 실행 532.6~767.3ms  (5회)
CPU 4x batched     N=300  LayoutCount+1  RecalcStyleCount+1  LayoutDuration 5.0~7.5ms  함수 실행 5.4~9.0ms  (5회)
```

- 교차 +300, 분리 +1. 횟수는 다섯 번 모두 같았다.
- 4× 스로틀에서 시간은 대략 4~5배가 됐다(교차 함수 0.53~0.77초, 사실 점검 재실행 포함 0.53~0.91초). 횟수는 그대로다.

### 5. 애니메이션 방식별 레이아웃

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04 — 집필 3회는 같은 값, 사실 점검 재실행 3회 중 1회는 `left` 61)

```text
run1 left      LayoutCount+62  RecalcStyleCount+62  trace: Layout=62 Paint=124 UpdateLayoutTree=62
run1 transform LayoutCount+1  RecalcStyleCount+62  trace: Layout=1 Paint=2 UpdateLayoutTree=62
run1 css       LayoutCount+2  RecalcStyleCount+6  trace: Layout=2 Paint=5 UpdateLayoutTree=6
```

- `left` 61~62(프레임마다), `transform`(rAF) 1, CSS 애니메이션 2.
- `transform`(rAF)에서 스타일 계산이 프레임마다(62) 도는 이유: 스크립트가 매 프레임 인라인 스타일을 바꾸므로 스타일은 다시 계산해야 한다. 다만 기하가 안 바뀌어 레이아웃·페인트는 건너뛴다.
- CSS 애니메이션은 (이 `transform` 애니메이션처럼 합성 가능한 경우) 진행을 컴포지터가 맡아 메인 스레드 스타일 계산도 6번이었다(해석).

### 6. 레이어 수와 메모리 어림

(실험, headless Chrome 151, 2026-10-04)

```text
will-change 요소   0개 → 레이어 4개, ...
will-change 요소  10개 → 레이어 14개, ...  "WillChangeTransform":10
will-change 요소 100개 → 레이어 104개, ... "WillChangeTransform":100
```

- 10개 → 14개, 100개 → 104개. 이 실험의 Chrome 151에서는 요소당 레이어 하나였다(`will-change`는 힌트라 요소가 너무 많으면 승격을 피할 수 있다 — CSS Will Change §2).
- 어림(예시): 100 × 200 × 20px × 4B = 1,600,000B ≈ 1.6MB. 타일 단위 할당·DPR·래스터 방식에 따라 실제와 다르고, 실험은 메모리를 직접 재지 않았다.

### 7. 선택자 매칭

- RuleSet 버킷: 규칙을 가장 오른쪽 compound(`a`)의 id·class·tag로 분류해 둔다. `<a>` 요소는 자기 태그·클래스·id 버킷과 UniversalRules 등에서 후보를 꺼낸다(Blink `style-calculation.md`, `element_rule_collector.cc`). 조상의 `.item`은 버킷 키가 아니라 다음 단계에서 검사한다.
- 오른쪽→왼쪽: 후보마다 요소에서 시작해 결합자를 따라 부모·조상으로 올라가며 `li.item`, `.list`를 찾는다(`selector_checker.cc` `MatchSelector`).
- Bloom 필터: DOM을 내려가며 조상들의 태그·id·클래스 해시를 비트 집합에 넣어 둔다. 필터가 "`.list` 조상은 없다"고 하면 조상 순회 없이 탈락시킨다(`selector_filter.h`). 거짓 양성은 있을 수 있어 통과하면 실제로 검사한다.

### 8. 아코디언 Forced reflow

- 확인: Performance 패널에서 Layout 막대가 촘촘히 반복되는 구간의 호출 스택. CDP로 재면 `LayoutCount`가 항목 수만큼 는다.
- 원인: 항목마다 높이를 쓰고 바로 `scrollHeight`·`offsetHeight`를 읽는다.
- 고치기: 항목들의 높이를 먼저 다 읽고 나중에 한꺼번에 쓴다. 쓰기는 rAF로 모은다. 가능하면 높이 측정 없이 CSS(`grid-template-rows: 0fr → 1fr` 전환, `interpolate-size` 등)로 바꾼다 [?: 대상 브라우저 지원 범위는 확인 필요].

### 9. `will-change` 남용

- 왜: 이 실험의 Chrome 151에서는 요소마다 합성 레이어가 생겼다(100개 → 104 레이어). 레이어마다 메모리·GPU 텍스처 업로드·관리 비용이 있어 메모리가 적은 기기에서 오히려 느려진다(web.dev 레이어 비용).
- 확인: DevTools Layers 패널, Rendering 탭 "Layer borders", CDP `LayerTree.compositingReasons`의 `WillChangeTransform` 개수.
- 고치기: 실제로 움직일 요소에만, 움직임을 예측할 수 있을 때 조금 앞서(예: hover 시) 걸고 끝나면 뗀다. 시작 바로 직전에 걸면 준비 시간이 없어 효과가 적다(CSS Will Change §1.2).
