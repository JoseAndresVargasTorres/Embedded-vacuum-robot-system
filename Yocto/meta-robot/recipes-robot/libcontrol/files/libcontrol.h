#ifndef LIBCONTROL_H
#define LIBCONTROL_H

/* ---- MOTORES ---- */
void motor_adelante(int velocidad);
void motor_atras(int velocidad);
void motor_izquierda(int velocidad);
void motor_derecha(int velocidad);
void motor_detener();

/* ---- SENSORES ---- */
float sensor_distancia_frontal();
float sensor_distancia_lateral();

/* ---- LEDS ---- */
void led_autonomo(int estado);
void led_manual(int estado);
void led_obstaculo(int estado);
void led_sistema(int estado);

/* ---- AUDIO ---- */
void audio_reproducir(const char* archivo);
void audio_detener();

#endif /* LIBCONTROL_H */
