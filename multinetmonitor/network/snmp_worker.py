import time
import asyncio
from PySide6.QtCore import QThread, Signal
from pysnmp.hlapi.v3arch.asyncio import *
from ..utils.logger import get_logger

class SNMPWorker(QThread):
    # Emit a dictionary of results: {'uptime': str, 'cpu': float, 'traffic_in': int, 'custom': {}} or error
    result_ready = Signal(dict)

    def __init__(self, target_ip, community='public', version=2, port=161, interval_sec=5.0, custom_oids=None, v3_creds=None):
        super().__init__()
        self.target_ip = target_ip
        self.community = community
        
        if version == 3:
            self.version = 3
        else:
            self.version = 0 if version == 1 else 1  # 0 for v1, 1 for v2c
            
        self.port = port
        self.interval_sec = interval_sec
        self.custom_oids = custom_oids or []
        self.v3_creds = v3_creds
        self.running = True
        self.logger = get_logger()

    def run(self):
        # QThread run method is synchronous, so we start a new asyncio event loop for this thread
        asyncio.run(self.async_run())

    async def async_run(self):
        # Only initialize SnmpEngine inside the thread to avoid sharing across threads
        self.snmpEngine = SnmpEngine()
        
        while self.running:
            data = await self._poll_snmp()
            self.result_ready.emit(data)
            
            # Sleep in increments so we can exit quickly
            for _ in range(int(self.interval_sec * 10)):
                if not self.running:
                    break
                await asyncio.sleep(0.1)

    async def _poll_snmp(self):
        result_data = {'custom': {}}
        
        oid_requests = [
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.3.0')),         # sysUpTime
            ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.10.1')),    # ifInOctets
            ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.16.1')),    # ifOutOctets
            ObjectType(ObjectIdentity('1.3.6.1.2.1.25.3.3.1.2.1'))   # hrProcessorLoad
        ]
        
        for co in self.custom_oids:
            try:
                oid_requests.append(ObjectType(ObjectIdentity(co['oid'])))
            except Exception as e:
                self.logger.error(f"Invalid OID {co['oid']} for {self.target_ip}: {e}")
                
        try:
            if self.version == 3 and self.v3_creds:
                auth_proto = usmHMACMD5AuthProtocol if self.v3_creds['auth_proto'] == 'MD5' else (usmHMACSHAAuthProtocol if self.v3_creds['auth_proto'] == 'SHA' else usmNoAuthProtocol)
                priv_proto = usmDESPrivProtocol if self.v3_creds['priv_proto'] == 'DES' else (usmAesCfb128Protocol if self.v3_creds['priv_proto'] == 'AES' else usmNoPrivProtocol)
                
                auth_key = self.v3_creds['auth_key'] if self.v3_creds['auth_proto'] != 'NONE' else None
                priv_key = self.v3_creds['priv_key'] if self.v3_creds['priv_proto'] != 'NONE' else None
                
                auth_data = UsmUserData(
                    self.v3_creds['user'],
                    authKey=auth_key,
                    privKey=priv_key,
                    authProtocol=auth_proto,
                    privProtocol=priv_proto
                )
            else:
                auth_data = CommunityData(self.community, mpModel=self.version)
                
            errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
                self.snmpEngine,
                auth_data,
                await UdpTransportTarget.create((self.target_ip, self.port), timeout=2.0, retries=1),
                ContextData(),
                *oid_requests
            )

            if errorIndication:
                result_data['error'] = str(errorIndication)
            elif errorStatus:
                result_data['error'] = f"{errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}"
            else:
                for varBind in varBinds:
                    oid = str(varBind[0])
                    val = varBind[1]
                    
                    if '1.3.6.1.2.1.1.3.0' in oid:
                        try:
                            ticks = int(val)
                            seconds = ticks / 100.0
                            m, s = divmod(seconds, 60)
                            h, m = divmod(m, 60)
                            d, h = divmod(h, 24)
                            result_data['uptime'] = f"{int(d)}d {int(h)}h {int(m)}m {int(s)}s"
                        except:
                            result_data['uptime'] = str(val)
                    elif '1.3.6.1.2.1.2.2.1.10.1' in oid:
                        result_data['traffic_in'] = int(val) if val.prettyPrint() != "No Such Instance currently exists at this OID" else 0
                    elif '1.3.6.1.2.1.2.2.1.16.1' in oid:
                        result_data['traffic_out'] = int(val) if val.prettyPrint() != "No Such Instance currently exists at this OID" else 0
                    elif '1.3.6.1.2.1.25.3.3.1.2.1' in oid:
                        try:
                            result_data['cpu'] = int(val)
                        except:
                            result_data['cpu'] = None
                            
                    # Check against custom OIDs
                    for co in self.custom_oids:
                        if co['oid'] in oid or oid in co['oid']:
                            val_str = val.prettyPrint()
                            if val_str == "No Such Instance currently exists at this OID" or val_str == "No Such Object currently exists at this OID":
                                val_str = "--"
                            if co['suffix']:
                                val_str += f" {co['suffix']}"
                            result_data['custom'][co['name']] = val_str

        except Exception as e:
            self.logger.error(f"SNMP exception for {self.target_ip}: {e}")
            result_data['error'] = str(e)
            
        return result_data

    def stop(self):
        self.running = False
