"""Virtual-webcam lifecycle test; fixture is a Y4M video with one visible face."""
import argparse
parser=argparse.ArgumentParser();parser.add_argument("--camera",required=True);args=parser.parse_args()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-video-capture='+args.camera])
    page=browser.new_page(viewport={'width':1280,'height':1000});page.set_default_timeout(60000)
    errors=[];external=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:external.append(r.url) if not r.url.startswith(('http://127.0.0.1:8765/','blob:','data:')) else None)
    page.goto('http://127.0.0.1:8765/',wait_until='networkidle');page.wait_for_function('window.LiveFruit?.getState().features===3')
    page.click('#start');page.wait_for_function('LiveFruit.getState().running && LiveFruit.getState().visible===3')
    print('CAMERA_START',page.evaluate('LiveFruit.getState()'),flush=True)
    assert page.evaluate("document.querySelector('#cameraVideo').srcObject.getAudioTracks().length") == 0
    page.evaluate("window.oldTracks=document.querySelector('#cameraVideo').srcObject.getTracks()")
    page.click('#calibrate');page.select_option('#fruit','pineapple');page.wait_for_function("LiveFruit.getState().model==='pineapple' && LiveFruit.getState().visible===3")
    page.click('#stop');page.wait_for_function('!LiveFruit.getState().running && LiveFruit.getState().visible===0')
    assert page.evaluate("oldTracks.every(t=>t.readyState==='ended')")
    assert page.evaluate("document.querySelector('#cameraVideo').srcObject===null")
    print('CAMERA_STOP_RELEASED',flush=True)
    page.click('#start');page.wait_for_function('LiveFruit.getState().running && LiveFruit.getState().visible===3');page.click('#stop')
    print('CAMERA_RESTART_PASS',flush=True)
    assert not errors and not external
    print('ERRORS',errors,'EXTERNAL',external,flush=True)
    browser.close()
