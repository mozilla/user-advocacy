
CREATE TABLE IF NOT EXISTS `daily_heartbeat_stats` (
  `id`                       int(11)                                   NOT NULL AUTO_INCREMENT,
  `survey_id`                varchar(100)                              NOT NULL,
  `question_id`              varchar(50)                               NOT NULL,
  `question_text`            varchar(500)                              NOT NULL,
  `date`                     date                                      NOT NULL,
  `channel`                  varchar(50)                               NOT NULL,
  `version`                  varchar(50)                               NOT NULL,
  `platform`                 varchar(50)                               NOT NULL,
  `max_score`                double                                    DEFAULT NULL,
  `is_response`              bool                                      NOT NULL,
  `score`                    double                                    DEFAULT NULL,
  `volume`                   int(11)                                   NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`id`, `survey_id`, `question_id`, `question_text`, 
        `date`, `channel`, `version`, `platform`, `max_score`, `is_response`, 
        `score`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `daily_desktop_stats` (
  `id`                       int(11)                                   NOT NULL AUTO_INCREMENT,
  `date`                     date                                      NOT NULL,
  `version`                  int(11)                                   NOT NULL,
  `channel`                  enum('Release','Beta','Aurora','Nightly') DEFAULT NULL,
  `input_average`            float                                     DEFAULT NULL,
  `input_volume`             int(11)                                   DEFAULT NULL,
  `sumo_posts`               int(11)                                   DEFAULT NULL,
  `sumo_unanswered_3_days`   int(11)                                   DEFAULT NULL,
  `sumo_in_product_views`    int(11)                                   DEFAULT NULL,
  `adis`                     int(11)                                   DEFAULT NULL,
  `heartbeat_average`        float                                     DEFAULT NULL,
  `heartbeat_response_rate`  float                                     DEFAULT NULL,
  `heartbeat_volume`         int(11)                                   DEFAULT NULL,
  `heartbeat_surveyed_users` int(11)                                   DEFAULT NULL,
  `input_average_7_days`     float                                     DEFAULT NULL,
  `days_since_epoch`         int(11)                                   DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`date`,`version`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `daily_mobile_stats` (
  `id`                       int(11)                                   NOT NULL AUTO_INCREMENT,
  `date`                     date                                      NOT NULL,
  `version`                  int(11)                                   NOT NULL,
  `channel`                  enum('Release','Beta','Aurora','Nightly') DEFAULT NULL,
  `input_average`            float                                     DEFAULT NULL,
  `input_volume`             int(11)                                   DEFAULT NULL,
  `sumo_posts`               int(11)                                   DEFAULT NULL,
  `sumo_unanswered_3_days`   int(11)                                   DEFAULT NULL,
  `sumo_in_product_views`    int(11)                                   DEFAULT NULL,
  `adis`                     int(11)                                   DEFAULT NULL,
  `play_average`             float                                     DEFAULT NULL,
  `play_volume`              int(11)                                   DEFAULT NULL,
  `heartbeat_average`        float                                     DEFAULT NULL,
  `heartbeat_volume`         int(11)                                   DEFAULT NULL,
  `input_average_7_days`     float                                     DEFAULT NULL,
  `days_since_epoch`         int(11)                                   DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`date`,`version`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1;