# issue/cross-cutting/database/catalog-presence-vs-enabled — 정답

태그: `silent-failure` · `fail-closed`

## 정답
<!-- 질문 1:1 대응 -->

1. **통과시키고, 그 뒤 갱신의 변경 표시를 놓친다.**\
   `DISABLE TRIGGER`는 트리거를 지우지 않는다 — `pg_trigger` 행은 그대로 있고 `tgenabled`만 `D`가 된다.\
   그래서 이름으로 행 수를 세는 검사는 "있다"로 통과한다.\
   기동한 시스템은 "갱신마다 트리거가 갱신 시각을 남긴다"를 전제로 **최근 바뀐 행만** 대조하는데, 트리거가 꺼져 있으니 갱신 시각이 바뀌지 않고, 그 행의 어긋남은 대조 창에 나타나지 않는다.\
   오류는 어디에서도 나지 않는다 — 결과는 "유실 없음" 불변식의 조용한 위반이고, 이 방식이 기본 경로라 영향 범위도 넓었다(리뷰에서 발견).
   > **DISABLE TRIGGER** — 트리거를 지우지 않고 발화만 멈추는 `ALTER TABLE` 문. 대량 적재·복구 작업에서 흔히 쓰고, 다시 켜는 것을 잊기 쉽다.

2. **`O`·`A`만 업무 세션에서 발화한다.**\
   `O`(origin) — 세션의 `session_replication_role`이 `origin`(기본)·`local`일 때 발화한다(`ENABLE TRIGGER`의 기본 상태).\
   `A`(always) — 복제 역할과 무관하게 늘 발화한다(`ENABLE ALWAYS TRIGGER`).\
   `R`(replica) — 복제 역할 세션에서**만** 발화한다(`ENABLE REPLICA TRIGGER`) — 보통 업무 세션에서는 발화하지 않는다.\
   `D`(disabled) — 발화하지 않는다.\
   그래서 `D`만 빼고 나머지를 활성으로 보면 `R`이 통과한다 — 활성은 **허용 목록(`O`·`A`)**으로 정의해야 한다.
   > **session_replication_role** — 세션이 복제 적용 세션인지(`replica`) 보통 세션인지(`origin`·`local`)를 나타내는 설정. 트리거 발화 여부를 `tgenabled`와 함께 정한다.

3. **범위 축소는 "다른 대상"을, 활성 확인은 "꺼진 상태"를 막는다.**\
   이전 리뷰에서 이 검사는 이미 "이 스키마의 이 테이블에 걸린 그 이름"으로 좁혀졌다 — 다른 스키마나 다른 테이블에 같은 이름의 트리거가 있어 통과하는 오판(대상 혼동)을 막은 것이다.\
   이번 결함은 대상은 맞는데 **그 대상의 상태**를 보지 않은 것이다 — 두 축은 독립이라 하나를 고쳐도 다른 하나가 남는다.

4. **"없어야 한다" 쪽은 존재로 남기는 것이 보수적이다.**\
   "있어야 한다" 검사의 실패는 유실(조용한 오답)이므로, 의심스러우면 거부 쪽으로 — 효력이 확인될 때(`O`·`A`)만 통과시킨다.\
   "없어야 한다" 검사의 목적은 그 트리거의 비용이 다른 방식의 측정·동작에 섞이지 않게 하는 것이다 — 꺼진 트리거도 누가 다시 켜면 비용이 새므로, 꺼져 있어도 "있음"으로 보고 거부한다.\
   즉 두 방향 모두 **틀렸을 때 피해가 큰 쪽으로 기울인다** — 한쪽은 효력 기준, 한쪽은 존재 기준이 된다. 지우려면 새 마이그레이션이나 수동 삭제로 명시적으로 한다.

5. **존재 ≠ 효력의 다른 예와 메시지.**\
   인덱스는 있지만 `indisvalid = false`(동시 생성 실패로 남은 무효 인덱스), 제약은 있지만 `NOT VALID`로 만들어 기존 행을 검증하지 않음, 확장은 설치됐지만 버전이 다름, 역할은 있지만 로그인·권한이 없음, 설정 파일은 있지만 다른 파일이 덮어씀 — 모두 카탈로그·파일의 "있음"이 실제 동작을 보장하지 않는다(일반 사례).\
   거부 메시지에는 **관측한 상태 값**(예: `tgenabled=[D]`)과 **허용 기준**(`O`·`A`만 활성), **고치는 문장**(`ALTER TABLE … ENABLE TRIGGER …` 또는 방식을 바꾸라)을 함께 넣었다 — 운영자가 문서를 찾지 않고 바로 고칠 수 있게.

6. **트리거를 끈 DB로 기동해 거부를 단언하고, 다시 켜서 기동을 단언한다.**\
   트리거가 만들어진 DB에서 `DISABLE TRIGGER`를 실행한 뒤 기본 설정으로 기동 → 거부되어야 한다(고치기 전 코드는 통과해 실패).\
   같은 DB에서 `ENABLE TRIGGER` 후 다시 기동 → 떠야 한다(검사가 지나치게 막지 않는지).\
   "기동이 됐다/안 됐다"만이 아니라 거부 사유가 이 검사의 것인지도 메시지로 확인한다.

## 문제 구조 (추상화 코드)

### 변형 A — 존재만 세는 "있어야 한다" 검사
① 문제 코드
```kotlin
val exists = jdbc.queryForObject(
    """SELECT count(*) FROM pg_trigger t
         JOIN pg_class c ON c.oid = t.tgrelid
         JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = current_schema() AND c.relname = 'counter' AND t.tgname = ?""",
    Int::class.java, TOUCH_TRIGGER,
)!! > 0
if (mode == Mode.TRIGGER) check(exists) { "트리거 $TOUCH_TRIGGER 가 없다" }   // 꺼진 트리거도 통과
```
② 고친 코드
```kotlin
val states = jdbc.queryForList(
    """SELECT t.tgenabled::text FROM pg_trigger t
         JOIN pg_class c ON c.oid = t.tgrelid
         JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = current_schema() AND c.relname = 'counter' AND t.tgname = ?""",
    String::class.java, TOUCH_TRIGGER,
)
val exists = states.isNotEmpty()
val active = states.any { it == "O" || it == "A" }        // 허용 목록 — R(복제 전용)·D(꺼짐)는 활성 아님

when (mode) {
    Mode.TRIGGER -> {
        check(exists) { "트리거 $TOUCH_TRIGGER 가 없다" }
        check(active) {
            "트리거 $TOUCH_TRIGGER 가 비활성이다(tgenabled=$states — O·A만 활성) — " +
                "ALTER TABLE counter ENABLE TRIGGER $TOUCH_TRIGGER 로 켜거나 방식을 바꿔라"
        }
    }
    else -> check(!exists) { "이 방식에서는 트리거 $TOUCH_TRIGGER 가 없어야 한다" }   // 꺼져 있어도 '있음' — 보수적
}
```
무엇이 깨졌나: 카탈로그의 "행 있음"을 "동작함"으로 읽어, 꺼진 트리거 위에서 변경 표시를 전제로 한 기능을 켰다.

## 검증 기록
- 2026-10-23: 사건 기록 대조·추상화(Claude 초안)

## 관련 카드
- [fail-closed-guard](../../reliability/fail-closed-guard/) — 허용은 양성 증명(allowlist)으로만 부여한다 — 활성 판정을 `O`·`A` 허용 목록으로 한 근거.
- [effective-uid-file-access](../../infra/effective-uid-file-access/) — "존재"가 아니라 실제 주체의 접근 가능성으로 판단한다 — 같은 존재 ≠ 효력 축의 파일 권한 사례.
- [silent-failure-vs-artifact](../../reliability/silent-failure-vs-artifact/) — 통과한 검사 뒤의 유실은 오류로 드러나지 않는다 — 산출물로 확인한다.
