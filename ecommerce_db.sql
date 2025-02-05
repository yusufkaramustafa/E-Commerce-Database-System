-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Jan 05, 2025 at 09:04 AM
-- Server version: 8.3.0
-- PHP Version: 8.2.18

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `ecommerce_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `address`
--

DROP TABLE IF EXISTS `address`;
CREATE TABLE IF NOT EXISTS `address` (
  `address_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `country` varchar(100) NOT NULL,
  `city` varchar(100) NOT NULL,
  `zip_code` varchar(20) NOT NULL,
  `address_line` varchar(255) NOT NULL,
  PRIMARY KEY (`address_id`),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `address`
--

INSERT INTO `address` (`address_id`, `user_id`, `country`, `city`, `zip_code`, `address_line`) VALUES
(1, 1, 'Turkey', 'Istanbul', '3400', 'ITU Maslak Kampus'),
(2, 1, 'Turkey', 'Istanbul', '34000', 'ITU Maslak');

-- --------------------------------------------------------

--
-- Table structure for table `cart`
--

DROP TABLE IF EXISTS `cart`;
CREATE TABLE IF NOT EXISTS `cart` (
  `cart_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `product_manufacturer_id` int NOT NULL,
  `quantity` int NOT NULL,
  PRIMARY KEY (`cart_id`),
  KEY `user_id` (`user_id`),
  KEY `product_manufacturer_id` (`product_manufacturer_id`)
) ;

--
-- Dumping data for table `cart`
--

INSERT INTO `cart` (`cart_id`, `user_id`, `product_manufacturer_id`, `quantity`) VALUES
(1, 1, 1, 1);

-- --------------------------------------------------------

--
-- Table structure for table `manufacturer`
--

DROP TABLE IF EXISTS `manufacturer`;
CREATE TABLE IF NOT EXISTS `manufacturer` (
  `manufacturer_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `rating` float DEFAULT '0',
  PRIMARY KEY (`manufacturer_id`)
) ;

--
-- Dumping data for table `manufacturer`
--

INSERT INTO `manufacturer` (`manufacturer_id`, `name`, `rating`) VALUES
(1, 'example_manufacturer', 3),
(2, 'Sound LTD.', 4.5);

-- --------------------------------------------------------

--
-- Table structure for table `order`
--

DROP TABLE IF EXISTS `order`;
CREATE TABLE IF NOT EXISTS `order` (
  `order_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `product_manufacturer_id` int NOT NULL,
  `order_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `order_quantity` int NOT NULL,
  `status` enum('Pending','Processing','Shipped','Delivered','Cancelled') NOT NULL DEFAULT 'Pending',
  PRIMARY KEY (`order_id`),
  KEY `user_id` (`user_id`),
  KEY `product_manufacturer_id` (`product_manufacturer_id`)
) ;

--
-- Dumping data for table `order`
--

INSERT INTO `order` (`order_id`, `user_id`, `product_manufacturer_id`, `order_date`, `order_quantity`, `status`) VALUES
(1, 1, 1, '2025-01-01 11:23:35', 2, 'Pending');

-- --------------------------------------------------------

--
-- Table structure for table `payment`
--

DROP TABLE IF EXISTS `payment`;
CREATE TABLE IF NOT EXISTS `payment` (
  `payment_id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `payment_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `amount_paid` float NOT NULL,
  `payment_method` varchar(50) NOT NULL,
  PRIMARY KEY (`payment_id`),
  KEY `order_id` (`order_id`)
) ;

--
-- Dumping data for table `payment`
--

INSERT INTO `payment` (`payment_id`, `order_id`, `payment_date`, `amount_paid`, `payment_method`) VALUES
(1, 1, '2025-01-01 11:25:32', 399.98, 'Credit Card');

-- --------------------------------------------------------

--
-- Table structure for table `product`
--

DROP TABLE IF EXISTS `product`;
CREATE TABLE IF NOT EXISTS `product` (
  `product_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `rating` float DEFAULT '0',
  PRIMARY KEY (`product_id`)
) ;

--
-- Dumping data for table `product`
--

INSERT INTO `product` (`product_id`, `name`, `description`, `rating`) VALUES
(1, 'Wireless Headphones', 'Noise-cancelling over-ear headphones', 4);

-- --------------------------------------------------------

--
-- Table structure for table `productmanufacturer`
--

DROP TABLE IF EXISTS `productmanufacturer`;
CREATE TABLE IF NOT EXISTS `productmanufacturer` (
  `product_manufacturer_id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `manufacturer_id` int NOT NULL,
  `price` float NOT NULL,
  `stock` int DEFAULT '0',
  PRIMARY KEY (`product_manufacturer_id`),
  KEY `product_id` (`product_id`),
  KEY `manufacturer_id` (`manufacturer_id`)
) ;

--
-- Dumping data for table `productmanufacturer`
--

INSERT INTO `productmanufacturer` (`product_manufacturer_id`, `product_id`, `manufacturer_id`, `price`, `stock`) VALUES
(1, 1, 1, 199.99, 48),
(2, 1, 2, 199.99, 50);

-- --------------------------------------------------------

--
-- Table structure for table `review`
--

DROP TABLE IF EXISTS `review`;
CREATE TABLE IF NOT EXISTS `review` (
  `review_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `product_id` int NOT NULL,
  `rating` int NOT NULL,
  `review_text` varchar(255) DEFAULT NULL,
  `review_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`review_id`),
  KEY `user_id` (`user_id`),
  KEY `product_id` (`product_id`)
) ;

--
-- Dumping data for table `review`
--

INSERT INTO `review` (`review_id`, `user_id`, `product_id`, `rating`, `review_text`, `review_date`) VALUES
(1, 1, 1, 5, 'Excellent!', '2025-01-01 11:27:19');

-- --------------------------------------------------------

--
-- Table structure for table `shipping`
--

DROP TABLE IF EXISTS `shipping`;
CREATE TABLE IF NOT EXISTS `shipping` (
  `shipping_id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `address_id` int NOT NULL,
  `shipping_date` datetime DEFAULT NULL,
  `estimated_delivery` datetime DEFAULT NULL,
  `status` varchar(100) NOT NULL DEFAULT 'Pending',
  PRIMARY KEY (`shipping_id`),
  KEY `order_id` (`order_id`),
  KEY `address_id` (`address_id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `shipping`
--

INSERT INTO `shipping` (`shipping_id`, `order_id`, `address_id`, `shipping_date`, `estimated_delivery`, `status`) VALUES
(1, 1, 1, '2024-12-15 10:00:00', '2024-12-20 18:00:00', 'Shipped');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
CREATE TABLE IF NOT EXISTS `user` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone_number` varchar(15) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(20) NOT NULL DEFAULT 'user',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `phone_number` (`phone_number`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`user_id`, `name`, `email`, `phone_number`, `password`, `role`) VALUES
(1, '1', '1', '1', 'scrypt:32768:8:1$HC3gDzWLlNcGZ01D$8a5a4213092ead38b166a45c83065e3a2bf9bc343ff95c987caef370ff39b3c0eb3b4049533b6676a79a69585430bd4a85d042039fde8baffafa54e4125bea90', 'admin'),
(3, 'John Johnson', 'John.johnson@example.com', '+1234567890', 'scrypt:32768:8:1$PYoUb7rGfvtzqI4q$5f29a033e58271692c7e4706ea80da6db65a7c0b32461cb8625884e4b788dc8adcc3070789f2bd08a2b23e0c76eefe34ae5724d5bea59657471e1d9c7728ee28', 'admin');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
