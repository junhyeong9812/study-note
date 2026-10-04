# engineering-practice/03-version-control-and-git-internals — 정답

## 정답

### 1. 스냅샷인데 크기가 폭증하지 않는 이유

- 커밋은 루트 트리를 가리키고, 트리는 파일·하위 트리를 해시로 가리킨다. 논리적으로는 매번 전체 스냅샷이다.
- 크기를 막는 두 성질
  - **콘텐츠 주소**: 같은 내용은 같은 ID라서 객체 하나를 공유한다. 바뀌지 않은 파일·디렉터리는 이전 객체를 그대로 가리킨다.
  - **경로 복사(Merkle DAG)**: 파일 하나가 바뀌면 그 파일 블롭과 루트까지 경로 위의 트리, 새 커밋만 새로 생긴다.
- 그 위에 packfile의 델타 압축(Pro Git 10.4)이 저장 공간을 더 줄인다. 이것은 저장 최적화이지 객체 모델이 diff라는 뜻이 아니다.

### 2. 블롭 ID

- `"blob 6\0hello\n"`의 SHA-1이다(Pro Git 10.2). 실험에서 `git hash-object`와 `printf 'blob 6\0hello\n' | sha1sum`이 모두 `ce013625030ba8dba906f756967f9e9ca394464a`였다. Java `MessageDigest`로 계산해도 같았다.
- 블롭에는 파일 이름이 없다. 이름·경로는 트리 항목에 있다. 그래서 이름을 바꾸거나 복사해도 **블롭 ID는 그대로**이고, 트리 ID만 바뀐다.
- 크기는 바이트 수다(UTF-8 한글은 글자당 여러 바이트).

### 3. 객체 수

- 첫 커밋 직후 5개: 블롭 2(hello 공유 1 + world 1), 트리 2(루트·src), 커밋 1. 실험 `count: 5`.
- `c.txt`만 고치면 새 객체 4개 → 9개(`objects before=5 after=9`).
  - 새 블롭(`world!`), 새 `src` 트리, 새 루트 트리, 새 커밋(부모 = 첫 커밋).
  - `a.txt`·`b.txt`의 블롭 `ce0136…`은 재사용된다.

### 4. 3-way 병합

```text
        base = merge-base(ours, theirs) = 두 커밋의 최소 공통 조상(LCA, 여럿일 수 있다)
       /    \
    ours    theirs
       \    /
       결과
```

| base | ours | theirs | 결과 |
|---|---|---|---|
| X | X | Y | Y (theirs만 바꿈) |
| X | Y | X | Y (ours만 바꿈) |
| X | Y | Y | Y (같게 바꿈) |
| X | Y | Z | 충돌 |

- 줄 단위로는 같은 영역을 양쪽이 다르게 바꿨을 때 충돌이다(git-merge 문서). 수정/삭제·이름 바꾸기·바이너리 양쪽 변경 같은 파일 단위 충돌도 따로 있다(git-merge-tree 문서). 실험에서 `label()`은 main만 바꿔 자동 반영됐고, `rate` 줄 주변만 충돌했다.
- 공통 조상이 여럿이면 `ort`(git 2.34+ 기본)는 조상들을 병합한 가상 base를 쓴다.

### 5. `--force-with-lease`

- fetch 전: 원격 `main`이 내 원격 추적 브랜치(`origin/main`) 값과 다르므로 거부된다. 실험 출력 `! [rejected] main -> main (stale info)`.
- fetch 후: 원격 추적 브랜치가 최신이 되어 "원격 = 내가 본 값"이 성립 → **통과**하고 동료 커밋을 덮어쓴다. 실험 `+ 0fdcdac...ef56ee6 main -> main (forced update)`.
- `--force-if-includes`(git 2.30+)를 더하면 원격 추적 끝(fetch로 받은 동료 커밋)이 내 로컬 브랜치 reflog의 어느 항목에서도 도달할 수 없으므로 거부된다. 실험 `(remote ref updated since checkout)`.
- git-push 문서도 값 없이 쓴 lease는 백그라운드 fetch와 만나면 보호가 사라진다고 경고한다.

### 6. reflog의 범위

- 복구할 수 있는 것: **이 저장소에서** 참조가 가리켰던 커밋(reset·rebase·amend·브랜치 이동 전 위치). 실험에서 `reset --hard origin/main` 뒤 `HEAD@{1}`로 `bob: fix`를 되살렸다.
- 복구할 수 없는 것
  - 커밋한 적 없는 작업 트리 변경(`reset --hard`로 날린 미커밋 수정).
  - **다른 저장소**의 이동 기록. reflog는 로컬이다.
- bare 원격: `core.logAllRefUpdates`가 bare에서 기본 false라 reflog가 없다. 실험에서 `origin.git/logs`가 없었다.
- 만료(git-gc 문서): `gc.reflogExpire` 90일, `gc.reflogExpireUnreachable` 30일. 도달 불가 객체 prune은 `gc.pruneExpire` 기본 2주.

### 7. 버그 재발 — 병합 오해결

- 병합 때 충돌을 한쪽으로 통째로 골라(예: `checkout --ours`) 수정 줄을 버렸다. git은 해결 결과를 그대로 기록하고, 수정 커밋은 이미 병합된 조상으로 취급한다. 그래서 재병합은 `Already up to date.`다.
- 확인
  - `git show --remerge-diff <병합 커밋>`(2.36+) — 기계적 병합 결과 대비 해결에서 지운 줄이 `-`로 보인다.
  - `git diff <병합>^2 <병합>` — 두 번째 부모 대비 사라진 줄.
  - `git log -m -S '<코드 조각>'` — 그 코드가 들어오고 사라진 커밋. `-m`이 없으면 병합 커밋의 diff를 보지 않아 버린 병합이 안 나온다(실험: `-S`만은 `fix: negative amount`만, `-m -S`는 `merge fix`도 출력).
- 복구: `git cherry-pick <수정 커밋>`으로 다시 적용하고 두 의도를 모두 살려 해결한다. 회귀 테스트를 추가한다.
- 예방: diff3/zdiff3로 base를 보며 해결, 해결 후 테스트.

### 8. `-s ours` vs `-X ours`

- `-s ours`(전략): 결과 트리가 **현재 브랜치 그대로**다(문서: "always that of the current branch head"). 상대 변경을 전부 무시한다.
- `-X ours`(ort 옵션): **충돌한 덩어리만** 내 쪽으로 정하고, 충돌하지 않은 상대 변경은 반영한다(merge-strategies 문서). 바이너리 파일은 파일 전체를 내 쪽에서 가져온다.
- `checkout --ours <파일>`은 그 **파일 전체**를 내 쪽 버전으로 한다. 그 파일 안의 상대 쪽 비충돌 변경까지 버리므로, 파일 단위로는 `-s ours`에 가깝다. 별도 실험(같은 파일에 theirs 쪽 충돌 줄 + 비충돌 줄)에서 결과가 갈렸다.

```text
== checkout-ours
rate=2 mid mid mid label=fee
== X-ours
rate=2 mid mid mid label=FEE-fixed
```

- `checkout --ours`는 theirs의 비충돌 수정(`label=FEE-fixed`)까지 버렸고, `-X ours`는 그것을 남겼다.

### 9. 충돌 없는 병합과 깨진 빌드

- 3-way 병합이 판정하는 것: **줄(텍스트) 영역이 겹치는가**.
- 판정하지 않는 것: 코드의 의미. 한쪽이 `total()`을 `totalWithShipping()`으로 바꾸고 다른 쪽이 새 파일에서 `total()`을 호출하면 텍스트는 겹치지 않아 깨끗이 병합되지만 컴파일이 실패한다(Fowler의 "semantic conflict"). 04번 실험에서 `Merge made by the 'ort' strategy.` 뒤 `javac`가 `cannot find symbol`로 실패했다.
- 그래서 병합 뒤에도 빌드·테스트(CI)가 필요하고, 자주 통합할수록 이런 충돌이 일찍 드러난다.
