# python/python-web/04 — Django Forms (폼 처리) — 정리 (힌트)

> 출처 — study-site 항목 `python/django-forms`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/django-forms.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `django` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Django 폼은 「관공서 민원 창구의 신청서와 접수원」이다.**
신청서에는 칸이 정해져 있고, 칸마다 쓰는 꼴(한 줄 칸 · 여러 줄 칸 · 체크 칸)이 다르다.
접수원은 서류를 받으면 칸마다 빈칸이 없는지, 형식이 맞는지 먼저 본다.
그다음 칸 하나에 걸린 특별 규칙(「이름에 숫자만 쓰면 안 된다」)을 보고, 마지막으로 칸끼리 맞물리는 규칙(「버그 신고면 설명을 길게」)을 본다.
통과한 서류만 처리하고, 걸린 서류는 빨간 펜 표시를 달아 돌려준다.
이미 장부에 있는 양식을 그대로 베낀 신청서도 있다 — 장부 항목이 곧 신청서 칸이고, 접수가 끝나면 장부에 바로 적는다.
Django 의 `Form` 과 `ModelForm` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 신청서 | `forms.Form` 을 상속한 클래스 |
| 칸 | 폼 필드(`CharField` · `EmailField` …) |
| 칸의 생김새(한 줄 · 여러 줄 · 체크) | 위젯(`TextInput` · `Textarea` · `CheckboxSelectMultiple` …) |
| 칸마다 보는 특별 규칙 | `clean_<필드명>()` · `validators` |
| 칸끼리 맞물리는 규칙 | `clean()` |
| 통과한 서류의 정리본 | `cleaned_data` |
| 빨간 펜 표시 | `form.errors` |
| 장부를 베낀 신청서 | `ModelForm` |
| 장부에 적기 | `form.save()` |

```text
  사용자 입력(request.POST)
          │
          ▼
  ┌──────────────── 폼 ────────────────┐
  │  칸마다 기본 검사 → 칸별 규칙       │
  │            → 칸끼리 규칙            │
  └───────────────┬────────────────────┘
          ┌───────┴────────┐
       통과              실패
          │                │
   cleaned_data       errors 를 단 채
   로 처리·저장       같은 폼을 다시 보여 준다
```

## 이 주제가 답하려는 질문

1. 입력 칸과 그 생김새를 파이썬 클래스로 어떻게 선언하나?
2. 칸 하나의 규칙과 여러 칸을 함께 보는 규칙을 어디에, 어떤 차례로 거나?
3. 모델이 이미 있을 때 폼을 다시 쓰지 않고 어떻게 만들고, 검사가 끝난 값을 어떻게 DB 에 넣나?
4. 뷰에서 「빈 폼 보여 주기 → 받기 → 검사 → 처리 또는 다시 보여 주기」를 어떤 꼴로 짜나?

## 동작 방식

### (1) 폼 정의 — 필드와 위젯

**언제 쓰나** — 모델과 무관한 입력(문의 · 검색 · 댓글)을 받을 때 `forms.Form` 을 상속해 칸을 직접 선언한다.

```text
 class ContactForm(forms.Form):
     name    = CharField(min_length=2, max_length=100, widget=TextInput(attrs=…))
     email   = EmailField(widget=EmailInput(…))
     subject = ChoiceField(choices=[('', '선택하세요'), ('general', …), …])
     message = CharField(widget=Textarea(attrs={'rows': 5}), validators=[…])
     agree   = BooleanField(required=True, error_messages={'required': …})
              │
              ▼
 필드 = 「무엇을 받나 + 어떻게 검사하나」
 위젯 = 「HTML 로 어떻게 그리나」
              │
              ▼
 템플릿에서 {{ form.as_p }} 등 → <input> · <textarea> · <select> 로 그려진다
```

- 필드 클래스가 값의 종류와 기본 검사를 정한다 — `EmailField` 는 이메일 형식을 스스로 검사하고, `ChoiceField` 는 `choices` 에 있는 값만 받는다.
- `max_length` · `min_length` · `required` 같은 인자가 기본 검사에 규칙을 더한다.
- `label` 은 화면에 보일 라벨이고, `error_messages` 는 오류 종류(`'required'` 등)마다 보일 문구를 바꾼다.
- `widget` 은 같은 필드를 다른 HTML 로 그리게 한다 — `CharField` 라도 `Textarea` 를 주면 여러 줄 칸이 된다.
- `attrs` 딕셔너리는 그 HTML 태그에 붙일 속성(`class` · `placeholder` · `rows`)이다.

> **위젯(widget)** — 폼 필드를 HTML 태그로 그리는 방식을 맡은 객체다.\
> 예: `forms.Textarea(attrs={'rows': 5})` 는 다섯 줄짜리 `<textarea>` 로 그린다.

원본이 정리해 둔 필드 종류는 다음과 같다.
`CharField` · `EmailField` · `URLField` · `IntegerField` · `FloatField` · `DecimalField` · `BooleanField` · `ChoiceField` · `MultipleChoiceField` · `DateField` · `DateTimeField` · `TimeField` · `FileField` · `ImageField` · `TypedChoiceField` · `SlugField` · `UUIDField` · `JSONField`.

### (2) `is_valid()` — 검사가 흐르는 차례

**언제 쓰나** — 받은 데이터로 만든 폼(바인딩된 폼)이 쓸 만한지 판정할 때 `form.is_valid()` 를 부른다.

> **바인딩된 폼** — 사용자가 보낸 데이터를 넣어 만든 폼이다.\
> 예: `ContactForm(request.POST)` 는 바인딩된 폼이고, `ContactForm()` 은 아니다.

```text
 form.is_valid()
   │
   ├─ 칸마다 (선언한 차례로)
   │    ① 필드 기본 검사   : 빈칸? 길이? 형식? choices 안?
   │    ② validators 목록  : MinLengthValidator · 직접 쓴 함수
   │         │ 실패 → 그 칸의 errors 에 기록, ③ 은 건너뜀
   │         ▼ 통과
   │    ③ clean_<필드명>()  : self.cleaned_data['그 칸'] 을 꺼내 검사
   │         → return 한 값이 cleaned_data['그 칸'] 이 된다
   │
   └─ 칸 검사가 다 끝난 뒤 한 번
        ④ clean()          : 여러 칸을 함께 본다
             raise → 특정 칸이 아닌 「폼 전체 오류」
   │
   ▼
 errors 가 비었으면 True, 아니면 False
```

- ① 은 필드 클래스와 인자가 정한 기본 검사다.
- ② 는 `validators=[...]` 에 넣은 함수들이다 — 원본의 `message` 는 `MinLengthValidator(10, …)` 로 10자 미만을 막는다.
- ③ 은 칸 하나에 대한 추가 규칙이다. 원본 주석대로 `is_valid()` 를 부르면 자동으로 실행된다.
- ③ 에서 무엇을 `return` 하느냐가 그 칸의 최종 값이 된다 — 원본 주석: 「정제된 값을 반드시 return해야 cleaned_data에 반영됨」.
  아무것도 돌려주지 않으면 파이썬 함수는 `None` 을 돌려주므로 그 칸의 값이 `None` 으로 바뀐다.
- ③ 은 ①·② 를 통과한 칸에만 불린다(Django 동작 — 2-summary 「구현 세부사항 대 언어 보장」 참고).
  그래서 `clean_name` 안에서는 `self.cleaned_data['name']` 처럼 대괄호로 꺼내도 키가 있다.
- ④ 의 시점에는 실패한 칸이 `cleaned_data` 에 없을 수 있다.
  그래서 원본의 `clean()` 은 `cleaned_data.get('subject')` 처럼 `.get()` 으로 꺼내고, `message` 가 있을 때만(`and message`) 길이를 잰다.
- ④ 에서 `ValidationError` 를 던지면 그 오류는 어느 한 칸이 아니라 폼 전체에 붙는다 — 템플릿에서는 `form.non_field_errors` 로 꺼낸다.
- ④ 는 맨 앞에서 `super().clean()` 을 불러 부모가 하는 일을 지키고, 끝에서 `cleaned_data` 를 돌려준다.

> **cleaned_data** — 검사를 통과해 파이썬 값으로 바뀐 입력을 담은 딕셔너리다.\
> 예: `form.cleaned_data['email']` 은 검사가 끝난 이메일 문자열이다.

> **ValidationError** — 폼이나 모델의 검사가 실패했음을 알리는 Django 의 표준 예외다.\
> 예: `raise ValidationError('이름에 숫자만 사용할 수 없습니다.')`.

원본 `ContactForm` 에 대입하면 이렇다.

```text
 name='007'  → ① 통과(3자) → ③ clean_name: '007'.isdigit() 참 → name 칸 오류
 name='a'    → ① min_length=2 실패 → ③ 건너뜀 → name 칸 오류(기본 문구)
 subject='bug', message=20자 → ② 통과(10자 이상) → ④ clean: 30자 미만 → 폼 전체 오류
```

### (3) 커스텀 validator — 여러 폼이 함께 쓰는 규칙

**언제 쓰나** — 같은 규칙(금지어 · 형식)을 여러 필드나 폼에 붙이고 싶을 때 함수 하나로 빼서 `validators` 에 등록한다.

```text
 def validate_no_profanity(value):
     for word in ['spam', 'scam']:
         if word.lower() in value.lower(): raise ValidationError(f'…: {word}')
              │
              ▼
 content = CharField(validators=[validate_no_profanity])
              │
              ▼
 is_valid() 때 ② 단계에서 value 하나를 받아 호출된다
   raise  → content 칸 오류
   끝까지 → 아무 일 없음(돌려준 값은 쓰지 않는다)
```

- validator 는 원본 주석대로 「단일 인자(value)를 받아 ValidationError 발생시키는 함수」다.
- `clean_<필드명>()` 과 달리 값을 바꿔 돌려주는 자리가 아니다 — 통과면 그냥 끝나면 된다.
- 원본은 양쪽을 `lower()` 로 바꿔 대소문자를 무시한다.
- `in` 은 부분 문자열 검사라서 금지어가 다른 낱말 속에 섞여 있어도 걸린다(2-summary 「어디서 틀리나 4」).

> **validator** — 값 하나를 받아 규칙에 어긋나면 `ValidationError` 를 던지는 호출 가능한 객체다.\
> 예: `MinLengthValidator(10, '최소 10자 이상 입력하세요.')`.

### (4) ModelForm — 모델에서 폼을 뽑아낸다

**언제 쓰나** — 입력이 곧 모델(DB 행)의 필드일 때, 칸을 다시 선언하지 않고 모델 정의에서 폼을 자동으로 만든다.

```text
 class PostForm(forms.ModelForm):
     class Meta:
         model  = Post
         fields = ['title', 'content', 'category', 'tags', 'status', 'excerpt']
         widgets / labels / help_texts / error_messages = {필드명: …}
              │
              ▼
 Post 의 모델 필드 → 폼 필드로 자동 변환 (원본 팁)
 Meta 의 딕셔너리들이 그중 일부의 생김새·라벨·안내·오류 문구를 덮어쓴다
              │
              ▼
 is_valid() → 통과 → form.save() → DB 에 저장
```

- `Meta.model` 은 기준 모델이고, `Meta.fields` 는 폼에 넣을 모델 필드 목록이다.
  반대로 뺄 것만 적으려면 `exclude = ['author', 'view_count']` 를 쓴다(원본에 주석으로 있다).
- `widgets` 는 필드마다 위젯을 바꾼다 — 원본은 `tags` 를 `CheckboxSelectMultiple()` 로 바꿔 체크박스 여러 개로 고르게 한다.
- `labels` 는 모델 필드의 `verbose_name` 대신 쓸 라벨이다(원본 주석).
- `help_texts` 는 필드 아래 안내 문구이고, `error_messages` 는 「필드 → 오류 종류 → 문구」 두 겹 딕셔너리다.
- ModelForm 에서도 `clean_<필드명>()` · `clean()` 을 똑같이 쓴다.

**`instance` — 새 행인가, 있던 행인가**

```text
 PostForm(request.POST)                 → 새 Post 를 만들 폼
 PostForm(instance=post)                → 있던 post 의 값으로 칸을 채운 폼(GET 수정 화면)
 PostForm(request.POST, instance=post)  → 받은 값을 있던 post 에 덮어쓸 폼
                                           form.save() → 그 post 행을 고친다
```

- `self.instance` 는 폼에 묶인 모델 객체다 — 원본 주석대로 수정 모드일 때 `pk` 가 있다.
- 원본 `clean_title` 은 이것으로 「같은 제목의 글이 이미 있나」를 볼 때 자기 자신을 뺀다.
  `qs.exclude(pk=self.instance.pk)` 가 없으면, 제목을 고치지 않고 본문만 고쳐도 DB 에 있는 자기 자신이 「같은 제목의 글」로 잡힌다.
- 새 글이면 `self.instance.pk` 가 비어 있어 제외 단계를 건너뛴다.

> **instance** — ModelForm 에 묶인 모델 객체다.\
> 예: `PostForm(instance=post)` 의 `form.instance` 는 `post` 다.

### (5) `save(commit=False)` 와 `save_m2m()` — 저장을 미룬다

**언제 쓰나** — 폼에 없는 필드(예: 작성자)를 코드에서 채운 뒤 저장해야 할 때, 원본 팁대로 `commit=False` 로 저장을 미룬다.

```text
 obj = form.save(commit=False)   → 모델 객체만 만들고 DB 에는 아직 안 쓴다
 obj.author = request.user       → 폼에 없던 필드를 채운다
 obj.save()                      → 이제 DB 에 행을 쓴다
 form.save_m2m()                 → 미뤄 둔 ManyToMany(예: tags) 를 따로 저장한다
```

- 원본 팁: 「commit=False로 저장을 지연시켜 추가 필드를 설정할 수 있다.」
- 원본 팁: 「save_m2m()은 commit=False일 때 ManyToMany 필드를 별도 저장한다.」
- 다대다 관계는 양쪽 행이 DB 에 있어야 연결 행을 쓸 수 있다.
  그래서 `commit=False` 로 아직 저장되지 않은 객체에는 `tags` 를 붙일 수 없고, 객체를 저장한 뒤 `save_m2m()` 으로 따로 붙인다.
- 원본 예제 코드의 `post_edit_view` 는 `form.save()` 만 쓴다 — `commit=False` 흐름은 팁에만 있고 예제에는 없다.

> **ManyToMany 필드** — 한 행이 상대 모델의 행 여럿과, 상대도 이쪽 여럿과 이어지는 관계 필드다.\
> 예: 글 하나에 태그 여럿, 태그 하나에 글 여럿.

### (6) 뷰에서의 표준 패턴 — GET 은 빈 폼, POST 는 검사

**언제 쓰나** — 폼을 보여 주고 받는 함수형 뷰(FBV)를 짤 때 원본의 이 틀을 그대로 쓴다.

```text
 요청 ──┬─ GET  → form = ContactForm(initial={'subject': 'general'})
        │                                    │
        └─ POST → form = ContactForm(request.POST)
                     │
                 is_valid()?
                 ├─ True  → cleaned_data 로 처리 → redirect('contact-success')
                 └─ False ─────────────────────┐
                                               ▼
                         render(request, 'contact.html', {'form': form})
                         (GET 이면 빈 폼, 실패한 POST 면 오류가 달린 폼)
```

- POST 이고 통과하면 처리 뒤 곧바로 `redirect` 한다.
  원본 주석: 「PRG 패턴: POST 후 redirect로 새로고침 시 재제출 방지」.
- POST 인데 실패하면 `if` 를 빠져나와 맨 아래 `render` 로 간다 — 이때의 `form` 은 사용자가 쓴 값과 `errors` 를 들고 있어서 다시 그리면 입력이 남은 채 오류가 보인다.
- `initial` 은 처음 보여 줄 값만 정한다 — 바인딩되지 않은 폼의 미리 채운 칸이다.
- `post_edit_view` 는 같은 틀에 `get_object_or_404(Post, pk=pk)` 로 객체를 찾고(없으면 404), GET 에서는 `instance=post` 로 기존 값을 보여 주며, POST 에서는 `instance=post` 와 함께 바인딩해 `form.save()` 로 고친다.

> **PRG 패턴(Post/Redirect/Get)** — POST 를 처리한 뒤 다른 주소로 redirect 해서 브라우저가 GET 으로 다시 들어오게 하는 짜임이다.\
> 예: 문의를 보낸 뒤 `contact-success` 화면으로 보낸다.

## 문법 — 형태와 규칙

```python
from django import forms
from django.core.exceptions import ValidationError

class SignupForm(forms.Form):
    nickname = forms.CharField(min_length=2, max_length=20, label='닉네임')
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='비밀번호 확인')

    def clean_nickname(self):
        nick = self.cleaned_data['nickname']
        if nick.lower() == 'admin':
            raise ValidationError('쓸 수 없는 닉네임입니다.')
        return nick

    def clean(self):
        data = super().clean()
        if data.get('password') != data.get('password2'):
            raise ValidationError('비밀번호가 서로 다릅니다.')
        return data
```

- 필드는 클래스 속성으로 선언한다 — `이름 = forms.필드클래스(인자…)`.
- 필드 인자: `label` · `required` · `max_length` · `min_length` · `widget` · `validators` · `error_messages` · `choices`(선택 필드) · `initial` 등.
- 위젯은 `forms.TextInput` · `forms.EmailInput` · `forms.Textarea` · `forms.CheckboxSelectMultiple` 처럼 쓰고, `attrs={...}` 로 HTML 속성을 단다.
- 칸 하나 검사: `def clean_<필드명>(self):` — `self.cleaned_data['<필드명>']` 을 꺼내 검사하고 **값을 return** 한다.
- 여러 칸 검사: `def clean(self):` — `super().clean()` 을 먼저 부르고, `.get()` 으로 꺼내고, `cleaned_data` 를 return 한다.
- 실패는 `raise ValidationError('문구')` 로 알린다.
- validator 함수: `def f(value): …` — 어긋나면 `raise`, 아니면 그냥 끝난다. `validators=[f]` 로 붙인다.
- ModelForm: `class X(forms.ModelForm):` 안에 `class Meta:` 를 두고 `model` 과 `fields`(또는 `exclude`)를 적는다. `widgets` · `labels` · `help_texts` · `error_messages` 는 「필드명 → 값」 딕셔너리다.
- 생성자: `Form()` 빈 폼 · `Form(request.POST)` 바인딩 · `Form(initial={...})` 초기값 · `ModelForm(instance=obj)` 기존 객체 · `ModelForm(request.POST, instance=obj)` 기존 객체에 덮어쓰기.
- 결과 사용: `form.is_valid()` → `form.cleaned_data[...]` · `form.errors` · ModelForm 이면 `form.save()` 또는 `form.save(commit=False)` + `obj.save()` + `form.save_m2m()`.

## 어디서 틀리나

### 1. `clean_<필드명>()` 에서 값을 돌려주지 않는다

검사만 하고 `return` 을 빠뜨리면 함수는 `None` 을 돌려주고, 그 칸의 `cleaned_data` 가 `None` 이 된다.
오류는 나지 않으니 뷰에서 값이 사라진 뒤에야 알아챈다.
원본 주석이 「반드시 return해야 cleaned_data에 반영됨」이라고 못 박는 까닭이다.

### 2. `clean()` 에서 대괄호로 꺼낸다

`clean()` 은 칸 검사가 다 끝난 뒤 불리고, 이때 실패한 칸은 `cleaned_data` 에 없다.
`cleaned_data['message']` 로 꺼내면 `message` 가 실패한 경우 `KeyError` 가 난다.
원본처럼 `.get()` 으로 꺼내고 `None` 일 때를 건너뛰게(`and message`) 짠다.

### 3. 원본 팁 — 단일 필드는 `clean_<field>()`, 다중 필드는 `clean()`

칸 하나만 보는 규칙을 `clean()` 에 넣으면 오류가 그 칸 옆이 아니라 폼 전체 오류로 뜬다.
거꾸로 두 칸을 보는 규칙을 `clean_<field>()` 에 넣으면 다른 칸이 아직 검사되지 않았을 수 있다(칸은 선언한 차례로 검사된다).
원본 `ContactForm` 은 이름 규칙을 `clean_name` 에, 「문의 유형 × 메시지 길이」 규칙을 `clean()` 에 나눠 둔다.

### 4. 부분 문자열 검사는 너무 많이 잡는다

`validate_no_profanity` 는 `word in value` 로 본다.
`'scampi'` 처럼 금지어를 품은 다른 낱말도 걸린다.
낱말 단위로 막으려면 낱말을 쪼개 비교하는 식으로 바꿔야 한다.

### 5. `isdigit()` 검사 뒤에 `strip()` 한다

원본 `clean_name` 은 `name.isdigit()` 을 본 뒤 `name.strip()` 을 돌려준다.
앞뒤에 공백이 붙은 `' 123 '` 은 공백 때문에 `isdigit()` 이 거짓이라 통과하고, 그다음 공백이 벗겨져 `'123'` 이 저장될 수 있다.
다만 `CharField` 가 기본으로 앞뒤 공백을 먼저 벗긴다면 이 틈은 닫힌다(확인 필요 — 2-summary 「구현 세부사항 대 언어 보장」).
순서를 「벗기기 → 검사」로 두면 이 걱정이 없다.

### 6. 수정 폼의 중복 검사에서 자기 자신을 빼지 않는다

「같은 값이 이미 있나」를 DB 에 물을 때 수정 중인 행도 DB 에 있다.
원본 `clean_title` 처럼 `self.instance.pk` 가 있으면 `exclude(pk=…)` 로 자기 자신을 뺀다.

### 7. 원본 팁 — `commit=False` 뒤 `save_m2m()` 을 빠뜨린다

`form.save(commit=False)` 로 받은 객체를 `obj.save()` 해도 `tags` 같은 ManyToMany 값은 저장되지 않는다.
`form.save_m2m()` 을 따로 불러야 한다.
`commit=False` 를 쓰지 않은 보통의 `form.save()` 에서는 부를 필요가 없다.

### 8. 원본 재료와 코드가 어긋나는 곳

- 원본의 설명은 「커스텀 위젯, 폼셋」을 말하지만, 예제는 기존 위젯에 `attrs` 를 다는 것만 보이고 위젯 클래스를 새로 만들지 않으며 폼셋은 나오지 않는다.
- 원본 팁의 `commit=False` · `save_m2m()` 은 예제 코드에 없다.
- `RegexValidator` 는 import 만 하고 쓰지 않는다.
- `Post` 모델과 `redirect` · `render` · `get_object_or_404` 는 정의나 import 가 없다.
  `class Meta:` 의 `model = Post` 는 클래스를 정의하는 순간 평가되므로, 이 파일만 따로 불러오면 `Post` 가 없다는 이름 오류에서 멈춘다(원본에 근거 없음 — 추론).
  실제 프로젝트에서는 `from .models import Post` · `from django.shortcuts import redirect, render, get_object_or_404` 같은 줄이 있어야 한다.

### 9. 실패한 POST 에서 새 폼을 만든다

실패했을 때 `form = ContactForm()` 으로 새로 만들어 보여 주면 사용자의 입력과 오류가 모두 사라진다.
원본처럼 실패한 바인딩 폼을 그대로 `render` 에 넘긴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `is_valid()` 가 필드 검사 → `clean_<필드명>()` → `clean()` 을 자동으로 부른다 | Django 프레임워크(문서화된 동작) — 파이썬 언어와는 무관 |
| `clean_<필드명>()` 은 그 칸의 기본 검사 · validators 가 통과했을 때만 불린다 | Django 프레임워크의 동작 (확인 필요 — 공식 문서 문구) |
| `clean()` 에서 던진 오류는 폼 전체 오류(`non_field_errors`)가 된다 | Django 프레임워크 |
| `min_length` 실패 등의 기본 오류 문구 | Django 버전 · 언어 설정에 따라 다르다 (확인 필요) |
| `CharField` 가 기본으로 앞뒤 공백을 벗긴다 | Django 의 기본값 (확인 필요) |
| 함수가 `return` 없이 끝나면 `None` 을 돌려준다 | 파이썬 언어 |
| `str.isdigit()` · `str.lower()` · `in` 의 부분 문자열 검사 | 파이썬 언어(내장 `str` 명세) — `isdigit()` 은 아라비아 숫자 말고 다른 유니코드 숫자 문자에도 참이다 |
| `Meta.model = Post` 가 클래스 정의 때 평가된다 | 파이썬 언어(클래스 본문은 정의 시점에 실행된다) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 문의 · 검색처럼 모델과 무관한 입력 | `forms.Form` | 억지로 만든 모델 + ModelForm |
| 입력이 곧 모델의 행 | `forms.ModelForm` + `Meta.fields` | 필드를 하나하나 다시 선언한 `Form` |
| 칸 하나의 추가 규칙 | `clean_<필드명>()` | `clean()` 안의 단일 칸 검사 |
| 칸 두 개 이상이 맞물리는 규칙 | `clean()` + `.get()` | 한 칸의 `clean_<필드명>()` 에서 다른 칸 읽기 |
| 여러 폼이 같이 쓰는 규칙 | validator 함수 + `validators=[…]` | 폼마다 같은 `clean_<필드명>()` 복사 |
| 폼에 없는 필드를 채워 저장 | `save(commit=False)` → 채우기 → `save()` → `save_m2m()` | 사용자 입력 칸으로 작성자 받기 |
| 처음 보여 줄 기본 선택 | `initial={...}` | 바인딩 데이터에 기본값 섞기 |
| 기존 행 고치기 | `instance=obj` | 새 폼 + 저장 뒤 손으로 옛 행 지우기 |

## 핵심 문장

1. **필드는 「무엇을 받고 어떻게 검사하나」, 위젯은 「HTML 로 어떻게 그리나」를 맡는다.**
2. **`is_valid()` 는 칸마다 기본 검사 → validators → `clean_<필드명>()` 을 거친 뒤, 마지막에 `clean()` 을 한 번 부른다.**
3. **`clean_<필드명>()` 은 돌려준 값이 최종 값이 되고, `clean()` 에서는 실패한 칸이 빠져 있을 수 있어 `.get()` 으로 꺼낸다.**
4. **`ModelForm` 은 `Meta` 로 모델에서 폼을 뽑고, `instance` 로 새 행과 기존 행을 가르며, `save()` 로 DB 에 쓴다.**
5. **뷰는 GET 이면 빈 폼, POST 면 바인딩 → 통과 시 처리하고 redirect, 실패 시 오류 달린 폼을 다시 그린다.**

## 관련 자료

- [django-models](../01-django-models/2-summary.md)
- [django-views](../02-django-views/2-summary.md)
- [django-rest](../05-django-rest/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `django-forms`

## 용어 풀이

- **Form** — `forms.Form` 을 상속해 칸을 직접 선언한 폼 클래스다.
- **ModelForm** — 모델 정의를 바탕으로 칸이 자동으로 만들어지는 폼 클래스다.
- **필드(폼 필드)** — 값 하나를 받고 기본 검사를 맡는 폼의 칸이다.
- **위젯** — 폼 필드를 HTML 태그로 그리는 방식을 맡은 객체다.
- **attrs** — 위젯이 그리는 HTML 태그에 붙일 속성 딕셔너리다.
- **바인딩된 폼** — 사용자가 보낸 데이터를 넣어 만든 폼이다.
- **is_valid()** — 모든 검사를 돌리고 통과 여부를 `True`/`False` 로 돌려주는 메서드다.
- **cleaned_data** — 검사를 통과해 파이썬 값으로 바뀐 입력을 담은 딕셔너리다.
- **errors** — 칸별 · 폼 전체 오류 문구를 담은 폼의 속성이다.
- **non_field_errors** — 특정 칸이 아닌 폼 전체에 붙은 오류다(`clean()` 의 오류가 여기로 간다).
- **clean_<필드명>()** — 칸 하나의 추가 검사를 맡고 그 칸의 최종 값을 돌려주는 메서드다.
- **clean()** — 칸 검사가 끝난 뒤 여러 칸을 함께 보는 메서드다.
- **validator** — 값 하나를 받아 규칙에 어긋나면 `ValidationError` 를 던지는 함수(또는 호출 가능한 객체)다.
- **ValidationError** — 검사 실패를 알리는 Django 의 표준 예외다.
- **Meta** — ModelForm 안에 두는, 기준 모델과 포함 필드 등을 적는 내부 클래스다.
- **fields / exclude** — ModelForm 에 넣을 필드 목록 / 뺄 필드 목록이다.
- **verbose_name** — 모델 필드에 붙인 사람이 읽을 이름이며, `labels` 가 없을 때 라벨이 된다.
- **instance** — ModelForm 에 묶인 모델 객체다.
- **initial** — 바인딩되지 않은 폼에 처음 채워 보여 줄 값이다.
- **commit=False** — `save()` 가 모델 객체만 만들고 DB 저장은 미루게 하는 인자다.
- **save_m2m()** — `commit=False` 로 미뤄 둔 ManyToMany 값을 따로 저장하는 메서드다.
- **ManyToMany 필드** — 양쪽이 서로 여럿과 이어지는 관계 필드다.
- **FBV** — 함수형 뷰(Function-Based View), 함수 하나로 요청을 처리하는 뷰다.
- **PRG 패턴** — POST 처리 뒤 redirect 해서 새로고침 재제출을 막는 짜임이다.
- **get_object_or_404** — 조건에 맞는 객체를 가져오고, 없으면 404 응답으로 끝내는 단축 함수다.
- **폼셋** — 같은 폼을 여러 벌 한 화면에서 다루는 묶음이다(원본 설명에만 나오고 예제에는 없다).

## 더 들어가면

- **폼셋** — `forms.formset_factory(폼클래스, extra=…)` 로 같은 폼을 여러 벌 만들고, 모델용으로 `modelformset_factory` · `inlineformset_factory` 가 있다. 템플릿에는 `{{ formset.management_form }}` 이 함께 있어야 한다 (확인 필요).
- **`add_error()`** — `clean()` 안에서 `self.add_error('message', '…')` 를 쓰면 폼 전체가 아니라 특정 칸에 오류를 붙일 수 있다 (확인 필요).
- **ModelForm 의 `clean()` 재정의** — ModelForm 에서 `clean()` 을 재정의할 때 `super().clean()` 을 부르지 않으면 모델 쪽 unique 검사가 빠질 수 있다 (확인 필요).
- **모델 검사 단계** — ModelForm 은 폼 검사 뒤 입력을 `instance` 에 옮기고 모델 필드 검사와 unique 검사를 한 번 더 돈다고 알려져 있다 (확인 필요).
- **unique 제약** — 제목 중복을 폼에서만 막으면 두 요청이 거의 동시에 들어올 때 둘 다 통과할 수 있다. DB 의 `unique=True` 제약을 함께 두는 편이 안전하다 (확인 필요).
- **CBV** — `FormView` · `CreateView` · `UpdateView` 같은 클래스형 뷰가 원본 FBV 틀(GET/POST 분기 · 검사 · redirect)을 대신 해 준다 (확인 필요).
- **CSRF** — POST 폼 템플릿에는 `{% csrf_token %}` 이 있어야 기본 설정에서 요청이 거절되지 않는다 (확인 필요).
- **템플릿 렌더 방식** — `{{ form.as_p }}` 말고 `as_table` · `as_ul` 이 있고, 최근 버전에는 `as_div` 도 있다고 알려져 있다 (확인 필요).
