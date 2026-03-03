from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `hari_libur` (
            `id_libur` int(11) NOT NULL AUTO_INCREMENT,
            `tanggal` date NOT NULL,
            `keterangan` varchar(100) NOT NULL,
            `tipe` enum('nasional','cuti_bersama') NOT NULL DEFAULT 'nasional',
            PRIMARY KEY (`id_libur`),
            UNIQUE KEY `uk_tanggal` (`tanggal`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `hari_libur`
    """
