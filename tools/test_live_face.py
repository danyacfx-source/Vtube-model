"""Integration test. Start live-face/serve.py first; requires Playwright and Chromium."""
import argparse,base64,json,time
parser=argparse.ArgumentParser();parser.add_argument("--image",required=True);args=parser.parse_args()
from playwright.sync_api import sync_playwright
payload=base64.b64encode(open(args.image,'rb').read()).decode()
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1280,'height':1000});page.set_default_timeout(90000)
    errors=[];remote=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:remote.append(r.url) if not r.url.startswith(('http://127.0.0.1:8765/','blob:','data:')) else None)
    page.goto('http://127.0.0.1:8765/',wait_until='networkidle')
    page.wait_for_function('window.LiveFruit && LiveFruit.getState().features===3')
    count=page.evaluate('''async data=>{const img=new Image();img.src='data:image/png;base64,'+data;await img.decode();window.testFace=img;return await LiveFruit.testImage(img);}''',payload)
    print('LANDMARKS',count,flush=True);assert count==468
    page.wait_for_timeout(300)
    print('LIVE',page.evaluate('LiveFruit.getState()'),flush=True)
    assert page.evaluate('LiveFruit.getState().visible')==3
    page.screenshot(path='/tmp/live-fruit-positive.png')
    page.select_option('#fruit','pineapple');page.wait_for_function("LiveFruit.getState().model==='pineapple' && document.querySelector('#status').textContent.includes('готова')")
    assert page.evaluate('LiveFruit.getState().features')==3
    assert page.evaluate('LiveFruit.getState().visible')==0
    assert page.evaluate('LiveFruit.testImage(window.testFace)')==468
    page.select_option('#background','blue');page.click('#output');assert page.locator('body').evaluate("e=>e.classList.contains('output-mode')")
    page.screenshot(path='/tmp/live-fruit-pineapple.png')
    page.keyboard.press('Escape');assert not page.locator('body').evaluate("e=>e.classList.contains('output-mode')")
    page.wait_for_timeout(700)
    blank=page.evaluate('''async()=>{const c=document.createElement('canvas');c.width=512;c.height=512;c.getContext('2d').fillRect(0,0,512,512);return await LiveFruit.testImage(c);}''')
    assert blank==0;assert page.evaluate('LiveFruit.getState().visible')==0
    print('NO_FACE',page.evaluate('LiveFruit.getState()'),flush=True)
    print('ERRORS',errors,flush=True);print('EXTERNAL',remote,flush=True);assert not errors and not remote
    browser.close()
