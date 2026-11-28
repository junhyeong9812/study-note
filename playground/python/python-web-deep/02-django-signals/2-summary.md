# python/python-web-deep/02 — Django 시그널: post_save와 커스텀 — 정리 (힌트)

> 출처 — study-site 항목 `python/django-signals`(항목 데이터 `data/python/django-flask-deep.json`) · 정답 코드 study-practice `python/python-web-deep/reference/django-signals.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다.

## 한눈에 — 쉽게 말하면

**Django 시그널은 「학교 안내 방송」이다.**
방송실은 「급식 준비 끝」 같은 소식을 방송만 한다.
누가 그 방송을 듣고 무엇을 할지는 방송실이 모른다.
듣고 싶은 반은 미리 「이 방송 나오면 알려 주세요」 명단에 이름을 올려 둔다.
「3반 관련 방송만 듣겠다」처럼 범위를 좁혀 신청할 수도 있다.
Django 시그널도 똑같은 구조다.
모델의 `save()` 는 「저장 끝났다」는 방송(`post_save`)만 하고, 프로필을 만들지 알림을 보낼지는 따로 등록된 함수가 정한다.

| 비유 | 실체 |
|---|---|
| 방송 채널 하나 | `Signal` 객체 하나(`post_save`, `pre_delete`, `payment_completed` …) |
| 듣기 신청 명단 | `Signal.receivers` 리스트 |
| 명단에 이름 올리기 | `connect()` 또는 `@receiver` 데코레이터 |
| 「3반 방송만 듣겠다」 | `sender=User` 로 발신자를 거르기 |
| 방송하기 | `send(sender, **kwargs)` |
| 방송 내용 | `instance` · `created` · `order_id` 같은 키워드 인자 |

```text
   [User.save()]                 ← 방송실: 누가 듣는지 모른다
        │  post_save.send(sender=User, instance=..., created=True)
        ▼
   ┌─────────── post_save 명단 ───────────┐
   │ create_profile   (User 만 듣기)  ──▶ 반응 │
   │ notify_order     (Order 만 듣기) ──▶ 무시 │
   └──────────────────────────────────────┘
```

> **시그널(signal)** — 어떤 일이 일어났다고 알리는 통로 객체로, 그 일에 반응할 함수들을 명단으로 들고 있다.\
> 예: `post_save` 는 「모델 저장이 끝났다」를 알리는 시그널이다.

> **디커플링(decoupling)** — 두 코드가 서로를 직접 부르지 않게 떼어 놓는 것이다.\
> 예: `User` 클래스 코드에는 `Profile` 이 한 글자도 나오지 않는데, 저장하면 프로필이 생긴다.

## 이 주제가 답하려는 질문

1. 모델을 저장 · 삭제할 때 「뒤따르는 일」을 모델 코드를 고치지 않고 어떻게 붙이나?
2. 같은 `post_save` 안에서 「새로 만든 것」과 「고친 것」을 어떻게 가르나?
3. 모델 이벤트가 아닌 업무 이벤트(결제 완료, 로그인)도 같은 방식으로 알릴 수 있나?
4. 수신자 함수를 써 놓았는데 왜 안 불리는 일이 생기나?

## 동작 방식

### (1) `Signal` — 수신자 명단과 `send`

**언제 쓰나** — 「무슨 일이 일어났다」는 사실 하나에 여러 함수가 각자 반응해야 할 때 쓴다.
알리는 쪽은 반응하는 쪽을 몰라도 된다.

```text
sig = Signal()                      receivers = []
sig.connect(f, sender=None)   ──▶   receivers = [(f, None)]
sig.connect(g, sender=Order)  ──▶   receivers = [(f, None), (g, Order)]

sig.send(sender=Order, x=1)
   ├─ (f, None)  : 거르는 값 None   → f(sender=Order, x=1) 호출
   └─ (g, Order) : Order == Order   → g(sender=Order, x=1) 호출
   ──▶ [(f, f의 반환값), (g, g의 반환값)] 를 돌려준다
```

- `connect` 는 `(수신자 함수, 거를 발신자)` 쌍을 리스트 끝에 붙인다.
- `send` 는 리스트를 앞에서부터 돈다 — 그래서 수신자는 등록한 순서대로 불린다.
- 쌍마다 거르는 값이 `None` 이거나 지금 발신자와 같으면 그 함수를 부른다.
- 부를 때는 언제나 `sender=` 키워드와 `send` 에 넘긴 키워드 인자를 그대로 넘긴다.
- 각 수신자의 반환값을 `(수신자, 반환값)` 쌍으로 모아 돌려준다.
- 수신자를 하나 부르고 그것이 끝나야 다음 수신자로 넘어간다 — 동기 실행이다.

`disconnect(f)` 는 명단에서 함수가 `f` 인 쌍을 모두 빼낸다.
이 시뮬레이션의 `disconnect` 는 `sender` 인자를 받기만 하고 거르는 데 쓰지 않는다.

> **수신자(receiver)** — 시그널 명단에 올라 있다가 시그널이 오면 불리는 함수다.\
> 예: `create_profile`, `notify_order`.

> **발신자(sender)** — 시그널을 보낸 쪽을 가리키는 값으로, 수신자가 거르는 기준이 된다.\
> 예: 모델 시그널에서는 `type(self)`, 즉 `User` 같은 클래스다.

### (2) `Model.save()` — `pre_save` → 저장 → `post_save` 와 `created`

**언제 쓰나** — 저장 직전 · 직후에 일을 끼워 넣을 때 쓴다.
`post_save` 는 「새로 생겼나」를 `created` 로 함께 알려 준다.

```text
obj.save()
  ① created = (obj.pk is None)          새 객체면 True, 이미 pk 가 있으면 False
  ② pre_save.send(sender=type(obj), instance=obj)
  ③ created 면 obj.pk = id(obj)          pk 를 매긴다(흉내)
  ④ post_save.send(sender=type(obj), instance=obj, created=created)
  ⑤ return obj
```

- ① 판정은 pk 를 매기기 **전에** 해야 한다 — ③ 뒤에 판정하면 언제나 pk 가 있어 늘 `False` 가 된다.
- ② `pre_save` 는 `created` 를 넘기지 않는다.
- ③ 새 객체만 pk 를 받는다; 이미 pk 가 있으면 그대로 둔다.
- ④ `post_save` 가 `created` 를 실어 보낸다 — 수신자는 이 값으로 생성과 수정을 가른다.

> **pk(primary key)** — 레코드 하나를 가리키는 고유 번호다.\
> 예: 저장하기 전의 모델은 `pk` 가 `None` 이다.

> **`created`** — `post_save` 가 넘기는 참/거짓 값으로, 이번 저장이 새로 만든 것이면 `True` 다.\
> 예: 같은 객체를 두 번째로 저장하면 `created=False` 다.

### (3) `Model.delete()` — `pre_delete` → 삭제 → `post_delete`

**언제 쓰나** — 지우기 전에 기록을 남기거나(감사 로그), 딸린 것을 정리할 때 쓴다.

```text
obj.delete()
  ① pre_delete.send(sender=type(obj), instance=obj)   ← 아직 pk 가 살아 있다
  ② pk = obj.pk ; obj.pk = None                        삭제(흉내)
  ③ post_delete.send(sender=type(obj), instance=obj)   ← pk 는 이제 None
  ④ return pk
```

- `pre_delete` 수신자는 지워지기 전의 객체를 본다 — 그래서 「삭제 예정」 기록에 알맞다.
- 삭제 뒤 `pk` 가 `None` 이 되므로, 같은 객체를 다시 `save()` 하면 (2)의 ① 판정에서 새 객체로 취급된다.

### (4) `sender` 거르기

**언제 쓰나** — 한 시그널(`post_save`)을 모든 모델이 함께 쓰므로, 특정 모델의 저장에만 반응하고 싶을 때 쓴다.

```text
post_save.connect(create_profile, sender=User)

User().save()     → send(sender=User)     User == User       → 불림
Profile().save()  → send(sender=Profile)  Profile == User ?  → 안 불림
Order().save()    → send(sender=Order)    Order == User ?    → 안 불림
```

- 모델 쪽은 `sender=type(self)` 를 보낸다 — 객체가 아니라 **그 객체의 클래스**다.
- 비교는 `expected_sender == sender` 다 — 클래스 자체가 같아야 한다.
  `Order` 를 상속한 클래스는 `type(self)` 가 그 하위 클래스라서 `Order` 와 같지 않다.
- `sender` 를 비우면(`None`) 어느 발신자가 보내든 다 받는다.
- 커스텀 시그널에서는 발신자가 클래스가 아니어도 된다 — 예제는 `'PaymentService'` 같은 문자열을 쓴다.

### (5) 수신자를 등록하는 두 방법

**언제 쓰나** — 함수 정의와 등록을 따로 두려면 `connect`, 함수 바로 위에 붙여 한눈에 보이게 하려면 `@receiver` 를 쓴다.

```text
방법 1                                   방법 2
def create_profile(...): ...             @receiver(post_save, sender=Order)
post_save.connect(create_profile,        def notify_order(...): ...
                  sender=User)
                                         ⇣ 풀어 쓰면
                                         decorator = receiver(post_save, sender=Order)
                                         notify_order = decorator(notify_order)
                                           └ 안에서 post_save.connect(notify_order, sender=Order)
                                           └ 함수는 그대로 돌려준다
```

- `receiver(signal, sender)` 는 데코레이터를 만들어 돌려주는 함수다.
- 데코레이터는 받은 함수를 `signal.connect(...)` 로 등록하고 **함수를 바꾸지 않고** 돌려준다.
- 둘 다 결과는 같다 — 명단에 `(함수, 발신자)` 쌍이 하나 붙는다.
- 등록은 데코레이터 줄이 **실행될 때**, 곧 그 모듈이 임포트될 때 일어난다.

> **데코레이터(decorator)** — 함수를 받아 무언가를 하고 함수를 돌려주는 함수로, `@이름` 꼴로 정의 위에 붙인다.\
> 예: `@receiver(post_save, sender=Order)`.

### (6) 커스텀 시그널 — 업무 이벤트 알리기

**언제 쓰나** — 「결제 완료」「로그인」처럼 모델 저장이 아닌 업무 사건에 여러 기능이 각자 반응해야 할 때 쓴다.

```text
payment_completed = Signal()
  명단: send_receipt → update_inventory → notify_seller   (등록 순서)

payment_completed.send(sender='PaymentService', order_id=1001, amount=50000)
  → send_receipt(sender=..., order_id=1001, amount=50000)    amount 를 쓴다
  → update_inventory(sender=..., order_id=1001, amount=50000) amount 는 **kwargs 가 받는다
  → notify_seller(sender=..., order_id=1001, amount=50000)    amount 는 **kwargs 가 받는다
```

- 시그널은 `Signal()` 하나로 만든다 — 모델 시그널과 다를 것이 없다.
- 결제 서비스는 영수증 · 재고 · 판매자 알림 코드를 모른다; 기능을 늘리려면 수신자를 하나 더 등록하면 된다.
- `send` 는 모든 키워드 인자를 **모든** 수신자에게 보낸다.
  그래서 필요 없는 인자를 받아 줄 `**kwargs` 가 수신자마다 있어야 한다.
- 수신자의 매개변수 이름은 `send` 가 넘기는 키워드 이름과 맞아야 한다(`order_id`, `user_id`, `ip` …).

> **`**kwargs`** — 이름을 정하지 않은 키워드 인자를 모두 딕셔너리로 받아 두는 매개변수다.\
> 예: `notify_seller` 는 `amount` 를 쓰지 않지만 `**kwargs` 가 받아 준다.

> **pub-sub(발행-구독) · Observer 패턴** — 발행자는 사건만 알리고, 구독자들은 미리 등록해 두었다가 각자 반응하는 구조다.\
> 예: `Signal.send` 가 발행, `connect` 가 구독이다.

### (7) 실제 Django 에서 등록되게 하기 — `signals.py` 와 `ready()`

**언제 쓰나** — 실제 Django 프로젝트에서 수신자를 `signals.py` 에 모아 둘 때 늘 쓴다.

```text
myapp/signals.py   @receiver(post_save, sender=User) def create_user_profile ...
                   ↑ 이 줄이 실행되어야 명단에 오른다

myapp/apps.py      class MyAppConfig(AppConfig):
                       def ready(self):
                           import myapp.signals   ← 여기서 모듈을 실행시킨다

아무도 signals.py 를 임포트하지 않으면 → @receiver 줄이 실행되지 않음
                                    → 명단이 비어 있음 → 저장해도 아무 일 없음
```

- (5)에서 본 대로 등록은 임포트 때 일어난다.
- `signals.py` 는 다른 코드가 임포트하지 않으면 실행되지 않는다.
- 그래서 앱이 준비될 때 불리는 `AppConfig.ready()` 안에서 임포트해 둔다(원본 팁).
- 원본의 실제 코드 패턴은 빌트인 시그널(`post_save` 로 프로필 만들기 · 저장)과 커스텀 시그널(`order_completed` 로 메일 · 분석)을 함께 보인다.

> **`AppConfig.ready()`** — Django 가 앱을 불러 준비를 마친 뒤 부르는 메서드다.\
> 예: `def ready(self): import myapp.signals`.

## 문법 — 형태와 규칙

```python
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

@receiver(post_save, sender=Article)            # 빌트인: Article 저장에만
def on_article_saved(sender, instance, created, **kwargs):
    if created:                                   # 새로 만든 때만
        print("새 글:", instance.pk)

article_published = Signal()                      # 커스텀 시그널

@receiver(article_published)                      # sender 를 비우면 모두 받는다
def on_published(sender, article_id, **kwargs):
    print("발행:", article_id)

article_published.send(sender="Editor", article_id=7)
```

- 수신자 꼴: `def 이름(sender, <쓸 인자들>, **kwargs)` — `sender` 와 `**kwargs` 는 빼지 않는다.
- 등록: `시그널.connect(함수, sender=거를값)` 또는 `@receiver(시그널, sender=거를값)`.
- 발송: `시그널.send(sender=보낸쪽, 키=값, …)` — 반환값은 `(수신자, 반환값)` 쌍의 리스트다.
- 해제: `시그널.disconnect(함수)`.
- 모델 시그널 넷과 넘기는 인자:

| 시그널 | 언제 | 넘기는 인자(이 시뮬레이션) |
|---|---|---|
| `pre_save` | 저장 직전 | `sender`, `instance` |
| `post_save` | 저장 직후 | `sender`, `instance`, `created` |
| `pre_delete` | 삭제 직전 | `sender`, `instance` |
| `post_delete` | 삭제 직후 | `sender`, `instance` |

- `post_save(created=True)` 는 새 객체 생성, `post_save(created=False)` 는 기존 객체 수정이다.
- 수신자 모듈은 `apps.py` 의 `ready()` 에서 임포트한다.

## 어디서 틀리나

### 1. `signals.py` 를 임포트하지 않아 수신자가 등록되지 않는다

수신자 함수를 다 써 놓아도 그 모듈이 실행되지 않으면 명단은 비어 있다.
오류도 나지 않고 그냥 아무 일도 일어나지 않아 찾기 어렵다.
`apps.py` 의 `ready()` 에서 `import myapp.signals` 를 해 둔다.

### 2. `created` 를 확인하지 않는다

`post_save` 는 수정할 때도 온다.
`create_profile` 이 `if created:` 없이 프로필을 만들면 사용자를 고칠 때마다 프로필이 하나씩 더 생긴다.
원본의 실제 패턴에서 `save_user_profile` 은 `created` 를 보지 않는다 — 생성 · 수정 모두에서 프로필을 다시 저장하려는 의도다.

### 3. 수신자에 `**kwargs` 가 없다

`send` 는 넘긴 키워드를 모든 수신자에게 보낸다.
`notify_seller(sender, order_id)` 처럼 `**kwargs` 를 빼면 `amount=50000` 을 받을 자리가 없어 `TypeError` 가 난다.
매개변수 이름이 `send` 의 키워드와 다를 때도 같은 오류가 난다.

### 4. `sender` 를 잘못 걸러 엉뚱한 저장에 반응하거나 반응하지 않는다

`sender` 를 비우면 모든 모델의 저장에 반응한다.
이 시뮬레이션은 클래스를 `==` 로 비교하므로, 하위 클래스의 저장은 상위 클래스로 건 수신자에 오지 않는다.

### 5. 수신자 안에서 저장하면 시그널이 또 나간다

`create_profile` 안의 `profile.save()` 도 `post_save` 를 보낸다(`sender=Profile`).
이번에는 `sender` 거르기 덕에 `create_profile` 이 다시 불리지 않는다.
`post_save` 수신자가 `sender` 도 `created` 도 거르지 않고 같은 객체를 다시 저장하면 수신자가 끝없이 자기를 부르게 된다(원본에 근거 없음 — 코드를 읽어 추론).

### 6. 시그널은 동기다 — 느린 일이 저장을 붙잡는다

`send` 는 수신자를 하나씩 불러 모두 끝나야 돌아온다.
메일 발송처럼 오래 걸리는 일을 수신자에 넣으면 `save()` 를 부른 쪽이 그만큼 기다린다.
원본은 비동기가 필요하면 Celery 를 쓰라고 한다.

### 7. 원본 주석 `providing_args deprecated in 4.0+`

원본의 주장 → `Signal()` 의 `providing_args` 인자가 4.0 이후로 폐기 예정이라는 것이다.
왜 의심스러운가 → 폐기 예고와 실제 제거가 다른 버전에서 일어났을 수 있어, 「4.0+ 에서 deprecated」라는 표현이 정확한지 불분명하다(확인 필요).
이 시뮬레이션의 `Signal.__init__` 도 `providing_args` 를 받기만 하고 쓰지 않는다.

### 8. 타입 힌트와 실제 내용이 어긋난다

원본은 `self.receivers: List[Callable]` 이라고 적지만 실제로는 `(함수, 발신자)` 튜플을 담는다.
타입 힌트는 실행에 영향을 주지 않으므로 코드는 돌아가지만, 읽는 사람을 헷갈리게 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `id(self)` 를 pk 로 쓰면 객체마다 다른 값이 나온다 | 파이썬 언어는 「살아 있는 동안 객체마다 고유한 정수」만 보장한다. 그 값이 메모리 주소라는 것은 CPython 구현의 동작이다. 실행할 때마다 값이 달라 미리 알 수 없다 |
| 수신자는 등록한 순서대로 불린다 | 이 시뮬레이션의 코드(리스트 끝에 붙이고 앞에서부터 순회)가 보장한다. 실제 Django 가 순서를 약속하는지는 (확인 필요) |
| 시그널은 동기로 실행된다 | 이 시뮬레이션의 `send` 코드가 보장하고, 원본이 Django 의 성질로 적는다 |
| `sender` 는 클래스를 `==` 로 비교한다 | 이 시뮬레이션의 코드다. 실제 Django 의 비교 방식은 (확인 필요) |
| `ready()` 에서 `signals.py` 를 임포트한다 | 파이썬 언어가 아니라 Django 프레임워크의 관례다(원본 팁) |
| `providing_args` 가 4.0+ 에서 폐기 | 원본 주석의 주장일 뿐이다(확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 사용자를 만들 때 프로필을 자동으로 함께 만들기 | `post_save` + `sender=User` + `if created:` | `User.save()` 안에 프로필 코드를 직접 넣기 |
| 삭제 전에 기록 남기기 | `pre_delete` | `post_delete`(이미 pk 가 지워진 뒤) |
| 결제 완료에 여러 기능이 반응 | 커스텀 시그널 하나 + 수신자 여럿 | 결제 코드가 영수증 · 재고 · 알림 함수를 차례로 직접 부르기 |
| 메일처럼 오래 걸리는 후처리 | 원본이 권하는 Celery 같은 비동기 처리 | 수신자 안에서 바로 처리하기(저장이 그만큼 느려진다) |
| 저장과 반드시 한 흐름으로 읽혀야 하는 핵심 업무 규칙 | 그 코드 안에 직접 쓰기(원본에 근거 없음 — 추론) | 시그널로 숨기기 — 어디서 불리는지 코드에 안 보인다 |

## 핵심 문장

1. **시그널은 「알리는 쪽」과 「반응하는 쪽」을 떼어 놓는다** — `send` 하는 코드는 누가 듣는지 모른다.
2. **`post_save` 는 `created` 로 생성과 수정을 가른다** — 판정은 pk 가 `None` 이었는지로 한다.
3. **`sender` 로 거르지 않으면 모든 발신자의 시그널을 받는다.**
4. **수신자는 `sender` 와 `**kwargs` 를 받아야 한다** — `send` 의 키워드가 모든 수신자에게 간다.
5. **등록은 임포트 때 일어나므로 `ready()` 에서 `signals.py` 를 임포트한다; 실행은 동기라 느린 일은 Celery 로 넘긴다.**

## 관련 자료

- `django-middleware` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [django-celery](../07-django-celery/2-summary.md)
- [django-testing](../06-django-testing/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/django-flask-deep.json` 의 `django-signals`

## 용어 풀이

- **시그널(signal)** — 사건을 알리는 통로 객체로, 반응할 수신자 명단을 들고 있다.
- **수신자(receiver)** — 시그널 명단에 올라 있다가 시그널이 오면 불리는 함수.
- **발신자(sender)** — 시그널을 보낸 쪽을 가리키는 값; 모델 시그널에서는 모델 클래스.
- **`connect` / `disconnect`** — 명단에 수신자를 올리기 / 빼기.
- **`send`** — 명단의 수신자를 차례로 부르고 반환값을 모아 돌려주기.
- **`@receiver`** — 함수를 시그널에 등록하고 함수를 그대로 돌려주는 데코레이터.
- **`pre_save` · `post_save`** — 저장 직전 · 직후에 오는 빌트인 시그널.
- **`pre_delete` · `post_delete`** — 삭제 직전 · 직후에 오는 빌트인 시그널.
- **`created`** — `post_save` 의 인자; 새로 만든 저장이면 `True`.
- **pk** — 레코드의 고유 번호; 저장 전에는 `None`.
- **커스텀 시그널** — `Signal()` 로 직접 만든, 업무 사건을 알리는 시그널.
- **디커플링** — 두 코드가 서로를 직접 부르지 않게 떼어 놓기.
- **pub-sub · Observer 패턴** — 발행자는 알리기만 하고 구독자들이 각자 반응하는 구조.
- **`**kwargs`** — 이름을 정하지 않은 키워드 인자를 모두 받아 두는 매개변수.
- **데코레이터** — 함수를 받아 처리하고 함수를 돌려주는 함수, `@` 로 붙인다.
- **`AppConfig.ready()`** — Django 가 앱 준비를 마친 뒤 부르는 메서드.
- **동기 실행** — 앞의 일이 끝나야 다음 일로 넘어가는 실행 방식.
- **Celery** — 원본이 비동기 후처리가 필요할 때 쓰라고 든 도구.

## 더 들어가면

- 실제 Django 의 `connect` 는 기본으로 수신자를 약한 참조로 들고 있어, 지역 함수나 람다를 등록하면 사라질 수 있다고 알려져 있다 — `weak=False` 로 막는다(확인 필요).
- 같은 수신자가 두 번 등록되는 것을 막으려고 `dispatch_uid` 인자를 쓴다(확인 필요).
- 실제 Django 의 `send` 는 수신자가 예외를 던지면 그대로 전파하고, `send_robust` 는 예외를 잡아 결과 리스트에 담는다(확인 필요).
- 실제 Django 의 `disconnect` 는 제거했는지를 참/거짓으로 돌려준다(확인 필요).
- `QuerySet.update()` 나 `bulk_create()` 처럼 모델의 `save()` 를 거치지 않는 경로에서는 `pre_save` · `post_save` 가 오지 않는다고 알려져 있다(확인 필요).
- 최근 Django 에는 비동기 수신자와 `asend` 가 들어왔다는 설명이 있다 — 버전은 (확인 필요).
- 트랜잭션이 커밋된 뒤에 일을 하려면 `transaction.on_commit` 을 함께 쓰는 패턴이 있다(확인 필요).
