#include "libcontrol.h"
#include <signal.h>
#include <stdio.h>

/* ================================================================
 *  main.c — Vacuum Cleaner Autónomo
 *
 *  Compilar:
 *    gcc main.c libcontrol.c -o vacuum -lpthread -lm
 *
 *  Ejecutar (requiere acceso a GPIO):
 *    sudo ./vacuum
 *
 *  Salir limpiamente:
 *    Ctrl+C  →  apaga motores y LEDs antes de salir
 * ================================================================ */

static void handle_sigint(int sig) {
    (void)sig;
    printf("\n[vacuum] Señal recibida — deteniendo...\n");
    audio_detener();
    control_cleanup();
    _exit(0);
}

int main(void) {

    /* Capturar Ctrl+C para apagado limpio */
    signal(SIGINT,  handle_sigint);
    signal(SIGTERM, handle_sigint);   /* también captura kill */

    /* Inicializar GPIO, hilo PWM y LEDs */
    control_init();

    /* Sonido de inicio del sistema */
    audio_reproducir("/usr/share/vacuum/inicio_sistema.mp3");

    /* Loop autónomo infinito — bloquea aquí */
    navegar_autonomo();

    return 0;
}