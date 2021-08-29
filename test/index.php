<?php
$servername = "127.0.0.1";
$username = "root";
$password = "123";
$dbname = "test1";
session_start();
$user_id = $_SESSION["user_id"];
if ($user_id < 1 || $user_id > 5){
    die();
}
$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    die("连接失败: " . $conn->connect_error);
}

$sql = "SELECT id, firstname, lastname FROM MyGuests where id>1 limit 1";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        if ($row["id"] == 1){
            echo 1;
        }
    }
} else {
    echo "0 结果";
}


$conn->close();