# Comandos de prueba del robot (post cambios)

Este documento sirve para validar que los cambios en `libcontrol`, `server.py` y dashboard quedaron funcionando.

## 0) Variables

Ejecuta esto primero en tu PC:

```bash
IP=192.168.100.154
HOST=root@$IP
```

---

## 1) Verificacion base (sin motores)

### 1.1 Red y SSH

```bash
ping -c 3 $IP
ssh $HOST "echo SSH_OK && hostname"
```

### 1.2 Servicio del servidor

```bash
ssh $HOST "ps | grep 'server.py' | grep -v grep || echo server_no_activo"
curl -s http://$IP:5000/status
```

### 1.3 Libreria instalada

```bash
ssh $HOST "ls -l /usr/lib/libcontrol.so && sha256sum /usr/lib/libcontrol.so"
```

### 1.4 Comparar hash local vs remoto de libcontrol

```bash
sha256sum /home/jose/poky/build/tmp-glibc/sysroots-components/cortexa72/libcontrol/usr/lib/libcontrol.so
ssh $HOST "sha256sum /usr/lib/libcontrol.so"
```

Los hashes deben ser iguales.

---

## 2) Verificacion API de control (sin motores)

### 2.1 Comandos de movimiento devuelven OK

```bash
curl -s -X POST http://$IP:5000/motor/adelante  -H 'Content-Type: application/json' -d '{"velocidad":20}'
curl -s -X POST http://$IP:5000/motor/atras     -H 'Content-Type: application/json' -d '{"velocidad":20}'
curl -s -X POST http://$IP:5000/motor/izquierda -H 'Content-Type: application/json' -d '{"velocidad":20}'
curl -s -X POST http://$IP:5000/motor/derecha   -H 'Content-Type: application/json' -d '{"velocidad":20}'
curl -s -X POST http://$IP:5000/motor/detener
```

### 2.2 Validar cambio de velocidad por API

```bash
curl -s -X POST http://$IP:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":20}'
curl -s -X POST http://$IP:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":60}'
curl -s -X POST http://$IP:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":100}'
```

Debe responder `"status":"ok"` y la `"velocidad"` enviada.

---

## 3) Verificacion PWM en runtime (si el sysfs expone canales)

```bash
ssh $HOST "ls -laL /sys/class/pwm/pwmchip0"
```

Si existen `pwm0` y `pwm1`, prueba:

```bash
curl -s -X POST http://$IP:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":20}'
ssh $HOST "echo v20 pwm0=$(cat /sys/class/pwm/pwmchip0/pwm0/duty_cycle) pwm1=$(cat /sys/class/pwm/pwmchip0/pwm1/duty_cycle)"

curl -s -X POST http://$IP:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":100}'
ssh $HOST "echo v100 pwm0=$(cat /sys/class/pwm/pwmchip0/pwm0/duty_cycle) pwm1=$(cat /sys/class/pwm/pwmchip0/pwm1/duty_cycle)"
```

`v100` debe ser mayor que `v20`.

---

## 4) Verificacion dashboard/estaticos

### 4.1 Archivos estaticos remotos existen

```bash
ssh $HOST "ls -l /opt/robot-server/static/dashboard.js /opt/robot-server/static/dashboard.css /opt/robot-server/templates/dashboard.html"
```

### 4.2 Hash local/remoto de dashboard.js

```bash
sha256sum /home/jose/poky/meta-robot/recipes-robot/robot-server/files/static/dashboard.js
ssh $HOST "sha256sum /opt/robot-server/static/dashboard.js"
```

---

## 5) Persistencia tras reinicio

```bash
ssh $HOST "reboot" 
# Espera ~40s y luego:
ssh $HOST "echo boot_ok && sha256sum /usr/lib/libcontrol.so"
curl -s http://$IP:5000/status
```

---

## 6) Prueba funcional cuando tengas motores

```bash
# Avance recto
curl -s -X POST http://$IP:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":20}'
sleep 2
curl -s -X POST http://$IP:5000/motor/detener

# Prueba de escalado
curl -s -X POST http://$IP:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":50}'
sleep 2
curl -s -X POST http://$IP:5000/motor/detener

curl -s -X POST http://$IP:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":100}'
sleep 2
curl -s -X POST http://$IP:5000/motor/detener
```

Observa:
- que adelante/atras no se desvie de forma extrema.
- que 100% se note mas rapido que 50% y 20%.

---

## 7) Comando rapido de health check

```bash
IP=192.168.100.154; HOST=root@$IP; \
ssh $HOST "sha256sum /usr/lib/libcontrol.so; ps | grep 'server.py' | grep -v grep || true"; \
curl -s http://$IP:5000/status
```



echo "==============================="
echo "PRUEBA: ADELANTE"
echo "==============================="
echo 20000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 20000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 1 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 1 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=1 IN2=0 IN3=0 IN4=1"
sleep 2

echo 1 > /sys/class/gpio/gpio27/value

echo "==============================="
echo "PRUEBA: DETENER"
echo "==============================="
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=0 IN2=0 IN3=0 IN4=0"
sleep 1

echo "==============================="
echo "PRUEBA: ATRAS"
echo "==============================="
echo 10000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 10000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 1 > /sys/class/gpio/gpio27/value
echo 1 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=0 IN2=1 IN3=1 IN4=0"
sleep 2

echo "==============================="
echo "PRUEBA: DETENER"
echo "==============================="
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
sleep 1

echo "==============================="
echo "PRUEBA: IZQUIERDA (pivot)"
echo "==============================="
echo 10000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 10000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 1 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 1 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=0 IN2=1 IN3=0 IN4=1"
sleep 2

echo "==============================="
echo "PRUEBA: DETENER"
echo "==============================="
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
sleep 1

echo "==============================="
echo "PRUEBA: DERECHA (pivot)"
echo "==============================="
echo 10000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 10000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 1 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 1 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=1 IN2=0 IN3=1 IN4=0"
sleep 2

echo "==============================="
echo "DETENER TODO"
echo "==============================="
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
echo "Listo"