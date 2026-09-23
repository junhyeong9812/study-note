# cs/issue/kotlin/spring/path-traversal-and-data-reality — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답

<!-- 질문 1:1 대응 -->

1. API가 사용자 경로를 받아 그 파일을 읽어 준다는 것은, 입력이 곧 "무엇을 읽을지"를 결정한다는 뜻이다. `path=../../etc/passwd`처럼 `..`(상위로 이동)를 섞으면 서비스가 의도한 폴더(허용 루트) **밖으로 기어 올라가** 시스템 파일·비밀·다른 사용자 자료를 읽어낼 수 있다. 트래버설이 성립하는 조건은 ① 입력이 파일 경로에 직접 쓰이고 ② 그 경로를 허용 루트로 가두는 검사가 없는 것이다. "밖으로 기어 올라간다"는 건 상대 경로 `..`이 디렉토리 트리를 부모 방향으로 거슬러, 서버가 노출하려던 범위를 벗어난다는 뜻이다.
   > **경로 트래버설(path traversal)** — 경로 입력에 `..` 등을 섞어 허용된 디렉토리 밖의 파일에 접근하는 공격(디렉토리 트래버설).

2. **금지 목록**은 "나쁜 패턴을 나열해 막는다"(`..`·`.git`)이고, **허용 목록**은 "정규화 후 허용 루트의 prefix인지"만 통과시킨다. 이 사례의 `isSafe`는 금지 목록 성격이지만, `.md`로 끝남 + 절대경로(`/`)·홈(`~`) 시작 금지 + 경로 조각 어디에도 `..`·`.git` 없음을 함께 걸어 **트래버설의 핵심 통로(상위 이동·숨은 git 디렉토리·비md 파일)** 를 막는다. 금지 목록의 원리적 약점은 **열거하지 못한 우회**다 — 인코딩 변형(서블릿이 쿼리 파라미터를 한 번 디코딩하므로 단일 `%2e%2e`는 여기선 `..`로 바뀌어 잡히지만, 뒤에서 한 번 더 디코딩하는 경로의 이중 인코딩), 다른 구분자(Windows `\`), 유니코드 정규화, 루트 안의 심볼릭 링크 등 미처 나열 못 한 변형을 놓칠 수 있다. 그래서 방어의 정석은 "경로를 실제 파일시스템 경로로 정규화(심링크까지 해소)한 뒤 허용 루트의 하위인지 **경로 컴포넌트 단위로** 확인"하는 허용 목록이다(문자열 prefix 비교는 `/data`가 `/data2`의 prefix가 되는 함정이 있다).

3. **미뤄도 되지 않는다.** "지금은 LAN에서만 부른다"는 현재의 호출자를 근거로 삼는 것인데, 입력 검증의 기준은 호출자가 아니라 **신뢰 경계(trust boundary)** 다 — 신뢰할 수 없는 입력이 시스템으로 들어오는 지점. 이 API는 이후 front를 통해 외부 요청을 받으므로, 경계는 "backend의 경로 입력 진입점"에 그어야 한다. 경계를 "네트워크 위치"로 착각하면, 위상이 바뀌는 순간(front 노출, 방화벽 변경) 검증 공백이 그대로 취약점이 된다. 그래서 처음부터 닫는다.
   > **신뢰 경계(trust boundary)** — 신뢰 수준이 다른 두 영역의 경계. 신뢰할 수 없는 입력은 이 경계를 넘는 지점에서 검증해야 한다.

4. 코드를 고치기 전에 **데이터가 실제로 어떤 상태인지**부터 확인했다 — 서버 clone 사본의 그 파일을 `wc -c`로 재보니 0바이트였고, 같은 폴더의 ES 청크 수도 0으로 일관됐다. "버그처럼 보이는 것의 절반은 데이터 실태"란, 관측된 이상 증상(빈 본문)이 **처리 코드의 결함이 아니라 입력 자체가 원래 그런 것**인 경우가 흔하다는 뜻이다. 빈 본문의 두 가설 — (a) 코드가 내용을 잃었다, (b) 원본이 원래 비어 있었다 — 중 어느 쪽인지는 코드가 아니라 데이터를 봐야 갈린다. 인코딩 사고 경험이 (a)로 눈을 몰았지만, 실태 확인이 (b)를 가리켰다.

5. **산출물에서 원본 방향으로** 거슬러 오르는 순서다. 서버 사본(현재 관측된 것) → 로컬 원본(서버가 받아온 소스) → git 이력(그 소스의 과거). 각 단계는 "이 지점에서 내용이 사라졌나"를 배제한다. ③(rename 이전 커밋에서도 0바이트)이 결정타인 이유: 우리가 한 변경(`problem.md`→`1-question.md` rename)이 내용을 날렸을 가능성을 **이력으로 확정 배제**하기 때문이다. 우리 작업 이전에도 0바이트였다면, 시스템 어느 단계도 내용을 잃지 않았고 파일은 **원래부터 빈 자리표**였다는 결론이 확정된다 — 94개 전부가 그랬다.

6. **멀쩡한 코드를 "고치러" 갔을 것이다.** 실제로는 색인 파이프라인이 빈 파일을 "청크 0개 → 건너뜀"으로 이미 정상 처리 중이었고 API도 있는 그대로 빈 `markdown`을 돌려준 것뿐인데, 이를 버그로 오인해 손대면 (a) 존재하지 않는 결함을 좇느라 시간을 쓰고 (b) 정상 동작에 불필요한 특수 처리를 넣어 새 결함을 만들고 (c) 진짜 원인(원본이 빈 자리표)을 영영 못 본다. 데이터 실태 확인의 비용은 명령 몇 줄(`wc -c`·`git show`)인데, 건너뛴 대가는 헛수고 + 회귀 위험이다.

## 발생한 문제 / 해결 (추상 원리)

**문제 1(보안):** 사용자 경로로 파일을 서빙하는 API의 트래버설. "LAN 전용"을 근거로 검증을 미루면 위상 변화 시 그대로 취약점이 된다.
**해결 1:** 경로 진입점에서 `.md` 형식 + 절대·홈 경로 금지 + `..`·`.git` 조각 차단으로 핵심 통로를 닫는다(정석은 정규화 후 허용 루트 prefix 확인). 신뢰 경계를 "입력 진입점"에 긋는다.

**문제 2(진단):** 코드 버그처럼 보이는 증상(빈 본문)이 실제로는 데이터 실태(0바이트 원본).
**해결 2:** 코드를 만지기 전에 산출물→원본 방향(서버 사본 → 로컬 원본 → git 이력)으로 실태를 역추적한다. "우리 작업 이전에도 그랬나"를 이력으로 확정해 우리 변경을 원인에서 배제하면, 멀쩡한 코드를 고치는 헛수고를 막는다.

## 문제 구조 (추상화 코드)

### 변형 A — 외부 입력을 경로로 결합하기 전에 진입점에서 검증
① 문제 코드
```kotlin
@GetMapping("/doc")
fun getDoc(@RequestParam path: String) = ok(repo.readFile(path))       // path=../../etc/passwd → 루트 밖
```
② 고친 코드
```kotlin
object PathCheck {                                                     // 단일 검증 함수 (공용)
    fun isSafeRelativeDoc(path: String): Boolean =
        path.endsWith(".md") && !path.startsWith("/") && !path.startsWith("~") &&
        path.split("/").none { it == ".." || it == ".git" } && path.isNotBlank()
}
fun getDoc(path: String, at: String?): Response {
    if (!PathCheck.isSafeRelativeDoc(path)) return status(422)
    if (at != null && !at.matches(Regex("^[0-9a-f]{7,64}$"))) return status(422)   // 시점 인자도 hex만 (주입 차단)
    val content = try { if (at != null) repo.readFileAt(at, path) else repo.readFile(path) }
                  catch (_: FileNotFoundException) { return status(404) }        // 부재만 404, I/O 장애는 전역 500
    // ...
}
```
무엇이 깨졌나: "LAN 전용"이라는 현재 호출자를 근거로 신뢰 경계의 검증을 미룰 뻔했다.\
같은 구조(다른 언어): 커맨드로 받은 식별자를 파일명에 조합 → 저장·로드·삭제·이름변경 모든 경로에서 allowlist 검증.
```rust
fn is_safe_id(id: &str) -> bool {
    !id.is_empty() && id.len() <= 128 && id.chars().all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
}
// save / load / delete / save_name 진입부에서 거부 + 회귀 테스트(unsafe id is rejected)
```

### 변형 B — 검증이 일부 진입점에만 있음
① 문제 코드
```java
class LocalFileStorage {
    String save(InputStream in, String name) { Path p = resolveSafe(name); /* ... */ }
    InputStream load(String storagePath) {                             // 절대경로면 그대로 사용
        Path p = Path.of(storagePath).isAbsolute() ? Path.of(storagePath) : basePath.resolve(storagePath);
        return Files.newInputStream(p);
    }
    InputStream loadPartial(String storagePath, long from, long to) { return open(Path.of(storagePath)); }   // 무검증
}
```
② 고친 코드
```java
InputStream load(String storagePath)        { return Files.newInputStream(resolveSafe(storagePath)); }
InputStream loadPartial(String sp, long f, long t) { return open(resolveSafe(sp), f, t); }
// 기존에 절대경로로 저장된 데이터는 basePath로 시작하는지만 검증 (저장 형식 마이그레이션 없이)
// — normalize(또는 toRealPath) 후 Path.startsWith(basePath)로: 문자열 startsWith는 ".."·형제 prefix에 뚫린다
```
무엇이 깨졌나: 검증하지 않은 진입점이 검증한 진입점의 우회로가 됐다.\
같은 구조: 새 파일 경로 분기를 추가할 때마다 같은 방어(경로 탈출·심링크)를 반복해서 빠뜨림 — 호출 지점마다 복제한 검증은 새 분기에서 누락된다(파일시스템 접근은 단일 검증 함수를 통과하게).

### 변형 C — 코드 버그처럼 보이는 증상이 데이터 실태
① 문제 코드 (오인)
```text
증상: 비ASCII 경로 문서의 본문이 빈 값      → "인코딩/조회 버그"로 코드 수정 착수?
증상: 적재기가 매 주기 "utf-8 codec can't decode byte 0xff"   → "인코딩 버그"?
증상: 레거시 값 비교가 평문 equals로 보임 → 평문 픽스처 테스트 green, 배포 후 전건 403
```
② 고친 코드 (실태 먼저)
```text
빈 본문:    서버 사본 크기 0 → 로컬 원본 0 → 이력의 이전 커밋에서도 0   → 원본이 빈 자리표. 고칠 코드 없음
0xff:       선두 바이트 ff d8 ff e0 ... JFIF = JPEG 매직 → 데이터 묶음에 이미지가 섞여 들어옴
```
```python
def read_rows(archive):
    skipped = []
    try:
        for m in archive.members():
            if m.is_dir() or ext(m.name) in IMAGE_EXTS: skipped.append(m.name); continue   # 스킵(재시도 안 함)
            yield from parse(m)
    finally:
        if skipped: log.warning("skipped non-text members: %s", skipped)   # 뒤 멤버 예외에도 경고 보장
# 테스트: assertLogs로 경고 자체 검증 + 이미지만 든 묶음의 빈 적재 성공 경로 실행
# 실패 묶음은 추측이 아니라 기록된 오류 문구로 분류해, 이 수정이 풀 건만 매칭
```
```java
// 레거시 저장값: 실 DB 값을 한 번 조회해 보니 암호문 (복호화는 코드의 다른 루프에 숨어 있었다)
Cipher c = Cipher.getInstance("AES/CBC/PKCS5Padding");
c.init(DECRYPT_MODE, new SecretKeySpec(key, "AES"), new IvParameterSpec(key));   // 레거시 호환 IV=키 (결정적 — 약함 인지)
byte[] plain = c.doFinal(Base64.getDecoder().decode(stored));
// 평문 혼재 폴백은 BadPadding/IllegalBlockSize에만, 키 길이 검증은 생성자로 올려 기동 실패화
// (틀린 키가 폴백에 흡수돼 조용히 원문을 돌려주던 무음 오답 → fail-fast)
// 한계: 길이 검증이 막는 건 길이 오류뿐 — 길이만 맞는 틀린 키는 여전히 BadPadding → 평문 폴백으로 흡수될 수 있고,
//       드물게(약 1/256) 패딩이 우연히 맞아 쓰레기 평문이 나온다. 평문/암호문 구분은 별도 표지가 있어야 확실하다
```
무엇이 깨졌나: 에러 메시지·코드 모양으로 원인을 추측했고, 데이터의 실제 상태·표현을 보지 않았다.

### 변형 D — 스키마가 보장하지 않는 데이터 분포
① 문제 코드
```sql
SELECT r.*, m.name FROM record r JOIN master m ON m.code = r.ref_code;   -- 마스터 누락 행은 조용히 빠짐
SELECT ... WHERE term = :term;           -- 문자열 날짜 컬럼에 빈 문자열·ISO 타임스탬프 혼재 → 집계 누락
SELECT ... WHERE lang = 'vi';            -- 같은 언어가 'vi'·'vn' 두 코드로 혼재 → 한쪽 누락
```
② 고친 코드
```sql
-- 먼저 분포를 본다: 조인 실패 건수·그룹
SELECT COUNT(*) FROM record r WHERE NOT EXISTS (SELECT 1 FROM master m WHERE m.code = r.ref_code);
-- 실패 그룹별 폴백 우선순위: 원천 테이블의 이름 컬럼 직접 사용 (의미가 다른 필드는 섞지 않고 별도 필드로)
SELECT ... WHERE term REGEXP '^[0-9]{6}([0-9]{2})?$';       -- 유효 형식만, ISO 형식은 정규화해 흡수
```
```java
Set<String> nativeCodes = Set.of("vi", "vn");               // 혼재 코드 명시 흡수
// 문자열 날짜 → 컨버터, epoch 정수 날짜는 별도 매핑, dedup 키는 정수 id 기준
```
무엇이 깨졌나: 코드가 "스키마가 이렇다"는 가정 위에서 짜였고, 실측 분포(누락·혼재 형식)를 보기 전엔 조용히 빠졌다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(위 변형 A~B)은 "진입점마다 입력 문자열을 패턴(allowlist·금지 조각)으로 검증한다"이다. 같은 원리(외부 입력이 경로 경계를 넘지 못하게 · 데이터 실태 먼저)에 다른 방안이 쓰인 사례:

### 방안 1 — 경로를 입력에서 받지 않고 서버가 신뢰 id에서 도출
```rust
// 문제: 클라이언트가 저장 경로를 넘김 → 임의 경로 저장 / 파일명 `${dir}/${name}`에 `..`·구분자
save_summary(req.summary_path, body);
// 고친
let path = summaries_dir().join(format!("{}.md", validated(req.prev_id)?));   // 서버가 id에서 도출
fn sanitized_name(key: &str) -> String {                                         // 파일명이 되는 키는 치환
    key.chars().map(|c| if c.is_ascii_alphanumeric() || c == '-' || c == '_' { c } else { '_' }).collect()
}
// 메타에 저장되는 참조 id도 write 시점에 fail-fast 검증 (불안전 값이 저장돼 나중에 체인이 조용히 잘리던 것 방지)
```

### 방안 2 — canonicalize 후 루트 prefix 비교 (문자열 조각 검사의 한계 보완)
```rust
// 문제: ".." 와 빈 경로만 거부 → 절대경로("/")·심링크로 루트 밖 생성·삭제·읽기
//       검사 인자 root가 Option → root를 안 넘긴 호출부는 무검사 삭제
fn remove(path: &str, root: Option<&str>) { if let Some(r) = root { check(r, path)? } fs::remove_dir_all(path) }
// 고친: root 필수(타입으로 무검사 경로 제거) + 단일 출처 함수(중복 5벌 → 1)
fn contained_prospective(root: &Path, path: &Path) -> Result<()> {
    let root_c = fs::canonicalize(root)?;
    // 전제: 미존재 꼬리에 ".." 성분이 없어야 한다 — 없으면 "root/없는폴더/../../x"가
    //       조상 root로 판정돼 통과한 뒤, 디렉터리 생성과 함께 루트 밖을 가리킨다. 먼저 거부:
    if path.components().any(|c| c == std::path::Component::ParentDir) { return Err(outside()); }
    let mut probe = path.to_path_buf();
    let resolved = loop {                                   // 아직 없는 새 파일 → 존재하는 가장 깊은 조상
        match fs::canonicalize(&probe) {
            Ok(c) => break c,
            Err(_) => match probe.parent() { Some(p) if p != probe => probe = p.to_path_buf(), _ => return Err(unresolvable()) },
        }
    };
    if resolved.starts_with(&root_c) { Ok(()) } else { Err(outside()) }   // 컴포넌트 단위 비교
}
fn remove(path: &Path, root: &Path) -> Result<()> { contained_prospective(root, path)?; /* ... */ }
// 테스트: symlink escape is outside
```
같은 구조(파괴 연산의 동일성·조상 판정): 옮기기/덮어쓰기에서 `src == dest`·`dest.startsWith(src + "/")`를 **문자열**로 판정 → 루트 안 심링크 별칭으로 우회해 원본 자기삭제·자기복제. 백엔드에서 canonical 동일성·조상 가드(존재하는 최심 조상 canonicalize 후 나머지 꼬리 재부착)로 재검사, 프론트 문자열 검사는 1차 안내용.

### 방안 3 — 허가(면제) 판정도 문자열 glob이 아니라 canonical 경로로, 정규화 실패는 fail-closed
```sh
# 문제: "*/docs/plans/*" 면제 glob을 ".../docs/plans/../../src/x.c" 나 면제 폴더 아래 심링크로 통과
#       상대경로는 선행 "/"를 요구하는 glob과 불일치해 가드 미발화 (테스트가 절대경로만 써서 못 잡음)
# 고친
canon_file() { local f="$1"; case "$f" in /*) ;; *) f="$CWD/$f" ;; esac   # 상대경로 선결합
  realpath -m -- "$f" 2>/dev/null && return 0          # 미존재 허용 + 마지막 성분 심링크까지 해소
  realpath -- "$f" 2>/dev/null && return 0
  python3 -I -S -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$f" 2>/dev/null && return 0
  return 1; }                                           # 전부 실패 → 호출자가 차단(exit 2)
# 판정: 정규 경로의 저장소 루트를 구해 "$ROOT/" 접두 확인 후 면제 glob을 다시 적용
```
초기 "부모 디렉터리만 정규화" 구현은 마지막 성분(leaf) 심링크를 놓쳤고, `realpath -m`은 GNU 전용이라 다른 플랫폼에서 전면 차단 → 폴백 체인으로 교체.

### 방안 4 — 입력 정의역을 먼저 닫고, 정규화 방식(lexical vs physical)을 명시적으로 선택
```sh
# 문제(조상 디렉터리에서 상태 파일 찾기):
#   physical(realpath) 정규화 → 디렉터리 심링크를 따라가 외부 트리의 상태 채택
#   lexical dirname         → "a/../b" 에서 형제 a의 상태 채택
#   HOME 후행 슬래시 1개만 제거 → "//" 에서 제외 규칙 뚫림  (경계를 하나씩 막을 때마다 새 우회)
# 고친: 비정규 입력은 조상 탐색을 하지 않는다
case "$cwd" in *//*|*/./*|*/../*|*/.|*/..) echo "$cwd/.state"; return 0 ;; esac   # 정의역 밖 → 폴백
while [ "$home" != "/" ] && [ "$home" != "${home%/}" ]; do home="${home%/}"; done   # 후행 슬래시 전량 제거
# 후보는 실존 정규 파일만([ -f "$c" ] && [ ! -L "$c" ]), 성분 수 상한, realpath 미사용
```
lexical은 `..`를 잘못 풀고 physical은 심링크 너머로 신뢰 경계를 넘는다 — 어느 쪽을 쓸지는 설계 결정이다.\
여기선 심링크 공격 선행조건이 없어(식별자가 난수) realpath를 전면 제거했고, 리뷰어 두 명의 판정이 정반대였으며 직접 짠 테스트가 심링크 추종 오동작을 정상으로 박제했었다.

### 방안 5 — 경로 봉쇄는 가드레일이지 보안 경계가 아니다 (한계를 테스트로 고정)
```rust
// 실측: 우회 시도 12종(중간 심링크·/proc/self/root·절대경로·미발행 루트·..) 중 11 거부, 하드링크는 통과
//  - canonicalize는 심링크만 해소, 하드링크는 루트 안의 두 번째 이름 그 자체
//  - 검사 후 경로 "문자열"을 다시 열어 씀 → 검사(check)와 사용(use) 사이 TOCTOU
//  - 같은 소켓으로 프로세스를 띄울 수 있는 호출자는 이미 사용자 권한 셸을 가짐
#[test]
fn a_hard_link_into_a_project_is_readable_and_the_docs_say_so() { /* 통과를 고정, 실패 메시지가 문서 갱신 요구 */ }
// 접근 제어는 파일 소유권(런타임 디렉터리 0700·소켓 0600)과 원격 접근 경로 하나로
// 두 단계 검사(루트가 발행 목록에 있나 → 경로가 그 루트 아래인가), 거부 사유 분리
// 잔여: 핸들 재사용으로 TOCTOU 줄이기는 미착수로 등재
```

### 방안 6 — 압축 해제 표면: zip-slip·심링크 entry·압축 폭탄
```java
// 문제: 업로드된 압축 파일을 서버 파일시스템에 풀어야 함 (경로·크기·링크를 신뢰할 수 없음)
for (ZipEntry e : entries(zip)) {
    String name = Path.of(e.getName()).getFileName().toString();   // leaf 파일명만 사용 (zip-slip 차단)
                                                                     // leaf가 ".."인 entry는 아래 확장자 allowlist가 함께 막는다
    if (!ALLOWED_EXT.contains(ext(name))) continue;                  // 확장자 allowlist
    long n = copyWithLimit(in, target.resolve(name), perFileMax);    // 파일당 한도
    if ((total += n) > totalMax) throw new IOException("limit");     // 총량 한도 (압축 폭탄)
}
// 사용한 표준 zip API는 심링크 entry를 일반 파일로 다룬다 / 덮어쓰기 전 속성 보존 백업
```

### 방안 7 — "스키마 동일 ≠ 값 타입 동일": 드라이버가 돌려주는 실제 클래스가 계약
```java
// 문제: 같은 이름의 컬럼이 원천마다 다른 타입으로 옴(한쪽은 Long, 한쪽은 String)
Map<String, Object> row = jdbc.queryForMap(sql);          // 타입이 비어 있는 Map 경로 → 불일치 침묵 통과
// 고친: 실 DB 프로브로 타입 매트릭스 작성 → 드라이버 반환 클래스를 보존하는 typed record
static final RowMapper<Record> MAPPER = (rs, i) -> new Record(str(rs, "name"), lng(rs, "created"), /* ... */);
// typed 물화가 처음으로 불일치를 거부(픽스처의 잘못된 타입도 이때 드러남)
// 실 DB 표본 + DDL 정적 대조로 삼각측량, 어쩔 수 없는 Object 필드는 명시 목록
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 진입점 문자열 검증 | 입력이 좁은 형식(상대 경로·id)이다 | 진입점마다 호출 | 절대경로·심링크·새 진입점 누락 | 형식이 단순하고 파일시스템이 신뢰 가능 |
| 1. 서버가 경로 도출 | 클라이언트가 경로를 정할 이유가 없다 | 도출 규칙 설계 | 도출에 쓰는 id 자체 미검증 | 저장 위치가 서버 정책인 경우 |
| 2. canonical containment + 필수 인자 | 경로 입력이 불가피하다 | 파일시스템 조회·미존재 경로 처리 | 하드링크·TOCTOU | 파일 CRUD·파괴 연산 |
| 3. canonical 기반 허가 + fail-closed | 허가 규칙이 경로 모양에 걸려 있다 | 정규화 도구 이식성 | 정규화 실패 시 과차단 | 정책 훅·면제 규칙 |
| 4. 정의역 닫기 + 정규화 방식 선택 | 비정규 입력을 거부해도 된다 | 폴백 경로 설계 | 정규화 방식을 잘못 고르면 경계 이탈 | 조상 탐색·상태 위치 결정 |
| 5. 가드레일로 한정 | 같은 권한의 호출자를 막을 수 없다 | 문서·테스트 정정 | 경계로 오인하면 과신 | 같은 사용자 권한 내 IPC |
| 6. 압축 해제 한도 | 압축 파일이 외부 입력이다 | 한도·allowlist 유지 | 한도 누락 시 디스크 고갈 | 업로드 압축 처리 |
| 7. 드라이버 반환 타입 실측 | 원천마다 물리 타입이 다를 수 있다 | 프로브·매트릭스 | Map 경로에선 불일치 침묵 | 다중 원천 적재·typed 전환 |

**결론**: 경로 입력이 필요 없다면 받지 않는 게 가장 강하다(1).\
받아야 하면 문자열이 아니라 **실체(canonical)**로 판정하고 검사 함수는 하나·검사 인자는 필수로 둔다(2·3) — 단 정규화 방식 자체가 신뢰 경계를 바꾸므로 입력 정의역부터 닫는다(4).\
그래도 같은 권한의 호출자 앞에서 경로 봉쇄는 가드레일일 뿐이니 보안 경계는 권한(소유권·소켓 권한)에 둔다(5).\
데이터 쪽(C·D·7)은 한 문장이다: 코드가 가정한 형식·타입이 아니라 **실제 값을 먼저 조회**한다.
