<?php
$servername = "127.0.0.1";
$username = "root";
$password = "123";
$dbname = "test1";
session_start();
if ($_SESSION["user_id"] < 1 || $_SESSION["user_id"] > 5){
    echo 0;
    die();
}
