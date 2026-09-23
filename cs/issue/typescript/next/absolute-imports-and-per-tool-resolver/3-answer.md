# cs/issue/typescript/next/absolute-imports-and-per-tool-resolver — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: —

## 정답

<!-- 질문 1:1 대응 -->

1. 상대 임포트의 기준점은 **그 임포트가 적힌 파일의 현재 위치**다. `./logger`는 "나와 같은 폴더의 logger"라는 뜻이라, 파일이 다른 폴더로 이사하면 "나와 같은 폴더"가 달라져 실제로 없는 경로를 가리키게 된다. 절대(alias) 임포트 `@/shared/lib/logger`의 기준점은 **고정된 src 루트**라, 임포트하는 파일이 어디로 가든 가리키는 대상이 불변이다. 그래서 파일 이동에 상대만 깨지고 절대는 안 깨진다.
   > **상대 임포트 / 절대 임포트** — 상대는 현재 파일 위치 기준(`./`, `../`), 절대는 프로젝트 루트 기준(`@/`). 전자는 "누가 부르느냐"에 따라, 후자는 부르는 쪽과 무관하게 대상이 정해진다.

2. 일괄 치환은 `@/lib/...`처럼 **문자열이 고정적인** 절대 임포트만 찾아 바꿀 수 있었고, `./logger`·`./client` 같은 상대 임포트는 치환 규칙의 대상 문자열이 아니어서 그대로 남았다(같은 `./logger`라도 파일마다 가리키는 실제 대상이 달라 기계적 치환이 어렵다). 빌드가 오류를 **한 번에 하나씩만** 뱉어 고치고-빌드를 3회 반복했다. 근본 원인은 "누가 실수했다"가 아니라 **상대·절대가 정책 없이 섞여 있던 것** — 정책 부재다. 혼용 상태에서는 파일을 옮길 때마다 어떤 임포트가 깨질지 예측할 수 없다.

3. "같은 폴더 안이라도 절대경로만" 정책은 **파일 이동이 임포트를 절대 못 깨뜨리게** 만든다. 방어하는 미래 사고: 리팩토링으로 파일을 폴더 간 이동할 때(응집 재편, 도메인 분리 등) 상대 임포트가 조용히 깨져 빌드가 연쇄로 터지는 것. 절대경로만 쓰면 파일의 위치가 임포트의 정확성과 **독립**이 되어, 옮기는 작업이 임포트 수정을 유발하지 않는다.

4. `@` alias가 `tsconfig.json`의 `paths`에 있어도 vitest만 못 찾은 이유는, **vitest가 tsconfig의 paths를 읽지 않고 자기 리졸버(vite)를 쓰기 때문**이다. `paths`는 Next(번들러)와 tsc(타입체커)가 읽는 설정이다. vitest는 vite 위에서 돌고, vite는 모듈을 자기 방식으로 해석하므로 `tsconfig.paths`에 뭐가 있든 모른다 — 같은 alias를 `vitest.config.ts`의 `resolve.alias`에 별도로 심어야 비로소 해석한다.

5. **리졸버**는 `@/foo` 같은 임포트 문자열을 실제 파일 경로로 바꿔 찾아주는 부품이고, 도구마다 이 부품이 다르다. Next는 번들러(webpack/turbopack)의 리졸버, tsc는 타입체커의 리졸버, vitest는 vite의 리졸버를 쓴다. "alias는 프로젝트 설정이 아니라 도구마다의 설정"이란, alias를 이해하는 주체가 "프로젝트"라는 추상적 존재가 아니라 **각자 독립된 리졸버를 가진 개별 도구들**이라는 뜻이다. 그래서 한 곳(tsconfig)에 적어도 그것을 안 읽는 도구는 여전히 모른다.
   > **리졸버(resolver)** — 임포트 문자열을 실제 파일 경로로 해소하는 부품. 빌드·타입체크·테스트 러너가 각자 다른 리졸버를 가지며, 각자 자기 설정에서 alias를 읽는다.

6. `tsconfig.json`의 `paths`는 **타입체커(tsc)·에디터·번들러가 "이 alias는 이 경로를 뜻한다"고 참고하는 힌트**다. `moduleResolution: "bundler"`·`noEmit: true`가 말해주듯, tsc는 여기서 타입만 검사하고 실제 JS를 내보내지 않으며, 런타임 모듈 로딩은 번들러(Next)가 담당한다. 즉 `paths`는 "런타임에 실제로 모듈을 찾는 방법"을 정의하는 게 아니라 타입 해석·에디터 점프·번들러 힌트용이다. 그래서 런타임에 실제로 모듈을 로드하는 각 도구(vite 등)에는 alias를 또 알려줘야 한다.

7. 두 원리가 붙어 다니는 이유: **①절대경로 정책을 채택하는 순간, 그 절대경로(`@/`)를 이해해야 하는 도구가 여러 개로 늘어나기 때문**이다. 상대 임포트만 쓸 때는 모든 도구가 파일시스템 상대 경로만 알면 되니 추가 설정이 없다. 그러나 `@/`라는 "프로젝트가 정의한 별칭"을 쓰기로 하면, 그 별칭의 뜻은 자연법칙이 아니라 각 도구에 가르쳐줘야 하는 규칙이 된다 — 빌드·타입체크·테스트 러너 각각의 리졸버에. 그래서 ①(정책 채택)이 ②(도구별 alias 등록)를 필연으로 부른다. alias는 편의를 주는 대신 "그 편의를 아는 도구를 빠짐없이 챙기라"는 유지비를 청구한다.

## 문제 구조 (추상화 코드)

### 변형 A — 파일 이동이 상대 임포트를 깨뜨림 (일괄 치환이 못 잡음)
① 문제 코드
```ts
// lib/client.ts  →  shared/api/client.ts 로 이동
import { log } from "./logger";          // 기준점 = 이 파일 위치 → 이동 후 없는 경로
import { cfg } from "@/lib/config";      // 일괄 치환은 고정 문자열인 절대 임포트만 바꿈
```
② 고친 코드
```ts
// shared/api/client.ts
import { log } from "@/shared/lib/logger";   // 같은 폴더라도 절대 경로만 (정책)
import { cfg } from "@/shared/lib/config";
```
무엇이 깨졌나: 상대·절대 임포트가 정책 없이 섞여, 파일 이동마다 어떤 임포트가 깨질지 예측할 수 없었다(빌드가 하나씩만 알려 3회 반복).\
같은 구조: 다른 언어(패키지 상대 임포트 `from ..pkg import x`)에서 모듈을 국가별 하위 패키지로 옮기자 `..`의 대상이 바뀌어 108곳이 깨짐 → 절대 임포트로 일괄 치환한 뒤 ① 옛 경로 grep 0건 ② 파일 내부 상호 참조 ③ 남은 상대 임포트를 확인. 호환용 재수출(shim) 제거도 "참조 grep → 원 경로로 교체 → grep 0건 → 삭제" 순서로.\
같은 구조: 폴더를 통째로 복제(포크)하면 폴더 **안** 상대 임포트는 사본을 따라가지만, 폴더 **밖**을 가리키는 `../other/x.js`는 여전히 원본을 가리켜 격리가 깨짐 → 경계를 넘는 임포트만 grep으로 찾아 치환.\
같은 구조: 사용처를 한 패턴으로 grep하면 상대 경로·alias·여러 줄에 걸친 import를 놓쳐 과소 집계(17곳 vs 실제 36곳) → 넓은 패턴 검색 + 삭제 후 빌드로 누락 검출.

### 변형 B — alias를 한 도구에만 알려줌
① 문제 코드
```jsonc
// tsconfig.json — 빌드·타입체크만 읽음
{ "compilerOptions": { "moduleResolution": "bundler", "noEmit": true, "paths": { "@/*": ["./src/*"] } } }
```
```ts
// vitest.config.ts — alias 없음 → 테스트 러너만 "Cannot find module '@/...'"
export default defineConfig({ /* ... */ });
```
② 고친 코드
```ts
// vitest.config.ts
export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
});
```
무엇이 깨졌나: alias를 "프로젝트 설정"으로 여겼지만 실제로는 리졸버마다의 설정이었다.\
같은 구조: 다른 테스트 러너(Jest)에서도 `src/`·`@/` alias가 풀리지 않아 `moduleNameMapper`에 별도 등록, ESM으로만 배포된 의존성은 `transformIgnorePatterns`에서 제외해 변환 대상에 포함.

### 변형 C — 상대 자산 경로 문자열의 기준점이 셋
```text
CSS url("img/a.png")               기준 = CSS 파일 위치        파일과 함께 이동 → 안전
JS/JSON 문자열 "img/a.png"          기준 = 현재 페이지 URL      라우트·파일 이동에 깨짐
new URL("img/a.png", import.meta.url) 기준 = 모듈 파일 위치     파일과 함께 이동 → 안전
```
고친 방법: 자산 참조를 `grep -rhoE '"/(css|js|data|images)/[^"]*"' | sort | uniq -c`로 지도화해 전부 `/`로 앵커링된 절대 경로인지 확인, 모듈 기준이 필요하면 `import.meta.url`.\
무엇이 깨질 수 있었나: 대규모 폴더 재편에서 "페이지 URL 기준" 문자열만 이동에 취약하다(실제 깨짐 전 점검으로 확인).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~C)은 "기준점이 고정된 절대 경로 + 도구마다 alias 등록"이다. 같은 원리(모듈 해석은 파일 위치·도구마다 기준이 달라 이동·도구 교체에 깨짐)에 다른 방안이 쓰인 사례:

### 방안 1 — CJS→ESM 로더 충돌은 의존성 버전 핀
```text
문제: 테스트 DOM 환경 패키지 새 메이저 → 전이 의존성(CJS)이 순수 ESM 패키지를 require
      → ERR_REQUIRE_ESM → 테스트 수집 0 (작업과 무관하게 main에서도 재현, 장기간 tsc·build로 대체)
고친: package.json devDependencies 에서 그 패키지를 이전 메이저로 고정 → 수집 0 → 18 테스트 green
```

### 방안 2 — JSON 동적 import의 타입은 정적 import로
```ts
// 문제: 해당 tsconfig 환경에서 import() 로 읽은 JSON 은 unknown 으로 추론 → 사용처와 타입 불일치
const dict = await import(`./dict/${locale}.json`);
// 고친: 로케일별 정적 import 후 매핑
import ko from "./dict/ko.json";
import en from "./dict/en.json";
const dicts = { ko, en };
```

### 방안 3 — 배럴(index) 대신 심층 경로 import
```ts
// 문제: 배럴이 서버 전용 모듈(요청 헤더 API 사용)까지 재수출 → 클라이언트가 배럴을 import하면 경계 위반
// features/menu/index.ts
export * from "./ui"; export * from "./server/getMenuTree";
// client component
import { MenuView } from "@/features/menu";          // 서버 전용 모듈이 의존 그래프에 들어옴
// 고친
import { MenuView } from "@/features/menu/ui/MenuView";
```
같은 구조: 서버 데이터 함수가 `catch { return null }`로 프레임워크의 동적 렌더 신호 예외까지 삼켜 렌더 모드 판정이 깨짐 → 그 예외(digest로 식별)는 rethrow, 그 외만 경고 1회 후 null.

### 방안 4 — classic script는 모듈이 아니다: 전역 이름 단일 선언 + 로드 순서 고정
```html
<!-- 문제: 큰 HTML의 인라인 스크립트를 파일 여러 개로 분리 → 모두 한 전역 스코프 공유
     → 두 파일에 같은 최상위 let 선언 → 재선언 SyntaxError, 교차 참조는 로드 순서 의존 -->
<script src="monitor.js"></script>   <!-- let errCount = 0; -->
<script src="migrate.js"></script>   <!-- let errCount = 0; -->
<!-- 고친: 한 파일에서만 선언, defer 로 순서 고정(core → monitor → ... ), 파일마다 문법 검사 -->
<script defer src="core.js"></script>
<script defer src="monitor.js"></script>
```

### 방안 5 — 존재하지 않는 named export는 빌드를 통과하고 undefined로 바인딩
```js
// 문제: 변환된 ESM 에서 없는 이름을 named import → 빌드 성공, 값은 undefined
import { searchEuFilter } from "@/api/search";   // 실제 export: searchEUFilter
const cfg = { filterApi: searchEuFilter };        // 여기선 조용함
cfg.filterApi(q);                                  // 호출 시점에야 "is not a function"
// 고친: export 이름과 정확히 일치
import { searchEUFilter } from "@/api/search";
```
같은 구조: `current?.value.trim()`은 `value`가 없으면 터짐 → `current?.value?.trim() ?? ""`.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 절대 경로 + 도구별 alias | 파일이 자주 이동한다, 도구가 여럿이다 | alias를 도구마다 등록 | 새 도구 추가 시 alias 누락 | 폴더 재편·리팩토링이 잦은 코드베이스 |
| 1. 버전 핀 | 전이 의존성의 모듈 형식이 바뀌었다 | 업그레이드 보류 | 핀이 오래되면 보안·호환 부채 | 도구 체인이 모듈 형식 충돌로 통째로 깨졌을 때 |
| 2. 정적 import | 대상 집합이 유한하다(로케일 등) | 대상 추가 시 import 추가 | 대상이 많으면 번들 증가 | 타입이 필요한 JSON 데이터 |
| 3. 심층 경로 import | 배럴이 서로 다른 실행 환경 모듈을 섞는다 | 긴 경로 | 배럴을 다시 쓰면 재발 | 서버/클라이언트 경계가 있는 프레임워크 |
| 4. 전역 단일 선언 + 순서 고정 | 모듈 시스템 없이 classic script를 쓴다 | 순서 관리 | 순서가 바뀌면 참조 실패 | 번들러 없는 레거시 페이지 |
| 5. export 이름 정확 일치 | 변환기가 없는 export를 오류로 내지 않는다 | 없음 | 호출 시점까지 발견 안 됨 | 트랜스파일된 ESM (타입 검사 없음) |

**결론**: 경로 문자열이 **무엇을 기준점으로** 해석되는지(파일 위치·페이지 URL·도구 설정)를 먼저 확인하고, 이동에 불변인 기준점(절대 경로)을 고른다 — 기본.\
도구 체인 자체가 모듈 형식·경계 때문에 깨지면 기준점이 아니라 **그래프에 무엇이 들어오는지**를 통제한다(1·3).\
전역 이름이 파일 경계 없이 섞이거나(4) 없는 이름이 조용히 undefined가 되는(5) 환경에서는 이름·선언을 한 곳으로 모으고 타입 검사·문법 검사로 빌드 시점에 끌어올린다.
