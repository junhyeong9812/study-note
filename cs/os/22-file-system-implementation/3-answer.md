# os/22-file-system-implementation — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. vsfs 배치

```text
  0    1    2    3 ... 7      8 ... 63
  [S]  [i]  [d]  [I x 5]      [D x 56]
```

- 슈퍼블록: inode 수·데이터 블록 수·inode 테이블 시작 위치·매직 넘버.
- inode 비트맵·데이터 비트맵: 객체마다 1비트, 0 빈칸 / 1 사용.
- inode 테이블: inode 배열. 데이터 영역: 파일·디렉터리 내용.
- 4 KB / 256 B = 블록당 16개 × 5블록 = **80개**. inode 테이블 크기가 파일 수 상한이다(OSTEP 40.2).

### 2. 최대 파일 크기

- 간접 블록 하나 = 4096 / 4 = 1024 포인터.
- (12 + 1024) × 4 KB = **4144 KB**(약 4 MB).
- 이중 간접 추가: (12 + 1024 + 1024²) × 4 KB ≈ **4 GB 조금 넘게**(OSTEP 40.3).

### 3. extent vs 다단계 인덱스

- 다단계 인덱스: 블록마다 포인터 하나. 1000블록이면 직접 12개 + 간접 블록 안 포인터 988개가 필요하다.
- extent: (논리 시작, 길이, 물리 시작) 한 쌍. 연속 1000블록이면 extent **하나**(`ee_len = 1000`)다(ext4 문서 ifork).
- extent 4개까지는 inode의 `i_block` 60바이트 안에 들어간다. 넘치면 extent 트리가 된다. 초기화된 extent 하나는 최대 32768블록이다.

### 4. open("/foo/bar")의 읽기 순서

1. 루트 inode 읽기 → 루트 디렉터리 데이터 읽기, "foo" → 44번 찾기
2. inode 44 읽기 → foo 디렉터리 데이터 읽기, "bar" → 번호 찾기
3. bar inode 읽기(권한·크기 확인), OFD 생성

- 루트는 부모가 없다. 그래서 inode 번호가 **약속된 값**이다. 대부분 유닉스 파일 시스템에서 2다(OSTEP 40.6).

### 5. 할당 write = I/O 5번

- 데이터 비트맵 읽기 → 빈 블록 표시 후 쓰기(2) + inode 읽기 → 새 블록 위치 적고 쓰기(2) + 데이터 블록 쓰기(1) = 5(OSTEP 40.6).
- 줄이는 것: 페이지 캐시·버퍼 캐시(읽기 제거, 쓰기 모아 내기), 쓰기 지연(ext4 delayed allocation — 23번), 블록 그룹 배치(탐색 거리 감소).

### 6. VFS 객체

- 슈퍼블록: 마운트된 파일 시스템 하나.
- inode: 파일 하나(디스크 inode를 메모리로 올린 것).
- dentry: 경로 요소 하나("foo")와 inode의 연결. **RAM에만 있고 디스크에 저장하지 않는다**(vfs.rst).
- file: 열린 파일. 21번의 OFD(`struct file`)다.

### 7. FFS의 그룹

- 초기 유닉스 FS는 데이터를 디스크 곳곳에 흩었다. 탐색 비용 때문에 대역폭의 2%까지 떨어졌다(OSTEP 41.1).
- 규칙(OSTEP 41.4)
  - 디렉터리: 디렉터리가 적고 빈 inode가 많은 그룹에.
  - 파일 데이터: 그 inode와 같은 그룹에.
  - 같은 디렉터리의 파일: 디렉터리와 같은 그룹에.
- 큰 파일이 한 그룹을 다 채우면 그 디렉터리의 다른 파일이 가까이 들어갈 자리가 없다. 그래서 덩어리로 나눠 여러 그룹에 흩는다(large-file exception, 41.6).

### 8. df 여유인데 ENOSPC

- 확인: `df -i` — `IUse%`가 100%면 inode 고갈이다.
- 이유: ext4는 inode 수를 포맷 때 bytes-per-inode 비율로 정하고, **비율은 나중에 못 바꾼다**(mke2fs(8)). 비율은 볼륨 크기별 usage type이 정한다(보통 볼륨 16384, 512 MB 미만 4096, 4 TB 이상 32768 등 — `/etc/mke2fs.conf`). 평균 파일 크기가 이 비율보다 작은 파일이 쌓이면 inode가 먼저 떨어진다.
- 대처: `du --inodes -x -d 2`로 범인 디렉터리를 찾아 정리한다. 근본은 작은 파일을 묶는 설계, 또는 `-i`를 작게 해 다시 포맷, 또는 inode를 동적 할당하는 파일 시스템(XFS 등).

### 9. 한 디렉터리 ENOSPC

- 커널 로그에서 `Directory (ino: N) index full, reach max htree level :2`와 `Large directory feature is not enabled on this filesystem`를 찾는다(fs/ext4/namei.c `ext4_dx_add_entry`).
- htree 깊이 상한(`large_dir` 없으면 2)에 닿은 것이다. `max_dir_size_kb` 마운트 제한일 수도 있다.
- 대처: 해시 접두어 하위 디렉터리로 나눈다. 필요하면 `large_dir`을 켠다.

### 10. 여유 vs 가용

- ext4는 블록의 5%(기본)를 root 전용으로 **예약**한다(mke2fs(8) `-m`).
- "여유(free)"는 예약분 포함, "가용(avail)"은 일반 사용자가 쓸 수 있는 양이다. statvfs의 `f_bfree` vs `f_bavail`이다.
- 그래서 가용이 0이면 앱은 `ENOSPC`, root는 예약분에 쓸 수 있다. 데이터 전용 볼륨이면 `tune2fs -m`으로 낮출 수 있다.
