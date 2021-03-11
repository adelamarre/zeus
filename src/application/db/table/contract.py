


from src.services.db import Db, DbTable
from datetime import datetime

class ContractTable(DbTable):
    def __init__(self, db: Db) -> None:
        super().__init__(db, 'contract')
    
    def addContract(self, clientId: int, code: str, description: str, count: int, status: str) -> int:
        return self.db.insert(f"INSERT INTO {self.name} \
            (client_id, code, description, count, date, status) \
            VALUES ({clientId:d}, '{code:s}', '{description:s}', {count:d}, '{str(datetime.now()):s}', '{status:s}')"
        )

    def findByCode(self, clientId: int, code: str, status: str = None):
        where = {
            'client_id': clientId,
            'code': code
        }
        if status:
            where['status'] = status
        return self.findBy(where)

    def findAllByClient(self, clientId: int):
        return self.findAllBy({'client_id': clientId})

