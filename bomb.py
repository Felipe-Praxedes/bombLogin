from platform import python_branch
from cv2 import cv2

from os import listdir
from src.logger import logger, loggerMapClicked
from random import randint
from random import random
import math
import pygetwindow
import numpy as np
import mss
import pyautogui
import time
import sys

import yaml

msg = """
>>---> Pressione ctrl + c para parar o bot.
"""

print(msg)
time.sleep(2)

if __name__ == '__main__':
    stream = open("config.yaml", 'r')
    c = yaml.safe_load(stream)

ct = c['threshold']
ch = c['home']

pause = c['time_intervals']['interval_between_moviments']
pyautogui.PAUSE = pause

pyautogui.FAILSAFE = False
hero_clicks = 0
login_attempts = 0
last_log_is_progress = False

def addRandomness(n, randomn_factor_size=None):
    if randomn_factor_size is None:
        randomness_percentage = 0.1
        randomn_factor_size = randomness_percentage * n

    random_factor = 2 * random() * randomn_factor_size
    if random_factor > 5:
        random_factor = 5
    without_average_random_factor = n - randomn_factor_size
    randomized_n = int(without_average_random_factor + random_factor)
    return int(randomized_n)

def moveToWithRandomness(x,y,t):
    pyautogui.moveTo(addRandomness(x,10),addRandomness(y,10),t+random()/2)

def remove_suffix(input_string, suffix):
    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string

def load_images():
    file_names = listdir('./targets/')
    targets = {}
    for file in file_names:
        path = 'targets/' + file
        targets[remove_suffix(file, '.png')] = cv2.imread(path)

    return targets

images = load_images()

def loadHeroesToSendHome():
    file_names = listdir('./targets/heroes-to-send-home')
    heroes = []
    for file in file_names:
        path = './targets/heroes-to-send-home/' + file
        heroes.append(cv2.imread(path))

    print('>>---> %d heroes that should be sent home loaded' % len(heroes))
    return heroes

if ch['enable']:
    home_heroes = loadHeroesToSendHome()

full_stamina = cv2.imread('targets/full-stamina.png')

def show(rectangles, img = None):

    if img is None:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            img = np.array(sct.grab(monitor))

    for (x, y, w, h) in rectangles:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255,255,255,255), 2)

    cv2.imshow('img',img)
    cv2.waitKey(0)

def printSreen():
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = np.array(sct.grab(monitor))
        return sct_img[:,:,:3]

def clickBtn(img,name=None, timeout=3, threshold = ct['default']):
    logger(None, progress_indicator=True)
    if not name is None:
        pass

    start = time.time()
    while(True):
        matches = positions(img, threshold=threshold)
        if(len(matches)==0):
            hast_timed_out = time.time()-start > timeout
            if(hast_timed_out):
                if not name is None:
                    pass

                return False

            continue

        x,y,w,h = matches[0]
        pos_click_x = x+w/2
        pos_click_y = y+h/2

        moveToWithRandomness(pos_click_x,pos_click_y,0.1)
        pyautogui.click()
        return True

def positions(target, threshold=ct['default'],img = None):
    if img is None:
        img = printSreen()
    result = cv2.matchTemplate(img,target,cv2.TM_CCOEFF_NORMED)
    w = target.shape[1]
    h = target.shape[0]

    yloc, xloc = np.where(result >= threshold)

    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    return rectangles

def scroll():

    commoms = positions(images['commom-text'], threshold = ct['commom'])
    if (len(commoms) == 0):
        return
    x,y,w,h = commoms[len(commoms)-1]

    moveToWithRandomness(x,y,0.5)

    if not c['use_click_and_drag_instead_of_scroll']:
        pyautogui.scroll(-c['scroll_size'])
    else:
        pyautogui.dragRel(0,-c['click_and_drag_amount'],duration=1, button='left')

def clickButtons():
    buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])
    # print('buttons: {}'.format(len(buttons)))
    for (x, y, w, h) in buttons:
        moveToWithRandomness(x+(w/2),y+(h/2),0.3)
        pyautogui.click()
        global hero_clicks
        hero_clicks = hero_clicks + 1
        # cv2.rectangle(sct_img, (x, y) , (x + w, y + h), (0,255,255),2)
        if hero_clicks > 20:
            logger('too many hero clicks, try to increase the go_to_work_btn threshold')
            return
    return len(buttons)

def isWorking(bar, buttons):
    y = bar[1]

    for (_,button_y,_,button_h) in buttons:
        isBelow = y < (button_y + button_h)
        isAbove = y > (button_y - button_h)
        if isBelow and isAbove:
            return False
    return True

def clickGreenBarButtons():
    offset = 120

    green_bars = positions(images['green-bar'], threshold=ct['green_bar'])
    buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])
    not_working_green_bars = []

    for bar in green_bars:
        if not isWorking(bar, buttons):
            not_working_green_bars.append(bar)
             
    for (x, y, w, h) in not_working_green_bars:
        moveToWithRandomness(x+offset+(w/2),y+(h/2),0.3)
        pyautogui.click()

    red_bars = positions(images['red-bar'], threshold=ct['green_bar'])
    buttons = positions(images['go-work'], threshold=ct['go_to_work_btn'])
    not_working_red_bars = []

    for bar in red_bars:
        if not isWorking(bar, buttons):
            not_working_red_bars.append(bar)
    
    for (x, y, w, h) in not_working_red_bars:
        moveToWithRandomness(x+offset+(w/2),y+(h/2),0.3)
        pyautogui.click()

    return len(not_working_green_bars)

def goToHeroes():
    global login_attempts
    clickBtn(images['go-back-arrow'])

    if clickBtn(images['hero-icon'], name ='hero', timeout=10):
        login_attempts = 0

    clickBtn(images['bar-wait'], name='commom', timeout = 10)

def goToGame():
    global login_attempts
    clickBtn(images['x'])

    if clickBtn(images['treasure-hunt-icon'], name='treasure', timeout = 5):
        login_attempts = 0

def refreshHeroesPositions():
    logger(' ')
    logger('Reposicionando Heróis')
    clickBtn(images['go-back-arrow'])
    clickBtn(images['treasure-hunt-icon'], name='treasure', timeout = 5)

def login(username, password):
    global login_attempts
    logger(' ')
    logger('Checkando se o Bomb não foi desconectado ')
    pyautogui.hotkey('enter')

    if login_attempts > 3:
        logger('Resetar o baguio...')
        login_attempts = 0
        pyautogui.hotkey('ctrl','f5')
        return
    
    if clickBtn(images['username'], name='sign button', timeout=1):
        pyautogui.typewrite(username)

        if clickBtn(images['password'], name='sign button', timeout = 1):
            pyautogui.typewrite(password)

        if clickBtn(images['login-btn'], name='okBtn', timeout=1):
            login_attempts = login_attempts + 1
    
    if clickBtn(images['ok'], name='okBtn', timeout=2):
        desconectado = True
        tempo = 30
    else:
        desconectado = False
        tempo = 2
        
    if clickBtn(images['connect-wallet'], name='connectWalletBtn', timeout = tempo):
        logger('Conecatar a carteira, vai bomb!')

        login_attempts = login_attempts + 1

        if clickBtn(images['username'], name='sign button', timeout=10):
            pyautogui.typewrite(username)

            if clickBtn(images['password'], name='signBtn', timeout = 1):
                pyautogui.typewrite(password)

            if clickBtn(images['login-btn'], name='okBtn', timeout=1):
                login_attempts = login_attempts + 1

            if desconectado:
                if clickBtn(images['treasure-hunt-icon'], name='teasureHunt', timeout=25):
                    login_attempts = 0
   
def refreshHeroes():
    global hero_clicks
    logger(' ')
    logger('Procurando Heróis para minerar')

    goToHeroes()

    buttonsClicked = 1

    empty_scrolls_attempts = c['scroll_attemps']

    buttonsClicked = clickGreenBarButtons()

    while(empty_scrolls_attempts >0):

        scroll()
        time.sleep(1)

        buttonsClicked = clickGreenBarButtons()

        empty_scrolls_attempts = empty_scrolls_attempts - 1
       
    if hero_clicks > 1:
        logger('{} Heróis enviados para o mapa'.format(hero_clicks))
        hero_clicks = 0
    else:
        logger('{} Herói enviado para o mapa'.format(hero_clicks))
        hero_clicks = 0
 
    goToGame()

def main():
    time.sleep(5)
    t = c['time_intervals']
    windows = []

    for w in pygetwindow.getWindowsWithTitle('bombcrypto'):
        windows.append({
            "window": w,
            "login" : 0,
            "heroes" : 0,
            "new_map" : 0,
            "refresh_heroes" : 0,
            })

     # https://app.bombcrypto.io/webgl/index.html

    while True:
        now = time.time()
        telas = len(windows)
        loginX = 0

        for last in windows:
            last["window"].activate()
            time.sleep(2)

            loginList = [
                ["FelipeBomb2","bomb2022"],
                ["FelipeBomb","bomb2022"],
                # ["Whanzz","15051994"],
                ["DTanami","T@nami12"],
                ["KTanami","T@nami12"],
                ["guidi12345","agm125558"],
            ]
            
            username = loginList[loginX][0]
            password = loginList[loginX][1]

            if now - last["login"] > addRandomness(t['check_for_login'] * 60):
                sys.stdout.flush()
                last["login"] = now
                login(username, password)

            if now - last["heroes"] > addRandomness(t['send_heroes_for_work'] * 60):
                last["heroes"] = now
                refreshHeroes()
            
            time.sleep(2)
            loginX = loginX + 1 
            logger(None, progress_indicator=True)

        logger('Visualizando %d telas com os Heróis minerando... ' % telas)

        tempo = math.floor( 20 / telas)
        tempoChest = math.floor( 16 / telas)

        tl = 1
        while tl <=7:
            for wx in windows:
                mapaLogin = loginList[(tl -1)%telas][0]

                logger(None, progress_indicator=True)

                wx["window"].activate()
                # if tl == 3:
                #     clickBtn(images['chest'])
                #     time.sleep(2)
                #     clickBtn(images['chest-x'])
                #     time.sleep(tempoChest)

                if tl == 7:
                    refreshHeroesPositions()

                else:
                    clickBtn(images['key'])
                    time.sleep(tempo)

            tl = tl + 1
                
        sys.stdout.flush()

        time.sleep(1)
            
main()


