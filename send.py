import time
import logging
from chronometer import Chronometer
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import selenium.webdriver.firefox.service as service
from configparser import SafeConfigParser
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import psutil
from optparse import OptionParser
from selenium.webdriver.common.action_chains import ActionChains
import zmq
import os
import sys
import ctypes
import re
#seta workdir como o caminho deste script
try:#if workdir is the same
    os.chdir(os.path.dirname(sys.argv[0]))
except:
    None
#sys.stdout = open("send_last_log.txt", "w")
logging.basicConfig(filename='send_last.log',level=logging.DEBUG)
#define global driver
#driver = None
    
class Sender:#cls indica que o metodo eh de classe
    def __init__(self):#self indica que o metodo eh de objeto
        self.driver = None
        self.msg = self.genericClass()
        self.msg.c_name = None
        self.msg.message = "Seu pedido saiu para entrega."
        self.getContatoBol = None
        self.connection = self.genericClass()
        self.context = None
        self.getSendOptions()
        self.loadConnectionConf()
        if not self.isServerRunning():
            logging.debug("o servidor (start.py) nao esta funcionando")
            sys.exit(1)
        self.requestResetWindow()
        
        #self.__atributoOuMetodo indica que eh privado, sem __ indica que eh publico
    def __del__(self):
        self.context.destroy()
    class genericClass():
        pass
    #http://tarunlalwani.com/post/reusing-existing-browser-session-selenium/
    @staticmethod
    def create_driver_session_firefox(session_id, executor_url):#Firefox only
        from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
    
        # Save the original function, so we can revert our patch
        org_command_execute = RemoteWebDriver.execute
    
        def new_command_execute(self, command, params=None):
            if command == "newSession":
                # Mock the response
                return {'success': 0, 'value': None, 'sessionId': session_id}
            else:
                return org_command_execute(self, command, params)
    
        # Patch the function before creating the driver object
        RemoteWebDriver.execute = new_command_execute
    
        new_driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
        new_driver.session_id = session_id
    
        # Replace the patched function with original function
        RemoteWebDriver.execute = org_command_execute
    
        return new_driver
    
    @staticmethod
    def create_driver_session(session_id, executor_url):#bug:está abrindo uma nova janela
        new_driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
        new_driver.close()
        new_driver.session_id = session_id
        return new_driver
    
    def __waitUntilTakeEl(self, driver, timeOut, xp):#return element #deprecated
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
    
    def sendMessage(self, message):
        def gotoChathead(name):
            elem = self.driver.find_element_by_xpath('//span[contains(text(),"'+name+'")]')
            elem.click()
        def sendMessage(msg='Hi!'):
            # web_obj = self.driver.find_element_by_xpath("//div[@contenteditable='true']")
            web_obj = self.driver.find_element_by_xpath("//footer//div[@contenteditable='true']")
            web_obj.click()
            #ActionChains(self.driver).key_down(Keys.SHIFT).send_keys("teste com amor").key_up(Keys.SHIFT)
            #web_obj.send_keys('teste com \n amor')
            #ActionChains(self.driver).key_up(Keys.SHIFT)
            #shiftEnter(msg,web_obj)
            textByJquery(msg,web_obj)
            web_obj.send_keys(Keys.RETURN)
        def shiftEnter(msg,elem):
            for part in msg.split('<br>'):
                elem.send_keys(part)
                elem.send_keys( Keys.SHIFT+Keys.ENTER )
        def convertBrToSlash(msg):
            texto=""
            for part in msg.split('<br>'):
                texto = texto + part + " \n "
            return texto
        def textByJquery(msg,ele):
            print("""$c("div[contenteditable='true']").html(('.""" + msg + """').replace(/<br>/g, "\\n"));""")
            self.driver.execute_script("""$c("div[contenteditable='true']").html(('.""" + msg + """').replace(/<br>/g, "\\n"));""")
            #self.driver.execute_script("""$c("div[contenteditable='true']").html(('.Love').replace(/<br>/g, "\\n"));""")
            
            ele.send_keys(Keys.HOME+Keys.DELETE)#apaga ponto final e faz com que o whats reconheca texto
        #gotoChathead(name=c_name)
        sendMessage(msg=message)
    
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
                    logging.debug("Firefox is dead, can't quit. Let's kill the driver")
                    firefox_process.kill()
                    return False
        else:
            logging.debug("driver has died")
            return False
    
    def pesquisarNumeroForcado(self, contato):
        achou = self.pesquisarNumero(contato=contato)
        if (achou):
            return achou
        else:#se nao achou, entao forca a pesquisa
            if re.match('^(\d{10}|\d{11})$', contato) is not None:#se tiver entre 10 ou 11 digitos, então reescreve o nono digito
                if re.match('^\d{10}$', contato) is not None:#se tiver 10, acrescenta o nono digito e pesquisa
                    n = contato[:2]+"9"+contato[-8:]
                    return self.pesquisarNumero(contato=n)
                if re.match('^\d{11}$', contato) is not None:#se tiver 11, tira o nono digito e pesquisa
                    n = contato[:2]+contato[-8:]
                return self.pesquisarNumero(contato=n)
            else:
                return achou
        
    def pesquisarNumero(self, contato, atual = None): #retorna um bool, se achou algum contato, então true
        logging.debug('CHEGOU AQUI0')
        if atual is not None:
            logging.debug('CHEGOU AQUI0 exite')
            if self.isTelefoneIguais(contato, atual):
                logging.debug('CHEGOU AQUI0 sao iguais')
                return False #não precisa pesquisa se são iguais
        if re.match('^.{8,25}$', contato):
            #ele = self.driver.find_element_by_xpath("//*[@id='side']/div/div/label/input")
            logging.debug('CHEGOU AQUI1')
            ele = self.driver.find_element_by_xpath("//*[@id='side']/div[1]/div/label/div/div[2]")
            #("//input[@id='input-chatlist-search']")#entra em pesquisa
            logging.debug('CHEGOU AQUI2')
            ele.clear()
            logging.debug('CHEGOU AQUI3')
            ele.send_keys(contato)
            logging.debug('CHEGOU AQUI4')
            time.sleep( 0.2 )
            logging.debug('CHEGOU AQUI5')
            temContato = len(self.driver.find_elements_by_xpath("//*[@id='pane-side']//div[text()='Conversas']")) > 0 #se achou Conversas
            logging.debug('CHEGOU AQUI6')
            ele.send_keys(Keys.RETURN) #então dá enter, e vai direto pro chat    
            logging.debug('CHEGOU AQUI7')
            if(temContato == False):#se não achou, então sai da pesquisa
                self.driver.find_element_by_xpath("//*[@id='side']//button//span[@data-icon='search']").click()
            return temContato
        else:
            logging.debug('CHEGOU AQUI7 outro')
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
    
    def desenvolvimento(self):
        #resetWindow()
        None
    def requestResetWindow(self):
        self.context = zmq.Context()
        socket = self.context.socket(zmq.REQ)
        socket.connect("tcp://localhost:6970")
        socket.send(b"resetWindow")
        logging.debug("Sended")
    
    def getSendOptions(self):
        usage = "usage: %prog [options] arg"
        parser = OptionParser(usage)
        parser.add_option("-n", "--name", dest="c_name",
                          help="Nome ou numero do Contato dentro de aspas")
        parser.add_option("-m", "--message", dest="message", default="Mensagem de Teste",
                          help="Mensagem dentro de aspas")
        parser.add_option("-g", "--getcontato", dest="getContatoBol", action="store_true", default=False,
                          help="Retornar o contato atual")
        (options, args) = parser.parse_args()
        if not (options.c_name or options.getContatoBol):
            parser.error("Passe ao menos o argumento -n 'nome do contato'")
        if options.c_name:
            self.msg.c_name = options.c_name
        if options.message:
            self.msg.message = options.message
        if options.getContatoBol:
            self.getContatoBol = options.getContatoBol
        return self.msg.c_name, self.msg.message, self.getContatoBol
    
    def loadConnectionConf(self):
        config = SafeConfigParser()
        config.read('connection.txt')
        self.connection.session_id = config.get('main', 'session_id')
        self.connection.executor_url = config.get('main', 'command_executor')
        try:
            self.connection.started = config.get('main', 'started')
        except:
            self.connection.started = 'False'
    def isServerRunning(self):
        if self.connection.started == 'False':
            return False
        else:
            pid = int(self.connection.started)
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x100000
            process = kernel32.OpenProcess(SYNCHRONIZE, 0, pid)
            if process != 0:
                return True
            else:
                return False
    
    # https://stackoverflow.com/a/14284815
    def closeInfoBar(self): #dispara evento de close, pois o selenium esta com bug no click com whatsappweb, e actionsChain nao funciona no modo remoto
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
        
    def lockScreen(self, bol=True):
        self.importJquery()
        if bol:
            self.driver.execute_script("""(function(){
    if( $c(".executando-automacao").length == 0 ){
    $c("body").prepend('<div class="executando-automacao">'+
    '<button style="user-select: all;pointer-events: all;text-align: center;width: 100%;background-color: lightgray;" onclick="$c(\\'.executando-automacao\\').hide()">fechar</button>'+
    '<div></div></div>');
    var style = $c('<style>'+
'.executando-automacao{pointer-events:none;margin:auto;position:fixed;display:none;z-index:1000;background-color:red;top:0;right:0;left:0;bottom:0;'+
'}.executando-automacao > div {border:15px solid #f3f3f3;border-radius:50%;border-top:15px solid #3498db;width: 80px;'+
'height:80px;animation:rodar 2s linear infinite;display:block;position:absolute;top:0;left:0;right:0;bottom:0;margin:auto;'+
'}@keyframes rodar {0% { transform: rotate(0deg); }100% { transform: rotate(360deg); }'+
'}'+
    '</style>');
    $c('html > head').append(style);}
    $c(".executando-automacao").show();
    })();""")
        else:
            self.driver.execute_script('$c(".executando-automacao").hide();')
    def conectar(self):
        self.driver = self.create_driver_session_firefox(self.connection.session_id, self.connection.executor_url)
        logging.debug(self.driver.current_url)
    def isTelefoneIguais(self, t1, t2):
        logging.debug("isTelefoneIguais")
        logging.debug(t1)
        logging.debug(t2)
        t1 = re.sub("[^0-9]", "", t1)
        t2 = re.sub("[^0-9]", "", t2)
        if len(t1) > 11:
            t1 = t1[2:] #exclui o 55
        if len(t2) > 11:
            t2 = t2[2:] #exclui o 55
        if not len(t1) == len(t2):
            if not len(t1)+1 == len(t2) and not len(t1)-1 == len(t2):
                return False
            if len(t1) > len(t2):
                t1 = t1[:-9]+t1[-8:] #exclui nono digito
            if len(t2) > len(t1):
                t2 = t2[:-9]+t2[-8:] #exclui nono digito
        logging.debug("teste telefone eh o ataual")        
        logging.debug(t1)
        logging.debug(t2)
        if t1 == t2:
            return True
        return False
    def enviarMensagem(self, c_name, message):
        self.lockScreen()#DEBUG
        tel_chatAberto = self.contatoAtual()
        logging.debug("enviarMensagem")    
        if( self.isTelefoneIguais(tel_chatAberto, c_name) ):
            logging.debug("sao iguais")   
            achou = True
        else:
            logging.debug("nao sao iguais")
            achou = self.pesquisarNumeroForcado(contato=c_name)
            
        if(achou):
            self.sendMessage(message=message)
            self.pesquisarNumero(contato=tel_chatAberto, atual = c_name)#só pesquisa o numero anterior se achou o da mensagem
    def getContato(self):
        return self.contatoAtual(secure=False)
    def sendFromOptions(self):
        with Chronometer() as t:
            self.conectar()#se não tiver -g ou -n então dá erro!
            logging.warn('conectar() demorou {:.3f} seconds!'.format(float(t)))
            if self.getContatoBol:
                print( self.getContato() )
                logging.warn('print( self.getContato() ) demorou {:.3f} seconds!'.format(float(t)))
            if self.msg.c_name:
                self.enviarMensagem(c_name = self.msg.c_name, message = self.msg.message)
            self.lockScreen(False)
        logging.warn('sendFromOptions() demorou {:.3f} seconds!'.format(float(t)))

#https://docs.python.org/2/library/optparse.html#putting-it-all-together
def main():
    #c_name, message = getSendOptions()
    #requestResetWindow()
    #enviarMensagem(c_name=c_name, message=message)
    #desenvolvimento()
    s = Sender()  
    s.sendFromOptions()
    del s

if __name__ == "__main__":
    with Chronometer() as t:
        main()
    logging.warn('main() demorou {:.3f} seconds!'.format(float(t)))#cronometro
