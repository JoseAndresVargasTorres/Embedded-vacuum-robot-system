#ifndef LIBCONTROL_H
#define LIBCONTROL_H

/* ================================================================
 *  libcontrol.h — Vacuum Cleaner Autónomo
 *
 *  Hardware:
 *    Raspberry Pi 4 + Yocto Linux
 *    L293D  — puente H para dos motores DC 12V
 *    HC-SR04 — sensor frontal (S1) y lateral derecho (S2)
 *    4 LEDs de estado
 *    mpg123 para audio MP3
 *
 *  Geometría:
 *    Radio chasis : 14 cm
 *    Radio llanta :  3 cm  → circunferencia = 18.85 cm/vuelta
 *    Peso         : 1.3 kg
 *    Sensor S1    : frontal centrado
 *    Sensor S2    : lateral derecho a 90°
 *
 *  Algoritmo de cobertura: aleatorio con rebote
 *    - Avanza recto a VEL_NORMAL
 *    - Obstáculo frontal  → reversa + giro aleatorio 90°–180°
 *    - Pared lateral der. → corrección suave a la izquierda
 *
 *  Dependencias: libc + libpthread (incluidas en Yocto base)
 *  Compilar: gcc ... -lpthread -lm
 * ================================================================ */


/* ----------------------------------------------------------------
 *  PINES GPIO
 *  Cambiar aquí si se reasignan cables.
 * ---------------------------------------------------------------- */

/* Sensor frontal (S1) */
#define TRIG_FRONTAL    24
#define ECHO_FRONTAL    25

/* Sensor lateral derecho (S2) */
#define TRIG_LATERAL     8
#define ECHO_LATERAL     7

/* Motor izquierdo — L293D entradas IN1/IN2 */
#define IN1_IZQ         17
#define IN2_IZQ         27

/* Motor derecho — L293D entradas IN3/IN4 */
#define IN3_DER         22
#define IN4_DER         23

/* LEDs */
#define LED_AUTONOMO     5   /* Modo autónomo activo   */
#define LED_MANUAL       6   /* Modo manual activo     */
#define LED_OBSTACULO   13   /* Obstáculo detectado    */
#define LED_SISTEMA     26   /* Sistema encendido      */


/* ----------------------------------------------------------------
 *  UMBRALES DE SENSORES
 *
 *  UMBRAL_FRONTAL: distancia mínima libre al frente antes de evadir.
 *  Con robot de 14cm de radio y VEL_NORMAL, 20cm da margen suficiente.
 *
 *  UMBRAL_LATERAL: distancia mínima al costado derecho.
 *  Si S2 < 15cm → el robot se está acercando a la pared → corregir.
 *
 *  Valor -1.0 del sensor = timeout = tratar como obstáculo presente.
 * ---------------------------------------------------------------- */

#define UMBRAL_FRONTAL    20.0f   /* cm */
#define UMBRAL_LATERAL    15.0f   /* cm */


/* ----------------------------------------------------------------
 *  TIEMPOS DE MOVIMIENTO  (microsegundos)
 *
 *  T_GIRO_90: tiempo para girar 90° sobre el eje.
 *  Calculado con llanta 3cm radio, chasis 14cm radio, ~80 RPM a 45%:
 *    Arco = (π/2) × 14 = 21.99 cm
 *    Vueltas = 21.99 / 18.85 = 1.17
 *    T = (1.17 / 80) × 60s = 0.88s
 *  CALIBRAR en robot real: si gira menos de 90° → subir T_GIRO_90.
 *
 *  T_GIRO_180: el doble, para giro de 180°.
 *  El algoritmo aleatorio elige entre T_GIRO_90 y T_GIRO_180.
 *
 *  T_REVERSA: tiempo de marcha atrás antes de girar.
 *  T_AJUSTE: corrección suave lateral.
 *  T_LOOP: cadencia del loop principal (100ms = 10 ciclos/segundo).
 * ---------------------------------------------------------------- */

#define T_GIRO_90       880000    /* us — ~90°   */
#define T_GIRO_180     1760000    /* us — ~180°  */
#define T_REVERSA       500000    /* us — 0.5s   */
#define T_AJUSTE        250000    /* us — 0.25s  */
#define T_LOOP          100000    /* us — 0.1s   */


/* ----------------------------------------------------------------
 *  VELOCIDADES PWM  (0–100, porcentaje)
 *
 *  Software PWM a 1kHz (período de 1ms).
 *  VEL_NORMAL: crucero — lento, es un vacuum no un auto.
 *  VEL_GIRO:   más lento al girar para mayor precisión angular.
 *  VEL_REVERSA: moderado, solo para alejarse del obstáculo.
 *
 *  Con caja reductora y 1.3kg de carga, estos valores son
 *  estimados — CALIBRAR midiendo velocidad real sobre el piso.
 * ---------------------------------------------------------------- */

#define PWM_PERIODO_US  1000   /* 1ms = 1kHz                  */
#define VEL_NORMAL        55   /* % crucero                   */
#define VEL_GIRO          45   /* % giro — lento y preciso    */
#define VEL_REVERSA       50   /* % reversa                   */


/* ----------------------------------------------------------------
 *  FUNCIONES — INICIALIZACIÓN
 * ---------------------------------------------------------------- */

/* Configura todos los pines GPIO e inicia el hilo PWM.
 * Llamar UNA SOLA VEZ al inicio del programa. */
void control_init(void);

/* Detiene el hilo PWM y apaga todos los GPIO.
 * Llamar al salir (Ctrl+C o señal). */
void control_cleanup(void);


/* ----------------------------------------------------------------
 *  FUNCIONES — MOTORES
 *
 *  velocidad: 0–100 (porcentaje de PWM).
 *
 *  motor_izquierda() / motor_derecha():
 *    Giro sobre el propio eje — radio de giro = 0.
 *    Una rueda va hacia adelante y la otra hacia atrás.
 *    El chasis rota sin desplazarse.
 * ---------------------------------------------------------------- */
void motor_adelante(int velocidad);
void motor_atras(int velocidad);
void motor_izquierda(int velocidad);   /* Giro en eje — izquierda */
void motor_derecha(int velocidad);     /* Giro en eje — derecha   */
void motor_detener(void);


/* ----------------------------------------------------------------
 *  FUNCIONES — SENSORES HC-SR04
 *
 *  Retorna distancia en centímetros (float).
 *  Retorna -1.0f si hay timeout o error de lectura.
 *  Regla: tratar -1.0f exactamente igual que obstáculo presente.
 * ---------------------------------------------------------------- */
float sensor_distancia_frontal(void);
float sensor_distancia_lateral(void);


/* ----------------------------------------------------------------
 *  FUNCIONES — NAVEGACIÓN AUTÓNOMA
 *
 *  navegar_ciclo():
 *    Ejecuta UN ciclo completo: leer sensores → decidir → actuar.
 *    Llamar dentro del loop principal.
 *
 *  navegar_autonomo():
 *    Loop infinito. Llama navegar_ciclo() + usleep(T_LOOP).
 *    Bloquea hasta recibir señal de parada (SIGINT).
 * ---------------------------------------------------------------- */
void navegar_ciclo(void);
void navegar_autonomo(void);


/* ----------------------------------------------------------------
 *  FUNCIONES — LEDs
 *  estado: 1 = encendido, 0 = apagado
 * ---------------------------------------------------------------- */
void led_autonomo(int estado);
void led_manual(int estado);
void led_obstaculo(int estado);
void led_sistema(int estado);


/* ----------------------------------------------------------------
 *  FUNCIONES — AUDIO
 * ---------------------------------------------------------------- */
void audio_reproducir(const char *archivo);
void audio_detener(void);


#endif /* LIBCONTROL_H */