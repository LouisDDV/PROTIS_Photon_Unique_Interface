#include "mbed.h"

BufferedSerial usb_pc(USBTX, USBRX, 115200); // Port série

DigitalOut led(LED1);
AnalogIn inE1(A0);  // Entrée analogique

int main() {
    led = 1;
    wait_us(200000);
    led = 0;
    wait_us(200000);

    char command;
    
    while (1) {
        if (usb_pc.readable()) {  // Vérifier si une commande est reçue
            usb_pc.read(&command, 1);  // Lire la commande

            if (command == 'A') {  // Si la commande est 'A'
                float signal_value = inE1.read();  // Lire le signal analogique

                char buffer[20];
                int len = sprintf(buffer, "%.6f\n", signal_value);  // Convertir en chaîne de caractères
                usb_pc.write(buffer, len);  // Envoyer via USB série
            }
        }
    }
}