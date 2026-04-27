#ifndef LIBCONTROL_H
#define LIBCONTROL_H

void control_init();

float sensor_distancia_frontal();
float sensor_distancia_izquierdo();
float sensor_distancia_derecho();

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

void aspiradora_encender();
void aspiradora_apagar();

void motor_adelante_independiente(int velocidad_izq, int velocidad_der);

#endif