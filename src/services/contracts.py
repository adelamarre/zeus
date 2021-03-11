from datetime import datetime
from src.application.db.table.contract import ContractTable
from src.services.db import Db



class ContractManager:
    def __init__(self, db: Db ) -> None:
        self.db = db
        self.contractTable = ContractTable(db)

    def getContractsChoices(self, clientId: int):
        contractChoices = []
        for contract in self.contractTable.findAllByClient(clientId, 'open'):
            contractChoices.append({
                'name': '%s (%s)' % (contract['code'], contract['description']),
                'value': int(contract['rowid'])
            })
        contractChoices.append({
            'name': 'Create a new contract',
            'value': 0
        })
        return contractChoices
        
    def addContract(self, clientId: int, code: str, description: str, count: int) -> int:
        return self.contractTable.addContract(
            clientId=clientId,
            code=code,
            description=description,
            count=count,
            status='open'
        )
        
        
        