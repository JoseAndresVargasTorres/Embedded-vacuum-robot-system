# Prueba de sensores (solo comandos)

Este documento es para probar unicamente los 3 sensores HC-SR04 del robot:
- Frontal
- Izquierdo
- Derecho

No requiere mover motores.

## 1) Variables base

IP fija del robot en esta guia:

```bash
IP=10.140.60.188
HOST=root@$IP
```

## 2) Verificar conectividad

```bash
ping -c 3 10.140.60.188
ssh root@10.140.60.188 "echo SSH_OK && hostname"
curl -s http://10.140.60.188:5000/status
```

Esperado:
- Ping responde.
- SSH entra.
- /status devuelve JSON de conexion.

## 3) Lectura simple de sensores por API

```bash
curl -s http://10.140.60.188:5000/sensores
```

Esperado (estructura):
- frontal
- izquierda
- derecha
- unidad = cm
- obstaculo_frontal / obstaculo_izquierda / obstaculo_derecha (boolean)

## 4) Monitoreo continuo (cada 0.5s)

```bash
while true; do curl -s http://10.140.60.188:5000/sensores; echo; sleep 0.5; done
```

Detener con Ctrl+C.

## 5) Prueba por sensor (manual)

Acerca la mano/objeto a cada sensor por separado y mira la lectura.

### 5.1 Frontal

```bash
for i in $(seq 1 10); do curl -s http://10.140.60.188:5000/sensores | grep -E 'frontal|obstaculo_frontal'; echo; sleep 0.5; done
```

### 5.2 Izquierdo

```bash
for i in $(seq 1 10); do curl -s http://10.140.60.188:5000/sensores | grep -E 'izquierda|obstaculo_izquierda'; echo; sleep 0.5; done
```

### 5.3 Derecho

```bash
for i in $(seq 1 10); do curl -s http://10.140.60.188:5000/sensores | grep -E 'derecha|obstaculo_derecha'; echo; sleep 0.5; done
```

## 6) Valores aproximados esperados

Para HC-SR04 en interior, estos rangos son normales:

1. Objeto muy cerca (mano a ~5-10 cm):
- Lecturas tipicas entre 4 y 12 cm.

2. Objeto a distancia media (~20-40 cm):
- Lecturas tipicas entre 18 y 45 cm.

3. Sin obstaculo cercano (espacio abierto):
- Lecturas mayores a 50 cm (dependiendo del cuarto pueden subir bastante).

4. Lectura invalida:
- -1.0 o valores 0 en algunas iteraciones indican timeout/eco no recibido en esa muestra.

## 7) Umbrales actuales del servidor (para alerta)

Segun server.py:
- Frontal: obstaculo si 0 < frontal < 25
- Laterales: obstaculo si 0 < izquierda/derecha < 20

Entonces, por ejemplo:
- frontal = 22 => obstaculo_frontal = true
- izquierda = 22 => obstaculo_izquierda = false

## 8) Prueba recomendada rapida (3 pasos)

1. Sin objeto cerca:
```bash
curl -s http://10.140.60.188:5000/sensores
```
Las 3 distancias deberian ser relativamente altas.

2. Mano frente al sensor frontal (~10 cm):
```bash
curl -s http://10.140.60.188:5000/sensores
```
frontal deberia bajar y obstaculo_frontal deberia pasar a true.

3. Mano frente a cada lateral (~10-15 cm):
```bash
curl -s http://10.140.60.188:5000/sensores
```
izquierda/derecha deberia bajar y su bandera de obstaculo pasar a true.

## 9) Si los valores salen raros

1. Revisa alimentacion de sensores (5V y GND comun).
2. Verifica divisor resistivo en ECHO hacia GPIO (para proteger 3.3V).
3. Revisa que no haya superficies muy inclinadas/absorbentes frente al sensor.
4. Repite prueba con objeto plano y perpendicular (libro/carton).
5. Si solo falla un sensor, revisa cableado de ese TRIG/ECHO.
