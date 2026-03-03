from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `absensi` (
            `id_absensi` int(11) NOT NULL AUTO_INCREMENT,
            `id_karyawan` varchar(10) NOT NULL,
            `tanggal_absen` timestamp NOT NULL DEFAULT current_timestamp(),
            `check_in` datetime NOT NULL,
            `check_out` datetime DEFAULT NULL,
            `latitude_checkin` double NOT NULL DEFAULT -999,
            `longitude_checkin` double NOT NULL DEFAULT -999,
            `latitude_checkout` double DEFAULT NULL,
            `longitude_checkout` double DEFAULT NULL,
            `foto_checkin` text NOT NULL COMMENT 'tampung url foto',
            `foto_checkout` text DEFAULT NULL,
            `pengajuan` enum('hadir','cuti','sakit','izin') NOT NULL DEFAULT 'hadir',
            `is_telat` tinyint(1) NOT NULL DEFAULT 0,
            `status_absen` enum('pending','approved','rejected') NOT NULL DEFAULT 'pending',
            `alasan_penolakan` varchar(50) DEFAULT NULL,
            PRIMARY KEY (`id_absensi`),
            KEY `fk_absensi_karyawan` (`id_karyawan`),
            CONSTRAINT `fk_absensi_karyawan` FOREIGN KEY (`id_karyawan`) REFERENCES `karyawan` (`id_karyawan`) ON DELETE CASCADE,
            CONSTRAINT `chk_absensi_checkout_after_checkin` CHECK (`check_out` is null or `check_out` >= `check_in`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `absensi`
    """
