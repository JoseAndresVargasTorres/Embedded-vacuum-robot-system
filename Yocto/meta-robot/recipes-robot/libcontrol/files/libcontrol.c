#include "libcontrol.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <pthread.h>

/* ================================================================
 *  libcontrol.c — Vacuum Cleaner Autónomo
 *  Algoritmo: cobertura aleatoria con rebote (random bounce)
 * ================================================================ */


/* ----------------------------------------------------------------
 *  GPIO — funciones internas
 *  Los pines se controlan escribiendo en /sys/class/gpio/
 * ---------------------------------------------------------------- */

static void gpio_export(int pin) {
    char path[64];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d", pin);
    if (access(path, F_OK) == 0) return;   /* ya exportado */
    FILE *f = fopen("/sys/class/gpio/export", "w");
    if (f) { fprintf(f, "%d", pin); fclose(f); usleep(100000); }
}

static void gpio_set_direction(int pin, const char *dir) {
    char path[64];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/direction", pin);
    FILE *f = fopen(path, "w");
    if (f) { fprintf(f, "%s", dir); fclose(f); }
}

static void gpio_write(int pin, int value) {
    char path[64];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/value", pin);
    FILE *f = fopen(path, "w");
    if (f) { fprintf(f, "%d", value); fclose(f); }
}

static int gpio_read(int pin) {
    char path[64];
    char val[4];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/value", pin);
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    fgets(val, sizeof(val), f);
    fclose(f);
    return atoi(val);
}

/* Tiempo en microsegundos — reloj monotónico, no se afecta por NTP */
static long tiempo_us(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000L + ts.tv_nsec / 1000;
}


/* ================================================================
 *  SOFTWARE PWM
 *
 *  Problema: el L293D solo recibe ON/OFF, sin PWM por hardware
 *  en los pines GPIO 17/27/22/23.
 *
 *  Solución: un hilo pthread corre en paralelo y hace ciclos de
 *  1ms (1kHz). En cada ciclo enciende el motor durante
 *  (velocidad% × 1000us) y lo apaga el resto.
 *
 *  El loop principal solo actualiza las variables compartidas:
 *    pwm_vel_izq / pwm_vel_der : 0–100
 *    pwm_dir_izq / pwm_dir_der : 1=adelante, -1=atrás, 0=stop
 *
 *  El hilo lee esas variables y aplica los pulsos.
 *  No hace falta mutex porque son escrituras atómicas de int.
 * ================================================================ */

static volatile int pwm_vel_izq  = 0;
static volatile int pwm_vel_der  = 0;
static volatile int pwm_dir_izq  = 0;
static volatile int pwm_dir_der  = 0;
static volatile int pwm_corriendo = 0;
static pthread_t    pwm_hilo;

static void* pwm_thread(void *arg) {
    (void)arg;

    while (pwm_corriendo) {

        /* Capturar estado actual de forma local */
        int vi = pwm_vel_izq;
        int vd = pwm_vel_der;
        int di = pwm_dir_izq;
        int dd = pwm_dir_der;

        /* Calcular tiempos ON proporcionales a velocidad */
        int ton_i  = (PWM_PERIODO_US * vi) / 100;
        int toff_i = PWM_PERIODO_US - ton_i;
        int ton_d  = (PWM_PERIODO_US * vd) / 100;
        int toff_d = PWM_PERIODO_US - ton_d;

        /* --- Fase ON: aplicar dirección a cada motor --- */
        if      (di ==  1) { gpio_write(IN1_IZQ,1); gpio_write(IN2_IZQ,0); }
        else if (di == -1) { gpio_write(IN1_IZQ,0); gpio_write(IN2_IZQ,1); }
        else               { gpio_write(IN1_IZQ,0); gpio_write(IN2_IZQ,0); }

        if      (dd ==  1) { gpio_write(IN3_DER,1); gpio_write(IN4_DER,0); }
        else if (dd == -1) { gpio_write(IN3_DER,0); gpio_write(IN4_DER,1); }
        else               { gpio_write(IN3_DER,0); gpio_write(IN4_DER,0); }

        /* Esperar el mayor tiempo ON de los dos motores */
        int ton_max = ton_i > ton_d ? ton_i : ton_d;
        if (ton_max > 0) usleep(ton_max);

        /* --- Fase OFF: apagar ambos motores --- */
        gpio_write(IN1_IZQ,0); gpio_write(IN2_IZQ,0);
        gpio_write(IN3_DER,0); gpio_write(IN4_DER,0);

        /* Esperar el menor tiempo OFF para completar 1ms */
        int toff_min = toff_i < toff_d ? toff_i : toff_d;
        if (toff_min > 0) usleep(toff_min);
    }

    return NULL;
}


/* ================================================================
 *  INICIALIZACIÓN
 * ================================================================ */

void control_init(void) {

    /* Semilla para el generador aleatorio del rebote */
    srand((unsigned int)time(NULL));

    /* --- Motores --- */
    gpio_export(IN1_IZQ); gpio_set_direction(IN1_IZQ,"out"); gpio_write(IN1_IZQ,0);
    gpio_export(IN2_IZQ); gpio_set_direction(IN2_IZQ,"out"); gpio_write(IN2_IZQ,0);
    gpio_export(IN3_DER); gpio_set_direction(IN3_DER,"out"); gpio_write(IN3_DER,0);
    gpio_export(IN4_DER); gpio_set_direction(IN4_DER,"out"); gpio_write(IN4_DER,0);

    /* --- Sensor frontal --- */
    gpio_export(TRIG_FRONTAL); gpio_set_direction(TRIG_FRONTAL,"out"); gpio_write(TRIG_FRONTAL,0);
    gpio_export(ECHO_FRONTAL); gpio_set_direction(ECHO_FRONTAL,"in");

    /* --- Sensor lateral derecho --- */
    gpio_export(TRIG_LATERAL); gpio_set_direction(TRIG_LATERAL,"out"); gpio_write(TRIG_LATERAL,0);
    gpio_export(ECHO_LATERAL); gpio_set_direction(ECHO_LATERAL,"in");

    /* --- LEDs --- */
    gpio_export(LED_AUTONOMO);  gpio_set_direction(LED_AUTONOMO, "out"); gpio_write(LED_AUTONOMO, 0);
    gpio_export(LED_MANUAL);    gpio_set_direction(LED_MANUAL,   "out"); gpio_write(LED_MANUAL,   0);
    gpio_export(LED_OBSTACULO); gpio_set_direction(LED_OBSTACULO,"out"); gpio_write(LED_OBSTACULO,0);
    gpio_export(LED_SISTEMA);   gpio_set_direction(LED_SISTEMA,  "out"); gpio_write(LED_SISTEMA,  1);

    /* --- Arrancar hilo PWM --- */
    pwm_corriendo = 1;
    pthread_create(&pwm_hilo, NULL, pwm_thread, NULL);

    usleep(500000);   /* 0.5s para que todo estabilice */
    printf("[vacuum] Hardware inicializado\n");
}

void control_cleanup(void) {
    pwm_corriendo = 0;
    pthread_join(pwm_hilo, NULL);
    motor_detener();
    led_autonomo(0);
    led_obstaculo(0);
    led_sistema(0);
    printf("[vacuum] Apagado limpio\n");
}


/* ================================================================
 *  MOTORES
 *  Solo actualizan las variables del hilo PWM.
 *  El hilo aplica los cambios en el siguiente ciclo (~1ms).
 * ================================================================ */

void motor_adelante(int velocidad) {
    pwm_vel_izq = velocidad;
    pwm_vel_der = velocidad;
    pwm_dir_izq =  1;
    pwm_dir_der =  1;
}

void motor_atras(int velocidad) {
    pwm_vel_izq = velocidad;
    pwm_vel_der = velocidad;
    pwm_dir_izq = -1;
    pwm_dir_der = -1;
}

/* Giro en eje hacia la izquierda:
   rueda izq. va ATRÁS, rueda der. va ADELANTE → robot rota a la izq.
   Radio de giro = 0. El centro del chasis no se desplaza. */
void motor_izquierda(int velocidad) {
    pwm_vel_izq = velocidad;
    pwm_vel_der = velocidad;
    pwm_dir_izq = -1;
    pwm_dir_der =  1;
}

/* Giro en eje hacia la derecha:
   rueda izq. va ADELANTE, rueda der. va ATRÁS → robot rota a la der. */
void motor_derecha(int velocidad) {
    pwm_vel_izq = velocidad;
    pwm_vel_der = velocidad;
    pwm_dir_izq =  1;
    pwm_dir_der = -1;
}

void motor_detener(void) {
    pwm_vel_izq = 0;
    pwm_vel_der = 0;
    pwm_dir_izq = 0;
    pwm_dir_der = 0;
    /* Escribe directo al GPIO para frenar sin esperar al hilo */
    gpio_write(IN1_IZQ,0); gpio_write(IN2_IZQ,0);
    gpio_write(IN3_DER,0); gpio_write(IN4_DER,0);
}


/* ================================================================
 *  SENSORES HC-SR04
 * ================================================================ */

static float medir_distancia(int trig, int echo) {
    long inicio, fin;
    const long timeout = 30000;   /* 30ms máximo por medición */

    /* Pulso de disparo: 10 microsegundos en TRIG */
    gpio_write(trig, 0); usleep(2);
    gpio_write(trig, 1); usleep(10);
    gpio_write(trig, 0);

    /* Esperar flanco de subida del ECHO */
    inicio = tiempo_us();
    while (gpio_read(echo) == 0) {
        if (tiempo_us() - inicio > timeout) return -1.0f;
    }

    /* Medir duración del pulso ECHO */
    inicio = tiempo_us();
    while (gpio_read(echo) == 1) {
        if (tiempo_us() - inicio > timeout) return -1.0f;
    }
    fin = tiempo_us();

    /* distancia (cm) = tiempo_us × velocidad_sonido_cm/us / 2 */
    return (fin - inicio) * 0.0343f / 2.0f;
}

float sensor_distancia_frontal(void) {
    return medir_distancia(TRIG_FRONTAL, ECHO_FRONTAL);
}

float sensor_distancia_lateral(void) {
    return medir_distancia(TRIG_LATERAL, ECHO_LATERAL);
}


/* ================================================================
 *  NAVEGACIÓN — ALGORITMO ALEATORIO CON REBOTE
 *
 *  Lógica de navegar_ciclo():
 *
 *  1. Leer S1 (frontal) y S2 (lateral derecho)
 *
 *  2. Si S1 < UMBRAL_FRONTAL o S1 == -1  →  EVASIÓN FRONTAL:
 *       a. Detener
 *       b. LED obstáculo ON
 *       c. Reversa T_REVERSA us
 *       d. Girar en eje hacia la izquierda un ángulo ALEATORIO:
 *            - 50% probabilidad: T_GIRO_90  (~90°)
 *            - 50% probabilidad: T_GIRO_180 (~180°)
 *          El ángulo aleatorio evita que el robot quede en bucle
 *          ante esquinas o configuraciones simétricas.
 *       e. Detener, pausa 50ms, LED obstáculo OFF
 *       f. return — el loop retoma en el siguiente ciclo
 *
 *  3. Si S2 < UMBRAL_LATERAL y S2 > 0  →  CORRECCIÓN LATERAL:
 *       Giro suave a la izquierda T_AJUSTE us
 *       Luego cae al paso 4 (no return)
 *
 *  4. Sin obstáculos  →  motor_adelante(VEL_NORMAL)
 * ================================================================ */

void navegar_ciclo(void) {

    float dist_f = sensor_distancia_frontal();
    float dist_l = sensor_distancia_lateral();

    printf("[nav] F:%5.1f cm  L:%5.1f cm\n", dist_f, dist_l);

    /* --- PRIORIDAD 1: obstáculo frontal --- */
    if (dist_f < UMBRAL_FRONTAL || dist_f < 0.0f) {

        led_obstaculo(1);
        motor_detener();
        usleep(50000);                        /* 50ms pausa */

        /* Reversa para alejarse del obstáculo */
        motor_atras(VEL_REVERSA);
        usleep(T_REVERSA);
        motor_detener();
        usleep(50000);

        /* Ángulo de giro aleatorio: 90° o 180° */
        long t_giro = (rand() % 2 == 0) ? T_GIRO_90 : T_GIRO_180;
        printf("[nav] EVASION — giro %s\n",
               t_giro == T_GIRO_90 ? "90 grados" : "180 grados");

        motor_izquierda(VEL_GIRO);
        usleep(t_giro);
        motor_detener();
        usleep(50000);

        led_obstaculo(0);
        return;   /* salir del ciclo — no ejecutar pasos siguientes */
    }

    /* --- PRIORIDAD 2: pared lateral derecha --- */
    if (dist_l < UMBRAL_LATERAL && dist_l > 0.0f) {
        printf("[nav] AJUSTE lateral (%.1f cm)\n", dist_l);

        /* Corrección suave a la izquierda */
        motor_izquierda(VEL_GIRO);
        usleep(T_AJUSTE);
        motor_detener();
        usleep(30000);
        /* Cae al paso siguiente — retoma avance */
    }

    /* --- PRIORIDAD 3: avanzar --- */
    motor_adelante(VEL_NORMAL);
}

void navegar_autonomo(void) {
    led_autonomo(1);
    led_manual(0);
    printf("[vacuum] Modo autonomo iniciado\n");
    audio_reproducir("/usr/share/vacuum/inicio_autonomo.mp3");

    while (1) {
        navegar_ciclo();
        usleep(T_LOOP);
    }
}


/* ================================================================
 *  LEDs
 * ================================================================ */

void led_autonomo(int estado)  { gpio_write(LED_AUTONOMO,  estado); }
void led_manual(int estado)    { gpio_write(LED_MANUAL,    estado); }
void led_obstaculo(int estado) { gpio_write(LED_OBSTACULO, estado); }
void led_sistema(int estado)   { gpio_write(LED_SISTEMA,   estado); }


/* ================================================================
 *  AUDIO
 *  mpg123 corre como proceso separado → no bloquea la navegación
 * ================================================================ */

void audio_reproducir(const char *archivo) {
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "mpg123 -q \"%s\" &", archivo);
    system(cmd);
}

void audio_detener(void) {
    system("killall mpg123 2>/dev/null");
}