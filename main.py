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

# CONFIGURACIÓN FIJA EN EL CÓDIGO
BOT_TOKEN = "8410047906:AAGntGHmkIuIvovBMQfy-gko2JTw3TNJsak"

# CONFIGURACIÓN ADMINISTRADOR
ADMIN_USERNAME = "Eliel_21"

# ZONA HORARIA DE CUBA
try:
    CUBA_TZ = pytz.timezone('America/Havana')
except:
    CUBA_TZ = None

# SEPARADOR PARA EVIDENCIAS POR USUARIO
USER_EVIDENCE_MARKER = " "  # Espacio como separador

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
        "proxy": "",
        "tokenize": 0
    },
    "maykolguille,yordante,veno_mancer,Miguwq,Emanuel14APK": {
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
        return "Todos los datos han sido eliminados"

memory_stats = MemoryStats()

def get_random_large_file_message():
    """Retorna un mensaje chistoso aleatorio para archivos grandes"""
    messages = [
        "Uy! Este archivo pesa mas que mis ganas de trabajar los lunes",
        "Seguro que no estas subiendo toda la temporada de tu serie favorita?",
        "Archivo detectado: XXL. Mi bandeja de entrada necesita hacer dieta",
        "500MB alert! Esto es mas grande que mi capacidad de decision en un restaurante",
        "Tu archivo necesita su propio codigo postal para viajar por internet",
        "Vaya, con este peso hasta el bot necesita ir al gimnasio",
        "Archivo XXL detectado! Preparando equipo de escalada para subirlo",
        "Este archivo es tan grande que necesita su propia habitacion en la nube",
        "Esto es un archivo o un elefante digital disfrazado?",
        "Alerta de megabyte! Tu archivo podria tener su propia orbita",
        "Archivo pesado detectado: activando modo grua industrial",
        "Este archivo hace que mi servidor sude bytes",
        "Tamaño maximo superado! Necesitare un cafe extra para esto",
        "Tu archivo es mas grande que mi lista de excusas para no hacer ejercicio",
        "Detectado: Archivo XXL. Preparando refuerzos estructurales",
        "Vaya! Este archivo es tan grande que necesita pasaporte para viajar",
        "Con este peso, hasta la nube digital va a necesitar paraguas",
        "500MB detectados! Traes la biblioteca de Alejandria en un ZIP?",
        "Tu archivo tiene mas MB que yo tengo neuronas despues del cafe",
        "Alerta! Archivo de tamaño epico detectado. Activando modo Hulk",
        "Este archivo es mas pesado que mis remordimientos del lunes",
        "Uy! Con este tamaño hasta internet va a sudar la gota gorda",
        "Seguro que no estas subiendo un elefante en formato MP4?",
        "Archivo XXL: Mi conexion acaba de pedir aumento de sueldo",
        "500MB! Hasta los pixeles estan haciendo dieta en este archivo"
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
        bot.editMessageText(message,'Preparando Para Subir')
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
            bot.editMessageText(message,'Error En La Pagina')
            return None
    except Exception as ex:
        bot.editMessageText(message,'Error ' + str(ex))
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
            print(f"Error obteniendo indice de evidencia: {e}")
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
        bot.editMessageText(message,'Error en la pagina')

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)
        else:
            try:
                bot.editMessageText(message,'Error en la descarga')
            except:
                bot.editMessageText(message,'Error en la descarga')

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
    """Elimina un mensaje despues de un retraso especifico"""
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
            bot.sendMessage(update.message.chat.id,'No tienes acceso a este bot')
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
                bot.editMessageText(msg,'Tarea Cancelada')
            except Exception as ex:
                print(str(ex))
            return

        message = bot.sendMessage(update.message.chat.id,'Procesando')
        thread.store('msg',message)

        if '/mystats' in msgText:
            user_stats = memory_stats.get_user_stats(username)
            if user_stats:
                total_size_formatted = format_file_size(user_stats['total_size'])
                
                stats_msg = f"""
TUS ESTADISTICAS

Usuario: @{username}
Archivos subidos: {user_stats['uploads']}
Archivos eliminados: {user_stats['deletes']}
Espacio total usado: {total_size_formatted}
Ultima actividad: {user_stats['last_activity']}
Nube: {user_info['moodle_host']}
━━━━━━━━━━━━━━━━━━━
Resumen:
• Subiste {user_stats['uploads']} archivo(s)
• Eliminaste {user_stats['deletes']} archivo(s)
• Usaste {total_size_formatted} de espacio
                """
            else:
                stats_msg = f"""
TUS ESTADISTICAS

Usuario: @{username}
Archivos subidos: 0
Archivos eliminados: 0
Espacio total usado: 0 B
Ultima actividad: Nunca
Nube: {user_info['moodle_host']}
━━━━━━━━━━━━━━━━━━━
Aun no has realizado ninguna accion
                """
            
            bot.editMessageText(message, stats_msg)
            return

        if username == ADMIN_USERNAME:
            if '/admin' in msgText:
                stats = memory_stats.get_all_stats()
                total_size_formatted = format_file_size(stats['total_size_uploaded'])
                current_date = format_cuba_date()
                
                if memory_stats.has_any_data():
                    admin_msg = f"""
PANEL DE ADMINISTRADOR
{current_date}
━━━━━━━━━━━━━━━━━━━
ESTADISTICAS GLOBALES:
• Subidas totales: {stats['total_uploads']}
• Eliminaciones totales: {stats['total_deletes']}
• Espacio total subido: {total_size_formatted}

COMANDOS DISPONIBLES:
/adm_logs - Ver ultimos logs
/adm_users - Ver estadisticas por usuario
/adm_uploads - Ver ultimas subidas
/adm_deletes - Ver ultimas eliminaciones
/adm_cleardata - Limpiar todos los datos
━━━━━━━━━━━━━━━━━━━
Hora Cuba: {format_cuba_datetime().split(' ')[1]}
                    """
                else:
                    admin_msg = f"""
PANEL DE ADMINISTRADOR
{current_date}
━━━━━━━━━━━━━━━━━━━
NO HAY DATOS REGISTRADOS
Aun no se ha realizado ninguna accion en el bot.

COMANDOS DISPONIBLES:
/adm_logs - Ver ultimos logs
/adm_users - Ver estadisticas por usuario
/adm_uploads - Ver ultimas subidas
/adm_deletes - Ver ultimas eliminaciones
━━━━━━━━━━━━━━━━━━━
Hora Cuba: {format_cuba_datetime().split(' ')[1]}
                    """
                
                bot.editMessageText(message, admin_msg)
                return
            
            elif '/adm_logs' in msgText:
                try:
                    if not memory_stats.has_any_data():
                        bot.editMessageText(message, "No hay datos registrados")
                        return
                    
                    limit = 20
                    if '_' in msgText:
                        try:
                            limit = int(msgText.split('_')[2])
                        except: pass
                    
                    uploads = memory_stats.get_recent_uploads(limit)
                    deletes = memory_stats.get_recent_deletes(limit)
                    
                    logs_msg = f"ULTIMOS LOGS\n"
                    logs_msg += f"{format_cuba_date()}\n"
                    logs_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    if uploads:
                        logs_msg += "ULTIMAS SUBIDAS:\n"
                        for log in uploads:
                            logs_msg += f"• {log['timestamp']} - @{log['username']}: {log['filename']} ({log['file_size_formatted']})\n"
                        logs_msg += "\n"
                    
                    if deletes:
                        logs_msg += "ULTIMAS ELIMINACIONES:\n"
                        for log in deletes:
                            if log['type'] == 'delete_all':
                                logs_msg += f"• {log['timestamp']} - @{log['username']}: ELIMINO TODO ({log.get('deleted_evidences', 1)} evidencia(s), {log.get('deleted_files', '?')} archivos)\n"
                            else:
                                logs_msg += f"• {log['timestamp']} - @{log['username']}: {log['filename']} (de: {log['evidence_name']})\n"
                    
                    if len(logs_msg) > 4000:
                        logs_msg = logs_msg[:4000] + "\n\nLogs truncados (demasiados)"
                    
                    bot.editMessageText(message, logs_msg)
                except Exception as e:
                    bot.editMessageText(message, f"Error al obtener logs: {str(e)}")
                return
            
            elif '/adm_users' in msgText:
                try:
                    users = memory_stats.get_all_users()
                    if not users:
                        bot.editMessageText(message, "No hay usuarios registrados")
                        return
                    
                    users_msg = f"ESTADISTICAS POR USUARIO\n"
                    users_msg += f"{format_cuba_date()}\n"
                    users_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    for user, data in sorted(users.items(), key=lambda x: x[1]['uploads'], reverse=True):
                        total_size_formatted = format_file_size(data['total_size'])
                        users_msg += f"@{user}\n"
                        users_msg += f"   Subidas: {data['uploads']}\n"
                        users_msg += f"   Eliminaciones: {data['deletes']}\n"
                        users_msg += f"   Espacio usado: {total_size_formatted}\n"
                        users_msg += f"   Ultima actividad: {data['last_activity']}\n\n"
                    
                    if len(users_msg) > 4000:
                        users_msg = users_msg[:4000] + "\n\nLista truncada (demasiados usuarios)"
                    
                    bot.editMessageText(message, users_msg)
                except Exception as e:
                    bot.editMessageText(message, f"Error al obtener usuarios: {str(e)}")
                return
            
            elif '/adm_uploads' in msgText:
                try:
                    uploads = memory_stats.get_recent_uploads(15)
                    if not uploads:
                        bot.editMessageText(message, "No hay subidas registradas")
                        return
                    
                    uploads_msg = f"ULTIMAS SUBIDAS\n"
                    uploads_msg += f"{format_cuba_date()}\n"
                    uploads_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    for i, log in enumerate(uploads, 1):
                        uploads_msg += f"{i}. {log['filename']}\n"
                        uploads_msg += f"   @{log['username']}\n"
                        uploads_msg += f"   {log['timestamp']}\n"
                        uploads_msg += f"   {log['file_size_formatted']}\n"
                        uploads_msg += f"   {log['moodle_host']}\n\n"
                    
                    bot.editMessageText(message, uploads_msg)
                except Exception as e:
                    bot.editMessageText(message, f"Error al obtener subidas: {str(e)}")
                return
            
            elif '/adm_deletes' in msgText:
                try:
                    deletes = memory_stats.get_recent_deletes(15)
                    if not deletes:
                        bot.editMessageText(message, "No hay eliminaciones registradas")
                        return
                    
                    deletes_msg = f"ULTIMAS ELIMINACIONES\n"
                    deletes_msg += f"{format_cuba_date()}\n"
                    deletes_msg += f"━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    for i, log in enumerate(deletes, 1):
                        if log['type'] == 'delete_all':
                            deletes_msg += f"{i}. ELIMINACION MASIVA\n"
                            deletes_msg += f"   @{log['username']}\n"
                            deletes_msg += f"   {log['timestamp']}\n"
                            deletes_msg += f"   ELIMINO {log.get('deleted_evidences', 1)} EVIDENCIA(S)\n"
                            deletes_msg += f"   Archivos borrados: {log.get('deleted_files', '?')}\n"
                        else:
                            deletes_msg += f"{i}. {log['filename']}\n"
                            deletes_msg += f"   @{log['username']}\n"
                            deletes_msg += f"   {log['timestamp']}\n"
                            deletes_msg += f"   Evidencia: {log['evidence_name']}\n"
                        
                        deletes_msg += f"   {log['moodle_host']}\n\n"
                    
                    bot.editMessageText(message, deletes_msg)
                except Exception as e:
                    bot.editMessageText(message, f"Error al obtener eliminaciones: {str(e)}")
                return
            
            elif '/adm_cleardata' in msgText:
                try:
                    if not memory_stats.has_any_data():
                        bot.editMessageText(message, "No hay datos para limpiar")
                        return
                    
                    result = memory_stats.clear_all_data()
                    bot.editMessageText(message, f"{result}")
                except Exception as e:
                    bot.editMessageText(message, f"Error al limpiar datos: {str(e)}")
                return

        if '/start' in msgText:
            start_msg = f'Usuario: @{username}\nNube: Moodle\nEvidence: Activado\nHost: {user_info["moodle_host"]}\nFileToLink: @fileeliellinkBot'
            bot.editMessageText(message,start_msg)
            
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
                    files_msg = "TUS EVIDENCIAS:\n\n"
                    
                    for idx, item in enumerate(visible_list):
                        files_msg += f"{item['name']} ({item['file_count']})\n"
                        files_msg += f"   /txt_{idx} /del_{idx}\n\n"
                    
                    files_msg += f"━━━━━━━━━━━━━━━━━━━\n"
                    files_msg += f"Total: {len(visible_list)} evidencia(s)"
                    
                    bot.editMessageText(message, files_msg)
                else:
                    bot.editMessageText(message,'No hay evidencias disponibles')
                client.logout()
            else:
                bot.editMessageText(message,'Error y Causas\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
                
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
                        bot.editMessageText(message, 'Indice invalido. Use /files para ver la lista.')
                        client.logout()
                        return
                    
                    evindex = visible_list[findex]['original']
                    clean_name = visible_list[findex]['clean_name']
                    
                    txtname = clean_name + '.txt'
                    
                    sendTxt(txtname, evindex['files'], update, bot)
                    
                    client.logout()
                    bot.editMessageText(message,'TXT Aqui')
                else:
                    bot.editMessageText(message,'Error y Causas\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except ValueError:
                bot.editMessageText(message, 'Formato incorrecto. Use: /txt_0 (donde 0 es el numero de la evidencia)')
            except Exception as e:
                bot.editMessageText(message, f'Error: {str(e)}')
                print(f"Error en /txt_: {e}")
             
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
                        bot.editMessageText(message, 'Indice invalido. Use /files para ver la lista.')
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
                    
                    confirmation_msg = f"Evidencia eliminada: {evidence_clean_name}\n"
                    confirmation_msg += f"Archivos borrados: {file_count}\n"
                    confirmation_msg += f"━━━━━━━━━━━━━━━━━━━\n"
                    
                    if len(updated_visible_list) > 0:
                        confirmation_msg += f"Tus evidencias actualizadas:\n\n"
                        
                        for idx, item in enumerate(updated_visible_list):
                            clean_name = item['clean_name']
                            item_file_count = len(item['original']['files']) if 'files' in item['original'] else 0
                            confirmation_msg += f"{clean_name} ({item_file_count})\n"
                            confirmation_msg += f"   /txt_{idx} /del_{idx}\n\n"
                        
                        bot.editMessageText(message, confirmation_msg)
                    else:
                        confirmation_msg += f"No hay evidencias disponibles"
                        bot.editMessageText(message, confirmation_msg)
                    
                else:
                    bot.editMessageText(message,'Error y Causas\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except ValueError:
                bot.editMessageText(message, 'Formato incorrecto. Use: /del_0 (donde 0 es el numero de la evidencia)')
            except Exception as e:
                bot.editMessageText(message, f'Error: {str(e)}')
                print(f"Error en /del_: {e}")
                
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
                        bot.editMessageText(message, 'No hay evidencias disponibles')
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
                    
                    deletion_msg = f"ELIMINACION MASIVA COMPLETADA\n"
                    deletion_msg += f"Resumen:\n"
                    deletion_msg += f"   • Evidencias eliminadas: {total_evidences}\n"
                    deletion_msg += f"   • Archivos borrados: {total_files}\n"
                    deletion_msg += f"\n━━━━━━━━━━━━━━━━━━━\n"
                    deletion_msg += f"Todas tus evidencias han sido eliminadas\n"
                    deletion_msg += f"No hay evidencias disponibles"
                    
                    bot.editMessageText(message, deletion_msg)
                    
                else:
                    bot.editMessageText(message,'Error y Causas\n1-Revise su Cuenta\n2-Servidor Deshabilitado: '+client.path)
            except Exception as e:
                bot.editMessageText(message, f'Error: {str(e)}')
                print(f"Error en /delall: {e}")
                
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
                                      f"{funny_message}\n\n"
                                      f"Cojoneee, tu piensas q esto es una nube artificial o q? Para q tu quieres subir {file_size_mb:.2f} MB?\n\n"
                                      f"Bueno, lo subire")
                    funny_message_sent = warning_msg
                
            except Exception as e:
                pass
            
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
            
            if funny_message_sent:
                delete_message_after_delay(bot, funny_message_sent.chat.id, funny_message_sent.message_id, 8)
            
        else:
            bot.editMessageText(message,'No se pudo procesar ')
            
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
