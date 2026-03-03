from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `konfigurasi_aplikasi` (
            `id_pengaturan` int(3) NOT NULL AUTO_INCREMENT,
            `toleransi_terlambat` int(2) NOT NULL DEFAULT 15 COMMENT '15 menit',
            `maks_hari_cuti` int(2) NOT NULL DEFAULT 12,
            PRIMARY KEY (`id_pengaturan`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `konfigurasi_aplikasi`
    """
