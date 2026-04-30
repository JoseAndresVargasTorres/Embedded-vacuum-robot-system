# Debug Completo del Robot — Todos los Endpoints

```bash
IP=192.168.100.154
```

---

## 1. Conectividad básica

```bash
# Ping
ping -c 3 192.168.100.220

# Verificar servidor Flask
curl -s http://192.168.100.220:5000/status

# Verificar proceso corriendo
ssh root@192.168.100.220 "ps | grep server.py | grep -v grep"

# Ver log del servidor en tiempo real
ssh root@192.168.100.220 "tail -f /tmp/robot-server.log"
```

---

## 2. Verificar libcontrol desplegada correctamente

```bash
# Los hashes deben ser idénticos
sha256sum ~/poky/build/tmp/deploy/images/raspberrypi4-64/../../../sysroots-components/cortexa72/libcontrol/usr/lib/libcontrol.so
ssh root@192.168.100.220 "sha256sum /usr/lib/libcontrol.so"
```

---

## 3. Autenticación

```bash
# Login (devuelve cookie de sesión)
curl -s -c /tmp/robot_cookie.txt -X POST http://192.168.100.220:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Robot2026!"}'

# Logout
curl -s -b /tmp/robot_cookie.txt http://192.168.100.220:5000/logout
```

---

## 4. Motores — prueba individual

> Cada comando imprime el estado real de los pines GPIO y PWM tras ejecutarse.

```bash
# Adelante a 50%
curl -s -X POST http://192.168.100.220:5000/motor/adelante \
  -H 'Content-Type: application/json' -d '{"velocidad":50}'

# Adelante a 100% (máximo)
curl -s -X POST http://192.168.100.220:5000/motor/adelante \
  -H 'Content-Type: application/json' -d '{"velocidad":100}'

# Atrás a 60%
curl -s -X POST http://192.168.100.220:5000/motor/atras \
  -H 'Content-Type: application/json' -d '{"velocidad":60}'

# Giro izquierda (pivot) a 100%
curl -s -X POST http://192.168.100.220:5000/motor/izquierda \
  -H 'Content-Type: application/json' -d '{"velocidad":100}'

# Giro derecha (pivot) a 100%
curl -s -X POST http://192.168.100.220:5000/motor/derecha \
  -H 'Content-Type: application/json' -d '{"velocidad":100}'

# Detener
curl -s -X POST http://192.168.100.220:5000/motor/detener
```

---

## 5. Motores — verificar pines GPIO directamente en la Rasp

```bash
# Ver estado de los 4 pines de dirección
ssh root@192.168.100.220 "
  echo IN1_IZQ\(GPIO17\): \$(cat /sys/class/gpio/gpio17/value)
  echo IN2_IZQ\(GPIO27\): \$(cat /sys/class/gpio/gpio27/value)
  echo IN3_DER\(GPIO22\): \$(cat /sys/class/gpio/gpio22/value)
  echo IN4_DER\(GPIO23\): \$(cat /sys/class/gpio/gpio23/value)
"

# Ver estado PWM
ssh root@192.168.100.220 "
  echo === PWM0 \(motor izquierdo\) ===
  cat /sys/class/pwm/pwmchip0/pwm0/duty_cycle
  cat /sys/class/pwm/pwmchip0/pwm0/period
  cat /sys/class/pwm/pwmchip0/pwm0/enable
  echo === PWM1 \(motor derecho\) ===
  cat /sys/class/pwm/pwmchip0/pwm1/duty_cycle
  cat /sys/class/pwm/pwmchip0/pwm1/period
  cat /sys/class/pwm/pwmchip0/pwm1/enable
"
```

### Valores esperados por movimiento

| Movimiento    | IN1 | IN2 | IN3 | IN4 | PWM0 | PWM1 |
|---------------|-----|-----|-----|-----|------|------|
| Adelante      |  1  |  0  |  0  |  1  |  >0  |  >0  |
| Atrás         |  0  |  1  |  1  |  0  |  >0  |  >0  |
| Izquierda     |  0  |  1  |  0  |  1  |  >0  |  >0  |
| Derecha       |  1  |  0  |  1  |  0  |  >0  |  >0  |
| Detenido      |  0  |  0  |  0  |  0  |   0  |   0  |

---

## 6. Motores — prueba secuencia completa con pausa

```bash
# Adelante 2s → detener → atrás 2s → detener
curl -s -X POST http://192.168.100.220:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":100}'
sleep 2
curl -s -X POST http://192.168.100.220:5000/motor/detener
sleep 1
curl -s -X POST http://192.168.100.220:5000/motor/atras -H 'Content-Type: application/json' -d '{"velocidad":60}'
sleep 2
curl -s -X POST http://192.168.100.220:5000/motor/detener

# Giro izquierda 0.80s (debe girar ~90°)
curl -s -X POST http://192.168.100.220:5000/motor/izquierda -H 'Content-Type: application/json' -d '{"velocidad":100}'
sleep 0.80
curl -s -X POST http://192.168.100.220:5000/motor/detener

# Giro derecha 0.80s (debe girar ~90°)
curl -s -X POST http://192.168.100.220:5000/motor/derecha -H 'Content-Type: application/json' -d '{"velocidad":100}'
sleep 0.80
curl -s -X POST http://192.168.100.220:5000/motor/detener
```

---

## 7. Diagnóstico motor izquierdo aislado

```bash
# Forzar solo motor izquierdo adelante (IN1=1, IN2=0, PWM0 alto, IN3/IN4=0, PWM1=0)
ssh root@192.168.100.220 "
  echo 17 > /sys/class/gpio/export 2>/dev/null; echo out > /sys/class/gpio/gpio17/direction
  echo 27 > /sys/class/gpio/export 2>/dev/null; echo out > /sys/class/gpio/gpio27/direction
  echo 22 > /sys/class/gpio/export 2>/dev/null; echo out > /sys/class/gpio/gpio22/direction
  echo 23 > /sys/class/gpio/export 2>/dev/null; echo out > /sys/class/gpio/gpio23/direction
  echo 1 > /sys/class/gpio/gpio17/value
  echo 0 > /sys/class/gpio/gpio27/value
  echo 0 > /sys/class/gpio/gpio22/value
  echo 0 > /sys/class/gpio/gpio23/value
  echo 20000000 > /sys/class/pwm/pwmchip0/pwm0/period
  echo 20000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
  echo 1        > /sys/class/pwm/pwmchip0/pwm0/enable
  echo 0        > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
  echo Motor IZQ forzado adelante
"
sleep 2
# Detener todo
ssh root@192.168.100.220 "
  echo 0 > /sys/class/gpio/gpio17/value
  echo 0 > /sys/class/gpio/gpio27/value
  echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
  echo Motor IZQ detenido
"

# Forzar solo motor derecho adelante (IN3=0, IN4=1, PWM1 alto, IN1/IN2=0, PWM0=0)
ssh root@192.168.100.220 "
  echo 0 > /sys/class/gpio/gpio16/value
  echo 0 > /sys/class/gpio/gpio27/value
  echo 0 > /sys/class/gpio/gpio22/value
  echo 1 > /sys/class/gpio/gpio23/value
  echo 0        > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
  echo 20000000 > /sys/class/pwm/pwmchip0/pwm1/period
  echo 20000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
  echo 1        > /sys/class/pwm/pwmchip0/pwm1/enable
  echo Motor DER forzado adelante
"
sleep 2
ssh root@192.168.100.220 "
  echo 0 > /sys/class/gpio/gpio23/value
  echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
  echo Motor DER detenido
"
```

---

## 8. Sensores

```bash
# Leer los 3 sensores
curl -s http://192.168.100.220:5000/sensores | python3 -m json.tool

# Leer 5 veces seguidas con intervalo (monitoreo)
for i in 1 2 3 4 5; do
  echo "--- Lectura $i ---"
  curl -s http://192.168.100.220:5000/sensores | python3 -m json.tool
  sleep 1
done

# Verificar GPIOs de sensores directamente
ssh root@192.168.100.220 "
  echo TRIG_FRONTAL\(GPIO24\):   \$(cat /sys/class/gpio/gpio24/direction 2>/dev/null || echo 'no exportado')
  echo ECHO_FRONTAL\(GPIO25\):   \$(cat /sys/class/gpio/gpio25/direction 2>/dev/null || echo 'no exportado')
  echo TRIG_IZQ\(GPIO8\):        \$(cat /sys/class/gpio/gpio8/direction  2>/dev/null || echo 'no exportado')
  echo ECHO_IZQ\(GPIO7\):        \$(cat /sys/class/gpio/gpio7/direction  2>/dev/null || echo 'no exportado')
  echo TRIG_DER\(GPIO20\):       \$(cat /sys/class/gpio/gpio20/direction 2>/dev/null || echo 'no exportado')
  echo ECHO_DER\(GPIO21\):       \$(cat /sys/class/gpio/gpio21/direction 2>/dev/null || echo 'no exportado')
"
```

---

## 9. LEDs

```bash
# Encender/apagar cada LED individualmente
curl -s -X POST http://192.168.100.220:5000/led/sistema/1
curl -s -X POST http://192.168.100.220:5000/led/sistema/0

curl -s -X POST http://192.168.100.220:5000/led/manual/1
curl -s -X POST http://192.168.100.220:5000/led/manual/0

curl -s -X POST http://192.168.100.220:5000/led/autonomo/1
curl -s -X POST http://192.168.100.220:5000/led/autonomo/0

curl -s -X POST http://192.168.100.220:5000/led/obstaculo/1
curl -s -X POST http://192.168.100.220:5000/led/obstaculo/0

# Verificar GPIOs de LEDs directamente
ssh root@192.168.100.220 "
  echo LED_SISTEMA\(GPIO26\):   \$(cat /sys/class/gpio/gpio26/value 2>/dev/null)
  echo LED_MANUAL\(GPIO6\):     \$(cat /sys/class/gpio/gpio6/value  2>/dev/null)
  echo LED_AUTONOMO\(GPIO5\):   \$(cat /sys/class/gpio/gpio5/value  2>/dev/null)
  echo LED_OBSTACULO\(GPIO13\): \$(cat /sys/class/gpio/gpio13/value 2>/dev/null)
"
```

---

## 10. Aspiradora

```bash
# Toggle (encender si apagada, apagar si encendida)
curl -s -X POST http://192.168.100.220:5000/aspiradora/toggle

# Ver estado actual
curl -s http://192.168.100.220:5000/aspiradora/estado

# Verificar GPIO directamente
ssh root@192.168.100.220 "cat /sys/class/gpio/gpio12/value"
```

---

## 11. Modo autónomo

```bash
# Iniciar
curl -s -X POST http://192.168.100.220:5000/autonomo/iniciar

# Ver estado en tiempo real (ejecutar en otra terminal)
watch -n 0.5 "curl -s http://192.168.100.220:5000/autonomo/estado | python3 -m json.tool"

# Detener
curl -s -X POST http://192.168.100.220:5000/autonomo/detener

# Ver estado del mapa
curl -s http://192.168.100.220:5000/mapa/estado | python3 -m json.tool

# Resetear mapa
curl -s -X POST http://192.168.100.220:5000/mapa/reset
```

---

## 12. Audio (música)

```bash
# Listar canciones disponibles
curl -s http://192.168.100.220:5000/audio/lista | python3 -m json.tool

# Reproducir una canción
curl -s -X POST http://192.168.100.220:5000/audio/reproducir \
  -H 'Content-Type: application/json' -d '{"archivo":"Devorame.mp3"}'

# Pausar / reanudar
curl -s -X POST http://192.168.100.220:5000/audio/pausar

# Siguiente canción
curl -s -X POST http://192.168.100.220:5000/audio/siguiente

# Canción anterior
curl -s -X POST http://192.168.100.220:5000/audio/anterior

# Detener
curl -s -X POST http://192.168.100.220:5000/audio/detener

# Volumen 0-100
curl -s -X POST http://192.168.100.220:5000/audio/volumen/70
```

---

## 13. Sonidos de evento

```bash
curl -s -X POST http://192.168.100.220:5000/sonido/manual
curl -s -X POST http://192.168.100.220:5000/sonido/autonomo
```

---

## 14. Estado general del sistema

```bash
# CPU, memoria, temperatura
ssh root@192.168.100.220 "
  echo === CPU/Memoria ===
  cat /proc/loadavg
  free -m
  echo === Temperatura ===
  cat /sys/class/thermal/thermal_zone0/temp | awk '{printf \"%.1f°C\n\", \$1/1000}'
  echo === Red ===
  ip addr show wlan0 | grep 'inet '
  echo === Procesos robot ===
  ps | grep -E 'server.py|mpg123|wpa_supplicant' | grep -v grep
  echo === PWM exportados ===
  ls /sys/class/pwm/pwmchip0/
  echo === GPIOs exportados ===
  ls /sys/class/gpio/ | grep gpio | sort -V
"
```

---

## 15. Secuencia de diagnóstico completa (orden recomendado)

```bash
# 1. Conectividad
ping -c 2 192.168.100.220 && curl -s http://192.168.100.220:5000/status

# 2. Sensores
curl -s http://192.168.100.220:5000/sensores | python3 -m json.tool

# 3. LEDs (visual)
curl -s -X POST http://192.168.100.220:5000/led/sistema/1
curl -s -X POST http://192.168.100.220:5000/led/manual/1
curl -s -X POST http://192.168.100.220:5000/led/autonomo/1
curl -s -X POST http://192.168.100.220:5000/led/obstaculo/1
sleep 2
curl -s -X POST http://192.168.100.220:5000/led/manual/0
curl -s -X POST http://192.168.100.220:5000/led/autonomo/0
curl -s -X POST http://192.168.100.220:5000/led/obstaculo/0

# 4. Motor derecho solo (ver si gira)
curl -s -X POST http://192.168.100.220:5000/motor/derecha -H 'Content-Type: application/json' -d '{"velocidad":100}'
sleep 1
curl -s -X POST http://192.168.100.220:5000/motor/detener

# 5. Motor izquierdo solo (ver si gira — punto del bug)
curl -s -X POST http://192.168.100.220:5000/motor/izquierda -H 'Content-Type: application/json' -d '{"velocidad":100}'
sleep 1
curl -s -X POST http://192.168.100.220:5000/motor/detener

# 6. Ambos adelante
curl -s -X POST http://192.168.100.220:5000/motor/adelante -H 'Content-Type: application/json' -d '{"velocidad":100}'
sleep 2
curl -s -X POST http://192.168.100.220:5000/motor/detener

# 7. Aspiradora
curl -s -X POST http://192.168.100.220:5000/aspiradora/toggle
sleep 2
curl -s -X POST http://192.168.100.220:5000/aspiradora/toggle

# 8. Sonido
curl -s -X POST http://192.168.100.220:5000/sonido/manual
```
