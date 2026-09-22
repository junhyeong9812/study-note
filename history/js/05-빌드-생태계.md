# JS 모듈·빌드·도구 생태계 변천사

> 원본: `~/project/js-history/05-빌드-생태계.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-19).\
> 연도·인명·버전·수치·코드·표는 원문 그대로다.\
> ASCII 도식 7개(그중 3개는 원문 mermaid 그림을 글자로 옮긴 것, 1개는 원문의 글자 도식 그대로)와 「한눈에」의 공구상 비유(대응표 포함), 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> `<script>` 태그 한 줄에서 시작해 Rust로 다시 쓰이기까지 — 자바스크립트는 어떻게 모듈을 갖고, 번들러를 만들고, 타입을 입었으며, 끝없이 파편화한 뒤 다시 수렴하고 있는가.

이 문서의 주 비유는 **표준 규격이 없던 시절의 공구상**이다.\
용어 블록에서만 잠깐 쓰는 국소 비유(서랍 등)가 몇 개 더 있다.

| 비유 | 실체 |
|------|------|
| 나사 규격을 정한 표준이 아직 없다 | 언어 명세(ECMAScript)가 모듈·도구를 정해 주지 않았다 |
| 가게마다 자기 규격의 나사를 판다 | CommonJS·AMD·UMD 같은 경쟁 규약이 난립했다 |
| 어느 가게 것이든 다 맞는 어댑터를 판다 | UMD — "둘 다 지원"하는 타협물 |
| 나중에 국가 표준 나사가 정해진다 | ES2015가 모듈(ESM)을 언어 표준으로 명세했다 |

- JavaScript는 **작은 용도로 출발한 언어**였다.\
  모듈도, 표준 라이브러리도, 빌드 도구도 없이 시작했다.
- 그런데 **서버(Node)와 대규모 앱(SPA)** 으로 떠밀려 올라갔다.\
  언어가 안 주는 것을 커뮤니티가 직접 만들어 메울 수밖에 없었다.
- 그래서 **같은 자리에 여러 답이 동시에 존재**했다 — 이것이 파편화다.\
  모듈도, 번들러도, 트랜스파일러도, 타입도, 패키지 매니저도 전부 이걸 겪었다.
- 표준이나 압도적 도구가 나오면 **다시 하나로 모인다** — 이것이 수렴이다.\
  이 편은 그 왕복(파편화 ↔ 수렴)을 다섯 축으로 따라간다.

> **모듈(module)** — 코드를 파일 단위로 나누고, 밖에 내줄 것과 감출 것을 구분하는 장치.\
> 예: 공구를 한 상자에 쏟아 붓지 않고 서랍마다 나눠 넣는 것.

> **파편화(divergence) / 수렴(convergence)** — 같은 문제에 경쟁 답이 여럿 생기는 것 / 그중 하나로 다시 모이는 것.\
> 예: 가게마다 다른 나사 규격이 파편화, 국가 표준 나사가 수렴이다.

## 큰 그림: 왜 이렇게 복잡해졌나

*(이 편의 「시대 배경 — 그전에는 어땠나」에 해당한다)*

자바스크립트는 1995년 브렌던 아이크가 **열흘** 만에 만든 언어다.\
애초에 웹페이지에 작은 동작 하나를 붙이는 용도였고, **모듈 시스템도, 표준 라이브러리도, 빌드 도구도 없었다.**\
그런데 2009년 Node.js가 등장하며 서버로, 2010년대 SPA(Single Page Application)가 확산되며 대규모 애플리케이션 언어로 떠밀려 올라갔다.\
언어 명세(ECMAScript)는 1999년 ES3 이후 2009년 ES5까지 10년간 정체됐고, 2015년 ES2015(ES6)에서야 모듈·클래스·`let`/`const`가 표준화됐다.

이 **"명세의 공백"** 이 핵심이다.\
언어가 채워주지 못한 빈자리를 커뮤니티가 라이브러리·관례·도구로 메웠고, 표준이 없으니 경쟁 구현이 난립했다.\
그래서 JS 생태계의 역사를 원문은 한 문장으로 요약한다.

> **표준이 비어 있던 시기에 커뮤니티가 파편화로 메우고(divergence), 표준과 성능이 따라잡으면서 다시 수렴한다(convergence).**

```text
진자 — 원문이 말하는 파편화와 수렴의 왕복

  표준이 비어 있다
        |
        v
  커뮤니티가 경쟁 구현으로 메운다   (파편화 / divergence)
        |
        v
  표준 또는 압도적 도구가 따라잡는다
        |
        v
  하나로 모인다                    (수렴 / convergence)
        |
        +--> 그리고 다시 위로 (반복)
```

- 원문의 두 낱말(divergence·convergence)을 그 순서 그대로 세로로 놓은 것이다.
- 원문이 "모듈도, 번들러도, 트랜스파일러도, 패키지 매니저도 전부 이 진자 운동을 반복했다"고 적은 그 운동이다.

모듈도, 번들러도, 트랜스파일러도, 패키지 매니저도 전부 이 진자 운동을 반복했다.\
아래는 그 진자의 5개 축이다.

| 축 | 파편화 시기 | 수렴점 |
|----|-----------|--------|
| **모듈 시스템** | 전역 → IIFE → CommonJS vs AMD vs UMD | **ESM (ES2015 표준)** |
| **번들러** | browserify / webpack / Rollup / Parcel | **Vite (+esbuild/Rollup)** — 사실상 표준 |
| **트랜스파일** | 6to5 / Traceur / TypeScript | **Babel + tsc**, 그리고 Rust(swc/oxc)로 이동 중 |
| **타입** | (없음) / Closure / Flow / TypeScript | **TypeScript** 지배 |
| **패키지 매니저** | npm → yarn → pnpm | 셋 공존, lockfile·workspace는 공통 |

---

## 1. 모듈 시스템: 전역 오염에서 ESM 표준까지

*(여기 1절부터 6절까지가 이 편의 「무엇이 바뀌었나」다)*

### 1.0 전역 변수 시대 (~2009)

초기 JS에는 모듈 개념이 없었다.\
코드는 HTML의 `<script>` 태그로 순서대로 로드됐고, **모든 변수가 하나의 전역(`window`) 객체를 공유**했다.\
파일이 늘어날수록 이름 충돌(namespace pollution), 로드 순서 의존성, 캡슐화 부재가 재앙이 됐다.

```html
<!-- 로드 순서가 곧 의존성. a.js의 함수가 b.js의 전역을 덮어쓰면 끝 -->
<script src="jquery.js"></script>
<script src="a.js"></script>   <!-- var helper = ... (전역 오염) -->
<script src="b.js"></script>   <!-- 또 var helper = ... 충돌! -->
```

> **전역 오염(namespace pollution)** — 모든 코드가 같은 이름 공간(`window`)을 써서, 같은 이름을 쓴 쪽이 서로를 덮어쓰는 상태.\
> 예: 위 코드의 `a.js`와 `b.js`가 둘 다 `helper`를 만들면 나중에 로드된 쪽만 남는다.

### 1.1 IIFE와 모듈 패턴 (~2010)

표준이 없으니 개발자들은 **함수 스코프**를 이용해 흉내 냈다.\
즉시 실행 함수 표현식(IIFE, Immediately Invoked Function Expression)으로 사적 스코프를 만들고, 필요한 것만 전역에 노출하는 "모듈 패턴"이다.

```javascript
// IIFE로 사적 스코프를 만들고 공개 API만 반환
var Counter = (function () {
  var count = 0;                 // 외부에서 못 건드리는 private
  return {
    increment: function () { count++; },
    value: function () { return count; }
  };
})();
Counter.increment();
Counter.value(); // 1
```

> **IIFE(즉시 실행 함수 표현식)** — 만들자마자 바로 실행해서, 그 안의 변수를 바깥에서 못 보게 가두는 함수.\
> 예: 위 코드의 `count`는 `Counter` 밖에서 손댈 수 없다.

이것이 jQuery 플러그인·라이브러리의 표준 작성법이었다.\
캡슐화는 얻었지만 **의존성 선언·자동 로딩은 여전히 수동**이었다.

### 1.2 CommonJS — 서버의 동기 모듈 (2009)

2009년 Node.js가 등장하며 게임이 바뀐다.\
서버에서는 파일시스템 접근이 빠르니 **동기(synchronous) 로딩**이 자연스러웠고, CommonJS 규약의 `require()` / `module.exports`가 채택됐다.

```javascript
// math.js
function add(a, b) { return a + b; }
module.exports = { add };

// main.js
const math = require('./math');   // 동기 로드, 즉시 사용 가능
console.log(math.add(2, 3));      // 5
```

> **동기 로딩(synchronous loading)** — 모듈을 다 읽어 올 때까지 그 자리에서 기다렸다가 바로 쓰는 방식.\
> 예: 위 코드의 `require('./math')`는 그 줄에서 파일을 다 읽고, 다음 줄에서 즉시 `math.add`를 쓴다.

CommonJS는 npm 생태계의 폭발을 떠받친 토대다.\
단순하고 직관적이라 수백만 패키지가 이 형식으로 쌓였다.

**대가는 무엇인가** — 원문이 적은 근본 충돌이다.\
**`require()`가 동기라는 점이 브라우저와 근본적으로 충돌했다** — 네트워크로 모듈을 받아오는 동안 페이지를 멈춰 세울 수는 없었다.

### 1.3 AMD / RequireJS — 브라우저의 비동기 모듈 (2011)

이 충돌을 풀려는 시도가 AMD(Asynchronous Module Definition)다.\
흥미롭게도 AMD는 **CommonJS 팀 내부에서 방향성에 이견을 가진 멤버들이 갈라져 나와** 만든 규약이다(파편화의 전형).\
`define()`으로 의존성을 비동기 로드하며, RequireJS가 이를 대중화했다.

```javascript
// AMD: 의존성을 배열로 선언, 콜백으로 비동기 주입
define(['jquery', './math'], function ($, math) {
  return {
    render: function () { $('#out').text(math.add(2, 3)); }
  };
});
```

문법이 장황하고 콜백 중첩이 많아 호불호가 갈렸다.\
그래서 **UMD(Universal Module Definition)** 라는 "둘 다 지원" 보일러플레이트가 등장했다 — CommonJS·AMD·전역을 런타임에 감지해 어디서든 동작하는, 파편화 시대의 타협물이었다.

```javascript
// UMD: 환경을 감지해 CommonJS/AMD/전역 어디든 붙는다 (파편화의 상처)
(function (root, factory) {
  if (typeof define === 'function' && define.amd) define([], factory);      // AMD
  else if (typeof module === 'object') module.exports = factory();          // CommonJS
  else root.MyLib = factory();                                              // 전역
}(this, function () { return { /* ... */ }; }));
```

> **UMD(Universal Module Definition)** — 실행 환경이 CommonJS인지 AMD인지 전역인지를 런타임에 감지해, 어디에 놓여도 붙도록 감싸 둔 보일러플레이트.\
> 예: 위 코드의 `if / else if / else` 세 갈래가 그 감지다.

### 1.4 ESM — ES2015 표준의 수렴점 (2015)

2015년 6월 **ECMAScript 2015(ES6)가 모듈을 언어 표준으로 명세했다.**\
`import` / `export` 문법은 서버와 브라우저 양쪽에서 동작하도록 설계됐고, 무엇보다 **정적(static)** 이다 — 의존성이 실행 전에 결정되므로 컴파일러가 분석할 수 있다.\
이 정적성이 곧 **트리 셰이킹(tree-shaking, 미사용 코드 제거)** 의 전제가 됐다.

```javascript
// math.js
export function add(a, b) { return a + b; }   // named export
export default class Calculator { /* ... */ } // default export

// main.js
import Calculator, { add } from './math.js';  // 정적 — 빌드 타임에 분석 가능
console.log(add(2, 3));
```

> **정적(static)** — 무엇을 불러오는지가 코드를 실행하기 전에 이미 정해져 있다는 뜻.\
> 예: 위 `import ... from './math.js'`는 실행해 보지 않아도 도구가 읽어서 의존 관계를 알 수 있다.

> **트리 셰이킹(tree-shaking)** — 실제로 쓰이는 코드만 번들에 넣고 나머지를 털어 내는 것. 정적 분석이 가능해야 할 수 있다.\
> 예: `math.js`가 여러 함수를 내보내도 `add` 하나만 import했다면 나머지는 결과물에 안 들어간다.

ESM은 **명세는 2015년이었지만 도착은 느렸다.**\
브라우저 네이티브 지원은 2017~2018년(Chrome 61, Safari 10.1, Firefox 60)에야 왔고, Node.js는 12(2019, 실험)에서 16(2021, 안정)에 걸쳐 받아들였다.\
CommonJS와 ESM은 한동안 어색하게 공존했고(`.mjs` 확장자, `"type": "module"`, dual package hazard 같은 상처가 그 흔적이다), 2025년 무렵에야 "**새 프로젝트는 ESM**"이 정착했다.

원문의 mermaid 계보 그림을 글자 도식으로 옮기면 이렇다(노드 문구와 화살표 방향은 그대로다).

```text
모듈 시스템의 계보

  전역 변수 (~2009) · window 오염
        |
        v
  IIFE/모듈 패턴 (~2010) · 함수 스코프
        |
        +---> CommonJS (2009, Node) · 동기 require
        |           |
        |           +---> UMD (타협: 둘 다 지원)
        |           |
        |           +---> ESM (ES2015 표준) · 정적 import/export
        |
        +---> AMD/RequireJS (2011, 브라우저) · 비동기 define
                    |
                    +---> UMD (타협: 둘 다 지원)
                    |
                    +---> ESM (ES2015 표준) · 정적 import/export

  UMD ....수렴....> ESM
```

- 노드 문구·연도·화살표의 출발점과 도착점은 전부 원문 그림 그대로다.
- 원문이 **관계의 종류를 밝힌 화살표는 맨 아래 점선의 「수렴」 하나뿐**이다. 나머지 실선 화살표에는 원문이 라벨을 붙이지 않았으므로, 여기서도 종류를 단정하지 않는다.
- UMD와 ESM이 두 번씩 나오는 것은 원문 그림에서 CommonJS와 AMD 양쪽이 각각 그 둘로 화살표를 보내기 때문이다.

원문이 이 절을 맺는 문장은 이것이다.

> **수렴의 교훈**: 동기(서버)와 비동기(브라우저)라는 두 요구가 CommonJS·AMD로 갈라졌고, 언어 표준(ESM)이 *정적 분석*이라는 제3의 답으로 둘을 흡수했다. 표준이 채워지자 파편화는 레거시 호환 부담만 남기고 사라졌다.

---

## 2. 번들러: 왜 묶어야 했나, 그리고 왜 안 묶게 됐나

### 2.0 번들러가 필요한 이유

모듈을 파일로 쪼개면 개발은 편하지만, 브라우저가 수백 개 파일을 일일이 HTTP로 받으면 느리다(특히 HTTP/1.1 시대).\
또 브라우저는 CommonJS의 `require()`를 이해하지 못한다.\
**번들러**는 ① 의존성 그래프를 따라가 ② 모든 모듈을 하나(또는 몇 개)의 파일로 합치고 ③ 브라우저가 모르는 문법을 변환하는 도구다.

```text
번들러가 하는 세 가지 — 원문이 ①②③으로 적은 일이다

  쪼개 둔 소스 파일들
        |
        v
  번들러가 하는 일
    ① 의존성 그래프를 따라간다
    ② 모든 모듈을 하나(또는 몇 개)의 파일로 합친다
    ③ 브라우저가 모르는 문법을 변환한다
        |
        v
  브라우저가 받는 결과물
```

- 세 가지 일의 문구는 원문 문장에서 가져왔다(끝맺음만 "…따라간다 / 합친다 / 변환한다"로 바꿨다). 맨 위·맨 아래 칸은 그 앞뒤를 보이기 위해 붙인 것이다.
- ①②③ 사이에는 화살표를 두지 않았다 — 원문이 이 셋을 한 문장 안에 ①②③으로 나란히 적었기 때문이다.

> **번들러(bundler)** — 흩어진 모듈을 의존성대로 모아 하나(또는 몇 개)의 파일로 합쳐 주는 도구.\
> 예: 수백 개 파일을 브라우저가 일일이 받지 않도록 미리 한 덩이로 만들어 두는 것.

### 2.1 browserify — "node를 브라우저에서" (2011)

최초의 대중적 번들러.\
James Halliday(substack)가 만들었고, **CommonJS `require()`를 브라우저에서 쓰게 해주는 것**이 핵심이었다.\
Node 모듈을 그대로 프론트엔드에 가져오는 길을 열었지만, 코드 분할·자산(CSS·이미지) 처리 같은 고급 기능은 없었다.

### 2.2 webpack — 모든 것을 모듈로 (2012, 2015 지배)

Tobias Koppers가 2012년 시작한 webpack은 패러다임을 바꿨다.\
**JS뿐 아니라 CSS·이미지·폰트까지 전부 "모듈"로 취급**(loader 개념)했고, 두 킬러 기능으로 표준이 됐다:

- **코드 분할(code splitting)**: 앱을 청크로 쪼개 필요할 때 로드 → 초기 로딩 단축
- **HMR(Hot Module Replacement)**: 개발 중 수정한 모듈만 페이지 새로고침 없이 교체

> **코드 분할(code splitting)** — 결과물을 청크로 쪼개, 지금 필요한 조각만 먼저 내려받게 하는 것.\
> 예: 첫 화면에 안 쓰는 설정 페이지 코드는 나중에 받는다 — 초기 로딩이 짧아진다.

> **HMR(Hot Module Replacement)** — 개발 중 고친 모듈만 갈아 끼워, 페이지를 새로고침하지 않고 반영하는 것.\
> 예: 스타일 한 줄을 고치면 페이지를 새로고침하지 않고 그 모듈만 갈아 끼워 반영된다.

React 생태계와 맞물려 2015~2016년경 webpack은 사실상 표준 번들러가 됐다.

**대가는 무엇인가** — 원문의 표현으로 **악명 높은 설정 복잡도**였다(`webpack.config.js`의 loader·plugin 미로).

```javascript
// webpack.config.js — 강력하지만 장황. 이 복잡도가 후발주자들의 빌미가 됐다
module.exports = {
  entry: './src/index.js',
  output: { filename: 'bundle.js', path: __dirname + '/dist' },
  module: {
    rules: [
      { test: /\.css$/, use: ['style-loader', 'css-loader'] },
      { test: /\.js$/, exclude: /node_modules/, use: 'babel-loader' }
    ]
  }
};
```

### 2.3 Rollup — 트리 셰이킹과 라이브러리 (2015)

Rich Harris(Svelte 제작자)가 2015년 만든 Rollup은 **ESM의 정적 구조를 정면으로 활용**했다.\
Harris가 만든 용어 **"트리 셰이킹"** — 실제로 쓰이는 코드만 번들에 포함 — 이 Rollup의 상징이다.\
출력이 깔끔하고 작아 **라이브러리 번들링의 표준**이 됐다(React, Vue 등 다수 라이브러리가 Rollup으로 배포).\
다만 초기엔 코드 분할·HMR이 없어 *앱* 번들링은 webpack의 영역이었다.\
webpack도 2016년 v2에서 ESM 기반 트리 셰이킹을 도입하며 따라갔다.

### 2.4 Parcel — 제로 설정 (2017)

Parcel은 **설정 파일이 필요 없다(zero-config)** 는 단 하나의 메시지로 webpack 피로감을 공략했다.\
진입점만 가리키면 알아서 변환·번들·HMR을 해줬다.\
멀티코어 병렬 처리와 캐싱으로 빠르기도 했다.\
webpack의 복잡도에 대한 직접적 반작용이었다.

> **제로 설정(zero-config)** — 설정 파일을 쓰지 않고 진입점만 알려 주면 되는 방식.\
> 예: Parcel은 `webpack.config.js` 같은 파일 없이 변환·번들·HMR을 알아서 해줬다.

### 2.5 esbuild & Vite — 네이티브 속도의 수렴 (2020)

진짜 분기점은 2020년이다.\
두 도구가 **번들러 게임의 규칙 자체를 바꿨다.**

**esbuild** (Evan Wallace, Figma 창업자) — JS 도구를 JS로 만들던 관행을 깨고 **Go로** 작성됐다.\
결과는 충격적이었다: 기존 JS 기반 번들러보다 **10~100배** 빠른 빌드.\
"빌드 속도는 원래 이 정도일 수 있었다"를 증명했다.

**Vite** (Evan You, Vue 제작자) — 핵심 통찰은 *"브라우저가 이미 ESM을 네이티브로 지원하는데, 개발 중에 굳이 번들할 필요가 있나?"*였다.\
Vite의 전략:

- **개발 시**: 번들하지 않는다. 소스를 ESM 그대로 브라우저에 서빙하고, 브라우저가 `import`를 따라 필요한 모듈만 요청 → **dev 서버가 200ms 이내 기동**(webpack의 2.5초 대비 ~15배). 의존성 사전 번들링만 esbuild로 처리.
- **배포 시**: Rollup으로 최적화된 번들 생성.

```text
Vite의 두 갈래 — 원문의 "개발 시 / 배포 시" 두 줄 그대로다

  개발 시 (dev) — 번들하지 않는다
    · 소스를 ESM 그대로 브라우저에 서빙
    · 브라우저가 import를 따라 필요한 모듈만 요청
        -> dev 서버 200ms 이내 기동 (webpack의 2.5초 대비 ~15배)
    · 의존성 사전 번들링만 esbuild로 처리

  배포 시 (build)
    · Rollup으로 최적화된 번들 생성
```

- 두 칸의 문구와 수치(200ms·2.5초·~15배)는 전부 원문 문장에서 그대로 가져왔다.
- "번들하지 않는다"가 개발 시의 **전제**라서 머리에 뒀다 — 아래 칸(배포 시)은 번들한다.
- 화살표는 하나뿐이고, 원문이 `→`로 이은 바로 그 자리(필요한 모듈만 요청 → 200ms 기동)다. 나머지 항목은 원문이 나열한 것이라 이어 붙이지 않았다.

```javascript
// vite.config.js — webpack.config.js와 비교하면 설정의 무게가 다르다
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],          // 대부분 이걸로 끝. dev 서버는 즉시 뜬다
});
```

2021년 Vite 2.0 이후 React·Svelte·SolidJS로 프레임워크 중립 확산했고, **2020년대 중반 "새 프로젝트의 사실상 표준 빌드 도구"로 webpack을 대체**했다.

원문의 mermaid 계보 그림을 글자 도식으로 옮기면 이렇다(노드 문구와 화살표 방향은 그대로다).

```text
번들러 계보

  browserify (2011) · require를 브라우저로
        |
        v
  webpack (2012, 2015 지배) · 모든 자산=모듈 · 코드분할·HMR
        |
        +---> Rollup (2015) · 트리 셰이킹 · 라이브러리용
        |
        +---> Parcel (2017) · 제로 설정

  Vite (2020) · dev=네이티브 ESM · build=Rollup 으로 들어오는 화살표는 셋이다
        Rollup (2015) ---> Vite
        esbuild (2020, Go) · 10~100배 빠름 ---> Vite
        Parcel (2017) ....속도/간편 압박....> Vite
```

- 노드 문구·연도·수치와 화살표의 출발점·도착점은 전부 원문 그림 그대로다.
- 원문 그림에서 esbuild는 webpack 계열 아래가 아니라 **따로 서서 Vite로만 화살표를 보낸다.** 그래서 아래쪽에 따로 적었다.
- 원문이 **종류를 밝힌 화살표는 Parcel에서 Vite로 가는 점선의 「속도/간편 압박」 하나뿐**이다. 나머지 실선에는 원문이 라벨을 붙이지 않았으므로, 여기서도 종류를 단정하지 않는다.

원문이 이 절을 맺는 문장은 이것이다.

> **수렴의 교훈**: webpack이 "전부 번들한다"로 표준을 세웠지만, 그 복잡도와 속도가 약점이 됐다. ESM 표준(브라우저 네이티브 지원)과 네이티브 언어(Go) 두 변수가 동시에 성숙하자, Vite가 *"개발 땐 번들 안 함 + 네이티브 속도"*로 둘을 흡수했다.

---

## 3. 트랜스파일: 미래의 문법을 오늘 쓰기 (Babel)

번들러가 "묶기"라면 트랜스파일러는 "**번역**"이다.\
ES2015의 새 문법(화살표 함수·`let`·클래스)을 쓰고 싶지만, 사용자의 구형 브라우저는 이해하지 못한다.\
**Babel**은 최신 JS를 구형 브라우저용 ES5로 변환해 이 간극을 메웠다.

> **트랜스파일(transpile)** — 한 언어(또는 새 문법)로 쓴 코드를, 같은 일을 하는 다른 문법의 코드로 번역하는 것.\
> 예: 화살표 함수 `(name) => ...`를 구형 브라우저가 아는 `function` 문법으로 바꿔 주는 것.

Babel은 2014년 9월, 당시 **17세 호주 고등학생** Sebastian McKenzie가 **`6to5`**("ES6를 ES5로")라는 이름으로 만들었다.\
2015년 2월 더 큰 야망(JSX·타입 제거·실험적 문법 등)을 담아 **Babel**로 개명했다.\
이름은 더글러스 애덤스의 *은하수를 여행하는 히치하이커를 위한 안내서*에 나오는 만능 번역기 "바벨 피시"에서 따왔다.

```javascript
// 입력: ES2015+ (개발자가 쓰고 싶은 코드)
const greet = (name = 'world') => `Hello, ${name}`;
class Animal { speak() { return 'sound'; } }

// Babel 출력: ES5 (구형 브라우저가 이해하는 코드)
var greet = function greet() {
  var name = arguments.length > 0 ? arguments[0] : 'world';
  return 'Hello, ' + name;
};
// class도 prototype 기반 함수로 변환된다
```

Babel의 진짜 가치는 단순 변환을 넘어선다.\
**JSX(React)·TypeScript·아직 표준이 안 된 제안(stage proposal) 문법**까지 플러그인으로 처리하는 *플랫폼*이 됐다.\
덕분에 커뮤니티는 표준 확정을 기다리지 않고 미래 문법을 실험할 수 있었다 — JS 진화 속도 자체를 끌어올린 도구다.\
(2020년대 들어 Babel의 변환 작업은 점점 더 빠른 Rust 기반 swc·oxc로 옮겨가고 있다 — §6 참조.)

---

## 4. TypeScript: 점진적 타입이 어떻게 생태계를 지배했나

### 4.1 등장 — 대규모 JS의 고통 (2012)

JS가 대규모 앱 언어로 떠밀리자 **타입의 부재**가 병목이 됐다.\
리팩터링하면 어디가 깨질지 모르고, IDE 자동완성도 약했다.\
Microsoft 내부·외부 고객 모두 같은 고통을 겪었다.

2012년 10월, **Anders Hejlsberg**(C#·Delphi·Turbo Pascal의 설계자)가 이끄는 팀이 2년의 내부 개발 끝에 **TypeScript 0.8**을 공개했다.\
원문의 표현대로 핵심 설계 결정이 운명을 갈랐다.

- **JS의 상위집합(superset)**: 모든 유효한 JS는 유효한 TS다 → 기존 코드·생태계를 버리지 않는다.
- **점진적 타입(gradual typing)**: `.js`를 `.ts`로 바꾸고 타입을 *원하는 만큼만* 붙인다. 전부 아니면 전무가 아니다.
- **컴파일 후 사라짐**: 타입은 검사용일 뿐, 트랜스파일하면 순수 JS만 남는다(런타임 비용 0).

> **상위집합(superset)** — 기존 언어의 모든 코드를 그대로 품으면서 기능을 더한 언어.\
> 예: 원문의 문장 그대로 — 모든 유효한 JS는 유효한 TS다.

> **점진적 타입(gradual typing)** — 타입을 전부 붙이거나 하나도 안 붙이거나가 아니라, 원하는 만큼만 붙여 가는 방식.\
> 예: `.js`를 `.ts`로 바꾸기만 하고 타입은 나중에 하나씩 채워 넣어도 된다.

```typescript
// 점진적: any에서 시작해 조금씩 조여간다
interface User { id: number; name: string; email?: string }  // email은 선택

function greet(user: User): string {
  return `Hi ${user.name}`;
}
greet({ id: 1, name: 'Ada' });
greet({ id: 2 });   // ❌ 컴파일 에러: name 누락 — 런타임 전에 잡힌다
```

### 4.2 경쟁과 승리

초기엔 라이벌이 있었다.\
Google의 **Closure Compiler**(JSDoc 주석 타입)와 Facebook의 **Flow**(2014)다.\
그러나 TypeScript가 이긴 이유로 원문은 네 가지를 든다 — ① 뛰어난 IDE 통합(VS Code 자체가 TS로 작성됨), ② `@types/*`(DefinitelyTyped)로 기존 JS 라이브러리에 타입을 입히는 거대 생태계, ③ Angular 2(2016)의 TS 채택, ④ 꾸준한 타입 시스템 발전(2.0의 `strictNullChecks` 등)이었다.

### 4.3 지배

2020년대 중반, TypeScript는 **JS 생태계의 사실상 공용어**가 됐다.\
전문 개발자의 약 73%가 새 프로젝트를 TS로 작성하고, 상위 1000개 npm 패키지의 약 85%가 타입 정의를 함께 배포한다.\
2025년 8월에는 GitHub 월간 기여자 수에서 **Python·JavaScript를 제치고 1위**에 올랐다.\
"타입 없는 JS"는 이제 소수파다.

원문이 이 절을 맺는 문장은 이것이다.

> **수렴의 교훈**: 타입 진영(Closure·Flow·TS)도 파편화했지만, *"기존 JS를 버리지 않는 점진적 상위집합"*이라는 설계와 압도적 도구·생태계가 TypeScript 단일 수렴을 만들었다. 호환을 깨지 않은 쪽이 이겼다.

---

## 5. 패키지 매니저: npm → yarn → pnpm

언어에 표준 라이브러리가 빈약했기에, JS는 **외부 패키지 의존도가 극단적으로 높다.**\
그 관문이 패키지 매니저다.

### 5.1 npm — 레지스트리의 탄생 (2010)

2010년 1월 12일 출시.\
Node.js의 기본 패키지 매니저이자 **세계 최대 소프트웨어 레지스트리**(현재 200만+ 패키지)가 됐다.

**대가는 무엇인가** — 원문이 적은 초기의 두 약점이다.\
**설치가 느렸고, 결정론적이지 않았다** — 같은 `package.json`이라도 설치 시점에 따라 `node_modules`가 달라질 수 있었다(lockfile 부재).

> **결정론(deterministic)** — 같은 입력이면 언제 어디서 해도 같은 결과가 나오는 성질.\
> 예: 같은 `package.json`으로 오늘 설치한 `node_modules`와 내일 설치한 것이 같다는 뜻이다.

### 5.2 yarn — 속도·결정론·lockfile (2016)

2016년 10월 Facebook이 주도해 발표.\
npm의 당대 약점을 정조준했다:

- **`yarn.lock`**: 의존성 트리를 고정해 어디서 설치하든 동일한 결과(결정론).
- **병렬 설치 + 오프라인 캐시**: 체감 속도 대폭 향상.

> **lockfile** — 실제로 설치된 의존성 트리를 통째로 적어 고정해 두는 파일.\
> 예: `yarn.lock`·`package-lock.json`이 그것이다.

yarn의 압박은 npm을 자극했고, **npm도 5.0(2017)에서 `package-lock.json`과 속도 개선으로 따라잡았다.**\
경쟁이 표준(lockfile)을 끌어올린 사례다.\
이후 yarn은 2.0(Berry, 2020)에서 **Plug'n'Play(PnP)** — `node_modules` 폴더 자체를 없애는 급진적 방향 — 로 갈라졌다.

### 5.3 pnpm — 콘텐츠 주소 저장소 (2017)

`node_modules`의 고질병은 **중복**이다.\
프로젝트마다 같은 패키지를 복사해 디스크를 잡아먹고(유명한 "node_modules는 우주에서 가장 무겁다" 농담), 평탄화(flattening) 때문에 선언하지 않은 의존성에도 접근되는 *유령 의존성(phantom dependency)* 문제가 있었다.

> **유령 의존성(phantom dependency)** — `package.json`에 적지 않았는데도 import가 되어 버리는 패키지.\
> 예: 평탄화 때문에 남의 의존성이 내 `node_modules` 꼭대기에 올라와, 적지 않은 것을 쓰게 된다.

**pnpm**(Performant npm, 2017)의 답은 **콘텐츠 주소 저장소**(content-addressable store)다.\
모든 패키지 버전을 전역 저장소(`~/.pnpm-store`)에 *단 한 번만* 실제 저장하고, 각 프로젝트의 `node_modules`는 하드 링크/심볼릭 링크로 연결한다.\
결과: **디스크 절약 + 빠른 설치 + 엄격한 의존성 격리**(유령 의존성 차단).

> **콘텐츠 주소 저장소(content-addressable store)** — 내용이 같으면 한 번만 저장해 두고, 쓰는 쪽은 링크로 가리키게 하는 저장 방식.\
> 예: 같은 패키지 버전을 프로젝트마다 복사하지 않고 `~/.pnpm-store`의 한 벌을 가리킨다.

원문의 글자 도식을 그대로 옮긴다.

```text
# 세 매니저의 node_modules 철학
npm/yarn  : 프로젝트마다 패키지를 복사 → 평탄화 → 중복·유령 의존성
yarn Berry: node_modules 폐지 → .pnp.cjs로 해석 (PnP)
pnpm      : 전역 저장소에 1회 저장 → 링크로 연결 → 중첩 구조·격리
```

- 세 줄은 원문 도식 그대로다. 가운데 줄(yarn Berry)만 `node_modules` 자체를 쓰지 않는다.

세 매니저는 지금도 공존하지만, **lockfile·`workspaces`(모노레포 지원)는 모두의 공통 기능으로 수렴**했다.\
pnpm은 모노레포·CI 효율 덕에 2020년대 들어 빠르게 점유율을 늘렸다.

---

## 6. 모노레포와 Rust 물결: 다음 수렴

### 6.1 모노레포 도구

여러 패키지를 한 저장소에서 관리하는 **모노레포**가 대규모 프론트엔드의 표준이 되면서 전용 도구가 생겼다.

> **모노레포(monorepo)** — 여러 패키지를 저장소 하나에 모아 관리하는 방식.\
> 예: 웹 앱과 그것이 쓰는 UI 라이브러리를 각각의 저장소가 아니라 한 저장소 안의 두 패키지로 둔다.

| 도구 | 등장 | 특징 |
|------|------|------|
| **Lerna** | 2015 | 최초의 대중적 JS 모노레포 도구. 워크스페이스·일괄 배포 개념 정립. 2022년 Nx 팀이 인수 |
| **Nx** | 2019~ | 빌드 시스템 + 계산 캐싱 + 의존성 그래프. 코어를 TS → **Rust로 이전 중** |
| **Turborepo** | 2021 (Vercel 인수) | Rust 기반. 증분 빌드·원격 캐싱. 단순 설정으로 인기 |

핵심 가치는 공통이다: **변경된 부분만 다시 빌드·테스트하는 증분 캐싱**.\
프로젝트가 커질수록 "전부 다시 빌드"는 불가능하기 때문이다.

> **증분 캐싱(incremental caching)** — 바뀐 부분만 다시 빌드·테스트하고 나머지는 지난 결과를 재사용하는 것.\
> 예: 패키지가 여럿일 때 이번에 바뀐 패키지만 다시 빌드·테스트하고, 나머지는 지난 결과를 재사용한다.

### 6.2 Rust가 도구체인을 먹는다 (2020~)

esbuild(Go)가 *"빌드는 100배 빠를 수 있다"*를 증명하자, JS 도구를 네이티브 언어 — 특히 **Rust** — 로 다시 쓰는 거대한 흐름이 시작됐다.\
JS 도구를 JS로 만들던 자기참조 시대의 종언이다.

| 도구 | 대체 대상 | 비고 |
|------|----------|------|
| **swc** (Speedy Web Compiler, 2017~) | Babel·tsc(트랜스파일) | 강동윤이 시작. Babel 대비 단일 코어 ~20배. Next.js·Parcel·Deno가 채택 |
| **Turbopack** (2022, Vercel) | webpack | "webpack의 후계자". Next.js 16(2025)부터 기본 번들러 |
| **Rspack** (2023, ByteDance) | webpack | webpack 호환 API + Rust 속도 |
| **Biome** (2023) | ESLint + Prettier | Sebastian McKenzie의 **Rome**(2020)이 2023년 startup 폐업으로 중단되자 포크. 린트+포맷 통합 |
| **Oxc / Rolldown** | ESLint / Rollup | Vite 팀이 추진. Vite의 미래 번들 코어(Rolldown)는 Rust로 작성된 Rollup 대체 |

흥미로운 매듭: Babel을 만든 Sebastian McKenzie는 이후 JS 도구의 파편화 자체를 풀려고 **Rome**(통합 도구체인)을 시도했고, 그 정신은 Rust로 다시 쓰인 **Biome**으로 이어졌다.\
도구를 만든 사람이 도구의 난립을 보고 통합을 시도한 셈이다.

여기에 **Bun**(Jarred Sumner, 2022 — Zig로 작성)은 런타임·번들러·패키지 매니저·테스트 러너를 *하나의 바이너리*로 묶어, 파편화 자체를 "올인원"으로 흡수하려는 또 다른 수렴 시도다.

원문의 mermaid 그림을 글자 도식으로 옮기면 이렇다(노드 문구와 화살표 라벨은 그대로다).

```text
1세대: JS로 만든 JS 도구 (느림)    ....대체....>    2세대: 네이티브 언어로 재작성 (빠름)

  Babel (트랜스파일)             ....>  swc / oxc (Rust)
  webpack (번들)                 ....>  Turbopack / Rspack (Rust)
  Rollup (번들)                  ....>  Rolldown (Rust)
  ESLint + Prettier (린트/포맷)  ....>  Biome (Rust)

  2세대에는 위 네 화살표를 받지 않는 칸이 둘 더 있다
    esbuild (Go)
    Bun (Zig) — 올인원

  esbuild (Go) --"속도 증명, 흐름 촉발"--> 2세대 전체
```

- 두 묶음의 이름(1세대·2세대)과 그 안의 칸 문구는 원문 그림의 subgraph 제목·노드 그대로다.
- 점선 네 개에 붙은 라벨은 원문 그대로 「대체」이고, 맨 아랫줄 실선의 라벨도 원문 그대로 「속도 증명, 흐름 촉발」이다.
- esbuild에서 나가는 화살표는 2세대 묶음 **전체**를 향한다 — 원문 그림에서도 개별 도구가 아니라 묶음을 가리킨다.

원문이 이 절을 맺는 문장은 이것이다.

> **다음 수렴의 방향**: ① 언어는 Rust/Go(네이티브 속도), ② 형태는 통합 도구체인(Biome·Bun·Vite+Rolldown처럼 여러 역할을 하나로). 1세대의 파편화(도구마다 별개 + 전부 JS라 느림)를 *네이티브 언어 + 통합*이라는 두 축으로 흡수하는 중이다.

---

## 7. 정리: 파편화와 수렴의 반복

*(골격상 이 절이 원문의 「정리·마치며」 슬롯 — 「왜 그렇게 갔나 — 남은 선택지와 트레이드오프」다. 원문에 별도의 「영향과 의의」 절은 없고, 아래 네 줄이 「남긴 것 — 오늘 우리가 쓰는 것」을 겸한다.)*

원문의 정리 표를 그대로 옮긴다.

| 시기 | 지배적 상태 | 추동력 |
|------|-----------|--------|
| ~2009 | 전역 변수 + `<script>` | 언어가 작은 용도로 출발 |
| 2009~2015 | CommonJS vs AMD vs UMD, npm, browserify→webpack | Node·SPA 부상, 표준 공백 |
| 2015 | **ES2015**: ESM·클래스·`let` 표준화 | 언어 명세가 따라잡음 |
| 2015~2020 | webpack + Babel + TypeScript 대세, yarn/pnpm | 정적 분석·트리셰이킹·점진적 타입 |
| 2020~ | **Vite + esbuild**, TypeScript 지배, Rust 도구 물결 | 네이티브 속도·ESM 네이티브 지원 |

아래 네 줄은 원문의 마지막 문단에 적힌 것이다.

- JS 생태계가 복잡해 보이는 건 무능해서가 아니라, **언어 표준이 비어 있던 시기에 커뮤니티가 빈자리를 경쟁적으로 메웠기 때문**이다.
- 모듈(ESM)·번들러(Vite)·타입(TypeScript)은 각각 표준 또는 압도적 도구로 수렴했고, 지금은 *Rust 기반 + 통합 도구체인*이라는 다음 수렴이 진행 중이다.
- 파편화는 혼란이지만 동시에 실험이었고, 수렴은 그 실험에서 최선을 골라낸 결과다.
- JS는 이 진자 운동을 30년째 반복하며 진화해 왔다.

## 용어 풀이

- **ECMAScript / ES3·ES5·ES2015(ES6)** — JavaScript의 언어 명세. 1999년 ES3 이후 2009년 ES5까지 10년간 정체됐고, 2015년 ES2015에서 모듈·클래스·`let`/`const`가 표준화됐다.
- **파편화(divergence) / 수렴(convergence)** — 같은 자리에 경쟁 답이 여럿 생기는 것 / 다시 하나로 모이는 것.
- **모듈(module)** — 코드를 파일 단위로 나누고 공개할 것과 감출 것을 구분하는 장치.
- **전역 오염(namespace pollution)** — 모두가 같은 `window`를 써서 같은 이름이 서로를 덮어쓰는 상태.
- **IIFE(즉시 실행 함수 표현식)** — 만들자마자 실행해 안의 변수를 바깥에서 못 보게 가두는 함수.
- **CommonJS** — `require()` / `module.exports`를 쓰는 동기 모듈 규약. 2009년 Node.js가 채택했다.
- **AMD(Asynchronous Module Definition) / RequireJS** — `define()`으로 의존성을 비동기 로드하는 브라우저용 규약(2011) / 그것을 대중화한 구현.
- **UMD(Universal Module Definition)** — CommonJS·AMD·전역을 런타임에 감지해 어디서든 동작하게 감싼 타협물.
- **ESM** — ES2015가 명세한 언어 표준 모듈. `import` / `export`, 그리고 **정적**이다.
- **정적(static) / 트리 셰이킹(tree-shaking)** — 의존성이 실행 전에 정해져 있다는 성질 / 그 덕에 쓰이지 않는 코드를 털어 내는 것.
- **번들러(bundler)** — 의존성 그래프를 따라 모듈을 합치고 브라우저가 모르는 문법을 변환하는 도구.
- **코드 분할(code splitting) / HMR(Hot Module Replacement)** — 청크로 쪼개 필요할 때 로드 / 고친 모듈만 새로고침 없이 교체.
- **제로 설정(zero-config)** — 설정 파일 없이 진입점만 알려 주면 되는 방식(Parcel).
- **트랜스파일(transpile)** — 새 문법의 코드를 같은 일을 하는 다른 문법으로 번역하는 것(Babel: ES2015+ → ES5).
- **상위집합(superset) / 점진적 타입(gradual typing)** — 기존 언어의 모든 코드를 품는 언어 / 타입을 원하는 만큼만 붙여 가는 방식.
- **lockfile / 결정론(deterministic)** — 설치된 의존성 트리를 고정해 적어 둔 파일 / 같은 입력이면 같은 결과가 나오는 성질.
- **평탄화(flattening) / 유령 의존성(phantom dependency)** — `node_modules`를 납작하게 펴는 것 / 그 때문에 선언하지 않은 패키지가 import되는 문제.
- **콘텐츠 주소 저장소(content-addressable store)** — 같은 내용은 한 번만 저장하고 링크로 가리키는 방식(pnpm).
- **Plug'n'Play(PnP)** — `node_modules` 폴더 자체를 없애고 `.pnp.cjs`로 해석하는 yarn 2.0(Berry, 2020)의 방향.
- **모노레포(monorepo) / 증분 캐싱** — 여러 패키지를 한 저장소에서 관리하는 방식 / 바뀐 부분만 다시 빌드·테스트하는 것.
- **네이티브 언어 재작성** — JS로 만들던 JS 도구를 Go·Rust·Zig로 다시 쓰는 흐름(esbuild·swc·Turbopack·Rspack·Biome·Rolldown·Bun).

## 참고 출처

- [History of JavaScript Modules — Script Tags to ESM (esmodules.com)](https://esmodules.com/history/)
- [Navigating the module maze: history of JavaScript module systems (Codilime)](https://codilime.com/blog/history-of-javascript-module-systems/)
- [JavaScript Module Systems Showdown: CommonJS vs AMD vs ES2015 (Auth0)](https://auth0.com/blog/javascript-module-systems-showdown/)
- [What the heck are CJS, AMD, UMD, and ESM? (DEV)](https://dev.to/iggredible/what-the-heck-are-cjs-amd-umd-and-esm-ikm)
- [Webpack and Rollup: the same but different — Rich Harris (Medium)](https://medium.com/webpack/webpack-and-rollup-the-same-but-different-a41ad427058c)
- [Tree-shaking versus dead code elimination — Rich Harris (Medium)](https://medium.com/@Rich_Harris/tree-shaking-versus-dead-code-elimination-d3765df85c80)
- [Tree Shaking (webpack 공식 문서)](https://webpack.js.org/guides/tree-shaking/)
- [Comparing JavaScript Bundlers: Rollup vs Webpack vs Parcel (Kinsta)](https://kinsta.com/blog/rollup-vs-webpack-vs-parcel/)
- [Announcing Vite 2.0 — Evan You (DEV)](https://dev.to/yyx990803/announcing-vite-2-0-2f0a)
- [Vite's Core Magic: How esbuild and Native ESM Reinvent Frontend (Leapcell)](https://leapcell.io/blog/vite-s-core-magic-how-esbuild-and-native-esm-reinvent-frontend-development)
- [Babel (transcompiler) — 역사 (Grokipedia)](https://grokipedia.com/page/Babel_(transcompiler))
- [6to5 JavaScript Transpiler Changes Name to Babel (InfoQ)](https://www.infoq.com/news/2015/02/babel-new-name-for-6to5/)
- [TypeScript (Wikipedia)](https://en.wikipedia.org/wiki/TypeScript)
- [Anders Hejlsberg (Wikipedia)](https://en.wikipedia.org/wiki/Anders_Hejlsberg)
- [An abbreviated history of JavaScript package managers (JS in Plain English)](https://medium.com/javascript-in-plain-english/an-abbreviated-history-of-javascript-package-managers-f9797be7cf0e)
- [JavaScript package managers compared: npm, Yarn, or pnpm? (LogRocket)](https://blog.logrocket.com/javascript-package-managers-compared/)
- [Rust Is Eating JavaScript — Lee Robinson](https://leerob.com/rust)
- [The Performance Revolution in JavaScript Tooling (AppSignal)](https://blog.appsignal.com/2025/12/03/the-performance-revolution-in-javascript-tooling.html)
- [Introducing Rome — Sebastian McKenzie (rome.tools)](https://rome.tools/blog/2020/08/08/introducing-rome/)
- [swc — Rust-based platform for the Web](https://swc.rs/)
- [Turborepo, Nx, and Lerna: monorepo tooling (DEV)](https://dev.to/dataformathub/turborepo-nx-and-lerna-the-truth-about-monorepo-tooling-in-2026-71)
- [State of JavaScript 2026 (LangPop)](https://langpop.com/blog/state-of-javascript-2026)
