#!/bin/bash
set -eux

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y nginx php-fpm php-mysql mysql-client

mkdir -p /var/www/html

cat > /var/www/html/submit.php <<EOF
<?php
\$db_host = "${db_host}";
\$db_name = "${db_name}";
\$db_user = "${db_user}";
\$db_pass = "${db_password}";

if (\$_SERVER["REQUEST_METHOD"] == "POST") {
    \$fullname = trim(\$_POST["fullname"] ?? "");
    \$email    = trim(\$_POST["email"] ?? "");
    \$phone    = trim(\$_POST["phone"] ?? "");

    if (empty(\$fullname) || empty(\$email) || empty(\$phone)) {
        die("All fields are required.");
    }

    try {
        \$pdo = new PDO("mysql:host=\$db_host;dbname=\$db_name;charset=utf8mb4", \$db_user, \$db_pass);
        \$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        \$pdo->exec("CREATE TABLE IF NOT EXISTS registrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fullname VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )");

        \$stmt = \$pdo->prepare("INSERT INTO registrations (fullname, email, phone) VALUES (?, ?, ?)");
        \$stmt->execute([\$fullname, \$email, \$phone]);

        echo "<h2>Registration successful!</h2>";
        echo "<p>Name: " . htmlspecialchars(\$fullname) . "</p>";
        echo "<p>Email: " . htmlspecialchars(\$email) . "</p>";
        echo "<p>Phone: " . htmlspecialchars(\$phone) . "</p>";
        echo "<p>Data stored in RDS MySQL successfully.</p>";
    } catch (PDOException \$e) {
        die("Database error: " . \$e->getMessage());
    }
} else {
    echo "Invalid request.";
}
?>
EOF

cat > /etc/nginx/sites-available/default <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.php index.html index.htm;
    server_name _;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php8.3-fpm.sock;
    }
}
EOF

chown -R www-data:www-data /var/www/html

systemctl restart php8.3-fpm
systemctl enable php8.3-fpm
systemctl restart nginx
systemctl enable nginx
