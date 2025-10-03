-- MySQL dump 10.13  Distrib 8.0.42, for macos15.2 (arm64)
--
-- Host: localhost    Database: lookbookSVELTE
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bridge_order_promotion`
--

DROP TABLE IF EXISTS `bridge_order_promotion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bridge_order_promotion` (
  `order_id` bigint NOT NULL,
  `promo_sk` bigint NOT NULL,
  PRIMARY KEY (`order_id`,`promo_sk`),
  KEY `ix_bop_promo` (`promo_sk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bridge_product_category`
--

DROP TABLE IF EXISTS `bridge_product_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bridge_product_category` (
  `product_id` bigint NOT NULL,
  `category_id` bigint NOT NULL,
  `position` int DEFAULT NULL,
  PRIMARY KEY (`product_id`,`category_id`),
  KEY `ix_bpc_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bridge_product_relation`
--

DROP TABLE IF EXISTS `bridge_product_relation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bridge_product_relation` (
  `parent_product_id` bigint NOT NULL,
  `child_product_id` bigint NOT NULL,
  `link_type` varchar(32) NOT NULL,
  PRIMARY KEY (`parent_product_id`,`child_product_id`,`link_type`),
  KEY `ix_bpr_child` (`child_product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `category_affinity`
--

DROP TABLE IF EXISTS `category_affinity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `category_affinity` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `customer_id` bigint NOT NULL,
  `category_id` bigint NOT NULL,
  `score_decayed` double NOT NULL,
  `probability` double NOT NULL,
  `event_span_days` int NOT NULL,
  `events_count` int NOT NULL,
  `last_event_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_customer_category` (`customer_id`,`category_id`),
  KEY `idx_customer` (`customer_id`),
  KEY `idx_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `category_affinity_run_log`
--

DROP TABLE IF EXISTS `category_affinity_run_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `category_affinity_run_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `started_at` datetime NOT NULL,
  `finished_at` datetime DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `rows_written` int DEFAULT '0',
  `decay_half_life_days` int NOT NULL,
  `purchase_weight` double NOT NULL,
  `atc_weight` double NOT NULL,
  `view_weight` double NOT NULL,
  `notes` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chat_messages`
--

DROP TABLE IF EXISTS `chat_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` varchar(36) NOT NULL,
  `message` text NOT NULL,
  `response` text,
  `outfit_ids` json DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `processing_time_ms` decimal(8,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_timestamp` (`timestamp`),
  CONSTRAINT `chat_messages_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chat_sessions`
--

DROP TABLE IF EXISTS `chat_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_sessions` (
  `id` varchar(36) NOT NULL,
  `user_id` varchar(100) DEFAULT NULL,
  `started_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_activity` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `context` json DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_last_activity` (`last_activity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_analytics`
--

DROP TABLE IF EXISTS `customer_analytics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_analytics` (
  `customer_id` int NOT NULL,
  `email` varchar(255) NOT NULL,
  `first_name` varchar(100) DEFAULT NULL,
  `last_name` varchar(100) DEFAULT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `customer_created_at` timestamp NULL DEFAULT NULL,
  `customer_updated_at` timestamp NULL DEFAULT NULL,
  `customer_group_id` int DEFAULT NULL,
  `customer_group_name` varchar(100) DEFAULT NULL,
  `billing_city` varchar(100) DEFAULT NULL,
  `billing_region` varchar(100) DEFAULT NULL,
  `billing_postcode` varchar(20) DEFAULT NULL,
  `billing_country` varchar(100) DEFAULT NULL,
  `shipping_city` varchar(100) DEFAULT NULL,
  `shipping_region` varchar(100) DEFAULT NULL,
  `shipping_postcode` varchar(20) DEFAULT NULL,
  `shipping_country` varchar(100) DEFAULT NULL,
  `order_count` int DEFAULT '0',
  `first_order_at` timestamp NULL DEFAULT NULL,
  `last_order_at` timestamp NULL DEFAULT NULL,
  `lifetime_gross_amount` decimal(12,2) DEFAULT '0.00',
  `lifetime_net_amount` decimal(12,2) DEFAULT '0.00',
  `last_order_status` varchar(50) DEFAULT NULL,
  `preferred_currency` varchar(10) DEFAULT NULL,
  `store_id` int DEFAULT NULL,
  `store_name` varchar(255) DEFAULT NULL,
  `newsletter_subscribed` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`customer_id`),
  KEY `idx_email` (`email`),
  KEY `idx_customer_group_id` (`customer_group_id`),
  KEY `idx_store_id` (`store_id`),
  KEY `idx_order_count` (`order_count`),
  KEY `idx_lifetime_gross` (`lifetime_gross_amount`),
  KEY `idx_last_order_at` (`last_order_at`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_price_stats`
--

DROP TABLE IF EXISTS `customer_price_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_price_stats` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `customer_id` bigint NOT NULL,
  `median_price` decimal(12,2) NOT NULL,
  `p95_price` decimal(12,2) NOT NULL,
  `avg_price` decimal(12,2) NOT NULL,
  `orders_count` int NOT NULL,
  `window_days` int NOT NULL,
  `last_order_at` datetime DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `customer_id` (`customer_id`),
  KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_segment_map`
--

DROP TABLE IF EXISTS `customer_segment_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_segment_map` (
  `customer_id` bigint NOT NULL,
  `segment_id` varchar(64) NOT NULL,
  `assigned_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `reason` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `first_name` varchar(100) DEFAULT NULL,
  `last_name` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` enum('male','female','other','prefer_not_to_say') DEFAULT NULL,
  `preferences` json DEFAULT (_utf8mb4'{}'),
  `marketing_opt_in` tinyint(1) DEFAULT '0',
  `account_status` enum('active','inactive','suspended') DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_login_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_email` (`email`),
  KEY `idx_account_status` (`account_status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_last_login_at` (`last_login_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_carrier`
--

DROP TABLE IF EXISTS `dim_carrier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_carrier` (
  `carrier_code` varchar(64) NOT NULL,
  `carrier_title` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`carrier_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_category`
--

DROP TABLE IF EXISTS `dim_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_category` (
  `category_id` bigint NOT NULL,
  `parent_id` bigint DEFAULT NULL,
  `level` int DEFAULT NULL,
  `path` varchar(255) DEFAULT NULL,
  `position` int DEFAULT NULL,
  `is_active` tinyint DEFAULT NULL,
  `url_key` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `store_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `uk_category_store` (`category_id`,`store_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_customer_address`
--

DROP TABLE IF EXISTS `dim_customer_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_customer_address` (
  `address_id` bigint NOT NULL,
  `customer_id` bigint NOT NULL,
  `firstname` varchar(255) DEFAULT NULL,
  `lastname` varchar(255) DEFAULT NULL,
  `company` varchar(255) DEFAULT NULL,
  `telephone` varchar(64) DEFAULT NULL,
  `street` text,
  `city` varchar(255) DEFAULT NULL,
  `region` varchar(255) DEFAULT NULL,
  `postcode` varchar(64) DEFAULT NULL,
  `country_id` varchar(2) DEFAULT NULL,
  `is_default_billing` tinyint DEFAULT NULL,
  `is_default_shipping` tinyint DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`address_id`),
  KEY `ix_dca_customer` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_media_asset`
--

DROP TABLE IF EXISTS `dim_media_asset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_media_asset` (
  `media_id` bigint NOT NULL AUTO_INCREMENT,
  `product_id` bigint NOT NULL,
  `image_key` varchar(512) DEFAULT NULL,
  `label` varchar(255) DEFAULT NULL,
  `position` int DEFAULT NULL,
  `media_type` varchar(64) DEFAULT NULL,
  `is_base` tinyint DEFAULT NULL,
  `is_small` tinyint DEFAULT NULL,
  `is_thumbnail` tinyint DEFAULT NULL,
  PRIMARY KEY (`media_id`),
  UNIQUE KEY `uk_media` (`product_id`,`image_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_payment_method`
--

DROP TABLE IF EXISTS `dim_payment_method`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_payment_method` (
  `method_code` varchar(64) NOT NULL,
  `method_title` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`method_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_product`
--

DROP TABLE IF EXISTS `dim_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_product` (
  `product_id` bigint NOT NULL,
  `sku` varchar(255) DEFAULT NULL,
  `type_id` varchar(32) DEFAULT NULL,
  `status` int DEFAULT NULL,
  `visibility` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `name` text,
  `description` text,
  `brand` varchar(255) DEFAULT NULL,
  `size_range` varchar(255) DEFAULT NULL,
  `material` varchar(255) DEFAULT NULL,
  `pattern` varchar(255) DEFAULT NULL,
  `style` varchar(255) DEFAULT NULL,
  `season` varchar(255) DEFAULT NULL,
  `occasion` varchar(255) DEFAULT NULL,
  `fit` varchar(255) DEFAULT NULL,
  `care_instructions` text,
  `url_key` varchar(255) DEFAULT NULL,
  `image_key` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`product_id`),
  UNIQUE KEY `sku` (`sku`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_promotion`
--

DROP TABLE IF EXISTS `dim_promotion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_promotion` (
  `promo_sk` bigint NOT NULL AUTO_INCREMENT,
  `rule_id` bigint DEFAULT NULL,
  `coupon_id` bigint NOT NULL DEFAULT '0',
  `rule_name` varchar(255) DEFAULT NULL,
  `rule_type` enum('cart','catalog') DEFAULT 'cart',
  `coupon_code` varchar(255) DEFAULT NULL,
  `from_date` date DEFAULT NULL,
  `to_date` date DEFAULT NULL,
  `is_active` tinyint DEFAULT NULL,
  PRIMARY KEY (`promo_sk`),
  UNIQUE KEY `uk_rule_coupon` (`rule_id`,`coupon_id`)
) ENGINE=InnoDB AUTO_INCREMENT=208 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_store`
--

DROP TABLE IF EXISTS `dim_store`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_store` (
  `store_id` int NOT NULL,
  `code` varchar(64) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `group_id` int DEFAULT NULL,
  `website_id` int DEFAULT NULL,
  `is_active` tinyint DEFAULT NULL,
  PRIMARY KEY (`store_id`),
  KEY `ix_ds_group` (`group_id`),
  KEY `ix_ds_website` (`website_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_store_group`
--

DROP TABLE IF EXISTS `dim_store_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_store_group` (
  `group_id` int NOT NULL,
  `website_id` int DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `root_category_id` bigint DEFAULT NULL,
  `default_store_id` int DEFAULT NULL,
  PRIMARY KEY (`group_id`),
  KEY `ix_dsg_website` (`website_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dim_store_website`
--

DROP TABLE IF EXISTS `dim_store_website`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dim_store_website` (
  `website_id` int NOT NULL,
  `code` varchar(64) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `default_group_id` int DEFAULT NULL,
  `sort_order` int DEFAULT NULL,
  `is_default` tinyint DEFAULT NULL,
  PRIMARY KEY (`website_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_creditmemo`
--

DROP TABLE IF EXISTS `fact_creditmemo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_creditmemo` (
  `creditmemo_id` bigint NOT NULL,
  `order_id` bigint NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `base_grand_total` decimal(18,4) DEFAULT NULL,
  `base_tax_amount` decimal(18,4) DEFAULT NULL,
  `base_discount_amount` decimal(18,4) DEFAULT NULL,
  PRIMARY KEY (`creditmemo_id`),
  KEY `ix_fcm_order` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_creditmemo_item`
--

DROP TABLE IF EXISTS `fact_creditmemo_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_creditmemo_item` (
  `creditmemo_item_id` bigint NOT NULL,
  `creditmemo_id` bigint NOT NULL,
  `order_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  `qty` decimal(18,4) DEFAULT NULL,
  `base_price` decimal(18,4) DEFAULT NULL,
  `base_row_total` decimal(18,4) DEFAULT NULL,
  `base_tax_amount` decimal(18,4) DEFAULT NULL,
  `base_discount_amount` decimal(18,4) DEFAULT NULL,
  PRIMARY KEY (`creditmemo_item_id`),
  KEY `ix_fcmi_cm` (`creditmemo_id`),
  KEY `ix_fcmi_product` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_customer_activity`
--

DROP TABLE IF EXISTS `fact_customer_activity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_customer_activity` (
  `activity_id` bigint NOT NULL AUTO_INCREMENT,
  `customer_id` bigint DEFAULT NULL,
  `event_type` varchar(64) DEFAULT NULL,
  `event_ts` timestamp NULL DEFAULT NULL,
  `reference_id` bigint DEFAULT NULL,
  `metadata` json DEFAULT NULL,
  PRIMARY KEY (`activity_id`),
  KEY `ix_fca_customer` (`customer_id`),
  KEY `ix_fca_event` (`event_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_inventory_daily_snapshot`
--

DROP TABLE IF EXISTS `fact_inventory_daily_snapshot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_inventory_daily_snapshot` (
  `snapshot_date` date NOT NULL,
  `product_id` bigint NOT NULL,
  `store_id` int DEFAULT NULL,
  `source_code` varchar(64) NOT NULL DEFAULT 'default',
  `qty` decimal(18,4) DEFAULT NULL,
  `is_in_stock` tinyint DEFAULT NULL,
  `backorders` tinyint DEFAULT NULL,
  `min_sale_qty` decimal(18,4) DEFAULT NULL,
  `max_sale_qty` decimal(18,4) DEFAULT NULL,
  PRIMARY KEY (`snapshot_date`,`product_id`,`source_code`),
  KEY `ix_inv_product` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_invoice`
--

DROP TABLE IF EXISTS `fact_invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_invoice` (
  `invoice_id` bigint NOT NULL,
  `order_id` bigint NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `base_grand_total` decimal(18,4) DEFAULT NULL,
  `base_subtotal` decimal(18,4) DEFAULT NULL,
  `base_tax_amount` decimal(18,4) DEFAULT NULL,
  `base_discount_amount` decimal(18,4) DEFAULT NULL,
  PRIMARY KEY (`invoice_id`),
  KEY `ix_fi_order` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_invoice_item`
--

DROP TABLE IF EXISTS `fact_invoice_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_invoice_item` (
  `invoice_item_id` bigint NOT NULL,
  `invoice_id` bigint NOT NULL,
  `order_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  `qty` decimal(18,4) DEFAULT NULL,
  `base_price` decimal(18,4) DEFAULT NULL,
  `base_row_total` decimal(18,4) DEFAULT NULL,
  `base_tax_amount` decimal(18,4) DEFAULT NULL,
  `base_discount_amount` decimal(18,4) DEFAULT NULL,
  PRIMARY KEY (`invoice_item_id`),
  KEY `ix_fii_invoice` (`invoice_id`),
  KEY `ix_fii_product` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_loyalty_wallet`
--

DROP TABLE IF EXISTS `fact_loyalty_wallet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_loyalty_wallet` (
  `entry_id` bigint NOT NULL,
  `customer_id` bigint NOT NULL,
  `program_type` enum('giftcard','store_credit','points') NOT NULL,
  `txn_type` varchar(64) DEFAULT NULL,
  `amount` decimal(18,4) DEFAULT NULL,
  `points` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `reference` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`entry_id`),
  KEY `ix_flw_customer` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_marketing_attribution`
--

DROP TABLE IF EXISTS `fact_marketing_attribution`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_marketing_attribution` (
  `order_id` bigint NOT NULL,
  `source` varchar(255) DEFAULT NULL,
  `medium` varchar(255) DEFAULT NULL,
  `campaign` varchar(255) DEFAULT NULL,
  `term` varchar(255) DEFAULT NULL,
  `content` varchar(255) DEFAULT NULL,
  `first_touch` json DEFAULT NULL,
  `last_touch` json DEFAULT NULL,
  `model` varchar(64) DEFAULT 'last_click',
  PRIMARY KEY (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_order_header`
--

DROP TABLE IF EXISTS `fact_order_header`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_order_header` (
  `order_id` bigint NOT NULL,
  `order_number` varchar(64) DEFAULT NULL,
  `customer_id` bigint DEFAULT NULL,
  `store_id` int DEFAULT NULL,
  `status` varchar(64) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `base_currency_code` varchar(8) DEFAULT NULL,
  `base_grand_total` decimal(18,4) DEFAULT NULL,
  `base_subtotal` decimal(18,4) DEFAULT NULL,
  `base_tax_amount` decimal(18,4) DEFAULT NULL,
  `base_discount_amount` decimal(18,4) DEFAULT NULL,
  `shipping_amount` decimal(18,4) DEFAULT NULL,
  `coupon_code` varchar(255) DEFAULT NULL,
  `applied_rule_ids` text,
  PRIMARY KEY (`order_id`),
  KEY `ix_foh_customer` (`customer_id`),
  KEY `ix_foh_store` (`store_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_order_item`
--

DROP TABLE IF EXISTS `fact_order_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_order_item` (
  `order_item_id` bigint NOT NULL,
  `order_id` bigint NOT NULL,
  `product_id` bigint DEFAULT NULL,
  `sku` varchar(255) DEFAULT NULL,
  `name` varchar(512) DEFAULT NULL,
  `qty_ordered` decimal(18,4) DEFAULT NULL,
  `qty_invoiced` decimal(18,4) DEFAULT NULL,
  `qty_shipped` decimal(18,4) DEFAULT NULL,
  `base_price` decimal(18,4) DEFAULT NULL,
  `base_row_total` decimal(18,4) DEFAULT NULL,
  `base_tax_amount` decimal(18,4) DEFAULT NULL,
  `base_discount_amount` decimal(18,4) DEFAULT NULL,
  PRIMARY KEY (`order_item_id`),
  KEY `ix_foi_order` (`order_id`),
  KEY `ix_foi_product` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_payment_transaction`
--

DROP TABLE IF EXISTS `fact_payment_transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_payment_transaction` (
  `transaction_id` bigint NOT NULL,
  `order_id` bigint NOT NULL,
  `method_code` varchar(64) DEFAULT NULL,
  `txn_type` varchar(64) DEFAULT NULL,
  `amount` decimal(18,4) DEFAULT NULL,
  `is_closed` tinyint DEFAULT NULL,
  `parent_txn_id` varchar(255) DEFAULT NULL,
  `last_trans_id` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`transaction_id`),
  KEY `ix_fpt_order` (`order_id`),
  KEY `ix_fpt_method` (`method_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_price_snapshot`
--

DROP TABLE IF EXISTS `fact_price_snapshot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_price_snapshot` (
  `snapshot_date` date NOT NULL,
  `product_id` bigint NOT NULL,
  `store_id` int NOT NULL,
  `list_price` decimal(18,4) DEFAULT NULL,
  `special_price` decimal(18,4) DEFAULT NULL,
  `special_from_date` date DEFAULT NULL,
  `special_to_date` date DEFAULT NULL,
  `tier_price_min` decimal(18,4) DEFAULT NULL,
  `effective_price` decimal(18,4) DEFAULT NULL,
  PRIMARY KEY (`snapshot_date`,`product_id`,`store_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_shipment`
--

DROP TABLE IF EXISTS `fact_shipment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_shipment` (
  `shipment_id` bigint NOT NULL,
  `order_id` bigint NOT NULL,
  `shipped_at` timestamp NULL DEFAULT NULL,
  `total_qty` decimal(18,4) DEFAULT NULL,
  `carrier_code` varchar(64) DEFAULT NULL,
  `track_number` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`shipment_id`),
  KEY `ix_fs_order` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fact_shipment_item`
--

DROP TABLE IF EXISTS `fact_shipment_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fact_shipment_item` (
  `shipment_item_id` bigint NOT NULL,
  `shipment_id` bigint NOT NULL,
  `order_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  `qty` decimal(18,4) DEFAULT NULL,
  PRIMARY KEY (`shipment_item_id`),
  KEY `ix_fsi_shipment` (`shipment_id`),
  KEY `ix_fsi_product` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `migration_history`
--

DROP TABLE IF EXISTS `migration_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `migration_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `migration_name` varchar(255) NOT NULL,
  `executed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `execution_time_ms` decimal(10,2) DEFAULT NULL,
  `success` tinyint(1) DEFAULT '1',
  `error_message` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `migration_name` (`migration_name`),
  KEY `idx_migration_name` (`migration_name`),
  KEY `idx_executed_at` (`executed_at`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_number` varchar(50) NOT NULL,
  `order_date` date NOT NULL,
  `order_datetime` datetime NOT NULL,
  `order_status` varchar(50) NOT NULL,
  `customer_id` int DEFAULT NULL,
  `customer_name` varchar(255) DEFAULT NULL,
  `customer_email` varchar(255) DEFAULT NULL,
  `customer_group_id` int DEFAULT NULL,
  `shipping_country` varchar(100) DEFAULT NULL,
  `shipping_region` varchar(100) DEFAULT NULL,
  `shipping_postcode` varchar(20) DEFAULT NULL,
  `product_name` varchar(500) DEFAULT NULL,
  `product_sku` varchar(100) DEFAULT NULL,
  `category_name` varchar(100) DEFAULT NULL,
  `category_id` int DEFAULT NULL,
  `value_id` int DEFAULT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `qty_invoiced` decimal(10,2) DEFAULT '0.00',
  `qty_shipped` decimal(10,2) DEFAULT '0.00',
  `total_price` decimal(10,2) NOT NULL,
  `unit_price_excl_tax` decimal(10,2) DEFAULT NULL,
  `total_price_incl_tax` decimal(10,2) DEFAULT NULL,
  `discount_amount` decimal(10,2) DEFAULT '0.00',
  `tax_amount` decimal(10,2) DEFAULT '0.00',
  `avg_price_per_unit` decimal(10,2) DEFAULT NULL,
  `store_id` int DEFAULT NULL,
  `store_name` varchar(255) DEFAULT NULL,
  `currency` varchar(10) DEFAULT 'USD',
  `order_grand_total` decimal(10,2) DEFAULT NULL,
  `order_subtotal` decimal(10,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_order_number` (`order_number`),
  KEY `idx_order_date` (`order_date`),
  KEY `idx_order_status` (`order_status`),
  KEY `idx_customer_id` (`customer_id`),
  KEY `idx_customer_email` (`customer_email`),
  KEY `idx_product_sku` (`product_sku`),
  KEY `idx_category_name` (`category_name`),
  KEY `idx_store_id` (`store_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=1211 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `outfit_items`
--

DROP TABLE IF EXISTS `outfit_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `outfit_items` (
  `outfit_id` int NOT NULL,
  `product_id` int NOT NULL,
  `sku` varchar(100) NOT NULL,
  `role` enum('top','bottom','outer','shoes','accessory','undergarment') NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`outfit_id`,`product_id`),
  KEY `idx_outfit_id` (`outfit_id`),
  KEY `idx_product_id` (`product_id`),
  KEY `idx_role` (`role`),
  CONSTRAINT `outfit_items_ibfk_1` FOREIGN KEY (`outfit_id`) REFERENCES `outfits` (`id`) ON DELETE CASCADE,
  CONSTRAINT `outfit_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `outfits`
--

DROP TABLE IF EXISTS `outfits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `outfits` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(300) NOT NULL,
  `description` text,
  `rationale` text,
  `intent_tags` json DEFAULT NULL,
  `status` enum('draft','published','archived') DEFAULT 'draft',
  `score` decimal(3,2) DEFAULT '0.00',
  `total_price` decimal(10,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`),
  KEY `idx_score` (`score`),
  KEY `idx_total_price` (`total_price`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sku` varchar(100) NOT NULL,
  `title` varchar(500) NOT NULL,
  `description` text,
  `price` decimal(10,2) NOT NULL,
  `original_price` decimal(10,2) DEFAULT NULL,
  `size_range` varchar(100) DEFAULT NULL,
  `image_key` varchar(500) DEFAULT NULL,
  `attrs` json DEFAULT NULL,
  `status` enum('active','inactive','out_of_stock','discontinued') DEFAULT 'active',
  `in_stock` tinyint(1) DEFAULT '1',
  `stock_quantity` int DEFAULT NULL,
  `season` varchar(50) DEFAULT NULL,
  `url_key` varchar(500) DEFAULT NULL,
  `product_created_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`),
  KEY `idx_sku` (`sku`),
  KEY `idx_status` (`status`),
  KEY `idx_in_stock` (`in_stock`),
  KEY `idx_price` (`price`),
  KEY `idx_season` (`season`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_attrs_color` ((cast(json_unquote(json_extract(`attrs`,_utf8mb4'$.color')) as char(50) charset utf8mb4))),
  KEY `idx_attrs_category` ((cast(json_unquote(json_extract(`attrs`,_utf8mb4'$.category')) as char(50) charset utf8mb4))),
  KEY `idx_attrs_material` ((cast(json_unquote(json_extract(`attrs`,_utf8mb4'$.material')) as char(50) charset utf8mb4))),
  KEY `idx_attrs_pattern` ((cast(json_unquote(json_extract(`attrs`,_utf8mb4'$.pattern')) as char(50) charset utf8mb4))),
  KEY `idx_attrs_style` ((cast(json_unquote(json_extract(`attrs`,_utf8mb4'$.style')) as char(50) charset utf8mb4)))
) ENGINE=InnoDB AUTO_INCREMENT=15316 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rules`
--

DROP TABLE IF EXISTS `rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` text,
  `intent` varchar(100) NOT NULL,
  `constraints` json DEFAULT NULL,
  `priority` int DEFAULT '1',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_name_intent` (`name`,`intent`),
  KEY `idx_intent` (`intent`),
  KEY `idx_priority` (`priority`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `segment_price_stats`
--

DROP TABLE IF EXISTS `segment_price_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `segment_price_stats` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `segment_id` varchar(64) NOT NULL,
  `median_price` decimal(12,2) NOT NULL,
  `p95_price` decimal(12,2) NOT NULL,
  `avg_price` decimal(12,2) NOT NULL,
  `customers_count` int NOT NULL,
  `window_days` int NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_segment` (`segment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-28 13:42:21
