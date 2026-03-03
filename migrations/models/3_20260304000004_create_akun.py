from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `akun` (
            `username` varchar(50) NOT NULL,
            `passwd` varchar(50) NOT NULL,
            `roles` enum('admin','owner','karyawan') NOT NULL,
            `last_login` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            `id_karyawan` varchar(10) NOT NULL,
            `device_id` text DEFAULT NULL,
            `status` enum('aktif','nonaktif') NOT NULL,
            PRIMARY KEY (`username`),
            KEY `fk_akun_karyawan` (`id_karyawan`),
            CONSTRAINT `fk_akun_karyawan` FOREIGN KEY (`id_karyawan`) REFERENCES `karyawan` (`id_karyawan`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `akun`
    """
