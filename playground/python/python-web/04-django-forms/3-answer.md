# python/python-web/04 — Django Forms (폼 처리) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `'007'` 은 `clean_name()` 에서, `'a'` 는 기본 길이 검사에서 걸린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `f1`(`'007'`): 길이 3이라 `min_length=2` · `max_length=100` 기본 검사를 통과한다. 이어 불린 `clean_name()` 에서 `'007'.isdigit()` 이 참이라 `name` 칸에 `이름에 숫자만 사용할 수 없습니다.` 가 붙는다.
- `f2`(`'a'`): 길이 1이라 기본 검사의 `min_length=2` 에서 실패한다. `name` 칸에 Django 의 기본 최소 길이 문구가 붙는다(문구는 버전 · 언어 설정에 따라 다르다 — 확인 필요).
- `clean_name()` 은 `f1` 에서만 불리고 `f2` 에서는 불리지 않는다.
- 두 폼 모두 `is_valid()` 는 `False` 다.

**왜 그런가**

`is_valid()` 는 칸마다 기본 검사 → validators → `clean_<필드명>()` 차례로 돌고, 앞 단계에서 실패한 칸은 `clean_<필드명>()` 을 건너뛴다.
나머지 칸(`email` · `subject` · `message` · `agree`)은 모두 규칙을 지키므로 오류는 `name` 칸에만 생긴다.
근거: 2-summary 「동작 방식 (2)」의 그림과 대입 예.

### 2. `False` — 오류는 폼 전체에 붙는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `ok` 는 `False` 다.
- 오류 문구는 `버그 리포트는 최소 30자 이상 상세히 작성해주세요.` 이고, 어느 칸도 아닌 폼 전체 오류(`non_field_errors`)로 붙는다.

**왜 그런가**

`message` 는 20자라 `MinLengthValidator(10, …)` 를 통과한다.
다른 칸도 모두 통과하므로 칸 검사 단계에서는 오류가 없다.
마지막 `clean()` 에서 `subject == 'bug'` 이고 `message` 가 있고 `len(message) < 30` 이 참이라 `ValidationError` 를 던진다.
`clean()` 에서 던진 오류는 특정 칸이 아니라 폼 전체에 붙는다.
근거: 2-summary 「동작 방식 (2)」의 ④ 와 대입 예.

### 3. 앞의 둘은 막히고 마지막은 조용히 끝난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `'Buy SPAM now'` → `ValidationError('부적절한 단어가 포함되어 있습니다: spam')` 이 난다.
- `'scampi pasta'` → `ValidationError('부적절한 단어가 포함되어 있습니다: scam')` 이 난다.
- `'hello world'` → 예외 없이 끝나고 `None` 을 돌려준다(돌려준 값은 쓰이지 않는다).

**왜 그런가**

함수는 값과 금지어를 둘 다 `lower()` 로 바꿔 비교하므로 `'SPAM'` 도 `'spam'` 으로 잡힌다.
문구에는 값 쪽이 아니라 목록의 낱말 `word` 가 들어가서 소문자 `spam` 이 찍힌다.
`in` 은 부분 문자열 검사라 `'scampi'` 안의 `'scam'` 도 걸린다.
금지어가 없으면 반복이 끝까지 돌고 함수가 그냥 끝난다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 4」.

### 4. redirect 없이 `contact.html` 을 그리고, 폼에는 입력값과 오류가 남아 있다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`request.method == 'POST'` 라 `form = ContactForm(request.POST)` 가 만들어지고, `is_valid()` 가 `False` 라 `if` 안의 `redirect` 에 닿지 않는다.
`if/else` 를 빠져나와 맨 아래 `render(request, 'contact.html', {'form': form})` 가 실행된다.
넘겨지는 `form` 은 사용자가 보낸 값으로 바인딩된 그 폼이라, 다시 그리면 입력이 남은 채 `errors` 의 문구가 함께 보인다.

**왜 그런가**

원본 뷰는 `render` 를 `if/else` 바깥 맨 끝에 하나만 둔다.
GET 의 빈 폼과 실패한 POST 의 폼이 같은 줄로 그려지는 짜임이다.
redirect 는 통과한 POST 에만 있다(PRG 패턴).
근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 9」.

### 5. 돌려준 값이 그 칸의 최종 값이 되기 때문이다

`is_valid()` 는 `clean_name()` 이 돌려준 값을 `cleaned_data['name']` 에 넣는다.
`return` 을 지우면 파이썬 함수는 `None` 을 돌려주므로 검사를 통과해도 `name` 이 `None` 이 된다.
예외가 나지 않아 `is_valid()` 는 `True` 인데, 뷰의 `form.cleaned_data['name']` 은 `None` 이다.
원본 주석도 「정제된 값을 반드시 return해야 cleaned_data에 반영됨」이라고 적는다.
근거: 2-summary 「동작 방식 (2)」의 ③, 「어디서 틀리나 1」, 「구현 세부사항 대 언어 보장」의 `None` 반환 줄.

### 6. `clean()` 시점에는 실패한 칸이 `cleaned_data` 에서 빠져 있을 수 있기 때문이다

`clean_name()` 은 `name` 칸의 기본 검사와 validators 를 통과했을 때만 불리므로 `cleaned_data` 에 `'name'` 이 반드시 있다.
`clean()` 은 칸 검사가 다 끝난 뒤 무조건 한 번 불리고, 그 사이 실패한 칸은 `cleaned_data` 에 없다.
예를 들어 `message` 가 10자 미만이면 `'message'` 키가 없어 대괄호로 꺼내면 `KeyError` 가 난다.
`.get()` 은 이때 `None` 을 주고, `and message` 가 `None` 에 `len()` 을 부르는 일을 막는다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 2」.

### 7. 새 글 쓰기는 멀쩡하고, 제목을 그대로 둔 수정이 막힌다

새 글이면 `self.instance.pk` 가 비어 있어 원래도 제외 단계를 건너뛰므로 동작이 바뀌지 않는다.
수정이면 고치는 글 자신이 DB 에 같은 제목으로 이미 있다.
제외 줄이 없으면 본문만 고치고 제목을 그대로 둬도 `qs.exists()` 가 참이 되어 `이미 같은 제목의 글이 존재합니다.` 로 막힌다.
제목을 다른 글과 겹치지 않는 새 제목으로 바꾸면 통과한다.
근거: 2-summary 「동작 방식 (4)」의 `instance` 해설, 「어디서 틀리나 6」.

### 8. 객체에 `author` 를 채우고 `save()` 한 뒤 `form.save_m2m()` 을 부른다

차례는 이렇다.

1. `obj = form.save(commit=False)` — 모델 객체만 받고 DB 에는 아직 쓰지 않는다.
2. `obj.author = request.user` 처럼 폼에 없는 필드를 채운다.
3. `obj.save()` — 행을 DB 에 쓴다.
4. `form.save_m2m()` — 미뤄 둔 `tags`(ManyToMany)를 저장한다.

다대다 연결은 양쪽 행이 DB 에 있어야 쓸 수 있어서, 아직 저장되지 않은 객체에는 `tags` 를 붙일 수 없다.
그래서 원본 팁대로 `commit=False` 를 썼다면 객체 저장 뒤 `save_m2m()` 을 따로 불러야 한다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 7」.

### 9. `initial` 은 보여 줄 값만, `instance` 는 저장될 모델 객체까지 정한다

`initial={'subject': 'general'}` 은 바인딩되지 않은 폼에 처음 보여 줄 값만 채운다 — 저장 대상과는 상관이 없다.
`instance=post` 는 폼을 모델 객체 하나에 묶는다.
GET 에서는 그 객체의 값으로 칸을 채우고, POST 에서 `request.POST` 와 함께 주면 `form.save()` 가 새 행이 아니라 그 행을 고친다.
`clean_title()` 처럼 검사 안에서 `self.instance.pk` 로 「지금 무엇을 고치나」를 알 수도 있다.
이 차이가 곧 `Form` 과 `ModelForm` 의 차이와 이어진다.
`Form` 은 모델과 무관해 저장할 객체가 없으니 `initial` 로 화면만 채우고, `ModelForm` 은 `Meta.model` 로 모델에 매여 있어 `instance` 와 `save()` 로 DB 행을 다룬다.
근거: 2-summary 「동작 방식 (1)」·「(4)」·「(6)」, 「문법 — 형태와 규칙」의 생성자 줄.

## 실습 정답

### 실습 1. 문의 폼 · 글 수정 폼 · 두 뷰 · 금지어 검사를 갖춘 Django 폼 모듈

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `name` 2~100자 · 한 줄 입력 | `name = forms.CharField(max_length=100, min_length=2, label='이름', widget=forms.TextInput(...))` |
| 2. `email` 이메일 형식 검사 | `email = forms.EmailField(label='이메일', widget=forms.EmailInput(...))` |
| 3. `subject` 네 선택지 | `subject = forms.ChoiceField(choices=[('', '선택하세요'), ...], label='문의 유형')` |
| 4. `message` 여러 줄 · 10자 validator | `message = forms.CharField(widget=forms.Textarea(...), validators=[MinLengthValidator(10, ...)])` |
| 5. `agree` 필수 체크 · 문구 | `agree = forms.BooleanField(required=True, error_messages={'required': '동의가 필요합니다.'})` |
| 6. 숫자만 된 이름 막기 · 공백 벗기기 | `def clean_name(self)` — `name.isdigit()` · `return name.strip()` |
| 7. 버그 리포트 30자 교차 검사 | `def clean(self)` — `super().clean()` · `.get('subject')` · `len(message) < 30` |
| 8. 기준 모델 · 필드 여섯 | `class Meta:` — `model = Post` · `fields = [...]` |
| 9. 위젯 바꾸기 | `Meta.widgets` — `TextInput` · `Textarea` · `CheckboxSelectMultiple()` |
| 10. 라벨 · 안내 · 오류 문구 | `Meta.labels` · `Meta.help_texts` · `Meta.error_messages` |
| 11. 제목 중복 검사(자기 자신 제외) | `def clean_title(self)` — `Post.objects.filter(title=title)` · `qs.exclude(pk=self.instance.pk)` · `qs.exists()` |
| 12. 문의 뷰 | `def contact_view(request)` — `ContactForm(request.POST)` · `is_valid()` · `cleaned_data` · `redirect('contact-success')` · `initial={'subject': 'general'}` · `render(..., 'contact.html', ...)` |
| 13. 글 수정 뷰 | `def post_edit_view(request, pk)` — `get_object_or_404(Post, pk=pk)` · `PostForm(request.POST, instance=post)` · `form.save()` · `redirect('post-detail', pk=post.pk)` · `PostForm(instance=post)` |
| 14. 금지어 validator | `def validate_no_profanity(value)` — `bad_words` · `word.lower() in value.lower()` · `raise ValidationError(f'...: {word}')` |
| 15. 댓글 폼 | `class CommentForm` — `content = forms.CharField(validators=[validate_no_profanity], widget=forms.Textarea(attrs={'rows': 3}))` |
| 16. 정리 출력 | 파일 끝의 `print(...)` 여덟 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/django-forms.py`

```python
# [웹 프레임워크] Django Forms (폼 처리)
# 설명: Form, ModelForm, 유효성 검사, 커스텀 위젯, 폼셋
# 팁: ModelForm은 모델 필드를 자동으로 폼 필드로 변환한다. clean_<field>()는 단일 필드, clean()은 다중 필드 검사에 사용한다. commit=False로 저장을 지연시켜 추가 필드를 설정할 수 있다. save_m2m()은 commit=False일 때 ManyToMany 필드를 별도 저장한다.

# Django Forms - 폼 정의와 유효성 검사

# forms 모듈: Form, Field, Widget 클래스 제공
from django import forms
# 내장 validator들: 길이/패턴 검사
from django.core.validators import MinLengthValidator, RegexValidator
# ValidationError: 폼/모델 유효성 실패 시 발생시키는 표준 예외
from django.core.exceptions import ValidationError


# === 1. 일반 Form ===
# forms.Form 상속: 모델과 무관한 폼 (예: 검색, 문의 등)
class ContactForm(forms.Form):
    # CharField: 문자열 입력 필드
    name = forms.CharField(
        max_length=100,
        min_length=2,
        # label: 화면에 표시될 라벨
        label='이름',
        # widget: HTML 렌더링 방식 커스터마이즈
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '이름을 입력하세요'
        })
    )
    # EmailField: 자동 이메일 형식 검증
    email = forms.EmailField(
        label='이메일',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    # ChoiceField: 선택 목록 (select 태그)
    subject = forms.ChoiceField(
        choices=[
            ('', '선택하세요'),
            ('general', '일반 문의'),
            ('bug', '버그 리포트'),
            ('feature', '기능 요청'),
        ],
        label='문의 유형'
    )
    # 다중 라인 텍스트 - Textarea 위젯
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5
        }),
        label='메시지',
        # validators 리스트로 추가 검증 규칙 부여
        validators=[MinLengthValidator(10, '최소 10자 이상 입력하세요.')]
    )
    # BooleanField: 체크박스 (필수 동의용)
    agree = forms.BooleanField(
        label='개인정보 수집 동의',
        required=True,
        # error_messages: 에러 메시지 커스터마이즈
        error_messages={'required': '동의가 필요합니다.'}
    )

    # 단일 필드 유효성 검사
    # clean_<필드명>: 해당 필드만 추가 검증 (is_valid() 호출 시 자동 실행)
    def clean_name(self):
        # cleaned_data: 기본 검증을 통과한 정제된 값
        name = self.cleaned_data['name']
        if name.isdigit():
            raise ValidationError('이름에 숫자만 사용할 수 없습니다.')
        # 정제된 값을 반드시 return해야 cleaned_data에 반영됨
        return name.strip()

    # 다중 필드 유효성 검사
    # clean(): 여러 필드 간 교차 검증
    def clean(self):
        cleaned_data = super().clean()
        subject = cleaned_data.get('subject')
        message = cleaned_data.get('message')
        # subject가 bug일 때만 message 길이 추가 검증
        if subject == 'bug' and message and len(message) < 30:
            raise ValidationError(
                '버그 리포트는 최소 30자 이상 상세히 작성해주세요.'
            )
        return cleaned_data


# === 2. ModelForm ===
# ModelForm: Model 정의를 기반으로 자동 생성되는 폼
class PostForm(forms.ModelForm):
    # 내부 Meta 클래스로 폼 메타정보 선언
    class Meta:
        model = Post  # 모델 지정
        # fields: 폼에 포함할 모델 필드 목록
        fields = ['title', 'content', 'category', 'tags', 'status', 'excerpt']
        # exclude = ['author', 'view_count']  # 제외할 필드
        # widgets: 필드별 HTML 위젯 오버라이드
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '제목을 입력하세요'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'tags': forms.CheckboxSelectMultiple(),  # 체크박스로 태그 선택
        }
        # labels: 모델 필드의 verbose_name 대신 사용할 라벨
        labels = {
            'title': '제목',
            'content': '내용',
            'excerpt': '요약',
        }
        # help_texts: 필드 아래 안내 문구
        help_texts = {
            'excerpt': '글의 간단한 요약 (선택사항)',
        }
        # error_messages: 필드별/오류종류별 메시지
        error_messages = {
            'title': {
                'max_length': '제목이 너무 깁니다.',
                'required': '제목을 입력해주세요.',
            },
        }

    # ModelForm에서도 clean 메서드 사용 가능
    def clean_title(self):
        title = self.cleaned_data['title']
        # 수정 시 중복 체크 (자기 자신 제외)
        # self.instance: 바인딩된 모델 인스턴스 (수정 모드일 때 pk 존재)
        qs = Post.objects.filter(title=title)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('이미 같은 제목의 글이 존재합니다.')
        return title


# === 3. 뷰에서 폼 사용 ===
# FBV에서 폼 처리 표준 패턴 (GET = 빈 폼, POST = 검증/저장)
def contact_view(request):
    if request.method == 'POST':
        # POST 데이터로 폼 인스턴스 생성
        form = ContactForm(request.POST)
        # is_valid(): 모든 검증 실행 후 True/False
        if form.is_valid():
            # form.cleaned_data로 정제된 데이터 접근
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            # 이메일 전송 등 처리
            # PRG 패턴: POST 후 redirect로 새로고침 시 재제출 방지
            return redirect('contact-success')
    else:
        # initial: 폼 초기값 사전 채우기
        form = ContactForm(initial={'subject': 'general'})  # 초기값
    # 템플릿에 폼 객체 전달 (템플릿에서 {{ form.as_p }} 등으로 렌더링)
    return render(request, 'contact.html', {'form': form})


def post_edit_view(request, pk):
    # 객체가 없으면 자동 404
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        # instance 인자: 기존 객체에 변경사항 적용
        form = PostForm(request.POST, instance=post)  # 기존 객체 바인딩
        if form.is_valid():
            form.save()  # ModelForm은 save()로 DB 저장
            return redirect('post-detail', pk=post.pk)
    else:
        # 수정 폼은 instance로 초기화하여 기존 값 표시
        form = PostForm(instance=post)  # 기존 데이터로 폼 채우기
    return render(request, 'blog/post_form.html', {'form': form})


# === 4. 커스텀 Validator ===
# validator: 단일 인자(value)를 받아 ValidationError 발생시키는 함수
def validate_no_profanity(value):
    bad_words = ['spam', 'scam']
    for word in bad_words:
        if word.lower() in value.lower():
            raise ValidationError(f'부적절한 단어가 포함되어 있습니다: {word}')

class CommentForm(forms.Form):
    content = forms.CharField(
        # validators 리스트에 함수 등록
        validators=[validate_no_profanity],
        widget=forms.Textarea(attrs={'rows': 3})
    )


# === 5. 폼 필드 타입 정리 ===
# CharField, EmailField, URLField, IntegerField, FloatField,
# DecimalField, BooleanField, ChoiceField, MultipleChoiceField,
# DateField, DateTimeField, TimeField, FileField, ImageField,
# TypedChoiceField, SlugField, UUIDField, JSONField

print("Django Forms 핵심 정리")
print("="*50)
print("Form: 수동 필드 정의, 유연한 유효성 검사")
print("ModelForm: 모델 기반 자동 생성, save()로 DB 저장")
print("clean_<field>(): 단일 필드 유효성 검사")
print("clean(): 다중 필드 교차 검사")
print("widgets: 폼 필드 HTML 위젯 커스터마이징")
print("initial: 폼 초기값 / instance: 기존 객체 바인딩")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `django` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**

- 칸 하나의 규칙은 필드 인자 · `validators` · `clean_<필드명>()` 으로, 칸끼리의 규칙은 `clean()` 으로 나눠 건다.
- `clean_<필드명>()` 은 반드시 값을 돌려주고, `clean()` 은 `super().clean()` 으로 시작해 `.get()` 으로 꺼내고 `cleaned_data` 를 돌려준다.
- `PostForm` 은 칸을 다시 선언하지 않고 `Meta` 로 모델에서 뽑은 뒤 위젯 · 라벨 · 안내 · 오류 문구만 덮어쓴다.
- 수정 화면의 중복 검사는 `self.instance.pk` 로 자기 자신을 뺀다.
- 두 뷰 모두 「POST → 바인딩 → 통과 시 처리 후 redirect / 그 밖은 같은 `render`」 틀이고, 수정 뷰는 GET · POST 모두 `instance=post` 를 넘긴다.
- 정답 코드에는 `Post` 와 `redirect` · `render` · `get_object_or_404` 의 import 가 없고, 팁의 `commit=False` · `save_m2m()` 도 쓰이지 않는다 — 프로젝트에 둘 때 import 를 보태고, 작성자 같은 필드를 채워야 하면 2-summary 「동작 방식 (5)」의 흐름을 덧붙인다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `django` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
