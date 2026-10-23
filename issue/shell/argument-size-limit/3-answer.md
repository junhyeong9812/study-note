# issue/shell/argument-size-limit — 정답

태그: `silent-failure` · `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **jq가 아니라 `execve`가 거부했다.**\
   `"$(cat file.json)"`은 파일 내용 전체를 **인수 문자열 하나**로 만든다 — 그 문자열이 프로세스의 argv로 커널에 넘어간다.\
   리눅스는 인수 문자열 하나의 길이를 `MAX_ARG_STRLEN`(32페이지 = 128KB)으로 막고, 인수와 환경 변수 전체 합을 `ARG_MAX`(보통 스택 한도의 1/4)로 막는다 — 넘으면 `execve`가 `E2BIG`을 돌려준다.\
   그래서 jq는 시작조차 하지 못했고, 메시지(`인수 명단이 너무 김` = Argument list too long)는 셸이 찍었다.\
   몇 주 동안 멀쩡했던 것은 산출물이 128KB 아래였기 때문이다 — 1초 주기 조건이 산출물을 약 190KB로 키운 회차부터 실패했다.
   > **E2BIG** — `execve`가 인수·환경이 상한을 넘을 때 돌려주는 오류. 프로그램 코드가 아니라 커널의 프로세스 생성 단계에서 난다.
   > **MAX_ARG_STRLEN** — 리눅스에서 인수(또는 환경 변수) 문자열 **하나**의 최대 길이. 전체 합 상한(`ARG_MAX`)과 따로 걸린다 — 전체가 작아도 하나가 크면 실패한다.

2. **빈 메타 파일과 "ok" 상태가 남는다.**\
   셸은 명령을 실행하기 **전에** 리다이렉트(`> meta.json`)를 연다 — 파일이 잘리거나 새로 생긴 뒤 `execve`가 실패하므로, 디스크에는 0바이트 `meta.json`이 남는다.\
   상태 파일은 그 줄보다 먼저 `ok`로 써졌으므로 회차는 "정상 종료"로 보인다.\
   집계 단계는 메타가 비어 있는 회차를 실패로 보지 않고 그 칸을 비운 채 표를 만들었다 — 메타에서 읽는 칸(조건별 표의 일부 행, 갱신 비율 칸)이 9회차에서 통째로 비었다.\
   측정 데이터(응답·CPU·DB 지표)는 다른 파일에 있어 유효했고, 빈 메타는 회차 산출물에서 같은 모양으로 복원했다(복원 규칙 검증 후).

3. **작은 페이지에서는 정상, 약 700행부터 그 페이지를 조용히 버린다.**\
   페이지(최대 2만 행 × 행당 약 190B)를 `--argjson`으로 넘기므로 한 페이지가 128KB를 넘는 순간(약 700행) jq가 실행되지 못한다.\
   그 실패는 `jq ... > acc.n && mv acc.n acc` 사슬 안에 있어 `mv`만 건너뛰고 루프는 계속된다 — 누적 결과에서 그 페이지가 빠질 뿐 오류가 위로 올라가지 않는다.\
   이 결함은 첫 사건을 고친 뒤 "인수로 데이터를 넘기는 자리" 전수 감사에서 찾았다(그때까지는 별도 대조 — 기대 행 수 미달 — 로만 드러났다).

4. **데이터가 argv를 거치지 않는다.**\
   `--slurpfile name file`은 jq가 **스스로 파일을 연다** — argv에는 경로만 들어가므로 내용 크기와 무관하다.\
   대신 파일 안의 JSON 값들을 **배열로** 묶어 바인딩한다(파일 하나에 값 하나면 `[값]`) — 그래서 식에서 `$name[0]`으로 꺼낸다.\
   파일이 없거나 깨졌을 때 이전 동작(`null`)을 유지하려고, 유효 JSON이면 그 경로를, 아니면 `null` 한 줄을 쓴 임시 파일 경로를 넘기는 도우미를 두었다(임시 파일은 호출자가 지운다).
   > **--slurpfile** — jq 옵션. 파일의 JSON 값들을 배열로 읽어 변수에 바인딩한다. 문자열 그대로 읽으려면 `--rawfile`.

5. **각각 "부분 산출물"·"무음 실패"·"끝난 척"을 막는다.**\
   ① 임시 파일 → 검증 → 이름 바꾸기: 쓰기 도중 실패해도 최종 경로에는 **완성된 파일만** 나타난다(빈 파일·잘린 파일이 정상 이름을 갖지 않는다).\
   ② 검증(`jq -e '필수 필드 존재'`): "명령이 0으로 끝남"이 아니라 **내용**으로 성공을 판정한다.\
   ③ 실패면 상태를 `meta-write-failed`로: 캠페인의 합격 사유 목록 밖이라 그 회차를 다시 잰다.\
   ④ 상태를 메타 **뒤**에: 둘 사이에서 끊기면 상태 파일이 없으므로 이어하기가 그 회차를 "끝나지 않음"으로 보고 다시 잰다 — 메타 없는 "끝난 회차"가 생길 수 없다.\
   같은 감사에서 계획 파일 쓰기도 같은 형태로 바꿨고, 못 쓰면 회차를 아예 돌리지 않는다(종료 코드 2).

6. **입력·측정 길이·주기에 비례해 자라는 값이 `$(...)`·`"$var"`로 인수 자리에 들어가는 곳.**\
   대표적으로 `--argjson`/`--arg`에 파일 내용·쿼리 결과 넣기, `curl -d "$big"`, `xargs` 없이 `cmd $(find ...)`, 거대한 환경 변수가 있다.\
   이런 자리는 작은 입력의 테스트·스모크에서 모두 정상이라 상한을 넘는 조건이 처음 생길 때 운영에서 터진다 — 그래서 한 곳을 고치면 같은 모양을 전수로 찾는다.\
   교정은 같다: 파일·표준 입력·`xargs`로 넘기고, 실패가 사슬에 묻히지 않게 비0을 반환해 위로 올린다.

## 문제 구조 (추상화 코드)

### 변형 A — 회차 메타를 인수로 조립 + 상태 선기록
① 문제 코드
```bash
finish_run() {
  echo "$status" > "$dir/status"                                   # 상태가 먼저 "끝남"
  jq -n --arg id "$id" \
        --argjson pre "$( { jq -ec . "$dir/pre.json" 2>/dev/null || echo null; } | head -1)" \
        --argjson gc  "$( { jq -ec . "$dir/gc.json"  2>/dev/null || echo null; } | head -1)" \
        '{id: $id, pre: $pre, gc: $gc}' > "$dir/meta.json"            # pre.json > 128KB → E2BIG, meta.json 0바이트
}
```
② 고친 코드
```bash
json_or_null_path() {                     # 유효 JSON이면 그 경로, 아니면 null 한 줄 임시 파일
  if [[ -s "$1" ]] && jq empty "$1" >/dev/null 2>&1; then echo "$1"; return; fi
  local t; t=$(mktemp) && echo null > "$t" && echo "$t"
}
finish_run() {
  local f_pre f_gc tmps=()
  f_pre=$(json_or_null_path "$dir/pre.json"); [[ "$f_pre" == "$dir/"* ]] || tmps+=("$f_pre")
  f_gc=$(json_or_null_path "$dir/gc.json");   [[ "$f_gc"  == "$dir/"* ]] || tmps+=("$f_gc")
  if ! jq -n --arg id "$id" --slurpfile pre "$f_pre" --slurpfile gc "$f_gc" \
         '{id: $id, pre: $pre[0], gc: $gc[0]}' > "$dir/meta.json.tmp" \
     || ! jq -e 'type == "object" and .id != null' "$dir/meta.json.tmp" >/dev/null 2>&1 \
     || ! mv "$dir/meta.json.tmp" "$dir/meta.json"; then
    echo "$(date -Is) meta-write-failed" >> "$dir/errors.log"
    rm -f "$dir/meta.json.tmp"; status="meta-write-failed"           # 재측정 대상
  fi
  (( ${#tmps[@]} )) && rm -f "${tmps[@]}"
  echo "$status" > "$dir/status"                                   # 상태는 마지막
}
```
무엇이 깨졌나: 자라는 데이터를 크기 상한이 있는 채널(argv)로 넘겼고, 그 실패가 먼저 써 둔 "ok"와 리다이렉트가 만든 빈 파일 뒤에 숨었다.

### 변형 B — 페이지 이어 붙이기 루프
① 문제 코드
```bash
while :; do
  page=$(query_page "$last") || return 1
  n=$(jq 'length' <<< "$page")
  (( n == 0 )) && break
  jq -c --argjson p "$page" '. + $p' "$acc" > "$acc.n" && mv "$acc.n" "$acc"   # 약 700행부터 실패 → mv 건너뜀
  last=$(jq '.[-1].id' <<< "$page")                                            # 커서는 전진 → 그 페이지 영구 누락
done
```
② 고친 코드
```bash
pf=$(mktemp)
while :; do
  query_page "$last" > "$pf" || { rm -f "$pf"; return 1; }
  n=$(jq 'length' "$pf") && [[ "$n" =~ ^[0-9]+$ ]] || { rm -f "$pf"; return 1; }
  (( n == 0 )) && break
  { jq -c --slurpfile p "$pf" '. + $p[0]' "$acc" > "$acc.n" && mv "$acc.n" "$acc" \
      && last=$(jq -e '.[-1].id' "$pf"); } || { rm -f "$pf" "$acc.n"; return 1; }    # 실패는 위로
done
rm -f "$pf"
```
무엇이 깨졌나: 실패한 단계 뒤에서 커서만 전진해, 실패가 "그 페이지 없음"으로 바뀌었다.

## 검증 기록
- 2026-10-23: 사건 기록 대조·추상화(Claude 초안)

## 관련 카드
- [silent-failure-vs-artifact](../../cross-cutting/reliability/silent-failure-vs-artifact/) — 상태·종료 코드가 아니라 산출물 내용으로 성공을 판정한다(이 카드는 그 실패를 만든 채널 상한).
- [atomic-file-replace](../../cross-cutting/reliability/atomic-file-replace/) — 임시 파일에 완성한 뒤 이름 바꾸기로 게시한다.
- [exit-status-semantics](../exit-status-semantics/) — `&&` 사슬·파이프라인에서 중간 실패가 묻히는 규칙.
