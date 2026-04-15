#ifndef LIBCONTROL_H
#define LIBCONTROL_H

void control_init();

float sensor_distancia_frontal();
float sensor_distancia_lateral();

void motor_adelante(int velocidad);
void motor_atras(int velocidad);
void motor_izquierda(int velocidad);
void motor_derecha(int velocidad);
void motor_detener();

void led_autonomo(int estado);
void led_manual(int estado);
void led_obstaculo(int estado);
void led_sistema(int estado);

void audio_reproducir(const char* archivo);
void audio_pausar();
void audio_detener();

#endif
