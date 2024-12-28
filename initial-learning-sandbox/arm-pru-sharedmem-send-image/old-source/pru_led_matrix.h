#ifndef PRU_LED_MATRIX
#define PRU_LED_MATRIX

#include <stdint.h>
#include <pru_cfg.h>
#include <stddef.h>
#include <rsc_types.h>
#include "prugpio.h"


#include "pru_pin_defs.h"

#define N_CHAN 3
#define N_ROW 32
#define N_COL 64

// uint32_t* GPIO_PORTS[4] = {(uint32_t *)GPIO0, (uint32_t *)GPIO1, (uint32_t *)GPIO2, (uint32_t *)GPIO3};



void write_color_bits(uint8_t r1, uint8_t g1, uint8_t b1, \
        uint8_t r2, uint8_t g2, uint8_t b2);

void write_row_pins(uint32_t* gpio_bank, uint8_t row);

void latch_and_enable(uint32_t* gpio_ports[4], uint32_t delay_ns);

void display_row(uint32_t delay_ns, uint8_t row_counter, uint8_t bit, \
        char* red_row1, char* green_row1, char* blue_row1, \
        char* red_row2, char* green_row2, char* blue_row2);

#endif //PRU_LED_MATRIX
