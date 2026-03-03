from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `pengajuan_absen` (
            `id_pengajuan` int(3) NOT NULL AUTO_INCREMENT,
            `id_karyawan` varchar(10) NOT NULL,
            `tipe_pengajuan` enum('sakit','izin','cuti') NOT NULL,
            `tanggal_mulai` date NOT NULL,
            `tanggal_akhir` date NOT NULL,
            `foto_lampiran` text DEFAULT NULL,
            `keterangan` text NOT NULL,
            `status` enum('pending','approved','rejected') NOT NULL DEFAULT 'pending' COMMENT 'status pengajuan cuti',
            `alasan_penolakan` text DEFAULT NULL,
            PRIMARY KEY (`id_pengajuan`),
            UNIQUE KEY `uk_karyawan_tanggal` (`id_karyawan`,`tanggal_mulai`),
            KEY `fk_pengajuan_karyawan` (`id_karyawan`),
            CONSTRAINT `fk_pengajuan_karyawan` FOREIGN KEY (`id_karyawan`) REFERENCES `karyawan` (`id_karyawan`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `pengajuan_absen`
    """
