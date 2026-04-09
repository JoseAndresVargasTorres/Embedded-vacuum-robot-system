#include "libcontrol.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

/* ---- Pines GPIO ---- */
#define TRIG_FRONTAL  24
#define ECHO_FRONTAL  25
#define TRIG_LATERAL  8
#define ECHO_LATERAL  7

/* LEDs */
#define LED_AUTONOMO  5
#define LED_MANUAL    6
#define LED_OBSTACULO 13
#define LED_SISTEMA   26

/* Motor izquierdo - L293D Canal 1 */
#define IN1_IZQ       17
#define IN2_IZQ       27

/* Motor derecho - L293D Canal 2 */
#define IN3_DER       22
#define IN4_DER       23

/* ---- GPIO helpers ---- */
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
    char path[64];
    char val[4];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/value", pin);
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    fgets(val, sizeof(val), f);
    fclose(f);
    return atoi(val);
}

/* ---- Tiempo en microsegundos ---- */
static long tiempo_us() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000L + ts.tv_nsec / 1000;
}

/* ---- INICIALIZACIÓN ---- */
void control_init() {
    /* Motor izquierdo */
    gpio_export(IN1_IZQ); gpio_set_direction(IN1_IZQ, "out"); gpio_write(IN1_IZQ, 0);
    gpio_export(IN2_IZQ); gpio_set_direction(IN2_IZQ, "out"); gpio_write(IN2_IZQ, 0);

    /* Motor derecho */
    gpio_export(IN3_DER); gpio_set_direction(IN3_DER, "out"); gpio_write(IN3_DER, 0);
    gpio_export(IN4_DER); gpio_set_direction(IN4_DER, "out"); gpio_write(IN4_DER, 0);

    /* Sensor frontal */
    gpio_export(TRIG_FRONTAL); gpio_set_direction(TRIG_FRONTAL, "out");
    gpio_export(ECHO_FRONTAL); gpio_set_direction(ECHO_FRONTAL, "in");
    gpio_write(TRIG_FRONTAL, 0);

    /* Sensor lateral */
    gpio_export(TRIG_LATERAL); gpio_set_direction(TRIG_LATERAL, "out");
    gpio_export(ECHO_LATERAL); gpio_set_direction(ECHO_LATERAL, "in");
    gpio_write(TRIG_LATERAL, 0);

    /* LEDs */
    gpio_export(LED_AUTONOMO);  gpio_set_direction(LED_AUTONOMO,  "out");
    gpio_export(LED_MANUAL);    gpio_set_direction(LED_MANUAL,    "out");
    gpio_export(LED_OBSTACULO); gpio_set_direction(LED_OBSTACULO, "out");
    gpio_export(LED_SISTEMA);   gpio_set_direction(LED_SISTEMA,   "out");
    gpio_write(LED_SISTEMA, 1);

    usleep(500000);
}

/* ---- SENSOR HC-SR04 ---- */
static float medir_distancia(int trig, int echo) {
    long inicio, fin;
    long timeout = 30000;

    gpio_write(trig, 0);
    usleep(2);
    gpio_write(trig, 1);
    usleep(10);
    gpio_write(trig, 0);

    inicio = tiempo_us();
    while (gpio_read(echo) == 0) {
        if (tiempo_us() - inicio > timeout) return -1.0f;
    }
    inicio = tiempo_us();

    while (gpio_read(echo) == 1) {
        if (tiempo_us() - inicio > timeout) return -1.0f;
    }
    fin = tiempo_us();

    return (fin - inicio) * 0.0343f / 2.0f;
}

float sensor_distancia_frontal() {
    return medir_distancia(TRIG_FRONTAL, ECHO_FRONTAL);
}

float sensor_distancia_lateral() {
    return medir_distancia(TRIG_LATERAL, ECHO_LATERAL);
}

/* ---- MOTORES L293D sin PWM (enable fijo a 5V) ---- */
void motor_adelante(int velocidad) {
    gpio_write(IN1_IZQ, 1); gpio_write(IN2_IZQ, 0);
    gpio_write(IN3_DER, 1); gpio_write(IN4_DER, 0);
}

void motor_atras(int velocidad) {
    gpio_write(IN1_IZQ, 0); gpio_write(IN2_IZQ, 1);
    gpio_write(IN3_DER, 0); gpio_write(IN4_DER, 1);
}

void motor_izquierda(int velocidad) {
    gpio_write(IN1_IZQ, 0); gpio_write(IN2_IZQ, 1);
    gpio_write(IN3_DER, 1); gpio_write(IN4_DER, 0);
}

void motor_derecha(int velocidad) {
    gpio_write(IN1_IZQ, 1); gpio_write(IN2_IZQ, 0);
    gpio_write(IN3_DER, 0); gpio_write(IN4_DER, 1);
}

void motor_detener() {
    gpio_write(IN1_IZQ, 0); gpio_write(IN2_IZQ, 0);
    gpio_write(IN3_DER, 0); gpio_write(IN4_DER, 0);
}

/* ---- LEDS ---- */
void led_autonomo(int estado)  { gpio_write(LED_AUTONOMO,  estado); }
void led_manual(int estado)    { gpio_write(LED_MANUAL,    estado); }
void led_obstaculo(int estado) { gpio_write(LED_OBSTACULO, estado); }
void led_sistema(int estado)   { gpio_write(LED_SISTEMA,   estado); }

/* ---- AUDIO ---- */
void audio_reproducir(const char* archivo) {
    char cmd[256];
    snprintf(cmd, sizeof(cmd), "mpg123 -q %s &", archivo);
    system(cmd);
}

void audio_detener() {
    system("killall mpg123");
}
