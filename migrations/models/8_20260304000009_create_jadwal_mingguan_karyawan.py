from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `jadwal_mingguan_karyawan` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `id_karyawan` varchar(10) NOT NULL,
            `hari` enum('Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu') NOT NULL,
            `kode_shift` enum('pagi','sore') NOT NULL DEFAULT 'pagi',
            PRIMARY KEY (`id`),
            UNIQUE KEY `uk_karyawan_hari` (`id_karyawan`,`hari`),
            KEY `fk_roster_jadwal` (`hari`,`kode_shift`),
            CONSTRAINT `fk_roster_jadwal` FOREIGN KEY (`hari`, `kode_shift`) REFERENCES `jadwal_kerja` (`hari_dalam_seminggu`, `nama_shift`) ON UPDATE CASCADE,
            CONSTRAINT `fk_roster_karyawan` FOREIGN KEY (`id_karyawan`) REFERENCES `karyawan` (`id_karyawan`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `jadwal_mingguan_karyawan`
    """
