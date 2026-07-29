import asyncio
import ipaddress
import platform
import subprocess
from PySide6.QtCore import QThread, Signal
from pysnmp.hlapi.v3arch.asyncio import *

class SubnetScannerWorker(QThread):
    # Emits (ip, status, sysName)
    host_found = Signal(str, str, str)
    scan_finished = Signal()
    progress_update = Signal(int, int) # current, total

    def __init__(self, subnet_str, community='public', version=2, port=161):
        super().__init__()
        self.subnet_str = subnet_str
        self.community = community
        self.version = 0 if version == 1 else 1
        self.port = port
        self.running = True
        
    def run(self):
        asyncio.run(self.async_run())

    async def async_run(self):
        try:
            network = ipaddress.IPv4Network(self.subnet_str, strict=False)
            hosts = list(network.hosts())
            total = len(hosts)
            
            # Batch process in chunks of 50 to avoid too many open files
            chunk_size = 50
            for i in range(0, total, chunk_size):
                if not self.running:
                    break
                    
                chunk = hosts[i:i+chunk_size]
                tasks = [self.scan_host(str(ip)) for ip in chunk]
                await asyncio.gather(*tasks)
                
                self.progress_update.emit(min(i+chunk_size, total), total)
                
        except Exception as e:
            print(f"Subnet scanner error: {e}")
            
        self.scan_finished.emit()

    async def scan_host(self, ip):
        # 1. Fast ICMP Ping
        extra_kwargs = {}
        if platform.system().lower() == "windows":
            ping_cmd = ['ping', '-n', '1', '-w', '1000', ip]
            extra_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        else:
            ping_cmd = ['ping', '-c', '1', '-W', '1', ip]

        process = await asyncio.create_subprocess_exec(
            *ping_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            **extra_kwargs
        )
        await process.communicate()
        
        if process.returncode != 0:
            return # Host down
            
        sys_name = "Unknown Device"
        # 2. Try SNMP sysName
        snmpEngine = SnmpEngine()
        try:
            target = await UdpTransportTarget.create((ip, self.port), timeout=1.0, retries=0)
            errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
                snmpEngine,
                CommunityData(self.community, mpModel=self.version),
                target,
                ContextData(),
                ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0'))
            )
            if not errorIndication and not errorStatus:
                sys_name = varBinds[0][1].prettyPrint()
        except Exception:
            pass
            
        if self.running:
            self.host_found.emit(ip, "Online", sys_name)

    def stop(self):
        self.running = False
