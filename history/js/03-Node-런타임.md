# Node.js와 JS 런타임 (2009~)

> 원본: `~/project/js-history/03-Node-런타임.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-19).\
> 연도·인명·표준번호·코드·표는 원문 그대로다.\
> ASCII 도식 5개와 「한눈에」의 식당 비유(대응표 포함), 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 브라우저 안에 갇혀 있던 JavaScript를 서버로 끌어낸 사건. 2009년 Node.js가 V8 엔진과 논블로킹 이벤트 루프를 결합하면서 "프론트엔드 언어"였던 JS는 백엔드·CLI·빌드 도구를 아우르는 범용 런타임 언어가 되었다. 이 장은 Node의 탄생부터 npm 생태계 폭발, io.js 분기와 재단화, 그리고 Deno·Bun·엣지 런타임이라는 차세대 경쟁자들까지의 흐름을 "언제·왜"의 관점에서 정리한다.

이 편의 주 비유는 **식당** 하나이고, 그 비유가 설명하는 것은 Node의 이벤트 루프 한 대목이다.\
나머지 절(npm·거버넌스·경쟁 런타임·엣지)은 **본문 흐름에는** 비유를 쓰지 않고 원문 서술을 그대로 따라간다.\
(용어 블록 안에는 「샌드박스 = 울타리」처럼 그 자리에서만 쓰는 짧은 풀이가 있다.)

| 비유 | 실체 |
|------|------|
| 손님 한 명마다 전담 웨이터를 붙이는 식당 | 들어오는 연결마다 스레드를 하나씩 할당하는 스레드-퍼-커넥션 |
| 웨이터가 주방 앞에 서서 음식이 나오기를 기다린다 | I/O가 끝날 때까지 스레드가 블로킹 상태로 대기한다 |
| 손님이 1만 명이면 웨이터도 1만 명이 든다 | 동시 접속 1만 개를 어떻게 감당할 것인가 — C10K 문제 |
| 웨이터 한 명이 주문만 받아 주방에 넘기고 다음 테이블로 간다 | 단일 스레드 + 이벤트 루프 + 논블로킹 I/O |
| 음식이 나오면 그때 그 테이블로 간다 | I/O 완료 이벤트가 큐에 들어오면 루프가 콜백을 실행한다 |

```text
식당 한 곳으로 옮겨 보면

손님마다 전담 웨이터                 웨이터 한 명
+--------------------------------+   +--------------------------------+
| 손님 1 - 웨이터 1              |   | 웨이터가 주문만 받아           |
| 손님 2 - 웨이터 2              |   | 주방에 넘기고 다음 테이블로    |
| 손님 3 - 웨이터 3              |   |                                |
|                                |   |                                |
| 각 웨이터는 음식이 나올 때까지 |   | 음식이 나오면 그때             |
| 주방 앞에 서서 기다린다        |   | 그 테이블로 간다               |
+--------------------------------+   +--------------------------------+
  손님이 1만이면 웨이터도 1만          웨이터는 한 명이면 된다
```

- 왼쪽이 원문이 적은 2000년대 후반의 모습이고, 오른쪽이 Ryan Dahl이 가야 한다고 본 방향이다.
- 두 칸의 대립축은 원문의 대립축 그대로다 — **연결마다 스레드를 붙이느냐, 단일 스레드가 이벤트 루프를 도느냐**.
- 손님 셋과 웨이터 셋은 그림을 위해 붙인 수이고, 원문에 있는 값은 아니다. 원문에 있는 값은 "동시 접속 1만 개"다.

## 한눈에 보는 타임라인

| 연도 | 사건 | 의미 |
|------|------|------|
| 2009 | Ryan Dahl, JSConf EU에서 Node.js 발표 | V8 + 논블로킹 I/O로 서버에 JS를 올림 |
| 2010 | npm 첫 릴리스 (Isaac Schlueter) | 패키지 생태계의 시작 |
| 2014.12 | io.js 분기 | 거버넌스 갈등으로 포크 |
| 2015.09 | Node.js 4.0 — io.js 재통합 | Node.js Foundation 출범, 코드 합류 |
| 2018 | Cloudflare Workers 정식 출시 | V8 isolate 기반 엣지 런타임 |
| 2019 | OpenJS Foundation 출범 | JS Foundation + Node.js Foundation 합병 |
| 2020.03 | GitHub(Microsoft)가 npm 인수 | 레지스트리가 GitHub 산하로 |
| 2020.05 | Deno 1.0 (Ryan Dahl) | 보안·TS 내장으로 Node를 재설계 |
| 2022.07 | Bun 0.1 (Jarred Sumner) | JavaScriptCore + Zig로 속도 추구 |
| 2022.09 | Cloudflare workerd 오픈소스 + WinterCG 출범 | 엣지 런타임 표준화 |

---

## 1. Node.js의 탄생 (2009) — 왜 서버에서 JavaScript인가

### 시대적 배경

2000년대 후반의 서버 프로그래밍은 대부분 **스레드-퍼-커넥션(thread-per-connection)** 모델이었다.\
Apache 같은 전통적 웹 서버는 들어오는 연결마다 스레드(또는 프로세스)를 하나씩 할당했고, 각 스레드는 디스크 읽기나 DB 쿼리 같은 I/O가 끝날 때까지 **블로킹(blocking)** 상태로 대기했다.\
동시 접속이 수천 개로 늘어나면 스레드 컨텍스트 스위칭과 메모리 비용이 폭발하는, 이른바 **C10K 문제**(동시 접속 1만 개를 어떻게 감당할 것인가)가 화두였다.

> **스레드-퍼-커넥션(thread-per-connection)** — 들어오는 연결마다 스레드(또는 프로세스)를 하나씩 할당하는 방식(원문의 서술 그대로).\
> 예: Apache 같은 전통적 웹 서버가 이 방식이었다.

> **블로킹(blocking)** — 결과가 나올 때까지 그 자리에서 멈춰 기다리는 것.\
> 예: 아래 코드의 `fs.readFileSync('big.log')`는 파일을 다 읽을 때까지 스레드가 멈춘다.

> **C10K 문제** — 동시 접속 1만 개를 어떻게 감당할 것인가(원문의 풀이 그대로).\
> 예: 연결마다 스레드를 붙이면 동시 접속이 수천 개로 늘어날 때 컨텍스트 스위칭과 메모리 비용이 폭발한다.

Ryan Dahl은 여기서 "I/O를 다루는 방식 자체가 틀렸다"고 봤다.\
대부분의 시간을 스레드가 그저 응답을 기다리며 노는 데 쓴다면, 차라리 **단일 스레드 + 이벤트 루프 + 논블로킹 I/O**로 가야 한다는 것이었다.

```text
서버가 연결을 받는 두 방식

스레드-퍼-커넥션                     단일 스레드 + 이벤트 루프
+----------------------------------+ +----------------------------------+
| 연결마다 스레드를 하나씩 할당    | | 단일 스레드가 콜백 큐를 돈다     |
| I/O가 끝날 때까지 블로킹 대기    | | I/O 요청은 운영체제에 떠넘긴다   |
+----------------------------------+ +----------------------------------+
  동시 접속이 수천 개로 늘어나면      자신은 즉시 다음 일을 처리하고,
  컨텍스트 스위칭과 메모리 비용이     I/O가 끝나면 그 완료 이벤트가
  폭발한다                            큐에 들어와 콜백이 실행된다
```

- 두 칸의 문구는 모두 원문 문장에서 가져온 것이다(폭 때문에 괄호 안 보충과 "빙빙"만 줄였다).
- 왼쪽 아래가 원문이 말한 C10K 문제의 내용이고, 오른쪽 아래가 원문이 적은 이벤트 루프의 동작이다.

그가 본 결정적 도구가 두 가지 있었다.

1. **Google V8** — Chrome에 막 탑재된, BSD 라이선스로 오픈소스화된 JIT 컴파일 JS 엔진. 당시 기준 압도적으로 빨랐다.
2. **JavaScript라는 언어 자체** — JS는 태생적으로 스레드가 없고, 콜백 기반의 이벤트 모델(브라우저의 `onclick`, `setTimeout`)에 이미 익숙한 언어였다. 즉 비동기 이벤트 프로그래밍에 "오염되지 않은" 깨끗한 언어였다.

> **JIT 컴파일** — 소스를 미리 전부 번역해 두는 대신, 실행하는 시점에 기계어로 번역해 돌리는 방식.\
> 예: 원문은 V8을 "JIT 컴파일 JS 엔진"이라 부르며, 당시 기준 압도적으로 빨랐다고 적는다.

> **왜 하필 JS였나** — 단지 빠른 엔진(V8)이 있어서만은 아니었다. 자바나 C로 논블로킹 서버를 짜려면 기존의 블로킹 라이브러리 관성과 싸워야 했지만, JS에는 블로킹 I/O 표준 라이브러리라는 "과거"가 아예 없었다. 게다가 프론트엔드 개발자가 이미 수백만 명이었으니, 같은 언어로 서버까지 짤 수 있다는 점(풀스택 단일 언어)은 거대한 채택 동력이었다.

### 핵심 아이디어: 이벤트 루프와 논블로킹 I/O

Node의 심장은 **이벤트 루프**다.\
단일 스레드가 콜백 큐를 빙빙 돌면서, I/O 요청은 운영체제(또는 백그라운드 스레드 풀)에 떠넘기고 자신은 즉시 다음 일을 처리한다.\
I/O가 끝나면 그 완료 이벤트가 큐에 들어오고, 루프가 등록된 콜백을 실행한다.\
이 비동기 I/O 추상화를 담당하는 C 라이브러리가 **libuv**다(초기엔 libev/libeio 기반, 이후 크로스플랫폼 libuv로 통합).

```text
논블로킹 I/O — 원문이 적은 순서 그대로

  +--> 단일 스레드가 콜백 큐를 빙빙 돈다
  |            |
  |            v
  |    I/O 요청은 운영체제(또는 백그라운드 스레드 풀)에 떠넘긴다
  |            |
  |            v
  |    자신은 즉시 다음 일을 처리한다
  |            |
  |            v
  |    I/O가 끝나면 그 완료 이벤트가 큐에 들어온다
  |            |
  |            v
  |    루프가 등록된 콜백을 실행한다
  |            |
  +------------+
```

- 다섯 칸은 원문이 이 절 첫 문단에 쓴 순서와 문구 그대로다.
- 마지막 칸에서 첫 칸으로 되돌아가는 왼쪽 화살표가 원문의 "**빙빙 돌면서**"다.\
  다섯 단계는 한 번 지나가고 끝나는 절차가 아니라, 계속 도는 **루프**다.
- 원문은 이 다섯 단계보다 더 안쪽의 세부는 다루지 않는다 — 여기서도 더 그리지 않는다.

> **이벤트 루프(event loop)** — 할 일을 담아 둔 큐를 계속 돌면서 준비된 것부터 실행하는 구조.\
> 예: I/O를 떠넘긴 뒤 즉시 다음 일을 하다가, 완료 이벤트가 큐에 들어오면 그 콜백을 실행한다.

> **논블로킹(non-blocking) I/O** — 결과를 기다리며 멈추지 않고, 일을 맡겨 둔 채 다음 줄로 넘어가는 입출력.\
> 예: 아래 코드의 `fs.readFile('big.log', (err, data) => { ... })`는 읽기를 맡기고 바로 다음 줄을 실행한다.

> **libuv** — 이 비동기 I/O 추상화를 담당하는 C 라이브러리(원문의 정의 그대로).\
> 예: 초기엔 libev/libeio 기반이었고, 이후 크로스플랫폼 libuv로 통합됐다.

```js
// 블로킹 방식(가상) — 파일을 다 읽을 때까지 스레드가 멈춘다
const data = fs.readFileSync('big.log');   // ⛔ 여기서 대기
console.log(data.length);
console.log('이 줄은 파일을 다 읽은 뒤에야 출력된다');

// Node의 논블로킹 방식 — 읽기를 OS에 맡기고 즉시 다음 줄로
fs.readFile('big.log', (err, data) => {     // ✅ 완료되면 콜백 호출
  if (err) throw err;
  console.log(data.length);
});
console.log('이 줄이 먼저 출력된다 — 메인 스레드는 멈추지 않는다');
```

발표 당시 Dahl이 보여준 상징적 예제가 **단 6줄짜리 HTTP 서버**였다.\
"프레임워크 없이, 한 파일로, 수천 동시 접속을 받는 서버"라는 충격이 컸다.

```js
// 2009년 발표의 상징 — http 모듈만으로 동작하는 서버
const http = require('http');

http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Hello World\n');
}).listen(8080);

console.log('http://localhost:8080 에서 서버 실행 중');
```

여기서 `require`는 Node가 채택한 **CommonJS** 모듈 시스템이다.\
브라우저 JS에는 모듈 개념이 없던 시절, Node는 파일 단위로 코드를 나누고 `module.exports` / `require`로 의존성을 연결하는 규약을 표준으로 삼았다(후일 ES Modules `import`/`export`와 공존하게 된다).

> **CommonJS** — 파일 단위로 코드를 나누고 `module.exports` / `require`로 의존성을 연결하는 규약(원문의 정의 그대로).\
> 예: 위 코드의 `const http = require('http');`가 그 방식으로 모듈을 가져오는 줄이다.

### 영향

Node는 실시간성(채팅·푸시·스트리밍)과 높은 동시성이 핵심인 I/O 바운드 서비스에서 빛났다.\
Netflix·LinkedIn·PayPal·Uber 등이 자바/루비 백엔드의 일부를 Node로 옮기며 응답 지연과 운영 비용을 줄였다는 사례가 줄을 이었다.

> **I/O 바운드 / CPU 바운드** — 걸리는 시간의 대부분이 입출력 대기인 일 / 계산 그 자체인 일.\
> 예: 채팅·푸시·스트리밍이 앞쪽이고, 이미지 처리·암호화·대규모 계산이 뒤쪽이다(원문이 든 예 그대로).

**대가는 무엇인가** — 원문이 손실로 적은 문장은 이것이다.

> 반대로 **CPU 바운드 작업**(이미지 처리·암호화·대규모 계산)에는 단일 스레드 모델이 약점이었고, 이는 후일 `worker_threads`(2018, Node 10.5+)로 보완된다.

---

## 2. npm과 생태계 폭발 (2010~)

### 패키지 매니저가 없으면 런타임은 외롭다

런타임만으로는 부족하다.\
코드를 공유·재사용할 **표준 배포 채널**이 있어야 생태계가 자란다.\
2010년 1월, Isaac Schlueter가 **npm**(Node Package Manager)을 내놓았다.\
`package.json`에 의존성을 선언하고 `npm install`로 내려받는 단순한 모델이었지만, 그 단순함이 폭발적 성장을 낳았다.

> **패키지 매니저(package manager)** — 남이 만든 코드 묶음을 받아다 내 프로젝트에 넣고 버전을 관리해 주는 도구.\
> 예: `package.json`에 의존성을 선언하고 `npm install`로 내려받는다(아래 코드).

```jsonc
// package.json — 프로젝트의 의존성·스크립트를 선언하는 매니페스트
{
  "name": "my-app",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.2"     // ^ = 호환되는 마이너/패치 업데이트 허용 (SemVer)
  },
  "scripts": {
    "start": "node server.js"
  }
}
```

```bash
npm install express     # 의존성을 node_modules/에 설치하고 package.json에 기록
npm start               # scripts.start 실행
```

npm은 **SemVer**(유의적 버전, MAJOR.MINOR.PATCH)를 의존성 표기의 기반으로 삼아, "어디까지 자동 업데이트를 허용할지"를 기호(`^`, `~`)로 표현하게 했다.\
또한 의존성의 의존성을 **중첩된 `node_modules` 트리**로 각자 격리해, 같은 패키지의 서로 다른 버전이 한 프로젝트에 공존할 수 있게 했다(초기엔 트리, 후일 평탄화(flat)로 진화).

> **SemVer(유의적 버전)** — 버전을 `MAJOR.MINOR.PATCH` 세 자리로 적어 변화의 크기를 드러내는 규칙.\
> 예: 위 `package.json`의 `"express": "^4.18.2"`에서 `^`는 호환되는 마이너/패치 업데이트를 허용한다는 뜻이다(원문 주석).

```text
중첩된 node_modules 트리 — 같은 패키지의 다른 버전이 공존한다

my-app/
  node_modules/
    A/                        A 가 B 의 1 버전을 쓴다
      node_modules/
        B (1 버전)
    C/                        C 가 B 의 2 버전을 쓴다
      node_modules/
        B (2 버전)
```

- 각자 자기 `node_modules` 안에 자기가 쓸 버전을 따로 갖는다 — 이것이 원문이 말한 "각자 격리"다.
- 패키지 이름 A·B·C와 버전 1·2는 그림을 위해 붙인 것이고, 원문에 있는 값은 아니다.
- 원문은 이 모양이 "초기엔 트리, 후일 평탄화(flat)로 진화"했다고 적는다.

### 세계 최대 레지스트리

npm 레지스트리는 이내 **세계에서 가장 큰 소프트웨어 레지스트리**가 되었다.\
패키지 수는 수십만 → 100만(2019년 돌파) → 그 이상으로 불었고, "작은 모듈을 많이 조합한다"는 Node 문화(예: 좌패딩 한 줄짜리 `left-pad`)가 양날의 검으로 작용했다.

**대가는 무엇인가** — 원문이 손실로 적은 문장은 이것이다.

> 재사용성은 극대화됐지만, **의존성 트리의 비대화와 공급망 보안**(2016년 left-pad 삭제 사태로 수많은 빌드가 깨진 사건, 악성 패키지 주입)이라는 숙제도 함께 커졌다.

> **공급망 보안(supply chain security)** — 내가 쓰는 남의 코드, 그리고 그 코드가 다시 쓰는 코드까지를 통째로 신뢰해야 하는 데서 오는 위험을 다루는 일.\
> 예: 원문이 든 대로 2016년 `left-pad`가 삭제되자 수많은 빌드가 깨졌고, 악성 패키지 주입 문제도 함께 커졌다.

경쟁·보완 도구도 등장했다.\
**Yarn**(2016, Facebook — 결정론적 lockfile·병렬 설치), **pnpm**(콘텐츠 주소화 저장소로 디스크·중복 절감)이 npm의 약점을 공략하며 표준을 끌어올렸다.\
npm 자신도 `package-lock.json`(lockfile)과 `npm audit`(취약점 점검)으로 응답했다.

> **lockfile** — 이번에 실제로 설치된 버전을 그대로 적어 두어, 다음에도 같은 것이 깔리게 하는 파일.\
> 예: 원문이 든 대로 Yarn의 "결정론적 lockfile"이 그것이고, npm도 `package-lock.json`으로 응답했다.

### 소유권의 이동

2014년 npm, Inc.가 설립되어 레지스트리를 운영하다가, **2020년 3월 GitHub(즉 Microsoft)가 npm을 인수**했다.\
자바스크립트 생태계의 중심 인프라가 GitHub 산하로 들어간 것이다.\
GitHub은 공개 레지스트리를 무료·개방으로 유지하겠다고 약속했고, 이로써 "코드 호스팅(GitHub) + 패키지 배포(npm)"가 한 지붕 아래 묶였다.

> **레지스트리(registry)** — 패키지를 올려 두고 내려받는 중앙 보관소.\
> 예: npm 레지스트리가 세계에서 가장 큰 소프트웨어 레지스트리가 됐고, 2020년 3월 GitHub가 그것을 인수했다.

---

## 3. io.js 분기와 재통합, 그리고 재단화 (2014~2019)

### 왜 갈라섰나 — 거버넌스 갈등

Node의 초기 모회사는 **Joyent**였다.\
그러나 2014년경, 핵심 기여자들은 Joyent 단일 기업이 프로젝트 방향을 좌우하고 릴리스가 정체된 데 불만이 컸다.\
"오픈소스 프로젝트는 특정 회사가 아니라 **공식 기술 위원회**(TSC)가 운영해야 한다"는 것이 명분이었다.\
2014년 12월, 이들은 코드를 포크해 **io.js**를 출범시켰다.

> **포크(fork)** — 남의 저장소를 통째로 복사해 거기서부터 따로 개발해 나가는 것.\
> 예: 원문이 적은 대로 2014년 12월 핵심 기여자들이 코드를 포크해 io.js를 출범시켰다.

> **거버넌스(governance)** — 그 프로젝트의 방향과 릴리스를 누가 어떤 절차로 정하는가.\
> 예: 단일 기업(Joyent)이 정하느냐, 공식 기술 위원회(TSC)가 정하느냐가 이 갈등의 쟁점이었다.

io.js는 단순한 반항이 아니라 **빠른 V8 업데이트와 개방형 거버넌스**라는 실리를 보여줬다.\
최신 V8을 따라잡아 ES6(ES2015) 기능을 먼저 지원했고, 투명한 의사결정으로 기여자를 끌어모았다.\
본가 Node가 정체된 사이, io.js가 사실상 더 활발한 개발 라인이 되었다.

### 어떻게 다시 합쳤나

분열은 생태계 모두에게 손해였다.\
양측은 협상 끝에 **중립적 재단** 아래 합치기로 했다.\
2015년 **Node.js Foundation**(Linux Foundation 산하)이 출범했고, 2015년 9월 **Node.js 4.0**이 릴리스되며 io.js의 코드와 빠른 V8, 그리고 Node의 브랜드·생태계가 하나로 합쳐졌다.

```text
분기와 재통합 — 원문이 적은 연도 그대로

2014.12  핵심 기여자들이 코드를 포크해 io.js 를 출범시켰다

  Node (Joyent 아래)              io.js
  릴리스가 정체됐다               최신 V8 을 따라잡아 3.x 까지 갔다
         |                              |
         +--------------+---------------+
                        |
                        v
2015     Node.js Foundation (Linux Foundation 산하) 출범
2015.09  Node.js 4.0 릴리스
         io.js 의 코드와 빠른 V8, 그리고 Node 의 브랜드·생태계가
         하나로 합쳐졌다
```

- 두 줄기가 아래에서 하나로 모이는 것이 원문이 적은 재통합이다.
- 각 줄기에 붙은 설명은 원문 문장에서 그대로 가져왔다 — 왼쪽은 "릴리스가 정체된 데 불만", 오른쪽은 "최신 V8을 따라잡아"와 "io.js가 이미 3.x까지 갔기 때문"이다.
- 원문이 이 재통합의 **동기**로 적은 문장은 그림 밖 본문에 그대로 있다 — "분열은 생태계 모두에게 손해였다."\
  손실 어휘이긴 하지만 이 절(어떻게 다시 합쳤나)에서 그 문장은 합친 이유이지 합쳐서 치른 대가가 아니므로, 「대가는 무엇인가」 표제를 붙이지 않았다.

> **버전 번호가 1·2·3을 건너뛴 이유** — io.js가 이미 3.x까지 갔기 때문에, 통합 버전은 두 라인을 모두 추월하는 의미로 **4.0**에서 시작했다. 이때 도입된 것이 **LTS(Long-Term Support) 릴리스 라인**이다. 짝수 메이저 버전을 LTS로 지정해 장기 보안 지원을 보장하고, 홀수 버전은 최신 기능 실험 라인으로 운용하는 모델이 자리 잡았다.

> **LTS(Long-Term Support)** — 그 버전을 오래 두고 보안 지원을 보장하는 릴리스 라인.\
> 예: 짝수 메이저 버전을 LTS로 지정하고, 홀수 버전은 최신 기능 실험 라인으로 쓴다(원문).

이 합병의 핵심 교훈은 명확하다 — **런타임의 성패는 기술만큼이나 거버넌스에 달려 있다.**\
단일 기업 종속을 끊고 중립 재단 + 위원회 모델로 가면서 Node는 비로소 안정적으로 성장할 토대를 얻었다.

### OpenJS Foundation (2019)

2019년, **Node.js Foundation과 JS Foundation이 합병해 OpenJS Foundation**이 되었다.\
Node뿐 아니라 jQuery·Webpack·Electron·ESLint 등 광범위한 JS 프로젝트를 한 재단이 품으면서, 자바스크립트 생태계 전반의 중립적 거버넌스 허브가 마련됐다.

---

## 4. 경쟁 런타임 — "Node의 후회"에서 출발하다

Node가 표준이 된 뒤 10년, 두 개의 도전자가 등장한다.\
흥미롭게도 첫 도전자는 **Node를 만든 바로 그 사람**이었다.

### 4-1. Deno (2020) — 보안과 TypeScript를 기본값으로

2018년 JSConf EU에서 Ryan Dahl은 "**Node.js에 대해 후회하는 10가지(10 Things I Regret About Node.js)**"라는 강연을 했다.\
그가 꼽은 후회는 다음과 같았다.

- **보안 모델의 부재** — V8은 본래 안전한 샌드박스인데, Node는 그것을 깨고 모든 스크립트에 파일·네트워크·환경변수 전권을 줬다.
- **`node_modules`와 `package.json`의 복잡성** — 중앙 집중 패키지 시스템과 비대한 의존성 트리.
- **모듈 해석의 마법** — 확장자 생략, `index.js` 암묵 해석 등 모호한 규칙.
- Promise를 API의 기본으로 삼지 않은 점, GYP 빌드 시스템 등.

> **샌드박스(sandbox)** — 프로그램이 건드릴 수 있는 것을 미리 울타리로 제한해 두고 그 안에서만 돌리는 것.\
> 예: 원문이 적은 대로 Node는 V8의 그 샌드박스를 깨고 모든 스크립트에 파일·네트워크·환경변수 전권을 줬고, Deno는 반대로 플래그로 허용한 것만 준다(아래 코드).

이 후회들을 **백지에서 다시 설계**한 결과가 2020년 5월의 **Deno 1.0**이다(공동 제작 Bert Belder).\
Deno는 V8 위에 **Rust**로 작성된 런타임이며, 핵심 차별점은 다음과 같다.

1. **기본 보안(secure by default)** — 코드는 샌드박스에서 실행되며, 파일·네트워크·환경 접근은 **명시적 플래그**로만 허용된다.
2. **TypeScript 일급 지원** — 별도 설정 없이 `.ts`를 바로 실행(내부적으로 트랜스파일·캐싱).
3. **웹 표준 지향** — `fetch`, `URL`, `Web Workers` 등 브라우저 API와 호환. 초기엔 `node_modules` 없이 **URL로 모듈을 직접 import**하는 모델을 밀었다(후일 npm 호환성도 추가).

```bash
# 권한을 주지 않으면 네트워크 접근이 거부된다
deno run server.ts
# ⛔ error: Requires net access. Run again with --allow-net

# 필요한 권한만 명시적으로 부여
deno run --allow-net server.ts
```

```ts
// Deno — 웹 표준 API와 TypeScript가 기본. import는 URL 또는 npm: 지정자
import { serve } from "https://deno.land/std/http/server.ts";

serve((_req: Request): Response => {
  return new Response("Hello from Deno\n");
}, { port: 8080 });
```

Deno는 "Node를 죽이려는" 시도라기보다, **런타임이 처음부터 보안·표준·DX(개발자 경험)를 갖췄다면 어땠을까**에 대한 답이었다.\
시장 점유는 Node에 크게 못 미쳤지만, 그 설계 철학(권한 모델·TS 내장·웹 표준 정렬)은 Node 자신과 엣지 런타임들에 강한 압력을 주었다.

### 4-2. Bun (2022) — 속도를 무기로

Deno가 "철학"으로 도전했다면, **Bun**은 **순수한 속도**로 도전했다.\
Jarred Sumner가 Next.js 프로젝트의 느린 빌드·설치 속도에 좌절한 것이 출발점이었고, 2022년 7월 **Bun 0.1**이 공개됐다.

Bun의 기술적 선택이 핵심이다.

- **JavaScriptCore 엔진** — Node·Deno가 V8을 쓰는 것과 달리, Bun은 Safari의 **JavaScriptCore**(JSC)를 채택했다. JSC는 V8보다 **시작 시간이 빠르고 메모리가 가벼운** 경향이 있어, 서버리스·CLI처럼 자주 켜고 끄는 환경에 유리하다.
- **Zig로 작성** — 런타임·번들러·트랜스파일러를 저수준 언어 Zig로 구현해 시스템 호출 오버헤드를 최소화했다.
- **올인원 툴킷** — 런타임뿐 아니라 **패키지 매니저(`bun install`)·번들러·테스트 러너·TS 실행**을 하나로 묶었다. "Node + npm + Webpack + Jest + ts-node"를 단일 바이너리로 대체한다는 그림.
- **Node 호환성** — `node_modules`와 다수 Node API를 그대로 지원해 마이그레이션 장벽을 낮췄다(Deno의 초기 비호환 노선과 대비).

> **번들러(bundler)** — 여러 파일로 흩어진 코드를 한 덩어리로 묶어 내보내는 도구.\
> 예: 원문이 "Node + npm + Webpack + Jest + ts-node"를 단일 바이너리로 대체한다고 적을 때, 그중 Webpack이 번들러다(원문에 없는 대응 — 이해를 돕는 보충).

```bash
bun install          # npm보다 수 배~수십 배 빠른 의존성 설치를 표방
bun run server.ts    # TS를 트랜스파일 설정 없이 바로 실행
bun test             # 내장 테스트 러너
```

```ts
// Bun — 내장 HTTP 서버 API. 별도 프레임워크 없이 동작
const server = Bun.serve({
  port: 8080,
  fetch(_req) {
    return new Response("Hello from Bun\n");
  },
});

console.log(`http://localhost:${server.port} 에서 실행 중`);
```

벤치마크 조건에 따라 Node·Deno 대비 수 배 빠른 처리량·시작 속도를 보였고, 이는 "JS 런타임도 아직 성능 최적화 여지가 크다"는 점을 환기시켰다.\
(참고로 2026년 들어 Bun은 Zig에서 **Rust로의 재작성**을 진행 중이라고 발표했다 — 런타임 경쟁이 여전히 진행형임을 보여주는 신호다.)

### Node·Deno·Bun 비교

| | Node.js (2009) | Deno (2020) | Bun (2022) |
|---|---|---|---|
| 엔진 | V8 | V8 | JavaScriptCore |
| 구현 언어 | C/C++ | Rust | Zig (→ Rust 재작성 중) |
| 보안 | 전권(기본 허용) | 샌드박스(명시 허용) | Node 호환(전권) |
| TypeScript | 별도 도구 필요 | 내장 | 내장 |
| 패키지 | npm | URL / npm 호환 | 내장 `bun install`(npm 호환) |
| 지향점 | 사실상 표준·안정성 | 보안·웹 표준·DX | 속도·올인원 툴킷 |

표를 읽는 법 — 왼쪽 열이 항목이고, 오른쪽 세 열이 세 런타임의 선택이다.\
같은 행을 가로로 읽으면 같은 항목에서 셋이 어떻게 갈렸는지 보인다.

---

## 5. 엣지 런타임 — 서버가 사용자 옆으로 (2017~)

### 왜 "엣지"인가

전통적 서버리스(AWS Lambda 등)는 요청마다 **컨테이너**를 띄운다.\
컨테이너가 식어 있으면(cold start) 기동에 수백 ms~수 초가 걸린다.\
또한 함수는 보통 한 리전(예: 미국 동부)에 있어, 지구 반대편 사용자에겐 물리적 왕복 지연이 따라붙는다.

> **콜드 스타트(cold start)** — 식어 있던 실행 환경을 처음부터 띄우느라 첫 요청이 느려지는 것.\
> 예: 컨테이너형은 기동에 수백 ms~수 초가 걸리고, isolate형은 1ms 미만이다(원문의 값 그대로).

**Cloudflare Workers**(2017 발표, 2018 정식 출시)는 다른 길을 택했다.\
컨테이너 대신 **V8 isolate**를 쓴다.\
isolate는 Chrome이 브라우저 탭을 격리하는 바로 그 기술로, 하나의 런타임 프로세스 안에서 수백~수천 개의 격리된 실행 컨텍스트를 띄울 수 있다.\
덕분에 **콜드 스타트가 1ms 미만**으로 사실상 사라진다.\
게다가 이 런타임을 Cloudflare의 **전 세계 수백 개 엣지 거점**에 깔아, 코드가 사용자와 가장 가까운 곳에서 실행되게 했다.

> **V8 isolate** — 하나의 런타임 프로세스 안에 여러 개를 띄울 수 있는, 서로 격리된 실행 컨텍스트(원문의 정의 그대로).\
> 예: Chrome이 브라우저 탭을 격리하는 바로 그 기술이고, 한 프로세스에 수백~수천 개가 들어간다.

> **엣지(edge)** — 중앙의 한 리전이 아니라 사용자와 가까운 곳에 흩어 둔 실행 거점.\
> 예: Cloudflare는 전 세계 수백 개 엣지 거점에 런타임을 깔아, 코드가 사용자와 가장 가까운 곳에서 돌게 했다.

```js
// Cloudflare Workers — 요청 핸들러를 export 하는 모듈 형태
// V8 isolate 위에서, 사용자와 가까운 엣지 노드에서 실행된다
export default {
  async fetch(request, env, ctx) {
    return new Response("Hello from the edge\n");
  },
};
```

### 격리(isolate) vs 컨테이너

| | 컨테이너형 서버리스(Lambda 등) | isolate형 엣지(Workers) |
|---|---|---|
| 격리 단위 | OS 컨테이너(무겁다) | V8 isolate(가볍다) |
| 콜드 스타트 | 100ms~수 초 | < 1ms |
| 실행 위치 | 특정 리전 | 전 세계 엣지 |
| 제약 | 거의 풀 Node API | 웹 표준 API 서브셋(파일시스템·네이티브 모듈 제한) |

표를 읽는 법 — 네 행 모두 왼쪽이 컨테이너형, 오른쪽이 isolate형이다.\
맨 아래 「제약」 행이 원문이 바로 다음 문단에서 "대가"로 풀어 쓴 항목이다.

**대가는 무엇인가** — 원문이 직접 "대가"라고 적은 대목은 이것이다.

> 대가도 있다. isolate는 가벼운 대신 **Node의 전체 API를 쓸 수 없다**. 파일시스템 접근이나 네이티브 애드온이 제한되고, 실행 시간·메모리도 빠듯하다. 그래서 엣지 런타임은 "풀 Node"가 아니라 **웹 표준 API의 서브셋**(`fetch`·`Request`·`Response`·`URL`·`crypto.subtle` 등)을 제공한다.

### 표준화 — WinterCG와 workerd

엣지 런타임이 늘면서(Cloudflare Workers, Vercel Edge Functions, Deno Deploy 등) "런타임마다 지원 API가 제각각"이라는 파편화가 문제가 됐다.\
이를 풀기 위해 2022년 **WinterCG**(Web-interoperable Runtimes Community Group)가 출범했다 — 브라우저가 아닌 JS 런타임들이 **공통으로 제공할 웹 API 서브셋**을 표준화하려는 모임으로, Cloudflare·Deno·Node·Vercel 등이 참여했다.

같은 2022년 9월, Cloudflare는 Workers의 실제 엔진을 `workerd`라는 이름으로 **오픈소스(Apache 2.0)** 공개했다.\
이로써 개발자가 엣지 런타임을 로컬·자체 호스팅 환경에서 그대로 돌릴 수 있게 됐고, 엣지가 특정 벤더에 종속되지 않는 방향으로 한 걸음 나아갔다.

> **흐름의 수렴** — Deno·Bun·엣지 런타임이 공통으로 **웹 표준 API**(`fetch` 등)로 수렴하고 있다는 점이 중요하다. 2009년 Node는 브라우저와 전혀 다른 독자 API(`require`·`http` 모듈)로 출발했지만, 2020년대의 런타임들은 "브라우저든 서버든 엣지든 같은 표준 코드가 돈다"는 **동형성**(isomorphism)을 지향한다. 십수 년을 돌아 JS 런타임 세계는 다시 웹 표준으로 합류하는 중이다.

> **동형성(isomorphism)** — 브라우저든 서버든 엣지든 같은 표준 코드가 그대로 도는 성질(원문의 풀이 그대로).\
> 예: `fetch` 같은 웹 표준 API를 세 곳이 모두 제공하면, 같은 코드를 옮겨 심을 수 있다.

---

## 6. 영향과 의의

*(이 편의 「남긴 것」에 해당한다. 아래 불릿은 원문 이 절의 다섯 불릿 그대로다.)*

- **언어의 영토 확장** — Node는 JavaScript를 브라우저 밖으로 꺼내, 백엔드·CLI·데스크톱(Electron)·빌드 도구(Webpack·Vite)·심지어 IoT까지 단일 언어로 다룰 수 있게 했다. 오늘날 프론트엔드 개발의 거의 모든 빌드 파이프라인이 Node 위에서 돈다.
- **비동기 프로그래밍의 대중화** — 콜백 → Promise → `async/await`로 이어진 비동기 패러다임의 진화는 Node가 실전 무대를 제공했기에 가능했다. (이 문법 진화는 ECMAScript 표준의 몫이며, 별도 장에서 다룬다.)
- **패키지 생태계의 명암** — npm은 재사용성의 천국이자 공급망 보안의 최전선이 되었다. "작은 모듈 다수 조합" 문화는 생산성과 위험을 동시에 키웠다.
- **거버넌스라는 교훈** — io.js 분기와 재통합, 재단화의 역사는 오픈소스 인프라가 **중립적 거버넌스** 없이는 지속되기 어렵다는 점을 보여준 사례로 남았다.
- **경쟁이 만든 진보** — Deno(보안·TS·웹 표준), Bun(속도·올인원), 엣지(분산·격리)라는 도전자들은 Node를 대체하진 못했어도, Node 자신이 안정적 TS 지원·내장 테스트 러너·`fetch` 내장·권한 모델 실험 등으로 빠르게 진화하도록 자극했다. JS 런타임 세계는 2009년 이래 가장 활발한 경쟁기를 지나는 중이다.

---

## 용어 풀이

- **런타임(runtime)** — 그 언어로 쓴 코드를 실제로 돌려 주는 환경. Node·Deno·Bun·엣지 런타임이 모두 여기에 속한다.
- **스레드-퍼-커넥션(thread-per-connection)** — 들어오는 연결마다 스레드를 하나씩 붙여 처리하는 방식.
- **블로킹(blocking) / 논블로킹(non-blocking)** — 결과가 날 때까지 멈춰 기다리는 것 / 맡겨 두고 다음 줄로 넘어가는 것.
- **C10K 문제** — 동시 접속 1만 개를 어떻게 감당할 것인가.
- **이벤트 루프(event loop)** — 할 일을 담아 둔 큐를 계속 돌며 준비된 것부터 실행하는 구조. Node의 심장이다.
- **libuv** — Node의 비동기 I/O 추상화를 담당하는 C 라이브러리.
- **V8 / JavaScriptCore(JSC)** — Chrome의 JS 엔진 / Safari의 JS 엔진. Bun이 뒤쪽을 택했다.
- **JIT 컴파일** — 실행하는 시점에 기계어로 번역해 돌리는 방식.
- **CommonJS** — 파일 단위로 코드를 나누고 `module.exports` / `require`로 의존성을 연결하는 규약.
- **I/O 바운드 / CPU 바운드** — 시간의 대부분이 입출력 대기인 일 / 계산 그 자체인 일.
- **`worker_threads`** — CPU 바운드 작업의 약점을 보완하려고 2018년 Node 10.5+에 들어온 것.
- **npm(Node Package Manager)** — 2010년 1월 Isaac Schlueter가 내놓은 패키지 매니저이자 그 레지스트리.
- **SemVer(유의적 버전)** — `MAJOR.MINOR.PATCH` 세 자리로 변화의 크기를 드러내는 버전 규칙.
- **`node_modules` 트리** — 의존성의 의존성을 중첩해 각자 격리하는 구조. 초기엔 트리, 후일 평탄화로 진화했다.
- **lockfile** — 실제로 설치된 버전을 적어 두어 다음에도 같은 것이 깔리게 하는 파일. `package-lock.json`.
- **공급망 보안** — 내가 쓰는 남의 코드와 그 코드가 다시 쓰는 코드까지를 신뢰해야 하는 데서 오는 위험을 다루는 일.
- **포크(fork) / 거버넌스(governance)** — 저장소를 복사해 따로 개발해 나가는 것 / 방향과 릴리스를 누가 어떤 절차로 정하는가.
- **TSC(기술 위원회) / 재단** — 프로젝트를 운영하는 공식 위원회 / Node.js Foundation, OpenJS Foundation 같은 중립 조직.
- **LTS(Long-Term Support)** — 장기 보안 지원을 보장하는 릴리스 라인. 짝수 메이저 버전이 여기에 해당한다.
- **샌드박스(sandbox)** — 건드릴 수 있는 것을 울타리로 제한해 두고 그 안에서만 돌리는 것.
- **번들러(bundler)** — 여러 파일로 흩어진 코드를 한 덩어리로 묶어 내보내는 도구.
- **서버리스 / 컨테이너** — 요청이 올 때만 실행 환경을 띄우는 방식 / 그 실행 환경을 담는 OS 단위 상자.
- **콜드 스타트(cold start)** — 식어 있던 실행 환경을 처음부터 띄우느라 첫 요청이 느려지는 것.
- **V8 isolate** — 한 런타임 프로세스 안에 여러 개 띄울 수 있는, 서로 격리된 실행 컨텍스트.
- **엣지(edge)** — 중앙의 한 리전이 아니라 사용자와 가까운 곳에 흩어 둔 실행 거점.
- **WinterCG / `workerd`** — 비브라우저 JS 런타임들의 공통 웹 API 서브셋을 표준화하려는 모임 / 2022년 9월 오픈소스로 공개된 Workers의 실제 엔진.
- **동형성(isomorphism)** — 브라우저든 서버든 엣지든 같은 표준 코드가 그대로 도는 성질.

---

## 참고 출처

- [Node.js — Wikipedia](https://en.wikipedia.org/wiki/Node.js)
- [Ryan Dahl: Node.js, Evented I/O for V8 Javascript — JSConf.eu 2009](https://www.jsconf.eu/2009/speaker/speakers_selected.html)
- [Node.js Internals: libuv and the event loop — Medium (Softup Technologies)](https://medium.com/softup-technologies/node-js-internals-libuv-and-the-event-loop-behind-the-curtain-30708c5ca83)
- [npm — Wikipedia](https://en.wikipedia.org/wiki/Npm)
- [npm passes the 1 millionth package milestone — Snyk](https://snyk.io/blog/npm-passes-the-1-millionth-package-milestone-what-can-we-learn/)
- [GitHub Acquires npm — The New Stack](https://thenewstack.io/github-acquires-npm-buying-microsoft-a-presence-in-the-node-javascript-community/)
- [Node.js and io.js Merge Under the Node Foundation — InfoQ](https://www.infoq.com/news/2015/05/nodejs-iojs/)
- [Node.js Foundation Combines Node.js and io.js Into Single Codebase (v4) — nodejs.org](https://nodejs.org/en/blog/announcements/foundation-v4-announce)
- [Deno (software) — Wikipedia](https://en.wikipedia.org/wiki/Deno_(software))
- [Exploring Deno Land with Ryan Dahl — Changelog #443](https://changelog.com/podcast/443)
- [Bun (software) — Wikipedia](https://en.wikipedia.org/wiki/Bun_(software))
- [Jarred Sumner, Bun's creator, talks tech, funding, and startups — InfoWorld](https://www.infoworld.com/article/2338698/interview-with-jarred-sumner-buns-creator-talks-tech-funding-and-startups.html)
- [How Workers works — Cloudflare Workers docs](https://developers.cloudflare.com/workers/reference/how-workers-works/)
- [Introducing workerd: the Open Source Workers runtime — Cloudflare Blog](https://blog.cloudflare.com/workerd-open-source-workers-runtime/)
