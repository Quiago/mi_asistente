# mi_asistente
server {
        listen 80;
        server_name 34.204.51.120:8000;
        location / {
                proxy_pass http://127.0.0.1:8000;
        }
}