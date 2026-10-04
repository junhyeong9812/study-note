# engineering-practice/03-version-control-and-git-internals — 버전 관리와 git 내부: 스냅샷·객체 모델·브랜치·병합 — 정리 (힌트)

## 해결하는 문제

버전 관리가 없으면 "어제 되던 코드"로 돌아갈 수 없다.

```text
  버전 관리 없이
  Fee.java  ── 덮어쓰기 ──> Fee.java  ── 덮어쓰기 ──> Fee.java
  (어제 되던 것)            (누가 왜 바꿨나?)            (둘이 동시에 고치면 한쪽이 사라짐)
```

- 버전 관리가 답하는 질문은 세 가지다.
  - **언제 무엇이었나**: 과거의 어느 시점 상태든 그대로 꺼낸다.
  - **누가 왜 바꿨나**: 변경마다 작성자·시각·메시지가 붙는다.
  - **동시에 고친 것을 어떻게 합치나**: 갈라진 작업을 병합한다.
- SWE@G 16장(Version Control and Branch Management, Titus Winters)은 여기에 하나를 더한다. 조직에는 **"하나의 저장소, 하나의 브랜치"가 최종 기준(source of truth)** 으로 정해져 있어야 한다. 아니면 어떤 변경이 들어갔는지조차 분명하지 않다.

쉬운 예: 문서 파일을 `보고서_최종.docx`, `보고서_최종2.docx`, `보고서_진짜최종.docx`로 복사해 두는 습관이다.
- 복사본마다 "그 시점 전체"가 들어 있다. 이것이 **스냅샷**이다.
- 그런데 어느 것이 어느 것에서 나왔는지, 같은 내용이 몇 번 중복 저장됐는지는 모른다.

똑같은 구조다.\
git도 커밋마다 프로젝트 전체의 스냅샷을 남긴다. 다만 ① 같은 내용은 한 번만 저장하고 ② 각 스냅샷이 부모를 가리켜 계보가 남는다. 이 두 가지를 **내용의 해시를 이름으로 쓰는 것**(콘텐츠 주소)으로 해결한다.

실무 예:
- 배포 후 장애 → "직전 배포 커밋으로 되돌리기"가 몇 초 안에 된다.
- 동료가 `push --force`로 원격 `main`을 덮어써 내 커밋이 원격 이력에서 사라진다(장애 1).
- 병합 충돌을 "내 것으로" 통째로 골라 동료의 버그 수정이 소리 없이 사라진다(장애 2).

## 동작·원리

### 1. 객체 네 종류와 Merkle DAG

```text
  refs/heads/main ──> commit c2e1cb ──parent──> commit 66a1b1
                         │ tree                     │ tree
                         v                          v
                      tree f0dd3b                tree d70b48
                       ├─ a.txt ─> blob ce0136 <──── a.txt   (같은 내용 → 같은 객체, 공유)
                       └─ src/ ──> tree f17b8d    └─ src/ ─> tree dfe677
                                    ├─ b.txt ─> blob ce0136   ├─ b.txt ─> blob ce0136
                                    └─ c.txt ─> blob (새것)    └─ c.txt ─> blob cc628c
```

- git 저장소의 핵심은 **객체**와 **참조**다(Pro Git 10.2 Git Objects, 10.3 Git References). 그 밖에 `.git`에는 스테이징 영역(`index`)·`HEAD`·`config`·hooks 등도 있다(Pro Git 10.1).
  - *블롭(blob)*: 파일 내용 바이트. 파일 이름은 들어 있지 않다.
  - *트리(tree)*: 디렉터리 한 층. "모드·종류·해시·이름" 줄의 목록이다.
  - *커밋(commit)*: 루트 트리 해시 + 부모 커밋 해시(0개 이상) + 작성자·커미터·메시지.
  - *태그 객체(annotated tag)*: 다른 객체를 가리키는 이름표 + 메시지(서명 가능).
- 객체 ID = **"종류 크기\0" + 내용의 해시**다(Pro Git 10.2). 기본은 SHA-1(40자 16진).
  - *콘텐츠 주소(content-addressed)*: 내용으로 이름을 정하는 방식. 내용이 같으면 이름이 같다. 내용이 1바이트라도 다르면 사실상 이름이 다르다 — 해시 충돌이 없다는 전제다(SHA-1은 2017년 실제 충돌 쌍이 공개됐다 — Google·CWI <https://security.googleblog.com/2017/02/announcing-first-sha1-collision.html>, 아래 충돌 탐지).
- 커밋은 트리 해시를, 트리는 하위 트리·블롭 해시를 담는다. 그래서 커밋 해시 하나가 **아래 전체**를 보증한다.
  - *Merkle DAG*: 노드가 자식들의 해시를 담아, 루트 해시가 전체 내용을 대표하는 방향 비순환 그래프. 기초는 [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md).
    - 흔한 오해: "git은 변경분(diff)을 저장한다." 논리 모델은 커밋마다 **전체 스냅샷**이다. 용량을 줄이는 델타 압축은 packfile 단계(Pro Git 10.4)의 저장 최적화일 뿐, 객체 모델과는 별개다.

### 실험: 객체를 직접 열고 해시를 다시 계산한다

일회용 저장소에서 `a.txt`·`src/b.txt`(둘 다 `hello`)와 `src/c.txt`(`world`)를 커밋했다(날짜 고정이라 해시가 재현된다).

(실험, git 2.43.0 / Ubuntu, 2026-10-05)

```text
== 루트 트리
100644 blob ce013625030ba8dba906f756967f9e9ca394464a	a.txt
040000 tree dfe6779b0a6c3e960199b85a6e66629c6011ce2b	src
== src 트리
100644 blob ce013625030ba8dba906f756967f9e9ca394464a	b.txt
100644 blob cc628ccd10742baea8241c5924df992b5c019f71	c.txt
== 객체 수(블롭 2 = hello·world, 트리 2, 커밋 1)
count: 5
== 블롭 해시 재계산
ce013625030ba8dba906f756967f9e9ca394464a                ← git hash-object a.txt
ce013625030ba8dba906f756967f9e9ca394464a  -             ← printf 'blob 6\0hello\n' | sha1sum
== 한 글자 바꾸면
4b32b59cf6f008703c95a6d2284f027e6ef86b54
== 두 번째 커밋: c.txt만 수정 → 바뀐 객체만 새로 생김
objects before=5 after=9
```

- `a.txt`와 `src/b.txt`는 이름·경로가 달라도 **블롭 하나**(`ce0136…`)를 함께 가리킨다. 파일 3개인데 블롭은 2개다.
- `c.txt`만 고치면 새 객체는 4개다: 새 블롭, 새 `src` 트리, 새 루트 트리, 새 커밋. `a.txt` 블롭은 그대로 재사용된다.
  - 바뀐 잎에서 루트까지 **경로 위의 노드만** 새로 만든다. [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)의 경로 복사와 같은 구조다.
- 커밋 해시도 같은 규칙이다. `commit <크기>\0` + `git cat-file commit HEAD` 출력의 SHA-1이 `git rev-parse HEAD`와 같았다(`c2e1cb47…`).
- `git init --object-format=sha256` 저장소에서는 같은 `hello\n` 블롭이 64자 SHA-256 ID(`2cf8d83d…`)를 받았다. `sha256sum`으로 다시 계산한 값과 같았다.
  - git 2.43 `git init` 문서: 값은 `sha1`과 (활성화된 경우) `sha256`, 기본은 `sha1`. SHA-256 저장소와 SHA-1 저장소는 **아직 서로 호환되지 않는다**.
- SHA-1 충돌 공격 대비: git 2.13부터 충돌 시도를 탐지하는 SHA-1 구현(Marc Stevens·Dan Shumow)이 기본이다(2.13.0 릴리스 노트).

### 2. 참조 — 브랜치는 "커밋을 가리키는 이름표"일 뿐

```text
  .git/refs/heads/main     = c2e1cb...   ← 브랜치 = 40자 ID 한 줄짜리 포인터 파일(또는 packed-refs 한 줄)
  .git/HEAD                = ref: refs/heads/main   ← 지금 어느 브랜치 위에 있나
  .git/logs/HEAD (reflog)  = 이 포인터가 언제 어디서 어디로 움직였나

  새 커밋 = 객체 추가 + 이름표를 앞으로 한 칸
  main ─────────────┐
                    v
  A ── B ── C ── D(새)
```

- *참조(ref)*: 객체 ID에 붙인 사람이 읽는 이름. 브랜치(`refs/heads/…`)·원격 추적 브랜치(`refs/remotes/…`)·태그(`refs/tags/…`).
- *HEAD*: 현재 체크아웃한 위치. 보통 브랜치를 가리키는 **심볼릭 참조**다.
- 그래서 브랜치를 만드는 비용은 파일 하나다. 브랜치를 지워도 커밋 객체는 바로 사라지지 않는다. 어떤 참조에서도 닿지 않게 될 뿐이다.
  - *도달 불가(unreachable) 객체*: 어떤 참조·reflog에서도 따라갈 수 없는 객체. `git gc`가 일정 기간 뒤 지운다.
- *reflog*: 참조가 움직인 기록. "1시간 전 `main`은 어디였나"에 답한다(git-config `core.logAllRefUpdates`).
  - 기본값(git 2.43 git-config 문서): 작업 트리가 있는 저장소에서는 **켜짐**, **bare 저장소에서는 꺼짐**. GitHub 같은 서버 쪽 원격은 보통 bare다.
  - 만료 기본값(git-gc 문서): `gc.reflogExpire` 90일, `gc.reflogExpireUnreachable`(현재 끝에서 닿지 않는 항목) 30일. 도달 불가 객체 정리는 `gc.pruneExpire` 기본 2주.
    - 흔한 오해: "reflog가 있으니 원격에서도 복구된다." reflog는 **각 저장소에 로컬**이다. 남의 클론, 서버의 bare 저장소에는 내 reflog가 없다.

### 3. 3-way 병합 — 공통 조상이 판정 기준

```text
            base (merge-base)
           /                 \
      ours (main)         theirs (fix)
           \                 /
            병합 결과 = base에서 각자 바꾼 것을 둘 다 적용

  줄 단위 판정
  ┌──────────┬──────────┬──────────┬─────────────────────┐
  │ base     │ ours     │ theirs   │ 결과                │
  ├──────────┼──────────┼──────────┼─────────────────────┤
  │ X        │ X        │ Y        │ Y  (theirs만 바꿈)  │
  │ X        │ Y        │ X        │ Y  (ours만 바꿈)    │
  │ X        │ Y        │ Y        │ Y  (같게 바꿈)      │
  │ X        │ Y        │ Z        │ 충돌 — 사람이 결정  │
  └──────────┴──────────┴──────────┴─────────────────────┘
```

- 두 버전만 비교하면 "누가 바꿨나"를 모른다. 공통 조상(base)이 있어야 "한쪽만 바꿨으면 바꾼 쪽을 택한다"가 가능하다.
  - *merge-base*: 두 커밋의 가장 가까운 공통 조상(best common ancestor). 커밋 DAG의 **최소 공통 조상(LCA)** 에 해당한다. `git merge-base A B`로 본다. 교차 병합 이력에서는 여러 개일 수 있다(git-merge-base 문서) — `--all`로 모두 본다.
  - *3-way merge*: base·ours·theirs 세 버전으로 줄 단위 변경을 합치는 병합. 줄 단위로는 두 쪽이 **같은 영역**을 다르게 바꿨을 때 충돌이다(git-merge 문서 "HOW CONFLICTS ARE PRESENTED"). 그 밖에 수정/삭제, 이름 바꾸기, 파일/디렉터리, 바이너리 파일 양쪽 변경 같은 파일 단위 충돌도 있다(git-merge-tree 문서 "MISTAKES TO AVOID").
- 기본 전략은 `ort`다. git 2.34 릴리스 노트: "The `ort` strategy is used instead of `recursive` as the default". merge-strategies 문서는 `recursive`가 v0.99.9k~v2.33.0의 기본이었고 v2.50.0부터 `ort`의 별칭이 됐다고 적는다.
  - 공통 조상이 여럿이면(교차 병합, criss-cross) `ort`는 공통 조상들을 먼저 병합한 **가상 base 트리**를 만들어 3-way의 기준으로 쓴다(merge-strategies 문서).
- 충돌 표시 형식: 기본은 ours/theirs만 보인다. `merge.conflictStyle=diff3`(또는 `zdiff3`)이면 `|||||||` 아래에 **base도 보여 준다**. base가 보이면 "양쪽이 각각 무엇을 바꾸려 했나"를 판단할 수 있다.
- **충돌은 텍스트 판정일 뿐이다.** 텍스트가 겹치지 않아도 의미가 깨질 수 있다(한쪽이 함수 이름을 바꾸고 다른 쪽이 옛 이름을 새로 호출). 이것은 [04-branching-strategies](../04-branching-strategies/2-summary.md)의 의미 충돌 실험에서 다룬다.

### 실험: 충돌을 "내 것"으로 통째로 골라 버그 수정을 잃는다

`main`은 수수료율을 3 → 2로, `fix`는 같은 줄 근처에 "음수 금액이면 0" 수정을 넣었다. `merge.conflictStyle=diff3`로 병합했다.

(실험, git 2.43.0, 2026-10-05)

```text
== 충돌 파일 (diff3 스타일: ours / base / theirs)
class Fee {
    static long fee(long amount) {
<<<<<<< HEAD
        long rate = 2;  // 프로모션
||||||| b4794c2
        long rate = 3;
=======
        long rate = 3;  // 3%
        if (amount <= 0) return 0;   // 음수 금액 버그 수정
>>>>>>> fix
        return amount * rate / 100;
    }
    static String label() { return "수수료"; }
}
```

- `label()`은 `main`만 바꿨으므로 충돌 없이 이미 반영됐다. 충돌은 `rate` 줄 주변 한 덩어리뿐이다.
- 여기서 `git checkout --ours Fee.java && git add Fee.java && git commit`으로 해결했다.

```text
== 컴파일·충돌 표식 없음 → 겉으로 정상
0
== 병합 커밋의 일반 diff (첫 부모 기준) — 비어 있음
(끝)
== 버그 수정 줄이 main에 있나
0
== 그런데 git log 는 fix 커밋을 main 이력에 포함한다
5bf24cf merge fix
eae51a1 promo: rate 2, label
05c9a37 fix: negative amount
b4794c2 base
== fix 브랜치를 다시 병합하면?
Already up to date.
```

- 관찰
  - 이력에는 `fix: negative amount`가 `main`에 들어간 것으로 나온다. 코드에는 그 줄이 없다.
  - `fix`를 다시 병합해도 "Already up to date"다. git은 이미 병합된 커밋으로 본다.
  - 첫 부모 기준 diff는 비어 있다. 병합 커밋을 `git show`나 일반 diff로 리뷰하면 **아무것도 안 보인다**.
- 탐지: `git show --remerge-diff`(git 2.36+)는 "기계적 병합 결과(충돌 표식 포함) 대비 실제 기록된 결과"를 보여 준다.

```text
== git show --remerge-diff : 자동 병합 결과 대비 사람이 한 해결
-<<<<<<< eae51a1 (promo: rate 2, label)
         long rate = 2;  // 프로모션
-||||||| b4794c2
-        long rate = 3;
-=======
-        long rate = 3;  // 3%
-        if (amount <= 0) return 0;   // 음수 금액 버그 수정
->>>>>>> 05c9a37 (fix: negative amount)
```

- `-        if (amount <= 0) return 0;` 줄이 "해결하면서 버린 것"으로 드러난다. 두 번째 부모 기준 `git diff HEAD^2 HEAD`에서도 그 줄이 `-`로 보였다.
- 복구는 `git cherry-pick fix`로 수정 커밋을 다시 적용하고, 이번에는 두 의도(요율 2 + 음수 방어)를 모두 살려 해결했다. 결과:

```text
        long rate = 2;  // 프로모션
        if (amount <= 0) return 0;   // 음수 금액 버그 수정
        return amount * rate / 100;
```

## 쓰이는 자료구조·알고리즘

| 자료구조·알고리즘 | git 안의 자리 | 링크 |
|---|---|---|
| Merkle DAG·콘텐츠 주소 | 커밋 → 트리 → 블롭, 해시가 곧 이름 | [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) |
| 영속 자료구조(경로 복사) | 바뀐 경로의 트리만 새로 만들고 나머지 공유 | [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md) |
| 암호 해시(SHA-1·SHA-256) | 객체 ID, 무결성 확인 | security 영역 [README](../../security/README.md)(관련 주제 미작성) |
| 최소 공통 조상(LCA) | `git merge-base` — 3-way 병합의 base | — |
| 최장 공통 부분수열 / Myers diff | `git diff`, 병합의 줄 단위 비교 | [algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md) |
| 추가 전용 로그 | reflog — 참조 이동 기록 | — |
| 그래프 도달 가능성(마크 앤 스윕) | `git gc`·`git fsck --unreachable` | — |

- 해시가 이름이므로 **두 저장소가 같은 ID를 가지면 내용이 같다**고 본다. 그래서 `fetch`는 상대에게 없는 객체만 주고받는다(Pro Git 10.6 Transfer Protocols).
- 커밋 DAG에서 "A가 B의 조상인가"(`git merge-base --is-ancestor`)는 fast-forward 판정·force push 판정의 기초다.
  - *fast-forward*: 원격 브랜치 끝이 내 커밋의 조상이라 포인터만 앞으로 옮기면 되는 갱신. `push`는 기본적으로 fast-forward만 허용한다(git-push 문서).

## 적용 — 풀어나가는 법

### 1. 상태를 객체 수준에서 읽는다

```bash
git cat-file -t <id>          # 종류: blob/tree/commit/tag
git cat-file -p HEAD          # 커밋 본문: tree, parent, author, message
git cat-file -p 'HEAD^{tree}' # 루트 트리
git rev-parse HEAD~2          # 이름 → 객체 ID
git merge-base main feature   # 3-way 병합의 base
git log --graph --oneline --all
```

같은 계산을 Java로 하면 "git ID는 내용의 해시"라는 주장을 직접 확인할 수 있다.

```java
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;

public class GitHash {
    // git 블롭 ID = 해시("blob " + 바이트 수 + "\0" + 내용)
    static String blobId(byte[] content, String algo) throws Exception {
        MessageDigest md = MessageDigest.getInstance(algo);
        md.update(("blob " + content.length + "\0").getBytes(StandardCharsets.US_ASCII));
        md.update(content);
        return HexFormat.of().formatHex(md.digest());
    }
    public static void main(String[] args) throws Exception {
        byte[] hello = "hello\n".getBytes(StandardCharsets.UTF_8);
        System.out.println("SHA-1   " + blobId(hello, "SHA-1"));
        System.out.println("SHA-256 " + blobId(hello, "SHA-256"));
    }
}
```

(실험, eclipse-temurin:21-jdk 컨테이너 OpenJDK 21.0.12, 2026-10-05)

```text
SHA-1   ce013625030ba8dba906f756967f9e9ca394464a
SHA-256 2cf8d83d9ee29543b34a87727421fdecb7e3f3a183d337639025de576db9ebb4
```

- `git hash-object`(SHA-1 저장소)·SHA-256 저장소의 결과와 같다.
- 바이트 수는 **문자 수가 아니라 바이트 수**다. 한글 파일이면 UTF-8 바이트로 센다.

### 2. 공유 브랜치의 이력은 고쳐 쓰지 않는다 — 꼭 해야 하면 조건부로

- 강제 push가 필요한지는 "원격 끝이 새 끝의 조상인가"(fast-forward인가)로 정해진다. 이미 push한 커밋을 rebase·amend·reset으로 바꿨으면 fast-forward가 아니라 강제가 필요하다. 이런 고쳐 쓰기는 자기 브랜치에서만 하고, 그때도 `--force` 대신 조건부 강제를 쓴다.

```bash
git push --force-with-lease --force-if-includes origin my-branch
```

- *--force-with-lease*: 원격 참조가 **내 원격 추적 브랜치 값과 같을 때만** 덮어쓴다. 그사이 누가 push했으면 거부한다(git-push 문서).
- *--force-if-includes*(git 2.30+): 원격 추적 브랜치의 끝이 **내 로컬 브랜치 reflog 항목 중 하나에서 도달 가능할 때만**(그 항목이거나 그 조상일 때) 허용한다(git-push 문서). 즉 "fetch만 하고 반영은 안 한" 상태를 거부한다.
  - git-push 문서의 경고: 값 없이 쓴 `--force-with-lease`는 백그라운드 `git fetch`(에디터·cron)와 만나면 보호가 사라진다. 원격 추적 값이 몰래 최신으로 바뀌기 때문이다.
- 저장소 쪽 방어(호스팅 기능): 보호 브랜치에서 force push 금지. 그러면 개인 실수가 공유 이력 유실로 번지지 않는다.

### 3. 병합 충돌은 base를 보고, 결과를 다시 확인한다

```bash
git config merge.conflictStyle zdiff3   # base를 함께 표시 (zdiff3는 git 2.35+, 2.35.0 릴리스 노트)
git merge feature
git diff                                # 충돌 덩어리만
git log --merge -p -- Fee.java          # 충돌 파일을 건드린 양쪽 커밋
# 해결 후
git show --remerge-diff HEAD            # 기계적 병합 대비 내가 무엇을 바꿨나
```

- 통째로 고르는 명령(`checkout --ours/--theirs`, `merge -s ours`, `-X ours`)은 적어도 충돌한 곳에서 **양쪽 의도 중 하나를 버리는 결정**이다(범위는 명령마다 다르다).
  - `-s ours` 전략: 상대 브랜치 변경을 **전부** 무시한다. `-X ours` 옵션: **충돌한 덩어리만** 내 쪽으로 정하고 충돌 안 한 상대 변경은 반영한다(merge-strategies 문서). 단 바이너리 파일은 덩어리로 나눌 수 없어 파일 전체를 내 쪽에서 가져온다. 이름이 비슷해 혼동하기 쉽다.
  - `checkout --ours <파일>`은 파일 전체를 내 버전으로 한다. 같은 파일 안 상대 쪽 **비충돌** 수정도 사라진다. 실험(git 2.43.0)에서 theirs가 `rate` 줄(충돌)과 `label` 줄(비충돌)을 고쳤을 때, `checkout --ours`의 결과는 `label=fee`(theirs 수정 소실), `-X ours`의 결과는 `label=FEE-fixed`(반영)였다.
- 해결 뒤 빌드·테스트를 돌린다. 충돌이 없던 파일도 의미 충돌이 있을 수 있다.

### 4. 사라진 것을 찾는 순서

```bash
git reflog                     # 내 HEAD가 지나온 커밋 (로컬, 기본 90/30일)
git reflog show origin/main    # 원격 추적 브랜치가 fetch로 움직인 기록
git fsck --unreachable --no-reflogs | grep commit   # 참조·reflog 어디에도 없는 커밋
git branch rescue <id>         # 찾은 커밋에 이름표를 붙여 gc 대상에서 뺀다
```

## 장애 시나리오와 대처

### 1. force push로 동료 커밋이 원격에서 사라진다 (⚠ 커리큘럼)

(실험, git 2.43.0, 일회용 bare 원격 + 클론 셋, 2026-10-05)

```text
== 일반 push
 ! [rejected]        main -> main (fetch first)
== --force-with-lease (fetch 전: 원격이 내가 마지막으로 본 값과 다름)
 ! [rejected]        main -> main (stale info)
== --force
 + 0fdcdac...ef56ee6 main -> main (forced update)
== origin main 이력
ef56ee6 alice: feature
8578c7d base
== bare 원격의 core.logAllRefUpdates
(미설정 → bare 기본: reflog 안 씀)
origin.git/logs 없음
== Bob 쪽: 로컬 main과 reflog에 여전히 있음
0fdcdac main@{0}: commit: bob: fix
== Carol: force push 뒤에 클론 → bob 커밋을 볼 길이 없음
ef56ee6 alice: feature
8578c7d base
fatal: Not a valid object name 0fdcdac
== origin 객체 저장소에는 아직 있음(도달 불가, gc 전)
commit
unreachable commit 0fdcdacc757e919a3a2171b5e38ecb19c77a28ba
```

- **현상**: 어제 병합된 동료의 수정이 `main`에서 사라졌다. 새로 클론한 사람은 그 커밋을 아예 받지 못한다.
- **보이는 형태**: push 출력의 `+ 0fdcdac...ef56ee6 main -> main (forced update)`. 동료 쪽 `git status`가 `[ahead 1, behind 1]`.
- **원인**: fast-forward가 아닌 갱신을 `--force`로 밀었다. 원격은 bare라 reflog가 없다. 도달 불가가 된 커밋은 새 클론에 전달되지 않는다.
- **대처**
  - 커밋을 아직 가진 사람(작성자 로컬 브랜치·reflog, 또는 fetch만 해 둔 사람의 `origin/main` reflog)이 다시 push하거나 병합한다.
  - 서버 객체 저장소에는 gc 전까지 도달 불가 객체로 남아 있을 수 있다(실험의 `unreachable commit`). 호스팅 서비스에서는 직접 접근이 어려우니 관리 기능·지원에 의존한다 `[?]`(서비스마다 다름).
  - 재발 방지: 보호 브랜치 force push 금지, `--force-with-lease --force-if-includes`.

### 2. 병합 충돌 오해결로 코드가 조용히 사라진다 (⚠ 커리큘럼)

- **현상**: "고쳤던 버그가 재발했다." 이력에는 수정 커밋이 분명히 `main`에 들어가 있다.
- **보이는 형태**: `git log`에는 수정 커밋이 보이는데 `git grep`으로 그 코드가 없다. 수정 브랜치를 다시 병합하면 `Already up to date.`. 병합 커밋의 일반 diff는 비어 있다.
- **원인**: 충돌을 `--ours`/`--theirs`로 통째로 골랐거나, 편집기에서 한쪽 덩어리를 지웠다. git은 해결 결과를 그대로 믿는다.
- **대처**
  - 찾기: `git show --remerge-diff <merge>`(2.36+), `git diff <merge>^2 <merge>`, `git log -m -S '<사라진 코드>'`(기본 `log -S`는 병합 커밋의 diff를 보지 않는다 — 실험에서 `-m`을 붙여야 `merge fix`가 나왔다).
  - 고치기: 수정 커밋을 `cherry-pick`해 다시 적용하고 양쪽 의도를 모두 살린다. 회귀 테스트를 함께 추가해 다음에는 CI가 막게 한다.
  - 예방: `merge.conflictStyle=diff3/zdiff3`로 base를 보며 해결, 해결 후 테스트, 큰 충돌은 두 작성자가 함께 해결.

### 3. `fetch` 뒤 `--force-with-lease`가 그냥 통과한다

```text
== 함정: fetch 한 뒤의 --force-with-lease 는 통과한다
-- alice: fetch 후 --force-with-lease --force-if-includes
 ! [rejected]        main -> main (remote ref updated since checkout)
-- alice: fetch 후 --force-with-lease
 + 0fdcdac...ef56ee6 main -> main (forced update)
```

- **현상**: "안전한 강제 push"를 썼는데도 동료 커밋이 사라졌다.
- **원인**: lease의 기대값은 원격 추적 브랜치다. fetch(수동이든 IDE 백그라운드든)가 그 값을 최신으로 바꾸면 "원격 = 내가 본 값"이 성립해 통과한다. 내가 그 커밋을 실제로 반영했는지는 보지 않는다.
- **대처**: `--force-if-includes`를 함께 쓴다(실험에서 `remote ref updated since checkout`로 거부). 또는 `--force-with-lease=main:<기대 ID>`로 기대값을 명시한다.

### 4. `reset --hard`·브랜치 삭제 뒤 "커밋이 없어졌다"

- **현상**: `git reset --hard origin/main` 뒤 로컬 커밋이 안 보인다.
- **원인**: 커밋이 지워진 게 아니라 이름표가 옮겨졌다. 객체는 남아 있고 reflog가 가리킨다.
- **대처**: `git reflog`에서 ID를 찾아 `git reset --hard HEAD@{1}` 또는 `git branch rescue <id>`. 실험에서 `HEAD@{1}`로 `bob: fix`를 되살렸다. 기본 만료(도달 불가 reflog 30일, 객체 prune 2주 유예) 안에 해야 한다.

## 핵심 문장

- git 커밋은 변경분이 아니라 프로젝트 전체의 스냅샷이며, 같은 내용은 같은 해시의 객체 하나로 공유된다.
- 객체 ID는 "종류 크기\0 + 내용"의 해시라서, 커밋 해시 하나가 그 아래 트리·블롭 전체를 보증한다(Merkle DAG).
- 브랜치는 커밋을 가리키는 이름표이고, reflog는 그 이름표의 이동 기록이며 저장소마다 로컬이다(bare 원격은 기본으로 안 남긴다).
- 3-way 병합은 merge-base를 기준으로 "한쪽만 바꾼 것"을 자동으로 고르고, 같은 영역을 둘 다 바꿨을 때(그리고 수정/삭제·이름 바꾸기 같은 파일 단위 충돌일 때) 사람에게 묻는다.
- 충돌 해결 결과는 git이 그대로 믿으므로, 한쪽을 통째로 고르면 이력에는 병합됐는데 코드에는 없는 수정이 생긴다 — `--remerge-diff`로 찾는다.
- 공유 브랜치는 고쳐 쓰지 않고, 강제 push가 필요하면 `--force-with-lease --force-if-includes`와 보호 브랜치로 막는다.

## 관련 주제·근거

- 선행
  - [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md) — 해시 트리, 루트 해시로 전체 보증
  - [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md) — 경로 복사·구조 공유
- 후속·연결
  - [04-branching-strategies](../04-branching-strategies/2-summary.md) — 브랜치를 얼마나 오래 두나, 의미 충돌
  - [05-code-review](../05-code-review/2-summary.md) — 병합 전 리뷰, `range-diff`로 재리뷰
  - [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md) · [07-build-systems-and-reproducibility](../07-build-systems-and-reproducibility/2-summary.md)
  - [algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md) — diff = LCS, Myers
  - [software-design/53-code-forensics-hotspots](../../software-design/53-code-forensics-hotspots/2-summary.md) — git 이력을 분석 데이터로 쓰기
- 교재·문서
  - Pro Git 2판 10장 Git Internals — 10.1 Plumbing and Porcelain, 10.2 Git Objects(블롭 헤더 `blob <size>\0`, zlib 압축, `.git/objects/xx/…`), 10.3 Git References, 10.4 Packfiles, 10.6 Transfer Protocols, 10.7 Maintenance and Data Recovery <https://git-scm.com/book/en/v2/Git-Internals-Git-Objects>
  - git 문서(2.43 설치본 man·git-scm.com/docs): git-push(`--force-with-lease`, `--force-if-includes`, 백그라운드 fetch 경고), merge-strategies(`ort` 기본, 가상 merge base, `-s ours` vs `-X ours`, `recursive`는 v2.50.0부터 별칭), git-merge "HOW CONFLICTS ARE PRESENTED"(diff3·zdiff3), git-gc(`gc.reflogExpire` 90일·`gc.reflogExpireUnreachable` 30일·`gc.pruneExpire` 2주), git-config `core.logAllRefUpdates`(bare 기본 false), git-init `--object-format`
  - git 릴리스 노트: 2.13.0(충돌 탐지 SHA-1 기본), 2.29.0(SHA-256 지원 실험적, 상호 운용 없음), 2.30.0(`--force-if-includes`), 2.34.0(`ort` 기본), 2.35.0(zdiff3), 2.36.0(`--remerge-diff`) — `/usr/share/doc/git/RelNotes/`
  - SWE@G 16장 "Version Control and Branch Management"(Titus Winters) — source of truth, one-version rule <https://abseil.io/resources/swe-book/html/ch16.html>
  - SWEBOK v4 Software Configuration Management KA(장 번호 `[?]`)
- 실험 목록(모두 일회용 저장소, author `Example <ex@example.invalid>`, 커밋 날짜 고정, git 2.43.0 / Ubuntu 호스트)
  - 객체 열기·해시 재계산·같은 내용 공유·바뀐 경로만 새 객체(5 → 9개)·커밋 해시 재계산·SHA-256 저장소
  - Java `MessageDigest`로 블롭 ID 재계산(eclipse-temurin:21-jdk, `--network none`)
  - bare 원격 + 클론 셋: 일반 push 거부, lease 거부(stale info), `--force` 유실, 새 클론에 전달 안 됨, 서버에 도달 불가 객체 잔존, reflog 복구, fetch 뒤 lease 통과 vs `--force-if-includes` 거부
  - 같은 파일에 충돌·비충돌 수정이 섞였을 때 `checkout --ours` vs `-X ours` 결과 비교
  - diff3 충돌 → `--ours` 해결로 수정 소실 → `Already up to date` → `--remerge-diff`·`HEAD^2` diff로 탐지 → cherry-pick 복구
  - 같은 병합에서 `git log -S` vs `git log -m -S` — `-m`을 붙여야 수정을 버린 병합 커밋이 나온다
