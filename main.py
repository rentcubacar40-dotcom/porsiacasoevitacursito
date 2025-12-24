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
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import S5Crypto
import traceback
import random
import pytz
import threading
import requests
import tempfile
from PIL import Image
import io
from urllib.parse import urlparse

# CONFIGURACIÓN FIJA EN EL CÓDIGO
BOT_TOKEN = "8410047906:AAGntGHmkIuIvovBMQfy-gko2JTw3TNJsak"

# CONFIGURACIÓN ADMINISTRADOR
ADMIN_USERNAME = "Eliel_21"

# ZONA HORARIA DE CUBA
try:
    CUBA_TZ = pytz.timezone('America/Havana')
except:
    CUBA_TZ = None

# URL DEL THUMBNAIL (MODIFICA ESTA URL CON LA TUYA)
THUMBNAIL_URL = "https://raw.githubusercontent.com/rentcubacar40-dotcom/ThaliElielUff/refs/heads/main/1A00B1DF-A44D-4DCB-B3FE-375DDA8CA507.png"  # ← CAMBIA ESTA URL

# SEPARADOR PARA EVIDENCIAS POR USUARIO
USER_EVIDENCE_MARKER = " "  # Espacio como separador

# PRE-CONFIGURACIÓN DE USUARIOS
PRE_CONFIGURATED_USERS = {
    "Thali355,Eliel_21,Kev_inn10,diana060698": {
        "cloudtype": "moodle",
        "moodle_host": "https://moodle.instec.cu/",
        "moodle_repo_id": 3,
        "moodle_user": "Kevin.cruz",
        "moodle_password": "Kevin10.",
        "zips": 1023,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    },
    "maykolguille,yordante,veno_mancer,Miguwq": {
        "cloudtype": "moodle",
        "moodle_host": "https://cursos.uo.edu.cu/",
        "moodle_repo_id": 4,
        "moodle_user": "eric.serrano",
        "moodle_password": "Rulebreaker2316",
        "zips": 99,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    },
    "eliel21,gatitoo_miauu": {
        "cloudtype": "moodle",
        "moodle_host": "https://caipd.ucf.edu.cu/",
        "moodle_repo_id": 5,
        "moodle_user": "eliel21",
        "moodle_password": "ElielThali2115.",
        "zips": 99,
        "uploadtype": "evidence",
        "proxy": "",
        "tokenize": 0
    }
}

# ==============================
# SISTEMA DE THUMBNAILS DESDE URL
# ==============================

class ThumbnailManager:
    """Gestor de thumbnails descargados desde una URL global"""
    
    def __init__(self, thumbnail_url=None):
        """Inicializa el gestor de thumbnails"""
        self.thumbnail_url = thumbnail_url or THUMBNAIL_URL
        self.thumbnail_path = None
        self.thumbnail_data = None
        self.last_download_time = None
        self.cache_duration = 3600  # 1 hora en segundos
        
    def download_thumbnail(self):
        """Descarga el thumbnail desde la URL global"""
        try:
            if not self.thumbnail_url or self.thumbnail_url.strip() == "":
                print("⚠️ No hay URL de thumbnail configurada")
                return False
            
            print(f"📥 Descargando thumbnail desde: {self.thumbnail_url}")
            
            # Descargar la imagen
            response = requests.get(self.thumbnail_url, timeout=10)
            response.raise_for_status()
            
            # Cargar y procesar la imagen
            image = Image.open(io.BytesIO(response.content))
            
            # Redimensionar si es muy grande (máx 320x320 para thumbnails de Telegram)
            max_size = (320, 320)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Guardar en memoria
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=85)
            self.thumbnail_data = img_byte_arr.getvalue()
            
            self.last_download_time = datetime.datetime.now()
            print("✅ Thumbnail descargado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error al descargar thumbnail: {str(e)}")
            return False
    
    def get_thumbnail(self):
        """Obtiene el thumbnail (descarga si es necesario)"""
        try:
            # Si ya tenemos datos y no han pasado más de cache_duration segundos
            if (self.thumbnail_data and self.last_download_time and 
                (datetime.datetime.now() - self.last_download_time).seconds < self.cache_duration):
                return self.thumbnail_data
            
            # Si no tenemos datos o han caducado, descargar
            if self.download_thumbnail():
                return self.thumbnail_data
            else:
                return None
                
        except Exception as e:
            print(f"Error obteniendo thumbnail: {e}")
            return None
    
    def has_thumbnail(self):
        """Verifica si hay thumbnail disponible"""
        return self.get_thumbnail() is not None

# Crear instancia global del gestor de thumbnails
thumbnail_manager = ThumbnailManager()

# ==============================
# SISTEMA DE CACHÉ PARA OPTIMIZACIÓN
# ==============================

class CloudCache:
    """Sistema de caché para evitar refrescos innecesarios"""
    def __init__(self, ttl_seconds=30):
        self.cache = {}
        self.ttl = ttl_seconds
        self.last_refresh = {}
        self.last_full_refresh = None
    
    def should_refresh(self, cloud_name=None):
        """Determina si debe refrescar los datos"""
        if cloud_name is None:
            # Para refresco completo
            if self.last_full_refresh is None:
                return True
            elapsed = (datetime.datetime.now() - self.last_full_refresh).total_seconds()
            return elapsed > self.ttl
        
        # Para nube específica
        if cloud_name not in self.last_refresh:
            return True
        elapsed = (datetime.datetime.now() - self.last_refresh[cloud_name]).total_seconds()
        return elapsed > self.ttl
    
    def update_cache(self, cloud_name, data):
        """Actualiza la caché para una nube específica"""
        self.cache[cloud_name] = data
        self.last_refresh[cloud_name] = datetime.datetime.now()
    
    def update_full_cache(self, data):
        """Actualiza caché completa"""
        self.cache = data.copy()
        self.last_full_refresh = datetime.datetime.now()
    
    def get_cache(self, cloud_name):
        """Obtiene datos de caché"""
        return self.cache.get(cloud_name)
    
    def clear_cache(self):
        """Limpia toda la caché"""
        self.cache = {}
        self.last_refresh = {}
        self.last_full_refresh = None

cloud_cache = CloudCache(ttl_seconds=30)  # 30 segundos de caché

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

memory_stats = MemoryStats()

def get_random_large_file_message():
    """Retorna un mensaje chistoso aleatorio para archivos grandes"""
    messages = [
        "¡Uy! Este archivo pesa más que mis ganas de trabajar los lunes 📦",
        "¿Seguro que no estás subiendo toda la temporada de tu serie favorita? 🎬",
        "Archivo detectado: XXL. Mi bandeja de entrada necesita hacer dieta 🍔",
        "¡500MB alert! Esto es más grande que mi capacidad de decisión en un restaurante 🍕",
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
        "Detectado: Archivo XXL. Preparando refuerzos estructurales 🏗️",
        "¡Vaya! Este archivo es tan grande que necesita pasaporte para viajar 🌍",
        "Con este peso, hasta la nube digital va a necesitar paraguas ☂️",
        "¡500MB detectados! ¿Traes la biblioteca de Alejandría en un ZIP? 📚",
        "Tu archivo tiene más MB que yo tengo neuronas después del café 🧠",
        "¡Alerta! Archivo de tamaño épico detectado. Activando modo Hulk 💚",
        "Este archivo es más pesado que mis remordimientos del lunes 🎭",
        "¡Uy! Con este tamaño hasta internet va a sudar la gota gorda 💧",
        "¿Seguro que no estás subiendo un elefante en formato MP4? 🐘📹",
        "Archivo XXL: Mi conexión acaba de pedir aumento de sueldo 💰",
        "¡500MB! Hasta los píxeles están haciendo dieta en este archivo 🥗"
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
        proxy = ProxyCloud.parse(user_info['proxy'])
        
        client = MoodleClient(user_info['moodle_user'],
                              user_info['moodle_password'],
                              user_info['moodle_host'],
                              user_info['moodle_repo_id'],
                              proxy=proxy)
        loged = client.login()
        if loged:
            evidences = client.getEvidences()
            username = update.message.sender.username
            
            original_evidname = str(filename).split('.')[0]
            visible_evidname = original_evidname
            internal_evidname = f"{original_evidname}{USER_EVIDENCE_MARKER}{username}"
            
            for evid in evidences:
                if evid['name'] == internal_evidname:
                    evidence = evid
                    break
            if evidence is None:
                evidence = client.createEvidence(internal_evidname)

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
            bot.editMessageText(message,'➥ Error En La Página ✗')
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
    
    username = update.message.sender.username
    
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
    
    visible_evidname = ''
    files = []
    if client:
        original_evidname = str(file).split('.')[0]
        visible_evidname = original_evidname
        internal_evidname = f"{original_evidname}{USER_EVIDENCE_MARKER}{username}"
        
        txtname = visible_evidname + '.txt'
        try:
            proxy = ProxyCloud.parse(getUser['proxy'])
            moodle_client = MoodleClient(getUser['moodle_user'],
                                         getUser['moodle_password'],
                                         getUser['moodle_host'],
                                         getUser['moodle_repo_id'],
                                         proxy=proxy)
            if moodle_client.login():
                evidences = moodle_client.getEvidences()
                
                evidence_index = -1
                for idx, ev in enumerate(evidences):
                    if ev['name'] == internal_evidname:
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
                
                findex = evidence_index if evidence_index != -1 else len(evidences) - 1
        except Exception as e:
            print(f"Error obteniendo índice de evidencia: {e}")
            findex = 0
        
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        
        filename_clean = os.path.basename(file)
        memory_stats.log_upload(
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
    """Envía un archivo TXT con thumbnail desde URL"""
    try:
        # Crear el archivo TXT
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
        
        # Obtener el thumbnail desde la URL global
        thumbnail_data = thumbnail_manager.get_thumbnail()
        
        # Enviar el archivo TXT con thumbnail si está disponible
        if thumbnail_data:
            try:
                # Crear un archivo temporal para el thumbnail
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_thumb:
                    temp_thumb.write(thumbnail_data)
                    temp_thumb_path = temp_thumb.name
                
                # Enviar el archivo con thumbnail
                with open(temp_thumb_path, 'rb') as thumb_file, open(name, 'rb') as txt_file:
                    bot.sendDocument(
                        chat_id=update.message.chat.id,
                        document=txt_file,
                        filename=os.path.basename(name),
                        thumb=thumb_file
                    )
                
                # Eliminar archivo temporal del thumbnail
                os.unlink(temp_thumb_path)
                
            except Exception as e:
                print(f"Error enviando con thumbnail: {e}")
                # Fallback: enviar sin thumbnail
                bot.sendFile(update.message.chat.id, name)
        else:
            # Enviar sin thumbnail
            bot.sendFile(update.message.chat.id, name)
        
        # Eliminar el archivo TXT temporal
        os.unlink(name)
        
    except Exception as e:
        print(f"Error en sendTxt: {e}")
        # Intentar enviar de forma simple si hay error
        try:
            bot.sendFile(update.message.chat.id, name)
            if os.path.exists(name):
                os.unlink(name)
        except:
            pass

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

def get_all_cloud_evidences_fast(use_cache=True):
    """
    Obtiene todas las evidencias de todas las nubes preconfiguradas (versión optimizada)
    """
    # Verificar caché primero
    if use_cache and not cloud_cache.should_refresh():
        cached_data = cloud_cache.get_cache('all_clouds')
        if cached_data:
            return cached_data
    
    all_evidences = []
    
    for user_group, cloud_config in PRE_CONFIGURATED_USERS.items():
        # Extraer la configuración de la nube
        moodle_host = cloud_config.get('moodle_host', '')
        moodle_user = cloud_config.get('moodle_user', '')
        moodle_password = cloud_config.get('moodle_password', '')
        moodle_repo_id = cloud_config.get('moodle_repo_id', '')
        proxy = cloud_config.get('proxy', '')
        
        # Verificar caché para esta nube específica
        if use_cache and not cloud_cache.should_refresh(moodle_host):
            cached_evidence = cloud_cache.get_cache(moodle_host)
            if cached_evidence:
                all_evidences.extend(cached_evidence)
                continue
        
        try:
            # Conectar a la nube con timeout
            proxy_parsed = ProxyCloud.parse(proxy)
            client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
            
            if client.login():
                # Obtener todas las evidencias de esta nube
                evidences = client.getEvidences()
                
                # Procesar cada evidencia
                for evidence in evidences:
                    evidence_info = {
                        'cloud_name': moodle_host,
                        'cloud_user': moodle_user,
                        'evidence_name': evidence.get('name', 'Sin nombre'),
                        'files_count': len(evidence.get('files', [])),
                        'evidence_data': evidence,
                        'group_users': user_group.split(','),
                        'cloud_config': cloud_config
                    }
                    all_evidences.append(evidence_info)
                
                client.logout()
                # Actualizar caché
                if use_cache:
                    cloud_cache.update_cache(moodle_host, [ev for ev in all_evidences if ev['cloud_name'] == moodle_host])
            else:
                print(f"No se pudo conectar a {moodle_host}")
                
        except Exception as e:
            print(f"Error obteniendo evidencias de {moodle_host}: {str(e)}")
    
    # Actualizar caché completa
    if use_cache:
        cloud_cache.update_full_cache(all_evidences)
    
    return all_evidences

def delete_evidence_from_cloud(cloud_config, evidence):
    """
    Elimina una evidencia específica de una nube
    """
    try:
        moodle_host = cloud_config.get('moodle_host', '')
        moodle_user = cloud_config.get('moodle_user', '')
        moodle_password = cloud_config.get('moodle_password', '')
        moodle_repo_id = cloud_config.get('moodle_repo_id', '')
        proxy = cloud_config.get('proxy', '')
        
        proxy_parsed = ProxyCloud.parse(proxy)
        client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
        
        if client.login():
            # Buscar la evidencia exacta
            all_evidences = client.getEvidences()
            evidence_to_delete = None
            
            for ev in all_evidences:
                if ev.get('id') == evidence.get('id'):
                    evidence_to_delete = ev
                    break
            
            if evidence_to_delete:
                evidence_name = evidence_to_delete.get('name', '')
                files_count = len(evidence_to_delete.get('files', []))
                # Eliminar la evidencia
                client.deleteEvidence(evidence_to_delete)
                client.logout()
                # Invalidar caché
                cloud_cache.clear_cache()
                return True, evidence_name, files_count
            else:
                client.logout()
                return False, "", 0
        else:
            return False, "", 0
            
    except Exception as e:
        return False, f"Error: {str(e)}", 0

def delete_all_evidences_from_cloud(cloud_config):
    """
    Elimina todas las evidencias de una nube específica
    """
    try:
        moodle_host = cloud_config.get('moodle_host', '')
        moodle_user = cloud_config.get('moodle_user', '')
        moodle_password = cloud_config.get('moodle_password', '')
        moodle_repo_id = cloud_config.get('moodle_repo_id', '')
        proxy = cloud_config.get('proxy', '')
        
        proxy_parsed = ProxyCloud.parse(proxy)
        client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
        
        if client.login():
            # Obtener todas las evidencias
            all_evidences = client.getEvidences()
            deleted_count = 0
            total_files = 0
            
            # Eliminar cada evidencia
            for evidence in all_evidences:
                try:
                    files_count = len(evidence.get('files', []))
                    client.deleteEvidence(evidence)
                    deleted_count += 1
                    total_files += files_count
                except:
                    pass
            
            client.logout()
            # Invalidar caché
            cloud_cache.clear_cache()
            return True, deleted_count, total_files
        else:
            return False, 0, 0
            
    except Exception as e:
        return False, 0, 0

class AdminEvidenceManager:
    """Gestor de evidencias para administrador"""
    
    def __init__(self):
        self.current_list = []
        self.clouds_dict = {}
        self.last_update = None
    
    def refresh_data(self, force=False):
        """Actualiza los datos de evidencias (con caché)"""
        if not force and not cloud_cache.should_refresh():
            return len(self.current_list)
        
        try:
            all_evidences = get_all_cloud_evidences_fast(use_cache=True)
            self.clouds_dict = {}
            
            for evidence in all_evidences:
                cloud_name = evidence['cloud_name']
                if cloud_name not in self.clouds_dict:
                    self.clouds_dict[cloud_name] = []
                self.clouds_dict[cloud_name].append(evidence)
            
            # Crear lista plana para acceso rápido
            self.current_list = []
            cloud_index = 0
            for cloud_name, evidences in self.clouds_dict.items():
                for idx, evidence in enumerate(evidences):
                    self.current_list.append({
                        'cloud_idx': cloud_index,
                        'evid_idx': idx,
                        'cloud_name': cloud_name,
                        'evidence': evidence
                    })
            
            self.last_update = datetime.datetime.now()
            return len(self.current_list)
        except Exception as e:
            print(f"Error refrescando datos: {e}")
            return len(self.current_list)
    
    def get_evidence(self, cloud_idx, evid_idx):
        """Obtiene una evidencia específica"""
        try:
            if cloud_idx is None or evid_idx is None:
                return None
                
            if cloud_idx < len(self.clouds_dict):
                cloud_name = list(self.clouds_dict.keys())[cloud_idx]
                if evid_idx < len(self.clouds_dict[cloud_name]):
                    return self.clouds_dict[cloud_name][evid_idx]
        except Exception as e:
            print(f"Error obteniendo evidencia: {e}")
        return None
    
    def get_txt_for_evidence(self, cloud_idx, evid_idx):
        """Obtiene el TXT de una evidencia"""
        evidence = self.get_evidence(cloud_idx, evid_idx)
        if evidence:
            try:
                cloud_config = evidence['cloud_config']
                evidence_data = evidence['evidence_data']
                
                moodle_host = cloud_config.get('moodle_host', '')
                moodle_user = cloud_config.get('moodle_user', '')
                moodle_password = cloud_config.get('moodle_password', '')
                moodle_repo_id = cloud_config.get('moodle_repo_id', '')
                proxy = cloud_config.get('proxy', '')
                
                proxy_parsed = ProxyCloud.parse(proxy)
                client = MoodleClient(moodle_user, moodle_password, moodle_host, moodle_repo_id, proxy=proxy_parsed)
                
                if client.login():
                    # Buscar la evidencia actualizada
                    all_evidences = client.getEvidences()
                    current_evidence = None
                    
                    for ev in all_evidences:
                        if ev.get('id') == evidence_data.get('id'):
                            current_evidence = ev
                            break
                    
                    if current_evidence:
                        files = current_evidence.get('files', [])
                        
                        # Preparar URLs
                        for i in range(len(files)):
                            url = files[i]['directurl']
                            if '?forcedownload=1' in url:
                                url = url.replace('?forcedownload=1', '')
                            elif '&forcedownload=1' in url:
                                url = url.replace('&forcedownload=1', '')
                            if '&token=' in url and '?' not in url:
                                url = url.replace('&token=', '?token=', 1)
                            files[i]['directurl'] = url
                        
                        client.logout()
                        return files
                    client.logout()
            except Exception as e:
                print(f"Error obteniendo TXT: {e}")
        return None
    
    def clear_cache(self):
        """Limpia la caché del manager"""
        cloud_cache.clear_cache()
        self.current_list = []
        self.clouds_dict = {}
        self.last_update = None

admin_evidence_manager = AdminEvidenceManager()

# ==============================
# FUNCIONES SIMPLES PARA EXTRACCIÓN DE PARÁMETROS
# ==============================

def extract_one_param_simple(msgText, prefix):
    """
    Extrae un parámetro de forma simple usando split
    """
    try:
        if prefix in msgText:
            parts = msgText.split('_')
            # El índice depende del prefijo
            if prefix == '/adm_cloud_':
                return int(parts[2]) if len(parts) > 2 else None
            elif prefix == '/adm_wipe_':
                return int(parts[2]) if len(parts) > 2 else None
    except (ValueError, IndexError):
        return None
    return None

def extract_two_params_simple(msgText, prefix):
    """
    Extrae dos parámetros de forma simple usando split
    """
    try:
        if prefix in msgText:
            parts = msgText.split('_')
            # Los comandos tienen formato: /adm_xxx_X_Y
            if len(parts) > 3:
                param1 = int(parts[2])  # Primer número
                param2 = int(parts[3])  # Segundo número
                return [param1, param2]
    except (ValueError, IndexError):
        return None
    return None

def show_updated_cloud(bot, message, cloud_idx):
    """Muestra la lista actualizada de una nube después de eliminar"""
    try:
        # Obtener datos actualizados
        admin_evidence_manager.refresh_data(force=True)  # Forzar refresco después de eliminar
        cloud_names = list(admin_evidence_manager.clouds_dict.keys())
        
        # Verificar que el índice sea válido
        if cloud_idx < 0 or cloud_idx >= len(cloud_names):
            # Si el índice es inválido, mostrar todas las nubes
            show_updated_all_clouds(bot, message)
            return
        
        cloud_name = cloud_names[cloud_idx]
        evidences = admin_evidence_manager.clouds_dict.get(cloud_name, [])
        
        # VERIFICACIÓN CRÍTICA: Si no hay evidencias, mostrar todas las nubes
        if not evidences:
            short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
            empty_msg = f"""
📭 NUBE VACÍA
━━━━━━━━━━━━━━━━━━━

✅ ELIMINACIÓN COMPLETA
☁️ {short_name}

🎉 ¡Has eliminado todas las evidencias de esta nube!

🔄 Regresando a todas las nubes...
━━━━━━━━━━━━━━━━━━━
            """
            bot.editMessageText(message, empty_msg)
            time.sleep(1.5)  # Breve pausa para que el usuario vea el mensaje
            show_updated_all_clouds(bot, message)  # MOSTRAR TODAS LAS NUBES
            return
        
        short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
        
        # Si hay evidencias, mostrar la lista normal
        list_msg = f"""
📋 NUBE ACTUALIZADA
☁️ {short_name}
━━━━━━━━━━━━━━━━━━━

"""
        for idx, evidence in enumerate(evidences):
            ev_name = evidence['evidence_name']
            
            # Limpiar nombre de evidencia
            clean_name = ev_name
            user_tags = []
            
            for user in evidence['group_users']:
                marker = f"{USER_EVIDENCE_MARKER}{user}"
                if marker in ev_name:
                    clean_name = ev_name.replace(marker, "").strip()
                    user_tags.append(f"@{user}")
            
            if user_tags:
                user_str = f" ({', '.join(user_tags[:2])})"
                if len(user_tags) > 2:
                    user_str = f" ({', '.join(user_tags[:2])}...)"
            else:
                user_str = ""
            
            list_msg += f"{idx}. {clean_name[:35]}"
            if len(clean_name) > 35:
                list_msg += "..."
            list_msg += f"{user_str}\n"
            list_msg += f"   📁 {evidence['files_count']} archivos\n"
            list_msg += f"   👁️ /adm_show_{cloud_idx}_{idx}\n"
            list_msg += f"   📄 /adm_fetch_{cloud_idx}_{idx}\n"
            list_msg += f"   🗑️ /adm_delete_{cloud_idx}_{idx}\n\n"
        
        total_evidences = len(evidences)
        total_files = sum(e['files_count'] for e in evidences)
        
        list_msg += f"""
━━━━━━━━━━━━━━━━━━━
🔧 ACCIONES MASIVAS:
/adm_wipe_{cloud_idx} - Eliminar TODO de esta nube

📊 RESUMEN:
• Evidencias: {total_evidences}
• Archivos: {total_files}
━━━━━━━━━━━━━━━━━━━
        """
        
        bot.editMessageText(message, list_msg)
        
    except Exception as e:
        # Manejo de error más amigable
        error_msg = f"""
❌ ERROR AL ACTUALIZAR
━━━━━━━━━━━━━━━━━━━

⚠️ No se pudo mostrar la nube actualizada.

🔧 Solución:
Usa /adm_allclouds para ver todas las nubes disponibles

━━━━━━━━━━━━━━━━━━━
        """
        bot.editMessageText(message, error_msg)

def show_updated_all_clouds(bot, message):
    """Muestra todas las nubes actualizadas después de una eliminación masiva"""
    try:
        # Refrescar datos primero (con caché)
        admin_evidence_manager.refresh_data()
        
        total_evidences = len(admin_evidence_manager.current_list)
        total_clouds = len(admin_evidence_manager.clouds_dict)
        total_files = 0
        
        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
            for ev in evidences:
                total_files += ev['files_count']
        
        if total_evidences == 0:
            # Si no hay evidencias en ninguna nube, mostrar mensaje simple
            empty_msg = f"""
👑 TODAS LAS NUBES ACTUALIZADAS
━━━━━━━━━━━━━━━━━━━

📊 RESUMEN GENERAL:
• Nubes: {total_clouds}
• Evidencias totales: 0
• Archivos totales: 0

━━━━━━━━━━━━━━━━━━━
✅ Todas las nubes están vacías
📭 No hay evidencias para eliminar
━━━━━━━━━━━━━━━━━━━
            """
            bot.editMessageText(message, empty_msg)
            return
        
        # Si hay evidencias, mostrar la lista completa
        menu_msg = f"""
👑 TODAS LAS NUBES ACTUALIZADAS
━━━━━━━━━━━━━━━━━━━

📊 RESUMEN GENERAL:
• Nubes: {total_clouds}
• Evidencias totales: {total_evidences}
• Archivos totales: {total_files}

📋 NUBES DISPONIBLES:"""
        
        cloud_index = 0
        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
            cloud_files = sum(ev['files_count'] for ev in evidences)
            short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
            
            menu_msg += f"\n\n{cloud_index}. {short_name}"
            menu_msg += f"\n   📁 {len(evidences)} evidencias, {cloud_files} archivos"
            menu_msg += f"\n   🔍 /adm_cloud_{cloud_index}"
            
            if len(evidences) > 0:
                menu_msg += f"\n   🗑️ /adm_wipe_{cloud_index}"
            
            cloud_index += 1
        
        if total_evidences > 0:
            menu_msg += f"""

━━━━━━━━━━━━━━━━━━━
🔧 OPCIONES MASIVAS:
/adm_nuke - ⚠️ Eliminar TODO (peligro)
━━━━━━━━━━━━━━━━━━━
        """
        
        bot.editMessageText(message, menu_msg)
        
    except Exception as e:
        bot.editMessageText(message, f'❌ Error al mostrar nubes actualizadas: {str(e)}')

def show_loading_progress(bot, message, step, total_steps=3):
    """Muestra una barra de progreso para operaciones largas"""
    progress_chars = ['○', '◔', '◑', '◕', '●']
    progress = int((step / total_steps) * 4)
    bar = progress_chars[progress] if progress < len(progress_chars) else progress_chars[-1]
    
    loading_msgs = [
        "🔄 Conectando con las nubes...",
        "📊 Procesando datos...",
        "✅ Actualizando información..."
    ]
    
    msg = loading_msgs[step-1] if step <= len(loading_msgs) else f"Procesando... ({step}/{total_steps})"
    bot.editMessageText(message, f"{msg} {bar}")

# ==============================
# FUNCIÓN PRINCIPAL ONMESSAGE CORREGIDA
# ==============================

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

        # ============================================
        # COMANDO /start MEJORADO
        # ============================================
        if '/start' in msgText:
            if username == ADMIN_USERNAME:
                start_msg = f"""
👑 USUARIO ADMINISTRADOR

👤 Usuario: @{username}
🔧 Rol: Administrador

⚠️ NOTA IMPORTANTE:
• Tienes acceso de administrador a TODAS las nubes
• Puedes gestionar evidencias de todos los usuarios

🎯 COMANDOS PRINCIPALES:
/admin - Panel principal de administración

📈 COMANDOS DE ESTADÍSTICAS:
/adm_logs - Ver logs del sistema
/adm_users - Ver usuarios y estadísticas
/adm_uploads - Ver últimas subidas
/adm_deletes - Ver últimas eliminaciones
/adm_cleardata - Limpiar estadísticas

☁️ COMANDOS DE GESTIÓN DE NUBES:
/adm_allclouds - Ver todas las nubes
/adm_cloud_X - Ver nube específica
/adm_show_X_Y - Ver detalles de evidencia
/adm_fetch_X_Y - Descargar TXT de evidencia
/adm_delete_X_Y - Eliminar una evidencia
/adm_wipe_X - Limpiar toda una nube
/adm_nuke - Eliminar TODO (peligro extremo)

🔧 TUS COMANDOS PERSONALES:
/files - Ver tus evidencias personales
/txt_X - Ver TXT de tu evidencia
/del_X - Eliminar tu evidencia
/delall - Eliminar todas tus evidencias
/mystats - Ver tus estadísticas

🔗 FileToLink: @fileeliellinkBot
                """
            else:
                start_msg = f"""
👤 USUARIO REGULAR

👤 Usuario: @{username}
☁️ Nube: Moodle
📁 Evidence: Activado
🔗 Host: {user_info["moodle_host"]}

🔧 TUS COMANDOS:
/start - Ver esta información
/files - Ver tus evidencias
/txt_X - Ver TXT de evidencia X
/del_X - Eliminar evidencia X
/delall - Eliminar todas tus evidencias
/mystats - Ver tus estadísticas

🔗 FileToLink: @fileeliellinkBot
                """
            
            bot.editMessageText(message, start_msg)
            return
        
        # ============================================
        # COMANDOS DE ADMINISTRADOR (SOLO SI ES ADMIN)
        # ============================================
        if username == ADMIN_USERNAME:
            # COMANDO /admin
            if msgText == '/admin':
                stats = memory_stats.get_all_stats()
                total_size_formatted = format_file_size(stats['total_size_uploaded'])
                current_date = format_cuba_date()
                
                if memory_stats.has_any_data():
                    admin_msg = f"""
👑 PANEL DE ADMINISTRADOR
📅 {current_date}
━━━━━━━━━━━━━━━━━━━
📊 ESTADÍSTICAS GLOBALES:
• Subidas totales: {stats['total_uploads']}
• Eliminaciones totales: {stats['total_deletes']}
• Espacio total subido: {total_size_formatted}
• Nubes configuradas: {len(PRE_CONFIGURATED_USERS)}

📈 COMANDOS DE ESTADÍSTICAS:
/adm_logs - Ver últimos logs
/adm_users - Ver estadísticas por usuario
/adm_uploads - Ver últimas subidas
/adm_deletes - Ver últimas eliminaciones
/adm_cleardata - Limpiar todos los datos

☁️ COMANDOS DE GESTIÓN DE NUBES:
/adm_allclouds - Ver todas las nubes
/adm_cloud_X - Ver nube específica
/adm_show_X_Y - Ver detalles de evidencia
/adm_fetch_X_Y - Descargar TXT de evidencia
/adm_delete_X_Y - Eliminar una evidencia
/adm_wipe_X - Limpiar toda una nube
/adm_nuke - Eliminar TODO (peligro)

🔧 OTROS COMANDOS:
/start - Ver información del usuario
━━━━━━━━━━━━━━━━━━━
🕐 Hora Cuba: {format_cuba_datetime()}
                    """
                else:
                    admin_msg = f"""
👑 PANEL DE ADMINISTRADOR
📅 {current_date}
━━━━━━━━━━━━━━━━━━━
⚠️ NO HAY DATOS REGISTRADOS
Aún no se ha realizado ninguna acción en el bot.

📊 Nubes configuradas: {len(PRE_CONFIGURATED_USERS)}

📈 COMANDOS DE ESTADÍSTICAS:
/adm_logs - Ver últimos logs
/adm_users - Ver estadísticas por usuario
/adm_uploads - Ver últimas subidas
/adm_deletes - Ver últimas eliminaciones

☁️ COMANDOS DE GESTIÓN DE NUBES:
/adm_allclouds - Ver todas las nubes
/adm_cloud_X - Ver nube específica
/adm_show_X_Y - Ver detalles de evidencia
/adm_fetch_X_Y - Descargar TXT de evidencia

🔧 OTROS COMANDOS:
/start - Ver información del usuario
━━━━━━━━━━━━━━━━━━━
🕐 Hora Cuba: {format_cuba_datetime()}
                    """
                
                bot.editMessageText(message, admin_msg)
                return
            
            # COMANDOS CON /adm_
            elif '/adm_' in msgText:
                # /adm_allclouds
                if '/adm_allclouds' in msgText:
                    try:
                        show_loading_progress(bot, message, 1, 3)
                        total_evidences = admin_evidence_manager.refresh_data()
                        show_loading_progress(bot, message, 2, 3)
                        
                        if total_evidences == 0:
                            # Mensaje cuando no hay evidencias
                            empty_msg = f"""
👑 TODAS LAS NUBES
━━━━━━━━━━━━━━━━━━━

📊 RESUMEN GENERAL:
• Nubes configuradas: {len(PRE_CONFIGURATED_USERS)}
• Evidencias totales: 0
• Archivos totales: 0

━━━━━━━━━━━━━━━━━━━
✅ Todas las nubes están vacías
📭 No hay evidencias para eliminar
━━━━━━━━━━━━━━━━━━━
                            """
                            bot.editMessageText(message, empty_msg)
                            return
                        
                        total_clouds = len(admin_evidence_manager.clouds_dict)
                        total_files = 0
                        
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            for ev in evidences:
                                total_files += ev['files_count']
                        
                        menu_msg = f"""
👑 GESTIÓN DE TODAS LAS NUBES
━━━━━━━━━━━━━━━━━━━

📊 RESUMEN GENERAL:
• Nubes: {total_clouds}
• Evidencias totales: {total_evidences}
• Archivos totales: {total_files}

📋 NUBES DISPONIBLES:"""
                        
                        cloud_index = 0
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            cloud_files = sum(ev['files_count'] for ev in evidences)
                            short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                            
                            menu_msg += f"\n\n{cloud_index}. {short_name}"
                            menu_msg += f"\n   📁 {len(evidences)} evidencias, {cloud_files} archivos"
                            menu_msg += f"\n   🔍 /adm_cloud_{cloud_index}"
                            
                            if len(evidences) > 0:
                                menu_msg += f"\n   🗑️ /adm_wipe_{cloud_index}"
                            
                            cloud_index += 1
                        
                        show_loading_progress(bot, message, 3, 3)
                        
                        if total_evidences > 0:
                            menu_msg += f"""

━━━━━━━━━━━━━━━━━━━
🔧 OPCIONES MASIVAS:
/adm_nuke - ⚠️ Eliminar TODO (peligro)
━━━━━━━━━━━━━━━━━━━
ℹ️ Usa /adm_cloud_X para ver evidencias de una nube
                            """
                        else:
                            menu_msg += f"""

━━━━━━━━━━━━━━━━━━━
✅ Todas las nubes están vacías
📭 No hay evidencias para eliminar
━━━━━━━━━━━━━━━━━━━
                            """
                        
                        bot.editMessageText(message, menu_msg)
                        
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                # /adm_cloud_X
                elif '/adm_cloud_' in msgText:
                    try:
                        cloud_idx = extract_one_param_simple(msgText, '/adm_cloud_')
                        if cloud_idx is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_cloud_0')
                            return
                        
                        # Refrescar datos primero (con caché)
                        admin_evidence_manager.refresh_data()
                        
                        if cloud_idx < 0 or cloud_idx >= len(admin_evidence_manager.clouds_dict):
                            bot.editMessageText(message, f'❌ Índice inválido. Máximo: {len(admin_evidence_manager.clouds_dict)-1}')
                            return
                        
                        cloud_name = list(admin_evidence_manager.clouds_dict.keys())[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict[cloud_name]
                        
                        short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                        
                        if not evidences:
                            empty_msg = f"""
📭 NUBE VACÍA
━━━━━━━━━━━━━━━━━━━

☁️ {short_name}
📊 No hay evidencias en esta nube.

🔍 Usa /adm_allclouds para ver otras nubes
━━━━━━━━━━━━━━━━━━━
                            """
                            bot.editMessageText(message, empty_msg)
                            return
                        
                        list_msg = f"""
📋 EVIDENCIAS DE LA NUBE
☁️ {short_name}
━━━━━━━━━━━━━━━━━━━

"""
                        for idx, evidence in enumerate(evidences):
                            ev_name = evidence['evidence_name']
                            
                            clean_name = ev_name
                            user_tags = []
                            
                            for user in evidence['group_users']:
                                marker = f"{USER_EVIDENCE_MARKER}{user}"
                                if marker in ev_name:
                                    clean_name = ev_name.replace(marker, "").strip()
                                    user_tags.append(f"@{user}")
                            
                            if user_tags:
                                user_str = f" ({', '.join(user_tags[:2])})"
                                if len(user_tags) > 2:
                                    user_str = f" ({', '.join(user_tags[:2])}...)"
                            else:
                                user_str = ""
                            
                            list_msg += f"{idx}. {clean_name[:35]}"
                            if len(clean_name) > 35:
                                list_msg += "..."
                            list_msg += f"{user_str}\n"
                            list_msg += f"   📁 {evidence['files_count']} archivos\n"
                            list_msg += f"   👁️ /adm_show_{cloud_idx}_{idx}\n"
                            list_msg += f"   📄 /adm_fetch_{cloud_idx}_{idx}\n"
                            list_msg += f"   🗑️ /adm_delete_{cloud_idx}_{idx}\n\n"
                        
                        total_evidences = len(evidences)
                        total_files = sum(e['files_count'] for e in evidences)
                        
                        list_msg += f"""
━━━━━━━━━━━━━━━━━━━
🔧 ACCIONES MASIVAS:
/adm_wipe_{cloud_idx} - Eliminar TODO de esta nube

📊 RESUMEN:
• Evidencias: {total_evidences}
• Archivos: {total_files}
━━━━━━━━━━━━━━━━━━━
                        """
                        
                        bot.editMessageText(message, list_msg)
                        
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                # /adm_show_X_Y
                elif '/adm_show_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_show_')
                        if params is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_show_0_1')
                            return
                        
                        cloud_idx, evid_idx = params
                        
                        evidence = admin_evidence_manager.get_evidence(cloud_idx, evid_idx)
                        if evidence:
                            ev_name = evidence['evidence_name']
                            cloud_name = evidence['cloud_name']
                            short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                            
                            clean_name = ev_name
                            for user in evidence['group_users']:
                                marker = f"{USER_EVIDENCE_MARKER}{user}"
                                if marker in ev_name:
                                    clean_name = ev_name.replace(marker, "").strip()
                                    break
                            
                            show_msg = f"""
👁️ DETALLES DE EVIDENCIA
━━━━━━━━━━━━━━━━━━━

📝 Nombre: {clean_name}
📁 Archivos: {evidence['files_count']}
☁️ Nube: {short_name}

🔧 ACCIONES DISPONIBLES:
📄 /adm_fetch_{cloud_idx}_{evid_idx} - Descargar TXT
🗑️ /adm_delete_{cloud_idx}_{evid_idx} - Eliminar

📊 ESTADÍSTICAS:
• Nube índice: {cloud_idx}
• Evidencia índice: {evid_idx}
━━━━━━━━━━━━━━━━━━━
                            """
                            
                            bot.editMessageText(message, show_msg)
                        else:
                            bot.editMessageText(message, '❌ No se encontró la evidencia')
                            
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                # /adm_fetch_X_Y
                elif '/adm_fetch_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_fetch_')
                        if params is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_fetch_0_1')
                            return
                        
                        cloud_idx, evid_idx = params
                        
                        bot.editMessageText(message, '📄 Obteniendo archivo TXT...')
                        
                        files = admin_evidence_manager.get_txt_for_evidence(cloud_idx, evid_idx)
                        
                        if files:
                            evidence = admin_evidence_manager.get_evidence(cloud_idx, evid_idx)
                            if evidence:
                                ev_name = evidence['evidence_name']
                                clean_name = ev_name
                                
                                for user in evidence['group_users']:
                                    marker = f"{USER_EVIDENCE_MARKER}{user}"
                                    if marker in ev_name:
                                        clean_name = ev_name.replace(marker, "").strip()
                                        break
                                
                                safe_name = ''.join(c for c in clean_name if c.isalnum() or c in (' ', '-', '_')).strip()
                                if not safe_name:
                                    safe_name = f"evidencia_{cloud_idx}_{evid_idx}"
                                
                                txtname = f"{safe_name}.txt"
                                
                                # Enviar el TXT con thumbnail
                                sendTxt(txtname, files, update, bot)
                                
                                bot.editMessageText(message, f'✅ TXT enviado: {clean_name[:50]}')
                            else:
                                bot.editMessageText(message, '❌ No se encontró la evidencia')
                        else:
                            bot.editMessageText(message, '❌ No hay archivos en esta evidencia')
                            
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                # /adm_delete_X_Y - ¡CORRECCIÓN PRINCIPAL!
                elif '/adm_delete_' in msgText:
                    try:
                        params = extract_two_params_simple(msgText, '/adm_delete_')
                        if params is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_delete_0_1')
                            return
                        
                        cloud_idx, evid_idx = params
                        
                        bot.editMessageText(message, '🔍 Verificando datos...')
                        
                        # Obtener datos actuales
                        admin_evidence_manager.refresh_data()
                        cloud_names = list(admin_evidence_manager.clouds_dict.keys())
                        
                        if cloud_idx < 0 or cloud_idx >= len(cloud_names):
                            bot.editMessageText(message, f'❌ Índice de nube inválido')
                            show_updated_all_clouds(bot, message)
                            return
                        
                        cloud_name = cloud_names[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict.get(cloud_name, [])
                        
                        if not evidences:
                            bot.editMessageText(message, f'📭 La nube {cloud_idx} ya está vacía')
                            show_updated_all_clouds(bot, message)
                            return
                        
                        if evid_idx < 0 or evid_idx >= len(evidences):
                            bot.editMessageText(message, f'❌ Índice de evidencia inválido')
                            return
                        
                        evidence = evidences[evid_idx]
                        
                        # Limpiar nombre para mostrar
                        ev_name = evidence['evidence_name']
                        clean_name = ev_name
                        for user in evidence['group_users']:
                            marker = f"{USER_EVIDENCE_MARKER}{user}"
                            if marker in ev_name:
                                clean_name = ev_name.replace(marker, "").strip()
                                break
                        
                        short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                        
                        bot.editMessageText(message, f'🗑️ Eliminando evidencia: {clean_name[:50]}...')
                        
                        # Eliminar
                        success, ev_name, files_count = delete_evidence_from_cloud(
                            evidence['cloud_config'], 
                            evidence['evidence_data']
                        )
                        
                        if success:
                            # Refrescar datos
                            admin_evidence_manager.refresh_data(force=True)
                            
                            # Obtener datos actualizados
                            cloud_names = list(admin_evidence_manager.clouds_dict.keys())
                            
                            if cloud_idx < len(cloud_names):
                                current_evidences = admin_evidence_manager.clouds_dict.get(cloud_names[cloud_idx], [])
                                
                                if current_evidences:
                                    # Si aún hay evidencias, mostrar esta nube actualizada
                                    result_msg = f"""
✅ ELIMINACIÓN EXITOSA
━━━━━━━━━━━━━━━━━━━

🗑️ Evidencia: {clean_name[:50]}
{'...' if len(clean_name) > 50 else ''}
📁 Archivos eliminados: {files_count}
☁️ Nube: {short_name}

🔄 Mostrando nube actualizada...
━━━━━━━━━━━━━━━━━━━
                                    """
                                    bot.editMessageText(message, result_msg)
                                    time.sleep(1)
                                    show_updated_cloud(bot, message, cloud_idx)
                                else:
                                    # Si NO hay evidencias, mostrar todas las nubes
                                    result_msg = f"""
✅ ELIMINACIÓN COMPLETA
━━━━━━━━━━━━━━━━━━━

🗑️ Última evidencia eliminada de esta nube
📁 Archivos borrados: {files_count}

🔄 Mostrando todas las nubes...
━━━━━━━━━━━━━━━━━━━
                                    """
                                    bot.editMessageText(message, result_msg)
                                    time.sleep(1)
                                    show_updated_all_clouds(bot, message)  # MOSTRAR TODAS LAS NUBES
                            else:
                                # Si por alguna razón la nube ya no está en la lista
                                show_updated_all_clouds(bot, message)
                        else:
                            bot.editMessageText(message, f'❌ Error al eliminar: {clean_name}')
                            
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                # /adm_wipe_X
                elif '/adm_wipe_' in msgText:
                    try:
                        cloud_idx = extract_one_param_simple(msgText, '/adm_wipe_')
                        if cloud_idx is None:
                            bot.editMessageText(message, '❌ Formato incorrecto. Use: /adm_wipe_0')
                            return
                        
                        if cloud_idx < 0 or cloud_idx >= len(admin_evidence_manager.clouds_dict):
                            bot.editMessageText(message, f'❌ Índice inválido. Máximo: {len(admin_evidence_manager.clouds_dict)-1}')
                            return
                        
                        cloud_name = list(admin_evidence_manager.clouds_dict.keys())[cloud_idx]
                        evidences = admin_evidence_manager.clouds_dict[cloud_name]
                        
                        if not evidences:
                            bot.editMessageText(message, f'📭 La nube {cloud_idx} ya está vacía')
                            return
                        
                        total_evidences = len(evidences)
                        total_files = sum(e['files_count'] for e in evidences)
                        short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                        
                        bot.editMessageText(message, f'💣 Limpiando nube {short_name}...')
                        
                        cloud_config = None
                        for user_group, config in PRE_CONFIGURATED_USERS.items():
                            if config.get('moodle_host') == cloud_name:
                                cloud_config = config
                                break
                        
                        if cloud_config:
                            success, deleted_count, total_files = delete_all_evidences_from_cloud(cloud_config)
                            
                            if success:
                                admin_evidence_manager.refresh_data(force=True)
                                
                                result_msg = f"""
💥 LIMPIEZA COMPLETA EXITOSA
━━━━━━━━━━━━━━━━━━━

✅ Nube: {short_name}
✅ Evidencias eliminadas: {deleted_count}
✅ Archivos borrados: {total_files}

🔄 Mostrando todas las nubes...
━━━━━━━━━━━━━━━━━━━
                                """
                                
                                bot.editMessageText(message, result_msg)
                                time.sleep(1)
                                
                                show_updated_all_clouds(bot, message)
                            else:
                                bot.editMessageText(message, f'❌ Error al limpiar la nube {short_name}')
                        else:
                            bot.editMessageText(message, '❌ No se encontró configuración para esta nube')
                            
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                # /adm_nuke
                elif '/adm_nuke' in msgText:
                    try:
                        total_clouds = len(admin_evidence_manager.clouds_dict)
                        total_evidences = len(admin_evidence_manager.current_list)
                        total_files = 0
                        
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            for ev in evidences:
                                total_files += ev['files_count']
                        
                        if total_evidences == 0:
                            bot.editMessageText(message, '📭 No hay evidencias para eliminar')
                            return
                        
                        bot.editMessageText(message, '💣💣💣 ELIMINANDO TODO DE TODAS LAS NUBES...')
                        
                        results = []
                        deleted_total = 0
                        files_total = 0
                        
                        for cloud_name, evidences in admin_evidence_manager.clouds_dict.items():
                            cloud_config = None
                            for user_group, config in PRE_CONFIGURATED_USERS.items():
                                if config.get('moodle_host') == cloud_name:
                                    cloud_config = config
                                    break
                            
                            if cloud_config:
                                success, deleted_count, total_files = delete_all_evidences_from_cloud(cloud_config)
                                
                                if success:
                                    deleted_total += deleted_count
                                    files_total += total_files
                                    
                                    short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                                    results.append(f"✅ {short_name}: {deleted_count} evidencias, {total_files} archivos")
                                else:
                                    short_name = cloud_name.replace('https://', '').replace('http://', '').split('/')[0]
                                    results.append(f"❌ {short_name}: Error al eliminar")
                        
                        admin_evidence_manager.refresh_data(force=True)
                        
                        final_msg = f"""
💥💥💥 ELIMINACIÓN MASIVA COMPLETADA 💥💥💥
━━━━━━━━━━━━━━━━━━━

📊 RESULTADOS FINALES:
• Nubes procesadas: {len(results)}
• Evidencias eliminadas: {deleted_total}
• Archivos borrados: {files_total}

━━━━━━━━━━━━━━━━━━━
📋 DETALLE POR NUBE:
"""
                        
                        for result in results:
                            final_msg += f"\n{result}"
                        
                        final_msg += f"""

━━━━━━━━━━━━━━━━━━━
✅ Todas las nubes han sido limpiadas.
📭 No quedan evidencias en ninguna nube.
━━━━━━━━━━━━━━━━━━━
                        """
                        
                        bot.editMessageText(message, final_msg)
                        
                    except Exception as e:
                        bot.editMessageText(message, f'❌ Error: {str(e)}')
                    return
                
                # COMANDOS DE ESTADÍSTICAS DE ADMIN
                elif '/adm_logs' in msgText:
                    try:
                        if not memory_stats.has_any_data():
                            bot.editMessageText(message, "⚠️ No hay datos registrados\nAún no se ha realizado ninguna acción en el bot.")
                            return
                        
                        limit = 20
                        if '_' in msgText:
                            try:
                                limit = int(msgText.split('_')[2])
                            except: pass
                        
                        uploads = memory_stats.get_recent_uploads(limit)
                        deletes = memory_stats.get_recent_deletes(limit)
                        
                        logs_msg = f"📋 ÚLTIMOS LOGS\n"
                        logs_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                        
                        if uploads:
                            logs_msg += "⬆️ ÚLTIMAS SUBIDAS:\n"
                            for log in uploads:
                                logs_msg += f"• {log['timestamp']} - @{log['username']}: {log['filename']} ({log['file_size_formatted']})\n"
                            logs_msg += "\n"
                        
                        if deletes:
                            logs_msg += "🗑️ ÚLTIMAS ELIMINACIONES:\n"
                            for log in deletes:
                                if log['type'] == 'delete_all':
                                    logs_msg += f"• {log['timestamp']} - @{log['username']}: ELIMINÓ TODO ({log.get('deleted_evidences', 1)} evidencia(s), {log.get('deleted_files', '?')} archivos)\n"
                                else:
                                    logs_msg += f"• {log['timestamp']} - @{log['username']}: {log['filename']} (de: {log['evidence_name']})\n"
                        
                        if len(logs_msg) > 4000:
                            logs_msg = logs_msg[:4000] + "\n\n⚠️ Logs truncados (demasiados)"
                        
                        bot.editMessageText(message, logs_msg)
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al obtener logs: {str(e)}")
                    return
                
                elif '/adm_users' in msgText:
                    try:
                        users = memory_stats.get_all_users()
                        if not users:
                            bot.editMessageText(message, "⚠️ No hay usuarios registrados\nAún no se ha completado ninguna acción exitosa.")
                            return
                        
                        users_msg = f"👥 ESTADÍSTICAS POR USUARIO\n"
                        users_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                        
                        for user, data in sorted(users.items(), key=lambda x: x[1]['uploads'], reverse=True):
                            total_size_formatted = format_file_size(data['total_size'])
                            users_msg += f"👤 @{user}\n"
                            users_msg += f"   📤 Subidas: {data['uploads']}\n"
                            users_msg += f"   🗑️ Eliminaciones: {data['deletes']}\n"
                            users_msg += f"   💾 Espacio usado: {total_size_formatted}\n"
                            users_msg += f"   📅 Última actividad: {data['last_activity']}\n\n"
                        
                        if len(users_msg) > 4000:
                            users_msg = users_msg[:4000] + "\n\n⚠️ Lista truncada (demasiados usuarios)"
                        
                        bot.editMessageText(message, users_msg)
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al obtener usuarios: {str(e)}")
                    return
                
                elif '/adm_uploads' in msgText:
                    try:
                        uploads = memory_stats.get_recent_uploads(15)
                        if not uploads:
                            bot.editMessageText(message, "⚠️ No hay subidas registradas\nAún no se ha completado ninguna subida exitosa.")
                            return
                        
                        uploads_msg = f"📤 ÚLTIMAS SUBIDAS\n"
                        uploads_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                        
                        for i, log in enumerate(uploads, 1):
                            uploads_msg += f"{i}. {log['filename']}\n"
                            uploads_msg += f"   👤 @{log['username']}\n"
                            uploads_msg += f"   📅 {log['timestamp']}\n"
                            uploads_msg += f"   📏 {log['file_size_formatted']}\n"
                            uploads_msg += f"   🔗 {log['moodle_host']}\n\n"
                        
                        bot.editMessageText(message, uploads_msg)
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al obtener subidas: {str(e)}")
                    return
                
                elif '/adm_deletes' in msgText:
                    try:
                        deletes = memory_stats.get_recent_deletes(15)
                        if not deletes:
                            bot.editMessageText(message, "⚠️ No hay eliminaciones registradas\nAún no se ha completado ninguna eliminación exitosa.")
                            return
                        
                        deletes_msg = f"🗑️ ÚLTIMAS ELIMINACIONES\n"
                        deletes_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                        
                        for i, log in enumerate(deletes, 1):
                            if log['type'] == 'delete_all':
                                deletes_msg += f"{i}. ELIMINACIÓN MASIVA\n"
                                deletes_msg += f"   👤 @{log['username']}\n"
                                deletes_msg += f"   📅 {log['timestamp']}\n"
                                deletes_msg += f"   ⚠️ ELIMINÓ {log.get('deleted_evidences', 1)} EVIDENCIA(S)\n"
                                deletes_msg += f"   🗑️ Archivos borrados: {log.get('deleted_files', '?')}\n"
                            else:
                                deletes_msg += f"{i}. {log['filename']}\n"
                                deletes_msg += f"   👤 @{log['username']}\n"
                                deletes_msg += f"   📅 {log['timestamp']}\n"
                                deletes_msg += f"   📁 Evidencia: {log['evidence_name']}\n"
                            
                            deletes_msg += f"   🔗 {log['moodle_host']}\n\n"
                        
                        bot.editMessageText(message, deletes_msg)
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al obtener eliminaciones: {str(e)}")
                    return
                
                elif '/adm_cleardata' in msgText:
                    try:
                        if not memory_stats.has_any_data():
                            bot.editMessageText(message, "⚠️ No hay datos para limpiar\nLa memoria está vacía.")
                            return
                        
                        result = memory_stats.clear_all_data()
                        bot.editMessageText(message, f"✅ {result}")
                    except Exception as e:
                        bot.editMessageText(message, f"❌ Error al limpiar datos: {str(e)}")
                    return
        
        # ============================================
        # COMANDOS REGULARES DE USUARIO (PARA TODOS, INCLUYENDO ADMIN)
        # ============================================
        
        # COMANDO /mystats (para todos)
        if '/mystats' in msgText:
            user_stats = memory_stats.get_user_stats(username)
            if user_stats:
                total_size_formatted = format_file_size(user_stats['total_size'])
                
                stats_msg = f"""
📊 TUS ESTADÍSTICAS
━━━━━━━━━━━━━━━━━━━

👤 Usuario: @{username}
📤 Archivos subidos: {user_stats['uploads']}
🗑️ Archivos eliminados: {user_stats['deletes']}
💾 Espacio total usado: {total_size_formatted}
📅 Última actividad: {user_stats['last_activity']}
🔗 Nube: {user_info['moodle_host']}
━━━━━━━━━━━━━━━━━━━
📈 Resumen:
• Subiste {user_stats['uploads']} archivo(s)
• Eliminaste {user_stats['deletes']} archivo(s)
• Usaste {total_size_formatted} de espacio
                """
            else:
                stats_msg = f"""
📊 TUS ESTADÍSTICAS
━━━━━━━━━━━━━━━━━━━

👤 Usuario: @{username}
📤 Archivos subidos: 0
🗑️ Archivos eliminados: 0
💾 Espacio total usado: 0 B
📅 Última actividad: Nunca
🔗 Nube: {user_info['moodle_host']}
━━━━━━━━━━━━━━━━━━━
ℹ️ Aún no has realizado ninguna acción
                """
            
            bot.editMessageText(message, stats_msg)
            return
        
        # COMANDO /files (para todos)
        elif '/files' == msgText:
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
            loged = client.login()
            if loged:
                all_evidences = client.getEvidences()
                
                visible_list = []
                search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                
                for ev in all_evidences:
                    if ev['name'].endswith(search_pattern):
                        clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                        file_count = len(ev['files']) if 'files' in ev else 0
                        visible_list.append({
                            'name': clean_name,
                            'file_count': file_count,
                            'original': ev
                        })
                
                if len(visible_list) > 0:
                    files_msg = f"📁 TUS EVIDENCIAS\n"
                    files_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    for idx, item in enumerate(visible_list):
                        files_msg += f" {item['name']} [ {item['file_count']} ]\n"
                        files_msg += f" /txt_{idx} /del_{idx}\n\n"
                   
                    files_msg += f"━━━━━━━━━━━━━━━━━━━\n"
                    files_msg += f"Total: {len(visible_list)} evidencia(s)"
                    
                    bot.editMessageText(message, files_msg)
                else:
                    bot.editMessageText(message, '📭 No hay evidencias disponibles')
                client.logout()
            else:
                bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
                
        # COMANDO /txt_X (para todos)
        elif '/txt_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],proxy=proxy)
                loged = client.login()
                if loged:
                    all_evidences = client.getEvidences()
                    
                    visible_list = []
                    search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                    
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                            visible_list.append({
                                'clean_name': clean_name,
                                'original': ev
                            })
                    
                    if findex < 0 or findex >= len(visible_list):
                        bot.editMessageText(message, '❌ Índice inválido. Use /files para ver la lista.')
                        client.logout()
                        return
                    
                    evindex = visible_list[findex]['original']
                    clean_name = visible_list[findex]['clean_name']
                    
                    txtname = clean_name + '.txt'
                    
                    # Enviar el TXT con thumbnail desde URL
                    sendTxt(txtname, evindex['files'], update, bot)
                    
                    client.logout()
                    bot.editMessageText(message,'📄 TXT Aquí (con thumbnail personalizado)')
                else:
                    bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except ValueError:
                bot.editMessageText(message, '❌ Formato incorrecto. Use: /txt_0 (donde 0 es el número de la evidencia)')
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                print(f"Error en /txt_: {e}")
             
        # COMANDO /del_X (para todos)
        elif '/del_' in msgText:
            try:
                findex = int(str(msgText).split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],
                                       proxy=proxy)
                loged = client.login()
                if loged:
                    all_evidences = client.getEvidences()
                    
                    visible_list = []
                    search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                    
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                            visible_list.append({
                                'clean_name': clean_name,
                                'original': ev
                            })
                    
                    if findex < 0 or findex >= len(visible_list):
                        bot.editMessageText(message, '❌ Índice inválido. Use /files para ver la lista.')
                        client.logout()
                        return
                    
                    evfile = visible_list[findex]['original']
                    evidence_clean_name = visible_list[findex]['clean_name']
                    
                    file_count = len(evfile['files']) if 'files' in evfile else 0
                    
                    client.deleteEvidence(evfile)
                    
                    all_evidences = client.getEvidences()
                    
                    updated_visible_list = []
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            clean_name = ev['name'].replace(f"{USER_EVIDENCE_MARKER}{username}", "")
                            updated_visible_list.append({
                                'clean_name': clean_name,
                                'original': ev
                            })
                    
                    client.logout()
                    
                    memory_stats.log_delete(
                        username=username,
                        filename=f"{evidence_clean_name} ({file_count} archivos)",
                        evidence_name=evidence_clean_name,
                        moodle_host=user_info['moodle_host']
                    )
                    
                    confirmation_msg = f"🗑️ Evidencia eliminada: {evidence_clean_name}\n"
                    confirmation_msg += f"📁 Archivos borrados: {file_count}\n"
                    confirmation_msg += f"━━━━━━━━━━━━━━━━━━━\n"
                    
                    if len(updated_visible_list) > 0:
                        confirmation_msg += f"📋 Tus evidencias actualizadas:\n\n"
                        
                        for idx, item in enumerate(updated_visible_list):
                            clean_name = item['clean_name']
                            item_file_count = len(item['original']['files']) if 'files' in item['original'] else 0
                            confirmation_msg += f" {clean_name} [ {item_file_count} ]\n"
                            confirmation_msg += f" /txt_{idx} /del_{idx}\n\n"
                        
                        bot.editMessageText(message, confirmation_msg)
                    else:
                        confirmation_msg += f"📭 No hay evidencias disponibles"
                        bot.editMessageText(message, confirmation_msg)
                    
                else:
                    bot.editMessageText(message,'➲ Error y Causas🧐\n11-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except ValueError:
                bot.editMessageText(message, '❌ Formato incorrecto. Use: /del_0 (donde 0 es el número de la evidencia)')
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                print(f"Error en /del_: {e}")
                
        # COMANDO /delall (para todos)
        elif '/delall' in msgText:
            try:
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                       user_info['moodle_password'],
                                       user_info['moodle_host'],
                                       user_info['moodle_repo_id'],
                                       proxy=proxy)
                loged = client.login()
                if loged:
                    all_evidences = client.getEvidences()
                    
                    user_evidences = []
                    search_pattern = f"{USER_EVIDENCE_MARKER}{username}"
                    for ev in all_evidences:
                        if ev['name'].endswith(search_pattern):
                            user_evidences.append(ev)
                    
                    if not user_evidences:
                        bot.editMessageText(message, '📭 No hay evidencias disponibles')
                        client.logout()
                        return
                    
                    total_evidences = len(user_evidences)
                    total_files = 0
                    
                    for ev in user_evidences:
                        files_in_evidence = ev.get('files', [])
                        total_files += len(files_in_evidence)
                    
                    for item in user_evidences:
                        try:
                            client.deleteEvidence(item)
                        except Exception as e:
                            print(f"Error eliminando evidencia: {e}")
                    
                    client.logout()
                    
                    memory_stats.log_delete_all(
                        username=username, 
                        deleted_evidences=total_evidences, 
                        deleted_files=total_files,
                        moodle_host=user_info['moodle_host']
                    )
                    
                    deletion_msg = f"🗑️ ELIMINACIÓN MASIVA COMPLETADA\n"
                    deletion_msg += f"📊 Resumen:\n"
                    deletion_msg += f"   • Evidencias eliminadas: {total_evidences}\n"
                    deletion_msg += f"   • Archivos borrados: {total_files}\n"
                    deletion_msg += f"\n━━━━━━━━━━━━━━━━━━━\n"
                    deletion_msg += f"✅ ¡Todas tus evidencias han sido eliminadas!\n"
                    deletion_msg += f"📭 No hay evidencias disponibles"
                    
                    bot.editMessageText(message, deletion_msg)
                    
                else:
                    bot.editMessageText(message,'➲ Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except Exception as e:
                bot.editMessageText(message, f'❌ Error: {str(e)}')
                print(f"Error en /delall: {e}")
                
        # PROCESAR ENLACES HTTP (para todos)
        elif 'http' in msgText:
            url = msgText
            
            funny_message_sent = None
            
            try:
                import requests
                headers = {}
                if user_info['proxy']:
                    proxy_dict = ProxyCloud.parse(user_info['proxy'])
                    if 'http' in proxy_dict:
                        headers.update({'Proxy': proxy_dict['http']})
                
                response = requests.head(url, allow_redirects=True, timeout=5, headers=headers)
                file_size = int(response.headers.get('content-length', 0))
                file_size_mb = file_size / (1024 * 1024)
                
                if file_size_mb > 500:
                    funny_message = get_random_large_file_message()
                    warning_msg = bot.sendMessage(update.message.chat.id, 
                                      f"⚠️ {funny_message}\n\n"
                                      f"❌ Cojoneee, tú piensas q esto es una nube artificial o q? Para q tú quieres subir {file_size_mb:.2f} MB?\n\n"
                                      f"⬆️ Bueno, lo subiré😡")
                    funny_message_sent = warning_msg
                
            except Exception as e:
                pass
            
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
            
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
