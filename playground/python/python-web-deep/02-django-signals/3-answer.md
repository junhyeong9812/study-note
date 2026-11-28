# python/python-web-deep/02 — Django 시그널: post_save와 커스텀 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 한 번 불리고, Profile 의 저장에는 반응하지 않으며, user_id 값은 미리 알 수 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`[시그널] Profile 생성: user_id=…` 꼴의 줄이 한 줄 찍힌다.
`…` 자리는 `id(user)` 값이라 실행마다 다르다.

**왜 그런가**

- `user.save()` 는 `pk` 가 `None` 이라 `created=True` 로 판정하고, pk 를 매긴 뒤 `post_save.send(sender=User, created=True)` 를 보낸다.
- 명단에서 `(create_profile, User)` 가 맞아 한 번 불린다; `(notify_order, Order)` 는 걸러진다.
- 안쪽 `profile.save()` 도 `post_save` 를 보내지만 `sender=Profile` 이다 — `Profile == User` 가 아니라 `create_profile` 은 다시 불리지 않는다.
- 출력 줄은 `profile.save()` 가 끝난 뒤에 찍힌다.
- pk 는 `id(self)` 로 매기는데, 이 값은 CPython 에서 객체 위치에 따라 정해져 미리 알 수 없다.

근거: 2-summary 「동작 방식 (2)」·「(4)」, 「구현 세부사항 대 언어 보장」.

### 2. 「주문 생성」→「주문 수정」→「주문 삭제 예정」, 모두 Python 책

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [시그널] 주문 생성: Python 책
  [시그널] 주문 수정: Python 책
  [시그널] 주문 삭제 예정: Python 책
```

**왜 그런가**

- 첫 `save()` 는 `pk` 가 `None` 이라 `created=True` → 「생성」.
- 두 번째 `save()` 는 이미 pk 가 있어 `created=False` → 「수정」. 가격이 바뀐 것은 찍지 않는다.
- `delete()` 는 먼저 `pre_delete` 를 보내므로 `log_deletion` 이 「삭제 예정」을 찍는다. `post_delete` 에는 수신자가 없다.

근거: 2-summary 「동작 방식 (2)」·「(3)」.

### 3. 영수증 → 재고 → 알림 순서, amount 는 **kwargs 가 받는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [영수증] 주문 #1001: 50000원 결제 완료
  [재고] 주문 #1001 재고 차감
  [알림] 판매자에게 주문 #1001 통보
```

**왜 그런가**

- 세 수신자는 `sender` 를 비워 등록했으므로 `'PaymentService'` 가 보낸 시그널을 모두 받는다.
- `send` 는 명단을 등록 순서대로 돈다.
- `send` 는 `order_id` · `amount` 를 모든 수신자에게 보낸다; `update_inventory` · `notify_seller` 는 `amount` 를 `**kwargs` 로 받고 쓰지 않는다.

근거: 2-summary 「동작 방식 (1)」·「(6)」.

### 4. pk 를 매긴 뒤에 판정하면 늘 「수정」이 되기 때문이다

새 객체인지는 「pk 가 아직 없나」로만 알 수 있다.
pk 를 먼저 매기면 `self.pk is None` 이 언제나 거짓이라 `created` 가 늘 `False` 가 되고, 생성과 수정을 가를 수 없다.
그래서 판정을 먼저 해 두고 그 값을 `post_save` 에 실어 보낸다.

근거: 2-summary 「동작 방식 (2)」.

### 5. 등록은 `@receiver` 줄이 실행될 때, 곧 모듈이 임포트될 때 일어나기 때문이다

`@receiver` 는 정의되는 순간 `signal.connect(...)` 를 부른다.
`signals.py` 를 아무도 임포트하지 않으면 그 줄이 실행되지 않아 명단이 비고, 저장해도 아무 일이 없다.
앱 준비가 끝날 때 불리는 `ready()` 에서 임포트하면 그 모듈이 반드시 실행된다.

근거: 2-summary 「동작 방식 (5)」·「(7)」, 「어디서 틀리나 1」.

### 6. `send` 가 `notify_seller` 를 부르는 순간 `TypeError` 가 난다

`send` 는 `receiver(sender=..., order_id=1001, amount=50000)` 꼴로 부른다.
`(sender, order_id)` 에는 `amount` 를 받을 자리가 없어 그 호출에서 `TypeError` 가 난다.
앞의 두 수신자는 이미 불린 뒤이고, 예외가 `send` 밖으로 나간다(원본에 근거 없음 — 추론).

근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 3」.

### 7. 비우면 모든 모델의 저장에 반응하고, 하위 클래스 저장에는 `notify_order` 가 불리지 않는다

`sender` 가 `None` 이면 `send` 의 거르기 조건 `expected_sender is None` 이 늘 참이라 `User` · `Order` · `Profile` 어느 저장에도 반응한다.
모델은 `sender=type(self)` 를 보내는데, 하위 클래스 객체의 `type(self)` 는 그 하위 클래스다.
이 시뮬레이션은 `==` 로 비교하므로 `Order` 와 같지 않아 걸러진다.
실제 Django 의 동작은 별개다(확인 필요).

근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 4」.

### 8. `created=True` — 새 객체로 취급된다

`delete()` 가 `self.pk = None` 으로 돌려놓았으므로, 다음 `save()` 의 판정 `self.pk is None` 이 참이 된다.
그래서 `notify_order` 는 「생성」을 찍고 pk 도 새로 매겨진다(이 시뮬레이션에서는 같은 `id(self)` 값이다).

근거: 2-summary 「동작 방식 (2)」·「(3)」.

### 9. `connect` 는 구독, `send` 는 발행이다

- `connect` 는 「이 사건이 오면 나를 불러 달라」고 명단에 오르는 구독이다.
- `send` 는 사건이 일어났음을 명단 전체에 알리는 발행이다.
- `User.save()` 는 `post_save` 를 발행할 뿐 `Profile` 을 부르지 않는다; 프로필 생성은 따로 구독한 `create_profile` 이 한다.
  그래서 `User` 코드를 고치지 않고 수신자를 붙이거나 뗄 수 있다 — 이것이 디커플링이다.

근거: 2-summary 「한눈에」, 「동작 방식 (1)」·「(6)」.

### 10. 부른 쪽이 그 시간만큼 기다리고, 그래서 느린 일은 비동기로 넘기라는 것이다

`send` 는 수신자를 하나씩 불러 모두 끝나야 돌아온다.
메일 수신자가 오래 걸리면 뒤 수신자도, `send` 를 부른 결제 코드(모델 시그널이면 `save()` 를 부른 쪽)도 그만큼 멈춘다.
원본은 시그널이 동기라는 점을 짚고, 비동기가 필요하면 Celery 를 쓰라고 덧붙인다.

근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 6」.

## 실습 정답

### 실습 1. Django 시그널 시스템을 순수 파이썬으로 흉내 내기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `(수신자, 발신자)` 쌍 명단 | `Signal.__init__` 의 `self.receivers` |
| 2. 명단 끝에 붙이기 | `Signal.connect` 의 `self.receivers.append((receiver, sender))` |
| 3. 함수가 든 쌍 빼기 | `Signal.disconnect` 의 리스트 내포 |
| 4. 거르고 부르고 결과 모으기 | `Signal.send` 의 `expected_sender is None or expected_sender == sender` 와 `results` |
| 5. 빌트인 시그널 넷 | `pre_save = Signal()` … `post_delete = Signal()` |
| 6. pk 와 속성 | `Model.__init__` 의 `self.pk = None`, `setattr` |
| 7. 저장 흐름 | `Model.save` 의 `created = self.pk is None`, `pre_save.send`, `self.pk = id(self)`, `post_save.send(..., created=created)` |
| 8. 삭제 흐름 | `Model.delete` 의 `pre_delete.send`, `self.pk = None`, `post_delete.send`, `return pk` |
| 9. 도메인 모델 | `class User(Model)` · `Order` · `Profile` |
| 10. 프로필 자동 생성 | `create_profile` 의 `if created:` 와 `post_save.connect(create_profile, sender=User)` |
| 11. 데코레이터 | `receiver` 안의 `decorator` — `signal.connect(func, ...)` 후 `return func` |
| 12. 주문 생성/수정 알림 | `@receiver(post_save, sender=Order)` `notify_order` |
| 13. 삭제 예정 기록 | `@receiver(pre_delete, sender=Order)` `log_deletion` |
| 14. User 저장 | `user = User(name="Alice", ...)`, `user.save()` |
| 15. Order 생성 · 수정 · 삭제 | `order.save()`, `order.price = 25000`, `order.save()`, `order.delete()` |
| 16. 커스텀 시그널 | `payment_completed = Signal()`, `user_logged_in = Signal()` |
| 17. 커스텀 수신자 | `send_receipt` · `update_inventory` · `notify_seller` · `record_login` |
| 18. 커스텀 발송 | `payment_completed.send(sender='PaymentService', ...)`, `user_logged_in.send(sender='AuthService', ...)` |
| 19. 패턴 · 정리 출력 | 섹션 7 의 `print("""…""")` 와 핵심 정리 `print` 여섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web-deep/reference/django-signals.py`

```python
# [웹 프레임워크 심화] Django 시그널: post_save와 커스텀
# 설명: post_save, pre_delete 시그널, 커스텀 시그널 정의, 디커플링
# 팁: Django 시그널은 모델 이벤트(save, delete)에 후처리 로직을 디커플링하는 패턴이다. post_save의 created 인자로 생성/수정을 구분하며, 커스텀 시그널로 비즈니스 이벤트도 정의할 수 있다. signals.py를 apps.py의 ready()에서 임포트해야 등록된다.

"""Django 시그널: 빌트인과 커스텀 시그널"""
# 타입 힌트
from typing import Any, Callable, List

# === Django 시그널 시스템 시뮬레이션 ===

# === 1. 시그널 디스패처 구현 ===
# Observer 패턴의 구현 — 발행자(send)와 구독자(connect)를 분리
class Signal:
    """Django의 Signal 클래스 핵심 구현"""
    def __init__(self, providing_args=None):
        # 등록된 (receiver, sender_filter) 쌍
        self.receivers: List[Callable] = []

    # 수신자 등록: 특정 sender만 받으려면 sender 파라미터 사용
    def connect(self, receiver: Callable, sender=None, **kwargs):
        """수신자 등록"""
        self.receivers.append((receiver, sender))

    # 수신자 제거 (앱 종료 시 정리 등)
    def disconnect(self, receiver: Callable, sender=None, **kwargs):
        """수신자 제거"""
        self.receivers = [(r, s) for r, s in self.receivers if r != receiver]

    # 시그널 발송: 모든 등록된 수신자를 동기적으로 호출
    def send(self, sender, **kwargs):
        """시그널 발송"""
        results = []
        for receiver, expected_sender in self.receivers:
            # sender 필터: None이면 모두 수신, 지정되면 해당 sender만
            if expected_sender is None or expected_sender == sender:
                result = receiver(sender=sender, **kwargs)
                results.append((receiver, result))
        return results

# === 2. 빌트인 시그널 시뮬레이션 ===
# Django 내장 시그널 (django.db.models.signals와 동일)
pre_save = Signal()
post_save = Signal()
pre_delete = Signal()
post_delete = Signal()

# === 3. 모델 시뮬레이션 ===
# Django Model의 save/delete가 시그널을 자동 발송하는 패턴
class Model:
    """Django Model 시뮬레이션"""
    def __init__(self, **kwargs):
        self.pk = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    # save 시 pre_save → 저장 → post_save (created 플래그)
    def save(self):
        # pk가 None이면 새 생성, 있으면 수정
        created = self.pk is None
        pre_save.send(sender=type(self), instance=self)

        if created:
            self.pk = id(self)  # 자동 PK 생성

        # post_save에 created 정보 함께 전달
        post_save.send(sender=type(self), instance=self, created=created)
        return self

    # delete 시 pre_delete → 삭제 → post_delete
    def delete(self):
        pre_delete.send(sender=type(self), instance=self)
        pk = self.pk
        self.pk = None
        post_delete.send(sender=type(self), instance=self)
        return pk

# 도메인 모델들 (모두 Model 상속)
class User(Model):
    pass

class Order(Model):
    pass

class Profile(Model):
    pass

# === 4. 시그널 수신자 (receiver) ===
print("=== 시그널 수신자 등록 ===")

# 방법 1: connect() 직접 호출
def create_profile(sender, instance, created, **kwargs):
    """User 생성 시 자동으로 Profile 생성"""
    # created 플래그로 신규/수정 구분 (수정 시에는 Profile을 다시 만들지 않음)
    if created:
        profile = Profile(user_id=instance.pk, bio="")
        profile.save()
        print(f"  [시그널] Profile 생성: user_id={instance.pk}")

# User sender에 한정해 등록
post_save.connect(create_profile, sender=User)

# 방법 2: 데코레이터 패턴 (Django @receiver)
def receiver(signal, sender=None, **kwargs):
    """Django의 @receiver 데코레이터"""
    def decorator(func):
        signal.connect(func, sender=sender, **kwargs)
        return func
    return decorator

# Order 저장 후 알림
@receiver(post_save, sender=Order)
def notify_order(sender, instance, created, **kwargs):
    """주문 생성/수정 시 알림"""
    action = "생성" if created else "수정"
    print(f"  [시그널] 주문 {action}: {getattr(instance, 'item', 'unknown')}")

# Order 삭제 직전 로깅 (감사 기록 용도)
@receiver(pre_delete, sender=Order)
def log_deletion(sender, instance, **kwargs):
    """삭제 전 로깅"""
    print(f"  [시그널] 주문 삭제 예정: {getattr(instance, 'item', 'unknown')}")

# === 5. 시그널 실행 ===
print("\n=== 시그널 실행 ===")

# User 생성 -> Profile 자동 생성 (디커플링: User 코드는 Profile을 모름)
print("--- User 생성 ---")
user = User(name="Alice", email="alice@example.com")
user.save()

# Order 생성 → notify_order 발화 (created=True)
print("\n--- Order 생성 ---")
order = Order(item="Python 책", price=30000)
order.save()

# Order 수정 → notify_order 발화 (created=False)
print("\n--- Order 수정 ---")
order.price = 25000
order.save()

# Order 삭제 → log_deletion 발화
print("\n--- Order 삭제 ---")
order.delete()

# === 6. 커스텀 시그널 ===
print("\n=== 커스텀 시그널 ===")

# 비즈니스 이벤트용 커스텀 시그널 (모델 이벤트와 별개)
payment_completed = Signal()
user_logged_in = Signal()

# 결제 완료 시 여러 핸들러가 독립적으로 반응 (확장 패턴: pub-sub)
@receiver(payment_completed)
def send_receipt(sender, order_id, amount, **kwargs):
    print(f"  [영수증] 주문 #{order_id}: {amount}원 결제 완료")

@receiver(payment_completed)
def update_inventory(sender, order_id, **kwargs):
    print(f"  [재고] 주문 #{order_id} 재고 차감")

@receiver(payment_completed)
def notify_seller(sender, order_id, **kwargs):
    print(f"  [알림] 판매자에게 주문 #{order_id} 통보")

# 로그인 이벤트 (보안 감사)
@receiver(user_logged_in)
def record_login(sender, user_id, ip, **kwargs):
    print(f"  [로그인] user_id={user_id}, ip={ip}")

# 커스텀 시그널 발송: 결제 서비스가 발행자
print("--- 결제 완료 시그널 ---")
payment_completed.send(
    sender='PaymentService',
    order_id=1001,
    amount=50000
)

# 인증 서비스가 발행자
print("\n--- 로그인 시그널 ---")
user_logged_in.send(
    sender='AuthService',
    user_id=42,
    ip='192.168.1.1'
)

# === 7. Django 실제 코드 패턴 ===
print("\n=== Django 실제 코드 패턴 ===")
# 시그널 등록 위치: apps.py의 ready()에서 import해야 module load 시점 보장
print("""
# signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver, Signal
from django.contrib.auth.models import User

# 빌트인 시그널
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# 커스텀 시그널
order_completed = Signal()  # providing_args deprecated in 4.0+

@receiver(order_completed)
def handle_completion(sender, order, **kwargs):
    send_email(order.user.email, 'Order Complete', ...)
    update_analytics(order)

# apps.py (시그널 등록)
class MyAppConfig(AppConfig):
    name = 'myapp'
    def ready(self):
        import myapp.signals  # 시그널 모듈 임포트
""")

print("=== 핵심 정리 ===")
print("1. post_save(created=True): 새 객체 생성 시")
print("2. post_save(created=False): 기존 객체 수정 시")
print("3. pre_delete: 삭제 전 정리 작업")
print("4. 커스텀 시그널: Signal() + @receiver로 비즈니스 이벤트")
print("5. apps.py의 ready()에서 signals 모듈을 임포트해야 등록됨")
print("6. 시그널은 동기적으로 실행됨 (비동기 필요 시 Celery)")
```

**실행 결과** — 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다.

**풀이 요점**

- `send` 의 핵심은 거르기 한 줄과 `receiver(sender=sender, **kwargs)` 호출이다 — 모든 키워드가 모든 수신자에게 간다.
- `created` 는 pk 를 매기기 전에 판정해야 생성과 수정이 갈린다.
- `create_profile` 안의 `profile.save()` 도 `post_save` 를 보내지만 `sender=User` 거르기 덕에 되돌아오지 않는다.
- 데코레이터는 등록만 하고 함수를 그대로 돌려준다 — 등록은 정의되는 순간 일어난다.
- 커스텀 수신자들은 `**kwargs` 로 쓰지 않는 인자를 흘려보내, 결제 쪽은 수신자 수와 모양을 몰라도 된다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
