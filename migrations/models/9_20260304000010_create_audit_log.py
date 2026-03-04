from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `audit_log` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `actor_username` varchar(100) DEFAULT NULL,
            `actor_id_karyawan` varchar(20) DEFAULT NULL,
            `actor_role` varchar(50) DEFAULT NULL,
            `action` varchar(30) NOT NULL,
            `table_name` varchar(100) NOT NULL,
            `record_id` varchar(100) DEFAULT NULL,
            `before_data` JSON DEFAULT NULL,
            `after_data` JSON DEFAULT NULL,
            `metadata` JSON DEFAULT NULL,
            `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            PRIMARY KEY (`id`),
            KEY `idx_audit_table_record` (`table_name`, `record_id`),
            KEY `idx_audit_actor` (`actor_username`, `actor_id_karyawan`),
            KEY `idx_audit_created` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `audit_log`
    """
