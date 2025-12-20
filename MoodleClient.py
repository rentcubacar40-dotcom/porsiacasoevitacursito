import requests
import os
import re
import json
import urllib
from bs4 import BeautifulSoup
import requests_toolbelt as rt
from requests_toolbelt import MultipartEncoderMonitor
from requests_toolbelt import MultipartEncoder
from functools import partial
import uuid
import time
from ProxyCloud import ProxyCloud
import random
import datetime

import S5Crypto


class CallingUpload:
    def __init__(self, func, filename, args):
        self.func = func
        self.args = args
        self.filename = filename
        self.time_start = time.time()
        self.time_total = 0
        self.speed = 0
        self.last_read_byte = 0
    
    def __call__(self, monitor):
        self.speed += monitor.bytes_read - self.last_read_byte
        self.last_read_byte = monitor.bytes_read
        tcurrent = time.time() - self.time_start
        self.time_total += tcurrent
        self.time_start = time.time()
        if self.time_total >= 1:
            clock_time = (monitor.len - monitor.bytes_read) / (self.speed) if self.speed > 0 else 0
            if self.func:
                self.func(self.filename, monitor.bytes_read, monitor.len, self.speed, clock_time, self.args)
            self.time_total = 0
            self.speed = 0


class CubaSimulator:
    """Simula un dispositivo desde Cuba"""
    
    @staticmethod
    def get_cuban_headers():
        """Headers típicos de navegadores en Cuba"""
        # User-Agents comunes en Cuba (dispositivos más antiguos, Android específico)
        cuban_user_agents = [
            # Android comunes en Cuba
            "Mozilla/5.0 (Linux; Android 10; SM-A307FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 9; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 8.1.0; HUAWEI Y9 2019) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36",
            # Windows común en Cuba
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
        ]
        
        # ISP comunes en Cuba
        cuban_isp_asn = [
            "AS27725",  # ETECSA - Empresa de Telecomunicaciones de Cuba S.A.
            "AS32787",  # CENIAInternet
            "AS11830",  # Ministerio de Informática y Comunicaciones
            "AS270729", # Universidad de las Ciencias Informáticas
        ]
        
        # Idioma (español cubano)
        accept_language = "es-CU,es;q=0.9,es-419;q=0.8,en;q=0.7"
        
        headers = {
            'User-Agent': random.choice(cuban_user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': accept_language,
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
            # Headers adicionales para parecer real
            'X-Client-Country': 'CU',
            'X-Client-Region': 'La Habana',
            'X-Client-City': 'La Habana',
            'X-Client-ISP': 'ETECSA',
            'X-Client-ASN': random.choice(cuban_isp_asn),
        }
        
        return headers
    
    @staticmethod
    def add_cuba_cookies(session, domain):
        """Añade cookies típicas de sesiones cubanas"""
        # Cookies comunes en sitios educativos cubanos
        cuba_cookies = {
            'country': 'CU',
            'lang': 'es_CU',
            'last_visit': str(int(time.time()) - random.randint(3600, 86400)),
            'device_type': random.choice(['mobile', 'desktop']),
            'network_type': random.choice(['wifi', 'mobile_data']),
        }
        
        for key, value in cuba_cookies.items():
            session.cookies.set(key, value, domain=domain)
    
    @staticmethod
    def simulate_cuba_network_latency():
        """Simula latencia de red típica de Cuba"""
        # Latencia típica en Cuba: 200-800ms
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)


class MoodleClient(object):
    def __init__(self, user, passw, host='', repo_id=4, proxy: ProxyCloud = None, simulate_cuba=False):
        self.username = user
        self.password = passw
        self.session = requests.Session()
        self.path = 'https://moodle.uclv.edu.cu/'
        self.host_tokenize = 'https://tguploader.url/'
        if host != '':
            self.path = host
        self.userdata = None
        self.userid = ''
        self.repo_id = repo_id
        self.sesskey = ''
        self.proxy = None
        self.simulate_cuba = simulate_cuba
        
        if proxy:
            self.proxy = proxy.as_dict_proxy()
        
        # Configurar sesión para parecer de Cuba si está activado
        if simulate_cuba:
            self._configure_cuba_session()
    
    def _configure_cuba_session(self):
        """Configura la sesión para simular conexión desde Cuba"""
        # Headers cubanos
        cuban_headers = CubaSimulator.get_cuban_headers()
        self.session.headers.update(cuban_headers)
        
        # Cookies cubanas
        domain = urllib.parse.urlparse(self.path).netloc
        CubaSimulator.add_cuba_cookies(self.session, domain)
    
    def getsession(self):
        return self.session
    
    def getUserData(self):
        try:
            if self.simulate_cuba:
                CubaSimulator.simulate_cuba_network_latency()
            
            tokenUrl = self.path + 'login/token.php?service=moodle_mobile_app&username=' + urllib.parse.quote(
                self.username) + '&password=' + urllib.parse.quote(self.password)
            resp = self.session.get(tokenUrl, proxies=self.proxy)
            data = self.parsejson(resp.text)
            data['s5token'] = S5Crypto.tokenize([self.username, self.password])
            
            # Añadir metadatos cubanos
            if self.simulate_cuba:
                data['client_country'] = 'CU'
            
            return data
        except:
            return None
    
    def getDirectUrl(self, url):
        tokens = str(url).split('/')
        direct = self.path + 'webservice/pluginfile.php/' + tokens[4] + '/user/private/' + tokens[-1] + '?token=' + \
                 self.data['token']
        return direct
    
    def getSessKey(self):
        if self.simulate_cuba:
            CubaSimulator.simulate_cuba_network_latency()
        
        fileurl = self.path + 'my/#'
        resp = self.session.get(fileurl, proxies=self.proxy)
        soup = BeautifulSoup(resp.text, 'html.parser')
        sesskey = soup.find('input', attrs={'name': 'sesskey'})['value']
        return sesskey
    
    def login(self):
        try:
            if self.simulate_cuba:
                CubaSimulator.simulate_cuba_network_latency()
            
            login = self.path + 'login/index.php'
            resp = self.session.get(login, proxies=self.proxy)
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            anchor = ''
            try:
                anchor = soup.find('input', attrs={'name': 'anchor'})['value']
            except:
                pass
            
            logintoken = ''
            try:
                logintoken = soup.find('input', attrs={'name': 'logintoken'})['value']
            except:
                pass
            
            username = self.username
            password = self.password
            payload = {'anchor': '', 'logintoken': logintoken, 'username': username, 'password': password,
                       'rememberusername': 1}
            
            # Añadir parámetros cubanos si está activado
            if self.simulate_cuba:
                payload['country'] = 'CU'
                payload['lang'] = 'es_cu'
            
            loginurl = self.path + 'login/index.php'
            
            if self.simulate_cuba:
                # Simular tiempo de respuesta de Cuba
                time.sleep(random.uniform(0.2, 0.6))
            
            resp2 = self.session.post(loginurl, data=payload, proxies=self.proxy)
            soup = BeautifulSoup(resp2.text, 'html.parser')
            counter = 0
            
            for i in resp2.text.splitlines():
                if "loginerrors" in i or (0 < counter <= 3):
                    counter += 1
                    print(i)
            
            if counter > 0:
                print('No pude iniciar sesion')
                return False
            else:
                try:
                    self.userid = soup.find('div', {'id': 'nav-notification-popover-container'})['data-userid']
                except:
                    try:
                        self.userid = soup.find('a', {'title': 'Enviar un mensaje'})['data-userid']
                    except:
                        pass
                
                print('He iniciado sesion con exito')
                self.userdata = self.getUserData()
                try:
                    self.sesskey = self.getSessKey()
                except:
                    pass
                
                # Configurar cookies de sesión cubanas
                if self.simulate_cuba:
                    domain = urllib.parse.urlparse(self.path).netloc
                    self.session.cookies.set('logged_in_from_cuba', 'true', domain=domain)
                
                return True
        except Exception as ex:
            print(f"Error en login: {str(ex)}")
        return False
    
    def createEvidence(self, name, desc=''):
        if self.simulate_cuba:
            CubaSimulator.simulate_cuba_network_latency()
        
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(evidenceurl, proxies=self.proxy)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        sesskey = self.sesskey
        files = self.extractQuery(soup.find('object')['data'])['itemid']
        
        saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id=&userid=' + self.userid + '&return='
        payload = {'userid': self.userid,
                   'sesskey': sesskey,
                   '_qf__tool_lp_form_user_evidence': 1,
                   'name': name, 'description[text]': desc,
                   'description[format]': 1,
                   'url': '',
                   'files': files,
                   'submitbutton': 'Guardar+cambios'}
        
        resp = self.session.post(saveevidence, data=payload, proxies=self.proxy)
        
        evidenceid = str(resp.url).split('?')[1].split('=')[1]
        
        return {'name': name, 'desc': desc, 'id': evidenceid, 'url': resp.url, 'files': []}
    
    def saveEvidence(self, evidence):
        evidenceurl = self.path + 'admin/tool/lp/user_evidence_edit.php?id=' + evidence['id'] + '&userid=' + self.userid + '&return=list'
        resp = self.session.get(evidenceurl, proxies=self.proxy)
        soup = BeautifulSoup(resp.text, 'html.parser')
        sesskey = soup.find('input', attrs={'name': 'sesskey'})['value']
        files = evidence['files']
        saveevidence = self.path + 'admin/tool/lp/user_evidence_edit.php?id=' + evidence['id'] + '&userid=' + self.userid + '&return=list'
        payload = {'userid': self.userid,
                   'sesskey': sesskey,
                   '_qf__tool_lp_form_user_evidence': 1,
                   'name': evidence['name'], 'description[text]': evidence['desc'],
                   'description[format]': 1, 'url': '',
                   'files': files,
                   'submitbutton': 'Guardar+cambios'}
        resp = self.session.post(saveevidence, data=payload, proxies=self.proxy)
        return evidence
    
    def getEvidences(self):
        if self.simulate_cuba:
            CubaSimulator.simulate_cuba_network_latency()
        
        evidencesurl = self.path + 'admin/tool/lp/user_evidence_list.php?userid=' + self.userid
        resp = self.session.get(evidencesurl, proxies=self.proxy)
        soup = BeautifulSoup(resp.text, 'html.parser')
        nodes = soup.find_all('tr', {'data-region': 'user-evidence-node'})
        list = []
        for n in nodes:
            nodetd = n.find_all('td')
            evurl = nodetd[0].find('a')['href']
            evname = n.find('a').next
            evid = evurl.split('?')[1].split('=')[1]
            nodefiles = nodetd[1].find_all('a')
            nfilelist = []
            for f in nodefiles:
                url = str(f['href'])
                directurl = url
                try:
                    directurl = url + '&token=' + self.userdata['token']
                    directurl = str(directurl).replace('pluginfile.php', 'webservice/pluginfile.php')
                except:
                    pass
                nfilelist.append({'name': f.next, 'url': url, 'directurl': directurl})
            list.append({'name': evname, 'desc': '', 'id': evid, 'url': evurl, 'files': nfilelist})
        return list
    
    def deleteEvidence(self, evidence):
        if self.simulate_cuba:
            CubaSimulator.simulate_cuba_network_latency()
        
        evidencesurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
        resp = self.session.get(evidencesurl, proxies=self.proxy)
        soup = BeautifulSoup(resp.text, 'html.parser')
        sesskey = soup.find('input', attrs={'name': 'sesskey'})['value']
        deleteUrl = self.path + 'lib/ajax/service.php?sesskey=' + sesskey + '&info=core_competency_delete_user_evidence,tool_lp_data_for_user_evidence_list_page'
        savejson = [{"index": 0, "methodname": "core_competency_delete_user_evidence", "args": {"id": evidence['id']}},
                    {"index": 1, "methodname": "tool_lp_data_for_user_evidence_list_page",
                     "args": {"userid": self.userid}}]
        headers = {'Content-type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01'}
        resp = self.session.post(deleteUrl, json=savejson, headers=headers, proxies=self.proxy)
        pass
    
    def upload_file(self, file, evidence=None, itemid=None, progressfunc=None, args=(), tokenize=False):
        try:
            if self.simulate_cuba:
                CubaSimulator.simulate_cuba_network_latency()
            
            fileurl = self.path + 'admin/tool/lp/user_evidence_edit.php?userid=' + self.userid
            resp = self.session.get(fileurl, proxies=self.proxy)
            soup = BeautifulSoup(resp.text, 'html.parser')
            sesskey = self.sesskey
            if self.sesskey == '':
                sesskey = soup.find('input', attrs={'name': 'sesskey'})['value']
            
            _qf__user_files_form = 1
            query = self.extractQuery(soup.find('object', attrs={'type': 'text/html'})['data'])
            client_id = self.getclientid(resp.text)
            
            itempostid = query['itemid']
            if itemid:
                itempostid = itemid
            
            # Añadir metadatos cubanos al upload si está activado
            if self.simulate_cuba:
                cuba_time = datetime.datetime.now()
            
            upload_data = {
                'title': (None, ''),
                'author': (None, 'ObysoftDev'),
                'license': (None, 'allrightsreserved'),
                'itemid': (None, itempostid),
                'repo_id': (None, str(self.repo_id)),
                'p': (None, ''),
                'page': (None, ''),
                'env': (None, query['env']),
                'sesskey': (None, sesskey),
                'client_id': (None, client_id),
                'maxbytes': (None, query['maxbytes']),
                'areamaxbytes': (None, query['areamaxbytes']),
                'ctx_id': (None, query['ctx_id']),
                'savepath': (None, '/'),
            }
            
            # Añadir parámetros cubanos si está activado
            if self.simulate_cuba:
                upload_data['client_country'] = (None, 'CU')
                upload_data['client_timezone'] = (None, 'America/Havana')
            
            of = open(file, 'rb')
            b = uuid.uuid4().hex
            upload_file = {
                'repo_upload_file': (file, of, 'application/octet-stream'),
                **upload_data
            }
            post_file_url = self.path + 'repository/repository_ajax.php?action=upload'
            encoder = rt.MultipartEncoder(upload_file, boundary=b)
            progrescall = CallingUpload(progressfunc, file, args)
            callback = partial(progrescall)
            monitor = MultipartEncoderMonitor(encoder, callback=callback)
            
            resp2 = self.session.post(post_file_url, data=monitor,
                                      headers={"Content-Type": "multipart/form-data; boundary=" + b},
                                      proxies=self.proxy)
            of.close()
            
            # save evidence
            if evidence:
                evidence['files'] = itempostid
            
            data = self.parsejson(resp2.text)
            data['url'] = str(data['url']).replace('\\', '')
            if self.userdata:
                if 'token' in self.userdata and not tokenize:
                    name = str(data['url']).split('/')[-1]
                    data['url'] = self.path + 'webservice/pluginfile.php/' + query['ctx_id'] + '/core_competency/userevidence/' + \
                                  evidence['id'] + '/' + name + '?token=' + self.userdata['token']
                if tokenize:
                    data['url'] = self.host_tokenize + S5Crypto.encrypt(data['url']) + '/' + self.userdata['s5token']
            
            # Añadir metadatos cubanos a la respuesta si está activado
            if self.simulate_cuba:
                data['upload_country'] = 'CU'
            
            return itempostid, data
        except Exception as e:
            print(f"Error en upload_file: {str(e)}")
            return None, None
    
    def parsejson(self, json_str):
        data = {}
        try:
            # Intentar parseo JSON estándar
            return json.loads(json_str)
        except:
            # Método de respaldo
            json_str = str(json_str).replace('{', '').replace('}', '')
            tokens = json_str.split(',')
            for t in tokens:
                if ':' in t:
                    split = str(t).split(':', 1)
                    key = str(split[0]).replace('"', '')
                    value = str(split[1]).replace('"', '')
                    data[key] = value
        return data
    
    def getclientid(self, html):
        index = str(html).index('client_id')
        max = 25
        ret = html[index:(index + max)]
        return str(ret).replace('client_id":"', '')
    
    def extractQuery(self, url):
        tokens = str(url).split('?')[1].split('&')
        retQuery = {}
        for q in tokens:
            qspl = q.split('=')
            try:
                retQuery[qspl[0]] = qspl[1]
            except:
                retQuery[qspl[0]] = None
        return retQuery
    
    def logout(self):
        logouturl = self.path + 'login/logout.php?sesskey=' + self.sesskey
        self.session.post(logouturl, proxies=self.proxy)
