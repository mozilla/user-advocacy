
CREATE TABLE IF NOT EXISTS `daily_desktop_stats` (
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
) ENGINE=InnoDB AUTO_INCREMENT=121908 DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `daily_mobile_stats` (
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
) ENGINE=InnoDB AUTO_INCREMENT=104980 DEFAULT CHARSET=latin1;