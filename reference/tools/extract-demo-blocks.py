#!/usr/bin/env python3
"""문서에서 `demo` 블록을 뽑아 다시 띄워 「보이는 것」이 실제로 그런지 대조한다.

왜 필요한가
-----------
`render-rules.md` 의 「쓴 사람이 직접 확인한다」는 **쓰는 동안** 확인하라는 규칙이다.
그것만으로는 **옮겨 적기 사고**가 안 걸린다 — 실제로 띄워 보고 값을 받아 놓고
문서로 옮기는 과정에서 틀리는 것. SQL 60주제에서 같은 유형이 4건 나왔고
넷 다 손으로 재배치한 블록이었다. 그래서 `extract-exec-blocks.py` 의 demo 판이 필요하다.

★ **이 도구는 「보이는 것」이 맞는지 판정하지 않는다.** 자연어라 기계가 못 읽는다.
하는 일은 **블록을 뽑아 실제로 띄우고 계산값을 덤프하는 것**까지다 —
그 덤프와 문서의 서술을 맞춰 보는 것은 사람이 한다. 판정을 자동화한 척하지 않는다.

쓰는 법
-------
    python3 extract-demo-blocks.py <문서.md ...>            # 블록 목록만
    python3 extract-demo-blocks.py --render <문서.md ...>   # 띄워서 계산값까지
    python3 extract-demo-blocks.py --render --window-size=1200,800 <문서.md ...>
    python3 extract-demo-blocks.py --render --shot=/tmp/shots <문서.md ...>   # 픽셀까지 볼 때

`--render` 는 Chrome headless 를 쓴다. 블록에는 `<!doctype>`·`<body>` 가 없으므로
**래퍼를 붙여서** 띄운다(`render-rules.md` 에 적힌 함정 — 안 붙이면 기본 여백 때문에
실측 좌표가 문서와 어긋난다).

한계 — 이 도구가 못 보는 것
--------------------------
- **입력이 걸린 것**(`:hover`·`:focus`·`:active`)은 못 켠다. CDP 로 `Input.dispatch*` 를
  넣어야 하고, 그건 블록마다 무엇을 누를지 사람이 정해야 한다.
- **시간이 걸린 것**(전환·애니메이션)은 한 시점만 본다.
- ★★ **웹폰트가 걸린 것은 「그럴듯하게 틀린」 값을 낸다.** `--dump-dom` 은 `document.fonts.ready` 를
  기다리지 않으므로 **폴백 글꼴로 잰 폭**이 나온다(실측: 120px 이어야 할 것이 82px 로 나왔다).
  값이 틀리게가 아니라 **그럴듯하게** 나오므로 눈으로는 안 잡힌다 — 실제로 문서가 맞는데 도구가 틀렸다.
- 그래서 **「이 블록은 이 도구로 확인이 안 된다」는 목록을 같이 낸다.** 조용히 통과시키지 않는다.
  ★ 이 도구는 지금까지 **거짓 합격을 낼 뻔한 적이 한 번 있다**(위 웹폰트 건).
  **「누락 0」은 「전부 봤다」가 아니라 「내가 보는 방식으로는 다 봤다」는 뜻**이라는 규칙이 여기에도 적용된다.
"""
import re, sys, subprocess, tempfile, os, json

FENCE = re.compile(r'^```(\w+)\s+demo\s*$')
CAPTION = re.compile(r'^>\s*\*\*(보이는 것|바꿔 볼 것|실측)\*\*')
NEEDS_INPUT = re.compile(r':hover|:focus|:active|:target|transition|animation|@keyframes')
# ★ 웹폰트가 걸린 블록은 이 도구가 「그럴듯하게 틀린」 값을 낸다 — 아래 한계 절 참조.
NEEDS_FONT = re.compile(r'@font-face|font-family\s*:\s*["\']?[A-Z]')

PROBE = """
<script>
var out=[];
document.querySelectorAll('*').forEach(function(el){
  if(['SCRIPT','STYLE','HEAD','HTML','PRE'].indexOf(el.tagName)>=0) return;
  var c=getComputedStyle(el), r=el.getBoundingClientRect();
  // ★ background-color 만 찍으면 그라디언트가 rgba(0,0,0,0) 으로 보여
  //   「색이 안 먹었다」와 「그라디언트다」가 구분되지 않는다.
  var bg=c.backgroundColor;
  if(c.backgroundImage && c.backgroundImage!=='none') bg += ' +image('+c.backgroundImage.slice(0,40)+')';
  out.push([el.tagName.toLowerCase()+(el.id?'#'+el.id:'')+(el.className&&typeof el.className==='string'?'.'+el.className.trim().replace(/\\s+/g,'.'):''),
    'rect='+Math.round(r.left)+','+Math.round(r.top)+' '+Math.round(r.width)+'x'+Math.round(r.height),
    'color='+c.color,'bg='+bg,'display='+c.display,
    'margin='+c.marginTop+'/'+c.marginBottom].join('  '));
});

// ★★ 「쓴 선언이 아무 요소에도 안 먹은 것」을 찾는다.
//   CSS 는 에러가 없는 언어라 명시도에 져도 조용하다. demo 에서 실제로 3건이 이 모양이었다
//   (`.col i` 가 `.r` 을 이겨서 색이 안 바뀌었는데 화면은 그럴듯했다).
//   ⚠️ 문맥 없이 정규화할 수 있는 속성만 본다 — 아래 목록 밖은 검사하지 않는다(거짓 양성 방지).
var SAFE=['color','background-color','font-weight','font-style','display','position','float',
          'clear','text-align','visibility','overflow','overflow-x','overflow-y','z-index',
          'opacity','text-decoration-line','flex-direction','justify-content','align-items',
          'align-content','flex-wrap','white-space','word-break','overflow-wrap','border-style',
          'vertical-align','box-sizing','mix-blend-mode','isolation'];
var scratch=document.createElement('div');
scratch.style.position='absolute';scratch.style.visibility='hidden';
document.body.appendChild(scratch);
function norm(prop,val){
  scratch.style.cssText='';
  try{ scratch.style.setProperty(prop,val); }catch(e){ return null; }
  var v=getComputedStyle(scratch).getPropertyValue(prop);
  return v||null;
}
var dead=[];
for(var i=0;i<document.styleSheets.length;i++){
  var rules;
  try{ rules=document.styleSheets[i].cssRules; }catch(e){ continue; }
  for(var j=0;j<rules.length;j++){
    var rule=rules[j];
    if(!rule.selectorText||!rule.style) continue;
    var els;
    try{ els=document.querySelectorAll(rule.selectorText); }catch(e){ continue; }
    for(var k=0;k<rule.style.length;k++){
      var prop=rule.style[k];
      if(SAFE.indexOf(prop)<0) continue;
      var want=norm(prop,rule.style.getPropertyValue(prop));
      if(want===null) continue;
      var won=false;
      for(var m=0;m<els.length;m++){
        if(getComputedStyle(els[m]).getPropertyValue(prop)===want){ won=true; break; }
      }
      if(els.length===0) dead.push(rule.selectorText+' { '+prop+' } — 이 선택자가 잡는 요소가 없다');
      else if(!won) dead.push(rule.selectorText+' { '+prop+': '+rule.style.getPropertyValue(prop)
                              +' } — 잡히기는 했는데 어느 요소에도 안 먹었다(명시도에 졌을 수 있다)');
    }
  }
}
scratch.remove();
if(dead.length) out.push('','★ 먹지 않은 선언 '+dead.length+'개 (문맥 없이 정규화되는 속성만 검사)','  '+dead.join('\\n  '));

var p=document.createElement('pre');
p.id='__probe';
p.textContent='<<<BEGIN>>>\\n'+out.join('\\n')+'\\n<<<END>>>';
document.body.appendChild(p);
</script>
"""


def blocks(path):
    """`demo` 펜스와 바로 뒤의 캡션 줄들을 함께 뽑는다."""
    lines = open(path, encoding='utf-8').read().split('\n')
    out, i = [], 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            i += 1
            continue
        start, lang, body = i + 1, m.group(1), []
        i += 1
        while i < len(lines) and not lines[i].startswith('```'):
            body.append(lines[i]); i += 1
        i += 1
        caps = []
        while i < len(lines):
            if not lines[i].strip():
                i += 1; continue
            if CAPTION.match(lines[i]):
                caps.append(lines[i].strip()); i += 1
            else:
                break
        src = '\n'.join(body)
        out.append(dict(file=path, line=start, lang=lang, src=src, captions=caps,
                        needs_input=bool(NEEDS_INPUT.search(src)),
                        needs_font=bool(NEEDS_FONT.search(src))))
    return out


def shoot(b, out_dir, idx, window=None):
    """블록을 PNG 로 찍는다 — 계산값이 같고 픽셀만 다른 경우를 잡기 위한 것.

    보간 색 공간·영역 잘림·타일 `round` 는 `getComputedStyle` 에 아무 흔적을 안 남긴다.
    찍은 PNG 는 **확인용이고 저장소에 넣지 않는다**(`render-rules.md`).
    """
    doc = ('<!doctype html><meta charset="utf-8"><title>demo</title>\n'
           '<style>body{margin:0}</style>\n' + b['src'])
    fd, p = tempfile.mkstemp(suffix='.html'); os.write(fd, doc.encode()); os.close(fd)
    png = os.path.join(out_dir, 'demo-%03d.png' % idx)
    try:
        cmd = ['google-chrome', '--headless', '--disable-gpu', '--no-sandbox',
               '--screenshot=' + png]
        if window:
            cmd.append('--window-size=' + window)
        cmd.append(p)
        subprocess.run(cmd, capture_output=True, timeout=60)
        return png if os.path.exists(png) else None
    finally:
        os.unlink(p)


def render(b, window=None):
    """블록을 띄워 계산값을 덤프한다.

    ★ `window` 로 창 크기를 지정할 수 있다 — 뷰포트·컨테이너 단위가 주제인 문서는
    기본 창(800x600, innerWidth 780)에서 재면 본문 실측과 숫자가 갈린다.
    ⚠️ **Chrome 의 창 폭 하한은 500 이다** — `--window-size=375,667` 을 줘도 `innerWidth` 가 500 으로 나온다.
    좁은 화면 조건은 이 도구로 만들 수 없다.
    """
    doc = ('<!doctype html><meta charset="utf-8"><title>demo</title>\n'
           '<style>body{margin:0}</style>\n' + b['src'] + PROBE)
    fd, p = tempfile.mkstemp(suffix='.html'); os.write(fd, doc.encode()); os.close(fd)
    try:
        cmd = ['google-chrome', '--headless', '--disable-gpu', '--no-sandbox']
        if window:
            cmd.append('--window-size=' + window)
        cmd += ['--dump-dom', p]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        m = re.search(r'&lt;&lt;&lt;BEGIN&gt;&gt;&gt;(.*?)&lt;&lt;&lt;END&gt;&gt;&gt;', r.stdout, re.S)
        if not m:
            m = re.search(r'<<<BEGIN>>>(.*?)<<<END>>>', r.stdout, re.S)
        return m.group(1).strip() if m else '(프로브 출력 없음)'
    finally:
        os.unlink(p)


if __name__ == '__main__':
    argv = sys.argv[1:]
    window = shot_dir = None
    for a in list(argv):
        if a.startswith('--window-size='):
            window = a.split('=', 1)[1]; argv.remove(a)
        elif a.startswith('--shot='):
            shot_dir = a.split('=', 1)[1]; argv.remove(a)
    args = [a for a in argv if a != '--render']
    do_render = '--render' in argv
    allb, no_caption, cannot = [], [], []
    for f in args:
        for b in blocks(f):
            allb.append(b)
            if not any('보이는 것' in c for c in b['captions']):
                no_caption.append(b)
            if b['needs_input'] or b['needs_font']:
                cannot.append(b)
            if do_render:
                print('===== %s:%d  (%s)' % (b['file'], b['line'], b['lang']))
                for c in b['captions']:
                    print('  ' + c)
                print(render(b, window))
                if shot_dir:
                    os.makedirs(shot_dir, exist_ok=True)
                    png = shoot(b, shot_dir, len(allb), window)
                    print('  PNG: ' + (png or '(찍히지 않음)'))
                print()
    print('demo 블록 %d개' % len(allb), file=sys.stderr)
    if no_caption:
        print('★ 「보이는 것」이 없는 블록 %d개 — render-rules 가 필수로 정한다'
              % len(no_caption), file=sys.stderr)
        for b in no_caption:
            print('   %s:%d' % (b['file'], b['line']), file=sys.stderr)
    if cannot:
        print('※ 이 도구로는 확인이 안 되는 블록 %d개 — 사람이 따로 확인한다' % len(cannot),
              file=sys.stderr)
        for b in cannot:
            why = []
            if b['needs_input']:
                why.append('입력·시간 → CDP 로')
            if b['needs_font']:
                why.append('웹폰트 → fonts.ready 뒤에 재라 (이 도구는 폴백 값을 낸다)')
            print('   %s:%d  [%s]' % (b['file'], b['line'], ' / '.join(why)), file=sys.stderr)
    sys.exit(1 if no_caption else 0)
