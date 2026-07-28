import asyncio
from PySide6.QtCore import QThread, Signal
from pysnmp.hlapi.v3arch.asyncio import *
from ..utils.logger import get_logger

class SNMPScannerWorker(QThread):
    # Emits a list of tuples: [(oid_str, val_str), ...]
    data_found = Signal(list)
    # Emits completion message or error string
    finished_scan = Signal(str)

    def __init__(self, target_ip, community='public', version=2, port=161):
        super().__init__()
        self.target_ip = target_ip
        self.community = community
        self.version = 0 if version == 1 else 1
        self.port = port
        self.running = True
        self.logger = get_logger()

    def run(self):
        asyncio.run(self.async_run())

    async def async_run(self):
        self.snmpEngine = SnmpEngine()
        try:
            target = await UdpTransportTarget.create((self.target_ip, self.port), timeout=2.0, retries=2)
            auth = CommunityData(self.community, mpModel=self.version)
            
            # Start walk at the very root to get everything
            start_oid = ObjectType(ObjectIdentity('1.3.6'))
            
            if self.version == 1:
                # v2c is 1, v1 is 0. If v1, we use walk_cmd.
                iterator = walk_cmd(
                    self.snmpEngine, auth, target, ContextData(),
                    start_oid,
                    lexicographicMode=True
                )
            else:
                iterator = bulk_walk_cmd(
                    self.snmpEngine, auth, target, ContextData(),
                    0, 50, # nonRepeaters, maxRepetitions
                    start_oid,
                    lexicographicMode=True
                )
            
            import inspect
            
            if inspect.iscoroutine(iterator):
                iterator = await iterator
                
            if hasattr(iterator, '__aiter__'):
                async for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                    if not self.running:
                        self.finished_scan.emit("Stopped by user.")
                        return
                    
                    if errorIndication:
                        self.finished_scan.emit(f"Error: {errorIndication}")
                        return
                    elif errorStatus:
                        self.finished_scan.emit(f"Error: {errorStatus.prettyPrint()}")
                        return
                    else:
                        batch = []
                        for varBind in varBinds:
                            oid = str(varBind[0])
                            val = varBind[1].prettyPrint()
                            batch.append((oid, val))
                        
                        if batch:
                            self.data_found.emit(batch)
            else:
                for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                    if not self.running:
                        self.finished_scan.emit("Stopped by user.")
                        return
                    
                    if errorIndication:
                        self.finished_scan.emit(f"Error: {errorIndication}")
                        return
                    elif errorStatus:
                        self.finished_scan.emit(f"Error: {errorStatus.prettyPrint()}")
                        return
                    else:
                        batch = []
                        for varBind in varBinds:
                            oid = str(varBind[0])
                            val = varBind[1].prettyPrint()
                            batch.append((oid, val))
                        
                        if batch:
                            self.data_found.emit(batch)
                            
            self.finished_scan.emit("Scan complete.")
            
        except Exception as e:
            self.logger.error(f"Scanner exception for {self.target_ip}: {e}")
            self.finished_scan.emit(f"Error: {e}")

    def stop(self):
        self.running = False
