


from src.services.db import Db, DbTable

class StatisticTable(DbTable):
    def __init__(self, db: Db) -> None:
        super().__init__(db, 'statistic')
    
    def addCount(self, 
        applicationId: int, 
        playlistId: int, 
        serverId: int,
        contractId: int, 
        trackId: int,
        ymdh: int,
        play_duration: int
    ):
    #CREATE TABLE vocabulary(word TEXT PRIMARY KEY, count INT DEFAULT 1);
    #INSERT INTO vocabulary(word) VALUES('jovial')
    #ON CONFLICT(word) DO UPDATE SET count=count+1;
        self.db.insert(f"INSERT INTO {self.name} \
            (application_id, playlist_id, server_id, contract_id, track_id, ymdh, count, play_duration) \
            VALUES ({applicationId:d}, {playlistId:d}, {serverId:d}, {contractId:d}, {trackId:d}, {ymdh:d}, 1, {play_duration:d}) \
            ON CONFLICT (application_id, playlist_id, server_id, contract_id, ymdh) DO UPDATE SET count = count + 1, play_duration= play_duration + {play_duration:d};"
        )
    def getContractStats(self, status=None):
        where =''
        if status:
            where = " where c.status='%s'" % status
        return self.db.select(f"""
select 
    a.name as `application`,
    l.name as `client`,
    c.code as `contract`,
    sum(c.count) as `sold`,
    sum(s.count) as `played`,
    c.status as 'status',
    case when sum(c.count)>0 then
        (sum(s.count)/sum(c.count))*100 else
        'n/a' end as `progress`
    from statistic s 
LEFT JOIN application a ON (s.application_id = a.rowid)
LEFT join contract c on (c.rowid = s.contract_id)
LEFT join client l on (l.rowid = c.client_id)
{where:s}
group by c.rowid;
""").fetchall()

    def getTracksStats(self, status=None):
        where =''
        if status:
            where = " where c.status='%s'" % status
        return self.db.select(f"""
select 
    a.name as `application`,
    l.name as `client`,
    c.code as `contract`,
    r.name as 'artist',
    t.name as 'track',
    sum(s.count) as `played`
    from statistic s 
LEFT JOIN application a ON (s.application_id = a.rowid)
LEFT join contract c on (c.rowid = s.contract_id)
LEFT join track t on (t.rowid = s.track_id)
LEFT join artist r on (r.rowid = t.artist_id)
LEFT join client l on (l.rowid = c.client_id)
{where:s}
group by t.rowid;
""").fetchall()