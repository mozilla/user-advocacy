-- MySQL dump 10.13  Distrib 5.5.40, for debian-linux-gnu (x86_64)
--
-- Host: advocacy-ro-vip.db.phx1.mozilla.com    Database: sentiment
-- ------------------------------------------------------
-- Server version	5.6.17-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `daily_desktop_stats`
--

DROP TABLE IF EXISTS `daily_desktop_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daily_desktop_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `version` int(11) NOT NULL,
  `channel` enum('Release','Beta','Aurora','Nightly') DEFAULT NULL,
  `input_average` float DEFAULT NULL,
  `input_volume` int(11) DEFAULT NULL,
  `sumo_posts` int(11) DEFAULT NULL,
  `sumo_unanswered_3_days` int(11) DEFAULT NULL,
  `sumo_in_product_views` int(11) DEFAULT NULL,
  `adis` int(11) DEFAULT NULL,
  `heartbeat_average` float DEFAULT NULL,
  `heartbeat_response_rate` float DEFAULT NULL,
  `heartbeat_volume` int(11) DEFAULT NULL,
  `heartbeat_surveyed_users` int(11) DEFAULT NULL,
  `input_average_7_days` float DEFAULT NULL,
  `days_since_epoch` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`date`,`version`)
) ENGINE=InnoDB AUTO_INCREMENT=175850 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_desktop_stats`
--

LOCK TABLES `daily_desktop_stats` WRITE;
/*!40000 ALTER TABLE `daily_desktop_stats` DISABLE KEYS */;
-- INSERT INTO `daily_desktop_stats` VALUES (...);
/*!40000 ALTER TABLE `daily_desktop_stats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `daily_heartbeat_stats`
--

DROP TABLE IF EXISTS `daily_heartbeat_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daily_heartbeat_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `survey_id` varchar(100) NOT NULL,
  `question_id` varchar(50) NOT NULL,
  `question_text` varchar(500) NOT NULL,
  `date` date NOT NULL,
  `channel` varchar(50) NOT NULL,
  `version` varchar(50) NOT NULL,
  `platform` varchar(50) NOT NULL,
  `max_score` double DEFAULT NULL,
  `is_response` tinyint(1) NOT NULL,
  `score` double DEFAULT NULL,
  `volume` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`id`,`survey_id`,`question_id`,`question_text`,`date`,`channel`,`version`,`platform`,`max_score`,`is_response`,`score`)
) ENGINE=InnoDB AUTO_INCREMENT=146915 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_heartbeat_stats`
--

LOCK TABLES `daily_heartbeat_stats` WRITE;
/*!40000 ALTER TABLE `daily_heartbeat_stats` DISABLE KEYS */;
-- INSERT INTO `daily_heartbeat_stats` VALUES (...);
/*!40000 ALTER TABLE `daily_heartbeat_stats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `daily_mobile_stats`
--

DROP TABLE IF EXISTS `daily_mobile_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daily_mobile_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `version` int(11) NOT NULL,
  `channel` enum('Release','Beta','Aurora','Nightly') DEFAULT NULL,
  `input_average` float DEFAULT NULL,
  `input_volume` int(11) DEFAULT NULL,
  `sumo_posts` int(11) DEFAULT NULL,
  `sumo_unanswered_3_days` int(11) DEFAULT NULL,
  `sumo_in_product_views` int(11) DEFAULT NULL,
  `adis` int(11) DEFAULT NULL,
  `play_average` float DEFAULT NULL,
  `play_volume` int(11) DEFAULT NULL,
  `heartbeat_average` float DEFAULT NULL,
  `heartbeat_volume` int(11) DEFAULT NULL,
  `input_average_7_days` float DEFAULT NULL,
  `days_since_epoch` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`date`,`version`)
) ENGINE=InnoDB AUTO_INCREMENT=107051 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_mobile_stats`
--

LOCK TABLES `daily_mobile_stats` WRITE;
/*!40000 ALTER TABLE `daily_mobile_stats` DISABLE KEYS */;
-- INSERT INTO `daily_mobile_stats` VALUES (...);
/*!40000 ALTER TABLE `daily_mobile_stats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `daily_product_stats`
--

DROP TABLE IF EXISTS `daily_product_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daily_product_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `version` int(11) NOT NULL,
  `channel` enum('Release','Beta','Aurora','Nightly') DEFAULT NULL,
  `product` enum('Firefox','Firefox for Android') DEFAULT NULL,
  `input_average` float DEFAULT NULL,
  `input_volume` int(11) DEFAULT NULL,
  `input_average_7_days` float DEFAULT NULL,
  `sumo_posts` int(11) DEFAULT NULL,
  `sumo_unanswered_3_days` int(11) DEFAULT NULL,
  `sumo_in_product_views` int(11) DEFAULT NULL,
  `adis` int(11) DEFAULT NULL,
  `heartbeat_average` float DEFAULT NULL,
  `heartbeat_volume` int(11) DEFAULT NULL,
  `heartbeat_response_rate` float DEFAULT NULL,
  `heartbeat_surveyed_users` int(11) DEFAULT NULL,
  `play_average` float DEFAULT NULL,
  `play_volume` int(11) DEFAULT NULL,
  `days_since_epoch` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`date`,`version`,`channel`,`product`)
) ENGINE=InnoDB AUTO_INCREMENT=180041 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_product_stats`
--

LOCK TABLES `daily_product_stats` WRITE;
/*!40000 ALTER TABLE `daily_product_stats` DISABLE KEYS */;
-- INSERT INTO `daily_product_stats` VALUES (...);
/*!40000 ALTER TABLE `daily_product_stats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `google_play_reviews`
--

DROP TABLE IF EXISTS `google_play_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `google_play_reviews` (
  `created` bigint(20) NOT NULL,
  `date` date DEFAULT NULL,
  `version` int(11) DEFAULT NULL,
  `language` text,
  `model` text,
  `rating` int(11) DEFAULT NULL,
  `title` text,
  `description` text,
  PRIMARY KEY (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `google_play_reviews`
--

LOCK TABLES `google_play_reviews` WRITE;
/*!40000 ALTER TABLE `google_play_reviews` DISABLE KEYS */;
-- INSERT INTO `google_play_reviews` VALUES (...);
/*!40000 ALTER TABLE `google_play_reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `min_release_info`
--

DROP TABLE IF EXISTS `min_release_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `min_release_info` (
  `version` int(11) NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `is_esr` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `min_release_info`
--

LOCK TABLES `min_release_info` WRITE;
/*!40000 ALTER TABLE `min_release_info` DISABLE KEYS */;
-- INSERT INTO `min_release_info` VALUES (...);
/*!40000 ALTER TABLE `min_release_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `release_info`
--

DROP TABLE IF EXISTS `release_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `release_info` (
  `version` int(11) NOT NULL,
  `release_start_date` date DEFAULT NULL,
  `release_end_date` date DEFAULT NULL,
  `beta_start_date` date DEFAULT NULL,
  `beta_end_date` date DEFAULT NULL,
  `aurora_start_date` date DEFAULT NULL,
  `aurora_end_date` date DEFAULT NULL,
  `nightly_start_date` date DEFAULT NULL,
  `nightly_end_date` date DEFAULT NULL,
  `is_esr` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `release_info`
--

LOCK TABLES `release_info` WRITE;
/*!40000 ALTER TABLE `release_info` DISABLE KEYS */;
-- INSERT INTO `release_info` VALUES (...);
/*!40000 ALTER TABLE `release_info` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-07-07 22:19:49
