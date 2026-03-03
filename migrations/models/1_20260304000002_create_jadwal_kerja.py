from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `jadwal_kerja` (
            `id_jadwal` int(11) NOT NULL AUTO_INCREMENT,
            `nama_shift` enum('pagi','sore') NOT NULL DEFAULT 'pagi',
            `shift_mulai` time NOT NULL,
            `shift_selesai` time NOT NULL,
            `hari_dalam_seminggu` enum('Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu') NOT NULL,
            PRIMARY KEY (`id_jadwal`),
            UNIQUE KEY `uk_hari_shift` (`hari_dalam_seminggu`,`nama_shift`),
            KEY `idx_hari` (`hari_dalam_seminggu`),
            KEY `idx_hari_shift` (`hari_dalam_seminggu`,`nama_shift`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `jadwal_kerja`
    """
