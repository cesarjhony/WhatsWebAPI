import time
import logging
import sys
import os
import ctypes
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.common.exceptions import NoSuchElementException
from configparser import SafeConfigParser,NoOptionError,NoSectionError,MissingSectionHeaderError
import psutil
import zmq #servidor para receber mensagem do outro script
import threading #iniciar servidor de forma asyncrona
from optparse import OptionParser
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from win32 import win32gui
from win32.lib import win32con
import win32com.client
import pythoncom #https://stackoverflow.com/questions/26745617/win32com-client-dispatch-cherrypy-coinitialize-has-not-been-called
#http://tarunlalwani.com/post/reusing-existing-browser-session-selenium/
#https://stackoverflow.com/questions/30435749/python-selenium-firefox-cant-start-firefox-with-specified-profile-path/33350778#33350778
sys.stdout = open("start_log.txt", "w")
logging.basicConfig(filename='start.log',level=logging.DEBUG)
#driver = None #deixar a variavel no escopo global pra facilitar uso

class AutomationW:
    def __init__(self, withServer=True):
        self.configFile = 'connection.txt'
        self.driver = None
        self.context = None
        if not self.isStarted():
            print("entrou no if")
            self.setStarted(True)
            self.driver = self.startSelenium()
            self.getUrlWhatsapp()
            self.setConnectionFile()
            if withServer:
                self.context = self.startServidor()#6970 by default
    def __del__(self):
        if not self.driver == None:
            self.setStarted(False)
        if not self.context == None:
            self.context.destroy()
    def isRunning(self):
        driver_process = psutil.Process(self.driver.service.process.pid)
        if driver_process.is_running():
            #print ("driver is running")
            firefox_process = driver_process.children()
            if firefox_process:
                firefox_process = firefox_process[0]
                if firefox_process.is_running():
                    #print("Firefox is still running, we can quit")
                    return True
                else:
                    print("Browser is dead, can't quit. Let's kill the driver")
                    firefox_process.kill()
                    return False
        else:
            print("driver has died")
            return False
    
    #DEPRECATED
    def getStartOptions(self):
        usage = "usage: %prog [--force]"
        parser = OptionParser(usage)
        parser.add_option("-f", "--force",
                      action="store_true", dest="force", default=False,
                      help="Forcar inicializacao")
        (options, args) = parser.parse_args()
        force = options.force
        return force #bool, inicializacao forcada
    
    def waitWhileIsOpen(self):
        if not self.driver == None:
            while (self.isRunning() == True):
                time.sleep(10) #verificacao de 10 em 10 segundos
            self.driver.quit()
    
    def isPidRunning2(self,pid):        
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x100000
        process = kernel32.OpenProcess(SYNCHRONIZE, 0, pid)
        if process != 0:
            print("isPidRunning() == True")
            return True
        else:
            print("isPidRunning() == False")
            return False
    def isPidRunning(self,pid):        
        try:
            process = psutil.Process(pid)
            if process.name() == "python.exe":
                print("isPidRunning() == True")
                return True
            else:
                print("isPidRunning() == False")
                return False
        except:
            print("isPidRunning() == False")
            return False
    def isStarted(self):
        config = SafeConfigParser()
        config.read(self.configFile)
        jaExisteInstancia=False
        try:
            if config.get('main', 'started') != 'False':
                pid = int(config.get('main', 'started'))
                jaExisteInstancia= self.isPidRunning(pid)
        except (NoOptionError,NoSectionError,MissingSectionHeaderError):
            jaExisteInstancia= False
        if jaExisteInstancia:
            texto = 'Uma instancia do script esta em execucao, outra instancia nao pode ser iniciada'
            print("Uma instancia do script esta em execucao")
            ctypes.windll.user32.MessageBoxW(0, texto, "Erro ao iniciar!", 0)#https://stackoverflow.com/questions/2963263/how-can-i-create-a-simple-message-box-in-python
        return jaExisteInstancia
    
    def startSelenium(self):#retorna o driver do selenium
        options = webdriver.ChromeOptions() 
        options.add_argument('user-data-dir=C:\\Users\\Jhony\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1')
        return webdriver.Chrome(chrome_options=options)
    def setConnectionFile(self):
        config = SafeConfigParser()
        config.read(self.configFile)
        if not config.has_section('main'):
            config.add_section('main')
        config.set('main', 'command_executor', self.driver.command_executor._url)
        config.set('main', 'session_id', self.driver.session_id)
        with open(self.configFile, 'w') as f:
            config.write(f)
    
    def getUrlWhatsapp(self, url = 'https://web.whatsapp.com'):
        self.driver.get(url)
    
    def start(self, confFile):
        #options = webdriver.ChromeOptions() 
        #options.add_argument('user-data-dir=C:\\Users\\Jhony\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 3') #Path to your chrome profile
        #global driver
        #driver = webdriver.Chrome(chrome_options=options)
        self.driver.get('https://web.whatsapp.com')
        
        #print (driver.service.port)
        print(self.driver.command_executor._url)
        print(self.driver.session_id)
        
        config = SafeConfigParser()
        config.read(confFile)
        if not config.has_section('main'):
            config.add_section('main')
        config.set('main', 'command_executor', self.driver.command_executor._url)
        config.set('main', 'session_id', self.driver.session_id)
        #config.set('main', 'started', True)
        with open(confFile, 'w') as f:
            config.write(f)
        self.waitWhileIsOpen(driver=self.driver)
    
    def setStarted(self,setBol):
        config = SafeConfigParser()
        config.read(self.configFile)
        if not config.has_section('main'):
            config.add_section('main')
        if setBol:
            pid = os.getpid()
            config.set('main', 'started', str(pid) )
        else:
            if config.has_option('main', 'started'):
                config.remove_option('main', 'started')
        with open(self.configFile, 'w') as f:
                    config.write(f)
    
    def resetWindow(self):
        def isMinimized( handle ):
            return win32gui.IsIconic( handle )
        def SetAsForegroundWindow(window, restore=False):
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')#msg obrigatoria antes de qualquer mudanca na gui do windows
            win32gui.SetForegroundWindow(window)
            if restore:
                win32gui.ShowWindow(window, win32con.SW_RESTORE)#https://msdn.microsoft.com/pt-br/library/windows/desktop/ms633548(v=vs.85).aspx
        def getForegroundWindow():
            return win32gui.GetForegroundWindow()
        print("resetWindow foi chamado")
        wtitle = self.driver.title + " - Google Chrome"
        window = win32gui.FindWindow(None, wtitle)
        if isMinimized(window):
            wInicial = getForegroundWindow()
            SetAsForegroundWindow(window, True)
            SetAsForegroundWindow(wInicial, False)
    
    def __waitUntilTakeEl(self, timeOut, xp):#return element #deprecated
        tpast = 0.001 #seconds
        while (tpast <= timeOut):
            exist = True
            element = None
            try:
                element=self.driver.find_element_by_xpath(xp)
                logging.debug("achou")
                logging.debug(tpast)
                return element
            except NoSuchElementException:
                exist = False #faz nada
            time.sleep(0.05)
            tpast += 0.05
        logging.debug("nao Achou em __waitUntilTakeEl")
        raise NoSuchElementException()
        return False
    def __waitForText(self, elem, timeOut=1):#return text
        tpast = 0.001 #seconds
        while (tpast <= timeOut):
            text = elem.text
            if not text == "":
                #print("achou2")
                logging.debug(tpast)
                #print(text)
                return text
            time.sleep(0.01)
            tpast += 0.01
        return False
    def contatoAtual(self, secure=True ):#retorna o numero do contato que estava com a conversa aberta
        logging.debug("contatoAtual")
        try:
            if secure:
                self.driver.find_element_by_xpath("//*[@id='side']//button//span[@data-icon='search']").click() #close any contexmenu
                time.sleep(0.3)#wait animation
        except NoSuchElementException:
            None
        try:
            close = self.driver.find_element_by_xpath("//span//div//button//span[@data-icon='x']")
        except NoSuchElementException:
            menus = self.driver.find_elements_by_xpath("//div[@id='main']/header/div")
            if len(menus) > 0:#se zero, a pagina esta com nenhum chat aberto, ou seja estah na tela inicial
                menus[1].click()#abro o menu
        try:
            logging.debug("tentando achar telefone")
            #ele_tel = self.driver.find_element_by_xpath("//div/span[@class='selectable-text invisible-space copyable-text']/span[contains(text(),'+55 ')]")
            ele_tel = self.driver.find_element_by_xpath("//div/span[contains(@class,'selectable-text invisible-space copyable-text')]/span[contains(text(),'+55 ')]")
            numero = self.__waitForText(elem = ele_tel, timeOut=1)
            #close = self.driver.find_element_by_xpath("//span//div//button//span[@data-icon='x']")
            #close = self.__waitUntilTakeEl(0.5, "//span//div//button//span[@data-icon='x']")
            #close.click()
            logging.debug("chegou1")
            logging.debug(numero)
            self.closeInfoBar()
            logging.debug("chegou2")
            logging.debug(numero)
            return numero
        except NoSuchElementException:
            logging.debug("deu exessão")
            logging.debug(NoSuchElementException)
            return ""
    def getContato(self):
        return self.contatoAtual(secure=False)
    
    def closeInfoBarOLD(self): 
        self.driver.find_elements_by_xpath("//body")[0].sendKeys(27) #aperta esc, dá problemas
    
    # https://stackoverflow.com/a/14284815
    def closeInfoBar(self): #dispara evento de close, pois o selenium esta com bug no click com whatsappweb, e actionsChain nao funciona no modo remoto
        self.importJquery()
        self.driver.execute_script("""(function(){
            //$x é xpath próprio dos navegadores, não eh jquery!
            //$x("//span//div//button//span[@data-icon='x']")[0].click()
            function getElementByXpath(path) {
              return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            }
            $c(
                getElementByXpath("//span//div//button//span[@data-icon='x']")
            ).trigger("click");
    })();""")
    def importJquery(self):#variavel jquery é $c
        try:
            jQ_exist = self.driver.execute_script("return typeof $c !== 'undefined'")
            logging.debug(jQ_exist)
            if not jQ_exist:
                logging.debug("entrou no if")
                self.driver.execute_script("""var jq = document.createElement("script");
                                  jq.src = "https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js";
                                  document.getElementsByTagName('head')[0].appendChild(jq);""")
                time.sleep(1)
                self.driver.execute_script("window.$c = jQuery.noConflict()")
        except:
            None
       
    def startServidor(self, port=6970):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:"+str(port))#https://stackoverflow.com/questions/44273941/python-script-not-terminating-after-timeout-in-zmq-recv
        socket.setsockopt( zmq.SNDTIMEO, 100 )#http://api.zeromq.org/3-2:zmq-setsockopt
        def servidor():
            pythoncom.CoInitialize()#https://stackoverflow.com/questions/26745617/win32com-client-dispatch-cherrypy-coinitialize-has-not-been-called
            while True:#  Wait for next request from client
                message = socket.recv()
                print("Received request: %s" % message)
                if message == b"resetWindow":
                    self.resetWindow()
                    socket.send(b"ok")#  Send reply back to client
                if message == b"getContatoAtual":
                    t = threading.Thread(target=self.resetWindow(),args=())#diminui pela metade o tempo
                    t.setDaemon(True)#faz com que a thread seja finalizada quando o script termina
                    t.start()
                    telef = self.getContato()
                    print(telef)
                    socket.send(telef.encode())
        t = threading.Thread(target=servidor,args=())
        t.setDaemon(True)#faz com que a thread seja finalizada quando o script termina
        t.start()
        return context
        
#https://docs.python.org/2/library/optparse.html#putting-it-all-together
def main():
    #configFile = 'connection.txt'
    #forceInit = getStartOptions()
    #if (not isStarted(confFile=configFile)) or (forceInit == True):
    #    try:#https://stackoverflow.com/questions/788411/check-to-see-if-python-script-is-running
    #        startServidor()#inicia o servidor de mensagens
    #        setStarted(confFile=configFile,setBol=True)
    #        start(confFile=configFile)
    #    finally:
    #        setStarted(confFile=configFile,setBol=False)
    #else:
    #    print("o pid ja existe")
    whats = AutomationW()
    whats.waitWhileIsOpen()
    del whats
if __name__ == "__main__":
    main()