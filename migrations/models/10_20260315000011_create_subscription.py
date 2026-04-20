from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `subscription` (
            `id_subscription` int(11) NOT NULL AUTO_INCREMENT,
            `plan_name` varchar(100) NOT NULL DEFAULT 'default',
            `status` varchar(20) NOT NULL DEFAULT 'active',
            `start_at` datetime(6) NOT NULL,
            `end_at` datetime(6) NOT NULL,
            `expired_at` datetime(6) DEFAULT NULL,
            `notes` varchar(255) DEFAULT NULL,
            `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            PRIMARY KEY (`id_subscription`),
            KEY `idx_subscription_status_end_at` (`status`, `end_at`),
            KEY `idx_subscription_start_at` (`start_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `subscription`
    """
