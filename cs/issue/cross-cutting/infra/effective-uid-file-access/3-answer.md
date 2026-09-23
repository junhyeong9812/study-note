# cs/issue/infra/effective-uid-file-access — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답
<!-- 질문 1:1 대응 -->

1. **컨테이너 프로세스는 이미지가 정한 uid로 돌기 때문이다.**\
   `sudo`는 compose(와 데몬에 요청하는 클라이언트)를 root로 실행할 뿐, 컨테이너 안 프로세스의 uid는 이미지의 `USER`(여기선 1000)다.\
   root가 만든 bind 디렉터리는 uid 1000이 쓸 수 없어 lock 파일 생성이 `AccessDenied`로 실패하고, 의존 서비스까지 기동에 실패했다.\
   교정: 해당 디렉터리를 그 uid로 `chown`(예: `1000:0`, `1000:1000`).\
   함정: NFS `root_squash`면 chown이 막히고, CIFS는 chown 자체가 안 돼 마운트 옵션으로 소유자를 지정한다.
   > **effective uid** — 커널이 권한 검사에 쓰는, 프로세스의 실제 사용자 ID.

2. **존재가 아니라 "그 uid로 읽을 수 있는가"를 의심한다. 재발은 새 파일의 생산자가 그대로라서다.**\
   파일이 `-rw-------+ root`(umask 077 + ACL)로 생성돼 uid 1000인 앱은 읽을 수 없었고, 컨트롤러는 `isReadable=false`로 404를 냈다.\
   `chown -R`은 **실행 시점에 존재하는** 파일만 고친다 — 다음 적재가 만든 파일은 다시 600 root다.\
   재발 방지: 적재 쪽 umask를 022로 하거나 추출 코드에서 권한을 명시하고, 디렉터리 default ACL(`getfacl`)을 확인한다.

3. **권한 거부도 그만큼 빠르기 때문이다.**\
   0~1ms 응답은 "핸들러 없음"뿐 아니라 "핸들러가 즉시 거절"과도 맞는다 — 지연만으로 원인을 가를 수 없다.\
   빈 본문(`Content-Length: 0`) 404는 핸들러는 존재하고 그 안의 판정(파일 제공 가능?)이 실패했다는 신호였다.\
   파일명 규칙·디스크·옛 빌드 가설 3개를 차례로 반증한 뒤에야 권한에 도달했다.

4. **호출한 사용자의 셸이 연다.**\
   `sudo cmd > LOG`에서 `> LOG`는 sudo의 인자가 아니라 셸 문법이다 — 셸이 먼저 파일을 열고 그다음 sudo를 실행한다.\
   셸은 일반 사용자 권한이라 root 소유 경로면 명령이 시작되기도 전에 실패한다.\
   교정: 로그는 쓸 수 있는 곳(`$HOME`)에 두고 권한은 명령에만 준다(또는 `sudo tee` 류로 쓰기 주체를 바꾼다). 백그라운드 실행 전에 `sudo -v`로 비번 프롬프트를 미리 해소한다.

5. **프로세스 생성(로그인·서비스 시작) 시점에 확정된다.**\
   보조 그룹 목록은 프로세스가 만들어질 때 자격 증명에 복사된다.\
   `usermod -aG`는 계정 DB만 바꿀 뿐 이미 돌고 있는 프로세스의 자격 증명은 그대로다.\
   교정: 서비스 재시작(대화형이면 재로그인이나 `newgrp`). 배포 스크립트엔 권한 실패 시 폴백 경로를 뒀다.

6. **일부 파일만 새 버전인, 반쯤 갱신된 상태로 남는다.**\
   git은 호출 사용자로 파일을 쓰는데, 다른 계정 소유 파일을 교체하지 못하면 pull이 중간에 멈춘다.\
   `sudo git pull`로 밀어붙이면 `.git/objects`까지 root 소유로 오염돼 다음 일반 pull이 또 깨진다.\
   복구: 저장소를 실사용 계정으로 chown하고, 부분 적용된 파일은 `git checkout -- <file>`로 되돌린 뒤 일반 사용자로 재시도한다.\
   (소유자가 다른 저장소에서 git이 거부하는 `dubious ownership`도 같은 뿌리다.)

7. **권한 판단의 주체는 "명령을 친 사람"이 아니라 "그 파일을 실제로 여는 프로세스"다.**\
   컨테이너 uid, 리다이렉트를 여는 셸, 기동 시 확정된 보조 그룹, git을 실행한 계정 — 모두 "누가 여는가"의 문제다.\
   그래서 판단 기준은 파일의 존재가 아니라 **그 주체의 읽기·쓰기 가능성**이다.

## 문제 구조 (추상화 코드)

### 변형 A — 컨테이너 uid vs 호스트 소유자
① 문제 코드
```yaml
services:
  search:
    image: search-engine        # USER 1000
    volumes: [ "./data:/usr/share/data" ]   # ./data는 root가 생성
# → node.lock AccessDenied → unhealthy → 의존 서비스 기동 실패
```
② 고친 코드
```sh
mkdir -p ./data && sudo chown -R 1000:0 ./data
mkdir -p ./uploads && sudo chown -R 1000:1000 ./uploads
```
깨진 것: 호스트에서 root로 띄워도 컨테이너 안에서 파일을 여는 것은 uid 1000이었다.

### 변형 B — 존재 ≠ 읽기 가능, 과거만 고치는 chown
① 문제 코드
```java
boolean isServable(Path p) {
    return Files.exists(p) && Files.isReadable(p);   // uid 1000 기준 → false → 404
}
```
```sh
# 적재기(생산자): umask 077 로 파일 생성 → -rw------- root
sudo chown -R 1000:1000 /images     # 오늘 파일만 고침, 내일 적재분은 다시 600 root
```
② 고친 코드
```sh
# 생산자를 고친다
umask 022                            # 또는 추출 시 명시 권한(0644)
getfacl /images                      # 디렉터리 default ACL이 권한을 좁히는지 확인
```
깨진 것: 앱 uid로 읽을 수 없는 파일이 계속 생산됐고, 소비자 쪽 일회성 chown으로는 재발을 막지 못했다.

### 변형 C — 리다이렉트는 셸이 연다
① 문제 코드
```sh
sudo rsync -a src/ dst/ > /root-owned/rsync.log 2>&1   # 셸(일반 사용자)이 로그를 먼저 열다 실패
```
② 고친 코드
```sh
sudo -v                                            # 비번 프롬프트 선해소
sudo rsync -a src/ dst/ > "$HOME/rsync.log" 2>&1   # 권한은 명령에만
```
깨진 것: sudo의 권한이 리다이렉트까지 덮는다고 가정했다.

### 변형 D — 보조 그룹은 기동 시 확정
① 문제 코드
```sh
sudo usermod -aG docker svcuser
# 실행 중 서비스: /var/run/docker.sock Permission denied (그대로)
```
② 고친 코드
```sh
sudo usermod -aG docker svcuser
sudo systemctl restart collector.service   # 새 프로세스가 새 그룹으로 생성됨
```
깨진 것: 계정 DB 변경이 이미 실행 중인 프로세스의 자격 증명에 반영된다고 가정했다.

### 변형 E — 혼용 계정의 부분 적용
① 문제 코드
```sh
git pull            # 일부 파일이 다른 계정 소유 → unable to unlink → 중간 실패
sudo git pull       # .git/objects까지 root 소유로 오염
```
② 고친 코드
```sh
sudo chown -R appuser:appuser /srv/repo
git checkout -- <부분 적용된 파일>
git pull            # 일반 사용자로
```
깨진 것: 한 작업 트리를 여러 uid가 쓰면서, 쓰기 도중 실패가 반쯤 갱신된 상태를 남겼다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
