# cs/issue/reliability/atomic-file-replace — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **덮어쓰기의 절단.** `write(path)`·`open(path,'w')`는 파일을 **먼저 truncate(0바이트로 비움)한 뒤** 새 내용을 쓴다.\
그래서 쓰는 도중 크래시·`ENOSPC`가 나면 원본은 이미 사라졌고 새 내용은 일부만 들어간 "이전도 새것도 아닌" 파일이 남는다(빈 파일·절단된 JSON·잘린 CSV).\
읽는 쪽 폴백이 흡수해 주더라도 그건 **데이터 손실을 조용히 삼키는 것**일 뿐 복구가 아니다.
   > **truncate** — 파일 길이를 0(또는 지정 길이)으로 잘라 기존 내용을 버리는 연산.

2. **rename이 원자적인 이유와 전제.** `rename(2)`는 디렉터리 엔트리 하나가 가리키는 inode를 한 번에 바꾼다 — 관찰자는 옛 파일 전체 아니면 새 파일 전체만 본다.\
전제 ① **같은 파일시스템**: 마운트가 다르면 rename은 `EXDEV`로 실패한다(복사+삭제로 떨어지면 원자성이 사라짐) → temp/staging은 목적지와 **같은 부모 디렉터리**에 만든다.\
전제 ② **유니크 이름**: temp 이름이 writer끼리 겹치면 두 writer가 같은 temp를 동시에 쓰다 서로를 덮어, 원자 게시되는 것 자체가 섞인 파일이 된다 → pid + 원자 카운터 같은 유일 접미사.\
실패하면 temp를 지워 잔해를 남기지 않고, 목록·로드 쪽은 `.tmp`와 파싱 실패 파일을 건너뛴다.
   > **EXDEV** — "cross-device link": 서로 다른 파일시스템 사이의 rename/link 시도에 대한 오류.

3. **고정 이름 temp / 임시 디렉터리 재사용.** `<id>.json.tmp`가 고정이면 같은 id의 두 writer가 한 temp에 번갈아 기록해 **temp 자체가 손상**되고, 그 손상본이 rename으로 정본이 될 수 있다.\
고정 이름의 백업 **디렉터리**를 재사용하면 이전 실행(심지어 다른 작업)의 잔재가 그대로 남아 있다가, 복원 단계의 와일드카드 복사(`$BK/*`)가 **그 잔재까지 대상에 되돌린다** — 증상은 엉뚱한 곳에서(컴파일 실패 등) 나타나 오진을 부른다.\
교정은 실행마다 새 경로(`mkdtemp`)를 받아 이름 충돌을 구조적으로 불가능하게 하는 것이다.

4. **디렉터리 교체의 파괴 창.** "옛 폴더 삭제 → 새 폴더 rename"은 두 동작 사이에 **대상이 아예 없는 창**을 만든다 — 그 사이 rename이 실패하거나 크래시하면 정상본만 사라진다.\
displaced rename: 새 내용을 `.tmp-*`에 준비 → 기존 대상을 `.old-*`로 **rename해 치움** → tmp를 대상 이름으로 rename → `.old` 제거.\
어느 rename이든 실패하면 `.old`를 원위치로 되돌린다.\
두 rename 사이 크래시로 남은 `.old-*`는 다음 실행이 정체성(메타 id)을 확인해 회수하고(자기치유), 목록 조회는 `.`으로 시작하는 작업 폴더를 제외한다.
   > **displaced rename** — 교체 대상을 지우지 않고 옆 이름으로 옮겨 두었다가, 새것이 자리 잡은 뒤에야 제거하는 교체 순서.

5. **교체 창의 옛 fd.** rename은 이름만 새 inode로 돌린다 — rename **이전에 열린 fd는 여전히 옛 inode**를 가리킨다.\
compact(파일 재작성) 동안 다른 writer가 옛 fd로 append하면, 그 줄은 **디렉터리에서 이름이 사라진 inode**에 들어가 무음 유실된다(락 없이 동시 append 300줄 중 280줄 소실, 3/3 재현).\
교정: 스냅샷→temp 작성→rename→**핸들 재오픈**까지 swap 전체를 writer 락으로 배타한다. 재오픈이 실패하면 옛 핸들로 계속 쓰지 말고 쓰기를 멈춰 단계별 오류로 보고한다.

6. **ETXTBSY.** 리눅스는 실행 중인(텍스트 영역이 매핑된) 실행 파일을 **쓰기 모드로 여는 것**을 `ETXTBSY`로 거부한다 — `cp`로 덮어쓰기는 기존 inode에 쓰는 것이라 막힌다.\
반면 새 파일을 옆에 만들고 `rename`하거나, `unlink` 후 새로 만들면 **새 inode**가 생기고 실행 중인 프로세스는 옛 inode를 계속 붙잡고 있으므로 허용된다.\
새 바이너리는 다음 재시작 때 적용된다 — 백업과 새 파일을 나란히 두고 종료 후 `mv` 한 번으로 교체하는 방식도 같은 원리다.
   > **inode** — 파일의 실체(데이터·메타데이터). 디렉터리 엔트리(이름)는 inode를 가리키는 링크일 뿐이다.

7. **원자성 ≠ 내구성.** rename이 원자적이어도 그 결과가 디스크에 내려갔다는 뜻은 아니다.\
파일 내용 `fsync`는 데이터만 내구화하고, **새 디렉터리 엔트리(파일 생성·rename)**는 부모 디렉터리를 `fsync`해야 크래시 후에도 남는다.\
append-only 저널은 크래시 직후 마지막 레코드가 부분 기록(torn tail)일 수 있다 — 정상 저널은 항상 개행으로 끝나므로 **개행 없는 마지막 줄만 버리고**, 중간 줄이 깨졌으면 복구 불가로 보고 기동을 거부한다.\
저널이 없거나 손상·권한 오류면 "빈 저널"로 취급하지 않는다(그러면 기록을 조용히 잃는다).\
락도 파일 경로(inode)가 아니라 **보호할 대상(target) 단위**로 걸어야 한다 — 경로 inode에 결박된 락은 "대상당 실행 하나"라는 배타를 보장하지 못한다.
   > **torn tail** — 크래시로 마지막 쓰기가 중간에서 끊겨 파일 끝에 남은 불완전 레코드.

## 문제 구조 (추상화 코드)

### 변형 A — 덮어쓰기로 저장 (중간 실패 시 절단)
① 문제 코드
```python
with open(path, 'w') as f:          # 여는 순간 원본 truncate
    write_rows(f, rows)             # 여기서 중단 → 잘린 파일
```
② 고친 코드
```python
tmp = path + '.tmp'
with open(tmp, 'w') as f:
    write_rows(f, rows)
os.replace(tmp, path)               # 같은 디렉터리 → 원자 교체
```
무엇이 깨졌나: truncate와 기록 사이의 중간 상태가 정본 경로에 그대로 노출됐다.\
같은 구조: 에디터 저장·메타 사이드카·스크롤백 저장이 모두 통째 덮어쓰기였다 — 같은 헬퍼로 교체.\
같은 구조: 백그라운드 폴링 스레드와 사용자 커맨드가 같은 파일을 비원자로 번갈아 씀 → 원자 교체 + 이름 필드를 별도 사이드카 파일로 분리해 서로의 본문을 덮지 않게 함.

### 변형 B — 고정 temp 이름 (동시 writer 충돌)
① 문제 코드
```rust
let tmp = dir.join(format!("{id}.json.tmp"));        // 같은 id면 writer끼리 같은 temp
fs::write(&tmp, json)?;
fs::rename(&tmp, dir.join(format!("{id}.json")))?;
```
② 고친 코드
```rust
static SEQ: AtomicU64 = AtomicU64::new(0);
let target = fs::canonicalize(p).unwrap_or_else(|_| p.to_path_buf());   // 심링크면 실제 대상의 부모에
let tmp = target.parent().unwrap().join(format!(
    ".{stem}.save-{}-{}.tmp", std::process::id(), SEQ.fetch_add(1, Ordering::Relaxed)));
fs::write(&tmp, content)?;
fs::rename(&tmp, &target).map_err(|e| { let _ = fs::remove_file(&tmp); e })?;
// 목록 조회는 *.tmp 와 파싱 실패 파일을 건너뜀
```
무엇이 깨졌나: 원자 게시의 전제(temp가 writer마다 유일)가 없었다.\
부수 함정: 새 파일은 `canonicalize`가 실패해 원 경로로 폴백하므로, 파일명 경로 탈출 검사는 따로 둔다.

### 변형 C — 다단계 생성(재귀 복사)의 부분 실패 잔해
① 문제 코드
```rust
copy_tree(from, to)?;        // 중간 실패 → 대상에 반쯤 복사된 잔해, 재시도도 "이미 존재"로 막힘
```
② 고친 코드
```rust
let tmp = parent.join(format!(".copy-{}-{}.tmp", pid, SEQ.fetch_add(1, Relaxed)));
if let Err(e) = copy_tree(from, &tmp) { remove_any(&tmp); return Err(e); }
if fs::symlink_metadata(to).is_ok() { remove_any(&tmp); return Err(AlreadyExists); }  // 게시 직전 재확인
fs::rename(&tmp, to).map_err(|e| { remove_any(&tmp); e })
```
무엇이 깨졌나: 여러 단계로 만들어지는 결과물의 중간 상태가 최종 경로에서 보였다.\
남은 창: 재확인~rename 사이 TOCTOU는 남는다(`rename`은 기존 대상을 조용히 교체한다 — no-clobber는 `RENAME_NOREPLACE` 류가 필요, 단일 사용자 위협모델이라 주석으로 수용).\
같은 구조: 내보내기 저장은 `create_new`로 대상 이름을 먼저 **예약**한 뒤 원자 쓰기, 실패 시 예약 제거(부분 파일 0).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~C)은 "같은 디렉터리의 유니크 temp에 완성 → rename 게시"이다. 같은 원리(덮어쓰기는 원자적이지 않다)에 교체 대상·위협이 달라 다른 방안이 쓰인 사례:

### 방안 1 — 디렉터리: displaced rename + 실패 시 복원
```rust
// 문제: remove_dir_all(final)?; rename(tmp, final)?;   → 사이 실패 시 정상본 소실
let mut displaced = vec![];
if final_dir.exists() {
    let old = parent.join(format!(".old-{}", uid));
    fs::rename(&final_dir, &old)?;
    displaced.push((final_dir.clone(), old));
}
if let Err(e) = fs::rename(&tmp_dir, &final_dir) {
    for (orig, moved) in &displaced { let _ = fs::rename(moved, orig); }   // 원위치 복원
    let _ = fs::remove_dir_all(&tmp_dir);
    return Err(e);
}
for (_, moved) in displaced { let _ = fs::remove_dir_all(moved); }
// 크래시로 남은 .old-* 는 다음 실행이 메타 id 일치 확인 후 회수 / 목록은 '.' 시작 폴더 제외
```

### 방안 2 — 교체 창 동안 writer 배제 락 (옛 fd append 유실)
```rust
// 문제: compact()가 keep 스냅샷 → tmp → rename → 재오픈 하는 동안
//       다른 스레드가 옛 핸들로 append → 이름 없는 inode로 사라짐
fn append(&self, rec: &Rec) -> Result<()> {
    let mut h = self.handle.lock();                 // compact와 같은 락
    writeln!(h, "{}", rec.to_json())?; h.flush()
}
fn compact(&self) -> Result<(), CompactErr> {
    let mut h = self.handle.lock();                 // rename ~ 재오픈 전체 보유
    let tmp = write_keep_snapshot().map_err(CompactErr::Building)?;
    fs::rename(&tmp, &self.path).map_err(CompactErr::Swapping)?;
    *h = open_append(&self.path).map_err(|e| { self.stop_writes(); CompactErr::Reopening(e) })?;
    Ok(())
}
```
락을 뺀 측정으로 손실 크기(300 중 280)를 먼저 실증한 뒤 도입했다.

### 방안 3 — 실행 중 바이너리: 옆 파일 + rename (ETXTBSY 회피)
```sh
# 문제
cp new-app "$INSTALLED"                        # 실행 중 → ETXTBSY
# 고친
cp new-app "$INSTALLED.new" && mv "$INSTALLED.new" "$INSTALLED"   # 새 inode로 교체
# 또는: rm -f "$INSTALLED" && cp new-app "$INSTALLED"             # 다음 재시작부터 적용
```

### 방안 4 — staging은 목적지와 같은 파일시스템에 (EXDEV)
```python
# 문제
staging = tempfile.mkdtemp()                     # /tmp — 목적지와 다른 FS일 수 있음
build_into(staging); os.rename(staging, dest)    # EXDEV
# 고친
staging = tempfile.mkdtemp(dir=dest.parent)      # 같은 부모 → 원자 rename
try:
    build_into(staging); os.rename(staging, dest)
except Exception:
    rollback(); raise                            # 반쯤 만든 결과 남기지 않음
```

### 방안 5 — 실행별 유니크 임시 경로 (고정 이름 잔재 복원)
```sh
# 문제
BK=$SCRATCH/backup                   # 고정 이름 — 이전 실행(다른 작업)의 파일이 남아 있음
cp -r "$BK"/* target/                # 복원이 잔재까지 되돌림
```
```python
# 고친
bk = tempfile.mkdtemp(prefix=f"mut-{box_id}-")   # 실행마다 새 경로, 작업 이름으로 격리
# ... 백업·변형·복원은 bk 안에서만
```

### 방안 6 — 내구성까지: 부모 디렉터리 fsync · torn tail 판정 · 대상 정체성 락
```python
def create_journal(path):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.fsync(fd)
    dfd = os.open(os.path.dirname(path), os.O_RDONLY); os.fsync(dfd)   # 새 엔트리 내구화

def load_journal(path):
    data = read_or_refuse(path)          # 부재·권한·손상 → 빈 저널 아님: 기동 거부/격리
    lines = data.split(b'\n')
    if not data.endswith(b'\n'):
        lines = lines[:-1]               # 개행 없는 끝줄 = torn tail → 버림
    for ln in lines:
        if ln and not parse(ln): raise Corrupt   # 중간 손상 = 치명
    # 재기동 시 ACCEPTED/RUNNING 레코드는 "미실행"이 아니라 UNKNOWN
# 락은 경로 inode가 아니라 대상(target) 단위 정체성에
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 유니크 temp + rename | 대상이 단일 파일, 같은 FS | 헬퍼 하나 | 기존 대상을 조용히 교체(no-clobber 아님) | 설정·스냅샷·문서 저장 |
| 1. displaced rename | 대상이 디렉터리 | rename 2회 + 복원 코드 | 두 rename 사이 크래시 → 잔여 `.old` 회수 필요 | 폴더 단위 아카이브·설치 |
| 2. writer 배제 락 | 교체 대상에 상시 append하는 writer가 있다 | 락 경합 | 재오픈 실패 시 쓰기 정지 | 로그·원장 compaction |
| 3. 옆 파일 + rename | 대상이 실행 중 바이너리 | 재시작 전까지 옛 버전 | 재시작 누락 시 옛 버전 계속 실행 | 자기 자신·데몬 교체 |
| 4. 같은 FS staging | 목적지 마운트가 /tmp와 다를 수 있다 | 없음 | 목적지 부모에 쓰기 권한 필요 | 디렉터리 초기화·설치 |
| 5. 실행별 유니크 경로 | 스크래치가 여러 실행·세션에 공유된다 | 없음 | 정리 누락 시 디스크 누적 | 백업·변형 테스트·병렬 작업 |
| 6. fsync + torn tail | 크래시 후에도 기록이 진실이어야 한다 | fsync 지연 | 중간 손상 시 기동 거부(의도된 소음) | 실행 원장·저널 |

**결론**: 단일 파일은 기본 방안으로 충분하다.\
대상이 디렉터리면 삭제 대신 **옆으로 치우고 복원 가능한 순서**를, 교체 대상에 살아 있는 writer·실행 프로세스가 있으면 **락 또는 새 inode 교체**를 쓴다.\
원자성은 "중간 상태가 안 보인다"까지만 보장한다 — 크래시 후 기록이 남아야 하는 곳이면 **부모 디렉터리 fsync와 torn tail 판정**을 별도로 더한다.
