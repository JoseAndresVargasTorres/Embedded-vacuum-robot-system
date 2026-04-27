#include "libcontrol.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

#define TRIG_FRONTAL    16
#define ECHO_FRONTAL    12
#define TRIG_IZQUIERDO  21
#define ECHO_IZQUIERDO  20
#define TRIG_DERECHO     1
#define ECHO_DERECHO     7
#define LED_AUTONOMO     8
#define LED_MANUAL      24
#define LED_OBSTACULO   23
#define LED_SISTEMA     25
#define IN1_IZQ         13
#define IN2_IZQ          6
#define IN3_DER          0
#define IN4_DER          5
#define GPIO_ASPIRADORA  4
#define PWM_CHIP        "/sys/class/pwm/pwmchip0"
#define PERIODO         20000000
#define PWM_MIN                20     // mínimo PWM para vencer fricción estática (~2.4V)
#define PWM_MAX                100    // máximo PWM (~12V)
#define FACTOR_CORRECCION_DER  95     // motor derecho al 95% para compensar desvío

static int pwm_configurado[2] = {0, 0};

/*
 * Mapeo lineal de velocidad solicitada a PWM real
 * Compensación por zona muerta del motor:
 * - 0% solicitado    -> 0% PWM (motor apagado)
 * - 1-100% solicitado -> PWM_MIN a PWM_MAX (20-100% PWM)
 */
static int calcular_velocidad(int velocidad_solicitada) {
    if (velocidad_solicitada <= 0)  return 0;
    if (velocidad_solicitada > 100) return 100;
    return PWM_MIN + ((velocidad_solicitada - 1) * (PWM_MAX - PWM_MIN)) / 99;
}

// Motor derecho con corrección de potencia para avance recto
static int calcular_velocidad_der(int velocidad_solicitada) {
    if (velocidad_solicitada <= 0) return 0;
    int vel = calcular_velocidad(velocidad_solicitada);
    vel = vel * FACTOR_CORRECCION_DER / 100;
    if (vel > PWM_MAX) vel = PWM_MAX;
    return vel;
}

static void gpio_export(int pin) {
    char path[64];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d", pin);
    if (access(path, F_OK) == 0) return;
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
    char path[64]; char val[4];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/value", pin);
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    fgets(val, sizeof(val), f); fclose(f);
    return atoi(val);
}

static void pwm_export(int canal) {
    char path[64];
    snprintf(path, sizeof(path), "%s/pwm%d", PWM_CHIP, canal);
    if (access(path, F_OK) == 0) return;
    FILE *f = fopen(PWM_CHIP "/export", "w");
    if (f) { fprintf(f, "%d", canal); fclose(f); usleep(100000); }
}

static void pwm_setup(int canal) {
    char path[128];
    FILE *f;

    snprintf(path, sizeof(path), "%s/pwm%d/period", PWM_CHIP, canal);
    f = fopen(path, "w");
    if (f) { fprintf(f, "%d", PERIODO); fclose(f); }
    usleep(1000);

    snprintf(path, sizeof(path), "%s/pwm%d/duty_cycle", PWM_CHIP, canal);
    f = fopen(path, "w");
    if (f) { fprintf(f, "0"); fclose(f); }
    usleep(1000);

    snprintf(path, sizeof(path), "%s/pwm%d/enable", PWM_CHIP, canal);
    f = fopen(path, "w");
    if (f) { fprintf(f, "1"); fclose(f); }
    usleep(1000);

    if (canal >= 0 && canal <= 1) pwm_configurado[canal] = 1;
}

static void pwm_set(int canal, int velocidad) {
    char path[128];
    long duty;

    if (velocidad < 0)   velocidad = 0;
    if (velocidad > 100) velocidad = 100;
    if (canal < 0 || canal > 1) return;
    if (!pwm_configurado[canal]) pwm_setup(canal);

    duty = (long)velocidad * PERIODO / 100;

    snprintf(path, sizeof(path), "%s/pwm%d/duty_cycle", PWM_CHIP, canal);
    FILE *f = fopen(path, "w");
    if (f) { fprintf(f, "%ld", duty); fclose(f); }
    usleep(1000);
}

static long tiempo_us() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000L + ts.tv_nsec / 1000;
}

void control_init() {
    gpio_export(IN1_IZQ); gpio_set_direction(IN1_IZQ, "out"); gpio_write(IN1_IZQ, 0);
    gpio_export(IN2_IZQ); gpio_set_direction(IN2_IZQ, "out"); gpio_write(IN2_IZQ, 0);
    gpio_export(IN3_DER); gpio_set_direction(IN3_DER, "out"); gpio_write(IN3_DER, 0);
    gpio_export(IN4_DER); gpio_set_direction(IN4_DER, "out"); gpio_write(IN4_DER, 0);

    gpio_export(TRIG_FRONTAL);   gpio_set_direction(TRIG_FRONTAL,   "out");
    gpio_export(ECHO_FRONTAL);   gpio_set_direction(ECHO_FRONTAL,   "in");
    gpio_write(TRIG_FRONTAL, 0);

    gpio_export(TRIG_IZQUIERDO); gpio_set_direction(TRIG_IZQUIERDO, "out");
    gpio_export(ECHO_IZQUIERDO); gpio_set_direction(ECHO_IZQUIERDO, "in");
    gpio_write(TRIG_IZQUIERDO, 0);

    gpio_export(TRIG_DERECHO);   gpio_set_direction(TRIG_DERECHO,   "out");
    gpio_export(ECHO_DERECHO);   gpio_set_direction(ECHO_DERECHO,   "in");
    gpio_write(TRIG_DERECHO, 0);

    gpio_export(LED_AUTONOMO);  gpio_set_direction(LED_AUTONOMO,  "out");
    gpio_export(LED_MANUAL);    gpio_set_direction(LED_MANUAL,    "out");
    gpio_export(LED_OBSTACULO); gpio_set_direction(LED_OBSTACULO, "out");
    gpio_export(LED_SISTEMA);   gpio_set_direction(LED_SISTEMA,   "out");
    gpio_write(LED_SISTEMA, 1);

    gpio_export(GPIO_ASPIRADORA);
    gpio_set_direction(GPIO_ASPIRADORA, "out");
    gpio_write(GPIO_ASPIRADORA, 0);

    pwm_export(0); pwm_export(1);
    pwm_setup(0);  pwm_setup(1);
}

static float medir_distancia(int trig, int echo) {
    long inicio, fin, timeout = 30000;
    gpio_write(trig, 0); usleep(2);
    gpio_write(trig, 1); usleep(10);
    gpio_write(trig, 0);
    inicio = tiempo_us();
    while (gpio_read(echo) == 0) { if (tiempo_us() - inicio > timeout) return -1.0f; }
    inicio = tiempo_us();
    while (gpio_read(echo) == 1) { if (tiempo_us() - inicio > timeout) return -1.0f; }
    fin = tiempo_us();
    return (fin - inicio) * 0.0343f / 2.0f;
}

float sensor_distancia_frontal()   { return medir_distancia(TRIG_FRONTAL,   ECHO_FRONTAL);   }
float sensor_distancia_izquierdo() { return medir_distancia(TRIG_IZQUIERDO, ECHO_IZQUIERDO); }
float sensor_distancia_derecho()   { return medir_distancia(TRIG_DERECHO,   ECHO_DERECHO);   }

/* ───────────────────────────────────────────────────────────────────────────
 * MOVIMIENTOS
 * ───────────────────────────────────────────────────────────────────────────
 * Motores montados en espejo:
 *   Motor IZQ: IN1=1 IN2=0 → avanza
 *   Motor DER: IN3=0 IN4=1 → avanza
 *
 *   Adelante:  IN1=1 IN2=0  IN3=0 IN4=1
 *   Atrás:     IN1=0 IN2=1  IN3=1 IN4=0
 *   Izquierda: IN1=0 IN2=1  IN3=0 IN4=1  (IZQ atrás,    DER adelante)
 *   Derecha:   IN1=1 IN2=0  IN3=1 IN4=0  (IZQ adelante, DER atrás)
 */

void motor_adelante(int velocidad) {
    pwm_set(1, calcular_velocidad(velocidad));
    pwm_set(0, calcular_velocidad_der(velocidad));
    gpio_write(IN1_IZQ, 1); gpio_write(IN2_IZQ, 0);
    gpio_write(IN3_DER, 0); gpio_write(IN4_DER, 1);
}

void motor_adelante_independiente(int velocidad_izq, int velocidad_der) {
    int vel_i = calcular_velocidad(velocidad_izq);
    int vel_d = calcular_velocidad_der(velocidad_der);
    pwm_set(0, vel_i);
    pwm_set(1, vel_d);
    gpio_write(IN1_IZQ, 1); gpio_write(IN2_IZQ, 0);
    gpio_write(IN3_DER, 0); gpio_write(IN4_DER, 1);
}

void motor_atras(int velocidad) {
    pwm_set(1, calcular_velocidad(velocidad));
    pwm_set(0, calcular_velocidad_der(velocidad));
    gpio_write(IN1_IZQ, 0); gpio_write(IN2_IZQ, 1);
    gpio_write(IN3_DER, 1); gpio_write(IN4_DER, 0);
}

/* Pivot izquierda: IZQ atrás, DER adelante */
void motor_izquierda(int velocidad) {
    int vel = calcular_velocidad(velocidad);
    pwm_set(1, vel);
    pwm_set(0, vel);
    gpio_write(IN1_IZQ, 0); gpio_write(IN2_IZQ, 1);
    gpio_write(IN3_DER, 0); gpio_write(IN4_DER, 1);
}

/* Pivot derecha: IZQ adelante, DER atrás */
void motor_derecha(int velocidad) {
    int vel = calcular_velocidad(velocidad);
    pwm_set(1, vel);
    pwm_set(0, vel);
    gpio_write(IN1_IZQ, 1); gpio_write(IN2_IZQ, 0);
    gpio_write(IN3_DER, 1); gpio_write(IN4_DER, 0);
}

void motor_detener() {
    pwm_set(0, 0); pwm_set(1, 0);
    gpio_write(IN1_IZQ, 0); gpio_write(IN2_IZQ, 0);
    gpio_write(IN3_DER, 0); gpio_write(IN4_DER, 0);
}

void led_autonomo(int estado)  { gpio_write(LED_AUTONOMO,  estado); }
void led_manual(int estado)    { gpio_write(LED_MANUAL,    estado); }
void led_obstaculo(int estado) { gpio_write(LED_OBSTACULO, estado); }
void led_sistema(int estado)   { gpio_write(LED_SISTEMA,   estado); }

void aspiradora_encender() {
    gpio_write(GPIO_ASPIRADORA, 1);
}

void aspiradora_apagar() {
    gpio_write(GPIO_ASPIRADORA, 0);
}

void audio_reproducir(const char* archivo) {
    char cmd[256];
    system("killall mpg123 2>/dev/null");
    usleep(200000);
    snprintf(cmd, sizeof(cmd), "mpg123 -o alsa -a hw:1,0 -q %s &", archivo);
    system(cmd);
}

void audio_pausar() {
    /* Pausa manejada desde Python con subprocess */
}

void audio_detener() {
    system("killall mpg123 2>/dev/null");
}
