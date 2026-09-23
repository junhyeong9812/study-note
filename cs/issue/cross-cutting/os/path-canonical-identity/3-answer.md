# cs/issue/os/path-canonical-identity — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **여러 표기.** `./`가 끼는 경우, `..`로 돌아오는 경우, 끝 슬래시 유무, 심링크(다른 이름의 같은 디렉토리), 구분자 차이(`/` vs `\`), 대소문자 비구분 파일시스템의 대소문자 차이가 있다.\
문자열 `===`로 비교하면 같은 대상을 다르다고 보는 **false-miss**(배지가 안 붙음, 브랜치가 빈 값)와, 다른 대상을 같다고 보는 **false-positive**(중첩 워크트리를 바깥 것으로 오매칭, 끝 슬래시 차이로 "다른 대상" 표시)가 모두 생겼다.
   > **canonical path** — 심링크·`.`·`..`·중복 구분자를 해석해 표기 차이를 없앤 정규 경로. 단 하드링크·바인드 마운트는 정규 경로로도 여러 개가 남는다(파일 신원 자체가 필요하면 device+inode). `..`는 심링크를 해석한 뒤 처리해야 한다 — 문자열로만 접으면 `/link/..`를 잘못 계산한다. 또 `realpath`류는 존재하는 경로에만 동작한다.

2. **접두 문자열 포함 판정.** `startsWith(root)`는 `/repo`가 `/repo2/x`의 접두가 되는 문제, 끝 슬래시 차이, 백슬래시 구분자를 처리하지 못한다.\
또 루트가 여러 개(중첩)면 짧은 쪽이 먼저 매칭된다.\
포함은 **세그먼트 단위 조상 관계**로 판정하고, 후보가 여럿이면 대상을 포함하는 **가장 긴 루트**(가장 가까운 조상)를 고른다.\
가능하면 도구가 정규화해 주는 값(예: VCS의 "최상위 디렉토리" 조회)을 받아 루트끼리 동등 비교한다.

3. **진입점별 정규화 불일치.** raw 경로 키와 canonical 경로 키는 같은 프로젝트에서도 다른 문자열이 되어 **서로 다른 저장 폴더**를 가리키고, 하위 프로세스에 넘기는 인자도 어긋났다.\
in-flight 잠금 키였다면, 같은 대상을 다른 별칭(심링크 등)으로 요청해 **잠금을 우회**하고 중복 실행할 수 있다.\
교정은 정규화 함수를 **단일 진입점**으로 만들고 모든 키·잠금이 그것을 거치게 하는 것이다(보안 경계로 쓰는 잠금이라면 정규화 후 심링크가 교체되는 경합까지는 이것만으로 막지 못한다).

4. **빈 문자열 = cwd, 멱등 API의 무음 성공.** 시스템 콜 수준에서는 빈 경로가 보통 ENOENT지만, 경로를 절대화·결합하는 많은 상위 API(resolve·abspath·join 류)는 빈 경로를 **현재 작업 디렉토리**로 해석한다.\
루트 바로 아래 항목(`/a`)의 부모를 `lastIndexOf("/")`로 자르면 `""`가 되고, 그 경로로 디렉토리를 다시 읽으면(이 사례의 경로 처리 계층에서는) **프로세스 cwd**의 내용이 트리에 섞인다.\
`create_dir_all`은 "이미 있으면 성공"인 멱등 API라, `.`·`/`·`...` 같은 퇴화 입력이 빈 세그먼트로 사라져도 아무것도 만들지 않고 성공을 보고한다.\
정규화 후 결과가 비면 **거부**하고, `dirname`은 결과가 비면 `/`를 돌려주게 한다.

5. **구분자로 둘러싼 패턴.** `/src/`는 앞뒤에 구분자가 있어야 매칭되므로, 상대경로의 **첫 세그먼트**(`src/foo`)는 앞 구분자가 없어 놓친다.\
결과적으로 다른 규칙(파일명 접미 치환)으로 떨어져 엉뚱한 경로가 계산됐다.\
경로를 세그먼트 목록으로 다루면 "첫 세그먼트/중간 세그먼트"의 구분 자체가 사라진다 — 최소한 선두 접두(`src/`) 분기를 따로 두고 회귀 테스트를 붙인다.

6. **정규화 불가 환경.** 브라우저·웹뷰는 파일시스템에 접근할 수 없어 심링크를 해석하지 못한다.\
그래서 그쪽은 끝 슬래시 제거 같은 **문자열 수준 정규화까지만** 하고, 심링크 해석이 필요한 비교는 FS에 접근 가능한 백엔드가 **정규화된 루트를 계산해 내려주게** 했다.\
해결하지 못한 잔여(비정규 경로)는 숨기지 않고 실패 표시·잔여 항목으로 가시화했다.\
원칙은 같다 — 정규화는 **그것을 할 수 있는 한 곳**에서 하고, 다른 곳은 결과만 쓴다.

7. **대소문자 캐시.** 대소문자 비구분 FS에서는 `File.ts`와 `file.ts`가 같은 파일이지만, 도구(언어 서버)의 캐시가 옛 표기를 키로 붙들면 import 인식이 어긋날 수 있다(이 방안의 출처는 사건 기록이 아니라 일반 가이드 수준).\
여기서는 비교 시 정규화를 도구 안에 넣을 수 없으므로, **입력 표기를 일관되게 강제**(대소문자가 다른 참조를 오류로)하고 캐시를 재시작하는 방안을 썼다 — 아래 「방안 비교」.

## 문제 구조 (추상화 코드)

### 변형 A — 경로 문자열 동등·접두 비교
① 문제 코드
```ts
const badge = sessions.filter(s => s.cwd === w.path);          // 하위 디렉토리·끝 슬래시·심링크에서 실패
const inside = target.startsWith(root.path + "/");               // 구분자·중첩 루트 미처리
const exists = names.includes(parent + "/" + name);              // "root/./a" vs "root/a" 중복 통과
```
② 고친 코드
```ts
// 백엔드: FS 접근 가능한 곳에서 루트를 정규화해 내려줌
session.root = worktreeRoot(session.cwd) ?? session.cwd;         // 도구가 canonicalize
const badge = sessions.filter(s => s.root === w.path);
const owner = roots.filter(r => isAncestor(r, target))           // 세그먼트 단위
                   .sort(byLengthDesc)[0];                       // 가장 가까운 조상
const exists = set.has(canonical(join(parent, name)));           // 정규형 기준 중복 검사
```
무엇이 깨졌나: 같은 대상의 다른 표기를 다른 것으로(또는 반대로) 판정했다.\
같은 구조: 이벤트 payload의 raw cwd 문자열 비교 → 진행 중 목록 재조회로 비교 자체를 제거 · 구분자 `/`만 처리 → 두 구분자 처리 · 후보 경로 비교 전 canonicalize.

### 변형 B — 진입점별 정규화 불일치
① 문제 코드
```rust
fn key_for_feature_x(p: &str) -> Key { Key::from(p) }                    // raw
fn key_for_feature_y(p: &str) -> Key { Key::from(canonicalize(p)?) }     // canonical
fn in_flight_guard(p: &str) -> Guard { lock(Key::from(p)) }              // 별칭으로 우회 가능
```
② 고친 코드
```rust
fn canonical_project(p: &str) -> Result<PathBuf> { /* 단일 진입점 */ }
fn key(p: &str) -> Key { Key::from(canonical_project(p)?) }             // 모든 기능 공통
fn in_flight_guard(p: &str) -> Guard { lock(key(p)) }
```
무엇이 깨졌나: 같은 대상이 기능마다 다른 키가 되어 저장 위치가 갈리고 잠금이 우회됐다.

### 변형 C — 퇴화 입력과 빈 문자열
① 문제 코드
```ts
const rel = input.replace(/\./g, "/");       // "." → "/" → 빈 세그먼트만 남음
await createDirAll(join(root, rel));          // 아무것도 안 만들고 성공
const parent = p.slice(0, p.lastIndexOf("/")); // "/a" → ""
reloadDir(parent);                             // "" = 프로세스 cwd → 트리 오염
```
② 고친 코드
```ts
const normalizeRel = (s: string): string => {
  const segs = s.split("/").map(x => x.trim()).filter(Boolean);
  if (segs.length === 0 || segs.some(x => x === "." || x === "..")) return "";
  return segs.join("/");
};
if (normalizeRel(input) === "") return reject();
const dirname = (p: string) => (p.lastIndexOf("/") <= 0 ? "/" : p.slice(0, p.lastIndexOf("/")));  // 절대경로 전제
```
무엇이 깨졌나: 무의미 입력이 멱등 API에서 성공으로 보고됐고, 빈 경로가 cwd로 해석됐다.

### 변형 D — 구분자로 둘러싼 세그먼트 검색
① 문제 코드
```rust
fn swap_seg(path: &str, from: &str, to: &str) -> Option<String> {
    let mid = format!("/{from}/");
    path.find(&mid).map(|i| /* ... 중간 세그먼트만 치환 */)   // "src/foo" 놓침
}
```
② 고친 코드
```rust
fn swap_seg(path: &str, from: &str, to: &str) -> Option<String> {
    if let Some(rest) = path.strip_prefix(&format!("{from}/")) {
        return Some(format!("{to}/{rest}"));                     // 선두 세그먼트
    }
    let mid = format!("/{from}/");
    path.find(&mid).map(|i| /* ... */)
}
```
무엇이 깨졌나: 경로를 세그먼트가 아니라 문자열로 다뤄 경계(선두)를 놓쳤다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

같은 원리(한 대상의 여러 표기)에 대한 두 방안.

### 방안 1 — 비교 시점에 정규화 (위 변형 A~D)
```rust
let k = key(canonical_project(input)?);   // 어떤 표기로 들어와도 한 키
```

### 방안 2 — 입력 표기를 일관되게 강제 (대소문자 비구분 FS·도구 캐시)
```jsonc
// 컴파일러/린터 설정
{ "compilerOptions": { "forceConsistentCasingInFileNames": true } }
// 대소문자만 다른 참조 = 오류, 파일명 변경 후 도구 캐시 재시작
```

| | 방안 1: 비교 시 정규화 | 방안 2: 표기 일관 강제 |
|---|---|---|
| 전제 | 비교 코드가 내 것이고 정규화 함수를 끼울 수 있다 | 비교가 외부 도구(캐시) 안에서 일어나 손댈 수 없다 |
| 비용 | 모든 진입점을 단일 함수로 모으는 리팩터링 | 설정 1줄 + 기존 불일치 참조 정리 |
| 실패 모드 | 진입점 하나라도 빠지면 키 분기 재발 · 정규화 불가 환경(웹뷰) 잔여 | 강제 밖의 경로(도구 외부 입력)는 여전히 불일치 · 캐시는 수동 재시작 |
| 맞는 조건 | 여러 표기가 정당하게 들어오는 입력(사용자 경로·심링크·이벤트 payload) | 표기를 사람이 통제하는 소스 코드 참조 |

결론: 입력 표기를 통제할 수 없으면 방안 1(단일 정규화 진입점)이 필요하다.\
비교 로직이 도구 안에 있어 손댈 수 없고 입력이 코드처럼 사람이 쓰는 것이면 방안 2가 싸고 충분하다.\
방안 2 사례는 일반 가이드 수준의 기록이라 실패 빈도·비용 수치는 확인되지 않았다.
