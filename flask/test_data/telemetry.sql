-- MySQL dump 10.13  Distrib 5.5.40, for debian-linux-gnu (x86_64)
--
-- Host: advocacy-ro-vip.db.phx1.mozilla.com    Database: telemetry
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
-- Table structure for table `telemetry_elements`
--

DROP TABLE IF EXISTS `telemetry_elements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `telemetry_elements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `category` varchar(200) NOT NULL DEFAULT '',
  `description` text,
  `screen_id` int(11) DEFAULT NULL,
  `x` int(11) DEFAULT NULL,
  `y` int(11) DEFAULT NULL,
  `width` int(11) DEFAULT NULL,
  `height` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`name`),
  KEY `screen_id` (`screen_id`),
  CONSTRAINT `telemetry_measures_ibfk_2` FOREIGN KEY (`screen_id`) REFERENCES `telemetry_screens` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=183 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `telemetry_elements`
--

LOCK TABLES `telemetry_elements` WRITE;
/*!40000 ALTER TABLE `telemetry_elements` DISABLE KEYS */;
-- INSERT INTO `telemetry_elements` VALUES (...);
/*!40000 ALTER TABLE `telemetry_elements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `telemetry_measures`
--

DROP TABLE IF EXISTS `telemetry_measures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `telemetry_measures` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `type` enum('int','bucket','bool','str') DEFAULT NULL,
  `table` varchar(200) NOT NULL DEFAULT '',
  `sort` int(11) DEFAULT '1000',
  `element_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`name`),
  KEY `telemetry_measures_element_id` (`element_id`),
  CONSTRAINT `telemetry_measures_element_id` FOREIGN KEY (`element_id`) REFERENCES `telemetry_elements` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=113 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `telemetry_measures`
--

LOCK TABLES `telemetry_measures` WRITE;
/*!40000 ALTER TABLE `telemetry_measures` DISABLE KEYS */;
-- INSERT INTO `telemetry_measures` VALUES (...);
/*!40000 ALTER TABLE `telemetry_measures` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `telemetry_screens`
--

DROP TABLE IF EXISTS `telemetry_screens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `telemetry_screens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `file` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `telemetry_screens`
--

LOCK TABLES `telemetry_screens` WRITE;
/*!40000 ALTER TABLE `telemetry_screens` DISABLE KEYS */;
/*!40000 ALTER TABLE `telemetry_screens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `weekly_telemetry_stats`
--

DROP TABLE IF EXISTS `weekly_telemetry_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `weekly_telemetry_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `version` int(11) DEFAULT NULL,
  `week` date NOT NULL,
  `os` enum('windows','mac','linux') DEFAULT NULL,
  `channel` enum('release','beta','nightly','aurora') DEFAULT NULL,
  `measure_id` int(11) DEFAULT NULL,
  `measure_name` varchar(200) DEFAULT NULL,
  `measure_value` varchar(200) DEFAULT NULL,
  `measure_average` float DEFAULT NULL,
  `measure_nonzero_average` float DEFAULT NULL,
  `users` int(11) DEFAULT '0',
  `active_users` int(11) DEFAULT NULL,
  `potential_users` int(11) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`version`,`week`,`os`,`channel`,`measure_name`,`measure_value`),
  KEY `measure_id` (`measure_id`),
  CONSTRAINT `weekly_telemetry_stats_ibfk_1` FOREIGN KEY (`measure_id`) REFERENCES `telemetry_measures` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=678404 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `weekly_telemetry_stats`
--

LOCK TABLES `weekly_telemetry_stats` WRITE;
/*!40000 ALTER TABLE `weekly_telemetry_stats` DISABLE KEYS */;
-- INSERT INTO `weekly_telemetry_stats` VALUES (...);
/*!40000 ALTER TABLE `weekly_telemetry_stats` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-07-07 22:19:26
