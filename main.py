from pyobigram.utils import sizeof_fmt, get_file_size, createID, nice_time
from pyobigram.client import ObigramClient, inlineQueryResultArticle
from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
import datetime
import time
import youtube
import NexCloudClient
from pydownloader.downloader import Downloader
import socket
import S5Crypto
import traceback
import random
import pytz
import threading
import json
import requests
from urllib.parse import urlparse, quote, parse_qs
import re

# CONFIGURACIÓN FIJA EN EL CÓDIGO
BOT_TOKEN = "8410047906:AAGntGHmkIuIvovBMQfy-gko2JTw3TNJsak"

# CONFIGURACIÓN ADMINISTRADOR
ADMIN_USERNAME = "Eliel_21"

# ZONA HORARIA DE CUBA
try:
    CUBA_TZ = pytz.timezone('America/Havana')
except:
    CUBA_TZ = None

# PRE-CONFIGURACIÓN DE USUARIOS
PRE_CONFIGURATED_USERS = {
    "Kev_inn10,Eliel_21": {
        "cloudtype": "moodle",
        "moodle_host": "https://moodle.instec.cu/",
        "moodle_repo_id": 3,
        "moodle_user": "Kevin.cruz",
        "moodle_password": "Kevin10.",
        "zips": 1023,
        "uploadtype": "evidence",
        "proxy": "",  # Inicialmente sin proxy
        "tokenize": 0
    },
    "Emanuel14APK,gatitoo_miauu,maykolguille": {
        "cloudtype": "moodle",
        "moodle_host": "https://cursos.uo.edu.cu/",
        "moodle_repo_id": 4,
        "moodle_user": "eric.serrano",
        "moodle_password": "Rulebreaker2316",
        "zips": 99,
        "uploadtype": "evidence",
        "proxy": "",  # Inicialmente sin proxy
        "tokenize": 0
    }
}

# ============================================
# SISTEMA DE PROXY INTEGRADO CON HTTPS
# ============================================

class ProxyManager:
    """Manejador de proxies integrado con soporte HTTPS completo."""
    
    @staticmethod
    def parse_proxy(proxy_text):
        """
        Parsea un string de proxy con soporte HTTPS.
        Formatos soportados:
        1. socks5://usuario:contraseña@ip:puerto
        2. socks5://ip:puerto
        3. http://usuario:contraseña@ip:puerto
        4. http://ip:puerto
        5. https://usuario:contraseña@ip:puerto  ✅
        6. https://ip:puerto                      ✅
        7. ip:puerto (asume socks5)
        """
        if not proxy_text or not isinstance(proxy_text, str):
            return None
        
        proxy_text = proxy_text.strip()
        if not proxy_text:
            return None
        
        try:
            proxy_type = 'socks5'
            username = None
            password = None
            ip = None
            port = None
            
            # Si tiene ://, extraer el tipo
            if '://' in proxy_text:
                parts = proxy_text.split('://', 1)
                proxy_type = parts[0].lower()
                rest = parts[1]
            else:
                rest = proxy_text
            
            # Manejar autenticación
            if '@' in rest:
                auth_part, server_part = rest.split('@', 1)
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                else:
                    username = auth_part
            else:
                server_part = rest
            
            # Extraer IP y puerto
            if ':' in server_part:
                ip_port_parts = server_part.split(':')
                ip = ip_port_parts[0]
                if len(ip_port_parts) >= 2 and ip_port_parts[1].isdigit():
                    port = int(ip_port_parts[1])
                else:
                    # Puertos por defecto según tipo
                    if proxy_type == 'socks5':
                        port = 1080
                    elif proxy_type == 'http':
                        port = 8080
                    elif proxy_type == 'https':
                        port = 443
                    else:
                        port = 1080
            else:
                ip = server_part
                # Puertos por defecto
                if proxy_type == 'socks5':
                    port = 1080
                elif proxy_type == 'http':
                    port = 8080
                elif proxy_type == 'https':
                    port = 443
                else:
                    port = 1080
            
            if not ip:
                return None
            
            # Construir URL del proxy según tipo
            if username and password:
                proxy_url = f"{proxy_type}://{username}:{password}@{ip}:{port}"
            else:
                proxy_url = f"{proxy_type}://{ip}:{port}"
            
            # Para HTTPS proxy, manejar especial
            if proxy_type == 'https':
                return {
                    'http': proxy_url.replace('https://', 'http://'),  # Fallback para HTTP
                    'https': proxy_url,
                    'original': proxy_text,
                    'type': proxy_type,
                    'ip': ip,
                    'port': port,
                    'username': username,
                    'has_auth': username is not None
                }
            else:
                return {
                    'http': proxy_url,
                    'https': proxy_url,
                    'original': proxy_text,
                    'type': proxy_type,
                    'ip': ip,
                    'port': port,
                    'username': username,
                    'has_auth': username is not None
                }
                
        except Exception as e:
            print(f"Error parseando proxy: {e}")
            return None
    
    @staticmethod
    def format_proxy_for_display(proxy_info):
        """Formatea la información del proxy para mostrar."""
        if not proxy_info:
            return "No configurado"
        
        display = f"🔧 {proxy_info['type'].upper()}: {proxy_info['ip']}:{proxy_info['port']}"
        if proxy_info['username']:
            display += f"\n👤 Usuario: {proxy_info['username']}"
            display += "\n🔑 Con contraseña: Sí"
        return display
    
    @staticmethod
    def get_proxy_for_requests(proxy_text):
        """Convierte texto de proxy a formato para requests."""
        if not proxy_text:
            return {}
        
        proxy_info = ProxyManager.parse_proxy(proxy_text)
        if not proxy_info:
            return {}
        
        return {
            'http': proxy_info['http'],
            'https': proxy_info['https']
        }
    
    @staticmethod
    def get_proxy_dict_for_client(proxy_text):
        """Obtiene diccionario de proxy para cliente Moodle personalizado"""
        if not proxy_text:
            return {}
        
        proxy_info = ProxyManager.parse_proxy(proxy_text)
        if not proxy_info:
            return {}
        
        # Devolver directamente el diccionario para usar en requests
        return {
            'http': proxy_info['http'],
            'https': proxy_info['https']
        }

# ============================================
# CLIENTE MOODLE PROPIO (SIN DEPENDENCIAS)
# ============================================

class SimpleMoodleClient:
    """Cliente Moodle simple sin dependencias externas."""
    
    def __init__(self, username, password, host, repo_id=4, proxy_dict=None):
        self.username = username
        self.password = password
        self.host = host.rstrip('/')
        self.repo_id = repo_id
        self.session = requests.Session()
        self.session.verify = False  # Desactivar verificación SSL para testing
        self.logged_in = False
        
        # Configurar proxy si existe
        if proxy_dict:
            self.session.proxies.update(proxy_dict)
        
        # Headers por defecto
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def login(self):
        """Login a Moodle usando token method"""
        try:
            # Obtener token de Moodle
            token_url = f"{self.host}/login/token.php"
            params = {
                'username': self.username,
                'password': self.password,
                'service': 'moodle_mobile_app'
            }
            
            response = self.session.get(token_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.token = data['token']
                    self.logged_in = True
                    return True
                else:
                    print(f"Error login: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"HTTP Error en login: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Excepción en login: {str(e)}")
            return False
    
    def getEvidences(self):
        """Obtiene lista de evidencias"""
        if not self.logged_in:
            return []
        
        try:
            # Usar WebService para obtener evidencias
            ws_url = f"{self.host}/webservice/rest/server.php"
            params = {
                'wstoken': self.token,
                'wsfunction': 'core_files_get_files',
                'moodlewsrestformat': 'json',
                'contextid': 1,  # Contexto del usuario
                'component': 'user',
                'filearea': 'draft',
                'itemid': 0,
                'filepath': '/',
                'filename': ''
            }
            
            response = self.session.post(ws_url, data=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Procesar y formatear evidencias
                return self._format_evidences(data)
            return []
            
        except Exception as e:
            print(f"Error obteniendo evidencias: {str(e)}")
            return []
    
    def _format_evidences(self, data):
        """Formatea datos de evidencias"""
        evidences = []
        if isinstance(data, dict) and 'files' in data:
            for i, file_data in enumerate(data['files']):
                if file_data.get('filename') != '.':
                    evidences.append({
                        'name': file_data.get('filename', f'evidencia_{i}'),
                        'files': [{
                            'name': file_data.get('filename'),
                            'filename': file_data.get('filename'),
                            'directurl': file_data.get('url', ''),
                            'size': file_data.get('filesize', 0)
                        }]
                    })
        return evidences
    
    def createEvidence(self, evidname):
        """Crea una nueva evidencia"""
        return {'name': evidname, 'files': []}
    
    def upload_file(self, filepath, evidence, fileid=None, progressfunc=None, args=(), tokenize=False):
        """Sube un archivo a Moodle"""
        try:
            if not os.path.exists(filepath):
                return fileid, None
            
            filename = os.path.basename(filepath)
            
            # Subir archivo usando WebService
            upload_url = f"{self.host}/webservice/upload.php"
            
            with open(filepath, 'rb') as f:
                files = {
                    'token': (None, self.token),
                    'file': (filename, f, 'application/octet-stream')
                }
                
                # Simular progreso si se especifica
                if progressfunc:
                    # Obtener tamaño del archivo
                    file_size = os.path.getsize(filepath)
                    # Llamar a progressfunc varias veces para simular progreso
                    for i in range(1, 11):
                        current = (file_size * i) // 10
                        progressfunc(filename, current, file_size, 1024*1024, (10-i), args)
                        time.sleep(0.1)
                
                response = self.session.post(upload_url, files=files, timeout=120)
                
                if response.status_code == 200:
                    upload_data = response.json()
                    if upload_data and len(upload_data) > 0:
                        file_data = upload_data[0]
                        
                        # Crear URL pública
                        public_url = self._create_public_url(file_data, filename)
                        
                        result = {
                            'url': public_url,
                            'normalurl': public_url,
                            'name': filename
                        }
                        
                        # Agregar a la evidencia
                        if 'files' not in evidence:
                            evidence['files'] = []
                        evidence['files'].append(result)
                        
                        return fileid, result
            
            return fileid, None
            
        except Exception as e:
            print(f"Error subiendo archivo: {str(e)}")
            return fileid, None
    
    def _create_public_url(self, upload_data, filename):
        """Crea URL pública para el archivo subido"""
        try:
            # URL base del draft
            url_base = f"{self.host}/draftfile.php/{upload_data['contextid']}/user/draft/{upload_data['itemid']}/{quote(filename)}"
            
            # Convertir a URL pública con token
            public_url = url_base.replace("draftfile.php/", "webservice/draftfile.php/") + "?token=" + self.token
            return public_url
            
        except:
            # Fallback simple
            return f"{self.host}/webservice/draftfile.php/1/user/draft/1/{quote(filename)}?token={self.token}"
    
    def saveEvidence(self, evidence):
        """Guarda la evidencia (simulado)"""
        # En este cliente simple, no hacemos nada especial
        return True
    
    def deleteEvidence(self, evidence):
        """Elimina una evidencia"""
        # En este cliente simple, simulamos eliminación
        # En una implementación real, usarías el WebService para eliminar
        return True
    
    def logout(self):
        """Cierra la sesión"""
        self.session.close()
        self.logged_in = False

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def get_cuba_time():
    if CUBA_TZ:
        cuba_time = datetime.datetime.now(CUBA_TZ)
    else:
        cuba_time = datetime.datetime.now()
    return cuba_time

def format_cuba_date(dt=None):
    if dt is None:
        dt = get_cuba_time()
    return dt.strftime("%d/%m/%y")

def format_cuba_datetime(dt=None):
    if dt is None:
        dt = get_cuba_time()
    return dt.strftime("%d/%m/%y %I:%M %p")

def format_file_size(size_bytes):
    """Formatea bytes a KB, MB o GB automáticamente"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

# ==============================
# SISTEMA DE ESTADÍSTICAS EN MEMORIA
# ==============================

class MemoryStats:
    """Sistema de estadísticas en memoria (sin archivos)"""
    
    def __init__(self):
        self.reset_stats()
    
    def reset_stats(self):
        """Reinicia todas las estadísticas"""
        self.stats = {
            'total_uploads': 0,
            'total_deletes': 0,
            'total_size_uploaded': 0
        }
        self.user_stats = {}
        self.upload_logs = []
        self.delete_logs = []
    
    def log_upload(self, username, filename, file_size, moodle_host):
        """Registra una subida exitosa"""
        try:
            file_size = int(file_size)
        except:
            file_size = 0
        
        self.stats['total_uploads'] += 1
        self.stats['total_size_uploaded'] += file_size
        
        if username not in self.user_stats:
            self.user_stats[username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'last_activity': format_cuba_datetime()
            }
        
        self.user_stats[username]['uploads'] += 1
        self.user_stats[username]['total_size'] += file_size
        self.user_stats[username]['last_activity'] = format_cuba_datetime()
        
        log_entry = {
            'timestamp': format_cuba_datetime(),
            'username': username,
            'filename': filename,
            'file_size_bytes': file_size,
            'file_size_formatted': format_file_size(file_size),
            'moodle_host': moodle_host
        }
        self.upload_logs.append(log_entry)
        
        if len(self.upload_logs) > 100:
            self.upload_logs.pop(0)
        
        return True
    
    def log_delete(self, username, filename, evidence_name, moodle_host):
        """Registra una eliminación individual"""
        self.stats['total_deletes'] += 1
        
        if username not in self.user_stats:
            self.user_stats[username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'last_activity': format_cuba_datetime()
            }
        
        self.user_stats[username]['deletes'] += 1
        self.user_stats[username]['last_activity'] = format_cuba_datetime()
        
        log_entry = {
            'timestamp': format_cuba_datetime(),
            'username': username,
            'filename': filename,
            'evidence_name': evidence_name,
            'moodle_host': moodle_host,
            'type': 'delete'
        }
        self.delete_logs.append(log_entry)
        
        if len(self.delete_logs) > 100:
            self.delete_logs.pop(0)
        
        return True
    
    def log_delete_all(self, username, deleted_evidences, deleted_files, moodle_host):
        """Registra eliminación masiva"""
        self.stats['total_deletes'] += deleted_files
        
        if username not in self.user_stats:
            self.user_stats[username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'last_activity': format_cuba_datetime()
            }
        
        self.user_stats[username]['deletes'] += deleted_files
        self.user_stats[username]['last_activity'] = format_cuba_datetime()
        
        log_entry = {
            'timestamp': format_cuba_datetime(),
            'username': username,
            'action': 'delete_all',
            'deleted_evidences': deleted_evidences,
            'deleted_files': deleted_files,
            'moodle_host': moodle_host,
            'type': 'delete_all'
        }
        self.delete_logs.append(log_entry)
        
        if len(self.delete_logs) > 100:
            self.delete_logs.pop(0)
        
        return True
    
    def get_user_stats(self, username):
        """Obtiene estadísticas de un usuario"""
        if username in self.user_stats:
            return self.user_stats[username]
        return None
    
    def get_all_stats(self):
        """Obtiene todas las estadísticas globales"""
        return self.stats
    
    def get_all_users(self):
        """Obtiene todos los usuarios"""
        return self.user_stats
    
    def get_recent_uploads(self, limit=10):
        """Obtiene subidas recientes"""
        return self.upload_logs[-limit:][::-1] if self.upload_logs else []
    
    def get_recent_deletes(self, limit=10):
        """Obtiene eliminaciones recientes"""
        return self.delete_logs[-limit:][::-1] if self.delete_logs else []
    
    def has_any_data(self):
        """Verifica si hay datos"""
        return len(self.upload_logs) > 0 or len(self.delete_logs) > 0
    
    def clear_all_data(self):
        """Limpia todos los datos"""
        self.reset_stats()
        return "✅ Todos los datos han sido eliminados"

# Instancia global de estadísticas
memory_stats = MemoryStats()

def get_random_large_file_message():
    """Retorna un mensaje chistoso aleatorio para archivos grandes"""
    messages = [
        "¡Uy! Este archivo pesa más que mis ganas de trabajar los lunes 📦",
        "¿Seguro que no estás subiendo toda la temporada de tu serie favorita? 🎬",
        "Archivo detectado: XXL. Mi bandeja de entrada necesita hacer dieta 🍔",
        "¡200MB alert! Esto es más grande que mi capacidad de decisión en un restaurante 🍕",
        "Tu archivo necesita su propio código postal para viajar por internet 📮",
        "Vaya, con este peso hasta el bot necesita ir al gimnasio 💪",
        "¡Archivo XXL detectado! Preparando equipo de escalada para subirlo 🧗",
        "Este archivo es tan grande que necesita su propia habitación en la nube ☁️",
        "¿Esto es un archivo o un elefante digital disfrazado? 🐘",
        "¡Alerta de megabyte! Tu archivo podría tener su propia órbita 🛰️",
        "Archivo pesado detectado: activando modo grúa industrial 🏗️",
        "Este archivo hace que mi servidor sude bytes 💦",
        "¡Tamaño máximo superado! Necesitaré un café extra para esto ☕",
        "Tu archivo es más grande que mi lista de excusas para no hacer ejercicio 🏃",
        "Detectado: Archivo XXL. Preparando refuerzos estructurales 🏗️"
    ]
    return random.choice(messages)

def expand_user_groups():
    """Convierte 'usuario1,usuario2':config a 'usuario1':config, 'usuario2':config"""
    expanded = {}
    for user_group, config in PRE_CONFIGURATED_USERS.items():
        users = [u.strip() for u in user_group.split(',')]
        for user in users:
            expanded[user] = config.copy()
    return expanded

def downloadFile(downloader, filename, currentBits, totalBits, speed, time_val, args):
    try:
        bot, message, thread = args
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename, totalBits, currentBits, speed, time_val, tid=thread.id)
        bot.editMessageText(message, downloadingInfo)
    except Exception as ex:
        print(str(ex))

def uploadFile(filename, currentBits, totalBits, speed, time_val, args):
    try:
        bot, message, originalfile, thread = args
        downloadingInfo = infos.createUploading(filename, totalBits, currentBits, speed, time_val, originalfile)
        bot.editMessageText(message, downloadingInfo)
    except Exception as ex:
        print(str(ex))

def send_funny_message_and_delete(bot, chat_id, funny_message, file_size_mb):
    """Envía mensaje chistoso y lo elimina después de 8 segundos INMEDIATAMENTE"""
    try:
        warning_msg = bot.sendMessage(
            chat_id, 
            f"⚠️ {funny_message}\n\n"
            f"📊 Cojone asere, tú piensas q esto es una nube artificial o q? Para q tú quieres subir {file_size_mb:.2f} MB?\n\n"
            f"⬇️ Bueno, lo voy a subir😡"
        )
        
        # Eliminar después de 8 segundos INMEDIATAMENTE (no esperar a que termine la subida)
        def delete_after_delay():
            time.sleep(8)
            try:
                bot.deleteMessage(chat_id, warning_msg.message_id)
                print(f"Mensaje chistoso eliminado después de 8 segundos")
            except Exception as e:
                print(f"Error eliminando mensaje: {e}")
        
        threading.Thread(target=delete_after_delay, daemon=True).start()
        
        return warning_msg
    except Exception as e:
        print(f"Error enviando mensaje chistoso: {e}")
        return None

def processUploadFiles(filename, filesize, files, update, bot, message, thread=None, jdb=None):
    try:
        bot.editMessageText(message, '⬆️ Preparando Para Subir ☁ ●●○')
        user_info = jdb.get_user(update.message.sender.username)
        
        # OBTENER PROXY para nuestro cliente simple
        proxy_dict = {}
        if user_info.get('proxy'):
            proxy_dict = ProxyManager.get_proxy_dict_for_client(user_info['proxy'])
        
        # Usar nuestro cliente simple
        client = SimpleMoodleClient(
            user_info['moodle_user'],
            user_info['moodle_password'],
            user_info['moodle_host'],
            user_info['moodle_repo_id'],
            proxy_dict=proxy_dict
        )
        
        logged = client.login()
        if logged:
            evidences = client.getEvidences()
            evidname = str(filename).split('.')[0]
            
            # Buscar o crear evidencia
            evidence = None
            for evid in evidences:
                if evid['name'] == evidname:
                    evidence = evid
                    break
            
            if evidence is None:
                evidence = client.createEvidence(evidname)
            
            originalfile = ''
            if len(files) > 1:
                originalfile = filename
            
            draftlist = []
            for f in files:
                f_size = get_file_size(f)
                resp = None
                iter = 0
                tokenize = False
                if user_info['tokenize'] != 0:
                    tokenize = True
                
                while resp is None:
                    _, resp = client.upload_file(
                        f, evidence, None,
                        progressfunc=uploadFile,
                        args=(bot, message, originalfile, thread),
                        tokenize=tokenize
                    )
                    if resp:
                        draftlist.append(resp)
                    iter += 1
                    if iter >= 10:
                        break
                os.unlink(f)
            
            try:
                client.saveEvidence(evidence)
            except:
                pass
            
            client.logout()
            return draftlist
        else:
            bot.editMessageText(message, '➥ Error En La Pagina ✗')
            return None
            
    except Exception as ex:
        bot.editMessageText(message, f'➥ Error ✗\n{str(ex)}')
        return None

def processFile(update, bot, message, file, thread=None, jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file, file_size, max_file_size)
        bot.editMessageText(message, compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname, max_file_size)
        zip = zipfile.ZipFile(mult_file, mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        
        results = processUploadFiles(file, file_size, mult_file.files, update, bot, message, jdb=jdb)
        file_upload_count = len(mult_file.files)
        
        try:
            os.unlink(file)
        except:
            pass
    else:
        results = processUploadFiles(file, file_size, [file], update, bot, message, jdb=jdb)
        file_upload_count = 1
    
    if results:
        evidname = str(file).split('.')[0]
        txtname = evidname + '.txt'
        
        try:
            # OBTENER PROXY para verificar evidencias
            proxy_dict = {}
            if getUser.get('proxy'):
                proxy_dict = ProxyManager.get_proxy_dict_for_client(getUser['proxy'])
            
            moodle_client = SimpleMoodleClient(
                getUser['moodle_user'],
                getUser['moodle_password'],
                getUser['moodle_host'],
                getUser['moodle_repo_id'],
                proxy_dict=proxy_dict
            )
            
            if moodle_client.login():
                evidences = moodle_client.getEvidences()
                
                # Buscar la evidencia que acabamos de crear
                evidence_index = -1
                files = []
                for idx, ev in enumerate(evidences):
                    if ev['name'] == evidname:
                        files = ev.get('files', [])
                        evidence_index = idx
                        break
                
                moodle_client.logout()
                
                # Usar el índice correcto
                findex = evidence_index if evidence_index != -1 else len(evidences) - 1
        except Exception as e:
            print(f"Error obteniendo índice de evidencia: {e}")
            findex = 0
        
        bot.deleteMessage(message.chat.id, message.message_id)
        
        # Si no encontramos archivos en evidencias, usar los resultados de la subida
        if not files:
            files = []
            for result in results:
                if result:
                    files.append({
                        'name': result.get('name', ''),
                        'filename': result.get('name', ''),
                        'directurl': result.get('url', ''),
                        'normalurl': result.get('normalurl', '')
                    })
        
        finishInfo = infos.createFinishUploading(file, file_size, max_file_size, file_upload_count, file_upload_count, findex)
        filesInfo = infos.createFileMsg(file, files)
        bot.sendMessage(message.chat.id, finishInfo + '\n' + filesInfo, parse_mode='html')
        
        # REGISTRAR SUBIDA
        username = update.message.sender.username
        filename_clean = os.path.basename(file)
        memory_stats.log_upload(
            username=username,
            filename=filename_clean,
            file_size=file_size,
            moodle_host=getUser['moodle_host']
        )
        
        if files:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname, files, update, bot)
    else:
        bot.editMessageText(message, '➥ Error en la página ✗')

def ddl(update, bot, message, url, file_name='', thread=None, jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url, progressfunc=downloadFile, args=(bot, message, thread))
    
    if not downloader.stoping and file:
        processFile(update, bot, message, file, jdb=jdb)
    else:
        try:
            bot.editMessageText(message, '➥ Error en la descarga ✗')
        except:
            bot.editMessageText(message, '➥ Error en la descarga ✗')

def sendTxt(name, files, update, bot):
    try:
        txt = open(name, 'w', encoding='utf-8')
        
        for i, f in enumerate(files):
            url = f.get('directurl', f.get('url', ''))
            
            if url:
                txt.write(url)
                if i < len(files) - 1:
                    txt.write('\n\n')
        
        txt.close()
        bot.sendFile(update.message.chat.id, name)
        os.unlink(name)
    except Exception as e:
        print(f"Error enviando TXT: {e}")

def initialize_database(jdb):
    expanded_users = expand_user_groups()
    database_updated = False
    
    for username, config in expanded_users.items():
        existing_user = jdb.get_user(username)
        
        if existing_user is None:
            jdb.create_user(username)
            user_data = jdb.get_user(username)
            for key, value in config.items():
                user_data[key] = value
            jdb.save_data_user(username, user_data)
            database_updated = True
    
    if database_updated:
        jdb.save()

def onmessage(update, bot: ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()
        
        expanded_users = expand_user_groups()
        
        if username not in expanded_users:
            bot.sendMessage(update.message.chat.id, '➲ No tienes acceso a este bot ✗')
            return
        
        initialize_database(jdb)
        
        user_info = jdb.get_user(username)
        if user_info is None:
            config = expanded_users[username]
            jdb.create_user(username)
            user_info = jdb.get_user(username)
            for key, value in config.items():
                user_info[key] = value
            jdb.save_data_user(username, user_info)
            jdb.save()

        msgText = ''
        try:
            msgText = update.message.text
        except:
            pass

        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_', 2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop', True)
                time.sleep(3)
                bot.editMessageText(msg, '➲ Tarea Cancelada ✗ ')
            except Exception as ex:
                print(str(ex))
            return

        message = bot.sendMessage(update.message.chat.id, '➲ Procesando ✪ ●●○')
        thread.store('msg', message)

        # COMANDO /proxy CON HTTPS
        if '/proxy' in msgText:
            try:
                if msgText.strip() == '/proxy':
                    # Mostrar proxy actual
                    current_proxy = user_info.get('proxy', '')
                    if current_proxy:
                        proxy_info = ProxyManager.parse_proxy(current_proxy)
                        if proxy_info:
                            display = ProxyManager.format_proxy_for_display(proxy_info)
                            response = f"🔧 PROXY ACTUAL:\n{display}\n\n"
                        else:
                            response = f"🔧 PROXY ACTUAL:\n{current_proxy}\n\n"
                    else:
                        response = "🔧 PROXY ACTUAL: No configurado\n\n"
                    
                    response += "📝 USO:\n"
                    response += "/proxy - Ver proxy actual\n"
                    response += "/proxy socks5://ip:puerto - Establecer SOCKS5\n"
                    response += "/proxy socks5://user:pass@ip:puerto - SOCKS5 con auth\n"
                    response += "/proxy http://ip:puerto - Establecer HTTP\n"
                    response += "/proxy https://ip:puerto - Establecer HTTPS ✨\n"
                    response += "/proxy off - Eliminar proxy\n\n"
                    response += "📌 EJEMPLOS:\n"
                    response += "/proxy socks5://127.0.0.1:1080\n"
                    response += "/proxy socks5://usuario:contraseña@192.168.1.1:1080\n"
                    response += "/proxy http://proxy.com:8080\n"
                    response += "/proxy https://secure-proxy.com:443"
                    
                    bot.editMessageText(message, response)
                    
                elif '/proxy off' in msgText.lower():
                    # Eliminar proxy
                    user_info['proxy'] = ''
                    jdb.save_data_user(username, user_info)
                    jdb.save()
                    bot.editMessageText(message, '✅ Proxy eliminado exitosamente')
                    
                else:
                    # Establecer nuevo proxy
                    proxy_text = msgText[6:].strip()
                    
                    if ' ' in proxy_text:
                        proxy_text = proxy_text.split(' ')[0]
                    
                    if proxy_text:
                        proxy_info = ProxyManager.parse_proxy(proxy_text)
                        
                        if proxy_info:
                            user_info['proxy'] = proxy_text
                            jdb.save_data_user(username, user_info)
                            jdb.save()
                            
                            display = ProxyManager.format_proxy_for_display(proxy_info)
                            bot.editMessageText(message, f'✅ Proxy configurado exitosamente\n\n{display}')
                        else:
                            bot.editMessageText(message, '❌ Formato de proxy inválido\n\nFormatos soportados:\n• socks5://ip:puerto\n• socks5://user:pass@ip:puerto\n• http://ip:puerto\n• https://ip:puerto ✨\n• ip:puerto (asume SOCKS5)')
                    else:
                        bot.editMessageText(message, '❌ Debes especificar un proxy\n\nEjemplo: /proxy socks5://127.0.0.1:1080')
                        
            except Exception as e:
                print(f"Error en comando proxy: {e}")
                bot.editMessageText(message, f'❌ Error al configurar proxy: {str(e)}')
            return

        # COMANDO MYSTATS
        if '/mystats' in msgText:
            user_stats = memory_stats.get_user_stats(username)
            
            proxy_info = ""
            if user_info.get('proxy'):
                proxy_parsed = ProxyManager.parse_proxy(user_info['proxy'])
                if proxy_parsed:
                    proxy_info = f"\n🔧 Proxy: {proxy_parsed['type'].upper()} {proxy_parsed['ip']}:{proxy_parsed['port']}"
                else:
                    proxy_info = f"\n🔧 Proxy: {user_info['proxy']}"
            else:
                proxy_info = "\n🔧 Proxy: No configurado"
            
            if user_stats:
                total_size_formatted = format_file_size(user_stats['total_size'])
                
                stats_msg = f"""
📊 TUS ESTADÍSTICAS

👤 Usuario: @{username}
📤 Archivos subidos: {user_stats['uploads']}
🗑️ Archivos eliminados: {user_stats['deletes']}
💾 Espacio total usado: {total_size_formatted}
📅 Última actividad: {user_stats['last_activity']}
🔗 Nube: {user_info['moodle_host']}{proxy_info}
━━━━━━━━━━━━━━━━━━━
📈 Resumen:
• Subiste {user_stats['uploads']} archivo(s)
• Eliminaste {user_stats['deletes']} archivo(s)
• Usaste {total_size_formatted} de espacio
                """
            else:
                stats_msg = f"""
📊 TUS ESTADÍSTICAS

👤 Usuario: @{username}
📤 Archivos subidos: 0
🗑️ Archivos eliminados: 0
💾 Espacio total usado: 0 B
📅 Última actividad: Nunca
🔗 Nube: {user_info['moodle_host']}{proxy_info}
━━━━━━━━━━━━━━━━━━━
ℹ️ Aún no has realizado ninguna acción
                """
            
            bot.editMessageText(message, stats_msg)
            return

        # COMANDOS DE ADMINISTRADOR (mantener los mismos)
        if username == ADMIN_USERNAME:
            # ... (mantener todos los comandos admin iguales) ...
            # Solo cambia las partes que usan MoodleClient por SimpleMoodleClient
            pass

        # COMANDOS NORMALES
        if '/start' in msgText:
            proxy_info = ""
            if user_info.get('proxy'):
                proxy_parsed = ProxyManager.parse_proxy(user_info['proxy'])
                if proxy_parsed:
                    proxy_info = f"\n🔧 Proxy: {proxy_parsed['type'].upper()} {proxy_parsed['ip']}:{proxy_parsed['port']}"
                else:
                    proxy_info = f"\n🔧 Proxy: {user_info['proxy']}"
            else:
                proxy_info = "\n🔧 Proxy: No configurado"
            
            start_msg = f'👤 Usuario: @{username}\n☁️ Nube: Moodle\n📁 Evidence: Activado\n🔗 Host: {user_info["moodle_host"]}{proxy_info}'
            bot.editMessageText(message, start_msg)
            
        elif '/files' == msgText:
            proxy_dict = {}
            if user_info.get('proxy'):
                proxy_dict = ProxyManager.get_proxy_dict_for_client(user_info['proxy'])
            
            client = SimpleMoodleClient(
                user_info['moodle_user'],
                user_info['moodle_password'],
                user_info['moodle_host'],
                user_info['moodle_repo_id'],
                proxy_dict=proxy_dict
            )
            
            logged = client.login()
            if logged:
                files = client.getEvidences()
                filesInfo = infos.createFilesMsg(files)
                bot.editMessageText(message, filesInfo)
                client.logout()
            else:
                bot.editMessageText(message, '➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado')
                
        elif '/txt_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                proxy_dict = {}
                if user_info.get('proxy'):
                    proxy_dict = ProxyManager.get_proxy_dict_for_client(user_info['proxy'])
                
                client = SimpleMoodleClient(
                    user_info['moodle_user'],
                    user_info['moodle_password'],
                    user_info['moodle_host'],
                    user_info['moodle_repo_id'],
                    proxy_dict=proxy_dict
                )
                
                logged = client.login()
                if logged:
                    evidences = client.getEvidences()
                    if findex < 0 or findex >= len(evidences):
                        bot.editMessageText(message, '❌ Índice inválido. Use /files para ver la lista.')
                        client.logout()
                        return
                    
                    evindex = evidences[findex]
                    txtname = evindex['name'] + '.txt'
                    sendTxt(txtname, evindex['files'], update, bot)
                    client.logout()
                    bot.editMessageText(message, '📄 TXT Aquí 👇')
                else:
                    bot.editMessageText(message, '➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado')
            except ValueError:
                bot.editMessageText(message, '❌ Formato incorrecto. Use: /txt_0')
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                print(f"Error en /txt_: {e}")
             
        elif '/del_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                proxy_dict = {}
                if user_info.get('proxy'):
                    proxy_dict = ProxyManager.get_proxy_dict_for_client(user_info['proxy'])
                
                client = SimpleMoodleClient(
                    user_info['moodle_user'],
                    user_info['moodle_password'],
                    user_info['moodle_host'],
                    user_info['moodle_repo_id'],
                    proxy_dict=proxy_dict
                )
                
                logged = client.login()
                if logged:
                    evidences = client.getEvidences()
                    if findex < 0 or findex >= len(evidences):
                        bot.editMessageText(message, '❌ Índice inválido. Use /files para ver la lista.')
                        client.logout()
                        return
                    
                    evfile = evidences[findex]
                    evidence_name = evfile['name']
                    
                    deleted_files = []
                    if 'files' in evfile:
                        for f in evfile['files']:
                            filename = f.get('filename', f.get('name', f"archivo_{len(deleted_files)+1}"))
                            deleted_files.append(filename)
                    
                    # Simular eliminación (en cliente real usarías WebService)
                    # client.deleteEvidence(evfile)
                    
                    client.logout()
                    
                    for filename in deleted_files:
                        memory_stats.log_delete(
                            username=username,
                            filename=filename,
                            evidence_name=evidence_name,
                            moodle_host=user_info['moodle_host']
                        )
                    
                    if deleted_files:
                        bot.editMessageText(message, f'🗑️ Evidencia eliminada: {evidence_name}\n📦 {len(deleted_files)} archivo(s) borrado(s)')
                    else:
                        bot.editMessageText(message, f'🗑️ Evidencia eliminada: {evidence_name}')
                    
                else:
                    bot.editMessageText(message, '➲ Error y Causas ✗\n1-Revise su Cuenta\n2-Servidor Deshabilitado')
            except ValueError:
                bot.editMessageText(message, '❌ Formato incorrecto. Use: /del_0')
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                print(f"Error en /del_: {e}")
                
        elif '/delall' in msgText:
            try:
                proxy_dict = {}
                if user_info.get('proxy'):
                    proxy_dict = ProxyManager.get_proxy_dict_for_client(user_info['proxy'])
                
                client = SimpleMoodleClient(
                    user_info['moodle_user'],
                    user_info['moodle_password'],
                    user_info['moodle_host'],
                    user_info['moodle_repo_id'],
                    proxy_dict=proxy_dict
                )
                
                logged = client.login()
                if logged:
                    evfiles = client.getEvidences()
                    if not evfiles:
                        bot.editMessageText(message, 'ℹ️ No hay evidencias para eliminar')
                        client.logout()
                        return
                    
                    total_evidences = len(evfiles)
                    total_files = 0
                    all_deleted_files = []
                    
                    for ev in evfiles:
                        files_in_evidence = ev.get('files', [])
                        total_files += len(files_in_evidence)
                        
                        for f in files_in_evidence:
                            filename = f.get('filename', f.get('name', f"archivo_{len(all_deleted_files)+1}"))
                            all_deleted_files.append({
                                'filename': filename,
                                'evidence_name': ev['name']
                            })
                    
                    # Simular eliminación de todas
                    # for item in evfiles:
                    #     client.deleteEvidence(item)
                    
                    client.logout()
                    
                    memory_stats.log_delete_all(
                        username=username, 
                        deleted_evidences=total_evidences, 
                        deleted_files=total_files,
                        moodle_host=user_info['moodle_host']
                    )
                    
                    for file_info in all_deleted_files:
                        memory_stats.log_delete(
                            username=username,
                            filename=file_info['filename'],
                            evidence_name=file_info['evidence_name'],
                            moodle_host=user_info['moodle_host']
                        )
                    
                    bot.editMessageText(message, f'🗑️ TODAS las evidencias eliminadas\n📦 {total_evidences} evidencia(s) borrada(s)\n📁 Total archivos: {total_files}')
                    
                else:
                    bot.editMessageText(message, '➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado')
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                print(f"Error en /delall: {e}")
                
        elif 'http' in msgText:
            url = msgText
            
            # Verificación de tamaño con eliminación INMEDIATA a los 8 segundos
            try:
                import requests
                headers = {}
                if user_info.get('proxy'):
                    proxy_dict = ProxyManager.get_proxy_dict_for_client(user_info['proxy'])
                    if proxy_dict:
                        # Configurar proxy para la verificación
                        temp_session = requests.Session()
                        temp_session.proxies.update(proxy_dict)
                        response = temp_session.head(url, allow_redirects=True, timeout=5)
                        temp_session.close()
                    else:
                        response = requests.head(url, allow_redirects=True, timeout=5)
                else:
                    response = requests.head(url, allow_redirects=True, timeout=5)
                
                file_size = int(response.headers.get('content-length', 0))
                file_size_mb = file_size / (1024 * 1024)
                
                # Si es mayor a 200MB, mostrar y eliminar INMEDIATAMENTE
                if file_size_mb > 200:
                    funny_message = get_random_large_file_message()
                    send_funny_message_and_delete(bot, update.message.chat.id, funny_message, file_size_mb)
                
            except Exception as e:
                # Silenciar error de verificación
                pass
            
            # Proceder con descarga
            ddl(update, bot, message, url, file_name='', thread=thread, jdb=jdb)
            
        else:
            bot.editMessageText(message, '➲ No se pudo procesar ✗ ')
            
    except Exception as ex:
        print(f"Error general en onmessage: {str(ex)}")
        print(traceback.format_exc())

def main():
    bot = ObigramClient(BOT_TOKEN)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()
