#!/bin/bash
set -eux

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y nginx

cat > /var/www/html/index.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Registration Form</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        form { width: 350px; }
        input { width: 100%; padding: 10px; margin: 8px 0; }
        button { padding: 10px 15px; cursor: pointer; }
    </style>
</head>
<body>
    <h2>User Registration</h2>
    <form method="POST" action="/submit.php">
        <label>Full Name</label>
        <input type="text" name="fullname" required>

        <label>Email</label>
        <input type="email" name="email" required>

        <label>Phone</label>
        <input type="text" name="phone" required>

        <button type="submit">Register</button>
    </form>
</body>
</html>
EOF

cat > /etc/nginx/sites-available/default <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html index.htm;
    server_name _;

    location / {
        try_files \$uri \$uri/ =404;
    }

    location = /submit.php {
        proxy_pass http://${app_private_ip}/submit.php;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

systemctl restart nginx
systemctl enable nginx
