from datetime import datetime
from src.services.db import Db



class ContractManager:
    def __init__(self, db: Db ) -> None:
        self.db = db

    def getContractsChoices(self, clientId: int):
        contractChoices = []
        for contract in self.getContracts(clientId, 'open'):
            contractChoices.append({
                'name': '%s (%s)' % (contract['code'], contract['description']),
                'value': int(contract['rowid'])
            })
        contractChoices.append({
            'name': 'Create a new contract',
            'value': 0
        })
        return contractChoices

    def getContracts(self, clientId: int = None, status: str = None):
        ##contracts = []
        where = ''
        statusConstraint = ''
        clientIdConstraint = ''

        constraints = []

        if clientId:
            constraints.append('client_id=%d' % clientId)
        
        if status:
            constraints.append("status='%s'" % status)
        
        if len(constraints):
            where = 'where ' + ' and '.join(constraints)

        return self.db.select(f"SELECT rowid, * FROM contract {where} order by rowid;").fetchall()
        
    def addContract(self, clientId: int, code: str, description: str) -> int:
        return self.db.insert("INSERT INTO contract \
            (client_id, code, description, date, status) \
            VALUES (%d, '%s', '%s', '%s', 'open')" % 
            (clientId, code, description, str(datetime.now()))
        )
        
        