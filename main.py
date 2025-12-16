from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

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
import ssl
import urllib3
from urllib.parse import urlparse
import requests

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
# SISTEMA DE ESTADÍSTICAS PERSISTENTE EN JSON
# ============================================

class PersistentStats:
    """Sistema de estadísticas persistente usando archivo JSON"""
    
    def __init__(self, filename='bot_stats.json'):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self):
        """Carga datos desde archivo JSON"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error cargando estadísticas: {e}")
        
        # Estructura inicial si no existe el archivo
        return {
            'created_at': self.get_current_timestamp(),
            'last_update': self.get_current_timestamp(),
            'total_uploads': 0,
            'total_deletes': 0,
            'total_size_uploaded': 0,  # en bytes
            'daily_stats': {},  # Estadísticas por día
            'user_stats': {},   # Estadísticas por usuario
            'upload_logs': [],  # Historial de subidas
            'delete_logs': []   # Historial de eliminaciones
        }
    
    def save_data(self):
        """Guarda datos al archivo JSON"""
        try:
            self.data['last_update'] = self.get_current_timestamp()
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando estadísticas: {e}")
            return False
    
    def get_current_timestamp(self):
        """Obtiene timestamp actual formateado"""
        dt = get_cuba_time()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_today_key(self):
        """Obtiene la clave para el día actual (ej: '2024-12-16')"""
        dt = get_cuba_time()
        return dt.strftime("%Y-%m-%d")
    
    def get_current_datetime_display(self):
        """Obtiene fecha/hora para mostrar"""
        return format_cuba_datetime()
    
    def log_upload(self, username, filename, file_size, moodle_host):
        """Registra una subida exitosa"""
        try:
            file_size = int(file_size)
        except:
            file_size = 0
        
        today = self.get_today_key()
        timestamp = self.get_current_timestamp()
        display_time = self.get_current_datetime_display()
        
        # Actualizar estadísticas globales
        self.data['total_uploads'] += 1
        self.data['total_size_uploaded'] += file_size
        
        # Actualizar estadísticas del día
        if today not in self.data['daily_stats']:
            self.data['daily_stats'][today] = {
                'date': today,
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'users': {}
            }
        
        self.data['daily_stats'][today]['uploads'] += 1
        self.data['daily_stats'][today]['total_size'] += file_size
        
        # Actualizar usuario en estadísticas del día
        if username not in self.data['daily_stats'][today]['users']:
            self.data['daily_stats'][today]['users'][username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0
            }
        
        self.data['daily_stats'][today]['users'][username]['uploads'] += 1
        self.data['daily_stats'][today]['users'][username]['total_size'] += file_size
        
        # Actualizar estadísticas del usuario (globales)
        if username not in self.data['user_stats']:
            self.data['user_stats'][username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'first_activity': timestamp,
                'last_activity': timestamp,
                'last_activity_display': display_time
            }
        
        self.data['user_stats'][username]['uploads'] += 1
        self.data['user_stats'][username]['total_size'] += file_size
        self.data['user_stats'][username]['last_activity'] = timestamp
        self.data['user_stats'][username]['last_activity_display'] = display_time
        
        # Registrar en logs
        log_entry = {
            'timestamp': timestamp,
            'display_time': display_time,
            'username': username,
            'filename': filename,
            'file_size_bytes': file_size,
            'file_size_formatted': format_file_size(file_size),
            'moodle_host': moodle_host,
            'date_key': today
        }
        self.data['upload_logs'].append(log_entry)
        
        # Mantener solo últimos 500 logs para no hacer el archivo muy grande
        if len(self.data['upload_logs']) > 500:
            self.data['upload_logs'].pop(0)
        
        # Guardar cambios
        self.save_data()
        return True
    
    def log_delete(self, username, filename, evidence_name, moodle_host):
        """Registra una eliminación individual"""
        today = self.get_today_key()
        timestamp = self.get_current_timestamp()
        display_time = self.get_current_datetime_display()
        
        # Actualizar estadísticas globales
        self.data['total_deletes'] += 1
        
        # Actualizar estadísticas del día
        if today not in self.data['daily_stats']:
            self.data['daily_stats'][today] = {
                'date': today,
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'users': {}
            }
        
        self.data['daily_stats'][today]['deletes'] += 1
        
        # Actualizar usuario en estadísticas del día
        if username not in self.data['daily_stats'][today]['users']:
            self.data['daily_stats'][today]['users'][username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0
            }
        
        self.data['daily_stats'][today]['users'][username]['deletes'] += 1
        
        # Actualizar estadísticas del usuario (globales)
        if username not in self.data['user_stats']:
            self.data['user_stats'][username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'first_activity': timestamp,
                'last_activity': timestamp,
                'last_activity_display': display_time
            }
        
        self.data['user_stats'][username]['deletes'] += 1
        self.data['user_stats'][username]['last_activity'] = timestamp
        self.data['user_stats'][username]['last_activity_display'] = display_time
        
        # Registrar en logs
        log_entry = {
            'timestamp': timestamp,
            'display_time': display_time,
            'username': username,
            'filename': filename,
            'evidence_name': evidence_name,
            'moodle_host': moodle_host,
            'type': 'delete',
            'date_key': today
        }
        self.data['delete_logs'].append(log_entry)
        
        # Mantener solo últimos 500 logs
        if len(self.data['delete_logs']) > 500:
            self.data['delete_logs'].pop(0)
        
        # Guardar cambios
        self.save_data()
        return True
    
    def log_delete_all(self, username, deleted_evidences, deleted_files, moodle_host):
        """Registra eliminación masiva"""
        today = self.get_today_key()
        timestamp = self.get_current_timestamp()
        display_time = self.get_current_datetime_display()
        
        # Actualizar estadísticas globales
        self.data['total_deletes'] += deleted_files
        
        # Actualizar estadísticas del día
        if today not in self.data['daily_stats']:
            self.data['daily_stats'][today] = {
                'date': today,
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'users': {}
            }
        
        self.data['daily_stats'][today]['deletes'] += deleted_files
        
        # Actualizar usuario en estadísticas del día
        if username not in self.data['daily_stats'][today]['users']:
            self.data['daily_stats'][today]['users'][username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0
            }
        
        self.data['daily_stats'][today]['users'][username]['deletes'] += deleted_files
        
        # Actualizar estadísticas del usuario (globales)
        if username not in self.data['user_stats']:
            self.data['user_stats'][username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'first_activity': timestamp,
                'last_activity': timestamp,
                'last_activity_display': display_time
            }
        
        self.data['user_stats'][username]['deletes'] += deleted_files
        self.data['user_stats'][username]['last_activity'] = timestamp
        self.data['user_stats'][username]['last_activity_display'] = display_time
        
        # Registrar en logs
        log_entry = {
            'timestamp': timestamp,
            'display_time': display_time,
            'username': username,
            'action': 'delete_all',
            'deleted_evidences': deleted_evidences,
            'deleted_files': deleted_files,
            'moodle_host': moodle_host,
            'type': 'delete_all',
            'date_key': today
        }
        self.data['delete_logs'].append(log_entry)
        
        # Mantener solo últimos 500 logs
        if len(self.data['delete_logs']) > 500:
            self.data['delete_logs'].pop(0)
        
        # Guardar cambios
        self.save_data()
        return True
    
    def get_user_stats(self, username):
        """Obtiene estadísticas de un usuario"""
        if username in self.data['user_stats']:
            return self.data['user_stats'][username]
        return None
    
    def get_all_stats(self):
        """Obtiene todas las estadísticas globales"""
        return {
            'total_uploads': self.data['total_uploads'],
            'total_deletes': self.data['total_deletes'],
            'total_size_uploaded': self.data['total_size_uploaded'],
            'created_at': self.data['created_at'],
            'last_update': self.data['last_update'],
            'total_days': len(self.data['daily_stats'])
        }
    
    def get_all_users(self):
        """Obtiene todos los usuarios"""
        return self.data['user_stats']
    
    def get_recent_uploads(self, limit=10):
        """Obtiene subidas recientes"""
        logs = self.data['upload_logs']
        return logs[-limit:][::-1] if logs else []
    
    def get_recent_deletes(self, limit=10):
        """Obtiene eliminaciones recientes"""
        logs = self.data['delete_logs']
        return logs[-limit:][::-1] if logs else []
    
    def get_daily_stats(self, date_key=None):
        """Obtiene estadísticas de un día específico o del último día"""
        if not self.data['daily_stats']:
            return None
        
        if date_key:
            return self.data['daily_stats'].get(date_key)
        else:
            # Obtener el último día
            sorted_dates = sorted(self.data['daily_stats'].keys(), reverse=True)
            if sorted_dates:
                return self.data['daily_stats'][sorted_dates[0]]
        return None
    
    def get_all_daily_stats(self):
        """Obtiene todas las estadísticas diarias"""
        return self.data['daily_stats']
    
    def has_any_data(self):
        """Verifica si hay datos"""
        return len(self.data['upload_logs']) > 0 or len(self.data['delete_logs']) > 0
    
    def clear_all_data(self):
        """Limpia todos los datos (pero mantiene el archivo)"""
        # Guardar solo información básica
        self.data = {
            'created_at': self.get_current_timestamp(),
            'last_update': self.get_current_timestamp(),
            'total_uploads': 0,
            'total_deletes': 0,
            'total_size_uploaded': 0,
            'daily_stats': {},
            'user_stats': {},
            'upload_logs': [],
            'delete_logs': []
        }
        self.save_data()
        return "✅ Todos los datos han sido eliminados (se creó nuevo archivo)"
    
    def get_stats_summary(self):
        """Obtiene un resumen completo de estadísticas"""
        total_days = len(self.data['daily_stats'])
        total_users = len(self.data['user_stats'])
        
        # Calcular promedio por día
        avg_uploads = self.data['total_uploads'] / total_days if total_days > 0 else 0
        avg_deletes = self.data['total_deletes'] / total_days if total_days > 0 else 0
        
        return {
            'total_days': total_days,
            'total_users': total_users,
            'avg_uploads_per_day': round(avg_uploads, 1),
            'avg_deletes_per_day': round(avg_deletes, 1)
        }

# Instancia global de estadísticas
persistent_stats = PersistentStats()

# ============================================
# SISTEMA DE PROXY MEJORADO CON SOPORTE HTTPS
# ============================================

class ProxyManager:
    """Manejador de proxies integrado con soporte HTTPS."""
    
    @staticmethod
    def parse_proxy(proxy_text):
        """
        Parsea un string de proxy.
        Formatos soportados:
        1. socks5://usuario:contraseña@ip:puerto
        2. socks5://ip:puerto
        3. http://usuario:contraseña@ip:puerto
        4. http://ip:puerto
        5. https://usuario:contraseña@ip:puerto  ← NUEVO
        6. https://ip:puerto                      ← NUEVO
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
                    # Puertos por defecto según el tipo de proxy
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
            
            # Construir URL del proxy según el tipo
            if username and password:
                if proxy_type == 'https':
                    # Para HTTPS proxy, usar autenticación básica en URL
                    proxy_url = f"https://{username}:{password}@{ip}:{port}"
                else:
                    proxy_url = f"{proxy_type}://{username}:{password}@{ip}:{port}"
            else:
                proxy_url = f"{proxy_type}://{ip}:{port}"
            
            # Para proxies HTTP/HTTPS, necesitamos configurar ambos
            if proxy_type == 'http':
                return {
                    'http': proxy_url,
                    'https': proxy_url,  # HTTP proxy también maneja HTTPS
                    'original': proxy_text,
                    'type': proxy_type,
                    'ip': ip,
                    'port': port,
                    'username': username,
                    'has_auth': username is not None
                }
            elif proxy_type == 'https':
                # Proxy HTTPS específico
                return {
                    'http': proxy_url.replace('https://', 'http://'),  # Fallback a HTTP
                    'https': proxy_url,
                    'original': proxy_text,
                    'type': proxy_type,
                    'ip': ip,
                    'port': port,
                    'username': username,
                    'has_auth': username is not None
                }
            else:  # socks5
                return {
                    'http': f'socks5://{ip}:{port}',
                    'https': f'socks5://{ip}:{port}',
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
        
        # Devolver solo las URLs para requests
        return {
            'http': proxy_info['http'],
            'https': proxy_info['https']
        }
    
    @staticmethod
    def test_proxy(proxy_text):
        """Testea si un proxy funciona."""
        if not proxy_text:
            return False, "No se proporcionó proxy"
        
        try:
            proxy_dict = ProxyManager.get_proxy_for_requests(proxy_text)
            if not proxy_dict:
                return False, "Formato de proxy inválido"
            
            # Intentar conectar a un sitio de prueba
            test_url = "http://httpbin.org/ip"
            timeout = 10
            
            response = requests.get(
                test_url, 
                proxies=proxy_dict,
                timeout=timeout,
                verify=False  # Desactivar verificación SSL para testing
            )
            
            if response.status_code == 200:
                # Verificar que estamos usando el proxy
                data = response.json()
                if 'origin' in data:
                    return True, f"✅ Proxy funcionando\nIP detectada: {data['origin']}"
                return True, "✅ Proxy funcionando"
            else:
                return False, f"❌ Error HTTP {response.status_code}"
                
        except requests.exceptions.ConnectTimeout:
            return False, "❌ Timeout de conexión"
        except requests.exceptions.ProxyError:
            return False, "❌ Error de proxy (no se pudo conectar)"
        except requests.exceptions.SSLError:
            return False, "❌ Error SSL (proxy HTTPS puede requerir certificados)"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

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

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'⬆️ Preparando Para Subir ☁ ●●○')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        
        # OBTENER PROXY USANDO EL NUEVO SISTEMA
        proxy = {}
        if user_info.get('proxy'):
            proxy = ProxyManager.get_proxy_for_requests(user_info['proxy'])
        
        client = MoodleClient(user_info['moodle_user'],
                              user_info['moodle_password'],
                              user_info['moodle_host'],
                              user_info['moodle_repo_id'],
                              proxy=proxy)
        loged = client.login()
        if loged:
            evidences = client.getEvidences()
            evidname = str(filename).split('.')[0]
            for evid in evidences:
                if evid['name'] == evidname:
                    evidence = evid
                    break
            if evidence is None:
                evidence = client.createEvidence(evidname)

            originalfile = ''
            if len(files)>1:
                originalfile = filename
            draftlist = []
            for f in files:
                f_size = get_file_size(f)
                resp = None
                iter = 0
                tokenize = False
                if user_info['tokenize']!=0:
                   tokenize = True
                while resp is None:
                    fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                    draftlist.append(resp)
                    iter += 1
                    if iter>=10:
                        break
                os.unlink(f)
            try:
                client.saveEvidence(evidence)
            except:pass
            return draftlist
        else:
            bot.editMessageText(message,'➥ Error En La Pagina ✗')
            return None
    except Exception as ex:
        bot.editMessageText(message,'➥ Error ✗\n' + str(ex))
        return None

def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(mult_file.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
        file_upload_count = 1
    
    evidname = ''
    files = []
    if client:
        evidname = str(file).split('.')[0]
        txtname = evidname + '.txt'
        try:
            # OBTENER PROXY USANDO EL NUEVO SISTEMA
            proxy = {}
            if getUser.get('proxy'):
                proxy = ProxyManager.get_proxy_for_requests(getUser['proxy'])
            
            moodle_client = MoodleClient(getUser['moodle_user'],
                                         getUser['moodle_password'],
                                         getUser['moodle_host'],
                                         getUser['moodle_repo_id'],
                                         proxy=proxy)
            if moodle_client.login():
                evidences = moodle_client.getEvidences()
                
                # Buscar la evidencia que acabamos de crear/subir
                evidence_index = -1
                for idx, ev in enumerate(evidences):
                    if ev['name'] == evidname:
                        files = ev['files']
                        for i in range(len(files)):
                            url = files[i]['directurl']
                            if '?forcedownload=1' in url:
                                url = url.replace('?forcedownload=1', '')
                            elif '&forcedownload=1' in url:
                                url = url.replace('&forcedownload=1', '')
                            if '&token=' in url and '?' not in url:
                                url = url.replace('&token=', '?token=', 1)
                            files[i]['directurl'] = url
                        evidence_index = idx
                        break
                
                moodle_client.logout()
                
                # Usar el índice correcto para el mensaje final
                findex = evidence_index if evidence_index != -1 else len(evidences) - 1
        except Exception as e:
            print(f"Error obteniendo índice de evidencia: {e}")
            findex = 0
        
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        
        # REGISTRAR SUBIDA EN ESTADÍSTICAS PERSISTENTES
        username = update.message.sender.username
        filename_clean = os.path.basename(file)
        persistent_stats.log_upload(
            username=username,
            filename=filename_clean,
            file_size=file_size,
            moodle_host=getUser['moodle_host']
        )
        
        if len(files)>0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
    else:
        bot.editMessageText(message,'➥ Error en la página ✗')

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)
        else:
            try:
                bot.editMessageText(message,'➥ Error en la descarga ✗')
            except:
                bot.editMessageText(message,'➥ Error en la descarga ✗')

def sendTxt(name,files,update,bot):
    txt = open(name,'w')
    
    for i, f in enumerate(files):
        url = f['directurl']
        
        if '?forcedownload=1' in url:
            url = url.replace('?forcedownload=1', '')
        elif '&forcedownload=1' in url:
            url = url.replace('&forcedownload=1', '')
        
        if '&token=' in url and '?' not in url:
            url = url.replace('&token=', '?token=', 1)
        
        txt.write(url)
        
        if i < len(files) - 1:
            txt.write('\n\n')
    
    txt.close()
    bot.sendFile(update.message.chat.id,name)
    os.unlink(name)

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

def delete_message_after_delay(bot, chat_id, message_id, delay=8):
    """Elimina un mensaje después de un retraso específico"""
    def delete():
        time.sleep(delay)
        try:
            bot.deleteMessage(chat_id, message_id)
        except Exception as e:
            print(f"Error al eliminar mensaje: {e}")
    
    thread = threading.Thread(target=delete)
    thread.daemon = True
    thread.start()

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()
        
        expanded_users = expand_user_groups()
        
        if username not in expanded_users:
            bot.sendMessage(update.message.chat.id,'➲ No tienes acceso a este bot ✗')
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
        try: msgText = update.message.text
        except:pass

        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'➲ Tarea Cancelada ✗ ')
            except Exception as ex:
                print(str(ex))
            return

        message = bot.sendMessage(update.message.chat.id,'➲ Procesando ✪ ●●○')
        thread.store('msg',message)

        # NUEVO COMANDO: /proxy - PARA CONFIGURAR PROXY DINÁMICAMENTE
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
                    response += "/proxy https://ip:puerto - Establecer HTTPS (nuevo) ✨\n"
                    response += "/proxy test - Probar proxy actual\n"
                    response += "/proxy off - Eliminar proxy\n\n"
                    response += "📌 EJEMPLOS:\n"
                    response += "/proxy socks5://127.0.0.1:1080\n"
                    response += "/proxy socks5://usuario:contraseña@192.168.1.1:1080\n"
                    response += "/proxy http://proxy.com:8080\n"
                    response += "/proxy https://secure-proxy.com:443"
                    
                    bot.editMessageText(message, response)
                    
                elif '/proxy test' in msgText.lower():
                    # Probar proxy actual
                    current_proxy = user_info.get('proxy', '')
                    if not current_proxy:
                        bot.editMessageText(message, "❌ No hay proxy configurado para probar")
                        return
                    
                    bot.editMessageText(message, "🔍 Probando conexión del proxy...")
                    success, result = ProxyManager.test_proxy(current_proxy)
                    bot.editMessageText(message, result)
                    
                elif '/proxy off' in msgText.lower():
                    # Eliminar proxy
                    user_info['proxy'] = ''
                    jdb.save_data_user(username, user_info)
                    jdb.save()
                    bot.editMessageText(message, '✅ Proxy eliminado exitosamente')
                    
                else:
                    # Establecer nuevo proxy
                    # Extraer el texto del proxy después de /proxy
                    proxy_text = msgText[6:].strip()  # Quita '/proxy'
                    
                    # Si todavía tiene espacios, tomar solo la primera parte
                    if ' ' in proxy_text:
                        # Si es "test", ya lo manejamos arriba
                        if proxy_text.split(' ')[0].lower() == 'test':
                            return
                        proxy_text = proxy_text.split(' ')[0]
                    
                    if proxy_text:
                        # Validar el formato del proxy
                        proxy_info = ProxyManager.parse_proxy(proxy_text)
                        
                        if proxy_info:
                            user_info['proxy'] = proxy_text
                            jdb.save_data_user(username, user_info)
                            jdb.save()
                            
                            display = ProxyManager.format_proxy_for_display(proxy_info)
                            bot.editMessageText(message, f'✅ Proxy configurado exitosamente\n\n{display}\n\n💡 Usa /proxy test para probarlo')
                        else:
                            bot.editMessageText(message, '❌ Formato de proxy inválido\n\nFormatos soportados:\n• socks5://ip:puerto\n• socks5://user:pass@ip:puerto\n• http://ip:puerto\n• https://ip:puerto ✨\n• ip:puerto (asume SOCKS5)')
                    else:
                        bot.editMessageText(message, '❌ Debes especificar un proxy\n\nEjemplo: /proxy socks5://127.0.0.1:1080')
                        
            except Exception as e:
                print(f"Error en comando proxy: {e}")
                bot.editMessageText(message, f'❌ Error al configurar proxy: {str(e)}')
            return

        # COMANDO MYSTATS PARA TODOS LOS USUARIOS
        if '/mystats' in msgText:
            user_stats = persistent_stats.get_user_stats(username)
            all_stats = persistent_stats.get_all_stats()
            
            # Obtener información del proxy actual
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
📅 Primera actividad: {user_stats.get('first_activity', 'N/A')}
📅 Última actividad: {user_stats.get('last_activity_display', 'N/A')}
🔗 Nube: {user_info['moodle_host']}{proxy_info}
━━━━━━━━━━━━━━━━━━━
📈 Resumen global:
• Total días registrados: {all_stats.get('total_days', 0)}
• Total subidas bot: {all_stats.get('total_uploads', 0)}
• Total eliminaciones: {all_stats.get('total_deletes', 0)}
                """
            else:
                stats_msg = f"""
📊 TUS ESTADÍSTICAS

👤 Usuario: @{username}
📤 Archivos subidos: 0
🗑️ Archivos eliminados: 0
💾 Espacio total usado: 0 B
📅 Primera actividad: Nunca
📅 Última actividad: Nunca
🔗 Nube: {user_info['moodle_host']}{proxy_info}
━━━━━━━━━━━━━━━━━━━
ℹ️ Aún no has realizado ninguna acción
                """
            
            bot.editMessageText(message, stats_msg)
            return

        # COMANDOS DE ADMINISTRADOR
        if username == ADMIN_USERNAME:
            if '/admin' in msgText:
                stats = persistent_stats.get_all_stats()
                summary = persistent_stats.get_stats_summary()
                total_size_formatted = format_file_size(stats['total_size_uploaded'])
                current_date = format_cuba_date()
                
                if persistent_stats.has_any_data():
                    admin_msg = f"""
👑 PANEL DE ADMINISTRADOR
📅 {current_date}
━━━━━━━━━━━━━━━━━━━
📊 ESTADÍSTICAS GLOBALES:
• Subidas totales: {stats['total_uploads']}
• Eliminaciones totales: {stats['total_deletes']}
• Espacio total subido: {total_size_formatted}
• Días registrados: {stats['total_days']}
• Usuarios únicos: {summary['total_users']}

📈 PROMEDIOS:
• {summary['avg_uploads_per_day']} subidas/día
• {summary['avg_deletes_per_day']} eliminaciones/día

🔧 COMANDOS DISPONIBLES:
/adm_logs - Ver últimos logs
/adm_users - Ver estadísticas por usuario
/adm_uploads - Ver últimas subidas
/adm_deletes - Ver últimas eliminaciones
/adm_daily - Ver estadísticas diarias
/adm_cleardata - Limpiar todos los datos
━━━━━━━━━━━━━━━━━━━
📅 Estadísticas desde: {stats['created_at']}
🕐 Hora Cuba: {format_cuba_datetime().split(' ')[1]}
                    """
                else:
                    admin_msg = f"""
👑 PANEL DE ADMINISTRADOR
📅 {current_date}
━━━━━━━━━━━━━━━━━━━
⚠️ NO HAY DATOS REGISTRADOS
Aún no se ha realizado ninguna acción en el bot.

🔧 COMANDOS DISPONIBLES:
/adm_logs - Ver últimos logs
/adm_users - Ver estadísticas por usuario
/adm_uploads - Ver últimas subidas
/adm_deletes - Ver últimas eliminaciones
/adm_daily - Ver estadísticas diarias
━━━━━━━━━━━━━━━━━━━
🕐 Hora Cuba: {format_cuba_datetime().split(' ')[1]}
                    """
                
                bot.editMessageText(message, admin_msg)
                return
            
            elif '/adm_logs' in msgText:
                try:
                    if not persistent_stats.has_any_data():
                        bot.editMessageText(message, "⚠️ No hay datos registrados\nAún no se ha realizado ninguna acción en el bot.")
                        return
                    
                    limit = 20
                    if '_' in msgText:
                        try:
                            limit = int(msgText.split('_')[2])
                        except: pass
                    
                    uploads = persistent_stats.get_recent_uploads(limit)
                    deletes = persistent_stats.get_recent_deletes(limit)
                    
                    logs_msg = f"📋 ÚLTIMOS LOGS\n"
                    logs_msg += f"📅 {format_cuba_date()}\n"
                    logs_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    if uploads:
                        logs_msg += "⬆️ ÚLTIMAS SUBIDAS:\n"
                        for log in uploads:
                            logs_msg += f"• {log['display_time']} - @{log['username']}: {log['filename']} ({log['file_size_formatted']})\n"
                        logs_msg += "\n"
                    
                    if deletes:
                        logs_msg += "🗑️ ÚLTIMAS ELIMINACIONES:\n"
                        for log in deletes:
                            if log['type'] == 'delete_all':
                                logs_msg += f"• {log['display_time']} - @{log['username']}: ELIMINÓ TODO ({log.get('deleted_evidences', 1)} evidencia(s), {log.get('deleted_files', '?')} archivos)\n"
                            else:
                                logs_msg += f"• {log['display_time']} - @{log['username']}: {log['filename']} (de: {log['evidence_name']})\n"
                    
                    if len(logs_msg) > 4000:
                        logs_msg = logs_msg[:4000] + "\n\n⚠️ Logs truncados (demasiados)"
                    
                    bot.editMessageText(message, logs_msg)
                except Exception as e:
                    bot.editMessageText(message, f"❌ Error al obtener logs: {str(e)}")
                return
            
            elif '/adm_users' in msgText:
                try:
                    users = persistent_stats.get_all_users()
                    if not users:
                        bot.editMessageText(message, "⚠️ No hay usuarios registrados\nAún no se ha completado ninguna acción exitosa.")
                        return
                    
                    users_msg = f"👥 ESTADÍSTICAS POR USUARIO\n"
                    users_msg += f"📅 {format_cuba_date()}\n"
                    users_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    for user, data in sorted(users.items(), key=lambda x: x[1]['uploads'], reverse=True):
                        total_size_formatted = format_file_size(data['total_size'])
                        users_msg += f"👤 @{user}\n"
                        users_msg += f"   📤 Subidas: {data['uploads']}\n"
                        users_msg += f"   🗑️ Eliminaciones: {data['deletes']}\n"
                        users_msg += f"   💾 Espacio usado: {total_size_formatted}\n"
                        users_msg += f"   📅 Última actividad: {data.get('last_activity_display', 'N/A')}\n\n"
                    
                    if len(users_msg) > 4000:
                        users_msg = users_msg[:4000] + "\n\n⚠️ Lista truncada (demasiados usuarios)"
                    
                    bot.editMessageText(message, users_msg)
                except Exception as e:
                    bot.editMessageText(message, f"❌ Error al obtener usuarios: {str(e)}")
                return
            
            elif '/adm_uploads' in msgText:
                try:
                    uploads = persistent_stats.get_recent_uploads(15)
                    if not uploads:
                        bot.editMessageText(message, "⚠️ No hay subidas registradas\nAún no se ha completado ninguna subida exitosa.")
                        return
                    
                    uploads_msg = f"📤 ÚLTIMAS SUBIDAS\n"
                    uploads_msg += f"📅 {format_cuba_date()}\n"
                    uploads_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    for i, log in enumerate(uploads, 1):
                        uploads_msg += f"{i}. {log['filename']}\n"
                        uploads_msg += f"   👤 @{log['username']}\n"
                        uploads_msg += f"   📅 {log['display_time']}\n"
                        uploads_msg += f"   📏 {log['file_size_formatted']}\n"
                        uploads_msg += f"   🔗 {log['moodle_host']}\n"
                        uploads_msg += f"   🗓️ Día: {log.get('date_key', 'N/A')}\n\n"
                    
                    bot.editMessageText(message, uploads_msg)
                except Exception as e:
                    bot.editMessageText(message, f"❌ Error al obtener subidas: {str(e)}")
                return
            
            elif '/adm_deletes' in msgText:
                try:
                    deletes = persistent_stats.get_recent_deletes(15)
                    if not deletes:
                        bot.editMessageText(message, "⚠️ No hay eliminaciones registradas\nAún no se ha completado ninguna eliminación exitosa.")
                        return
                    
                    deletes_msg = f"🗑️ ÚLTIMAS ELIMINACIONES\n"
                    deletes_msg += f"📅 {format_cuba_date()}\n"
                    deletes_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    for i, log in enumerate(deletes, 1):
                        if log['type'] == 'delete_all':
                            deletes_msg += f"{i}. ELIMINACIÓN MASIVA\n"
                            deletes_msg += f"   👤 @{log['username']}\n"
                            deletes_msg += f"   📅 {log['display_time']}\n"
                            deletes_msg += f"   ⚠️ ELIMINÓ {log.get('deleted_evidences', 1)} EVIDENCIA(S)\n"
                            deletes_msg += f"   🗑️ Archivos borrados: {log.get('deleted_files', '?')}\n"
                        else:
                            deletes_msg += f"{i}. {log['filename']}\n"
                            deletes_msg += f"   👤 @{log['username']}\n"
                            deletes_msg += f"   📅 {log['display_time']}\n"
                            deletes_msg += f"   📁 Evidencia: {log['evidence_name']}\n"
                        
                        deletes_msg += f"   🔗 {log['moodle_host']}\n"
                        deletes_msg += f"   🗓️ Día: {log.get('date_key', 'N/A')}\n\n"
                    
                    bot.editMessageText(message, deletes_msg)
                except Exception as e:
                    bot.editMessageText(message, f"❌ Error al obtener eliminaciones: {str(e)}")
                return
            
            elif '/adm_daily' in msgText:
                try:
                    daily_stats = persistent_stats.get_all_daily_stats()
                    if not daily_stats:
                        bot.editMessageText(message, "⚠️ No hay estadísticas diarias")
                        return
                    
                    # Ordenar fechas de más reciente a más antigua
                    sorted_dates = sorted(daily_stats.keys(), reverse=True)
                    
                    daily_msg = f"📅 ESTADÍSTICAS DIARIAS\n"
                    daily_msg += f"Total días: {len(sorted_dates)}\n"
                    daily_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    # Mostrar últimos 7 días o todos si son menos
                    limit = min(7, len(sorted_dates))
                    for i in range(limit):
                        date_key = sorted_dates[i]
                        day_data = daily_stats[date_key]
                        
                        # Formatear fecha
                        try:
                            year, month, day = date_key.split('-')
                            formatted_date = f"{day}/{month}/{year}"
                        except:
                            formatted_date = date_key
                        
                        daily_msg += f"📅 {formatted_date}\n"
                        daily_msg += f"   📤 Subidas: {day_data.get('uploads', 0)}\n"
                        daily_msg += f"   🗑️ Eliminaciones: {day_data.get('deletes', 0)}\n"
                        daily_msg += f"   💾 Tamaño: {format_file_size(day_data.get('total_size', 0))}\n"
                        daily_msg += f"   👥 Usuarios: {len(day_data.get('users', {}))}\n\n"
                    
                    if len(sorted_dates) > 7:
                        daily_msg += f"... y {len(sorted_dates) - 7} días más\n"
                    
                    bot.editMessageText(message, daily_msg)
                except Exception as e:
                    bot.editMessageText(message, f"❌ Error al obtener estadísticas diarias: {str(e)}")
                return
            
            elif '/adm_cleardata' in msgText:
                try:
                    if not persistent_stats.has_any_data():
                        bot.editMessageText(message, "⚠️ No hay datos para limpiar\nLa base de datos está vacía.")
                        return
                    
                    result = persistent_stats.clear_all_data()
                    bot.editMessageText(message, f"✅ {result}")
                except Exception as e:
                    bot.editMessageText(message, f"❌ Error al limpiar datos: {str(e)}")
                return

        # COMANDOS NORMALES
        if '/start' in msgText:
            # Mostrar información del proxy actual
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
            bot.editMessageText(message,start_msg)
            
        elif '/files' == msgText:
             # OBTENER PROXY USANDO EL NUEVO SISTEMA
             proxy = {}
             if user_info.get('proxy'):
                 proxy = ProxyManager.get_proxy_for_requests(user_info['proxy'])
             
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 bot.editMessageText(message,filesInfo)
                 client.logout()
             else:
                bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
                
        elif '/txt_' in msgText:
             try:
                 findex = int(str(msgText).split('_')[1])
                 # OBTENER PROXY USANDO EL NUEVO SISTEMA
                 proxy = {}
                 if user_info.get('proxy'):
                     proxy = ProxyManager.get_proxy_for_requests(user_info['proxy'])
                 
                 client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],proxy=proxy)
                 loged = client.login()
                 if loged:
                     evidences = client.getEvidences()
                     if findex < 0 or findex >= len(evidences):
                         bot.editMessageText(message, f'❌ Índice inválido. Use /files para ver la lista.')
                         client.logout()
                         return
                     
                     evindex = evidences[findex]
                     txtname = evindex['name']+'.txt'
                     sendTxt(txtname,evindex['files'],update,bot)
                     client.logout()
                     bot.editMessageText(message,'📄 TXT Aquí 👇')
                 else:
                    bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
             except ValueError:
                 bot.editMessageText(message, '❌ Formato incorrecto. Use: /txt_0 (donde 0 es el número de la evidencia)')
             except Exception as e:
                 bot.editMessageText(message, f'❌ Error: {str(e)}')
                 print(f"Error en /txt_: {e}")
             
        elif '/del_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                # OBTENER PROXY USANDO EL NUEVO SISTEMA
                proxy = {}
                if user_info.get('proxy'):
                    proxy = ProxyManager.get_proxy_for_requests(user_info['proxy'])
                
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],
                                       proxy=proxy)
                loged = client.login()
                if loged:
                    evidences = client.getEvidences()
                    if findex < 0 or findex >= len(evidences):
                        bot.editMessageText(message, f'❌ Índice inválido. Use /files para ver la lista.')
                        client.logout()
                        return
                    
                    evfile = evidences[findex]
                    evidence_name = evfile['name']
                    
                    # OBTENER NOMBRES REALES DE LOS ARCHIVOS
                    deleted_files = []
                    if 'files' in evfile:
                        for f in evfile['files']:
                            filename = None
                            if 'filename' in f:
                                filename = f['filename']
                            elif 'name' in f:
                                filename = f['name']
                            elif 'title' in f:
                                filename = f['title']
                            elif 'directurl' in f:
                                url = f['directurl']
                                if 'filename=' in url:
                                    import urllib.parse
                                    parsed = urllib.parse.urlparse(url)
                                    params = urllib.parse.parse_qs(parsed.query)
                                    if 'filename' in params:
                                        filename = params['filename'][0]
                                elif '/' in url:
                                    filename = url.split('/')[-1].split('?')[0]
                            
                            if not filename:
                                filename = f"archivo_{len(deleted_files)+1}"
                            
                            deleted_files.append(filename)
                    
                    # Eliminar la evidencia
                    client.deleteEvidence(evfile)
                    client.logout()
                    
                    # REGISTRAR CADA ARCHIVO ELIMINADO
                    for filename in deleted_files:
                        persistent_stats.log_delete(
                            username=username,
                            filename=filename,
                            evidence_name=evidence_name,
                            moodle_host=user_info['moodle_host']
                        )
                    
                    if len(deleted_files) > 0:
                        bot.editMessageText(message, f'🗑️ Evidencia eliminada: {evidence_name}\n📦 {len(deleted_files)} archivo(s) borrado(s)')
                    else:
                        bot.editMessageText(message, f'🗑️ Evidencia eliminada: {evidence_name}')
                    
                else:
                    bot.editMessageText(message,'➲ Error y Causas ✗\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except ValueError:
                bot.editMessageText(message, '❌ Formato incorrecto. Use: /del_0 (donde 0 es el número de la evidencia)')
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                print(f"Error en /del_: {e}")
                
        elif '/delall' in msgText:
            try:
                # OBTENER PROXY USANDO EL NUEVO SISTEMA
                proxy = {}
                if user_info.get('proxy'):
                    proxy = ProxyManager.get_proxy_for_requests(user_info['proxy'])
                
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],
                                       proxy=proxy)
                loged = client.login()
                if loged:
                    evfiles = client.getEvidences()
                    if not evfiles:
                        bot.editMessageText(message, 'ℹ️ No hay evidencias para eliminar')
                        client.logout()
                        return
                    
                    total_evidences = len(evfiles)
                    total_files = 0
                    
                    # Contar archivos totales y registrar cada archivo individual
                    all_deleted_files = []
                    for ev in evfiles:
                        files_in_evidence = ev.get('files', [])
                        total_files += len(files_in_evidence)
                        
                        # Registrar cada archivo individual para estadísticas
                        for f in files_in_evidence:
                            filename = None
                            if 'filename' in f:
                                filename = f['filename']
                            elif 'name' in f:
                                filename = f['name']
                            elif 'title' in f:
                                filename = f['title']
                            elif 'directurl' in f:
                                url = f['directurl']
                                if 'filename=' in url:
                                    import urllib.parse
                                    parsed = urllib.parse.urlparse(url)
                                    params = urllib.parse.parse_qs(parsed.query)
                                    if 'filename' in params:
                                        filename = params['filename'][0]
                                elif '/' in url:
                                    filename = url.split('/')[-1].split('?')[0]
                            
                            if not filename:
                                filename = f"archivo_{len(all_deleted_files)+1}"
                            
                            all_deleted_files.append({
                                'filename': filename,
                                'evidence_name': ev['name']
                            })
                    
                    # Eliminar TODAS las evidencias
                    for item in evfiles:
                        try:
                            client.deleteEvidence(item)
                        except Exception as e:
                            print(f"Error eliminando evidencia: {e}")
                    
                    client.logout()
                    
                    # REGISTRAR ELIMINACIÓN MASIVA
                    persistent_stats.log_delete_all(
                        username=username, 
                        deleted_evidences=total_evidences, 
                        deleted_files=total_files,
                        moodle_host=user_info['moodle_host']
                    )
                    
                    # También registrar cada archivo individualmente para logs detallados
                    for file_info in all_deleted_files:
                        persistent_stats.log_delete(
                            username=username,
                            filename=file_info['filename'],
                            evidence_name=file_info['evidence_name'],
                            moodle_host=user_info['moodle_host']
                        )
                    
                    bot.editMessageText(message, f'🗑️ TODAS las evidencias eliminadas\n📦 {total_evidences} evidencia(s) borrada(s)\n📁 Total archivos: {total_files}')
                    
                else:
                    bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                print(f"Error en /delall: {e}")
                
        elif 'http' in msgText:
            url = msgText
            
            # Verificación SILENCIOSA del tamaño (sin mostrar mensaje al usuario)
            funny_message_sent = None
            
            try:
                import requests
                # OBTENER PROXY USANDO EL NUEVO SISTEMA
                headers = {}
                if user_info.get('proxy'):
                    proxy_dict = ProxyManager.get_proxy_for_requests(user_info['proxy'])
                    if proxy_dict:
                        headers.update({'Proxy': proxy_dict.get('http', '')})
                
                response = requests.head(url, allow_redirects=True, timeout=5, headers=headers)
                file_size = int(response.headers.get('content-length', 0))
                file_size_mb = file_size / (1024 * 1024)
                
                # Si es mayor a 200MB, mostrar mensaje chistoso
                if file_size_mb > 200:
                    funny_message = get_random_large_file_message()
                    warning_msg = bot.sendMessage(update.message.chat.id, 
                                      f"⚠️ {funny_message}\n\n"
                                      f"📊 Tamaño detectado: {file_size_mb:.2f} MB\n"
                                      f"📁 Límite: 200 MB\n\n"
                                      f"⬇️ Iniciando descarga igualmente...")
                    funny_message_sent = warning_msg
                
            except Exception as e:
                # Silenciar cualquier error de verificación
                pass
            
            # PROCEDER CON LA DESCARGA
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
            
            # Eliminar mensaje chistoso después de 8 segundos si existe
            if funny_message_sent:
                delete_message_after_delay(bot, funny_message_sent.chat.id, funny_message_sent.message_id, 8)
            
        else:
            bot.editMessageText(message,'➲ No se pudo procesar ✗ ')
            
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
