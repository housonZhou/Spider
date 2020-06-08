CREATE TABLE `spider_zhengce_gov` (
  `id` int(11) NOT NULL DEFAULT '0',
  `row_id` varchar(45) NOT NULL,
  `content` longtext,
  `website` varchar(100) DEFAULT NULL,
  `source_module` varchar(100) DEFAULT NULL,
  `url` longtext,
  `title` longtext,
  `classify` varchar(100) DEFAULT NULL,
  `source` varchar(200) DEFAULT NULL,
  `file_type` varchar(30) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `publish_time` varchar(100) DEFAULT NULL,
  `html_content` longtext,
  `extension` longtext,
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `remark` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

