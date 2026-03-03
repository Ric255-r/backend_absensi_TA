from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `departemen` (
            `id_departemen` int(3) NOT NULL AUTO_INCREMENT,
            `nama_departemen` varchar(50) NOT NULL,
            PRIMARY KEY (`id_departemen`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `departemen`
    """
