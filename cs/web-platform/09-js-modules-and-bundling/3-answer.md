# web-platform/09-js-modules-and-bundling — 정답

## 정답

### 1. 나눠 보내기 vs 합쳐 보내기

- 나눠 보내면: 모듈을 받아 파싱해야 다음 import를 알기 때문에 의존 깊이만큼 왕복이 순차로 쌓인다.
- 합쳐 보내면: 왕복은 한 번이지만 안 쓰는 코드·첫 화면에 필요 없는 코드까지 먼저 받고 파싱한다.
- 번들러가 하는 일: ① 의존 그래프 구축 ② 트리 셰이킹(안 쓰는 export 제거) ③ 코드 분할(동적 import 경계로 청크) ④ 축소 + 내용 해시 파일명.

### 2. CommonJS vs ES 모듈

- CommonJS: 실행 중 `require`가 불릴 때 불러온다(동적·동기). `require()`는 `module.exports` 값을 돌려준다(객체면 그 참조, 구조 분해하면 그 순간 값을 복사).
- ES 모듈: 실행 전에 import·export 구조가 정해진다(정적). 가져온 이름은 내보낸 변수에 대한 살아 있는 바인딩이다.
- 정적 구조라 빌드 때 "어떤 export가 쓰이나"를 판정할 수 있어 트리 셰이킹이 된다. CommonJS는 조건부 `require`·동적 키 접근 때문에 판정이 어렵다.

### 3. 세 단계

```text
  파싱·적재 ──▶ 링크(Link) ──▶ 평가(Evaluate)
                  └ 없는 export 이름 → SyntaxError (실행 전)
```

- 평가는 의존 모듈부터 후위 순서로 한 번씩.
- 순환은 ECMA-262가 DFS + `[[DFSIndex]]`·`[[DFSAncestorIndex]]`로 강연결 요소를 묶어 처리한다(Tarjan식).

### 4. 의존 사슬 깊이 6

```text
(실험, headless Chrome 151, latency 100ms 에뮬레이션)
/unbundled.html   JS 요청 7개, 마지막 모듈 실행 시각(performance.now) = [870, 868, 866] ms
/preload.html     JS 요청 7개, 마지막 모듈 실행 시각(performance.now) = [329, 337, 333] ms
/bundled.html     JS 요청 1개, 마지막 모듈 실행 시각(performance.now) = [225, 222, 224] ms
```

- (c) 번들 약 225ms < (b) modulepreload 약 330ms < (a) 번들 없음 약 870ms. 두 번째 실행도 866~881 / 331~337 / 227ms, 사실 점검 재실행 2회도 871~895 / 334~350 / 226~233ms로 같은 순서.
- (a)는 각 모듈을 받아 파싱한 뒤에야 다음 모듈을 요청하므로 7개 요청이 순차로 100ms씩 쌓인다. (b)는 HTML이 m0~m5를 미리 알려 여섯 개를 동시에 요청한다. 다만 이 HTTP/1.1 서버에서는 동시 연결이 6개라 `entry.js`는 연결이 빌 때까지 한 왕복 기다렸다(서버 도착 시각 측정). 그래서 번들(2왕복)보다 한 왕복 정도 느리다.

### 5. TABLE과 PURE

```text
2-treeshake.min.js            625 B  unused-A/B:0  row-:1
3-treeshake-pure.min.js       529 B  unused-A/B:0  row-:0
```

- 트리 셰이킹만으로는 남는다(`row-:1`). `Array.from(...)` 호출에 부수 효과가 있을지 모르기 때문이다. 쓰이지 않는 함수 선언 `bigUnusedA/B`는 빠졌다.
- `/* @__PURE__ */`를 붙이면 "부수 효과 없는 호출"로 보고 제거된다(529B, `row-:0`).

### 6. sideEffects 오선언

```text
▲ [WARNING] Ignoring this import because "src3/node_modules/mylib/register.js" was marked as having no side effects [ignored-bare-import]
```

- `register.js` import가 통째로 사라져 `window.__registered` 코드가 번들에 없다.
- esbuild는 위 경고를 낸다.
- 같은 원리로: 컴포넌트의 `import './Button.css'`가 사라져 프로덕션에서만 스타일이 없거나, 폴리필이 빠져 구형 브라우저에서만 `is not a function`. 대처: `"sideEffects": ["**/*.css", ...]`.

### 7. 바꿔치기 뒤 동적 import

```text
탭에서 차트 버튼 클릭 → TypeError: Failed to fetch dynamically imported module: http://127.0.0.1:PORT/chart-XZXOI6CO.js
서버 요청: /chart-XZXOI6CO.js
새로고침 후 클릭 → chart-v2
```

- Chrome 151 네이티브 ESM: `TypeError: Failed to fetch dynamically imported module: <옛 청크 URL>`(그 청크 404).
- webpack 런타임: `ChunkLoadError`, 메시지 `Loading chunk <id> failed.`(webpack `JsonpChunkLoadingRuntimeModule.js`).
- Vite: `vite:preloadError` 이벤트(`preventDefault()`로 오류 전파를 막고 새로고침 등 처리).

### 8. 해시 연쇄

- `main`의 내용에 chart 청크의 파일명(`import("./chart-XZXOI6CO.js")`)이 들어 있다. chart 해시가 바뀌면 그 문자열이 바뀌어 `main` 내용도, 해시도 바뀐다.
- 의미: 한 청크 수정이 그것을 가리키는 부모 청크들의 캐시까지 무효화한다. 런타임 매니페스트를 따로 빼거나 import map으로 이름 연결을 분리하면 연쇄를 줄일 수 있다.

### 9. 배포 직후 ChunkLoadError

- 원인
  - 열린 탭의 옛 코드가 옛 해시 청크를 가리키는데 배포가 옛 파일을 지웠다.
  - CDN이나 서비스 워커에 캐시된 옛 HTML이 옛 `main`을 가리킨다.
- 예방
  - 옛 해시 자산을 몇 배포분 보존한다.
  - HTML은 `Cache-Control: no-cache`, 해시 자산은 `immutable`.
  - 청크 오류를 잡아 한 번만 새로고침(무한 루프 방지 플래그). 서비스 워커는 HTML을 network-first로.

### 10. 큰 main.js

- 순서: 번들 분석(메타파일·분석기)으로 큰 모듈 찾기 → Coverage로 미사용 비율 확인 → 전체 import를 개별·ESM import로 → 라우트·상호작용 단위 동적 import → `@__PURE__`·`sideEffects` 정리 → 크기 예산을 CI에.
- 너무 잘게 나누면 청크 요청 수와 순차 발견(폭포)이 다시 늘어 4번의 (a)(실험 B) 같은 지연이 돌아온다. 공유 청크·preload로 보완한다.
