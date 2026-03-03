from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `karyawan` (
            `id_karyawan` varchar(10) NOT NULL COMMENT 'id unik krywn',
            `nama_karyawan` varchar(50) NOT NULL,
            `email_karyawan` varchar(50) DEFAULT NULL COMMENT 'opsional, klo direkrut ada email, isi',
            `nomor_hp` varchar(15) NOT NULL,
            `foto_profile` text NOT NULL,
            `tanggal_rekrut` date NOT NULL COMMENT 'tanggal bergabung ke perusahaan',
            `status` enum('aktif','nonaktif') NOT NULL COMMENT 'status karyawan',
            `id_departemen` int(3) NOT NULL COMMENT 'id departemen yang mengacu ke tabel departemen',
            `posisi` varchar(30) NOT NULL COMMENT 'posisi pekerjaannya',
            `jatah_cuti_tahunan` int(3) NOT NULL DEFAULT 12 COMMENT 'Kuota cuti individu',
            PRIMARY KEY (`id_karyawan`),
            KEY `fk_departemen` (`id_departemen`),
            KEY `id_karyawan` (`id_karyawan`),
            CONSTRAINT `fk_departemen` FOREIGN KEY (`id_departemen`) REFERENCES `departemen` (`id_departemen`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `karyawan`
    """
