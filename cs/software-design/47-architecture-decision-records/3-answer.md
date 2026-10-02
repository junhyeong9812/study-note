# software-design/47-architecture-decision-records — 정답

## 정답

### 1. 기록이 없을 때의 두 선택지

- **맹목적으로 따른다**: 결정이 아직 유효하면 괜찮다. 맥락이 바뀌어 다시 볼 때가 됐는데도 아무도 못 건드린다. 이런 결정이 쌓이면 팀이 아무것도 못 바꾸게 된다.
- **맹목적으로 바꾼다**: 결정이 지키던 동기·결과를 모른 채 바꾼다. 예) 아직 시험되지 않은 비기능 요구를 지키던 결정을 깨뜨린다.
- Nygard는 둘 다 피하는 것이 낫다고 적는다.

### 2. 다섯 부분

```text
 Title         짧은 명사구 ("ADR 9: LDAP for Multitenant Integration")
 Status        proposed / accepted / deprecated / superseded(대체 ADR 링크)
 Context       작용하는 힘들(기술·정치·사회·프로젝트), 가치 중립적인 사실
 Decision      "We will …" 능동태 완전한 문장
 Consequences  결정 뒤의 결과 맥락
```

- 결과 절에는 **좋은 것만이 아니라 모든 결과**(긍정·부정·중립)를 적는다.
- 문서 하나는 한두 쪽이고, 미래 개발자와 대화하듯 완전한 문장으로 쓴다.

### 3. 고쳐 쓰지 않는 이유와 번호

- 뒤집힌 결정도 "그때는 그것이 결정이었다"는 사실이 의미가 있다. 고쳐 쓰면 언제·왜 바뀌었는지가 사라진다.
- 새 ADR을 쓰고 옛 것은 superseded로 표시해 링크한다.
- 번호는 순서대로 단조 증가하고 재사용하지 않는다(Nygard). 추가 전용 로그다.

### 4. `-s 2`의 결과

(실험, adr-tools `b3279ba` — 출력의 마크다운 링크 `[제목](파일)`은 `[제목] → 파일`로 바꿔 실었다)

```text
### 0002 상태 절
## Status

Superceded by [4. 결제 재시도는 최대 2회, 지수 백오프와 지터] → 0004-2.md
### 0004 상태 절
## Status

Accepted

Supercedes [2. 결제 재시도는 클라이언트 라이브러리 기본값을 쓴다] → 0002-.md
```

- 2번은 `Accepted`가 `Superceded by [4 …]`로 바뀐다. 새 ADR에는 `Accepted`와 `Supercedes [2 …]`가 붙는다. 링크가 양방향으로 생긴다.
- 철자 `Superceded`는 도구 소스 그대로다.

### 5. 한글 제목의 파일 이름

- `doc/adr/0002-.md`. slug가 비었다.
- `adr-new`는 `tr -Ccs [:alnum:] -`로 slug를 만든다. GNU `tr`(이 호스트 9.4)는 바이트 단위로 동작해 한글 바이트를 영숫자로 보지 않는다. 그래서 한글이 `-`로 바뀌고, 앞뒤 `-` 제거 뒤 빈 문자열이 된다. 같은 이유로 "결제 재시도는 최대 2회, …"는 `0004-2.md`가 됐다.
- 대처: 제목에 영문 키워드를 함께 넣거나, 만든 뒤 이름을 바꾸고 링크를 고친다.

### 6. `git log -S`로 이유 찾기

(실험, git 2.43.0 — 해시는 실행마다 다르다)

```text
########## [no-adr] git log -S'max-attempts=2' --format='%h %ad %s' --date=short
6730ffe 2026-10-02 fix
## 그 커밋이 바꾼 파일
   src/application.properties | 2 +-
   1 file changed, 1 insertion(+), 1 deletion(-)
########## [with-adr] git log -S'max-attempts=2' --format='%h %ad %s' --date=short
5aa7bdb 2026-10-02 결제 재시도 5→2 (ADR-0004)
## 그 커밋이 바꾼 파일
   doc/adr/0004-payment-retry.md | 17 +++++++++++++++++
   src/application.properties    |  2 +-
   2 files changed, 18 insertions(+), 1 deletion(-)
```

- 기록 없는 쪽: 값을 바꾼 커밋 "fix"와 설정 파일 한 줄 변경까지만 보인다. 이유는 기억 속에만 있다.
- ADR 동반 쪽: 같은 검색 한 번으로 ADR 파일에 닿는다. 맥락·결정·대가·재검토 조건을 읽을 수 있다.
- 남는 빈틈: 설정 줄 자체에는 ADR 표시가 없다(`git grep` 결과). `git log -S`를 모르는 사람은 못 찾는다. 설정 옆 `# ADR-0004` 주석이 길을 하나 더 만든다.

### 7. MADR에만 있는 절

- **Considered Options**(검토한 대안). 같은 대안을 다시 제안하고 다시 기각하는 반복을 막는다.
- **Confirmation**(결정을 지키는지 확인하는 법, 전체판). 결정이 코드에서 조용히 무너지는 것을 막는다.
- MADR 전체판에는 Decision Drivers와 Pros and Cons of the Options도 있다. 메타데이터로 status·date·decision-makers·consulted·informed를 둘 수 있다.

### 8. 5 → 2 → 5 회귀

- 원인: 2회로 줄인 결정이 무엇을 막고 있었는지(재시도 폭주로 PG 회복 지연)가 보이지 않았다. 다음 사람이 "성공률을 올리자"며 맹목적으로 바꿨다.
- 증상 확인: `git log -S'max-attempts=5'`와 `-S'max-attempts=2'`로 값이 오간 커밋들을 찾는다. 사후 검토에 "예전에도 있었던 문제"가 적힌다.
- 대처
  - ADR 결과 절에 막고 있는 위험과 재검토 조건을 적는다.
  - 커밋 메시지·설정 주석으로 ADR에 연결한다.
  - 그 값을 지키는 시나리오 테스트를 둔다(46).
  - 다시 바꾸려면 새 ADR로 옛 것을 대체한다.

### 9. 두는 곳

- 코드 저장소 안(`doc/adr/` 등)에 두고, 결정과 같은 PR·커밋에 넣는다.
- 위키에 두면 생기는 증상: 문서는 "Kafka 사용"인데 코드는 이미 다른 것으로 바뀌었다. 문서 수정일이 코드 변경보다 훨씬 오래됐다. 결정과 코드가 다른 리뷰 과정을 거치기 때문이다.
- Thoughtworks Radar("Lightweight Architecture Decision Records", Adopt): 위키·웹사이트 대신 소스 관리에 두라고 권한다. 코드와 동기화된 기록이 되기 때문이다.
